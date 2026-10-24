# dqquan.com（半亩方塘）

泉森的个人刊物：100 期读书札记 + 按国家收拢的影像档案。
纯静态 HTML，GitHub Pages 托管，Cloudflare 代理。

- 域名：https://dqquan.com
- 仓库：`sarah-veil/dqquan-home`（main 分支根目录发布）

---

## 目录结构：哪些是正本，哪些是生成物

```
src/
  html/NN.html      ✅ 书页正文正本（00=序）。改内容改这里。
  NN.md             原始 Markdown 稿（归档用，不参与构建）
books/
  NNN/index.html    ⚙️ 生成物（由 src/html/NN.html 生成）
  NN.html           ⚙️ 兼容跳转页（旧链接 → /books/NNN/）
  index.html        ⚙️ 生成物（目录，分组 + 进度）
photos/
  index.html        ✅ 手写（国家索引；缩略图链接指向各国相册）
  <slug>/index.html ⚙️ 生成物（国家相册，数据在 build.py 的 COUNTRIES）
about/index.html    ✅ 手写（正文由老爷写；build 只在不存在时建骨架）
index.html          ✅ 手写（首页；build 只补 OG 和期号链接）
img/countries/
  *.jpg             ✅ 原图（点开看大图用）
  w800/ w1600/      ⚙️ 生成物（WebP 两档，给 srcset 用）
sitemap.xml         ⚙️ 生成物（全量收录）
404.html            ⚙️ 生成物
```

## 构建

```bash
python3 build.py            # 全部重建（书页/目录/相册/sitemap/404/OG）
python3 build.py books      # 只重建书页
python3 build.py photos     # 只重建相册
python3 build.py sitemap    # 只重建 sitemap

python3 make_images.py      # 生成 WebP 两档（新增国家照片后跑）
```

幂等，可反复跑。**改完本地起服务看一遍再推：**

```bash
python3 -m http.server 8899
# 浏览器打开 http://127.0.0.1:8899/
```

## 发布的惯常流程

1. 新一期：把写好的 HTML 放进 `src/html/NN.html`（照现有格式），
2. `python3 build.py`
3. 本地看一眼 `/books/0NN/`、`/books/`
4. `git add -A && git commit -m "第 N 期 · 书名" && git push`

GitHub Pages 会在 1 分钟内自动发布。

## ⚠️ 三个坑（都踩过）

1. **绝不要拿 `books/*.html` 当正文源。**
   build 会把这些文件改写成兼容跳转页，第二次跑就只剩跳转页了。
   正本只在 `src/html/`。

2. **`legacy_gen_books.py` 不要跑。**
   它是早期版本（从知识库台账生成目录，链接指向公众号文章），已被 `build.py` 取代。
   跑了会覆盖 `books/index.html`。

3. **图片必须两档都生成。**
   相册页的 `srcset` 指向 `w800/` 和 `w1600/`，缺文件会退化成空白图。

## 期号规则

- `00` = 序，`01`–`100` = 各期。
- URL 一律三位补零：`/books/031/`。这样第 100 期是 `100`，字典序不会乱。
- 旧链接 `/books/31.html` 会以 meta refresh 跳到新地址，不会被搜到（`noindex`）。

## 导航约定

导航保持三个词：**阅读 / 记录 / 关于**。
正文里不出现作者职务、单位、社交账号。
