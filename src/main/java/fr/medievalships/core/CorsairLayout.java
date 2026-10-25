package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Old Corsair ({@code old_corsair}): a patched-up three-master of 42 blocks (52 with the
 * bowsprit), 10 wide, 38 high from the keel to the main masthead. It sails like the galleon but has
 * rooms: the captain's cabin under the quarterdeck, and two decks under the main deck (lower deck:
 * common room, kitchen, crew quarters and their coursive; the hold, below the waterline). The rooms,
 * the hull and the decks are described by its interior grid ({@code tools/corsair_interior.py}).
 *
 * <p>Ship-local blocks, the same numbers as {@code tools/corsair_shape.py}: y = 0 is the waterline.
 */
public final class CorsairLayout {
	public static final double HALF_LENGTH = 21.0;
	public static final double TIP = 22.0;
	public static final double MAX_HALF_WIDTH = 5.0;
	public static final double WATERLINE_Y = 0.0;
	public static final double KEEL_DEPTH = 3.4;
	public static final double MAIN_DECK_Y = 4.5;
	public static final double LOWER_FLOOR_Y = 1.0;
	public static final double HOLD_FLOOR_Y = -2.0;
	public static final double QUARTERDECK_Y = 7.0;
	public static final double CABIN_FLOOR_Y = 4.0;
	public static final double CABIN_FRONT_Z = -14.0;
	public static final double TRANSOM_Z = -21.0;
	public static final double DECK_MAX_Z = 20.5;
	public static final double FORE_MAST_Z = 11.5;
	public static final double FORE_MAST_TOP = 33.5;
	public static final double MAIN_MAST_Z = 2.5;
	public static final double MAIN_MAST_TOP = 34.6;
	public static final double MIZZEN_Z = -7.5;
	public static final double MIZZEN_TOP = 30.0;
	public static final double[] BOWSPRIT_TIP = {0.0, 10.4, 30.8};
	/** End of the spanker boom, beyond the stern. */
	public static final double BOOM_END_Z = -24.6;
	public static final double BOOM_Y = 9.1;
	/** Half span of the longest yard (main course). */
	public static final double YARD_HALF = 7.8;
	public static final double HELM_Z = -15.3;
	public static final double PILOT_Z = -16.1;
	/** Stairs: main deck -> quarterdeck (both sides), main deck -> common room (port), lower deck -> hold. */
	public static final double[] QD_STAIR_X = {2.0, 3.5};
	public static final double[] QD_STAIR_Z = {-11.5, -14.0};
	public static final double[] COMPANION_X = {2.0, 3.5};
	public static final double[] COMPANION_Z = {1.0, 4.5};
	public static final double[] HOLD_STAIR_X = {-1.0, 1.0};
	public static final double[] HOLD_STAIR_Z = {-17.0, -14.0};
	/** Doors of the interior grid. */
	public static final int CABIN_DOOR = 0;
	public static final int COMMON_DOOR = 1;
	public static final int KITCHEN_DOOR = 2;
	public static final int CREW_PORT_DOOR = 3;
	public static final int CREW_STBD_DOOR = 4;
	public static final String GRID = "/assets/medievalships/interiors/old_corsair.grid";
	public static final String DECOR = "/assets/medievalships/interiors/old_corsair_decor.json";

	private CorsairLayout() {
	}

	/** The ship type (registered as {@link Ships#OLD_CORSAIR}). */
	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 21.6;
		p.forePowA = 3.2;
		p.forePowB = 0.6;
		p.aftScale = 27.0;
		p.aftPowA = 4.0;
		p.aftPowB = 0.5;
		p.keelDepth = KEEL_DEPTH;
		p.keelRise = 2.2;
		p.keelPow = 3.0;
		p.railBase = 5.6;
		p.railRiseFore = 1.4;
		p.railRiseAft = 0.4;
		p.railPow = 2.2;
		p.railFloors = List.of(new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, CABIN_FRONT_Z, QUARTERDECK_Y + 1.0));
		p.waterlineY = WATERLINE_Y;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = CABIN_FRONT_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.45, 0.9}, {0.8, 0.55}, {0.97, 0.12}};
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		double q = QUARTERDECK_Y;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the wheel on the quarterdeck
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, q + 0.28, PILOT_Z, true, new double[] {1.2, q + 0.02, PILOT_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, q + 0.2, HELM_Z - 0.4, 0.8, q + 1.8, HELM_Z + 0.4);
		// the masts above the main deck (the grid holds them below it)
		double m = MAIN_DECK_Y;
		spec.masts = List.of(
				new ShipGeometry.Mast(0, MAIN_MAST_Z, m, MAIN_MAST_TOP, 0.4),
				new ShipGeometry.Mast(0, FORE_MAST_Z, m, FORE_MAST_TOP, 0.36),
				new ShipGeometry.Mast(0, MIZZEN_Z, m, MIZZEN_TOP, 0.32));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (ShipGeometry.Mast mast : spec.masts) {
			solids.add(new ShipGeometry.LocalBox(mast.x() - mast.half(), mast.bottom(), mast.z() - mast.half(), mast.x() + mast.half(), mast.top(),
					mast.z() + mast.half()));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.2, 2.0, 4.5};
		// the bowsprit, the boom beyond the stern and the yard arms touch the shore before the hull
		List<double[]> probes = new ArrayList<>();
		for (double t = 0.0; t <= 1.0001; t += 0.25) {
			probes.add(new double[] {0, 5.8 + (BOWSPRIT_TIP[1] - 5.8) * t, 22.0 + (BOWSPRIT_TIP[2] - 22.0) * t});
		}
		probes.add(new double[] {0, BOOM_Y, BOOM_END_Z});
		probes.add(new double[] {0, BOOM_Y, -22.5});
		for (double side : new double[] {1, -1}) {
			probes.add(new double[] {side * YARD_HALF, 17.0, MAIN_MAST_Z});
			probes.add(new double[] {side * (YARD_HALF - 0.4), 16.0, FORE_MAST_Z});
			probes.add(new double[] {side * 5.6, 23.4, MIZZEN_Z});
		}
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = BOWSPRIT_TIP[2] + 1.0;
		spec.aiReach = BOWSPRIT_TIP[2];
		spec.aiBack = -BOOM_END_Z;
		spec.aiHalfWidth = MAX_HALF_WIDTH + 1.0;
		spec.lowestY = -KEEL_DEPTH;
		spec.boardMinZ = -10.5;
		spec.boardMaxZ = 17.0;
		spec.boardHalfWidth = 1.6;
		spec.avoidZ = new double[] {};
		spec.sternPost = false;
		return new ShipType("old_corsair", "Vieux Corsaire", new ShipGeometry(hull, spec), CorsairLayout::config);
	}

	/** A big, heavy sailing ship: slow to gather way and to stop, long glide, wide turns, no oars to pivot. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.8;
		c.normalSpeed = 4.2;
		c.fastSpeed = 7.0;
		c.reverseSpeed = 0.9;
		c.acceleration = 0.28;
		c.braking = 0.5;
		c.waterDrag = 0.06;
		c.maxTurnRate = 7.0;
		c.minTurnFactor = 0.08;
		c.helmRate = 0.8;
		c.helmReturnRate = 0.55;
		c.turnResponse = 0.5;
		c.turnSpeedLoss = 0.12;
		c.waveRocking = 0.8;
		c.aiWaypointRadius = 14.0;
		c.aiStopRadius = 3.5;
		c.aiLookahead = 26.0;
		c.aiProbeDistance = 70.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 1.8;
		return c;
	}
}
