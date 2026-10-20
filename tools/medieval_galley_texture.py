"""Texture of the red medieval galley (medieval_galley).

  medieval_galley.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours taken from the reference picture: red hull with dark brown planking, blue trim
along the sheer, gold mouldings, red round shields with a white cross and a gold rim,
red and white vertical stripes on the sail, red dragon heads with gold eyes.
"""
import math
import random

from PIL import Image

from galley_texture import (GOLD_STOPS, _jitter, _mix, _ramp, _rgb, _scale, fine_wood, hammered_iron, paint_lamp_glass,
                            painted_planks, polished_metal, twisted_rope)

SIZE = 256

REGIONS = {
    "hull_dark":   (0, 0, 64, 32),
    "hull_red":    (64, 0, 64, 32),
    "blue_trim":   (128, 0, 64, 16),
    "wale":        (128, 16, 64, 16),
    "gold":        (192, 0, 32, 32),
    "ivory":       (224, 0, 16, 16),
    "eye":         (240, 0, 16, 16),
    "iron":        (224, 16, 16, 16),
    "glow":        (240, 16, 16, 16),
    "deck":        (0, 32, 64, 64),
    "dark_wood":   (64, 32, 32, 16),
    "end_grain":   (96, 32, 16, 16),
    "lantern":     (112, 32, 16, 16),
    "rope":        (64, 48, 16, 16),
    "cloth_roll":  (80, 48, 48, 16),
    "oar":         (128, 32, 64, 16),
    "mast":        (128, 48, 64, 16),
    "dragon":      (192, 32, 32, 32),
    "dragon_dark": (224, 32, 32, 32),
    "shield":      (64, 64, 32, 32),
    "flag":        (96, 64, 32, 16),
    "hull_light":  (128, 64, 64, 32),
    "red_paint":   (192, 64, 64, 16),
    "sail":        (0, 128, 128, 128),
    "dragon_neck": (128, 128, 128, 32),
    "shield_back": (0, 96, 32, 32),
}


