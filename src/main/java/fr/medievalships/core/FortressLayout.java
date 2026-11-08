package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Fortress Ship ({@code fortress_ship}): a floating castle that keeps a ship's shape, 43 blocks over its raked
 * stem and its castle (48.5 with the bowsprit), 13 wide, 30.5 high from the keel to the main masthead. A massive
 * dark-wood hull clad with grey stone (wales, studded belt, ribs, crenellated parapets), red panels between the
 * ribs, a raised forecastle, a two storey stern castle (the captain's cabin under the quarterdeck, the keep with its
 * battlements over the aft part) and a turret with a pointed red roof; three masts with red sails bordered in white
 * bearing a castle tower. It sails like the Blue-Sailed Frigate, heavier still, and has rooms on five levels, all
 * described by its interior grid ({@code tools/fortress_interior.py}).
 *
 * <p>Ship-local blocks, the same numbers as {@code tools/fortress_shape.py}: y = 0 is the waterline.
 */
public final class FortressLayout {
	public static final double HALF_LENGTH = 19.0;
	public static final double TIP = 22.5;
	public static final double MAX_HALF_WIDTH = 6.5;
	public static final double WATERLINE_Y = 0.0;
	public static final double KEEL_DEPTH = 3.0;
	public static final double MAIN_DECK_Y = 4.5;
	public static final double LOWER_FLOOR_Y = 1.0;
	public static final double FORECASTLE_Y = 7.0;
	public static final double QUARTERDECK_Y = 8.0;
	public static final double KEEP_Y = 11.0;
	public static final double CABIN_FLOOR_Y = 4.5;
	/** Collision tops of the bulwarks and parapets (1.5 above their deck). */
	public static final double WAIST_WALL = 6.0;
	public static final double FC_WALL = 8.5;
	public static final double QD_WALL = 9.5;
	public static final double KEEP_WALL = 12.5;
	public static final double TRANSOM_Z = -19.5;
	/** Front bulkhead of the castle (the captain's cabin) and front of the quarterdeck. */
	public static final double CABIN_FRONT_Z = -9.0;
	/** Front wall of the keep (the officers' room), aft end of the open quarterdeck. */
	public static final double KEEP_FRONT_Z = -13.0;
	/** Aft bulkhead of the forecastle (the crew's mess). */
	public static final double FC_FRONT_Z = 6.0;
	/** Between the cargo hold (aft) and the crew quarters (forward), on the lower deck. */
	public static final double CREW_BULKHEAD_Z = 5.5;
	public static final double DECK_MAX_Z = 19.0;
	public static final double STEM_HEAD_Z = 22.5;
	/** The turret on the keep's roof: half width, z range, top of its walls and of its roof. */
	public static final double TURRET_HALF = 2.5;
	public static final double[] TURRET_Z = {-19.0, -15.0};
	public static final double TURRET_WALL_TOP = 14.5;
	public static final double TURRET_ROOF_TOP = 18.6;
	/** The fore and main masts, stepped on the keel (through the lower deck); the fore mast stands on the forecastle. */
	public static final double FORE_MAST_Z = 8.0;
	public static final double FORE_MAST_TOP = 24.0;
	public static final double MAIN_MAST_Z = -1.0;
	public static final double MAIN_MAST_TOP = 27.5;
	/** The mizzen, stepped on the quarterdeck. */
	public static final double MIZZEN_Z = -11.5;
	public static final double MIZZEN_TOP = 24.5;
	public static final double[] BOWSPRIT_FOOT = {0.0, 8.4, 19.5};
	public static final double[] BOWSPRIT_TIP = {0.0, 11.6, 28.0};
	/** The stone beak at the stem head, the rudder blade and the stern lanterns, the turret's finial. */
	public static final double[] BEAK_PROBE = {0.0, 9.5, 24.3};
	public static final double STERN_REACH_Z = -21.3;
	public static final double FINIAL_TOP = 21.0;
	/** Half span of the longest yard (the main course) and the angle the square yards are braced round by. */
	public static final double YARD_HALF = 9.1;
	public static final double BRACE_DEG = 38.0;
	public static final double HELM_Z = -9.7;
	public static final double PILOT_Z = -10.5;
	/** Stairs: main deck -> quarterdeck (both sides), main deck -> forecastle (both sides), keep -> its roof, main deck -> lower deck. */
	public static final double[] QD_STAIR_X = {3.0, 4.5};
	public static final double[] QD_STAIR_Z = {-5.5, -9.0};
	public static final double[] FC_STAIR_X = {2.5, 4.0};
	public static final double[] FC_STAIR_Z = {3.5, 6.0};
	public static final double[] KEEP_STAIR_X = {2.5, 4.0};
	public static final double[] KEEP_STAIR_Z = {-15.0, -17.5};
	public static final double[] COMPANION_X = {2.5, 4.0};
	public static final double[] COMPANION_Z = {-5.0, -1.5};
	/** Doors of the interior grid. */
	public static final int CABIN_DOOR = 0;
	public static final int KEEP_DOOR = 1;
	public static final int MESS_DOOR = 2;
	public static final int CREW_DOOR = 3;
	public static final int TURRET_DOOR = 4;
	public static final String GRID = "/assets/medievalships/interiors/fortress_ship.grid";
	public static final String DECOR = "/assets/medievalships/interiors/fortress_ship_decor.json";

