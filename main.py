#!/usr/bin/env python3
"""Render entry.png (1024x1024): an editorial front-page poster that sums up
19 November 2026 world news in one image -- a lead story, four panels, and a
dense 37-item sourced wire section (42 stories in total, date-checked).
Everything is drawn in code with Pillow -- crisp vector-style shapes and real
rendered text, so every headline stays legible (unlike AI-generated images).
Run:  python3 main.py   ->  writes /output/entry.png (and entry.png here).
Deterministic: same input always produces byte-identical output.
"""

import glob
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = "/output"
OUT = os.path.join(OUT_DIR, "entry.png")
LOCAL = os.path.join(HERE, "entry.png")

W = H = 1024
PAPER = (247, 242, 231)   # #f7f2e7
INK = (25, 25, 34)        # #191922
RED = (179, 49, 42)       # #b3312a
NAVY = (20, 64, 107)      # #14406b
GOLD = (201, 162, 39)     # #c9a227
SMOKE = (150, 144, 128)
WHITE = (255, 255, 255)
TEAL = (31, 110, 96)      # #1f6e60

MARGIN = 44
CONTENT_W = W - 2 * MARGIN  # 936


# ---------------------------------------------------------------- fonts ----
def find_font(*patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    raise FileNotFoundError(patterns)


BOLD_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/LiberationSans-Bold.ttf",
)
REG_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/**/NotoSans-Regular.ttf",
    "/usr/share/fonts/**/LiberationSans-Regular.ttf",
)

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def bold(size):
    return font(BOLD_PATH, size)


def regular(size):
    return font(REG_PATH, size)


# ------------------------------------------------------------ text utils ----
_probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def text_w(text, fnt):
    return _probe.textlength(text, font=fnt)


def wrap(text, fnt, max_w):
    """Greedy word wrap measured with the real font metrics."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(text, path, start, minimum, max_w, max_h, lh_factor=1.18,
              max_lines=None):
    """Shrink the font until the wrapped block fits the box.

    Returns (font, lines, line_height, total_height)."""
    size = start
    while size >= minimum:
        fnt = font(path, size)
        lines = wrap(text, fnt, max_w)
        lh = int(size * lh_factor)
        total = lh * len(lines)
        if total <= max_h and (max_lines is None or len(lines) <= max_lines):
            return fnt, lines, lh, total
        size -= 1
    fnt = font(path, minimum)
    lines = wrap(text, fnt, max_w)
    lh = int(minimum * lh_factor)
    return fnt, lines, lh, lh * len(lines)


def draw_lines(d, x, y, lines, fnt, lh, fill, align="left", box_w=None):
    for line in lines:
        if align == "center":
            lx = x + (box_w - text_w(line, fnt)) / 2
        else:
            lx = x
        d.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def draw_tracked(d, x, y, text, fnt, fill, tracking=3):
    """Draw letterspaced caps (for kickers); returns the end x."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=fnt, fill=fill)
        cx += text_w(ch, fnt) + tracking
    return cx - tracking


REPORT = []


def note(name, box, used_h, lines=None):
    REPORT.append((name, box, used_h, lines))


# ------------------------------------------------------------- pictograms ----
def pic_summit(d, x, y, w, h):
    """Shenzhen summit, compact: three flag poles over a summit table band."""
    base = y + h
    # thin gold rule above the table
    d.rectangle([x, base - 24, x + w, base - 20], fill=GOLD)
    # summit table band
    d.rectangle([x, base - 18, x + w, base - 6], fill=INK)
    d.rectangle([x, base - 4, x + w, base], fill=NAVY)
    # three flag poles, one flag each (red / navy / gold)
    for i, col in enumerate((RED, NAVY, GOLD)):
        px = x + w * (0.20 + 0.30 * i)
        top = y + 4 + (8 if i == 1 else 0)
        d.line([px, top, px, base - 18], fill=INK, width=5)
        fw, fh = 56, 32
        d.polygon([(px, top), (px + fw, top + 4), (px + fw - 8, top + fh / 2),
                   (px + fw, top + fh - 4), (px, top + fh)], fill=col,
                  outline=INK)
        d.ellipse([px - 4, top - 5, px + 4, top + 3], fill=GOLD)


