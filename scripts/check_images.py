"""Cozy Desk の記事の写真(image: / thumbnail:)が、今も写真として開けるかを確かめる。

python scripts/check_images.py          # 開けない写真を一覧にする(全部開ければ「すべて開けました」)
python scripts/check_images.py --json   # 結果を JSON で出す(毎晩の見回りで使う)

2026-11-01 に Lian Li の公式サイトがロボットよけの画面を返すようになり、写真が2枚出なくなった。
それを毎晩見つけるために作った。写真の代わりにウェブページ(text/html)が返る・404 などを「開けない」とする。
403 だけは、写真の置き場所がプログラムからの取得を断っているだけで、ブラウザでは開けることがある
(例: エレコムの写真)。そのため「要ブラウザ確認」として分けて出す。
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.8",
}


def collect() -> list[tuple[str, str, str]]:
    """(写真のURL, 記事のファイル名, 物の名前) を全部集める"""
    rows = []
    for path in sorted((ROOT / "content" / "posts").glob("*.md")):
        fm = path.read_text(encoding="utf-8").split("---", 2)[1]
        name = "(記事の表紙)"
        for line in fm.splitlines():
            m = re.match(r'\s*-?\s*name:\s*"?(.+?)"?\s*$', line)
            if m and line.lstrip().startswith("- name:"):
                name = m.group(1)
            m = re.match(r'\s*(image|thumbnail|inside):\s*"?([^"\s]+)"?', line)
            if m and m.group(2).startswith("http"):
                rows.append((m.group(2), path.name, "(記事の表紙)" if m.group(1) == "thumbnail" else name + ("(中の写真)" if m.group(1) == "inside" else "")))
    return rows


def check(url: str) -> tuple[str, str]:
    """('ok' | 'ng' | 'browser', 理由)"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            ctype = r.headers.get("Content-Type", "")
            head = r.read(512)
            if ctype.startswith("image/") or head[:4] in (b"\x89PNG", b"RIFF", b"GIF8") or head[:2] == b"\xff\xd8":
                return "ok", ctype
            return "ng", f"写真でなく {ctype or '中身の分からないもの'} が返る(ロボットよけ画面やページ移動のことが多い)"
    except urllib.error.HTTPError as ex:
        if ex.code == 403:
            return "browser", "403(プログラムからの取得を断っている。ブラウザでは開けることがある)"
        return "ng", f"HTTP {ex.code}"
    except Exception as ex:  # noqa: BLE001  通信の失敗はまとめて「開けない」
        return "ng", f"つながらない({type(ex).__name__})"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = collect()
    urls = sorted({u for u, _, _ in rows})
    with ThreadPoolExecutor(12) as ex:
        result = dict(zip(urls, ex.map(check, urls)))
    bad = [{"url": u, "post": p, "item": n, "state": result[u][0], "why": result[u][1]}
           for u, p, n in rows if result[u][0] != "ok"]
    if "--json" in sys.argv:
        print(json.dumps({"checked": len(urls), "bad": bad}, ensure_ascii=False, indent=1))
        return
    if not bad:
        print(f"写真 {len(urls)} 枚、すべて開けました")
        return
    print(f"写真 {len(urls)} 枚のうち、{len(bad)} か所に問題があります")
    for b in bad:
        mark = "要ブラウザ確認" if b["state"] == "browser" else "開けない"
        print(f"- [{mark}] {b['post']} / {b['item']}\n    {b['url']}\n    {b['why']}")
    sys.exit(1 if any(b["state"] == "ng" for b in bad) else 0)


if __name__ == "__main__":
    main()
