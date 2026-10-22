#!/usr/bin/env python3
"""Render issue sections into index.html from data/issues.json.
Only issues with public:true are shown (flip after the Kit broadcast goes out).
Keep unpublished drafts OUT of issues.json (the repo is public), or leave public:false."""
import json, html, re, datetime, pathlib
from zoneinfo import ZoneInfo
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
        f'<p class="move"><a href="moves/{L["move"]}.html" aria-label="Luck habit #{L["move"]}">Luck habit #<span class="count" data-to="{L["move"]}">{L["move"]}</span></a> of 33: {e(L["move_line"])}</p>'
    )
    if L.get("youtube"):
        y = e(L["youtube"])
        out.append(
            f'<a class="yt" href="https://youtu.be/{y}" target="_blank" rel="noopener" '
            f'aria-label="Watch Henrik\'s video on luck habit #{L["move"]} on YouTube">'
            f'<img src="https://i.ytimg.com/vi/{y}/hqdefault.jpg" alt="{e(L.get("youtube_alt") or "Video thumbnail: " + L["title"])}" width="480" height="270" '
            f'loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span>'
            f'<span class="ytcap">Watch the video on this luck habit</span></a>'
        )
    # Rule: a new issue goes out every Sunday at 08:00 Stockholm local time (DST aware).
    STHLM = ZoneInfo("Europe/Stockholm")
    d0 = datetime.date.fromisoformat(L["date"])
    nd = d0 + datetime.timedelta(days=(6 - d0.weekday()) % 7 or 7)  # next Sunday after the latest issue
    nsend = datetime.datetime.combine(nd, datetime.time(8, 0), tzinfo=STHLM)
    nxt = nsend.strftime("%A %-d %b at %H:%M")
    out.append(
        f'<p class="note">Source: <a href="{e(L["source_url"])}">{e(L["source_name"])}</a></p>\n'
        f'<p class="note nextup">Next story: {nxt}. <a href="#signup">Get it by email</a>, free.</p></section>'
    )
elif not issues:
    out.append(
        f'<section class="sample reveal"><p class="kicker">First issue {DOT} Sunday 18 Oct {DOT} 08:00</p>\n'
        '<h2>He bet $3 on a jacket someone put back</h2>\n'
        '<blockquote><p>By 7:30 on an ordinary Thursday, Quinn Brown, 19, was in line at the Goodwill '
        'bins in Hillsboro, outside Portland. The man next to him, a few years older, tossed an old '
        'Lakers warm-up jacket back in front of him. Brown grabbed it right away and paid about $3. '
        'It was the jacket Wilt Chamberlain wore in the 1972 NBA Finals, and in July it sold at '
        'auction for $89,600.</p>\n'
        '<p class="move">Luck habit #26: Know the field well enough to see the odd result.</p></blockquote>\n'
        f'<p class="note">Source: <a href="https://www.wweek.com/culture/2026/07/20/'
        f'wilt-chamberlain-jacket-found-by-portland-teenager-sells-for-89600/">Willamette Week</a> '
        f'{DOT} Subscribe above and it lands in your inbox first.</p></section>'
    )
if earlier:
    out.append('<section class="earlier reveal"><h2>Earlier issues</h2><ul>')
    for i in earlier:
        out.append(
            f'<li id="issue-{i["number"]}"><b>#{i["number"]} {e(i["title"])}</b> '
            f'<span class="mv">Luck habit #{i["move"]}</span><br>'
            f'<span class="note">{nice(i["date"])} {DOT} {e(i["teaser"])} {DOT} '
            f'<a href="{e(i["source_url"])}">Source</a></span></li>'
        )
    out.append("</ul></section>")
def load_moves():
    """moves.md is local only (not committed). On a clean checkout fall back to the
    habit names already in the committed moves/N.html pages."""
    src = root / "moves.md"
    if src.exists():
        return [re.sub(r"^\d+\.\s*", "", l).strip() for l in src.read_text().splitlines() if re.match(r"^\d+\.", l)]
    names = []
    for m in range(1, 34):
        mp = root / f"moves/{m}.html"
        h = re.search(r"<h1>(.*?)</h1>", mp.read_text(), re.S) if mp.exists() else None
        if not h:
            raise SystemExit(f"moves.md missing and moves/{m}.html has no habit name; cannot build")
        names.append(html.unescape(h.group(1)))
    print("moves.md not found, using habit names from committed moves pages")
    return names
