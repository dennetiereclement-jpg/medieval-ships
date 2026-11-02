"""Texture atlas of the jeweller's workbench (workshops_c.png, 256x256), 1.22.0.

Dark oak (warm brown, lighter moulded edges, drawer fronts with a keyhole), iron (hammered, riveted corner plates, the
cast-iron grey of the gem-cutting machine, polished steel for the tools), gold (polished, ingots with a stamped top,
nuggets), brass, the purple runner (its top with gold borders, its hanging part with the gold dagged hem and the gold
cut-gem symbol), faceted gems (red, blue, green, purple), the white stone of the tray, the polishing disc, the spoked
hand wheel, the loupe's lens, wood and leather handles.

Every region is (u, v, w, h) in pixels, packed automatically (deterministic order) into REGIONS; used by
tools/workshops/generate_workshop_jeweler.py (through wslib_b, pointed at this module). Regions with transparent pixels
(the runner's dagged hem, the disc, the wheel, the lens) are cut out in game.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, end_grain, polished_metal, GOLD_STOPS  # noqa: E402
import tent_texture as tt  # noqa: E402

SIZE = 256
NAME = "workshops_c.png"

_LAYOUT = [
    ("runner_hang", 48, 64), ("cloth_purple", 32, 64), ("disc", 32, 32), ("wheel", 32, 32), ("runner_back", 48, 16),
    ("plank_top", 64, 16), ("wood_dark", 64, 16), ("wood_edge", 64, 16), ("wood_mid", 64, 16),
    ("drawer", 48, 16), ("end_grain", 16, 16), ("iron", 16, 16), ("iron_dark", 16, 16), ("iron_rivet", 16, 16),
    ("cast_iron", 16, 16), ("steel", 16, 16), ("gold", 16, 16), ("brass", 16, 16), ("gold_ingot", 16, 8), ("gold_side", 16, 8),
    ("marble", 16, 16), ("marble_dark", 16, 16), ("lens", 16, 16), ("handle", 16, 16), ("leather", 16, 16), ("disc_rim", 16, 16),
    ("gem_red", 8, 8), ("gem_blue", 8, 8), ("gem_green", 8, 8), ("gem_purple", 8, 8), ("nugget", 8, 8),
]


def _pack(layout, size):
    regions, x, y, row_h = {}, 0, 0, 0
    for name, w, h in layout:
        if x + w > size:
            x, y, row_h = 0, y + row_h, 0
        regions[name] = (x, y, w, h)
        x += w
        row_h = max(row_h, h)
    assert y + row_h <= size, "atlas full"
    return regions


REGIONS = _pack(_LAYOUT, SIZE)

PURPLE = _rgb("5c2486")
PURPLE_DARK = _rgb("3a1458")
GOLD = _rgb("e8b83c")
GOLD_LIGHT = _rgb("fbe08a")
GOLD_DARK = _rgb("8a6418")
CLEAR = (0, 0, 0, 0)
# the row of runner_hang where the cloth folds over the bench's front edge (the generator hangs it to match)
FOLD = 17
GEMS = {"red": _rgb("e0283c"), "blue": _rgb("2e6ef0"), "green": _rgb("22c060"), "purple": _rgb("a040e8")}


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(c[:3]) + (a,)


def _cloth(rng, x, y, base=PURPLE):
    """A woven purple: small 2 px cells a little lighter or darker."""
    k = 1.0 + (0.06 if (x // 2 + y // 2) % 2 else -0.05) + rng.uniform(-0.03, 0.03)
    return _scale(base, k)


def _gem_outline(draw, cx, cy, w, h, color, width):
    """The cut-gem symbol: a crown (trapezoid) over a pavilion (triangle), with its facet lines."""
    top = cy - h * 0.42
    gird = cy - h * 0.12
    tip = cy + h * 0.5
    pts = [(cx - w * 0.3, top), (cx + w * 0.3, top), (cx + w * 0.5, gird), (cx, tip), (cx - w * 0.5, gird)]
    draw.line(pts + [pts[0]], fill=color, width=width, joint="curve")
    draw.line([(cx - w * 0.5, gird), (cx + w * 0.5, gird)], fill=color, width=width)
    for a, b in (((cx - w * 0.1, top), (cx - w * 0.2, gird)), ((cx + w * 0.1, top), (cx + w * 0.2, gird)),
                 ((cx - w * 0.2, gird), (cx, tip)), ((cx + w * 0.2, gird), (cx, tip))):
        draw.line([a, b], fill=color, width=max(1, width - 1))


def _runner_hang(img, region, rng):
    """The hanging part of the runner: purple, gold bands down both sides, the gold cut-gem symbol in the middle of the
    part below the bench's edge, a gold zig-zag (dagged) hem, transparent below the points."""
    u, v, w, h = region
    px = img.load()
    points = 5
    hem = 9
    for y in range(h):
        for x in range(w):
            ph = ((x + 0.5) * points / w) % 1.0
            bottom = h - hem + hem * (1 - abs(ph - 0.5) * 2)       # the point's tip reaches the bottom row
            if y >= bottom:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            c = _cloth(rng, x, y)
            if y < FOLD:
                c = _scale(c, 1.06)                                 # the part over the bench's edge
            if y == FOLD:
                c = _scale(PURPLE_DARK, 0.9)                        # the fold at the edge
            if x in (2, 3, w - 4, w - 3) and FOLD + 2 <= y < bottom - 4:
                c = GOLD
            if bottom - 4 <= y < bottom - 1.5:
                c = GOLD if (x + y) % 4 else GOLD_LIGHT              # the gold hem following the points
            elif y >= bottom - 1.5:
                c = GOLD_DARK
            if x in (0, w - 1):
                c = _scale(c, 0.8)
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    # the cut-gem symbol, drawn 4x then reduced (crisp gold lines)
    S = 4
    layer = Image.new("RGBA", (w * S, h * S), CLEAR)
    d = ImageDraw.Draw(layer)
    _gem_outline(d, w * S / 2, 36.5 * S, 26 * S, 22 * S, GOLD + (255,), 2 * S)
    small = layer.resize((w, h), Image.LANCZOS)
    sp = small.load()
    for y in range(h):
        for x in range(w):
            a = sp[x, y][3]
            if a > 90 and px[u + x, v + y][3] > 0:
                c = _mix(GOLD, GOLD_LIGHT, 0.3 if (x + y) % 3 == 0 else 0.0)
                _put(px, u, v, x, y, c)


