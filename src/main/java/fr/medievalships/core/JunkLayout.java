package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Dragon Junk ({@code dragon_junk}): an Asian-style junk that flies, 39 blocks from its square bow to the top of its
 * transom (42 with the pale beak pointing forwards low down under the bow, 44 with the short bowsprit), 8.8 wide, about
 * 30 high from the anchor to the masthead. A long dark hull in a rounded V, narrowing forwards to a square bow half as wide,
 * its counter sweeping up aft in a V to a small raked transom; a white band of plaster blocks along the bulwarks, red
 * lacquered panels aft under a carved frieze; the stern gallery round the multi-level stern house (white plaster, dark
 * beams) under a tall red roof of four stacked tiers, the porch's lower gable in front of it, the companion house's lean-to
 * at the break; one mast stepped far forward and raked aft carries the great red sail with the black dragon: two battened
 * panels spread in a V from a short yard under the masthead. It flies like the other airships ({@link Flight}), with a
 * handling between the slow Crystal Airship and the agile Rustic Skiff, and can hover low over the water; its rooms are
 * described by an interior grid (tools/junk_interior.py): players walk on its decks and in its rooms (main room, storage,
 * bedroom, stern cabin) while it flies.
 *
 * <p>Ship-local blocks, shared with tools/junk_shape.py (same numbers, same formulas; checked by JunkTest):
 * x = lateral (+x = port), y = up (0 = the main deck), z = forward (+z = bow).
 */
public final class JunkLayout {
	// ---- levels
	public static final double MAIN_DECK_Y = 0.0;
	public static final double QUARTERDECK_Y = 2.5;
	public static final double LOWER_DECK_Y = -3.0;
	public static final double BEDROOM_Y = -0.5;
	public static final double HOUSE_CEIL_Y = 6.0;
	public static final double RAIL_H = 1.0;

	// ---- hull
	public static final double BOW_Z = 19.5;
	/** The transom's top; it rakes forwards down to its foot ({@link #TRANSOM_FOOT}), the counter sweeping down from there. */
	public static final double STERN_Z = -19.5;
	public static final double HULL_HW = 4.4;
	public static final double BOW_HW = 2.4;
	public static final double STERN_HW = 3.9;
	private static final double[] FULL_Z = {-5.0, 4.0};
	private static final double BOW_PLAN_POW = 1.4;
	private static final double STERN_PLAN_POW = 2.0;
	public static final double SIDE_Y = 1.0;
	private static final double FLAT = 0.03;
	private static final double BILGE_POW = 4.0;
	private static final double BILGE_Q = 1.6;
	public static final double SHEER_FORE = 1.0;
	private static final double[] BOW_SHEER = {10.0, 0.75};
	public static final double BREAK_Z = -1.5;
	private static final double[] BREAK_RISE = {1.2, -1.5};
	public static final double WALE_Y = -0.9;
	public static final double BEAK_TIP_Z = 22.6;
	public static final double BEAK_TIP_Y = -3.6;
	private static final double PINCH_Z = 12.5;
	private static final double[] RUN = {-9.0, 7.0, 0.5, 1.0, 0.5};
	public static final double[] TRANSOM_FOOT = {-19.1, 0.9};
	private static final double[][] KEEL_PTS = {TRANSOM_FOOT, {-18.3, -0.45}, {-17.2, -1.85}, {-15.8, -3.15}, {-14.0, -4.15}, {-11.5, -4.8},
			{-8.5, -5.04}, {-4.0, -5.1}, {1.0, -5.08}, {6.0, -4.92}, {10.0, -4.66}, {14.0, -4.3}, {17.0, -4.02}, {20.0, -3.8}, {22.6, -3.6}};
	private static final double[] KEEL_SLOPES = slopes(KEEL_PTS);

