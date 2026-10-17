#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从知识库台账 + 排期表生成：
   ① books/index.html —— 半亩方塘书目索引（已读/已发 + 待读），风格与首页一致
   ② feed.xml        —— RSS 2.0，指向公众号文章（可订阅）
数据源（只读）：
   ✍️ 思考沉淀/半亩方塘_重温百部名著/发布记录_台账.md
   ✍️ 思考沉淀/半亩方塘_重温百部名著/书单排期_半亩方塘.md
"""
import re, html, datetime, os

VAULT = "/Volumes/home/knowledge-vault/✍️ 思考沉淀/半亩方塘_重温百部名著/"
OUT = "/Users/apple/CodexProjects/dqquan_home/"
SITE = "https://dqquan.com"

tai = open(VAULT + "发布记录_台账.md", encoding="utf-8").read()
pai = open(VAULT + "书单排期_半亩方塘.md", encoding="utf-8").read()


def clean(s):
    s = s.replace("**", "").replace("\\", "").strip()
    return s


def parse_table(txt):
    rows = []
    for line in txt.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [clean(c) for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


# ---- ① 台账：期 | 书名 | 发表时间 | 链接 ----
tai_rows = parse_table(tai)
books = {}
for c in tai_rows:
    m = re.match(r"^(\d+|序)$", c[0])
    if not m or len(c) < 4:
        continue
    no = c[0]
    if no == "序":
        no = "0"
    name = re.sub(r"^《|》$", "", c[1]).strip()
    link = c[3].strip()
    if not link.startswith("http"):
        link = ""
    books[int(no)] = {"no": int(no), "name": name, "date": c[2].strip(), "link": link}

# ---- ② 排期表：期 | 书名 | 国别/作者 ----
pai_rows = parse_table(pai)
for c in pai_rows:
    m = re.match(r"^\*{0,2}(\d+)\*{0,2}$", c[0])
    if not m or len(c) < 3:
        continue
    no = int(m.group(1))
    name = re.sub(r"^《|》$", "", c[1]).strip()
    tag = c[2].strip()
    tag = re.sub(r"\s*·\s*", " · ", tag)
    if no in books:
        books[no].setdefault("tag", tag)
        if not books[no].get("tag"):
            books[no]["tag"] = tag
        # 日期从排期的状态里补（"已发表 2026-10-07" 之类）
        if not books[no]["date"] or books[no]["date"] == "—":
            d = re.search(r"(20\d\d-\d\d-\d\d)", c[3] if len(c) > 3 else "")
            if d:
                books[no]["date"] = d.group(1)
    else:
        books[no] = {"no": no, "name": name, "tag": tag, "date": "", "link": ""}

items = [books[k] for k in sorted(books) if books[k].get("name")]
issued = [b for b in items if b["no"] >= 1]

print("解析到 %d 条（序 + 正文 %d 条）" % (len(items), len(issued)))

# ---- 生成 books/index.html ----
def row(b):
    no = "序" if b["no"] == 0 else str(b["no"])
    name = html.escape(b["name"])
    tag = html.escape(b.get("tag") or "")
    date = html.escape((b.get("date") or "").replace("—", "").strip())
    if b.get("link"):
        return ('<li><a href="{u}" target="_blank" rel="noopener">'
                '<span class="no">{n}</span><span class="t">{t}</span>'
                '<span class="g">{g}</span><span class="d">{d}</span></a></li>').format(
            u=html.escape(b["link"]), n=no, t=name, g=tag, d=date)
    return ('<li class="todo"><span class="no">{n}</span><span class="t">{t}</span>'
            '<span class="g">{g}</span><span class="d">待补链接</span></li>').format(
        n=no, t=name, g=tag)


CSS = """
:root{--ink:#1f1f1f;--ink-2:#555;--ink-3:#8a8a8a;--paper:#fbfaf7;--line:#e3e0d8;--seal:#a63a2c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC","STSong",Georgia,serif;
 line-height:1.85;-webkit-font-smoothing:antialiased}
