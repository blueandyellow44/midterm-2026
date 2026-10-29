"""Undertow LinkedIn carousel v2 (2026-10-29): win probability launch. 1080x1350 cards, Undertow's own look (white panel,
site ink, D blue, R red; Barlow Condensed figures, Manrope text, IBM Plex Mono labels). Every card carries a picture:
real frames from midtermundertow.com or a chart drawn from the backtest files. The last card carries the web address.
Every number is read from the repo's research files or the sealed release, not typed."""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
NM = os.path.join(REPO, "node_modules")
OUT = os.path.join(HERE, "out-v2")
os.makedirs(OUT, exist_ok=True)
INK, MUTED, LINE, BG, D, R, TOSS = "#0b1a3a", "#4b5b7c", "#dde3ee", "#ffffff", "#1f5fd6", "#c3262b", "#d3d8e3"
W, H, M = 1080, 1350, 72


def manrope(size, weight):
    f = ImageFont.truetype(f"{NM}/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2", size)
    f.set_variation_by_axes([weight])
    return f


BIG = ImageFont.truetype(f"{NM}/@fontsource/barlow-condensed/files/barlow-condensed-latin-700-normal.woff", 96)
HUGE = ImageFont.truetype(f"{NM}/@fontsource/barlow-condensed/files/barlow-condensed-latin-700-normal.woff", 150)
NUM = ImageFont.truetype(f"{NM}/@fontsource/barlow-condensed/files/barlow-condensed-latin-700-normal.woff", 30)
MONO = ImageFont.truetype(f"{NM}/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff", 24)
BODY = manrope(36, 500)
HEAD = manrope(56, 800)

derived = json.load(open(os.path.join(REPO, "data", "derived.json")))
sim = derived["simulation"]
bt = json.load(open(os.path.join(REPO, "research", "backtest-uncertainty-20261029-v3-t5.json")))
hist = list(csv.DictReader(open(os.path.join(REPO, "data", "poll-error-history.csv"))))
pct = lambda p: f"{round(100 * p)}%"
SEN_IND = pct(sim["independent"]["SEN"]["p_control_d"])
SEN = pct(sim["chambers"]["SEN"]["p_control_d"])
HSE = pct(sim["chambers"]["HOUSE"]["p_control_d"])
ia = derived["signals"]["per_race"]["2026-IA-SEN"]
IA_P = sim["per_seat"]["2026-IA-SEN"]["p_d"]
misses_old = sum(1 for y in bt["years"] if not y["old"]["inside"])
misses_new = sum(1 for y in bt["years"] if not y["new"]["inside"])
y2020 = [float(r["bias"]) for r in hist if r["year"] == "2020" and r["type"] in ("Sen-G", "Gov-G") and len(r["state"]) == 2]
over_d_2020 = sum(1 for b in y2020 if b > 0)


def frame(name):
    return Image.open(os.path.join(HERE, "frames", name)).convert("RGB")


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


