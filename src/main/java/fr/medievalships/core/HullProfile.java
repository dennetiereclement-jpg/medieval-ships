package fr.medievalships.core;

/**
 * Shape of the galley hull. MUST stay identical to tools/hull_profile.py, which
 * generates the 3D model: collisions, seats and terrain probes use these formulas.
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

	public static double halfWidth(double z) {
		double a = Math.abs(z) / 10.3;
		if (a >= 1.0) {
			return 0.0;
		}
		return 2.55 * Math.pow(1.0 - Math.pow(a, 2.3), 0.75);
	}

	public static double deckY(double z) {
		return z < AFT_DECK_START || z > FORE_DECK_START ? RAISED_DECK_Y : MAIN_DECK_Y;
	}

	public static double railY(double z) {
		double a = Math.abs(z) / 10.0;
		return 1.6 + a * a * a;
	}

	public static double keelY(double z) {
		double a = Math.abs(z) / 10.0;
		return -1.2 + a * a * a * a;
	}

	/** Half width of the walkable deck (inside of the planking). */
	public static double innerHalfWidth(double z) {
		return Math.max(0.0, 0.97 * halfWidth(z) - 0.12);
	}
}
