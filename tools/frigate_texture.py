"""Procedural pixel-art textures of the Blue-Sailed Frigate (blue_frigate): a 512x512 atlas of the
hull, the fittings and the rooms (blue_frigate.png) and a 512x512 atlas of the sails
(blue_frigate_sails.png), so that the fleurs-de-lis keep their resolution.

Colours of the reference: a royal blue planked hull between a gold band at the waterline and the
gold planksheer, dark brown wood below the water, gold rails and balusters, red gun-port lids in gold
frames, pale blue sails made of blocky cloths (light blue and white wool of the reference) bearing a
black (navy) fleur-de-lis, tricolour flags, gold-brown masts, tarred hemp ropes, lit windows and
lanterns; inside, dark panelling with a gold rail in the captain's cabin, plank floors and beams, the
plain planks of the hold.

Every region is (u, v, w, h); REGIONS and SAIL_REGIONS are shared with tools/generate_frigate.py.
"""
import math
import random

from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass
import corsair_texture as ct

SIZE = 512
SAIL_SIZE = 512

REGIONS = {
    # hull and upper works
    "hull_blue":   (0, 0, 64, 32),
    "hull_blue2":  (64, 0, 64, 32),     # the same, a little weathered
    "gold":        (128, 0, 64, 16),    # plain gold (rails, balusters, bands)
    "gold_band":   (128, 16, 64, 16),   # gold band with its dark edge lines (hull trims)
    "hull_brown":  (192, 0, 64, 32),    # below the waterline
    "wood_dark":   (256, 0, 64, 32),
    "wood_mid":    (320, 0, 64, 32),
    "wood_light":  (384, 0, 64, 32),
    "rail":        (448, 0, 64, 16),    # gold cap rail
    "mast":        (448, 16, 64, 16),
    "deck":        (0, 32, 64, 64),
    "lantern":     (64, 32, 16, 16),
    "rope":        (80, 32, 16, 16),
    "iron":        (96, 32, 16, 16),
    "bronze":      (112, 32, 16, 16),
    "glow":        (64, 48, 16, 16),
    "end_grain":   (80, 48, 16, 16),
    "rope_light":  (96, 48, 16, 16),    # ratlines and shrouds (tarred hemp)
    "glass":       (112, 48, 16, 16),
    "dark_wood":   (64, 64, 32, 16),
    "red_paint":   (96, 64, 16, 16),
    "white_paint": (112, 64, 16, 16),
    "navy":        (64, 80, 16, 16),
    "compass":     (80, 80, 16, 16),
    "cloth_roll":  (96, 80, 32, 16),    # furled pale blue canvas
    "glow_window": (128, 32, 32, 32),
    "window_in":   (160, 32, 32, 32),
    "door":        (192, 32, 32, 32),
    "grating":     (224, 32, 32, 32),
    "gunport":     (256, 32, 32, 32),   # red lid in its gold frame
    "flag":        (288, 32, 64, 40),   # the tricolour, swallow-tailed
    "chart":       (352, 32, 32, 32),
    "books":       (384, 32, 32, 32),
    "carving":     (416, 32, 64, 16),   # gold carved moulding
    "bedding":     (416, 48, 32, 16),
    "linen":       (448, 48, 16, 16),
    "sack":        (464, 48, 16, 16),
    "canvas":      (480, 48, 32, 16),
    "cannon":      (352, 64, 32, 16),   # dark bronze gun
    "bore":        (384, 64, 16, 16),
    "painting":    (480, 64, 32, 24),
    "stern_lily":  (320, 160, 48, 48),  # gold fleur-de-lis on a blue field (stern and bow emblems)
    "wall_stone":  (416, 64, 64, 32),
    # the hull strakes (one plank each, stretched on its board: the planking follows the sheer instead of
    # tiling little bricks), a darker one low, a brighter one high, the dark wood of the bottom
    "strake_lo":   (0, 160, 64, 16),
    "strake_mid":  (64, 160, 64, 16),
    "strake_hi":   (128, 160, 64, 16),
    "strake_brown": (192, 160, 64, 16),
    "strake_brown2": (256, 160, 64, 16),
    "rope_dark":   (368, 160, 16, 16),  # tarred shrouds and ratlines (near black, as on the reference)
    "gunport_open": (0, 176, 32, 32),   # the open port: gold frame round a dark opening
    "gunport_lid": (32, 176, 32, 16),   # the red lid, raised (outside face)
    "castle_panel": (64, 176, 64, 32),  # the stern castle: royal blue panel in a thin gold frame
    "taffrail":    (128, 176, 64, 24),  # gold carved taffrail with scrolls
    # rooms
    "wall_wood":   (0, 96, 64, 64),     # the cabin: dark panelling, a gold rail
    "floor":       (64, 96, 64, 64),
    "ceil":        (128, 96, 64, 64),
    "hold_floor":  (192, 96, 64, 64),
    "hold_wall":   (256, 96, 64, 64),
    "carpet":      (320, 96, 32, 64),
    "rug":         (352, 96, 32, 64),
    "boat":        (384, 96, 64, 32),
    "ham":         (448, 96, 16, 16),
}
# names used by the shared helpers (ship_details, generate_galleon, corsair_furniture): the same pixels
for _alias, _src in (("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"), ("wood_trim", "wood_dark"),
                     ("wood_honey", "wood_mid"), ("blue_paint", "hull_blue"), ("pilaster", "wood_dark"), ("velvet", "red_paint"),
                     ("cushion", "red_paint"), ("brass", "bronze"), ("organ_wood", "wood_dark"), ("steel", "iron"), ("stripe", "white_paint"),
                     ("patch_wood", "wood_light"), ("repair", "wood_mid"), ("plate", "iron"), ("hearth_stone", "wall_stone"), ("soot", "iron"),
                     ("stone_floor", "wall_stone")):
    REGIONS[_alias] = REGIONS[_src]

