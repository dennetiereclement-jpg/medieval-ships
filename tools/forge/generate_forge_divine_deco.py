"""Genere le modele DECOR de la Forge divine (1.34.0) :
src/main/resources/assets/medievalships/models/entity/forge_divine_deco.bbmodel (+ copie blockbench/) et
textures/entity/forge_divine_deco.png. Bibliotheque : tools/forge/forgelib_deco.py ; audit :
tools/forge/forge_audit_deco.py (et tools/forge/forge_audit.py de la structure).

Contenu (cale sur tools/forge/CALAGE.md) : statue divine ailee (socle sculpte, robe, croix lumineuse, ailes en
gradins de plumes sur 4 couches, aureole), bannieres bleues a bordure or et etoile sacree sous les potences
(x = +-5.6), chaines et lanternes (x = +-3.6, +-6.15, +-4.75, lanternes basses x = +-5.6), tableau de plans sur
chevalet (etabli gauche), rateliers d'outils (etabli arriere gauche, etabli droit), cristal dore, presse mecanique.
Os : deco > statue, wing_l, wing_r, halo, craft_holy (lumiere renforcee en fabrication), fx_holy_0..7 (vides),
banners, chains, lanterns, benches, press. Usage : python3 tools/forge/generate_forge_divine_deco.py [--no-structure]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forgelib_deco as fd  # noqa: E402

U = 1.0 / 32          # unite de dessin (1/32 bloc)
STRUCT = os.path.join(fd.ASSETS, "models/entity/forge_divine.bbmodel")

# calage (tools/forge/CALAGE.md)
BODY_TOP = 6.5
ARM_Y = 8.4           # dessous des bras des potences
ARM_Z = 0.6
BANNER_X = 5.6
LANTERN_X = 3.6
BENCH_L = (-4.6, 1.0, 1.3)          # centre dessus etabli gauche
BENCH_BL = (-2.725, 1.0, 0.75)      # etabli arriere gauche (rateliers au mur z = 0.25)
BENCH_R = (2.95, 1.0, 0.75)         # etabli droit (deplace par A)
WALL_Z = 0.25
PRESS = (5.2, 0.9, 1.3)
SEAT = (5.6, 1.2, -0.2)             # sieges des lanternes basses
HOOK_Y = 3.3


def q(v):
    return round(v / U) * U


def sym(fn):
    for s, tag in ((-1, "l"), (1, "r")):
        fn(s, tag)


def X(s, a, b):
    """Intervalle x [a, b] (cote droit, a < b) recopie en miroir pour s = -1."""
    return (a, b) if s > 0 else (-b, -a)


# ------------------------------------------------------------------ statue
def statue(m):
    st = m.bone("statue", pivot=(0, BODY_TOP, -0.5))
    zc = -0.5
    B = m.box
    # socle sculpte pierre / or (enfonce de 1/32 dans le corps)
    y0 = BODY_TOP - U
    B(st, "socle_base", -0.625, y0, zc - 0.5, 0.625, 6.71875, zc + 0.5, "stone")
    B(st, "socle_corniche", -0.6875, 6.71875, zc - 0.5625, 0.6875, 6.8125, zc + 0.5625, "gold")
    B(st, "socle_haut", -0.8125, 6.8125, zc - 0.40625, 0.8125, 6.96875, zc + 0.40625, "stone")
    B(st, "socle_plateau", -0.46875, 6.96875, zc - 0.34375, 0.46875, 7.03125, zc + 0.34375, "gold_l")
    B(st, "socle_plaque", -0.25, 6.5, zc + 0.46875, 0.25, 6.6875, zc + 0.53125, "gold")
    B(st, "glow_socle_gemme", -0.0625, 6.53125, zc + 0.5, 0.0625, 6.65625, zc + 0.5625, "glow_gold")
    B(st, "socle_plaque_haut", -0.1875, 6.84375, zc + 0.375, 0.1875, 6.9375, zc + 0.4375, "gold")

    def corners(s, tag):
        xa, xb = X(s, 0.4375, 0.59375)
        B(st, "socle_coin_%s" % tag, xa, y0, zc + 0.4375, xb, 6.6875, zc + 0.53125, "gold")
        # colonnettes dorees de part et d'autre (elles portent le bas des ailes)
        xa, xb = X(s, 0.75, 0.90625)
        B(st, "colonnette_%s" % tag, xa, y0, zc - 0.125, xb, 7.40625, zc + 0.03125, "gold")
        xa, xb = X(s, 0.71875, 0.9375)
        B(st, "colonnette_pied_%s" % tag, xa, y0, zc - 0.15625, xb, 6.625, zc + 0.0625, "bronze")
        B(st, "colonnette_chap_%s" % tag, xa, 7.34375, zc - 0.15625, xb, 7.46875, zc + 0.0625, "gold_l")
    sym(corners)
    # dossier entre les colonnettes (derriere la figure)
    B(st, "dossier", -0.90625, 6.96875, zc - 0.21875, 0.90625, 7.5, zc - 0.15625, "stone")
    B(st, "dossier_or", -0.875, 7.5, zc - 0.21875 - U, 0.875, 7.5625, zc - 0.15625 + U, "gold")
    # figure en robe
    B(st, "robe_ourlet", -0.40625, 7.03125, zc - 0.28125, 0.40625, 7.15625, zc + 0.25, "gold")
    B(st, "robe_bas", -0.34375, 7.15625, zc - 0.25, 0.34375, 7.875, zc + 0.1875, "gold")
    B(st, "robe_blanche", -0.1875, 7.03125, zc - 0.0625, 0.1875, 7.96875, zc + 0.28125, "robe")
    B(st, "ceinture", -0.3125, 7.78125, zc - 0.21875, 0.3125, 7.875, zc + 0.25, "gold_l")
    B(st, "torse", -0.28125, 7.875, zc - 0.21875, 0.28125, 8.375, zc + 0.15625, "gold")
    B(st, "epaules", -0.40625, 8.25, zc - 0.1875, 0.40625, 8.4375, zc + 0.125, "gold")
    B(st, "cou", -0.09375, 8.4375, zc - 0.125, 0.09375, 8.5, zc + 0.0625, "gold")
    B(st, "col", -0.34375, 8.40625, zc - 0.25, 0.34375, 8.625, zc - 0.03125, "gold_l")
    B(st, "tete", -0.15625, 8.5, zc - 0.15625, 0.15625, 8.8125, zc + 0.15625, "gold")
    B(st, "glow_visage", -0.09375, 8.5625, zc + 0.125, 0.09375, 8.75, zc + 0.1875, "glow_gold")
    B(st, "coiffe", -0.1875, 8.75, zc - 0.1875, 0.1875, 8.875, zc + 0.09375, "gold_l")

    def arms(s, tag):
        xa, xb = X(s, 0.375, 0.53125)
        B(st, "bras_%s" % tag, xa, 7.96875, zc - 0.125, xb, 8.40625, zc + 0.0625, "gold")
        xa, xb = X(s, 0.46875, 0.625)
        B(st, "main_%s" % tag, xa, 7.8125, zc - 0.09375, xb, 8.0, zc + 0.21875, "gold_l")
        xa, xb = X(s, 0.21875, 0.375)
        B(st, "manche_%s" % tag, xa, 7.6875, zc - 0.03125, xb, 7.90625, zc + 0.21875, "gold")
    sym(arms)
    # grande croix doree a coeur lumineux, tenue devant la poitrine
    B(st, "croix_v", -0.0625, 7.5625, zc + 0.15625, 0.0625, 8.53125, zc + 0.25, "gold_l")
    B(st, "croix_h", -0.25, 8.0625, zc + 0.125, 0.25, 8.1875, zc + 0.21875, "gold_l")
    B(st, "glow_croix_coeur", -0.09375, 8.03125, zc + 0.1875, 0.09375, 8.21875, zc + 0.3125, "glow_gold")
    B(st, "glow_croix_pied", -0.03125, 7.625, zc + 0.21875, 0.03125, 7.96875, zc + 0.28125, "glow_gold")
    return st


def wing(m, s, tag):
    """Aile deployee en vrai volume : 12 colonnes de plumes (1/8 bloc) en 4 gradins de profondeur, le bord d'attaque
    epais en haut, les remiges longues derriere ; les pointes avancent vers l'avant (courbure)."""
    w = m.bone("wing_%s" % tag, pivot=(s * 0.35, 8.3, -0.75))
    zc = -0.5
    n = 12
    x_in, cw = 0.375, 0.125
    H = 1.0 / 64
    # decalages en x (en 1/64, modulo le pas de 8/64) : bord (0, 2), couvertures (4, 6), secondaires (1, 3),
    # primaires (5, 7) -> aucune face x de l'aile n'en rencontre une autre ; colonnes de 10/64 qui se recouvrent
    offs = {"bord": (0, 2), "couv": (4, 6), "sec": (1, 3), "prim": (5, 7)}
    for i in range(n):
        t = i / (n - 1)
        x8 = x_in + i * cw
        xm = x8 + cw / 2
        top = 8.5 + 0.76 * t ** 0.75
        if i == n - 1:
            top -= 0.1875
        elif i == n - 2:
            top -= 0.0625
        top = q(top)
        if xm <= 0.8:
            bot = 7.34375
        else:
            bot = 7.34375 + (xm - 0.8) / (1.85 - 0.8) * 1.3
        bot = q(bot)
        bend = 2 * q(0.11 * t ** 1.6) + (U if i % 2 else 0)
        H_ = top - bot

        def xr(tier):
            a, b = offs[tier]
            return X(s, x8 + a * H, x8 + cw + b * H)
        couv_bot = q(top - max(0.34375, H_ * 0.36))
        sec_top = min(q(top - H_ * 0.25), top - 0.25 - U)
        sec_bot = q(bot + H_ * 0.30)
        prim_top = min(q(top - H_ * 0.45), couv_bot - U)
        if sec_top - sec_bot < 0.125:
            sec_bot = sec_top - 0.125
        prim_top = max(prim_top, sec_bot + 0.0625)
        xa, xb = xr("bord")
        m.box(w, "aile_bord_%s%d" % (tag, i), xa, top - 0.25, zc - 0.40625 + bend, xb, top, zc - 0.0625 + bend, "feather_l")
        xa, xb = xr("couv")
        m.box(w, "aile_couv_%s%d" % (tag, i), xa, couv_bot, zc - 0.34375 + H + bend, xb, top - 0.0625,
              zc - 0.09375 + H + bend, "feather")
        xa, xb = xr("sec")
        m.box(w, "aile_sec_%s%d" % (tag, i), xa, sec_bot, zc - 0.40625 + bend, xb, sec_top, zc - 0.15625 + bend, "feather")
        xa, xb = xr("prim")
        m.box(w, "aile_prim_%s%d" % (tag, i), xa, bot, zc - 0.46875 + H + bend, xb, prim_top, zc - 0.21875 + H + bend,
              "feather2")
    # attache de l'aile dans le dos
    xa, xb = X(s, 0.21875, 0.46875)
    m.box(w, "aile_attache_%s" % tag, xa, 7.34375, zc - 0.4375, xb, 8.53125, zc - 0.15625, "feather_l")
    return w


