r"""X の「新作」の画像を作る(公式写真を1〜4枚、物を大きく。右下に Cozy Desk のロゴ)。

2026-11-14 本人と型を変えた(それまでは 11/7 の「物とシロネを同じ床に並べる」1枚)。
  - シロネとの大きさ比べはしない。シロネも入れない(本人「やっぱりいらない」)。かわりに右下にサイトのロゴ
  - 物をなるべく大きく、しっかり見せる。写真は複数枚を別々の画像にして、X に並べて載せる
    (手本: 机の写真の人がよくやる、写真を2〜4枚そのまま添付する形。X では同じ高さで横に並ぶ)
  - 1枚目の左上にだけ「新作」の札と物の名前を小さく。ワクワクする一言は画像に入れず、本文に書く
  - 写真は公式写真。白い背景は自動で抜く(rembg。JapanHasThat-shorts の .venv の Python を使う)。
    部屋に置いた写真など、背景ごと見せたい写真は先頭に「raw:」を付けると、抜かずに枠いっぱいに敷く

    python scripts/x_new.py --out assets/x/<id>.jpg --name "ASUS TUF Gaming VG27AQL5F-W" ^
        --image <正面の写真> --image <背中の写真> --image <横の写真> --credit "画像: ASUS 公式サイト"

  → assets/x/<id>-1.jpg, <id>-2.jpg ... ができる(下書きの images にこの順で並べる)

画像の形: 高さ 1200px。横幅は物の形に合わせて 800〜1600px(縦長の物は縦長、横長の物は横長の画像)。
1枚目は札が入るよう 1200px 以上にする。--fill で物の大きさ(枠に対する割合、ふつう 0.86)。
文字とロゴは丸文字 Zen Maru Gothic(scripts/fonts)。背景は淡いラベンダーから白への、継ぎ目のない色。
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FD = ROOT / "scripts" / "fonts"
REMBG_PY = ROOT.parent.parent / "shorts" / "JapanHasThat-shorts" / ".venv" / "Scripts" / "python.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
H = 1200
INK, ACC, CREDIT = (74, 64, 92), (122, 107, 170), (150, 142, 165)
COCOA, OAK = (74, 64, 57), (212, 184, 150)  # サイトの --cocoa と --oak(ヘッダーのロゴと同じ色)


def F(n: int, w: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FD / f"ZenMaruGothic-{w}.ttf"), n)


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=60).read()
        return Image.open(io.BytesIO(data))
    return Image.open(src)


def cutout(ph: Image.Image) -> Image.Image:
    """背景を抜いた物だけの絵。もとから透明な PNG ならそのまま使う"""
    if ph.mode in ("RGBA", "LA", "P") and ph.convert("RGBA").getchannel("A").getextrema()[0] < 200:
        im = ph.convert("RGBA")
    else:
        if not REMBG_PY.exists():
            sys.exit(f"背景を抜く道具が見つからない: {REMBG_PY}")
        with tempfile.TemporaryDirectory() as t:
            src, dst = Path(t) / "in.png", Path(t) / "out.png"
            ph.convert("RGB").save(src)
            code = ("import sys;from rembg import remove,new_session;from PIL import Image;"
                    "remove(Image.open(sys.argv[1]),session=new_session('isnet-general-use')).save(sys.argv[2])")
            subprocess.run([str(REMBG_PY), "-c", code, str(src), str(dst)], check=True)
            im = Image.open(dst).convert("RGBA")
            im.load()
    a = im.getchannel("A").point(lambda v: 255 if v > 24 else 0)  # うっすら残った影で枠が広がらないように
    return im.crop(a.getbbox())


def background(w: int, h: int) -> Image.Image:
    """継ぎ目のない撮影用の背景(上の淡いラベンダーから下の白へ)。壁と机の境目の線は作らない"""
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    top, mid, bot = (236, 230, 245), (244, 240, 240), (250, 249, 247)
    for y in range(h):
        t = y / h
        a, b, u = (top, mid, t / 0.55) if t < 0.55 else (mid, bot, (t - 0.55) / 0.45)
        u = u * u * (3 - 2 * u)
        d.line([(0, y), (w, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
    return im.convert("RGBA")


def logo(im: Image.Image, size: int = 40, pill: bool = False) -> None:
    """右下にサイトのヘッダーと同じロゴ: cozy●desk(Black・ココア色・字間 .06em・間にオークの点)"""
    W, Hh = im.size
    d = ImageDraw.Draw(im)
    f = F(size, "Black")
    sp, dot, gap = size * 0.06, size * 0.38, size * 0.1

    def tw(t: str) -> float:
        return sum(d.textlength(c, font=f) for c in t) + sp * (len(t) - 1)

    total = tw("cozy") + gap * 2 + dot + tw("desk")
    x, y = W - 40 - total, Hh - 34
    if pill:  # 写真を敷いた画像では、読めるように白い札にのせる
        d.rounded_rectangle([x - 20, y - size - 4, W - 20, y + 16], radius=(size + 20) // 2, fill=(251, 249, 246))
    for part in ("cozy", None, "desk"):
        if part is None:
            cy = y - size * 0.17
            d.ellipse([x + gap, cy - dot / 2, x + gap + dot, cy + dot / 2], fill=OAK)
            x += gap * 2 + dot
            continue
        for c in part:
            d.text((x, y), c, font=f, fill=COCOA, anchor="ls")
            x += d.textlength(c, font=f) + sp


def tag(im: Image.Image, name: str) -> None:
    """1枚目の左上: 「新作」の札と物の名前"""
    d = ImageDraw.Draw(im)
    f1 = F(30, "Black")
    tw = d.textlength("新作", font=f1)
    room = im.width - 40 - (40 + tw + 54) - 30
    size = 30
    while size > 18 and d.textlength(name, font=F(size)) > room:
        size -= 2
    d.rounded_rectangle([40, 40, 40 + tw + 36, 92], 26, fill=ACC)
    d.text((58, 66), "新作", font=f1, fill="white", anchor="lm")
    d.text((40 + tw + 54, 66), name, font=F(size), fill=INK, anchor="lm")


def card(src: str, first: bool, name: str, credit: str, fill: float) -> Image.Image:
    raw = src.startswith("raw:")
    ph = load(src[4:] if raw else src)
    if raw:  # 背景ごと見せる写真: そのまま枠いっぱいに(4:3〜2:3 に収める)
        ph = ph.convert("RGB")
        r = min(max(ph.width / ph.height, 2 / 3), 4 / 3)
        w = max(int(H * r), 1200 if first else 800)
        im = ImageOps.fit(ph, (w, H), Image.LANCZOS).convert("RGBA")
    else:
        obj = cutout(ph)
        r = obj.width / obj.height
        w = int(min(max(H * r * 1.08, 800), 1600))  # 物の形に合わせた枠。縦長の物は縦長の画像に
        if first:
            w = max(w, 1200)
        im = background(w, H)
        top, bottom = (120 if first else 60), 90  # 札・ロゴと重ならない範囲で、物をいちばん大きく
        s = min(w * fill / obj.width, (H - top - bottom) / obj.height)
        obj = obj.resize((max(1, round(obj.width * s)), max(1, round(obj.height * s))), Image.LANCZOS)
        x = (w - obj.width) // 2
        y = top + (H - top - bottom - obj.height) // 2
        floor = y + obj.height
        sh = Image.new("RGBA", (w, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([x + obj.width * 0.1, floor - 14, x + obj.width * 0.9, floor + 16], fill=(90, 80, 100, 60))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        im.alpha_composite(obj, (x, y))
    if first:
        tag(im, name)
    logo(im, pill=raw)
    d = ImageDraw.Draw(im)
    fc = F(20, "Medium")
    if raw:  # 写真の上では読めないので、ロゴと同じ白い札にのせる
        d.rounded_rectangle([24, H - 58, 56 + d.textlength(credit, font=fc), H - 20], radius=19, fill=(251, 249, 246))
    d.text((40, H - 32), credit, font=fc, fill=CREDIT, anchor="ls")
    return im


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", action="append", required=True, help="公式写真の URL かファイル。1〜4回。背景ごと見せるなら raw: を前に")
    ap.add_argument("--out", required=True, help="assets/x/<id>.jpg → <id>-1.jpg, -2.jpg ... ができる")
    ap.add_argument("--name", required=True, help="1枚目の札の横に出す物の名前(メーカー名から)")
    ap.add_argument("--credit", required=True, help="左下の出典。例: 画像: ASUS 公式サイト")
    ap.add_argument("--fill", type=float, default=0.86)
    a = ap.parse_args()
    if len(a.image) > 4:
        sys.exit("X に載せられる画像は4枚まで")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(a.image, 1):
        im = card(src, i == 1, a.name.replace("|", " "), a.credit, a.fill)
        p = out.with_name(f"{out.stem}-{i}.jpg")
        im.convert("RGB").save(p, quality=90)
        print(p, im.size)


if __name__ == "__main__":
    main()
