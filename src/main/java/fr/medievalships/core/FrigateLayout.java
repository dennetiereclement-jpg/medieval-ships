package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Blue-Sailed Frigate ({@code blue_frigate}): a big three-masted ship of the line of 36 blocks (46 with
 * the bowsprit), 10 wide, 33 high from the keel to the main masthead, with a royal blue hull banded with
 * gold, a row of red gun ports, pale blue sails bearing black fleurs-de-lis and tricolour flags. It sails
 * like the Old Corsair (heavier and slower) and has rooms: the captain's cabin under the quarterdeck and
 * the hold under the main deck (cargo, the guns behind the ports). The rooms, the hull and the decks are
 * described by its interior grid ({@code tools/frigate_interior.py}).
 *
 * <p>Ship-local blocks, the same numbers as {@code tools/frigate_shape.py}: y = 0 is the waterline.
 */
public final class FrigateLayout {
	public static final double HALF_LENGTH = 18.0;
	public static final double TIP = 19.0;
	public static final double MAX_HALF_WIDTH = 5.0;
	public static final double WATERLINE_Y = 0.0;
	public static final double KEEL_DEPTH = 3.4;
	public static final double MAIN_DECK_Y = 5.5;
	public static final double LOWER_FLOOR_Y = 2.0;
	public static final double QUARTERDECK_Y = 8.5;
	public static final double CABIN_FLOOR_Y = 5.5;
	public static final double CABIN_FRONT_Z = -9.5;
	public static final double TRANSOM_Z = -18.0;
	public static final double DECK_MAX_Z = 17.5;
	/** The fore and main masts, stepped on the keel (through the hold). */
	public static final double FORE_MAST_Z = 6.0;
	public static final double FORE_MAST_TOP = 28.5;
	public static final double MAIN_MAST_Z = -4.0;
	public static final double MAIN_MAST_TOP = 30.0;
	/** The mizzen, stepped on the quarterdeck. */
	public static final double MIZZEN_Z = -14.0;
	public static final double MIZZEN_TOP = 21.0;
	public static final double[] BOWSPRIT_TIP = {0.0, 12.6, 27.5};
	/** End of the spanker boom, a block before the taffrail (clear of the great stern lantern). */
	public static final double BOOM_END_Z = -17.0;
	public static final double BOOM_Y = 11.4;
	/** How far aft the rudder blade and the stern lanterns reach. */
	public static final double STERN_REACH_Z = -19.6;
	/** The gilded lion figurehead and the lowest head rail reach forward of the hull, under the bowsprit. */
	public static final double[] FIGUREHEAD_PROBE = {0.0, 8.4, 23.6};
	public static final double[] HEAD_RAIL_PROBE = {0.0, 7.2, 21.8};
	/** Half span of the longest yard (the fore and main courses). */
	public static final double YARD_HALF = 8.6;
	/** The square yards are braced round by this angle (port arms aft), as in the model. */
	public static final double BRACE_DEG = 32.0;
	public static final double HELM_Z = -11.5;
	public static final double PILOT_Z = -12.3;
	/** Stairs: main deck -> quarterdeck (both sides), main deck -> hold (port, between the masts). */
	public static final double[] QD_STAIR_X = {2.0, 3.5};
	public static final double[] QD_STAIR_Z = {-6.5, -9.5};
	public static final double[] COMPANION_X = {2.0, 3.5};
	public static final double[] COMPANION_Z = {0.5, 4.0};
	/** The gun ports (red lids, decorative) along each side, eight at 3 blocks, and their height. */
	public static final double[] GUNPORT_Z = {-10.5, -7.5, -4.5, -1.5, 1.5, 4.5, 7.5, 10.5};
	public static final double GUNPORT_Y = 3.9;
	/** Doors of the interior grid. */
	public static final int CABIN_DOOR = 0;
	public static final String GRID = "/assets/medievalships/interiors/blue_frigate.grid";
	public static final String DECOR = "/assets/medievalships/interiors/blue_frigate_decor.json";

	private FrigateLayout() {
	}

