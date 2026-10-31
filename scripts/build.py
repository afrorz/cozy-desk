"""Cozy Desk のサイトを作る。content/posts/*.md → public/

python scripts/build.py           # public/ を作り直す
python scripts/build.py --serve   # 作ったあと http://localhost:8790 で確認
"""
from __future__ import annotations

import datetime as dt
import html
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
KIND = {"new": "海外の新作", "buy": "日本で今買える"}
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
    <span>© {years} {e(SITE['title'])} ・ <a href="/about/">このサイトについて</a> ・ <a href="https://x.com/{e(SITE['x_account'])}">X @{e(SITE['x_account'])}</a></span>
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


def prodcard(it: dict) -> str:
    tones = sorted({tone(c) for c in it.get("colors") or []}, key=TONES.index)
    img = (f'<img src="{e(it["image"])}" alt="{e(it["name"])}" loading="lazy" referrerpolicy="no-referrer">'
           if it.get("image") else "")
    colors = "".join(f'<i style="background:{e(c["hex"])}" title="{e(c["name"])}"></i>' for c in it.get("colors") or [])
    price = f'<span class="price">{e(it["price"])}</span>' if it.get("price") else ""
    return (f'<a class="pcard prod" href="{e(it["url"])}" data-tones="{" ".join(tones)}">'
            f'<div class="img fit{"" if img else " noimg"}">{img}</div>'
            f'<div class="body"><h3>{e(it["name"])}</h3><div class="meta">{price}{colors}</div>'
            f'<span class="jpnote">{e(it["from"])}</span></div></a>')


def pcard(p: dict) -> str:
    badge = f'<span class="badge">{KIND[p["kind"]]}</span>'
    price = f'<span class="price">{e(p["price"])}</span>' if p.get("price") else ""
    colors = "".join(f'<i style="background:{e(c["hex"])}" title="{e(c["name"])}"></i>' for c in p.get("colors") or [])
    return (f'<a class="pcard" href="{p["url"]}" data-kind="{p["kind"]}">'
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
      <div class="sec-h"><h2 id="h-new">新着</h2><small>海外の新作と、日本で今買えるもの</small></div>
      <div class="bento">
{latest}
      </div>
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
            have = {t for it in items for c2 in it.get("colors") or [] for t in [tone(c2)]}
            chips = ""
            if len(have) > 1:
                chips = ('<div class="filters" role="group" aria-label="色で選ぶ" data-for="prod">'
                         '<button class="on" data-k="all">すべての色</button>'
                         + "".join(f'<button data-k="{t}">{t}</button>' for t in TONES if t in have) + "</div>")
            grid += (f'<section class="cat-sec"><div class="sec-h"><h2>色で選ぶ</h2><small>{len(items)}点</small></div>'
                     f'{chips}<div class="grid3" data-list="prod">' + "\n".join(prodcard(it) for it in items)
                     + '</div><p class="empty-tone" hidden>この色の物は、いま載っていません。</p></section>')
        if mine:
            kinds = sorted({p["kind"] for p in mine})
            chips = ""
            if len(kinds) > 1:
                chips = ('<div class="filters" role="group" aria-label="記事の種類" data-for="post">'
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
    {grid}
  </div>
</main>
<script>
document.querySelectorAll('.filters').forEach(f => f.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {{
  f.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
  const k = b.dataset.k, list = document.querySelector('[data-list="' + f.dataset.for + '"]');
  let shown = 0;
  list.querySelectorAll('.pcard').forEach(c => {{
    const hit = k === 'all' || (f.dataset.for === 'prod' ? c.dataset.tones.split(' ').includes(k) : c.dataset.kind === k);
    c.hidden = !hit; shown += hit;
  }});
  const none = list.parentElement.querySelector('.empty-tone');
  if (none) none.hidden = shown > 0;
}})));
</script>"""
    return page(title=f"白・淡い色の{c['name']}", desc=f"白デスク・淡色デスクに合う、{c['lead']}", path=f"/c/{c['slug']}/",
                body=body, current=c["slug"])


def build_post(p: dict, posts: list[dict]) -> str:
    c = CAT[p["category"]]
    fig = ""
    if p.get("thumbnail"):
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
    <h1>{e(p['title'])}</h1>
    <p class="lead">{e(p['summary'])}</p>
    <p class="date">{KIND[p['kind']]} ・ {p['date'].isoformat()} 掲載</p>
    {fig}
    {palette}
    <div class="prose">{p['html']}</div>
    {items}
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
<h2>運営</h2>
<p>{e(SITE['author'])} ・ お問い合わせ: {e(SITE['contact_email'])}</p>
</div></div></main>"""
    return page(title="このサイトについて", desc="Cozy Desk の載せ方の決まりと運営者", path="/about/", body=body)


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
    write("about/index.html", build_about())
    write("404.html", page(title="ページが見つかりません", desc="", path="/404.html",
                           body='<main class="article"><div class="wrap"><h1>ページが見つかりません</h1>'
                                '<p><a href="/">トップへ戻る</a></p></div></main>'))
    base = SITE["base_url"].rstrip("/")
    urls = ["/", "/about/"] + [f"/c/{c['slug']}/" for c in CATS] + [p["url"] for p in posts]
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
