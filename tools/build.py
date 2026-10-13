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
covered = {i["move"]: i["number"] for i in issues}
tiles = []
for m in range(1, 34):
    if m in covered:
        tiles.append(
            f'<a class="tile on" href="#issue-{covered[m]}" title="Move {m}: issue #{covered[m]}">{m}</a>'
        )
    else:
        tiles.append(f'<span class="tile" aria-hidden="true">{m}</span>')
out.append(
    f'<section class="moves reveal"><h2>The 33 moves</h2>'
    f'<p class="note">{len(covered)} of 33 covered so far. Each issue lights one up.</p>\n'
    f'<div class="strip" role="list" aria-label="Moves covered in issues">{"".join(tiles)}</div></section>'
)
block = "<!-- ISSUES:START -->\n" + "\n".join(out) + "\n<!-- ISSUES:END -->"
p = root / "index.html"
s = p.read_text()
p.write_text(re.sub(r"<!-- ISSUES:START -->.*?<!-- ISSUES:END -->", lambda _: block, s, flags=re.S))
print(f"built {len(issues)} public issue(s); moves covered: {sorted(covered)}")
