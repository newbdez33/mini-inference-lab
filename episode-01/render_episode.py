"""竖屏教学片：基础推理。确定性绘制，不使用视频生成模型。

视觉参照 pyon-promo-r4 的插画段：暖米底、圆角白卡、粗标题、底部胶囊、
慢速圆点、逐步高亮。不复制实拍、吉祥物、网址和营销结尾。
节奏按教学停顿，不按广告切点。
"""

from __future__ import annotations

import asyncio
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SERIES = ROOT.parent
JSON_PATH = ROOT / "tokenizer_verification.json"
FONT_BOLD = SERIES / "assets" / "fonts" / "NotoSansSC-Bold.ttf"
FONT_MED = SERIES / "assets" / "fonts" / "NotoSansSC-Medium.ttf"
FONT_REG = SERIES / "assets" / "fonts" / "NotoSansSC-Regular.ttf"
AUDIO_DIR = ROOT / "audio"
STILL_DIR = ROOT / "stills"
OUT_MP4 = ROOT / "mini-inference-ep01.mp4"
COVER_PATH = ROOT / "cover-ep01.png"
SRT_PATH = ROOT / "subtitles.srt"
NARRATION_PATH = ROOT / "narration.md"
AVATAR_PATH = ROOT / "avatar" / "avatar-2d.png"
SERIES_NAME = "Mini 模型推理课"
EPISODE_TITLE = "从 Python 到第一次模型推理"

W, H = 1080, 1920
FPS = 30
SR = 48000

CARD_BOX = (64, 348, 1016, 1316)
CARD_W = CARD_BOX[2] - CARD_BOX[0]
CARD_H = CARD_BOX[3] - CARD_BOX[1]
RADIUS = 44

BG_TOP = (250, 245, 233)
BG_BOT = (236, 242, 221)
CARD = (255, 252, 248)
INK = (44, 51, 44)
TITLE = (61, 88, 45)
MUTED = (116, 110, 100)
ACCENT = (214, 122, 61)
BROWN = (138, 86, 54)
SAGE = (232, 239, 220)
SAGE_DEEP = (214, 226, 196)
PEACH = (248, 232, 214)
PEACH_DEEP = (239, 214, 186)
BLUE = (214, 228, 238)
LINE = (226, 218, 204)
WHITE = (255, 252, 248)

VOICE = "zh-CN-XiaoxiaoNeural"
VOICE_RATE = "-3%"


def cue(scene, title, capsule, say, show=None, tag="示意"):
    return {
        "scene": scene,
        "title": title,
        "capsule": capsule,
        "say": say,
        "show": show or say,
        "tag": tag,
    }


CUES = [
    cue("hook", EPISODE_TITLE, "一次只长一个 token", "你会写 Python。这集我们走到第一次模型推理。"),
    cue("hook", EPISODE_TITLE, "一次只长一个 token", "模型不是一口吐出整段话，而是一次只挑下一个 token。"),
    cue("model", "只用这一句", "同一句贯穿全片", "今天只请一个小模型出场。", tag="公开模型"),
    cue(
        "model",
        "只用这一句",
        "同一句贯穿全片",
        "Qwen 二点五，零点五 B，Instruct。",
        "Qwen2.5-0.5B-Instruct。",
        tag="公开模型",
    ),
    cue(
        "model",
        "只用这一句",
        "同一句贯穿全片",
        "输入只有一句：什么是 token？后面都用它。",
        "输入只有一句：「什么是 token？」后面都用它。",
        tag="公开模型",
    ),
    cue("loop", "整条推理环", "生成是一个循环", "文字变成编号，编号排成张量。"),
    cue("loop", "整条推理环", "生成是一个循环", "模型选出下一个 token，接回去，再选。"),
    cue("loop", "整条推理环", "生成是一个循环", "最后只把新编号解码成文字。"),
    cue("tokens", "真实切分", "一个 token 可以含多个字", "token 不是固定一个汉字，也不是一个单词。", tag="分词器核对"),
    cue(
        "tokens",
        "真实切分",
        "一个 token 可以含多个字",
        "「什么是」三个字，被切成了同一个 token。",
        "「什么是」三个字，是同一个 token。",
        tag="分词器核对",
    ),
    cue(
        "tokens",
        "真实切分",
        "一个 token 可以含多个字",
        "中间这块还带着一个空格。编号是分词器给出的。",
        "中间这块带着空格。编号来自分词器。",
        tag="分词器核对",
    ),
    cue("template", "套上对话模板", "默认会加上系统提示", "指令模型看到的，通常不止这三块。", tag="已核对"),
    cue(
        "template",
        "套上对话模板",
        "默认会加上系统提示",
        "apply chat template 会加上系统提示和角色标记。",
        "apply_chat_template 会加上系统提示和角色标记。",
        tag="已核对",
    ),
    cue(
        "template",
        "套上对话模板",
        "默认会加上系统提示",
        "核对后，送进模型的是三十二个 token。形状是一乘三十二。",
        "核对后共 32 个 token，形状是 [1, 32]。",
        tag="已核对",
    ),
    cue("code", "加载并进入推理", "先标明现在是推理", "AutoTokenizer 加载分词器，AutoModel 加载因果语言模型。", "AutoTokenizer 与 AutoModelForCausalLM。", tag="代码"),
    cue(
        "code",
        "加载并进入推理",
        "先标明现在是推理",
        "然后 model 点 eval，再放进 torch 的 inference mode。",
        "然后 model.eval()，放进 torch.inference_mode()。",
        tag="代码",
    ),
    cue("gen", "循环选出下一个", "一次只追加一个", "generate 看当前序列，选出一个，接到末尾。", tag="示意"),
    cue(
        "gen",
        "循环选出下一个",
        "一次只追加一个",
        "max new tokens 是最多再长几个，不是一定要写满。",
        "max_new_tokens 是上限，不一定写满。",
        tag="示意",
    ),
    cue("decode", "只解码新增部分", "回答是示例，未跑权重", "返回序列的前半段，其实是输入本身。", tag="示例"),
    cue("decode", "只解码新增部分", "回答是示例，未跑权重", "解码时切掉前面，只留新 token。", tag="示例"),
    cue("decode", "只解码新增部分", "回答是示例，未跑权重", "画面上的答句是示例。这次没有下载权重，也没有生成。", tag="示例"),
    cue("params", "生成参数", "温度只在抽样时生效", "这个模型的默认配置是抽样。贪心要显式关掉 do sample。", "默认配置是抽样。贪心要显式关掉 do_sample。", tag="示意"),
    cue("params", "生成参数", "温度只在抽样时生效", "关掉之后，每次走当前最高分，temperature 不参与。", "关掉之后走当前最高分，temperature 不参与。", tag="示意"),
    cue(
        "params",
        "生成参数",
        "温度只在抽样时生效",
        "打开抽样，温度低更稳，温度高更散。top p 收窄候选。",
        "打开抽样后，温度低更稳，高更散。top_p 收窄候选。",
        tag="示意",
    ),
    cue("params", "生成参数", "温度只在抽样时生效", "这些旋钮只改变倾向，不保证答对。", tag="示意"),
    cue("memory", "显存分成三块", "理论权重不等于实际显存", "大致是权重、KV Cache，以及临时张量和框架开销。", tag="理论估算"),
    cue(
        "memory",
        "显存分成三块",
        "理论权重不等于实际显存",
        "按五亿参数，FP32 理论权重约二 GB，十六位约一 GB。",
        "按 0.5B 参数，FP32 约 2.0 GB，16 位约 1.0 GB。",
        tag="理论估算",
    ),
    cue(
        "memory",
        "显存分成三块",
        "理论权重不等于实际显存",
        "GB 按十亿字节。这只算权重，不是整张显卡的占用。",
        "十进制 GB。只算权重，不是整张显卡的占用。",
        tag="理论估算",
    ),
    cue(
        "memory",
        "显存分成三块",
        "理论权重不等于实际显存",
        "用公开结构逐层相加，大约四亿九千四百万参数，十六位约零点九九 GB。",
        "结构加总约 4.94 亿参数，16 位约 0.99 GB。同样是理论值。",
        tag="理论估算",
    ),
    cue(
        "memory",
        "显存分成三块",
        "理论权重不等于实际显存",
        "按这个结构，十六位、一条序列，每增加一个 token，缓存大约增加一万二千三百字节。",
        "16 位、一条序列，每增加 1 个 token，KV 约增 12.3 KB。",
        tag="理论估算",
    ),
    cue(
        "memory",
        "显存分成三块",
        "理论权重不等于实际显存",
        "模型变大，权重上涨。上下文更长，或一次算更多条，另外两块也会涨。",
        "模型变大，权重上涨。上下文或并发变多，后两块也涨。",
        tag="理论估算",
    ),
    cue("precision", "同是 16 位", "存储一样，本事不一样", "FP16 和 BF16 都是十六位。一个参数大约两字节。", "FP16 和 BF16 都是 16 位。一个参数大约 2 字节。", tag="结构"),
    cue(
        "precision",
        "同是 16 位",
        "存储一样，本事不一样",
        "FP16 是一位符号、五位指数、十位尾数。尾数多，小数更细。",
        "FP16 是 1 位符号、5 位指数、10 位尾数。小数更细。",
        tag="结构",
    ),
    cue(
        "precision",
        "同是 16 位",
        "存储一样，本事不一样",
        "BF16 是一位符号、八位指数、七位尾数。指数宽，范围更大。",
        "BF16 是 1 位符号、8 位指数、7 位尾数。范围更大。",
        tag="结构",
    ),
    cue("precision", "同是 16 位", "存储一样，本事不一样", "它并不更省显存，也不总是更精确。硬件要支持，模型也得配得上。", tag="结构"),
    cue("close", "这条环就够", "完整示例在附件里", "今天只讲推理，不展开训练。", tag=""),
    cue("close", "这条环就够", "完整示例在附件里", "记住：切分，张量，下一个 token，只解码新增的部分。", tag=""),
]

