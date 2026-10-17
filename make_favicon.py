#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成站点图标：朱红方印 + 白「泉」，输出 favicon 32/64/180 PNG。"""
from PIL import Image, ImageDraw, ImageFont

RED = (166, 58, 44, 255)     # #a63a2c 与站点印章同色
WHITE = (251, 250, 247, 255)  # #fbfaf7 纸白
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
OUT = "/Users/apple/CodexProjects/dqquan_home/"

for size in (32, 64, 180, 512):
    S = size * 8                      # 8x 超采样再缩，边缘干净
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(S * 0.06)
    d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=int(S * 0.12), fill=RED)
    # 「泉」字，居中
    f = ImageFont.truetype(FONT, int(S * 0.62))
    box = d.textbbox((0, 0), "泉", font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((S - w) / 2 - box[0], (S - h) / 2 - box[1] - S * 0.015), "泉", font=f, fill=WHITE)
    im = im.resize((size, size), Image.LANCZOS)
    name = {32: "favicon-32.png", 64: "favicon-64.png",
            180: "apple-touch-icon.png", 512: "favicon-512.png"}[size]
    im.save(OUT + name)
    print("  写出", name, size, "x", size)
