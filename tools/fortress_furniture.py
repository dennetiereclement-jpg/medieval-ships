"""Furniture modelled for the Fortress Ship (decoration phase): what the decoration mods lack, or what must carry the
arms of Havre-Fort. The mods' pieces (beds, desk, wardrobe, bookcases, dining tables, chairs, benches, stools, stove,
counter, crates, barrels, sacks, bales, plates, bottles, lanterns) are placed by tools/fortress_decor.py; these are
drawn in the ship's model by tools/generate_fortress.py, in the regions of tools/fortress_texture.py:

  the red carpets with the white tower, wall banners and heater shields with the tower (crossed swords or spears behind
  them), the armour stands in their red surcoats, the weapon racks (spears, halberds, swords), barrels of arrows, the
  war council's campaign map with its tokens, wrought-iron candle chandeliers and candlesticks, the cushioned window
  seat under the stern windows, the inside of the castle's windows, the armourer's anvil, the signal brazier of the
  battlements, the lookout's flag chest, pallets of cut stone and squared timber for the fort (the cargo), crates under
  a lashed canvas, a rolled spare sail, bread and cheese, an inkwell and an hourglass on the captain's desk.

Every builder takes the bone, a name prefix and its placement (ship-local blocks). Element names start with "lit"
(shaded like the rooms) or "glow" (full bright: flames, embers).
"""
import math

import numpy as np

import generate_galleon as gn
import generate_galley as gg
import nautilus_furniture as nf

v3, norm, add_cube, beam, Bone = gg.v3, gg.norm, gg.add_cube, gg.beam, gg.Bone
ry = gg.ry
disc, turned = gn.disc, gn.turned
frame, yaw_of = nf.frame, nf.yaw_of
EYE = np.eye(3)


# ---------------------------------------------------------------- small parts
def candle(bone, name, p, h=0.2, holder="iron"):
    """A cream candle in a cup, its flame full bright."""
    p = v3(*p)
    disc(bone, "lit_%s_cup" % name, p + v3(0, 0.02, 0), (0, 1, 0), 0.055, 0.04, holder)
    add_cube(bone, "lit_%s_wax" % name, p + v3(0, 0.04 + h / 2, 0), EYE, (0.055, h, 0.055), "candle")
    add_cube(bone, "glow_%s_flame" % name, p + v3(0, 0.08 + h, 0), EYE, (0.035, 0.08, 0.035), "glow")


def candlestick(bone, name, p, h=0.32):
    """A wrought-iron candlestick: a round foot, a turned stem, the candle."""
    p = v3(*p)
    disc(bone, "lit_%s_foot" % name, p + v3(0, 0.02, 0), (0, 1, 0), 0.1, 0.04, "iron", n=3)
    turned(bone, "lit_%s_stem" % name, p + v3(0, 0.04, 0), p + v3(0, h, 0), [(0, 0.05), (0.4, 0.08), (0.6, 0.04), (1, 0.06)], "iron")
    candle(bone, name + "_c", p + v3(0, h, 0), h=0.18)


def sword(bone, name, hilt, tip, flat=(1, 0, 0)):
    """A sword from its pommel end (hilt) to its tip: steel blade, an iron cross guard across `flat`, a leather grip,
    a bronze pommel."""
    hilt, tip = v3(*hilt), v3(*tip)
    d = norm(tip - hilt)
    f = norm(v3(*flat) - np.dot(v3(*flat), d) * d)
    grip = hilt + d * 0.22
    beam(bone, "lit_%s_blade" % name, grip + d * 0.03, tip, 0.025, "blade", width=0.075, up=np.cross(d, f))
    beam(bone, "lit_%s_guard" % name, grip - f * 0.15, grip + f * 0.15, 0.04, "iron", width=0.05)
    beam(bone, "lit_%s_grip" % name, hilt + d * 0.04, grip, 0.045, "leather")
    disc(bone, "lit_%s_pommel" % name, hilt + d * 0.03, d, 0.04, 0.06, "bronze")


