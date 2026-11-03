"""Build the print sheet of the election night ballot (Max, 2026-11-03) into public/ballot/.

Same race rule as lib/ballot.ts: both control picks, then every Senate and governor seat up in 2026 that Cook rates
Toss-up to Likely in data/seats.csv, named from data/derived.json, with untracked nominees from lib/ballot-nominees.json.
Writes an HTML file to .ballot-print/ and renders it to PDF with headless Chrome (fonts from node_modules, no network).

Usage: python3 scripts/ballot/build_print.py
"""
import csv
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_PDF = ROOT / "public/ballot/undertow-election-night-ballot.pdf"
WORK = ROOT / ".ballot-print"
# A browser to print with: BALLOT_CHROME if set, else the first Chrome or Chromium found (Greptile on PR #3).
CHROME_CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "google-chrome-stable",
                     "chromium", "chromium-browser", "chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]


def find_chrome():
    import os
    import shutil
    if os.environ.get("BALLOT_CHROME"):
        path = os.environ["BALLOT_CHROME"]
        if not (os.path.isfile(path) or shutil.which(path)):
            raise SystemExit(f"BALLOT_CHROME points at {path}, which is not a browser on this machine")
        return path
    for c in CHROME_CANDIDATES:
        if os.path.isfile(c) or shutil.which(c):
            return c if os.path.isfile(c) else shutil.which(c)
    raise SystemExit("No Chrome or Chromium found; set BALLOT_CHROME to the browser's path")
POINTS = {"CONTROL": 1, "SEN": 1, "GOV": 1}   # every pick 1 point (Max, 2026-11-03); the score is a count of checks
CATS = [("CONTROL", "Who wins control", "Senate and House"), ("SEN", "Senate races", "Toss-up to Likely"), ("GOV", "Governor races", "Toss-up to Likely")]
RATINGS = ("Toss-up", "Lean D", "Lean R", "Likely D", "Likely R")
SHORT = {"CONTROL": "Control", "SEN": "Senate", "GOV": "Governors"}
STATES = {"AK": "Alaska", "AZ": "Arizona", "FL": "Florida", "GA": "Georgia", "IA": "Iowa", "KS": "Kansas", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "NC": "North Carolina", "OK": "Oklahoma", "VT": "Vermont",
          "NE": "Nebraska", "NH": "New Hampshire", "NV": "Nevada", "OH": "Ohio", "OR": "Oregon", "SC": "South Carolina", "TX": "Texas", "WI": "Wisconsin"}
TIEBREAKERS = [("Senate seats for Democrats", "of 100, with the independents who caucus with them"),
               ("House seats Democrats win", "of 435"), ("Time the AP calls the House", "your time, or “not tonight”")]


def races():
    seats = list(csv.DictReader(open(ROOT / "data/seats.csv")))
    cands = json.load(open(ROOT / "data/derived.json"))["candidates"]
    extra = json.load(open(ROOT / "lib/ballot-nominees.json"))
    out = [dict(id="SENATE-CONTROL", cat="CONTROL", label="The Senate", held="R", d="Democrats", r="Republicans", inc=None, dparty="D", note="R hold now · 50-50 goes R"),
           dict(id="HOUSE-CONTROL", cat="CONTROL", label="The House", held="R", d="Democrats", r="Republicans", inc=None, dparty="D", note="R hold now · 218 to win")]
    for s in seats:
        if s["up_2026"] != "1" or s["cook_rating"] not in RATINGS or s["chamber"] not in ("SEN", "GOV"):
            continue
        c = cands.get(s["seat"]) or {}
        d = (c.get("D") or {}).get("candidate") or extra.get(s["seat"], {}).get("D")
        r = (c.get("R") or {}).get("candidate") or extra.get(s["seat"], {}).get("R")
        if not d or not r:
            raise SystemExit(f"no nominees for {s['seat']}")
        inc = s["incumbent_on_ballot"] if s["incumbent_on_ballot"] in ("D", "R") else None
        label = STATES[s["state"]] + (" (special)" if s["special"] == "1" else "")
        dparty = "I" if s["seat"] == "2026-NE-SEN" or str((c.get("D") or {}).get("party", "")).lower().startswith("independent") else "D"
        out.append(dict(id=s["seat"], cat=s["chamber"], label=label, held=s["holder_party"], d=d, r=r, inc=inc, dparty=dparty, note=f"{s['cook_rating']} · held {s['holder_party']}"))
    order = {c: i for i, (c, _, _) in enumerate(CATS)}
    # Control keeps Senate then House; seat races sort by state.
    return sorted(out, key=lambda x: (order[x["cat"]], "" if x["cat"] == "CONTROL" else x["label"]))


