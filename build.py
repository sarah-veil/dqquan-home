#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dqquan.com 站点构建脚本

一期：三位期号 + 旧链接兼容页 + 全量 sitemap + OG 卡片 + 404 + 国家相册
二期：图片 srcset 挂接 + 翻页 + 目录分组 + 关于页骨架

用法：
    python3 build.py            # 构建全部
    python3 build.py books      # 只重建书页
    python3 build.py photos     # 只重建相册
    python3 build.py sitemap    # 只重建 sitemap/404

原则：幂等。可反复跑。不删除任何原文件（旧链接用兼容页占位）。
"""
import os
import re
import sys
import html
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SITE = "https://dqquan.com"
TZ = timezone.utc

OG_IMAGE = f"{SITE}/img/photo-3.jpg"

# ── 国家相册数据（图注取自 photos/index.html 现有内容）────────────────
COUNTRIES = [
    dict(
        slug="peru-2026", year="2026", name="秘鲁", key="peru",
        lead="从太平洋岸到高原湿地，留下三帧关于花、水与岩壁的画面。",
        photos=[("peru-01.jpg", "紫色花穗上的蜂鸟", "tall"),
                ("peru-02.jpg", "浅水中觅食的火烈鸟", "tall"),
                ("peru-03.jpg", "岩壁上的印加燕鸥", "tall")],
    ),
    dict(
        slug="colombia-2019", year="2019", name="哥伦比亚", key="colombia",
        lead="安第斯山把云雾林、花朵和蜂鸟放在同一片山坡上。",
        photos=[("colombia-01.jpg", "蜂鸟停在橙色钟形花前", "wide"),
                ("colombia-02.jpg", "正面悬停的蜂鸟", "tall"),
                ("colombia-03.jpg", "云雾林中的安第斯冠伞鸟", "wide")],
    ),
    dict(
        slug="kenya-2017", year="2017", name="肯尼亚", key="kenya",
        lead="草原上的一天，从狮子的脚步开始，在落日和飞鸟里结束。",
        photos=[("kenya-01.jpg", "草原上迎面走来的雄狮", "tall"),
                ("kenya-02.jpg", "草原落日", "wide"),
                ("kenya-03.jpg", "掠过水面的火烈鸟", "wide")],
    ),
    dict(
        slug="norway-2015", year="2015", name="挪威", key="norway",
        lead="一条跨海的路，一排临水的木屋，以及天色将暗时的峡湾。",
        photos=[("norway-01.jpg", "大西洋海滨公路", "wide"),
                ("norway-02.jpg", "卑尔根布吕根木屋", "wide"),
                ("norway-03.jpg", "暮色中的峡湾小镇", "wide")],
    ),
]

CSS_TOKENS = """:root{--paper:#fbfaf7;--ink:#1f1f1f;--ink-2:#555;--ink-3:#6e6a62;--line:#e3e0d8;--seal:#a63a2c}"""


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def mtime_iso(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=TZ)
    return ts.strftime("%Y-%m-%d")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ {rel(path)}")


# ── 书目 ─────────────────────────────────────────────────────────────
def load_books():
    """读取 src/html/NN.html（正文正本），返回按数字排序的列表。

    ⚠️ 正本在 src/html/，不在 books/ —— books/NN.html 会被 build 写成兼容跳转页，
    所以绝不能拿 books/ 当源，否则第二次跑就把正文覆盖没了（2026-10-24 踩过）。
    """
    books = []
    src_dir = ROOT / "src" / "html"
    for p in sorted(src_dir.glob("*.html")):
        if p.name == "index.html":
            continue
        m = re.fullmatch(r"(\d+)\.html", p.name)
        if not m:
            continue
        no = int(m.group(1))
        src = p.read_text(encoding="utf-8")
        tm = re.search(r"<title>([^<]+)</title>", src)
        title = html.unescape(tm.group(1)).split(" · ")[0].strip() if tm else f"第{no}期"
        books.append(dict(no=no, slug=f"{no:03d}", title=title,
                          path=ROOT / "books" / p.name, html=src))
    books.sort(key=lambda b: b["no"])
    return books


OG_BLOCK = """<meta name="description" content="{desc}">
<meta property="og:site_name" content="半亩方塘">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
"""

PAGER_CSS = """
  .pager{display:flex;justify-content:space-between;gap:24px;margin:56px 0 0;
    padding-top:22px;border-top:1px solid var(--line);font-size:13px;letter-spacing:.06em}
  .pager a{text-decoration:none;color:var(--ink-2);max-width:46%}
  .pager a:hover{color:var(--seal)}
  .pager .next{margin-left:auto;text-align:right}
  @media (max-width:640px){.pager{flex-direction:column;gap:14px}.pager .next{margin-left:0;text-align:left}}
"""


def build_book_page(b: dict, books: list) -> None:
    out_dir = ROOT / "books" / b["slug"]
    out = out_dir / "index.html"
    s = b["html"]

    # 1) 相对路径上移一层：books/xx.html → books/xxx/index.html
    s = re.sub(r'(href|src)="\.\./', r'\1="../../', s)

    # 2) OG + canonical
    url = f"{SITE}/books/{b['slug']}/"
    label = "序" if b["no"] == 0 else f"第 {b['no']} 期"
    desc = f"{label} · 重温百部名著" if b["no"] else "半亩方塘 · 开卷"
    og = OG_BLOCK.format(desc=desc, ogtype="article", title=f"{b['title']} · 半亩方塘",
                         url=url, image=OG_IMAGE)
    if "</head>" in s:
        s = s.replace("</head>", og + "</head>", 1)
    else:
        s = s.replace("</style></head>", "</style>" + og + "</head>", 1)

    # 3) 翻页样式
    if "</style>" in s:
        s = s.replace("</style>", PAGER_CSS + "</style>", 1)

    # 4) 上一期 / 下一期
    idx = books.index(b)
    prev_b = books[idx - 1] if idx > 0 else None
    next_b = books[idx + 1] if idx + 1 < len(books) else None
    links = []
    if prev_b:
        lbl = "序" if prev_b["no"] == 0 else f"第 {prev_b['no']} 期"
        links.append(f'<a href="../{prev_b["slug"]}/">← {lbl} · {html.escape(prev_b["title"])}</a>')
    else:
        links.append('<a href="../">← 全部目录</a>')
    if next_b:
        lbl = f"第 {next_b['no']} 期"
        links.append(f'<a class="next" href="../{next_b["slug"]}/">{lbl} · {html.escape(next_b["title"])} →</a>')
    else:
        links.append('<a class="next" href="../">全部目录 →</a>')
    pager = '<nav class="pager">' + "".join(links) + "</nav>"

    if "</article>" in s:
        s = s.replace("</article>", "</article>\n" + pager, 1)
    else:
        s = s.replace("<footer", pager + "\n<footer", 1)

    write(out, s)


def build_legacy_redirect(b: dict) -> None:
    """books/31.html → 兼容页，跳到 books/031/"""
    target = f"{b['slug']}/"
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html.escape(b['title'])} · 半亩方塘</title>
<link rel="canonical" href="{SITE}/books/{b['slug']}/">
<meta http-equiv="refresh" content="0; url={target}">
<meta name="robots" content="noindex,follow">
<style>body{{margin:0;padding:72px 24px;background:#fbfaf7;color:#1f1f1f;
font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.9;text-align:center}}
a{{color:#a63a2c}}</style>
</head>
<body><p>这一期已迁至新地址：<a href="{target}">第 {b['no']} 期 · {html.escape(b['title'])}</a></p></body>
</html>
"""
    write(b["path"], page)


# ── 目录页 ───────────────────────────────────────────────────────────
def build_books_index(books: list) -> None:
    published = len([b for b in books if b["no"] > 0])
    groups = {}
    for b in books:
        # 序单独一组；01-10 → 0，11-20 → 1 ……
        key = -1 if b["no"] == 0 else (b["no"] - 1) // 10
        groups.setdefault(key, []).append(b)

    def group_title(k):
        if k == -1:
            return "开卷"
        lo, hi = k * 10 + 1, k * 10 + 10
        return f"{lo:02d} — {hi:02d}"

    parts = []
    for k in sorted(groups):
        parts.append(f'<h2 class="grp">{group_title(k)}</h2><ul>')
        for b in groups[k]:
            num = "序" if b["no"] == 0 else f'{b["no"]:02d}'
            parts.append(
                f'<li><a href="{b["slug"]}/"><span>{num}</span>{html.escape(b["title"])}</a></li>')
        parts.append("</ul>")
    listing = "\n".join(parts)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>重温百部名著 · 半亩方塘</title>
{OG_BLOCK.format(desc=f"已读 {published} 期 · 一百部书，一百个夜晚。", ogtype="website",
                title="重温百部名著 · 半亩方塘", url=f"{SITE}/books/", image=OG_IMAGE)}
<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png">
<style>
{CSS_TOKENS}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.9}}
.wrap{{max-width:720px;margin:0 auto;padding:0 26px}}
header{{display:flex;justify-content:space-between;padding:30px 0 16px;border-bottom:1px solid var(--line);font-size:13px;letter-spacing:.2em}}
header a{{text-decoration:none}}
h1{{font-size:34px;font-weight:500;margin:46px 0 8px}}
p.lede{{color:var(--ink-2);font-size:14px;margin:0 0 10px}}
.progress{{font-size:12px;color:var(--ink-3);letter-spacing:.14em;margin:0 0 34px}}
.bar{{height:2px;background:var(--line);margin:10px 0 0}}
.bar i{{display:block;height:2px;background:var(--seal);width:{min(published,100)}%}}
h2.grp{{font-size:12px;letter-spacing:.3em;color:var(--ink-3);font-weight:400;margin:44px 0 6px}}
ul{{list-style:none;padding:0;margin:0}}
li{{border-bottom:1px solid var(--line)}}
li a{{display:flex;gap:18px;padding:14px 2px;text-decoration:none;font-size:17px}}
li a:hover{{color:var(--seal)}}
li span{{color:var(--ink-3);font-size:12px;min-width:26px;padding-top:4px}}
header .mark{{color:var(--seal)}}
footer{{margin:60px 0 70px;font-size:12px;color:var(--ink-3);letter-spacing:.08em}}
footer a{{text-decoration:none;border-bottom:1px solid var(--line)}}
</style></head><body><div class="wrap">
<header><span class="mark">半亩方塘</span><a href="../index.html">回到首页</a></header>
<h1>重温百部名著</h1>
<p class="lede">一百部书，一百个夜晚。</p>
<p class="progress">已读 {published} / 100</p>
<div class="bar"><i></i></div>
{listing}
<footer><a href="../index.html">泉森 · 半亩方塘</a> · <a href="../feed.xml">RSS</a></footer>
</div></body></html>
"""
    write(ROOT / "books" / "index.html", page)


# ── 国家相册 ─────────────────────────────────────────────────────────
def photo_page(c: dict, prev_c, next_c) -> str:
    figs = []
    for fn, cap, ratio in c["photos"]:
        stem = fn.rsplit(".", 1)[0]
        # 两档：800w / 1600w（图未生成时浏览器回落原图）
        srcset = (f'../../img/countries/w800/{stem}.webp 800w, '
                  f'../../img/countries/w1600/{stem}.webp 1600w')
        figs.append(f"""      <figure class="{ratio}">
        <a href="../../img/countries/{fn}" target="_blank" rel="noopener">
          <img loading="lazy" src="../../img/countries/{fn}"
               srcset="{srcset}" sizes="(max-width:820px) 92vw, 720px"
               alt="{html.escape(cap)}">
        </a>
        <figcaption>{html.escape(cap)}</figcaption>
      </figure>""")
    gallery = "\n".join(figs)

    nav = []
    if prev_c:
        nav.append(f'<a href="../{prev_c["slug"]}/">← {prev_c["year"]} · {prev_c["name"]}</a>')
    else:
        nav.append('<a href="../">全部国家影像</a>')
    if next_c:
        nav.append(f'<a class="next" href="../{next_c["slug"]}/">{next_c["year"]} · {next_c["name"]} →</a>')
    else:
        nav.append('<a class="next" href="../">全部国家影像 →</a>')

    url = f"{SITE}/photos/{c['slug']}/"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{OG_BLOCK.format(desc=c["lead"], ogtype="article", title=f'{c["name"]} · {c["year"]} · 半亩方塘', url=url, image=f"{SITE}/img/countries/{c['photos'][0][0]}")}
<link rel="icon" type="image/png" sizes="32x32" href="../../favicon-32.png">
<style>
{CSS_TOKENS}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.9}}
.wrap{{max-width:860px;margin:0 auto;padding:0 26px}}
header{{display:flex;justify-content:space-between;padding:30px 0 16px;border-bottom:1px solid var(--line);font-size:13px;letter-spacing:.2em}}
header a{{text-decoration:none;color:var(--ink-2)}}
header a:hover{{color:var(--seal)}}
header .mark{{color:var(--seal)}}
.intro{{padding:54px 0 34px;border-bottom:1px solid var(--line)}}
.year{{font-size:12px;letter-spacing:.24em;color:var(--ink-3);margin:0 0 8px}}
h1{{font-size:clamp(30px,4.6vw,46px);font-weight:500;margin:0 0 14px;line-height:1.25}}
.intro p{{font-size:15px;color:var(--ink-2);margin:0;max-width:32em}}
.gallery{{padding:44px 0 10px}}
figure{{margin:0 0 46px}}
figure img{{display:block;width:100%;height:auto;filter:grayscale(.12)}}
figure.tall img{{aspect-ratio:4/5;object-fit:cover}}
figure.wide img{{aspect-ratio:3/2;object-fit:cover}}
figcaption{{font-size:12px;color:var(--ink-3);letter-spacing:.06em;margin-top:10px}}
.pager{{display:flex;justify-content:space-between;gap:24px;padding:22px 0 0;border-top:1px solid var(--line);font-size:13px}}
.pager a{{text-decoration:none;color:var(--ink-2)}}
.pager a:hover{{color:var(--seal)}}
.pager .next{{margin-left:auto}}
footer{{margin:56px 0 70px;font-size:12px;color:var(--ink-3);letter-spacing:.08em}}
footer a{{text-decoration:none;border-bottom:1px solid var(--line)}}
@media (max-width:820px){{.wrap{{padding:0 20px}}figure.tall img,figure.wide img{{aspect-ratio:auto}}}}
</style></head>
<body><div class="wrap">
<header><a class="mark" href="../../index.html">半亩方塘</a><a href="../">全部国家影像</a></header>
<div class="intro">
  <p class="year">{c["year"]}</p>
  <h1>{c["name"]}</h1>
  <p>{c["lead"]}</p>