SCENE_TAIL = {
    "hook": 0.55,
    "model": 0.45,
    "loop": 0.4,
    "tokens": 0.75,
    "template": 0.6,
    "code": 0.4,
    "gen": 0.45,
    "decode": 0.55,
    "params": 0.5,
    "memory": 0.75,
    "precision": 0.65,
    "close": 0.9,
}

DOTS = [
    (120, 180, 34, 0.2, (244, 214, 214)),
    (860, 260, 22, 1.4, (206, 224, 206)),
    (960, 640, 40, 2.2, (244, 224, 196)),
    (80, 860, 26, 0.8, (206, 222, 234)),
    (980, 1100, 30, 3.1, (242, 210, 210)),
    (150, 1280, 18, 2.6, (214, 228, 196)),
    (900, 1500, 36, 1.1, (232, 220, 240)),
    (220, 1680, 24, 4.0, (244, 226, 200)),
    (700, 120, 16, 5.2, (210, 226, 216)),
    (40, 480, 20, 3.6, (238, 214, 206)),
    (520, 1760, 28, 2.8, (214, 226, 236)),
    (760, 820, 14, 0.4, (236, 220, 196)),
]


def load_fonts():
    return {
        "title": ImageFont.truetype(str(FONT_BOLD), 78),
        "eyebrow": ImageFont.truetype(str(FONT_MED), 28),
        "tag": ImageFont.truetype(str(FONT_MED), 24),
        "capsule": ImageFont.truetype(str(FONT_MED), 32),
        "sub": ImageFont.truetype(str(FONT_REG), 34),
        "h": ImageFont.truetype(str(FONT_BOLD), 46),
        "body": ImageFont.truetype(str(FONT_MED), 34),
        "small": ImageFont.truetype(str(FONT_REG), 26),
        "tiny": ImageFont.truetype(str(FONT_REG), 22),
        "chip": ImageFont.truetype(str(FONT_BOLD), 36),
        "id": ImageFont.truetype(str(FONT_MED), 24),
        "big": ImageFont.truetype(str(FONT_BOLD), 64),
        "num": ImageFont.truetype(str(FONT_BOLD), 52),
    }


FONTS = None
WARNINGS = []


def fonts():
    global FONTS
    if FONTS is None:
        FONTS = load_fonts()
    return FONTS


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def ease_out_back(u):
    u = max(0.0, min(1.0, u))
    c1 = 1.18
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def appear(age, delay=0.0, duration=0.42):
    t = age - delay
    if t <= 0:
        return 0.0, 26.0
    u = min(1.0, t / duration)
    eased = ease_out_back(u)
    alpha = min(1.0, t / 0.18)
    dy = (1 - eased) * 22
    return alpha, dy


def text_width(font, text):
    box = font.getbbox(text)
    return box[2] - box[0]


def wrap_text(text, font, max_w):
    lines = []
    current = ""
    for char in text:
        trial = current + char
        if text_width(font, trial) <= max_w or not current:
            current = trial
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def center_text(draw, box, text, font, fill, anchor="mm"):
    x0, y0, x1, y1 = box
    width = text_width(font, text)
    if width > (x1 - x0) - 6:
        WARNINGS.append(f"overflow {text!r} {width}>{x1 - x0}")
    draw.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font, fill=fill, anchor=anchor)


def draw_lines(draw, xy, lines, font, fill, gap, align="center", max_w=None):
    x, y = xy
    for line in lines:
        width = text_width(font, line)
        height = font.getbbox(line)[3] - font.getbbox(line)[1]
        if max_w and width > max_w + 2:
            WARNINGS.append(f"line overflow {line!r}")
        left = x - width / 2 if align == "center" else x
        draw.text((left, y), line, font=font, fill=fill, anchor="lt")
        y += height + gap
    return y


def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def load_report():
    report = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    pieces = report["bare_pieces"]
    if [piece["text"] for piece in pieces] != ["什么是", " token", "？"]:
        raise SystemExit(f"分词结果和画面不一致: {pieces}")
    if report["prompt_count"] != 32:
        raise SystemExit("模板 token 数不是 32")
    if report["round_half_billion"]["fp32_gb"] != 2.0:
        raise SystemExit("FP32 理论值不是 2.0")
    if report["round_half_billion"]["fp16_or_bf16_gb"] != 1.0:
        raise SystemExit("16 位理论值不是 1.0")
    if report["kv_bytes_per_token_fp16"] != 12288:
        raise SystemExit("KV 字节数变了")
    return report


GRADIENT = None


