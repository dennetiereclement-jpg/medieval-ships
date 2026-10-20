"""Texture of the steampunk airship (steampunk_airship).

  steampunk_airship.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours of the reference picture: a cream balloon in stitched panels with a blue-grey nose cap and
blue-grey bands, a brown rope net (transparent between the cords), orange braided rope hoops and
suspension lines with gold clasps and rings, triangular cream fins on wooden spars, a wooden
propeller with a brass hub, a dark brown wooden gondola with brass fittings and an iron engine.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _fill, _jitter, _planks, _rgb, paint_lamp_glass

SIZE = 256

REGIONS = {
    "balloon":     (0, 0, 32, 32),
    "balloon_blue": (32, 0, 32, 32),
    "band":        (64, 0, 32, 16),
    "net":         (96, 0, 32, 32),
    "rope":        (128, 0, 16, 16),
    "gold":        (144, 0, 16, 16),
    "brass":       (160, 0, 32, 32),
    "iron":        (192, 0, 16, 16),
    "copper":      (208, 0, 16, 16),
    "lantern":     (224, 0, 16, 16),
    "glow":        (240, 0, 16, 16),
    "hull":        (0, 32, 64, 32),
    "hull_light":  (64, 32, 64, 16),
    "deck":        (64, 48, 64, 32),
    "dark_wood":   (128, 32, 32, 16),
    "wood":        (128, 48, 64, 16),
    "end_grain":   (160, 32, 16, 16),
    "boiler":      (192, 32, 64, 32),
    "prop":        (0, 64, 64, 16),
    "balloon_in":  (176, 32, 16, 16),
    "fin":         (0, 96, 96, 96),
    # gondola fittings
    "copper_plate": (128, 64, 64, 32),
    "leather":     (192, 64, 32, 16),
    "leather_dark": (192, 80, 16, 16),
    "rope_dark":   (208, 80, 16, 16),
    "fire":        (224, 64, 32, 32),
    "crate":       (128, 96, 32, 32),
    "rug":         (160, 96, 32, 64),
    "rug_edge":    (192, 96, 16, 16),
    "grate":       (208, 96, 16, 16),
    "coal":        (224, 96, 16, 16),
    "burlap":      (240, 96, 16, 16),
    "barrel":      (192, 112, 32, 32),
    "glass":       (224, 112, 16, 16),
    "gauge":       (128, 128, 32, 32),
    "porthole":    (128, 160, 32, 32),
    "telegraph":   (160, 160, 32, 32),
    "boiler_door": (192, 160, 32, 32),
}

CREAM = _rgb("e9d6ad")
CREAM_DARK = _rgb("c4ac80")
BLUE = _rgb("5e7088")
BLUE_DARK = _rgb("3f4d61")
ROPE = _rgb("b46e33")
ROPE_DARK = _rgb("7a4520")


def _shade(c, k):
    return tuple(max(0, min(255, int(q * k))) for q in c)


def _metal(px, region, shades, rng):
    """Polished metal: a soft broad highlight across the region (round parts catch it on one facet),
    fine brushing streaks along it and a few darker spots of wear."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.8 * math.cos(2 * math.pi * (x + 0.5) / w - 0.9) + 0.1 * math.sin(2 * math.pi * y / h * 2 + 1.3)
            t += 0.12 * math.sin(y * 2.7 + x * 0.15) + rng.uniform(-0.06, 0.06)
            i = 0 if t > 0.72 else 1 if t > 0.25 else 2 if t > -0.25 else 3 if t > -0.7 else 4
            c = _rgb(shades[i])
            if rng.random() < 0.04:
                c = _shade(c, 0.88)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wood(px, region, base, dark, plank_h, rng, joints=True, nails=None, grain=0.16):
    """Planks with wood grain: each plank has its own tone, wavy darker grain lines along it, a dark
    seam under it, butt joints and (optionally) a pair of nail heads at each joint."""
    u, v, w, h = region
    rows = h // plank_h
    for r in range(rows):
        tone = _jitter(base, rng, 9)
        joint = rng.randint(5, w - 6)
        phase = rng.uniform(0, 6.3)
        freq = rng.uniform(0.18, 0.35)
        for y in range(plank_h):
            for x in range(w):
                if y == plank_h - 1:
                    c = dark
                elif joints and x == joint:
                    c = dark
                else:
                    g = math.sin(x * freq + phase + 2.2 * math.sin(x * 0.07 + r)) + 0.6 * math.sin(y * 2.1 + phase)
                    k = 1.0 - grain * (g > 1.05) + 0.05 * (g < -1.2)
                    c = _shade(tone, k)
                    if nails and joints and x in (joint - 2, joint + 2) and y == plank_h // 2 - 1:
                        c = _rgb(nails)
                px[u + x, v + r * plank_h + y] = _jitter(c, rng, 4) + (255,)