</div>
<div class="gallery">
{gallery}
</div>
<nav class="pager">{"".join(nav)}</nav>
<footer><a href="../../index.html">泉森 · 半亩方塘</a> · <a href="../">影像档案</a></footer>
</div></body></html>
"""


def build_photo_pages() -> None:
    for i, c in enumerate(COUNTRIES):
        prev_c = COUNTRIES[i - 1] if i > 0 else None
        next_c = COUNTRIES[i + 1] if i + 1 < len(COUNTRIES) else None
        write(ROOT / "photos" / c["slug"] / "index.html", photo_page(c, prev_c, next_c))


# ── 首页 / 影像索引：加 OG、链接指向新地址 ──────────────────────────
def upgrade_static_pages(books: list) -> None:
    idx = ROOT / "index.html"
    s = idx.read_text(encoding="utf-8")
    for b in books:
        if b["no"] == 0:
            continue
        s = s.replace(f'href="books/{b["no"]}.html"', f'href="books/{b["slug"]}/"')
    if "og:site_name" not in s:
        og = OG_BLOCK.format(
            desc="泉森的半亩方塘：一百部书的札记，按国家收拢的照片。",
            ogtype="website", title="泉森 · 半亩方塘", url=f"{SITE}/", image=OG_IMAGE)
        s = s.replace("</head>", og + "</head>", 1)
    idx.write_text(s, encoding="utf-8")
    print(f"  ✓ {rel(idx)}（OG + 期号链接）")

    ph = ROOT / "photos" / "index.html"
    t = ph.read_text(encoding="utf-8")
    for c in COUNTRIES:
        t = re.sub(rf'href="\.\./img/countries/{c["key"]}-\d+\.jpg"',
                   f'href="{c["slug"]}/"', t)
    if "og:site_name" not in t:
        og = OG_BLOCK.format(
            desc="泉森的影像档案：按国家收录风光、建筑、街景与物种。",
            ogtype="website", title="影像档案 · 半亩方塘",
            url=f"{SITE}/photos/", image=OG_IMAGE)
        t = t.replace("</head>", og + "</head>", 1)
    ph.write_text(t, encoding="utf-8")
    print(f"  ✓ {rel(ph)}（OG + 相册入口）")


# ── sitemap / 404 / 关于 ─────────────────────────────────────────────
def build_sitemap(books: list) -> None:
    urls = []

    def add(loc: str, lastmod: str, priority="0.7", freq="monthly"):
        urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    add(f"{SITE}/", mtime_iso(ROOT / "index.html"), "1.0")
    add(f"{SITE}/books/", mtime_iso(ROOT / "books" / "index.html"), "0.9", "weekly")
    for b in books:
        p = ROOT / "books" / b["slug"] / "index.html"
        add(f"{SITE}/books/{b['slug']}/", mtime_iso(p if p.exists() else b["path"]), "0.8")
    add(f"{SITE}/photos/", mtime_iso(ROOT / "photos" / "index.html"), "0.9", "weekly")
    for c in COUNTRIES:
        p = ROOT / "photos" / c["slug"] / "index.html"
        add(f"{SITE}/photos/{c['slug']}/", mtime_iso(p), "0.7")
    about = ROOT / "about" / "index.html"
    if about.exists():
        add(f"{SITE}/about/", mtime_iso(about), "0.6", "yearly")

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""
    write(ROOT / "sitemap.xml", body)


def build_404() -> None:
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>没有这一页 · 半亩方塘</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<style>
{CSS_TOKENS}
body{{margin:0;min-height:100vh;display:flex;align-items:center;background:var(--paper);color:var(--ink);
font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.95}}
.wrap{{max-width:620px;margin:0 auto;padding:0 26px}}
h1{{font-size:34px;font-weight:500;margin:0 0 16px}}
p{{color:var(--ink-2);font-size:15px;margin:0 0 30px}}
.links{{display:flex;gap:26px;font-size:13px;letter-spacing:.1em}}
.links a{{color:var(--seal);text-decoration:none;border-bottom:1px solid var(--seal);padding-bottom:2px}}
.mark{{color:var(--seal);font-size:13px;letter-spacing:.3em;margin-bottom:26px}}
</style></head>
<body><div class="wrap">
<div class="mark">半亩方塘</div>
<h1>这一页没有找到。</h1>
<p>可能是地址写错了，也可能是它还没写出来。<br>不急着走，往回翻翻。</p>
<div class="links">
  <a href="/">回到首页</a>
  <a href="/books/">去读书</a>
  <a href="/photos/">去看照片</a>
</div>
</div></body></html>
"""
    write(ROOT / "404.html", page)