MOVES = load_moves()
STORIES = json.load(open(root / "data/stories.json"))
VIDEOS = json.load(open(root / "data/videos.json"))
vsec = []
if VIDEOS:
    vsec.append('<section class="videos reveal"><h2>Watch the stories</h2>'
               '<p class="note">Short videos from Henrik\'s YouTube channel, <a href="https://www.youtube.com/@OverWise-i9s" target="_blank" rel="noopener">OverWise</a>. Each one tells the true story behind a luck habit.</p>')
    vsec.append('<ul class="vids">' + "".join(
        f'<li><a class="vthumb" href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">'
        f'<img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt="{e(v["alt"])}" width="480" height="270" loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span></a>'
        f'<b>{e(v["title"])}</b>'
        f'<span class="note"><a class="mv" href="moves/{v["move"]}.html">Luck habit #{v["move"]}</a> {DOT} '
        f'<a href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">Watch on YouTube</a></span></li>'
        for v in VIDEOS) + '</ul></section>')
covered = {i["move"]: i["number"] for i in issues}
storied = {x["move"] for x in STORIES} | {v["move"] for v in VIDEOS}
def has_content(m):
    """One test for 'this habit has content': a story, a video or a public issue.
    Tiles, noindex, the sitemap and the final check all use it."""
    return m in storied or m in covered
tiles = []
for m in range(1, 34):
    cls = "tile on" if m in covered else ("tile has" if m in storied else "tile")
    tiles.append(f'<a class="{cls}" href="moves/{m}.html" title="Luck habit #{m}: {e(MOVES[m-1])}">{m}</a>')
has_story = {m for m in range(1, 34) if has_content(m)}
n_st = len(has_story)
legend = (f"{n_st} of 33 already have a true, sourced story. Habits #16 to #22 are about risk. Tap a tile with a story to read it."
          if n_st else "Tap a luck habit to see the true stories behind it.")
key_items = ['<span><i class="sw"></i>No story yet</span>']
if n_st:
    key_items.append('<span><i class="sw has"></i>Has a true story</span>')
if covered:
    key_items.append('<span><i class="sw on"></i>Had its own issue</span>')
key = f'<p class="note key">{"".join(key_items)}</p>' if len(key_items) > 1 else ""
out.append(
    f'<section class="moves reveal"><h2>The 33 luck habits</h2>'
    f'<p class="note">{legend}</p>\n'
    f'<div class="strip" role="list" aria-label="The 33 luck habits">{"".join(tiles)}</div>'
    f'{key}</section>'
)
out.extend(vsec)
block = "<!-- ISSUES:START -->\n" + "\n".join(out) + "\n<!-- ISSUES:END -->"
p = root / "index.html"
s = p.read_text()
rendered = re.sub(r"<!-- ISSUES:START -->.*?<!-- ISSUES:END -->", lambda _: block, s, flags=re.S)
# data/site.json keeps the day the homepage last changed, for the sitemap lastmod.
# It moves to today (Stockholm) only when this build changes index.html; no git needed.
# Nothing is written until every page is built and checked (see the end of this file).
site_path = root / "data/site.json"
SITE = json.load(open(site_path))
writes = {}
if rendered != s:
    SITE["home_updated"] = datetime.datetime.now(ZoneInfo("Europe/Stockholm")).date().isoformat()
    writes[site_path] = json.dumps(SITE, indent=2) + "\n"
    writes[p] = rendered
print(f"built {len(issues)} public issue(s); moves covered: {sorted(covered)}")