	// ---- stern house and its roofs, the stern gallery, the companion house
	public static final double HOUSE_FRONT_Z = -8.0;
	public static final double EAVE_Y = 6.15;
	public static final double RIDGE_Y = 12.5;
	public static final double TIER_LIFT = 0.3;
	public static final double ROOF_HW = 5.2;
	public static final double ROOF_FRONT_Z = -8.6;
	public static final double GABLE_LEAN = 0.08;
	public static final double ROOF_BACK_Z = -20.9;
	public static final int ROOF_TIERS = 4;
	private static final double[] ROOF_EDGES = {0.0, 1.45, 2.25, 3.35};
	private static final double[] ROOF_CURVE = {0.32, 1.8};
	public static final double PORCH_FRONT_Z = -5.6;
	public static final double PORCH_RIDGE_Y = 10.1;
	private static final double[] PORCH_CURVE = {0.55, 1.6};
	public static final double[][] STERN_POLE = {{0.0, 13.6, -10.5}, {0.0, 16.6, -13.9}};
	public static final double GALLERY_OUT = 0.9;
	public static final double GALLERY_AFT = 1.05;
	public static final double GALLERY_RAIL_H = 1.0;
	public static final double[] MID_Z = {-1.5, 4.0};
	public static final double MID_WALL_Y = 3.0;
	public static final double MID_HIGH_Y = 4.6;
	public static final double MID_EAVE_Y = 2.4;

	// ---- mast, sail, spars
	public static final double[] MAST_FOOT = {0.0, 0.0, 16.5};
	public static final double MAST_RAKE_DEG = 26.0;
	public static final double MAST_HEAD_Y = 22.0;
	public static final double[][] YARD = {{0.0, 18.0, 10.42}, {0.0, 18.0, 5.62}};
	public static final double[] SAIL_TACK = {0.45, 3.3, 19.6};
	public static final double[] SAIL_CLEW = {6.4, 1.2, 3.0};
	public static final double SAIL_BILLOW = 0.85;
	public static final double[][] FORE_BOOM = {{0.0, 3.35, 12.2}, {0.0, 3.5, 19.9}};
	public static final double[] CLEW_BOOM_END = {4.75, -1.25, -5.0};
	public static final double[][] BOWSPRIT = {{0.0, 1.3, 18.4}, {0.0, 2.45, 23.4}};
	public static final double[][] BOW_YARD = {{0.0, 1.42, 20.3}, {0.0, 1.98, 22.8}};
	public static final double BOW_SAIL_DROP = 2.3;

	// ---- fittings
	public static final double[] ANCHOR = {4.6, 7.3};
	public static final double ANCHOR_TOP_Y = -5.3;
	public static final double ANCHOR_BOTTOM_Y = -7.6;
	public static final double HELM_Z = -4.8;
	public static final double PILOT_Z = -5.6;
	/** The rudder under the counter: its stock's z, the blade's bottom, its width aft of the stock. */
	public static final double[] RUDDER = {-16.0, -4.9, 1.7};
	public static final double[][] SIDE_STAIR = {{4.65, 2.3, -8.3}, {4.65, -2.6, -4.6}};
	/** The keel stays this high over the water when the junk comes down on it (DragonJunkEntity). */
	public static final double WATER_HOVER = 0.8;

	// ---- interior
	public static final String GRID = "/assets/medievalships/interiors/dragon_junk.grid";
	public static final String DECOR = "/assets/medievalships/interiors/dragon_junk_decor.json";
	/** Doors of the interior grid (tools/junk_interior.py DOORS). */
	public static final int STERN_DOOR = 0;
	public static final int BEDROOM_DOOR = 1;
	public static final int COMPANION_DOOR = 2;
	public static final int STORAGE_DOOR = 3;
	public static final int HATCH = 4;

	private JunkLayout() {
	}

	// ------------------------------------------------------------------ shape (as in junk_shape.py)

	private static double smooth(double t) {
		t = Math.max(0.0, Math.min(1.0, t));
		return t * t * (3 - 2 * t);
	}

	private static double[] slopes(double[][] p) {
		int n = p.length;
		double[] d = new double[n - 1];
		for (int i = 0; i < n - 1; i++) {
			d[i] = (p[i + 1][1] - p[i][1]) / (p[i + 1][0] - p[i][0]);
		}
		double[] m = new double[n];
		m[0] = d[0];
		m[n - 1] = d[n - 2];
		for (int i = 1; i < n - 1; i++) {
			m[i] = d[i - 1] * d[i] <= 0 ? 0.0 : (d[i - 1] + d[i]) / 2;
		}
		for (int i = 0; i < n - 1; i++) {
			if (d[i] == 0) {
				m[i] = 0.0;
				m[i + 1] = 0.0;
				continue;
			}
			double a = m[i] / d[i], b = m[i + 1] / d[i];
			double s = a * a + b * b;
			if (s > 9) {
				double t = 3 / Math.sqrt(s);
				m[i] = t * a * d[i];
				m[i + 1] = t * b * d[i];
			}
		}
		return m;
	}