def build_about_stub() -> None:
    """关于页骨架：正文留空位，等老爷写。已存在则不覆盖。"""
    out = ROOT / "about" / "index.html"
    if out.exists():
        print(f"  · {rel(out)} 已存在，跳过（不覆盖）")
        return
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{OG_BLOCK.format(desc="关于半亩方塘，以及写这些字、拍这些照片的人。", ogtype="website",
                title="关于 · 半亩方塘", url=f"{SITE}/about/", image=OG_IMAGE)}
<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png">
<style>
{CSS_TOKENS}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.95}}
.wrap{{max-width:680px;margin:0 auto;padding:0 26px}}
header{{display:flex;justify-content:space-between;align-items:baseline;padding:34px 0 18px;border-bottom:1px solid var(--line)}}
.mark{{font-size:20px;letter-spacing:.3em;color:var(--seal)}}
header a{{text-decoration:none;font-size:13px;letter-spacing:.2em;color:var(--ink-2)}}
h1{{font-size:clamp(28px,4vw,40px);font-weight:500;margin:64px 0 34px;line-height:1.3}}
section{{margin:0 0 40px}}
h2{{font-size:12px;letter-spacing:.36em;color:var(--ink-3);font-weight:400;margin:0 0 14px}}
p{{font-size:16px;color:var(--ink-2);margin:0 0 14px;max-width:30em}}
.seal{{margin:52px 0 0}}
.seal img{{width:92px;height:92px}}
footer{{margin:70px 0 80px;padding-top:22px;border-top:1px solid var(--line);font-size:12px;color:var(--ink-3);letter-spacing:.08em}}
footer a{{text-decoration:none;border-bottom:1px solid var(--line)}}
</style></head>
<body><div class="wrap">
<header><span class="mark">半亩方塘</span><a href="../index.html">回到首页</a></header>
<h1>关于这半亩方塘</h1>
<section>
  <h2>我是谁</h2>
  <p>（待写。两三句就够，不必交代履历。）</p>
