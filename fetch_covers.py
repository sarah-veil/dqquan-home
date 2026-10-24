#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从公众号原文抓每期封面图。

数据源：知识库台账「已发表清单」的链接列
输出：img/covers/wx/bNN.jpg（原始封面）+ 报告

用法：python3 fetch_covers.py [--dry]
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "img" / "covers" / "wx"
TAI = Path("/Volumes/home/knowledge-vault/✍️ 思考沉淀/半亩方塘_重温百部名著/发布记录_台账.md")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


def parse_tai(path: Path):
    txt = path.read_text(encoding="utf-8")
    m = re.search(r"##\s*已发表清单.*?(?=\n##\s|\Z)", txt, re.S)
    if m:
        txt = m.group(0)
    rows = []
    for line in txt.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        no_raw, name, _, link = cells[0], cells[1], cells[2], cells[3]
        mm = re.match(r"^(\d+|序)$", no_raw)
        if not mm:
            continue
        no = 0 if no_raw == "序" else int(mm.group(1))
        um = re.search(r"https://mp\.weixin\.qq\.com/s/[\w-]+", link)
        rows.append(dict(no=no, name=name, url=um.group(0) if um else ""))
    return rows


def fetch(url: str, timeout=25) -> str:
    r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True, errors="ignore")
    return r.stdout


def main():
    dry = "--dry" in sys.argv
    rows = parse_tai(TAI)
    print(f"台账解析到 {len(rows)} 条\n")
    OUT.mkdir(parents=True, exist_ok=True)
    ok = miss = fail = 0
    for row in rows:
        tag = f"b{row['no']:02d}"
        if not row["url"]:
            print(f"  · {tag} {row['name']}: 台账无链接")
            miss += 1
            continue
        html = fetch(row["url"])
        m = re.search(r'property="og:image"\s+content="([^"]+)"', html) or \
            re.search(r'msg_cdn_url\s*=\s*"([^"]+)"', html)
        if not m:
            print(f"  ✗ {tag} {row['name']}: 没找到封面（页面 {len(html)} 字节）")
            fail += 1
            continue
        img_url = m.group(1).replace("&amp;", "&")
        dest = OUT / f"{tag}.jpg"
        if dry:
            print(f"  · {tag} {row['name']}: {img_url[:80]}")
            ok += 1
            continue
        d = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA,
                            "-e", "https://mp.weixin.qq.com/", img_url, "-o", str(dest)],
                           capture_output=True)
        size = dest.stat().st_size if dest.exists() else 0
        if d.returncode == 0 and size > 5000:
            print(f"  ✓ {tag} {row['name']}: {size//1024}KB")
            ok += 1
        else:
            print(f"  ✗ {tag} {row['name']}: 下载失败（{size} 字节）")
            fail += 1
    print(f"\n成功 {ok} / 无链接 {miss} / 失败 {fail}")


if __name__ == "__main__":
    main()
