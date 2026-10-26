"""Procedural pixel-art texture of the Rustic Skyskiff (rustic_skiff): one 512x512 atlas.

Colours of the reference sheet: an old brown hull of irregular planks, patched with lighter and darker
lengths, iron plates and nails, moss on the cap rails and on the reinforcing boards; light weathered planks
on the bow's lean-to; a big worn beige canvas roof, stained and patched, with torn strips hanging from its
eaves; tan canvas wings stitched from panels, holed and patched, on dark wooden ribs; tattered pennants
(beige, red, black); bronze-brown tubes bound with iron at the stern; warm lanterns; inside, rough plank
walls and floors, beams, a red runner and a red rug with a gold border.

Every region is (u, v, w, h); REGIONS is shared with tools/generate_skiff.py.
"""
import math
import random

from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass
from corsair_texture import _planks, _blocks, _fill, _window, _rope, _carpet, _rug, _replaced, _replaced_boards, _iron_patch, \
    _weave, _books, _chart, _mix, _scale

SIZE = 512

REGIONS = {
    # hull and wood
    "hull":        (0, 0, 64, 32),      # brown planks along u, patched
    "hull_low":    (64, 0, 64, 32),     # the bottom: darker, weathered, a little green
    "hull_patch":  (128, 0, 64, 32),    # lengths of other woods nailed over the planks
    "moss":        (192, 0, 64, 16),    # mossy cap rails and reinforcing boards
    "moss_board":  (192, 16, 64, 16),   # a reinforcing board, moss on its top half
    "wood":        (256, 0, 32, 16),    # plain mid brown
    "dark_wood":   (288, 0, 32, 16),
    "light_wood":  (320, 0, 32, 16),    # pale weathered planks (the bow's lean-to, the crates)
    "pole":        (352, 0, 32, 16),    # rough pole (grain along u)
    "rib":         (384, 0, 32, 16),    # dark wing ribs
    "deck":        (0, 32, 32, 32),     # deck planks, 2 blocks
    "cabin_wall":  (32, 32, 32, 32),    # vertical planks of the cabin walls
    "lean":        (64, 32, 32, 32),    # the lean-to's planks (along u)
    "end_grain":   (416, 0, 16, 16),
    "rope":        (432, 0, 16, 16),
    "rope_dark":   (448, 0, 16, 16),
    "iron":        (464, 0, 16, 16),
    "chain":       (480, 0, 16, 16),
    "glow":        (496, 0, 16, 16),
    "lantern":     (256, 16, 16, 16),
    "bronze":      (272, 16, 16, 16),
    "tube":        (288, 16, 32, 16),   # the stern tubes: bronze-brown, riveted seams along u
    "tube_mouth":  (320, 16, 16, 16),   # inside a tube: dark, a red glow at the back
    "window":      (336, 16, 16, 16),   # lit window with its cross bars
    "grate":       (352, 16, 16, 16),   # iron grating (holes transparent)
    "door_leaf":   (96, 32, 16, 32),    # one leaf of the 2 block door: planks, iron straps, a ring
    "hatch":       (112, 32, 16, 16),
    "rung":        (368, 16, 16, 16),
    "red_paint":   (384, 16, 16, 16),
    "linen":       (400, 16, 16, 16),
    "bedding":     (416, 16, 16, 16),
    "sack":        (432, 16, 16, 16),
    "glass":       (448, 16, 16, 16),
    "carving":     (464, 16, 32, 16),
    "iron_light":  (128, 32, 16, 16),
    "tube_rim":    (128, 48, 16, 16),   # the tubes' bells: worn bronze-brown   # grey iron: ring bolts, bollards, fittings
    "iron_dark":   (144, 32, 16, 16),   # blackened iron: the fans in the tubes
    "bone":        (160, 32, 32, 16),   # pale bone segments of the wings' ribs
    "tube_in":     (192, 32, 16, 16),   # inside of the tubes' bells: dark
    "emblem":      (208, 32, 32, 32),   # the carved square panel of the cabin's sides
    "window_in":   (240, 32, 16, 16),   # a window seen from inside: the sky through small panes
    "curtain":     (256, 32, 16, 32),   # a ragged curtain
    "quilt":       (272, 32, 32, 32),   # the bed's red quilt, a darker border, the folded sheet at its head
    # cloth
    "canvas":      (0, 64, 64, 64),     # the roof canvas: worn beige, stains, stitched patches
    "canvas_under": (64, 64, 32, 32),   # its underside, darker
    "fringe":      (96, 64, 32, 32),    # torn strips hanging from the eaves (ragged, transparent tears)
    "wing":        (128, 64, 64, 64),   # the wings' canvas: tan panels, holes, patches
    "wing_t":      (384, 64, 64, 64),   # the same, transposed (the quads along the wings' free edges)
    "pennant_beige": (320, 64, 16, 32),   # big tattered pennants: notched, ragged tails
    "pennant_red": (336, 64, 16, 32),
    "pennant_black": (352, 64, 16, 32),
    "pennant_brown": (368, 64, 16, 32),
    "cloth":       (240, 64, 16, 16),   # plain worn canvas (bundles, the tent's ends)
    "books":       (256, 64, 32, 32),
    "chart":       (288, 64, 32, 32),
    # rooms (2 block tiles)
    "in_wall":     (0, 128, 32, 32),    # rough planks, a dark beam at the top
    "in_floor":    (32, 128, 32, 32),
    "in_ceil":     (64, 128, 32, 32),
    "in_wall_hold": (96, 128, 32, 32),
    "in_floor_hold": (128, 128, 32, 32),
    "carpet":      (160, 128, 32, 64),  # red runner with a gold border
    "rug":         (192, 128, 64, 64),
}