def _rivet_plates(px, region, base, edge, rivet, rng, pw=16, ph=16, tarnish=None):
    """Riveted metal plates (lapped, a row of rivets along each seam, a soft tarnish)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            xx, yy = (x + (ph // 2 if (y // ph) % 2 else 0)) % pw, y % ph
            k = 1.0 + 0.1 * math.cos(math.pi * (yy + 0.5) / ph) - 0.06 * (xx / pw)
            c = _shade(base, k)
            if tarnish and (math.sin(x * 0.7 + y * 0.3) + math.sin(y * 0.9 - x * 0.2)) > 1.75:
                c = _rgb(tarnish)
            if yy == ph - 1 or xx == 0:
                c = edge
            elif (yy == 2 and xx % 4 == 2) or (xx == 2 and yy % 4 == 2):
                c = rivet
            elif (yy == 3 and xx % 4 == 2) or (xx == 3 and yy % 4 == 2):
                c = _shade(edge, 1.3)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _round_face(px, region, paint, clear=True):
    """Paint a round face: paint(rr, ang, x, y) -> colour or None for each pixel inside the circle
    (rr in [0, 1] from the centre, ang in radians from the top, clockwise); transparent outside."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            rr = math.hypot(dx, dy)
            if rr > 1.0:
                if clear:
                    px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = paint(rr, math.atan2(dx, -dy), x, y)
            if c is not None:
                px[u + x, v + y] = tuple(c[:3]) + (255,)


