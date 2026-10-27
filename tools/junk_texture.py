"""Textures of the Dragon Junk (dragon_junk).

  dragon_junk.png            512x512 atlas of the outside (REGIONS: u, v, w, h)
  dragon_junk_interior.png   512x512 atlas of the rooms and their furniture: the Sky Leviathan's interior atlas
                             (tools/leviathan_texture.make_interior_texture, the same region names "in_*"), with the
                             junk's own regions added in its free part (REGIONS_IN_EXTRA: the stern cabin's white
                             plaster walls between dark posts, red lacquer, paper screens)
  dragon_junk_sail.png       512x512: the great red sail with the black dragon (one panel; both panels use it, the
                             starboard one seen mirrored so that the dragon always faces the bow)

Colours of the reference sheet: a dark brown planked hull, a pale beak, cream-white plaster walls and bulwarks in
blocks, dark beams and posts, red lacquered panels, red tiled roofs with pale bamboo battens, a red-brown sail of
patched cloth, the dragon in black ink, a cream bow sail, warm lantern light.
"""
import math
import os
import random
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from galley_texture import _jitter, _rgb, _mix, _scale, fine_wood, polished_metal, hammered_iron, woven, twisted_rope, end_grain, \
    paint_lamp_glass
import leviathan_texture as lt
import junk_shape as js
import junk_dragon as jd

SIZE = 512
SIZE_IN = 512
SIZE_SAIL = 512

REGIONS = {
    # hull
    "hull":         (0, 0, 64, 32),     # dark weathered planks (along u)
    "hull_low":     (0, 32, 64, 32),    # the bottom, darker, tarred
    "beak":         (64, 0, 64, 32),    # pale planks of the beak (along u)
    "plaster":      (64, 32, 64, 32),   # cream-white plaster blocks of the bulwarks (rows along u)
    "plaster_wall": (128, 0, 64, 64),   # the stern house's walls: cream boards
    "red_panel":    (192, 0, 32, 32),   # red lacquered panel in a dark frame
    "red":          (224, 0, 16, 16),   # red lacquer
    "red_dark":     (240, 0, 16, 16),
    "post":         (224, 16, 32, 16),  # dark timber with iron straps (along u)
    "deck":         (256, 0, 64, 64),   # warm deck planks along u, 4 block tiles
    "roof":         (320, 0, 64, 64),   # red barrel tiles: courses along u, the tiles running down v
    "roof_under":   (384, 0, 32, 32),   # dark red-brown underside of the eaves, rafters
    "tile_end":     (416, 0, 32, 16),   # the round ends of a course of tiles
    "ridge":        (416, 16, 32, 16),  # dark ridge tiles
    "bamboo":       (448, 0, 32, 16),   # pale bamboo battens (along u, nodes)
    "bargeboard":   (448, 16, 32, 16),  # pale carved boards of the gables
    "emblem":       (480, 0, 32, 32),   # the round white plaque with the red coiled dragon
    "window":       (0, 64, 32, 32),    # lattice window lit from inside
    "window_dark":  (32, 64, 32, 32),
    "door_leaf":    (64, 64, 32, 64),   # one leaf of a door (1 x 2 blocks): dark frame, red panels, brass studs
    "grating":      (96, 64, 32, 32),   # the deck grating (open squares)
    "hatch":        (96, 96, 32, 32),
    "bow_sail":     (128, 64, 64, 64),  # cream canvas, battens, a worn ragged foot
    "pennant":      (192, 64, 32, 64),  # red pennant with a ragged fly
    "flag":         (224, 64, 64, 32),  # red flag with the black dragon roundel
    "stone":        (288, 64, 32, 32),  # pale stone of the lantern pedestals
    "gable":        (320, 64, 64, 64),  # plaster and dark beams of the gables
    "lattice":      (384, 64, 32, 32),  # red lattice of the balustrades (open)
    "sail_edge":    (416, 64, 32, 16),  # the rolled red cloth along the yard
    "chain_big":    (448, 64, 16, 32),  # the anchor chain (big links)
    "plank_light":  (464, 64, 32, 16),
    # the stern and the roofs (second round)
    "frieze":       (0, 176, 32, 16),   # carved frieze under the quarterdeck: pale wood, dark ring motifs (one panel)
    "baluster":     (32, 176, 32, 16),  # pale turned balusters between thin rails (open between them), 2 blocks along u
    "window_arch":  (64, 176, 16, 24),  # an arched lattice window lit from inside (transparent outside the arch)
    "arch_frame":   (80, 176, 16, 24),  # the carved dark frame round it (transparent in the opening)
    "carved":       (96, 176, 32, 32),  # dark carved panels (the gables' infill, between the windows)
    "sternpost":    (128, 176, 32, 16), # pale timber with iron bands (along u)
    "medallion":    (160, 176, 32, 32), # the round carved medallion: a beige disc with a dark interlaced knot
    "eave_frieze":  (192, 176, 64, 16), # the dark band under the eaves with carved brackets (along u)
    "void":         (256, 176, 16, 16), # the dark hold seen through the grating
    # the stern (third round)
    "parapet":      (272, 176, 32, 16), # the stern gallery's solid parapet: pale boards in dark frames, a carved lozenge
}
# small regions copied from the Sky Leviathan's atlas (same names, same look)
COPIED = ("iron", "steel", "brass", "gold", "copper", "chain", "rope", "rope_dark", "glow", "lantern", "glass", "gauge", "wax", "pearl",
          "coral_red", "organ_wood", "steel_dark", "chart", "bedding", "red_velvet", "leather", "coal", "fire", "porthole", "end_grain",
          "burlap", "barrel", "crate", "rung", "gear_iron", "dark_wood", "wood", "rail", "wale")


def _pack():
    """Places the copied regions in the free rows of the atlas (shelf packing from v = 128)."""
    x, y, row_h = 0, 128, 0
    for name in COPIED:
        w, h = lt.REGIONS[name][2:]
        if x + w > SIZE:
            x, y, row_h = 0, y + row_h, 0
        REGIONS[name] = (x, y, w, h)
        x += w
        row_h = max(row_h, h)


_pack()

