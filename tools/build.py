#!/usr/bin/env python3
"""Render issue sections into index.html from data/issues.json.
Only issues with public:true are shown (flip after the Kit broadcast goes out).
Keep unpublished drafts OUT of issues.json (the repo is public), or leave public:false."""
import urllib.parse
import json, html, re, datetime, pathlib
from zoneinfo import ZoneInfo
root = pathlib.Path(__file__).resolve().parent.parent
issues = [i for i in json.load(open(root / "data/issues.json")) if i.get("public") is True]
issues.sort(key=lambda i: i["number"] if type(i.get("number")) is int else -1, reverse=True)
e = html.escape
DOT = "·"
def nice(d):
    return datetime.date.fromisoformat(d).strftime("%-d %b %Y")
latest, earlier = (issues[0] if issues else None), issues[1:]
# One stylesheet version for every page: read it from the homepage head, so bumping it there is enough.
CSS_V = re.search(r'assets/style\.css\?v=(\w+)"', (root / "index.html").read_text()).group(1)
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
if len(MOVES) != 33:
    raise SystemExit(f"expected 33 habit names, found {len(MOVES)}; cannot build")
for n, name in enumerate(MOVES, 1):
    if not name.strip():
        raise SystemExit(f"habit #{n} has an empty name (check moves.md or moves/{n}.html); cannot build")
# Zero-width characters that look empty but pass str.strip() (Kent, 2 Nov 2026).
_ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u2060\u00ad\u180e"))
def without_zw(s):
    """Remove zero-width characters so a name made only of them counts as empty."""
    return s.translate(_ZW)
errors = []
_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
def good_https(v):
    """A real https link (no quote, angle bracket, backtick or backslash): scheme https, a host name with a dot, no user part, and a valid port if one is given."""
    try:
        u = urllib.parse.urlsplit(v)
        port = u.port
    except ValueError:
        return False
    if u.scheme != "https" or not v.startswith("https://") or "@" in u.netloc:
        return False
    if not u.hostname or not _HOST.fullmatch(u.hostname):
        return False
    if port is not None and not 1 <= port <= 65535:
        return False
    if u.netloc.endswith(":"):
        return False
    return not any(ord(c) < 32 or ord(c) == 127 or c in "\"'<>`\\" for c in v)
def need(rec, keys, where):
    """Collect an error if a field the page shows is missing, empty, only spaces
    or only zero-width characters, so the build can never publish an empty link
    or an image with no accessible name. Every bad field is reported together."""
    for k in keys:
        v = rec.get(k)
        cleaned = without_zw(v) if isinstance(v, str) else ""
        if not isinstance(v, str) or not cleaned.strip():
            errors.append(f"{where} has an empty or missing {k}; cannot build")
            continue
        # Check the raw value: a hidden zero-width character or a space inside a link would go straight into the href.
        if k.endswith("_url") and (cleaned != v or any(c.isspace() for c in v) or not good_https(v)):
            errors.append(f"{where} has {k}={v!r}, which is not a full https:// link; cannot build")
for i in issues:
    where = f"data/issues.json issue #{i.get('number')}"
    need(i, ("title", "teaser", "move_line", "date", "source_name", "source_url"), where)
    for k in ("number", "move"):
        if type(i.get(k)) is not int or (k == "move" and not 1 <= i[k] <= 33):
            errors.append(f"{where} has {k}={i.get(k)!r}, which is not a whole number{' from 1 to 33' if k == 'move' else ''}; cannot build")
    d = i.get("date")
    if isinstance(d, str) and without_zw(d).strip():
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", d):
                raise ValueError
            datetime.date.fromisoformat(d)
        except ValueError:
            errors.append(f"{where} has date={d!r}, not YYYY-MM-DD; cannot build")
    for k in ("youtube", "youtube_alt"):
        if k in i and i[k] is not None and not isinstance(i[k], str):
            errors.append(f"{where} has {k}={i[k]!r}, which is not text; cannot build")
# Validate every record before rendering anything, so a missing or non-string field is reported, never a crash (Kent, 8 Nov 2026).
STORIES = json.load(open(root / "data/stories.json"))
VIDEOS = json.load(open(root / "data/videos.json"))
for x in STORIES:
    need(x, ("source_name", "source_url"), f"data/stories.json story on habit #{x.get('move')}")
# Floor for video "added" dates: the site went live on 2026-10-13 (see site-improvements.md).
SITE_LAUNCH = datetime.date(2026, 10, 13)
for v in VIDEOS:
    where = f"data/videos.json video on habit #{v.get('move')}"
    need(v, ("id", "alt", "title", "added"), where)
    # "added" is the day the video went on the site; it is the sitemap lastmod for video-only habit pages.
    a = v.get("added")
    if not isinstance(a, str) or not without_zw(a).strip():
        continue
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", a):
            raise ValueError
        ad = datetime.date.fromisoformat(a)
    except ValueError:
        errors.append(f"{where} has added={a!r}, not YYYY-MM-DD; cannot build")
        continue
    if ad > datetime.datetime.now(ZoneInfo("Europe/Stockholm")).date():
        errors.append(f"{where} has added={a!r}, later than today; cannot build")
    elif ad < SITE_LAUNCH:
        errors.append(f"{where} has added={a!r}, before site launch {SITE_LAUNCH.isoformat()}; cannot build")
