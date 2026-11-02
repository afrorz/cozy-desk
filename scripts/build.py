"""Cozy Desk のサイトを作る。content/posts/*.md → public/

python scripts/build.py           # public/ を作り直す
python scripts/build.py --serve   # 作ったあと http://localhost:8790 で確認
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
CFG = yaml.safe_load((ROOT / "config" / "site.yaml").read_text(encoding="utf-8"))
SITE = CFG["site"]
CATS = CFG["categories"]
CAT = {c["slug"]: c for c in CATS}
KIND = {"new": "海外の新作", "buy": "まとめ"}
CSS_VER = int((ROOT / "assets" / "cozy.css").stat().st_mtime)  # 直したら古い見た目が残らないように
FONTS = "https://fonts.googleapis.com/css2?family=DM+Mono:wght@400&family=Noto+Sans+JP:wght@400;500;700&family=Zen+Maru+Gothic:wght@700;900&display=swap"

# 種類のアイコン(線画)。一覧とページの見出しで使う
ICON = {
    "desk": '<path d="M6 18h36v4H6zM9 22v16M39 22v16M30 22v10h9"/>',
    "chair": '<path d="M15 8h18v16H15zM12 26h24M24 26v8M14 40l10-6 10 6M24 34v6"/>',
    "pc": '<path d="M13 5h22v38H13zM13 11h22"/><circle cx="24" cy="21" r="4.5"/><circle cx="24" cy="33" r="4.5"/>',
    "monitor": '<path d="M6 9h36v24H6zM24 33v6M15 40h18"/>',
    "mouse": '<path d="M24 6c-7 0-11 5-11 12v12c0 7 5 12 11 12s11-5 11-12V18c0-7-4-12-11-12zM24 6v12M13 18h22"/>',
    "keyboard": '<path d="M5 15h38v20H5zM11 21h2M17 21h2M23 21h2M29 21h2M35 21h2M11 27h2M35 27h2M17 29h14"/>',
    "speaker": '<path d="M14 6h20v36H14z"/><circle cx="24" cy="29" r="6"/><circle cx="24" cy="14" r="1.5"/>',
    "gear": '<path d="M10 28a14 14 0 0 1 28 0M8 28h6v10H8zM34 28h6v10h-6z"/>',
    "interior": '<path d="M16 30h16l-2 12H18zM24 30V18M24 20c-6-2-9-7-8-12 5 1 8 5 8 12zM24 22c5-3 10-3 12 1-4 3-8 3-12-1z"/>',
}


def icon(slug: str) -> str:
    return (f'<svg viewBox="0 0 48 48" aria-hidden="true" fill="none" stroke="currentColor" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{ICON[slug]}</svg>')


def e(s) -> str:
    return html.escape(str(s or ""), quote=True)


# ── 記事を読む ──────────────────────────────────────────────

def load_posts() -> list[dict]:
    posts = []
    for path in sorted((ROOT / "content" / "posts").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            sys.exit(f"front matter がない: {path.name}")
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        for key in ("title", "date", "category", "kind", "summary"):
            if not meta.get(key):
                sys.exit(f"{path.name}: {key} がない")
        if meta["category"] not in CAT:
            sys.exit(f"{path.name}: 種類 {meta['category']} は config にない")
        if meta["kind"] not in KIND:
            sys.exit(f"{path.name}: kind は new か buy")
        if meta.get("draft"):
            continue
        meta["slug"] = path.stem
        meta["url"] = f"/p/{path.stem}/"
        meta["date"] = meta["date"] if isinstance(meta["date"], dt.date) else dt.date.fromisoformat(str(meta["date"]))
        meta["html"] = markdown.markdown(body, extensions=["tables", "attr_list"])
        posts.append(meta)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


# ── 買う所へのリンク ────────────────────────────────────────

STORES = [
    ("rakuten", "楽天で見る", "https://search.rakuten.co.jp/search/mall/{q}/"),
    ("amazon", "Amazon で見る", "https://www.amazon.co.jp/s?k={q}"),
    ("yahoo", "Yahoo!ショッピングで見る", "https://shopping.yahoo.co.jp/search?p={q}"),
]
AFF = CFG.get("affiliate") or {}
HAS_AFF = any(AFF.get(k) for k, _, _ in STORES)


def store_buttons(q: str, where: str, only: list[str] | None = None) -> str:
    out = []
    stores = [s for s in STORES if not only or s[0] in only]
    if only and not stores:
        sys.exit(f"stores の名前が違う: {only}(rakuten / amazon / yahoo)")
    for i, (key, label, base) in enumerate(stores):
        url = base.replace("{q}", quote(q, safe=""))
        tmpl = AFF.get(key) or ""
        attrs = ""
        if tmpl:
            url = tmpl.replace("{url}", quote(url, safe=""))
            attrs = ' rel="sponsored noopener"'
        out.append(f'<a class="btn{" buy" if i == 0 else ""}" href="{e(url)}" target="_blank"{attrs} '
                   f'data-store="{key}" data-where="{e(where)}">{label}</a>')
    return '<div class="btns">' + "".join(out) + "</div>"


def first_store(it: dict, where: str) -> tuple[str, str, str]:
    """(URL, aタグの追加属性, 「楽天」などの短い店の名前)。その物を売っている最初の店"""
    key, label, base = next(st for st in STORES if not it.get("stores") or st[0] in it["stores"])
    url = base.replace("{q}", quote(it.get("q") or it["name"], safe=""))
    attrs = f' target="_blank" data-store="{key}" data-where="{e(where)}"'
    if AFF.get(key):
        url = AFF[key].replace("{url}", quote(url, safe=""))
        attrs += ' rel="sponsored noopener"'
    return url, attrs, label.replace("で見る", "").replace("ショッピング", "").strip()


def mini_thumbs(html_: str, p: dict) -> str:
    """本文の書き込みを、物の写真つきの部品に置き換える。押すと売っている最初の店のページが開く
    (2026-11-02 本人「選び方の中にサムネイルを入れたい。クリックしたら購入リンク先に飛ぶように」「もっといい感じにまとめて」)
    - {{items:3,2}} … その番号の物の小さな写真を並べる
    - {{sizes ... }} … 1行に「札|見出し|説明|番号,番号」。大きさなどで分けた箱を横に並べ、物を写真・名前・大きさで1行ずつ出す
    - {{features ... }} … 1行に「見出し|説明|番号:特徴の文;番号:特徴の文」。分け方ごとの帯を縦に積み、物の札(写真・名前・長めの説明)を並べる
    - {{matrix ... }} … 1行目に列の名前「A|B|C」、2行目から「番号:○|説明|」(空=なし、○=あり、文=ありと一言)。物×できることの早見の表
    - {{cell:3}} … 比べ表の名前の欄に書く。小さな写真・短い名前・店のリンクになる
    - {{drops ... }} … 1行に「見出し|説明|番号,番号」。上から強い順の段に、しずくの印と物の丸い写真を並べる(水や汚れへの強さなど)"""
    prods = p.get("products") or []

    def item(n: int) -> dict:
        if not 1 <= n <= len(prods):
            sys.exit(f"{p['slug']}: 本文の物の番号 {n} がありません")
        return prods[n - 1]

    def one(n: int) -> str:
        it = item(n)
        url, attrs, short = first_store(it, p["slug"])
        img = f'<img src="{e(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if it.get("image") else ""
        return (f'<a class="mini" href="{e(url)}"{attrs} title="{e(it["name"])}を{e(short)}で見る">{img}<span>{e(short)}で見る</span></a>')

    def row(n: int) -> str:
        it = item(n)
        url, attrs, short = first_store(it, p["slug"])
        m = re.search(r"約?[\d.]+×[\d.]+×[\d.]+cm", it.get("jp") or "")
        size = f'<span class="sz-size">{e(m.group(0))}</span>' if m else ""
        img = f'<img src="{e(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if it.get("image") else ""
        return (f'<a class="sz-item" href="{e(url)}"{attrs}><span class="sz-img">{img}</span>'
                f'<span class="sz-txt"><span class="sz-name">{e(it.get("short") or it["name"])}</span>{size}</span>'
                f'<span class="sz-go">{e(short)}で見る</span></a>')

    def sizes(m: re.Match) -> str:
        cols = []
        for line in m.group(1).strip().splitlines():
            if not line.strip():
                continue
            tag, head, desc, nums = (x.strip() for x in line.split("|"))
            cols.append(f'<div class="sz-col"><div class="sz-head"><span class="sz-tag">{e(tag)}</span>'
                        f'<b>{e(head)}</b><p>{e(desc)}</p></div>'
                        + "".join(row(int(x)) for x in nums.split(",") if x.strip()) + "</div>")
        return f'<div class="sizes">{"".join(cols)}</div>'

    def features(m: re.Match) -> str:
        bands = []
        for line in m.group(1).strip().splitlines():
            if not line.strip():
                continue
            head, desc, rest = (x.strip() for x in line.split("|", 2))
            cards = []
            for part in rest.split(";"):
                num, _, text = part.partition(":")
                it = item(int(num))
                url, attrs, short = first_store(it, p["slug"])
                img = f'<img src="{e(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if it.get("image") else ""
                cls = "ft-card"
                if it.get("inside"):  # 中を開いた写真があれば大きく出し、外の写真は右下に小さく(2026-11-02 本人「中の仕切り画像はマスト」)
                    cls += " has-in"
                    img = (f'<img src="{e(it["inside"])}" alt="{e(it.get("short") or it["name"])}の中" loading="lazy" referrerpolicy="no-referrer">'
                           f'<span class="ft-out">{img}</span>')
                cards.append(f'<a class="{cls}" href="{e(url)}"{attrs}><span class="ft-img">{img}</span>'
                             f'<span class="ft-txt"><b>{e(it.get("short") or it["name"])}</b><span>{e(text.strip())}</span>'
                             f'<em>{e(short)}で見る</em></span></a>')
            bands.append(f'<div class="ft-band"><div class="ft-head"><b>{e(head)}</b><span>{e(desc)}</span>'
                         f'<i>{len(cards)}点</i></div><div class="ft-cards">{"".join(cards)}</div></div>')
        return f'<div class="features">{"".join(bands)}</div>'

    def thumb(it: dict) -> str:
        return f'<img src="{e(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if it.get("image") else ""

    def matrix(m: re.Match) -> str:
        lines = [x for x in m.group(1).strip().splitlines() if x.strip()]
        heads = [h.strip() for h in lines[0].split("|")]
        out = ['<div class="mx" style="--n:%d"><div class="mx-row mx-top"><span></span>' % len(heads)
               + "".join(f'<span class="mx-h">{e(h)}</span>' for h in heads) + "</div>"]
        for line in lines[1:]:
            num, _, cells = line.partition(":")
            it = item(int(num))
            url, attrs, short = first_store(it, p["slug"])
            vals = [c.strip() for c in cells.split("|")] + [""] * len(heads)
            tds = ""
            for h, v in zip(heads, vals):
                if not v:
                    tds += f'<span class="mx-c no" aria-label="{e(h)}: なし">-</span>'
                else:
                    note = "" if v == "○" else f'<small>{e(v)}</small>'
                    tds += f'<span class="mx-c yes"><i aria-label="{e(h)}">✓</i>{note}</span>'
            out.append(f'<a class="mx-row" href="{e(url)}"{attrs}><span class="mx-name"><span class="mx-img">{thumb(it)}</span>'
                       f'<span><b>{e(it.get("short") or it["name"])}</b><em>{e(short)}で見る</em></span></span>{tds}</a>')
        return "".join(out) + "</div>"

    def drops(m: re.Match) -> str:
        rows = []
        for k, line in enumerate(x for x in m.group(1).strip().splitlines() if x.strip()):
            head, desc, nums = (x.strip() for x in line.split("|"))
            items_ = []
            for x in nums.split(","):
                it = item(int(x))
                url, attrs, short = first_store(it, p["slug"])
                items_.append(f'<a class="dp-item" href="{e(url)}"{attrs} title="{e(it["name"])}を{e(short)}で見る">'
                              f'<span class="dp-img">{thumb(it)}</span><span>{e(it.get("short") or it["name"])}</span></a>')
            rows.append(f'<div class="dp-row lv{k}"><span class="dp-icon" aria-hidden="true"><i></i></span>'
                        f'<div class="dp-txt"><b>{e(head)}</b><p>{e(desc)}</p></div><div class="dp-items">{"".join(items_)}</div></div>')
        return f'<div class="drops">{"".join(rows)}</div>'

    def cell(m: re.Match) -> str:  # 比べ表の名前の欄。小さな写真・短い名前・店のリンク
        it = item(int(m.group(1)))
        url, attrs, short = first_store(it, p["slug"])
        return (f'<a class="tb-item" href="{e(url)}"{attrs}><span class="tb-img">{thumb(it)}</span>'
                f'<span><b>{e(it.get("short") or it["name"])}</b><em>{e(short)}で見る</em></span></a>')

    html_ = re.sub(r"\{\{cell:(\d+)\}\}", cell, html_)
    html_ = re.sub(r"<p>\{\{matrix\s*(.*?)\}\}</p>", matrix, html_, flags=re.S)
    html_ = re.sub(r"<p>\{\{drops\s*(.*?)\}\}</p>", drops, html_, flags=re.S)
    html_ = re.sub(r"<p>\{\{sizes\s*(.*?)\}\}</p>", sizes, html_, flags=re.S)
    html_ = re.sub(r"<p>\{\{features\s*(.*?)\}\}</p>", features, html_, flags=re.S)
    return re.sub(r"\{\{items:([\d,\s]+)\}\}",
                  lambda m: '<span class="minis">' + "".join(one(int(x)) for x in m.group(1).split(",") if x.strip()) + "</span>",
                  html_)

def dots(colors, cls="dots") -> str:
    if not colors:
        return ""
    names = "、".join(c["name"] for c in colors)
    return (f'<span class="{cls}" aria-label="色: {e(names)}">'
            + "".join(f'<b style="background:{e(c["hex"])}"></b>' for c in colors) + "</span>")


# ── 外枠 ────────────────────────────────────────────────────

def nav(current: str = "") -> str:
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="/c/{c["slug"]}/"{cur if c["slug"] == current else ""}>{e(c["name"])}</a>'
        for c in CATS)
    return f'<nav class="cats" aria-label="種類で探す">{links}</nav>'


def page(*, title: str, desc: str, path: str, body: str, current: str = "", image: str = "", pr: bool = False) -> str:
    full = f"{title}｜{SITE['title']}" if title else f"{SITE['title']}｜{SITE['tagline']}"
    url = SITE["base_url"].rstrip("/") + path
    og = image or SITE["base_url"].rstrip("/") + "/assets/scene.jpg"
    extra = ""
    if SITE.get("search_console_verification"):
        extra += f'<meta name="google-site-verification" content="{e(SITE["search_console_verification"])}">\n'
    if SITE.get("cf_analytics_token"):
        extra += ("<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
                  f"data-cf-beacon='{{\"token\": \"{e(SITE['cf_analytics_token'])}\"}}'></script>\n")
    # GA4(2026-11-01)。X から来た人がどの記事を読み、紹介リンクへ進むかを見る。空なら出さない
    if SITE.get("analytics_id"):
        gid = e(SITE["analytics_id"])
        extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
                  "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
                  f"gtag('js',new Date());gtag('config','{gid}');</script>\n")
    year = dt.date.today().year
    years = f"{SITE['copyright_from']}" + (f"–{year}" if year > SITE["copyright_from"] else "")
    ad_note = "このサイトはアフィリエイト広告(Amazon・楽天・Yahoo!ショッピング)を含みます" if HAS_AFF else "Gadget Terminal の姉妹サイト"
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="{'article' if path.startswith('/p/') else 'website'}">
<meta property="og:site_name" content="{e(SITE['title'])}">
<meta property="og:title" content="{e(title or SITE['title'])}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(og)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@{e(SITE['x_account'])}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/assets/cozy.css?v={CSS_VER}">
{extra}</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="logo" href="/"><b>cozy<i></i>desk</b><span>{e(SITE['tagline'])}</span></a>
    {nav(current)}
  </div>
</header>
{body}
<footer>
  <div class="wrap">
    <span>© {years} {e(SITE['title'])} ・ <a href="/tools/desk-size/">机の横幅を図で確かめる</a> ・ <a href="/tools/my-desk/">デスクを組んでみる</a> ・ <a href="/about/">このサイトについて</a> ・ <a href="https://x.com/{e(SITE['x_account'])}">X @{e(SITE['x_account'])}</a></span>
    <span>{ad_note}</span>
  </div>
</footer>
</body>
</html>
"""