def spear(bone, name, foot, top, kind="spear", blade_dir=(1, 0, 0)):
    """A spear (leaf head) or a halberd (axe blade, beak and spike) on an ash shaft from `foot` to `top`."""
    foot, top = v3(*foot), v3(*top)
    d = norm(top - foot)
    b = norm(v3(*blade_dir) - np.dot(v3(*blade_dir), d) * d)
    beam(bone, "lit_%s_shaft" % name, foot, top, 0.055, "wood_mid")
    beam(bone, "lit_%s_ferrule" % name, foot, foot + d * 0.08, 0.07, "iron")
    if kind == "halberd":
        beam(bone, "lit_%s_spike" % name, top - d * 0.05, top + d * 0.32, 0.03, "blade", width=0.06, up=np.cross(d, b))
        add_cube(bone, "lit_%s_axe" % name, top - d * 0.14 + b * 0.16, np.column_stack([b, d, np.cross(b, d)]), (0.26, 0.3, 0.02), "blade")
        beam(bone, "lit_%s_beak" % name, top - d * 0.14, top - d * 0.18 - b * 0.18, 0.03, "iron", width=0.04)
        beam(bone, "lit_%s_socket" % name, top - d * 0.3, top, 0.07, "iron")
    else:
        beam(bone, "lit_%s_socket" % name, top - d * 0.02, top + d * 0.1, 0.065, "iron")
        beam(bone, "lit_%s_head" % name, top + d * 0.08, top + d * 0.36, 0.025, "blade", width=0.1, up=np.cross(d, b))
        beam(bone, "lit_%s_point" % name, top + d * 0.34, top + d * 0.44, 0.02, "blade", width=0.04, up=np.cross(d, b))


