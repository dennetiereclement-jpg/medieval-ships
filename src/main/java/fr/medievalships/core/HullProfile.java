package fr.medievalships.core;

/**
 * Shape of the medieval galley hull. MUST stay identical to tools/hull_profile.py, which
 * generates the 3D model. Kept as a static facade: the generic code uses {@link HullShape}
 * through {@link Ships#GALLEY}.
 *
 * <p>Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = waterline),
 * z = forward (+z = bow).
 */
public final class HullProfile {
	public static final double HALF_LENGTH = 10.0;
	/** Extreme ends of the stem and stern posts. */
	public static final double TIP = 10.9;
	public static final double MAIN_DECK_Y = 0.45;
	public static final double RAISED_DECK_Y = 0.95;
	public static final double AFT_DECK_START = -6.6;
	public static final double FORE_DECK_START = 7.2;
	public static final double MAX_HALF_WIDTH = 2.55;
	public static final double MAST_Z = 0.5;
	public static final double MAST_TOP = 13.2;

	private HullProfile() {
	}

	private static HullShape hull() {
		return Ships.GALLEY.hull();
	}

	public static double halfWidth(double z) {
		return hull().halfWidth(z);
	}

	public static double deckY(double z) {
		return hull().deckY(z);
	}

	public static double railY(double z) {
		return hull().railY(z);
	}

	public static double keelY(double z) {
		return hull().keelY(z);
	}

	public static double bottomY(double z, double absX) {
		return hull().bottomY(z, absX);
	}

	/** Half width of the walkable deck (inside of the planking). */
	public static double innerHalfWidth(double z) {
		return hull().innerHalfWidth(z);
	}
}