# ── 部品 ────────────────────────────────────────────────────

def img_tag(p: dict) -> str:
    if not p.get("thumbnail"):
        return icon(p["category"])
    return f'<img src="{e(p["thumbnail"])}" alt="{e(p.get("thumbnail_alt") or p["title"])}" loading="lazy" referrerpolicy="no-referrer">'


def thumb(p: dict) -> str:
    cls = "img" + (" fit" if p.get("thumb_fit") else "") + ("" if p.get("thumbnail") else " noimg")
    return f'<div class="{cls}">{img_tag(p)}</div>'


def post_card(p: dict, cls: str = "") -> str:
    meta = f'{CAT[p["category"]]["name"]} ・ {KIND[p["kind"]]}'
    if p.get("price"):
        meta += f' ・ {e(p["price"])}'
    return (f'<a class="post {cls}" href="{p["url"]}">{dots(p.get("colors"))}{thumb(p)}'
            f'<div class="body"><span class="kind">{meta}</span><h3>{e(p["title"])}</h3></div></a>')


# 色の名前はメーカーごとにばらばらなので、hex から「色で選ぶ」の系統を決める。tone: を書けばそちらを使う
TONES = ["白", "グレー", "ベージュ", "ピンク", "パープル", "ブルー", "グリーン", "黒・こげ茶"]