def _scales(px, region, base, edge, light, rng, sw=8, sh=5):
    """Overlapping dragon scales: round scales in rows offset by half a scale, each row lying over
    the one below it (roof tiles); every scale is lit towards its root and has a dark rim round its free edge."""
    u, v, w, h = region
    R = sw * 0.62
    for y in range(h):
        for x in range(w):
            best = None
            for row in range(-1, h // sh + 2):
                off = sw / 2 if row % 2 else 0.0
                cy = row * sh
                for j in range(-1, w // sw + 2):
                    cx = j * sw + off + sw / 2
                    # wrap round so that the region tiles
                    for ddx in (-w, 0, w):
                        dx, dy = x + 0.5 - (cx + ddx), y + 0.5 - cy
                        if dy >= -0.5 and math.hypot(dx, dy) < R and (best is None or cy < best[0]):
                            best = (cy, dx, dy)
            if best is None:
                c = edge
            else:
                _, dx, dy = best
                d = math.hypot(dx, dy) / R
                if d > 0.82:
                    c = _mix(edge, base, 0.3)
                else:
                    c = _mix(light, base, min(1.0, 0.15 + dy / (sh * 0.8)))
                    c = _scale(c, 1.0 - 0.1 * abs(dx) / R)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _neck_scales(img, region, rng):
    """Long strip of scales for the dragon neck and tail, mapped continuously along them: u runs
    along the neck (each scale's free edge points down the neck, towards the hull), v round it:
    dark back with the crest (top), red sides, a paler, warmer belly (bottom)."""
    u, v, w, h = region
    tmp = Image.new("RGBA", (h, w))
    _scales(tmp.load(), (0, 0, h, w), _rgb("b02219"), _rgb("5a0f0a"), _rgb("de5238"), rng, sw=8, sh=6)
    src = tmp.load()
    px = img.load()
    for x in range(w):
        for y in range(h):
            c = src[y, w - 1 - x][:3]
            f = (y + 0.5) / h
            if f < 0.34:
                c = _scale(c, 0.72 + 0.28 * f / 0.34)
            elif f > 0.66:
                c = _mix(c, _rgb("e0874a"), 0.35 * (f - 0.66) / 0.34)
            px[u + x, v + y] = c + (255,)


def make_texture(path):
    rng = random.Random(1066)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    fine_wood(img, REGIONS["hull_dark"], _rgb("4b2d18"), _rgb("26160a"), 4, rng)
    painted_planks(img, REGIONS["hull_red"], _rgb("a8261d"), _rgb("4e0e0a"), 4, rng, joints=True)
    fine_wood(img, REGIONS["wale"], _rgb("3a2212"), _rgb("2a180c"), 8, rng, joints=False, grain=0.12)
    fine_wood(img, REGIONS["deck"], _rgb("b07a42"), _rgb("5e3c1c"), 4, rng, knots=0.2)
    fine_wood(img, REGIONS["dark_wood"], _rgb("5a3a1c"), _rgb("2e1d0c"), 4, rng)
    fine_wood(img, REGIONS["oar"], _rgb("d6a35c"), _rgb("b0844a"), 8, rng, joints=False, knots=0.1, shade=0.06)
    fine_wood(img, REGIONS["mast"], _rgb("7a4f27"), _rgb("5a3818"), 8, rng, joints=False, knots=0.3, shade=0.07)
    fine_wood(img, REGIONS["hull_light"], _rgb("a0703a"), _rgb("5e3c1c"), 4, rng)
    painted_planks(img, REGIONS["red_paint"], _rgb("b3261d"), _rgb("861c15"), 8, rng)
    hammered_iron(img, REGIONS["iron"], _rgb("3d3d42"), rng)
    px = img.load()

    def reg(name):
        return REGIONS[name]

    # end grain: growth rings
    u, v, w, h = reg("end_grain")
    for y in range(h):
        for x in range(w):
            r = math.hypot(x + 0.5 - w * 0.47, y + 0.5 - h * 0.53)
            px[u + x, v + y] = _jitter(_scale(_rgb("8c5e30"), 1.0 + 0.09 * math.sin(r * 2.1)), rng, 3) + (255,)
    # blue trim: painted, a gilded bead along both edges, a running gold dot-and-lozenge pattern
    u, v, w, h = reg("blue_trim")
    for y in range(h):
        for x in range(w):
            if y in (0, h - 1):
                c = _ramp(GOLD_STOPS, 0.45)
            elif y in (1, h - 2):
                c = _ramp(GOLD_STOPS, 0.85)
            else:
                c = _scale(_rgb("2c5b9c"), 1.0 + 0.03 * math.sin(x * 0.3 + y) + (0.06 if y == 2 else 0) - (0.08 if y == h - 3 else 0))
                xm = (x % 8) - 3.5
                if abs(xm) + abs(y - h / 2 + 0.5) * 1.4 < 2.0:
                    c = _ramp(GOLD_STOPS, 0.75 if y < h / 2 else 0.5)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # polished gold
    polished_metal(img, reg("gold"), GOLD_STOPS, rng)
    # ivory: fangs, lit along one side
    u, v, w, h = reg("ivory")
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("efe6cf"), 1.04 - 0.1 * (x % 4) / 3 - 0.05 * (y / h))
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # dragon eye: gold iris shading to amber, slit pupil, a white glint
    u, v, w, h = reg("eye")
    for y in range(h):
        for x in range(w):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if abs(x - 7.5) < 1.2 and d < 6:
                c = _rgb("1a0f08")
            elif d < 6.5:
                c = _mix(_rgb("fff07a"), _rgb("e08a1a"), d / 6.5)
            elif d < 7.3:
                c = _rgb("5e110c")
            else:
                c = _rgb("b3261d")
            if 4 <= x <= 5 and 4 <= y <= 5:
                c = _rgb("fffbe6")
            px[u + x, v + y] = c + (255,)
    # dragon skin: overlapping rounded scales, darker for the crest and the jaw
    _scales(px, reg("dragon"), _rgb("b8261d"), _rgb("74140e"), _rgb("d84e38"), rng)
    _scales(px, reg("dragon_dark"), _rgb("861812"), _rgb("3e0806"), _rgb("b8302a"), rng)
    _neck_scales(img, reg("dragon_neck"), rng)
    twisted_rope(img, reg("rope"), _rgb("5a4630"), _rgb("22180e"), rng)
    # furled canvas: stripes, folds of the rolled cloth, lashings
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            stripe = (x // 6) % 2 == 0
            c = _rgb("b3221c") if stripe else _rgb("eee6d3")
            c = _scale(c, 1.0 - 0.12 * abs(math.sin((x * 0.5 + y) * 0.6)))
            if x % 16 in (7, 8):
                c = _rgb("5a4630") if (x + y) % 3 else _rgb("3a2a1a")
            px[u + x, v + y] = c + (255,)
    # lantern frame and glow
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # round shield: planks under the paint, studded gold rim, red field, white cross, gold boss
    u, v, w, h = reg("shield")
    for y in range(h):
        for x in range(w):
            dx, dy = x - w / 2 + 0.5, y - h / 2 + 0.5
            r = (dx * dx + dy * dy) ** 0.5
            if r > w / 2 - 0.3:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if r > w / 2 - 3:
                ang = math.degrees(math.atan2(dy, dx)) % 30
                c = _ramp(GOLD_STOPS, 0.55 + 0.35 * (dy < 0) - 0.25 * (r > w / 2 - 1.2))
                if ang < 5 and w / 2 - 2.6 < r < w / 2 - 1.2:
                    c = _ramp(GOLD_STOPS, 0.98)  # rivet
            elif r < 3:
                c = _ramp(GOLD_STOPS, 0.9 if dx + dy < 0 else 0.4)
            elif r < 3.7:
                c = _rgb("4a2e12")
            else:
                if abs(dx) < 2.6 or abs(dy) < 2.6:
                    c = _rgb("f2ede2")
                else:
                    c = _rgb("b3221c")
                c = _scale(c, 1.0 - 0.08 * ((x % 6) == 0) + 0.05 * (-dy / (w / 2)))  # planks under the paint, light from above
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # back of the shield: round, bare planks with a dark rim and the hand grip across (the
    # corners are transparent, so the shields hung on the gunwale look round from the deck too)
    u, v, w, h = reg("shield_back")
    for y in range(h):
        for x in range(w):
            dx, dy = x - w / 2 + 0.5, y - h / 2 + 0.5
            r = (dx * dx + dy * dy) ** 0.5
            if r > w / 2 - 0.3:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("6a4424"), 1.0 - 0.1 * ((x % 6) == 0) + 0.04 * math.sin(y * 0.7 + x // 6))
            if r > w / 2 - 2.2:
                c = _rgb("3a2410")
            elif abs(dy) < 1.6 and abs(dx) < 9:
                c = _rgb("4a2e14") if abs(dy) > 0.8 else _rgb("5e3c1c")
            elif r < 3.2:
                c = _ramp(GOLD_STOPS, 0.35)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # flag: red with a white cross, a soft fold
    u, v, w, h = reg("flag")
    for y in range(h):
        for x in range(w):
            cross = abs(x - w * 0.38) < 2 or abs(y - h / 2 + 0.5) < 2
            c = _scale(_rgb("f2ede2") if cross else _rgb("c4231d"), 1.0 + 0.06 * math.sin(x * 0.4))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # sail: nine vertical cloths, red and white alternately (red at both edges); each cloth puffs
    # out between its double-stitched seams; two reef bands with their reef points, corner patches,
    # a darker reinforced head along the yard and a bolt rope round the edges
    u, v, w, h = reg("sail")
    n = 9
    for y in range(h):
        for x in range(w):
            f = x * n / w
            k_ = int(f)
            red = k_ % 2 == 0
            c = _rgb("c32a22") if red else _rgb("f1ead9")
            within = f - k_
            shade = 1.0 - 0.06 * abs(y / h - 0.5) + 0.05 * math.sin(math.pi * within) - 0.03
            c = _scale(c, shade)
            sd_ = min(within, 1 - within) * w / n
            if sd_ < 0.5 and 0 < x < w - 1:
                c = _scale(c, 0.78)  # seam between two cloths
            elif 0.9 < sd_ < 1.6 and y % 3 == 0 and 0 < x < w - 1:
                c = _scale(c, 0.9)   # its stitching
            for band in (0.3, 0.48):
                by = int(h * band)
                if by <= y <= by + 2:
                    c = _scale(c, 0.9 if y == by + 2 else 0.94)
                if x % 7 == 3 and by + 3 <= y <= by + 5:
                    c = _rgb("5a3a1c") if y < by + 5 else _rgb("7a5a34")  # reef points hanging from the band
            corner = min(math.hypot(x - cx_, y - cy_) for cx_, cy_ in ((0, 0), (w, 0), (0, h), (w, h)))
            if corner < 12:
                c = _scale(c, 0.93)
                if 11 < corner < 12:
                    c = _scale(c, 0.85)
            if y < 3:
                c = _rgb("8a1b15") if red else _rgb("c9bfa6")
            if x < 1 or x >= w - 1 or y >= h - 1:
                c = _rgb("6b4a2a")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: red galley with its striped sail."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    for x in range(1, 15):
        lift = 2 if x < 3 or x > 12 else (1 if x < 4 or x > 11 else 0)
        for y in range(12 - lift, 14):
            p[x, y] = _rgb("a8261d" if y < 13 else "4b2d18") + (255,)
        if 3 <= x <= 12 and x % 2 == 1:
            p[x, 12 - lift] = _rgb("e8e2d0") + (255,)
    for y in range(9, 12):
        p[0, y] = _rgb("c0281f") + (255,)
        p[15, y] = _rgb("c0281f") + (255,)
    for y in range(2, 12):
        p[8, y] = _rgb("5a3a1c") + (255,)
    for x in range(4, 13):
        for y in range(3, 9):
            p[x, y] = (_rgb("c32a22") if (x // 2) % 2 == 0 else _rgb("f1ead9")) + (255,)
    p[8, 1] = _rgb("c4231d") + (255,)
    p[9, 1] = _rgb("c4231d") + (255,)
    icon.save(path)