	/** z of the raked transom at height y: its foot forward of its top. */
	public static double transomZ(double y) {
		double f = (QUARTERDECK_Y - y) / (QUARTERDECK_Y - TRANSOM_FOOT[1]);
		return STERN_Z + (TRANSOM_FOOT[0] - STERN_Z) * Math.max(0.0, Math.min(1.0, f));
	}

	/** Bottom of the hull at z: the keel, the raked transom's lower edge aft of its foot, the beak's lower edge forward of the bow. */
	public static double keelY(double z) {
		double[][] p = KEEL_PTS;
		if (z <= p[0][0]) {
			double f = (z - STERN_Z) / (TRANSOM_FOOT[0] - STERN_Z);
			return QUARTERDECK_Y + (TRANSOM_FOOT[1] - QUARTERDECK_Y) * Math.max(0.0, Math.min(1.0, f));
		}
		if (z >= p[p.length - 1][0]) {
			return p[p.length - 1][1];
		}
		int i = 0;
		while (z > p[i + 1][0]) {
			i++;
		}
		double h = p[i + 1][0] - p[i][0];
		double t = (z - p[i][0]) / h;
		double h00 = 2 * t * t * t - 3 * t * t + 1, h10 = t * t * t - 2 * t * t + t, h01 = -2 * t * t * t + 3 * t * t, h11 = t * t * t - t * t;
		return h00 * p[i][1] + h10 * h * KEEL_SLOPES[i] + h01 * p[i + 1][1] + h11 * h * KEEL_SLOPES[i + 1];
	}

	/** Half width of the hull at the sheer at z, between the transom and the square bow. */
	public static double planHw(double z) {
		if (z > BOW_Z || z < STERN_Z) {
			return 0.0;
		}
		if (z > FULL_Z[1]) {
			double t = (z - FULL_Z[1]) / (BOW_Z - FULL_Z[1]);
			return HULL_HW - (HULL_HW - BOW_HW) * Math.pow(t, BOW_PLAN_POW);
		}
		if (z < FULL_Z[0]) {
			double t = (FULL_Z[0] - z) / (FULL_Z[0] - STERN_Z);
			return HULL_HW - (HULL_HW - STERN_HW) * Math.pow(t, STERN_PLAN_POW);
		}
		return HULL_HW;
	}

	/** Top edge of the beak forward of the bow face. */
	public static double beakTop(double z) {
		double t = (z - BOW_Z) / (BEAK_TIP_Z - BOW_Z);
		return WALE_Y + (BEAK_TIP_Y - WALE_Y) * Math.max(0.0, Math.min(1.0, t));
	}

	/**
	 * Top of the hull's side planking: the white bulwark of the main deck, sweeping up to the bow, rising at the break to the
	 * quarterdeck.
	 */
	public static double sheerY(double z) {
		return SHEER_FORE + (QUARTERDECK_Y - SHEER_FORE) * smooth((BREAK_RISE[0] - z) / (BREAK_RISE[0] - BREAK_RISE[1]))
				+ BOW_SHEER[1] * Math.pow(smooth((z - BOW_SHEER[0]) / (BOW_Z - BOW_SHEER[0])), 1.5);
	}

	public static double deckY(double z) {
		return z <= BREAK_Z ? QUARTERDECK_Y : MAIN_DECK_Y;
	}