def tone(c: dict) -> str:
    if c.get("tone"):
        return c["tone"]
    h = c["hex"].lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    hi, lo = max(r, g, b), min(r, g, b)
    light = (hi + lo) / 510
    if light < 0.3:
        return "黒・こげ茶"
    if hi - lo < 22:
        return "白" if light > 0.86 else "グレー"
    if hi == r:
        hue = (60 * (g - b) / (hi - lo)) % 360
    elif hi == g:
        hue = 60 * (b - r) / (hi - lo) + 120
    else:
        hue = 60 * (r - g) / (hi - lo) + 240
    if hue >= 330 or hue < 15:
        return "ピンク"
    if hue < 65:
        return "ベージュ"
    if hue < 170:
        return "グリーン"
    if hue < 250:
        return "ブルー"
    return "パープル"


def products_in(slug: str, posts: list[dict]) -> list[dict]:
    """その種類の物を、全部の記事から集める。同じ物は、その種類の記事に載っている方を残す"""
    found: dict[str, dict] = {}
    for p in posts:
        for i, it in enumerate(p.get("products") or [], 1):
            if (it.get("category") or p["category"]) != slug:
                continue
            row = {**it, "url": f'{p["url"]}#item-{i}', "from": p["title"], "home": p["category"] == slug}
            if it["name"] not in found or (row["home"] and not found[it["name"]]["home"]):
                found[it["name"]] = row
        if p["kind"] == "new" and p["category"] == slug:
            found[p["title"]] = {"name": p["title"], "image": p.get("thumbnail"), "price": p.get("price"),
                                 "colors": p.get("colors"), "url": p["url"], "from": "海外の新作", "home": True}
    return list(found.values())


# 種類ページの「〜で選ぶ」の軸。site.yaml の categories に facets: を書いた種類はそれを使い(デスクは横幅と形)、
# 書いていない種類は色。物の側は products の facets: {width: 160cm以上, shape: 昇降} のように書く
TONE_FACET = {"key": "tone", "name": "色", "values": TONES}


def facets_of(c: dict) -> list[dict]:
    return c.get("facets") or [TONE_FACET]


def facet_values(it: dict, f: dict) -> list[str]:
    if f["key"] == "tone":
        return sorted({tone(c) for c in it.get("colors") or []}, key=TONES.index)
    v = (it.get("facets") or {}).get(f["key"])
    vals = v if isinstance(v, list) else ([v] if v else [])
    bad = [x for x in vals if x not in f["values"]]
    if bad:
        sys.exit(f'{it["name"]}: facets.{f["key"]} の値 {bad} は site.yaml に無い(使えるのは {f["values"]})')
    return vals


def prodcard(it: dict, facets: list[dict]) -> str:
    attrs = "".join(f' data-f-{f["key"]}="{e(" ".join(facet_values(it, f)))}"' for f in facets)
    img = (f'<img src="{e(it["image"])}" alt="{e(it["name"])}" loading="lazy" referrerpolicy="no-referrer">'
           if it.get("image") else "")
    colors = "".join(f'<i style="background:{e(c["hex"])}" title="{e(c["name"])}"></i>' for c in it.get("colors") or [])
    # 一覧では「6,990円」だけにして、カードの高さをそろえる。どこの値段かは記事の中に書いてある
    price = f'<span class="price">{e(it["price"].split("(")[0])}</span>' if it.get("price") else ""
    return (f'<a class="pcard prod" href="{e(it["url"])}"{attrs}>'
            f'<div class="img fit{"" if img else " noimg"}">{img}</div>'
            f'<div class="body"><h3>{e(it["name"])}</h3><div class="meta">{price}{colors}</div>'
            f'<span class="jpnote">{e(it["from"])}</span></div></a>')


def pcard(p: dict) -> str:
    badge = f'<span class="badge">{KIND[p["kind"]]}</span>'
    price = f'<span class="price">{e(p["price"])}</span>' if p.get("price") else ""
    colors = "".join(f'<i style="background:{e(c["hex"])}" title="{e(c["name"])}"></i>' for c in p.get("colors") or [])
    return (f'<a class="pcard" href="{p["url"]}" data-f-kind="{p["kind"]}">'
            f'<div class="img{" fit" if p.get("thumb_fit") else ""}{"" if p.get("thumbnail") else " noimg"}">{badge}{img_tag(p)}</div>'
            f'<div class="body"><h3>{e(p["title"])}</h3><div class="meta">{price}{colors}</div>'
            f'<span class="jpnote">{e(p["summary"])}</span></div></a>')


# ── ページ ──────────────────────────────────────────────────

