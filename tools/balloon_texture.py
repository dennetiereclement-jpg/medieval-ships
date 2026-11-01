"""Texture of the steampunk hot-air balloon (hot_air_balloon).

  hot_air_balloon.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours of the reference picture: an envelope of olive-green and beige gores (stitched cloth, a brass load band
with gold ornaments), gold chains, a small dark green-stained wooden basket with dark rims, lit windows along its
sides and warm lanterns under its ends, a copper and brass burner column with a glowing flame, a black riveted
boiler with its stack, a big wooden gear wheel on the side.
"""
import math
import random

from PIL import Image

from galley_texture import _fill, _jitter, _rgb, paint_lamp_glass
from airship_texture import _metal, _wood, _rivet_plates, _panel, _round_face, _shade

SIZE = 256

REGIONS = {
    # the envelope (each gore panel shows the whole region: u along the gore, v round the balloon)
    "gore_green":  (0, 0, 64, 32),
    "gore_beige":  (0, 32, 64, 32),
    "balloon_in":  (64, 0, 16, 16),
    "band":        (64, 16, 32, 16),     # the brass load band: riveted, a gold bead along it
    # metals
    "brass":       (96, 0, 32, 32),
    "gold":        (128, 0, 16, 16),
    "copper":      (144, 0, 32, 32),
    "iron":        (176, 0, 16, 16),
    "iron_dark":   (192, 0, 16, 16),
    "chain":       (208, 0, 16, 16),
    "rope":        (224, 0, 16, 16),
    "lantern":     (240, 0, 16, 16),
    "glow":        (128, 16, 16, 16),
    "window":      (176, 16, 16, 16),    # a lit window with its bars (full bright)
    "fire":        (192, 16, 16, 16),    # the burner's mouth: glowing orange
    "end_grain":   (208, 16, 16, 16),
    "leather":     (224, 16, 16, 16),
    "leather_dark": (240, 16, 16, 16),
    "flame":       (64, 64, 32, 48),     # the flame (transparent outside)
    # woods
    "hull":        (96, 32, 64, 32),     # green-stained planks of the basket's sides
    "hull_dark":   (160, 32, 64, 32),    # dark planks of its bottom
    "deck":        (0, 64, 64, 32),
    "dark_wood":   (96, 64, 32, 16),
    "wood":        (128, 64, 64, 16),
    "gear_wood":   (96, 80, 64, 16),     # the big wheel's rim and spokes: oak, iron straps
    "rim":         (160, 80, 32, 16),    # the basket's rims: dark varnished wood
    "boiler":      (192, 64, 64, 32),    # black riveted iron plates
    "gauge":       (0, 96, 32, 32),
    "platform":    (32, 96, 32, 32),     # the platform's planks, 2 blocks
    "canvas":      (64, 112, 16, 16),
    "glass":       (80, 112, 16, 16),
}


def _check_regions():
    items = list(REGIONS.items())
    for i, (na, (ua, va, wa, ha)) in enumerate(items):
        assert ua + wa <= SIZE and va + ha <= SIZE, na
        for nb, (ub, vb, wb, hb) in items[i + 1:]:
            if ua < ub + wb and ub < ua + wa and va < vb + hb and vb < va + ha:
                raise AssertionError("regions overlap: %s %s" % (na, nb))


_check_regions()

GREEN = _rgb("66744a")
GREEN_DARK = _rgb("3f4a27")
BEIGE = _rgb("e0d2ac")
BEIGE_DARK = _rgb("a8976c")
CHAIN = _rgb("c9a24a")
CHAIN_DARK = _rgb("7e5d1e")
ROPE = _rgb("b48a4a")
ROPE_DARK = _rgb("7a5a28")


def _stripes(px, region, base, dark, rng, k=3):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = dark if y % k == k - 1 else base
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)