# names used by shared furniture builders (tools/corsair_furniture.py): the same pixels
for _alias, _src in (("wood_dark", "dark_wood"), ("wood_mid", "wood"), ("wood_light", "light_wood"), ("gold", "bronze"),
                     ("brass", "bronze"), ("rail", "dark_wood"), ("hull_mid", "wood"), ("canvas_cloth", "cloth"),
                     ("wall_wood", "in_wall"), ("compass", "bronze")):
    REGIONS[_alias] = REGIONS[_src]


def _noise(w, h, cells, rng):
    """Smooth value noise in [-1, 1]."""
    grid = [[rng.uniform(-1, 1) for _ in range(cells + 2)] for _ in range(cells + 2)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / w * cells, y / h * cells
            i, j = int(gx), int(gy)
            fx, fy = gx - i, gy - j
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            a = grid[j][i] * (1 - fx) + grid[j][i + 1] * fx
            b = grid[j + 1][i] * (1 - fx) + grid[j + 1][i + 1] * fx
            out[y][x] = a * (1 - fy) + b * fy
    return out


def _moss(px, region, rng, top=1.0, amount=0.55):
    """Moss over planks: olive green patches, denser towards the top (v = 0) of the region."""
    u, v, w, h = region
    n = _noise(w, h, 5, rng)
    greens = [_rgb(c) for c in ("5d6b33", "4f5a2c", "66703a", "48522a", "56603a")]
    browns = [_rgb(c) for c in ("4a3e26", "5a4a2e")]
    for y in range(h):
        for x in range(w):
            k = n[y][x] * 0.6 + rng.uniform(-0.25, 0.25) + amount - (y / h) * (1.0 - top) * 1.2
            if k > 0.25:
                c = rng.choice(browns) if rng.random() < 0.14 else rng.choice(greens)
                r, g, b, a = px[u + x, v + y]
                px[u + x, v + y] = _jitter(_mix((r, g, b), c, min(1.0, 0.5 + k * 0.45)), rng, 4) + (255,)


def _canvas(px, region, rng, base, dark, light, patches=4, alpha_holes=0, seams=True, patch_cols=None, stitches=False):
    """Worn canvas: a fine weave, stains, darker seams of the stitched widths, stitched patches."""
    u, v, w, h = region
    base, dark, light = _rgb(base), _rgb(dark), _rgb(light)
    n = _noise(w, h, 4, rng)
    n2 = _noise(w, h, 9, rng)
    for y in range(h):
        for x in range(w):
            k = n[y][x] * 0.5 + n2[y][x] * 0.3
            c = _mix(base, dark, max(0.0, k)) if k > 0 else _mix(base, light, -k * 0.8)
            if (x + 2 * y) % 3 == 0:
                c = _scale(c, 0.95)
            if seams and x % 16 == 15:
                c = _scale(c, 0.78)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    for _ in range(patches):
        pw, ph = rng.randint(6, 14), rng.randint(6, 12)
        x0, y0 = rng.randrange(1, w - pw - 1), rng.randrange(1, h - ph - 1)
        pc = _scale(rng.choice(patch_cols or (base, light, dark)), rng.uniform(0.9, 1.05))
        for y in range(ph):
            for x in range(pw):
                edge = x in (0, pw - 1) or y in (0, ph - 1)
                c = _scale(pc, 0.75) if edge and (x + y) % 2 == 0 else pc
                px[u + x0 + x, v + y0 + y] = _jitter(c, rng, 3) + (255,)
    if stitches:
        # stitched seams between the widths of cloth: a dark line with pale stitches across it
        for x in range(7, w, 16):
            for y in range(h):
                px[u + x, v + y] = _jitter(_scale(dark, 0.85), rng, 3) + (255,)
                if y % 3 == 0:
                    for xx in (x - 1, x + 1):
                        if 0 <= xx < w:
                            px[u + xx, v + y] = _jitter(_mix(light, (230, 220, 190), 0.4), rng, 3) + (255,)
    for _ in range(alpha_holes):
        cx, cy, r = rng.uniform(4, w - 4), rng.uniform(4, h - 4), rng.uniform(1.0, 2.6)
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, (y - cy) * 0.8)
                if d < r:
                    px[u + x, v + y] = (0, 0, 0, 0)
                elif d < r + 1.0:
                    rr, gg, bb, a = px[u + x, v + y]
                    px[u + x, v + y] = (int(rr * 0.6), int(gg * 0.6), int(bb * 0.6), 255)


