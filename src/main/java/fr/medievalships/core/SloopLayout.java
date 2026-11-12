package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The trade sloop ({@code trade_sloop}): a small merchant sailing boat, 15 blocks of hull (20 with the
 * bowsprit), 4.6 wide. Brown planking with a wide band of blue strakes along the sides, a raised bow with
 * a long bowsprit, one mast with a big gaff mainsail and a large jib, a walkable deck with a few crates and
 * barrels, a small raised stern platform where the pilot stands at the tiller; 5 places.
 *
 * <p>The numbers are mirrored in {@code tools/sloop_shape.py} (the model generator); the collision hull,
 * the seats and the probes come from them (checked by {@code SloopTest}).
 */
public final class SloopLayout {
	public static final double HALF_LENGTH = 7.5;
	public static final double TIP = 8.2;
	public static final double MAX_HALF_WIDTH = 2.3;
	/** The water is 0.1 block above the model origin (1.30.0: 0.6 deeper, just under the blue band; a laden merchant). */
	public static final double WATERLINE_Y = 0.1;
	public static final double MAIN_DECK_Y = 0.6;
	/** Small raised stern platform (storage and the tiller), one step up from the main deck. */
	public static final double AFT_DECK_Y = 1.1;
	public static final double AFT_DECK_START = -3.6;
	public static final double RAIL_ABOVE_DECK = 0.95;
	public static final double DECK_MIN_Z = -6.9;
	public static final double DECK_MAX_Z = 6.9;
	public static final double MAST_Z = 1.2;
	public static final double MAST_TOP = 14.0;
	public static final double CROSSTREE_Y = 11.0;
	/** The pilot stands at the tiller, on the stern platform. */
	public static final double PILOT_Z = -5.0;
	public static final double HELM_Z = -6.0;
	public static final double RUDDER_Z = -7.7;
	public static final double BOOM_Y = 3.1;
	public static final double BOOM_END_Z = -8.8;
	public static final double GAFF_THROAT_Y = 10.2;
	public static final double[] GAFF_PEAK = {11.6, -6.3};
	public static final double[] BOWSPRIT_HEEL = {3.45, 6.9};
	public static final double[] BOWSPRIT_TIP = {4.9, 12.2};
	public static final double JIB_HEAD_Y = 10.6;
	public static final double[] JIB_CLEW = {3.2, 2.2};
	/** Passenger seats (x, z) on the main deck: two benches along the bulwarks, a bench at the bow. */
	public static final double[][] BENCH_SEATS = {{1.55, -2.0}, {-1.55, -2.0}, {0.0, 4.8}};
	/** A crate to sit on, on the stern platform (x, z). */
	public static final double[] AFT_SEAT = {1.0, -6.3};
	/** Cargo on the decks (solid): crates (x, z, size) and barrels (x, z, radius). */
	public static final double[][] CRATES = {{-0.85, -6.3, 0.72}, {-0.85, -5.45, 0.6}, {1.0, -6.3, 0.7}, {1.3, 3.6, 0.62}, {1.3, 2.95, 0.5}};
	public static final double[][] BARRELS = {{1.5, 0.3, 0.3}, {-1.55, 0.3, 0.3}, {-1.2, 4.1, 0.28}};
	public static final double BARREL_H = 0.8;

	private SloopLayout() {
	}

	/** Overall length, stern post to bowsprit tip. */
	public static double overallLength() {
		return TIP + BOWSPRIT_TIP[1];
	}

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 8.1;
		p.forePowA = 2.0;
		p.forePowB = 0.8;
		p.aftScale = 8.0;
		p.aftPowA = 3.2;
		p.aftPowB = 0.6;
		p.keelDepth = 1.5;
		p.keelRise = 1.1;
		p.keelPow = 2.6;
		p.railBase = 2.1;
		p.railRiseFore = 1.4;
		p.railRiseAft = 0.25;
		p.railPow = 2.2;
		p.railAboveDeck = RAIL_ABOVE_DECK;
		p.waterlineY = WATERLINE_Y;
		p.mainDeckY = MAIN_DECK_Y;
		p.raisedDecks = List.of(new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, AFT_DECK_START, AFT_DECK_Y));
		p.deckMinZ = DECK_MIN_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.45, 0.9}, {0.8, 0.55}, {0.97, 0.15}};
		HullShape hull = new HullShape(p);

		double main = MAIN_DECK_Y, aft = AFT_DECK_Y;
		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the tiller on the stern platform, steps off beside it
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, aft + 0.28, PILOT_Z, true, new double[] {0.0, aft + 0.02, PILOT_Z + 1.2}));
		for (double[] b : BENCH_SEATS) {
			double dx = b[0] == 0 ? 0.0 : b[0] * 0.5, dz = b[0] == 0 ? b[1] - 0.9 : b[1];
			seats.add(new ShipGeometry.Seat(seats.size(), b[0], main + 0.47, b[1], false, new double[] {dx, main + 0.02, dz}));
		}
		seats.add(new ShipGeometry.Seat(seats.size(), AFT_SEAT[0], aft + 0.73, AFT_SEAT[1], false, new double[] {0.0, aft + 0.02, AFT_SEAT[1] + 0.9}));
		spec.seats = List.copyOf(seats);
		// the tiller: a rod from the rudder head sweeping over the stern platform
		spec.helm = new ShipGeometry.LocalBox(-0.5, aft + 0.4, HELM_Z - 1.3, 0.5, aft + 1.2, HELM_Z + 0.9);
		spec.masts = List.of(new ShipGeometry.Mast(0, MAST_Z, main, MAST_TOP, 0.2));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (double[] c : CRATES) {
			double y0 = c[1] < AFT_DECK_START ? aft : main;
			solids.add(new ShipGeometry.LocalBox(c[0] - c[2] / 2, y0, c[1] - c[2] / 2, c[0] + c[2] / 2, y0 + c[2], c[1] + c[2] / 2));
		}
		for (double[] b : BARRELS) {
			double y0 = b[1] < AFT_DECK_START ? aft : main;
			solids.add(new ShipGeometry.LocalBox(b[0] - b[2], y0, b[1] - b[2], b[0] + b[2], y0 + BARREL_H, b[1] + b[2]));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {WATERLINE_Y + 0.15, 0.15, 1.2};
		spec.boardMinZ = -6.4;
		spec.boardMaxZ = 6.4;
		spec.avoidZ = new double[] {-2.0, 0.3, 3.6};
		return new ShipType("trade_sloop", "petit voilier de commerce", new ShipGeometry(hull, spec), SloopLayout::config);
	}

	/**
	 * A light boat, but a laden merchant: gathers way progressively, moderate top speed, smooth easy turns
	 * with a little inertia, rocks on the waves more than the big ships; the sails furl when stopped.
	 */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.4;
		c.normalSpeed = 5.2;
		c.fastSpeed = 7.8;
		c.reverseSpeed = 1.4;
		c.acceleration = 0.65;
		c.braking = 1.3;
		c.waterDrag = 0.14;
		c.maxTurnRate = 15.0;
		c.minTurnFactor = 0.25;
		c.helmRate = 1.5;
		c.helmReturnRate = 0.9;
		c.turnResponse = 1.3;
		c.turnSpeedLoss = 0.16;
		c.waveRocking = 1.15;
		c.aiWaypointRadius = 6.0;
		c.aiStopRadius = 1.8;
		c.aiLookahead = 12.0;
		c.aiProbeDistance = 32.0;
		c.aiStuckSeconds = 6;
		c.aiTurnAroundSpeed = 0.8;
		c.furlSailWhenStopped = true;
		return c;
	}
}
