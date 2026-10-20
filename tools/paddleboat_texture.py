"""Texture of the armoured steam paddleboat (steam_paddleboat).

  steam_paddleboat.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours from the reference picture: dark grey riveted armour plates, darker rusty plates
low on the hull, a brown wooden deckhouse with brass frames and lit windows, grey brick
funnels ringed with riveted iron bands and blackened by soot, brass guns, hub and lamps,
a wooden paddle wheel with an iron rim.
"""
import math
import random

from PIL import Image

from galley_texture import _jitter, _mix, _ramp, _rgb, _scale, fine_wood, hammered_iron, polished_metal

BRASS = [(0.0, _rgb("6a4a14")), (0.22, _rgb("936a1e")), (0.45, _rgb("c4952f")), (0.7, _rgb("e2b850")), (0.9, _rgb("fbe39a")),
         (1.0, _rgb("fff4cc"))]
COPPER = [(0.0, _rgb("5a2e18")), (0.25, _rgb("7e4526")), (0.5, _rgb("a8643a")), (0.75, _rgb("d08a54")), (0.92, _rgb("f0b08a")),
          (1.0, _rgb("ffd8bc"))]

SIZE = 256

REGIONS = {
    "plate":       (0, 0, 64, 32),
    "plate_dark":  (64, 0, 64, 32),
    "iron":        (128, 0, 16, 16),
    "gunmetal":    (144, 0, 16, 16),
    "brass":       (160, 0, 32, 32),
    "copper":      (192, 0, 32, 16),
    "rust":        (192, 16, 32, 16),
    "rivet_band":  (224, 0, 32, 16),
    "wood":        (224, 16, 32, 16),
    "deck":        (0, 32, 64, 64),
    "house":       (64, 32, 64, 32),
    "window":      (128, 16, 16, 16),
    "porthole":    (144, 16, 16, 16),
    "funnel":      (160, 32, 32, 32),
    "funnel_band": (192, 32, 32, 8),
    "soot":        (192, 40, 32, 8),
    "dark_wood":   (224, 32, 32, 16),
    "plate_inner": (64, 64, 64, 32),
    "paddle":      (128, 32, 32, 16),
    "grate":       (192, 48, 32, 32),
    "lantern":     (128, 48, 16, 16),
    "glow":        (144, 48, 16, 16),
    "rope":        (224, 48, 16, 16),
    "gauge":       (240, 48, 16, 16),
    "flag":        (128, 64, 32, 16),
    "door":        (160, 64, 16, 32),
    "roof":        (0, 96, 64, 32),
    "red_paint":   (176, 64, 16, 16),
    "lamp_glass":  (176, 80, 16, 16),
}


