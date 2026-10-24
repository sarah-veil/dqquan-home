#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理：把 img/countries/*.jpg 转成两档 WebP（800w / 1600w）

用法：
    python3 make_images.py            # 全部国家图
    python3 make_images.py --check    # 只看会产出什么，不写文件

输出：
    img/countries/w800/<stem>.webp
    img/countries/w1600/<stem>.webp

原 JPEG 保留（相册页里点开原图仍然可用）。
依赖：ImageMagick（magick）
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "img" / "countries"
SIZES = [("w800", 800), ("w1600", 1600)]
QUALITY = 82


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    check = "--check" in sys.argv
    jpgs = sorted(p for p in SRC.glob("*.jpg") if p.is_file())
    if not jpgs:
        print("没有找到 img/countries/*.jpg")
        return
    print(f"源图 {len(jpgs)} 张")
    total_before = sum(p.stat().st_size for p in jpgs)
    total_after = 0
    made = 0

    for jpg in jpgs:
        for sub, width in SIZES:
            out = SRC / sub / f"{jpg.stem}.webp"
            if check:
                print(f"  · {out.relative_to(ROOT)}  (宽 {width})")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            r = run(["magick", str(jpg), "-auto-orient",
                     "-resize", f"{width}x>", "-quality", str(QUALITY),
                     str(out)])
            if r.returncode != 0:
                print(f"  ✗ {jpg.name} → {sub}: {r.stderr.strip()[:120]}")
                continue
            made += 1
            if sub == "w1600":
                total_after += out.stat().st_size

    if check:
        return
    print(f"生成 {made} 个文件")
    if total_after:
        print(f"原图合计 {total_before/1024:.0f} KB → 1600w WebP 合计 {total_after/1024:.0f} KB"
              f"（省 {100 - total_after/total_before*100:.0f}%）")


if __name__ == "__main__":
    main()
