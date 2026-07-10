#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/items.json から docs/index.html を生成
デザイン: 「新聞折込チラシに赤ペンで丸をつける」がコンセプト。
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

# 赤ペンで丸をつけるお得ワード
MARK_WORDS = re.compile(
    r"(無料|タダ|0円|半額|先着|全額|実質無料|\d+%(?:OFF|還元|オフ|引き)|"
    r"ポイント最大?\d*倍|\d+倍|\d+円引き|期間限定|本日限り)"
)

STAMP_STYLE = {  # 判子チップの見た目
    "free": "stamp-red",
    "point": "stamp-ink",
    "limited": "stamp-line",
}
STAMP_LABEL = {"free": "無料", "point": "還元", "limited": "限定"}


def esc(s: str) -> str:
    return html.escape(s or "")


def fmt_time(iso: str, fmt: str = "%m/%d %H:%M") -> str:
    try:
        return datetime.fromisoformat(iso).strftime(fmt)
    except ValueError:
        return ""


def mark(title: str) -> str:
    """エスケープ後、お得ワードに赤丸マークを付与"""
    safe = esc(title)
    return MARK_WORDS.sub(r'<em class="mk">\1</em>', safe)


def row(it) -> str:
    src = f'<span class="src">{esc(it["source"])}</span>' if it.get("source") else ""
    return f"""<a class="row" href="{esc(it['link'])}" target="_blank" rel="noopener">
  <p class="t">{mark(it['title'])}</p>
  <p class="m">{src}<time>{fmt_time(it['published'])}</time></p>
</a>"""


def main():
    data = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    items = data["items"]
    gen = datetime.fromisoformat(data["generated_at"])

    sections = ""
    for b in CONFIG["buckets"]:
        group = [it for it in items if it.get("bucket") == b["id"]]
        if not group:
            continue
        rows = "\n".join(row(it) for it in group)
        bid = b["id"]
        sections += f"""
<section>
  <header class="sec">
    <span class="stamp {STAMP_STYLE.get(bid, 'stamp-line')}">{STAMP_LABEL.get(bid, bid)}</span>
    <span class="cnt">{len(group)}件</span>
  </header>
  <div class="list">{rows}</div>
</section>"""

    if not sections:
        sections = '<p class="empty">まだ情報がありません。次の更新（朝7時・夜7時）をお待ちください。</p>'

    tpl = (
        TEMPLATE
        .replace("{{TITLE}}", esc(CONFIG["site_title"]))
        .replace("{{DATE}}", gen.strftime("%-m月%-d日"))
        .replace("{{TIME}}", gen.strftime("%H:%M"))
        .replace("{{COUNT}}", str(data["count"]))
        .replace("{{SECTIONS}}", sections)
    )
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(tpl, encoding="utf-8")
    print(f"docs/index.html を生成（{data['count']}件）")


