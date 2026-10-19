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

SIZE = 512

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
    "door":        (208, 32, 32, 32),  # watertight door: riveted steel, thick frame, wheel painted
    "murk":        (416, 96, 8, 8),
    "seam":        (448, 96, 16, 8),   # a riveted butt strap of the hull plating (tiled along the seams)    # plain white: the murky sea behind the glass (tinted by the renderer, see ShipRenderer)
    "door_leaf":   (192, 96, 32, 64),  # one leaf of a 2 block door (1 x 2): mahogany, bronze straps, porthole, panels
    # rooms: luxury (salon, library, dining room, Aronnax), austere and technical
    "wall_lux":    (0, 64, 32, 32),    # dark wood panelling, gilded band, red fabric above
    "floor_lux":   (32, 64, 32, 32),   # herringbone parquet
    "ceil_lux":    (64, 64, 32, 32),   # coffered dark wood with gilded rosettes
    "carpet":      (96, 64, 32, 32),   # red runner with a gold border
    "wall_steel":  (128, 64, 32, 32),  # riveted steel, copper band
    "floor_grate": (160, 64, 32, 32),  # iron grating
    "ceil_steel":  (192, 64, 32, 32),  # steel with ribs and pipes
    "hull_light":  (224, 64, 32, 32),  # lighter copper (casing, wheelhouse)
    "salon_frame": (0, 96, 32, 16),
    # furniture made for the Nautilus (what the decoration mods do not have)
    "gold":        (256, 0, 16, 16),
    "silver":      (272, 0, 16, 16),   # organ pipes
    "wax":         (288, 0, 16, 16),
    "pearl":       (304, 0, 16, 16),
    "shell":       (320, 0, 16, 16),
    "coral_red":   (336, 0, 16, 16),
    "coral_pink":  (352, 0, 16, 16),
    "coral_orange": (368, 0, 16, 16),
    "gauge":       (384, 0, 16, 16),   # dial with a needle
    "copper":      (400, 0, 16, 16),
    "coil":        (416, 0, 16, 16),   # copper winding
    "keys":        (432, 0, 32, 8),    # organ keyboard
    "bedding":     (464, 0, 16, 16),
    "helmet":      (480, 0, 16, 16),   # diving helmet window
    "red_velvet":  (256, 16, 32, 32),
    "green_leather": (288, 16, 32, 32),
    "books":       (320, 16, 64, 32),
    "organ_wood":  (384, 16, 32, 32),
    "battery":     (416, 16, 16, 32),
    "suit":        (432, 16, 32, 32),  # diving suit canvas
    "rug":         (256, 48, 64, 64),  # oriental rug
    "painting_sea": (320, 48, 64, 48),
    "painting_storm": (384, 48, 64, 48),
    "portrait":    (448, 48, 32, 48),
    "chart":       (256, 112, 64, 48),
    "boat_wood":   (320, 112, 64, 32),
    "plank_light": (384, 112, 32, 32),
    # translucent effects: the projector beam fading away (4 lengths), the water of the airlock
    "beam0":       (464, 16, 16, 16),
    "beam1":       (480, 16, 16, 16),
    "beam2":       (496, 16, 16, 16),
    "beam3":       (464, 32, 16, 16),
    "water":       (480, 32, 16, 16),
    "glassfx":     (496, 32, 16, 16),  # pale sea-green glass, see-through
    # warmer rooms (cabins, corridors, kitchen, machinery)
    "wall_wood":   (32, 96, 32, 32),   # copper plate above, brass rail, dark walnut planks below
    "floor_tile":  (64, 96, 32, 32),   # terracotta and slate tiles
    "wall_engine": (96, 96, 32, 32),   # bronze plates with copper pipes
    "ceil_wood":   (128, 96, 32, 32),  # dark planks between beams
    "globe":       (160, 96, 32, 32),  # map of the world for the globe (longitude across, latitude down)
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


def _hull_plates(px, region, base, seam, rivet, rng, wear=0.02):
    """Hull plating for a panel stretched over a gore: one large plate per panel, its light upper
    edge and shadowed lower edge, a soft seam, a row of small rivets along the edges, faint patina."""
    u, v, w, h = region
    n1 = _noise(w, h, 4, rng)
    n2 = _noise(w, h, 8, rng)
    tone = _jitter(base, rng, 6)
    for y in range(h):
        for x in range(w):
            k = 0.94 + 0.1 * (1 - y / h) + 0.08 * n1[y][x] + 0.03 * n2[y][x]
            c = tuple(q * k for q in tone)
            if x == 0 or y == 0:
                c = _mix(c, seam, 0.55)
            elif x == 1 or y == 1:
                c = _shade(c, 1.1)
            elif x == w - 1 or y == h - 1:
                c = _shade(c, 0.84)
            elif (x == 3 and y % 6 == 3) or (y == 3 and x % 6 == 3) or (x == w - 4 and y % 6 == 3):
                c = _mix(c, rivet, 0.6)
            if wear and n2[y][x] > 0.85:
                c = _mix(c, _rgb("4f6b52"), 0.25 * (n2[y][x] - 0.85) / 0.15)
            px[u + x, v + y] = tuple(max(0, min(255, int(q))) for q in c) + (255,)


def make_texture(path):
    rng = random.Random(1870)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    _hull_plates(px, R["plate"], _rgb("7e4a2a"), _rgb("2e1a0e"), _rgb("c48a52"), rng, wear=0.02)
    _hull_plates(px, R["plate_dark"], _rgb("4e3020"), _rgb("1e120a"), _rgb("8a6040"), rng, wear=0.035)
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
    _paint_rooms(img, px, rng)
    _paint_furniture(img, px, rng)
    _paint_effects(px, rng)
    _paint_smooth_rooms(px, rng)
    _paint_door_leaf(px, rng)
    _paint_finish(px, rng)
    img.save(path)