def build_index(posts: list[dict]) -> str:
    sc = CFG["scene"]
    pts = "\n".join(
        f'<a class="hs{" left" if pt.get("left") else ""}" href="/c/{pt["cat"]}/" style="left:{pt["x"]}%;top:{pt["y"]}%">'
        f'<span class="pin"></span><span class="lab">{e(pt["label"])}</span></a>' for pt in sc["points"])
    count = {c["slug"]: 0 for c in CATS}
    for p in posts:
        count[p["category"]] += 1
    cats = "\n".join(
        f'<a class="cat8" href="/c/{c["slug"]}/">{icon(c["slug"])}<span><b>{e(c["name"])}</b>'
        f'<small>{e(c["sub"])}</small></span></a>' for c in CATS)
    small_cats = "".join(f'<a href="/c/{c["slug"]}/">{e(c["name"])}</a>' for c in CATS)
    sizes = ["big", "", "", "wide", "", ""]
    latest = "\n".join(post_card(p, sizes[i] if i < len(sizes) else "") for i, p in enumerate(posts[:6]))
    body = f"""<main>
  <section class="scene-sec">
    <div class="wrap">
      <div class="scene photo">
        <div class="scene-copy">
          <span class="eyebrow">٭ 白でそろえる机</span>
          <p class="hero-logo">cozy<i></i>desk</p>
          <h1>白と淡い色の、<br>デスク周りのガジェット</h1>
          <p class="hint">気になる物を、絵の中で押してみて。</p>
        </div>
        <div class="stage">
          <img src="/assets/{e(sc['image'])}" width="{sc['width']}" height="{sc['height']}" alt="{e(sc['alt'])}">
{pts}
        </div>
      </div>
      <nav class="scene-cats" aria-label="種類で探す">{small_cats}</nav>
    </div>
  </section>

  <section class="sec" aria-labelledby="h-cats">
    <div class="wrap">
      <div class="sec-h"><h2 id="h-cats">種類で探す</h2><small>白・淡い色のものだけを集めています</small></div>
      <div class="cats8">
{cats}
      </div>
    </div>
  </section>

  <section class="sec" aria-labelledby="h-new">
    <div class="wrap">
      <div class="sec-h"><h2 id="h-new">新着</h2><small>海外の新作と、選んで集めたもの</small></div>
      <div class="bento">
{latest}
      </div>
    </div>
  </section>

  <section class="sec" aria-labelledby="h-tools">
    <div class="wrap">
      <div class="sec-h"><h2 id="h-tools">迷ったら</h2><small>机の大きさを図で確かめる・自分のデスクを組んでみる</small></div>
      {tool_cards()}
    </div>
  </section>
</main>"""
    return page(title="", desc=SITE["description"], path="/", body=body)


def build_category(c: dict, posts: list[dict]) -> str:
    mine = [p for p in posts if p["category"] == c["slug"]]
    items = products_in(c["slug"], posts)
    if mine or items:
        grid = ""
        if items:
            facets = facets_of(c)
            chips = ""
            if len(items) > 1:
                for f in facets:
                    have = {v for it in items for v in facet_values(it, f)}
                    if len(have) > 1:
                        chips += (f'<div class="filters" role="group" aria-label="{e(f["name"])}で選ぶ" data-for="prod" data-facet="{f["key"]}">'
                                  f'<span class="flabel">{e(f["name"])}</span><button class="on" data-k="all">すべて</button>'
                                  + "".join(f'<button data-k="{e(v)}">{e(v)}</button>' for v in f["values"] if v in have) + "</div>")
            head = "・".join(f["name"] for f in facets) + "で選ぶ" if chips else "載っている物"
            grid += (f'<section class="cat-sec"><div class="sec-h"><h2>{e(head)}</h2><small>{len(items)}点</small></div>'
                     f'{chips}<div class="grid3" data-list="prod">' + "\n".join(prodcard(it, facets) for it in items)
                     + '</div><p class="empty-tone" hidden>この条件の物は、いま載っていません。</p></section>')
        if mine:
            kinds = sorted({p["kind"] for p in mine})
            chips = ""
            if len(kinds) > 1:
                chips = ('<div class="filters" role="group" aria-label="記事の種類" data-for="post" data-facet="kind">'
                         '<button class="on" data-k="all">すべて</button>'
                         + "".join(f'<button data-k="{k}">{KIND[k]}</button>' for k in kinds) + "</div>")
            grid += ('<section class="cat-sec"><div class="sec-h"><h2>記事</h2></div>' + chips
                     + '<div class="grid3" data-list="post">' + "\n".join(pcard(p) for p in mine) + "</div></section>")
    else:
        grid = ('<div class="empty"><p>この種類の記事は、いま準備しています。</p>'
                '<p>ほかの種類から、白と淡い色の物を見てみてください。</p>'
                '<div class="btns">' + "".join(f'<a class="btn" href="/c/{x["slug"]}/">{e(x["name"])}</a>'
                                              for x in CATS if x["slug"] != c["slug"]) + "</div></div>")
    body = f"""<main class="sec">
  <div class="wrap">
    <div class="crumb"><a href="/">トップ</a> / {e(c['name'])}</div>
    <div class="cat-hero">
      {icon(c['slug'])}
      <div>
        <span class="eyebrow">٭ {e(c['name'])}</span>
        <h1>白・淡い色の{e(c['name'])}</h1>
        <p>{e(c['lead'])}色の名前と値段、日本で使えるかを確かめて載せています。</p>
      </div>
    </div>
    {SIZE_LINK if c["slug"] == "desk" else ""}
    {grid}
  </div>
</main>
<script>
// 軸(色・横幅・形…)ごとにボタンの列があり、全部の列の条件を満たす物だけ見せる
document.querySelectorAll('.filters').forEach(f => f.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {{
  f.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
  const groups = [...document.querySelectorAll('.filters[data-for="' + f.dataset.for + '"]')];
  const list = document.querySelector('[data-list="' + f.dataset.for + '"]');
  let shown = 0;
  list.querySelectorAll('.pcard').forEach(c => {{
    const hit = groups.every(g => {{
      const k = g.querySelector('button.on').dataset.k;
      return k === 'all' || (c.getAttribute('data-f-' + g.dataset.facet) || '').split(' ').includes(k);
    }});
    c.hidden = !hit; shown += hit;
  }});
  const none = list.parentElement.querySelector('.empty-tone');
  if (none) none.hidden = shown > 0;
}})));
</script>"""
    return page(title=f"白・淡い色の{c['name']}", desc=f"白デスク・淡色デスクに合う、{c['lead']}", path=f"/c/{c['slug']}/",
                body=body, current=c["slug"])


def decorate_guide(html_: str) -> str:
    """商品の下の「買う前に見る所」の見出しに飾りをつける(2026-11-01 本人「文字ばっかりだから、タイトルにあしらいを」)。
    「選び方1: …」は番号の札＋見出し、「Nつを比べる」は「比べ表」の札、「買う前に見る所」は帯にする"""
    steps = len(re.findall(r"<h2>選び方\d+[:：]", html_))
    html_ = re.sub(r"<h2>選び方(\d+)[:：]\s*(.*?)</h2>",
                   r'<h2 class="step"><span class="step-n">選び方 <b>\1</b></span><span class="step-t">\2</span></h2>', html_)
    html_ = re.sub(r"<h2>(\d+)\s*つを比べる</h2>",
                   r'<h2 class="step"><span class="step-n">比べ表</span><span class="step-t">\1つを比べる</span></h2>', html_)
    sub = f"選び方{steps}つと、比べ表" if steps else "選び方と比べ表"
    html_ = html_.replace('<h2 id="erabikata">買う前に見る所</h2>',
                          f'<div class="guide-head" id="erabikata"><span class="eyebrow">٭ 失敗しないために</span>'
                          f'<h2>買う前に見る所</h2><p>{sub}</p></div>')
    return html_


TAPES = ["#F3C9D1", "#CFE0E8", "#E8DCC8", "#D9E5CF"]
TILTS = [-5, 4, -3, 5, 4, -6, 7, -4, 3, -2, 6, -5]
JIT_X = [0.0, 1.2, -0.8, 0.6, -1.0, 0.9, -0.5, 1.1, -1.2, 0.4, -0.7, 0.8]
JIT_Y = [0.0, -1.5, 1.2, -0.6, 1.4, -1.0, 0.8, -1.3, 0.5, 1.1, -0.9, 0.3]