# 赤ペンの丸: 手描き風楕円をSVG data-URIで
PEN = ("data:image/svg+xml;utf8,"
       "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44' "
       "preserveAspectRatio='none'%3E%3Cpath d='M14 24 C 16 8, 66 2, 94 8 "
       "C 116 13, 118 30, 92 37 C 62 44, 12 42, 8 28 C 5 18, 28 7, 60 6' "
       "fill='none' stroke='%23D7261D' stroke-width='3.2' "
       "stroke-linecap='round' opacity='.85'/%3E%3C/svg%3E")

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{{TITLE}}">
<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#FAF8F3; --paper2:#F1EDE3; --ink:#211F1C; --sub:#7A756B;
    --line:#E2DDD1; --red:#D7261D; --yellow:#FFD32E;
    --serif:'Shippori Mincho B1', serif;
    --sans:'Zen Kaku Gothic New', -apple-system, 'Hiragino Sans', sans-serif;
  }
  @media (prefers-color-scheme: dark){
    :root{ --paper:#171614; --paper2:#211F1B; --ink:#F0EDE6; --sub:#948E82;
           --line:#33302A; --red:#F04438; --yellow:#B8930A; }
  }
  *{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html{ background:var(--paper); }
  body{
    margin:0 auto; max-width:640px; min-height:100dvh;
    color:var(--ink); font-family:var(--sans); font-size:15px; line-height:1.6;
    padding:calc(env(safe-area-inset-top) + 22px) 20px 64px;
    background:
      repeating-linear-gradient(0deg, transparent 0 3px, rgba(0,0,0,.006) 3px 4px),
      var(--paper);
  }

  /* ── マストヘッド ─────────────────────── */
  .mast{ display:flex; align-items:flex-start; justify-content:space-between; gap:14px; }
  .mast h1{
    margin:0; font-family:var(--serif); font-weight:800;
    font-size:clamp(30px, 8.5vw, 42px); line-height:1.18; letter-spacing:.015em;
  }
  .mast h1 small{
    display:block; font-family:var(--sans); font-weight:500;
    font-size:11px; letter-spacing:.32em; color:var(--sub); margin-bottom:8px;
  }
  /* 消印スタンプ */
  .postmark{
    flex:none; width:86px; height:86px; border-radius:50%;
    border:2.5px solid var(--red); color:var(--red);
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:1px; transform:rotate(7deg); margin-top:6px;
    font-family:var(--serif); font-weight:700; text-align:center;
    -webkit-mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9' /%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .93 0'/%3E%3C/filter%3E%3Crect width='100' height='100' filter='url(%23n)'/%3E%3C/svg%3E");
    mask-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9' /%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .93 0'/%3E%3C/filter%3E%3Crect width='100' height='100' filter='url(%23n)'/%3E%3C/svg%3E");
  }
  .postmark .d{ font-size:14px; line-height:1; }
  .postmark .h{ font-size:17px; line-height:1.15; }
  .postmark .u{ font-size:9px; font-family:var(--sans); letter-spacing:.25em; text-indent:.25em; }
  .lede{
    margin:14px 0 0; padding-top:12px; border-top:1px solid var(--ink);
    display:flex; justify-content:space-between; font-size:11.5px; color:var(--sub);
    letter-spacing:.06em;
  }
  .lede b{ color:var(--ink); font-weight:700; }

  /* ── セクション ───────────────────────── */
  section{ margin-top:34px; }
  .sec{ display:flex; align-items:baseline; gap:10px; margin-bottom:2px; }
  .stamp{
    font-family:var(--serif); font-weight:800; font-size:15px;
    padding:5px 9px 4px; line-height:1; letter-spacing:.18em; text-indent:.18em;
    transform:rotate(-1.2deg);
  }
  .stamp-red { background:var(--red); color:var(--paper); }
  .stamp-ink { background:var(--ink); color:var(--paper); }
  .stamp-line{ background:transparent; color:var(--red); box-shadow:inset 0 0 0 2px var(--red); }
  .cnt{ font-size:11.5px; color:var(--sub); letter-spacing:.08em; }

  /* ── 記事行 ──────────────────────────── */
  .row{
    display:block; text-decoration:none; color:inherit;
    padding:15px 2px 14px; border-bottom:1px solid var(--line);
  }
  .row:active{ background:var(--paper2); }
  @media (hover:hover){ .row:hover{ background:var(--paper2); } }
  .t{ margin:0; font-weight:500; font-size:15px; line-height:1.72; }
  .m{ margin:7px 0 0; display:flex; align-items:baseline; gap:10px;
      font-size:11px; color:var(--sub); letter-spacing:.04em; }
  .src{ color:var(--red); font-weight:700; }
  time{ margin-left:auto; font-variant-numeric:tabular-nums; }

  /* 赤ペンの丸 */
  .mk{
    font-style:normal; font-weight:700; position:relative;
    padding:.05em .3em; margin:0 .05em; white-space:nowrap;
  }
  .mk::after{
    content:""; position:absolute; inset:-.28em -.32em -.34em;
    background:url("__PEN__") no-repeat center / 100% 100%;
    pointer-events:none;
  }

  .empty{ text-align:center; color:var(--sub); margin-top:72px; font-size:13px; }
  footer{
    margin-top:56px; padding-top:14px; border-top:1px solid var(--ink);
    display:flex; justify-content:space-between;
    font-size:10.5px; color:var(--sub); letter-spacing:.1em;
  }

  /* 入場アニメーション（控えめ） */
  @media (prefers-reduced-motion: no-preference){
    .mast, section, footer{ animation:up .5s cubic-bezier(.2,.7,.2,1) both; }
    section:nth-of-type(1){ animation-delay:.06s }
    section:nth-of-type(2){ animation-delay:.12s }
    section:nth-of-type(3){ animation-delay:.18s }
    footer{ animation-delay:.24s }
    @keyframes up{ from{ opacity:0; transform:translateY(10px) } to{ opacity:1 } }
  }
  a:focus-visible{ outline:2px solid var(--red); outline-offset:3px; border-radius:2px; }
</style>
</head>
<body>
<header class="mast">
  <h1><small>朝夕2回・自動更新</small>{{TITLE}}</h1>
  <div class="postmark" role="img" aria-label="{{DATE}} {{TIME}} 更新">
    <span class="d">{{DATE}}</span>
    <span class="h">{{TIME}}</span>
    <span class="u">更新</span>
  </div>
</header>
<p class="lede"><span>本日の掲載 <b>{{COUNT}}件</b></span><span>無料・還元・限定</span></p>

<main>
  <section id="rakuten" hidden></section>
  {{SECTIONS}}
</main>

<footer><span>Google ニュース RSS ＋ 楽天API</span><span>おとくまとめ</span></footer>
<script src="rakuten.js"></script>
</body>
</html>
""".replace("__PEN__", PEN)

if __name__ == "__main__":
    main()