def pic_tanker(d, x, y, s):
    """Oil tanker on waves with a burst of flame and mine dots."""
    # sea: three stacked wave bands
    for i, yy in enumerate((0.72, 0.82, 0.92)):
        col = NAVY if i % 2 == 0 else TEAL
        d.rectangle([x, y + s * yy, x + s, y + s * (yy + 0.06)], fill=col)
    # hull
    d.polygon([(x + s * 0.08, y + s * 0.62), (x + s * 0.92, y + s * 0.62),
               (x + s * 0.84, y + s * 0.74), (x + s * 0.16, y + s * 0.74)],
              fill=INK)
    # deck tanks (three cylinders)
    for f in (0.24, 0.44, 0.64):
        cx = x + s * f
        d.ellipse([cx - 13, y + s * 0.50, cx + 13, y + s * 0.62], fill=WHITE,
                  outline=INK, width=3)
    # funnel
    d.rectangle([x + s * 0.78, y + s * 0.44, x + s * 0.88, y + s * 0.62],
                fill=RED)
    # flame burst above the bow: jagged star in gold with red core
    cx, cy = x + s * 0.20, y + s * 0.30
    star = []
    for i in range(16):
        r = s * (0.24 if i % 2 == 0 else 0.11)
        a = -math.pi / 2 + i * math.pi / 8
        star.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star, fill=GOLD)
    star2 = []
    for i in range(12):
        r = s * (0.13 if i % 2 == 0 else 0.06)
        a = -math.pi / 2 + i * math.pi / 6
        star2.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star2, fill=RED)
    # sea mines: spiked dots drifting right of the ship
    for fx, fy in ((0.68, 0.86), (0.86, 0.80)):
        mx, my = x + s * fx, y + s * fy
        d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=INK)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            d.line([mx + 7 * math.cos(a), my + 7 * math.sin(a),
                    mx + 12 * math.cos(a), my + 12 * math.sin(a)],
                   fill=INK, width=2)


def pic_scales(d, x, y, s):
    """Scales of justice under a courthouse pediment."""
    cx = x + s / 2
    # pediment
    d.polygon([(x + 4, y + s * 0.26), (x + s - 4, y + s * 0.26),
               (cx, y + s * 0.04)], fill=NAVY)
    d.rectangle([x + 8, y + s * 0.28, x + s - 8, y + s * 0.33], fill=NAVY)
    # central pillar
    d.line([cx, y + s * 0.33, cx, y + s * 0.82], fill=INK, width=6)
    d.ellipse([cx - 7, y + s * 0.30, cx + 7, y + s * 0.30 + 14], fill=GOLD,
              outline=INK, width=2)
    # beam
    d.line([x + s * 0.14, y + s * 0.42, x + s * 0.86, y + s * 0.42],
           fill=INK, width=6)
    # two pans hanging from the beam ends
    for fx in (0.14, 0.86):
        px = x + s * fx
        d.line([px, y + s * 0.42, px - 16, y + s * 0.62], fill=INK, width=3)
        d.line([px, y + s * 0.42, px + 16, y + s * 0.62], fill=INK, width=3)
        d.line([px, y + s * 0.42, px, y + s * 0.62], fill=INK, width=3)
        d.pieslice([px - 22, y + s * 0.60, px + 22, y + s * 0.78],
                   start=0, end=180, fill=GOLD, outline=INK, width=3)
    # base
    d.rectangle([x + s * 0.30, y + s * 0.84, x + s * 0.70, y + s * 0.88],
                fill=INK)
    d.rectangle([x + s * 0.22, y + s * 0.90, x + s * 0.78, y + s * 0.95],
                fill=NAVY)


def pic_bridge(d, x, y, s):
    """Kerch Bridge: deck with a broken gap, twin pylons, rail line."""
    # pylons
    for fx in (0.24, 0.76):
        px = x + s * fx
        d.rectangle([px - 6, y + s * 0.14, px + 6, y + s * 0.66], fill=INK)
        d.ellipse([px - 9, y + s * 0.10, px + 9, y + s * 0.10 + 18],
                  fill=GOLD, outline=INK, width=2)
    # suspension cables from the pylon tops to the deck
    for fx, tx in ((0.24, 0.44), (0.24, 0.04), (0.76, 0.56), (0.76, 0.96)):
        d.line([x + s * fx, y + s * 0.14, x + s * tx, y + s * 0.60],
               fill=NAVY, width=3)
    # deck, split in two by a blast gap in the middle
    d.rectangle([x + 4, y + s * 0.60, x + s * 0.44, y + s * 0.68], fill=INK)
    d.rectangle([x + s * 0.56, y + s * 0.60, x + s - 4, y + s * 0.68],
                fill=INK)
    # rail line on the deck (broken at the gap)
    for seg in ((0.06, 0.44), (0.56, 0.94)):
        d.line([x + s * seg[0], y + s * 0.64, x + s * seg[1], y + s * 0.64],
               fill=GOLD, width=4)
    # smoke plume rising from the gap
    for i in range(5):
        t = i / 4.0
        cx = x + s * (0.50 + 0.02 * t)
        cy = y + s * (0.52 - 0.12 * t)
        r = 4 + 6 * t
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SMOKE)
    # water below
    d.rectangle([x, y + s * 0.80, x + s, y + s * 0.85], fill=TEAL)
    d.rectangle([x, y + s * 0.90, x + s, y + s * 0.94], fill=NAVY)