REGIONS_IN_EXTRA = {
    "in_wall_plaster": (0, 256, 32, 64),   # stern cabin: white plaster between dark posts, a red rail, a dark beam
    "in_lacquer":      (32, 256, 16, 16),  # red lacquer (furniture)
    "in_screen":       (48, 256, 32, 32),  # paper screen in a dark lattice (lit)
    "in_floor_light":  (80, 256, 32, 32),  # warm polished planks of the stern cabin
    "in_ceil_beams":   (112, 256, 32, 32),  # ceiling planks between heavy dark beams
    "in_gold_trim":    (144, 256, 16, 16),
    "in_tatami":       (160, 256, 32, 32),  # straw mat
}
REGIONS_SAIL = {"sail": (0, 0, SIZE_SAIL, SIZE_SAIL)}


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(int(max(0, min(255, q))) for q in c[:3]) + (a,)


def _noise(w, h, cells, rng):
    g = np.array([[rng.uniform(-1, 1) for _ in range(cells + 2)] for _ in range(cells + 2)])
    ys, xs = np.mgrid[0:h, 0:w]
    gx, gy = xs / w * cells, ys / h * cells
    i, j = gx.astype(int), gy.astype(int)
    fx, fy = gx - i, gy - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g[j, i] * (1 - fx) + g[j, i + 1] * fx
    b = g[j + 1, i] * (1 - fx) + g[j + 1, i + 1] * fx
    return a * (1 - fy) + b * fy


