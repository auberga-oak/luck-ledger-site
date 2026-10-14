#!/usr/bin/env python3
"""Render issue sections into index.html from data/issues.json.
Only issues with public:true are shown (flip after the Kit broadcast goes out).
Keep unpublished drafts OUT of issues.json (the repo is public), or leave public:false."""
import json, html, re, datetime, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
issues = [i for i in json.load(open(root / "data/issues.json")) if i.get("public") is True]
issues.sort(key=lambda i: i["number"], reverse=True)
e = html.escape
DOT = "·"
def nice(d):
    return datetime.date.fromisoformat(d).strftime("%-d %b %Y")
latest, earlier = (issues[0] if issues else None), issues[1:]
out = []
if latest:
    L = latest
    out.append(
        f'<section class="latest reveal" id="issue-{L["number"]}"><p class="kicker">Latest {DOT} Issue #{L["number"]} {DOT} {nice(L["date"])}</p>\n'
        f'<h2>{e(L["title"])}</h2><p>{e(L["teaser"])}</p>\n'
        f'<p class="move">Move <span class="count" data-to="{L["move"]}">{L["move"]}</span> of 33: {e(L["move_line"])}</p>'
    )
    if L.get("youtube"):
        y = e(L["youtube"])
        out.append(
            f'<a class="yt" href="https://youtu.be/{y}" target="_blank" rel="noopener" '
            f'aria-label="Watch Henrik\'s video on move {L["move"]} on YouTube">'
            f'<img src="https://i.ytimg.com/vi/{y}/hqdefault.jpg" alt="" width="480" height="270" '
            f'loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span>'
            f'<span class="ytcap">Watch the video on this move</span></a>'
        )
    out.append(
        f'<p class="note">Source: <a href="{e(L["source_url"])}">{e(L["source_name"])}</a></p></section>'
    )
elif not issues:
    out.append(
        f'<section class="sample reveal"><p class="kicker">First issue {DOT} Sunday 18 Oct {DOT} 08:00</p>\n'
        '<h2>The $3 jacket somebody else put back</h2>\n'
        '<blockquote><p>At 7:30 on an ordinary Thursday, an older reseller in a Portland Goodwill '
        'picked up an old Lakers warm-up jacket and tossed it back. Quinn Brown, 19, grabbed it '
        '"in half a second." He paid about $3. It was the jacket Wilt Chamberlain wore in the 1972 '
        'NBA Finals, and Sotheby&#x27;s sold it for $89,600.</p>\n'
        '<p class="move">Move 26: Know the field well enough to see the odd result.</p></blockquote>\n'
        f'<p class="note">Source: <a href="https://www.wweek.com/culture/2026/07/20/'
        f'wilt-chamberlain-jacket-found-by-portland-teenager-sells-for-89600/">Willamette Week</a> '
        f'{DOT} Subscribe above and it lands in your inbox first.</p></section>'
    )
if earlier:
    out.append('<section class="earlier reveal"><h2>Earlier issues</h2><ul>')
    for i in earlier:
        out.append(
            f'<li id="issue-{i["number"]}"><b>#{i["number"]} {e(i["title"])}</b> '
            f'<span class="mv">Move {i["move"]}</span><br>'
            f'<span class="note">{nice(i["date"])} {DOT} {e(i["teaser"])} {DOT} '
            f'<a href="{e(i["source_url"])}">Source</a></span></li>'
        )
    out.append("</ul></section>")
MOVES = [re.sub(r"^\d+\.\s*", "", l).strip() for l in (root / "moves.md").read_text().splitlines() if re.match(r"^\d+\.", l)]
STORIES = json.load(open(root / "data/stories.json"))
covered = {i["move"]: i["number"] for i in issues}
storied = {x["move"] for x in STORIES}
tiles = []
for m in range(1, 34):
    cls = "tile on" if m in covered else ("tile has" if m in storied else "tile")
    tiles.append(f'<a class="{cls}" href="moves/{m}.html" title="Move {m}: {e(MOVES[m-1])}">{m}</a>')
n_st = len(storied | set(covered))
legend = (f"{n_st} of 33 moves already have a true, sourced story. The darker tiles have stories, so tap one to read them."
          if n_st else "Tap a move to see the true stories behind it.")
if covered:
    legend += f" Green ones have had their own issue ({len(covered)} so far)."
out.append(
    f'<section class="moves reveal"><h2>The 33 moves</h2>'
    f'<p class="note">{legend}</p>\n'
    f'<div class="strip" role="list" aria-label="The 33 moves">{"".join(tiles)}</div></section>'
)
block = "<!-- ISSUES:START -->\n" + "\n".join(out) + "\n<!-- ISSUES:END -->"
p = root / "index.html"
s = p.read_text()
p.write_text(re.sub(r"<!-- ISSUES:START -->.*?<!-- ISSUES:END -->", lambda _: block, s, flags=re.S))
print(f"built {len(issues)} public issue(s); moves covered: {sorted(covered)}")

# Move pages: the Ledger
(root / "moves").mkdir(exist_ok=True)
withs = 0
for m in range(1, 34):
    ss = sorted([x for x in STORIES if x["move"] == m], key=lambda x: x["date"], reverse=True)
    if ss: withs += 1
    if ss:
        body = "<ul class=\"stories\">" + "".join(
            f'<li><b>{e(x["name"])}</b>: {e(x["title"])}<br>{e(x["why"])}<br>'
            f'<span class="note">Source: <a href="{e(x["source_url"])}" rel="noopener">{e(x["source_name"])}</a>, {nice(x["date"])}</span></li>'
            for x in ss) + "</ul>"
    else:
        body = '<p class="note">No stories here yet. When we find a true one with a name and a source, it goes here.</p>'
    nav = (f'<a href="{m-1}.html">&larr; Move {m-1}</a> ' if m > 1 else "") + '<a href="../">All moves</a>' + (f' <a href="{m+1}.html">Move {m+1} &rarr;</a>' if m < 33 else "")
    t = e(MOVES[m-1])
    (root / f"moves/{m}.html").write_text(
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Move {m}: {t} | Luck Ledger</title><meta name="description" content="True, sourced stories of people who got lucky by doing this: {t}.">'
        f'<link rel="canonical" href="https://catalysi.si/moves/{m}.html"><link rel="icon" href="../favicon.svg" type="image/svg+xml">'
        f'<link rel="stylesheet" href="../assets/style.css"></head><body><header><a class="logo" href="../">Luck Ledger</a><span class="tag">catalysi.si</span></header>'
        f'<main id="main"><section><p class="kicker">Move {m} of 33</p><h1>{t}</h1>'
        f'<p>Real people who got lucky this way. Each story links to where we read it, so you can check it yourself.</p>{body}'
        f'<p class="note">{nav}</p><p><a href="../#signup">Get one story like this every Sunday</a></p></section></main>'
        f'<footer>Luck Ledger is written by Henrik Ekenberg in Stockholm. © 2026 Finansium AB</footer><script data-goatcounter="https://luckledger.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n</body></html>\n')
print(f"move pages: 33, with stories: {withs}")