	/** Half width of the outside of the hull at (z, y) (0 outside it). */
	public static double hullX(double z, double y) {
		double k = keelY(z);
		if (y < k || z < STERN_Z || z > BEAK_TIP_Z) {
			return 0.0;
		}
		double w;
		if (z > BOW_Z) {
			if (y > beakTop(z)) {
				return 0.0;
			}
			w = BOW_HW;
		} else {
			w = planHw(z);
		}
		if (w <= 0) {
			return 0.0;
		}
		double x;
		if (y >= SIDE_Y) {
			x = w;
		} else {
			double ks = keelY(Math.max(z, TRANSOM_FOOT[0]));
			double eta = (y - ks) / (SIDE_Y - ks);
			double fr = smooth((RUN[0] - z) / RUN[1]);
			double flat = FLAT * (1.0 - RUN[2] * fr);
			x = w * (flat + (1.0 - flat) * Math.pow(1.0 - Math.pow(1.0 - eta, BILGE_POW - RUN[3] * fr), BILGE_Q + RUN[4] * fr));
		}
		if (z > PINCH_Z && y < WALE_Y + 0.1) {
			double pz = smooth((z - PINCH_Z) / (BEAK_TIP_Z - PINCH_Z));
			double gy = smooth((WALE_Y + 0.1 - y) / 0.8);
			x *= 1.0 - 0.9 * pz * gy;
		}
		if (z > BEAK_TIP_Z - 1.6) {
			x *= (BEAK_TIP_Z - z) / 1.6;
		}
		return x;
	}

	/** Height of the stern house's main roof (its tiers' envelope) at a distance d from its eaves. */
	public static double roofY(double d) {
		d = Math.max(0.0, Math.min(ROOF_HW, d));
		double t = d / ROOF_HW;
		return EAVE_Y + (RIDGE_Y - EAVE_Y) * (ROOF_CURVE[0] * t + (1.0 - ROOF_CURVE[0]) * (1.0 - Math.pow(1.0 - t, ROOF_CURVE[1])));
	}

	/** Height of the main roof's tiles at a distance d from the eaves, with the lifts of the stacked tiers. */
	public static double roofTop(double d) {
		int k = 0;
		for (int i = 0; i < ROOF_EDGES.length; i++) {
			if (d >= ROOF_EDGES[i] - 1e-9) {
				k = i;
			}
		}
		return roofY(d) + TIER_LIFT * k;
	}

	public static double ridgeTop() {
		return RIDGE_Y + TIER_LIFT * (ROOF_TIERS - 1);
	}

	public static double roofFrontZ(double d) {
		return ROOF_FRONT_Z + GABLE_LEAN * Math.max(0.0, d);
	}

	/** Height of the porch's lower gable roof at a distance d from its eaves. */
	public static double porchY(double d) {
		d = Math.max(0.0, Math.min(ROOF_HW, d));
		double t = d / ROOF_HW;
		return EAVE_Y + (PORCH_RIDGE_Y - EAVE_Y) * (PORCH_CURVE[0] * t + (1.0 - PORCH_CURVE[0]) * Math.pow(t, PORCH_CURVE[1]));
	}

	/** Point of the raked mast's axis at height y. */
	public static double[] mastPoint(double y) {
		double a = Math.toRadians(MAST_RAKE_DEG);
		double t = (y - MAST_FOOT[1]) / Math.cos(a);
		return new double[] {0.0, y, MAST_FOOT[2] - Math.sin(a) * t};
	}

	public static double[] mastHead() {
		return mastPoint(MAST_HEAD_Y);
	}

	/** Head fore, head aft, tack, clew of the sail panel on this side (+1 port, -1 starboard). */
	public static double[][] sailCorners(int side) {
		return new double[][] {{side * 0.14, YARD[0][1] - 0.18, YARD[0][2] - 0.2}, {side * 0.14, YARD[1][1] - 0.18, YARD[1][2] + 0.25},
				{side * SAIL_TACK[0], SAIL_TACK[1], SAIL_TACK[2]}, {side * SAIL_CLEW[0], SAIL_CLEW[1], SAIL_CLEW[2]}};
	}

	private static double[] lerp(double[] a, double[] b, double t) {
		return new double[] {a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t};
	}

