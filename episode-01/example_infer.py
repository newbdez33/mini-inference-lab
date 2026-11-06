"""用 Qwen2.5-0.5B-Instruct 做一次最小推理。

观众会写 Python，但还没把模型跑起来。这个文件只做四件事：

1. 用分词器把同一句「什么是 token？」切成 token。
2. 用 apply_chat_template 包成这个指令模型要的输入。
3. 加载模型，在 inference_mode 里 generate。
4. 只解码新生成的 token。

分词部分已在本环境用 Transformers 5.22.1 跑通。当时只下载了
config.json 和 tokenizer 文件，没有下载模型权重，也没有调用 generate。
生成函数按同一版本的写法准备好，直接运行会下载约 1GB 量级的权重。

    python example_infer.py --tokens-only
    python example_infer.py
"""

from __future__ import annotations

import argparse
import json
import sys

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
USER_TEXT = "什么是 token？"

# 视频里的整数估算：0.5B = 5×10^8 个参数。不是这个检查点的实测参数量。
ROUND_PARAMS = 500_000_000


def theoretical_weight_gb(num_params: int, bytes_per_param: int) -> float:
    """十进制 GB（1 GB = 10^9 字节）。只代表权重占用，不是显存实测。"""
    return num_params * bytes_per_param / 1_000_000_000


def structure_param_count() -> int:
    """按 Transformers 5.22.1 里 Qwen2 的模块定义，和这份 config 逐项相加。

    公开 config（Qwen/Qwen2.5-0.5B-Instruct）：
    vocab 151936，hidden 896，layers 24，intermediate 4864，
    attention heads 14，kv heads 2，tie_word_embeddings true。
    head_dim 在 config 里没有单独写出，模型代码用 hidden // heads = 64。

    计入：词嵌入、每层 q/k/v/o、MLP、两个 RMSNorm、最终 RMSNorm。
    q/k/v 带 bias，o 和 MLP 不带。lm_head 与词嵌入共享，只计一次。
    RoPE 的 inv_freq 是 buffer，不计。
    没有加载 state_dict，所以这是结构推算，不是文件大小。
    """
    hidden = 896
    vocab = 151936
    layers = 24
    intermediate = 4864
    num_heads = 14
    num_kv_heads = 2
    head_dim = hidden // num_heads
    q = hidden * (num_heads * head_dim) + num_heads * head_dim
    k = hidden * (num_kv_heads * head_dim) + num_kv_heads * head_dim
    v = k
    o = (num_heads * head_dim) * hidden
    mlp = 3 * hidden * intermediate
    layer = q + k + v + o + mlp + 2 * hidden
    return vocab * hidden + layers * layer + hidden


def kv_bytes_per_token(bytes_per_elem: int = 2) -> int:
    """一条序列、每多一个 token，K 和 V 的理论字节数。

    2 个状态 × 24 层 × 2 个 kv head × 64 维 × 每元素字节数。
    """
    return 2 * 24 * 2 * 64 * bytes_per_elem


def show_tokenization(save_path: str | None = None) -> dict:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    bare = tokenizer(USER_TEXT, add_special_tokens=False)
    bare_pieces = [
        {"id": int(index), "text": tokenizer.decode([index])}
        for index in bare["input_ids"]
    ]

    messages = [{"role": "user", "content": USER_TEXT}]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(prompt, add_special_tokens=False, return_offsets_mapping=True)
    pieces = []
    for index, (start, end) in zip(encoded["input_ids"], encoded["offset_mapping"]):
        pieces.append(
            {
                "id": int(index),
                "text": prompt[start:end],
                "start": int(start),
                "end": int(end),
            }
        )

    import transformers

    report = {
        "model_id": MODEL_ID,
        "user_text": USER_TEXT,
        "transformers": transformers.__version__,
        "bare_pieces": bare_pieces,
        "bare_count": len(bare_pieces),
        "prompt": prompt,
        "prompt_pieces": pieces,
        "prompt_count": len(pieces),
        "round_half_billion": {
            "params": ROUND_PARAMS,
            "fp32_gb": theoretical_weight_gb(ROUND_PARAMS, 4),
            "fp16_or_bf16_gb": theoretical_weight_gb(ROUND_PARAMS, 2),
            "note": "十进制 GB。只按 5×10^8 参数乘每参数字节数，不是显存实测。",
        },
        "structure_params": structure_param_count(),
        "structure_fp32_gb": theoretical_weight_gb(structure_param_count(), 4),
        "structure_fp16_or_bf16_gb": theoretical_weight_gb(structure_param_count(), 2),
        "kv_bytes_per_token_fp16": kv_bytes_per_token(2),
        "notes": [
            "bare_pieces 是正文本身，没有对话模板。",
            "prompt 含默认系统提示、user 标记和 assistant 生成提示。",
            "结构参数按当前库的 Qwen2 模块相加，未加载权重核对。",
            "FP16 与 BF16 每个权重参数都是 2 字节，理论体积相同。",
        ],
    }
    print(f"transformers {report['transformers']}")
    print("正文切分（未套模板）:")
    for piece in bare_pieces:
        print(f"  {piece['id']:>8}  {piece['text']!r}")
    print(f"套上模板后共 {report['prompt_count']} 个 token")
    print(
        "0.5B 理论权重 "
        f"FP32 {report['round_half_billion']['fp32_gb']:.1f} GB，"
        f"16 位 {report['round_half_billion']['fp16_or_bf16_gb']:.1f} GB"
    )
    print(
        f"结构加总 {report['structure_params']} 参数，"
        f"16 位约 {report['structure_fp16_or_bf16_gb']:.3f} GB"
    )
    print(f"KV 每 token（16 位，一条序列）{report['kv_bytes_per_token_fp16']} 字节")
    if save_path:
        with open(save_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"写入 {save_path}")
    return report


