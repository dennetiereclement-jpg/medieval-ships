package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Royal Lion Ship ({@code royal_lion_ship}, "Navire royal au lion", city of Lion Port): a big royal merchant ship
 * of 40 blocks (51 with the bowsprit), 12 wide, a high dark wooden hull with a strong sheer, royal blue strakes
 * between gilded wales, blue heater shields bearing a gold rampant lion and long lion banners along each side, a whole
 * leaping gilded lion as figurehead, a raised forecastle, three masts with royal blue square sails bordered in gold (a
 * big gold lion on the courses), gold-railed fighting tops with lanterns, and a big stern castle 12 blocks long (the
 * captain's cabin under the quarterdeck, the royal state room in the upper storey of 8 blocks under a blue mansard
 * roof, a striped awning over the helm). It sails like the Blue-Sailed Frigate (heavier still) and has rooms: the
 * captain's cabin, the state room, the crew quarters and the cargo hold, described by its interior grid
 * ({@code tools/royal_lion_interior.py}).
 *
 * <p>Ship-local blocks, the same numbers as {@code tools/royal_lion_shape.py}: y = 0 is the waterline.
 */
public final class RoyalLionLayout {
	public static final double HALF_LENGTH = 20.0;
	public static final double TIP = 21.0;
	public static final double MAX_HALF_WIDTH = 6.0;
	public static final double WATERLINE_Y = 0.6;
	public static final double KEEL_DEPTH = 3.6;
	public static final double MAIN_DECK_Y = 5.0;
	public static final double LOWER_FLOOR_Y = 1.5;
	public static final double QUARTERDECK_Y = 8.5;
	public static final double CABIN_FLOOR_Y = 5.0;
	public static final double FORECASTLE_Y = 7.0;
	/** The royal state room (the roundhouse, the castle's upper storey on the quarterdeck): floor, ceiling, front wall. */
	public static final double STATEROOM_FLOOR_Y = 8.5;
	public static final double STATEROOM_CEIL_Y = 12.0;
	public static final double ROUNDHOUSE_FRONT_Z = -12.0;
	public static final double CABIN_FRONT_Z = -8.0;
	public static final double FORECASTLE_Z = 13.0;
	public static final double TRANSOM_Z = -20.0;
	public static final double DECK_MAX_Z = 19.5;
	public static final double FC_BULWARK_TOP = 8.2;
	public static final double QD_BULWARK_TOP = 9.6;
	/** The lower deck: the crew quarters aft of the bulkhead, the cargo hold forward of it. */
	public static final double LOWER_AFT_Z = -15.0;
	public static final double LOWER_FORE_Z = 14.5;
	public static final double[] BULKHEAD_Z = {-3.0, -2.5};
	/** The fore and main masts, stepped on the keel (through the hold). */
	public static final double FORE_MAST_Z = 12.5;
	public static final double FORE_MAST_TOP = 29.5;
	public static final double MAIN_MAST_Z = -0.5;
	public static final double MAIN_MAST_TOP = 30.5;
	/** The mizzen, stepped on the quarterdeck at the front of the state room, between its two doors. */
	public static final double MIZZEN_Z = -11.5;
	public static final double MIZZEN_TOP = 26.0;
	public static final double[] BOWSPRIT_FOOT = {0.0, 9.0, 17.5};
	public static final double[] BOWSPRIT_TIP = {0.0, 14.8, 31.0};
	/** How far aft the rudder blade, the stern gallery and the stern lanterns reach. */
	public static final double STERN_REACH_Z = -21.6;
	/** The leaping gilded lion figurehead (its head and its forepaws) and the head rails reach forward of the stem. */
	public static final double[] FIGUREHEAD_PROBE = {0.0, 9.4, 28.5};
	public static final double[] FIGUREHEAD_PAW_PROBE = {0.0, 6.9, 29.5};
	public static final double[] HEAD_RAIL_PROBE = {0.0, 8.3, 23.6};
	/** The square yards are braced round by this angle (port arms aft), as in the model. */
	public static final double BRACE_DEG = 6.0;
	/** Half span of the longest yard (the main course's). */
	public static final double YARD_HALF = 11.4;
	public static final double HELM_Z = -9.4;
	public static final double PILOT_Z = -10.2;
	/** Stairs: main deck -> quarterdeck and main deck -> forecastle (both sides), the companionways down. */
	public static final double[] QD_STAIR_X = {2.5, 4.0};
	public static final double[] QD_STAIR_Z = {-4.5, -8.0};
	public static final double[] FC_STAIR_X = {2.0, 3.5};
	public static final double[] FC_STAIR_Z = {11.0, 13.0};
	public static final double[] CREW_STAIR_X = {-2.2, -0.7};
	public static final double[] CREW_STAIR_Z = {-7.0, -3.5};
	public static final double[] HOLD_STAIR_X = {2.0, 3.5};
	public static final double[] HOLD_STAIR_Z = {3.5, 7.0};
	/** The shields along each side (the waist and the forecastle), and the height of their centre. */
	public static final double[] SHIELD_Z = {-5.5, 0.5, 6.5, 12.5};
	public static final double SHIELD_Y = 4.6;
	/** Doors of the interior grid. */
	public static final int CABIN_DOOR = 0;
	public static final int STATEROOM_DOOR = 1;
	public static final int BULKHEAD_DOOR = 2;
	/** The state room's second door, starboard of the mizzen ({@link #STATEROOM_DOOR} is port of it). */
	public static final int STATEROOM_DOOR_S = 3;
	public static final String GRID = "/assets/medievalships/interiors/royal_lion_ship.grid";
	public static final String DECOR = "/assets/medievalships/interiors/royal_lion_ship_decor.json";

