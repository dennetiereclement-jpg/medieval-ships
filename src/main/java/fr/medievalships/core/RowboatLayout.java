package fr.medievalships.core;

import java.util.List;

/**
 * The Rowboat ({@code rowboat}): a small clinker-built fishing rowboat of natural brown wood, double-ended, 5 blocks
 * of hull (5.44 post to post), 2 wide, 0.78 of freeboard amidships rising to the two pointed ends, 0.32 of draught.
 * Three thwarts just under the gunwale (the rower in the middle, a passenger aft), a pair of oars pivoting on the
 * tholepins, a mooring rope on the stem post. It floats on a single block of water and is placed like a vanilla boat.
 *
 * <p>Ship-local blocks, shared with tools/rowboat_shape.py (same numbers, same formulas; checked by RowboatTest):
 * x = lateral (+x = port), y = up (0 = the water surface), z = forward (+z = bow).
 */
public final class RowboatLayout {
	// ---- hull (HullShape.Params)
	public static final double HALF_LENGTH = 2.5;
	public static final double TIP = 2.72;
	public static final double MAX_HALF_WIDTH = 1.0;
	/** Plan: hw = max (1 - (|z| / scale) ^ a) ^ b, fore and aft. */
	private static final double[] FORE_PLAN = {2.62, 2.3, 0.56};
	private static final double[] AFT_PLAN = {2.62, 2.3, 0.6};
	/** Keel: depth, rise, power (rocker). */
	private static final double[] KEEL = {0.32, 0.24, 2.2};
	/** Sheer: base, rise fore, rise aft, power. */
	private static final double[] RAIL = {0.78, 0.33, 0.26, 2.6};
	public static final double WATERLINE_Y = 0.0;
	/** Top of the floorboards (the "deck" of the hull shape), under the water surface. */
	public static final double FLOOR_Y = -0.12;
	public static final double DECK_MIN_Z = -2.1;
	public static final double DECK_MAX_Z = 2.1;
	private static final double[][] BOTTOM_SECTION = {{0.0, 1.0}, {0.45, 0.9}, {0.8, 0.55}, {0.97, 0.15}};

	// ---- fittings
	/** The three thwarts: fore, middle (the rower), aft (the passenger). */
	public static final double[] THWART_Z = {1.25, 0.05, -1.15};
	public static final double THWART_TOP = 0.62;
	public static final double THWART_W = 0.5;
	public static final double SEAT_Y = THWART_TOP;
	public static final double PILOT_Z = THWART_Z[1];
	public static final double PASSENGER_Z = THWART_Z[2];
	/** The rower's tholepins, just forward of the middle thwart; the oars pivot there. */
	public static final double OARLOCK_Z = 0.35;
	public static final double OAR_IN = 1.1;
	public static final double OAR_OUT = 2.45;
	public static final double OAR_DOWN_DEG = 18.0;
	public static final double GUNWALE_H = 0.14;
	public static final double POST_TOP = 0.2;
	/** Where a passenger leaving the boat lands by default: in the water beside it (the entity looks for ground first). */
	public static final double DISMOUNT_X = 1.6;

	private RowboatLayout() {
	}

	public static double halfWidth(double z) {
		double[] p = z >= 0 ? FORE_PLAN : AFT_PLAN;
		double t = Math.abs(z) / p[0];
		return t >= 1.0 ? 0.0 : MAX_HALF_WIDTH * Math.pow(1.0 - Math.pow(t, p[1]), p[2]);
	}

	public static double keelY(double z) {
		return -KEEL[0] + KEEL[1] * Math.pow(Math.abs(z) / HALF_LENGTH, KEEL[2]);
	}

	public static double railY(double z) {
		return RAIL[0] + (z >= 0 ? RAIL[1] : RAIL[2]) * Math.pow(Math.abs(z) / HALF_LENGTH, RAIL[3]);
	}