def halo(m):
    """Aureole doree horizontale au-dessus de la tete (anneau pixel art en cellules de 1/16, pleine lumiere)."""
    h = m.bone("halo", pivot=(0, 9.05, -0.5))
    zc, R0, R1 = -0.5, 0.40, 0.56
    c = 1.0 / 16
    rows = {}
    for j in range(-10, 10):
        z = (j + 0.5) * c
        segs = []
        cur = None
        for i in range(-10, 10):
            x = (i + 0.5) * c
            inside = R0 <= math.hypot(x, z) <= R1
            if inside and cur is None:
                cur = i
            if not inside and cur is not None:
                segs.append((cur, i))
                cur = None
        if cur is not None:
            segs.append((cur, 10))
        rows[j] = segs
    # disque de lumiere sacree dans l'anneau (plus mince, sous le dessus de l'anneau)
    for j in range(-7, 7):
        z = (j + 0.5) * c
        half = math.sqrt(max(0.0, (R0 + 0.03) ** 2 - z * z))
        n = int(round(half / c))
        if n < 1:
            continue
        m.box(h, "glow_halo_lumiere_%d" % j, -n * c, 9.015625 + (U if j % 2 else 0), zc + j * c, n * c,
              9.0625 + (U if j % 2 else 0), zc + (j + 1) * c, "glow_white")
    for j, segs in rows.items():
        odd = j % 2 != 0
        for a, b in segs:
            y0, y1 = (9.0, 9.09375) if not odd else (9.0 - U, 9.09375 + U)
            ext = U if odd else 0
            m.box(h, "glow_halo_%d_%d" % (j, a), a * c - ext, y0, zc + j * c - ext, b * c + ext, y1, zc + (j + 1) * c + ext,
                  "glow_gold")
    return h