def background(t):
    global GRADIENT
    if GRADIENT is None:
        column = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        top = np.array(BG_TOP, dtype=np.float32)
        bot = np.array(BG_BOT, dtype=np.float32)
        gradient = (top * (1 - column) + bot * column).astype(np.uint8)
        GRADIENT = Image.fromarray(np.broadcast_to(gradient, (H, W, 3)).copy(), "RGB").convert("RGBA")
    image = GRADIENT.copy()
    draw = ImageDraw.Draw(image)
    for index, (x, y, radius, phase, color) in enumerate(DOTS):
        dx = 16 * math.sin(t * 0.22 + phase)
        dy = (y + t * 8 + index * 40) % (H + 120) - 60
        draw.ellipse((x + dx - radius, dy - radius, x + dx + radius, dy + radius), fill=color + (255,))
    return image


def shadow_image():
    pad = 80
    image = Image.new("RGBA", (CARD_W + pad * 2, CARD_H + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (pad, pad + 14, pad + CARD_W, pad + 14 + CARD_H),
        RADIUS,
        fill=(120, 96, 60, 42),
    )
    return image.filter(ImageFilter.GaussianBlur(20)), pad


SHADOW = None


def get_shadow():
    global SHADOW
    if SHADOW is None:
        SHADOW = shadow_image()
    return SHADOW


def blit_card(base, card, scene_age):
    scale = ease_out_back(min(1.0, scene_age / 0.48))
    alpha = min(1.0, max(0.0, scene_age / 0.16))
    shadow, pad = get_shadow()
    if abs(scale - 1) > 0.01:
        card_draw = card.resize((max(1, int(CARD_W * scale)), max(1, int(CARD_H * scale))), Image.Resampling.LANCZOS)
        shadow_draw = shadow.resize(
            (max(1, int(shadow.width * scale)), max(1, int(shadow.height * scale))),
            Image.Resampling.BILINEAR,
        )
    else:
        card_draw = card
        shadow_draw = shadow
    if alpha < 1:
        card_draw = card_draw.copy()
        band = card_draw.split()[-1].point(lambda value: int(value * alpha))
        card_draw.putalpha(band)
    cx = (CARD_BOX[0] + CARD_BOX[2]) / 2
    cy = (CARD_BOX[1] + CARD_BOX[3]) / 2
    sx = int(cx - shadow_draw.width / 2)
    sy = int(cy - shadow_draw.height / 2 + 8)
    base.alpha_composite(shadow_draw, (sx, sy))
    base.alpha_composite(card_draw, (int(cx - card_draw.width / 2), int(cy - card_draw.height / 2)))


def new_card():
    image = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    rounded(draw, (0, 0, CARD_W - 1, CARD_H - 1), RADIUS, CARD)
    return image, draw


def paint_header(base, title, tag, scene_age):
    draw = ImageDraw.Draw(base)
    alpha, dy = appear(scene_age, 0.0, 0.36)
    fill = TITLE + (int(255 * alpha),)
    muted = MUTED + (int(255 * alpha),)
    draw.text((76, 92 + dy), f"{SERIES_NAME}  ·  EP1", font=fonts()["eyebrow"], fill=muted)
    title_font = fonts()["title"]
    lines = wrap_text(title, title_font, 900)
    if len(lines) > 1:
        title_font = ImageFont.truetype(str(FONT_BOLD), 58)
        lines = wrap_text(title, title_font, 920)
    if len(lines) > 2:
        WARNINGS.append(f"title {title}")
    y = 148 + dy
    for line in lines:
        width = text_width(title_font, line)
        draw.text(((W - width) / 2, y), line, font=title_font, fill=fill)
        y += 74
    if tag:
        label = tag
        width = text_width(fonts()["tag"], label) + 36
        box = (W - 76 - width, 88 + dy, W - 76, 132 + dy)
        rounded(draw, box, 18, SAGE + (int(255 * alpha),))
        center_text(draw, box, label, fonts()["tag"], TITLE + (int(255 * alpha),))


def paint_capsule(base, text, scene_age):
    draw = ImageDraw.Draw(base)
    alpha, dy = appear(max(0, scene_age - 0.08), 0.0, 0.34)
    font = fonts()["capsule"]
    width = min(700, text_width(font, text) + 56)
    if text_width(font, text) > 680:
        WARNINGS.append(f"capsule {text}")
    left_limit, right_limit = 318, W - 64
    x0 = left_limit + max(0, (right_limit - left_limit - width) / 2)
    y0 = 1344 + dy
    box = (x0, y0, x0 + width, y0 + 72)
    rounded(draw, box, 36, WHITE + (int(255 * alpha),), PEACH_DEEP + (int(255 * alpha),), 3)
    center_text(draw, box, text, font, BROWN + (int(255 * alpha),))


def paint_subtitle(base, text, alpha=1.0):
    draw = ImageDraw.Draw(base)
    font = fonts()["sub"]
    lines = wrap_text(text, font, 900)
    if len(lines) > 2:
        font = ImageFont.truetype(str(FONT_REG), 30)
        lines = wrap_text(text, font, 920)
    if len(lines) > 2:
        WARNINGS.append(f"subtitle {text}")
    line_h = 44
    block_h = 24 + line_h * max(2, len(lines))
    y0 = 1708
    box = (56, y0, W - 56, min(H - 36, y0 + block_h))
    fill = (255, 252, 248, int(235 * alpha))
    rounded(draw, box, 28, fill)
    y = y0 + 14
    for line in lines:
        width = text_width(font, line)
        draw.text(((W - width) / 2, y), line, font=font, fill=INK + (int(255 * alpha),))
        y += line_h


def active_fill(on, age):
    if not on:
        return SAGE, INK, MUTED
    shift = min(1.0, max(0.0, age) / 0.28)
    return lerp(SAGE, PEACH, shift), lerp(INK, (120, 62, 28), shift), lerp(MUTED, ACCENT, shift)


def draw_hook(draw, step, age):
    font = fonts()
    alpha, dy = appear(age if step == 0 else 1, 0)
    ink = INK + (int(255 * alpha),)
    draw.text((70, 70 + dy), "不是这样", font=font["body"], fill=MUTED + (int(220 * alpha),))
    bar_fill = lerp(SAGE, (236, 232, 224), 0.4 if step else 0)
    rounded(draw, (70, 130 + dy, CARD_W - 70, 250 + dy), 28, bar_fill + (255,))
    center_text(draw, (70, 130 + dy, CARD_W - 70, 250 + dy), "整段回答一次出现", font["h"], MUTED)
    draw.text((70, 330), "实际是这样", font=font["body"], fill=TITLE)
    labels = ["已有", "已有", "下一个", "再下一个"]
    slot_w, slot_h, gap = 180, 168, 22
    total = 4 * slot_w + 3 * gap
    left = (CARD_W - total) / 2
    top = 410
    for index, label in enumerate(labels):
        delay = 0.08 * index
        local_age = age if step >= 1 else -1
        pop, offset = appear(local_age, delay)
        if step < 1 and index > 0:
            pop = 0.35
            offset = 0
        if step < 1 and index == 0:
            pop = 0.35
        box = (left + index * (slot_w + gap), top + offset, left + index * (slot_w + gap) + slot_w, top + slot_h + offset)
        on = step >= 1 and index <= min(2, int(age / 0.16))
        if step >= 1 and index == 2:
            on = True
        fill, text_color, _ = active_fill(on and index == 2, age)
        if index < 2 and step >= 1:
            fill = SAGE_DEEP
            text_color = TITLE
        if index == 3:
            fill = (248, 246, 240)
            text_color = MUTED
        rounded(draw, box, 28, fill + (int(255 * max(pop, 0.35)),), LINE, 3)
        center_text(draw, box, label, font["body"], text_color)
    draw.text((70, 650), "空位是下一步。示意，不是真实切分。", font=font["small"], fill=MUTED)


def draw_model(draw, step, age, report):
    font = fonts()
    alpha, dy = appear(age, 0)
    rounded(draw, (80, 90 + dy, CARD_W - 80, 250 + dy), 28, SAGE)
    center_text(draw, (80, 90 + dy, CARD_W - 80, 250 + dy), "Qwen2.5-0.5B-Instruct", font["h"], TITLE)
    quote_on = step >= 2
    fill = PEACH if quote_on else (248, 246, 242)
    alpha2, dy2 = appear(age if step >= 1 else age, 0.05)
    rounded(draw, (80, 330 + dy2, CARD_W - 80, 560 + dy2), 32, fill)
    center_text(draw, (100, 360 + dy2, CARD_W - 100, 470 + dy2), "什么是 token？", font["big"], INK if quote_on else MUTED)
    draw.text((100, 500 + dy2), "同一句输入", font=font["small"], fill=BROWN if quote_on else MUTED)
    note = "后面的切分、模板、参数，都回到这一句。"
    if step >= 2:
        draw.text((80, 640), note, font=font["body"], fill=INK)
    else:
        draw.text((80, 640), "先记住模型名。", font=font["body"], fill=MUTED)
    draw.text((80, 760), "不在这里下载权重。", font=font["small"], fill=MUTED)


def draw_loop(draw, step, age):
    font = fonts()
    steps = ["文字", "token / 编号", "PyTorch 张量", "模型", "下一个 token", "解码新词"]
    top = 28
    for index, label in enumerate(steps):
        on = index <= step + 1 or (step >= 2 and index <= 5)
        # light progressively: cue 0 shows 0-2, cue 1 shows 3-4, cue 2 shows 5
        if step == 0:
            on = index <= 2
        elif step == 1:
            on = index <= 4
        else:
            on = True
        hot = (step == 0 and index == 2) or (step == 1 and index == 4) or (step >= 2 and index == 5)
        y = top + index * 132
        alpha, dy = appear(age, 0.05 * index if on else 9)
        if not on:
            alpha = 0.28
            dy = 0
        fill = PEACH if hot else (SAGE if on else (246, 243, 236))
        rounded(draw, (90, y + dy, CARD_W - 90, y + 112 + dy), 26, fill + (int(255 * max(alpha, 0.28)),))
        center_text(draw, (90, y + dy, CARD_W - 90, y + 112 + dy), label, font["h"], TITLE if on else MUTED)


def token_chip(draw, box, title, subtitle, hot, alpha=1.0):
    fill = PEACH if hot else SAGE
    color = (120, 62, 28) if hot else TITLE
    rounded(draw, box, 26, fill + (int(255 * alpha),), ACCENT if hot else LINE, 3)
    x0, y0, x1, y1 = box
    center_text(draw, (x0, y0 + 8, x1, y0 + 86), title, fonts()["chip"], color)
    center_text(draw, (x0, y0 + 86, x1, y1 - 8), subtitle, fonts()["id"], MUTED)


def draw_tokens(draw, step, age, report):
    font = fonts()
    pieces = report["bare_pieces"]
    draw.text((70, 60), "正文 · 还没套对话模板", font=font["small"], fill=MUTED)
    rounded(draw, (70, 110, CARD_W - 70, 250), 28, (248, 246, 242))
    center_text(draw, (70, 110, CARD_W - 70, 250), USER_TEXT, font["big"], INK)
    specs = [
        ("什么是", f"id {pieces[0]['id']}", "三个汉字"),
        ("空格 token", f"id {pieces[1]['id']}", "含前导空格"),
        ("？", f"id {pieces[2]['id']}", "单独一个"),
    ]
    chip_w, chip_h, gap = 250, 168, 24
    total = 3 * chip_w + 2 * gap
    left = (CARD_W - total) / 2
    top = 330
    for index, (title, subtitle, note) in enumerate(specs):
        shown = step >= index
        alpha, dy = appear(age if shown else -1, 0.0)
        if step > index:
            alpha, dy = 1.0, 0.0
        box = (left + index * (chip_w + gap), top + dy, left + index * (chip_w + gap) + chip_w, top + chip_h + dy)
        if shown or step > index:
            token_chip(draw, box, title, subtitle, hot=(step == index), alpha=max(alpha, 0.01))
            if step == index or step > index:
                draw.text((box[0], box[3] + 16), note, font=font["tiny"], fill=ACCENT if step == index else MUTED)
        else:
            rounded(draw, box, 26, (248, 246, 242), LINE, 2)
    draw.text((70, 640), "「什么是」不是三个 token。token 也不是一个英文单词。", font=font["body"], fill=INK)
    draw.text((70, 720), "编号用 Qwen2.5-0.5B-Instruct 的 tokenizer 跑过。", font=font["small"], fill=MUTED)
    draw.text((70, 770), "芯片的位置是排版，切分和 id 不是示意。", font=font["small"], fill=MUTED)


def draw_template(draw, step, age, report):
    font = fonts()
    rows = [
        ("系统", "默认系统提示", "21 个 token", "英文提示收成一块，示意"),
        ("user", "什么是    空格 token    ？", "正文仍是那 3 个", "106582 · 3950 · 11319"),
        ("assistant", "等待生成", "3 个标记", "<|im_start|> assistant"),
    ]
    for index, (role, title, meta, foot) in enumerate(rows):
        visible = step >= index
        alpha, dy = appear(age if visible else -1, 0)
        if step > index:
            alpha, dy = 1, 0
        y = 36 + index * 270 + dy
        hot = step == index
        fill = PEACH if hot else (SAGE if visible else (248, 246, 242))
        rounded(draw, (60, y, CARD_W - 60, y + 230), 30, fill + (int(255 * max(alpha, 0.2)),))
        draw.text((92, y + 28), role, font=font["tiny"], fill=ACCENT if hot else MUTED)
        draw.text((92, y + 68), title, font=font["h"], fill=TITLE if visible else MUTED)
        draw.text((92, y + 150), meta, font=font["body"], fill=INK if visible else MUTED)
        draw.text((92, y + 186), foot, font=font["small"], fill=MUTED)
    if step >= 2:
        draw.text((70, 880), "合计 32。input_ids 形状 [1, 32]。一批，一句。", font=font["body"], fill=INK)


def draw_code(draw, step, age):
    font = fonts()
    lines = [
        "tokenizer = AutoTokenizer.from_pretrained(model_id)",
        "model = AutoModelForCausalLM.from_pretrained(",
        "    model_id, dtype=dtype)",
        "model.eval()",
        "with torch.inference_mode():",
        "    model.generate(...)",
    ]
    groups = [0, 0, 0, 1, 1, 1]
    y = 48
    for index, line in enumerate(lines):
        hot = groups[index] == step
        fill = PEACH if hot else (248, 246, 242)
        alpha, dy = appear(age if hot else 1, 0 if hot else 0)
        box = (48, y + (dy if hot else 0), CARD_W - 48, y + 112 + (dy if hot else 0))
        rounded(draw, box, 22, fill)
        # shrink long lines
        use = font["small"]
        if text_width(use, line) > CARD_W - 150:
            WARNINGS.append(f"code {line}")
        draw.text((78, box[1] + 38), line, font=use, fill=INK if hot else MUTED)
        y += 132
    note = "dtype 用 FP16、BF16 或 CPU 上的 FP32。" if step == 0 else "eval 标明推理。inference_mode 里不做梯度。"
    draw.text((70, 880), note, font=font["small"], fill=MUTED)


def draw_gen(draw, step, age):
    font = fonts()
    draw.text((70, 70), "已有序列", font=font["small"], fill=MUTED)
    base_labels = ["什么是", "token", "？"]
    extra = ["新 1", "新 2"] if step == 0 else ["…", "停或满"]
    labels = base_labels + extra
    chip_w, gap = 150, 16
    left = 50
    top = 150
    for index, label in enumerate(labels):
        born = 0 if index < 3 else (0.05 if step == 0 else 0.1)
        alpha, dy = appear(age, born + index * 0.04)
        if index < 3:
            alpha, dy = 1, 0
        box = (left + index * (chip_w + gap), top + dy, left + index * (chip_w + gap) + chip_w, top + 120 + dy)
        hot = index >= 3
        rounded(draw, box, 22, (PEACH if hot else SAGE) + (int(255 * alpha),))
        center_text(draw, box, label, font["small"], ACCENT if hot else TITLE)
    if step == 0:
        rounded(draw, (70, 360, CARD_W - 70, 560), 28, SAGE)
        center_text(draw, (70, 360, CARD_W - 70, 560), "选一个，接到末尾", font["h"], TITLE)
        draw.text((90, 620), "图上的「新 1」「新 2」是示意，不是模型输出。", font=font["small"], fill=MUTED)
    else:
        rounded(draw, (70, 360, CARD_W - 70, 620), 28, PEACH)
        center_text(draw, (70, 380, CARD_W - 70, 500), "max_new_tokens = 32", font["h"], (120, 62, 28))
        center_text(draw, (90, 500, CARD_W - 90, 600), "最多再长 32 个，可以更早结束", font["body"], INK)
        draw.text((90, 680), "它是上限，不是必须写满的配额。", font=font["small"], fill=MUTED)
    draw.text((70, 820), "循环直到遇到结束符，或新 token 达到上限。", font=font["body"], fill=INK)


def draw_decode(draw, step, age):
    font = fonts()
    draw.text((70, 60), "generate 返回的整段编号", font=font["small"], fill=MUTED)
    left_w = 520 if step == 0 else 430
    rounded(draw, (60, 120, 60 + left_w, 280), 26, SAGE)
    center_text(draw, (60, 120, 60 + left_w, 280), "输入  32", font["h"], TITLE)
    right = (70 + left_w, 120, CARD_W - 60, 280)
    hot = step >= 1
    rounded(draw, right, 26, PEACH if hot else (248, 246, 242), ACCENT if hot else LINE, 3)
    center_text(draw, right, "新增", font["h"], ACCENT if hot else MUTED)
    if step >= 1:
        draw.text((70, 320), "只把右边送进 decode。", font=font["body"], fill=INK)
    else:
        draw.text((70, 320), "左边是问题，已经在输入里。", font=font["body"], fill=MUTED)
    rounded(draw, (60, 430, CARD_W - 60, 820), 30, (255, 250, 244), ACCENT, 3)
    draw.text((90, 460), "示例回答", font=font["tiny"], fill=ACCENT)
    center_text(draw, (90, 520, CARD_W - 90, 680), "token 是切出来的小块。", font["h"], INK)
    rounded(draw, (90, 700, 430, 780), 18, PEACH)
    center_text(draw, (90, 700, 430, 780), "未运行权重", font["body"], BROWN)
    if step >= 2:
        draw.text((90, 860), "这句不是模型生成的。附件里的脚本可以真的跑。", font=font["small"], fill=MUTED)
    else:
        draw.text((90, 860), "制作这支片子时，没有下载权重。", font=font["small"], fill=MUTED)


def mini_bars(draw, box, heights, pick):
    x0, y0, x1, y1 = box
    count = len(heights)
    gap = 18
    width = (x1 - x0 - gap * (count - 1)) / count
    for index, height in enumerate(heights):
        bar_h = 8 + height * (y1 - y0 - 16)
        bx0 = x0 + index * (width + gap)
        rounded(draw, (bx0, y1 - bar_h, bx0 + width, y1), 10, ACCENT if index == pick else SAGE_DEEP)


def draw_params(draw, step, age):
    font = fonts()
    banner = PEACH if step == 0 else SAGE
    rounded(draw, (60, 40, CARD_W - 60, 150), 24, banner)
    center_text(draw, (60, 40, CARD_W - 60, 150), "默认 do_sample = true", font["body"], TITLE)
    rows = [
        (1, "max_new_tokens", "32", "长度上限"),
        (2, "do_sample = false", "贪心", "temperature 不参与"),
        (3, "do_sample = true", "0.7 / 0.8", "temperature / top_p"),
    ]
    for index, (need, name, value, note) in enumerate(rows):
        hot = step == need or (step == 0 and False)
        # step 0 highlights banner; 1 highlights max? Wait cues:
        # 0 default sampling, 1 greedy, 2 sampling params, 3 tendency
        # Remap: step 0 banner, step 1 row greedy which is rows[1], also show max always
        y = 170 + index * 210
        if step == 1:
            hot = index == 1
        elif step == 2:
            hot = index == 2
        elif step >= 3:
            hot = True
        else:
            hot = index == 0
        fill = PEACH if hot else (248, 246, 242)
        rounded(draw, (60, y, CARD_W - 60, y + 188), 26, fill, ACCENT if hot else None, 3)
        draw.text((88, y + 28), name, font=font["body"], fill=INK)
        draw.text((88, y + 90), value, font=font["h"], fill=ACCENT if hot else TITLE)
        draw.text((88, y + 150), note, font=font["small"], fill=MUTED)
    if step >= 3:
        draw.text((70, 860), "低温度更集中，高温度更分散。示意，不是实测分布。", font=font["small"], fill=MUTED)


def memory_column(draw, box, title, lines, hot):
    fill = PEACH if hot else SAGE
    rounded(draw, box, 28, fill, ACCENT if hot else None, 3)
    x0, y0, x1, y1 = box
    draw.text((x0 + 24, y0 + 28), title, font=fonts()["body"], fill=TITLE)
    y = y0 + 100
    for line in lines:
        draw.text((x0 + 24, y), line, font=fonts()["small"], fill=INK)
        y += 42


def draw_memory(draw, step, age, report):
    font = fonts()
    gap = 22
    width = (CARD_W - 80 - gap * 2) / 3
    specs = [
        ("权重", ["理论体积", "FP32  2.0 GB", "16位  1.0 GB", "按 0.5B"]),
        ("KV Cache", ["随上下文", "随并发变", "16位每 token", "约 12.3 KB"]),
        ("临时张量", ["激活、框架", "没有固定 GB", "随计算波动", "示意"]),
    ]
    hot = [False, False, False]
    if step <= 2:
        hot = [step == 1, False, False]
    elif step == 3:
        hot = [True, False, False]
    elif step == 4:
        hot = [False, True, False]
    else:
        hot = [True, True, True]
    for index, ((title, lines), is_hot) in enumerate(zip(specs, hot)):
        x = 40 + index * (width + gap)
        memory_column(draw, (x, 50, x + width, 470), title, lines, is_hot)
    rounded(draw, (50, 520, CARD_W - 50, 860), 28, (255, 250, 244))
    messages = [
        "三块一起，才是运行时的占用。",
        "2.0 GB 和 1.0 GB 只按 5 亿参数去乘。",
        "1 GB = 10⁹ 字节。不是 nvidia-smi。",
        "结构加总 494,032,768 参数。",
        "16 位约 0.988 GB，画面写约 0.99 GB。",
        "高度不按同一把尺子。不能拿来比大小。",
    ]
    text = messages[min(step, len(messages) - 1)]
    center_text(draw, (70, 540, CARD_W - 70, 680), text, font["body"], INK)
    draw.text((80, 720), "未加载权重，也没有测量显卡。", font=font["small"], fill=MUTED)
    if step >= 4:
        draw.text((80, 780), "12.3 KB = 12288 字节 ÷ 1000。一条序列。", font=font["small"], fill=MUTED)
    if step >= 5:
        draw.text((80, 820), "模型更大，权重上涨。上下文或并发变多，后两块也涨。", font=font["small"], fill=TITLE)


def bit_row(draw, y, title, groups, hot_group, age):
    font = fonts()
    draw.text((50, y), title, font=font["body"], fill=TITLE)
    colors = [(226, 160, 106), (197, 214, 168), (169, 199, 228)]
    names = ["符号", "指数", "尾数"]
    cells = []
    for group_index, count in enumerate(groups):
        cells.extend([group_index] * count)
    cell_w, gap = 46, 6
    total = 16 * cell_w + 15 * gap
    left = (CARD_W - total) / 2
    top = y + 64
    for index, group_index in enumerate(cells):
        alpha, dy = appear(age, index * 0.012)
        if hot_group is not None and group_index != hot_group:
            alpha = min(alpha, 0.45)
        fill = colors[group_index]
        box = (left + index * (cell_w + gap), top + dy, left + index * (cell_w + gap) + cell_w, top + 64 + dy)
        rounded(draw, box, 10, fill + (int(255 * alpha),))
    # group captions
    cursor = 0
    for group_index, count in enumerate(groups):
        span_left = left + cursor * (cell_w + gap)
        span_right = left + (cursor + count) * (cell_w + gap) - gap
        caption = f"{names[group_index]} {count}"
        center_text(draw, (span_left, top + 78, span_right, top + 120), caption, font["tiny"], INK if hot_group in (None, group_index) else MUTED)
        cursor += count


def draw_precision(draw, step, age):
    font = fonts()
    hot_fp = 2 if step == 1 else None
    hot_bf = 1 if step == 2 else None
    bit_row(draw, 40, "FP16", (1, 5, 10), hot_fp, age if step <= 1 else 1.0)
    bit_row(draw, 280, "BF16", (1, 8, 7), hot_bf, age if step >= 2 else 1.0)
    draw.text((60, 560), "两位格式都是 16 bit，权重都按约 2 字节存。", font=font["body"], fill=INK)
    myths = [("BF16 更省显存", step >= 3), ("BF16 总是更精确", step >= 3)]
    for index, (text, strike) in enumerate(myths):
        x = 60 + index * 450
        y = 680
        rounded(draw, (x, y, x + 420, y + 110), 22, (248, 246, 242))
        center_text(draw, (x, y, x + 420, y + 110), text, font["small"], MUTED if strike else INK)
        if strike:
            draw.line((x + 28, y + 55, x + 392, y + 55), fill=ACCENT, width=4)
    if step >= 3:
        draw.text((60, 840), "存储相同。一个范围更大，一个小数更细。", font=font["body"], fill=TITLE)
        draw.text((60, 900), "要看硬件支不支持，也要看权重是不是这个格式。", font=font["small"], fill=MUTED)
    elif step == 1:
        draw.text((60, 840), "尾数位更多，能把小数分得更细。", font=font["body"], fill=TITLE)
    elif step == 2:
        draw.text((60, 840), "指数位和 FP32 一样宽，数值范围更大。", font=font["body"], fill=TITLE)
    else:
        draw.text((60, 840), "省的是同一项：每个参数少一半字节。", font=font["body"], fill=TITLE)


def draw_close(draw, step, age):
    font = fonts()
    items = ["切分", "张量", "下一个", "只解码新增"]
    positions = [(80, 120), (500, 120), (80, 420), (500, 420)]
    for index, (label, (x, y)) in enumerate(zip(items, positions)):
        alpha, dy = appear(age, index * 0.08)
        if step == 0 and index > 1:
            alpha = 0.35
        hot = step >= 1 and index == 3 or (step >= 1 and index <= 3)
        rounded(draw, (x, y + dy, x + 370, y + 220 + dy), 32, PEACH if index == 3 and step >= 1 else SAGE)
        center_text(draw, (x, y + dy, x + 370, y + 220 + dy), label, font["h"], TITLE)
    draw.text((80, 720), "按从左到右、从上到下看。示意。", font=font["small"], fill=MUTED)
    if step >= 1:
        draw.text((80, 800), "附件里有同一句的可运行示例。", font=font["body"], fill=INK)
        draw.text((80, 880), "真实占用和回答，以你自己的运行为准。", font=font["small"], fill=MUTED)


USER_TEXT = "什么是 token？"

DRAWERS = {
    "hook": lambda draw, step, age, report: draw_hook(draw, step, age),
    "model": lambda draw, step, age, report: draw_model(draw, step, age, report),
    "loop": lambda draw, step, age, report: draw_loop(draw, step, age),
    "tokens": lambda draw, step, age, report: draw_tokens(draw, step, age, report),
    "template": lambda draw, step, age, report: draw_template(draw, step, age, report),
    "code": lambda draw, step, age, report: draw_code(draw, step, age),
    "gen": lambda draw, step, age, report: draw_gen(draw, step, age),
    "decode": lambda draw, step, age, report: draw_decode(draw, step, age),
    "params": lambda draw, step, age, report: draw_params(draw, step, age),
    "memory": lambda draw, step, age, report: draw_memory(draw, step, age, report),
    "precision": lambda draw, step, age, report: draw_precision(draw, step, age),
    "close": lambda draw, step, age, report: draw_close(draw, step, age),
}


def scene_steps():
    counts = {}
    for item in CUES:
        counts[item["scene"]] = counts.get(item["scene"], 0) + 1
    running = {}
    steps = []
    for item in CUES:
        index = running.get(item["scene"], 0)
        running[item["scene"]] = index + 1
        steps.append(index)
    return steps


STEPS = None


def steps():
    global STEPS
    if STEPS is None:
        STEPS = scene_steps()
    return STEPS


AVATAR_CROP = (410, 16, 940, 600)
MOUTH_CENTER = (666, 438)
EYES = ((574, 364, 38, 34), (710, 340, 40, 30))
AVATAR_BASE = None
AVATAR_SPRITES = {}
AVATAR_READY = {}


def keyed_avatar():
    global AVATAR_BASE
    if AVATAR_BASE is None:
        source = Image.open(AVATAR_PATH).convert("RGB")
        pixels = np.asarray(source).astype(np.float32)
        background_color = np.array([234, 229, 233], dtype=np.float32)
        distance = np.linalg.norm(pixels - background_color, axis=2)
        alpha = np.clip((distance - 14) / 16, 0, 1)
        AVATAR_BASE = Image.fromarray(np.dstack([pixels, alpha * 255]).astype(np.uint8), "RGBA")
    return AVATAR_BASE


def mouth_overlay(level):
    image = keyed_avatar().copy()
    if level < 0.08:
        return image
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = MOUTH_CENTER
    width = 8 + int(18 * level)
    height = 3 + int(5 * level)
    draw.ellipse((cx - width - 2, cy - height - 1, cx + width + 2, cy + height + 2), fill=(214, 150, 154, 255))
    draw.ellipse((cx - width + 2, cy - height + 2, cx + width - 2, cy + height), fill=(120, 66, 72, 255))
    image.alpha_composite(layer)
    return image


def blink_crop(sprite):
    pixels = np.asarray(sprite)
    red, green, blue, alpha = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2], pixels[:, :, 3]
    height, width = alpha.shape
    band = np.zeros_like(alpha, dtype=bool)
    band[int(height * 0.40) : int(height * 0.58), int(width * 0.18) : int(width * 0.78)] = True
    iris = (
        (alpha > 200)
        & (red > 70)
        & (red < 175)
        & (green > 35)
        & (green < 125)
        & (blue < 110)
        & (red > green + 8)
        & band
    )
    ys, xs = np.where(iris)
    if len(xs) < 40:
        return sprite
    image = sprite.copy()
    draw = ImageDraw.Draw(image)
    middle = int(np.median(xs))
    for mask in (xs < middle, xs >= middle):
        if int(mask.sum()) < 20:
            continue
        x0, x1 = int(xs[mask].min()), int(xs[mask].max())
        y0, y1 = int(ys[mask].min()), int(ys[mask].max())
        box = (x0 - 3, y0 - 2, x1 + 3, y1 + 3)
        draw.ellipse(box, fill=(246, 214, 200, 255))
        draw.arc((box[0], box[1], box[2], box[3] + 5), 12, 168, fill=(42, 32, 36, 255), width=3)
    return image


