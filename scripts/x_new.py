"""X の「新作」の画像(1200x675)を作る。公式写真を切り抜いて大きく置き、右下にシロネの顔のスタンプ。

    python scripts/x_new.py --image <公式写真のURLかファイル> --out assets/x/<id>.jpg \
        --credit "画像: ◯◯ 公式サイト・Cozy Desk(シロネ)" [--face wow] [--photo]

--face  : wow(驚き)/ happy / calm / smug(docs/character/shirone/face_*.png)。物に合わせて選ぶ
--photo : 部屋の写真など切り抜けない写真のとき。切り抜かずに角丸の写真として置く
決まりは docs/X_POSTING.md(背景は継ぎ目なし・文字は丸文字)。
"""
from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from x_render import DESK, SH, H, W, base, credit, place  # noqa: E402

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=60).read()
        return Image.open(io.BytesIO(data))
    return Image.open(src)


def cutout(im: Image.Image) -> Image.Image:
    """もう透明な背景ならそのまま。そうでなければ rembg で切り抜き、中の穴(白い部品など)は元の色で埋める"""
    if im.mode in ("RGBA", "LA", "P"):
        a = np.array(im.convert("RGBA"))[..., 3]
        if (a < 10).mean() > 0.05:
            o = im.convert("RGBA")
            return o.crop(o.getbbox())
    from rembg import new_session, remove
    from scipy.ndimage import binary_fill_holes
    rgb = im.convert("RGB")
    pad = Image.new("RGB", (rgb.width + 80, rgb.height + 80), rgb.getpixel((2, 2)))
    pad.paste(rgb, (40, 40))
    out = np.array(remove(pad, session=new_session("isnet-general-use")))
    al = out[..., 3].astype(int)
    m = al >= 60
    holes = binary_fill_holes(m) & ~m
    src = np.array(pad)
    out[..., :3] = np.where(holes[..., None], src, out[..., :3])
    al = np.where(holes, 255, np.where(m, al, 0)).astype(np.uint8)
    o = Image.fromarray(np.dstack([out[..., :3], al]))
    return o.crop(o.getbbox())


def stamp(im: Image.Image, face: str) -> None:
    f0 = Image.open(f"{SH}face_{face}.png").convert("RGBA")
    f0 = f0.crop(f0.getbbox())
    D = 170
    st = Image.new("RGBA", (D + 16, D + 16), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.ellipse([8, 10, D + 8, D + 10], fill=(90, 80, 110, 50))
    st = st.filter(ImageFilter.GaussianBlur(5))
    sd = ImageDraw.Draw(st)
    sd.ellipse([8, 6, D + 8, D + 6], fill=(255, 255, 255, 255), outline=(207, 198, 232, 255), width=4)
    fw = int(D * 0.82)
    f = f0.resize((fw, int(f0.height * fw / f0.width)), Image.LANCZOS)
    st.alpha_composite(f, (8 + (D - fw) // 2, 6 + (D - f.height) // 2 + 4))
    im.paste(st, (W - D - 60, DESK - D + 40), st)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--credit", required=True)
    ap.add_argument("--face", default="wow")
    ap.add_argument("--photo", action="store_true")
    a = ap.parse_args()
    src = load(a.image)
    im = base()
    if a.photo:
        ph = src.convert("RGB")
        ph.thumbnail((860, 540), Image.LANCZOS)
        mask = Image.new("L", ph.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, ph.width, ph.height], 28, fill=255)
        x, y = (W - 230 - ph.width) // 2 + 20, (H - 60 - ph.height) // 2
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x, y + 8, x + ph.width, y + ph.height + 8], 28, fill=(90, 80, 120, 50))
        sh = sh.filter(ImageFilter.GaussianBlur(12))
        im.paste(sh, (0, 0), sh)
        im.paste(ph, (x, y), mask)
    else:
        obj = cutout(src)
        # 横長の物(キーボード・タップ)は幅で、縦長の物は高さでそろえる
        px = int(min(440, 820 * obj.height / obj.width))
        place(im, obj, 540, px=px)
    stamp(im, a.face)
    credit(im, a.credit)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out, quality=90)
    print(a.out)


if __name__ == "__main__":
    main()
