#!/usr/bin/env python3
"""Render issue sections into index.html from data/issues.json.
Only issues that are public:true or whose date has passed are shown.
Keep unpublished drafts OUT of issues.json (the repo is public)."""
import json, html, re, datetime, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
today = datetime.date.today().isoformat()
issues = [i for i in json.load(open(root/'data/issues.json')) if i.get('public') or i['date'] <= today]
issues.sort(key=lambda i: i['number'], reverse=True)
e = html.escape
def nice(d): return datetime.date.fromisoformat(d).strftime('%-d %b %Y')
latest, earlier = (issues[0] if issues else None), issues[1:]
out = []
if latest:
    L = latest
    out.append(f'''<section class="latest reveal" id="issue-{L['number']}"><p class="kicker">Latest · Issue #{L['number']} · {nice(L['date'])}</p>
<h2>{e(L['title'])}</h2><p>{e(L['teaser'])}</p>
<p class="move">Move <span class="count" data-to="{L['move']}">{L['move']}</span> of 33: {e(L['move_line'])}</p>''')
    if L.get('youtube'):
        y = e(L['youtube'])
        out.append(f'''<a class="yt" href="https://youtu.be/{y}" target="_blank" rel="noopener" aria-label="Watch Henrik's video on move {L['move']} on YouTube"><img src="https://i.ytimg.com/vi/{y}/hqdefault.jpg" alt="" width="480" height="270" loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span><span class="ytcap">Watch the video on this move</span></a>''')
    out.append(f'''<p class="note">Source: <a href="{e(L['source_url'])}">{e(L['source_name'])}</a></p></section>''')
if earlier:
    out.append('<section class="earlier reveal"><h2>Earlier issues</h2><ul>')
    for i in earlier:
        out.append(f'''<li id="issue-{i['number']}"><b>#{i['number']} {e(i['title'])}</b> <span class="mv">Move {i['move']}</span><br><span class="note">{nice(i['date'])} · {e(i['teaser'])} · <a href="{e(i['source_url'])}">Source</a></span></li>''')
    out.append('</ul></section>')
covered = {i['move']: i['number'] for i in issues}
tiles = []
for m in range(1, 34):
    if m in covered:
        tiles.append(f'<a class="tile on" href="#issue-{covered[m]}" title="Move {m}: issue #{covered[m]}">{m}</a>')
    else:
        tiles.append(f'<span class="tile" aria-hidden="true">{m}</span>')
out.append(f'''<section class="moves reveal"><h2>The 33 moves</h2><p class="note">{len(covered)} of 33 covered so far. Each issue lights one up.</p>
<div class="strip" role="list" aria-label="Moves covered in issues">{''.join(tiles)}</div></section>''')
block = '<!-- ISSUES:START -->\n' + '\n'.join(out) + '\n<!-- ISSUES:END -->'
p = root/'index.html'; s = p.read_text()
p.write_text(re.sub(r'<!-- ISSUES:START -->.*?<!-- ISSUES:END -->', lambda _: block, s, flags=re.S))
print(f'built {len(issues)} issue(s); moves covered: {sorted(covered)}')