def avatar_sprite(mouth_step, blinked):
    key = (mouth_step, blinked)
    if key not in AVATAR_SPRITES:
        level = (0.0, 0.42, 0.82)[mouth_step]
        crop = mouth_overlay(level).crop(AVATAR_CROP)
        AVATAR_SPRITES[key] = blink_crop(crop) if blinked else crop
    return AVATAR_SPRITES[key]


def blink_amount(t):
    phase = (t + 0.8) % 3.7
    if phase < 0.16:
        return math.sin(phase / 0.16 * math.pi)
    return 0.0


def paste_avatar(base, scene, t, speech):
    mouth_step = 0 if speech < 0.18 else 1 if speech < 0.55 else 2
    # 自动找眼睛会把眼皮画成一块遮罩。口型跟点头已经能跟着说话，眨眼先关掉。
    blinked = False
    emphasis = scene in {"hook", "tokens", "memory", "precision", "close"}
    shrink = scene in {"code", "template", "gen"}
    mode = "emphasis" if emphasis else "shrink" if shrink else "normal"
    cache_key = (mouth_step, blinked, mode)
    frame = AVATAR_READY.get(cache_key)
    if frame is None:
        sprite = avatar_sprite(mouth_step, blinked)
        scale = 1.12 if emphasis else 0.86 if shrink else 1.0
        if emphasis:
            sprite = sprite.rotate(-7, resample=Image.Resampling.BICUBIC, expand=True)
        width = max(1, int(208 * scale))
        height = max(1, int(width * sprite.height / sprite.width))
        frame = sprite.resize((width, height), Image.Resampling.LANCZOS)
        AVATAR_READY[cache_key] = frame
    nod = math.sin(t * 2.5) * (2.2 + 4.2 * speech)
    x = 26 + (12 if emphasis else 0)
    bottom = 1664 + nod + (-10 if emphasis else 0)
    y = int(bottom - frame.height)
    if y < 1336:
        y = 1336
    if y + frame.height > 1692:
        y = 1692 - frame.height
    base.alpha_composite(frame, (int(x), int(y)))