	private FortressLayout() {
	}

	/** The ship type (registered as {@link Ships#FORTRESS_SHIP}). */
	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 18.5;
		p.forePowA = 2.4;
		p.forePowB = 0.62;
		p.aftScale = 24.0;
		p.aftPowA = 3.4;
		p.aftPowB = 0.5;
		p.keelDepth = KEEL_DEPTH;
		p.keelRise = 2.0;
		p.keelPow = 3.0;
		p.railBase = 5.5;
		p.railRiseFore = 2.5;
		p.railRiseAft = 0.0;
		p.railPow = 3.0;
		p.railFloors = List.of(new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, KEEP_FRONT_Z, KEEP_WALL),
				new HullShape.RaisedDeck(KEEP_FRONT_Z, CABIN_FRONT_Z, QD_WALL), new HullShape.RaisedDeck(FC_FRONT_Z, Double.POSITIVE_INFINITY, FC_WALL));
		p.waterlineY = WATERLINE_Y;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = CABIN_FRONT_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.5, 0.88}, {0.82, 0.5}, {0.97, 0.1}};
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		double q = QUARTERDECK_Y;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the wheel on the quarterdeck, the mizzen behind him
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, q + 0.28, PILOT_Z, true, new double[] {1.4, q + 0.02, PILOT_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, q + 0.2, HELM_Z - 0.4, 0.8, q + 1.8, HELM_Z + 0.4);
		// the masts above the decks (the grid holds them below)
		spec.masts = List.of(
				new ShipGeometry.Mast(0, MAIN_MAST_Z, MAIN_DECK_Y, MAIN_MAST_TOP, 0.48),
				new ShipGeometry.Mast(0, FORE_MAST_Z, FORECASTLE_Y, FORE_MAST_TOP, 0.45),
				new ShipGeometry.Mast(0, MIZZEN_Z, q, MIZZEN_TOP, 0.37));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (ShipGeometry.Mast mast : spec.masts) {
			solids.add(new ShipGeometry.LocalBox(mast.x() - mast.half(), mast.bottom(), mast.z() - mast.half(), mast.x() + mast.half(), mast.top(),
					mast.z() + mast.half()));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.2, 2.0, 4.0, 6.0};
		// the bowsprit, the beak, the stern, the turret and the yard arms touch the shore before the hull
		List<double[]> probes = new ArrayList<>();
		for (double t = 0.0; t <= 1.0001; t += 0.25) {
			probes.add(new double[] {0, BOWSPRIT_FOOT[1] + (BOWSPRIT_TIP[1] - BOWSPRIT_FOOT[1]) * t, BOWSPRIT_FOOT[2] + (BOWSPRIT_TIP[2] - BOWSPRIT_FOOT[2]) * t});
		}
		probes.add(BEAK_PROBE.clone());
		probes.add(new double[] {0, 1.0, STERN_REACH_Z});
		probes.add(new double[] {0, KEEP_WALL, STERN_REACH_Z + 0.6});
		yardArms(probes, 15.3, FORE_MAST_Z, 0.62, 7.4);
		yardArms(probes, 16.7, MAIN_MAST_Z, 0.65, YARD_HALF);
		yardArms(probes, 23.7, MAIN_MAST_Z + 0.45, 0.49, 6.3);
		yardArms(probes, 19.6, MIZZEN_Z, 0.54, 5.3);
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = BOWSPRIT_TIP[2] + 1.0;
		spec.aiReach = BOWSPRIT_TIP[2];
		spec.aiBack = -STERN_REACH_Z;
		spec.aiHalfWidth = MAX_HALF_WIDTH + 1.5;
		spec.lowestY = -KEEL_DEPTH;
		spec.boardMinZ = -7.5;
		spec.boardMaxZ = 4.5;
		spec.boardHalfWidth = 2.0;
		spec.avoidZ = new double[] {};
		spec.sternPost = false;
		return new ShipType("fortress_ship", "Navire forteresse", new ShipGeometry(hull, spec), FortressLayout::config);
	}

	/** Both ends of a yard at height y, hung {@code off} before its mast at z, braced round by {@link #BRACE_DEG}. */
	private static void yardArms(List<double[]> probes, double y, double mastZ, double off, double half) {
		double c = Math.cos(Math.toRadians(BRACE_DEG));
		double s = Math.sin(Math.toRadians(BRACE_DEG));
		for (double side : new double[] {1, -1}) {
			probes.add(new double[] {side * half * c + off * s, y, mastZ - side * half * s + off * c});
		}
	}

	/** The heaviest of the sailing ships: very slow to gather way and to stop, the longest glide, the widest turns. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.3;
		c.normalSpeed = 3.2;
		c.fastSpeed = 5.4;
		c.reverseSpeed = 0.7;
		c.acceleration = 0.18;
		c.braking = 0.35;
		c.waterDrag = 0.045;
		c.maxTurnRate = 5.0;
		c.minTurnFactor = 0.07;
		c.helmRate = 0.6;
		c.helmReturnRate = 0.45;
		c.turnResponse = 0.4;
		c.turnSpeedLoss = 0.12;
		c.waveRocking = 0.55;
		c.aiWaypointRadius = 15.0;
		c.aiStopRadius = 4.0;
		c.aiLookahead = 30.0;
		c.aiProbeDistance = 80.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 1.5;
		return c;
	}
}