# ---------------------------------------------------------------- painters
def _blocks(px, region, base, mortar, rng, bw=16, bh=8, offset=True, stains=0.15):
    """Plaster / stone blocks in courses, a thin dark mortar line, each block its own tone, some chipped."""
    u, v, w, h = region
    nz = _noise(w, h, 5, rng)
    rows = h // bh + 1
    for r in range(rows):
        sh = (bw // 2) * (r % 2) if offset else 0
        x = -sh
        while x < w:
            ln = bw + rng.choice((-4, 0, 0, 4))
            tone = _jitter(base, rng, 9)
            chip = rng.random() < 0.18
            for yy in range(bh):
                y = r * bh + yy
                if y >= h:
                    break
                for xx in range(ln):
                    xa = x + xx
                    if xa < 0 or xa >= w:
                        continue
                    if yy == bh - 1 or xx == 0:
                        c = mortar
                    else:
                        k = 1.0 + 0.06 * nz[y, xa] + (0.07 if yy == 0 else -0.05 if yy == bh - 2 else 0.0)
                        c = _scale(tone, k)
                        if chip and xx < 4 and yy > bh - 4:
                            c = _scale(tone, 0.82)
                        if stains and nz[y, xa] < -0.55:
                            c = _mix(c, (120, 104, 80), stains)
                    _put(px, u, v, xa, y, _jitter(c, rng, 3))
            x += ln


def _planks(px, region, base, dark, rng, plank_w=4, along_u=True, repairs=0.12, lengths=(14, 34), tone_var=10, nail_p=0.5,
            patch_cols=None):
    lt._plank_field(px, region, base, dark, rng, plank_w=plank_w, along_u=along_u, repairs=repairs, lengths=lengths, tone_var=tone_var,
                    nail_p=nail_p, patch_cols=patch_cols)


def _red_panel(px, region, rng):
    u, v, w, h = region
    nz = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                c = _scale(_rgb("2e1d12"), 1.0 + 0.08 * math.sin(x + y))      # dark frame
            elif e == 3:
                c = _rgb("5a1e14")
            elif e == 4:
                c = _rgb("c4523c")                                               # bevel highlight
            else:
                c = _scale(_rgb("9a2e22"), 1.0 + 0.07 * nz[y, x] - 0.1 * (y / h))
                if (x + 2 * y) % 17 == 0:
                    c = _scale(c, 0.85)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _roof(px, region, rng):
    """Red tiles in lapped courses (the courses run along u, the tiles hang down v): each tile's lower end rounded, the
    shadow of each course under the next one's scalloped edge, a soft highlight down the crowns, a darker brick red
    with each tile its own tone, a few darker or faded ones."""
    u, v, w, h = region
    nz = _noise(w, h, 6, rng)
    tw, course = 8, 8
    tones = {}
    for y in range(h):
        for x in range(w):
            row = y // course
            xs = x + (tw // 2 if row % 2 else 0)
            col = xs // tw
            lx = (xs % tw) + 0.5
            ly = (y % course) + 0.5
            key = (row, col % (w // tw + 1))
            if key not in tones:
                r = rng.random()
                tones[key] = 0.82 if r < 0.12 else 1.1 if r < 0.2 else 1.0 + rng.uniform(-0.05, 0.05)
            base = _scale(_rgb("8e3e2c"), tones[key])
            edge = course - 1.6 * math.sqrt(max(0.0, 1.0 - ((lx - tw / 2) / (tw / 2)) ** 2))   # the rounded lower end
            crown = math.cos((lx / tw - 0.5) * math.pi) ** 1.2
            k = 0.86 + 0.16 * crown - 0.1 * (ly / course) + 0.04 * nz[y, x]
            c = _scale(base, k)
            if ly > edge:
                c = _scale(_rgb("8e3e2c"), 0.55)          # the shadow under the next course's edge
            elif ly > edge - 1.0:
                c = _scale(base, 0.75)
            if lx < 0.9:
                c = _scale(base, 0.7)                     # the joint between two tiles
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _bamboo(px, region, rng, base="bc9862"):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            ny = (y + 0.5) / h
            k = 0.72 + 0.4 * math.sin(ny * math.pi) ** 0.6
            c = _scale(_rgb(base), k)
            if x % 12 in (0, 1):
                c = _scale(_rgb("8a6a3a"), k)          # the nodes
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _lattice(px, region, base, frame, open_alpha=True, step=6):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            bar = x % step in (0, 1) or y % step in (0, 1) or min(x, y, w - 1 - x, h - 1 - y) < 2
            if bar:
                c = frame if min(x, y, w - 1 - x, h - 1 - y) < 2 else base
                _put(px, u, v, x, y, c)
            else:
                px[u + x, v + y] = (0, 0, 0, 0) if open_alpha else (40, 30, 24, 255)


def _window_lattice(px, region, lit=True):
    """A window of paper panes behind a dark lattice (a fret of squares and a central diamond), lit warm from
    inside or dark."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 2:
                c = (46, 30, 18)
            elif x % 5 == 2 or y % 5 == 2 or abs((x - w / 2) + (y - h / 2)) < 0.8 or abs((x - w / 2) - (y - h / 2)) < 0.8:
                c = (58, 38, 22)
            else:
                g = 1.0 - 0.3 * abs((y + 0.5) / h - 0.5)
                c = _scale((255, 206, 128), g) if lit else _scale((92, 80, 62), g)
            _put(px, u, v, x, y, c)


def _door(px, region, rng):
    """An oriental door leaf: a dark frame, two red lacquered panels with a fret, brass studs and ring."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            c = _scale(_rgb("3a2414"), 1.0 + 0.05 * math.sin(y * 0.4))
            in_upper = 5 <= x < w - 5 and 6 <= y < h // 2 - 3
            in_lower = 5 <= x < w - 5 and h // 2 + 3 <= y < h - 6
            if in_upper or in_lower:
                c = _scale(_rgb("8e2a1e"), 1.0 + 0.05 * math.sin(x * 0.9 + y * 0.3))
                if in_upper and ((x - 5) % 6 == 0 or (y - 6) % 6 == 0):
                    c = _rgb("4a1a10")
            if e < 2:
                c = _rgb("24160c")
            if (x in (3, w - 4)) and y % 8 == 4:
                c = _rgb("c8a050")
            if abs(x - (w - 8)) <= 1 and abs(y - h // 2) <= 2:
                c = _rgb("d4b060")
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _emblem(px, region):
    """A round white plaque carved with a red coiled dragon (a spiral with a head), in a dark ring."""
    u, v, w, h = region
    im = Image.new("RGBA", (w * 4, h * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W = w * 4
    d.ellipse((2, 2, W - 3, W - 3), fill=(52, 34, 22, 255))
    d.ellipse((8, 8, W - 9, W - 9), fill=(222, 210, 184, 255))
    pts = []
    for k in range(120):
        a = k / 120 * 4.2 * math.pi
        r = (0.06 + 0.3 * k / 120) * W
        pts.append((W / 2 + math.cos(a) * r, W / 2 + math.sin(a) * r))
    d.line(pts, fill=(150, 42, 30, 255), width=7)
    d.ellipse((W / 2 - 9, W / 2 - 9, W / 2 + 9, W / 2 + 9), fill=(150, 42, 30, 255))
    im = im.resize((w, h), Image.LANCZOS)
    for y in range(h):
        for x in range(w):
            c = im.getpixel((x, y))
            px[u + x, v + y] = c if c[3] > 100 else (0, 0, 0, 0)


def _canvas(px, region, rng, base="d8ccb0", battens=(0.3, 0.62), ragged=True):
    """The cream bow sail: woven canvas, a few patches and seams, battens across, a worn ragged foot."""
    u, v, w, h = region
    nz = _noise(w, h, 5, rng)
    foot = [h - 1 - abs(int(4 * math.sin(x * 0.7) + 3 * math.sin(x * 1.9))) for x in range(w)]
    for y in range(h):
        for x in range(w):
            if ragged and y > foot[x]:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            k = 1.0 + 0.05 * nz[y, x] + 0.03 * ((x + y) % 2) - 0.12 * (y / h)
            c = _scale(_rgb(base), k)
            if x % 16 == 0:
                c = _scale(c, 0.85)            # seams of the cloths
            for b in battens:
                if abs(y - b * h) < 1.6:
                    c = _scale(_rgb("8a6a44"), 1.0)
            if 18 < x < 30 and 34 < y < 46:
                c = _scale(_rgb("c8b894"), k)  # a patch
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _pennant(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        width = w * (1.0 - 0.75 * y / h)
        for x in range(w):
            if abs(x - w / 2) > width / 2 or (y > h * 0.8 and (x + y) % 5 == 0):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("a8301f"), 1.0 + 0.08 * math.sin(y * 0.4) - 0.15 * y / h)
            if abs(x - w / 2) > width / 2 - 2:
                c = _rgb("d0a040")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _flag(px, region, rng):
    u, v, w, h = region
    im = Image.new("RGBA", (w * 4, h * 4), (164, 44, 30, 255))
    d = ImageDraw.Draw(im)
    W, H = w * 4, h * 4
    d.rectangle((0, 0, W - 1, 10), fill=(200, 160, 70, 255))
    d.rectangle((0, H - 11, W - 1, H - 1), fill=(200, 160, 70, 255))
    d.ellipse((W * 0.3, H * 0.15, W * 0.7, H * 0.85), fill=(226, 214, 190, 255))
    jd.draw_dragon(d, (W * 0.3, H * 0.17, W * 0.7, H * 0.83), gap=(226, 214, 190, 255))
    im = im.resize((w, h), Image.LANCZOS)
    for y in range(h):
        for x in range(w):
            c = im.getpixel((x, y))
            if x > w - 6 and (y * 3 + x) % 7 < 3:
                px[u + x, v + y] = (0, 0, 0, 0)
            else:
                _put(px, u, v, x, y, _jitter(c, rng, 3))


def _gable(px, region, rng):
    """Gable: white plaster between dark beams (a king post, two struts, a collar), a carved dark disc."""
    u, v, w, h = region
    _blocks(px, region, _rgb("ddd2b8"), _rgb("b8aa8c"), rng, bw=16, bh=8, stains=0.1)
    for y in range(h):
        for x in range(w):
            beam = abs(x - w / 2) < 3 or abs(y - h * 0.62) < 2.5 or abs(abs(x - w / 2) - (h - y) * 0.55) < 2.2 or y < 3 or y > h - 4
            if beam:
                _put(px, u, v, x, y, _jitter(_scale(_rgb("3a2414"), 1.0 + 0.06 * math.sin(x + y)), rng, 3))


def _frieze(px, region, rng):
    """One panel of the carved frieze: pale wood between dark rails, two dark rings with a knot, small dark studs."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("b89a6c"), 1.0 + 0.06 * math.sin(x * 0.7 + y * 0.2) - 0.05 * ((x * 3 + y * 5) % 7 == 0))
            if y < 2 or y > h - 3:
                c = _scale(_rgb("3a2414"), 1.0 + 0.05 * math.sin(x))
            for cx in (w * 0.25, w * 0.75):
                r = math.hypot(x + 0.5 - cx, (y + 0.5 - h / 2) * 1.05)
                if 3.6 < r < 5.6:
                    c = _scale(_rgb("2e1c10"), 1.0 + 0.1 * math.sin(math.atan2(y - h / 2, x - cx) * 3))
                elif r <= 1.6:
                    c = _rgb("4a2e18")
            if x in (0, w - 1):
                c = _rgb("3a2414")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _baluster(px, region, rng):
    """Pale turned balusters (a swelling every 8 pixels) between the rails, open between them."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            cx = (x % 8) + 0.5 - 4
            t = (y + 0.5) / h
            r = 1.3 + 1.1 * math.sin(math.pi * t) ** 2 + (0.6 if abs(t - 0.22) < 0.07 or abs(t - 0.78) < 0.07 else 0.0)
            if y < 2 or y > h - 3:
                c = _scale(_rgb("8a6a44"), 1.0 + 0.05 * math.sin(x))
            elif abs(cx) <= r:
                c = _scale(_rgb("c8aa78"), 0.8 + 0.35 * math.cos(cx / (r + 0.5) * 1.4))
            else:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _parapet(px, region, rng):
    """The stern gallery's parapet round the stern: panels of pale boards (one a block) in dark frames, each with a small
    carved dark lozenge, worn and stained like the back view's."""
    u, v, w, h = region
    nz = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            xx = x % 16
            board = y // 4
            c = _scale(_rgb("d4c09a"), 1.0 + 0.05 * math.sin(board * 2.1 + 1.0) + 0.06 * nz[y, x])
            if y % 4 == 3:
                c = _scale(c, 0.84)                    # the seams between the boards
            if nz[y, x] < -0.5:
                c = _mix(c, (130, 108, 78), 0.3)        # weathering
            dx, dy = abs(xx + 0.5 - 8), abs(y + 0.5 - h / 2)
            if dx / 2.6 + dy / 2.6 <= 1.0:
                c = _scale(_rgb("6a4a2c"), 1.0 + 0.12 * (dx + dy < 1.2))
            if xx in (0, 15):
                c = _scale(_rgb("4a3020"), 1.0 + 0.06 * math.sin(x + y))
            elif xx in (1, 14) or y in (0, h - 1):
                c = _scale(c, 0.86)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _wall_boards(px, region, rng):
    """The stern house's walls: cream boards laid along u (the back and side views show the boards' lines), each board
    its own tone, thin darker seams, a little grain, weathering low down."""
    u, v, w, h = region
    nz = _noise(w, h, 6, rng)
    bh = 5
    for y in range(h):
        board = y // bh
        tone = 1.0 + 0.045 * math.sin(board * 2.7 + 0.4) + 0.02 * math.sin(board * 7.1)
        joint = (board * 23) % 40 + 8
        for x in range(w):
            c = _scale(_rgb("e2d4b2"), tone + 0.04 * nz[y, x] - 0.06 * (y / h) + 0.02 * math.sin(x * 0.45 + board * 1.3))
            if y % bh == bh - 1:
                c = _scale(c, 0.8)
            elif y % bh == 0:
                c = _scale(c, 1.03)
            if x == joint % w:
                c = _scale(c, 0.82)
            if nz[y, x] < -0.62:
                c = _mix(c, (150, 128, 98), 0.25)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _arch_shape(x, y, w, h, inset=0.0):
    """Is (x, y) inside the arched opening (a rectangle with a round top) of a w x h panel, shrunk by inset pixels?"""
    r = w / 2 - inset
    cy = r + inset
    if y < cy:
        return math.hypot(x + 0.5 - w / 2, y + 0.5 - cy) <= r
    return inset <= x + 0.5 <= w - inset and y + 0.5 <= h - inset


def _window_arch(px, region):
    """The arched window's lit paper panes behind a dark lattice (transparent outside the arch)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if not _arch_shape(x, y, w, h):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if x % 4 == 1 or y % 4 == 1:
                c = (64, 40, 22)
            else:
                g = 1.0 - 0.35 * abs((y + 0.5) / h - 0.55)
                c = _scale((255, 204, 122), g)
            _put(px, u, v, x, y, c)


def _arch_frame(px, region, rng):
    """The carved dark frame of an arched window: a thick arch band, carved spandrels, transparent in the opening."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if _arch_shape(x, y, w, h, inset=2.6):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("3a2414"), 1.0 + 0.07 * math.sin(x * 1.3 + y * 0.7))
            if not _arch_shape(x, y, w, h, inset=1.2) and _arch_shape(x, y, w + 6, h + 6, inset=0.0) and 2 < y < h - 2:
                c = _scale(_rgb("5a3a20"), 1.0)
            if y < w / 2 and not _arch_shape(x, y, w, h, inset=0.4) and (x + y) % 3 == 0:
                c = _rgb("6a4a2a")                     # carving in the spandrels
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _carved(px, region, rng):
    """Dark carved panels: a raised frame, a fret of interlocking squares, worn highlights."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            xx, yy = x % 16, y % 16
            e = min(xx, yy, 15 - xx, 15 - yy)
            c = _scale(_rgb("3e2716"), 1.0 + 0.06 * math.sin(x * 0.9 + y * 0.4))
            if e == 0:
                c = _rgb("1e120a")
            elif e == 1:
                c = _rgb("6a4a2c")
            elif e >= 3:
                fx, fy = xx - 3, yy - 3
                fret = (fx in (0, 9) and 0 <= fy <= 9) or (fy in (0, 9) and 0 <= fx <= 9) or (fx == 4 and 2 <= fy <= 9) or (fy == 4 and 0 <= fx <= 6)
                if fret:
                    c = _scale(_rgb("7a5634"), 1.0 + 0.05 * math.sin(x + y))
                elif (fx, fy) in ((2, 2), (7, 7), (2, 7), (7, 2)):
                    c = _rgb("a07a48")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _medallion(px, region):
    """The round carved medallion: a beige disc in a dark rim with a dark interlaced knot (no spiral)."""
    u, v, w, h = region
    S = 4
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W = w * S
    d.ellipse((1, 1, W - 2, W - 2), fill=(46, 30, 18, 255))
    d.ellipse((7, 7, W - 8, W - 8), fill=(206, 186, 146, 255))
    d.ellipse((14, 14, W - 15, W - 15), outline=(120, 92, 60, 255), width=3)
    c = W / 2
    # an endless knot: two interlaced loops and a ring
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        ox, oy = math.cos(a) * W * 0.17, math.sin(a) * W * 0.17
        r = W * 0.15
        d.ellipse((c + ox - r, c + oy - r, c + ox + r, c + oy + r), outline=(52, 34, 20, 255), width=6)
    d.ellipse((c - W * 0.09, c - W * 0.09, c + W * 0.09, c + W * 0.09), outline=(52, 34, 20, 255), width=6)
    im = im.resize((w, h), Image.LANCZOS)
    for y in range(h):
        for x in range(w):
            q = im.getpixel((x, y))
            px[u + x, v + y] = q if q[3] > 110 else (0, 0, 0, 0)


def _eave_frieze(px, region, rng):
    """The band under the eaves: dark boards, carved brackets every block, a pale bead along the bottom."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("34200f"), 1.0 + 0.06 * math.sin(x * 0.5 + y))
            xx = x % 16
            if 5 <= xx <= 10 and y > 3:
                c = _scale(_rgb("4e3218"), 1.0 + (0.12 if xx in (5, 10) else 0.0))      # a bracket
                if y > h - 6 and xx in (7, 8):
                    c = _rgb("8a6038")
            if y >= h - 2:
                c = _rgb("8a6a44")
            if y < 2:
                c = _rgb("24160c")
            _put(px, u, v, x, y, _jitter(c, rng, 2))


# ---------------------------------------------------------------- the atlas
def make_texture(path):
    rng = random.Random(23)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    # the shared small parts: painted by the Sky Leviathan's texture code, copied here
    with tempfile.TemporaryDirectory() as tmp:
        lev = lt.make_texture(os.path.join(tmp, "lev.png"))
    for name in COPIED:
        su, sv, w, h = lt.REGIONS[name]
        du, dv, _, _ = REGIONS[name]
        img.paste(lev.crop((su, sv, su + w, sv + h)), (du, dv))
    R = REGIONS
    weathered = [_rgb("6e5038"), _rgb("4a3424"), _rgb("5e4a38"), _rgb("7a5a3c")]
    _planks(px, R["hull"], _rgb("5c3e28"), _rgb("24160c"), rng, plank_w=4, repairs=0.16, tone_var=9, patch_cols=weathered)
    _planks(px, R["hull_low"], _rgb("4a3220"), _rgb("1c120a"), rng, plank_w=4, repairs=0.12, tone_var=8, patch_cols=weathered)
    _planks(px, R["beak"], _rgb("a88a62"), _rgb("4a3622"), rng, plank_w=4, repairs=0.2, lengths=(8, 20), tone_var=12,
            patch_cols=[_rgb("bea078"), _rgb("8e7050"), _rgb("9a8a6a")])
    _blocks(px, R["plaster"], _rgb("ddd0b2"), _rgb("8a7a60"), rng, bw=16, bh=8, stains=0.18)
    _wall_boards(px, R["plaster_wall"], rng)
    _red_panel(px, R["red_panel"], rng)
    for name, col in (("red", "a2301f"), ("red_dark", "6a1e14")):
        u, v, w, h = R[name]
        for y in range(h):
            for x in range(w):
                _put(px, u, v, x, y, _jitter(_scale(_rgb(col), 1.0 + 0.06 * math.sin(x * 0.8 + y * 0.5)), rng, 4))
    fine_wood(img, R["post"], _rgb("3e2818"), _rgb("160c06"), 4, rng, knots=0.0)
    u, v, w, h = R["post"]
    for y in range(h):
        for x in (3, 4, w - 5, w - 4):
            _put(px, u, v, x, y, _rgb("2a2a2c") if y % 5 else _rgb("6a6662"))
    _planks(px, R["deck"], _rgb("9a7448"), _rgb("3c2814"), rng, plank_w=8, repairs=0.14, lengths=(20, 48), tone_var=10,
            patch_cols=[_rgb("aa865a"), _rgb("80603c"), _rgb("8e7a5e")])
    _roof(px, R["roof"], rng)
    _planks(px, R["roof_under"], _rgb("5a2a1c"), _rgb("22100a"), rng, plank_w=4, repairs=0.05, lengths=(32, 32), tone_var=6, nail_p=0.0)
    u, v, w, h = R["tile_end"]
    for y in range(h):
        for x in range(w):
            cx = (x % 8 + 0.5) / 8 - 0.5
            cy = (y + 0.5) / h - 0.5
            r = math.hypot(cx * 1.0, cy * 0.9)
            c = _rgb("3a1410") if r > 0.48 else _scale(_rgb("b04a36"), 1.1 - r) if r > 0.24 else _rgb("c46a4a")
            _put(px, u, v, x, y, c)
    u, v, w, h = R["ridge"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("5a1e16"), 0.8 + 0.35 * math.sin((y + 0.5) / h * math.pi) - (0.25 if x % 8 == 0 else 0.0))
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    _bamboo(px, R["bamboo"], rng)
    u, v, w, h = R["bargeboard"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("8a6440"), 1.0 + 0.08 * math.sin(x * 0.6) * math.sin(y * 0.9) + 0.05 * math.sin(x * 2.1))
            if y in (1, h - 2):
                c = _rgb("a88458")                      # beads along both edges
            if y in (0, h - 1):
                c = _rgb("3a2614")
            if x % 16 == 0:
                c = _rgb("4a3220")                      # the joints between the heavy blocks
            if 4 <= y <= h - 5 and (x % 8 in (3, 4)) and abs(y - h / 2) < 3:
                c = _rgb("5a3e24")                      # carved rosettes
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    _emblem(px, R["emblem"])
    _frieze(px, R["frieze"], rng)
    _baluster(px, R["baluster"], rng)
    _parapet(px, R["parapet"], rng)
    _window_arch(px, R["window_arch"])
    _arch_frame(px, R["arch_frame"], rng)
    _carved(px, R["carved"], rng)
    fine_wood(img, R["sternpost"], _rgb("b08e60"), _rgb("5a4028"), 4, rng, knots=0.05)
    u, v, w, h = R["sternpost"]
    for y in range(h):
        for x in range(w):
            if x % 16 in (6, 7):
                _put(px, u, v, x, y, _rgb("3a3a3c") if y % 5 else _rgb("74706a"))
    _medallion(px, R["medallion"])
    _eave_frieze(px, R["eave_frieze"], rng)
    u, v, w, h = R["void"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter((20, 14, 10), rng, 2))
    _window_lattice(px, R["window"], lit=True)
    _window_lattice(px, R["window_dark"], lit=False)
    _door(px, R["door_leaf"], rng)
    _lattice(px, R["grating"], _rgb("6a4a2c"), _rgb("3a2616"), step=8)
    u, v, w, h = R["hatch"]
    for y in range(h):
        for x in range(w):
            c = _rgb("6a4a2c") if (x % 4) else _rgb("2e1e10")
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                c = _rgb("2c2a28")
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    _canvas(px, R["bow_sail"], rng)
    _pennant(px, R["pennant"], rng)
    _flag(px, R["flag"], rng)
    _blocks(px, R["stone"], _rgb("c8baa0"), _rgb("6a5a44"), rng, bw=16, bh=8, stains=0.25)
    _gable(px, R["gable"], rng)
    _lattice(px, R["lattice"], _rgb("962c1e"), _rgb("3a2616"), step=7)
    u, v, w, h = R["sail_edge"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("8e3426"), 0.75 + 0.4 * math.sin((y + 0.5) / h * math.pi) + 0.05 * math.sin(x * 0.9))
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    u, v, w, h = R["chain_big"]
    for y in range(h):
        for x in range(w):
            link = (y // 8) % 2
            if link == 0:
                ring = (x in (3, 4, 11, 12) and 1 <= y % 8 <= 6) or (y % 8 in (0, 7) and 4 <= x <= 11)
            else:
                ring = 6 <= x <= 9
            c = _rgb("5e5a56") if ring else None
            if c is None:
                px[u + x, v + y] = (0, 0, 0, 0)
            else:
                _put(px, u, v, x, y, _jitter(c, rng, 6))
    fine_wood(img, R["plank_light"], _rgb("a4825a"), _rgb("4a3420"), 4, rng, knots=0.1)
    img.save(path)
    return img


# ---------------------------------------------------------------- the interior atlas
def make_interior_texture(path):
    """The Sky Leviathan's room atlas (wood panelling, plank floors, ceilings with joists, red rugs, the furniture
    made for the ships) and the junk's own regions in its free part."""
    img = lt.make_interior_texture(path)
    px = img.load()
    rng = random.Random(61)
    R = REGIONS_IN_EXTRA
    # the stern cabin: white plaster panels between dark posts, a dark beam under the ceiling, a red rail at
    # chair height, dark skirting (v spans the room height from the ceiling down)
    u, v, w, h = R["in_wall_plaster"]
    nz = _noise(w, h, 5, rng)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("e0d6be"), 1.0 + 0.05 * nz[y, x])
            if x % 16 in (0, 1, 2):
                c = _scale(_rgb("3a2414"), 1.0 + 0.06 * math.sin(y * 0.5))
            if y < 5:
                c = _scale(_rgb("3a2414"), 1.0 + (0.1 if y == 0 else 0.0))
            elif h * 0.62 < y < h * 0.62 + 3:
                c = _rgb("8e2a1e")
            elif y >= h - 5:
                c = _scale(_rgb("3a2414"), 0.95)
            _put(px, u, v, x, y, _jitter(c, rng, 2))
    u, v, w, h = R["in_lacquer"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_scale(_rgb("9a2c1e"), 1.0 + 0.06 * math.sin(x + y)), rng, 3))
    _window_lattice(px, R["in_screen"], lit=True)
    lt._plank_field(px, R["in_floor_light"], _rgb("8a5e36"), _rgb("2e1c0e"), rng, plank_w=4, along_u=True, repairs=0.08, lengths=(16, 32),
                    nail_p=0.3)
    u, v, w, h = R["in_ceil_beams"]
    lt._plank_field(px, R["in_ceil_beams"], _rgb("6a4428"), _rgb("2a180a"), rng, plank_w=4, along_u=True, repairs=0.05, lengths=(32, 32),
                    nail_p=0.0)
    for y in range(h):
        for x in range(w):
            if x % 16 < 4:
                _put(px, u, v, x, y, _scale(_rgb("2e1c10"), 1.0 + (0.12 if x % 16 == 0 else 0.0)))
    polished_metal(img, R["in_gold_trim"], [(0.0, (110, 76, 28)), (0.5, (196, 150, 64)), (1.0, (240, 210, 130))], rng)
    u, v, w, h = R["in_tatami"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("b8a670"), 1.0 + 0.06 * ((y % 2) - 0.5) + 0.03 * math.sin(x * 2.1))
            if x < 2 or x > w - 3:
                c = _rgb("2a3a24")
            _put(px, u, v, x, y, _jitter(c, rng, 2))
    img.save(path)
    return img


# ---------------------------------------------------------------- the great sail
def sail_frame():
    """The port panel flattened in its plane: 2D coordinates (along the yard aft, down) of its four corners
    (head fore, head aft, tack, clew), in blocks."""
    h0, h1, tack, clew = (np.array(p, dtype=float) for p in js.sail_corners(1))
    e1 = h1 - h0
    e1 /= np.linalg.norm(e1)
    n = np.array(js.sail_normal(1))
    e2 = np.cross(n, e1)
    if np.dot(e2, tack - h0) < 0:
        e2 = -e2

    def flat(p):
        return np.array([np.dot(p - h0, e1), np.dot(p - h0, e2)])
    return [flat(p) for p in (h0, h1, tack, clew)]


def _bilinear(c, s, t):
    """2D point of the panel at (s down from the head, t from the luff to the leech)."""
    h0, h1, tack, clew = c
    top = h0 + (h1 - h0) * t[..., None]
    bot = tack + (clew - tack) * t[..., None]
    return top + (bot - top) * s[..., None]


ARCH = (0.5, 0.8, 3.9)     # the arch cut round the mast: from / to (fractions of the foot from the clew), its height (blocks);
#                            a broad leg of cloth (a fifth of the foot) stays forward of it, down to the tack


def sail_outline_2d():
    """Outline of the panel in its flattened plane (blocks): the head along the yard, the leech bulging a little
    aft, the foot from the clew with a gentle hollow and, near the tack, the high arch cut round the mast
    (side and perspective views), the straight luff up to the yard."""
    h0, h1, tack, clew = sail_frame()
    pts = []
    for k in range(9):
        pts.append(h0 + (h1 - h0) * k / 8)
    n = 24
    lee = clew - h1
    lee_n = np.array([lee[1], -lee[0]]) / np.linalg.norm(lee)
    if np.dot(lee_n, h1 - h0) < 0:
        lee_n = -lee_n
    for k in range(1, n + 1):
        f = k / n
        pts.append(h1 + lee * f + lee_n * 0.55 * math.sin(math.pi * f))
    foot = tack - clew
    up = h0 - (tack + clew) / 2
    up /= np.linalg.norm(up)
    for k in range(1, 61):
        f = k / 60          # 0 at the clew, 1 at the tack
        lift = 0.45 * math.sin(math.pi * f)
        if ARCH[0] < f < ARCH[1]:
            lift += ARCH[2] * math.sin(math.pi * (f - ARCH[0]) / (ARCH[1] - ARCH[0])) ** 0.7
        pts.append(clew + foot * f + up * lift)
    for k in range(1, 8):
        pts.append(tack + (h0 - tack) * k / 8)
    return pts


def sail_inside(s, t):
    """Is the panel's cloth there, at (s, t) (arrays)? Used for the texture's alpha and to clip the battens."""
    c = sail_frame()
    p = _bilinear(c, np.asarray(s, dtype=float), np.asarray(t, dtype=float))
    if not _MASK:
        allp = np.array(sail_outline_2d())
        amin = allp.min(axis=0) - 1.0
        amax = allp.max(axis=0) + 1.0
        ppb = 20
        im = Image.new("L", (int((amax[0] - amin[0]) * ppb), int((amax[1] - amin[1]) * ppb)), 0)
        ImageDraw.Draw(im).polygon([((q[0] - amin[0]) * ppb, (q[1] - amin[1]) * ppb) for q in allp], fill=255)
        _MASK.append((np.asarray(im), amin, ppb))
    m, amin, ppb = _MASK[0]
    ix = np.clip(((p[..., 0] - amin[0]) * ppb).astype(int), 0, m.shape[1] - 1)
    iy = np.clip(((p[..., 1] - amin[1]) * ppb).astype(int), 0, m.shape[0] - 1)
    return m[iy, ix] > 127


_MASK = []


def make_sail_texture(path, ppb=40):
    """The sail panel: the outline cut out of patched red-brown cloth (seams, darker and paler cloths, stitched
    patches, wear at the edges, the battens' shadows), the black dragon painted big in its middle, drawn in the
    flattened panel at ppb pixels a block, then mapped onto the panel's (s, t) texture square."""
    rng = random.Random(5)
    c = sail_frame()
    allp = np.array(sail_outline_2d())
    amin, amax = allp.min(axis=0) - 1.0, allp.max(axis=0) + 1.0
    Wc, Hc = int((amax[0] - amin[0]) * ppb), int((amax[1] - amin[1]) * ppb)

    def C(p):
        return ((p[0] - amin[0]) * ppb, (p[1] - amin[1]) * ppb)
    canvas = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    outline = [C(p) for p in allp]
    # the cloth: panels of slightly different reds, diagonal seams (the reference's patchwork)
    base = np.array([178, 72, 56], dtype=float)
    cloth = Image.new("RGB", (Wc, Hc))
    arr = np.zeros((Hc, Wc, 3))
    ys, xs = np.mgrid[0:Hc, 0:Wc]
    bx = (xs / ppb + amin[0])
    by = (ys / ppb + amin[1])
    band = np.floor((bx * 0.55 + by * 0.85) / 1.6)
    tone = 1.0 + 0.05 * np.sin(band * 2.3) + 0.03 * np.cos(band * 5.1)
    nz = _noise(Wc, Hc, 14, rng)
    nz2 = _noise(Wc, Hc, 40, rng)
    shade = tone + 0.06 * nz + 0.03 * nz2
    for k in range(3):
        arr[..., k] = base[k] * shade
    seam = np.abs(((bx * 0.55 + by * 0.85) / 1.6) % 1.0 - 0.0) < (1.2 / ppb / 1.6 * 2.2)
    arr[seam] *= 0.86
    # cross seams (horizontal cloths) and the weave
    seam2 = np.abs((by / 2.4) % 1.0) < 0.012
    arr[seam2] *= 0.9
    weave = ((xs + ys) % 2 == 0)
    arr[weave] *= 1.025
    # patches: stitched rectangles of paler or darker cloth
    for k in range(9):
        cx, cy = rng.uniform(amin[0] + 2, amax[0] - 2), rng.uniform(amin[1] + 2, amax[1] - 2)
        w, h = rng.uniform(0.9, 2.2), rng.uniform(0.8, 1.8)
        f = rng.choice((0.93, 1.05, 0.96, 1.07))
        m = (np.abs(bx - cx) < w / 2) & (np.abs(by - cy) < h / 2)
        arr[m] *= f
        edge = m & ((np.abs(np.abs(bx - cx) - w / 2) < 1.5 / ppb) | (np.abs(np.abs(by - cy) - h / 2) < 1.5 / ppb))
        stitch = edge & ((xs + ys) % 4 < 2)
        arr[stitch] = arr[stitch] * 0.7 + np.array((190, 130, 90)) * 0.3
    cloth = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    mask = Image.new("L", (Wc, Hc), 0)
    ImageDraw.Draw(mask).polygon(outline, fill=255)
    # worn, darker edges (a band along the outline)
    edge_dark = mask.filter(ImageFilter.GaussianBlur(ppb * 0.35))
    ed = np.asarray(edge_dark, dtype=float) / 255.0
    arr = np.asarray(cloth, dtype=float)
    arr *= (0.8 + 0.2 * np.clip((ed - 0.5) * 2.2, 0, 1))[..., None]
    # the battens' shadows across the cloth
    for sb in js.SAIL_BATTENS:
        for k in range(60):
            t = k / 59
            p = _bilinear(c, np.array(sb), np.array(t))
            px_, py_ = C(p)
            r = ppb * 0.22
            x0_, x1_ = int(max(0, px_ - r)), int(min(Wc, px_ + r))
            y0_, y1_ = int(max(0, py_ - r * 0.4)), int(min(Hc, py_ + r * 1.6))
            arr[y0_:y1_, x0_:x1_] *= 0.965
    cloth = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # the dragon, painted in black ink, its head towards the luff (forwards); placed after the side and
    # perspective views: a tall column from a fifth of the way down the panel to just above the foot, its middle a
    # little aft of the panel's middle
    ink = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    di = ImageDraw.Draw(ink)
    h0, h1, tack, clew = c
    box_w = 5.7                         # blocks; the design is jd.DESIGN_H widths high
    ox, oy = -1.85, 3.6
    x0_, y0_ = C((ox, oy))
    x1_, y1_ = C((ox + box_w, oy + box_w * jd.DESIGN_H))
    jd.draw_dragon(di, (x0_, y0_, x1_, y1_), ink=(20, 12, 10, 255), gap=None)
    ink_a = np.asarray(ink, dtype=float)[..., 3] / 255.0
    # worn paint: the cloth's weave shows a little through the ink
    wear = np.clip(0.88 + 0.12 * nz2 + 0.05 * nz, 0.6, 1.0)
    cl = np.asarray(cloth, dtype=float)
    inkc = np.array([20, 12, 10], dtype=float)
    a = (ink_a * wear)[..., None]
    cl[..., :3] = cl[..., :3] * (1 - a) + inkc * a
    cl[..., 3] = np.asarray(mask, dtype=float)
    design = Image.fromarray(np.clip(cl, 0, 255).astype(np.uint8), "RGBA")
    # the texture is the flattened panel itself (its box sail_box()), cut out by its alpha: the model lays its cells
    # on a grid of this plane (generate_junk.sail_panel), so the outline is drawn at the texture's resolution
    N = SIZE_SAIL
    out = np.asarray(design.resize((N, N), Image.LANCZOS), dtype=float).copy()
    out[..., 3] = np.where(out[..., 3] > 110, 255, 0)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(path)
    return design


def sail_box():
    """(amin, amax): the box of the flattened panel covered by the sail texture (blocks, along the yard / down)."""
    allp = np.array(sail_outline_2d())
    return allp.min(axis=0) - 1.0, allp.max(axis=0) + 1.0


def flat_to_st(a, b):
    """(s, t) of the panel's bilinear patch at the flattened point (a, b) (Newton; may lie a little outside [0, 1]
    for the bulge of the leech)."""
    h0, h1, tack, clew = sail_frame()
    s, t = 0.5, 0.5
    target = np.array([a, b], dtype=float)
    for _ in range(30):
        p = _bilinear((h0, h1, tack, clew), np.array(s), np.array(t))
        top, bot = h0 + (h1 - h0) * t, tack + (clew - tack) * t
        ds = bot - top
        dt = (h1 - h0) * (1 - s) + (clew - tack) * s
        J = np.column_stack([ds, dt])
        e = target - p
        if np.abs(e).max() < 1e-9:
            break
        d = np.linalg.solve(J, e)
        s, t = s + d[0], t + d[1]
    return float(s), float(t)


def inside_flat(a, b):
    """Is the cloth at the flattened point (a, b)?"""
    if not _MASK:
        sail_inside(np.array([0.5]), np.array([0.5]))
    m, amin, ppb = _MASK[0]
    ix = int(np.clip((a - amin[0]) * ppb, 0, m.shape[1] - 1))
    iy = int(np.clip((b - amin[1]) * ppb, 0, m.shape[0] - 1))
    return m[iy, ix] > 127


# ---------------------------------------------------------------- item icon
def make_item_icon(path):
    """16x16 icon: the red sail with a black dragon stroke over the dark hull and the red stern roof."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line((4, 1, 6, 11), fill=(58, 40, 26, 255))                                  # the raked mast
    d.polygon([(5, 2), (9, 2), (12, 10), (2, 10)], fill=(164, 52, 38, 255), outline=(110, 34, 24, 255))   # the sail
    d.line((7, 4, 8, 5), fill=(20, 14, 14, 255))
    d.line((8, 5, 7, 7), fill=(20, 14, 14, 255))
    d.line((7, 7, 9, 8), fill=(20, 14, 14, 255))
    d.point((6, 4), fill=(20, 14, 14, 255))
    d.polygon([(10, 7), (13, 5), (15, 7), (15, 9), (10, 9)], fill=(172, 50, 36, 255), outline=(96, 30, 20, 255))  # the stern roof
    d.rectangle((11, 9, 14, 10), fill=(226, 214, 188, 255))
    d.polygon([(0, 13), (2, 11), (15, 11), (14, 14), (3, 14)], fill=(84, 56, 36, 255), outline=(36, 24, 14, 255))   # the hull, the beak
    d.line((2, 11, 13, 11), fill=(226, 214, 188, 255))
    d.point((12, 12), fill=(255, 214, 130, 255))
    img.save(path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    make_texture(os.path.join(out, "dragon_junk.png"))
    make_sail_texture(os.path.join(out, "dragon_junk_sail.png"))
    make_interior_texture(os.path.join(out, "dragon_junk_interior.png"))
    make_item_icon(os.path.join(out, "icon.png"))
