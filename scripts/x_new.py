r"""X の「新作」の画像(1200x675)を作る。2026-11-04 本人が3案から選んだ形(案①)。

  左 720px: 公式写真(白背景ならそのまま、まわりは写真の角の色で埋める)
  右 480px: 淡いラベンダーの面に「新作」の札・メーカー名・物の名前・ワクワクする一言、右下にシロネ
  シロネは斜めの姿(docs/character/shirone/diag.png)で、左の写真の方を向く。**物に背を向けさせない**(本人)

    python scripts/x_new.py --image <公式写真のURLかファイル> --out assets/x/<id>.jpg ^
        --maker ELECOM --name "しろちゃん|ディスプレイケーブル" --hook "顔を見れば、|充電の強さがわかる" ^
        --credit "画像: エレコム・Cozy Desk(シロネ)" [--zoom 0.85] [--fx 0.5]

--name : 物の名前。「|」で2行に分けると、1行目が大きく2行目が少し小さい。長いと自動で縮む
--hook : ワクワクする一言(docs/X_POSTING.md「いちばん大事なこと」)。「|」で2行まで
--zoom : 写真の大きさ。1.0 で左の面いっぱい(はみ出た所は切れる)。物の端が切れるなら小さくする
--fx   : 写真を左右どちらに寄せて切るか(0=左を見せる・1=右を見せる)
文字は丸文字 Zen Maru Gothic(scripts/fonts)。
"""
from __future__ import annotations

import argparse
import io
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FD = ROOT / "scripts" / "fonts"
SHIRONE = ROOT / "docs" / "character" / "shirone" / "diag.png"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
W, H, LW = 1200, 675, 720
INK, ACC, SUB, CREDIT = (74, 64, 92), (122, 107, 170), (130, 120, 148), (150, 142, 165)
TX, TW = LW + 56, 1200 - LW - 56 - 40  # 右の面の文字の左端と幅


def F(n: int, w: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FD / f"ZenMaruGothic-{w}.ttf"), n)


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=60).read()
        return Image.open(io.BytesIO(data))
    return Image.open(src)


def panel() -> Image.Image:
    a, b = (236, 230, 246), (248, 245, 250)
    g = Image.new("RGB", (W - LW, H))
    d = ImageDraw.Draw(g)
    for y in range(H):
        t = y / H
        t = t * t * (3 - 2 * t)
        d.line([(0, y), (W - LW, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return g


def fit(d: ImageDraw.ImageDraw, text: str, size: int, weight: str) -> ImageFont.FreeTypeFont:
    while size > 20 and d.textlength(text, font=F(size, weight)) > TW:
        size -= 2
    return F(size, weight)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--maker", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--hook", required=True)
    ap.add_argument("--credit", required=True)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--fx", type=float, default=0.5)
    ap.add_argument("--fy", type=float, default=0.5)
    a = ap.parse_args()

    ph = load(a.image).convert("RGB")
    bg = ph.getpixel((3, 3))
    im = Image.new("RGBA", (W, H), (*bg, 255))
    s = max(LW / ph.width, H / ph.height) * a.zoom
    p = ph.resize((round(ph.width * s), round(ph.height * s)), Image.LANCZOS)
    x = int((LW - p.width) * a.fx) if p.width > LW else (LW - p.width) // 2
    y = int((H - p.height) * a.fy) if p.height > H else (H - p.height) // 2
    left = Image.new("RGB", (LW, H), bg)
    left.paste(p, (x, y))
    im.paste(left, (0, 0))
    im.paste(panel(), (LW, 0))

    d = ImageDraw.Draw(im)
    f = F(22)
    tw = d.textlength("新作", font=f)
    d.rounded_rectangle([TX, 60, TX + tw + 36, 102], 21, fill=(255, 255, 255), outline=(214, 206, 236), width=2)
    d.text((TX + 18, 68), "新作", font=f, fill=ACC)
    d.text((TX + tw + 56, 68), a.maker, font=F(22, "Medium"), fill=SUB)
    y = 118
    names = a.name.split("|")
    for i, line in enumerate(names):
        fnt = fit(d, line, 50 if i == 0 else 40, "Black")
        d.text((TX, y), line, font=fnt, fill=INK)
        y += fnt.size + 14
    y += 16
    d.line([(TX + 2, y), (TX + 42, y)], fill=(200, 190, 228), width=3)
    y += 18
    for line in a.hook.split("|")[:2]:
        fnt = fit(d, line, 28, "Medium")
        d.text((TX, y), line, font=fnt, fill=ACC)
        y += 38

    sh = Image.open(SHIRONE).convert("RGBA")  # 左(物の方)を向いている。左右反転しない
    sh_h = min(290, H - y - 40)
    sh = sh.resize((int(sh.width * sh_h / sh.height), sh_h), Image.LANCZOS)
    im.alpha_composite(sh, (W - sh.width - 46, H - sh.height - 14))
    d.text((24, H - 36), a.credit, font=F(18, "Medium"), fill=CREDIT)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(a.out, quality=90)
    print(a.out)


if __name__ == "__main__":
    main()
