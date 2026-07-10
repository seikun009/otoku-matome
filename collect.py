#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
お得情報コレクター
Google ニュース RSS を検索して「無料 / ポイント還元 / 期間限定」の情報を集める。
外部ライブラリ不要（標準ライブラリのみ）。GitHub Actions でそのまま動く。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
JST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 otoku-matome/1.0"


def news_rss_url(query: str) -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def clean_title(title: str) -> str:
    # Google ニュースは末尾に「 - 媒体名」を付ける
    return re.sub(r"\s*-\s*[^-]+$", "", title).strip()


def parse_items(xml_text: str, query: str):
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for it in root.iterfind(".//item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("{*}source")
        source = (src_el.text.strip() if src_el is not None and src_el.text else "")
        try:
            dt = parsedate_to_datetime(pub).astimezone(JST) if pub else datetime.now(JST)
        except (TypeError, ValueError):
            dt = datetime.now(JST)
        items.append({
            "title": clean_title(title),
            "raw_title": title,
            "link": link,
            "source": source,
            "published": dt.isoformat(),
            "query": query,
        })
    return items


def assign_bucket(title: str) -> str:
    for b in CONFIG["buckets"]:
        if any(kw in title for kw in b["keywords"]):
            return b["id"]
    return CONFIG["buckets"][-1]["id"]  # 既定は期間限定


def dedupe(items):
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x["published"], reverse=True):
        key = re.sub(r"\s+", "", it["title"])[:40]
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def main():
    cutoff = datetime.now(JST) - timedelta(days=CONFIG["keep_days"])
    all_items = []
    for q in CONFIG["queries"]:
        try:
            xml = fetch(news_rss_url(q))
            got = parse_items(xml, q)[: CONFIG["max_per_query"]]
            all_items.extend(got)
            print(f"[OK] {q} -> {len(got)}件")
        except Exception as e:  # noqa: BLE001  1件失敗しても全体は止めない
            print(f"[NG] {q}: {e}", file=sys.stderr)
        time.sleep(1)

    # 日付フィルタ → バケット付与 → 重複除去
    fresh = [it for it in all_items if datetime.fromisoformat(it["published"]) >= cutoff]
    for it in fresh:
        it["bucket"] = assign_bucket(it["title"])
    fresh = dedupe(fresh)

    out = {
        "generated_at": datetime.now(JST).isoformat(),
        "count": len(fresh),
        "items": fresh,
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "items.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n合計 {len(fresh)} 件を data/items.json に保存")


if __name__ == "__main__":
    main()