def holy(m):
    """Lumiere sacree renforcee pendant une fabrication (os craft_holy) : rayons dores derriere la statue et
    couronne lumineuse au pied ; os vides fx_holy_<n> = points d'emission des particules sacrees."""
    cr = m.bone("craft_holy", pivot=(0, 8.3, -0.5))
    zc = -0.5
    # nimbe : disque lumineux plein derriere la tete et les epaules (rangees de 1/16, alternance d'epaisseur)
    c = 1.0 / 16
    cy, R = 8.6875, 0.5
    for j in range(-8, 8):
        y = (j + 0.5) * c
        half = math.sqrt(max(0.0, R * R - y * y))
        n = int(half / c)
        if n < 1:
            continue
        odd = j % 2 != 0
        e = U if odd else 0
        z0, z1 = (-0.8125, -0.75) if not odd else (-0.8125 - U, -0.75 + U)
        m.box(cr, "glow_craft_nimbe_%d" % j, -n * c - e, cy + j * c - e, zc + z0, n * c + e, cy + (j + 1) * c + e, zc + z1,
              "glow_white")
    m.box(cr, "glow_craft_couronne", -0.71875, 6.6875, zc - 0.59375, 0.71875, 6.84375, zc + 0.59375, "glow_gold")
    m.box(cr, "glow_craft_aureole", -0.15625, 9.0, zc - 0.15625, 0.15625, 9.09375, zc + 0.15625, "glow_white")
    pts = [(0, 9.1, -0.5), (0, 8.15, -0.15), (-1.75, 9.1, -0.4), (1.75, 9.1, -0.4), (-0.55, 7.9, -0.3),
           (0.55, 7.9, -0.3), (0, 6.75, 0.1), (0, 9.6, -0.5)]
    for i, p in enumerate(pts):
        m.empty("fx_holy_%d" % i, p)


