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

from galley_texture import _fill, _jitter, _planks, _rgb

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
}


def _plates(px, region, base, seam, rivet, rng, pw=16, ph=8, rust=0.0):
    u, v, w, h = region
    tones = {}
    for y in range(h):
        for x in range(w):
            row = y // ph
            off = pw // 2 if row % 2 else 0
            col = (x + off) // pw
            if (row, col) not in tones:
                tones[(row, col)] = _jitter(base, rng, 7)
            fx, fy = (x + off) % pw, y % ph
            c = tones[(row, col)]
            if fx == 0 or fy == 0:
                c = seam
            elif (fy == 2 or fy == ph - 2) and fx % 4 == 2:
                c = rivet
            elif fy == ph - 1 or fx == pw - 1:
                c = tuple(max(0, k - 10) for k in c)
            if rust and rng.random() < rust * (fy / ph):
                c = _jitter(_rgb("6e3a1e"), rng, 10)
            px[u + x, v + y] = c + (255,)


def make_texture(path):
    rng = random.Random(1851)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    _plates(px, REGIONS["plate"], _rgb("5d6166"), _rgb("2d3033"), _rgb("9aa0a6"), rng, rust=0.04)
    _plates(px, REGIONS["plate_dark"], _rgb("3d3f42"), _rgb("1f2022"), _rgb("6c7074"), rng, rust=0.12)
    _plates(px, REGIONS["plate_inner"], _rgb("6d7176"), _rgb("44474b"), _rgb("a2a8ae"), rng)
    _plates(px, REGIONS["roof"], _rgb("4a4d51"), _rgb("2a2c2f"), _rgb("80868c"), rng, pw=32, ph=16)
    _fill(img, REGIONS["iron"], _rgb("2e3034"), rng, 6)
    _fill(img, REGIONS["gunmetal"], _rgb("4a4f55"), rng, 8)
    _fill(img, REGIONS["rust"], _rgb("7a4022"), rng, 14)
    _fill(img, REGIONS["red_paint"], _rgb("8e1f19"), rng, 8)
    _planks(img, REGIONS["deck"], _rgb("6e5a44"), _rgb("3b2f22"), 4, rng)
    _planks(img, REGIONS["wood"], _rgb("8a5a2c"), _rgb("5a3818"), 8, rng, joints=False)
    _planks(img, REGIONS["dark_wood"], _rgb("4f3420"), _rgb("2c1c10"), 4, rng)
    _planks(img, REGIONS["paddle"], _rgb("7a5232"), _rgb("4a301a"), 4, rng)

    def reg(name):
        return REGIONS[name]

    # brass and copper with highlights
    for name, base, hi in (("brass", "b8892e", "f0c868"), ("copper", "a0592e", "d08a54")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                c = _rgb(hi) if (x * 3 + y * 7) % 13 == 0 or y == 1 else _rgb(base)
                px[u + x, v + y] = _jitter(c, rng, 8) + (255,)
    # dark band with a row of rivets
    for name, base, top in (("rivet_band", "26282b", None), ("funnel_band", "1e1f21", None)):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                c = _rgb("8d9399") if (y == h // 2 and x % 4 == 1) else _rgb(base)
                px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("soot")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("151515") if rng.random() < 0.7 else _rgb("2b2b2b"), rng, 4) + (255,)
    # funnel: grey bricks with soot towards the top
    u, v, w, h = reg("funnel")
    for y in range(h):
        for x in range(w):
            row = y // 4
            off = 4 if row % 2 else 0
            mortar = y % 4 == 3 or (x + off) % 8 == 7
            c = _rgb("2a2a2c") if mortar else _jitter(_rgb("6a6c70"), rng, 10)
            k = 1.0 - 0.45 * (1 - y / h) ** 2
            c = tuple(int(q * k) for q in c)
            px[u + x, v + y] = c + (255,)
    # deckhouse: brown wooden panels in brass frames
    u, v, w, h = reg("house")
    for y in range(h):
        for x in range(w):
            fx, fy = x % 16, y
            if fx in (0, 15) or fy in (0, 1, h - 2, h - 1):
                c = _rgb("b8892e")
            elif fx in (2, 13) or fy in (3, h - 4):
                c = _rgb("4a2e17")
            else:
                c = _rgb("7a4f2a") if (fy // 3) % 2 else _rgb("704828")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # lit window in a brass frame, round porthole
    u, v, w, h = reg("window")
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
                c = _rgb("c99a3e")
            elif x == w // 2 or y == h // 2:
                c = _rgb("5a3a1c")
            else:
                c = _rgb("ffe2a0") if (x + y) % 6 < 2 else _rgb("f2b552")
            px[u + x, v + y] = c + (255,)
    u, v, w, h = reg("porthole")
    for y in range(h):
        for x in range(w):
            r = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if r > 7.6:
                c = _rgb("5d6166")
            elif r > 5.6:
                c = _rgb("c99a3e") if (int(math.degrees(math.atan2(y - 7.5, x - 7.5))) // 45) % 2 else _rgb("8a6a26")
            else:
                c = _rgb("ffdf96") if r < 2.5 else _rgb("f0a84a")
            px[u + x, v + y] = c + (255,)
    # hatch grating
    u, v, w, h = reg("grate")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            c = _rgb("2e3034") if frame else (_rgb("111111") if (x % 5 > 1 and y % 5 > 1) else _rgb("4a4f55"))
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
            px[u + x, v + y] = (_rgb("3a2a1a") if (x + y) % 3 else _rgb("22180e")) + (255,)
    # pressure gauge
    u, v, w, h = reg("gauge")
    for y in range(h):
        for x in range(w):
            r = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            c = _rgb("c99a3e") if r > 6 else (_rgb("1a1a1a") if abs((x - 7.5) + (y - 7.5)) < 0.8 and x < 8 else _rgb("efe6cf"))
            px[u + x, v + y] = c + (255,)
    # flag: dark red with a brass cog wheel
    u, v, w, h = reg("flag")
    for y in range(h):
        for x in range(w):
            dx, dy = x - w * 0.4, (y - h / 2 + 0.5) * 1.6
            r = (dx * dx + dy * dy) ** 0.5
            a = math.atan2(dy, dx)
            tooth = 6.2 + (1.4 if math.cos(8 * a) > 0.3 else 0)
            c = _rgb("d4aa45") if (3 < r < tooth) else _rgb("7a1712")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # iron door with rivets
    u, v, w, h = reg("door")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2
            c = _rgb("2e3034") if frame else (_rgb("8d9399") if (x in (3, w - 4) and y % 5 == 2) else _rgb("4a4f55"))
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
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