def pic_controller(d, x, y, s):
    """Game controller with a gold star burst above it."""
    # star burst
    cx, cy = x + s / 2, y + s * 0.20
    star = []
    for i in range(16):
        r = s * (0.17 if i % 2 == 0 else 0.08)
        a = -math.pi / 2 + i * math.pi / 8
        star.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star, fill=GOLD)
    # controller body
    d.rounded_rectangle([x + s * 0.10, y + s * 0.44, x + s * 0.90,
                         y + s * 0.82], radius=18, fill=INK)
    # grips
    d.rounded_rectangle([x + s * 0.06, y + s * 0.68, x + s * 0.26,
                         y + s * 0.98], radius=12, fill=INK)
    d.rounded_rectangle([x + s * 0.74, y + s * 0.68, x + s * 0.94,
                         y + s * 0.98], radius=12, fill=INK)
    # d-pad (left)
    dcx, dcy = x + s * 0.28, y + s * 0.62
    d.rectangle([dcx - 8, dcy - 20, dcx + 8, dcy + 20], fill=GOLD)
    d.rectangle([dcx - 20, dcy - 8, dcx + 20, dcy + 8], fill=GOLD)
    # action buttons (right): four dots
    for fx, fy, col in ((0.68, 0.55, RED), (0.78, 0.62, GOLD),
                        (0.68, 0.70, WHITE), (0.58, 0.62, TEAL)):
        bx, by = x + s * fx, y + s * fy
        d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=col, outline=WHITE,
                  width=2)
    # centre home button
    d.ellipse([x + s * 0.47, y + s * 0.57, x + s * 0.53, y + s * 0.63],
              fill=RED)