# ------------------------------------------------------------------ chaines, lanternes, bannieres
def chain(m, bone, name, x, z, y_top, y_bot, metal="iron"):
    """Chaine de maillons alternes (de face / de chant) de y_top (accroche) a y_bot."""
    y, k = y_top, 0
    while y - 0.25 > y_bot - 0.12:
        if k % 2 == 0:
            m.box(bone, "%s_m%d" % (name, k), x - 0.0625, y - 0.25, z - U, x + 0.0625, y, z + U,
                  {"all": metal, "+z": "link", "-z": "link"})
        else:
            m.box(bone, "%s_m%d" % (name, k), x - U, y - 0.25, z - 0.0625, x + U, y, z + 0.0625,
                  {"all": metal, "+x": "link", "-x": "link"})
        y -= 0.1875
        k += 1
    return y - 0.0625      # bas du dernier maillon


def lantern(m, bone, name, x, y_top, z, w=0.4375, h=0.5625):
    """Lanterne en bronze sombre : chapeau, toit, anneau, vitres allumees (glow, cadre peint) de la largeur du
    chapeau (silhouette sans encoche), socle, pommeau."""
    hw = w / 2
    gt, gb = y_top - 0.09375, y_top - h + 0.09375
    m.box(bone, "glow_%s_vitre" % name, x - hw, gb, z - hw, x + hw, gt, z + hw,
          {"all": ("lantern_glass", "stretch"), "+y": "bronze", "-y": "bronze"})
    m.box(bone, name + "_chapeau", x - hw, gt, z - hw, x + hw, y_top, z + hw, "wood_d")
    m.box(bone, name + "_toit", x - hw + 0.09375, y_top, z - hw + 0.09375, x + hw - 0.09375, y_top + 0.0625,
          z + hw - 0.09375, "bronze")
    m.box(bone, name + "_anneau", x - 0.0625, y_top + 0.0625, z - U, x + 0.0625, y_top + 0.125, z + U, "iron")
    m.box(bone, name + "_socle", x - hw, gb - 0.0625, z - hw, x + hw, gb, z + hw, "wood_d")
    return y_top + 0.125


