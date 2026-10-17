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
		p.keelDepth = 1.8;
		p.keelRise = 1.4;
		p.keelPow = 3.5;
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
		p.keelDepth = 1.9;
		p.keelRise = 1.3;
		p.keelPow = 4.0;
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

	public static final List<ShipType> ALL = List.of(GALLEY, GALLEON, WARSHIP);

	public static ShipType byId(String id) {
		for (ShipType t : ALL) {
			if (t.id().equalsIgnoreCase(id)) {
				return t;
			}
		}
		return null;
	}
}
