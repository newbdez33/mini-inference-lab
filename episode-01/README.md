# EP1 · 从 Python 到第一次模型推理

Mini 模型推理课的第一集。观众会写 Python，但还没自己把模型跑起来。

时长 3 分 29 秒（209.4 秒）。系列目录、怎么跑、怎么重渲染，见仓库根目录的 README。

这一集只用一个小模型和同一句输入：`什么是 token？`。模型是 Qwen2.5-0.5B-Instruct。

## 成片

- `mini-inference-ep01.mp4`：1080×1920，H.264，yuv420p，带普通话旁白和烧录字幕
- `cover-ep01.png`：封面
- `subtitles.srt`：字幕
- `narration.md`：口播和字幕对照
- `example_infer.py`：同一句的可运行示例
- `tokenizer_verification.json`：分词器实际切分和理论体积
- `render_episode.py`：确定性画面渲染，不用视频生成模型

## 示例怎么跑

只核对分词，不下载权重：

```sh
python -m pip install -r requirements.txt
python example_infer.py --tokens-only
```

`apply_chat_template` 需要 `jinja2>=3.1`。Transformers 5.22 的默认安装不带它，所以写在 `requirements.txt` 里。

真的生成时会下载约 1GB 量级的权重。制作这集时没有跑这一步，所以片子里的答句标成「示例」。

```sh
python example_infer.py
```

分词部分在 Transformers 5.22.1 上跑过。生成函数按同一版本的 `dtype=` 和 `generate` 写法准备。CPU 上用 FP32，支持的 GPU 上优先 BF16，否则 FP16。

## 画面里的数字

都是理论估算，不是 `nvidia-smi`，也没有加载权重核对。

- 按 0.5B = 5×10^8 个参数：FP32 理论权重 2.0 GB，FP16 或 BF16 为 1.0 GB。GB 按 10^9 字节。
- 用公开 config 和 Transformers 5.22.1 里的 Qwen2 结构逐层相加，约 494,032,768 个参数。16 位约 0.988 GB。词嵌入和 lm_head 共享，只计一次。
- KV Cache：16 位、一条序列，每增加 1 个 token 约 12288 字节，也就是 12.3 KB（按 1000 字节）。

FP16 是 1 位符号、5 位指数、10 位尾数。BF16 是 1、8、7。两边都是 16 位，存一个参数都大约 2 字节。BF16 不更省显存，也不总是更精确。

正文切分（未套模板）来自分词器：

| 文本 | id |
| --- | --- |
| 什么是 | 106582 |
| 空格 + token | 3950 |
| ？ | 11319 |

套上 `apply_chat_template` 之后一共 32 个 token，形状是 `[1, 32]`。系统提示在画面里收成一块，那一块的排版是示意，token 数核对过。

## 重做画面

需要 ffmpeg、上面的 Python 包，以及 `assets/fonts/` 里的 Noto Sans SC。字体是 SIL Open Font License。

```sh
python render_episode.py preview
python render_episode.py build
```

`build` 会用 edge-tts 的 `zh-CN-XiaoxiaoNeural` 生成旁白，再混一条很轻的原创垫乐。旁白大约 -16 LUFS，垫乐更低。

## 头像

`avatar/avatar-2d.png` 是已确认的 Mini 当前 2D 头像：黑直发齐刘海、粉心发夹、金圈耳环、棕眼。文件名保持这样，渲染脚本按这个路径读取；文件内容是 JPEG。入库时去掉了内嵌清单，像素没有重编码。渲染时去掉浅灰底，裁成头和一点脖子，放在左下角。说话时在原来的嘴上叠一个小开口，头会轻轻点。没有另画一张脸，也没有放其他角色的素材。