	private RoyalLionLayout() {
	}

	/** The ship type (registered as {@link Ships#ROYAL_LION_SHIP}). */
	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 20.6;
		p.forePowA = 2.6;
		p.forePowB = 0.6;
		p.aftScale = 25.0;
		p.aftPowA = 4.0;
		p.aftPowB = 0.5;
		p.keelDepth = KEEL_DEPTH;
		p.keelRise = 2.6;
		p.keelPow = 2.6;
		p.railBase = 6.7;
		p.railRiseFore = 3.6;
		p.railRiseAft = 1.2;
		p.railPow = 2.0;
		p.railFloors = List.of(new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, CABIN_FRONT_Z, QUARTERDECK_Y + 1.0),
				new HullShape.RaisedDeck(FORECASTLE_Z, Double.POSITIVE_INFINITY, FORECASTLE_Y + 1.0));
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
		// the pilot stands at the wheel on the quarterdeck, under the striped awning, forward of the mizzen
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
				new ShipGeometry.Mast(0, MAIN_MAST_Z, m, MAIN_MAST_TOP, 0.53),
				new ShipGeometry.Mast(0, FORE_MAST_Z, m, FORE_MAST_TOP, 0.5),
				new ShipGeometry.Mast(0, MIZZEN_Z, q, MIZZEN_TOP, 0.4));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (ShipGeometry.Mast mast : spec.masts) {
			solids.add(new ShipGeometry.LocalBox(mast.x() - mast.half(), mast.bottom(), mast.z() - mast.half(), mast.x() + mast.half(), mast.top(),
					mast.z() + mast.half()));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.2, 2.0, 4.0, 6.0};
		// the bowsprit, the lion figurehead, the stern gallery and rudder and the yard arms touch the shore before the hull
		List<double[]> probes = new ArrayList<>();
		for (double t = 0.0; t <= 1.0001; t += 0.25) {
			probes.add(new double[] {0, BOWSPRIT_FOOT[1] + (BOWSPRIT_TIP[1] - BOWSPRIT_FOOT[1]) * t,
					BOWSPRIT_FOOT[2] + (BOWSPRIT_TIP[2] - BOWSPRIT_FOOT[2]) * t});
		}
		probes.add(new double[] {0, 1.0, STERN_REACH_Z});
		probes.add(new double[] {0, 6.0, STERN_REACH_Z + 0.5});
		probes.add(new double[] {0, 9.0, STERN_REACH_Z + 0.6});
		probes.add(FIGUREHEAD_PROBE.clone());
		probes.add(FIGUREHEAD_PAW_PROBE.clone());
		probes.add(HEAD_RAIL_PROBE.clone());
		// the ends of the braced yards: the courses, the topsails, the mizzen course
		yardArms(probes, 19.8, FORE_MAST_Z, 0.67, 10.6);
		yardArms(probes, 20.2, MAIN_MAST_Z, 0.7, YARD_HALF);
		yardArms(probes, 26.8, FORE_MAST_Z + 0.45, 0.5, 7.4);
		yardArms(probes, 27.8, MAIN_MAST_Z + 0.45, 0.52, 7.8);
		yardArms(probes, 20.4, MIZZEN_Z, 0.57, 7.7);
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = BOWSPRIT_TIP[2] + 1.0;
		spec.aiReach = BOWSPRIT_TIP[2];
		spec.aiBack = -STERN_REACH_Z;
		spec.aiHalfWidth = MAX_HALF_WIDTH + 1.0;
		spec.lowestY = -KEEL_DEPTH;
		// boarding on the main deck between the crew companionway and the forecastle (clear of both hatches)
		spec.boardMinZ = -3.0;
		spec.boardMaxZ = 11.0;
		spec.boardHalfWidth = 1.6;
		spec.avoidZ = new double[] {};
		spec.sternPost = false;
		return new ShipType("royal_lion_ship", "Navire royal au lion", new ShipGeometry(hull, spec), RoyalLionLayout::config);
	}

	/** Both ends of a yard at height y, hung {@code off} before its mast at z, braced round by {@link #BRACE_DEG}. */
	private static void yardArms(List<double[]> probes, double y, double mastZ, double off, double half) {
		double c = Math.cos(Math.toRadians(BRACE_DEG));
		double s = Math.sin(Math.toRadians(BRACE_DEG));
		for (double side : new double[] {1, -1}) {
			probes.add(new double[] {side * half * c + off * s, y, mastZ - side * half * s + off * c});
		}
	}

	/** A big, heavy royal ship: slower to gather way and to stop than the frigate, a long glide, wide turns. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.4;
		c.normalSpeed = 3.4;
		c.fastSpeed = 5.6;
		c.reverseSpeed = 0.7;
		c.acceleration = 0.2;
		c.braking = 0.36;
		c.waterDrag = 0.045;
		c.maxTurnRate = 5.5;
		c.minTurnFactor = 0.07;
		c.helmRate = 0.65;
		c.helmReturnRate = 0.5;
		c.turnResponse = 0.42;
		c.turnSpeedLoss = 0.12;
		c.waveRocking = 0.6;
		c.aiWaypointRadius = 15.0;
		c.aiStopRadius = 3.5;
		c.aiLookahead = 30.0;
		c.aiProbeDistance = 80.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 1.5;
		return c;
	}
}
