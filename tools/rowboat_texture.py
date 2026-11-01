"""Procedural pixel-art texture of the Rowboat (rowboat): one 128x128 atlas.

Colours of the reference: warm natural brown planking, darker and a little greyer towards the keel, a light
tan gunwale, pale ribs, dark floorboards, dark forged iron bands, a tan laid rope.

Every region is (u, v, w, h); REGIONS is shared with tools/generate_rowboat.py.
"""
import math
import random

from PIL import Image

from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain

SIZE = 128

REGIONS = {
    # one clinker strake each: lit upper edge, grain, the dark shadow of the lap along the bottom (stretched over a
    # strake's height, u windowed by the generator)
    "strake":      (0, 0, 64, 6),      # mid brown (topsides)
    "strake_up":   (0, 8, 64, 6),      # greyer, weathered (the sheer strake under the rail)
    "strake_low":  (0, 16, 64, 6),     # darker, greyer (bilge and garboard)
    "inner":       (0, 24, 64, 8),     # the inside of the planking (raw, lighter)
    "gunwale":     (64, 0, 64, 8),     # light tan rail, grain along u
    "rib":         (64, 8, 32, 8),     # pale ribs
    "floor":       (64, 16, 64, 8),    # dark floorboards along u
    "thwart":      (0, 32, 64, 8),     # bench planks along u (two planks)
    "keel":        (0, 40, 64, 8),     # dark keel plank
    "oar":         (64, 40, 64, 8),
    "blade":       (64, 48, 32, 8),
    "post":        (64, 24, 16, 16),   # stem / stern posts, tholepins (grain along u)
    "end_grain":   (80, 24, 16, 16),
    "iron":        (96, 48, 16, 16),
    "rope":        (112, 48, 16, 16),
    "seat":        (0, 48, 32, 8),     # the stern seat board (across)
}


def _strake(img, region, rng, base, dark, seam, lit=1.1, knots=0.08):
    """One clinker plank the height of the region: a lit upper edge, wavy grain, a dark lap shadow at the bottom."""
    u, v, w, h = region
    px = img.load()
    f1, p1 = rng.uniform(0.05, 0.11), rng.uniform(0, 6.3)
    lines = [(rng.uniform(1.0, h - 2.2), rng.uniform(0.2, 0.6), rng.uniform(0.08, 0.25), rng.uniform(0, 6.3)) for _ in range(2)]
    knot = rng.uniform(4, w - 5) if rng.random() < knots * 8 else None
    for x in range(w):
        k = 1.0 + 0.05 * math.sin(x * f1 + p1)
        for y in range(h):
            if y == h - 1:
                c = seam
            elif y == h - 2:
                c = _mix(dark, base, 0.35)
            else:
                kk = k
                for c0, amp, fr, ph in lines:
                    if abs(y + 0.5 - (c0 + amp * math.sin(x * fr + ph))) < 0.5:
                        kk -= 0.1
                if y == 0:
                    kk *= lit
                if knot is not None and math.hypot((x - knot) / 1.6, y - h / 2 + 0.5) < 1.1:
                    kk -= 0.28
                c = _scale(base, kk)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path):
    rng = random.Random(4471)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    _strake(img, REGIONS["strake"], rng, _rgb("9c6733"), _rgb("4e3219"), _rgb("2e1c0e"))
    _strake(img, REGIONS["strake_up"], rng, _rgb("8a6239"), _rgb("4a331b"), _rgb("2a1a0c"), lit=1.07)
    _strake(img, REGIONS["strake_low"], rng, _rgb("7e5530"), _rgb("3f2816"), _rgb("22150a"), lit=1.06)
    fine_wood(img, REGIONS["inner"], _rgb("a2733d"), _rgb("5e3f20"), 8, rng, joints=False, knots=0.2, grain=0.09, shade=0.06)
    fine_wood(img, REGIONS["gunwale"], _rgb("c4904e"), _rgb("8a5e30"), 8, rng, joints=False, knots=0.1, grain=0.07, shade=0.07)
    fine_wood(img, REGIONS["rib"], _rgb("c69a5c"), _rgb("8a6436"), 8, rng, joints=False, knots=0.0, grain=0.08, shade=0.05)
    fine_wood(img, REGIONS["floor"], _rgb("5a4028"), _rgb("2a1c10"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.06)
    fine_wood(img, REGIONS["thwart"], _rgb("a87542"), _rgb("5a3a1c"), 4, rng, joints=True, knots=0.2, grain=0.1, shade=0.06)
    fine_wood(img, REGIONS["keel"], _rgb("4e3419"), _rgb("261709"), 8, rng, joints=False, knots=0.1, grain=0.08, shade=0.05)
    fine_wood(img, REGIONS["oar"], _rgb("a0703a"), _rgb("7a5229"), 8, rng, joints=False, knots=0.05, grain=0.07, shade=0.06)
    fine_wood(img, REGIONS["blade"], _rgb("b07c42"), _rgb("7a5229"), 8, rng, joints=False, knots=0.0, grain=0.08, shade=0.06)
    # posts and tholepins are beams: their long faces have the texture's u along their length
    fine_wood(img, REGIONS["post"], _rgb("7a4f27"), _rgb("4a2f18"), 16, rng, joints=False, knots=0.2, grain=0.09, shade=0.06)
    fine_wood(img, REGIONS["seat"], _rgb("a87542"), _rgb("5a3a1c"), 8, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    end_grain(img, REGIONS["end_grain"], _rgb("94653a"), _rgb("5a3a1c"), rng)
    hammered_iron(img, REGIONS["iron"], _rgb("4a4a50"), rng)
    twisted_rope(img, REGIONS["rope"], _rgb("c09a5e"), _rgb("6a4c2a"), rng)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: the brown rowboat seen from the side, an oar across it."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    hull, dark, rail, light = _rgb("8f5f2f"), _rgb("4a2f18"), _rgb("c4904e"), _rgb("a8743a")
    # hull: a shallow crescent, the ends rising
    for x in range(1, 15):
        t = abs(x - 7.5) / 7.5
        top = 7 - int(round(2.2 * t * t))
        bottom = 11 - int(round(2.5 * t * t))
        for y in range(top, bottom + 1):
            c = rail if y == top else light if y == top + 1 else hull if y < bottom else dark
            if x in (1, 14) and y > top + 1:
                c = dark
            p[x, y] = c + (255,)
    # the posts at the ends
    for y in range(3, 6):
        p[1, y] = dark + (255,)
        p[14, y] = dark + (255,)
    # thwarts seen edge-on, the oar sloping down to the left
    for x in (5, 8, 11):
        p[x, 6] = _rgb("a87542") + (255,)
    oar = _rgb("a0703a")
    for i, (x, y) in enumerate(((10, 4), (9, 4), (8, 5), (7, 5), (6, 6), (5, 7), (4, 8), (3, 9))):
        p[x, y] = oar + (255,)
    p[2, 10] = oar + (255,)
    p[2, 11] = oar + (255,)
    p[3, 10] = oar + (255,)
    # water
    for x in range(0, 16):
        if x % 3 != 1:
            p[x, 13] = _rgb("3b6fb8") + (255,)
    icon.save(path)