# ------------------------------------------------------------- wire items ----
# 37 one-line stories for "THE DAY IN BRIEF": the 29 briefed items plus 8
# more verified from today's Scoop/RNZ, Outlook India and Manila Times
# newswires. Tags are the reporting outlet; PFNZ = Palestine Forum of New
# Zealand, ICHRP = the rights group that reported the release, CAN =
# Climate Action Network.
WIRE = [
    ("RNZ", "RIO TINTO PAYS $250M OVER BOUGAINVILLE MINE DAMAGE"),
    ("RNZ", "TONGA DECLARES EMERGENCY AS EL NIÑO DROUGHT BITES"),
    ("RNZ", "U.S. BOOSTS PACIFIC ISLANDS FUNDING BY $450M"),
    ("SAVE THE CHILDREN", "1 IN 4 CHILDREN NOW LIVE IN CONFLICT ZONES — RECORD"),
    ("ICHRP", "236 ANTI-TRUMP PROTESTERS FREED"),
    ("PFNZ", "GAZA ESCALATION THREATENS CIVILIANS, DISPLACEMENT GROWS"),
    ("DAILY MIRROR", "DOZENS MISSING AS MIGRANT BOAT SINKS OFF SENEGAL"),
    ("REPORT", "CHINA SEEKS ADVANCED NVIDIA CHIPS FOR AI WEAPONS"),
    ("DAILY MIRROR", "MIAMI COURT CONVICTS PASTOR OVER HAITI PRESIDENT KILLING"),
    ("JAPAN TIMES", "SOUTH KOREA COURT ORDERS RETRIAL OF EX-PM HAN"),
    ("JUST SECURITY", "DENMARK, GREENLAND, U.S. SEAL ARCTIC SECURITY DEAL"),
    ("JUST SECURITY", "JAPAN'S TAKAICHI TALKS WITH PUTIN, VOWS TO KEEP TALKING"),
    ("JUST SECURITY", "IAEA: NORTH KOREA EXPANDS YONGBYON ENRICHMENT"),
    ("OPEN CHRONICLE", "SOUTH KOREA'S LEE URGES RENEWED DIALOGUE WITH PYONGYANG"),
    ("DAILY MIRROR", "RUSSIAN MILITARY PLANE CRASHES, ALL 19 ABOARD KILLED"),
    ("MANILA TIMES", "MUSK: 'PRETTY FOOLISH' OVER FAILED ELECTION SPENDING"),
    ("JAPAN TIMES", "TRUMP, MARCOS HAIL ALLIANCE, PLEDGE CLOSER TRADE TIES"),
    ("MANILA TIMES", "EL NIÑO RAINS FLOOD SOUTH FLORIDA, ROOF COLLAPSES"),
    ("NDTV", "FRANCE JAILS 3 WOMEN FOR JOINING ISIS IN SYRIA"),
    ("NDTV", "ALLEGED RUSSIAN AGENT HELD OVER U.S. TECH SPYING"),
    ("JUST SECURITY", "TRUMP: 'SEE WHAT HAPPENS' IN IRAN WAR AFTER JAN 1"),
    ("JUST SECURITY", "ISRAELI FORCES PUSH INTO CENTRAL GAZA DESPITE CEASEFIRE"),
    ("NDTV", "U.S. REISSUES SECURITY WARNINGS IN BAHRAIN, SAUDI"),
    ("MANILA TIMES", "MUSLIMS PROJECTED TO OUTNUMBER CHRISTIANS BY 2035"),
    ("JAPAN TIMES", "SPAIN BRACES FOR ANTI-IMMIGRATION GOVERNMENT AFTER SNAP VOTE"),
    ("NDTV", "OUTAGES: OLD U.S. GRID MEETS AI-DRIVEN FIXES"),
    ("JAPAN TIMES", "BANGLADESH UNREST SPREADS AS YUNUS HOME IS TORCHED"),
    ("DAILY MIRROR", "VOYAGER 1 REACHES ONE LIGHT-DAY FROM EARTH"),
    ("NDTV", "JEFFRIES SET TO BE FIRST BLACK U.S. HOUSE SPEAKER"),
    ("OUTLOOK INDIA", "CYCLONE AKVAN BEARS DOWN ON INDIA'S EAST COAST"),
    ("OUTLOOK INDIA", "APEC LEADERS ADOPT 'SHENZHEN OUTLOOK' ON SCAMS"),
    ("OUTLOOK INDIA", "KREMLIN: UKRAINE WAR 'NOT CENTRAL TOPIC' AT SUMMIT"),
    ("OUTLOOK INDIA", "RUSSIA LAUNCHES FRESH STRIKES ON UKRAINE"),
    ("OUTLOOK INDIA", "MUSK JOINS U.S. DELEGATION TO CHINA FOR APEC"),
    ("ATRADIUS", "WORLD GROWTH FORECAST LIFTED TO 2.7% FOR 2026"),
    ("CAN", "NEPAL TAKES CLIMATE JUSTICE AWARD; NORWAY 'FOSSIL OF THE DAY'"),
    ("GLOBE NEWSWIRE", "AI FUTURE FORUM DEBUTS IN DUBAI"),
]


def wire_wrap(headline, tag, fnt, col_w, tag_fnt=None):
    """Wrap a wire headline with a red tag prefix on the first line.

    Headline is set in fnt (regular), the tag in tag_fnt (bold).
    Returns (lines, tag_width, tag)."""
    tag_w = text_w(tag, tag_fnt or fnt) + 8
    lines, cur, avail = [], "", col_w - tag_w
    for word in headline.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= avail:
            cur = trial
        else:
            lines.append(cur)
            cur, avail = word, col_w
    if cur:
        lines.append(cur)
    return lines, tag_w, tag


