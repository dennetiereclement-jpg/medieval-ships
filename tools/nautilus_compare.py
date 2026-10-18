"""Comparison sheets of the Nautilus: each view of the reference sheet next to the screenshot of the
real game (taken by the in-game test, see ShipClientGameTest.nautilusTour).

usage: python3 tools/nautilus_compare.py <reference sheet> <folder of in-game screenshots> [suffix]
writes docs/comparaison_nautilus_exterieur<suffix>.png and docs/comparaison_nautilus_interieur<suffix>.png
"""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# panels of the reference sheet (1536 x 1024): name, crop box, screenshot name in the test
EXTERIOR = [
    ("Vue de côté", (0, 0, 1105, 325), "nautilus_1_droite"),
    ("Vue de dessus", (1110, 0, 1370, 115), "nautilus_0a_vue_de_dessus"),
    ("Vue avant (proue)", (1373, 0, 1536, 200), "nautilus_0b_vue_avant"),
    ("Vue arrière (poupe)", (1110, 118, 1370, 325), "nautilus_0c_vue_arriere"),
    ("Vue en perspective", (1373, 203, 1536, 325), "nautilus_3_perspective"),
    ("Sous l'eau", (0, 0, 1105, 325), "nautilus_7_sous_l_eau"),
]
INTERIOR = [
    ("1. Salle à manger", (5, 330, 315, 555), "nautilus_p01_salle_a_manger"),
    ("2. Bibliothèque", (318, 330, 648, 555), "nautilus_p02_bibliotheque"),
    ("3. Grand salon", (652, 330, 1050, 555), "nautilus_p03_grand_salon"),
    ("4. Cabine du professeur Aronnax", (1055, 330, 1300, 555), "nautilus_p04_cabine_aronnax"),
    ("5. Cabine du capitaine Nemo", (1303, 330, 1536, 555), "nautilus_p05_cabine_nemo"),
    ("6. Timonerie", (5, 560, 408, 778), "nautilus_p06_timonerie"),
    ("7. Cage du projecteur", (412, 560, 770, 778), "nautilus_p07_cage_du_projecteur"),
    ("7b. Le faisceau", (412, 560, 770, 778), "nautilus_p07b_faisceau"),
    ("8. Coursive", (773, 560, 1000, 778), "nautilus_p08_coursive"),
    ("9. Escalier central", (1003, 560, 1276, 778), "nautilus_p09_escalier"),
    ("10. Accès extérieur (trappe)", (1280, 560, 1536, 778), "nautilus_p10_acces_exterieur"),
    ("11. Cuisine", (5, 782, 310, 1024), "nautilus_p11_cuisine"),
    ("12. Machines : piles", (313, 782, 617, 1024), "nautilus_p12_machines_piles"),
    ("13. Machines : moteur", (620, 782, 1003, 1024), "nautilus_p13_machines_moteur"),
    ("14. Sas des scaphandres", (1006, 782, 1276, 1024), "nautilus_p14_sas_des_scaphandres"),
    ("15. Canot de sauvetage", (1280, 782, 1536, 1024), "nautilus_p15_canot"),
]
CELL_W, CELL_H = 520, 300


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def fit(im, w, h):
    im = im.copy()
    im.thumbnail((w, h))
    out = Image.new("RGB", (w, h), (14, 18, 28))
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def find_shot(folder, name):
    for prefix in ("solo", "dedie"):
        hits = sorted(glob.glob(os.path.join(folder, "*_%s_%s.png" % (prefix, name))))
        if hits:
            return hits[0]
    return None


def sheet(ref, folder, panels, title, out, note):
    rows = len(panels)
    W, H = 2 * CELL_W + 30, rows * (CELL_H + 34) + 90
    img = Image.new("RGB", (W, H), (10, 12, 20))
    d = ImageDraw.Draw(img)
    d.text((10, 10), title, fill=(255, 238, 200), font=font(24))
    d.text((10, 44), note, fill=(200, 200, 210), font=font(14))
    d.text((10 + CELL_W // 2, 70), "Planche de référence", fill=(230, 210, 160), font=font(15), anchor="mm")
    d.text((20 + CELL_W + CELL_W // 2, 70), "Dans le jeu (capture du test automatique)", fill=(230, 210, 160), font=font(15), anchor="mm")
    y = 84
    missing = []
    for label, box, shot in panels:
        d.text((10, y + 4), label, fill=(240, 230, 210), font=font(16))
        y += 26
        img.paste(fit(ref.crop(box), CELL_W, CELL_H), (10, y))
        path = find_shot(folder, shot)
        if path:
            img.paste(fit(Image.open(path).convert("RGB"), CELL_W, CELL_H), (20 + CELL_W, y))
        else:
            missing.append(shot)
            d.rectangle((20 + CELL_W, y, 20 + 2 * CELL_W, y + CELL_H), outline=(120, 60, 60))
            d.text((20 + CELL_W + CELL_W // 2, y + CELL_H // 2), "capture absente", fill=(220, 120, 120), font=font(16), anchor="mm")
        y += CELL_H + 8
    img.save(out)
    print(out, img.size, "missing:", missing)


def main():
    ref = Image.open(sys.argv[1]).convert("RGB")
    folder = sys.argv[2]
    suffix = sys.argv[3] if len(sys.argv) > 3 else ""
    note = sys.argv[4] if len(sys.argv) > 4 else ""
    sheet(ref, folder, EXTERIOR, "Nautilus — extérieur : référence et jeu", os.path.join(ROOT, "docs/comparaison_nautilus_exterieur%s.png" % suffix),
          note)
    sheet(ref, folder, INTERIOR, "Nautilus — les 15 panneaux de l'intérieur : référence et jeu",
          os.path.join(ROOT, "docs/comparaison_nautilus_interieur%s.png" % suffix), note)


if __name__ == "__main__":
    main()