# Move pages: the Ledger
withs = 0
for m in range(1, 34):
    ss = sorted([x for x in STORIES if x["move"] == m], key=lambda x: x["date"], reverse=True)
    if ss: withs += 1
    if ss:
        body = "<ul class=\"stories\">" + "".join(
            f'<li><b>{e(x["name"])}</b>: {e(x["title"])}<br>{e(x["why"])}<br>'
            f'<span class="note">Source: <a href="{e(x["source_url"])}" rel="noopener">{e(x["source_name"])}</a>, {nice(x["date"])}</span></li>'
            for x in ss) + "</ul>"
    vs = [v for v in VIDEOS if v["move"] == m]
    if vs and not ss: withs += 1
    if vs:
        vbody = '<h2>Watch</h2><ul class="stories">' + "".join(
            f'<li><b>{e(v["title"])}</b><br><a href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">Watch on YouTube</a></li>'
            for v in vs) + "</ul>"
    else:
        vbody = ""
    iss = [i for i in issues if i["move"] == m]
    if ss:
        pass
    elif vs:
        body = ""
    elif iss:  # a public issue is the only content: list it, linking to it on the homepage
        withs += 1
        body = "<ul class=\"stories\">" + "".join(
            f'<li><b><a href="../#issue-{i["number"]}">Issue #{i["number"]}</a></b>: {e(i["title"])}<br>{e(i["teaser"])}<br>'
            f'<span class="note">Source: <a href="{e(i["source_url"])}" rel="noopener">{e(i["source_name"])}</a>, {nice(i["date"])}</span></li>'
            for i in iss) + "</ul>"
    else:
        body = '<p class="note">No stories here yet. When we find a true one with a name and a source, it goes here.</p>'
    nav = (f'<a href="{m-1}.html">&larr; Luck habit #{m-1}</a> ' if m > 1 else "") + '<a href="../">All luck habits</a>' + (f' <a href="{m+1}.html">Luck habit #{m+1} &rarr;</a>' if m < 33 else "")
    t = e(MOVES[m-1])
    # Same test as the tile strip: a page with no content stays out of search results until it gets one.
    robots = "" if has_content(m) else '<meta name="robots" content="noindex, follow">'
    writes[root / f"moves/{m}.html"] = (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Luck habit #{m}: {t} | Luck Habits</title><meta name="description" content="True, sourced stories of people who got lucky by doing this: {t}.">'
        f'{robots}<link rel="canonical" href="https://luckhabits.com/moves/{m}.html"><link rel="icon" href="../favicon.svg" type="image/svg+xml">'
        f'<link rel="stylesheet" href="../assets/style.css"></head><body><header><a class="logo" href="../">Luck Habits</a><span class="tag">luckhabits.com</span></header>'
        f'<main id="main"><section><p class="kicker">Luck habit #{m} of 33</p><h1>{t}</h1>'
        f'<p>Real people who got lucky this way. Each story links to where we read it, so you can check it yourself.</p>{body}{vbody}'
        f'<p class="note">{nav}</p><p><a href="../#signup">Get one story like this every Sunday</a></p></section></main>'
        f'<footer>Luck Habits is written by Henrik Ekenberg in Stockholm. © 2026 Finansium AB</footer><script data-goatcounter="https://luckledger.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n</body></html>\n')
print(f"move pages: 33, with stories: {withs}")
print(f"noindex: {[m for m in range(1, 34) if m not in has_story]}")

# sitemap.xml: homepage, privacy notice and the move pages that have a story (same set as the tiles).
# lastmod comes from the data, so a clean build always gives the same file.
site_last = max([i["date"] for i in issues] + [x["date"] for x in STORIES])
def page_last(m):
    ds = [x["date"] for x in STORIES if x["move"] == m] + [i["date"] for i in issues if i["move"] == m]
    return max(ds) if ds else site_last
pm = re.search(r"Last updated (\d+ \w+ \d{4})", (root / "privacy.html").read_text())
priv_last = datetime.datetime.strptime(pm.group(1), "%d %B %Y").date().isoformat() if pm else site_last
urls = [("https://luckhabits.com/", max(site_last, SITE["home_updated"])), ("https://luckhabits.com/privacy.html", priv_last)]
urls += [(f"https://luckhabits.com/moves/{m}.html", page_last(m)) for m in sorted(has_story)]
writes[root / "sitemap.xml"] = (
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    + "</urlset>\n")

# Check before writing anything: a failure leaves every file as it was.
indexed = {m for m in range(1, 34) if 'name="robots"' not in writes[root / f"moves/{m}.html"]}
in_sitemap = {int(x) for x in re.findall(r"/moves/(\d+)\.html<", writes[root / "sitemap.xml"])}
if not (withs == len(has_story) and indexed == has_story == in_sitemap):
    raise SystemExit(f"story count mismatch: pages {withs}, tile strip {len(has_story)}, "
                     f"indexed {sorted(indexed ^ has_story)}, sitemap {sorted(in_sitemap ^ has_story)}; nothing written")
(root / "moves").mkdir(exist_ok=True)
changed = 0
for path, text in writes.items():
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
        changed += 1
print(f"sitemap.xml: {len(urls)} urls; files changed: {changed}")