def esc(s):
    return html.escape(s, quote=True)


def row(x):

    def side(p):
        name = x["d"] if p == "D" else x["r"]
        star = '<span class="inc">★</span> ' if x["inc"] == p else ""
        letter = x["dparty"] if p == "D" else "R"
        party = "" if x["cat"] == "CONTROL" else f'<span class="pty is-{p.lower()}">{letter}</span>'
        # The star and party letter stay on the line of the last name, never alone on a line of their own.
        *first, last = esc(name).split(" ")
        tail = f'<span class="nowrap">{last} {star}{party}</span>' if (star or party) else last
        return f'<span class="opt"><span class="bubble"></span><span class="nm">{" ".join(first + [tail])}</span></span>'
    return (f'<div class="row"><span class="lbl">{esc(x["label"])}<em>{esc(x["note"])}</em></span>{side("D")}{side("R")}'
            f'<span class="pts"><span class="ptbox"></span></span></div>')


def page(rs):
    word = re.search(r'const WORD="([^"]+)"', (ROOT / "components/UI.tsx").read_text()).group(1)
    fonts = ROOT / "node_modules"
    face = lambda fam, path, w: f"@font-face{{font-family:'{fam}';src:url('file://{fonts / path}') format('woff2');font-weight:{w};}}"
    css_fonts = "".join([face("Manrope", "@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2", "200 800"),
                         face("Barlow Condensed", "@fontsource/barlow-condensed/files/barlow-condensed-latin-800-normal.woff2", 800),
                         face("IBM Plex Mono", "@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2", 400),
                         face("IBM Plex Mono", "@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-600-normal.woff2", 600)])
    top = sum(POINTS[x["cat"]] for x in rs)
    out = {c: sum(POINTS[x["cat"]] for x in rs if x["cat"] == c) for c, _, _ in CATS}
    # Each section ends in its own subtotal line, so the tally is added down the right-hand column.
    colhead = '<div class="colhead"><span>Race</span><span>Your pick</span><span></span><span>Right?</span></div>'
    sec = {c: f'<section class="cat"><h2>{esc(t)}<span>{esc(n)}</span></h2>{"".join(row(x) for x in rs if x["cat"] == c)}'
              f'<div class="sub"><span>{SHORT[c]} subtotal</span><i></i><em>/ {out[c]}</em></div></section>' for c, t, n in CATS}
    tally = "".join(f'<div class="t"><span>{SHORT[c]}</span><i></i><em>/ {out[c]}</em></div><b class="op">+</b>' for c, _, _ in CATS)
    tally = tally[: tally.rfind('<b class="op">+</b>')] + f'<b class="op">=</b><div class="t final"><span>Final score</span><i></i><em>/ {top}</em></div>'
    tbs = "".join(f'<div class="tb"><span>{esc(t)}<em>{esc(n)}</em></span><i></i></div>' for t, n in TIEBREAKERS)
    mark = ('<svg class="mark" viewBox="0 0 120 120" aria-hidden="true"><path d="M8 30h104" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>'
            '<path d="M24 30v34a36 36 0 0 0 72 0V30" stroke="currentColor" stroke-width="14" fill="none"/><path d="M60 46c10 0 16 8 16 16s-7 15-16 15-14-6-14-12 5-10 10-10 8 3 8 7" stroke="#c3262b" stroke-width="6" fill="none" stroke-linecap="round"/></svg>')
    wordmark = (f'<svg class="wordmark" viewBox="-2 -100 456 104" role="img" aria-label="Undertow"><defs><clipPath id="t"><rect x="-10" y="-120" width="480" height="95"/></clipPath>'
                f'<clipPath id="b"><rect x="-10" y="-25" width="480" height="40"/></clipPath></defs><path d="{word}" fill="currentColor" clip-path="url(#t)"/>'
                f'<g clip-path="url(#b)"><path d="{word}" fill="#c3262b" transform="translate(9 0)"/></g></svg>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Undertow election night ballot</title><style>{css_fonts}
@page {{size:letter;margin:0.42in 0.5in;}}
:root {{--ink:#0b1a3a;--muted:#4b5b7c;--line:#dde3ee;--soft:#f4f6fa;--d:#1b4fc4;--r:#c3262b;}}
* {{box-sizing:border-box;}}
html,body {{margin:0;background:#fff;color:var(--ink);font-family:'Manrope',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
.sheet {{width:7.5in;height:10.1in;display:flex;flex-direction:column;gap:8px;}}
header {{display:grid;grid-template-columns:auto 1fr auto;align-items:end;gap:16px;padding-bottom:10px;border-bottom:4px solid;border-image:linear-gradient(90deg,#1f5fd6 0 50%,#c3262b 50% 100%) 1;}}
.brand {{display:flex;align-items:center;gap:10px;}} .mark {{width:42px;height:42px;}} .wordmark {{height:26px;display:block;}}
.kicker {{white-space:nowrap;font:600 9px/1.4 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:3px 0 0;}}
h1 {{font:800 32px/.9 'Barlow Condensed',sans-serif;text-transform:uppercase;margin:0;white-space:nowrap;}}
h1 small {{display:block;font:600 9px/1.4 'IBM Plex Mono',monospace;letter-spacing:.14em;color:var(--muted);margin-top:6px;}}
.who {{display:grid;grid-template-columns:auto 1.55in;gap:8px;align-items:end;font:600 9px 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}}
.who i {{border-bottom:1px solid var(--ink);height:16px;}}
.key {{display:flex;flex-wrap:nowrap;gap:5px 14px;white-space:nowrap;align-items:center;padding:7px 12px;background:var(--soft);border-radius:4px;font-size:9.5px;}}
.key b {{font:800 13px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;}}
.key > span {{display:inline-flex;align-items:center;gap:6px;}}
.key code {{font:600 9px 'IBM Plex Mono',monospace;letter-spacing:.06em;}}
.key .ptbox {{width:14px;height:14px;}}
.cols {{display:grid;grid-template-columns:1fr 1fr;gap:20px;}} .col {{display:flex;flex-direction:column;gap:8px;min-width:0;}}
.colhead {{display:grid;grid-template-columns:0.95in 1fr 1fr 0.42in;gap:10px;padding:0 4px;font:600 8px 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}}
.colhead span:last-child {{text-align:center;}}
.cat h2 {{display:flex;justify-content:space-between;align-items:baseline;margin:0;padding:4px 8px;background:var(--ink);color:#fff;font:800 16px/1.1 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;border-radius:3px;}}
.cat h2 span {{font:500 8.5px 'IBM Plex Mono',monospace;letter-spacing:.06em;text-transform:none;opacity:.85;}}
.row {{display:grid;grid-template-columns:0.95in 1fr 1fr 0.42in;align-items:center;gap:6px;padding:4px 2px;border-bottom:1px solid var(--line);}}
.lbl {{font-weight:700;font-size:10.5px;line-height:1.15;}}
.lbl em {{display:block;font:400 7.5px/1.3 'IBM Plex Mono',monospace;font-style:normal;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:2px;}}
.opt {{display:flex;align-items:center;gap:5px;font-size:9.5px;line-height:1.2;}}
.bubble {{flex:none;width:12px;height:12px;border:1.5px solid var(--ink);border-radius:50%;}}
.nm {{font-weight:600;}} .nowrap {{white-space:nowrap;}}
.inc {{color:var(--muted);font-size:9px;}}
.pty {{font:600 8.5px 'IBM Plex Mono',monospace;}} .is-d {{color:var(--d);}} .is-r {{color:var(--r);}}
.pts {{display:flex;justify-content:center;}}
.ptbox {{display:inline-grid;place-items:center;width:20px;height:20px;border:1.5px solid var(--ink);border-radius:3px;font:800 13px 'Barlow Condensed',sans-serif;color:var(--muted);}}
.sub {{display:flex;justify-content:flex-end;align-items:flex-end;gap:8px;padding:5px 4px 0;font:600 8.5px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:right;}}
.sub i {{width:0.45in;border-bottom:1.5px solid var(--ink);height:16px;}}
.sub em {{font-style:normal;font-size:9px;width:0.35in;text-align:left;}}
.bottom {{display:block;margin-top:auto;}} .tbbox {{margin-top:6px;}}
.score .tally {{max-width:5.2in;}} .score {{grid-template-columns:auto 1fr;align-items:center;column-gap:24px;}} .score h3 {{grid-row:span 2;}}
.box {{border:1.5px solid var(--ink);border-radius:4px;padding:8px 12px 10px;display:grid;gap:8px;align-content:start;}}
.box h3 {{margin:0;font:800 16px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;}}
.tb {{display:grid;grid-template-columns:1fr 0.7in;gap:10px;align-items:end;font-size:10px;font-weight:600;}}
.tb em {{display:block;font:400 7.5px 'IBM Plex Mono',monospace;font-style:normal;color:var(--muted);}}
.tb i {{border-bottom:1px solid var(--ink);height:16px;}}
.score {{background:var(--soft);}}
.tally {{display:flex;align-items:flex-end;gap:6px;}}
.t {{flex:1;display:grid;gap:3px;font:600 7.5px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:center;}}
.t i {{height:30px;border:1.5px solid var(--ink);border-radius:3px;background:#fff;}}
.t em {{font-style:normal;font-size:7.5px;}}
.t.final {{flex:1.4;color:var(--ink);}} .t.final i {{border-width:2.5px;}}
.op {{font:800 18px 'Barlow Condensed',sans-serif;padding-bottom:16px;}}
.rules {{font-size:8.5px;line-height:1.45;color:var(--muted);margin:0;}} .rules b {{color:var(--ink);}}
footer {{display:flex;justify-content:space-between;gap:12px;font:400 7.5px 'IBM Plex Mono',monospace;color:var(--muted);}}
</style></head><body><div class="sheet">
<header><div class="brand">{mark}<div>{wordmark}<p class="kicker">2026 · Field notes</p></div></div>
<h1>Election night ballot<small>Tuesday, November 3, 2026 · A game, not a wager</small></h1>
<div class="who">Name<i></i></div></header>
<div class="key"><b>Key</b><span><span class="bubble"></span>Fill one per race</span><span><span class="ptbox"></span>Check if your pick wins</span><span><span class="inc">★</span>Incumbent</span><span><code>HELD R</code>Party holding it now</span><span><code class="is-d">D</code>Democrat <code class="is-d">I</code>independent <code class="is-r">R</code>Republican</span></div>
<div class="cols"><div class="col">{colhead}{sec["CONTROL"]}{sec["SEN"]}</div><div class="col">{colhead}{sec["GOV"]}<div class="box tbbox"><h3>Tiebreakers</h3>{tbs}</div></div></div>
<div class="bottom"><div class="box score"><h3>Score</h3><div class="tally">{tally}</div>
<p class="rules"><b>How it scores.</b> Count your checks: every correct pick is 1 point, once the AP calls it. Uncalled at the end of the night scores zero for everyone. A tie goes to the closest Senate number, then the House number, then the time. Races: every Senate and governor seat Cook did not rate safe, October 20 to 30, 2026. Play along on the phone at <b>midtermundertow.com/ballot</b>.</p></div></div>
</div></body></html>"""


if __name__ == "__main__":
    rs = races()
    WORK.mkdir(exist_ok=True)
    src = WORK / "ballot-print.html"
    src.write_text(page(rs))
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--virtual-time-budget=5000", f"--print-to-pdf={OUT_PDF}", f"file://{src}"], check=True, capture_output=True)
    print(f"{len(rs)} picks, top score {sum(POINTS[x['cat']] for x in rs)}, wrote {OUT_PDF.relative_to(ROOT)}")
