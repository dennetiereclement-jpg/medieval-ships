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
		public static final double STAIR_X1 = 3.5;
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
		// transom (flat stern) from the keel to the rail
		double tw = hull.halfWidth(GalleonLayout.TRANSOM_Z) + 0.05;
		solids.add(new ShipGeometry.LocalBox(-tw, hull.keelY(hull.halfLength), -hull.halfLength, tw,
				hull.railY(GalleonLayout.TRANSOM_Z) + 0.1, GalleonLayout.TRANSOM_Z + 0.05));
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
				solids.add(box(side, x0, x1, main, top, zBack, zBack + d));
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
		spec.avoidZ = benchZ;
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

	public static final List<ShipType> ALL = List.of(GALLEY, GALLEON);

	public static ShipType byId(String id) {
		for (ShipType t : ALL) {
			if (t.id().equalsIgnoreCase(id)) {
				return t;
			}
		}
		return null;
	}
}
