"""Texture of the Nautilus (nautilus).

  nautilus.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours of the reference sheet: aged copper and bronze plates, blackened steel, brown metal,
rivets everywhere, a few gilded details, warm yellow lights; inside, dark wood floors, riveted
steel walls with a copper band, dark ceilings.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _fill, _jitter, _planks, _rgb, paint_lamp_glass

SIZE = 256

REGIONS = {
    "plate":       (0, 0, 64, 32),     # copper plates of the upper hull
    "plate_dark":  (64, 0, 64, 32),    # darker bronze plates low on the hull
    "steel":       (128, 0, 32, 32),   # blackened steel (ram, fins, tower frame)
    "brass":       (160, 0, 32, 32),
    "iron":        (192, 0, 16, 16),
    "glass":       (208, 0, 16, 16),
    "glow":        (224, 0, 16, 16),
    "lantern":     (240, 0, 16, 16),
    "floor":       (0, 32, 32, 32),    # dark wood parquet
    "wall":        (32, 32, 32, 32),   # riveted steel, copper band
    "ceiling":     (64, 32, 32, 32),
    "deck":        (96, 32, 32, 32),   # iron grating of the top walkway and the shafts
    "prop":        (128, 32, 32, 16),
    "rung":        (160, 32, 16, 16),
    "hatch":       (176, 32, 32, 32),
}


def _shade(c, k):
    return tuple(max(0, min(255, int(q * k))) for q in c)


def _riveted(px, region, base, seam, rivet, rng, pw=16, ph=8, wear=0.0):
    """Overlapping metal plates with rows of rivets, light on the upper edge, some patina."""
    u, v, w, h = region
    tones = {}
    for y in range(h):
        for x in range(w):
            row = y // ph
            off = pw // 2 if row % 2 else 0
            col = (x + off) // pw
            if (row, col) not in tones:
                tones[(row, col)] = _jitter(base, rng, 9)
            fx, fy = (x + off) % pw, y % ph
            c = tones[(row, col)]
            if fx == 0 or fy == 0:
                c = seam
            elif (fy == 2 or fy == ph - 2) and fx % 4 == 2:
                c = rivet
            elif fy == 1:
                c = _shade(c, 1.12)
            else:
                c = _shade(c, 1.0 - 0.07 * fy / ph)
            if wear and rng.random() < wear:
                c = _jitter(_rgb("4f6b52"), rng, 8)  # verdigris
            px[u + x, v + y] = c + (255,)


def make_texture(path):
    rng = random.Random(1870)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    _riveted(px, R["plate"], _rgb("8a5a34"), _rgb("4a2c18"), _rgb("c08a52"), rng, wear=0.02)
    _riveted(px, R["plate_dark"], _rgb("5a3b26"), _rgb("2e1d12"), _rgb("8f6a44"), rng, wear=0.03)
    _riveted(px, R["steel"], _rgb("3a3634"), _rgb("1d1b1a"), _rgb("6d6660"), rng, pw=8, ph=8)
    _fill(img, R["iron"], _rgb("2f2d2c"), rng, 6)
    for name, cols in (("brass", ("f6dc93", "dcb055", "bf8f34", "906523", "684716")),):
        u, v, w, h = R[name]
        for y in range(h):
            for x in range(w):
                t = 0.55 * math.sin(x * 0.42 + math.sin(y * 0.3) * 1.5) + 0.45 * math.cos(y * 0.36 + x * 0.12)
                i = 0 if t > 0.65 else 1 if t > 0.2 else 2 if t > -0.35 else 3 if t > -0.75 else 4
                px[u + x, v + y] = _jitter(_rgb(cols[i]), rng, 3) + (255,)
    # glass: deep sea blue-green with a highlight
    u, v, w, h = R["glass"]
    for y in range(h):
        for x in range(w):
            c = _rgb("1d4a5a") if (x + y) % 9 else _rgb("4f8a96")
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("b8913c")
            px[u + x, v + y] = c + (255,)
    u, v, w, h = R["glow"]
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    # inside
    _planks(img, R["floor"], _rgb("5a3820"), _rgb("2a180c"), 4, rng)
    _riveted(px, R["wall"], _rgb("6b6158"), _rgb("3b342e"), _rgb("a39684"), rng, pw=16, ph=16)
    u, v, w, h = R["wall"]
    for y in range(h):
        for x in range(w):
            if 20 <= y <= 23:
                px[u + x, v + y] = _jitter(_rgb("b8753e") if y in (21, 22) else _rgb("7a4a26"), rng, 5) + (255,)
            elif y >= 24:
                px[u + x, v + y] = _jitter(_rgb("4a2e1a") if x % 8 else _rgb("2e1c10"), rng, 4) + (255,)  # wood wainscot
    _riveted(px, R["ceiling"], _rgb("3e3834"), _rgb("221e1b"), _rgb("6a625a"), rng, pw=16, ph=16)
    u, v, w, h = R["deck"]
    for y in range(h):
        for x in range(w):
            c = _rgb("2a2826") if (x % 4 == 0 or y % 4 == 0) else _rgb("4a4542")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    _planks(img, R["prop"], _rgb("6e4a2c"), _rgb("3a2414"), 8, rng, joints=False)
    _fill(img, R["rung"], _rgb("6d6660"), rng, 6)
    u, v, w, h = R["hatch"]
    _riveted(px, (u, v, w, h), _rgb("4a4542"), _rgb("1f1d1c"), _rgb("b8913c"), rng, pw=32, ph=32)
    d = ImageDraw.Draw(img)
    d.ellipse((u + 6, v + 6, u + w - 7, v + h - 7), outline=_rgb("b8913c") + (255,), width=2)
    d.line((u + w // 2, v + 8, u + w // 2, v + h - 9), fill=_rgb("b8913c") + (255,), width=2)
    d.line((u + 8, v + h // 2, u + w - 9, v + h // 2), fill=_rgb("b8913c") + (255,), width=2)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: a copper cigar-shaped hull with a ram, a wheelhouse and a tail fin."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 6, 14, 11), fill=_rgb("8a5a34") + (255,), outline=_rgb("3a2414") + (255,))
    d.line((14, 8, 15, 8), fill=_rgb("3a3634") + (255,))
    d.rectangle((9, 4, 11, 6), fill=_rgb("6a4527") + (255,))
    d.point((10, 5), fill=_rgb("ffc94a") + (255,))
    d.polygon([(2, 8), (0, 5), (0, 11)], fill=_rgb("5a3b26") + (255,))
    d.point((7, 8), fill=_rgb("ffc94a") + (255,))
    d.line((4, 10, 12, 10), fill=_rgb("5a3b26") + (255,))
    img.save(path)
