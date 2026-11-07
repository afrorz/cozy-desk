r"""X の「新作」の画像(1200x675)を作る。

2026-11-07 本人と壁打ちして型を変えた(それまでは 11/4 の「左に公式写真・右に札とシロネ」)。
左右に分けた型は、型番が主役で物が単体で置かれ、シロネが飾りになるので、男性向けのガジェット発表カードに見えた。
「大きさ比べ」の投稿(コンセントハウス・タワー型)のほうが、シロネの10cmの世界に見えて、かわいかった。そこで:

  - ワクワクする一言をいちばん大きく(左上)。物の名前は「新作」の札の横に小さく
  - 物とシロネを同じ淡い床に、ほぼ本当の大きさの比率で並べる(シロネは背丈10cm)。シロネは物の方を向く
  - 右下に、物の大きさとシロネの背丈を小さく書く
  - 写真は公式写真。白い背景は自動で抜く(rembg。JapanHasThat-shorts の .venv の Python を使う)

    python scripts/x_new.py --image <公式写真のURLかファイル> --out assets/x/<id>.jpg ^
        --maker AULA --name "NEOS75 Venus" --hook "机の上に、|小さな美術館" ^
        --cm 37.3 --by w --credit "画像: AULA 公式ストア・Cozy Desk(シロネ)"

--cm   : 物の大きさ(公式の寸法、cm)。写真の横幅(--by w)か高さ(--by h)が、この長さだと見なしてシロネの大きさを決める
--by   : w=横幅(キーボード・マウス・机に横長に置く物)、h=高さ(ヘッドホン・ライト・縦長の物)
--size : 右下の文字。省くと「横幅 37.3cm ・ シロネ 10cm」のように自動
--hook : ワクワクする一言(docs/X_POSTING.md「いちばん大事なこと」)。「|」で2行まで
--name : 物の名前。「|」は空白に置きかえて1行にする
--zoom : 物の大きさ(1.0 で置ける枠いっぱい)。シロネも同じ割合で変わる
文字は丸文字 Zen Maru Gothic(scripts/fonts)。背景と床は x_render.py と同じ。
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from x_render import base  # noqa: E402  淡いラベンダーから白への、継ぎ目のない背景

ROOT = Path(__file__).resolve().parent.parent
FD = ROOT / "scripts" / "fonts"
SHIRONE = ROOT / "docs" / "character" / "shirone" / "diag.png"  # 左(物の方)を向いている。左右反転しない
REMBG_PY = ROOT.parent.parent / "shorts" / "JapanHasThat-shorts" / ".venv" / "Scripts" / "python.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
W, H = 1200, 675
INK, ACC, SUB, CREDIT = (74, 64, 92), (122, 107, 170), (130, 120, 148), (150, 142, 165)
TX, TW = 64, 1200 - 64 * 2
SH_MIN, SH_MAX = 120, 360  # シロネの高さ(px)。小さすぎると見えず、大きすぎると物が豆つぶになる


def F(n: int, w: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FD / f"ZenMaruGothic-{w}.ttf"), n)


def load(src: str) -> Image.Image:
    if src.startswith("http"):
        data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=60).read()
        return Image.open(io.BytesIO(data))
    return Image.open(src)


def cutout(ph: Image.Image) -> Image.Image:
    """背景を抜いた物だけの絵。もとから透明な PNG ならそのまま使う"""
    if ph.mode in ("RGBA", "LA") and ph.getchannel("A").getextrema()[0] < 200:
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


def fit(d: ImageDraw.ImageDraw, text: str, size: int, weight: str, width: int = TW) -> ImageFont.FreeTypeFont:
    while size > 20 and d.textlength(text, font=F(size, weight)) > width:
        size -= 2
    return F(size, weight)


def shadow(im: Image.Image, x0: float, x1: float, y: int, k: float) -> None:
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x0, y - 12, x1, y + 14], fill=(90, 80, 100, int(70 * k)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--maker", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--hook", required=True)
    ap.add_argument("--credit", required=True)
    ap.add_argument("--cm", type=float, required=True)
    ap.add_argument("--by", choices=["w", "h"], default="w")
    ap.add_argument("--size", default="")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--floor", type=int, default=625)
    a = ap.parse_args()

    im = base().convert("RGBA")
    d = ImageDraw.Draw(im)

    # 一言(主役)
    y = 46
    for line in a.hook.split("|")[:2]:
        fnt = fit(d, line, 54, "Bold")
        d.text((TX, y), line, font=fnt, fill=INK)
        y += fnt.size + 18
    # 小さな札: 新作・メーカー・名前
    y += 4
    f = F(22)
    cw = d.textlength("新作", font=f)
    d.rounded_rectangle([TX, y, TX + cw + 28, y + 36], radius=18, fill=(255, 255, 255), outline=(200, 190, 222), width=2)
    d.text((TX + 14, y + 4), "新作", font=f, fill=ACC)
    name = f"{a.maker}  {a.name.replace('|', ' ')}"
    d.text((TX + cw + 44, y + 4), name, font=fit(d, name, 24, "Medium", TW - cw - 44), fill=SUB)
    top = y + 36 + 22  # ここより下に物を置く

    # 物とシロネの大きさ。物を置ける枠いっぱいにし、シロネを同じ縮尺の10cmにする
    p = cutout(load(a.image))
    sh = Image.open(SHIRONE).convert("RGBA")
    sh = sh.crop(sh.getbbox())
    box_h = a.floor - top
    box_w = 820
    s = min(box_w / p.width, box_h / p.height) * a.zoom
    ppcm = (p.width * s if a.by == "w" else p.height * s) / a.cm
    sh_h = 10 * ppcm
    if sh_h > SH_MAX or sh_h > box_h:  # 小さな物: シロネを上限にして、物を同じ割合で小さく
        k = min(SH_MAX, box_h) / sh_h
        s, sh_h = s * k, sh_h * k
    pw, ph_ = round(p.width * s), round(p.height * s)
    sh_h = round(sh_h)
    if sh_h < SH_MIN:
        print(f"注意: シロネが {sh_h}px と小さい(物が大きい)。--zoom を下げると見やすくなる", file=sys.stderr)
    p = p.resize((pw, ph_), Image.LANCZOS)
    sh = sh.resize((max(1, round(sh.width * sh_h / sh.height)), sh_h), Image.LANCZOS)

    gap = 26
    total = pw + gap + sh.width
    x0 = max(40, min((W - total) // 2 + 40, W - total - 60))  # まとまりを真ん中より少し右に
    xs = x0 + pw + gap
    shadow(im, x0 + pw * 0.08, x0 + pw * 0.92, a.floor, 0.5)
    shadow(im, xs + sh.width * 0.1, xs + sh.width * 0.9, a.floor, 0.7)
    im.alpha_composite(p, (x0, a.floor - ph_))
    im.alpha_composite(sh, (xs, a.floor - sh_h))

    d = ImageDraw.Draw(im)
    size = a.size or f"{'横幅' if a.by == 'w' else '高さ'} {a.cm:g}cm ・ シロネ 10cm"
    f = F(22, "Medium")
    d.text((W - 40 - d.textlength(size, font=f), H - 44), size, font=f, fill=SUB)
    d.text((24, H - 40), a.credit, font=F(18, "Medium"), fill=CREDIT)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(a.out, quality=90)
    print(a.out)


if __name__ == "__main__":
    main()