def _runner_back(img, region, rng):
    """The short drop at the back: purple, a gold line, the dagged gold hem."""
    u, v, w, h = region
    px = img.load()
    points = 5
    hem = 6
    for y in range(h):
        for x in range(w):
            ph = ((x + 0.5) * points / w) % 1.0
            bottom = h - hem + hem * (1 - abs(ph - 0.5) * 2)
            if y >= bottom:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            c = _cloth(rng, x, y)
            if bottom - 3 <= y:
                c = GOLD if y < bottom - 1 else GOLD_DARK
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _cloth_top(img, region, rng):
    """The runner on the top (u across the bench, v front to back): purple, a gold band near each long edge."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _cloth(rng, x, y)
            if x in (2, 3, w - 4, w - 3):
                c = GOLD
            elif x in (0, w - 1):
                c = _scale(PURPLE_DARK, 1.0)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _drawer(img, region, rng):
    """A drawer front: a lighter moulded frame round a dark oak panel, a small iron keyhole plate at the top middle."""
    u, v, w, h = region
    sub = Image.new("RGBA", (w, h))
    fine_wood(sub, (0, 0, w, h), _rgb("7a5232"), _rgb("3e2614"), h, rng, joints=False, knots=0.1, grain=0.1, shade=0.04)
    sp = sub.load()
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = sp[x, y][:3]
            if x in (0, w - 1) or y in (0, h - 1):
                c = _scale(_rgb("2e1c0e"), 1.0)
            elif x in (1, w - 2) or y in (1, h - 2):
                c = _scale(_rgb("a87c4e"), 1.0)                       # the lighter moulding
            elif x in (2, w - 3) or y in (2, h - 3):
                c = _scale(c, 0.72)
            # the keyhole plate
            cx = w / 2 - 0.5
            if abs(x - cx) <= 2.5 and 3 <= y <= 7:
                c = _rgb("5a5a60") if abs(x - cx) < 2 and 4 <= y <= 6 else _rgb("38383c")
                if abs(x - cx) < 1 and y in (5, 6):
                    c = _rgb("0e0e10")
            _put(px, u, v, x, y, c)


def _rivet_plate(img, region, rng):
    """A dark iron plate with a rim and four round rivet heads (the corner fittings)."""
    u, v, w, h = region
    hammered_iron(img, region, _rgb("34343a"), rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                _put(px, u, v, x, y, _rgb("1c1c20"))
    for cx, cy in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4), (w // 2, h // 2)):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dy) <= 1:
                    c = _rgb("9a9aa4") if (dx, dy) in ((-1, 0), (0, -1)) else _rgb("6a6a72") if (dx, dy) == (0, 0) else _rgb("26262a")
                    _put(px, u, v, cx + dx, cy + dy, c)


def _ingot(img, region, rng, side=False):
    """A gold ingot's top (a bright bevelled face with a stamped mark) or its sides (darker gold)."""
    u, v, w, h = region
    polished_metal(img, region, GOLD_STOPS, rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = px[u + x, v + y][:3]
            if side:
                c = _scale(c, 0.82)
                if y == 0:
                    c = GOLD_LIGHT
            else:
                if x in (0, w - 1) or y in (0, h - 1):
                    c = _scale(GOLD, 0.75)
                elif x in (1, w - 2) or y in (1, h - 2):
                    c = _mix(c, GOLD_LIGHT, 0.5)
                elif 6 <= x <= 9 and 3 <= y <= 4:
                    c = _scale(GOLD, 0.7)                           # the stamp
            _put(px, u, v, x, y, c)


def _marble(img, region, rng, base):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.04 * math.sin(x * 0.7 + y * 0.35)
            c = _scale(base, k)
            if abs(math.sin(x * 0.45 + y * 0.9 + 1.3 * math.sin(y * 0.3))) < 0.08:
                c = _scale(base, 0.86)                             # a grey vein
            if x in (0, w - 1) or y in (0, h - 1):
                c = _scale(base, 0.82)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _gem(img, region, rng, color):
    """A faceted gem: a light table in the middle, facets of three tones round it, a white glint."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx, dy = x - (w - 1) / 2, y - (h - 1) / 2
            r = max(abs(dx), abs(dy))
            if r < 1.6:
                c = _mix(color, (255, 255, 255), 0.35)
            elif (dx < 0) == (dy < 0):
                c = _scale(color, 1.12 if dx < 0 else 0.62)
            else:
                c = _scale(color, 0.88)
            if abs(abs(dx) - abs(dy)) < 0.6 and r >= 1.6:
                c = _scale(color, 0.5)                              # the facet edges
            _put(px, u, v, x, y, c)
    _put(px, u, v, 1, 1, _mix(color, (255, 255, 255), 0.8))


def _disc(img, region, rng):
    """The polishing disc's face: a round grey lap with fine concentric rings and a dark hub; transparent corners."""
    u, v, w, h = region
    px = img.load()
    R = w / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - R + 0.5, y - R + 0.5)
            if d > R - 0.2:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            if d > R - 2.2:
                c = _rgb("3c3c42")                                  # the iron rim
            elif d < 3:
                c = _rgb("2a2a2e") if d > 1.5 else _rgb("8a8a92")    # the hub, the axle's end
            else:
                c = _scale(_rgb("d8dce2"), 0.9 + 0.1 * math.sin(d * 2.1))
                ang = math.atan2(y - R, x - R)
                c = _scale(c, 1.0 + 0.12 * math.cos(ang - 2.4))     # a soft polished reflection
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _wheel(img, region, rng, spokes=5):
    """The hand wheel: a dark iron ring, spokes and a hub; transparent between the spokes."""
    u, v, w, h = region
    S = 4
    layer = Image.new("RGBA", (w * S, h * S), CLEAR)
    d = ImageDraw.Draw(layer)
    c = w * S / 2
    R = w * S / 2 - S * 0.5
    d.ellipse([c - R, c - R, c + R, c + R], outline=(52, 52, 58, 255), width=int(3.2 * S))
    for k in range(spokes):
        a = 2 * math.pi * k / spokes - math.pi / 2
        d.line([(c, c), (c + math.cos(a) * R * 0.95, c + math.sin(a) * R * 0.95)], fill=(62, 62, 68, 255), width=int(2.2 * S))
    d.ellipse([c - 3.5 * S, c - 3.5 * S, c + 3.5 * S, c + 3.5 * S], fill=(40, 40, 44, 255))
    small = layer.resize((w, h), Image.LANCZOS).load()
    px = img.load()
    for y in range(h):
        for x in range(w):
            if small[x, y][3] > 110:
                col = _scale((62, 62, 68), 1.0 + 0.25 * (1 if (x + y) < w else -0.3))
                _put(px, u, v, x, y, _jitter(col, rng, 4))
            else:
                _put(px, u, v, x, y, CLEAR, 0)