# the sails (second texture): one region each, 16 px a block of canvas
SAIL_REGIONS = {
    "fore_course":     (0, 0, 256, 144),
    "main_course":     (256, 0, 256, 152),
    "fore_topsail":    (0, 152, 208, 112),
    "main_topsail":    (208, 152, 216, 112),
    "fore_topgallant": (0, 264, 160, 80),
    "main_topgallant": (160, 264, 160, 88),
    "mizzen_topsail":  (320, 264, 144, 72),
    "jib":             (0, 352, 128, 160),
    "spanker":         (128, 352, 128, 112),
}
SAIL_CELLS = {  # (columns, rows) of cloth blocks drawn in each sail region
    "fore_course": (16, 9), "main_course": (16, 9), "fore_topsail": (13, 7), "main_topsail": (13, 7),
    "fore_topgallant": (10, 5), "main_topgallant": (10, 5), "mizzen_topsail": (9, 4), "jib": (8, 10), "spanker": (8, 7),
}
# which sails carry the fleur-de-lis (the reference shows it on the topsails and topgallants; the courses,
# the biggest sails seen from the deck, carry it too)
EMBLEM_SAILS = ("fore_topsail", "main_topsail", "fore_topgallant", "main_topgallant", "fore_course", "main_course")

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill


# ---------------------------------------------------------------- the fleur-de-lis
# The heraldic fleur-de-lis, drawn by hand in 16 x 18 cells (the blocky emblem of the reference): a pointed
# central petal, two side petals rising from the band, bending outward and drooping at their tips, the band,
# the stem and its two curled feet.
LILY = [
    ".......XX.......",
    "......XXXX......",
    "......XXXX......",
    ".....XXXXXX.....",
    ".....XXXXXX.....",
    "..XX.XXXXXX.XX..",
    ".XXXX.XXXX.XXXX.",
    "XXXXX.XXXX.XXXXX",
    "XX.XX.XXXX.XX.XX",
    "X..XX.XXXX.XX..X",
    "X..XX..XX..XX..X",
    "...XX..XX..XX...",
    "..XXXXXXXXXXXX..",
    "..XXXXXXXXXXXX..",
    "......XXXX......",
    ".....XXXXXX.....",
    "...XX.XXXX.XX...",
    "..XX..XXXX..XX..",
]