	/** Outward normal of the panel on this side. */
	public static double[] sailNormal(int side) {
		double[][] c = sailCorners(side);
		double[] a = {c[3][0] - c[0][0], c[3][1] - c[0][1], c[3][2] - c[0][2]};
		double[] b = {c[2][0] - c[1][0], c[2][1] - c[1][1], c[2][2] - c[1][2]};
		double[] n = {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
		double l = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
		double s = n[0] * side > 0 ? 1.0 / l : -1.0 / l;
		return new double[] {n[0] * s, n[1] * s, n[2] * s};
	}

	/** Point of the panel (s from the head down to the foot, t from the luff to the leech), billowed by the wind. */
	public static double[] sailPoint(int side, double s, double t) {
		double[][] c = sailCorners(side);
		double[] p = lerp(lerp(c[0], c[1], t), lerp(c[2], c[3], t), s);
		double[] n = sailNormal(side);
		double sc = Math.max(0.0, Math.min(1.0, s)), tc = Math.max(0.0, Math.min(1.0, t));
		double b = SAIL_BILLOW * Math.pow(Math.sin(Math.PI * sc), 0.9) * Math.pow(Math.sin(Math.PI * tc), 0.8);
		return new double[] {p[0] + n[0] * b, p[1] + n[1] * b, p[2] + n[2] * b};
	}

	/** Lowest point: the anchor's crown. */
	public static double lowestY() {
		return ANCHOR_BOTTOM_Y - 0.05;
	}

	/** Highest point: the masthead's truck. */
	public static double topY() {
		return MAST_HEAD_Y + 0.9;
	}

	// ------------------------------------------------------------------ the ship type

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = BOW_Z;
		p.tip = BOWSPRIT[1][2];
		p.maxHalfWidth = HULL_HW;
		p.foreScale = 24.0;
		p.forePowA = 3.0;
		p.forePowB = 0.5;
		p.aftScale = 24.0;
		p.aftPowA = 3.0;
		p.aftPowB = 0.5;
		// keelY(0) under the whole grid, so the collision query never cuts the lower deck
		p.keelDepth = 6.0;
		p.keelRise = 0.0;
		p.keelPow = 2.0;
		p.railBase = SHEER_FORE;
		p.railRiseFore = 0.0;
		p.railRiseAft = 0.0;
		p.waterlineY = 0.0;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = BREAK_Z;
		p.deckMaxZ = BOW_Z - 0.5;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		spec.flying = true;
		spec.hullProbes = false;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		double q = QUARTERDECK_Y;
		// the pilot stands on the quarterdeck behind the wheel, under the eaves of the stern house's porch
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, q + 0.28, PILOT_Z, true, new double[] {1.3, q + 0.02, PILOT_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, q + 0.5, HELM_Z - 0.6, 0.8, q + 2.0, HELM_Z + 0.3);
		// not solid (the grid is): the mast's foot keeps boarding spots off it, its head gives the height
		double[] head = mastHead();
		spec.masts = List.of(new ShipGeometry.Mast(0.0, MAST_FOOT[2], MAIN_DECK_Y, topY(), 0.4),
				new ShipGeometry.Mast(0.0, head[2], MAIN_DECK_Y + 6.0, topY(), 0.25));
		spec.extraProbes = List.copyOf(probes());
		spec.boundingRadius = Math.hypot(BOWSPRIT[1][2] + 0.5, SAIL_CLEW[0] + 0.6) + 1.0;
		spec.aiReach = BOWSPRIT[1][2] + 0.3;
		spec.aiBack = -ROOF_BACK_Z + 0.8;
		spec.aiHalfWidth = SAIL_CLEW[0] + 0.6;
		spec.lowestY = lowestY();
		spec.boardMinZ = 8.5;
		spec.boardMaxZ = 12.5;
		spec.boardHalfWidth = 1.0;
		spec.avoidZ = new double[] {};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("dragon_junk", "Jonque du Dragon", new ShipGeometry(hull, spec), JunkLayout::config);
	}

