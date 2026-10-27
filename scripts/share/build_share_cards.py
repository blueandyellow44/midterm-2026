#!/usr/bin/env python3
"""Per-race share images from the synced release (data/derived.json).

1200x630 link previews (Facebook, texts) -> public/og/<slug>.png
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
C = {"paper": "#f7f7f2", "ink": "#24272b", "muted": "#5c6268", "rust": "#a54816", "d": "#285b98", "r": "#a7474b", "line": "#ddddd5"}
STATES = {"TX": "Texas", "IA": "Iowa", "ME": "Maine", "AK": "Alaska", "OH": "Ohio", "MI": "Michigan", "NC": "North Carolina", "GA": "Georgia", "WI": "Wisconsin"}
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


def text(face: Face, s: str, size: float, x: float, y: float, fill: str, track: float = 0.0) -> tuple[str, float]:
    d, w = face.path(s, size, x, y, track)
    return f'<path d="{d}" fill="{fill}"/>', w


def surname(n: str) -> str:
    return n.strip().split()[-1]


def side(m: float, names: dict) -> tuple[str, str]:
    if abs(m) < EVEN:
        return "Even", C["ink"]
    return (f"{surname(names['D'])} +{abs(m):.1f}", C["d"]) if m > 0 else (f"{surname(names['R'])} +{abs(m):.1f}", C["r"])


def race_name(rid: str) -> str:
    return f"{STATES[rid.split('-')[1]]} {'governor' if 'GOV' in rid else 'Senate'}{' special' if 'SPECIAL' in rid else ''}"


def brand(x: float, y: float, s: float, word: str) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})"><path d="M8 30h104" stroke="{C["ink"]}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M24 30v34a36 36 0 0 0 72 0V30" stroke="{C["ink"]}" stroke-width="14" fill="none"/>'
            f'<path d="M60 46c10 0 16 8 16 16s-7 15-16 15-14-6-14-12 5-10 10-10 8 3 8 7" stroke="{C["rust"]}" stroke-width="6" fill="none" stroke-linecap="round"/></g>'
            f'<defs><clipPath id="wt"><rect x="-10" y="-120" width="480" height="95"/></clipPath><clipPath id="wb"><rect x="-10" y="-25" width="480" height="40"/></clipPath></defs>'
            f'<g transform="translate({x + 150 * s} {y + 92 * s}) scale({0.62 * s})"><path d="{word}" fill="{C["ink"]}" clip-path="url(#wt)"/>'
            f'<g clip-path="url(#wb)"><path d="{word}" fill="{C["rust"]}" transform="translate(9 0)"/></g></g>')


def card(rid: str, s: dict, names: dict, word: str, portrait: bool) -> str:
    w, h = (1080, 1350) if portrait else (1200, 630)
    L = (dict(pad=90, brand_y=90, brand_s=0.62, title=72, title_y=330, label=26, polls=56, mine=104, pull=72, rows=(460, 650, 870), foot=22)
         if portrait else dict(pad=70, brand_y=46, brand_s=0.42, title=48, title_y=160, label=19, polls=38, mine=70, pull=48, rows=(200, 300, 432), foot=20))
    polls, pc = side(s["polling_margin"], names)
    mine, mc = side(s["adjusted_margin"], names)
    dt = s["delta_total"]
    pull, pullc = ("none", C["ink"]) if abs(dt) < EVEN else (f"{abs(dt):.1f} toward {surname(names['D'] if dt > 0 else names['R'])}", C["d"] if dt > 0 else C["r"])
    parts = [f'<rect width="{w}" height="{h}" fill="{C["paper"]}"/>', brand(L["pad"], L["brand_y"], L["brand_s"], word)]
    parts.append(text(BOLD, race_name(rid), L["title"], L["pad"], L["title_y"], C["ink"], -0.02)[0])
    for (label, val, size, face, color), y in zip((("POLLS", polls, L["polls"], MED, C["muted"]), ("UNDERTOW", mine, L["mine"], BOLD, mc), ("THE PULL", pull, L["pull"], BOLD, pullc)), L["rows"]):
        parts.append(text(MONO, label, L["label"], L["pad"], y, C["muted"], 0.14)[0])
        svg, vw = text(face, val, size, L["pad"], y + L["label"] * 0.6 + size, color, -0.02)
        parts.append(svg)
        if label == "UNDERTOW":
            parts.append(text(MED, f"± {s['range_sd']:.1f}", size * 0.42, L["pad"] + vw + size * 0.18, y + L["label"] * 0.6 + size, C["muted"])[0])
    if portrait:
        for i, line in enumerate(("The pull is how far last fall’s polling miss", "and outside money move this race off its polls.")):
            parts.append(text(MED, line, 32, L["pad"], 1080 + i * 46, C["ink"])[0])
    fy = h - (90 if portrait else 46)
    parts.append(f'<rect x="{L["pad"]}" y="{fy - (60 if portrait else 40)}" width="{w - 2 * L["pad"]}" height="2" fill="{C["line"]}"/>')
    parts.append(text(MONO, "midtermundertow.com · by Max Sheahan · frozen Nov 2, graded after", L["foot"], L["pad"], fy, C["muted"])[0])
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


def main() -> int:
    derived = json.loads((ROOT / "data/derived.json").read_text())
    per = (derived.get("signals") or {}).get("per_race")
    if not per:
        raise SystemExit("no signals block in data/derived.json: sync a signals release first")
    word = json.loads((ROOT / "lib/brand/wordmark-paths.json").read_text())["lower"]["d"]
    jobs = []
    with tempfile.TemporaryDirectory() as tmp:
        for rid, s in per.items():
            for k in ("polling_margin", "adjusted_margin", "delta_total", "range_sd"):
                if not isinstance(s.get(k), (int, float)):
                    raise SystemExit(f"incomplete reading for {rid}: {k}")
            c = derived["section9_heat"]["per_race"][rid]["candidates"]
            names = {"D": c["D"]["candidate"], "R": c["R"]["candidate"]}
            slug = rid.replace("2026-", "").lower()
            for portrait, out in ((False, ROOT / "public/og" / f"{slug}.png"), (True, ROOT / "public/share" / f"{slug}.png")):
                out.parent.mkdir(parents=True, exist_ok=True)
                src = Path(tmp) / f"{slug}-{int(portrait)}.svg"
                src.write_text(card(rid, s, names, word, portrait))
                jobs.append([str(src), str(out)])
        js = "const sharp=require('sharp');const jobs=JSON.parse(process.argv[1]);Promise.all(jobs.map(([a,b])=>sharp(a).png().toFile(b))).then(()=>console.log('ok'))"
        subprocess.run(["node", "-e", js, json.dumps(jobs)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print(f"share cards: {len(per)} races x 2 sizes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
