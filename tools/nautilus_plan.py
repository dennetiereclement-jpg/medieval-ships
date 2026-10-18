"""Plan of the Nautilus's rooms (docs/nautilus_plan.png), drawn from the real interior grid: one top
view per level (main level, lower level, wheelhouse on the casing), the rooms named, the doors
numbered as in /ship nautilus porte <n>, ladders, airlock, furniture and controls.

usage: python3 tools/nautilus_plan.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nautilus_interior as ni  # noqa: E402
import nautilus_decor as nd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs/nautilus_plan.png")

NAMES = {
    "corridor_fore": "Coursive avant", "cabin_nemo": "Cabine de Nemo", "cabin_aronnax": "Cabine d'Aronnax",
    "dining": "Salle à manger", "library": "Bibliothèque", "salon": "Grand salon\n(orgue, baies)", "stair_hall": "Escalier\nen colimaçon",
    "engine_room": "Salle des machines\n(piles, moteur)", "coursive": "Coursive", "cross_fore": "", "airlock": "Sas\n(scaphandres)",
    "kitchen": "Cuisine", "crew": "Équipage", "corridor_aft": "Couloir", "junction": "", "store_port": "Cale bâbord",
    "store_stbd": "Cale tribord", "crawlway": "Double fond", "wheelhouse": "Timonerie", "lamp_cage": "Cage du\nprojecteur",
}
LEVELS = [
    ("Pont principal (y 0 à 4,5)", ni.M0 + 1.0, ("corridor_fore", "cabin_nemo", "cabin_aronnax", "dining", "library", "salon", "stair_hall",
                                                 "engine_room")),
    ("Pont inférieur (y -4,5 à -0,5)", ni.L0 + 1.0, ("coursive", "airlock", "kitchen", "crew", "corridor_aft", "store_port", "store_stbd",
                                                     "stair_hall", "engine_room")),
    ("Sur la coque : timonerie et cage du projecteur (y 9)", ni.ns.CASING_TOP_Y + 1.0, ("wheelhouse", "lamp_cage")),
]
COLORS = {
    ni.OUT: (24, 32, 48), ni.SOLID: (92, 70, 52), ni.DRY: (226, 214, 190), ni.LADDER: (120, 170, 220), ni.AIRLOCK: (110, 170, 200),
    ni.WINDOW: (150, 220, 240), ni.FURNITURE: (176, 130, 90),
}
S = 9  # pixels per cell (half a block)


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def level_image(g, title, y, rooms):
    iy = int(np.floor((y - g.y0) / ni.CELL))
    k = g.k[:, iy, :]  # (x, z)
    nx, nz = k.shape
    # z along the image width (bow on the right), x along the height (port on top)
    W, H = nz * S, nx * S
    pad_top = 40
    img = Image.new("RGB", (W + 20, H + pad_top + 20), (18, 22, 34))
    d = ImageDraw.Draw(img)
    d.text((10, 8), title, fill=(240, 225, 190), font=font(20))
    ox, oy = 10, pad_top

    def px(x, z):
        return ox + (z - g.z0) / ni.CELL * S, oy + (g.x1 - x) / ni.CELL * S

    for i in range(nx):
        for j in range(nz):
            c = k[i, j]
            col = COLORS.get(int(c), (200, 80, 60) if c >= ni.DOOR else (255, 0, 255))
            x0, y0 = ox + j * S, oy + (nx - 1 - i) * S
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=col)
    # doors: their numbers
    f = font(13)
    for door in sorted(set(int(c) - ni.DOOR for c in np.unique(k) if c >= ni.DOOR)):
        m = k == ni.DOOR + door
        ii, jj = np.nonzero(m)
        x = g.x0 + (ii.mean() + 0.5) * ni.CELL
        z = g.z0 + (jj.mean() + 0.5) * ni.CELL
        cx, cy = px(x, z)
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(200, 60, 40), outline=(255, 230, 200))
        d.text((cx, cy), str(door), fill=(255, 255, 255), font=f, anchor="mm")
    # controls on this level
    for w in nd.SWITCHES:
        if abs(w["y"] - y) < 2.5:
            cx, cy = px(w["x"], w["z"])
            d.rectangle((cx - 5, cy - 5, cx + 5, cy + 5), fill=(250, 200, 60), outline=(60, 40, 10))
    # room names
    f = font(14)
    for name in rooms:
        x0, x1, y0, y1, z0, z1 = ni.ROOMS[name]
        label = NAMES.get(name, "")
        if not label or not (y0 <= y <= y1):
            continue
        cx, cy = px((x0 + x1) / 2, (z0 + z1) / 2)
        d.multiline_text((cx, cy), label, fill=(20, 16, 12), font=f, anchor="mm", align="center", stroke_width=2,
                         stroke_fill=(240, 232, 214))
    return img


def main():
    g = ni.build()
    nd.build()
    nd.apply_to_grid(g)
    g.x0, g.y0, g.z0, g.x1 = ni.X0, ni.Y0, ni.Z0, ni.X1
    images = [level_image(g, t, y, rooms) for t, y, rooms in LEVELS]
    W = max(im.width for im in images)
    legend_h = 70
    sheet = Image.new("RGB", (W, sum(im.height for im in images) + legend_h + 50), (18, 22, 34))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "Nautilus — plan des salles (vue de dessus, la proue à droite, bâbord en haut)", fill=(255, 240, 200), font=font(24))
    y = 50
    for im in images:
        sheet.paste(im, (0, y))
        y += im.height
    f = font(15)
    items = [((226, 214, 190), "salle / couloir"), ((92, 70, 52), "cloison, plancher"), ((176, 130, 90), "meuble"),
             ((150, 220, 240), "vitre / hublot"), ((120, 170, 220), "échelle"), ((110, 170, 200), "sas (inondable)"),
             ((200, 60, 40), "porte n (/ship nautilus porte n)"), ((250, 200, 60), "levier / vanne")]
    x = 10
    for col, label in items:
        d.rectangle((x, y + 20, x + 18, y + 38), fill=col, outline=(0, 0, 0))
        d.text((x + 24, y + 20), label, fill=(235, 225, 200), font=f)
        x += 34 + int(d.textlength(label, font=f))
    sheet.save(OUT)
    print("plan:", OUT, sheet.size)


if __name__ == "__main__":
    main()