def board_words(p: dict) -> tuple[str, str]:
    """看板の札の文字(小さい行, 大きい行)。記事の board: {lead, title} があればそれを使う"""
    b = p.get("board") or {}
    if b.get("title"):
        return b.get("lead", ""), b["title"]
    t = p["title"]
    if "。" in t:
        lead, _, big = t.partition("。")
        return lead, big
    return CAT[p["category"]]["name"], t


def note_board(p: dict, shots: list) -> str:
    """まとめ記事の看板。方眼ノートに写真をマスキングテープで貼った形(2026-11-02 本人が見本3案から選んだ)。
    物の数から、上の段と下の段に分けて、置き場所と傾きを自動で決める。真ん中に題の札。押すとその物へ飛ぶ"""
    n = len(shots)
    rows = [shots[: (n + 1) // 2], shots[(n + 1) // 2:]]
    cards = []
    k_all = 0
    for r, row in enumerate(rows):
        k = len(row)
        slot = 96 / max(k, 1)
        w = min(21.0, slot - 1.8)
        for j, (i, it) in enumerate(row):
            x = 2 + j * slot + (slot - w) / 2 + JIT_X[k_all % 12]
            y = 5 + JIT_Y[k_all % 12] if r == 0 else 5 - JIT_Y[k_all % 12]
            pos = f"top:{y:.1f}%" if r == 0 else f"bottom:{y:.1f}%"
            cards.append(
                f'<a class="nb-card" href="#item-{i}" title="{e(it["name"])}" '
                f'style="left:{x:.1f}%;{pos};width:{w:.1f}%;--tilt:{TILTS[k_all % 12]}deg;--tape:{TAPES[k_all % 4]}">'
                f'<img src="{e(it["image"])}" alt="{e(it["name"])}" referrerpolicy="no-referrer"></a>')
            k_all += 1
    lead, big = board_words(p)
    credits = "・".join(dict.fromkeys(it.get("image_credit") for _, it in shots if it.get("image_credit")))
    return (f'<figure class="board note">{"".join(cards)}'
            f'<div class="nb-label"><small>{e(lead)}</small><b>{e(big)}</b></div></figure>'
            f'<p class="credit">画像: {e(credits)}</p>')


def build_post(p: dict, posts: list[dict]) -> str:
    c = CAT[p["category"]]
    fig = ""
    shots = [(i, it) for i, it in enumerate(p.get("products") or [], 1) if it.get("image")][:12]
    if p.get("board_style") == "note" and len(shots) >= 3:  # 記事ごとに選ぶ(11/2 本人「とりあえずガジェットポーチだけ」)
        fig = note_board(p, shots)
    elif p.get("thumbnail"):
        fig = (f'<figure class="board{" fit" if p.get("thumb_fit") else ""}"><img src="{e(p["thumbnail"])}" '
               f'alt="{e(p.get("thumbnail_alt") or p["title"])}" referrerpolicy="no-referrer"></figure>'
               f'<p class="credit">画像: {e(p.get("thumbnail_credit"))}</p>')
    palette = ""
    if p.get("colors") and p["kind"] == "new":  # まとめ記事は物ごとに色を出すので、上には出さない
        palette = ('<h2>選べる色</h2><div class="palette">'
                   + "".join(f'<div><i style="background:{e(x["hex"])}"></i>{e(x["name"])}</div>' for x in p["colors"]) + "</div>")
    items = ""
    for i, it in enumerate(p.get("products") or [], 1):
        img = (f'<div class="it-img"><img src="{e(it["image"])}" alt="{e(it["name"])}" loading="lazy" referrerpolicy="no-referrer"></div>'
               if it.get("image") else f'<div class="it-img noimg">{icon(p["category"])}</div>')
        colors = "".join(f'<i style="background:{e(x["hex"])}" title="{e(x["name"])}"></i>' for x in it.get("colors") or [])
        cname = "・".join(x["name"] for x in it.get("colors") or [])
        credit = f'<p class="it-credit">画像: {e(it["image_credit"])}</p>' if it.get("image_credit") else ""
        items += f"""<section class="item" id="item-{i}">
  {img}
  <div class="it-body">
    <h3>{e(it['name'])}</h3>
    <div class="meta"><span class="price">{e(it.get('price'))}</span>{colors}<span>{e(cname)}</span></div>
    <p>{e(it.get('note'))}</p>
    <p class="jpnote">{e(it.get('jp'))}</p>
    {store_buttons(it.get('q') or it['name'], p['slug'], it.get('stores'))}
    {credit}
  </div>
</section>
"""
    if items:
        items = f'<div class="items-list">{items}</div>'
    # 本文に <!-- after-items --> があれば、そこから後ろ(選び方・比べ表など)を商品の下に出す。
    # 長い説明で商品が下に押しやられないように(2026-11-01 PCケースの記事で選び方を厚くしたとき)
    before, _, rest = mini_thumbs(p["html"], p).partition("<!-- after-items -->")
    after = f'<div class="prose guide">{decorate_guide(rest)}</div>' if rest.strip() else ""
    japan = ""
    if p.get("japan"):
        japan = f'<h2>日本で買える？使える？</h2><div class="jp">{markdown.markdown(p["japan"])}</div>'
    buy = ""
    if p.get("alt_q"):
        buy = (f'<div class="buybox"><h3>日本で今買える、近い色・形の{e(c["name"])}</h3>'
               f'<p>値段・在庫は各ストアで確かめてください。</p>{store_buttons(p["alt_q"], p["slug"])}</div>')
    srcs = ""
    if p.get("sources"):
        srcs = '<p class="src">出典: ' + " / ".join(
            f'<a href="{e(s["url"])}" rel="nofollow noopener" target="_blank">{e(s["name"])}</a>' for s in p["sources"]) + "。</p>"
    pr = '<span class="pr">この記事にはアフィリエイト広告を含みます</span>' if HAS_AFF and (items or buy) else ""
    more = [x for x in posts if x["category"] == p["category"] and x["slug"] != p["slug"]][:3]
    related = ""
    if more:
        related = ('<section class="sec related"><div class="wrap"><div class="sec-h"><h2>ほかの' + e(c["name"]) + '</h2></div>'
                   '<div class="grid3">' + "".join(pcard(x) for x in more) + "</div></div></section>")
    body = f"""<main class="article">
  <div class="wrap">
    <div class="crumb"><a href="/">トップ</a> / <a href="/c/{c['slug']}/">{e(c['name'])}</a></div>
    {pr}
    <h1>{e(p['title']).replace('。', '。<br class="br-pc">', 1) if p.get('title_break') else e(p['title'])}</h1>
    <p class="lead">{e(p['summary'])}</p>
    <p class="date">{KIND[p['kind']]} ・ {p['date'].isoformat()} 掲載</p>
    {fig}
    {palette}
    <div class="prose">{before}</div>
    {items}
    {after}
    {SIZE_LINK if p["category"] == "desk" else ""}
    {japan}
    {buy}
    {srcs}
  </div>
</main>
{related}"""
    img = p.get("thumbnail") or ""
    if img.startswith("/"):
        img = SITE["base_url"].rstrip("/") + img
    return page(title=p["title"], desc=p["summary"], path=p["url"], body=body, current=p["category"], image=img)


def build_about() -> str:
    aff = ("紹介しているストアへのリンクの一部はアフィリエイトリンク(もしもアフィリエイト経由の Amazon・楽天市場・Yahoo!ショッピング)です。"
           "リンクから買い物をされると、運営者に紹介料が入ることがあります。紹介料の有無で、載せる物や書く内容は変えません。"
           if HAS_AFF else "いまはストアへのリンクに紹介料はついていません。")
    analytics = ("<h2>アクセス解析について</h2><p>サイトの利用状況を知るため、Google社のアクセス解析(Google アナリティクス)を使っています。"
                 "Google アナリティクスは Cookie を使ってアクセス状況を集計します。氏名やメールアドレスなど個人を特定する情報は含まれません。"
                 "ブラウザの設定で Cookie を無効にすると、収集を拒否できます。"
                 '詳しくは<a href="https://policies.google.com/technologies/partner-sites?hl=ja">Google のポリシー</a>をご覧ください。</p>\n'
                 if SITE.get("analytics_id") else "")
    body = f"""<main class="article"><div class="wrap">
<h1>このサイトについて</h1>
<div class="prose">
<p>Cozy Desk は、白デスク・淡色デスクに合う、白と淡い色のガジェットを種類ごとに集めているサイトです。海外ガジェットの媒体 <a href="https://gadgetterminal.com/">Gadget Terminal</a> の姉妹サイトとして、同じ運営者が作っています。</p>
<h2>載せ方の決まり</h2>
<ul>
<li>色の名前・値段・大きさは、メーカーの公式ページで確かめたものだけを書きます。値段と在庫は掲載時点のものです</li>
<li>海外の新作は、日本に届くか、日本で安心して使えるかを、確かめられた範囲で書きます</li>
<li>製品の画像は、メーカー公式ページの画像を出典つきで載せています</li>
<li>使ってみた感想は書きません。編集部が実際に使った物ではないためです</li>
</ul>
<h2>広告について</h2>
<p>{aff}</p>
{analytics}<h2>運営</h2>
<p>{e(SITE['author'])} ・ お問い合わせ: {e(SITE['contact_email'])}</p>
</div></div></main>"""
    return page(title="このサイトについて", desc="Cozy Desk の載せ方の決まりと運営者", path="/about/", body=body)


# ── 道具(2026-11-01): 机の横幅を図で確かめる・自分のデスクを組む ──────────
# どちらも「迷い」に答えて、そのまま載せている物の買うボタンへつなぐためのもの

def price_yen(s: str | None) -> int | None:
    """「3万1,800円」「8万300円」「12,980円」→ 円の数。読めなければ None"""
    m = re.search(r"(?:(\d+)万)?([\d,]+)?円", s or "")
    if not m or not (m.group(1) or m.group(2)):
        return None
    return int(m.group(1) or 0) * 10000 + int((m.group(2) or "0").replace(",", "") or 0)


def item_id(name: str) -> str:
    # 共有アドレスに入れる短い名前。物の名前から作るので、記事を足しても変わらない
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]


def catalog(posts: list[dict]) -> list[dict]:
    """買うボタンが出せる物(日本で今買える物)を、種類の順に全部集める"""
    rows, seen = [], set()
    for c in CATS:
        for it in products_in(c["slug"], posts):
            if not it.get("q") or it["name"] in seen:
                continue
            seen.add(it["name"])
            rows.append({"id": item_id(it["name"]), "cat": c["slug"], "name": it["name"], "img": it.get("image") or "",
                         "price": (it.get("price") or "").split("(")[0], "yen": price_yen(it.get("price")),
                         "url": it["url"], "btns": store_buttons(it["q"], "my-desk", it.get("stores"))})
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        sys.exit("物の短い名前がかぶった(item_id)。桁を増やす")
    return rows


def tool_cards() -> str:
    return """<div class="tools2">
  <a class="tool-card" href="/tools/desk-size/"><span class="eyebrow">٭ 図で確かめる</span><b>机の横幅、何cmにする？</b>
    <small>モニターの大きさと台数、スピーカー、PC を選ぶと、机の上を縮尺どおりの図で見られます。</small></a>
  <a class="tool-card blush" href="/tools/my-desk/"><span class="eyebrow">٭ 組んでみる</span><b>白いデスクを、組んでみる</b>
    <small>載っている物から選ぶと、1枚に並んで合計の値段が出ます。組んだデスクは X に貼れます。</small></a>
</div>"""


def jdump(x) -> str:
    # <script> の中に置く JSON。</script> で切れないように < を逃がす
    return json.dumps(x, ensure_ascii=False).replace("<", "\\u003c")


def seg(key: str, label: str, opts: list[tuple[str, str]], on: str) -> str:
    return (f'<div class="filters seg" role="group" aria-label="{e(label)}" data-key="{key}"><span class="flabel">{e(label)}</span>'
            + "".join(f'<button type="button" data-v="{e(v)}" class="{"on" if v == on else ""}" aria-pressed="{"true" if v == on else "false"}">{e(t)}</button>'
                      for v, t in opts) + "</div>")


SIZE_LINK = ('<a class="size-link" href="/tools/desk-size/"><b>横幅で迷ったら</b>'
             '<span>モニターの大きさと台数を選ぶと、机の上を縮尺どおりの図で確かめられます</span></a>')


def build_desk_size(posts: list[dict]) -> str:
    wf = next(f for f in facets_of(CAT["desk"]) if f["key"] == "width")
    cards = "\n".join(prodcard(it, [wf]) for it in products_in("desk", posts))
    controls = "".join([
        seg("w", "横幅", [("100", "100cm"), ("120", "120cm"), ("140", "140cm"), ("160", "160cm"), ("180", "180cm")], "120"),
        seg("d", "奥行", [("60", "60cm"), ("70", "70cm"), ("80", "80cm")], "60"),
        seg("mon", "モニター", [("54", "24インチ"), ("61", "27インチ"), ("71", "32インチ"), ("81", "34インチ横長")], "61"),
        seg("n", "台数", [("1", "1台"), ("2", "2台")], "1"),
        seg("arm", "置き方", [("0", "付属の台"), ("1", "モニターアーム")], "0"),
        seg("spk", "スピーカー", [("0", "なし"), ("12", "小さめ"), ("15", "大きめ")], "12"),
        seg("pc", "PC 本体", [("0", "机の下・なし"), ("1", "机の上")], "0"),
        seg("kb", "キーボード", [("32", "小さめ"), ("36", "テンキーなし"), ("44", "テンキーつき")], "36"),
    ])
    js = r"""
(() => {
const S = {};
document.querySelectorAll('.seg').forEach(g => {
  S[g.dataset.key] = +g.querySelector('button.on').dataset.v;
  g.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    g.querySelectorAll('button').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); });
    S[g.dataset.key] = +b.dataset.v; draw();
  }));
});
const NS = 'http://www.w3.org/2000/svg', svg = document.getElementById('fig');
function el(tag, a, txt) { const n = document.createElementNS(NS, tag); for (const k in a) n.setAttribute(k, a[k]); if (txt != null) n.textContent = txt; svg.appendChild(n); return n; }
function box(x, y, w, h, cls, label) {
  el('rect', {x, y, width: w, height: h, rx: 1.2, class: cls});
  if (label) el('text', {x: x + w / 2, y: y + h / 2 + 1.1, class: 'lb', 'text-anchor': 'middle'}, label);
}
const INCH = {54: '24インチ', 61: '27インチ', 71: '32インチ', 81: '34インチ'};
function draw() {
  const W = S.w, D = S.d, M = 22, gap = 2;
  const monW = S.mon, n = S.n, spk = S.spk, pcW = 25, pcD = 45, kb = S.kb;
  const standD = S.arm ? 0 : 22;
  // 奥の列: スピーカー・モニター・スピーカーを真ん中に、PC は右の奥
  const mid = monW * n + (n - 1) + (spk ? (spk + gap) * 2 : 0);
  const pcUse = S.pc ? pcW + gap : 0;
  const free = W - mid - pcUse;
  // 手前の列: キーボード＋マウスの場所(25cm)。奥行が浅いと PC 本体の手前にかかる
  const frontNeed = kb + 5 + 25, frontAvail = W - (S.pc && D - pcD < 25 ? pcUse : 0);
  svg.setAttribute('viewBox', `0 0 ${W + M * 2} ${D + M * 2 + 6}`);
  svg.innerHTML = '';
  const X = M, Y = M;
  el('rect', {x: X, y: Y, width: W, height: D, rx: 2, class: 'desk'});
  el('line', {x1: X, y1: Y - 9, x2: X + W, y2: Y - 9, class: 'dim'});
  el('text', {x: X + W / 2, y: Y - 11.5, class: 'dimt', 'text-anchor': 'middle'}, `${W}cm`);
  el('line', {x1: X - 9, y1: Y, x2: X - 9, y2: Y + D, class: 'dim'});
  el('text', {x: X - 11.5, y: Y + D / 2, class: 'dimt', 'text-anchor': 'middle', transform: `rotate(-90 ${X - 11.5} ${Y + D / 2})`}, `${D}cm`);
  const areaW = W - pcUse;
  let cx = X + (areaW - mid) / 2;
  const over = free < 0 ? ' over' : '';
  const spkD = spk === 12 ? 12 : 18;
  if (spk) { box(cx, Y + 4, spk, spkD, 'thing' + over, ''); cx += spk + gap; }
  for (let i = 0; i < n; i++) {
    if (standD) box(cx + monW / 2 - 11, Y + 2, 22, standD - 2, 'stand', '');
    const sy = Y + (standD ? 9 : 3);
    box(cx, sy, monW, 3.2, 'screen' + over, '');
    el('text', {x: cx + monW / 2, y: sy + 9.5, class: 'lb', 'text-anchor': 'middle'}, INCH[monW]);
    cx += monW + 1;
  }
  if (spk) { cx += gap - 1; box(cx, Y + 4, spk, spkD, 'thing' + over, ''); }
  if (S.pc) box(X + W - pcW, Y, pcW, pcD, 'thing' + over, 'PC');
  if (S.arm) el('rect', {x: X + areaW / 2 - 6, y: Y - 1.5, width: 12, height: 4, rx: 1, class: 'clamp'});
  const fy = Y + D - 10 - 13, fx = X + (areaW - frontNeed) / 2 + 2;
  const fover = frontNeed > frontAvail ? ' over' : '';
  box(fx, fy, kb, 13, 'thing' + fover, 'キーボード');
  el('rect', {x: fx + kb + 5, y: fy - 3, width: 25, height: 20, rx: 2, class: 'pad'});
  el('ellipse', {cx: fx + kb + 17.5, cy: fy + 7, rx: 3.2, ry: 5.5, class: 'thing'});
  el('path', {d: `M ${X + areaW / 2 - 14} ${Y + D + 12} q 14 -9 28 0`, class: 'me'});
  el('text', {x: X + areaW / 2, y: Y + D + 19, class: 'lb mute', 'text-anchor': 'middle'}, 'ここに座る');
  // 読み取り
  const eye = D - (S.arm ? 8 : 12) + 15;
  const depthNeed = (standD || 6) + 4 + 13 + 10;
  const r = [];
  r.push(free >= 0 ? `<li class="ok"><b>横はあと ${free}cm 余ります。</b>${free >= 20 ? '小物やライトを置く余裕があります。' : 'ほぼぴったりです。'}</li>`
                   : `<li class="ng"><b>横が ${-free}cm 足りません。</b>横幅を広げるか、モニターかスピーカーを小さくします。${S.pc ? 'PC 本体を机の下に置くと、約27cm 空きます。' : ''}</li>`);
  if (fover) r.push(`<li class="ng"><b>手前も狭いです。</b>キーボードとマウスの場所が、PC 本体とぶつかります。</li>`);
  r.push(depthNeed <= D ? `<li class="ok"><b>奥行は足ります。</b>${S.arm ? 'モニターアームなら台の場所がいらず、手前が広く使えます。' : '付属の台は奥行を約22cm使います。'}</li>`
                        : `<li class="ng"><b>奥行が窮屈です。</b>付属の台をやめてモニターアームにすると、約22cm 空きます。</li>`);
  r.push(`<li><b>画面から目まで、およそ ${eye}cm。</b>厚生労働省の目安は40cm以上です。大きい画面ほど、離した方が端まで見渡しやすくなります。</li>`);
  document.getElementById('read').innerHTML = r.join('');
  // 合う机
  const bucket = W >= 160 ? '160cm以上' : W + 'cm前後';
  let shown = 0;
  document.querySelectorAll('#desks .pcard').forEach(c => {
    const hit = (c.getAttribute('data-f-width') || '').split(' ').includes(bucket);
    c.hidden = !hit; shown += hit;
  });
  document.getElementById('desk-h').textContent = `横幅 ${bucket}の白い机`;
  document.getElementById('desk-n').textContent = shown ? `${shown}点` : '';
  document.getElementById('desk-none').hidden = shown > 0;
  const more = [['/c/monitor/', S.arm ? '白いモニターアーム' : '白いモニター']];
  if (spk) more.push(['/c/speaker/', '白い PC スピーカー']);
  if (S.pc) more.push(['/c/pc/', '白い PC ケース']);
  more.push(['/c/keyboard/', '白いキーボード'], ['/c/mouse/', '白いマウス'], ['/c/chair/', '白い椅子']);
  document.getElementById('more').innerHTML = more.map(([u, t], i) => `<a class="btn${i ? '' : ' buy'}" href="${u}">${t}</a>`).join('');
}
draw();
})();
"""
    body = f"""<main class="sec tool">
  <div class="wrap">
    <div class="crumb"><a href="/">トップ</a> / 机の横幅を図で確かめる</div>
    <div class="tool-hero">
      <span class="eyebrow">٭ 図で確かめる</span>
      <h1>机の横幅、何cmにする？</h1>
      <p>机の大きさと、載せたい物を選ぶと、上から見た図を縮尺どおりに描きます。横にあと何cm余るか、画面から目までどのくらい離れるかも出します。</p>
    </div>
    <div class="sizer">
      <div class="sizer-ctl">{controls}</div>
      <div class="sizer-view">
        <div class="sizer-fig"><svg id="fig" role="img" aria-label="机を上から見た図"></svg></div>
        <ul class="sizer-read" id="read" aria-live="polite"></ul>
        <p class="sizer-note">大きさは、よくある物の目安です(24インチは幅約54cm、27インチは約61cm、32インチは約71cm、34インチの横長は約81cm)。買う物が決まったら、その物の寸法で確かめてください。</p>
      </div>
    </div>
    <section class="cat-sec">
      <div class="sec-h"><h2 id="desk-h">この横幅の白い机</h2><small id="desk-n"></small></div>
      <div class="grid3" id="desks">{cards}</div>
      <p class="empty-tone" id="desk-none" hidden>この横幅の机は、いま載っていません。<a href="/c/desk/">白い机を全部見る</a></p>
    </section>
    <section class="cat-sec">
      <div class="sec-h"><h2>図の物を、白でそろえるなら</h2></div>
      <div class="btns" id="more"></div>
    </section>
    <section class="cat-sec">{tool_cards()}</section>
  </div>
</main>
<script>{js}</script>"""
    return page(title="机の横幅、何cmにする？ 図で確かめる",
                desc="机の横幅と奥行、モニターの大きさと台数、スピーカー、PC を選ぶと、机の上を縮尺どおりの図で描きます。横の余りと、画面から目までの距離も出します。",
                path="/tools/desk-size/", body=body)


def build_my_desk(posts: list[dict]) -> str:
    rows = catalog(posts)
    have = [c for c in CATS if any(r["cat"] == c["slug"] for r in rows)]
    tabs = ('<div class="filters" role="group" aria-label="種類" id="tabs">'
            + "".join(f'<button type="button" data-k="{c["slug"]}" class="{"on" if i == 0 else ""}">{e(c["name"])}<span class="cnt" data-c="{c["slug"]}"></span></button>'
                      for i, c in enumerate(have)) + "</div>")
    cats = {c["slug"]: c["name"] for c in CATS}
    js = r"""
(() => {
const ITEMS = __ITEMS__;
const CATS = __CATS__;
const BY = Object.fromEntries(ITEMS.map(x => [x.id, x]));
let picked = (new URLSearchParams(location.search).get('d') || '').split('.').filter(id => BY[id]);
let tab = document.querySelector('#tabs button.on').dataset.k;
const yen = n => n.toLocaleString('ja-JP') + '円';
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[c]);
const pic = (x, alt) => x.img ? `<img src="${esc(x.img)}" alt="${alt}" loading="lazy" referrerpolicy="no-referrer">` : '';
function url() { return location.origin + location.pathname + (picked.length ? '?d=' + picked.join('.') : ''); }
function renderPick() {
  document.getElementById('pick').innerHTML = ITEMS.filter(x => x.cat === tab).map(x => `
    <button type="button" class="pk${picked.includes(x.id) ? ' on' : ''}" data-id="${x.id}" aria-pressed="${picked.includes(x.id)}">
      <span class="pk-img">${pic(x, '')}</span>
      <span class="pk-name">${esc(x.name)}</span><span class="pk-price">${esc(x.price)}</span><i class="pk-ok" aria-hidden="true"></i>
    </button>`).join('');
}
function render() {
  history.replaceState(null, '', url());
  const sel = picked.map(id => BY[id]);
  const sum = sel.reduce((a, x) => a + (x.yen || 0), 0);
  document.getElementById('sum').textContent = yen(sum);
  document.getElementById('cnt').textContent = sel.length ? sel.length + '点' : '';
  document.getElementById('board').innerHTML = sel.length ? sel.map(x => `
    <figure class="tile"><button type="button" class="rm" data-id="${x.id}" aria-label="${esc(x.name)} を外す">×</button>
      ${pic(x, esc(x.name))}<figcaption>${esc(CATS[x.cat])}</figcaption></figure>`).join('')
    : '<p class="tray-empty">一覧から選ぶと、ここに並びます。</p>';
  document.querySelectorAll('#tabs .cnt').forEach(s => { const k = sel.filter(x => x.cat === s.dataset.c).length; s.textContent = k ? ' ' + k : ''; });
  document.getElementById('buy-sec').hidden = !sel.length;
  document.getElementById('buylist').innerHTML = sel.map(x => `
    <div class="brow"><span class="brow-img">${pic(x, '')}</span>
      <div><b>${esc(x.name)}</b><span class="brow-meta"><span class="price">${esc(x.price)}</span> ・ <a href="${esc(x.url)}">記事で詳しく見る</a></span>${x.btns}</div></div>`).join('');
  const text = sel.length ? `白でそろえた私のデスク、${sel.length}点で合計${yen(sum)}` : '白いデスクを組んでみる';
  document.getElementById('share').href = 'https://x.com/intent/post?text=' + encodeURIComponent(text + ' #CozyDesk') + '&url=' + encodeURIComponent(url());
  document.getElementById('bar').hidden = !sel.length;
  document.getElementById('bar-t').textContent = `${sel.length}点 ・ 合計${yen(sum)}`;
  document.querySelectorAll('#pick .pk').forEach(b => { const on = picked.includes(b.dataset.id); b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
}
document.getElementById('tabs').addEventListener('click', ev => {
  const b = ev.target.closest('button'); if (!b) return;
  tab = b.dataset.k;
  document.querySelectorAll('#tabs button').forEach(x => x.classList.toggle('on', x === b));
  renderPick();
});
document.getElementById('pick').addEventListener('click', ev => {
  const b = ev.target.closest('.pk'); if (!b) return;
  const id = b.dataset.id;
  picked = picked.includes(id) ? picked.filter(x => x !== id) : [...picked, id];
  render();
});
document.getElementById('board').addEventListener('click', ev => {
  const b = ev.target.closest('.rm'); if (!b) return;
  picked = picked.filter(x => x !== b.dataset.id); render();
});
document.getElementById('clear').addEventListener('click', () => { picked = []; render(); });
document.getElementById('copy').addEventListener('click', async ev => {
  const b = ev.currentTarget;
  try { await navigator.clipboard.writeText(url()); b.textContent = 'コピーしました'; }
  catch (_) { b.textContent = 'コピーできませんでした'; }
  setTimeout(() => b.textContent = 'アドレスをコピー', 1800);
});
renderPick();
render();
})();
""".replace("__ITEMS__", jdump(rows)).replace("__CATS__", jdump(cats))
    body = f"""<main class="sec tool">
  <div class="wrap">
    <div class="crumb"><a href="/">トップ</a> / 白いデスクを組んでみる</div>
    <div class="tool-hero">
      <span class="eyebrow">٭ 組んでみる</span>
      <h1>白いデスクを、組んでみる</h1>
      <p>このサイトに載っている物から、気になる物を選んでください。選んだ物が1枚に並び、合計の値段と、買えるお店が出ます。組んだデスクは、アドレスをそのまま X に貼れます。</p>
    </div>
    <div class="mydesk">
      <div class="picker">
        {tabs}
        <div class="pick-grid" id="pick"></div>
      </div>
      <aside class="tray" id="tray" aria-labelledby="tray-h">
        <div class="tray-head"><h2 id="tray-h">私のデスク</h2><span id="cnt"></span></div>
        <div class="tray-board" id="board"></div>
        <div class="tray-sum"><span>合計</span><b id="sum">0円</b></div>
        <p class="tray-note">掲載時点の値段の合計です。セールなどで変わります。</p>
        <div class="tray-act">
          <a class="btn buy" id="share" href="#" target="_blank" rel="noopener">X に貼る</a>
          <button type="button" class="btn" id="copy">アドレスをコピー</button>
          <button type="button" class="btn" id="clear">空にする</button>
        </div>
      </aside>
    </div>
    <section class="cat-sec" id="buy-sec" hidden>
      <div class="sec-h"><h2>選んだ物を買うなら</h2><small>売っているお店のボタンだけ出しています</small></div>
      <div class="buylist" id="buylist"></div>
    </section>
    <section class="cat-sec">{tool_cards()}</section>
  </div>
</main>
<a class="tray-bar" id="bar" href="#tray" hidden><span id="bar-t"></span><b>見る</b></a>
<script>{js}</script>"""
    return page(title="白いデスクを、組んでみる",
                desc="Cozy Desk に載っている白と淡い色のガジェットから選んで、自分のデスクを組めます。選んだ物が1枚に並び、合計の値段と買えるお店が出ます。",
                path="/tools/my-desk/", body=body)


# ── 書き出し ────────────────────────────────────────────────

def write(rel: str, text: str) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    posts = load_posts()
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    write("index.html", build_index(posts))
    for c in CATS:
        write(f"c/{c['slug']}/index.html", build_category(c, posts))
    for p in posts:
        write(f"p/{p['slug']}/index.html", build_post(p, posts))
    write("tools/desk-size/index.html", build_desk_size(posts))
    write("tools/my-desk/index.html", build_my_desk(posts))
    write("about/index.html", build_about())
    write("404.html", page(title="ページが見つかりません", desc="", path="/404.html",
                           body='<main class="article"><div class="wrap"><h1>ページが見つかりません</h1>'
                                '<p><a href="/">トップへ戻る</a></p></div></main>'))
    base = SITE["base_url"].rstrip("/")
    urls = ["/", "/about/", "/tools/desk-size/", "/tools/my-desk/"] + [f"/c/{c['slug']}/" for c in CATS] + [p["url"] for p in posts]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    write("CNAME", base.split("://", 1)[1] + "\n")
    print(f"記事 {len(posts)} 本・種類 {len(CATS)} ・ public/ に書き出した")

    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("http://localhost:8790")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8790), handler).serve_forever()


if __name__ == "__main__":
    main()