if errors:
    raise SystemExit("\n".join(errors))
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
        alt = L.get("youtube_alt") or ("Video: " + L["title"])
        if not alt.endswith("."):
            alt = alt + "."
        out.append(
            # No aria-label: it would hide the img alt. The link's name is the alt, the
            # visually hidden YouTube hint, and the visible caption.
            f'<a class="yt" href="https://youtu.be/{y}" target="_blank" rel="noopener">'
            f'<img src="https://i.ytimg.com/vi/{y}/hqdefault.jpg" alt="{e(alt)}" width="480" height="270" '
            f'loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span>'
            f'<span class="sr-only">(YouTube, opens in a new tab)</span>'
            f'<span class="ytcap">Watch the video on this luck habit</span></a>'
        )
    # Rule: a new issue goes out every Sunday at 08:00 Stockholm local time (DST aware).
    STHLM = ZoneInfo("Europe/Stockholm")
    d0 = datetime.date.fromisoformat(L["date"])
    nd = d0 + datetime.timedelta(days=(6 - d0.weekday()) % 7 or 7)  # next Sunday after the latest issue
    nsend = datetime.datetime.combine(nd, datetime.time(8, 0), tzinfo=STHLM)
    nxt = nsend.strftime("%A %-d %b at %H:%M") + " Stockholm time"
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
            f'<a class="mv" href="moves/{i["move"]}.html">Luck habit #{i["move"]}: {e(MOVES[i["move"]-1])}</a><br>'
            f'<span class="note">{nice(i["date"])} {DOT} {e(i["teaser"])} {DOT} '
            f'Source: <a href="{e(i["source_url"])}">{e(i["source_name"])}</a>'
            + (f' {DOT} <a href="https://youtu.be/{e(i["youtube"])}" target="_blank" rel="noopener">Watch on YouTube</a>' if i.get("youtube") else "")
            + '</span></li>'
        )
    out.append("</ul></section>")
vsec = []
if VIDEOS:
    vsec.append('<section class="videos reveal"><h2>Watch the stories</h2>'
               '<p class="note">Short videos from Henrik\'s YouTube channel, <a href="https://www.youtube.com/@OverWise-i9s" target="_blank" rel="noopener">OverWise</a>. Each one tells the true story behind a luck habit.</p>')
    vsec.append('<ul class="vids">' + "".join(
        f'<li><a class="vthumb" href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">'
        f'<img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt="{e(v["alt"])}" width="480" height="270" loading="lazy" decoding="async"><span class="play" aria-hidden="true"></span></a>'
        f'<b>{e(v["title"])}</b>'
        f'<span class="note"><a class="mv" href="moves/{v["move"]}.html">Luck habit #{v["move"]}: {e(MOVES[v["move"]-1])}</a> {DOT} '
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
    state = "had its own issue" if m in covered else ("has a true story" if m in storied else "no story yet")
    tiles.append(f'<a class="{cls}" href="moves/{m}.html" title="Luck habit #{m}: {e(MOVES[m-1])}" '
                 f'aria-label="Luck habit #{m}: {e(MOVES[m-1])} ({state})">{m}</a>')
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
    f'<div class="strip" role="group" aria-label="The 33 luck habits">{"".join(tiles)}</div>'
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
    # A habit's sent issues always come first, with their video and source, then its stories.
    iss = [i for i in issues if i["move"] == m]
    ibody = "".join(
        f'<li><b><a href="../#issue-{i["number"]}">Issue #{i["number"]}</a></b>, {nice(i["date"])}: {e(i["title"])}<br>{e(i["teaser"])}<br>'
        + (f'<a href="https://youtu.be/{e(i["youtube"])}" target="_blank" rel="noopener">Watch the video on YouTube</a><br>' if i.get("youtube") else "")
        + f'<span class="note">Source: <a href="{e(i["source_url"])}" rel="noopener">{e(i["source_name"])}</a></span></li>'
        for i in iss)
    ss = sorted([x for x in STORIES if x["move"] == m], key=lambda x: x["date"], reverse=True)
    sbody = "".join(
        f'<li><b>{e(x["name"])}</b>: {e(x["title"])}<br>{e(x["why"])}<br>'
        f'<span class="note">Source: <a href="{e(x["source_url"])}" rel="noopener">{e(x["source_name"])}</a>, {nice(x["date"])}</span></li>'
        for x in ss)
    vs = [v for v in VIDEOS if v["move"] == m]
    vbody = ('<h2>Watch</h2><ul class="stories">' + "".join(
        f'<li><b>{e(v["title"])}</b><br><a href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">Watch on YouTube</a></li>'
        for v in vs) + "</ul>") if vs else ""
    if iss or ss or vs:
        withs += 1
    if iss or ss:
        body = f'<ul class="stories">{ibody}{sbody}</ul>'
    elif vs:
        body = ""
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
        f'<link rel="stylesheet" href="../assets/style.css?v={CSS_V}"></head><body><header><a class="logo" href="../">Luck Habits</a><span class="tag">luckhabits.com</span></header>'
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
    # Each habit page's own newest date: its stories, its sent issues and the videos it lists.
    ds = ([x["date"] for x in STORIES if x["move"] == m] + [i["date"] for i in issues if i["move"] == m]
          + [v["added"] for v in VIDEOS if v["move"] == m])
    return max(ds) if ds else site_last
pm = re.search(r"Last updated (\d+ \w+ \d{4})", (root / "privacy.html").read_text())
priv_last = datetime.datetime.strptime(pm.group(1), "%d %B %Y").date().isoformat() if pm else site_last
urls = [("https://luckhabits.com/", max(site_last, SITE["home_updated"])), ("https://luckhabits.com/privacy.html", priv_last)]
urls += [(f"https://luckhabits.com/moves/{m}.html", page_last(m)) for m in sorted(has_story)]
# Static pages share the homepage's stylesheet version, so they also get fresh CSS after a change.
for name in ("privacy.html", "404.html"):
    sp = root / name
    writes[sp] = re.sub(r'(assets/style\.css)(\?v=\w+)?"', rf'\1?v={CSS_V}"', sp.read_text())
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
