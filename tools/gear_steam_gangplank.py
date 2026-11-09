#!/usr/bin/env python3
"""The boarding gangplank of the Gear Steamship (gear_steamship), with the shared gangplank system
(docs/PASSERELLES.md, core/Gangplank.java, tools/gangplank/ships_g2.py + gangplanklib.py), without editing them:

    python3 tools/gear_steam_gangplank.py            # gangplanks/gear_steamship.json + models/entity/gangplank_gear_steamship.bbmodel
    python3 tools/gear_steam_gangplank.py compact    # measure the flush fit of the stowed pack on the ship model

The plank: steel style (as the steam paddleboat), 2.4 x 8.0, on the starboard waist between the main mast and the
forecastle stairs, hinged on the outer face of the bulwark at its collision top (6.0, the grid), through a gate in
the copper railing; the stairs climb from the main deck (4.5) to the hinge; the lever stands on the deck aft of
them. Stowed, its compact pack hangs flat under the hinge on the smooth iron plates under the waist cap; its outer
skin wears the dark steel and brass of the steam paddleboat's camouflage cell (the same colours as this hull: the
shared atlas is left as it is).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "gangplank"))
import ships_g2 as g2  # noqa: E402   (its module code fills SPECS for every other ship; only ours is written here)
import gangplanklib as gp  # noqa: E402
import gear_steam_shape as gs  # noqa: E402

SHIP = "gear_steamship"
Z, WIDTH, LENGTH = 8.2, 2.4, 8.0
HINGE_Y = gs.WAIST_BULWARK_TOP
HX = round(gs.hull_x(Z, HINGE_Y), 2)
INNER = round(HX - 0.6, 2)
# the compact pack's fit, measured on the ship model by `compact` (stow_offset, stow_tilt)
STOW_OFFSET, STOW_TILT = 0.16, 0
STOW_DROP = 0.45            # the pack hangs under the copper cap (drawn at 5.5, the collision top is 6.0)

g2.place(SHIP, "starboard", Z, WIDTH, HINGE_Y, HX, gs.MAIN_DECK_Y, INNER, LENGTH, "steel", (-15, 42), rail_gap=False, lever_end=-1)
g2.SPECS[SHIP]["stow_drop"] = STOW_DROP
g2.SPECS[SHIP]["stow_offset"] = STOW_OFFSET
if STOW_TILT:
    g2.SPECS[SHIP]["stow_tilt"] = STOW_TILT

_camo = gp.camo_regions


def camo_regions(ship_id):
    """Our pack wears the steam paddleboat's cell: dark riveted steel with a brass trim, as this hull."""
    return _camo("steam_paddleboat" if ship_id == SHIP else ship_id)


gp.camo_regions = camo_regions


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "compact":
        worst, rows = g2.compact_probe(SHIP)
        off, tilt, gap = g2.fit_stow(rows, g2.SPECS[SHIP].get("stow_drop", g2.STOW_DROP))
        print("%s: model surface up to %.3f outboard of the hinge; flush fit stow_offset %.3f stow_tilt %d (gap %.3f)" % (SHIP, worst, off, tilt, gap))
        print("   ", " ".join("%.2f:%.2f" % r for r in rows))
        return
    g2.write_specs([SHIP])
    s = g2.SPECS[SHIP]
    gp.make_plank(SHIP, s["width"], s["length"], s["style"], handrails=s.get("handrails", True), segments=s.get("segments"))
    print("spec", {k: s[k] for k in ("hinge", "lever", "step", "max_drop", "stow_offset")})


if __name__ == "__main__":
    main()
