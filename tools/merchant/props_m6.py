"""Props of the armour merchant's tent (tente_armures, agent M6): textures (polished silver / dark steel / gold plate,
gilded filigree, chain mail, cuirass fronts, helmet faces, the blue shield with the golden eagle, the eagle rug, the
iron-bound chests) and the geometry: armour stands in four styles (knight, fantasy, heavy, soldier), helmets of six
shapes (great helm, barbute, armet, bascinet, nasal helm, sallet), breastplates on a stand, iron-bound chests,
two-tier display pedestals, the eagle shield.

Usage (after ml.setup and ml.Atlas):
    import props_m6 as p6
    p6.add_regions(atlas)                 # the m6_* regions, before export
    p6.armour_stand(shell, det, "knight", (x, y, z), style="knight", yaw=0.0, helm=None, pedestal="block")
    p6.helmet(det, "helm", (x, y, z), kind="great", metal="m6_silver", yaw=0.0, s=1.0)
"""
import math
import random

import merchantlib as ml

v3, UP, EYE = ml.v3, ml.UP, ml.EYE
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale

GOLD_C, GOLD_D, GOLD_L = (226, 176, 58), (128, 86, 20), (252, 226, 140)


# ---------------------------------------------------------------- painters
def _ramp(stops, t):
    t = min(1.0, max(0.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return _mix(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


SILVER = [(0.0, (50, 56, 74)), (0.4, (102, 110, 132)), (0.75, (152, 160, 180)), (1.0, (204, 212, 226))]
DARK = [(0.0, (26, 28, 38)), (0.4, (50, 56, 74)), (0.75, (84, 92, 116)), (1.0, (128, 138, 164))]
GOLDS = [(0.0, (92, 58, 14)), (0.4, (160, 110, 32)), (0.75, (210, 160, 58)), (1.0, (246, 214, 124))]


def _plates(stops, seed, lame=None, rivet=GOLD_C, edge=None):
    """A plate (each cube stretches the whole region): rounded sheen across u, lighter at the top, a dark outline,
    an optional coloured trim line along the top and bottom edges (gold), rivets in the corners; lame = a dark line
    every `lame` px (several lames on one face, e.g. the skirt) or None."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        for y in range(h):
            for x in range(w):
                fy = (y % lame) / lame if lame else y / h
                t = 0.3 + 0.5 * math.sin((x + 0.5) / w * math.pi) + 0.18 * (1 - fy) - 0.12 * fy + 0.05 * math.sin(y * 0.9 + x * 0.4)
                c = _ramp(stops, t)
                if x == 0 or x == w - 1 or y == 0 or y == h - 1 or (lame and y % lame == lame - 1):
                    c = _scale(_ramp(stops, 0.05), 0.75)
                elif edge is not None and (y in (1, 2) or y in (h - 2, h - 3) or (lame and y % lame in (0, 1))):
                    c = edge if (x + y) % 4 else _scale(edge, 0.8)
                img.putpixel((x, y), _jitter(c, rng, 3) + (255,))
        if rivet:
            for (x, y) in ((3, 4), (w - 4, 4), (3, h - 5), (w - 4, h - 5)):
                img.putpixel((x, y), rivet + (255,))
    return paint


def _filigree(img):
    """Steel with gold filigree: a gold border, gold scrolls, polished centre (the fantasy armour)."""
    from PIL import Image, ImageDraw
    rng = random.Random(61)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            t = 0.4 + 0.45 * math.sin((x + 0.5) / w * math.pi) - 0.15 * ((y % 8) / 8)
            c = _ramp(SILVER, t)
            img.putpixel((x, y), _jitter(c, rng, 3) + (255,))
    S = 4
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    W, H = w * S, h * S
    d.rectangle([0, 0, W - 1, H - 1], outline=GOLD_C + (255,), width=S * 2)
    for k in range(1, 4):
        y = H * k / 4
        d.line([(0, y), (W, y)], fill=GOLD_D + (255,), width=S)
    for k in range(4):
        cy = H * (k + 0.5) / 4
        d.arc([W * 0.3, cy - H * 0.08, W * 0.5, cy + H * 0.08], 90, 360, fill=GOLD_C + (255,), width=S)
        d.arc([W * 0.5, cy - H * 0.08, W * 0.7, cy + H * 0.08], 180, 90, fill=GOLD_C + (255,), width=S)
    img.alpha_composite(big.resize((w, h), Image.LANCZOS))


def _mail(img):
    """Chain mail: rows of small rings, offset every other row, grey with dark gaps."""
    rng = random.Random(62)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            ox = 1 if (y // 2) % 2 else 0
            lx, ly = (x + ox) % 2, y % 2
            c = (150, 154, 162) if (lx == 0 and ly == 0) else (110, 114, 122) if lx != ly else (52, 54, 60)
            k = 0.85 + 0.25 * math.sin((x + 0.5) / w * math.pi)
            img.putpixel((x, y), _jitter(_scale(c, k), rng, 6) + (255,))


def _cuirass(stops, seed, trim=GOLD_C, trim_d=GOLD_D, ridge=True, belly_lames=3):
    """Front of a cuirass: rounded breast sheen, a centre ridge, a gold neck line and side trims, lames at the belly."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        for y in range(h):
            for x in range(w):
                fx = (x + 0.5) / w
                fy = (y + 0.5) / h
                t = 0.3 + 0.55 * math.sin(fx * math.pi) * (1.0 - 0.35 * fy) + (0.12 if (ridge and abs(fx - 0.5) < 0.04) else 0.0)
                if ridge and 0.47 < fx < 0.5:
                    t -= 0.18
                c = _ramp(stops, t)
                lam_top = 1.0 - belly_lames * 0.11
                if fy > lam_top:
                    ly = (fy - lam_top) / 0.11
                    if ly % 1.0 > 0.82:
                        c = _scale(_ramp(stops, 0.1), 0.8)
                    elif ly % 1.0 < 0.18 and trim:
                        c = trim
                if trim and (y <= 1 or x <= 1 or x >= w - 2):
                    c = trim if (y <= 1 or (x + y) % 3) else trim_d
                if trim and y == 2:
                    c = trim_d
                img.putpixel((x, y), _jitter(c, rng, 3) + (255,))
    return paint


def _face(kind, stops, seed):
    """A helmet's front: polished metal and its opening (slit, T, visor slits, open face with a nose guard)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        for y in range(h):
            for x in range(w):
                fx = (x + 0.5) / w
                c = _ramp(stops, 0.3 + 0.55 * math.sin(fx * math.pi) - 0.15 * (y / h))
                dark = False
                if kind == "great":     # an eye slit, a vertical rib, breathing holes
                    dark = (5 <= y <= 6 and 1 <= x <= w - 2) or (y >= 10 and y % 3 == 0 and x % 3 == 1 and 2 <= x <= w - 3)
                    if x in (w // 2 - 1, w // 2) and y > 6:
                        c = _ramp(stops, 0.95)
                elif kind == "barbute":  # T opening
                    dark = (5 <= y <= 7 and 3 <= x <= w - 4) or (abs(x - (w - 1) / 2) <= 1.6 and 5 <= y <= h - 2)
                elif kind == "armet":    # two visor slits above a pointed bevor with holes
                    dark = (y in (5, 7) and 2 <= x <= w - 3 and abs(x - (w - 1) / 2) > 0.8) or (y >= 11 and y % 2 == 1 and x % 3 == 0 and 3 <= x <= w - 4)
                elif kind == "bascinet":  # an open face in a round helm
                    dark = (abs(x - (w - 1) / 2) < w * 0.28 and h * 0.32 < y < h * 0.86)
                elif kind == "nasal":    # open face, a nose guard down the middle
                    dark = (abs(x - (w - 1) / 2) < w * 0.32 and h * 0.38 < y < h * 0.95 and abs(x - (w - 1) / 2) > 1.0)
                if dark:
                    c = (18, 18, 22)
                img.putpixel((x, y), _jitter(c, rng, 3) + (255,))
    return paint


def _heater(W, H):
    """The outline of a heater shield in a W x H box (flat top, straight upper sides, curved to a point)."""
    pts = [(0, 0), (W - 1, 0), (W - 1, H * 0.42)]
    for k in range(1, 14):
        t = k / 14
        pts.append((W / 2 + (W / 2 - 1) * math.cos(t * math.pi / 2), H * 0.42 + H * 0.58 * math.sin(t * math.pi / 2) - 1))
    pts += [(W / 2 - (W / 2 - 1) * math.cos(t * math.pi / 2), H * 0.42 + H * 0.58 * math.sin(t * math.pi / 2) - 1)
            for t in [k / 14 for k in range(13, 0, -1)]]
    pts.append((0, H * 0.42))
    return pts


def _eagle(d, P, W, gold=GOLD_C, dark=GOLD_D, light=GOLD_L):
    """A displayed eagle (spread wings, head turned to its right, fanned tail) in gold."""
    lw = max(1, int(W * 0.012))
    # wings: three feather tiers each side
    for s in (-1, 1):
        def Q(x, y):
            return P(0.5 + s * x, y)
        wing = [Q(0.06, 0.34), Q(0.18, 0.2), Q(0.32, 0.12), Q(0.44, 0.08), Q(0.43, 0.2), Q(0.46, 0.24), Q(0.42, 0.34), Q(0.45, 0.4),
                Q(0.38, 0.46), Q(0.4, 0.52), Q(0.3, 0.55), Q(0.2, 0.56), Q(0.08, 0.5)]
        d.polygon(wing, fill=gold, outline=dark)
        for k in range(4):
            y0 = 0.22 + k * 0.08
            d.line([Q(0.12, y0 + 0.08), Q(0.36 + 0.02 * k, y0 + 0.02)], fill=dark, width=lw)
        # legs and talons
        d.line([Q(0.06, 0.62), Q(0.13, 0.72), Q(0.18, 0.74)], fill=gold, width=lw * 4)
        d.line([Q(0.13, 0.72), Q(0.12, 0.78)], fill=dark, width=lw * 2)
    body = [P(0.42, 0.3), P(0.58, 0.3), P(0.6, 0.48), P(0.56, 0.64), P(0.5, 0.68), P(0.44, 0.64), P(0.4, 0.48)]
    d.polygon(body, fill=gold, outline=dark)
    for k in range(3):
        d.arc([*P(0.44, 0.38 + k * 0.08), *P(0.56, 0.46 + k * 0.08)], 20, 160, fill=dark, width=lw)
    # tail
    d.polygon([P(0.45, 0.64), P(0.55, 0.64), P(0.62, 0.84), P(0.56, 0.8), P(0.5, 0.88), P(0.44, 0.8), P(0.38, 0.84)], fill=gold,
              outline=dark)
    # neck and head (turned to the viewer's left), beak
    d.polygon([P(0.45, 0.32), P(0.55, 0.32), P(0.52, 0.2), P(0.46, 0.2)], fill=gold, outline=dark)
    d.ellipse([*P(0.4, 0.1), *P(0.54, 0.24)], fill=gold, outline=dark)
    d.polygon([P(0.41, 0.15), P(0.33, 0.18), P(0.38, 0.21), P(0.42, 0.2)], fill=light, outline=dark)
    ex, ey = P(0.45, 0.15)
    d.ellipse([ex - lw * 1.5, ey - lw * 1.5, ex + lw * 1.5, ey + lw * 1.5], fill=(40, 24, 10))


def _eagle_shield(img):
    """The big heater shield: gold rim, blue field, a golden eagle displayed (cut-out outside the shield)."""
    from PIL import Image, ImageDraw
    w, h = img.size
    S = 4
    W, H = w * S, h * S
    big = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    out = _heater(W, H)
    d.polygon(out, fill=(176, 130, 44))
    inner = [(W / 2 + (x - W / 2) * 0.88, H * 0.045 + y * 0.92) for (x, y) in out]
    d.polygon(inner, fill=(40, 70, 150))
    inner2 = [(W / 2 + (x - W / 2) * 0.8, H * 0.08 + y * 0.85) for (x, y) in out]
    d.polygon(inner2, fill=(46, 84, 172))
    d.line(inner + [inner[0]], fill=(226, 184, 80), width=S)

    def P(x, y):
        return (W * (0.1 + 0.8 * x), H * (0.1 + 0.68 * y))
    _eagle(d, P, W)
    im = big.resize((w, h), Image.LANCZOS)
    # sheen + rivets on the rim
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a:
                k = 1.0 + 0.12 * math.sin((x + 0.5) / w * math.pi) - 0.1 * (y / h)
                px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), a)
    img.alpha_composite(im)


def _rug(img):
    """The blue rug: dark blue field, two gold borders with a corner motif, a golden eagle in the middle, fringes."""
    from PIL import Image, ImageDraw
    rng = random.Random(66)
    w, h = img.size
    blue, blue_d, blue_l = (52, 66, 138), (30, 38, 86), (70, 86, 160)
    for y in range(h):
        for x in range(w):
            c = blue if ((x // 2 + y // 2) % 2) else _scale(blue, 0.94)
            img.putpixel((x, y), _jitter(c, rng, 5) + (255,))
    S = 3
    W, H = w * S, h * S
    big = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    g = GOLD_C + (255,)
    d.rectangle([S * 3, S * 3, W - S * 4, H - S * 4], outline=g, width=S * 3)
    d.rectangle([S * 8, S * 8, W - S * 9, H - S * 9], outline=blue_d + (255,), width=S * 2)
    d.rectangle([S * 11, S * 11, W - S * 12, H - S * 12], outline=g, width=S * 2)
    for cx, cy in ((S * 18, S * 18), (W - S * 19, S * 18), (S * 18, H - S * 19), (W - S * 19, H - S * 19)):
        r = S * 4
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=g)
    # a lozenge medallion and the eagle in it
    cx, cy = W / 2, H / 2
    rx, ry = W * 0.32, H * 0.24
    d.polygon([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)], fill=blue_l + (255,), outline=g, width=S * 2)

    def P(x, y):
        return (cx - W * 0.26 + W * 0.52 * x, cy - H * 0.21 + H * 0.42 * y)
    _eagle(d, P, W * 0.6)
    img.alpha_composite(big.resize((w, h), Image.LANCZOS))
    for x in range(0, w, 2):
        for y in (0, h - 1):
            img.putpixel((x, y), (230, 214, 170, 255))


def _chest(top=False):
    """Light iron-bound planks (the chests and pedestals): horizontal boards, dark iron bands along the edges,
    corner plates with rivets (top: boards across, a band each side)."""
    def paint(img):
        rng = random.Random(67 + top)
        w, h = img.size
        for y in range(h):
            for x in range(w):
                board = y // 8
                c = _mix((196, 128, 58), (150, 92, 40), 0.3 + 0.4 * ((board * 37) % 5) / 5 + 0.15 * math.sin(x * 0.5 + board))
                if y % 8 == 7:
                    c = (96, 58, 26)
                img.putpixel((x, y), _jitter(c, rng, 7) + (255,))
        iron, iron_l = (54, 54, 60), (96, 96, 104)
        for y in range(h):
            for x in range(w):
                band = y < 3 or y >= h - 3 or ((x < 3 or x >= w - 3) and not top)
                corner = (x < 7 or x >= w - 7) and (y < 7 or y >= h - 7)
                if band or corner:
                    img.putpixel((x, y), _jitter(iron if (x + y) % 5 else iron_l, rng, 4) + (255,))
        for (x, y) in ((4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)):
            img.putpixel((x, y), (190, 160, 96, 255))
    return paint


def _plank_wall(img):
    """The wooden lining of the back wall: vertical boards, warm and light, dark joints."""
    rng = random.Random(68)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            b = x // 8
            c = _mix((170, 108, 52), (120, 72, 34), 0.25 + 0.5 * ((b * 53) % 7) / 7 + 0.12 * math.sin(y * 0.35 + b * 1.7))
            if x % 8 == 7:
                c = (70, 42, 20)
            if (y + b * 11) % 37 == 0:
                c = _scale(c, 0.8)
            img.putpixel((x, y), _jitter(c, rng, 6) + (255,))


REGIONS = [
    ("m6_silver", 16, 16, _plates(SILVER, 601, edge=None)),
    ("m6_silver_t", 16, 16, _plates(SILVER, 602, edge=GOLD_C)),
    ("m6_dark", 16, 16, _plates(DARK, 603, rivet=GOLD_C)),
    ("m6_dark_t", 16, 16, _plates(DARK, 606, edge=(176, 132, 46), rivet=None)),
    ("m6_gold", 16, 16, _plates(GOLDS, 604, rivet=(110, 70, 18))),
    ("m6_steel", 16, 16, _plates(SILVER, 605, rivet=None)),
    ("m6_fancy", 32, 32, _filigree),
    ("m6_mail", 32, 32, _mail),
    ("m6_cuir_silver", 32, 32, _cuirass(SILVER, 611)),
    ("m6_cuir_dark", 32, 32, _cuirass(DARK, 612)),
    ("m6_cuir_fancy", 32, 32, _cuirass(SILVER, 613, belly_lames=4)),
    ("m6_cuir_plain", 32, 32, _cuirass(SILVER, 614, trim=None, belly_lames=2)),
    ("m6_v_great", 16, 16, _face("great", SILVER, 621)),
    ("m6_v_great_d", 16, 16, _face("great", DARK, 622)),
    ("m6_v_barbute", 16, 16, _face("barbute", SILVER, 623)),
    ("m6_v_armet", 16, 16, _face("armet", SILVER, 624)),
    ("m6_v_armet_d", 16, 16, _face("armet", DARK, 625)),
    ("m6_v_bascinet", 16, 16, _face("bascinet", DARK, 626)),
    ("m6_v_nasal", 16, 16, _face("nasal", SILVER, 627)),
    ("m6_chest", 32, 32, _chest(False)),
    ("m6_chest_top", 32, 32, _chest(True)),
    ("m6_wall", 64, 64, _plank_wall),
    ("m6_eagle", 48, 60, _eagle_shield),
    ("m6_rug", 100, 140, _rug),
]


def add_regions(atlas):
    for name, w, h, painter in REGIONS:
        atlas.add(name, w, h, painter)


# ---------------------------------------------------------------- geometry
def _local(foot, yaw):
    foot = v3(*foot)
    R = ml.ry(yaw)

    def P(x, y, z):
        return foot + R @ v3(x, y, z)
    return P, R


FACES = {"m6_silver": "m6_v_great", "m6_silver_t": "m6_v_great", "m6_steel": "m6_v_great", "m6_dark": "m6_v_great_d",
         "m6_gold": "m6_v_armet"}


def helmet(bone, name, foot, kind="great", metal="m6_silver", yaw=0.0, s=1.0, crest=None, face=None):
    """A helmet standing on `foot` (its front towards +z turned by yaw): great (flat-topped bucket helm, eye slit),
    barbute (rounded, T opening), armet (rounded skull, pointed visor), bascinet (round, open face), nasal (conical,
    nose guard), sallet (rounded, a tail at the back). crest: a region for a ridge on top (e.g. "gold")."""
    P, R = _local(foot, yaw)

    def B(nm, c, size, reg, rot=None):
        ml.add_cube(bone, "%s_%s" % (name, nm), P(*[k * s for k in c]), R @ (rot if rot is not None else EYE), [k * s for k in size], reg,
                    stretch=True)
    if kind == "great":
        B("body", (0, 0.14, 0), (0.25, 0.28, 0.27), {"all": metal, "+3": face or FACES.get(metal, "m6_v_great")})
        B("top", (0, 0.3, 0), (0.21, 0.05, 0.23), metal)
    elif kind == "barbute":
        B("body", (0, 0.12, 0), (0.25, 0.24, 0.27), {"all": metal, "+3": face or "m6_v_barbute"})
        B("dome", (0, 0.27, 0), (0.22, 0.07, 0.24), metal)
        B("cap", (0, 0.32, 0), (0.14, 0.04, 0.16), metal)
    elif kind == "armet":
        B("body", (0, 0.11, -0.01), (0.24, 0.22, 0.25), metal)
        B("dome", (0, 0.255, -0.01), (0.21, 0.07, 0.23), metal)
        B("cap", (0, 0.3, -0.01), (0.13, 0.04, 0.15), metal)
        B("visor", (0, 0.13, 0.09), (0.15, 0.16, 0.15), {"all": metal, "+3": face or "m6_v_armet", "-1": face or "m6_v_armet"},
          rot=ml.ry(math.pi / 4))
    elif kind == "bascinet":
        for k, (r, h, y) in enumerate(((0.13, 0.17, 0.0), (0.118, 0.06, 0.17), (0.088, 0.05, 0.23), (0.045, 0.03, 0.28))):
            ml.octo(bone, "%s_l%d" % (name, k), P(0, y * s, 0), r * s, h * s, metal, yaw=yaw)
        B("face", (0, 0.1, 0.105), (0.13, 0.14, 0.02), {"all": metal, "+3": face or "m6_v_bascinet"})
    elif kind == "nasal":
        for k, (r, h, y) in enumerate(((0.13, 0.13, 0.0), (0.095, 0.08, 0.13), (0.045, 0.07, 0.21))):
            ml.octo(bone, "%s_l%d" % (name, k), P(0, y * s, 0), r * s, h * s, metal, yaw=yaw)
        B("band", (0, 0.03, 0), (0.25, 0.04, 0.25), "iron")
        B("nose", (0, 0.0, 0.125), (0.035, 0.13, 0.025), "iron")
    elif kind == "sallet":
        B("body", (0, 0.12, 0), (0.24, 0.2, 0.26), {"all": metal, "+3": face or "m6_v_armet"})
        B("dome", (0, 0.25, -0.01), (0.2, 0.08, 0.23), metal)
        B("tail", (0, 0.06, -0.17), (0.22, 0.05, 0.14), metal, rot=ml.rx(-0.35))
    else:
        raise KeyError(kind)
    if crest:
        top = {"great": 0.33, "barbute": 0.34, "armet": 0.32, "bascinet": 0.31, "nasal": 0.28, "sallet": 0.29}[kind]
        B("crest", (0, top, -0.01), (0.035, 0.06, 0.24), crest)


STYLES = {
    # cuirass sides, cuirass front, pauldrons, arms, gauntlets, skirt, belt, trims (None: none), width, bulk
    "knight":  dict(body="m6_silver", front="m6_cuir_silver", pauld="m6_silver_t", arm="m6_silver", gaunt="m6_silver",
                    skirt="m6_silver_t", belt="leather", trim="gold", w=1.0, bulk=1.0, pauld_n=2),
    "fantasy": dict(body="m6_fancy", front="m6_cuir_fancy", pauld="m6_gold", arm="m6_gold", gaunt="gold",
                    skirt="m6_silver_t", belt="gold", trim="gold", w=1.0, bulk=1.12, pauld_n=3),
    "heavy":   dict(body="m6_dark", front="m6_cuir_dark", pauld="m6_dark", arm="m6_dark", gaunt="m6_dark",
                    skirt="m6_dark", belt="gold", trim=None, w=1.05, bulk=1.25, pauld_n=3),
    "soldier": dict(body="m6_mail", front="m6_cuir_plain", pauld="m6_steel", arm="m6_mail", gaunt="leather",
                    skirt="m6_mail", belt="leather", trim=None, w=0.95, bulk=0.9, pauld_n=1),
}


def pedestal(bone, name, foot, kind="tier", yaw=0.0, solid=True, s=1.0):
    """A display pedestal of iron-bound planks: tier (a wide base and a smaller step), block (one square block), or
    tall (a high block for a breastplate behind a counter). Returns its top height."""
    P, R = _local(foot, yaw)
    reg = {"all": "m6_chest", "+2": "m6_chest_top"}
    if kind == "tier":
        ml.rbox(bone, name + "_base", P(0, 0, 0), (0.8 * s, 0.2 * s, 0.64 * s), yaw, reg, solid=solid, stretch=True)
        ml.rbox(bone, name + "_step", P(0, 0.2 * s, 0), (0.56 * s, 0.14 * s, 0.46 * s), yaw, reg, stretch=True)
        return v3(*foot)[1] + 0.34 * s
    if kind == "tall":
        ml.rbox(bone, name + "_base", P(0, 0, 0), (0.62 * s, 0.8, 0.5 * s), yaw, reg, solid=solid, stretch=True)
        return v3(*foot)[1] + 0.8
    ml.rbox(bone, name + "_base", P(0, 0, 0), (0.62 * s, 0.24 * s, 0.5 * s), yaw, reg, solid=solid, stretch=True)
    return v3(*foot)[1] + 0.24 * s


def armour_stand(bone, det, name, foot, style="knight", yaw=0.0, helm=None, pedestal_kind="tier", skirt=True, arms=True,
                 solid=True, s=1.0):
    """An armour on a wooden stand (torso armour on a post: skirt of lames, belt, cuirass with a ridge, gorget, layered
    pauldrons, arms with couters and gauntlets), on a pedestal; helm = (kind, metal, crest) or None (an open neck)."""
    st = STYLES[style]
    foot = v3(*foot)
    y0 = pedestal(bone, name + "_ped", foot, pedestal_kind, yaw=yaw, solid=False, s=s) if pedestal_kind else foot[1]
    P, R = _local((foot[0], y0, foot[2]), yaw)
    w, bk = st["w"], st["bulk"]

    def B(nm, c, size, reg, rot=None, b=None):
        ml.add_cube(b or bone, "%s_%s" % (name, nm), P(*[k * s for k in c]), R @ (rot if rot is not None else EYE), [k * s for k in size], reg,
                    stretch=True)
    B("post", (0, 0.42, -0.02), (0.13, 0.84, 0.13), {"all": "wood_dark", "+2": "end_grain", "-2": "end_grain"})
    if skirt:
        for k in range(3):   # the faulds: three lames widening downwards
            B("skirt_%d" % k, (0, 0.985 - k * 0.08, 0), ((0.44 + 0.04 * k) * w, 0.09, (0.28 + 0.02 * k) * bk), st["skirt"])
        for sx in (-1, 1):
            B("tasset_%d" % sx, (sx * 0.12 * w, 0.66, 0.15 * bk + 0.025), (0.21 * w, 0.24, 0.035), st["skirt"], rot=ml.rx(-0.15) @ ml.rz(sx * 0.1))
    B("belt", (0, 1.065, 0), (0.45 * w + 0.01, 0.06, 0.29 * bk + 0.02), st["belt"])
    B("buckle", (0, 1.065, 0.145 * bk + 0.025), (0.09, 0.085, 0.03), "gold" if st["belt"] != "gold" else "brass", b=det)
    B("waist", (0, 1.2, 0), (0.42 * w, 0.2, 0.27 * bk), {"all": st["body"], "+3": st["skirt"]})
    B("chest", (0, 1.44, 0), (0.5 * w, 0.28, 0.31 * bk), {"all": st["body"], "+3": st["front"]})
    B("ridge", (0, 1.42, 0.155 * bk - 0.08), (0.15, 0.26, 0.15), st["body"], rot=ml.ry(math.pi / 4))
    B("gorget", (0, 1.61, 0), (0.3 * w, 0.07, 0.26 * bk), st["pauld"])
    if st["trim"]:
        B("neck_trim", (0, 1.655, 0), (0.2, 0.03, 0.18), st["trim"], b=det)
    for sx in (-1, 1):
        B("pauld_%d" % sx, (sx * 0.27 * w, 1.57, 0), (0.25 * bk, 0.15, 0.36 * bk), st["pauld"], rot=ml.rz(-sx * 0.42))
        for k in range(st["pauld_n"] - 1):
            B("pauld_%d_%d" % (sx, k), (sx * (0.315 + 0.025 * k) * w, 1.48 - 0.075 * k, 0), (0.21 * bk, 0.085, (0.35 - 0.01 * k) * bk), st["pauld"],
              rot=ml.rz(-sx * (0.75 + 0.15 * k)))
        if style == "fantasy":   # raised guards on the pauldrons
            B("haute_%d" % sx, (sx * 0.2 * w, 1.66, 0), (0.035, 0.1, 0.3 * bk), "gold", b=det)
        if st["trim"]:
            k = st["pauld_n"] - 2
            B("pauld_trim_%d" % sx, (sx * (0.335 + 0.025 * k) * w, 1.44 - 0.075 * k, 0), (0.19 * bk, 0.022, (0.36 - 0.01 * k) * bk), st["trim"],
              rot=ml.rz(-sx * (0.8 + 0.15 * k)), b=det)
        if arms:
            ax = sx * (0.33 * w + 0.05 * (bk - 1))
            B("arm_%d" % sx, (ax, 1.27, 0), (0.13 * bk, 0.24, 0.15 * bk), st["arm"])
            B("couter_%d" % sx, (ax, 1.12, 0.02), (0.15 * bk, 0.09, 0.17 * bk), st["pauld"], b=det)
            B("forearm_%d" % sx, (ax, 0.98, 0.04), (0.12 * bk, 0.2, 0.13 * bk), st["arm"], rot=ml.rx(-0.12))
            B("gauntlet_%d" % sx, (ax, 0.84, 0.06), (0.11 * bk, 0.11, 0.13 * bk), st["gaunt"], b=det)
    if helm:
        kind, metal, crest = helm
        helmet(bone, name + "_helm", P(0, 1.64 * s, 0), kind=kind, metal=metal, yaw=yaw, s=1.05 * s, crest=crest)
    else:
        B("neck", (0, 1.7, -0.02), (0.1, 0.08, 0.1), {"all": "wood_dark", "+2": "end_grain"}, b=det)
    if solid:
        hx = 0.4 * max(1.0, w) * s     # the pedestal's footprint (the pauldrons overhang it a little)
        hz = (0.33 if pedestal_kind == "tier" else 0.27) * s
        ml.collide((foot[0] - hx, foot[1], foot[2] - hz, foot[0] + hx, y0 + 1.75 * s, foot[2] + hz))


def chest(bone, det, name, foot, size=(0.8, 0.52, 0.56), yaw=0.0, solid=True):
    """An iron-bound chest (light planks, a rounded lid, two iron straps over it, a gold lock plate)."""
    P, R = _local(foot, yaw)
    w, h, d = size
    hb = h * 0.68
    reg = {"all": "m6_chest", "+2": "m6_chest_top", "-2": "m6_chest_top"}
    ml.rbox(bone, name, P(0, 0, 0), (w, hb, d), yaw, reg, stretch=True)
    ml.rbox(bone, name + "_lid", P(0, hb, 0), (w + 0.02, h * 0.2, d + 0.02), yaw, reg, stretch=True)
    ml.rbox(bone, name + "_lid_top", P(0, hb + h * 0.2, 0), (w, h * 0.12, d * 0.72), yaw, {"all": "m6_chest_top"}, stretch=True)
    for k, sx in enumerate((-0.28, 0.28)):
        ml.rbox(det, "%s_strap_%d" % (name, k), P(sx * w, -0.005, 0), (0.06, h * 0.9 + 0.01, d + 0.03), yaw, "black_iron")
        ml.rbox(det, "%s_strap_top_%d" % (name, k), P(sx * w, h * 0.9, 0), (0.06, h * 0.12, d * 0.74), yaw, "black_iron")
    ml.add_cube(det, name + "_lock", P(0, hb - 0.02, d / 2 + 0.015), R, (0.11, 0.13, 0.03), "gold")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        f = v3(*foot)
        ml.collide((f[0] - ex, f[1], f[2] - ez, f[0] + ex, f[1] + h, f[2] + ez))
    return v3(*foot)[1] + h * 0.9 + 0.02


def eagle_shield(bone, det, name, center, normal, w=0.84, h=1.06):
    """The big blue heater shield with the golden eagle (both faces), a wooden back board and a grip."""
    c = v3(*center)
    n = ml.norm(v3(*normal))
    ml.plate(bone, name, c, w, h, "m6_eagle", normal=n, th=0.05, edge=None)
    side = ml.norm(ml.np.cross(UP, n))
    up = ml.np.cross(n, side)
    axes = ml.np.column_stack([side, up, n])
    ml.add_cube(det, name + "_back", c - n * 0.035 + up * 0.12, axes, (w * 0.82, h * 0.5, 0.025), "wood_dark")
    ml.add_cube(det, name + "_grip", c - n * 0.06 + up * 0.1, axes, (0.24, 0.05, 0.03), "leather")