.wrap{max-width:760px;margin:0 auto;padding:64px 24px 96px}
a{color:inherit;text-decoration:none}
header{border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:8px}
h1{font-size:26px;letter-spacing:.18em;font-weight:500;margin:0 0 8px}
.sub{color:var(--ink-3);font-size:13px;letter-spacing:.12em}
.back{display:inline-block;margin:22px 0 0;font-size:13px;color:var(--ink-3)}
.back:hover{color:var(--seal)}
.note{color:var(--ink-2);font-size:14px;margin:26px 0 10px}
ul{list-style:none;margin:0;padding:0}
li{border-bottom:1px dotted var(--line)}
li:last-child{border-bottom:0}
li a,li.todo{display:grid;grid-template-columns:46px 1fr 92px 92px;gap:12px;
 align-items:baseline;padding:11px 2px;font-size:15.5px}
li a:hover .t{color:var(--seal)}
.no{color:var(--ink-3);font-size:12.5px;letter-spacing:.06em}
.g{color:var(--ink-3);font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.d{color:var(--ink-3);font-size:12.5px;text-align:right;white-space:nowrap}
li.todo{color:var(--ink-3)}
footer{border-top:1px solid var(--line);margin-top:44px;padding-top:20px;
 color:var(--ink-3);font-size:12.5px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px}
@media(max-width:560px){
 .wrap{padding:44px 18px 72px}
 li a,li.todo{grid-template-columns:38px 1fr;gap:2px 10px;font-size:15px}
 .g,.d{grid-column:2;font-size:12px}
 .d{text-align:left}
}
"""

rows_html = "\n".join(row(b) for b in issued)
n = len(issued)
today = datetime.date.today().isoformat()

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>书目索引 · 半亩方塘</title>
<meta name="description" content="半亩方塘 · 重温百部名著：已读书目索引，含读完日期与原文链接。">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<style>%s</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>书目索引</h1>
    <div class="sub">半亩方塘 · 重温百部名著　｜　已 {n} 部</div>
    <a class="back" href="/">← 回首页</a>
  </header>

  <p class="note">按发表顺序排列。点书名可读原文。<b>已读 {n} 部</b>，书目持续增加。</p>

  <ul>
%s
  </ul>

  <footer>
    <span>© 2026 泉森</span>
    <span><a href="/feed.xml">RSS 订阅</a>　·　dqquan.com</span>
  </footer>
</div>
</body>
</html>
""" % (CSS, rows_html)

os.makedirs(OUT + "books", exist_ok=True)
open(OUT + "books/index.html", "w", encoding="utf-8").write(page.replace("{n}", str(n)))
print("写出 books/index.html：%d 条" % len(issued))

# ---- 生成 feed.xml（RSS 2.0）----
now = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
entries = []
for b in reversed(issued):
    if not b.get("link"):
        continue
    title = ("序 · " if b["no"] == 0 else "第 %d 期 · " % b["no"]) + b["name"]
    entries.append(
        "    <item>\n"
        "      <title>%s</title>\n"
        "      <link>%s</link>\n"
        "      <guid isPermaLink=\"true\">%s</guid>\n"
        "      <description>半亩方塘 · 重温百部名著｜%s</description>\n"
        "    </item>" % (html.escape(title), html.escape(b["link"]), html.escape(b["link"]),
                         html.escape(b.get("tag") or "")))
feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>半亩方塘 · 重温百部名著</title>
    <link>%s</link>
    <description>读完一本，说几句话。</description>
    <language>zh-cn</language>
    <lastBuildDate>%s</lastBuildDate>
%s
  </channel>
</rss>
""" % (SITE + "/books/", now, "\n".join(entries))
open(OUT + "feed.xml", "w", encoding="utf-8").write(feed)
print("写出 feed.xml：%d 条（有链接的才进 feed）" % len(entries))
