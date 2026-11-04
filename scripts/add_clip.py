r"""記事に、メーカー公式 YouTube 動画の3秒・音なしの切り出しを1カット足す(2026-11-04 本人「メーカー動画を使えるところは使いたい」)。

決まり(GT と同じ。「画像を自分のサーバーに置かない」の唯一の例外):
  - メーカー自身の公式チャンネルの動画だけ。レビュー・ニュース・ほかの人の動画は使わない
  - 1カット3秒・音なし・1記事3カットまで。出典(チャンネル名と元の動画の URL)を書く(自動)

使い方(yt-dlp と ffmpeg が入っている gadget-shorts の Python で動かす):
  D:\MyDocument\ClaudeApp\shorts\gadget-shorts\.venv\Scripts\python.exe scripts\add_clip.py ^
      <記事の名前(日付なし)> <カットの名前> <YouTube の URL> <始まりの秒> [--caption "一言"]
できる物: assets/clips/<記事>/<カット>.mp4 と .jpg(止めた絵)。記事の front matter の clips に1行足す。
本文に {{clip:番号}} と書いた所に出る。書かなければ一番上の写真のすぐ下(build.py の clip_fig)。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(r"D:\MyDocument\ClaudeApp\shorts\gadget-shorts\.cache\yt")  # GT の動画づくりと同じ置き場(git に入らない)
MAX_CLIPS = 3
SEC = 3.0


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("name")
    ap.add_argument("url")
    ap.add_argument("start", type=float)
    ap.add_argument("--caption", default="")
    a = ap.parse_args()
    post = next((ROOT / "content" / "posts").glob(f"*-{a.slug}.md"), None)
    if not post:
        sys.exit(f"記事がありません: {a.slug}")
    text = post.read_text(encoding="utf-8")
    fm_end = text.index("\n---", 3)
    fm = text[:fm_end]
    n_now = len(re.findall(r"^\s*- file: ", fm, re.M))
    if n_now >= MAX_CLIPS:
        sys.exit(f"もう {MAX_CLIPS} カットあります(1記事3カットまで)")

    yt = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--js-runtimes", "node"]
    info = json.loads(subprocess.run(yt + ["-J", a.url], capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    channel = info.get("channel") or ""
    print(f"チャンネル: {channel}  題名: {info.get('title')}  長さ: {info.get('duration')}秒")
    if a.start + SEC > (info.get("duration") or 0):
        sys.exit("始まりの秒が動画の終わりを越えています")
    url = f"https://www.youtube.com/watch?v={info['id']}"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    CACHE.mkdir(parents=True, exist_ok=True)
    src = CACHE / f"{info['id']}.mp4"
    if not src.exists():
        subprocess.run(yt + ["-q", "-f", "bv*[ext=mp4][height<=1080]/bv*[height<=1080]", "--remux-video", "mp4",
                             "--ffmpeg-location", ff, "-o", str(src), url], check=True)
    out = ROOT / "assets" / "clips" / a.slug / f"{a.name}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    # 記事の幅には 960px で足りる。1カット 100〜200KB(写真1枚と同じくらい)
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", f"{a.start}", "-i", str(src), "-t", f"{SEC}", "-an",
                    "-vf", "scale=960:-2,fps=30", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(out), "-frames:v", "1", "-q:v", "5",
                    str(out.with_suffix(".jpg"))], check=True)
    print(f"置きました: {out.relative_to(ROOT)}({out.stat().st_size // 1024}KB)")

    q = lambda s: json.dumps(s, ensure_ascii=False)  # noqa: E731  YAML のダブルクォート文字列として使える
    item = (f"  - file: {a.slug}/{a.name}.mp4\n    caption: {q(a.caption)}\n"
            f"    credit: {q(channel + ' 公式 YouTube')}\n    source: {q(url)}\n")
    if re.search(r"^clips:", fm, re.M):
        m = re.search(r"^clips:\n(?:  .*\n)*", text, re.M)
        text = text[:m.end()] + item + text[m.end():]
    else:
        m = re.search(r"^sources:", fm, re.M)
        at = m.start() if m else fm_end + 1
        text = text[:at] + "clips:\n" + item + text[at:]
    post.write_text(text, encoding="utf-8")
    print(f"記事に足しました({n_now + 1} カット目): {post.name}  本文の置き場所は {{{{clip:{n_now + 1}}}}}")


if __name__ == "__main__":
    main()