def _panel(px, region, base, seam, rng, weave=0.035):
    """Balloon panel (each panel strip shows the whole region): fabric weave, slight shading,
    stitched seams along both long edges."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            # the cloth bulges between the seams: lighter in the middle of the gore, darker at its edges
            k = 1.0 - weave * ((x + 2 * y) % 3 == 0) - 0.14 * (2 * abs((y + 0.5) / h - 0.5)) ** 2 \
                - 0.05 * (2 * abs((x + 0.5) / w - 0.5)) ** 3 + 0.025 * math.sin((x + y * 0.6) * 0.45)
            c = _shade(base, k)
            if y in (0, h - 1):
                c = seam
            elif y in (1, h - 2) and x % 3 == 1:
                c = _shade(seam, 1.12)   # stitching
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _fin_shape(fin_tri, fin_curve, w, h):
    """(inside, edge distance in pixels) of a fin texture pixel. fin_curve = (C, A, B, curves) from the
    generator: tip, roots and the hollowed edges (start, edge vector, inward normal, sag) in 3D; the
    region maps C + (A - C) u + Vp v (Vp: part of B - C normal to the luff)."""
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    def sub(a, b):
        return [x - y for x, y in zip(a, b)]
    C, A, B, curves = fin_curve
    U = sub(A, C)
    L = math.sqrt(dot(U, U))
    Un = [x / L for x in U]
    BC = sub(B, C)
    Vp = [b - dot(BC, Un) * u for b, u in zip(BC, Un)]
    px_per_block = w / L

    def point(x, y):
        u, v = x / w, y / h
        return [c + uu * u + vv * v for c, uu, vv in zip(C, U, Vp)]
    AB = sub(B, A)
    ab2 = dot(AB, AB)
    # inward normal of the root edge, in the fin plane
    mid = [(a + b) / 2 for a, b in zip(A, B)]
    to_c = sub(C, mid)
    root_in = [c - dot(to_c, AB) / ab2 * e for c, e in zip(to_c, AB)]
    rl = math.sqrt(dot(root_in, root_in))
    root_in = [x / rl for x in root_in]

    def shape(x, y):
        X = point(x, y)
        dmin = dot(sub(X, A), root_in)
        if dmin < 0:
            return False, 0.0
        for E0, e, inward, sag in curves:
            e2 = dot(e, e)
            t = dot(sub(X, E0), e) / e2
            sig = dot(sub(X, E0), inward)
            tt = max(0.0, min(1.0, t))
            d = sig - sag * math.sin(math.pi * tt)
            if d < 0:
                return False, 0.0
            dmin = min(dmin, d)
        return True, dmin * px_per_block
    return shape


def make_texture(path, fin_tri, fin_curve=None):
    """fin_tri: triangle of the fins in [0, 1] region coordinates (from the generator); fin_curve: its
    curved edges (see _fin_shape)."""
    rng = random.Random(1852)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name]

    _panel(px, reg("balloon"), CREAM, CREAM_DARK, rng)
    _panel(px, reg("balloon_blue"), BLUE, BLUE_DARK, rng)
    _fill(img, reg("balloon_in"), _rgb("b8a780"), rng, 6)
    # blue-grey band: stitched edges and a row of brass eyelets
    u, v, w, h = reg("band")
    for y in range(h):
        for x in range(w):
            c = BLUE
            if y in (0, h - 1):
                c = BLUE_DARK
            elif y == h // 2 and x % 8 == 4:
                c = _rgb("d8b25a")
            elif y in (2, h - 3) and x % 3 == 0:
                c = _shade(BLUE, 1.18)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # rope net: two diamonds per tile, transparent between the cords, knots where they cross
    u, v, w, h = reg("net")
    for y in range(h):
        for x in range(w):
            a = (x + y) % 16
            b = (x - y) % 16
            on = a == 0 or b == 0
            if on:
                c = ROPE_DARK if a == 0 and b == 0 else _rgb("8c5a30")
                px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
            else:
                px[u + x, v + y] = (0, 0, 0, 0)
    # braided rope
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            c = ROPE if (x + y) % 4 < 2 else ROPE_DARK
            if (x - y) % 4 == 0:
                c = _shade(ROPE, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    _metal(px, reg("gold"), ("fbe7a1", "e6bf5a", "cfa23f", "a97f2a", "7c5a1c"), rng)
    _metal(px, reg("brass"), ("f6dc93", "dcb055", "bf8f34", "906523", "684716"), rng)
    _metal(px, reg("copper"), ("f0b08a", "d08a54", "a8643a", "7e4526", "5a2e18"), rng)
    _fill(img, reg("iron"), _rgb("3a3c40"), rng, 6)
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # wood: grained planks, nail heads at the butt joints
    _wood(px, reg("hull"), _rgb("6a4527"), _rgb("2e1d10"), 4, rng)
    _wood(px, reg("hull_light"), _rgb("7a5232"), _rgb("4a301a"), 4, rng)
    _wood(px, reg("deck"), _rgb("8a6644"), _rgb("4e3820"), 4, rng, nails="3e3026")
    _wood(px, reg("dark_wood"), _rgb("4a301a"), _rgb("281809"), 4, rng)
    _wood(px, reg("wood"), _rgb("b38a58"), _rgb("7a5a34"), 8, rng, joints=False, grain=0.1)
    # end grain: growth rings
    u, v, w, h = reg("end_grain")
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
            c = _shade(_rgb("8c5e30"), 0.86 if int(d * 0.9 + 0.3 * math.sin(x + y)) % 3 == 0 else 1.0)
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    _wood(px, reg("prop"), _rgb("8e6038"), _rgb("5a3a1e"), 8, rng, joints=False, grain=0.12)
    # copper sheathing of the gondola bottom: lapped riveted plates, darkened, a touch of verdigris
    _rivet_plates(px, reg("copper_plate"), _rgb("965a36"), _rgb("5a3018"), _rgb("c48858"), rng, tarnish="7e6446")
    # buttoned (chesterfield) leather: diamond tufts with a brass button at each crossing
    u, v, w, h = reg("leather")
    for y in range(h):
        for x in range(w):
            a, b = (x + y) % 8, (x - y) % 8
            k = 1.0 + 0.1 * math.sin(math.pi * a / 8) * math.sin(math.pi * b / 8) - 0.06
            c = _shade(_rgb("7a2e1e"), k)
            if a == 0 or b == 0:
                c = _rgb("4e1a10")
            if x % 8 == 4 and y % 8 == 0:
                c = _rgb("d8b25a")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    _fill(img, reg("leather_dark"), _rgb("4e1a10"), rng, 5)
    u, v, w, h = reg("rope_dark")
    for y in range(h):
        for x in range(w):
            c = ROPE_DARK if (x + y) % 4 < 2 else _shade(ROPE_DARK, 0.75)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # fire in the firebox: glowing coals behind the dark grate bars
    u, v, w, h = reg("fire")
    for y in range(h):
        for x in range(w):
            if x % 6 in (0, 1) or y in (0, h - 1):
                c = _rgb("2a1a12") if x % 6 == 0 else _rgb("4a2a18")
            else:
                f = (y / h) + 0.25 * math.sin(x * 0.9 + y * 0.4) + rng.uniform(-0.15, 0.15)
                c = _rgb("fff1a8") if f > 0.85 else _rgb("ffc94a") if f > 0.55 else _rgb("f08a2a") if f > 0.3 else _rgb("b8401a")
            px[u + x, v + y] = c + (255,)
    # crate: a frame of darker boards round lighter planks, a diagonal brace, nail heads
    u, v, w, h = reg("crate")
    for y in range(h):
        for x in range(w):
            if x < 4 or x >= w - 4 or y < 4 or y >= h - 4:
                c = _rgb("6e4a28")
                if (x in (1, w - 2) or y in (1, h - 2)) and (x + y) % 6 == 0:
                    c = _rgb("2a2420")
            elif abs((x - 4) - (y - 4)) < 3:
                c = _rgb("7e5630")
            else:
                c = _shade(_rgb("a88352"), 0.86 if y % 6 == 5 else 1.0 - 0.06 * ((x * 3 + y // 6) % 5 == 0))
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # runner rug: deep red with a gold and blue border and a repeating medallion
    u, v, w, h = reg("rug")
    for y in range(h):
        for x in range(w):
            ex = min(x, w - 1 - x)
            if ex == 0:
                c = _rgb("3a1410")
            elif ex < 3:
                c = _rgb("c9a04a")
            elif ex < 5:
                c = _rgb("2f4060") if (y // 2) % 2 else _rgb("c9a04a")
            elif ex == 5:
                c = _rgb("c9a04a")
            else:
                cx, cy = x - w / 2 + 0.5, (y % 32) - 15.5
                d = abs(cx) + abs(cy) * 0.6
                c = _rgb("8a2a22")
                if 7 < d < 9:
                    c = _rgb("d9b45a")
                elif d < 3:
                    c = _rgb("2f4060")
                elif (x + y) % 4 == 0 and d > 9:
                    c = _rgb("7a221c")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    _fill(img, reg("rug_edge"), _rgb("c9a04a"), rng, 8)
    # iron grating: square holes between bars
    u, v, w, h = reg("grate")
    for y in range(h):
        for x in range(w):
            c = _rgb("1a1612") if (x % 4 in (1, 2) and y % 4 in (1, 2)) else _rgb("5a3e24")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # coal
    u, v, w, h = reg("coal")
    for y in range(h):
        for x in range(w):
            c = _rgb("1c1c20") if rng.random() < 0.7 else _rgb("3a3c44") if rng.random() < 0.6 else _rgb("0c0c0e")
            px[u + x, v + y] = c + (255,)
    # burlap (sandbags, sacks): coarse weave
    u, v, w, h = reg("burlap")
    for y in range(h):
        for x in range(w):
            c = _shade(_rgb("9c8256"), 0.9 if (x % 2) ^ (y % 2) else 1.04)
            if y % 5 == 4 and x % 3 == 0:
                c = _rgb("8a7048")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # barrel: vertical staves with dark seams
    u, v, w, h = reg("barrel")
    for y in range(h):
        for x in range(w):
            c = _shade(_rgb("8c5e34"), 1.0 - 0.07 * ((x // 4) % 3) + 0.05 * math.sin(y * 0.4 + x))
            if x % 4 == 3:
                c = _rgb("4a301a")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # water glass: a glass tube half full of water
    u, v, w, h = reg("glass")
    for y in range(h):
        for x in range(w):
            c = _rgb("cfe4ec") if y < h * 0.45 else _rgb("4f7f9a")
            if x in (2, 3):
                c = _shade(c, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)

    def bezel(rr, inner=0.8):
        if rr > 0.93:
            return _rgb("684716")
        if rr > inner + 0.05:
            return _rgb("f6dc93") if rr < (0.93 + inner) / 2 else _rgb("bf8f34")
        if rr > inner:
            return _rgb("906523")
        return None

    def gauge(rr, ang, x, y):
        b = bezel(rr)
        if b:
            return b
        c = _rgb("efe6cf")
        if rr > 0.62 and (ang % (math.pi / 6)) < 0.12 and abs(ang) < 2.4:
            c = _rgb("2a2420")
        if rr > 0.62 and ang > 1.6 and ang < 2.4:
            c = _rgb("b03020")     # red sector: high pressure
        # needle at about 2 o'clock
        na = 0.9
        if rr < 0.68 and abs(math.sin(ang - na)) * rr < 0.045 and math.cos(ang - na) > 0:
            c = _rgb("1a1a1a")
        if rr < 0.1:
            c = _rgb("bf8f34")
        return c
    _round_face(px, reg("gauge"), gauge)

    def porthole(rr, ang, x, y):
        b = bezel(rr, 0.72)
        if b:
            # four bolt heads on the rim
            if 0.78 < rr < 0.9 and abs(math.sin(2 * ang)) > 0.97:
                return _rgb("fbe7a1")
            return b
        c = _rgb("2c4a5e") if rr > 0.3 else _rgb("3d6680")
        if 0.2 < rr < 0.55 and -2.3 < ang < -1.2:
            c = _rgb("a8d0e0")    # reflection
        return c
    _round_face(px, reg("porthole"), porthole)

    def telegraph(rr, ang, x, y):
        b = bezel(rr, 0.84)
        if b:
            return b
        sector = int((ang + math.pi) / (math.pi / 4)) % 8
        c = _rgb("efe6cf") if sector % 2 else _rgb("d8c8a0")
        if rr < 0.2:
            c = _rgb("bf8f34")
        elif abs(math.sin(ang * 4)) < 0.06:
            c = _rgb("2a2420")
        if rr < 0.8 and abs(math.sin(ang - 0.0)) * rr < 0.05 and math.cos(ang) > 0:
            c = _rgb("b03020")
        return c
    _round_face(px, reg("telegraph"), telegraph)
    # firebox door: riveted iron with a brass latch bar and air vents
    u, v, w, h = reg("boiler_door")
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("3e4045"), rng, 5)
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("1e2023")
            elif (x in (2, w - 3) or y in (2, h - 3)) and (x + y) % 5 == 0:
                c = _rgb("8d9399")
            elif 13 <= y <= 15 and 4 <= x <= w - 5:
                c = _rgb("c99a3e")
            elif 20 <= y <= 25 and x % 5 == 2 and 6 <= x <= w - 7:
                c = _rgb("120c0a")
            px[u + x, v + y] = c + (255,)
    # boiler: riveted iron plates with a brass band
    u, v, w, h = reg("boiler")
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("45484d"), rng, 5)
            if x % 16 == 0 or y % 16 == 0:
                c = _rgb("26282b")
            elif (x % 16 in (2, 13)) and y % 4 == 2:
                c = _rgb("8d9399")
            if 12 <= y <= 15:
                c = _jitter(_rgb("c99a3e"), rng, 6)
            px[u + x, v + y] = c + (255,)
    # fins: cream canvas with a brown bolt rope and seams parallel to the leading edge,
    # transparent outside the triangle
    u, v, w, h = reg("fin")
    tri = [(p[0] * w, p[1] * h) for p in fin_tri]

    def inside(x, y):
        (ax, ay), (bx, by), (cx, cy) = tri

        def side(x1, y1, x2, y2):
            return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
        d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    def edge_dist(x, y):
        d = 1e9
        for i in range(3):
            (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
            ex, ey = x2 - x1, y2 - y1
            L2 = ex * ex + ey * ey
            t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / L2))
            d = min(d, math.hypot(x - x1 - ex * t, y - y1 - ey * t))
        return d
    shape = _fin_shape(fin_tri, fin_curve, w, h) if fin_curve is not None else None
    for y in range(h):
        for x in range(w):
            if shape is not None:
                ok, d = shape(x + 0.5, y + 0.5)
            else:
                ok = inside(x + 0.5, y + 0.5)
                d = edge_dist(x + 0.5, y + 0.5) if ok else 0.0
            if not ok:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            # canvas: fine weave, a soft shade between the seams that run parallel to the root
            c = _shade(_rgb("efdcae"), 1.0 - 0.04 * ((x * 3 + y) % 7 == 0) - 0.05 * (0.5 - 0.5 * math.cos(2 * math.pi * y / 12)))
            if y % 12 == 0:
                c = _shade(c, 0.86)
            if d < 1.6:
                c = _rgb("6e4a2a")
            elif d < 3.0:
                c = _rgb("d4c296")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: cream balloon with a blue nose, net lines, fin, gondola below."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 14, 9), fill=CREAM + (255,), outline=_rgb("8c6a40") + (255,))
    d.pieslice((9, 2, 15, 9), -90, 90, fill=BLUE + (255,))
    for x in (5, 8, 11):
        d.line((x, 3, x, 8), fill=ROPE + (255,))
    d.line((3, 5, 13, 5), fill=BLUE_DARK + (255,))
    d.polygon([(2, 4), (0, 1), (3, 3)], fill=_rgb("efe2bf") + (255,))
    d.line((0, 6, 2, 6), fill=_rgb("7a5232") + (255,))
    d.line((6, 9, 5, 12), fill=ROPE + (255,))
    d.line((10, 9, 11, 12), fill=ROPE + (255,))
    d.polygon([(3, 12), (13, 12), (12, 14), (4, 14)], fill=_rgb("5a3a22") + (255,))
    d.line((3, 12, 13, 12), fill=_rgb("d8b25a") + (255,))
    img.save(path)
