"""Run one CPU or CUDA inference experiment with a small chat model."""

import argparse
import sys


MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu", help="Inference device (default: cpu).")
    args = parser.parse_args(argv)

    try:
        question = input("Prompt: ").strip()
    except EOFError:
        print("No prompt received.", file=sys.stderr)
        return 2
    if not question:
        print("Prompt must not be empty.", file=sys.stderr)
        return 2

    import torch

    if args.device == "cuda" and not torch.cuda.is_available():
        print(
            "CUDA is not available. Check the NVIDIA driver and CUDA build of PyTorch, "
            "or run again with --device cpu.",
            file=sys.stderr,
        )
        return 2

    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

    print(f"Loading {MODEL_ID} on {args.device.upper()} (float32)...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, dtype=torch.float32
    ).to(args.device)
    model.eval()

    messages = [{"role": "user", "content": question}]
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(args.device)

    # Keep model-specific sampling defaults out of this greedy experiment.
    generation = GenerationConfig(
        max_new_tokens=64,
        do_sample=False,
        eos_token_id=model.generation_config.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    print("Generating...", flush=True)
    with torch.inference_mode():
        output = model.generate(**inputs, generation_config=generation)

    new_ids = output[0, inputs["input_ids"].shape[-1]:]
    answer = tokenizer.decode(new_ids, skip_special_tokens=True)
    print("Answer:")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