# ---------------------------------------------------------------- walls
def wall_banner(bone, name, center, normal, w, h):
    """A red banner with the white tower hung against a wall from an iron rod with bronze finials."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.04
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.01), {"all": None, "+3": "banner", "-3": "banner"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    top = c + v3(0, h / 2 - 0.02, 0) + n * 0.02
    beam(bone, "lit_%s_rod" % name, top - u * (w / 2 + 0.1), top + u * (w / 2 + 0.1), 0.045, "iron")
    for k, s in enumerate((1, -1)):
        disc(bone, "lit_%s_finial_%d" % (name, k), top + u * s * (w / 2 + 0.13), u, 0.04, 0.06, "bronze")
        add_cube(bone, "lit_%s_hook_%d" % (name, k), top + u * s * (w / 2 - 0.05) - n * 0.03, R, (0.04, 0.08, 0.06), "iron")


def wall_shield(bone, name, center, normal, w=0.62, h=0.78, behind="swords"):
    """A heater shield with the white tower on the red field and a gold rim, hung on a wall; two crossed swords (or
    spears) behind it."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.09
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.01), {"all": None, "+3": "shield"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    add_cube(bone, "lit_%s_back" % name, c - n * 0.03 + v3(0, h * 0.12, 0), R, (w * 0.86, h * 0.6, 0.04), "wood_dark")
    if behind == "swords":
        for k, s in enumerate((1, -1)):
            a = c - n * 0.06 + u * s * 0.42 - v3(0, 0.5, 0)
            b = c - n * 0.06 - u * s * 0.42 + v3(0, 0.52, 0)
            sword(bone, "%s_sword_%d" % (name, k), a, b, flat=n)
    elif behind == "spears":
        for k, s in enumerate((1, -1)):
            spear(bone, "%s_spear_%d" % (name, k), c - n * 0.06 + u * s * 0.6 - v3(0, 0.62, 0), c - n * 0.06 - u * s * 0.5 + v3(0, 0.48, 0),
                  blade_dir=n)


def inner_window(bone, name, c, normal, w, h, arch=False):
    """The inside of a castle window (the leaded panes seen from the room), a dark wooden frame, a pale stone sill;
    arch: an arched window (its round-topped frame drawn in the texture: only the sill is added)."""
    R, u, n = frame(normal)
    c = v3(*c) + n * 0.012
    if arch:
        add_cube(bone, "lit_" + name, c, R, (w, h, 0.01), {"all": None, "+3": "arch_dark"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
        add_cube(bone, "lit_%s_sill" % name, c - v3(0, h / 2 + 0.04, 0) + n * 0.06, R, (w + 0.24, 0.08, 0.14), "stone_light")
        return
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.01), {"all": None, "+3": "window_in"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    fr = 0.08
    for k, s in enumerate((1, -1)):
        add_cube(bone, "lit_%s_jamb_%d" % (name, k), c + u * s * (w / 2 + fr / 2) + n * 0.02, R, (fr, h + fr, 0.05), "wood_dark")
    add_cube(bone, "lit_%s_lintel" % name, c + v3(0, h / 2 + fr / 2, 0) + n * 0.02, R, (w + 2 * fr, fr, 0.05), "wood_dark")
    add_cube(bone, "lit_%s_sill" % name, c - v3(0, h / 2 + fr / 2, 0) + n * 0.06, R, (w + 3 * fr, fr, 0.14), "stone_light")


# ---------------------------------------------------------------- the rooms' pieces
def tower_rug(bone, name, p, w, l, yaw=0.0):
    """The red carpet with the white tower, flat on the floor (w across x, l along z before the yaw)."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, 0.014, 0), R, (w, 0.02, l), {"all": None, "+2": "tower_rug"}, stretch=True,
             u_dir=R @ v3(1, 0, 0), v_dir=R @ v3(0, 0, 1))


def iron_chandelier(parent, name, hook, drop=0.45, r=0.5, n=6):
    """A wrought-iron cartwheel chandelier on its chain from a ceiling hook: a ring of iron bars, four spokes, a candle on
    every bend of the ring. Its own bone (named lantern_*) swings with the lanterns."""
    hook = v3(*hook)
    b = Bone("lantern_" + name, origin=tuple(hook), parent=parent)
    add_cube(b, "lit_%s_hook" % name, hook - v3(0, 0.03, 0), EYE, (0.16, 0.06, 0.16), "iron")
    for k in range(3):
        add_cube(b, "lit_%s_chain_%d" % (name, k), hook - v3(0, 0.06 + (k + 0.5) * drop / 3, 0), ry(k * math.pi / 4),
                 (0.05, drop / 3 - 0.02, 0.05), "iron")
    hub = hook - v3(0, drop + 0.1, 0)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        q = hub + v3(math.cos(a) * r, -0.05, math.sin(a) * r)
        beam(b, "lit_%s_strap_%d" % (name, k), hook - v3(0, drop, 0), q, 0.03, "iron")
        beam(b, "lit_%s_spoke_%d" % (name, k), hub, q, 0.035, "iron")
    pts = [hub + v3(math.cos(2 * math.pi * k / n) * r, -0.05, math.sin(2 * math.pi * k / n) * r) for k in range(n)]
    for k in range(n):
        beam(b, "lit_%s_ring_%d" % (name, k), pts[k], pts[(k + 1) % n], 0.045, "iron", extend=0.02)
        candle(b, "%s_candle_%d" % (name, k), pts[k] + v3(0, 0.02, 0), h=0.16)
    disc(b, "lit_%s_boss" % name, hub, (0, 1, 0), 0.08, 0.1, "iron", n=3)
    return b


def window_seat(bone, name, x0, x1, z_wall, y, depth=0.55, normal=1.0):
    """The cushioned bench under the stern windows: a dark carved front with an iron rail, the red velvet cushion,
    round bolsters at the ends, back cushions against the wall."""
    zf = z_wall + normal * depth
    zc = (z_wall + zf) / 2
    xc, w = (x0 + x1) / 2, x1 - x0
    add_cube(bone, "lit_%s_body" % name, (xc, y + 0.2, zc), EYE, (w, 0.36, depth), "wood_dark")
    add_cube(bone, "lit_%s_rail" % name, (xc, y + 0.3, zf + normal * 0.01), EYE, (w + 0.02, 0.05, 0.03), "iron")
    add_cube(bone, "lit_%s_plinth" % name, (xc, y + 0.03, zf - normal * 0.02), EYE, (w + 0.04, 0.06, 0.06), "stone_light")
    add_cube(bone, "lit_%s_cushion" % name, (xc, y + 0.43, zc), EYE, (w - 0.06, 0.1, depth - 0.06), "velvet_red")
    for k, s in enumerate((-1, 1)):
        disc(bone, "lit_%s_bolster_%d" % (name, k), ((x0 + 0.12) if s < 0 else (x1 - 0.12), y + 0.55, zc), (1, 0, 0), 0.1, 0.22,
             "velvet_red", n=3)
    nb = max(1, int(round(w / 0.9)))
    for k in range(nb):
        xa = x0 + (k + 0.5) * w / nb
        add_cube(bone, "lit_%s_back_%d" % (name, k), (xa, y + 0.72, z_wall + normal * 0.09), gg.rx(normal * -0.12),
                 (w / nb - 0.1, 0.42, 0.12), "velvet_red")


def armour_stand(bone, name, p, facing="bow", held="spear"):
    """A suit of plate armour on its stand in the red surcoat with the white tower: greaves, mail skirt, pauldrons,
    arms, gauntlets, a great helm with its eye slit and a red crest; a spear (or a shield) at its side."""
    p = v3(*p)
    R = ry(yaw_of(facing))
    disc(bone, "lit_%s_base" % name, p + v3(0, 0.04, 0), (0, 1, 0), 0.32, 0.08, "wood_dark", n=3)
    add_cube(bone, "lit_%s_post" % name, p + v3(0, 0.3, 0), R, (0.08, 0.5, 0.08), "wood_dark")
    for k, s in enumerate((1, -1)):
        add_cube(bone, "lit_%s_greave_%d" % (name, k), p + R @ v3(s * 0.11, 0.38, 0), R, (0.15, 0.64, 0.17), "blade")
        add_cube(bone, "lit_%s_sabaton_%d" % (name, k), p + R @ v3(s * 0.11, 0.09, 0.04), R, (0.16, 0.1, 0.26), "iron")
        add_cube(bone, "lit_%s_knee_%d" % (name, k), p + R @ v3(s * 0.11, 0.62, 0.03), R, (0.17, 0.1, 0.16), "iron")
    add_cube(bone, "lit_%s_mail" % name, p + R @ v3(0, 0.82, 0), R, (0.42, 0.3, 0.26), "mail")
    add_cube(bone, "lit_%s_surcoat" % name, p + R @ v3(0, 1.08, 0), R, (0.46, 0.56, 0.28),
             {"all": "red_paint", "+3": "surcoat", "-3": "surcoat"}, stretch=True)
    add_cube(bone, "lit_%s_belt" % name, p + R @ v3(0, 0.9, 0), R, (0.48, 0.06, 0.3), "leather")
    add_cube(bone, "lit_%s_gorget" % name, p + R @ v3(0, 1.39, 0), R, (0.26, 0.08, 0.22), "iron")
    for k, s in enumerate((1, -1)):
        disc(bone, "lit_%s_pauldron_%d" % (name, k), p + R @ v3(s * 0.3, 1.3, 0), R @ v3(1, 0.3 * s, 0), 0.14, 0.18, "blade", n=3)
        add_cube(bone, "lit_%s_arm_%d" % (name, k), p + R @ v3(s * 0.31, 1.04, 0.02), R @ gg.rz(s * 0.06), (0.12, 0.42, 0.13), "blade")
        add_cube(bone, "lit_%s_gauntlet_%d" % (name, k), p + R @ v3(s * 0.32, 0.78, 0.05), R, (0.12, 0.14, 0.14), "iron")
    add_cube(bone, "lit_%s_helm" % name, p + R @ v3(0, 1.6, 0), R, (0.26, 0.32, 0.27), "blade")
    add_cube(bone, "lit_%s_slit" % name, p + R @ v3(0, 1.64, 0.136), R, (0.2, 0.035, 0.01), "bore")
    add_cube(bone, "lit_%s_crest" % name, p + R @ v3(0, 1.8, -0.02), R, (0.05, 0.1, 0.24), "red_paint")
    if held == "spear":
        spear(bone, name + "_spear", p + R @ v3(0.42, 0.0, 0.08), p + R @ v3(0.42, 2.05, 0.1), blade_dir=R @ v3(0, 0, 1))
    elif held == "shield":
        add_cube(bone, "lit_%s_shield" % name, p + R @ v3(-0.4, 0.62, 0.12), R @ gg.rz(0.12) @ ry(-0.5), (0.5, 0.62, 0.01),
                 {"all": None, "+3": "shield", "-3": "shield"}, stretch=True)


def weapon_rack(bone, name, p, normal, l=1.6, top=1.5, items=("spear", "halberd", "spear", "halberd", "spear")):
    """A floor rack against a wall (normal: into the room): a slotted foot board, a cross bar on two posts, the weapons
    standing in it and leaning a little back against the bar; a pair of swords hanging from the bar's ends."""
    R, u, n = frame(normal)
    p = v3(*p)
    add_cube(bone, "lit_%s_foot" % name, p + v3(0, 0.08, 0) + n * 0.18, R, (l, 0.16, 0.3), "wood_dark")
    for k, s in enumerate((1, -1)):
        add_cube(bone, "lit_%s_post_%d" % (name, k), p + u * s * (l / 2 - 0.05) + v3(0, top / 2, 0) + n * 0.06, R, (0.09, top, 0.09),
                 "wood_dark")
    add_cube(bone, "lit_%s_bar" % name, p + v3(0, top - 0.1, 0) + n * 0.06, R, (l, 0.1, 0.08), "wood_dark")
    add_cube(bone, "lit_%s_bar2" % name, p + v3(0, top * 0.55, 0) + n * 0.06, R, (l, 0.07, 0.06), "wood_dark")
    m = len(items)
    for k, kind in enumerate(items):
        t = (k + 0.5) / m - 0.5
        foot = p + u * (t * (l - 0.3)) + n * 0.2 + v3(0, 0.1, 0)
        if kind == "sword":
            sword(bone, "%s_sw_%d" % (name, k), foot + v3(0, 0.9, 0) - n * 0.1, foot + v3(0, 0.05, 0), flat=u)
        else:
            topp = foot + v3(0, top + (0.35 if kind == "spear" else 0.2), 0) - n * 0.12
            spear(bone, "%s_w_%d" % (name, k), foot, topp, kind=kind, blade_dir=u)


def arrow_barrel(bone, name, p, n=14, r=0.27, h=0.75, seed=0):
    """An open barrel full of arrows: the staves and hoops, the shafts sticking out at all angles, their fletching."""
    p = v3(*p)
    turned(bone, "lit_%s_staves" % name, p + v3(0, 0.02, 0), p + v3(0, h, 0), [(0, 1.7 * r), (0.22, 1.95 * r), (0.78, 1.7 * r), (1, 0)], "wood_mid")
    for k, t in enumerate((0.12, 0.88)):
        disc(bone, "lit_%s_hoop_%d" % (name, k), p + v3(0, h * t, 0), (0, 1, 0), r * (0.9 if t > 0.5 else 0.89), 0.05, "iron")
    disc(bone, "lit_%s_fill" % name, p + v3(0, h - 0.04, 0), (0, 1, 0), 0.78 * r, 0.015, "dark_wood")
    rng = np.random.RandomState(7 + seed)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        rr = r * rng.uniform(0.1, 0.65)
        foot = p + v3(math.cos(a) * rr, h - 0.3, math.sin(a) * rr)
        tilt = v3(math.cos(a) * rng.uniform(0.05, 0.25), 1, math.sin(a) * rng.uniform(0.05, 0.25))
        tip = foot + norm(tilt) * rng.uniform(0.65, 0.8)
        beam(bone, "lit_%s_shaft_%d" % (name, k), foot, tip, 0.02, "wood_light")
        add_cube(bone, "lit_%s_fletch_%d" % (name, k), tip - norm(tilt) * 0.08, ry(a), (0.06, 0.14, 0.012), "fletching")


def war_map(bone, name, p, w, l, yaw=0.0, seed=0):
    """The campaign map spread on the council table: the map, red and white tokens, a dagger pinning a corner, two iron
    candlesticks."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, 0.008, 0), R, (w, 0.012, l), {"all": None, "+2": "war_map"}, stretch=True,
             u_dir=R @ v3(1, 0, 0), v_dir=R @ v3(0, 0, 1))
    rng = np.random.RandomState(31 + seed)
    for k in range(7):
        q = p + R @ v3(rng.uniform(-0.4, 0.4) * w, 0.04, rng.uniform(-0.35, 0.35) * l)
        add_cube(bone, "lit_%s_token_%d" % (name, k), q, ry(rng.uniform(0, 1.5)), (0.07, 0.07, 0.07), "red_paint" if k % 2 else "white_paint")
    corner = p + R @ v3(w * 0.42, 0.02, l * 0.38)
    sword(bone, name + "_dagger", corner + v3(0, 0.28, 0), corner, flat=R @ v3(1, 0, 0))
    for k, s in enumerate((1, -1)):
        candlestick(bone, "%s_light_%d" % (name, k), p + R @ v3(s * (w / 2 + 0.12), 0.0, -s * 0.15))


def anvil(bone, name, p, facing="bow"):
    """The armourer's anvil on its oak stump, a hammer and tongs beside it."""
    p = v3(*p)
    R = ry(yaw_of(facing))
    turned(bone, "lit_%s_stump" % name, p, p + v3(0, 0.45, 0), [(0, 0.6), (0.15, 0.52), (1, 0)], "wood_mid")
    disc(bone, "lit_%s_top" % name, p + v3(0, 0.455, 0), (0, 1, 0), 0.25, 0.01, "end_grain")
    add_cube(bone, "lit_%s_foot" % name, p + v3(0, 0.52, 0), R, (0.26, 0.12, 0.42), "iron")
    add_cube(bone, "lit_%s_waist" % name, p + v3(0, 0.63, 0), R, (0.16, 0.12, 0.3), "iron")
    add_cube(bone, "lit_%s_face" % name, p + v3(0, 0.74, -0.02), R, (0.24, 0.1, 0.5), "blade")
    beam(bone, "lit_%s_horn" % name, p + R @ v3(0, 0.75, 0.22), p + R @ v3(0, 0.77, 0.44), 0.08, "iron", width=0.12)
    beam(bone, "lit_%s_horn_tip" % name, p + R @ v3(0, 0.77, 0.43), p + R @ v3(0, 0.79, 0.52), 0.04, "iron", width=0.05)
    q = p + R @ v3(0.05, 0.79, -0.1)
    beam(bone, "lit_%s_hammer" % name, q, q + R @ v3(0.28, 0.02, 0.06), 0.035, "wood_mid")
    add_cube(bone, "lit_%s_hammer_head" % name, q + R @ v3(0.3, 0.03, 0.06), R, (0.06, 0.07, 0.15), "iron")
    beam(bone, "lit_%s_tongs_0" % name, p + R @ v3(-0.2, 0.02, 0.32), p + R @ v3(-0.08, 0.02, -0.1), 0.025, "iron")
    beam(bone, "lit_%s_tongs_1" % name, p + R @ v3(-0.24, 0.02, 0.3), p + R @ v3(-0.08, 0.02, -0.1), 0.025, "iron")


def brazier(bone, name, p, r=0.32):
    """The signal brazier of the battlements: an iron fire basket on three legs, glowing coals heaped in it, a few
    flames (full bright)."""
    p = v3(*p)
    top = p + v3(0, 0.75, 0)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        beam(bone, "lit_%s_leg_%d" % (name, k), p + v3(math.cos(a) * r * 1.1, 0, math.sin(a) * r * 1.1), top + v3(math.cos(a) * r * 0.7, 0, math.sin(a) * r * 0.7),
             0.05, "iron")
    disc(bone, "lit_%s_bowl" % name, top, (0, 1, 0), r * 0.75, 0.08, "iron", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        q0 = top + v3(math.cos(a) * r * 0.75, 0.02, math.sin(a) * r * 0.75)
        q1 = top + v3(math.cos(a) * r, 0.28, math.sin(a) * r)
        beam(bone, "lit_%s_bar_%d" % (name, k), q0, q1, 0.03, "iron")
    disc(bone, "lit_%s_rim" % name, top + v3(0, 0.27, 0), (0, 1, 0), r, 0.04, "iron", n=3)
    disc(bone, "glow_%s_coals" % name, top + v3(0, 0.12, 0), (0, 1, 0), r * 0.82, 0.16, "embers", n=3)
    for k, (dx, dz, hh) in enumerate(((0.0, 0.0, 0.3), (0.12, 0.08, 0.2), (-0.1, 0.06, 0.18), (0.02, -0.12, 0.22))):
        add_cube(bone, "glow_%s_flame_%d" % (name, k), top + v3(dx, 0.2 + hh / 2, dz), ry(k * 0.7), (0.09, hh, 0.09), "glow")


def flag_chest(bone, name, p, yaw=0.0):
    """The lookout's chest of signal flags: an open wooden box, rolled red and white flags standing in it."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_%s_box" % name, p + v3(0, 0.22, 0), R, (0.7, 0.44, 0.45), {"all": "wood_mid", "+2": "dark_wood"})
    add_cube(bone, "lit_%s_lid" % name, p + R @ v3(0, 0.62, -0.25), R @ gg.rx(-0.25), (0.72, 0.4, 0.04), "wood_dark")
    for k, (dx, dz, reg) in enumerate(((-0.22, -0.08, "cloth_roll"), (-0.05, 0.08, "white_paint"), (0.12, -0.06, "cloth_roll"),
                                       (0.24, 0.1, "white_paint"), (0.02, -0.12, "cloth_roll"))):
        q = p + R @ v3(dx, 0.2, dz)
        disc(bone, "lit_%s_flag_%d" % (name, k), q + v3(0, 0.28, 0), (0.05 * dx, 1, 0.05 * dz), 0.06, 0.56, reg)
        disc(bone, "lit_%s_staff_%d" % (name, k), q + v3(0, 0.62, 0), (0, 1, 0), 0.02, 0.14, "wood_dark")


def stone_pallet(bone, name, p, yaw=0.0, cols=2, rows=2, layers=2, s=0.5):
    """A pallet of cut stone for the fort: three slats on runners, dressed stone blocks stacked with gaps, two rope
    lashings over them."""
    p = v3(*p)
    R = ry(yaw)
    W, D = cols * (s + 0.04) + 0.06, rows * (s + 0.04) + 0.06
    for k, dx in enumerate(np.linspace(-W / 2 + 0.08, W / 2 - 0.08, 3)):
        add_cube(bone, "lit_%s_runner_%d" % (name, k), p + R @ v3(dx, 0.05, 0), R, (0.12, 0.1, D), "wood_dark")
    add_cube(bone, "lit_%s_deck" % name, p + v3(0, 0.12, 0), R, (W, 0.04, D), "wood_mid")
    for ly in range(layers):
        for i in range(cols):
            for j in range(rows):
                if ly == layers - 1 and (i + j) % 3 == 2:
                    continue
                c = p + R @ v3((i - (cols - 1) / 2) * (s + 0.04), 0.14 + ly * (s + 0.01) + s / 2, (j - (rows - 1) / 2) * (s + 0.04))
                add_cube(bone, "lit_%s_stone_%d_%d_%d" % (name, ly, i, j), c, R, (s, s, s), "stone_light" if (i + j + ly) % 2 else "stone")
    top = 0.14 + layers * (s + 0.01)
    for k, t in enumerate((-0.25, 0.25)):
        add_cube(bone, "lit_%s_lash_%d" % (name, k), p + R @ v3(t * W, top / 2 + 0.06, 0), R, (0.04, top - 0.04, D + 0.03), "rope")


def timber_stack(bone, name, p, yaw=0.0, l=2.2, n=(3, 2), s=0.3):
    """Squared timber for the fort's works: beams laid along the length (before the yaw: along z) on two chocks, a rope."""
    p = v3(*p)
    R = ry(yaw)
    cols, layers = n
    W = cols * (s + 0.03)
    for k, dz in enumerate((-l * 0.32, l * 0.32)):
        add_cube(bone, "lit_%s_chock_%d" % (name, k), p + R @ v3(0, 0.06, dz), R, (W + 0.1, 0.12, 0.18), "wood_dark")
    for ly in range(layers):
        for i in range(cols - (ly % 2)):
            x = (i - (cols - 1 - (ly % 2)) / 2) * (s + 0.03)
            add_cube(bone, "lit_%s_beam_%d_%d" % (name, ly, i), p + R @ v3(x, 0.12 + ly * (s + 0.01) + s / 2, 0.02 * (i % 2)), R,
                     (s, s, l - 0.04 * (i % 2)), {"all": "mast", "+3": "end_grain", "-3": "end_grain"})
    for k, dz in enumerate((-l * 0.32, l * 0.32)):
        add_cube(bone, "lit_%s_rope_%d" % (name, k), p + R @ v3(0, 0.12 + layers * (s + 0.01) / 2, dz), R,
                 (W + 0.03, layers * (s + 0.01) + 0.02, 0.04), "rope")


def tarp_stack(bone, name, p, yaw=0.0, w=2.0, d=1.0, h=1.0):
    """Crates under a canvas lashed down: the cover over the stack, its skirts hanging, two ropes over it pegged at
    the foot."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_%s_cover" % name, p + v3(0, h - 0.04, 0), R, (w + 0.06, 0.08, d + 0.06), "awning")
    for k, s in enumerate((1, -1)):
        add_cube(bone, "lit_%s_skirt_x_%d" % (name, k), p + R @ v3(s * (w / 2 + 0.03), h * 0.6, 0), R, (0.03, h * 0.75, d + 0.06), "awning")
        add_cube(bone, "lit_%s_skirt_z_%d" % (name, k), p + R @ v3(0, h * 0.6, s * (d / 2 + 0.03)), R, (w + 0.06, h * 0.75, 0.03), "awning")
    for k, t in enumerate((-0.28, 0.28)):
        add_cube(bone, "lit_%s_rope_%d" % (name, k), p + R @ v3(t * w, h * 0.5, 0), R, (0.04, h + 0.02, d + 0.1), "rope")


def sail_roll(bone, name, p, yaw=0.0, l=2.4, r=0.22):
    """A spare red sail rolled and tied, lying on the floor (along z before the yaw)."""
    p = v3(*p)
    d = ry(yaw) @ v3(0, 0, 1)
    disc(bone, "lit_%s" % name, p + v3(0, r, 0), d, r, l, "cloth_roll", n=3)
    for k, t in enumerate((-0.35, 0.0, 0.35)):
        disc(bone, "lit_%s_tie_%d" % (name, k), p + v3(0, r, 0) + d * (t * l), d, r + 0.015, 0.05, "rope", n=3)


def bread_cheese(bone, name, p):
    """Two loaves of bread and a cheese wheel with a wedge cut out, on a board."""
    p = v3(*p)
    add_cube(bone, "lit_%s_board" % name, p + v3(0, 0.015, 0), ry(0.2), (0.5, 0.03, 0.32), "wood_light")
    for k, (dx, dz, a) in enumerate(((-0.12, -0.04, 0.3), (0.0, 0.08, -0.2))):
        add_cube(bone, "lit_%s_loaf_%d" % (name, k), p + v3(dx, 0.08, dz), ry(a), (0.28, 0.1, 0.14), "bread")
        add_cube(bone, "lit_%s_loaf_top_%d" % (name, k), p + v3(dx, 0.14, dz), ry(a), (0.22, 0.04, 0.1), "bread")
    disc(bone, "lit_%s_cheese" % name, p + v3(0.15, 0.08, -0.03), (0, 1, 0), 0.1, 0.1, "cheese", n=3)


def inkwell(bone, name, p):
    """An inkwell with a quill and a sealed letter, on the desk."""
    p = v3(*p)
    disc(bone, "lit_%s_pot" % name, p + v3(0, 0.035, 0), (0, 1, 0), 0.04, 0.07, "bore")
    beam(bone, "lit_%s_quill" % name, p + v3(0, 0.05, 0), p + v3(0.08, 0.26, 0.05), 0.012, "white_paint", width=0.035)
    add_cube(bone, "lit_%s_letter" % name, p + v3(-0.18, 0.006, 0.08), ry(0.4), (0.18, 0.012, 0.13), "parchment")
    disc(bone, "lit_%s_seal" % name, p + v3(-0.18, 0.014, 0.08), (0, 1, 0), 0.025, 0.008, "red_paint")


def hourglass(bone, name, p):
    p = v3(*p)
    for k, y in enumerate((0.01, 0.23)):
        disc(bone, "lit_%s_plate_%d" % (name, k), p + v3(0, y, 0), (0, 1, 0), 0.06, 0.02, "wood_dark")
    for k in range(3):
        a = 2 * math.pi * k / 3
        add_cube(bone, "lit_%s_rod_%d" % (name, k), p + v3(math.cos(a) * 0.05, 0.12, math.sin(a) * 0.05), EYE, (0.015, 0.22, 0.015), "bronze")
    turned(bone, "lit_%s_glass" % name, p + v3(0, 0.02, 0), p + v3(0, 0.22, 0), [(0, 0.08), (0.4, 0.03), (0.6, 0.08), (1, 0)], "glass")


def dice_cards(bone, name, p):
    """Dice and a hand of cards on the crew's table."""
    p = v3(*p)
    for k, (dx, dz) in enumerate(((0.0, 0.0), (0.06, 0.05))):
        add_cube(bone, "lit_%s_die_%d" % (name, k), p + v3(dx, 0.025, dz), ry(0.3 * k), (0.05, 0.05, 0.05), "white_paint")
    for k in range(4):
        add_cube(bone, "lit_%s_card_%d" % (name, k), p + v3(-0.15 + 0.03 * k, 0.004 + 0.002 * k, 0.12), ry(0.25 * k - 0.4), (0.07, 0.004, 0.1),
                 "parchment")


BUILDERS = {"candle": candle, "candlestick": candlestick, "wall_banner": wall_banner, "wall_shield": wall_shield, "inner_window": inner_window,
            "tower_rug": tower_rug, "iron_chandelier": iron_chandelier, "window_seat": window_seat, "armour_stand": armour_stand,
            "weapon_rack": weapon_rack, "arrow_barrel": arrow_barrel, "war_map": war_map, "anvil": anvil, "brazier": brazier,
            "flag_chest": flag_chest, "stone_pallet": stone_pallet, "timber_stack": timber_stack, "tarp_stack": tarp_stack,
            "sail_roll": sail_roll, "bread_cheese": bread_cheese, "inkwell": inkwell, "hourglass": hourglass, "dice_cards": dice_cards}