def render_frame(report, cue_index, age, scene_age, global_t, show_sub=True, speech=0.0):
    item = CUES[cue_index]
    base = background(global_t)
    paint_header(base, item["title"], item["tag"], scene_age)
    card, draw = new_card()
    DRAWERS[item["scene"]](draw, steps()[cue_index], age, report)
    blit_card(base, card, scene_age)
    paint_capsule(base, item["capsule"], scene_age)
    if show_sub:
        paint_subtitle(base, item["show"])
    paste_avatar(base, item["scene"], global_t, speech)
    return base.convert("RGB")


def build_timeline(durations):
    entries = []
    clock = 0.5
    previous = None
    scene_start = clock
    for index, (item, duration) in enumerate(zip(CUES, durations)):
        if item["scene"] != previous:
            if previous is not None:
                clock += SCENE_TAIL.get(previous, 0.4)
            scene_start = clock
            previous = item["scene"]
        elif index:
            clock += 0.2
        entries.append(
            {
                **item,
                "index": index,
                "start": clock,
                "duration": duration,
                "scene_start": scene_start,
            }
        )
        clock += duration
    clock += SCENE_TAIL.get(previous, 0.5)
    clock += 0.35
    return entries, clock


def locate(entries, t):
    current = entries[0]
    for entry in entries:
        if entry["start"] <= t:
            current = entry
        else:
            break
    return current, t - current["start"], t - current["scene_start"]


