"""新作の候補を集める(2026-11-04〜)。

config/feeds.yaml の RSS を読み、色の言葉と物の言葉が両方入った話題を
data/candidates/<日本の日付>.json に足していく。一度見た URL は data/seen.json で飛ばす。
GitHub Actions の collect.yml が30分おきに回す(PR TIMES の一覧が直近1時間半ぶんしか載らないため)。
毎朝の記事づくり(docs/DAILY.md)は、この候補から1件選んで書く。

    python scripts/collect.py          # 集めて保存
    python scripts/collect.py --dry    # 保存せずに数だけ見る
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONF = yaml.safe_load((ROOT / "config/feeds.yaml").read_text(encoding="utf-8"))
OUT = ROOT / "data/candidates"
SEEN = ROOT / "data/seen.json"
JST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def text(el) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(el or ""))).strip()


def parse_date(s: str) -> str:
    if not s:
        return ""
    try:
        d = parsedate_to_datetime(s) if not re.match(r"\d{4}-", s) else datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(JST).strftime("%Y-%m-%d %H:%M")
    except Exception:  # noqa: BLE001
        return s[:16]


def items(xml: bytes):
    root = ET.fromstring(xml)
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        f = {}
        for ch in el:
            k = ch.tag.split("}")[-1]
            if k == "link" and ch.get("href"):
                f.setdefault("link", ch.get("href"))
            elif ch.text:
                f.setdefault(k, ch.text)
        link = (f.get("link") or el.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about") or "").strip()
        yield {
            "title": text(f.get("title")),
            "url": link,
            "summary": text(f.get("description") or f.get("summary") or f.get("encoded") or "")[:300],
            "date": parse_date(f.get("date") or f.get("pubDate") or f.get("published") or f.get("updated") or ""),
        }


def match(words: list[str], s: str, region: str) -> list[str]:
    if region == "world":
        return [w for w in words if re.search(r"\b" + re.escape(w) + r"s?\b", s, re.I)]
    return [w for w in words if w in s]


def main() -> None:
    dry = "--dry" in sys.argv
    seen: dict = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    today = datetime.now(JST).strftime("%Y-%m-%d")
    path = OUT / f"{today}.json"
    found: list = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    added = 0
    old = (datetime.now(JST) - timedelta(days=14)).strftime("%Y-%m-%d")  # ブランドのブログは古い記事も並ぶので、2週間より前は飛ばす(11/9)
    for feed in CONF["feeds"]:
        try:
            req = urllib.request.Request(feed["url"], headers={"User-Agent": UA})
            xml = urllib.request.urlopen(req, timeout=30).read()
            got = list(items(xml))
        except Exception as ex:  # noqa: BLE001  1か所落ちても、ほかは続ける
            print(f"! {feed['name']}: {ex}")
            continue
        w = CONF["words"][feed["region"]]
        hit = 0
        for it in got:
            if not it["url"] or it["url"] in seen:
                continue
            seen[it["url"]] = today
            if re.match(r"\d{4}-\d{2}-\d{2}", it["date"]) and it["date"][:10] < old:
                continue
            s = f'{it["title"]} {it["summary"]}'
            c, t = match(w["color"], s, feed["region"]), match(w["thing"], s, feed["region"])
            if c and t:
                found.append({**it, "source": feed["name"], "region": feed["region"], "words": c + t})
                hit += 1
        added += hit
        print(f"{feed['name']}: {len(got)}件 → 候補 {hit}")
    print(f"今日の候補に {added} 件足した(合計 {len(found)})")
    if dry:
        for f in found[-added:] if added else []:
            print(f"  [{f['region']}] {f['title']}  ({', '.join(f['words'])})")
        return
    # 見た URL は30日で忘れる(ファイルが太り続けないように)
    cut = (datetime.now(JST) - timedelta(days=30)).strftime("%Y-%m-%d")
    seen = {k: v for k, v in seen.items() if v >= cut}
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    SEEN.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