def _plates(px, region, base, seam, rivet, rng, pw=16, ph=8, rust=0.0):
    """Riveted armour plates laid like bricks: each plate its own tone, lit along its upper edge and
    shading softly downwards, a dark seam, a single row of domed rivets (lit dot, shadow under it)
    along the top of every plate and down its forward edge, a few streaks of rust and grime running
    down from the rivets."""
    u, v, w, h = region
    tones = {}
    for y in range(h):
        for x in range(w):
            row = y // ph
            off = pw // 2 if row % 2 else 0
            col = (x + off) // pw
            if (row, col) not in tones:
                tones[(row, col)] = (_jitter(base, rng, 6), rng.uniform(-0.03, 0.03))
            tone, tilt = tones[(row, col)]
            fx, fy = (x + off) % pw, y % ph
            k = 1.0 - 0.09 * fy / ph + tilt * (fx / pw - 0.5) + 0.015 * math.sin(x * 0.7 + y * 0.3)
            if fy == 0 or fx == 0:
                c = seam
            else:
                if fy == 1:
                    k += 0.1
                elif fy == ph - 1 or fx == pw - 1:
                    k -= 0.06
                c = _scale(tone, k)
                if fy == 2 and fx % 4 == 2:
                    c = rivet
                elif fy == 3 and fx % 4 == 2:
                    c = _scale(tone, 0.72)   # shadow under the rivet head
                elif fx == 2 and fy == ph // 2 + 1 and ph >= 8:
                    c = rivet
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # rust and grime running down from a few rivets
    for _ in range(int(w * h / 110 * (1 + 8 * rust))):
        x = rng.randrange(w)
        y = (rng.randrange(h) // ph) * ph + 3
        n = rng.randrange(3, ph + 2)
        col = _rgb("7a3e1e") if rng.random() < rust * 4 else _scale(base, 0.8)
        for i in range(n):
            if y + i >= h:
                break
            r, g, b, a = px[u + x, v + y + i]
            f = 0.5 * (1 - i / n)
            px[u + x, v + y + i] = (int(r + (col[0] - r) * f), int(g + (col[1] - g) * f), int(b + (col[2] - b) * f), a)


def _window(px, u, v, w, h):
    """Lit cabin window: a brass frame, a dark red curtain drawn to each side, four warm panes
    behind glazing bars, brighter towards the lamp inside."""
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
                c = _ramp(BRASS, 0.85 if (x < 1 or y < 1) else 0.6 if (x < 2 or y < 2) else 0.35)
            elif x == w // 2 or y == h // 2:
                c = _rgb("5a3a1c")
            elif (x < 4 or x >= w - 4) and y < h - 3:
                c = _rgb("7a1712") if (x + y // 2) % 2 else _rgb("5e110c")   # curtain folds
            else:
                d = math.hypot(x + 0.5 - w / 2, (y + 0.5 - h * 0.6) * 1.1)
                c = _mix(_rgb("fff0c0"), _rgb("e8a046"), min(1.0, d / (w * 0.45)))
                if (x - y) % 7 == 0 and y < h / 2:
                    c = _mix(c, _rgb("ffffff"), 0.35)   # a glint on the glass
            px[u + x, v + y] = c + (255,)


def make_texture(path):
    rng = random.Random(1851)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    _plates(px, REGIONS["plate"], _rgb("5d6166"), _rgb("2d3033"), _rgb("a4aab0"), rng, rust=0.03)
    _plates(px, REGIONS["plate_dark"], _rgb("3d3f42"), _rgb("1f2022"), _rgb("74787c"), rng, rust=0.1)
    _plates(px, REGIONS["plate_inner"], _rgb("6d7176"), _rgb("44474b"), _rgb("a2a8ae"), rng)
    _plates(px, REGIONS["roof"], _rgb("4a4d51"), _rgb("2a2c2f"), _rgb("80868c"), rng, pw=32, ph=16)
    hammered_iron(img, REGIONS["iron"], _rgb("2e3034"), rng)
    hammered_iron(img, REGIONS["gunmetal"], _rgb("4a4f55"), rng, dent=0.09)
    hammered_iron(img, REGIONS["rust"], _rgb("7a4022"), rng, dent=0.12, noise=6)
    u, v, w, h = REGIONS["red_paint"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(_rgb("8e1f19"), 1.06 - 0.12 * y / h), rng, 2) + (255,)
    fine_wood(img, REGIONS["deck"], _rgb("6e5a44"), _rgb("2e241a"), 4, rng, knots=0.12)
    fine_wood(img, REGIONS["wood"], _rgb("8a5a2c"), _rgb("6a4420"), 8, rng, joints=False, knots=0.2)
    fine_wood(img, REGIONS["dark_wood"], _rgb("4f3420"), _rgb("2c1c10"), 4, rng)
    fine_wood(img, REGIONS["paddle"], _rgb("7a5232"), _rgb("3e2814"), 4, rng, knots=0.25)

    def reg(name):
        return REGIONS[name]

    polished_metal(img, reg("brass"), BRASS, rng)
    polished_metal(img, reg("copper"), COPPER, rng, seed=1.3)
    # lantern glass: thin dark iron frame and glazing bars, warm light brighter round the flame
    u, v, w, h = reg("lamp_glass")
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("2a2c30")
            elif x == w // 2:
                c = _rgb("3a3c40")
            else:
                d = ((x - w / 2 + 0.5) ** 2 + ((y - h * 0.55) * 0.8) ** 2) ** 0.5
                c = _rgb("fff6c8") if d < 2.6 else _rgb("ffd77a") if d < 4.6 else _rgb("f2ac44") if d < 6.4 else _rgb("d98a2c")
            px[u + x, v + y] = c + (255,)
    # dark iron band with a row of domed rivets
    for name, base in (("rivet_band", "26282b"), ("funnel_band", "1e1f21")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                c = _scale(_rgb(base), 1.15 - 0.3 * y / h)
                if y == h // 2 and x % 4 == 1:
                    c = _rgb("9aa0a6")
                elif y == h // 2 + 1 and x % 4 == 1:
                    c = _rgb("121314")
                px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # soot: velvety black with a faint warm glow of embers
    u, v, w, h = reg("soot")
    for y in range(h):
        for x in range(w):
            k = 0.5 + 0.5 * math.sin(x * 0.9 + math.sin(y * 1.3) * 2)
            c = _mix(_rgb("101010"), _rgb("2e2a26"), k * 0.8)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # funnel: riveted iron rings, a vertical seam, blackening with soot towards the top
    u, v, w, h = reg("funnel")
    for y in range(h):
        for x in range(w):
            fy = y % 8
            c = _scale(_rgb("4c4f54"), 1.0 + 0.04 * math.sin(x * 2 * math.pi / w * 2) - 0.05 * fy / 8)
            if fy == 0:
                c = _rgb("26282b")
            elif fy == 1 and x % 4 == 2:
                c = _rgb("8d9399")
            elif fy == 2 and x % 4 == 2:
                c = _scale(c, 0.75)
            elif fy == 1:
                c = _scale(c, 1.12)
            elif x % 16 == 0:
                c = _rgb("35373b")  # vertical seam of the plates
            k = 1.0 - 0.55 * (1 - y / h) ** 2
            c = _scale(c, k)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # deckhouse: raised wooden panels (lit on top and left, shaded bottom and right) in brass frames
    u, v, w, h = reg("house")
    tmp = Image.new("RGBA", (w, h))
    fine_wood(tmp, (0, 0, w, h), _rgb("7a4f2a"), _rgb("5a3a1c"), 32, rng, joints=False, vertical=True, knots=0.05, grain=0.12)
    tp = tmp.load()
    for y in range(h):
        for x in range(w):
            wd = tp[x, y][:3]
            fx, fy = x % 16, y
            if fx in (0, 15) or fy in (0, 1, h - 2, h - 1):
                c = _ramp(BRASS, 0.75 if fy in (0, h - 2) or fx == 0 else 0.45)
            elif fx in (2, 13) or fy in (3, h - 4):
                # the bevel round the raised panel
                lit = fx == 2 or fy == 3
                c = _scale(wd, 1.2 if lit else 0.65)
            elif fx in (1, 14) or fy in (2, h - 3):
                c = _scale(wd, 0.85)
            else:
                c = _scale(wd, 1.0 + 0.04 * (1 - fy / h))
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # lit window, round porthole
    u, v, w, h = reg("window")
    _window(px, u, v, w, h)
    u, v, w, h = reg("porthole")
    for y in range(h):
        for x in range(w):
            r = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            ang = math.atan2(y - 7.5, x - 7.5)
            if r > 7.6:
                c = _rgb("5d6166")
            elif r > 5.6:
                c = _ramp(BRASS, 0.55 + 0.35 * math.sin(ang + 2.4))
                if r > 6.2 and (int(math.degrees(ang) + 360) % 45) < 9:
                    c = _ramp(BRASS, 0.98)   # bolt
            elif r > 5.0:
                c = _rgb("3a2a10")
            else:
                c = _mix(_rgb("fff0b8"), _rgb("e89a40"), r / 5.0)
                if abs((x - 7.5) - (y - 7.5) * 0.6 + 1.5) < 0.6 and r < 4:
                    c = _mix(c, _rgb("ffffff"), 0.4)
            px[u + x, v + y] = c + (255,)
    # hatch grating
    u, v, w, h = reg("grate")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            if frame:
                c = _scale(_rgb("3a3c40"), 1.15 if (x < 1 or y < 1) else 0.9)
            elif x % 5 > 1 and y % 5 > 1:
                c = _rgb("0e0e0e") if (x % 5 == 2 or y % 5 == 2) else _rgb("1a1a1a")
            else:
                c = _scale(_rgb("4a4f55"), 1.15 if (x % 5 == 0 or y % 5 == 0) else 0.9)
            px[u + x, v + y] = c + (255,)
    # lantern and glow
    u, v, w, h = reg("lantern")
    for y in range(h):
        for x in range(w):
            border = x in (0, w - 1) or y in (0, h - 1) or x == w // 2
            px[u + x, v + y] = (_rgb("8a6a26") if border else _rgb("f2c25a")) + (255,)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            t = ((x + y) % 4) / 4.0
            px[u + x, v + y] = _ramp([(0.0, _rgb("22180e")), (0.35, _rgb("4a3826")), (1.0, _rgb("22180e"))], t) + (255,)
    # pressure gauge: brass bezel, cream dial with ticks, a needle
    u, v, w, h = reg("gauge")
    for y in range(h):
        for x in range(w):
            r = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            ang = math.atan2(y - 7.5, x - 7.5)
            if r > 6:
                c = _ramp(BRASS, 0.5 + 0.4 * math.sin(ang + 2.4))
            elif abs((x - 7.5) + (y - 7.5)) < 0.8 and x < 8:
                c = _rgb("1a1a1a")
            elif r > 4.6 and (int(math.degrees(ang) + 360) % 30) < 8 and y < 11:
                c = _rgb("3a3a3a")
            else:
                c = _rgb("efe6cf")
            px[u + x, v + y] = c + (255,)
    # flag: dark red with a brass cog wheel, a soft fold
    u, v, w, h = reg("flag")
    for y in range(h):
        for x in range(w):
            dx, dy = x - w * 0.4, (y - h / 2 + 0.5) * 1.6
            r = (dx * dx + dy * dy) ** 0.5
            a = math.atan2(dy, dx)
            tooth = 6.2 + (1.4 if math.cos(8 * a) > 0.3 else 0)
            c = _ramp(BRASS, 0.7 - 0.2 * dy / 8) if (3 < r < tooth) else _rgb("7a1712")
            c = _scale(c, 1.0 + 0.06 * math.sin(x * 0.4))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # iron door: riveted frame, two panels, a small round window and a brass handle
    u, v, w, h = reg("door")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2
            c = _scale(_rgb("4a4f55"), 1.0 - 0.1 * y / h)
            if frame:
                c = _rgb("2e3034")
            elif x in (3, w - 4) and y % 5 == 2:
                c = _rgb("8d9399")
            elif y in (h // 2, h // 2 + 1):
                c = _rgb("35383c")
            r = math.hypot(x + 0.5 - w / 2, y + 0.5 - 8)
            if r < 3.0:
                c = _mix(_rgb("fff0b8"), _rgb("e89a40"), r / 3.0)
            elif r < 4.0:
                c = _ramp(BRASS, 0.7)
            if x == w - 4 and h // 2 + 2 <= y <= h // 2 + 3:
                c = _ramp(BRASS, 0.9)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: grey paddleboat with its two funnels and the wheel."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    for x in range(1, 15):
        for y in range(10, 14):
            p[x, y] = _rgb("5d6166" if y < 13 else "3d3f42") + (255,)
    for x in range(4, 12):
        for y in range(8, 10):
            p[x, y] = _rgb("7a4f2a") + (255,)
    for fx in (6, 9):
        for y in range(2, 8):
            p[fx, y] = _rgb("6a6c70") + (255,)
        p[fx, 1] = _rgb("2b2b2b") + (255,)
    for a in range(0, 360, 30):
        x = int(round(10 + 2.6 * math.cos(math.radians(a))))
        y = int(round(11 + 2.6 * math.sin(math.radians(a))))
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = _rgb("8a5a2c") + (255,)
    p[10, 11] = _rgb("b8892e") + (255,)
    icon.save(path)