def banner(m, bone, s, tag):
    cx, z = s * BANNER_X, ARM_Z
    zf0, zf1 = z - U, z + U                 # toile (1/16)
    zb0, zb1 = z - 2 * U, z + 2 * U         # bordure or (deborde de 1/32 des deux cotes)
    rod_y0, rod_y1 = 8.0625, 8.1875
    # deux chaines courtes jusqu'au bras
    for k, dx in enumerate((-0.40625, 0.40625)):
        chain(m, bone, "ban_%s_ch%d" % (tag, k), cx + dx, z, ARM_Y + U, rod_y1)
    m.box(bone, "ban_%s_tringle" % tag, cx - 0.59375, rod_y0, z - 0.09375, cx + 0.59375, rod_y1, z + 0.09375, "gold")
    for k, dx in enumerate((-0.65625, 0.65625)):
        m.box(bone, "ban_%s_pommeau%d" % (tag, k), cx + dx - 0.0625, rod_y0 - U, z - 0.125, cx + dx + 0.0625, rod_y1 + U,
              z + 0.125, "gold_l")
    top = rod_y0 + U
    ncol = 8
    cw = 1.0 / ncol
    x0 = cx - 0.5
    body_bot = 5.5
    bottoms = [q(body_bot - 0.125 - (3 - min(j, ncol - 1 - j)) * 0.21875) for j in range(ncol)]
    # toile : un grand panneau, puis les colonnes de la pointe (plus minces de 1/64 de chaque cote, enfoncees
    # de 1/16 dans le panneau), chacune posee sur son liseret or
    m.box(bone, "ban_%s_toile" % tag, x0, body_bot, zf0, x0 + 1.0, top, zf1, "navy")
    H = 1.0 / 64
    j = 0
    while j < ncol:
        span = 2 if j == ncol // 2 - 1 else 1
        xa, xb = x0 + j * cw, x0 + (j + span) * cw
        bot = bottoms[j]
        ext_l = U if j == 0 else 0
        ext_r = U if j + span == ncol else 0
        if j in (0, ncol - 1):
            m.box(bone, "ban_%s_pointe%d" % (tag, j), xa - ext_l, bot, zb0, xb + ext_r, body_bot + 0.0625, zb1, "gold")
        else:
            m.box(bone, "ban_%s_queue%d" % (tag, j), xa, bot + 0.125, zf0 + H, xb, body_bot + 0.0625, zf1 - H, "navy")
            m.box(bone, "ban_%s_pointe%d" % (tag, j), xa, bot, zb0, xb, bot + 0.125, zb1, "gold")
        j += span
    # bordures laterales (du liseret de bout a la tringle)
    m.box(bone, "ban_%s_bord_g" % tag, x0 - U, body_bot + 0.0625, zb0, x0 + 0.09375, top, zb1, "gold")
    m.box(bone, "ban_%s_bord_d" % tag, x0 + 1.0 - 0.09375, body_bot + 0.0625, zb0, x0 + 1.0 + U, top, zb1, "gold")
    # etoile sacree rayonnante (relief or devant ET derriere, coeur lumineux)
    sy = 7.28125
    for side, (za, zb) in (("av", (zf1 - U, zf1 + U)), ("ar", (zf0 - U, zf0 + U))):
        b = "ban_%s_%s" % (tag, side)
        m.box(bone, b + "_v", cx - 0.0625, 6.78125, za, cx + 0.0625, 7.71875, zb, "gold_l")
        m.box(bone, b + "_h", cx - 0.28125, sy - 0.0625, za, cx + 0.28125, sy + 0.0625, zb, "gold_l")
        for k, (dx, dy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
            for r in (1, 2):
                px, py = cx + dx * (0.0625 + r * 0.0625), sy + dy * (0.0625 + r * 0.0625)
                m.box(bone, "%s_ray%d%d" % (b, k, r), px - U, py - U, za, px + U, py + U, zb, "gold")
        m.box(bone, b + "_fer", cx - 0.09375, 6.84375, za, cx + 0.09375, 6.96875, zb, "gold")
        m.box(bone, b + "_haut", cx - 0.09375, 7.59375, za, cx + 0.09375, 7.65625, zb, "gold")
        zz = (zb + U) if side == "av" else (za - U)
        m.box(bone, "glow_" + b + "_coeur", cx - 0.0625, sy - 0.0625 - U, min(za, zz) if side == "ar" else za + U,
              cx + 0.0625, sy + 0.0625 + U, zz if side == "av" else zb - U, "glow_gold")


def hangings(m):
    ban = m.bone("banners")
    ch = m.bone("chains")
    la = m.bone("lanterns")

    def side(s, tag):
        banner(m, ban, s, tag)
        # lanterne de la potence interieure (x = +-3.6)
        y = chain(m, ch, "ch_pot_%s" % tag, s * LANTERN_X, ARM_Z, ARM_Y + U, 7.5)
        lantern(m, la, "lant_pot_%s" % tag, s * LANTERN_X, y - 0.125, ARM_Z)
        # lanterne exterieure (bout du bras, a cote de la banniere)
        y = chain(m, ch, "ch_ext_%s" % tag, s * 6.28125, 0.84375, ARM_Y + U, 6.75)
        lantern(m, la, "lant_ext_%s" % tag, s * 6.28125, y - 0.125, 0.84375, w=0.375, h=0.5)
        # petite lanterne cote interieur de la banniere
        y = chain(m, ch, "ch_int_%s" % tag, s * 4.78125, 0.375, ARM_Y + U, 6.4)
        lantern(m, la, "lant_int_%s" % tag, s * 4.78125, y - 0.125, 0.375, w=0.375, h=0.5)
        # lanterne basse posee sur son siege, chaine jusqu'au crochet sous le tuyau
        sx, sy, sz = s * SEAT[0], SEAT[1], SEAT[2]
        top = sy + 0.5625 - U
        lantern(m, la, "lant_bas_%s" % tag, sx, top, sz)
        chain(m, ch, "ch_bas_%s" % tag, sx, sz, HOOK_Y + U, top + 0.125)
    sym(side)


# ------------------------------------------------------------------ etablis, outils, presse
def hammer(m, bone, name, x, y_hang, z, head=0.375, length=0.75, mat="iron"):
    """Marteau suspendu tete en haut, contre le mur (z = face arriere)."""
    m.box(bone, name + "_manche", x - U, y_hang - length, z, x + U, y_hang, z + 0.0625, "wood")
    m.box(bone, name + "_tete", x - head / 2, y_hang, z - U, x + head / 2, y_hang + 0.15625, z + 0.09375, mat)


def wrench(m, bone, name, x, y_hang, z, length=0.5):
    """Cle plate suspendue par l'anneau, machoires ouvertes vers le bas."""
    m.box(bone, name + "_anneau", x - 0.0625, y_hang - 0.0625, z, x + 0.0625, y_hang + 0.0625, z + 0.0625, "iron")
    m.box(bone, name + "_tige", x - U, y_hang - length, z + U * 0.5, x + U, y_hang - 0.0625, z + 0.0625 - U * 0.5, "iron")
    yb = y_hang - length
    m.box(bone, name + "_mors_g", x - 0.09375, yb - 0.125, z, x - U, yb + U, z + 0.0625, "iron")
    m.box(bone, name + "_mors_d", x + U, yb - 0.125, z, x + 0.09375, yb + U, z + 0.0625, "iron")


def rack(m, bone, name, x0, x1, y0, y1, tools):
    """Ratelier d'outils fixe au mur (z = WALL_Z) : planche, barre de suspension, outils."""
    z = WALL_Z + U
    m.box(bone, name + "_barre", x0 + 0.0625, y1 - 0.25, z, x1 - 0.0625, y1 - 0.15625, z + 0.125, "bronze")
    zt = z + 0.125
    for i, (kind, x) in enumerate(tools):
        if kind == "hammer":
            hammer(m, bone, "%s_marteau%d" % (name, i), x, y1 - 0.28125, zt)
        elif kind == "mallet":
            hammer(m, bone, "%s_masse%d" % (name, i), x, y1 - 0.28125, zt, head=0.25, length=0.6875, mat="wood_d")
        elif kind == "wrench":
            wrench(m, bone, "%s_cle%d" % (name, i), x, y1 - 0.40625, zt)
        elif kind == "tongs":
            m.box(bone, "%s_pince%d_tete" % (name, i), x - 0.0625, y1 - 0.375, zt, x + 0.0625, y1 - 0.25, zt + 0.0625, "iron")
            m.box(bone, "%s_pince%d_bras" % (name, i), x - 0.046875, y1 - 0.875, zt + U * 0.5, x + 0.046875, y1 - 0.375,
                  zt + 0.0625 - U * 0.5, "iron")
        elif kind == "file":
            m.box(bone, "%s_lime%d_m" % (name, i), x - U, y1 - 0.5, zt, x + U, y1 - 0.25, zt + 0.0625, "wood")
            m.box(bone, "%s_lime%d_l" % (name, i), x - U, y1 - 0.84375, zt + U, x + U, y1 - 0.5 + U, zt + 0.09375, "iron")


def benches(m):
    be = m.bone("benches")
    # --- etabli gauche : tableau de plans sur chevalet
    cx, ty, cz = BENCH_L
    bz = cz - 0.0625
    m.box(be, "chevalet_pied", cx - 0.5625, ty - U, bz - 0.25, cx + 0.5625, ty + 0.3125 + U, bz + 0.1875, "woodg")
    m.box(be, "chevalet_mat", cx - 0.0625, ty + 0.09375, bz - 0.1875, cx + 0.0625, ty + 0.5, bz - 0.0625, "woodg")
    m.box(be, "tableau_fond", cx - 0.625, ty + 0.375, bz - 0.0625, cx + 0.625, ty + 1.46875, bz + 0.03125, "wood")
    m.box(be, "tableau_plan", cx - 0.53125, ty + 0.46875, bz, cx + 0.53125, ty + 1.375, bz + 0.0625,
          {"all": "wood", "+z": ("blueprint", "stretch")})
    m.box(be, "tableau_cadre_g", cx - 0.6875, ty + 0.34375, bz - U, cx - 0.53125, ty + 1.5, bz + 0.09375, "woodg")
    m.box(be, "tableau_cadre_d", cx + 0.53125, ty + 0.34375, bz - U, cx + 0.6875, ty + 1.5, bz + 0.09375, "woodg")
    m.box(be, "tableau_cadre_h", cx - 0.53125, ty + 1.375, bz - 0.0625 + U, cx + 0.53125, ty + 1.46875, bz + 0.125, "woodg")
    m.box(be, "tableau_cadre_b", cx - 0.53125, ty + 0.375, bz - 0.0625 + U, cx + 0.53125, ty + 0.46875, bz + 0.125, "woodg")
    m.box(be, "tableau_tablette", cx - 0.71875, ty + 0.3125, bz - 0.09375, cx + 0.71875, ty + 0.375 + U, bz + 0.25, "woodg")
    # rouleaux de plans et compas sur l'etabli
    m.box(be, "rouleau_0", cx - 0.875, ty - U, cz + 0.25, cx - 0.5625, ty + 0.09375, cz + 0.375, "robe")
    m.box(be, "rouleau_1", cx + 0.5625, ty - U, cz + 0.3125, cx + 0.84375, ty + 0.0625 + U, cz + 0.40625, "robe")
    # --- etabli arriere gauche : ratelier (marteaux, cles, pinces)
    bx = BENCH_BL[0]
    rack(m, be, "rat_g", bx - 0.71875, bx + 0.71875, 1.4375, 2.5625,
         [("hammer", bx - 0.5), ("hammer", bx - 0.21875), ("mallet", bx + 0.0625), ("wrench", bx + 0.3125),
          ("tongs", bx + 0.53125)])
    # petits outils poses sur l'etabli arriere
    m.box(be, "etau_g", bx + 0.25, 1.0 - U, 0.5, bx + 0.5, 1.15625, 0.75, "iron")
    m.box(be, "etau_g_vis", bx + 0.34375, 1.15625, 0.5625, bx + 0.40625, 1.25, 0.6875, "bronze")
    m.box(be, "burin_g", bx - 0.5, 1.0 - U, 0.6875, bx - 0.15625, 1.0625, 0.75, "iron")
    # --- etabli droit : cristal dore lumineux, ratelier, outils
    cx, ty, cz = BENCH_R
    kx = cx + 0.5
    m.box(be, "cristal_socle", kx - 0.25, ty - U, cz - 0.25, kx + 0.25, ty + 0.0625, cz + 0.25, "gold")
    m.box(be, "cristal_socle2", kx - 0.1875, ty + 0.0625, cz - 0.1875, kx + 0.1875, ty + 0.15625, cz + 0.1875, "gold_l")
    m.box(be, "glow_cristal_coeur", kx - 0.125, ty + 0.125, cz - 0.125, kx + 0.125, ty + 0.8125, cz + 0.125,
          {"all": ("crystal", "stretch")})
    m.box(be, "glow_cristal_ventre", kx - 0.1875, ty + 0.25, cz - 0.15625, kx + 0.1875, ty + 0.65625, cz + 0.15625,
          {"all": ("crystal", "stretch")})
    m.box(be, "glow_cristal_pointe", kx - 0.0625, ty + 0.8125 - U, cz - 0.0625, kx + 0.0625, ty + 0.9375,
          cz + 0.0625, {"all": ("crystal", "stretch")})
    for k, dx in enumerate((-0.1875, 0.1875)):
        m.box(be, "cristal_griffe%d" % k, kx + dx - 0.0625, ty + 0.0625, cz - U, kx + dx + 0.0625, ty + 0.25, cz + U, "gold")
    rack(m, be, "rat_d", cx - 0.875, cx + 0.0625, 1.4375, 2.375,
         [("file", cx - 0.6875), ("file", cx - 0.4375), ("wrench", cx - 0.125)])
    m.box(be, "marteau_pose_manche", cx - 0.6875, ty - U, cz + 0.15625, cx - 0.21875, ty + 0.0625, cz + 0.21875, "wood")
    m.box(be, "marteau_pose_tete", cx - 0.28125, ty - U, cz + 0.0625, cx - 0.15625, ty + 0.09375, cz + 0.3125, "iron")
    m.box(be, "pince_posee", cx - 0.9375, ty - U, cz - 0.25, cx - 0.8125, ty + 0.0625, cz + 0.0625, "iron")


def press(m):
    pr = m.bone("press", pivot=PRESS)
    cx, ty, cz = PRESS
    m.box(pr, "presse_base", cx - 0.5, ty - U, cz - 0.375, cx + 0.5, ty + 0.09375, cz + 0.375, "gold")
    m.box(pr, "presse_base2", cx - 0.40625, ty + 0.09375, cz - 0.28125, cx + 0.40625, ty + 0.15625, cz + 0.28125, "gold_l")
    m.box(pr, "presse_plateau", cx - 0.21875, ty + 0.15625, cz - 0.1875, cx + 0.21875, ty + 0.21875, cz + 0.1875, "iron")
    for k, dx in enumerate((-0.375, 0.375)):
        m.box(pr, "presse_colonne%d" % k, cx + dx - 0.0625, ty + 0.15625, cz - 0.0625, cx + dx + 0.0625, ty + 1.03125,
              cz + 0.0625, "gold")
        m.box(pr, "presse_pied%d" % k, cx + dx - 0.09375, ty + 0.15625 - U, cz - 0.09375, cx + dx + 0.09375, ty + 0.28125,
              cz + 0.09375, "gold_l")
    m.box(pr, "presse_traverse", cx - 0.5, ty + 1.03125, cz - 0.125, cx + 0.5, ty + 1.1875, cz + 0.125, "gold_l")
    m.box(pr, "presse_vis", cx - 0.0625, ty + 1.15625, cz - 0.0625, cx + 0.0625, ty + 1.5, cz + 0.0625, "iron")
    m.box(pr, "presse_ecrou", cx - 0.125, ty + 1.1875, cz - 0.125, cx + 0.125, ty + 1.28125, cz + 0.125, "bronze")
    m.box(pr, "presse_coulisseau", cx - 0.40625, ty + 0.75, cz - 0.09375, cx + 0.40625, ty + 1.03125 + U, cz + 0.09375, "iron")
    m.box(pr, "presse_matrice", cx - 0.1875, ty + 0.65625, cz - 0.15625, cx + 0.1875, ty + 0.75 + U, cz + 0.15625, "bronze")
    m.box(pr, "presse_chapeau", cx - 0.125, ty + 1.5, cz - 0.125, cx + 0.125, ty + 1.65625, cz + 0.125, "iron")
    m.box(pr, "presse_levier", cx - 0.40625, ty + 1.53125, cz - U, cx + 0.40625, ty + 1.59375, cz + U, "iron")
    for k, dx in enumerate((-0.4375, 0.4375)):
        m.box(pr, "presse_boule%d" % k, cx + dx - 0.0625, ty + 1.5, cz - 0.0625, cx + dx + 0.0625, ty + 1.625, cz + 0.0625,
              "gold_l")


def build():
    m = fd.Model("forge_divine_deco")
    statue(m)
    sym(lambda s, tag: wing(m, s, tag))
    halo(m)
    holy(m)
    hangings(m)
    benches(m)
    press(m)
    return m


def main():
    m = build()
    fixed = [] if "--no-structure" in sys.argv else fd.structure_faces(STRUCT)
    print("faces de la structure (obstacles fixes): %d" % len(fixed))
    moved = m.resolve(fixed)
    model = m.export()
    print("forge_divine_deco: %d cubes, %d deplacements du resolveur, texture %dx%d" % (
        len(model["elements"]), moved, fd.TEX, fd.TEX))


if __name__ == "__main__":
    main()
