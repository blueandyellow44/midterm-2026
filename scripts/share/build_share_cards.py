#!/usr/bin/env python3
"""Per-race share images from the synced release (data/derived.json).

1200x630 link previews (Facebook, texts) -> public/og/<slug>.png; the home preview -> public/og.png; favicon -> public/favicon.svg/.png
1080x1350 portrait cards (Instagram feed) -> public/share/<slug>.png
Every number comes from derived.json; this script only formats. All text is outlined to vector paths with the site's
own fonts (Manrope, IBM Plex Mono) so the cards render identically anywhere. Rasterized with sharp via node.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = Path(__file__).resolve().parent / "fonts"
C = {"paper": "#ffffff", "ink": "#0b1a3a", "muted": "#4b5b7c", "red": "#c3262b", "d": "#1b4fc4", "r": "#c3262b", "d_bar": "#1f5fd6", "r_bar": "#c3262b", "line": "#dde3ee", "soft": "#f4f6fa"}
STATES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "CA": "California", "CO": "Colorado", "FL": "Florida", "GA": "Georgia", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina", "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NV": "Nevada", "NY": "New York", "OH": "Ohio", "PA": "Pennsylvania", "SC": "South Carolina", "TX": "Texas", "VA": "Virginia", "WA": "Washington", "WI": "Wisconsin"}
EVEN = 0.05


class Face:
    def __init__(self, path: Path):
        self.f = TTFont(str(path))
        self.gs, self.cmap, self.hm, self.upm = self.f.getGlyphSet(), self.f.getBestCmap(), self.f["hmtx"], self.f["head"].unitsPerEm

    def path(self, text: str, size: float, x: float, y: float, track: float = 0.0) -> tuple[str, float]:
        pen, s, cx = SVGPathPen(self.gs), size / self.upm, x
        for ch in text:
            g = self.cmap.get(ord(ch)) or self.cmap.get(ord("?"))
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            cx += self.hm[g][0] * s + track * size
        return pen.getCommands(), cx - x


BOLD, MED, MONO = Face(FONTS / "manrope-800.ttf"), Face(FONTS / "manrope-500.ttf"), Face(FONTS / "plexmono-400.ttf")
NUM = Face(FONTS / "barlow-condensed-800.woff")   # condensed numerals, as on the site


def fit(face: Face, s: str, size: float, width: float) -> float:
    w = face.path(s, size, 0, 0)[1]
    return size if w <= width else size * width / w


def text(face: Face, s: str, size: float, x: float, y: float, fill: str, track: float = 0.0) -> tuple[str, float]:
    d, w = face.path(s, size, x, y, track)
    return f'<path d="{d}" fill="{fill}"/>', w


def surname(n: str) -> str:
    return n.strip().split()[-1]


def side(m: float, names: dict) -> tuple[str, str]:
    if abs(m) < EVEN:
        return "Even", C["ink"]
    return (f"{surname(names['D'])} +{abs(m):.1f}", C["d"]) if m > 0 else (f"{surname(names['R'])} +{abs(m):.1f}", C["r"])


def ordinal(n: int) -> str:
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def race_name(rid: str) -> str:
    st = rid.split("-")[1]
    if rid.endswith("-HOUSE"):
        d = rid.split("-")[2]
        return f"{STATES[st]} {'at-large' if d == 'AL' else ordinal(int(d))} District"
    return f"{STATES[st]} {'governor' if 'GOV' in rid else 'Senate'}{' special' if 'SPECIAL' in rid else ''}"


def office_word(rid: str) -> str:
    return "HOUSE" if rid.endswith("-HOUSE") else "GOVERNOR" if "GOV" in rid else "SENATE"


def mark(x: float, y: float, s: float, ink: str, swirl: str) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})"><path d="M8 30h104" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M24 30v34a36 36 0 0 0 72 0V30" stroke="{ink}" stroke-width="14" fill="none"/>'
            f'<path d="M60 46c10 0 16 8 16 16s-7 15-16 15-14-6-14-12 5-10 10-10 8 3 8 7" stroke="{swirl}" stroke-width="6" fill="none" stroke-linecap="round"/></g>')


def brand(x: float, y: float, s: float, word: str) -> str:
    return (mark(x, y, s, C["ink"], C["red"]) +
            f'<defs><clipPath id="wt"><rect x="-10" y="-120" width="480" height="95"/></clipPath><clipPath id="wb"><rect x="-10" y="-25" width="480" height="40"/></clipPath></defs>'
            f'<g transform="translate({x + 150 * s} {y + 92 * s}) scale({0.62 * s})"><path d="{word}" fill="{C["ink"]}" clip-path="url(#wt)"/>'
            f'<g clip-path="url(#wb)"><path d="{word}" fill="{C["red"]}" transform="translate(9 0)"/></g></g>')


def rule(w: float, h: float = 8) -> str:
    return f'<rect width="{w / 2}" height="{h}" fill="{C["d_bar"]}"/><rect x="{w / 2}" width="{w / 2}" height="{h}" fill="{C["r_bar"]}"/>'


def track(x: float, y: float, w: float, h: float, v: float, tick: float, span: float = 20) -> str:
    at = lambda m: x + w * (0.5 + 0.5 * max(-span, min(span, m)) / span)
    mid, p = x + w / 2, at(v)
    color = C["d_bar"] if v >= 0 else C["r_bar"]
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 4}" fill="{C["soft"]}"/>'
            f'<rect x="{min(mid, p)}" y="{y + h * 0.18}" width="{abs(p - mid)}" height="{h * 0.64}" rx="{h / 6}" fill="{color}"/>'
            f'<rect x="{mid - 1}" y="{y - 4}" width="2" height="{h + 8}" fill="{C["muted"]}"/>'
            f'<rect x="{at(tick) - 2}" y="{y - 6}" width="4" height="{h + 12}" fill="{C["ink"]}"/>')


def card(rid: str, s: dict, names: dict, word: str, portrait: bool) -> str:
    w, h = (1080, 1350) if portrait else (1200, 630)
    pad = 80 if portrait else 64
    polls, pc = side(s["polling_margin"], names)
    mine, mc = side(s["adjusted_margin"], names)
    dt = s["delta_total"]
    pull, pullc = ("None", C["ink"]) if abs(dt) < EVEN else (f"{abs(dt):.1f} toward {('I' if rid in ('2026-NE-SEN', '2026-AK-AL-HOUSE') else 'D') if dt > 0 else 'R'}", C["d"] if dt > 0 else C["r"])
    st = rid.split("-")[1]
    kicker = f"2026 · {st} · {office_word(rid)}{' · SPECIAL' if 'SPECIAL' in rid else ''}"
    parts = [f'<rect width="{w}" height="{h}" fill="{C["paper"]}"/>', rule(w)]
    if portrait:
        parts.append(brand(pad, 70, 0.6, word))
        parts.append(text(MONO, kicker, 24, pad, 250, C["muted"], 0.12)[0])
        parts.append(text(BOLD, race_name(rid), 76, pad, 340, C["ink"], -0.02)[0])
        d, dw = text(MED, f"{names['D']} ({'I' if rid in ('2026-NE-SEN', '2026-AK-AL-HOUSE') else 'D'})", 34, pad, 400, C["d"])
        v_, vw = text(MED, " vs ", 34, pad + dw, 400, C["ink"])
        r, _ = text(MED, f"{names['R']} (R)", 34, pad + dw + vw, 400, C["r"])
        parts += [d, v_, r, f'<rect x="{pad}" y="450" width="{w - 2 * pad}" height="2" fill="{C["line"]}"/>']
        rows = (("POLLS", polls, pc, "weighted average of the polls"), ("UNDERTOW", mine, mc, f"± {s['range_sd']:.1f} · my call, frozen Nov 2"), ("THE PULL", pull, pullc, "Undertow minus the polls"))
        for i, (label, val, color, sub) in enumerate(rows):
            y = 530 + i * 190
            parts.append(text(MONO, label, 24, pad, y, C["muted"], 0.14)[0])
            parts.append(text(NUM, val, fit(NUM, val, 120, w - 2 * pad), pad, y + 118, color)[0])
            parts.append(text(MED, sub, 26, pad, y + 156, C["muted"])[0])
        parts.append(track(pad, 1130, w - 2 * pad, 30, s["adjusted_margin"], s["polling_margin"]))
        parts.append(text(MONO, names['R'].split()[-1], 22, pad, 1200, C["r"])[0])
        rt, rtw = MONO.path(names['D'].split()[-1], 22, 0, 0)
        parts.append(text(MONO, names['D'].split()[-1], 22, w - pad - rtw, 1200, C["d"])[0])
        fy = h - 60
    else:
        parts.append(brand(pad, 34, 0.4, word))
        kw = MONO.path(kicker, 18, 0, 0, 0.12)[1]
        parts.append(text(MONO, kicker, 18, w - pad - kw, 78, C["muted"], 0.12)[0])
        parts.append(text(BOLD, race_name(rid), 54, pad, 190, C["ink"], -0.02)[0])
        d, dw = text(MED, f"{names['D']} ({'I' if rid in ('2026-NE-SEN', '2026-AK-AL-HOUSE') else 'D'})", 26, pad, 236, C["d"])
        v_, vw = text(MED, " vs ", 26, pad + dw, 236, C["ink"])
        r, _ = text(MED, f"{names['R']} (R)", 26, pad + dw + vw, 236, C["r"])
        parts += [d, v_, r, f'<rect x="{pad}" y="268" width="{w - 2 * pad}" height="2" fill="{C["line"]}"/>']
        colw = (w - 2 * pad) / 3
        for i, (label, val, color, sub) in enumerate((("POLLS", polls, pc, "weighted average"), ("UNDERTOW", mine, mc, f"± {s['range_sd']:.1f} · frozen Nov 2"), ("THE PULL", pull, pullc, "Undertow minus the polls"))):
            x = pad + i * colw
            parts.append(text(MONO, label, 17, x, 312, C["muted"], 0.14)[0])
            parts.append(text(NUM, val, fit(NUM, val, 74, colw - 24), x, 388, color)[0])
            parts.append(text(MED, sub, 18, x, 420, C["muted"])[0])
        parts.append(track(pad, 466, w - 2 * pad, 22, s["adjusted_margin"], s["polling_margin"]))
        parts.append(text(MONO, names['R'].split()[-1], 16, pad, 516, C["r"])[0])
        rtw = MONO.path(names['D'].split()[-1], 16, 0, 0)[1]
        parts.append(text(MONO, names['D'].split()[-1], 16, w - pad - rtw, 516, C["d"])[0])
        fy = h - 34
    parts.append(f'<rect x="{pad}" y="{fy - (44 if portrait else 32)}" width="{w - 2 * pad}" height="2" fill="{C["line"]}"/>')
    parts.append(text(MONO, "midtermundertow.com · by Max Sheahan · bar: Undertow · tick: polls", 22 if portrait else 17, pad, fy, C["muted"])[0])
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


def home_card(per: dict, derived: dict, word: str) -> str:
    """The home link preview: the headline and the six biggest pulls, as a board."""
    w, h, pad = 1200, 630, 64
    miss = (derived.get("signals") or {}).get("rules", {}).get("poll_error_2025_miss")
    head = f"POLLS HAVE MISSED DEMOCRATS BY {miss:.1f} SINCE LAST FALL." if isinstance(miss, (int, float)) else "WHERE THE 2026 POLLS ARE LIKELY WRONG."
    parts = [f'<rect width="{w}" height="{h}" fill="{C["paper"]}"/>', rule(w), brand(pad, 34, 0.4, word)]
    kw = MONO.path(f"{len(per)} RACES · FROZEN NOV 2", 18, 0, 0, 0.12)[1]
    parts.append(text(MONO, f"{len(per)} RACES · FROZEN NOV 2", 18, w - pad - kw, 78, C["muted"], 0.12)[0])
    parts.append(text(NUM, head, 50, pad, 170, C["ink"])[0])
    parts.append(text(NUM, "I THINK THEY ARE MISSING IT AGAIN.", 50, pad, 222, C["muted"])[0])
    top = sorted(per.items(), key=lambda kv: -abs(kv[1]["delta_total"]))[:6]
    for i, (rid, s) in enumerate(top):
        y = 268 + i * 50
        c = (derived.get("candidates") or {}).get(rid) or derived["section9_heat"]["per_race"][rid]["candidates"]
        names = {"D": c["D"]["candidate"], "R": c["R"]["candidate"]}
        val, color = side(s["adjusted_margin"], names)
        st = rid.split("-")[1]
        parts.append(text(BOLD, f"{st}-{rid.split('-')[2]}" if rid.endswith("-HOUSE") else f"{st} {'GOV' if 'GOV' in rid else 'SEN'}", 22, pad, y + 26, C["ink"])[0])
        parts.append(track(pad + 110, y + 8, 760, 20, s["adjusted_margin"], s["polling_margin"]))
        vw = NUM.path(val, 34, 0, 0)[1]
        parts.append(text(NUM, val, 34, w - pad - vw, y + 30, color)[0])
    parts.append(f'<rect x="{pad}" y="{h - 66}" width="{w - 2 * pad}" height="2" fill="{C["line"]}"/>')
    parts.append(text(MONO, "midtermundertow.com · by Max Sheahan · bar: Undertow · tick: polls", 17, pad, h - 34, C["muted"])[0])
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


def favicon() -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><clipPath id="t"><rect width="64" height="64" rx="14"/></clipPath></defs>'
            f'<g clip-path="url(#t)"><rect width="64" height="64" fill="{C["ink"]}"/><rect x="0" y="56" width="32" height="8" fill="{C["d_bar"]}"/><rect x="32" y="56" width="32" height="8" fill="{C["r_bar"]}"/></g>'
            f'<path d="M8 14h48" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/><path d="M16 14v16a16 16 0 0 0 32 0V14" stroke="#ffffff" stroke-width="8" fill="none"/>'
            f'<path d="M32 22c5 0 8 4 8 8s-3.5 7.5-8 7.5-7-3-7-6 2.5-5 5-5 4 1.5 4 3.5" stroke="#ff6f72" stroke-width="3.5" fill="none" stroke-linecap="round"/></svg>')


def main() -> int:
    derived = json.loads((ROOT / "data/derived.json").read_text())
    per = (derived.get("signals") or {}).get("per_race")
    if not per:
        raise SystemExit("no signals block in data/derived.json: sync a signals release first")
    # Only races with a reading get a card: districts with no public polls are listed on the site without a number.
    cands = derived.get("candidates") or {rid: v["candidates"] for rid, v in derived["section9_heat"]["per_race"].items()}
    per = {rid: s for rid, s in per.items() if isinstance(s.get("adjusted_margin"), (int, float)) and rid in cands}
    word = json.loads((ROOT / "lib/brand/wordmark-paths.json").read_text())["lower"]["d"]
    jobs = []
    with tempfile.TemporaryDirectory() as tmp:
        for rid, s in per.items():
            for k in ("polling_margin", "adjusted_margin", "delta_total", "range_sd"):
                if not isinstance(s.get(k), (int, float)):
                    raise SystemExit(f"incomplete reading for {rid}: {k}")
            c = cands[rid]
            names = {"D": c["D"]["candidate"], "R": c["R"]["candidate"]}
            slug = rid.replace("2026-", "").lower()
            for portrait, out in ((False, ROOT / "public/og" / f"{slug}.png"), (True, ROOT / "public/share" / f"{slug}.png")):
                out.parent.mkdir(parents=True, exist_ok=True)
                src = Path(tmp) / f"{slug}-{int(portrait)}.svg"
                src.write_text(card(rid, s, names, word, portrait))
                jobs.append([str(src), str(out)])
        (ROOT / "public/favicon.svg").write_text(favicon())
        jobs.append([str(ROOT / "public/favicon.svg"), str(ROOT / "public/favicon.png"), 512])
        jobs.append([str(ROOT / "public/favicon.svg"), str(ROOT / "public/apple-touch-icon.png"), 180])
        hsrc = Path(tmp) / "home.svg"
        hsrc.write_text(home_card(per, derived, word))
        (ROOT / "public/og.svg").write_text(hsrc.read_text())
        jobs.append([str(hsrc), str(ROOT / "public/og.png")])
        js = "const sharp=require('sharp');const jobs=JSON.parse(process.argv[1]);Promise.all(jobs.map(([a,b,z])=>(z?sharp(a,{density:600}).resize(z,z):sharp(a)).png().toFile(b))).then(()=>console.log('ok'))"
        subprocess.run(["node", "-e", js, json.dumps(jobs)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print(f"share cards: {len(per)} races x 2 sizes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