def make_texture(path):
    rng = random.Random(1783)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name]

    # ---- the envelope: stitched cloth gores, a dark inside, the brass load band
    _panel(px, reg("gore_green"), GREEN, GREEN_DARK, rng, weave=0.045)
    _panel(px, reg("gore_beige"), BEIGE, BEIGE_DARK, rng, weave=0.045)
    _fill(img, reg("balloon_in"), _rgb("6a6248"), rng, 6)
    u, v, w, h = reg("band")
    for y in range(h):
        for x in range(w):
            t = 1.0 + 0.12 * math.cos(math.pi * (y + 0.5) / h - 0.3)
            c = _shade(_rgb("c99a3c"), t)
            if y in (0, h - 1):
                c = _rgb("684716")
            elif y in (2, h - 3) and x % 4 == 1:
                c = _rgb("fbe7a1")        # rivets
            elif y == h // 2 and x % 8 in (3, 4):
                c = _rgb("f6dc93")        # a gold bead
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # ---- metals
    _metal(px, reg("gold"), ("fbe7a1", "e6bf5a", "cfa23f", "a97f2a", "7c5a1c"), rng)
    _metal(px, reg("brass"), ("f6dc93", "dcb055", "bf8f34", "906523", "684716"), rng)
    _metal(px, reg("copper"), ("f0b08a", "d08a54", "a8643a", "7e4526", "5a2e18"), rng)
    _fill(img, reg("iron"), _rgb("3a3c40"), rng, 6)
    _fill(img, reg("iron_dark"), _rgb("22232a"), rng, 5)
    # gold chain links: a bright link on a dark ground
    u, v, w, h = reg("chain")
    for y in range(h):
        for x in range(w):
            ring = 2 <= y <= h - 3 and (x in (1, 2, w - 3, w - 2) or y in (2, 3, h - 4, h - 3))
            c = CHAIN if ring else CHAIN_DARK
            if ring and (x + y) % 5 == 0:
                c = _rgb("fbe7a1")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            c = ROPE if (x + y) % 4 < 2 else ROPE_DARK
            if (x - y) % 4 == 0:
                c = _shade(ROPE, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # a lit window: brass frame, a cross of bars, warm light brighter in the middle
    u, v, w, h = reg("window")
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("bf8f34")
            elif x == w // 2 or y == h // 2:
                c = _rgb("3a2a18")
            else:
                d = math.hypot(x - w / 2 + 0.5, (y - h / 2 + 0.5) * 1.2)
                c = _rgb("fff0b0") if d < 3 else _rgb("ffcf5e") if d < 5.5 else _rgb("f0a238")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = reg("fire")
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
            c = _rgb("fff4b0") if d < 2.5 else _rgb("ffc94a") if d < 4.5 else _rgb("f07a28") if d < 6.5 else _rgb("a83a18")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # ---- the flame: a tongue of fire, yellow core, orange then red edges, transparent outside
    u, v, w, h = reg("flame")
    for y in range(h):
        for x in range(w):
            fy = (y + 0.5) / h              # 0 at the top of the flame, 1 at its base
            cx = (x + 0.5) / w * 2 - 1
            # width of the tongue at this height: pointed top, full at the base, a wobble
            wd = 0.15 + 0.85 * fy ** 0.8 + 0.08 * math.sin(fy * 9.0 + 0.6)
            k = abs(cx) / max(0.05, wd)
            if k > 1.0 or (fy < 0.06 and abs(cx) > 0.1):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            core = 1.0 - k
            core *= 0.6 + 0.4 * (1 - fy) if fy > 0.25 else 1.0
            c = _rgb("fffbd0") if core > 0.8 else _rgb("fff0a0") if core > 0.6 else _rgb("ffc84a") if core > 0.4 \
                else _rgb("f58a2a") if core > 0.2 else _rgb("d84a1a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # ---- woods
    _wood(px, reg("hull"), _rgb("5a6a3c"), _rgb("2c2a16"), 4, rng, nails="2a2420", grain=0.14)
    _wood(px, reg("hull_dark"), _rgb("4a3420"), _rgb("261809"), 4, rng, nails="3a2e26")
    _wood(px, reg("deck"), _rgb("8a6644"), _rgb("4e3820"), 4, rng, nails="3e3026")
    _wood(px, reg("platform"), _rgb("7e5c3a"), _rgb("46301a"), 4, rng, nails="3e3026")
    _wood(px, reg("dark_wood"), _rgb("4a301a"), _rgb("281809"), 4, rng)
    _wood(px, reg("wood"), _rgb("b38a58"), _rgb("7a5a34"), 8, rng, joints=False, grain=0.1)
    _wood(px, reg("rim"), _rgb("3c2614"), _rgb("1e1208"), 8, rng, joints=False, grain=0.2)
    # the gear wheel's oak: planks with iron straps across them
    _wood(px, reg("gear_wood"), _rgb("8e6236"), _rgb("5a3a1e"), 8, rng, joints=False, grain=0.14)
    u, v, w, h = reg("gear_wood")
    for y in range(h):
        for x in range(w):
            if x % 16 in (6, 7, 8):
                c = _rgb("3a3c40") if x % 16 == 7 else _rgb("2a2c30")
                if y % 5 == 2 and x % 16 == 7:
                    c = _rgb("6a6c70")
                px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    u, v, w, h = reg("end_grain")
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
            c = _shade(_rgb("8c5e30"), 0.86 if int(d * 0.9 + 0.3 * math.sin(x + y)) % 3 == 0 else 1.0)
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # ---- the boiler: black iron plates, lapped, rivet rows, a soft sheen
    _rivet_plates(px, reg("boiler"), _rgb("2c2d32"), _rgb("16171a"), _rgb("5a5c62"), rng, tarnish="3c3830")
    # buttoned leather of the benches
    u, v, w, h = reg("leather")
    for y in range(h):
        for x in range(w):
            a, b = (x + y) % 8, (x - y) % 8
            k = 1.0 + 0.1 * math.sin(math.pi * a / 8) * math.sin(math.pi * b / 8) - 0.06
            c = _shade(_rgb("6e3a22"), k)
            if a == 0 or b == 0:
                c = _rgb("44200f")
            if x % 8 == 4 and y % 8 == 0:
                c = _rgb("d8b25a")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    _fill(img, reg("leather_dark"), _rgb("44200f"), rng, 5)
    _fill(img, reg("canvas"), _rgb("b9a780"), rng, 7)
    u, v, w, h = reg("glass")
    for y in range(h):
        for x in range(w):
            c = _rgb("cfe4ec") if y < h * 0.45 else _rgb("4f7f9a")
            if x in (2, 3):
                c = _shade(c, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)

    # a round pressure gauge: brass bezel, cream dial, black ticks, a red sector, the needle
    def gauge(rr, ang, x, y):
        if rr > 0.93:
            return _rgb("684716")
        if rr > 0.85:
            return _rgb("f6dc93") if rr < 0.89 else _rgb("bf8f34")
        if rr > 0.8:
            return _rgb("906523")
        c = _rgb("efe6cf")
        if rr > 0.62 and (ang % (math.pi / 6)) < 0.12 and abs(ang) < 2.4:
            c = _rgb("2a2420")
        if rr > 0.62 and 1.6 < ang < 2.4:
            c = _rgb("b03020")
        na = 0.9
        if rr < 0.68 and abs(math.sin(ang - na)) * rr < 0.045 and math.cos(ang - na) > 0:
            c = _rgb("1a1a1a")
        if rr < 0.1:
            c = _rgb("bf8f34")
        return c
    _round_face(px, reg("gauge"), gauge)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: the striped round balloon, chains, the small basket with its lanterns."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    green, beige, dark = GREEN + (255,), BEIGE + (255,), GREEN_DARK + (255,)
    brass, chain = _rgb("c99a3c") + (255,), CHAIN + (255,)
    hull, rim, lamp = _rgb("5a6a3c") + (255,), _rgb("3c2614") + (255,), _rgb("ffd27a") + (255,)
    # the envelope: an ellipse 11 wide, 10 tall, vertical gores
    for y in range(0, 10):
        for x in range(2, 14):
            dx, dy = (x - 7.5) / 6.0, (y - 4.5) / 5.0
            if dx * dx + dy * dy <= 1.0:
                px[x, y] = beige if (x // 2) % 2 else green
                if dx * dx + dy * dy > 0.78:
                    px[x, y] = dark if (x // 2) % 2 == 0 else BEIGE_DARK + (255,)
    for x in range(4, 12):
        px[x, 7] = brass
    # the skirt and the chains
    for x in (5, 10):
        px[x, 9] = dark if x == 5 else BEIGE_DARK + (255,)
    for y, xs in ((10, (6, 9)), (11, (6, 9)), (12, (5, 10))):
        for x in xs:
            px[x, y] = chain
    px[7, 10] = px[8, 10] = brass
    px[7, 11] = px[8, 11] = _rgb("ffb03a") + (255,)
    # the basket
    for x in range(4, 12):
        px[x, 13] = rim
        px[x, 14] = hull
    for x in range(5, 11):
        px[x, 15] = rim
    px[3, 14] = lamp
    px[12, 14] = lamp
    img.save(path)