</section>
<section>
  <h2>为什么读</h2>
  <p>（待写。）</p>
</section>
<section>
  <h2>为什么拍</h2>
  <p>（待写。）</p>
</section>
<section>
  <h2>联系</h2>
  <p><a href="mailto:quan@dqquan.com">quan@dqquan.com</a>　·　<a href="../feed.xml">RSS 订阅</a></p>
</section>
<div class="seal"><img src="../img/seal.svg" alt="半亩方塘"></div>
<footer><a href="../index.html">泉森 · 半亩方塘</a></footer>
</div></body></html>
"""
    write(out, page)


# ── 主流程 ───────────────────────────────────────────────────────────
def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    books = load_books()
    print(f"读到 {len(books)} 个书页（含序）")

    if what in ("all", "books"):
        print("\n[书页] 三位期号 + OG + 翻页")
        for b in books:
            build_book_page(b, books)
        print("\n[书页] 旧链接兼容页")
        for b in books:
            build_legacy_redirect(b)
        print("\n[目录] 分组 + 进度")
        build_books_index(books)

    if what in ("all", "404"):
        print("\n[404]")
        build_404()
        print("\n[关于] 骨架（不覆盖已有）")
        build_about_stub()

    if what in ("all", "photos"):
        print("\n[相册] 四个国家页")
        build_photo_pages()

    if what in ("all", "static"):
        print("\n[静态页] 首页 / 影像索引")
        upgrade_static_pages(books)

    if what in ("all", "sitemap"):
        print("\n[sitemap] 全量")
        build_sitemap(books)

    print("\n完成。")


if __name__ == "__main__":
    main()
