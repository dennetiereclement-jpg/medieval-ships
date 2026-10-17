"""Texture regions of the cabin furniture and inner windows, shared by the three atlases.

paint(px, regions) paints every region of INTERIOR_REGIONS that the atlas defines;
`regions` maps a region name to its (u, v, w, h) rectangle.
"""
import math
import random

from galley_texture import _jitter, _rgb

INTERIOR_REGIONS = ("window_in", "arch_window_in", "rug", "books", "chart", "bedding", "painting")


def paint(px, regions):
    rng = random.Random(1715)
    for name in INTERIOR_REGIONS:
        if name in regions:
            globals()["_" + name](px, *regions[name], rng)


def _window_in(px, u, v, w, h, rng):
    """Window seen from inside: dark wooden frame and cross bar, leaded panes of daylight."""
    for y in range(h):
        for x in range(w):
            if x < 3 or x >= w - 3 or y < 3 or y >= h - 3:
                c = _jitter(_rgb("4a2e15"), rng, 5)
            elif abs(x - w / 2 + 0.5) < 1.2 or abs(y - h / 2 + 0.5) < 1.2:
                c = _rgb("5a3a1c")
            elif (x + y) % 5 == 0 or (x - y) % 5 == 0:
                c = _rgb("7d8f99")
            else:
                t = y / h
                c = tuple(int(a + (b - a) * t) for a, b in zip(_rgb("e4f1f8"), _rgb("9cc3dc")))
            px[u + x, v + y] = c + (255,)


def _arch_window_in(px, u, v, w, h, rng):
    for y in range(h):
        for x in range(w):
            r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - w / 2) ** 2) ** 0.5
            if y < w / 2 and r > w / 2:
                continue
            frame = x < 2 or x >= w - 2 or y >= h - 2 or (y < w / 2 and r > w / 2 - 2)
            if frame:
                c = _rgb("4a2e15")
            elif (x - 2) % 6 == 5 or y % 6 == 5:
                c = _rgb("6c7c86")
            else:
                c = _rgb("dcebf4") if y < h / 2 else _rgb("a7c9df")
            px[u + x, v + y] = c + (255,)


def _rug(px, u, v, w, h, rng):
    """Oriental carpet: fringed ends, gold border, red field, blue medallion."""
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2:
                c = _rgb("e8dcc0") if y % 2 else _rgb("cdbf9f")
            elif x < 5 or x >= w - 5 or y < 3 or y >= h - 3:
                c = _rgb("d4aa45") if (x + y) % 4 else _rgb("27407a")
            else:
                dx, dy = abs(x - w / 2 + 0.5) / (w / 2 - 5), abs(y - h / 2 + 0.5) / (h / 2 - 3)
                d = dx + dy
                if d < 0.35:
                    c = _rgb("27407a") if d < 0.25 else _rgb("e8c35a")
                elif abs(d - 0.7) < 0.05:
                    c = _rgb("e8c35a")
                elif (x // 4 + y // 4) % 2 == 0 and d > 0.75:
                    c = _rgb("7a1a16")
                else:
                    c = _rgb("9e2620")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)


def _books(px, u, v, w, h, rng):
    """Bookshelf front: two shelves of leather spines."""
    colours = ["8b1e1e", "27407a", "2e5a2e", "6b4a1e", "4a2a4a", "a0632a", "1f3a3a"]
    shelf_h = h // 2
    for row in range(2):
        x = 1
        while x < w - 1:
            bw = rng.choice((2, 2, 3, 3, 4))
            col = _rgb(rng.choice(colours))
            top = rng.choice((2, 3, 3, 4, 5))
            for xx in range(x, min(x + bw, w - 1)):
                for y in range(row * shelf_h + top, (row + 1) * shelf_h - 2):
                    gold = (y - row * shelf_h) in (top + 2, shelf_h - 5)
                    c = _rgb("d4aa45") if gold and xx == x + bw // 2 else col
                    if xx == x:
                        c = tuple(int(k * 0.7) for k in c)
                    px[u + xx, v + y] = _jitter(c, rng, 5) + (255,)
            x += bw
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[u + x, v + y]
            shelf = (y % shelf_h) >= shelf_h - 2 or x == 0 or x == w - 1 or y == 0
            if shelf:
                px[u + x, v + y] = _jitter(_rgb("4a2e15"), rng, 5) + (255,)
            elif a == 0 or (r, g, b) == (0, 0, 0):
                px[u + x, v + y] = _rgb("1c120a") + (255,)


def _chart(px, u, v, w, h, rng):
    """Sea chart: parchment, coast lines, rhumb lines and a compass rose."""
    cx, cy = w * 0.62, h * 0.55
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("e2cd9c"), rng, 7)
            coast = abs(y - (h * 0.25 + 5 * math.sin(x / 4.0))) < 0.8 or abs(x - (w * 0.2 + 3 * math.sin(y / 3.0))) < 0.8
            land = y < h * 0.25 + 5 * math.sin(x / 4.0) and x < w * 0.55
            if land:
                c = _jitter(_rgb("c9b07a"), rng, 6)
            if coast:
                c = _rgb("6b4a2a")
            ang = math.atan2(y - cy, x - cx)
            if abs(math.sin(4 * ang)) < 0.06 and not land:
                c = _rgb("a07850")
            if (x - cx) ** 2 + (y - cy) ** 2 < 4:
                c = _rgb("8b1e1e")
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                c = _rgb("b89a64")
            px[u + x, v + y] = c + (255,)


def _bedding(px, u, v, w, h, rng):
    """Top: pillow and folded sheet, then a striped wool blanket."""
    for y in range(h):
        for x in range(w):
            if x < 6:
                c = _rgb("eee8da") if (x + y) % 5 else _rgb("d6cfbf")
            elif x < 9:
                c = _rgb("f4efe4")
            else:
                c = _rgb("27407a") if (x // 4) % 3 else _rgb("b3221c")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)


def _painting(px, u, v, w, h, rng):
    """Framed painting of a ship at sea."""
    for y in range(h):
        for x in range(w):
            if x < 3 or x >= w - 3 or y < 3 or y >= h - 3:
                c = _rgb("d4aa45") if (x + y) % 3 else _rgb("9c7a2a")
            elif y < h * 0.6:
                t = (y - 3) / (h * 0.6)
                c = tuple(int(a + (b - a) * t) for a, b in zip(_rgb("7fa6c9"), _rgb("e3d2a8")))
            else:
                c = _rgb("2b4a6b") if (x + y // 2) % 4 else _rgb("4b6f90")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # the ship: hull and sails
    for x in range(int(w * 0.35), int(w * 0.68)):
        for y in range(int(h * 0.56), int(h * 0.64)):
            px[u + x, v + y] = _rgb("3a2414") + (255,)
    for mx in (int(w * 0.44), int(w * 0.58)):
        for y in range(int(h * 0.28), int(h * 0.56)):
            px[u + mx, v + y] = _rgb("3a2414") + (255,)
        for y in range(int(h * 0.31), int(h * 0.52)):
            for x in range(mx - 3, mx + 4):
                if x != mx:
                    px[u + x, v + y] = _rgb("f2ead8") + (255,)
