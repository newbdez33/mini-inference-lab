# Mini 模型推理课

给会写 Python、还没自己把模型跑起来的人。竖屏讲一次推理里发生的事。

目前入库的是 **EP1《从 Python 到第一次模型推理》**。成片 3 分 29 秒（容器时长 209.4 秒，1080×1920，H.264 + AAC）。

## 目录

```text
README.md
assets/fonts/                         各集共用的 Noto Sans SC（SIL OFL 1.1）
  OFL.txt
  NotoSansSC-Regular.ttf
  NotoSansSC-Medium.ttf
  NotoSansSC-Bold.ttf
episode-01/                           本集
  README.md
  mini-inference-ep01.mp4             成片，约 10.6 MB
  cover-ep01.png
  subtitles.srt
  narration.md
  example_infer.py
  requirements.txt
  tokenizer_verification.json
  render_episode.py
  avatar/avatar-2d.png                Mini 当前 2D 头像
```

以后每一集放在 `episode-NN/`。文件名沿用 `mini-inference-epNN.mp4`、`cover-epNN.png`、`narration.md`、`subtitles.srt`、`example_infer.py`、`render_episode.py`、`README.md`。画面是暖米底、圆角白卡、大标题、底部胶囊和慢速圆点。讲解员是 Mini 的头部，放在左下角。这个仓库只收 Mini 这一套头像。

## 这一集

| | |
| --- | --- |
| 系列 | Mini 模型推理课 |
| 集数 | EP1 |
| 标题 | 从 Python 到第一次模型推理 |
| 时长 | 3 分 29 秒（209.4 秒） |
| 模型 | Qwen2.5-0.5B-Instruct |
| 例句 | 什么是 token？ |
| 成片 | [episode-01/mini-inference-ep01.mp4](episode-01/mini-inference-ep01.mp4) |
| 封面 | [episode-01/cover-ep01.png](episode-01/cover-ep01.png) |
| 旁白和字幕 | [episode-01/narration.md](episode-01/narration.md)、[episode-01/subtitles.srt](episode-01/subtitles.srt) |
| 示例 | [episode-01/example_infer.py](episode-01/example_infer.py) |
| 本集说明 | [episode-01/README.md](episode-01/README.md) |

画面上的答句标成「示例」。制作时核对过分词，没有下载权重，也没有调用 generate。

## 运行分词示例

在 `episode-01/`：

```sh
python -m pip install -r requirements.txt
python example_infer.py --tokens-only
```

这一步下载分词器和 config，不下载权重。Transformers 5.22 的 `apply_chat_template` 需要 `jinja2>=3.1`。这个包不在 transformers 的默认依赖里，`requirements.txt` 已单独列出。

核对结果应与 `tokenizer_verification.json` 一致：

| 文本 | id |
| --- | --- |
| 什么是 | 106582 |
| 空格 + token | 3950 |
| ？ | 11319 |

套上 `apply_chat_template` 之后一共 32 个 token，形状是 `[1, 32]`。系统提示在画面里收成一块，那一块的排版是示意，token 数核对过（21 + 正文所在轮次 8 + assistant 起始 3）。

直接运行 `python example_infer.py` 会下载约 1 GB 量级的权重并调用 generate。制作这集时没有跑这一步，仓库里也不附带权重。CPU 上用 FP32；有 CUDA 且支持 BF16 时用 BF16，否则用 FP16。`temperature` 只在 `do_sample=True` 时传入。

## 显存数字

都是理论估算，按十进制 GB（1 GB = 10^9 字节），只计权重，不是显卡实测。

- 按 0.5B = 5×10^8 个参数：FP32 理论权重 2.0 GB，FP16 或 BF16 为 1.0 GB。
- 用公开 config 和 Transformers 5.22.1 里的 Qwen2 结构逐层相加：494,032,768 个参数。16 位约 0.988 GB，字幕写成约 0.99 GB。词嵌入和 lm_head 共享，只计一次。
- FP16 是 1 位符号、5 位指数、10 位尾数。BF16 是 1 位符号、8 位指数、7 位尾数。两边都是 16 位，一个参数大约 2 字节。
- KV Cache：16 位、一条序列，每增加 1 个 token 为 12288 字节，也就是 12.3 KB（按 1000 字节）。

## 重新渲染

需要系统里的 `ffmpeg`，以及 `requirements.txt` 里的 Pillow、NumPy、edge-tts。中文用 `assets/fonts/` 的 Noto Sans SC。许可证在 [assets/fonts/OFL.txt](assets/fonts/OFL.txt)。版权为 Adobe 2014–2021，保留字体名 Source。请保持字体文件原名。

在仓库根目录：

```sh
python episode-01/render_episode.py preview
python episode-01/render_episode.py build
```

`preview` 把静帧写到 `episode-01/stills/`，并重写封面。`build` 用 edge-tts 的 `zh-CN-XiaoxiaoNeural`（语速 -3%）合成旁白，混一条很轻的原创垫乐，然后覆盖本集的 mp4、srt、旁白稿和封面。旁白大约 -16 LUFS。仓库里的 mp4 是已经交付的这一版成片。`stills/` 和 `audio/` 是中间文件，不提交。

渲染脚本按路径读取 `episode-01/avatar/avatar-2d.png`。这个文件名保持不变；内容是 JPEG，画面是 Mini 当前的 2D 头像：黑直发齐刘海、粉心发夹、金圈耳环、棕眼。入库时去掉了内嵌清单，像素没有重编码。

## 后续主题（计划，尚未制作）

下面只是可以接着做的题目。仓库里还没有这些集的目录或成片。

- 把系统提示从一整块拆开，看那 21 个 token 各自是什么
- 同一句上对照贪心和抽样，看 `temperature` 如何只在 `do_sample=True` 时生效
- 沿着每 token 12.3 KB，讲 KV Cache 怎样随上下文变长
- 第一次真正下载权重并 generate，只解码新增的 token
- 同一小模型在 CPU FP32 与 GPU FP16/BF16 之间怎么选 dtype