	/** The ship type (registered as {@link Ships#BLUE_FRIGATE}). */
	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 18.6;
		p.forePowA = 3.0;
		p.forePowB = 0.6;
		p.aftScale = 23.0;
		p.aftPowA = 4.0;
		p.aftPowB = 0.5;
		p.keelDepth = KEEL_DEPTH;
		p.keelRise = 2.2;
		p.keelPow = 3.0;
		p.railBase = 7.0;
		p.railRiseFore = 2.2;
		p.railRiseAft = 0.3;
		p.railPow = 2.6;
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
		// the masts above the decks (the grid holds them below)
		double m = MAIN_DECK_Y;
		spec.masts = List.of(
				new ShipGeometry.Mast(0, MAIN_MAST_Z, m, MAIN_MAST_TOP, 0.48),
				new ShipGeometry.Mast(0, FORE_MAST_Z, m, FORE_MAST_TOP, 0.46),
				new ShipGeometry.Mast(0, MIZZEN_Z, q, MIZZEN_TOP, 0.36));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (ShipGeometry.Mast mast : spec.masts) {
			solids.add(new ShipGeometry.LocalBox(mast.x() - mast.half(), mast.bottom(), mast.z() - mast.half(), mast.x() + mast.half(), mast.top(),
					mast.z() + mast.half()));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.2, 2.0, 4.0, 6.0};
		// the bowsprit, the boom beyond the stern and the yard arms touch the shore before the hull
		List<double[]> probes = new ArrayList<>();
		for (double t = 0.0; t <= 1.0001; t += 0.25) {
			probes.add(new double[] {0, 7.6 + (BOWSPRIT_TIP[1] - 7.6) * t, 15.5 + (BOWSPRIT_TIP[2] - 15.5) * t});
		}
		probes.add(new double[] {0, BOOM_Y, BOOM_END_Z});
		probes.add(new double[] {0, 1.0, STERN_REACH_Z});
		probes.add(FIGUREHEAD_PROBE.clone());
		probes.add(HEAD_RAIL_PROBE.clone());
		// the ends of the braced yards: the courses, the topsails, the mizzen topsail
		yardArms(probes, 15.4, FORE_MAST_Z, 0.65, YARD_HALF);
		yardArms(probes, 16.4, MAIN_MAST_Z, 0.67, YARD_HALF);
		yardArms(probes, 22.4, FORE_MAST_Z + 0.45, 0.48, 6.8);
		yardArms(probes, 23.6, MAIN_MAST_Z + 0.45, 0.5, 7.0);
		yardArms(probes, 17.6, MIZZEN_Z + 0.35, 0.4, 4.6);
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = BOWSPRIT_TIP[2] + 1.0;
		spec.aiReach = BOWSPRIT_TIP[2];
		spec.aiBack = -STERN_REACH_Z;
		spec.aiHalfWidth = MAX_HALF_WIDTH + 1.0;
		spec.lowestY = -KEEL_DEPTH;
		spec.boardMinZ = -7.5;
		spec.boardMaxZ = 15.0;
		spec.boardHalfWidth = 1.6;
		spec.avoidZ = new double[] {};
		spec.sternPost = false;
		return new ShipType("blue_frigate", "Grand navire aux voiles bleues", new ShipGeometry(hull, spec), FrigateLayout::config);
	}

	/** Both ends of a yard at height y, hung {@code off} before its mast at z, braced round by {@link #BRACE_DEG}. */
	private static void yardArms(List<double[]> probes, double y, double mastZ, double off, double half) {
		double c = Math.cos(Math.toRadians(BRACE_DEG));
		double s = Math.sin(Math.toRadians(BRACE_DEG));
		for (double side : new double[] {1, -1}) {
			probes.add(new double[] {side * half * c + off * s, y, mastZ - side * half * s + off * c});
		}
	}

	/** The biggest and heaviest of the sailing ships: very slow to gather way and to stop, a long glide, wide turns. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.5;
		c.normalSpeed = 3.6;
		c.fastSpeed = 6.0;
		c.reverseSpeed = 0.8;
		c.acceleration = 0.22;
		c.braking = 0.4;
		c.waterDrag = 0.05;
		c.maxTurnRate = 6.0;
		c.minTurnFactor = 0.07;
		c.helmRate = 0.7;
		c.helmReturnRate = 0.5;
		c.turnResponse = 0.45;
		c.turnSpeedLoss = 0.12;
		c.waveRocking = 0.7;
		c.aiWaypointRadius = 14.0;
		c.aiStopRadius = 3.5;
		c.aiLookahead = 28.0;
		c.aiProbeDistance = 75.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 1.6;
		return c;
	}
}
