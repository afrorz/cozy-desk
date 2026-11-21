r"""X の「まとめ」画像を1枚で作る(まとめ記事の物を、1枚の中にたくさん並べる)。

2026-11-16 本人「1枚の中にいろいろ載ってるのがいい」。新作の型(写真を1枚ずつ)とは別。
  - 縦長 1200x1500。上に小さい一言と題、その下に白いカードを格子に並べる(4つなら2列、9つなら3列)
  - カードには物の写真(背景を抜いて大きく)・番号・短い名前・色の名前
  - 値段や数字は入れない(X_POSTING.md の決まり。値段は返信の記事で)。シロネも入れない。右下に Cozy Desk のロゴ

    python scripts/x_matome.py --out assets/x/<id>.jpg --lead "カフェの机に出しても、かわいいまま" --title "ガジェットポーチ 9選" ^
        --item "<公式写真>|MOTTERU マシカクポーチ|ピンクライラック" --item ... --credit "画像: MOTTERU・コクヨ ほか各社公式"
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from x_new import F, INK, ACC, CREDIT, background, cutout, load, logo

W, H = 1200, 1500
SUB = (125, 117, 140)


def main_part(obj: Image.Image) -> Image.Image:
    """写真にのっている文字やマーク(色の名前・素材のマーク)を外し、いちばん大きなかたまり=物だけ残す"""
    import numpy as np
    from scipy import ndimage
    a = np.array(obj.getchannel("A")) > 40
    lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=6))
    if n > 1:
        big = np.argmax(ndimage.sum(a, lab, range(1, n + 1))) + 1
        keep = (lab == big) & a
        al = np.array(obj.getchannel("A"))
        al[~keep] = 0
        obj = obj.copy()
        obj.putalpha(Image.fromarray(al))
    return obj.crop(obj.getchannel("A").getbbox())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--lead", required=True, help="題の上の小さい一言")
    ap.add_argument("--title", required=True)
    ap.add_argument("--item", action="append", required=True, help="写真|名前|色の名前。4〜9回")
    ap.add_argument("--credit", required=True)
    a = ap.parse_args()
    items = [s.split("|") for s in a.item]
    n = len(items)
    cols = 2 if n <= 4 else 3
    rows = math.ceil(n / cols)

    im = background(W, H)
    d = ImageDraw.Draw(im)
    d.text((60, 52), a.lead, font=F(34), fill=SUB)
    size = 64
    while d.textlength(a.title, font=F(size, "Black")) > W - 120:
        size -= 2
    d.text((60, 96), a.title, font=F(size, "Black"), fill=INK)

    top, bottom, gap, side = 200, 96, 22, 46
    cw = (W - 2 * side - gap * (cols - 1)) // cols
    ch = (H - top - bottom - gap * (rows - 1)) // rows
    text_h = 92
    for k, it in enumerate(items):
        src, name, color = (it + ["", ""])[:3]
        r, c = divmod(k, cols)
        x = side + c * (cw + gap)
        y = top + r * (ch + gap)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x, y + 6, x + cw, y + ch + 6], 26, fill=(90, 80, 120, 36))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x, y, x + cw, y + ch], 26, fill=(255, 255, 255))
        if src.startswith("white:"):
            # 白い背景の写真で、物の中にも白い所がある(モニターの白い画面など)とき。
            # 背景を抜くと物の白まで消えるので、まわりの白い余白を切るだけにして白いカードに置く(2026-11-21)
            from PIL import ImageChops
            obj = load(src[6:]).convert("RGB")
            diff = ImageChops.difference(obj, Image.new("RGB", obj.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 12 else 0)
            obj = obj.crop(diff.getbbox() or (0, 0, *obj.size)).convert("RGBA")
        else:
            obj = main_part(cutout(load(src)))
        bw, bh = cw - 36, ch - text_h - 30
        s = min(bw / obj.width, bh / obj.height)
        obj = obj.resize((max(1, round(obj.width * s)), max(1, round(obj.height * s))), Image.LANCZOS)
        im.alpha_composite(obj, (x + (cw - obj.width) // 2, y + 18 + (bh - obj.height) // 2))
        d = ImageDraw.Draw(im)
        ty = y + ch - text_h + 6
        d.text((x + 20, ty), str(k + 1), font=F(24, "Black"), fill=(190, 180, 220))
        fs = 26
        while fs > 18 and d.textlength(name, font=F(fs)) > cw - 64:
            fs -= 1
        d.text((x + 50, ty - 2), name, font=F(fs), fill=INK)
        d.text((x + 50, ty + 38), color, font=F(21, "Medium"), fill=SUB)
        print(k + 1, name, flush=True)

    logo(im)
    d = ImageDraw.Draw(im)
    d.text((40, H - 32), a.credit, font=F(20, "Medium"), fill=CREDIT, anchor="ls")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out, quality=90)
    print(out, im.size)


if __name__ == "__main__":
    main()