# ----------------------------------------------------------------- layout ----
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    f_title, t_lines, t_lh, t_h = fit_block(
        "THE WORLD IN ONE IMAGE", BOLD_PATH, 52, 40, CONTENT_W, 58,
        lh_factor=1.0, max_lines=1)
    draw_lines(d, MARGIN, 8, t_lines, f_title, t_lh, INK,
               align="center", box_w=CONTENT_W)
    note("masthead title", (MARGIN, 8, CONTENT_W, 58), t_h, t_lines)

    date_f = regular(20)
    date_txt = "THURSDAY · 19 NOVEMBER 2026 · 42 STORIES · SOURCED"
    d.text((MARGIN, 66), date_txt, font=date_f, fill=NAVY)

    # date-check corner box (right of the date line)
    bx0, by0, bx1, by1 = W - MARGIN - 210, 58, W - MARGIN, 94
    d.rectangle([bx0, by0, bx1, by1], outline=RED, width=3)
    dc1, dc2 = bold(15), bold(13)
    t1, t2 = "DATE CHECK ✓", "THU 19 NOV 2026"
    d.text(((bx0 + bx1 - text_w(t1, dc1)) / 2, by0 + 3), t1, font=dc1,
           fill=RED)
    d.text(((bx0 + bx1 - text_w(t2, dc2)) / 2, by0 + 19), t2, font=dc2,
           fill=INK)
    note("date-check box", (bx0, by0, 210, 36), 36, [t1, t2])

    # thin double rules
    d.rectangle([MARGIN, 102, W - MARGIN, 107], fill=INK)
    d.rectangle([MARGIN, 111, W - MARGIN, 113], fill=INK)

    # ---- lead panel (118..324) ----
    lead_top, lead_bot = 118, 324
    draw_tracked(d, MARGIN, lead_top, "DIPLOMACY", bold(14), RED, tracking=4)
    pic_summit(d, MARGIN, lead_top + 20, CONTENT_W, 56)
    hy = lead_top + 20 + 56 + 6
    f_h, h_lines, h_lh, h_h = fit_block(
        "TRUMP, XI AND PUTIN OPEN FIRST TRILATERAL SUMMIT", BOLD_PATH, 34,
        28, CONTENT_W, 76, lh_factor=1.12, max_lines=2)
    draw_lines(d, MARGIN, hy, h_lines, f_h, h_lh, INK)
    note("lead headline", (MARGIN, hy, CONTENT_W, 76), h_h, h_lines)
    cy = hy + h_h + 6
    f_c, c_lines, c_lh, c_h = fit_block(
        "The three leaders meet in Shenzhen for the first-ever "
        "US–China–Russia summit — a 90-minute meeting ends with a “peace "
        "declaration”; nuclear arms control, Ukraine and Iran on the table.",
        REG_PATH, 18, 16, CONTENT_W, lead_bot - cy, lh_factor=1.28,
        max_lines=2)
    draw_lines(d, MARGIN, cy, c_lines, f_c, c_lh, INK)
    note("lead caption", (MARGIN, cy, CONTENT_W, lead_bot - cy), c_h, c_lines)

    # rule under lead
    d.rectangle([MARGIN, 332, W - MARGIN, 334], fill=INK)

    # ---- 2x2 grid (340..556) ----
    grid_top, grid_bot = 340, 556
    row_h = (grid_bot - grid_top - 8) // 2  # 104, gap 8 with rule
    col_w = (CONTENT_W - 28) // 2            # 454, gutter 28
    col_x = [MARGIN, MARGIN + col_w + 28]
    row_y = [grid_top, grid_top + row_h + 8]
    # vertical rule between columns
    d.line([W // 2, grid_top + 4, W // 2, grid_bot - 4], fill=INK, width=2)
    # horizontal rule between rows
    d.rectangle([MARGIN, grid_top + row_h + 3, W - MARGIN,
                 grid_top + row_h + 5], fill=INK)

    panels = [
        ("WAR", pic_tanker,
         "IRAN WIDENS ITS WAR ACROSS THE GULF",
         "Iran attacks Kuwait and Bahrain; a Houthi missile hits the Saudi "
         "wealth fund tower; tankers hit mines."),
        ("JUSTICE", pic_scales,
         "MYANMAR COMMITTED GENOCIDE",
         "The top U.N. court rules Myanmar committed state-sponsored "
         "genocide against the Rohingya."),
        ("UKRAINE", pic_bridge,
         "THIRD STRIKE HALTS KERCH BRIDGE RAIL",
         "A third Ukrainian strike in four days halts rail traffic on the "
         "Kerch Bridge to occupied Crimea."),
        ("CULTURE", pic_controller,
         "GRAND THEFT AUTO VI LAUNCHES WORLDWIDE",
         "GTA VI launches to global fanfare after a 13-year wait."),
    ]

    for idx, (kicker, pic, headline, caption) in enumerate(panels):
        px = col_x[idx % 2]
        py = row_y[idx // 2]
        draw_tracked(d, px, py, kicker, bold(12), RED, tracking=4)
        content_top = py + 16
        avail_h = (py + row_h) - content_top
        # pictogram on the left, text on the right
        pic(d, px, content_top + (avail_h - 68) // 2, 68)
        tx = px + 100
        tw = col_w - 100
        # headline gets up to ~55% of the height, caption the rest
        f_h, h_lines, h_lh, h_h = fit_block(
            headline, BOLD_PATH, 22, 18, tw, int(avail_h * 0.56),
            lh_factor=1.14, max_lines=2)
        draw_lines(d, tx, content_top, h_lines, f_h, h_lh, INK)
        note(f"panel {kicker} headline", (tx, content_top, tw,
             int(avail_h * 0.56)), h_h, h_lines)
        cap_y = content_top + h_h + 6
        f_c, c_lines, c_lh, c_h = fit_block(
            caption, REG_PATH, 14, 12, tw, (py + row_h) - cap_y,
            lh_factor=1.22, max_lines=2)
        draw_lines(d, tx, cap_y, c_lines, f_c, c_lh, INK)
        note(f"panel {kicker} caption", (tx, cap_y, tw, (py + row_h) - cap_y),
             c_h, c_lines)

    # rule under grid
    d.rectangle([MARGIN, 564, W - MARGIN, 566], fill=INK)

    # ---- wire section header (572..594) ----
    wh_f = bold(16)
    wh_txt = "THE DAY IN BRIEF · 37 MORE STORIES"
    d.text((MARGIN, 572), wh_txt, font=wh_f, fill=INK)
    wr_f = regular(13)
    wr_txt = "WIRE · 19 NOV 2026 (UTC)"
    d.text((W - MARGIN - text_w(wr_txt, wr_f), 575), wr_txt, font=wr_f,
           fill=NAVY)

    # ---- wire columns (598..978) ----
    wire_top, wire_bot = 598, 978
    wire_h = wire_bot - wire_top
    wcol_w = (CONTENT_W - 2 * 16) // 3  # 301
    wcol_x = [MARGIN, MARGIN + wcol_w + 16, MARGIN + 2 * (wcol_w + 16)]
    # pick the largest wire size whose tallest balanced column fits
    # (headlines regular, tags bold -- regular is narrower, so 14px fits)
    chosen = None
    for size in (14, 13, 12):
        wf = regular(size)
        tf = bold(size)
        lh = size  # caps-only wire text: tight leading, no descenders
        wrapped = [wire_wrap(head, tag, wf, wcol_w, tf)
                   for tag, head in WIRE]
        # longest-first balancing keeps the tallest column minimal
        wrapped.sort(key=lambda it: -len(it[0]))
        cols, heights = [[], [], []], [0, 0, 0]
        for item in wrapped:
            ci = heights.index(min(heights))
            cols[ci].append(item)
            heights[ci] += len(item[0])
        if max(heights) * lh <= wire_h:
            chosen = (size, lh, cols, heights)
            break
    size, lh, cols, heights = chosen
    wf = regular(size)
    tf = bold(size)
    note("wire columns", (MARGIN, wire_top, CONTENT_W, wire_h),
         max(heights) * lh, [f"size={size} lines={heights}"])
    for ci, items in enumerate(cols):
        cy = wire_top
        for lines, tag_w, tag in items:
            d.text((wcol_x[ci], cy), tag, font=tf, fill=RED)
            for li, line in enumerate(lines):
                lx = wcol_x[ci] + (tag_w if li == 0 else 0)
                d.text((lx, cy), line, font=wf, fill=INK)
                cy += lh

    # ---- footer band (986..1024) ----
    d.rectangle([0, 986, W, H], fill=NAVY)
    footer = ("ALSO TODAY · Voyager 1 reaches one light-day from Earth · "
              "Hakeem Jeffries set to become the first African-American "
              "Speaker · Bangladesh unrest — ex-leader Yunus’s family home "
              "set ablaze")
    f_f, f_lines, f_lh, f_h = fit_block(
        footer, REG_PATH, 14, 12, CONTENT_W, 34, lh_factor=1.22, max_lines=2)
    fy = 986 + (38 - f_h) // 2
    draw_lines(d, MARGIN, fy, f_lines, f_f, f_lh, WHITE)
    note("footer", (MARGIN, 986, CONTENT_W, 38), f_h, f_lines)

    os.makedirs(OUT_DIR, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    img.save(LOCAL, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"saved {OUT}: {img.size[0]}x{img.size[1]}, {size} bytes")
    print("--- layout measurements (box -> used) ---")
    for name, (bx, by, bw, bh), used, lines in REPORT:
        flag = "OK " if used <= bh else "OVERFLOW"
        print(f"{flag} {name}: box h={bh} used h={used} lines={lines}")


if __name__ == "__main__":
    main()