def fleur_de_lis_mask(w, h, cell=None):
    """Mask (0/255, size w x h) of the fleur-de-lis LILY, drawn in square cells as big as fit in w x h
    (or `cell` px when given), centred."""
    cw, ch = len(LILY[0]), len(LILY)
    cell = cell or max(1, min(w // cw, h // ch))
    img = Image.new("L", (w, h), 0)
    px = img.load()
    ox, oy = (w - cw * cell) // 2, (h - ch * cell) // 2
    for r, row in enumerate(LILY):
        for c, ch_ in enumerate(row):
            if ch_ != "X":
                continue
            for y in range(cell):
                for x in range(cell):
                    X, Y = ox + c * cell + x, oy + r * cell + y
                    if 0 <= X < w and 0 <= Y < h:
                        px[X, Y] = 255
    return img


# ---------------------------------------------------------------- painters
def _sail(px, region, cols, rows, rng, emblem=False, tri=None, whiter=0.0):
    """Pale blue blocky sail: one tone per cloth block (the light blue, white and pale wool blocks of
    the reference), a soft lighter sheen, darker worn edges, seams; the fleur-de-lis in navy on the
    middle; tri = triangle mask (region fractions) for the jibs."""
    u, v, w, h = region
    blues = [_rgb(c) for c in ("9cc1ea", "a6c8ee", "92b9e6", "b2d0f1", "8db5e3", "a0c4ec", "bcd6f3")]
    white = _rgb("e6eff9")
    dark = _rgb("5a7fb4")
    cw, ch = w / cols, h / rows
    tone = [[_scale(rng.choice(blues), rng.uniform(0.96, 1.04)) for _ in range(cols)] for _ in range(rows)]
    # whole white cloths among the blue ones (the reference mixes white and light blue wool), and the
    # middle of the sail catches the light: whiter towards the centre, bluer in the shadowed edges
    for r in range(rows):
        for c in range(cols):
            if rng.random() < 0.16:
                tone[r][c] = _mix(white, rng.choice(blues), rng.uniform(0.1, 0.4))
            dx, dy = (c + 0.5) / cols - 0.5, (r + 0.5) / rows - 0.45
            dd = math.hypot(dx * 1.3, dy * 1.1)
            tone[r][c] = _mix(tone[r][c], white, max(0.0, 0.42 - dd * 0.9))
            if whiter:
                tone[r][c] = _mix(tone[r][c], white, whiter)
            tone[r][c] = _mix(tone[r][c], dark, max(0.0, dd - 0.42) * 0.5)
    mask = None
    if emblem:
        # the emblem (16 x 18 cells of the LILY) about a third of the width, 4/5 of the height at most
        cell = max(2, min(int(w * 0.38) // 16, int(h * 0.82) // 18))
        ew, eh = 16 * cell, 18 * cell
        mask = fleur_de_lis_mask(ew, eh, cell)
        mx, my = (w - ew) // 2, int(h * 0.47 - eh / 2)
    navy = _rgb("141f44")
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            if tri is not None and not ct._tri_inside(tri, fx, fy):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c_, r_ = min(cols - 1, int(x / cw)), min(rows - 1, int(y / ch))
            lx, ly = x - c_ * cw, y - r_ * ch
            c = tone[r_][c_]
            if lx < 1 or ly < 1:
                c = _scale(c, 0.9)       # the edges of the cloth blocks
            elif (x * 7 + y * 13) % 29 == 0:
                c = _scale(c, 0.95)
            edge = min(fx, 1 - fx, fy, 1 - fy) if tri is None else min(fy, 1 - fy, 0.5)
            if edge < 0.02:
                c = _mix(c, dark, 0.65)  # bolt rope
            elif fy > 0.9:
                c = _mix(c, dark, (fy - 0.9) * 1.5)
            if mask is not None and mx <= x < mx + mask.width and my <= y < my + mask.height and mask.getpixel((x - mx, y - my)):
                c = _mix(navy, _rgb("1e2d58"), 0.5 * ((x // 4 + y // 4) % 2))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    if tri is not None:
        for y in range(h):
            for x in range(w):
                fx, fy = (x + 0.5) / w, (y + 0.5) / h
                if not ct._tri_inside(tri, fx, fy):
                    continue
                if not all(ct._tri_inside(tri, fx + dx / w, fy + dy / h) for dx, dy in ((1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6))):
                    px[u + x, v + y] = _jitter(dark, rng, 3) + (255,)


def _tricolour(px, region, rng):
    """The French tricolour (blue at the hoist), swallow-tailed at the fly (transparent notch)."""
    u, v, w, h = region
    cols = [_rgb("1f3f9e"), _rgb("f0ede6"), _rgb("c8262a")]
    for y in range(h):
        for x in range(w):
            k = min(2, int(3 * x / w))
            c = cols[k]
            fx = x / w
            notch = fx > 0.72 and abs(y - h / 2 + 0.5) < (fx - 0.72) / 0.28 * (h / 2 - 1)
            if notch:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(c, 1.0 + 0.04 * math.sin(x * 0.9 + y * 0.5))
            if x == 0 or x == 1:
                c = _mix(c, _rgb("8a7a50"), 0.6)  # the hoist's rope
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gunport(px, region, rng):
    """A closed red lid in a gold frame, hinged at the top."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 4 or x >= w - 4 or y < 4 or y >= h - 4
            if frame:
                c = _rgb("d9a521") if (x + y) % 5 else _rgb("b8891a")
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    c = _rgb("6e5210")
            else:
                c = _scale(_rgb("b4262a"), 1.0 + 0.05 * math.sin(x * 0.7) - 0.1 * (y > h - 8))
                if y in (6, 7) or y in (h - 9, h - 8):
                    c = _rgb("2c2c30")   # iron straps
                if 14 <= x <= 17 and 16 <= y <= 19:
                    c = _rgb("5a5a5e")   # ring
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gold_band(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("e0ad2a"), _rgb("c28f18"), 0.5 + 0.5 * math.sin(x * 0.5 + y))
            if y in (0, h - 1):
                c = _rgb("6e5210")
            elif y in (1, h - 2):
                c = _rgb("f2c64a")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _strake(px, region, tones, seam, rng, grain=0.05, nails=True):
    """One hull strake (stretched on each board): a dark seam along the top and the bottom, a light
    edge under the upper seam, the grain along the plank, a few nail heads."""
    u, v, w, h = region
    seam = _rgb(seam)
    tones = [_rgb(t) for t in tones]
    base = rng.choice(tones)
    f1, p1 = rng.uniform(0.1, 0.25), rng.uniform(0, 6.28)
    for y in range(h):
        for x in range(w):
            if y == 0 or y == h - 1:
                c = seam
            else:
                k = 1.0 + grain * math.sin(x * f1 + p1 + y * 1.3) + (0.07 if y == 1 else 0) - (0.06 if y == h - 2 else 0)
                # a slow tone drift along the strake (several planks end to end, no hard joints)
                k *= 1.0 + 0.04 * math.sin(x * 0.2 + p1)
                c = _scale(base, k)
                if nails and y in (3, h - 4) and x % 16 == 7:
                    c = _scale(c, 0.72)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gunport_open(px, region, rng):
    """An open gun port: gold frame round a dark opening (the gun's muzzle stands in it)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 4 or x >= w - 4 or y < 3 or y >= h - 4
            if frame:
                c = _rgb("e0ac26") if (x + y) % 5 else _rgb("bf8f1a")
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    c = _rgb("6e5210")
            else:
                d = min(x - 4, w - 5 - x, y - 3, h - 5 - y)
                c = _mix(_rgb("0c0a08"), _rgb("2a2218"), 0.5 if d < 2 else 0.0)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _gunport_lid(px, region, rng):
    """The raised red lid: red boards with two dark iron straps and the hinge line."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("b8282c"), 1.0 + 0.05 * math.sin(x * 0.6) + (0.06 if y < 2 else 0) - (0.1 if y >= h - 2 else 0))
            if y == 0:
                c = _rgb("4a3a30")   # the hinge
            if x in (7, 8, w - 9, w - 8) and 1 < y < h - 1:
                c = _rgb("2c2c30")   # iron straps
            if x == 0 or x == w - 1:
                c = _rgb("5a1416")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _castle_panel(px, region, rng):
    """The stern castle: a royal blue panel of vertical boards in a thin gold frame."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = (x // 6) % 3
            c = _scale(_rgb(("2152b8", "1d4aa9", "2558c4")[k]), 1.0 + 0.04 * math.sin(y * 0.4 + x))
            if x % 6 == 5:
                c = _rgb("132f6e")
            if y < 2 or y >= h - 2 or x < 2 or x >= w - 2:
                c = _rgb("d9a521") if (x + y) % 3 else _rgb("f0c84e")
            if y in (0, h - 1):
                c = _rgb("7a5a12")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _taffrail(px, region, rng):
    """Gold carved taffrail: scrolls (dark S curls) between gold edge lines."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("e2ae2a"), _rgb("c08c18"), abs(y - h / 2) / (h / 2))
            fx, fy = (x % 16) / 16.0, y / h
            # an S scroll every 16 px
            s = math.sin(fx * 2 * math.pi) * 0.28 + 0.5
            if 0.2 < fy < 0.8 and abs(fy - s) < 0.1:
                c = _rgb("7a5a12")
            if y in (1, h - 2):
                c = _rgb("f4cc52")
            if y in (0, h - 1):
                c = _rgb("6e5210")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gold(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("dcaa26"), _rgb("c6931c"), 0.5 + 0.5 * math.sin(x * 0.7 + y * 0.4))
            if (x * 3 + y * 5) % 17 == 0:
                c = _rgb("f0c84e")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _carving(px, region, rng):
    """Gold moulding with a row of dark acanthus-like notches."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("dcaa26"), _rgb("b8861a"), abs(y - h / 2) / (h / 2))
            k = (x % 8)
            if 4 <= y <= h - 5 and k in (0, 1) or (y in (3, h - 4) and k < 4):
                c = _rgb("7a5a12")
            if y in (0, h - 1):
                c = _rgb("6e5210")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _stern_lily(px, region, rng):
    """A gold fleur-de-lis on a royal blue field (the stern emblem)."""
    u, v, w, h = region
    mask = fleur_de_lis_mask(w - 8, h - 4, cell=2)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("1f4fb5"), 1.0 + 0.04 * math.sin(x * 0.8 + y * 0.6))
            if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                c = _rgb("d9a521")
            elif 4 <= x < w - 4 and 2 <= y < h - 2 and mask.getpixel((x - 4, y - 2)):
                c = _mix(_rgb("e6b532"), _rgb("c28f18"), 0.5 * ((x + y) % 2))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _cabin_wall(px, region, rng):
    """The captain's cabin: dark panelling, a gold chair rail and a gold cornice, lower panels."""
    u, v, w, h = region
    col = _rgb("5a3a20")
    for x in range(w):
        if x % 8 == 0:
            col = _scale(_rgb(rng.choice(("5e3c22", "553620", "66422a", "5a3a1e"))), rng.uniform(0.94, 1.06))
        for y in range(h):
            if x % 8 == 7:
                c = _rgb("2a1a0d")
            else:
                c = _scale(col, 1.0 + 0.05 * math.sin(y * 0.35 + x))
            if y in (2, 3) or 38 <= y <= 40:
                c = _rgb("c9981f") if (x + y) % 7 else _rgb("e0b230")   # cornice and chair rail
            elif y > 40 and (x % 16 in (2, 13) or y in (44, 60)):
                c = _scale(c, 0.8)  # panel mouldings
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _cannon_tex(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("4a4238"), _rgb("6a5a3c"), 0.5 + 0.5 * math.sin(y * 0.6))
            if (x * 5 + y) % 13 == 0:
                c = _scale(c, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def make_texture(path, tris=None):
    """The main atlas. tris: the triangle (region fractions) of the jibs, as the model cuts them (unused here:
    the jibs live in the sail atlas)."""
    rng = random.Random(1789)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    _planks(px, R["hull_blue"], ("2152b8", "1d4aa9", "2558c4", "1f4eb0"), "0f2a66", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["hull_blue2"], ("2050b2", "1b47a2", "2a5bc2", "234fae"), "0f2a66", rng, plank_h=4, joints=3, grain=0.06,
            worn=0.05, worn_col="5a6f9a")
    _gold(px, R["gold"], rng)
    _gold_band(px, R["gold_band"], rng)
    _planks(px, R["hull_brown"], ("3e2616", "36200f", "462c1a", "3a2414"), "1a0f06", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["wood_dark"], ("5a3a20", "4e321c", "634126", "553620"), "24170c", rng)
    _planks(px, R["wood_mid"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng)
    _planks(px, R["wood_light"], ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", rng)
    _planks(px, R["rail"], ("d9a521", "c8941c"), "7a5a12", rng, plank_h=8, joints=1)
    _planks(px, R["mast"], ("a87a3a", "9a6e32", "b48542"), "5a401c", rng, plank_h=4, joints=0, grain=0.1)
    _planks(px, R["deck"], ("8a6340", "7d5838", "936a44", "80603e", "6f5234"), "3a2716", rng, plank_h=4, joints=2)
    _planks(px, R["dark_wood"], ("4a2f1a", "40281a"), "1e140a", rng, plank_h=4, joints=1)
    _planks(px, R["cloth_roll"], ("8db4e2", "7fa9dc", "98bce6"), "5f82b2", rng, plank_h=4, joints=0)
    _carving(px, R["carving"], rng)
    _strake(px, R["strake_lo"], ("1b44a4", "1a41a0", "1e49ad"), "0b1f52", rng)
    _strake(px, R["strake_mid"], ("2152b8", "2354bc", "1f4fb4"), "0d2459", rng)
    _strake(px, R["strake_hi"], ("2a5ccb", "2858c6", "2d61d0"), "0f2a66", rng)
    _strake(px, R["strake_brown"], ("3e2616", "3a2414"), "160c04", rng, grain=0.07)
    _strake(px, R["strake_brown2"], ("46291a", "402617"), "160c04", rng, grain=0.07)
    _gunport_open(px, R["gunport_open"], rng)
    _gunport_lid(px, R["gunport_lid"], rng)
    _castle_panel(px, R["castle_panel"], rng)
    _taffrail(px, R["taffrail"], rng)
    ct._rope(px, R["rope"], "a88e62", "6e5a3a", rng)
    ct._rope(px, R["rope_light"], "8a7250", "5a4830", rng)
    ct._rope(px, R["rope_dark"], "3a3028", "1e1812", rng)
    _fill(px, R["iron"], "3a3b3e", rng, 6)
    _fill(px, R["bronze"], "b08a2e", rng, 8)
    _fill(px, R["glow"], "ffd27a", rng, 4)
    _fill(px, R["glass"], "b8d4dc", rng, 4)
    _fill(px, R["red_paint"], "a8262a", rng, 6)
    _fill(px, R["white_paint"], "ece8dc", rng, 5)
    _fill(px, R["navy"], "17244c", rng, 4)
    _fill(px, R["end_grain"], "8a6a42", rng, 10)
    _fill(px, R["bore"], "141210", rng, 3)
    _cannon_tex(px, R["cannon"], rng)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    ct._window(px, R["glow_window"], rng, lit=True)
    ct._window(px, R["window_in"], rng, lit=False)
    ct._door(px, R["door"], rng)
    ct._grating(px, R["grating"], rng)
    _gunport(px, R["gunport"], rng)
    _tricolour(px, R["flag"], rng)
    ct._compass(px, R["compass"], rng)
    ct._chart(px, R["chart"], rng)
    ct._books(px, R["books"], rng)
    ct._painting(px, R["painting"], rng)
    _stern_lily(px, R["stern_lily"], rng)
    _cabin_wall(px, R["wall_wood"], rng)
    _planks(px, R["floor"], ("6e4a2a", "634226", "7a5230", "5a3c22"), "2b1b0e", rng, plank_h=8, joints=2)
    ct._ceil(px, R["ceil"], rng)
    _planks(px, R["hold_floor"], ("5e4228", "553b24", "684a2e"), "241810", rng, plank_h=8, joints=3, worn=0.04, worn_col="3a3a30")
    _planks(px, R["hold_wall"], ("4e3420", "5a3c24", "46301c"), "1e140a", rng, plank_h=8, joints=2)
    _blocks(px, R["wall_stone"], ("7f7a72", "8a857c", "736e66"), "3e3b36", rng, bw=16, bh=8)
    ct._carpet(px, R["carpet"], rng, border="c9981f", field="1f3f9e", centre="162c6e")
    ct._rug(px, R["rug"], rng)
    ct._boat(px, R["boat"], rng)
    ct._weave(px, R["sack"], rng, "a98b5e", "8e7349")
    ct._weave(px, R["canvas"], rng, "ab9a76", "9c8a66", period=1)
    _fill(px, R["linen"], "e6dfcc", rng, 4)
    _blocks(px, R["ham"], ("9a4632", "8a3c2a"), "5a2418", rng, bw=8, bh=4)
    _fill(px, R["bedding"], "1f3f9e", rng, 8)
    img.save(path)
    return img


def make_sail_texture(path, tris=None):
    rng = random.Random(1643)
    img = Image.new("RGBA", (SAIL_SIZE, SAIL_SIZE), (0, 0, 0, 0))
    px = img.load()
    for name, (cols, rows) in SAIL_CELLS.items():
        tri = None
        if name == "jib":
            tri = (tris or {}).get(name) or [(0.0, 0.0), (1.0, 0.0), (0.62, 1.0)]
        # the jibs are whiter than the square sails on the reference
        _sail(px, SAIL_REGIONS[name], cols, rows, rng, emblem=name in EMBLEM_SAILS, tri=tri, whiter=0.35 if name == "jib" else 0.0)
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 icon: the blue hull with its gold bands, three masts with pale blue square sails (a navy
    mark on the main topsail), a tricolour at the fore masthead."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    blue, gold, brown = _rgb("2152b8"), _rgb("d9a521"), _rgb("3e2616")
    pale, pale2, mast, navy = _rgb("a9c4e6"), _rgb("c0d4ee"), _rgb("9a6e32"), _rgb("17244c")
    for x in range(1, 15):
        for y in range(10, 15):
            if y == 14 and (x < 3 or x > 13):
                continue
            c = gold if y in (10, 13) else (brown if y == 14 else blue)
            px[x, y] = c + (255,)
    for x in range(0, 3):
        px[x, 9 - x] = mast + (255,)  # bowsprit
    for mx, top, w in ((5, 1, 2), (10, 0, 2), (14, 5, 1)):
        for y in range(top, 10):
            px[mx, y] = mast + (255,)
    for y, x0, x1 in ((2, 4, 6), (3, 4, 6), (5, 3, 7), (6, 3, 7), (8, 3, 7), (9, 3, 7)):
        for x in range(x0, x1 + 1):
            if x != 5:
                px[x, y] = (pale if (x + y) % 3 else pale2) + (255,)
    for y, x0, x1 in ((1, 9, 11), (2, 9, 11), (4, 8, 12), (5, 8, 12), (7, 8, 12), (8, 8, 12), (9, 8, 12)):
        for x in range(x0, x1 + 1):
            if x != 10:
                px[x, y] = (pale if (x + y) % 3 else pale2) + (255,)
    px[9, 4] = navy + (255,)
    px[11, 5] = navy + (255,)
    for y in (6, 7, 8):
        px[13, y] = pale + (255,)
    px[6, 1] = _rgb("1f3f9e") + (255,)
    px[7, 1] = _rgb("f0ede6") + (255,)
    px[8, 1] = _rgb("c8262a") + (255,)
    img.save(path)


if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", "/tmp/claude-0/agent_frigate")
    os.makedirs(out, exist_ok=True)
    make_texture(os.path.join(out, "blue_frigate.png"))
    make_sail_texture(os.path.join(out, "blue_frigate_sails.png"))
    make_item_icon(os.path.join(out, "icon.png"))
    fleur_de_lis_mask(76, 88).resize((76 * 4, 88 * 4), Image.NEAREST).save(os.path.join(out, "lily.png"))
    print("ok")