def _fringe(px, region, rng):
    """Four torn tongues of cloth side by side (8 px each): the roof canvas's colour, full width at the top (the eave),
    tapering to a ragged point, the tip darker."""
    u, v, w, h = region
    base, dark, tip = _rgb("76604a"), _rgb("584634"), _rgb("3a2e22")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    for k in range(w // 8):
        x0 = k * 8
        skew = rng.uniform(-1.2, 1.2)
        for y in range(h):
            t = y / (h - 1)
            half = 4.0 * (1.0 - t ** 1.35) + 0.4
            cx = x0 + 3.5 + skew * t
            for x in range(x0, x0 + 8):
                d = abs(x - cx)
                if d <= half + rng.uniform(-0.6, 0.3):
                    if t > 0.5 and rng.random() < 0.06:
                        continue   # a tear
                    c = _mix(base, dark, 0.3 * rng.random() + (0.25 if d > half - 1 else 0))
                    c = _mix(c, tip, max(0.0, (t - 0.55) / 0.45) * 0.8)
                    if (x + 2 * y) % 3 == 0:
                        c = _scale(c, 0.95)
                    px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _pennant(px, region, rng, col, dark):
    """A big tattered pennant: the hoist along the top (v = 0), the sides tapering a little, a deep notch cut in the
    tail and ragged edges, a few tears."""
    u, v, w, h = region
    col, dark = _rgb(col), _rgb(dark)
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    for y in range(h):
        t = y / h
        half = (w / 2) * (1.0 - 0.45 * t) + rng.uniform(-0.7, 0.2)
        notch = max(0.0, (t - 0.62) / 0.38) * (w / 2) * 0.95     # the swallowtail
        for x in range(w):
            d = abs(x - w / 2 + 0.5)
            if d <= half and d >= notch - rng.uniform(0, 0.8):
                if t > 0.5 and rng.random() < 0.1:
                    continue   # tears
                c = _mix(col, dark, 0.35 * t + (0.25 if (x + y) % 5 == 0 else 0) + (0.2 if d > half - 1.2 else 0))
                px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    for x in range(w):
        px[u + x, v] = _jitter(_rgb("6a5638"), rng, 3) + (255,)   # the hem round the rope
        px[u + x, v + 1] = _jitter(_rgb("7a6646"), rng, 3) + (255,)


def _tube(px, region, rng):
    """Polished, darkened bronze-brown plates: a soft highlight down the middle of each facet, dark riveted seams,
    soot and a little verdigris."""
    u, v, w, h = region
    base = _rgb("6e4a2a")
    for y in range(h):
        for x in range(w):
            k = 0.82 + 0.3 * math.exp(-((y / h - 0.45) / 0.22) ** 2) + 0.03 * math.sin(x * 0.9 + y * 0.3)
            c = _scale(base, k)
            if x % 16 in (0, 15):
                c = _rgb("2a1c10")
            elif x % 16 in (2, 13) and y % 4 == 2:
                c = _rgb("a8824e")   # rivets
            if rng.random() < 0.04:
                c = _mix(c, _rgb("3e5a4a"), 0.35)
            elif rng.random() < 0.06:
                c = _scale(c, 0.8)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _tube_mouth(px, region, rng):
    """The back of a tube's throat: near black, a dim deep red glow in the middle."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5) / (w / 2)
            c = _mix(_rgb("4a1a0c"), _rgb("100a08"), min(1.0, d * 1.5)) if d < 0.7 else _rgb("0e0a08")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _emblem(px, region, rng):
    """The carved panel: light planks, a dark carved emblem (a winged diamond on a cross), a bevelled edge."""
    u, v, w, h = region
    _planks(px, region, ("8a6a48", "806244", "927252"), "5a4430", rng, plank_h=8, joints=0, grain=0.06)
    cx, cy = w / 2 - 0.5, h / 2 - 0.5
    dark, mid = _rgb("2e1f12"), _rgb("4a3420")
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            edge = x < 2 or y < 2 or x >= w - 2 or y >= h - 2
            cross = (abs(dx) < 1.6 and abs(dy) < 11) or (abs(dy) < 1.6 and abs(dx) < 11)
            diamond = abs(dx) + abs(dy) < 6.5
            wing = abs(dy + 0.35 * abs(dx) - 1) < 1.8 and 3 < abs(dx) < 12
            if edge:
                px[u + x, v + y] = _jitter(_scale(_rgb("6a4e34"), 0.85 if x < 2 or y < 2 else 0.7), rng, 3) + (255,)
            elif diamond and abs(dx) + abs(dy) > 4:
                px[u + x, v + y] = _jitter(mid, rng, 3) + (255,)
            elif diamond or cross or wing:
                px[u + x, v + y] = _jitter(dark, rng, 3) + (255,)


def _window_in(px, region, rng):
    """A small-paned window seen from inside: the sky (lighter at the bottom), dark wooden bars."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            bar = abs(x - w / 2 + 0.5) < 1.0 or abs(y - h / 2 + 0.5) < 1.0
            if frame or bar:
                c = _rgb("3a2614")
            else:
                c = _mix(_rgb("7eaee0"), _rgb("c8dcec"), y / h)
                if (x + y) % 7 == 0:
                    c = _scale(c, 1.06)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _curtain(px, region, rng):
    """A ragged curtain: worn beige cloth in folds, its bottom torn (transparent)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            bottom = h - 2 - 4 * abs(math.sin(x * 1.7)) - rng.uniform(0, 3)
            if y > bottom:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("a8946e"), 0.8 + 0.25 * (0.5 + 0.5 * math.sin(x * 1.3)))
            if y < 2:
                c = _rgb("5a4630")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _quilt(px, region, rng):
    """The bed's red quilt: patched red squares, a darker border, the folded linen sheet at its head (v = 0)."""
    u, v, w, h = region
    reds = [_rgb(c) for c in ("8e1c1c", "7e1818", "9a2420", "862020")]
    for y in range(h):
        for x in range(w):
            if y < 6:
                c = _scale(_rgb("ddd2bc"), 0.9 + 0.1 * (y % 3 == 0))
                if y == 5:
                    c = _rgb("9a8a70")
            elif x < 2 or x >= w - 2 or y >= h - 2:
                c = _rgb("4e0e0c")
            else:
                c = reds[((x - 2) // 7 + (y - 6) // 7) % len(reds)]
                if (x - 2) % 7 == 0 or (y - 6) % 7 == 0:
                    c = _scale(c, 0.78)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _grate(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 1 or x >= w - 1 or y < 1 or y >= h - 1
            bar = x % 4 == 0 or y % 4 == 0
            if frame or bar:
                c = _scale(_rgb("3c3a38"), 1.0 + 0.1 * ((x + y) % 3 == 0))
                px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
            else:
                px[u + x, v + y] = (0, 0, 0, 0)


def _door_leaf(px, region, rng):
    """One leaf (1 x 2 blocks): vertical planks, two iron straps, a ring handle, a dark frame."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb(("6b4426", "5e3b20", "73492a", "654024")[x // 4]), 1.0 + 0.06 * math.sin(y * 0.5 + x)) if x % 4 else _rgb("2e1d10")
            if y in (5, 6, h - 7, h - 6):
                c = _rgb("2c2c30")
            if x < 1 or x >= w - 1 or y < 1 or y >= h - 1:
                c = _rgb("2e1d10")
            if 11 <= x <= 13 and 15 <= y <= 18:
                c = _rgb("8a7a50")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wall_rough(px, region, rng, tones, beam="2e1c0e"):
    """Rough cabin walls: horizontal planks of uneven tones, a dark beam along the top, nail heads."""
    u, v, w, h = region
    _planks(px, region, tones, "24160a", rng, plank_h=4, joints=2, grain=0.07)
    for y in range(4):
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(_rgb(beam), 1.0 + 0.06 * math.sin(x * 0.4)), rng, 3) + (255,)
    for x in (0, w - 1):
        for y in range(h):
            px[u + x, v + y] = _jitter(_rgb(beam), rng, 3) + (255,)


def _ceiling(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            beam = (x % 16) < 4
            c = _scale(_rgb("3a2414"), 1.0 + 0.05 * math.sin(y * 0.3)) if beam else _scale(_rgb("5a3a20"), 1.0 + 0.05 * math.sin(y * 0.5 + x))
            if (x % 16) == 4 or ((y % 4) == 3 and not beam):
                c = _rgb("24160a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path):
    rng = random.Random(9137)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    # the hull: old brown planks of uneven tones, replaced lengths, iron plates, nails
    _planks(px, R["hull"], ("8e6236", "78522e", "9a6c3e", "835a32", "a47644", "6c4a2a"), "2e1c0c", rng, plank_h=4, joints=3, grain=0.08)
    _replaced(px, R["hull"], rng, 4, 5, ("9a7448", "4a301a", "86603c", "a07c50"), seam="24160a")
    _iron_patch(px, R["hull"], rng, 0.3, 0.4, 5, 4)
    _iron_patch(px, R["hull"], rng, 0.8, 0.7, 4, 5)
    _planks(px, R["hull_low"], ("5a3e26", "65462a", "4e3620", "6a4a2e"), "1e1208", rng, plank_h=4, joints=3, grain=0.07, worn=0.05,
            worn_col="4a5030")
    _replaced(px, R["hull_low"], rng, 4, 4, ("6a4a2c", "33241a", "5e4a32"), seam="1a1008")
    _moss(px, R["hull_low"], random.Random(31), top=0.6, amount=0.05)
    _planks(px, R["hull_patch"], ("9a7448", "4a301a", "86603c", "a07c50", "6e6658", "3a2a1e"), "1e1208", rng, plank_h=4, joints=4)
    _iron_patch(px, R["hull_patch"], rng, 0.55, 0.3, 6, 5)
    _planks(px, R["moss"], ("5e4228", "6a4a2c", "553a22"), "24160a", rng, plank_h=8, joints=1)
    _moss(px, R["moss"], random.Random(32), top=1.0, amount=0.45)
    _planks(px, R["moss_board"], ("5a3e24", "654628"), "24160a", rng, plank_h=8, joints=0)
    _moss(px, R["moss_board"], random.Random(33), top=0.2, amount=0.5)
    _planks(px, R["wood"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng)
    _planks(px, R["dark_wood"], ("4a2f1a", "40281a", "4e3420"), "1e140a", rng, plank_h=4, joints=1)
    _planks(px, R["light_wood"], ("a8906c", "9a8262", "b29a74", "8e7658"), "5a4630", rng, plank_h=4, joints=2, grain=0.07)
    _planks(px, R["pole"], ("6a4e34", "5e442c", "735638"), "3a2818", rng, plank_h=4, joints=0, grain=0.12)
    _planks(px, R["rib"], ("3e2816", "35220f", "46301c"), "1c1006", rng, plank_h=4, joints=0, grain=0.1)
    _planks(px, R["deck"], ("86603c", "7c5836", "8c6640", "74522f", "80603a"), "4a3018", rng, plank_h=4, joints=2)
    _replaced(px, R["deck"], rng, 4, 2, ("94704a", "6a4a2c"), seam="4a3018")
    _wall_rough(px, R["cabin_wall"], rng, ("5e3e22", "6a4628", "553820", "73502e"))
    _replaced_boards(px, R["cabin_wall"], rng, 2, ("8a6a48", "3e2a18"), board_w=4)
    _planks(px, R["lean"], ("8a7460", "7e6854", "947c66", "766250", "866e5a"), "5a4838", rng, plank_h=8, joints=1, grain=0.06, worn=0.04,
            worn_col="9a8a78")
    _fill(px, R["end_grain"], "8a6a42", rng, 10)
    _rope(px, R["rope"], "b09468", "6e5a3a", rng)
    _rope(px, R["rope_dark"], "7a6446", "4a3a26", rng)
    _fill(px, R["iron"], "3a3a3c", rng, 6)
    _fill(px, R["iron_light"], "6c6c6e", rng, 8)
    _fill(px, R["iron_dark"], "222224", rng, 4)
    _planks(px, R["bone"], ("a89a7e", "9e9074", "b0a286"), "7a6e58", rng, plank_h=4, joints=0, grain=0.05)
    _planks(px, R["tube_rim"], ("8a6440", "7e5a38", "936c46"), "4a3420", rng, plank_h=4, joints=0, grain=0.05)
    _fill(px, R["tube_in"], "1e1610", rng, 3)
    _emblem(px, R["emblem"], rng)
    _window_in(px, R["window_in"], rng)
    _curtain(px, R["curtain"], rng)
    _quilt(px, R["quilt"], rng)
    _blocks(px, R["chain"], ("4a4744", "3a3836", "56524c"), "1e1c1a", rng, bw=4, bh=2)
    _fill(px, R["glow"], "ffd27a", rng, 4)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    _fill(px, R["bronze"], "9a6e32", rng, 8)
    _tube(px, R["tube"], rng)
    _tube_mouth(px, R["tube_mouth"], rng)
    _window(px, R["window"], rng, lit=True)
    _grate(px, R["grate"], rng)
    _door_leaf(px, R["door_leaf"], rng)
    _planks(px, R["hatch"], ("6e4a2a", "5e3e22"), "24160a", rng, plank_h=4, joints=0)
    _fill(px, R["rung"], "6e4c2c", rng, 6)
    _fill(px, R["red_paint"], "8e2a1e", rng, 6)
    _fill(px, R["linen"], "e0d6c0", rng, 4)
    _blocks(px, R["bedding"], ("8e1c1c", "7e1818", "9a2420"), "5e1010", rng, bw=4, bh=4)
    _weave(px, R["sack"], rng, "a98b5e", "8e7349")
    _fill(px, R["glass"], "b8d4dc", rng, 4)
    _planks(px, R["carving"], ("5e3e22", "4a2f1a"), "24160a", rng, plank_h=4, joints=4)
    # cloth
    _canvas(px, R["canvas"], random.Random(41), "866e52", "5e4c38", "9c8466", patches=7, patch_cols=(_rgb("765f46"), _rgb("7e6a52"), _rgb("6a5640")))
    _canvas(px, R["canvas_under"], random.Random(42), "5a4836", "3e3226", "6a5642", patches=2)
    _fringe(px, R["fringe"], random.Random(43))
    _canvas(px, R["wing"], random.Random(44), "8c6640", "684a2c", "a27a50", patches=6, alpha_holes=2, seams=False, stitches=True,
            patch_cols=(_rgb("7a5838"), _rgb("96704a"), _rgb("82603c")))
    u0, v0, w0, h0 = R["wing"]
    u1, v1, _, _ = R["wing_t"]
    for y in range(h0):
        for x in range(w0):
            px[u1 + y, v1 + x] = px[u0 + x, v0 + y]
    _pennant(px, R["pennant_beige"], random.Random(45), "c0a884", "8a7656")
    _pennant(px, R["pennant_red"], random.Random(46), "8a2418", "561410")
    _pennant(px, R["pennant_black"], random.Random(47), "2e2a28", "141210")
    _pennant(px, R["pennant_brown"], random.Random(49), "7a5a38", "4a3420")
    _canvas(px, R["cloth"], random.Random(48), "a89070", "7a6650", "c0aa88", patches=1, seams=False)
    _books(px, R["books"], rng)
    _chart(px, R["chart"], rng)
    # rooms
    _wall_rough(px, R["in_wall"], random.Random(51), ("5e3e22", "6a4628", "553820", "73502e", "4e3420"))
    _replaced_boards(px, R["in_wall"], rng, 2, ("3e2a18", "4a3220"), board_w=4)
    _planks(px, R["in_floor"], ("6e4a2a", "634226", "7a5230", "5a3c22"), "2b1b0e", random.Random(52), plank_h=4, joints=2)
    _replaced(px, R["in_floor"], rng, 4, 3, ("86603c", "4a3220", "7a4a2e"))
    _ceiling(px, R["in_ceil"], random.Random(53))
    _wall_rough(px, R["in_wall_hold"], random.Random(54), ("4e3420", "5a3c24", "46301c", "553a22"), beam="24160a")
    _planks(px, R["in_floor_hold"], ("5e4228", "553b24", "684a2e"), "241810", random.Random(55), plank_h=4, joints=3, worn=0.04,
            worn_col="3a3a30")
    _carpet(px, R["carpet"], random.Random(56), border="b08a3e", field="7a1a16", centre="4a0e0c")
    _rug(px, R["rug"], random.Random(57))
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 icon: the long brown hull with its raised bow, the cabin and the beige canvas roof on its poles,
    a wing hanging under the side, the tubes at the stern."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    hull, hull_d, moss = _rgb("6e4a2a"), _rgb("4a3020"), _rgb("5d6b2a")
    canvas, canvas_d, pole = _rgb("9a8466"), _rgb("6e5a44"), _rgb("4a321c")
    wing, tube, lamp = _rgb("9a7048"), _rgb("8a6038"), _rgb("ffd27a")
    # hull (bow to the left, rising)
    rows = {8: (0, 13), 9: (1, 13), 10: (2, 12), 11: (4, 11)}
    for y, (x0, x1) in rows.items():
        for x in range(x0, x1 + 1):
            px[x, y] = (hull if (x + y) % 4 else hull_d) + (255,)
    for x in range(1, 14):
        px[x, 8] = moss + (255,) if x % 3 else hull + (255,)
    px[0, 7] = hull + (255,)
    # cabin and pilot rail
    for y in range(6, 8):
        for x in range(8, 14):
            px[x, y] = hull_d + (255,)
    px[10, 7] = lamp + (255,)
    # poles and the canvas roof
    for y in range(2, 6):
        px[8, y] = pole + (255,)
        px[13, y] = pole + (255,)
    for y, x0, x1 in ((1, 10, 11), (2, 8, 13), (3, 7, 14)):
        for x in range(x0, x1 + 1):
            px[x, y] = (canvas if (x + y) % 3 else canvas_d) + (255,)
    px[10, 0] = pole + (255,)
    # tubes at the stern
    for x in (14, 15):
        px[x, 7] = tube + (255,)
        px[x, 9] = tube + (255,)
    # a wing hanging under the side
    for y, x0, x1 in ((12, 6, 11), (13, 7, 10), (14, 8, 9), (15, 8, 8)):
        for x in range(x0, x1 + 1):
            px[x, y] = wing + (255,)
    img.save(path)