def write_srt(entries):
    def stamp(seconds):
        seconds = max(0, seconds)
        millis = int(round(seconds * 1000))
        hours, millis = divmod(millis, 3600000)
        minutes, millis = divmod(millis, 60000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    blocks = []
    for number, entry in enumerate(entries, start=1):
        end = entry["start"] + entry["duration"]
        if number < len(entries):
            end = min(end + 0.12, entries[number]["start"])
        blocks.append(f"{number}\n{stamp(entry['start'])} --> {stamp(end)}\n{entry['show']}\n")
    SRT_PATH.write_text("\n".join(blocks), encoding="utf-8")


def write_narration(entries, total):
    lines = [
        "# 旁白稿",
        "",
        "声音：zh-CN-XiaoxiaoNeural，语速 -3%。字幕用书面数字，口播用中文读法。",
        f"成片目标时长约 {total:.1f} 秒。",
        "",
    ]
    scene = None
    for entry in entries:
        if entry["scene"] != scene:
            scene = entry["scene"]
            lines.append(f"## {entry['title']}")
            lines.append("")
        lines.append(f"- 口播：{entry['say']}")
        if entry["show"] != entry["say"]:
            lines.append(f"- 字幕：{entry['show']}")
        lines.append("")
    NARRATION_PATH.write_text("\n".join(lines), encoding="utf-8")


def render_cover(report):
    frame = render_frame(report, 1, 1.2, 1.2, 1.15, show_sub=False, speech=0.45)
    draw = ImageDraw.Draw(frame)
    font = fonts()["small"]
    draw.text((330, 1648), "分词  ·  生成参数  ·  显存  ·  FP16 / BF16", font=font, fill=TITLE)
    frame.save(COVER_PATH, quality=95)
    return frame


def preview(report):
    STILL_DIR.mkdir(parents=True, exist_ok=True)
    WARNINGS.clear()
    seen = {}
    for index, item in enumerate(CUES):
        seen.setdefault(item["scene"], index)
        clock = 1.5 + index * 0.15
        speech = 0.2 + 0.65 * abs(math.sin(clock * 5))
        frame = render_frame(report, index, 0.95, 1.1, clock, show_sub=True, speech=speech)
        frame.save(STILL_DIR / f"{index:02d}_{item['scene']}.png")
    render_cover(report)
    print("stills", len(CUES), "warnings", len(WARNINGS))
    for warning in WARNINGS[:40]:
        print("WARN", warning)


async def synthesize(rate):
    import edge_tts

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    async def one(index, text):
        path = AUDIO_DIR / f"line_{index:02d}.mp3"
        communicate = edge_tts.Communicate(text, VOICE, rate=rate)
        await communicate.save(str(path))

    await asyncio.gather(*(one(index, item["say"]) for index, item in enumerate(CUES)))


def wav_duration_and_samples(path):
    with wave.open(str(path), "rb") as handle:
        if handle.getframerate() != SR or handle.getnchannels() != 1:
            raise SystemExit(f"音频格式不符 {path}")
        frames = handle.readframes(handle.getnframes())
    data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return data


def decode_lines():
    durations = []
    clips = []
    for index in range(len(CUES)):
        mp3 = AUDIO_DIR / f"line_{index:02d}.mp3"
        wav = AUDIO_DIR / f"line_{index:02d}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        samples = wav_duration_and_samples(wav)
        fade = int(0.02 * SR)
        if len(samples) > fade * 2:
            ramp = np.linspace(0, 1, fade, dtype=np.float32)
            samples[:fade] *= ramp
            samples[-fade:] *= ramp[::-1]
        clips.append(samples)
        durations.append(len(samples) / SR)
    return durations, clips


def music(n_samples):
    time = np.arange(n_samples, dtype=np.float32) / SR
    tone = np.zeros(n_samples, dtype=np.float32)
    # soft pad, C major
    for freq, gain in ((130.81, 0.08), (164.81, 0.05), (196.00, 0.05), (261.63, 0.03)):
        tone += gain * np.sin(2 * math.pi * freq * time)
    tremolo = 0.85 + 0.15 * np.sin(2 * math.pi * 0.12 * time)
    tone *= tremolo
    beat = 60 / 72
    scale = [261.63, 293.66, 329.63, 392.00, 440.00, 329.63, 392.00, 493.88]
    pattern = [0, 2, 4, 2, 3, 4, 7, 4, 0, 4, 3, 2, 4, 2, 0, 3]
    for index, degree in enumerate(pattern * (int(time[-1] / beat) // len(pattern) + 2)):
        start = int(index * beat * SR)
        if start >= n_samples:
            break
        length = int(0.42 * SR)
        end = min(n_samples, start + length)
        local = np.arange(end - start, dtype=np.float32) / SR
        env = np.exp(-local * 5.5)
        freq = scale[degree % len(scale)]
        pluck = env * (0.22 * np.sin(2 * math.pi * freq * local) + 0.05 * np.sin(2 * math.pi * freq * 2 * local))
        tone[start:end] += pluck
    peak = np.max(np.abs(tone)) + 1e-8
    tone = tone / peak * 0.045
    fade = int(1.2 * SR)
    if n_samples > fade * 2:
        ramp = np.linspace(0, 1, fade, dtype=np.float32)
        tone[:fade] *= ramp
        tone[-fade:] *= ramp[::-1]
    return np.stack([tone, tone], axis=1)


def assemble_audio(entries, clips, total):
    n = int(round(total * SR))
    voice = np.zeros(n, dtype=np.float32)
    for entry, clip in zip(entries, clips):
        start = int(round(entry["start"] * SR))
        end = min(n, start + len(clip))
        voice[start:end] += clip[: end - start]
    # peak safety before loudnorm
    peak = np.max(np.abs(voice)) + 1e-8
    if peak > 0.98:
        voice *= 0.98 / peak
    voice_path = AUDIO_DIR / "voice.wav"
    music_path = AUDIO_DIR / "music.wav"
    mix_path = AUDIO_DIR / "mix.wav"
    write_wav(voice_path, voice.reshape(-1, 1))
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(voice_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(AUDIO_DIR / "voice_norm.wav"),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    voice = read_any(AUDIO_DIR / "voice_norm.wav")
    if len(voice) < n:
        voice = np.pad(voice, (0, n - len(voice)))
    voice = voice[:n]
    bed = music(n)
    mix = bed.copy()
    mix[:, 0] += voice
    mix[:, 1] += voice
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    write_wav(mix_path, mix)
    write_wav(music_path, bed)
    return mix_path


def write_wav(path, samples):
    audio = np.clip(samples, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(samples.shape[1] if samples.ndim == 2 else 1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


def read_any(path):
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        frames = handle.readframes(handle.getnframes())
    data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data


def speech_levels(voice, n_frames):
    levels = np.zeros(n_frames, dtype=np.float32)
    if n_frames == 0 or len(voice) == 0:
        return levels
    hop = len(voice) / n_frames
    for index in range(n_frames):
        start = int(index * hop)
        stop = max(start + 1, int((index + 1) * hop))
        chunk = voice[start:stop]
        levels[index] = float(np.sqrt(np.mean(chunk * chunk)))
    levels = np.clip((levels - 0.015) / 0.07, 0, 1)
    kernel = np.array([0.12, 0.2, 0.36, 0.2, 0.12], dtype=np.float32)
    return np.convolve(levels, kernel, mode="same")


def render_video(report, entries, total, mix_path, levels):
    n_frames = int(round(total * FPS))
    command = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(mix_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "18",
        "-preset", "medium", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "160k", "-ar", str(SR), "-ac", "2",
        "-shortest",
        str(OUT_MP4),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_index in range(n_frames):
            t = frame_index / FPS
            entry, age, scene_age = locate(entries, t)
            # fade ends
            speech = float(levels[frame_index]) if frame_index < len(levels) else 0.0
            image = render_frame(report, entry["index"], age, scene_age, t, show_sub=True, speech=speech)
            if t < 0.35:
                image = Image.blend(Image.new("RGB", (W, H), BG_TOP), image, t / 0.35)
            if total - t < 0.45:
                image = Image.blend(image, Image.new("RGB", (W, H), BG_BOT), (0.45 - (total - t)) / 0.45)
            process.stdin.write(image.tobytes())
            if frame_index % (FPS * 5) == 0:
                print(f"frame {frame_index}/{n_frames}", flush=True)
    finally:
        if process.stdin:
            process.stdin.close()
        err = process.stderr.read().decode("utf-8", "replace") if process.stderr else ""
        code = process.wait()
    if code != 0:
        raise SystemExit(err[-2000:])
    print("wrote", OUT_MP4)


def build(rate):
    report = load_report()
    asyncio.run(synthesize(rate))
    durations, clips = decode_lines()
    entries, total = build_timeline(durations)
    print(f"duration {total:.2f}s rate {rate} speech {sum(durations):.1f}s")
    write_srt(entries)
    write_narration(entries, total)
    render_cover(report)
    mix = assemble_audio(entries, clips, total)
    voice = read_any(AUDIO_DIR / "voice_norm.wav")
    levels = speech_levels(voice, int(round(total * FPS)))
    render_video(report, entries, total, mix, levels)
    return total


def main():
    import sys

    report = load_report()
    command = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if command == "preview":
        preview(report)
    elif command == "build":
        rate = sys.argv[2] if len(sys.argv) > 2 else VOICE_RATE
        build(rate)
    else:
        raise SystemExit("usage: preview | build [rate]")


if __name__ == "__main__":
    main()