def _lens(img, region, rng):
    """The loupe's lens seen face on: a brass ring round pale bluish glass with a glint; transparent corners."""
    u, v, w, h = region
    px = img.load()
    R = w / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - R + 0.5, y - R + 0.5)
            if d > R - 0.1:
                _put(px, u, v, x, y, CLEAR, 0)
            elif d > R - 2.2:
                _put(px, u, v, x, y, _rgb("c89a40") if (x + y) % 3 else _rgb("f0d080"))
            else:
                c = _mix(_rgb("bfe0ea"), _rgb("7aa8b8"), d / R)
                if 3 <= x <= 5 and 4 <= y <= 6:
                    c = (250, 255, 255)
                _put(px, u, v, x, y, c)


def make_texture(path):
    rng = random.Random(2122)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    R = REGIONS
    # dark oak, warm brown; the edges lighter
    fine_wood(img, R["plank_top"], _rgb("7c5434"), _rgb("3c2412"), 5, rng, joints=True, knots=0.15, grain=0.1, shade=0.07)
    fine_wood(img, R["wood_dark"], _rgb("5e3e22"), _rgb("2c1a0a"), 8, rng, joints=False, knots=0.15, grain=0.1, shade=0.06)
    fine_wood(img, R["wood_edge"], _rgb("a07448"), _rgb("5a3a1c"), 8, rng, joints=False, knots=0.05, grain=0.1, shade=0.05)
    fine_wood(img, R["wood_mid"], _rgb("6e4a2a"), _rgb("361f0e"), 8, rng, joints=False, knots=0.1, grain=0.1, shade=0.05)
    end_grain(img, R["end_grain"], _rgb("9a6e44"), _rgb("4a2e14"), rng)
    _drawer(img, R["drawer"], rng)
    fine_wood(img, R["handle"], _rgb("b08050"), _rgb("6a4424"), 16, rng, joints=False, knots=0.0, grain=0.1, shade=0.04)
    tt._fill(img, R["leather"], _rgb("6a2c1c"), rng, noise=7)
    # metals
    hammered_iron(img, R["iron"], _rgb("50505a"), rng)
    hammered_iron(img, R["iron_dark"], _rgb("2c2c32"), rng)
    _rivet_plate(img, R["iron_rivet"], rng)
    hammered_iron(img, R["cast_iron"], _rgb("6a6e76"), rng, dent=0.05)
    polished_metal(img, R["steel"], [(0.0, _rgb("4a4e56")), (0.45, _rgb("8a9098")), (0.85, _rgb("c8ced6")), (1.0, _rgb("eef2f6"))], rng)
    polished_metal(img, R["gold"], GOLD_STOPS, rng)
    polished_metal(img, R["brass"], [(0.0, _rgb("6a5020")), (0.4, _rgb("a88838")), (0.8, _rgb("d8b860")), (1.0, _rgb("f0dc98"))], rng)
    _ingot(img, R["gold_ingot"], rng)
    _ingot(img, R["gold_side"], rng, side=True)
    polished_metal(img, R["nugget"], GOLD_STOPS, rng, fx=0.9, fy=0.8)
    tt._fill(img, R["disc_rim"], _rgb("3a3a40"), rng, noise=4)
    # cloth
    _cloth_top(img, R["cloth_purple"], rng)
    _runner_hang(img, R["runner_hang"], rng)
    _runner_back(img, R["runner_back"], rng)
    # stone, gems, glass
    _marble(img, R["marble"], rng, _rgb("e8e4dc"))
    _marble(img, R["marble_dark"], rng, _rgb("c4beb2"))
    for name, col in GEMS.items():
        _gem(img, R["gem_" + name], rng, col)
    _disc(img, R["disc"], rng)
    _wheel(img, R["wheel"], rng)
    _lens(img, R["lens"], rng)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/agent_jeweler/workshops_c.png"
    make_texture(out)
    print("wrote", out, len(REGIONS), "regions")