	/** The tholepin pivot of an oar ({@code side} +1 port, -1 starboard), ship-local. */
	public static double[] oarPivot(int side) {
		return new double[] {side * (halfWidth(OARLOCK_Z) * 1.02 + 0.06), railY(OARLOCK_Z) + GUNWALE_H + 0.02, OARLOCK_Z};
	}

	/**
	 * The tip of an oar's blade, ship-local, for a sweep (degrees, positive = blade towards the bow) and a lift
	 * (degrees, positive = blade up) of the rowing animation: where the blade enters and leaves the water.
	 */
	public static double[] oarBlade(int side, double sweepDeg, double liftDeg) {
		double[] p = oarPivot(side);
		double down = Math.toRadians(OAR_DOWN_DEG - liftDeg), sweep = Math.toRadians(sweepDeg);
		double reach = OAR_OUT * Math.cos(down);
		return new double[] {p[0] + side * reach * Math.cos(sweep), p[1] - OAR_OUT * Math.sin(down), p[2] + reach * Math.sin(sweep)};
	}

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = FORE_PLAN[0];
		p.forePowA = FORE_PLAN[1];
		p.forePowB = FORE_PLAN[2];
		p.aftScale = AFT_PLAN[0];
		p.aftPowA = AFT_PLAN[1];
		p.aftPowB = AFT_PLAN[2];
		p.keelDepth = KEEL[0];
		p.keelRise = KEEL[1];
		p.keelPow = KEEL[2];
		p.railBase = RAIL[0];
		p.railRiseFore = RAIL[1];
		p.railRiseAft = RAIL[2];
		p.railPow = RAIL[3];
		p.waterlineY = WATERLINE_Y;
		p.mainDeckY = FLOOR_Y;
		p.deckMinZ = DECK_MIN_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = BOTTOM_SECTION;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		// two seats on the thwarts: the rower (the pilot, seated, not standing) and a passenger behind him; both sit
		// high enough for a seated player's feet to stay out of the water
		spec.seats = List.of(
				new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, SEAT_Y, PILOT_Z, true, new double[] {DISMOUNT_X, 0.0, PILOT_Z}),
				new ShipGeometry.Seat(1, 0.0, SEAT_Y, PASSENGER_Z, false, new double[] {-DISMOUNT_X, 0.0, PASSENGER_Z}));
		// no deck to stand on (the floorboards are under the water): a click anywhere on the boat seats the player
		spec.helm = new ShipGeometry.LocalBox(-MAX_HALF_WIDTH - 0.15, keelY(0) - 0.1, -TIP - 0.1, MAX_HALF_WIDTH + 0.15,
				railY(HALF_LENGTH) + GUNWALE_H + POST_TOP + 0.05, TIP + 0.1);
		spec.probeStep = 0.5;
		spec.probeHeights = new double[] {0.15, 0.6};
		spec.boardMinZ = -1.8;
		spec.boardMaxZ = 1.8;
		spec.avoidZ = THWART_Z;
		return new ShipType("rowboat", "petite barque", new ShipGeometry(hull, spec), RowboatLayout::config);
	}

	/** Light and short: gathers way and stops quickly, turns on the spot with the oars, modest speeds. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.0;
		c.normalSpeed = 3.5;
		c.fastSpeed = 5.0;
		c.reverseSpeed = 1.6;
		c.acceleration = 1.6;
		c.braking = 2.8;
		c.waterDrag = 0.55;
		c.maxTurnRate = 45.0;
		c.minTurnFactor = 0.7;
		c.helmRate = 3.0;
		c.helmReturnRate = 2.0;
		c.turnResponse = 4.0;
		c.turnSpeedLoss = 0.12;
		c.waveRocking = 1.0;
		c.aiWaypointRadius = 3.0;
		c.aiStopRadius = 1.2;
		c.aiLookahead = 6.0;
		c.aiProbeDistance = 14.0;
		c.aiStuckSeconds = 5;
		c.aiTurnAroundSpeed = 0.8;
		c.furlSailWhenStopped = false;
		return c;
	}
}