	/**
	 * Terrain probes over the whole volume: sections of the hull (keel, bilge, sides, bulwark) from the transom to the beak,
	 * the counter and the rudder, the stern gallery, the stern house and its roofs (eaves, tiers, ridge, the staff, the
	 * porch's gable), the companion house's roof, the mast, the yard, the sail's corners and its middle, the booms, the
	 * bowsprit, the bow sail, the anchor, the outside stair.
	 */
	static List<double[]> probes() {
		List<double[]> probes = new ArrayList<>();
		for (double z = STERN_Z + 0.2; z <= BEAK_TIP_Z - 0.2 + 1e-6; z += 2.0) {
			double k = keelY(z);
			probes.add(new double[] {0, k + 0.1, z});
			double top = z > BOW_Z ? beakTop(z) : sheerY(z) + (z <= BREAK_Z ? RAIL_H : 0.0);
			for (double y : new double[] {k + 0.6, (k + SIDE_Y) / 2, SIDE_Y, top - 0.1}) {
				double x = hullX(z, Math.min(Math.max(y, k + 0.01), z > BOW_Z ? beakTop(z) : sheerY(z))) - 0.05;
				if (x > 0.1) {
					probes.add(new double[] {x, y, z});
					probes.add(new double[] {-x, y, z});
				}
			}
		}
		probes.add(new double[] {0, BEAK_TIP_Y + 0.1, BEAK_TIP_Z - 0.1});
		// the transom's foot, the rudder hanging under the counter
		probes.add(new double[] {0, TRANSOM_FOOT[1], TRANSOM_FOOT[0]});
		probes.add(new double[] {0, RUDDER[1] + 0.1, RUDDER[0]});
		probes.add(new double[] {0, RUDDER[1] + 0.3, RUDDER[0] - RUDDER[2]});
		probes.add(new double[] {0, (RUDDER[1] + keelY(RUDDER[0] - RUDDER[2])) / 2, RUDDER[0] - RUDDER[2]});
		// the stern gallery round the house (its outer corners and the middle of its back)
		for (int side = -1; side <= 1; side += 2) {
			for (double z : new double[] {-9.0, -14.0, STERN_Z + 0.9}) {
				probes.add(new double[] {side * (hullX(z, QUARTERDECK_Y) + GALLERY_OUT), QUARTERDECK_Y + GALLERY_RAIL_H, z});
			}
			probes.add(new double[] {side * (hullX(STERN_Z + 0.9, QUARTERDECK_Y) + GALLERY_OUT - 0.9), QUARTERDECK_Y + 0.5, STERN_Z - GALLERY_AFT});
		}
		probes.add(new double[] {0, QUARTERDECK_Y + 0.5, STERN_Z - GALLERY_AFT});
		// the stern house: its walls' top corners, the roof's eaves (corners and middles), its tiers and its ridge
		for (double z : new double[] {HOUSE_FRONT_Z, (HOUSE_FRONT_Z + STERN_Z) / 2, STERN_Z + 0.05}) {
			double w = hullX(z, QUARTERDECK_Y - 0.1);
			probes.add(new double[] {w, EAVE_Y, z});
			probes.add(new double[] {-w, EAVE_Y, z});
		}
		for (double z : new double[] {PORCH_FRONT_Z - 0.2, ROOF_FRONT_Z, -11.0, -13.0, -17.0, ROOF_BACK_Z + 0.2}) {
			probes.add(new double[] {ROOF_HW + 0.3, EAVE_Y + 0.2, z});
			probes.add(new double[] {-ROOF_HW - 0.3, EAVE_Y + 0.2, z});
		}
		for (double d : ROOF_EDGES) {
			if (d <= 0) {
				continue;
			}
			for (double z : new double[] {roofFrontZ(d), -12.0, ROOF_BACK_Z + d}) {
				probes.add(new double[] {ROOF_HW - d, roofTop(d) + 0.2, z});
				probes.add(new double[] {-(ROOF_HW - d), roofTop(d) + 0.2, z});
			}
		}
		for (double z = roofFrontZ(ROOF_HW); z >= ROOF_BACK_Z + ROOF_HW - 1e-6; z -= 2.2) {
			probes.add(new double[] {0, ridgeTop() + 1.0, z});
		}
		probes.add(new double[] {0, ridgeTop() + 1.0, ROOF_BACK_Z + ROOF_HW});
		// the spire on the ridge's back end, the upturned corners of the lowest eaves (their knobbed corner posts)
		probes.add(new double[] {0, ridgeTop() + 2.6, ROOF_BACK_Z + ROOF_HW});
		for (int side = -1; side <= 1; side += 2) {
			probes.add(new double[] {side * (ROOF_HW + 0.4), EAVE_Y + 1.4, ROOF_BACK_Z - 0.3});
			probes.add(new double[] {side * (ROOF_HW + 0.4), EAVE_Y + 1.2, ROOF_FRONT_Z + 0.3});
		}
		probes.add(new double[] {0, PORCH_RIDGE_Y + 1.0, PORCH_FRONT_Z - 0.3});
		probes.add(new double[] {0, 0.0, ROOF_BACK_Z});
		probes.add(STERN_POLE[1].clone());
		// the companion house's lean-to roof (its high edge inboard)
		for (double z : MID_Z) {
			probes.add(new double[] {0.3, MID_HIGH_Y + 0.4, z});
			probes.add(new double[] {hullX(1.0, 0.5) + 0.6, MID_EAVE_Y, z});
		}
		// the mast, the yard, the sail (corners, middle of each edge, the middle), the booms, the bowsprit, the bow sail
		for (double y = 2.0; y <= MAST_HEAD_Y + 0.6; y += 2.5) {
			probes.add(mastPoint(y));
		}
		probes.add(mastPoint(MAST_HEAD_Y + 0.8));
		probes.add(YARD[0].clone());
		probes.add(YARD[1].clone());
		for (int side = -1; side <= 1; side += 2) {
			for (double[] st : new double[][] {{1, 1}, {1, 0}, {0.5, 1}, {0.5, 0}, {0.5, 0.5}, {0.75, 0.75}, {1, 0.5}, {0.25, 0.5}}) {
				probes.add(sailPoint(side, st[0], st[1]));
			}
			probes.add(new double[] {side * CLEW_BOOM_END[0], CLEW_BOOM_END[1], CLEW_BOOM_END[2]});
		}
		probes.add(FORE_BOOM[1].clone());
		probes.add(BOWSPRIT[1].clone());
		probes.add(new double[] {0, BOW_YARD[1][1] - BOW_SAIL_DROP, BOW_YARD[1][2] - 0.4});
		probes.add(new double[] {0, BOW_YARD[0][1] - BOW_SAIL_DROP, BOW_YARD[0][2] + 0.6});
		// the anchor hanging on its chain, the foot of the outside stair
		probes.add(new double[] {ANCHOR[0] + 0.5, ANCHOR_BOTTOM_Y + 0.05, ANCHOR[1]});
		probes.add(new double[] {ANCHOR[0] + 0.5, (ANCHOR_TOP_Y + ANCHOR_BOTTOM_Y) / 2, ANCHOR[1] + 1.0});
		probes.add(new double[] {ANCHOR[0] + 0.5, (ANCHOR_TOP_Y + ANCHOR_BOTTOM_Y) / 2, ANCHOR[1] - 1.0});
		probes.add(new double[] {SIDE_STAIR[1][0] + 0.5, SIDE_STAIR[1][1], SIDE_STAIR[1][2]});
		return probes;
	}