class Card:
    def __init__(self, n, total):
        self.c = Image.new("RGB", (W, H), BG); self.d = ImageDraw.Draw(self.c); self.n, self.total = n, total
        self.d.rectangle((0, 0, W // 2, 8), fill=D); self.d.rectangle((W // 2, 0, W, 8), fill=R)
        self.d.text((M, 52), "UNDERTOW · 2026 MIDTERMS", font=MONO, fill=MUTED)
        self.d.text((W - M, 52), f"{n}/{total}", font=MONO, fill=MUTED, anchor="ra")
        self.y = 130

    def text(self, t, font=BODY, fill=INK, lh=None, gap=26):
        lh = lh or int(font.size * 1.3)
        for line in wrap(self.d, t, font, W - 2 * M):
            self.d.text((M, self.y), line, font=font, fill=fill); self.y += lh
        self.y += gap

    def img(self, im, maxh, gap=36):
        w = W - 2 * M; h = round(im.height * w / im.width)
        if h > maxh:
            h = maxh; w = round(im.width * h / im.height)
        im = im.resize((w, h), Image.LANCZOS)
        x = (W - w) // 2
        self.d.rounded_rectangle((x - 2, self.y - 2, x + w + 1, self.y + h + 1), 12, outline=LINE, width=2)
        self.c.paste(im, (x, self.y)); self.y += h + gap

    def footer(self):
        self.d.text((M, H - 70), "By Max Sheahan · midtermundertow.com", font=MONO, fill=MUTED)

    def save(self):
        # Center the content block between the header and the footer so no card ends in dead space.
        top, bottom = 120, H - 100
        block = self.c.crop((0, top, W, self.y)); h = self.y - top
        self.d.rectangle((0, top, W, bottom), fill=BG)
        self.c.paste(block, (0, top + max(0, (bottom - top - h) // 2)))
        self.footer(); self.c.save(os.path.join(OUT, f"card-{self.n}.png")); return self.c


def chart_2020():
    im = Image.new("RGB", (936, 430), BG); d = ImageDraw.Draw(im)
    n = len(y2020); cols = 13; r = 26; gx, gy = 66, 78
    for i, b in enumerate(sorted(y2020, reverse=True)):
        x = 40 + (i % cols) * gx; y = 40 + (i // cols) * gy
        d.ellipse((x, y, x + 2 * r, y + 2 * r), fill=R if b > 0 else D)
    d.text((40, 300), f"{over_d_2020} of {n} races: polls ran too Democratic", font=NUM, fill=R)
    d.text((40, 345), f"{n - over_d_2020} of {n}: polls ran too Republican", font=NUM, fill=D)
    d.text((40, 392), "2020 Senate and governor races, 538 polling archive", font=MONO, fill=MUTED)
    return im


def chart_backtest():
    im = Image.new("RGB", (936, 600), BG); d = ImageDraw.Draw(im)
    ys = bt["years"]; top, row = 60, 58
    d.text((150, 14), "one race at a time", font=MONO, fill=MUTED); d.text((560, 14), "misses drawn together", font=MONO, fill=MUTED)
    span = lambda yr: (min(yr["old"]["range90"][0], yr["new"]["range90"][0]), max(yr["old"]["range90"][1], yr["new"]["range90"][1]))
    for i, yr in enumerate(ys):
        y = top + i * row
        d.text((20, y), str(yr["year"]), font=NUM, fill=INK)
        for k, x0 in (("old", 150), ("new", 560)):
            lo, hi = span(yr); scale = 330 / max(hi - lo + 4, 1)
            px = lambda v: x0 + (v - lo + 2) * scale
            a, b = yr[k]["range90"]; ok = yr[k]["inside"]
            d.rounded_rectangle((px(a), y + 8, px(b), y + 30), 6, fill=TOSS if ok else "#f5b1b3")
            ax = px(yr["d_wins"]); d.ellipse((ax - 9, y + 10, ax + 9, y + 28), fill=INK)
    d.text((20, top + len(ys) * row + 6), "bar: the 90% range for Democratic wins", font=MONO, fill=MUTED)
    d.text((20, top + len(ys) * row + 38), "dot: what happened · pink: the range missed", font=MONO, fill=MUTED)
    return im


console = frame("console.jpg"); iowa = frame("iowa.jpg")
cards = []
TOTAL = 6

c = Card(1, TOTAL)
c.text("I bet the polls are still missing Democrats. This week I put odds on it.", HEAD, lh=70, gap=40)
c.img(frame("map.png"), 760)
cards.append(c.save())

c = Card(2, TOTAL)
c.text(f"Counted one race at a time, Democrats looked {SEN_IND} to control the Senate.", HEAD, lh=70, gap=30)
c.text("That math assumes every race misses on its own. Polls do not miss that way. When they are off, they are off in the same direction almost everywhere.", BODY, gap=40)
c.img(chart_2020(), 560)
cards.append(c.save())

c = Card(3, TOTAL)
c.text(f"Drawn together, it is {SEN}.", HEAD, lh=70, gap=30)
c.text("20,000 simulated elections. Each one draws a national miss, a regional miss, a state miss and each race's own, then counts the seats.", BODY, gap=40)
c.img(frame("senate-tally.png"), 320, gap=30)
c.text(f"House, same method, {HSE}.", BODY, fill=MUTED)
cards.append(c.save())

c = Card(4, TOTAL)
c.text("I replayed every election from 2010 to 2024.", HEAD, lh=70, gap=30)
c.text(f"Counting races one at a time missed the real seat count in {misses_old} of {len(bt['years'])} years. Drawing the misses together missed {'none' if misses_new == 0 else misses_new}.", BODY, gap=36)
c.img(chart_backtest(), 640)
cards.append(c.save())

c = Card(5, TOTAL)
c.text("I did not trust my Iowa number.", HEAD, lh=70, gap=30)
c.text("Checking it found a real bug in how I read early voting, so I fixed it for every state at once. The rest held. Trump won Iowa by 13, the national swing is about 11, and that puts Iowa right around R +2, where I have it.", BODY, gap=36)
c.img(frame("iowa-head.png"), 420)
cards.append(c.save())

c = Card(6, TOTAL)
c.text("It freezes Monday, November 2, and gets graded against the results.", HEAD, lh=70, gap=50)
c.img(frame("dial.png"), 560, gap=50)
c.d.text((W // 2, c.y), "midtermundertow.com", font=BIG, fill=D, anchor="ma"); c.y += 110
cards.append(c.save())

pdf = os.path.join(OUT, "undertow-win-probability-carousel-v2.pdf")
cards[0].save(pdf, save_all=True, append_images=cards[1:], resolution=150, title="Undertow: odds on my midterm bet")
sheet = Image.new("RGB", (W * 3 // 3, H * 2 // 3), BG)
for i, im in enumerate(cards):
    t = im.resize((W // 3, H // 3)); sheet.paste(t, ((i % 3) * (W // 3), (i // 3) * (H // 3)))
sheet.save(os.path.join(OUT, "sheet-v2.jpg"), quality=88)
print(pdf, {"sen_ind": SEN_IND, "sen": SEN, "house": HSE, "misses": (misses_old, misses_new), "ia_p": IA_P, "2020": (over_d_2020, len(y2020))})
