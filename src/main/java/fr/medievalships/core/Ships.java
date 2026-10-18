package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/** The ship types of the mod. */
public final class Ships {
	private Ships() {
	}

	// ------------------------------------------------------------------ medieval galley

	/** Medieval galley: 20 blocks, one lateen sail, 16 oars, 9 seats. Values must never change. */
	public static final ShipType GALLEY = galley();

	private static ShipType galley() {
		HullShape.Params p = new HullShape.Params(); // the defaults are the galley
		p.raisedDecks = List.of(
				new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, HullProfile.AFT_DECK_START, HullProfile.RAISED_DECK_Y),
				new HullShape.RaisedDeck(HullProfile.FORE_DECK_START, Double.POSITIVE_INFINITY, HullProfile.RAISED_DECK_Y));
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, HullProfile.RAISED_DECK_Y + 0.28, -8.05, true,
				new double[] {0.0, HullProfile.RAISED_DECK_Y + 0.02, -7.35}));
		double[] benchZ = {-4.8, -1.6, 1.6, 4.8};
		int i = 1;
		for (double z : benchZ) {
			for (double x : new double[] {1.0, -1.0}) {
				seats.add(new ShipGeometry.Seat(i++, x, HullProfile.MAIN_DECK_Y + 0.47, z, false,
						new double[] {x * 0.9, HullProfile.MAIN_DECK_Y + 0.02, z + 0.8}));
			}
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.5, HullProfile.RAISED_DECK_Y + 0.1, -8.6, 0.5, HullProfile.RAISED_DECK_Y + 1.1, -7.4);
		spec.masts = List.of(new ShipGeometry.Mast(0, HullProfile.MAST_Z, HullProfile.MAIN_DECK_Y, HullProfile.MAST_TOP, 0.2));
		spec.avoidZ = benchZ;
		return new ShipType("galley", "galère", new ShipGeometry(hull, spec), ShipConfig::new);
	}

	// ------------------------------------------------------------------ great galleon

	/**
	 * Great galleon: 35 block hull (42 with the bowsprit), 9 wide, three masts, forecastle,
	 * quarterdeck over the great cabin, poop house with its red roof, 16 seats.
	 * The same numbers are used by {@code tools/generate_galleon.py}.
	 */
	public static final ShipType GALLEON = galleon();

	/** Galleon layout, ship-local blocks (shared with the model generator). */
	public static final class GalleonLayout {
		public static final double MAIN_DECK_Y = 1.0;
		public static final double FORECASTLE_Y = 3.0;
		public static final double FORECASTLE_START = 10.5;
		/** Quarterdeck floor (roof of the great cabin), its slab and the cabin bulkhead. */
		public static final double QUARTERDECK_Y = 3.6;
		public static final double QUARTERDECK_SLAB = 0.3;
		public static final double BULKHEAD_Z = -8.5;
		public static final double BULKHEAD_THICK = 0.3;
		public static final double DOOR_HALF = 0.7;
		public static final double DOOR_TOP = 3.05;
		public static final double TRANSOM_Z = -17.3;
		/** The galleon floats high: the water is 1.5 blocks under the model origin. */
		public static final double WATERLINE_Y = -1.5;
		/** Poop house (red roof) at the stern of the quarterdeck. */
		public static final double POOP_FRONT = -14.2;
		public static final double POOP_BACK = -16.9;
		public static final double POOP_HALF = 2.9;
		public static final double POOP_WALL_TOP = 6.3;
		public static final double POOP_RIDGE = 7.4;
		public static final double MAIN_MAST_Z = 1.5;
		public static final double MAIN_MAST_TOP = 25.5;
		public static final double FORE_MAST_Z = 12.8;
		public static final double FORE_MAST_TOP = 21.0;
		public static final double MIZZEN_Z = -12.6;
		public static final double MIZZEN_TOP = 17.5;
		public static final double HELM_Z = -9.6;
		public static final double PILOT_Z = -10.35;
		/** Stairs: x range (both sides) and z ranges of the steps, lowest step first. */
		public static final double STAIR_X0 = 1.9;
		public static final double STAIR_X1 = 3.6;
		public static final double FC_STAIR_X0 = 1.5;
		public static final double FC_STAIR_X1 = 3.0;
		/** Guard rails at the front of the castles, between the stairs. */
		public static final double RAIL_HEIGHT = 0.9;
		public static final double RAIL_THICK = 0.12;
		/** Stern balcony (gallery) outside the great cabin, through a door in the transom. */
		public static final double BALCONY_BACK = -18.3;
		public static final double BALCONY_HALF = 2.3;
		public static final double BALCONY_FLOOR = 0.25;
		public static final double BALCONY_RAIL = 1.0;
		/** Decorative gun ports in the bulwarks of the main deck (future cannons). */
		public static final double[] GUNPORT_Z = {-6.0, -3.0, 0.0, 2.75, 5.5, 8.0};
		public static final double GUNPORT_Y = 1.62;
		public static final double QD_STAIR_START = -6.0;
		public static final double FC_STAIR_START = 8.5;
		public static final double STEP_DEPTH = 0.5;

		private GalleonLayout() {
		}
	}

	private static ShipType galleon() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = 17.5;
		p.tip = 18.3;
		p.maxHalfWidth = 4.5;
		p.foreScale = 18.0;
		p.forePowA = 2.0;
		p.forePowB = 0.6;
		p.aftScale = 19.5;
		p.aftPowA = 3.0;
		p.aftPowB = 0.5;
		p.keelDepth = 2.9;
		p.keelRise = 2.1;
		p.keelPow = 3.0;
		p.waterlineY = GalleonLayout.WATERLINE_Y;
		p.railBase = 2.2;
		p.railRiseFore = 0.8;
		p.railRiseAft = 0.8;
		p.railPow = 2.5;
		p.mainDeckY = GalleonLayout.MAIN_DECK_Y;
		p.raisedDecks = List.of(new HullShape.RaisedDeck(GalleonLayout.FORECASTLE_START, Double.POSITIVE_INFINITY, GalleonLayout.FORECASTLE_Y));
		p.railFloors = List.of(
				new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, GalleonLayout.BULKHEAD_Z, GalleonLayout.QUARTERDECK_Y + 1.0),
				new HullShape.RaisedDeck(GalleonLayout.FORECASTLE_START, Double.POSITIVE_INFINITY, GalleonLayout.FORECASTLE_Y + 1.0));
		p.deckMinZ = GalleonLayout.TRANSOM_Z;
		p.deckMaxZ = 17.2;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.45, 0.92}, {0.8, 0.6}, {0.97, 0.15}};
		HullShape hull = new HullShape(p);

		double main = GalleonLayout.MAIN_DECK_Y, fc = GalleonLayout.FORECASTLE_Y, qd = GalleonLayout.QUARTERDECK_Y;
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		// quarterdeck floor = roof of the great cabin, in 1 block bands following the hull
		double slabBottom = qd - GalleonLayout.QUARTERDECK_SLAB;
		for (double z0 = GalleonLayout.TRANSOM_Z; z0 < GalleonLayout.BULKHEAD_Z - 1e-6; z0 += 1.0) {
			double z1 = Math.min(GalleonLayout.BULKHEAD_Z, z0 + 1.0);
			double w = Math.min(hull.innerHalfWidth(z0), hull.innerHalfWidth(z1)) + 0.12;
			solids.add(new ShipGeometry.LocalBox(-w, slabBottom, z0, w, qd, z1));
		}
		// cabin bulkhead with its door, and the lintel above the door
		double bz0 = GalleonLayout.BULKHEAD_Z - GalleonLayout.BULKHEAD_THICK, bz1 = GalleonLayout.BULKHEAD_Z;
		double bw = hull.innerHalfWidth(bz0) + 0.12, door = GalleonLayout.DOOR_HALF;
		solids.add(new ShipGeometry.LocalBox(door, main, bz0, bw, slabBottom, bz1));
		solids.add(new ShipGeometry.LocalBox(-bw, main, bz0, -door, slabBottom, bz1));
		solids.add(new ShipGeometry.LocalBox(-door, GalleonLayout.DOOR_TOP, bz0, door, slabBottom, bz1));
		// transom (flat stern) from the keel to the rail, with the balcony door of the great cabin
		double tw = hull.halfWidth(GalleonLayout.TRANSOM_Z) + 0.05;
		double tz0 = -hull.halfLength, tz1 = GalleonLayout.TRANSOM_Z + 0.05, tTop = hull.railY(GalleonLayout.TRANSOM_Z) + 0.1;
		solids.add(new ShipGeometry.LocalBox(-tw, hull.keelY(hull.halfLength), tz0, tw, main, tz1));
		solids.add(new ShipGeometry.LocalBox(door, main, tz0, tw, tTop, tz1));
		solids.add(new ShipGeometry.LocalBox(-tw, main, tz0, -door, tTop, tz1));
		solids.add(new ShipGeometry.LocalBox(-door, GalleonLayout.DOOR_TOP, tz0, door, tTop, tz1));
		// stern balcony: floor and balustrade
		double bh = GalleonLayout.BALCONY_HALF, bb = GalleonLayout.BALCONY_BACK, rt = GalleonLayout.RAIL_THICK;
		double railTop = main + GalleonLayout.BALCONY_RAIL;
		solids.add(new ShipGeometry.LocalBox(-bh, main - GalleonLayout.BALCONY_FLOOR, bb, bh, main, tz0));
		solids.add(new ShipGeometry.LocalBox(-bh, main, bb, bh, railTop, bb + rt));
		solids.add(new ShipGeometry.LocalBox(bh - rt, main, bb, bh, railTop, tz0));
		solids.add(new ShipGeometry.LocalBox(-bh, main, bb, -bh + rt, railTop, tz0));
		// guard rails at the front of the quarterdeck and of the forecastle, between the stairs
		double qx = GalleonLayout.STAIR_X0 - 0.1, fx = GalleonLayout.FC_STAIR_X0 - 0.1;
		solids.add(new ShipGeometry.LocalBox(-qx, qd, GalleonLayout.BULKHEAD_Z - rt, qx, qd + GalleonLayout.RAIL_HEIGHT, GalleonLayout.BULKHEAD_Z));
		solids.add(new ShipGeometry.LocalBox(-fx, fc, GalleonLayout.FORECASTLE_START, fx, fc + GalleonLayout.RAIL_HEIGHT,
				GalleonLayout.FORECASTLE_START + rt));
		// poop house and its roof
		solids.add(new ShipGeometry.LocalBox(-GalleonLayout.POOP_HALF, qd, GalleonLayout.POOP_BACK,
				GalleonLayout.POOP_HALF, GalleonLayout.POOP_WALL_TOP, GalleonLayout.POOP_FRONT));
		solids.add(new ShipGeometry.LocalBox(-GalleonLayout.POOP_HALF * 0.5, GalleonLayout.POOP_WALL_TOP, GalleonLayout.POOP_BACK,
				GalleonLayout.POOP_HALF * 0.5, (GalleonLayout.POOP_WALL_TOP + GalleonLayout.POOP_RIDGE) / 2 + 0.1, GalleonLayout.POOP_FRONT));
		// stairs to the quarterdeck (5 steps of 0.52) and to the forecastle (4 steps of 0.5), both sides
		double x0 = GalleonLayout.STAIR_X0, x1 = GalleonLayout.STAIR_X1, d = GalleonLayout.STEP_DEPTH;
		for (int k = 1; k <= 5; k++) {
			double top = main + (qd - main) * k / 5.0;
			double zFront = GalleonLayout.QD_STAIR_START - (k - 1) * d;
			for (double side : new double[] {1, -1}) {
				solids.add(box(side, x0, x1, main, top, zFront - d, zFront));
			}
		}
		for (int k = 1; k <= 4; k++) {
			double top = main + (fc - main) * k / 4.0;
			double zBack = GalleonLayout.FC_STAIR_START + (k - 1) * d;
			for (double side : new double[] {1, -1}) {
				solids.add(box(side, GalleonLayout.FC_STAIR_X0, GalleonLayout.FC_STAIR_X1, main, top, zBack, zBack + d));
			}
		}

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, qd + 0.28, GalleonLayout.PILOT_Z, true,
				new double[] {1.2, qd + 0.02, GalleonLayout.PILOT_Z}));
		// main deck: benches along the bulwarks
		double[] benchZ = {-4.5, -1.5, 4.0, 7.0};
		for (double z : benchZ) {
			for (double x : new double[] {3.1, -3.1}) {
				seats.add(seat(seats.size(), x, main, z, x * 0.75, z));
			}
		}
		// forecastle
		seats.add(seat(seats.size(), 2.2, fc, 11.6, 1.3, 11.6));
		seats.add(seat(seats.size(), -2.2, fc, 11.6, -1.3, 11.6));
		seats.add(seat(seats.size(), 0.0, fc, 15.4, 0.0, 14.6));
		// quarterdeck
		seats.add(seat(seats.size(), 2.7, qd, -11.4, 1.8, -11.4));
		seats.add(seat(seats.size(), -2.7, qd, -11.4, -1.8, -11.4));
		// great cabin
		seats.add(seat(seats.size(), 2.2, main, -13.0, 1.2, -12.2));
		seats.add(seat(seats.size(), -2.2, main, -13.0, -1.2, -12.2));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.7, qd + 0.1, GalleonLayout.HELM_Z - 0.35, 0.7, qd + 1.6, GalleonLayout.HELM_Z + 0.35);
		spec.masts = List.of(
				new ShipGeometry.Mast(0, GalleonLayout.MAIN_MAST_Z, main, GalleonLayout.MAIN_MAST_TOP, 0.32),
				new ShipGeometry.Mast(0, GalleonLayout.FORE_MAST_Z, fc, GalleonLayout.FORE_MAST_TOP, 0.26),
				new ShipGeometry.Mast(0, GalleonLayout.MIZZEN_Z, main, GalleonLayout.MIZZEN_TOP, 0.22));
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.15, 1.2, 3.2};
		spec.boardMinZ = GalleonLayout.POOP_FRONT + 0.4;
		spec.boardMaxZ = 16.0;
		// bench rows, and the cabin bulkhead (never board against it)
		spec.avoidZ = new double[] {benchZ[0], benchZ[1], benchZ[2], benchZ[3], GalleonLayout.BULKHEAD_Z};
		spec.sternPost = false;
		List<ShipGeometry.Gunport> ports = new ArrayList<>();
		for (double side : new double[] {1, -1}) {
			for (double z : GalleonLayout.GUNPORT_Z) {
				ports.add(new ShipGeometry.Gunport(ports.size(), side * hull.halfWidth(z), GalleonLayout.GUNPORT_Y, z, (int) side));
			}
		}
		spec.gunports = List.copyOf(ports);
		return new ShipType("galleon", "grand galion", new ShipGeometry(hull, spec), Ships::galleonConfig);
	}

	private static ShipGeometry.LocalBox box(double side, double x0, double x1, double y0, double y1, double z0, double z1) {
		return side > 0 ? new ShipGeometry.LocalBox(x0, y0, z0, x1, y1, z1) : new ShipGeometry.LocalBox(-x1, y0, z0, -x0, y1, z1);
	}

	private static ShipGeometry.Seat seat(int index, double x, double deck, double z, double dx, double dz) {
		return new ShipGeometry.Seat(index, x, deck + 0.47, z, false, new double[] {dx, deck + 0.02, dz});
	}

	/** Heavy ship: slow to gather way, long glide, wide turns, sails only (no oars to pivot). */
	private static ShipConfig galleonConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.0;
		c.normalSpeed = 4.5;
		c.fastSpeed = 7.5;
		c.reverseSpeed = 1.0;
		c.acceleration = 0.35;
		c.braking = 0.6;
		c.waterDrag = 0.07;
		c.maxTurnRate = 8.0;
		c.minTurnFactor = 0.1;
		c.helmRate = 0.9;
		c.helmReturnRate = 0.6;
		c.turnResponse = 0.6;
		c.turnSpeedLoss = 0.12;
		c.aiWaypointRadius = 12.0;
		c.aiStopRadius = 3.0;
		c.aiLookahead = 22.0;
		c.aiProbeDistance = 64.0;
		c.aiStuckSeconds = 10;
		c.aiTurnAroundSpeed = 2.0;
		return c;
	}

	// ------------------------------------------------------------------ great warship

	/**
	 * Great three-decker warship: 55 block hull (≈ 65 with the bowsprit), 13 wide, 42 high,
	 * main deck, forecastle, quarterdeck over the great cabin, poop deck, 58 gun ports, 24 seats.
	 * The same numbers are used by {@code tools/warship_shape.py}.
	 */
	public static final ShipType WARSHIP = warship();

	/** Warship layout, ship-local blocks (shared with the model generator). */
	public static final class WarshipLayout {
		public static final double MAIN_DECK_Y = 4.5;
		public static final double FORECASTLE_Y = 6.8;
		public static final double FORECASTLE_START = 17.0;
		/** Quarterdeck: floor of the great cabin's roof; poop deck above the upper cabin. */
		public static final double QUARTERDECK_Y = 7.1;
		public static final double QUARTERDECK_START = -10.0;
		public static final double POOP_Y = 9.4;
		public static final double POOP_START = -19.0;
		public static final double SLAB = 0.3;
		public static final double BULKHEAD_THICK = 0.3;
		public static final double DOOR_HALF = 0.8;
		public static final double DOOR_TOP = 6.55;
		public static final double TRANSOM_Z = -27.3;
		/** The warship floats high: the water is 1.1 blocks under the model origin. */
		public static final double WATERLINE_Y = -1.1;
		public static final double DECK_MAX_Z = 27.0;
		public static final double FORE_MAST_Z = 17.5;
		public static final double FORE_MAST_TOP = 34.0;
		public static final double MAIN_MAST_Z = 1.0;
		public static final double MAIN_MAST_TOP = 40.5;
		public static final double MIZZEN_Z = -14.5;
		public static final double MIZZEN_TOP = 30.0;
		public static final double HELM_Z = -11.2;
		public static final double PILOT_Z = -12.0;
		/** Stairs (both sides): main deck -> quarterdeck, quarterdeck -> poop, main deck -> forecastle. */
		public static final double QD_STAIR_X0 = 2.4;
		public static final double QD_STAIR_X1 = 4.4;
		public static final double QD_STAIR_START = -7.5;
		public static final double POOP_STAIR_X0 = 2.4;
		public static final double POOP_STAIR_X1 = 4.0;
		public static final double POOP_STAIR_START = -16.5;
		public static final double FC_STAIR_X0 = 1.8;
		public static final double FC_STAIR_X1 = 3.4;
		public static final double FC_STAIR_START = 14.5;
		public static final double STEP_DEPTH = 0.5;
		public static final double RAIL_HEIGHT = 0.9;
		public static final double RAIL_THICK = 0.12;
		/** Gun carriages on the main deck (each one is also a seat). */
		public static final double[] CARRIAGE_Z = {-7.0, -3.5, 0.0, 3.5, 7.0, 10.5};
		public static final double CARRIAGE_TOP = MAIN_DECK_Y + 0.6;
		/** Gun port rows in the hull side: lower and middle gun decks (decorative), and the main deck. */
		public static final double LOWER_GUN_Y = 1.5;
		public static final double MIDDLE_GUN_Y = 3.2;
		public static final double MAIN_GUN_Y = MAIN_DECK_Y + 0.9;
		public static final int LOWER_GUNS = 12;
		public static final int MIDDLE_GUNS = 11;
		public static final double GUN_Z0 = -20.0;
		public static final double GUN_Z1 = 18.5;

		private WarshipLayout() {
		}

		/** The hull bands and gun rows rise towards the ends, parallel to the sheer (not the flat decks). */
		public static final double BAND_LIFT = 0.7;

		/** Height added to the hull bands and gun rows at {@code z}. */
		public static double bandLift(HullShape hull, double z) {
			double a = Math.abs(z) / hull.halfLength;
			double rise = z >= 0 ? hull.params().railRiseFore : hull.params().railRiseAft;
			return BAND_LIFT * rise * Math.pow(a, hull.params().railPow);
		}

		/** Ship's boat on its skids on the main deck, between the main and fore masts (solid). */
		public static final double BOAT_Z0 = 4.6;
		public static final double BOAT_Z1 = 11.6;
		public static final double BOAT_HALF = 1.15;
		public static final double BOAT_TOP = MAIN_DECK_Y + 1.5;

		/** z of gun port k of a row of n ports. */
		public static double gunZ(int k, int n) {
			return GUN_Z0 + (GUN_Z1 - GUN_Z0) * (k + 0.5) / n;
		}
	}

	private static ShipType warship() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = 27.5;
		p.tip = 28.6;
		p.maxHalfWidth = 6.5;
		p.foreScale = 28.4;
		p.forePowA = 2.2;
		p.forePowB = 0.55;
		p.aftScale = 30.5;
		p.aftPowA = 3.2;
		p.aftPowB = 0.45;
		p.keelDepth = 2.9;
		p.keelRise = 2.2;
		p.keelPow = 3.5;
		p.waterlineY = WarshipLayout.WATERLINE_Y;
		p.railBase = 5.8;
		p.railRiseFore = 1.8;
		p.railRiseAft = 2.0;
		p.railPow = 2.5;
		p.mainDeckY = WarshipLayout.MAIN_DECK_Y;
		p.raisedDecks = List.of(new HullShape.RaisedDeck(WarshipLayout.FORECASTLE_START, Double.POSITIVE_INFINITY, WarshipLayout.FORECASTLE_Y));
		p.railFloors = List.of(
				new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, WarshipLayout.POOP_START, WarshipLayout.POOP_Y + 1.0),
				new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, WarshipLayout.QUARTERDECK_START, WarshipLayout.QUARTERDECK_Y + 1.0),
				new HullShape.RaisedDeck(WarshipLayout.FORECASTLE_START, Double.POSITIVE_INFINITY, WarshipLayout.FORECASTLE_Y + 1.0));
		p.deckMinZ = WarshipLayout.TRANSOM_Z;
		p.deckMaxZ = WarshipLayout.DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.5, 0.9}, {0.82, 0.55}, {0.97, 0.12}};
		HullShape hull = new HullShape(p);

		double main = WarshipLayout.MAIN_DECK_Y, fc = WarshipLayout.FORECASTLE_Y;
		double qd = WarshipLayout.QUARTERDECK_Y, poop = WarshipLayout.POOP_Y;
		double rt = WarshipLayout.RAIL_THICK, d = WarshipLayout.STEP_DEPTH;
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		// quarterdeck floor (roof of the great cabin), and the upper cabin under the poop deck
		// (closed: solid up to the poop deck), in 1 block bands following the hull
		for (double z0 = WarshipLayout.TRANSOM_Z; z0 < WarshipLayout.QUARTERDECK_START - 1e-6; z0 += 1.0) {
			double z1 = Math.min(WarshipLayout.QUARTERDECK_START, z0 + 1.0);
			double w = Math.min(hull.innerHalfWidth(z0), hull.innerHalfWidth(z1)) + 0.12;
			solids.add(new ShipGeometry.LocalBox(-w, qd - WarshipLayout.SLAB, z0, w, qd, z1));
		}
		for (double z0 = WarshipLayout.TRANSOM_Z; z0 < WarshipLayout.POOP_START - 1e-6; z0 += 1.0) {
			double z1 = Math.min(WarshipLayout.POOP_START, z0 + 1.0);
			double w = Math.min(hull.innerHalfWidth(z0), hull.innerHalfWidth(z1)) + 0.12;
			solids.add(new ShipGeometry.LocalBox(-w, qd, z0, w, poop, z1));
		}
		// great cabin bulkhead with its door
		double bz0 = WarshipLayout.QUARTERDECK_START - WarshipLayout.BULKHEAD_THICK, bz1 = WarshipLayout.QUARTERDECK_START;
		double bw = hull.innerHalfWidth(bz0) + 0.12, door = WarshipLayout.DOOR_HALF, slabBottom = qd - WarshipLayout.SLAB;
		solids.add(new ShipGeometry.LocalBox(door, main, bz0, bw, slabBottom, bz1));
		solids.add(new ShipGeometry.LocalBox(-bw, main, bz0, -door, slabBottom, bz1));
		solids.add(new ShipGeometry.LocalBox(-door, WarshipLayout.DOOR_TOP, bz0, door, slabBottom, bz1));
		// transom (flat stern) from the keel to the poop rail
		double tw = hull.halfWidth(WarshipLayout.TRANSOM_Z) + 0.05;
		solids.add(new ShipGeometry.LocalBox(-tw, hull.keelY(hull.halfLength), -hull.halfLength, tw,
				hull.railY(WarshipLayout.TRANSOM_Z) + 0.1, WarshipLayout.TRANSOM_Z + 0.05));
		// stairs: main deck -> quarterdeck (5 steps), quarterdeck -> poop deck (5), main deck -> forecastle (5)
		for (int k = 1; k <= 5; k++) {
			double zFront = WarshipLayout.QD_STAIR_START - (k - 1) * d;
			double zPoop = WarshipLayout.POOP_STAIR_START - (k - 1) * d;
			double zBack = WarshipLayout.FC_STAIR_START + (k - 1) * d;
			for (double side : new double[] {1, -1}) {
				solids.add(box(side, WarshipLayout.QD_STAIR_X0, WarshipLayout.QD_STAIR_X1, main, main + (qd - main) * k / 5.0, zFront - d, zFront));
				solids.add(box(side, WarshipLayout.POOP_STAIR_X0, WarshipLayout.POOP_STAIR_X1, qd, qd + (poop - qd) * k / 5.0, zPoop - d, zPoop));
				solids.add(box(side, WarshipLayout.FC_STAIR_X0, WarshipLayout.FC_STAIR_X1, main, main + (fc - main) * k / 5.0, zBack, zBack + d));
			}
		}
		// guard rails at the front of each raised deck, between the stairs
		double rh = WarshipLayout.RAIL_HEIGHT;
		solids.add(new ShipGeometry.LocalBox(-(WarshipLayout.QD_STAIR_X0 - 0.1), qd, bz1 - rt, WarshipLayout.QD_STAIR_X0 - 0.1, qd + rh, bz1));
		solids.add(new ShipGeometry.LocalBox(-(WarshipLayout.POOP_STAIR_X0 - 0.1), poop, WarshipLayout.POOP_START - rt,
				WarshipLayout.POOP_STAIR_X0 - 0.1, poop + rh, WarshipLayout.POOP_START));
		solids.add(new ShipGeometry.LocalBox(-(WarshipLayout.FC_STAIR_X0 - 0.1), fc, WarshipLayout.FORECASTLE_START,
				WarshipLayout.FC_STAIR_X0 - 0.1, fc + rh, WarshipLayout.FORECASTLE_START + rt));
		// the ship's boat on its skids in the waist
		solids.add(new ShipGeometry.LocalBox(-WarshipLayout.BOAT_HALF, main, WarshipLayout.BOAT_Z0, WarshipLayout.BOAT_HALF,
				WarshipLayout.BOAT_TOP, WarshipLayout.BOAT_Z1));
		// gun carriages on the main deck (seats)
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, qd + 0.28, WarshipLayout.PILOT_Z, true,
				new double[] {1.4, qd + 0.02, WarshipLayout.PILOT_Z}));
		for (double z : WarshipLayout.CARRIAGE_Z) {
			double in = hull.innerHalfWidth(z);
			for (double side : new double[] {1, -1}) {
				solids.add(box(side, in - 1.3, in - 0.1, main, WarshipLayout.CARRIAGE_TOP, z - 0.45, z + 0.45));
				seats.add(new ShipGeometry.Seat(seats.size(), side * (in - 0.75), WarshipLayout.CARRIAGE_TOP + 0.35, z, false,
						new double[] {side * (in - 2.0), main + 0.02, z}));
			}
		}
		// forecastle, quarterdeck, poop deck, great cabin
		seats.add(seat(seats.size(), 2.5, fc, 20.0, 1.5, 20.0));
		seats.add(seat(seats.size(), -2.5, fc, 20.0, -1.5, 20.0));
		seats.add(seat(seats.size(), 0.0, fc, 24.0, 0.0, 23.2));
		for (double z : new double[] {-12.5, -15.5}) {
			seats.add(seat(seats.size(), 4.0, qd, z, 3.0, z));
			seats.add(seat(seats.size(), -4.0, qd, z, -3.0, z));
		}
		seats.add(seat(seats.size(), 2.5, poop, -23.0, 1.5, -23.0));
		seats.add(seat(seats.size(), -2.5, poop, -23.0, -1.5, -23.0));
		seats.add(seat(seats.size(), 3.0, main, -16.0, 2.0, -15.2));
		seats.add(seat(seats.size(), -3.0, main, -16.0, -2.0, -15.2));

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, qd + 0.1, WarshipLayout.HELM_Z - 0.35, 0.8, qd + 1.8, WarshipLayout.HELM_Z + 0.35);
		spec.masts = List.of(
				new ShipGeometry.Mast(0, WarshipLayout.MAIN_MAST_Z, main, WarshipLayout.MAIN_MAST_TOP, 0.45),
				new ShipGeometry.Mast(0, WarshipLayout.FORE_MAST_Z, fc, WarshipLayout.FORE_MAST_TOP, 0.38),
				new ShipGeometry.Mast(0, WarshipLayout.MIZZEN_Z, main, WarshipLayout.MIZZEN_TOP, 0.32));
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.15, 1.2, 3.2, 5.5};
		spec.boardMinZ = WarshipLayout.POOP_START + 0.45;
		spec.boardMaxZ = 26.0;
		double[] avoid = new double[WarshipLayout.CARRIAGE_Z.length + 1];
		System.arraycopy(WarshipLayout.CARRIAGE_Z, 0, avoid, 0, WarshipLayout.CARRIAGE_Z.length);
		avoid[avoid.length - 1] = WarshipLayout.QUARTERDECK_START;
		spec.avoidZ = avoid;
		spec.sternPost = false;
		List<ShipGeometry.Gunport> ports = new ArrayList<>();
		for (double side : new double[] {1, -1}) {
			for (int k = 0; k < WarshipLayout.LOWER_GUNS; k++) {
				double z = WarshipLayout.gunZ(k, WarshipLayout.LOWER_GUNS);
				ports.add(new ShipGeometry.Gunport(ports.size(), side * hull.halfWidth(z), WarshipLayout.LOWER_GUN_Y + WarshipLayout.bandLift(hull, z), z, (int) side));
			}
			for (int k = 0; k < WarshipLayout.MIDDLE_GUNS; k++) {
				double z = WarshipLayout.gunZ(k, WarshipLayout.MIDDLE_GUNS);
				ports.add(new ShipGeometry.Gunport(ports.size(), side * hull.halfWidth(z), WarshipLayout.MIDDLE_GUN_Y + WarshipLayout.bandLift(hull, z), z, (int) side));
			}
			for (double z : WarshipLayout.CARRIAGE_Z) {
				ports.add(new ShipGeometry.Gunport(ports.size(), side * hull.halfWidth(z), WarshipLayout.MAIN_GUN_Y, z, (int) side));
			}
		}
		spec.gunports = List.copyOf(ports);
		return new ShipType("warship", "grand vaisseau de guerre", new ShipGeometry(hull, spec), Ships::warshipConfig);
	}

	/** Very heavy ship: long run-up, very long glide, very wide turns. */
	private static ShipConfig warshipConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.8;
		c.normalSpeed = 3.8;
		c.fastSpeed = 6.5;
		c.reverseSpeed = 0.8;
		c.acceleration = 0.22;
		c.braking = 0.4;
		c.waterDrag = 0.05;
		c.maxTurnRate = 5.5;
		c.minTurnFactor = 0.08;
		c.helmRate = 0.6;
		c.helmReturnRate = 0.4;
		c.turnResponse = 0.4;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 1.0;
		c.aiWaypointRadius = 18.0;
		c.aiStopRadius = 4.0;
		c.aiLookahead = 32.0;
		c.aiProbeDistance = 90.0;
		c.aiStuckSeconds = 15;
		c.aiTurnAroundSpeed = 2.4;
		return c;
	}

	// ------------------------------------------------------------------ red medieval galley

	/**
	 * Red medieval galley: 28 blocks overall (26 block hull), 5 wide, crescent hull rising into
	 * two carved dragon heads, 28 round shields, 24 oars, one mast with a red and white striped
	 * square sail, 10 seats. The same numbers are used by {@code tools/medieval_galley_shape.py}.
	 */
	public static final ShipType MEDIEVAL_GALLEY = medievalGalley();

	/** Red galley layout, ship-local blocks (shared with the model generator). */
	public static final class MedievalGalleyLayout {
		public static final double HALF_LENGTH = 12.6;
		public static final double TIP = 13.6;
		public static final double MAX_HALF_WIDTH = 2.5;
		public static final double MAIN_DECK_Y = 0.45;
		/** The water is 0.45 blocks under the model origin. */
		public static final double WATERLINE_Y = -0.45;
		public static final double DECK_MIN_Z = -11.2;
		public static final double DECK_MAX_Z = 11.2;
		public static final double MAST_Z = 0.6;
		public static final double MAST_TOP = 13.2;
		public static final double PILOT_Z = -10.2;
		/** Rowing benches carrying the passengers (two seats each). */
		public static final double[] BENCH_Z = {-7.6, -4.4, 3.6, 6.8};
		/** Seat at the bow, behind the dragon post. */
		public static final double BOW_SEAT_Z = 9.6;

		private MedievalGalleyLayout() {
		}
	}

	private static ShipType medievalGalley() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = MedievalGalleyLayout.HALF_LENGTH;
		p.tip = MedievalGalleyLayout.TIP;
		p.maxHalfWidth = MedievalGalleyLayout.MAX_HALF_WIDTH;
		p.foreScale = 13.2;
		p.forePowA = 2.1;
		p.forePowB = 0.75;
		p.aftScale = 13.2;
		p.aftPowA = 2.1;
		p.aftPowB = 0.75;
		p.keelDepth = 1.25;
		p.keelRise = 1.2;
		p.keelPow = 3.0;
		p.railBase = 1.75;
		p.railRiseFore = 2.2;
		p.railRiseAft = 2.2;
		p.railPow = 3.0;
		p.waterlineY = MedievalGalleyLayout.WATERLINE_Y;
		p.mainDeckY = MedievalGalleyLayout.MAIN_DECK_Y;
		p.deckMinZ = MedievalGalleyLayout.DECK_MIN_Z;
		p.deckMaxZ = MedievalGalleyLayout.DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.5, 0.88}, {0.85, 0.5}, {0.98, 0.1}};
		HullShape hull = new HullShape(p);

		double main = MedievalGalleyLayout.MAIN_DECK_Y;
		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, main + 0.28, MedievalGalleyLayout.PILOT_Z, true,
				new double[] {0.0, main + 0.02, MedievalGalleyLayout.PILOT_Z + 0.8}));
		for (double z : MedievalGalleyLayout.BENCH_Z) {
			for (double x : new double[] {0.95, -0.95}) {
				seats.add(seat(seats.size(), x, main, z, x * 0.85, z + 0.75));
			}
		}
		seats.add(seat(seats.size(), 0.0, main, MedievalGalleyLayout.BOW_SEAT_Z, 0.0, MedievalGalleyLayout.BOW_SEAT_Z - 0.8));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.5, main + 0.1, MedievalGalleyLayout.PILOT_Z - 0.6, 0.5, main + 1.1,
				MedievalGalleyLayout.PILOT_Z + 0.5);
		spec.masts = List.of(new ShipGeometry.Mast(0, MedievalGalleyLayout.MAST_Z, main, MedievalGalleyLayout.MAST_TOP, 0.2));
		spec.probeHeights = new double[] {MedievalGalleyLayout.WATERLINE_Y + 0.15, 0.15, 1.2};
		spec.boardMinZ = -9.6;
		spec.boardMaxZ = 9.0;
		spec.avoidZ = MedievalGalleyLayout.BENCH_Z;
		return new ShipType("medieval_galley", "galère rouge", new ShipGeometry(hull, spec), Ships::medievalGalleyConfig);
	}

	/** Light and nimble: quick to gather way, tight turns, the oars pivot the hull at rest. */
	private static ShipConfig medievalGalleyConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.8;
		c.normalSpeed = 6.0;
		c.fastSpeed = 9.5;
		c.reverseSpeed = 2.0;
		c.acceleration = 1.1;
		c.braking = 2.0;
		c.waterDrag = 0.2;
		c.maxTurnRate = 18.0;
		c.minTurnFactor = 0.35;
		c.helmRate = 1.8;
		c.turnResponse = 1.8;
		c.aiWaypointRadius = 8.0;
		c.aiLookahead = 14.0;
		c.aiProbeDistance = 40.0;
		return c;
	}

	// ------------------------------------------------------------------ steam paddleboat

	/**
	 * Armoured steam paddleboat: 22 blocks, 8 wide (12 with the paddle boxes), riveted iron hull,
	 * deckhouse with two funnels, a paddle wheel on each side, two guns, 8 seats.
	 * The same numbers are used by {@code tools/paddleboat_shape.py}.
	 */
	public static final ShipType STEAM_PADDLEBOAT = steamPaddleboat();

	/** Paddleboat layout, ship-local blocks (shared with the model generator). */
	public static final class PaddleboatLayout {
		public static final double HALF_LENGTH = 10.5;
		public static final double TIP = 11.2;
		public static final double MAX_HALF_WIDTH = 4.0;
		public static final double FORE_SCALE = 11.2;
		public static final double AFT_SCALE = 11.6;
		/** The water is 0.8 blocks under the model origin. */
		public static final double WATERLINE_Y = -0.8;
		public static final double MAIN_DECK_Y = 2.4;
		public static final double DECK_MIN_Z = -10.3;
		public static final double DECK_MAX_Z = 10.3;
		public static final double HOUSE_Z0 = -5.0;
		public static final double HOUSE_Z1 = 4.0;
		public static final double HOUSE_HALF = 2.5;
		public static final double HOUSE_TOP = 4.7;
		public static final double[] FUNNEL_Z = {-1.9, 1.3};
		public static final double FUNNEL_HALF = 0.55;
		public static final double FUNNEL_TOP = 10.9;
		public static final double HELM_Z = 5.75;
		public static final double PILOT_Z = 5.0;
		/** Paddle wheels (one on each side, |x|): centre, radius, inner / outer faces, box. */
		public static final double WHEEL_Z = 1.2;
		public static final double WHEEL_Y = 0.75;
		public static final double WHEEL_R = 2.45;
		public static final double WHEEL_X0 = 4.2;
		public static final double WHEEL_X1 = 5.7;
		public static final double BOX_X1 = 6.0;
		/** Raised round gun platforms (barbettes) under the two guns. */
		public static final double GUN_PLATFORM = 0.6;
		public static final double GUN_FORE_Z = 8.0;
		public static final double GUN_AFT_Z = -7.6;
		public static final double MAST_Z = -9.0;
		public static final double MAST_TOP = 9.6;

		private PaddleboatLayout() {
		}
	}

	private static ShipType steamPaddleboat() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = PaddleboatLayout.HALF_LENGTH;
		p.tip = PaddleboatLayout.TIP;
		p.maxHalfWidth = PaddleboatLayout.MAX_HALF_WIDTH;
		p.foreScale = PaddleboatLayout.FORE_SCALE;
		p.forePowA = 2.0;
		p.forePowB = 0.7;
		p.aftScale = PaddleboatLayout.AFT_SCALE;
		p.aftPowA = 3.2;
		p.aftPowB = 0.42;
		p.keelDepth = 1.8;
		p.keelRise = 0.7;
		p.keelPow = 4.0;
		p.railBase = 3.3;
		p.railRiseFore = 0.35;
		p.railRiseAft = 0.2;
		p.railPow = 2.0;
		p.waterlineY = PaddleboatLayout.WATERLINE_Y;
		p.mainDeckY = PaddleboatLayout.MAIN_DECK_Y;
		p.deckMinZ = PaddleboatLayout.DECK_MIN_Z;
		p.deckMaxZ = PaddleboatLayout.DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.6, 0.94}, {0.9, 0.62}, {0.99, 0.18}};
		HullShape hull = new HullShape(p);

		double main = PaddleboatLayout.MAIN_DECK_Y;
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		// the deckhouse (closed) and the funnels on its roof
		double hh = PaddleboatLayout.HOUSE_HALF;
		solids.add(new ShipGeometry.LocalBox(-hh, main, PaddleboatLayout.HOUSE_Z0, hh, PaddleboatLayout.HOUSE_TOP, PaddleboatLayout.HOUSE_Z1));
		for (double z : PaddleboatLayout.FUNNEL_Z) {
			double f = PaddleboatLayout.FUNNEL_HALF;
			solids.add(new ShipGeometry.LocalBox(-f, PaddleboatLayout.HOUSE_TOP, z - f, f, PaddleboatLayout.FUNNEL_TOP, z + f));
		}
		// the two guns on their carriages, on raised platforms one can step onto
		double gp = PaddleboatLayout.GUN_PLATFORM;
		for (double z : new double[] {PaddleboatLayout.GUN_FORE_Z, PaddleboatLayout.GUN_AFT_Z}) {
			solids.add(new ShipGeometry.LocalBox(-0.95, main, z - 0.95, 0.95, main + gp, z + 0.95));
			solids.add(new ShipGeometry.LocalBox(-0.5, main + gp, z - 0.8, 0.5, main + gp + 1.15, z + 0.8));
		}
		// the hull closes beyond the side walls: rounded counter at the stern, pointed bow
		for (double z = hull.halfLength - 0.1; z < PaddleboatLayout.FORE_SCALE - 0.1; z += 0.3) {
			double w = hull.halfWidth(z);
			solids.add(new ShipGeometry.LocalBox(-w, hull.keelY(z), z, w, hull.railY(z) + 0.1, z + 0.3));
		}
		for (double z = -hull.halfLength + 0.1; z > -PaddleboatLayout.AFT_SCALE + 0.1; z -= 0.3) {
			double w = hull.halfWidth(z);
			solids.add(new ShipGeometry.LocalBox(-w, hull.keelY(z), z - 0.3, w, hull.railY(z) + 0.1, z));
		}
		// the two paddle boxes, one on each side, outside the hull (above the water)
		double wz = PaddleboatLayout.WHEEL_Z, r = PaddleboatLayout.WHEEL_R + 0.35;
		for (double side : new double[] {1, -1}) {
			solids.add(box(side, hull.halfWidth(wz) - 0.05, PaddleboatLayout.BOX_X1, PaddleboatLayout.WATERLINE_Y - 0.2,
					PaddleboatLayout.WHEEL_Y + r + 0.1, wz - r, wz + r));
		}

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, main + 0.28, PaddleboatLayout.PILOT_Z, true,
				new double[] {1.4, main + 0.02, PaddleboatLayout.PILOT_Z}));
		// benches along the deckhouse, the gunners, the stern bench
		for (double z : new double[] {-3.4, -0.6}) {
			for (double x : new double[] {2.85, -2.85}) {
				seats.add(seat(seats.size(), x, main, z, x * 1.12, z + 0.8));
			}
		}
		// the gunners sit on the gun platforms, beside their guns
		seats.add(seat(seats.size(), 0.85, main + gp, PaddleboatLayout.GUN_FORE_Z - 0.4, 0.85, PaddleboatLayout.GUN_FORE_Z - 0.4));
		seats.add(seat(seats.size(), -0.85, main + gp, PaddleboatLayout.GUN_AFT_Z + 0.4, -0.85, PaddleboatLayout.GUN_AFT_Z + 0.4));
		seats.add(seat(seats.size(), 1.6, main, -9.0, 1.6, -8.2));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.65, main + 0.5, PaddleboatLayout.HELM_Z - 0.3, 0.65, main + 1.75,
				PaddleboatLayout.HELM_Z + 0.35);
		spec.masts = List.of(new ShipGeometry.Mast(0, PaddleboatLayout.MAST_Z, main, PaddleboatLayout.MAST_TOP, 0.12));
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {PaddleboatLayout.WATERLINE_Y + 0.15, 0.15, 1.2, 2.6};
		List<double[]> extra = new ArrayList<>();
		for (double side : new double[] {1, -1}) {
			for (double z = wz - r; z <= wz + r + 1e-6; z += r / 2) {
				extra.add(new double[] {side * (PaddleboatLayout.BOX_X1 - 0.1), PaddleboatLayout.WATERLINE_Y + 0.15, z});
				extra.add(new double[] {side * (PaddleboatLayout.BOX_X1 - 0.1), PaddleboatLayout.WHEEL_Y + 1.5, z});
			}
		}
		spec.extraProbes = List.copyOf(extra);
		spec.aiHalfWidth = PaddleboatLayout.BOX_X1 - 0.3;
		spec.boardMinZ = -9.2;
		spec.boardMaxZ = 8.6;
		spec.avoidZ = new double[] {PaddleboatLayout.HOUSE_Z0 - 0.4, PaddleboatLayout.HOUSE_Z1 + 0.4};
		spec.sternPost = false;
		return new ShipType("steam_paddleboat", "bateau à roue à vapeur", new ShipGeometry(hull, spec), Ships::paddleboatConfig);
	}

	/** Steam engine: progressive acceleration, handy at low speed (the wheel can pivot it), no sail. */
	private static ShipConfig paddleboatConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.2;
		c.normalSpeed = 5.0;
		c.fastSpeed = 7.5;
		c.reverseSpeed = 2.5;
		c.acceleration = 0.5;
		c.braking = 1.4;
		c.waterDrag = 0.12;
		c.maxTurnRate = 13.0;
		c.minTurnFactor = 0.5;
		c.helmRate = 1.4;
		c.helmReturnRate = 1.0;
		c.turnResponse = 1.3;
		c.turnSpeedLoss = 0.15;
		c.waveRocking = 0.8;
		c.aiWaypointRadius = 9.0;
		c.aiLookahead = 16.0;
		c.aiProbeDistance = 48.0;
		c.aiStuckSeconds = 8;
		c.aiTurnAroundSpeed = 1.0;
		c.furlSailWhenStopped = false;
		return c;
	}

	// ------------------------------------------------------------------ elven sailboat

	/**
	 * Elven sailboat: 30 blocks overall (24 block hull), 6 wide, slender turquoise and gold hull, a
	 * long carved prow, one tall mast with three triangular sails, 8 seats. The same numbers are
	 * used by {@code tools/elven_shape.py}.
	 */
	public static final ShipType ELVEN_SAILBOAT = elvenSailboat();

	/** Elven sailboat layout, ship-local blocks (shared with the model generator). */
	public static final class ElvenLayout {
		public static final double HALF_LENGTH = 12.0;
		public static final double TIP = 13.0;
		public static final double MAX_HALF_WIDTH = 3.0;
		/** The water is 0.6 blocks under the model origin. */
		public static final double WATERLINE_Y = -0.6;
		public static final double MAIN_DECK_Y = 0.6;
		public static final double DECK_MIN_Z = -11.0;
		public static final double DECK_MAX_Z = 11.0;
		public static final double MAST_Z = 1.0;
		public static final double MAST_TOP = 19.2;
		public static final double HELM_Z = -9.4;
		public static final double PILOT_Z = -10.2;
		/** Prow scroll tip (y, z), beyond the hull. */
		public static final double PROW_TIP_Z = 16.7;

		private ElvenLayout() {
		}
	}

	private static ShipType elvenSailboat() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = ElvenLayout.HALF_LENGTH;
		p.tip = ElvenLayout.TIP;
		p.maxHalfWidth = ElvenLayout.MAX_HALF_WIDTH;
		p.foreScale = 13.0;
		p.forePowA = 1.8;
		p.forePowB = 0.9;
		p.aftScale = 12.8;
		p.aftPowA = 2.2;
		p.aftPowB = 0.7;
		p.keelDepth = 1.9;
		p.keelRise = 1.3;
		p.keelPow = 2.5;
		p.railBase = 1.85;
		p.railRiseFore = 1.6;
		p.railRiseAft = 1.2;
		p.railPow = 2.5;
		p.waterlineY = ElvenLayout.WATERLINE_Y;
		p.mainDeckY = ElvenLayout.MAIN_DECK_Y;
		p.deckMinZ = ElvenLayout.DECK_MIN_Z;
		p.deckMaxZ = ElvenLayout.DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.4, 0.9}, {0.78, 0.55}, {0.97, 0.12}};
		HullShape hull = new HullShape(p);

		double main = ElvenLayout.MAIN_DECK_Y;
		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, main + 0.28, ElvenLayout.PILOT_Z, true,
				new double[] {0.7, main + 0.02, ElvenLayout.PILOT_Z + 0.9}));
		// cushioned benches along the sides, one at the bow
		for (double[] b : new double[][] {{1.9, -5.5}, {-1.9, -5.5}, {1.9, -2.0}, {-1.9, -2.0}, {1.75, 4.6}, {-1.75, 4.6}}) {
			seats.add(seat(seats.size(), b[0], main, b[1], b[0] * 0.55, b[1]));
		}
		seats.add(seat(seats.size(), 0.0, main, 8.4, 0.0, 7.6));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.6, main + 0.55, ElvenLayout.HELM_Z - 0.3, 0.6, main + 1.75, ElvenLayout.HELM_Z + 0.35);
		spec.masts = List.of(new ShipGeometry.Mast(0, ElvenLayout.MAST_Z, main, ElvenLayout.MAST_TOP, 0.17));
		spec.probeHeights = new double[] {ElvenLayout.WATERLINE_Y + 0.15, 0.15, 1.2};
		spec.boardMinZ = -9.6;
		spec.boardMaxZ = 9.6;
		spec.avoidZ = new double[] {-5.5, -2.0, 4.6};
		return new ShipType("elven_sailboat", "voilier elfique", new ShipGeometry(hull, spec), Ships::elvenConfig);
	}

	/** Light and fast, fluid turns (smooth yaw response), long glide. */
	private static ShipConfig elvenConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 3.0;
		c.normalSpeed = 6.8;
		c.fastSpeed = 10.5;
		c.reverseSpeed = 1.5;
		c.acceleration = 0.8;
		c.braking = 1.2;
		c.waterDrag = 0.1;
		c.maxTurnRate = 13.0;
		c.minTurnFactor = 0.15;
		c.helmRate = 1.2;
		c.helmReturnRate = 0.8;
		c.turnResponse = 1.1;
		c.turnSpeedLoss = 0.1;
		c.waveRocking = 0.9;
		c.aiWaypointRadius = 9.0;
		c.aiLookahead = 16.0;
		c.aiProbeDistance = 48.0;
		c.aiTurnAroundSpeed = 1.2;
		c.furlSailWhenStopped = false; // the triangular sails stay set at rest
		return c;
	}

	// ------------------------------------------------------------------ steampunk airship

	/**
	 * Steampunk airship: a long cream and blue-grey balloon (19 x 8.5 blocks) under a rope net, three
	 * triangular fins and a wooden propeller at the tail, and a 15 block wooden gondola hanging
	 * 5 blocks below it on ropes. It flies (no water, no gravity while flying); 6 places.
	 */
	public static final ShipType STEAMPUNK_AIRSHIP = steampunkAirship();

	/** Airship layout, ship-local blocks (shared with the model generator, tools/airship_shape.py). */
	public static final class AirshipLayout {
		public static final double HALF_LENGTH = 7.0;
		public static final double TIP = 7.6;
		public static final double MAX_HALF_WIDTH = 1.8;
		public static final double MAIN_DECK_Y = 0.0;
		public static final double DECK_MIN_Z = -6.4;
		public static final double DECK_MAX_Z = 6.4;
		public static final double LOWEST_Y = -1.65;
		public static final double BALLOON_Z = -1.1;
		public static final double BALLOON_Y = 10.4;
		public static final double BALLOON_HALF = 9.5;
		public static final double BALLOON_R = 4.25;
		public static final double BALLOON_REAR_T = 0.92;
		public static final double NOSE_ROD_Z = BALLOON_Z + BALLOON_HALF + 2.0;
		public static final double TAIL_END_Z = -14.6;
		public static final double PROP_Z = -15.2;
		public static final double PROP_R = 2.4;
		public static final double[] FIN_AZIMUTHS = {0.0, 125.0, -125.0};
		public static final double FIN_ROOT_Z0 = -3.6;
		public static final double FIN_ROOT_Z1 = -9.6;
		public static final double FIN_TIP_Z = -12.4;
		public static final double FIN_SPAN = 5.0;
		public static final double PILLAR_Z = BALLOON_Z;
		public static final double HELM_Z = -3.6;
		public static final double PILOT_Z = -4.5;
		public static final double ENGINE_Z0 = -6.6;
		public static final double ENGINE_Z1 = -5.0;
		public static final double[] BENCH_Z = {1.0, 3.2};
		public static final double BOW_SEAT_Z = 5.6;

		/** Balloon radius at z (body of revolution about y = BALLOON_Y), as in airship_shape.py. */
		public static double balloonRadius(double z) {
			double t = (z - BALLOON_Z) / BALLOON_HALF;
			double a = t >= 0 ? 2.4 : 2.0, b = t >= 0 ? 0.5 : 0.55;
			t = Math.abs(t);
			return t >= 1.0 ? 0.0 : BALLOON_R * Math.pow(1.0 - Math.pow(t, a), b);
		}

		private AirshipLayout() {
		}
	}

	private static ShipType steampunkAirship() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = AirshipLayout.HALF_LENGTH;
		p.tip = AirshipLayout.TIP;
		p.maxHalfWidth = AirshipLayout.MAX_HALF_WIDTH;
		p.foreScale = 7.6;
		p.forePowA = 2.0;
		p.forePowB = 0.75;
		p.aftScale = 7.5;
		p.aftPowA = 2.4;
		p.aftPowB = 0.6;
		p.keelDepth = 1.4;
		p.keelRise = 1.3;
		p.keelPow = 2.0;
		p.railBase = 1.0;
		p.railRiseFore = 1.7;
		p.railRiseAft = 1.3;
		p.railPow = 2.2;
		p.waterlineY = 0.0;
		p.mainDeckY = AirshipLayout.MAIN_DECK_Y;
		p.deckMinZ = AirshipLayout.DECK_MIN_Z;
		p.deckMaxZ = AirshipLayout.DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.5, 0.88}, {0.85, 0.5}, {0.98, 0.1}};
		HullShape hull = new HullShape(p);

		double main = AirshipLayout.MAIN_DECK_Y;
		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, main + 0.28, AirshipLayout.PILOT_Z, true,
				new double[] {0.9, main + 0.02, AirshipLayout.PILOT_Z + 0.4}));
		// benches along both sides, facing inwards, and a seat at the bow
		for (double z : AirshipLayout.BENCH_Z) {
			for (double x : new double[] {1.05, -1.05}) {
				seats.add(seat(seats.size(), x, main, z, x * 0.3, z + 0.9));
			}
		}
		seats.add(seat(seats.size(), 0.0, main, AirshipLayout.BOW_SEAT_Z, 0.0, AirshipLayout.BOW_SEAT_Z - 0.9));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.6, main + 0.45, AirshipLayout.HELM_Z - 0.3, 0.6, main + 1.65, AirshipLayout.HELM_Z + 0.35);
		double balloonBottom = AirshipLayout.BALLOON_Y - AirshipLayout.BALLOON_R;
		spec.masts = List.of(new ShipGeometry.Mast(0, AirshipLayout.PILLAR_Z, main, balloonBottom + 0.3, 0.3));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		// the engine at the stern of the gondola
		solids.add(new ShipGeometry.LocalBox(-0.75, main, AirshipLayout.ENGINE_Z0, 0.75, main + 1.5, AirshipLayout.ENGINE_Z1));
		// the balloon, in 1.5 block slices (players cannot walk through it, picking hits it)
		double front = AirshipLayout.BALLOON_Z + AirshipLayout.BALLOON_HALF;
		double rear = AirshipLayout.BALLOON_Z - AirshipLayout.BALLOON_HALF * AirshipLayout.BALLOON_REAR_T;
		for (double z0 = rear; z0 < front - 0.3; z0 += 1.5) {
			double z1 = Math.min(front, z0 + 1.5);
			double r = Math.min(AirshipLayout.balloonRadius(z0), AirshipLayout.balloonRadius(z1)) * 0.86;
			if (r < 0.3) {
				continue;
			}
			solids.add(new ShipGeometry.LocalBox(-r, AirshipLayout.BALLOON_Y - r, z0, r, AirshipLayout.BALLOON_Y + r, z1));
		}
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.15, 1.2};
		// terrain probes for everything outside the gondola: balloon rings, tail, propeller, fins, nose rod, keel
		List<double[]> probes = new ArrayList<>();
		for (double z = rear; z <= front + 1e-6; z += 1.4) {
			double r = AirshipLayout.balloonRadius(z);
			for (int k = 0; k < 8; k++) {
				double a = Math.toRadians(45 * k);
				probes.add(new double[] {Math.sin(a) * r, AirshipLayout.BALLOON_Y + Math.cos(a) * r, z});
			}
		}
		probes.add(new double[] {0, AirshipLayout.BALLOON_Y, front});
		probes.add(new double[] {0, AirshipLayout.BALLOON_Y, AirshipLayout.NOSE_ROD_Z});
		for (double z = rear; z >= AirshipLayout.PROP_Z; z -= 1.2) {
			probes.add(new double[] {0, AirshipLayout.BALLOON_Y, z});
		}
		for (int k = 0; k < 6; k++) {
			double a = Math.toRadians(60 * k + 30);
			double r = AirshipLayout.PROP_R;
			probes.add(new double[] {Math.sin(a) * r, AirshipLayout.BALLOON_Y + Math.cos(a) * r, AirshipLayout.PROP_Z});
		}
		for (double az : AirshipLayout.FIN_AZIMUTHS) {
			double a = Math.toRadians(az);
			double rr = AirshipLayout.balloonRadius(AirshipLayout.FIN_TIP_Z + 2.5) + AirshipLayout.FIN_SPAN;
			for (double f : new double[] {0.5, 1.0}) {
				double r = AirshipLayout.balloonRadius(AirshipLayout.FIN_ROOT_Z1) * (1 - f) + rr * f;
				double z = AirshipLayout.FIN_ROOT_Z1 + (AirshipLayout.FIN_TIP_Z - AirshipLayout.FIN_ROOT_Z1) * f;
				probes.add(new double[] {Math.sin(a) * r, AirshipLayout.BALLOON_Y + Math.cos(a) * r, z});
			}
		}
		for (double z = -5.5; z <= 5.5; z += 1.5) {
			probes.add(new double[] {0, AirshipLayout.LOWEST_Y + 0.05, z});
		}
		spec.extraProbes = List.copyOf(probes);
		spec.flying = true;
		spec.boundingRadius = -AirshipLayout.PROP_Z + AirshipLayout.PROP_R + 0.6;
		spec.aiReach = AirshipLayout.NOSE_ROD_Z + 0.3;
		spec.aiBack = -AirshipLayout.PROP_Z;
		spec.aiHalfWidth = AirshipLayout.BALLOON_R + 2.2;
		spec.lowestY = AirshipLayout.LOWEST_Y;
		spec.boardMinZ = -4.0;
		spec.boardMaxZ = 6.0;
		spec.avoidZ = new double[] {AirshipLayout.BENCH_Z[0], AirshipLayout.BENCH_Z[1], AirshipLayout.PILLAR_Z};
		spec.sternPost = false;
		return new ShipType("steampunk_airship", "dirigeable steampunk", new ShipGeometry(hull, spec), Ships::airshipConfig);
	}

	/** An airship, not an aeroplane: slow to gather way, long glide, gentle turns, can turn on the spot. */
	private static ShipConfig airshipConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.5;
		c.normalSpeed = 5.0;
		c.fastSpeed = 8.0;
		c.reverseSpeed = 1.5;
		c.acceleration = 0.55;
		c.braking = 0.9;
		c.waterDrag = 0.22;
		c.maxTurnRate = 12.0;
		c.minTurnFactor = 0.55;
		c.helmRate = 1.2;
		c.helmReturnRate = 1.0;
		c.turnResponse = 0.9;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 0.6;
		c.aiWaypointRadius = 8.0;
		c.aiStopRadius = 2.5;
		c.aiLookahead = 16.0;
		c.aiProbeDistance = 40.0;
		c.aiStuckSeconds = 8;
		c.aiTurnAroundSpeed = 0.8;
		c.furlSailWhenStopped = false;
		c.flight = new FlightConfig();
		return c;
	}

	/**
	 * The Nautilus of Captain Nemo: a 96 block steampunk submarine (ram and tail fin included),
	 * 14 wide, 17 high, 23 with the wheelhouse. Its rooms are described by an interior grid
	 * (tools/nautilus_interior.py): players walk inside while it sails and dives, the
	 * compartments stay dry under the sea.
	 */
	public static final ShipType NAUTILUS = nautilus();

	/** Nautilus layout, ship-local blocks (shared with tools/nautilus_shape.py and nautilus_interior.py). */
	public static final class NautilusLayout {
		public static final double BOW_Z = 41.5;
		public static final double STERN_Z = -35.0;
		public static final double MAX_HALF_WIDTH = 7.0;
		public static final double MAX_HALF_HEIGHT = 7.75;
		public static final double AXIS_Y = -0.25;
		public static final double SHELL = 0.5;
		public static final double RAM_TIP_Z = 48.0;
		public static final double TAIL_END_Z = -48.0;
		public static final double PROP_Z = -41.6;
		public static final double PROP_R = 3.2;
		public static final double FIN_TOP = 9.6;
		public static final double FIN_BOTTOM = -8.4;
		public static final double FIN_SPAN = 6.5;
		public static final double LOWER_FLOOR_Y = -4.5;
		public static final double MAIN_FLOOR_Y = 0.0;
		public static final double BILGE_FLOOR_Y = -7.0;
		public static final double WATERLINE_Y = -0.2;
		public static final double CASING_HALF_WIDTH = 2.0;
		public static final double CASING_TOP_Y = 9.0;
		public static final double CASING_Z0 = -24.0;
		public static final double CASING_Z1 = 27.0;
		/** The wheelhouse stands on the casing: its floor is the casing top. */
		public static final double TOWER_FLOOR_Y = CASING_TOP_Y;
		public static final double TOWER_TOP_Y = 12.5;
		public static final double TOWER_Z0 = 15.0;
		public static final double TOWER_Z1 = 22.5;
		public static final double TOWER_HALF_WIDTH = 2.0;
		public static final double LAMP_CAGE_Z0 = 10.0;
		public static final double LAMP_CAGE_TOP_Y = 14.2;
		public static final double LENS_Y = 13.0;
		public static final double PILOT_Z = 20.6;
		public static final double KEEL_BOTTOM_Y = -9.5;
		/** Ladder up to the hatch on the casing (stair hall), and the hatch itself (door 0). */
		public static final double HATCH_X = 1.5;
		public static final double HATCH_Z = -8.5;
		public static final int HATCH_DOOR = 0;
		public static final int AIRLOCK_INNER_DOOR = 8;
		public static final int AIRLOCK_OUTER_DOOR = 9;
		public static final int WHEELHOUSE_TRAP = 11;
		public static final String GRID = "/assets/medievalships/interiors/nautilus.grid";
		public static final String DECOR = "/assets/medievalships/interiors/nautilus_decor.json";

		/** Section scale at z (1 in the middle, 0 at the ends of the hull body), as in nautilus_shape.py. */
		public static double scale(double z) {
			double t, a, b;
			if (z >= 0) {
				t = z / BOW_Z;
				a = 2.8;
				b = 0.55;
			} else {
				t = z / STERN_Z;
				a = 4.0;
				b = 0.45;
			}
			return t >= 1.0 ? 0.0 : Math.pow(1.0 - Math.pow(t, a), b);
		}

		public static double halfWidth(double z) {
			return MAX_HALF_WIDTH * scale(z);
		}

		public static double halfHeight(double z) {
			return MAX_HALF_HEIGHT * scale(z);
		}

		private NautilusLayout() {
		}
	}

	private static ShipType nautilus() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = NautilusLayout.BOW_Z;
		p.tip = NautilusLayout.RAM_TIP_Z;
		p.maxHalfWidth = NautilusLayout.MAX_HALF_WIDTH;
		p.foreScale = NautilusLayout.BOW_Z;
		p.forePowA = 2.8;
		p.forePowB = 0.55;
		p.aftScale = -NautilusLayout.STERN_Z;
		p.aftPowA = 4.0;
		p.aftPowB = 0.45;
		p.keelDepth = NautilusLayout.MAX_HALF_HEIGHT - NautilusLayout.AXIS_Y;
		p.keelRise = 4.0;
		p.keelPow = 2.0;
		p.railBase = NautilusLayout.CASING_TOP_Y;
		p.railRiseFore = -4.0;
		p.railRiseAft = -4.0;
		p.railPow = 2.0;
		p.waterlineY = NautilusLayout.WATERLINE_Y;
		p.mainDeckY = NautilusLayout.MAIN_FLOOR_Y;
		p.deckMinZ = -6.0;
		p.deckMaxZ = 18.0;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = NautilusLayout.GRID;
		spec.decor = NautilusLayout.DECOR;
		spec.submarine = true;
		spec.hullProbes = false;
		double tower = NautilusLayout.TOWER_FLOOR_Y;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, tower + 0.28, NautilusLayout.PILOT_Z, true,
				new double[] {0.0, tower + 0.02, NautilusLayout.PILOT_Z - 1.0}));
		// the chairs, sofas and benches of the rooms
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(NautilusLayout.DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.7, tower + 0.4, NautilusLayout.PILOT_Z + 0.2, 0.7, tower + 1.8, NautilusLayout.PILOT_Z + 1.0);
		// terrain probes: rings around the hull body, the ram, the tail and its fins, the casing, the wheelhouse, the keels
		List<double[]> probes = new ArrayList<>();
		for (double z = NautilusLayout.STERN_Z + 1.0; z <= NautilusLayout.BOW_Z - 1.0 + 1e-6; z += 2.0) {
			double w = NautilusLayout.halfWidth(z), h = NautilusLayout.halfHeight(z);
			for (int k = 0; k < 12; k++) {
				double a = Math.toRadians(30 * k);
				probes.add(new double[] {Math.sin(a) * w, NautilusLayout.AXIS_Y + Math.cos(a) * h, z});
			}
		}
		for (double z = NautilusLayout.BOW_Z - 1.0; z <= NautilusLayout.RAM_TIP_Z + 1e-6; z += 1.0) {
			probes.add(new double[] {0, NautilusLayout.AXIS_Y, z});
		}
		for (double z = NautilusLayout.STERN_Z; z >= NautilusLayout.TAIL_END_Z - 1e-6; z -= 1.0) {
			probes.add(new double[] {0, NautilusLayout.AXIS_Y, z});
		}
		double fz = NautilusLayout.TAIL_END_Z + 0.5;
		probes.add(new double[] {0, NautilusLayout.AXIS_Y + NautilusLayout.FIN_TOP, fz});
		probes.add(new double[] {0, NautilusLayout.AXIS_Y + NautilusLayout.FIN_BOTTOM, fz});
		probes.add(new double[] {NautilusLayout.FIN_SPAN, NautilusLayout.AXIS_Y, fz});
		probes.add(new double[] {-NautilusLayout.FIN_SPAN, NautilusLayout.AXIS_Y, fz});
		for (double z = NautilusLayout.CASING_Z0; z <= NautilusLayout.CASING_Z1 + 1e-6; z += 2.0) {
			for (double x : new double[] {-NautilusLayout.CASING_HALF_WIDTH, NautilusLayout.CASING_HALF_WIDTH}) {
				probes.add(new double[] {x, NautilusLayout.CASING_TOP_Y, z});
			}
		}
		for (double z : new double[] {NautilusLayout.TOWER_Z0, NautilusLayout.TOWER_Z1}) {
			for (double x : new double[] {-NautilusLayout.TOWER_HALF_WIDTH, NautilusLayout.TOWER_HALF_WIDTH}) {
				probes.add(new double[] {x, NautilusLayout.TOWER_TOP_Y, z});
			}
		}
		probes.add(new double[] {0, NautilusLayout.LAMP_CAGE_TOP_Y, NautilusLayout.LAMP_CAGE_Z0});
		for (double z : new double[] {10.0, 15.5, 21.0, -22.0, -14.0, -6.0}) {
			probes.add(new double[] {0, NautilusLayout.KEEL_BOTTOM_Y, z});
		}
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = NautilusLayout.RAM_TIP_Z + 1.0;
		spec.aiReach = NautilusLayout.RAM_TIP_Z;
		spec.aiBack = -NautilusLayout.TAIL_END_Z;
		spec.aiHalfWidth = NautilusLayout.MAX_HALF_WIDTH + 1.0;
		spec.lowestY = NautilusLayout.KEEL_BOTTOM_Y;
		spec.boardMinZ = 13.5;
		spec.boardMaxZ = 17.5;
		spec.boardHalfWidth = 3.5;
		spec.avoidZ = new double[] {};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("nautilus", "Nautilus", new ShipGeometry(hull, spec), Ships::nautilusConfig);
	}

	/** A very large hull: slow to gather way and to stop, wide turns, ballasts slow to answer. */
	private static ShipConfig nautilusConfig() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.0;
		c.normalSpeed = 4.5;
		c.fastSpeed = 7.0;
		c.reverseSpeed = 1.5;
		c.acceleration = 0.35;
		c.braking = 0.7;
		c.waterDrag = 0.12;
		c.maxTurnRate = 6.0;
		c.minTurnFactor = 0.25;
		c.helmRate = 0.8;
		c.helmReturnRate = 0.8;
		c.turnResponse = 0.6;
		c.turnSpeedLoss = 0.15;
		c.waveRocking = 0.25;
		c.aiWaypointRadius = 14.0;
		c.aiStopRadius = 4.0;
		c.aiLookahead = 30.0;
		c.aiProbeDistance = 70.0;
		c.aiStuckSeconds = 10;
		c.aiTurnAroundSpeed = 0.6;
		c.furlSailWhenStopped = false;
		c.dive = new DiveConfig();
		return c;
	}

	public static final List<ShipType> ALL = List.of(GALLEY, GALLEON, WARSHIP, MEDIEVAL_GALLEY, STEAM_PADDLEBOAT, ELVEN_SAILBOAT, STEAMPUNK_AIRSHIP, NAUTILUS);

	/**
	 * Other names accepted by the commands (the ids used in saves and configs never change):
	 * {@code grand_warship} is the great warship ({@code warship}).
	 */
	public static final java.util.Map<String, ShipType> ALIASES = java.util.Map.of("grand_warship", WARSHIP);

	public static ShipType byId(String id) {
		for (ShipType t : ALL) {
			if (t.id().equalsIgnoreCase(id)) {
				return t;
			}
		}
		return id == null ? null : ALIASES.get(id.toLowerCase(java.util.Locale.ROOT));
	}
}