def _paint_effects(px, rng):
    for k, alpha in enumerate((96, 70, 44, 20)):
        u, v, w, h = REGIONS["beam%d" % k]
        for y in range(h):
            for x in range(w):
                a = alpha + rng.randint(-4, 4)
                px[u + x, v + y] = (255, 246, 205, max(0, a))
    u, v, w, h = REGIONS["glassfx"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (150, 205, 210, 60 if (x + y) % 7 else 95)
    u, v, w, h = REGIONS["water"]
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin(x * 0.8 + math.sin(y * 0.6) * 2.0)
            c = (int(28 + 30 * t), int(80 + 40 * t), int(140 + 40 * t))
            px[u + x, v + y] = c + (150,)


def _paint_rooms(img, px, rng):
    R = REGIONS
    d = ImageDraw.Draw(img)
    # watertight door
    u, v, w, h = R["door"]
    _riveted(px, (u, v, w, h), _rgb("4d4743"), _rgb("1f1d1c"), _rgb("b8913c"), rng, pw=32, ph=32)
    d.rectangle((u, v, u + w - 1, v + h - 1), outline=_rgb("2a2624") + (255,), width=3)
    d.ellipse((u + 9, v + 9, u + 22, v + 22), outline=_rgb("c9a24a") + (255,), width=2)
    d.line((u + 15, v + 9, u + 15, v + 22), fill=_rgb("c9a24a") + (255,))
    d.line((u + 9, v + 15, u + 22, v + 15), fill=_rgb("c9a24a") + (255,))
    # luxury panelling: dark wood panels in the lower two thirds, a gilded rail, red damask above
    u, v, w, h = R["wall_lux"]
    for y in range(h):
        for x in range(w):
            if y < 10:
                c = _rgb("6e1f22") if (x + 2 * y) % 7 else _rgb("8a2c2c")
                if (x % 8 == 4 and y % 5 == 2):
                    c = _rgb("a8803a")
            elif y < 12:
                c = _rgb("d8b25a") if y == 10 else _rgb("8a6a2a")
            else:
                fx, fy = x % 16, (y - 12) % 20
                c = _rgb("3e2414")
                if fx in (0, 15) or fy in (0, 19):
                    c = _rgb("2a170c")
                elif fx in (2, 13) or fy in (2, 17):
                    c = _rgb("5a3820")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # herringbone parquet
    u, v, w, h = R["floor_lux"]
    for y in range(h):
        for x in range(w):
            a = ((x + y) // 4) % 2
            c = _rgb("6a4024") if ((x // 4 + y // 4) % 2 == 0) == bool(a) else _rgb("4e2e18")
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                c = _rgb("2e1a0c")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # coffered ceiling
    u, v, w, h = R["ceil_lux"]
    for y in range(h):
        for x in range(w):
            fx, fy = x % 16, y % 16
            c = _rgb("3a2414")
            if fx < 2 or fy < 2:
                c = _rgb("24160c")
            elif 6 <= fx <= 9 and 6 <= fy <= 9:
                c = _rgb("c9a24a") if (fx + fy) % 2 == 0 else _rgb("8a6a2a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # red runner with a gold border
    u, v, w, h = R["carpet"]
    for y in range(h):
        for x in range(w):
            c = _rgb("8a1e1e")
            if x in (2, 3, w - 4, w - 3):
                c = _rgb("c9a24a")
            elif x < 2 or x > w - 3:
                c = _rgb("4a1010")
            elif (x * 3 + y) % 11 == 0:
                c = _rgb("6e1616")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    _riveted(px, R["wall_steel"], _rgb("76624e"), _rgb("3a2c20"), _rgb("c49c64"), rng, pw=16, ph=16)
    u, v, w, h = R["wall_steel"]
    for y in range(13, 16):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("b8753e") if y == 14 else _rgb("7a4a26"), rng, 4) + (255,)
    u, v, w, h = R["floor_grate"]
    for y in range(h):
        for x in range(w):
            c = _rgb("1e1813") if (x % 4 == 0 or y % 4 == 0) else _rgb("4a3e33")
            if x % 16 == 0 or y % 16 == 0:
                c = _rgb("7a5e3e")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    u, v, w, h = R["ceil_steel"]
    _riveted(px, (u, v, w, h), _rgb("3e3228"), _rgb("1c1510"), _rgb("7a6248"), rng, pw=16, ph=16)
    for x in range(w):
        for y in (6, 7, 22, 23):
            px[u + x, v + y] = _jitter(_rgb("7a4a26") if y % 2 else _rgb("a8693a"), rng, 4) + (255,)  # copper pipes
    _paint_warm_rooms(px, rng)
    _hull_plates(px, R["hull_light"], _rgb("8a5632"), _rgb("2e1a0e"), _rgb("d09a62"), rng, wear=0.02)
    _fill(img, R["salon_frame"], _rgb("b8913c"), rng, 8)


def _paint_warm_rooms(px, rng):
    R = REGIONS
    # wood panelling: riveted copper plate above, a brass rail, dark walnut planks below
    u, v, w, h = R["wall_wood"]
    _riveted(px, (u, v, w, 9), _rgb("8a5a36"), _rgb("3a2414"), _rgb("d8a862"), rng, pw=16, ph=9)
    for y in range(9, h):
        for x in range(w):
            if y in (9, 10):
                c = _rgb("e0b860") if y == 9 else _rgb("8a6a2a")
            else:
                plank = x // 4
                base = _rgb("4a2c18") if plank % 2 else _rgb("553420")
                c = base
                if x % 4 == 0:
                    c = _rgb("24140a")
                elif (y * 7 + plank * 13) % 9 == 0:
                    c = _shade(base, 0.82)
                if y == h - 1:
                    c = _rgb("2a180c")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # terracotta and slate tiles
    u, v, w, h = R["floor_tile"]
    for y in range(h):
        for x in range(w):
            c = _rgb("9a4a2a") if (x // 8 + y // 8) % 2 == 0 else _rgb("3a3430")
            if x % 8 == 0 or y % 8 == 0:
                c = _rgb("1e1a16")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # machinery: bronze plates, two copper pipes running up
    u, v, w, h = R["wall_engine"]
    _riveted(px, (u, v, w, h), _rgb("6e5640"), _rgb("2e2218"), _rgb("c49a5e"), rng, pw=16, ph=16)
    for x0 in (5, 21):
        for y in range(h):
            for dx, col in ((0, "6e3a1e"), (1, "c87a44"), (2, "e8a06a"), (3, "8a4a26")):
                px[u + x0 + dx, v + y] = _jitter(_rgb(col), rng, 3) + (255,)
            if y % 12 == 3:
                for dx in range(-1, 5):
                    px[u + x0 + dx, v + y] = _rgb("d8b25a") + (255,)
    # dark planks between beams
    u, v, w, h = R["ceil_wood"]
    for y in range(h):
        for x in range(w):
            c = _rgb("3a2414") if (y // 4) % 2 else _rgb("33200f")
            if y % 4 == 0:
                c = _rgb("1e1208")
            if x % 16 in (0, 1, 2):
                c = _rgb("24160a") if x % 16 else _rgb("5a3a1e")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


# ---------------------------------------------------------------- smooth interior materials
def _noise(w, h, cells, rng):
    """Tileable value noise (bilinear), values 0..1."""
    grid = [[rng.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            fx, fy = x * cells / w, y * cells / h
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0 % cells][x0 % cells]
            b = grid[y0 % cells][(x0 + 1) % cells]
            c = grid[(y0 + 1) % cells][x0 % cells]
            d = grid[(y0 + 1) % cells][(x0 + 1) % cells]
            out[y][x] = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return out


def _mix(a, b, t):
    return tuple(int(round(p + (q - p) * t)) for p, q in zip(a, b))


def _put(px, u, v, x, y, c):
    px[u + x, v + y] = tuple(max(0, min(255, int(q))) for q in c) + (255,)


def _smooth_metal(px, region, top, bottom, rng, rail=None, rail_y=None, seam_every=32, wainscot=None):
    """Painted metal: a soft vertical gradient (lighter at the top), faint mottling, a soft seam
    every `seam_every` px with a few small rivets, an optional darker wainscot and a brass rail."""
    u, v, w, h = region
    n1 = _noise(w, h, 4, rng)
    n2 = _noise(w, h, 8, rng)
    for y in range(h):
        for x in range(w):
            t = y / (h - 1)
            c = _mix(top, bottom, t)
            if wainscot and y >= wainscot[0]:
                c = _mix(c, wainscot[1], 0.55)
            k = 0.93 + 0.1 * n1[y][x] + 0.04 * n2[y][x]
            c = tuple(q * k for q in c)
            if seam_every and x % seam_every == 0:
                c = tuple(q * 0.78 for q in c)
            elif seam_every and x % seam_every == 1:
                c = tuple(q * 1.08 for q in c)
            if seam_every and x % seam_every == 3 and y % 8 == 4:
                c = tuple(q * 1.25 for q in c)  # small rivet head along the seam
            if wainscot and y == wainscot[0]:
                c = tuple(q * 0.75 for q in c)
            _put(px, u, v, x, y, c)
    if rail:
        for y in range(rail_y, rail_y + 2):
            for x in range(w):
                c = _mix(rail, (255, 240, 190), 0.35) if y == rail_y else rail
                _put(px, u, v, x, y, tuple(q * (0.95 + 0.08 * n2[y][x]) for q in c))


def _wood_grain(px, region, base, dark, rng, horizontal=True, plank=None):
    u, v, w, h = region
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            a, b = (x, y) if horizontal else (y, x)
            g = 0.5 + 0.5 * math.sin(b * 2 * math.pi * 7 / 32 + 3.0 * n[y][x] + math.sin(a * 2 * math.pi / 32) * 1.5)
            c = _mix(base, dark, 0.25 + 0.35 * g)
            if plank and b % plank == 0:
                c = _mix(c, dark, 0.6)
            _put(px, u, v, x, y, c)


def _paint_door_leaf(px, rng):
    """One leaf of the doors of the rooms (1 x 2 blocks, 32 x 64 px, drawn upright): varnished
    mahogany with a vertical grain, a riveted bronze strap all round, a round porthole with a bolted
    brass collar and a glint on its glass, a brass band, two raised panels with gilded mouldings and
    bevels, a brass kick plate at the foot."""
    u, v, w, h = REGIONS["door_leaf"]
    _wood_grain(px, (u, v, w, h), _rgb("7a3a22"), _rgb("2e120a"), rng, horizontal=False)
    bronze, bronze_dark, brass, gold = _rgb("8a5a2e"), _rgb("4a2e16"), _rgb("c9a24a"), _rgb("f0d27a")
    n = _noise(w, h, 4, rng)

    def put(x, y, c):
        _put(px, u, v, x, y, tuple(q * (0.94 + 0.1 * n[y][x]) for q in c))

    # raised panels: lighter field, bevel lit from the top left, a gilded moulding round them
    for y0, y1 in ((27, 44), (47, 57)):
        x0, x1 = 6, w - 7
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if y in (y0, y1) or x in (x0, x1):
                    c = gold if (y == y0 or x == x0) else brass
                elif y == y0 + 1 or x == x0 + 1:
                    c = _mix(_rgb("8a4a2c"), (255, 220, 180), 0.15)
                elif y == y1 - 1 or x == x1 - 1:
                    c = _rgb("2a1008")
                else:
                    continue
                put(x, y, c)
    # bronze strap round the leaf, rivets along it
    for y in range(h):
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if edge < 3:
                c = bronze_dark if edge == 0 else _mix(bronze, (255, 230, 180), 0.2) if edge == 1 else bronze
                if edge == 1 and (x + y) % 5 == 0:
                    c = gold
                put(x, y, c)
    # brass band across the middle, and the kick plate
    for y in range(22, 25):
        for x in range(3, w - 3):
            put(x, y, gold if y == 22 else brass if y == 23 else _rgb("7a5a20"))
    for y in range(59, 61):
        for x in range(3, w - 3):
            put(x, y, brass if y == 59 else _rgb("8a6a2a"))
    for x in range(5, w - 4, 4):
        put(x, 23, _rgb("fff0b0"))
    # porthole: brass collar with 8 bolts, green-blue glass with a glint
    cx, cy, r = w / 2 - 0.5, 12.0, 7.5
    for y in range(3, 22):
        for x in range(3, w - 3):
            d = math.hypot(x - cx, y - cy)
            if d <= r - 2:
                t = d / (r - 2)
                c = _mix(_rgb("2a5a60"), _rgb("0e2228"), t)
                if 1.5 < (x - cx + 3) ** 2 + (y - cy + 3) ** 2 < 6:
                    c = _rgb("b8e8e8")
                put(x, y, c)
            elif d <= r:
                c = gold if (y - cy) < 0 and d < r - 0.8 else brass if d < r - 0.8 else _rgb("6a4a18")
                put(x, y, c)
    for k in range(8):
        a = 2 * math.pi * k / 8
        put(int(round(cx + math.cos(a) * (r - 1))), int(round(cy + math.sin(a) * (r - 1))), _rgb("fff0b0"))


def _polished(px, region, light, mid, dark, rng, period=None, brushed=0.06):
    """Polished metal that tiles: a soft diagonal sheen (light bands on a darker body), fine brushed
    streaks along x, no blotches."""
    u, v, w, h = region
    period = period or w
    n = _noise(w, h, 4, rng)
    rows = [rng.random() for _ in range(h)]
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin(2 * math.pi * (x + y) / period + 1.2 * (n[y][x] - 0.5))
            t = 0.3 + 0.5 * t  # a gentle sheen, not stripes
            c = _mix(dark, mid, t / 0.55) if t < 0.55 else _mix(mid, light, (t - 0.55) / 0.45)
            k = 1.0 + brushed * (rows[y] - 0.5) + 0.04 * (n[y][x] - 0.5)
            _put(px, u, v, x, y, tuple(q * k for q in c))


def _parquet(px, region, light, dark, rng, cell=8):
    """Basket-weave parquet: square cells of two planks each, alternately along x and along z, a
    grain along each plank, dark joints, each plank its own tone; tiles."""
    u, v, w, h = region
    n = _noise(w, h, 8, rng)
    tones = {}
    for y in range(h):
        for x in range(w):
            cx, cy = x // cell, y // cell
            along_x = (cx + cy) % 2 == 0
            a, b = (x % cell, y % cell) if along_x else (y % cell, x % cell)
            plank = (cx, cy, b // (cell // 2))
            if plank not in tones:
                tones[plank] = 0.85 + 0.3 * rng.random()
            g = 0.5 + 0.5 * math.sin((a * 0.9 + b * 3.1) + 4.0 * n[y][x])
            c = _mix(light, dark, 0.2 + 0.45 * g)
            c = tuple(q * tones[plank] for q in c)
            if b % (cell // 2) == 0 or a == 0:
                c = _mix(c, (20, 10, 4), 0.6)
            elif b % (cell // 2) == 1:
                c = tuple(q * 1.08 for q in c)
            _put(px, u, v, x, y, c)


def _fabric(px, region, base, dark, rng, folds=True, crackle=False):
    """Velvet / leather: a soft nap that changes with the light, vertical folds (curtains, backs),
    leather with fine creases and a sheen; tiles."""
    u, v, w, h = region
    n1 = _noise(w, h, 4, rng)
    n2 = _noise(w, h, 16, rng)
    for y in range(h):
        for x in range(w):
            t = 0.55 + 0.3 * (n1[y][x] - 0.5)
            if folds:
                t += 0.22 * math.sin(2 * math.pi * x / w * 2 + 0.8 * n1[y][x])
            c = _mix(dark, base, max(0.0, min(1.0, t + 0.25)))
            c = tuple(q * (0.96 + 0.08 * n2[y][x]) for q in c)
            if crackle and abs(n2[y][x] - 0.5) < 0.03:
                c = _shade(c, 0.8)
            if crackle and n1[y][x] > 0.72:
                c = _mix(c, (255, 240, 220), 0.12 * (n1[y][x] - 0.72) / 0.28)
            _put(px, u, v, x, y, c)


def _skin(px, region, base, rng, patina=0.0):
    """Smooth copper skin for the hull, the casing and the wheelhouse: no seams or rivets that would
    repeat on every panel (the panels then read as one smooth curved surface), only a soft, slow
    mottling and some verdigris; tiles."""
    u, v, w, h = region
    n1 = _noise(w, h, 2, rng)
    n2 = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            k = 0.95 + 0.07 * n1[y][x] + 0.03 * n2[y][x]
            c = tuple(q * k for q in base)
            if patina and n2[y][x] > 0.8:
                c = _mix(c, _rgb("4f7a5c"), patina * (n2[y][x] - 0.8) / 0.2)
            _put(px, u, v, x, y, c)


def _paint_hatch(px, rng):
    """Watertight hatch, seen from above or below: a dished steel plate, a raised brass coaming ring,
    six dogs clamping it, a handwheel with spokes in the middle, two hinge straps, rivets."""
    u, v, w, h = REGIONS["hatch"]
    n = _noise(w, h, 4, rng)
    cx = cy = (w - 1) / 2
    steel, steel_l, steel_d = _rgb("5a5550"), _rgb("8a847c"), _rgb("2a2724")
    brass, gold, brass_d = _rgb("c9a24a"), _rgb("f0d27a"), _rgb("7a5a20")
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            c = _mix(steel_l, steel, min(1.0, d / 14))  # dished: lighter in the middle
            c = tuple(q * (0.94 + 0.1 * n[y][x]) for q in c)
            if min(x, y, w - 1 - x, h - 1 - y) == 0:
                c = steel_d
            elif min(x, y, w - 1 - x, h - 1 - y) == 1:
                c = _shade(steel, 1.15)
            elif min(x, y, w - 1 - x, h - 1 - y) == 2 and (x + y) % 4 == 0:
                c = steel_l
            if 12.2 < d < 14.2:  # coaming ring
                c = gold if (y - cy) < -(x - cx) * 0.3 else brass if d < 13.6 else brass_d
            if 4.5 < d < 6.0:  # handwheel rim
                c = gold if y < cy else brass
            elif d < 1.6:
                c = brass_d
            elif d < 5.0:
                a = math.degrees(math.atan2(y - cy, x - cx)) % 60
                if a < 8 or a > 52:  # six spokes
                    c = brass
            _put(px, u, v, x, y, c)
    for k in range(6):  # the dogs, clamping the coaming
        a = 2 * math.pi * k / 6 + math.pi / 6
        for t in range(-1, 2):
            x = int(round(cx + math.cos(a) * (13.2 + t)))
            y = int(round(cy + math.sin(a) * (13.2 + t)))
            _put(px, u, v, x, y, steel_d if t else _rgb("b8b0a4"))
    for y0 in (8, 22):  # hinge straps on one side
        for y in range(y0, y0 + 3):
            for x in range(2, 9):
                _put(px, u, v, x, y, _rgb("3a3634") if y != y0 else _rgb("6d6660"))


def _paint_finish(px, rng):
    """Last pass over the most seen materials: polished gold, brass and silver, velvet and leather,
    the parquet of the salons and the tiled floors."""
    R = REGIONS
    _paint_hatch(px, rng)
    u, v, w, h = R["murk"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (255, 255, 255, 255)
    _skin(px, R["plate"], _rgb("9a5a30"), rng, patina=0.25)
    _skin(px, R["plate_dark"], _rgb("6e4228"), rng, patina=0.35)
    _skin(px, R["hull_light"], _rgb("a2663a"), rng, patina=0.2)
    u, v, w, h = R["seam"]
    for y in range(h):
        for x in range(w):
            c = _rgb("7a4626")
            if y == 0:
                c = _rgb("b87a48")
            elif y == h - 1:
                c = _rgb("3e2010")
            if y in (3, 4) and x % 4 in (1, 2):
                c = _rgb("d49a62") if y == 3 else _rgb("5a3018")  # rivet heads, lit from above
            _put(px, u, v, x, y, c)
    _polished(px, R["gold"], _rgb("fff2b0"), _rgb("e0b450"), _rgb("9a6e20"), rng)
    _polished(px, R["steel"], _rgb("6a6662"), _rgb("44403c"), _rgb("24211f"), rng, brushed=0.1)
    _polished(px, R["brass"], _rgb("f8e0a0"), _rgb("c99a44"), _rgb("7a5420"), rng)
    # organ pipes: a cylinder's sheen, light down one side, dark down the other, along the pipe
    u, v, w, h = R["silver"]
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.cos(2 * math.pi * (x - 4) / w)
            c = _mix(_rgb("6a6a68"), _rgb("f6f6f2"), t ** 1.5)
            _put(px, u, v, x, y, tuple(q * (0.97 + 0.05 * rng.random()) for q in c))
    _fabric(px, R["red_velvet"], _rgb("b02a30"), _rgb("4e0c10"), rng)
    _fabric(px, R["green_leather"], _rgb("3a7a4a"), _rgb("123018"), rng, folds=False, crackle=True)
    _parquet(px, R["floor_lux"], _rgb("8a5530"), _rgb("3a1e0e"), rng, cell=16)
    # tiled floors: terracotta and slate in a checker, with grout and worn, slightly varied tiles
    u, v, w, h = R["floor_tile"]
    n = _noise(w, h, 8, rng)
    tones = {}
    for y in range(h):
        for x in range(w):
            cx, cy = x // 8, y // 8
            if (cx, cy) not in tones:
                tones[(cx, cy)] = 0.9 + 0.2 * rng.random()
            c = _rgb("a85a38") if (cx + cy) % 2 == 0 else _rgb("4a4a50")
            c = tuple(q * tones[(cx, cy)] * (0.94 + 0.12 * n[y][x]) for q in c)
            if x % 8 == 0 or y % 8 == 0:
                c = _rgb("2a2622")
            elif x % 8 == 1 or y % 8 == 1:
                c = _shade(c, 1.12)
            _put(px, u, v, x, y, c)


def _paint_smooth_rooms(px, rng):
    R = REGIONS
    brass = _rgb("b8913c")
    # corridors and working rooms: warm painted steel, darker wainscot, brass rail
    _smooth_metal(px, R["wall_steel"], _rgb("8a7258"), _rgb("6a5642"), rng, rail=brass, rail_y=19,
                  wainscot=(21, _rgb("4a3a2c")))
    _smooth_metal(px, R["wall"], _rgb("847060"), _rgb("605044"), rng, rail=brass, rail_y=19, wainscot=(21, _rgb("44382e")))
    # machinery: bronze, the copper pipes kept smooth and round
    _smooth_metal(px, R["wall_engine"], _rgb("8a6a4a"), _rgb("5e4630"), rng, seam_every=16)
    u, v, w, h = R["wall_engine"]
    for x0 in (5, 21):
        for y in range(h):
            for dx in range(4):
                shade = 0.65 + 0.55 * math.sin(math.pi * (dx + 0.5) / 4)
                c = tuple(q * shade for q in _rgb("b06a3a"))
                if y % 16 == 7:
                    c = _rgb("d8b25a")
                _put(px, u, v, x0 + dx, y, c)
    # ceilings: smooth plates between soft ribs
    for name, top in (("ceil_steel", "4a3c2e"), ("ceiling", "463a30")):
        u, v, w, h = R[name]
        n = _noise(w, h, 4, rng)
        for y in range(h):
            for x in range(w):
                c = tuple(q * (0.9 + 0.12 * n[y][x]) for q in _rgb(top))
                if y % 16 in (0, 1):
                    c = tuple(q * (0.7 if y % 16 == 0 else 1.2) for q in _rgb("6a5038"))
                if y % 16 == 8 and x % 8 == 4:
                    c = tuple(q * 1.3 for q in c)
                _put(px, u, v, x, y, c)
    # wood panelling: raised panels with bevels, a brass rail, copper-brown frieze above
    u, v, w, h = R["wall_wood"]
    _wood_grain(px, R["wall_wood"], _rgb("6a4228"), _rgb("2e1a0c"), rng, horizontal=False)
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            if y < 8:
                c = tuple(q * (0.92 + 0.1 * n[y][x]) for q in _rgb("7a4e30"))
                _put(px, u, v, x, y, c)
            elif y in (8, 9):
                _put(px, u, v, x, y, _mix(brass, (255, 236, 180), 0.3) if y == 8 else brass)
            else:
                fx, fy = x % 16, y - 10
                if fx in (0, 15) or fy in (0, 21):
                    _put(px, u, v, x, y, tuple(q * 0.62 for q in px[u + x, v + y][:3]))
                elif fx == 1 or fy == 1:
                    _put(px, u, v, x, y, tuple(q * 1.18 for q in px[u + x, v + y][:3]))
                elif fx == 14 or fy == 20:
                    _put(px, u, v, x, y, tuple(q * 0.8 for q in px[u + x, v + y][:3]))
    # luxury rooms: red damask frieze, gilded rail, dark carved panels
    u, v, w, h = R["wall_lux"]
    _wood_grain(px, R["wall_lux"], _rgb("4e2c18"), _rgb("22120a"), rng, horizontal=False)
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            if y < 10:
                dam = 0.5 + 0.5 * math.sin(x * 0.785) * math.sin(y * 0.63 + 0.4)
                c = _mix(_rgb("6e1c20"), _rgb("8e2a2a"), 0.3 + 0.4 * dam)
                c = tuple(q * (0.93 + 0.1 * n[y][x]) for q in c)
                _put(px, u, v, x, y, c)
            elif y < 12:
                _put(px, u, v, x, y, _mix(_rgb("e0bc68"), _rgb("8a6a2a"), y - 10))
            else:
                fx, fy = x % 16, y - 12
                if fx in (0, 15) or fy in (0, 19):
                    _put(px, u, v, x, y, tuple(q * 0.6 for q in px[u + x, v + y][:3]))
                elif fx == 1 or fy == 1:
                    _put(px, u, v, x, y, tuple(q * 1.22 for q in px[u + x, v + y][:3]))
                elif fx in (3, 12) and 3 <= fy <= 16 or fy in (3, 16) and 3 <= fx <= 12:
                    _put(px, u, v, x, y, _mix(px[u + x, v + y][:3], _rgb("c9a24a"), 0.5))
    # coffered ceiling: soft wells, gilded rosettes
    u, v, w, h = R["ceil_lux"]
    _wood_grain(px, R["ceil_lux"], _rgb("4a2c18"), _rgb("24140a"), rng)
    for y in range(h):
        for x in range(w):
            fx, fy = x % 16, y % 16
            c = px[u + x, v + y][:3]
            if fx < 2 or fy < 2:
                c = tuple(q * (0.7 if fx == 0 or fy == 0 else 1.15) for q in c)
            elif math.hypot(fx - 8.5, fy - 8.5) < 2.2:
                c = _mix(_rgb("e0bc68"), _rgb("8a6a2a"), math.hypot(fx - 8.5, fy - 8.5) / 2.2)
            _put(px, u, v, x, y, c)
    # floors: long planks with grain, herringbone in the luxury rooms
    _wood_grain(px, R["floor"], _rgb("6a4428"), _rgb("2e1a0c"), rng, plank=8)
    u, v, w, h = R["floor_lux"]
    for y in range(h):
        for x in range(w):
            a = ((x + y) // 4) % 2
            light = ((x // 4 + y // 4) % 2 == 0) == bool(a)
            c = _rgb("7a4a2a") if light else _rgb("5a3420")
            g = 0.9 + 0.12 * math.sin((x if light else y) * 1.4)
            c = tuple(q * g for q in c)
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                c = tuple(q * 0.72 for q in c)
            _put(px, u, v, x, y, c)
    _wood_grain(px, R["ceil_wood"], _rgb("4a2e1a"), _rgb("22140a"), rng, plank=8)
    u, v, w, h = R["ceil_wood"]
    for y in range(h):
        for x in range(w):
            if x % 16 in (0, 1, 2):
                _put(px, u, v, x, y, _mix(_rgb("5a3a20"), _rgb("2a1a0c"), (x % 16) / 2))
    # tiles: terracotta and slate, glazed, soft grout
    u, v, w, h = R["floor_tile"]
    n = _noise(w, h, 8, rng)
    for y in range(h):
        for x in range(w):
            c = _rgb("a85a34") if (x // 8 + y // 8) % 2 == 0 else _rgb("4a423c")
            c = tuple(q * (0.88 + 0.18 * n[y][x]) for q in c)
            if x % 8 == 0 or y % 8 == 0:
                c = _rgb("2a241e")
            elif x % 8 == 1 or y % 8 == 1:
                c = tuple(q * 1.12 for q in c)
            _put(px, u, v, x, y, c)
    # deck of the casing: bronze tread plate, soft seams and rivets
    u, v, w, h = R["deck"]
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            c = tuple(q * (0.9 + 0.12 * n[y][x]) for q in _rgb("6e5034"))
            if (x + 2 * y) % 8 in (0, 1) and (x // 4 + y // 4) % 2 == 0:
                c = tuple(q * 1.22 for q in c)  # raised tread
            if x % 32 == 0 or y % 32 == 0:
                c = tuple(q * 0.7 for q in c)
            elif (x % 32 == 2 or y % 32 == 2) and (x + y) % 6 == 0:
                c = tuple(q * 1.3 for q in c)
            _put(px, u, v, x, y, c)
    # velvet and leather: smooth, a soft sheen, faint creases
    for name, base, dark in (("red_velvet", "9a2226", "5e1014"), ("green_leather", "2e6a3e", "173a20")):
        u, v, w, h = R[name]
        n = _noise(w, h, 4, rng)
        for y in range(h):
            for x in range(w):
                sheen = 0.5 + 0.5 * math.sin((x + y) * 2 * math.pi / 32 + 2.5 * n[y][x])
                c = _mix(_rgb(dark), _rgb(base), 0.55 + 0.4 * sheen)
                _put(px, u, v, x, y, c)
    # the globe: parchment-coloured oceans, ochre and green continents, graticule
    u, v, w, h = R["globe"]
    n = _noise(w, h, 6, rng)
    for y in range(h):
        for x in range(w):
            land = n[y][x] > 0.58
            c = _mix(_rgb("8a7a4a"), _rgb("5a6a3a"), n[y][x]) if land else _mix(_rgb("d8c8a0"), _rgb("b8a878"), n[y][x])
            if x % 8 == 0 or y % 8 == 0:
                c = tuple(q * 0.82 for q in c)
            _put(px, u, v, x, y, c)
    # diving suit canvas: soft folds, seams
    u, v, w, h = R["suit"]
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            fold = 0.5 + 0.5 * math.sin(y * 2 * math.pi / 8 + 2.0 * n[y][x])
            c = tuple(q * (0.86 + 0.16 * fold) for q in _rgb("a08458"))
            if x % 16 == 0:
                c = tuple(q * 0.78 for q in c)
            _put(px, u, v, x, y, c)
    # carpet: deep red with a small woven diamond pattern, no border (it covers whole floors)
    u, v, w, h = R["carpet"]
    n = _noise(w, h, 4, rng)
    for y in range(h):
        for x in range(w):
            d = (abs((x % 16) - 7.5) + abs((y % 16) - 7.5))
            c = _rgb("8a1e1e")
            if 5.5 < d < 7.0:
                c = _rgb("6e1414")  # a darker woven lozenge
            elif d < 1.6:
                c = _rgb("9a6a2a")  # small dull-gold dot at its centre
            c = tuple(q * (0.92 + 0.12 * n[y][x]) for q in c)
            _put(px, u, v, x, y, c)
    # grating of the machinery floors: softer
    u, v, w, h = R["floor_grate"]
    for y in range(h):
        for x in range(w):
            c = _rgb("2a221a") if (x % 4 == 0 or y % 4 == 0) else _rgb("52463a")
            if x % 4 == 1 or y % 4 == 1:
                c = _rgb("6a5a48")
            _put(px, u, v, x, y, c)


def _metal_region(px, region, cols, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.55 * math.sin(x * 0.42 + math.sin(y * 0.3) * 1.5) + 0.45 * math.cos(y * 0.36 + x * 0.12)
            i = 0 if t > 0.65 else 1 if t > 0.2 else 2 if t > -0.35 else 3 if t > -0.75 else 4
            px[u + x, v + y] = _jitter(_rgb(cols[i]), rng, 3) + (255,)


def _paint_furniture(img, px, rng):
    R = REGIONS
    d = ImageDraw.Draw(img)
    _metal_region(px, R["gold"], ("fff0a8", "f0c85a", "d4a43c", "a87c26", "7a5816"), rng)
    _metal_region(px, R["silver"], ("f4f4f0", "d8d8d2", "b4b4ae", "8a8a86", "62625e"), rng)
    _metal_region(px, R["copper"], ("f0b08a", "d08a54", "a8643a", "7e4526", "5a2e18"), rng)
    _fill(img, R["wax"], _rgb("efe6cc"), rng, 6)
    _fill(img, R["bedding"], _rgb("e8e4da"), rng, 5)
    for name, base, dark in (("coral_red", "c8322e", "8a1c1a"), ("coral_pink", "e87a9a", "b04a6a"), ("coral_orange", "f08a3a", "b45a1e")):
        u, v, w, h = R[name]
        for y in range(h):
            for x in range(w):
                c = _rgb(base) if (x * 5 + y * 3) % 7 else _rgb(dark)
                px[u + x, v + y] = _jitter(c, rng, 10) + (255,)
    u, v, w, h = R["shell"]
    for y in range(h):
        for x in range(w):
            c = _rgb("f2e2c8") if (x + y) % 4 else _rgb("d8a878")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    u, v, w, h = R["pearl"]
    for y in range(h):
        for x in range(w):
            dd = math.hypot(x - 5.5, y - 5.5)
            px[u + x, v + y] = (_rgb("ffffff") if dd < 3 else _rgb("ece6f0") if dd < 8 else _rgb("c8c0d0")) + (255,)
    u, v, w, h = R["gauge"]
    d.rectangle((u, v, u + w - 1, v + h - 1), fill=_rgb("b8913c") + (255,))
    d.ellipse((u + 1, v + 1, u + w - 2, v + h - 2), fill=_rgb("f2ead6") + (255,), outline=_rgb("3a2a14") + (255,))
    for k in range(8):
        a = math.radians(-135 + 270 * k / 7)
        d.point((u + 7.5 + math.sin(a) * 5.5, v + 7.5 - math.cos(a) * 5.5), fill=_rgb("2a2a2a") + (255,))
    d.line((u + 7, v + 8, u + 11, v + 4), fill=_rgb("a01818") + (255,))
    u, v, w, h = R["coil"]
    for y in range(h):
        for x in range(w):
            c = _rgb("d08a54") if y % 2 else _rgb("8a4a24")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    u, v, w, h = R["keys"]
    for y in range(h):
        for x in range(w):
            c = _rgb("f2ecdc")
            if x % 3 == 2:
                c = _rgb("6a6050")
            if y < 5 and x % 7 in (1, 4):
                c = _rgb("1a1612")
            px[u + x, v + y] = c + (255,)
    u, v, w, h = R["helmet"]
    d.rectangle((u, v, u + w - 1, v + h - 1), fill=_rgb("c88a40") + (255,))
    d.ellipse((u + 3, v + 3, u + 12, v + 12), fill=_rgb("1d3a48") + (255,), outline=_rgb("e8c070") + (255,))
    d.line((u + 5, v + 7, u + 11, v + 7), fill=_rgb("c88a40") + (255,))
    d.line((u + 7, v + 5, u + 7, v + 11), fill=_rgb("c88a40") + (255,))
    # velvet, leather (tufted), books
    u, v, w, h = R["red_velvet"]
    for y in range(h):
        for x in range(w):
            c = _shade(_rgb("8a1a20"), 1.0 - 0.15 * ((x + y) % 5 == 0) + 0.08 * math.sin(x * 0.5))
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    u, v, w, h = R["green_leather"]
    for y in range(h):
        for x in range(w):
            fx, fy = (x + (4 if (y // 8) % 2 else 0)) % 8, y % 8
            dd = math.hypot(fx - 4, fy - 4)
            c = _shade(_rgb("2e5a36"), 1.15 - dd * 0.06)
            if dd < 0.8:
                c = _rgb("163020")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = R["books"]
    cols = ["7a1e1e", "1e3a6a", "2a5a2a", "6a4a1e", "4a1e4a", "8a6a2a", "2a2a2a", "5a2a14"]
    x = 0
    while x < w:
        bw = rng.choice((2, 2, 3, 3, 4))
        c = _rgb(rng.choice(cols))
        for row in (0, 16):
            bh = rng.randint(11, 15)
            for yy in range(16 - bh, 16):
                for xx in range(x, min(w, x + bw)):
                    cc = c
                    if yy in (16 - bh + 2, 14) or (xx == x):
                        cc = _shade(c, 0.6) if xx == x else _rgb("c9a24a")
                    px[u + xx, v + row + yy] = cc + (255,)
            for yy in range(0, 16 - bh):
                for xx in range(x, min(w, x + bw)):
                    px[u + xx, v + row + yy] = _rgb("1a0e06") + (255,)
        x += bw
    for x in range(w):
        for yy in (15, 31):
            px[u + x, v + yy] = _rgb("3e2414") + (255,)
    _riveted(px, R["organ_wood"], _rgb("3a2010"), _rgb("1e100a"), _rgb("c9a24a"), rng, pw=16, ph=32)
    u, v, w, h = R["battery"]
    for y in range(h):
        for x in range(w):
            c = _rgb("9ac8c0") if y > 8 else _rgb("dcecea")
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("5a6a68")
            elif x in (4, 11) and y > 4:
                c = _rgb("b8753e")
            px[u + x, v + y] = c + (255,)
    u, v, w, h = R["suit"]
    for y in range(h):
        for x in range(w):
            c = _rgb("8a6a44") if (x + y) % 3 else _rgb("6e5234")
            if y % 10 == 0:
                c = _rgb("5a4228")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # oriental rug: red field, a medallion, a blue border with gold
    u, v, w, h = R["rug"]
    for y in range(h):
        for x in range(w):
            bx = min(x, w - 1 - x, y, h - 1 - y)
            c = _rgb("8a1c1c")
            if bx < 3:
                c = _rgb("1e2a5a")
            elif bx < 5:
                c = _rgb("c9a24a")
            elif bx < 9:
                c = _rgb("1e2a5a") if (x + y) % 4 else _rgb("c9a24a")
            else:
                dd = abs(x - w / 2) + abs(y - h / 2)
                if dd < 10:
                    c = _rgb("c9a24a") if dd > 7 else _rgb("1e2a5a")
                elif (x * 3 + y * 5) % 13 == 0:
                    c = _rgb("e0b070")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # paintings: a seascape with a ship, a stormy sea, a portrait, a sea chart
    for name in ("painting_sea", "painting_storm"):
        u, v, w, h = R[name]
        storm = name == "painting_storm"
        for y in range(h):
            for x in range(w):
                if y < h * 0.55:
                    t = y / (h * 0.55)
                    c = tuple(int(a + (b - a) * t) for a, b in zip(_rgb("3a4a5a" if storm else "8ab0d0"), _rgb("6a6a6a" if storm else "e8d8b0")))
                else:
                    t = (y - h * 0.55) / (h * 0.45)
                    c = tuple(int(a + (b - a) * t) for a, b in zip(_rgb("2a5a6a" if storm else "2a6a8a"), _rgb("10283a")))
                    if (x + int(4 * math.sin(y * 0.8))) % 9 == 0:
                        c = _rgb("d8e8e8")
                px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
        # a ship: hull and sails
        cx, cy = u + w // 2 + (6 if storm else 0), v + int(h * 0.55)
        d.polygon([(cx - 10, cy - 1), (cx + 10, cy - 1), (cx + 7, cy + 3), (cx - 7, cy + 3)], fill=_rgb("3a2414") + (255,))
        for k, (dx, hh) in enumerate(((-5, 12), (1, 15), (6, 10))):
            d.line((cx + dx, cy - 1, cx + dx, cy - 1 - hh), fill=_rgb("2a1a0e") + (255,))
            d.rectangle((cx + dx - 3, cy - hh, cx + dx + 3, cy - hh + 8), fill=_rgb("f0e8d0") + (255,))
    u, v, w, h = R["portrait"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("2a1e14"), rng, 4) + (255,)
    d.ellipse((u + 10, v + 8, u + 21, v + 22), fill=_rgb("d8b090") + (255,))
    d.polygon([(u + 4, v + h - 1), (u + 27, v + h - 1), (u + 22, v + 26), (u + 9, v + 26)], fill=_rgb("1a2a3a") + (255,))
    d.rectangle((u + 13, v + 25, u + 18, v + 28), fill=_rgb("e8e4da") + (255,))
    u, v, w, h = R["chart"]
    for y in range(h):
        for x in range(w):
            c = _rgb("e8d8a8")
            if (x - 20) ** 2 / 300 + (y - 20) ** 2 / 120 < 1 or (x - 48) ** 2 / 80 + (y - 32) ** 2 / 60 < 1:
                c = _rgb("b89a5a")
            if x % 12 == 0 or y % 12 == 0:
                c = _shade(c, 0.85)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    d.line((u + 6, v + 40, u + 30, v + 26, u + 56, v + 12), fill=_rgb("a01818") + (255,))
    _planks(img, R["boat_wood"], _rgb("8a5a30"), _rgb("4a2e16"), 4, rng)
    _planks(img, R["plank_light"], _rgb("a87a48"), _rgb("6a4a28"), 4, rng)


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
