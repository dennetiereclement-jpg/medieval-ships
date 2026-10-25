"""Comparison sheet of the Sky Leviathan: each view of the reference sheet next to the screenshot of the real
game taken by the in-game test (LeviathanGameTest, decor variant: the rooms furnished with the decoration mods).

usage: python3 tools/leviathan_compare.py <reference sheet> <folder of in-game screenshots> [note]
writes docs/comparaison_sky_leviathan.png (two reference / game pairs per row)
"""
import os
import sys

from PIL import Image, ImageDraw

from nautilus_compare import find_shot, fit, font

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# panels of the reference sheet (1536 x 1024): label, crop box, screenshot name in the test, and for the outside
# views the part of the screenshot around the airship (fractions of its width and height)
PANELS = [
    ("Vue de côté", (0, 0, 965, 750), "sky_leviathan_1_cote", (0.14, 0.0, 0.92, 0.95)),
    ("Vue en perspective", (970, 495, 1282, 750), "sky_leviathan_5_perspective", (0.16, 0.08, 0.76, 0.78)),
    ("Vue avant", (970, 0, 1250, 305), "sky_leviathan_2_avant", (0.3, 0.1, 0.7, 0.86)),
    ("Vue arrière", (1253, 0, 1536, 305), "sky_leviathan_3_arriere", (0.28, 0.1, 0.72, 0.86)),
    ("Vue de dessus", (970, 310, 1536, 490), "sky_leviathan_4_dessus", (0.2, 0.3, 0.84, 0.72)),
    ("Détails (ailerons, pavillon, lanternes, filets) et les ailerons en jeu", (1285, 497, 1536, 750), "sky_leviathan_19_ailerons"),
    ("Pont principal", (0, 757, 260, 1024), "sky_leviathan_16_pont_principal"),
    ("Salle commune", (262, 757, 528, 1024), "sky_leviathan_9_salle_commune"),
    ("Cabine du capitaine", (532, 757, 790, 1024), "sky_leviathan_10_cabine_capitaine"),
    ("Cale / stockage", (795, 757, 1050, 1024), "sky_leviathan_13_cale"),
    ("Coursive", (1055, 757, 1280, 1024), "sky_leviathan_14_coursive"),
    ("Salle des machines", (1283, 757, 1536, 1024), "sky_leviathan_15_salle_machines"),
]
CELL_W, CELL_H = 400, 250
PAIRS_PER_ROW = 2


def main():
    ref = Image.open(sys.argv[1]).convert("RGB")
    folder = sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    rows = (len(PANELS) + PAIRS_PER_ROW - 1) // PAIRS_PER_ROW
    pair_w = 2 * CELL_W + 10
    W = PAIRS_PER_ROW * pair_w + (PAIRS_PER_ROW - 1) * 30 + 20
    H = rows * (CELL_H + 34) + 96
    img = Image.new("RGB", (W, H), (10, 12, 20))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Le Léviathan des Cieux : planche de référence et jeu", fill=(255, 238, 200), font=font(24))
    d.text((10, 44), note, fill=(200, 200, 210), font=font(14))
    for p in range(PAIRS_PER_ROW):
        x = 10 + p * (pair_w + 30)
        d.text((x + CELL_W // 2, 76), "Référence", fill=(230, 210, 160), font=font(15), anchor="mm")
        d.text((x + CELL_W + 10 + CELL_W // 2, 76), "Dans le jeu (capture du test)", fill=(230, 210, 160), font=font(15), anchor="mm")
    missing = []
    for k, (label, box, shot, *frame) in enumerate(PANELS):
        x = 10 + (k % PAIRS_PER_ROW) * (pair_w + 30)
        y = 90 + (k // PAIRS_PER_ROW) * (CELL_H + 34)
        d.text((x, y + 4), label, fill=(240, 230, 210), font=font(16))
        y += 26
        img.paste(fit(ref.crop(box), CELL_W, CELL_H), (x, y))
        path = find_shot(folder, shot)
        gx = x + CELL_W + 10
        if path:
            game = Image.open(path).convert("RGB")
            if frame:
                f = frame[0]
                game = game.crop((round(f[0] * game.width), round(f[1] * game.height), round(f[2] * game.width), round(f[3] * game.height)))
            img.paste(fit(game, CELL_W, CELL_H), (gx, y))
        else:
            missing.append(shot)
            d.rectangle((gx, y, gx + CELL_W, y + CELL_H), outline=(120, 60, 60))
            d.text((gx + CELL_W // 2, y + CELL_H // 2), "capture absente", fill=(220, 120, 120), font=font(16), anchor="mm")
    out = os.path.join(ROOT, "docs/comparaison_sky_leviathan.png")
    img.save(out, optimize=True)
    print(out, img.size, "missing:", missing)


if __name__ == "__main__":
    main()