def choose_dtype_and_device():
    import torch

    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16, "cuda"
    if torch.cuda.is_available():
        return torch.float16, "cuda"
    # CPU 上用 FP32 更稳妥。16 位能省的是显存里的权重体积，不是正确率保证。
    return torch.float32, "cpu"


def load_model(dtype, device):
    import torch
    from transformers import AutoModelForCausalLM

    kwargs = {"dtype": dtype}
    try:
        model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
    except TypeError:
        # Transformers 4.x 用 torch_dtype。5.x 改成 dtype，旧名字仍可用。
        model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=dtype)
    model.to(device)
    model.eval()
    return model


def generate_once(model, tokenizer, device, *, do_sample: bool):
    """贪心或抽样。temperature 只在 do_sample=True 时传入。

    这份模型的 generation_config.json 默认 do_sample=true，
    temperature=0.7，top_p=0.8，top_k=20，repetition_penalty=1.1。
    所以贪心必须显式写 do_sample=False。
    抽样示例把 top_k 和 repetition_penalty 也写明，避免默认值悄悄参与。
    这些参数只影响倾向，不保证回答正确。
    """
    messages = [{"role": "user", "content": USER_TEXT}]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}
    prompt_len = inputs["input_ids"].shape[-1]

    generate_kwargs = {
        "max_new_tokens": 32,
        "do_sample": do_sample,
        "repetition_penalty": 1.0,
    }
    if do_sample:
        generate_kwargs["temperature"] = 0.7
        generate_kwargs["top_p"] = 0.8
        generate_kwargs["top_k"] = 20
    # 贪心时不传 temperature、top_p、top_k。关掉抽样后它们不参与选择。

    import torch

    with torch.inference_mode():
        output_ids = model.generate(**inputs, **generate_kwargs)

    new_ids = output_ids[0, prompt_len:]
    text = tokenizer.decode(new_ids, skip_special_tokens=True)
    return {
        "prompt_len": int(prompt_len),
        "new_ids": [int(item) for item in new_ids.tolist()],
        "text": text,
        "do_sample": do_sample,
    }


def run_generation() -> None:
    from transformers import AutoTokenizer

    dtype, device = choose_dtype_and_device()
    print(f"加载 {MODEL_ID}  dtype={dtype}  device={device}")
    print("这一步会下载权重。视频制作时没有执行这里。")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = load_model(dtype, device)

    greedy = generate_once(model, tokenizer, device, do_sample=False)
    print("贪心解码:", greedy["text"])
    sampled = generate_once(model, tokenizer, device, do_sample=True)
    print("抽样解码:", sampled["text"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Qwen2.5-0.5B-Instruct 最小推理示例")
    parser.add_argument(
        "--tokens-only",
        action="store_true",
        help="只跑分词和理论体积，不下载权重",
    )
    parser.add_argument(
        "--save-json",
        default="",
        help="把分词核对结果写成 JSON",
    )
    args = parser.parse_args(argv)
    show_tokenization(args.save_json or None)
    if args.tokens_only:
        return 0
    run_generation()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