	/**
	 * The vertical speed the junk keeps skimming the water: {@code gap} is the lowest height of its keel over the water under
	 * it (NaN without water), {@code vy} the speed the flight would keep, {@code accelPerTick} the speed it gains in a tick.
	 * Within the hover height it holds its altitude (cancelling a descent order), pushed lower it rises gently; higher, or
	 * climbing, it is left alone.
	 */
	public static double skimVy(double gap, double vy, double accelPerTick) {
		if (Double.isNaN(gap) || gap >= WATER_HOVER + 0.05) {
			return vy;
		}
		if (gap < WATER_HOVER - 0.3) {
			return Math.max(vy, 0.6);
		}
		return vy <= accelPerTick ? accelPerTick : vy;
	}

	/**
	 * Between the slow, majestic Crystal Airship and the agile Rustic Skiff: it gathers way and turns at a moderate pace,
	 * changes altitude progressively, and its autopilot may hover low over the water or the ground.
	 */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.4;
		c.normalSpeed = 5.0;
		c.fastSpeed = 7.8;
		c.reverseSpeed = 1.6;
		c.acceleration = 0.55;
		c.braking = 0.9;
		c.waterDrag = 0.2;
		c.maxTurnRate = 11.0;
		c.minTurnFactor = 0.55;
		c.helmRate = 1.2;
		c.helmReturnRate = 1.1;
		c.turnResponse = 0.9;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 0.6;
		c.aiWaypointRadius = 10.0;
		c.aiStopRadius = 3.0;
		c.aiLookahead = 26.0;
		c.aiProbeDistance = 60.0;
		c.aiStuckSeconds = 10;
		c.aiTurnAroundSpeed = 0.8;
		c.furlSailWhenStopped = false;
		FlightConfig f = new FlightConfig();
		f.climbSpeed = 1.7;
		f.descendSpeed = 1.45;
		f.verticalAcceleration = 0.9;
		f.aiClearance = 5.0;
		f.aiApproachDistance = 32.0;
		f.aiLandingClearance = 0.6;
		f.sway = 0.75;
		c.flight = f;
		return c;
	}
}
