package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Crystal Airship ({@code crystal_airship}, "Le Grand Dirigeable de Cristal"): a huge and luxurious steampunk airship,
 * a cluster of seven cream balloon lobes (a big central egg, a fore and an aft lobe on the axis, four side lobes at the
 * corners) low over the big golden ring, a 49 block hull of brown wood and dark green planks (a banana keel, a sheer
 * sweeping up to a tall stem, a rounded stern with a brass gear medallion), a stern castle in tiers with the cockpit,
 * ornate brass engines on its aft sides, propeller pods and glowing blue crystals.
 * It flies like the steampunk airship and the Sky Leviathan ({@link Flight}), slower and heavier; its rooms are described
 * by an interior grid (tools/crystal_interior.py): players walk on its decks and in its rooms (cockpit, officers' mess,
 * lounge, storeroom, hold, engine room) while it flies.
 *
 * <p>Ship-local blocks, shared with tools/crystal_shape.py (same numbers, same formulas; checked by CrystalTest):
 * x = lateral (+x = port), y = up (0 = the main deck), z = forward (+z = bow).
 */
public final class CrystalLayout {
	// ---- balloon lobes: centre x, y, z, half width, half height, half length, a, b (sections scaled by (1 - |t|^a)^b)
	public static final double CY = 14.0;
	public static final String[] LOBE_NAMES = {"c", "f", "r", "fp", "fs", "rp", "rs"};
	static final double[][] LOBES = {
			{0.0, CY, -0.3, 7.6, 6.9, 15.8, 2.4, 0.5},
			{0.0, CY + 2.9, 14.6, 4.2, 3.4, 6.6, 2.8, 0.5},
			{0.0, CY + 2.5, -12.0, 4.9, 4.4, 8.6, 2.8, 0.5},
			{6.4, CY + 1.0, 9.6, 4.2, 4.3, 5.4, 2.8, 0.5},
			{-6.4, CY + 1.0, 9.6, 4.2, 4.3, 5.4, 2.8, 0.5},
			{6.4, CY + 1.0, -9.8, 4.3, 4.4, 6.0, 2.8, 0.5},
			{-6.4, CY + 1.0, -9.8, 4.3, 4.4, 6.0, 2.8, 0.5}};
	public static final double MAST_Z = -0.3;
	public static final double MAST_BASE = CY + 6.9;
	public static final double MAST_TOP = MAST_BASE + 4.6;

	// ---- the golden ring over the main deck
	public static final double RING_Y = 5.4;
	public static final double RING_Z = -0.3;
	public static final double RING_R = 4.1;

	// ---- hull
	public static final double MAIN_DECK_Y = 0.0;
	public static final double HULL_HW = 6.0;
	public static final double BOW_Z = 25.6;
	public static final double STERN_Z = -23.0;
	private static final double[] BOW_PLAN = {26.6, 2.0, 0.6};
	private static final double[] STERN_PLAN = {40.0, 2.5, 0.5};
	/** The stern rounds off in plan from this z to STERN_Z (a superellipse of this exponent). */
	private static final double[] STERN_ROUND = {-18.6, 2.5};
	public static final double SHEER_WAIST = 1.0;
	/** The sheer sweeps up to the forecastle between these z by this much, and on up to the stem by SHEER_BOW. */
	private static final double[] SHEER_FWD = {8.5, 14.0, 1.45};
	private static final double SHEER_BOW = 0.85;
	private static final double SHEER_AFT = 0.0;
	private static final double SECTION_P = 1.6;
	private static final double TUMBLE = 0.02;
	private static final double[][] KEEL_PTS = {{-23.0, -6.2}, {-21.5, -7.2}, {-19.5, -7.85}, {-16.0, -8.35}, {-12.0, -8.7}, {-7.0, -9.05},
			{-2.0, -9.3}, {3.0, -9.4}, {8.0, -8.9}, {13.0, -7.8}, {17.0, -6.2}, {20.5, -4.2}, {23.0, -2.0}, {24.8, 0.2}, {25.8, 2.0}, {26.3, 3.4}};
	private static final double[] KEEL_SLOPES = keelSlopes();
	/** The bowsprit's tip (with its gilded cap). */
	public static final double BEAK_TIP_Z = 28.8;
	public static final double FORECASTLE_Y = 2.0;
	public static final double FORECASTLE_Z = 13.3;
	public static final double RAIL_H = 1.0;

	// ---- stern castle
	public static final double CASTLE_Z = -10.1;
	public static final double L1_TOP = 3.0;
	public static final double L2_Z = -14.0;
	public static final double L2_Y = 3.0;
	public static final double L2_TOP = 6.4;
	/** Storeys 1 and 2: inset of their walls from the hull's side. */
	private static final double[] CASTLE_INSET = {0.3, 0.45};
	/** Storey 1 rounds off in plan from this z to STERN1_END (a superellipse of this exponent). */
	private static final double[] CASTLE1_ROUND = {STERN_ROUND[0] + 0.15, 2.2};
	/** Storey 2 rounds off over this length before STERN2_Z (a superellipse of this exponent): a round stern. */
	private static final double[] CASTLE2_ROUND = {5.0, 2.1};
	/** Storey 2's round back is tucked in by up to this much more towards its stern (the tiers step). */
	private static final double CASTLE2_TUCK = 0.45;
	/** The stern of storey 1 (inside the hull's rounded stern) and of storey 2 (overhanging it). */
	public static final double STERN1_END = -22.75;
	public static final double STERN2_Z = -23.9;
	/**
	 * The green mansard roof over storey 2 (solid in the grid): its eave's overhang past the walls, its inset at the top, the
	 * height of the eave (the cornice) and of its flat top (railed, walkable).
	 */
	public static final double MANSARD_OVERHANG = 0.2;
	public static final double MANSARD_INSET = 1.0;
	public static final double MANSARD_EAVE = 5.85;
	public static final double MANSARD_TOP = 8.0;
	/** Top of the castle's roof and of the gilded scroll crest at its gable's top. */
	public static final double ROOF_TOP = MANSARD_TOP;
	public static final double CREST_Y = 9.5;
	private static final double DECK_SLAB = 0.5;
	public static final double HELM_Z = -15.9;
	public static final double PILOT_Z = -16.8;

	// ---- the rooms' levels
	public static final double LOUNGE_Y = -4.0;
	public static final double HOLD_Y = -7.5;
	public static final double ENGINE_FLOOR_Y = -7.5;

	// ---- engines and crystals
	/** Side engines: x (both sides), y, z0 (the end of the iron cap), z1 (the helmet's nose), radius of the drum. */
	public static final double[] NACELLE = {7.5, -2.3, -24.4, -9.6, 3.1};
	private static final double[] NACELLE_NOSE = {2.4, -13.6, -15.0};
	/** The taper's start, the small iron drum's start, its radius, the radius of its flat end (the grille). */
	private static final double[] NACELLE_TAIL = {-20.4, -23.0, 1.2, 0.75};
	public static final double NACELLE_EYE_Z = -18.0;
	/** The gear medallion on the stern, tucked under the stern gallery: y, z of its face, radius (its dark rim). */
	public static final double[] MEDALLION = {-2.5, -23.0, 2.25};
	/** Propeller pods under the stern: x (both sides), root (y, z), hub (y, z), blade length. */
	public static final double[] PROP_PODS = {7.0, -6.6, -5.0, -10.0, -10.4, 4.0};
	/** The crystal platform under the keel: z, platform y, radius, tip y. */
	public static final double[] BOTTOM_CRYSTAL = {0.3, -12.0, 3.1, -15.0};
	public static final double[] FRONT_POD = {0.0, 7.2, 24.4};
	public static final double[] REAR_POD = {0.0, 12.9, -25.4};
	public static final double POD_R = 2.0;
	/** The crystal engine in the engine room (x, z), as tools/crystal_interior.py ENGINE (the tests check it is solid). */
	public static final double ENGINE_X = 0.0;
	public static final double ENGINE_Z = -16.6;
	/** The ensign boom aft from storey 2's stern at the cornice's height: its tip (y, z), with its gilded scroll. */
	public static final double[] ENSIGN_TIP = {MANSARD_EAVE, STERN2_Z - 4.3 - 0.3};

	// ---- interior
	public static final String GRID = "/assets/medievalships/interiors/crystal_airship.grid";
	public static final String DECOR = "/assets/medievalships/interiors/crystal_airship_decor.json";
	/** Doors of the interior grid (tools/crystal_interior.py DOORS). */
	public static final int CASTLE_DOOR = 0;
	public static final int ENGINE_DOOR = 1;
	public static final int STORE_DOOR = 2;
	public static final int HOLD_HATCH = 3;
	public static final int TERRACE_DOOR = 4;

	private CrystalLayout() {
	}

	// ------------------------------------------------------------------ shape (as in crystal_shape.py)

	public static double lobeScale(int k, double z) {
		double[] lb = LOBES[k];
		double t = (z - lb[2]) / lb[5];
		if (Math.abs(t) >= 1.0) {
			return 0.0;
		}
		return Math.pow(1.0 - Math.pow(Math.abs(t), lb[6]), lb[7]);
	}

	/** Point of lobe k's surface at z and azimuth (degrees from the top, + towards port). */
	public static double[] lobePoint(int k, double z, double azimuthDeg) {
		double[] lb = LOBES[k];
		double s = lobeScale(k, z);
		double a = Math.toRadians(azimuthDeg);
		return new double[] {lb[0] + Math.sin(a) * lb[3] * s, lb[1] + Math.cos(a) * lb[4] * s, z};
	}

	public static boolean insideBalloon(double x, double y, double z) {
		for (int k = 0; k < LOBES.length; k++) {
			double s = lobeScale(k, z);
			double w = LOBES[k][3] * s, h = LOBES[k][4] * s;
			if (w > 0 && h > 0 && Math.pow((x - LOBES[k][0]) / w, 2) + Math.pow((y - LOBES[k][1]) / h, 2) <= 1.0) {
				return true;
			}
		}
		return false;
	}

	/** Half beam of the plan at z before the stern is rounded off. */
	public static double planHalfWidth(double z) {
		if (z > BOW_Z + 0.75) {
			return 0.0;
		}
		double[] p = z >= 0 ? BOW_PLAN : STERN_PLAN;
		double t = Math.abs(z) / p[0];
		if (t >= 1.0) {
			return 0.0;
		}
		return HULL_HW * Math.pow(1.0 - Math.pow(t, p[1]), p[2]);
	}

	/** Factor rounding a plan off between z0 and its end zEnd (a superellipse quarter of exponent p). */
	static double sternRound(double z, double zEnd, double z0, double p) {
		if (z >= z0) {
			return 1.0;
		}
		if (z <= zEnd) {
			return 0.0;
		}
		double u = (z0 - z) / (z0 - zEnd);
		return Math.pow(1.0 - Math.pow(u, p), 1.0 / p);
	}

	/** Half beam of the plan at z (at the bulwark): a rounded stern. */
	public static double hullHalfWidth(double z) {
		if (z < STERN_Z) {
			return 0.0;
		}
		return planHalfWidth(z) * sternRound(z, STERN_Z, STERN_ROUND[0], STERN_ROUND[1]);
	}

	private static double[] keelSlopes() {
		double[][] p = KEEL_PTS;
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

	/** Bottom of the hull at z (monotone cubic through the keel line of the reference); beyond the stem's head: none. */
	public static double keelY(double z) {
		double[][] p = KEEL_PTS;
		if (z <= p[0][0]) {
			return p[0][1];
		}
		if (z >= p[p.length - 1][0]) {
			return 99.0;
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

	public static double deckY(double z) {
		return z >= FORECASTLE_Z ? FORECASTLE_Y : MAIN_DECK_Y;
	}

	private static double smooth(double t) {
		t = Math.max(0.0, Math.min(1.0, t));
		return t * t * (3 - 2 * t);
	}

	/** Top of the hull planking: a sheer sweeping up from the waist to the forecastle and on to the stem. */
	public static double sheerY(double z) {
		double y = SHEER_WAIST + SHEER_FWD[2] * smooth((z - SHEER_FWD[0]) / (SHEER_FWD[1] - SHEER_FWD[0]));
		if (z > SHEER_FWD[1]) {
			y += SHEER_BOW * Math.pow(Math.min(1.0, (z - SHEER_FWD[1]) / (BOW_Z - SHEER_FWD[1])), 1.4);
		}
		if (z < -3.0) {
			y += SHEER_AFT * smooth((-3.0 - z) / 7.0);
		}
		return y;
	}

	/** Half width of the outside of the hull at (z, y). */
	public static double hullX(double z, double y) {
		double w = hullHalfWidth(z);
		if (w <= 0) {
			return 0.0;
		}
		double k = keelY(z);
		if (y < k) {
			return 0.0;
		}
		if (y <= SHEER_WAIST) {
			double eta = (y - k) / Math.max(0.05, SHEER_WAIST - k);
			return w * (0.1 + 0.9 * Math.pow(1.0 - Math.pow(1.0 - eta, SECTION_P), 0.5));
		}
		return w * (1.0 - TUMBLE * (y - SHEER_WAIST));
	}

	/** Half width of the outside of storey 1's walls: the hull's plan, inset, rounded at the stern. */
	public static double castle1X(double z) {
		if (z > CASTLE_Z || z < STERN_Z) {
			return 0.0;
		}
		return Math.max(0.0, (planHalfWidth(z) - CASTLE_INSET[0]) * sternRound(z, STERN1_END, CASTLE1_ROUND[0], CASTLE1_ROUND[1]));
	}

	/** Half width of the outside of storey 2's walls: nearly as wide as storey 1, round at the stern (tucked in a little), overhanging it. */
	public static double castle2X(double z) {
		if (z > L2_Z || z < STERN2_Z) {
			return 0.0;
		}
		double tuck = CASTLE2_TUCK * smooth((STERN2_Z + CASTLE2_ROUND[0] - z) / CASTLE2_ROUND[0]);
		return Math.max(0.0, (planHalfWidth(z) - CASTLE_INSET[1] - tuck) * sternRound(z, STERN2_Z, STERN2_Z + CASTLE2_ROUND[0], CASTLE2_ROUND[1]));
	}

	/** Half width of the outside of the stern castle's walls at z and height y (storey 1, its floor slab, storey 2). */
	public static double castleX(double z, double y) {
		if (y < L1_TOP - DECK_SLAB) {
			return castle1X(z);
		}
		if (y < L1_TOP) {
			return Math.max(castle1X(z), castle2X(z));
		}
		return castle2X(z);
	}

	/** Top of the castle's walls at z (0 where there is no castle). */
	public static double castleTop(double z) {
		if (z > CASTLE_Z || z < STERN2_Z) {
			return 0.0;
		}
		return z > L2_Z ? L1_TOP : L2_TOP;
	}

	/** Radius of a side engine at z: a brass helmet, its neck, the drum round the eye, a taper, a small iron drum narrowing to its flat end. */
	public static double nacelleR(double z) {
		double z0 = NACELLE[2], z1 = NACELLE[3], r = NACELLE[4];
		double rn = NACELLE_NOSE[0], zb = NACELLE_NOSE[1], zd = NACELLE_NOSE[2];
		double za = NACELLE_TAIL[0], zc = NACELLE_TAIL[1], rc = NACELLE_TAIL[2], re = NACELLE_TAIL[3];
		if (z > z1 || z < z0) {
			return 0.0;
		}
		if (z > z1 - rn) {
			double t = (z - (z1 - rn)) / rn;
			return rn * Math.sqrt(Math.max(0.0, 1.0 - t * t));
		}
		if (z > zb) {
			return rn;
		}
		if (z > zd) {
			return rn + (r - rn) * smooth((zb - z) / (zb - zd));
		}
		if (z > za) {
			return r;
		}
		if (z > zc) {
			return r - (r - rc) * smooth((za - z) / (za - zc));
		}
		double t = (zc - z) / (zc - z0);
		return rc + (re - rc) * Math.pow(t, 1.5);
	}

	/** Lowest point: the tip of the crystal under the keel. */
	public static double lowestY() {
		return BOTTOM_CRYSTAL[3] - 0.1;
	}

	/** Farthest point aft: the ensign spar over the stern, or the crystal of the floating pod behind the aft lobe. */
	public static double tailEndZ() {
		return Math.min(ENSIGN_TIP[1], REAR_POD[2] - 0.35 - 1.05 * POD_R * 1.25);
	}

	/** Half width of the whole airship: the engines with their wings and the bezels of their eyes. */
	public static double halfWidth() {
		return NACELLE[0] + NACELLE[4] + 1.0;
	}

	// ------------------------------------------------------------------ the ship type

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = BOW_Z;
		p.tip = BEAK_TIP_Z;
		p.maxHalfWidth = HULL_HW;
		p.foreScale = BOW_PLAN[0];
		p.forePowA = BOW_PLAN[1];
		p.forePowB = BOW_PLAN[2];
		p.aftScale = STERN_PLAN[0];
		p.aftPowA = STERN_PLAN[1];
		p.aftPowB = STERN_PLAN[2];
		// under the whole grid, so the collision query never cuts the hold or the engine room
		p.keelDepth = 10.5;
		p.keelRise = 0.0;
		p.keelPow = 2.0;
		p.railBase = SHEER_WAIST;
		p.railRiseFore = 0.0;
		p.railRiseAft = 0.0;
		p.waterlineY = 0.0;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = CASTLE_Z;
		p.deckMaxZ = FORECASTLE_Z;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		spec.flying = true;
		spec.hullProbes = false;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		double c = L2_Y;
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, c + 0.28, PILOT_Z, true, new double[] {0.9, c + 0.02, PILOT_Z - 0.6}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-1.0, c + 0.2, HELM_Z - 0.4, 1.0, c + 2.5, HELM_Z + 0.6);
		// not solid (the grid is): the ring's pillar keeps boarding spots off it, the mast gives the height
		spec.masts = List.of(new ShipGeometry.Mast(0.0, RING_Z, MAIN_DECK_Y, RING_Y + RING_R, 1.0),
				new ShipGeometry.Mast(0.0, MAST_Z, MAST_BASE, MAST_TOP, 0.2));
		spec.extraProbes = List.copyOf(probes());
		spec.boundingRadius = Math.hypot(Math.max(BEAK_TIP_Z, -tailEndZ()) + 0.5, halfWidth()) + 1.0;
		spec.aiReach = BEAK_TIP_Z + 0.5;
		spec.aiBack = -tailEndZ() + 0.3;
		spec.aiHalfWidth = halfWidth() + 0.3;
		spec.lowestY = lowestY();
		spec.boardMinZ = 1.5;
		spec.boardMaxZ = 8.5;
		spec.boardHalfWidth = 0.6;
		spec.avoidZ = new double[] {};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("crystal_airship", "Grand Dirigeable de Cristal", new ShipGeometry(hull, spec), CrystalLayout::config);
	}

	/**
	 * Terrain probes over the whole volume: rings round every balloon lobe and the crystal finials at the side lobes' ends,
	 * the mast, the ring, the hull's sections, the castle's tiers and its green mansard roof (eave, railed top, crest,
	 * pennant poles and flags, the quarter lanterns), the engines (their wings, fins and eyes), the stern medallion, the
	 * ensign boom, the propeller pods and their blades, the crystals and the floating pods.
	 */
	static List<double[]> probes() {
		List<double[]> probes = new ArrayList<>();
		for (int k = 0; k < LOBES.length; k++) {
			double[] lb = LOBES[k];
			for (double z = lb[2] - lb[5] + 0.6; z <= lb[2] + lb[5] - 0.6 + 1e-6; z += 2.4) {
				for (int a = 0; a < 12; a++) {
					double[] q = lobePoint(k, z, 30 * a);
					if (!insideBalloonOther(k, q[0], q[1], q[2])) {
						probes.add(q);
					}
				}
			}
			probes.add(new double[] {lb[0], lb[1], lb[2] + lb[5] - 0.1});
			probes.add(new double[] {lb[0], lb[1], lb[2] - lb[5] + 0.1});
		}
		// the crystal finials at the side lobes' outer ends (fore for fp/fs, aft for rp/rs)
		for (int k = 3; k < LOBES.length; k++) {
			double[] lb = LOBES[k];
			double end = k < 5 ? 1.0 : -1.0;
			probes.add(new double[] {lb[0], lb[1], lb[2] + end * (0.93 * lb[5] + 1.6)});
		}
		probes.add(new double[] {0, MAST_TOP + 0.5, MAST_Z});
		for (double x : new double[] {-1.7, 1.7}) {
			probes.add(new double[] {x, MAST_BASE + 1.0, MAST_Z});
		}
		// the ring
		for (int a = 0; a < 8; a++) {
			double t = Math.toRadians(45 * a);
			probes.add(new double[] {0, RING_Y + Math.cos(t) * RING_R, RING_Z + Math.sin(t) * RING_R});
		}
		// the hull's sections and the bulwarks, the beak
		for (double z = STERN_Z + 0.2; z <= 26.0 + 1e-6; z += 2.0) {
			double k = keelY(z);
			probes.add(new double[] {0, k + 0.1, z});
			double top = sheerY(z);
			for (double y : new double[] {k + 1.0, (k + SHEER_WAIST) / 2, SHEER_WAIST - 0.1, top - 0.1}) {
				double x = hullX(z, Math.min(y, top)) - 0.05;
				if (x > 0.1) {
					probes.add(new double[] {x, y, z});
					probes.add(new double[] {-x, y, z});
				}
			}
		}
		probes.add(new double[] {0, 1.3, BEAK_TIP_Z});
		probes.add(new double[] {0, 4.6, 26.0});   // the stem head
		// the castle's tiers: storey 1 round its rounded stern, storey 2 overhanging it, the green mansard roof (its eave and
		// its railed top), the lanterns on the quarter posts, the crest, the pennant poles and their flags, the ensign boom
		for (double z = STERN1_END + 0.15; z <= CASTLE_Z - 0.2 + 1e-6; z += 1.5) {
			double x = castle1X(z) - 0.05;
			probes.add(new double[] {x, L1_TOP - 0.1, z});
			probes.add(new double[] {-x, L1_TOP - 0.1, z});
		}
		for (double z = STERN2_Z + 0.1; z <= L2_Z - 0.2 + 1e-6; z += 1.5) {
			double x = castle2X(z);
			for (double sx : new double[] {-1, 1}) {
				probes.add(new double[] {sx * (x - 0.05), L1_TOP - 0.4, z});
				probes.add(new double[] {sx * (x + MANSARD_OVERHANG + 0.05), MANSARD_EAVE + 0.1, z});
				if (x - MANSARD_INSET > 0.2) {
					probes.add(new double[] {sx * (x - MANSARD_INSET), MANSARD_TOP + 0.4, z});
				}
			}
		}
		probes.add(new double[] {0, L1_TOP - 0.4, STERN2_Z + 0.05});
		probes.add(new double[] {0, MANSARD_EAVE + 0.1, STERN2_Z - MANSARD_OVERHANG});
		probes.add(new double[] {0, MANSARD_TOP + 0.4, STERN2_Z + MANSARD_INSET + 0.1});
		probes.add(new double[] {0, CREST_Y, L2_Z - 0.3});
		double qx = castle1X(CASTLE1_ROUND[0]) + 0.21;
		double px = castle2X(L2_Z - 1.4) - MANSARD_INSET - 0.25;
		for (double sx : new double[] {-1, 1}) {
			probes.add(new double[] {sx * qx, MANSARD_EAVE + 1.3, CASTLE1_ROUND[0]});        // the quarter lanterns
			probes.add(new double[] {sx * px, MANSARD_TOP + 3.1, L2_Z - 1.65});              // the pennant poles' tops
			probes.add(new double[] {sx * px, MANSARD_TOP + 2.6, L2_Z - 4.2});               // the pennants' tips
		}
		probes.add(new double[] {0, ENSIGN_TIP[0], ENSIGN_TIP[1] + 0.05});
		// the engines: rings of probes along them, the tips of their wings and fins, the bezels of their eyes, the tanks
		for (double side : new double[] {-1, 1}) {
			for (double z = NACELLE[2] + 0.05; z <= NACELLE[3] + 1.4 + 1e-6; z += 1.25) {
				double r = Math.max(0.3, nacelleR(Math.min(z, NACELLE[3] - 0.05)));
				for (int a = 0; a < 8; a++) {
					double t = Math.toRadians(45 * a);
					probes.add(new double[] {side * (NACELLE[0] + Math.sin(t) * r), NACELLE[1] + Math.cos(t) * r, z});
				}
			}
			double w = halfWidth() - 0.1;
			probes.add(new double[] {side * w, NACELLE[1] + 3.6, -14.9});            // the tips of the big wing
			probes.add(new double[] {side * (NACELLE[0] + 1.2), NACELLE[1] + 4.6, -14.6});  // the top wing
			probes.add(new double[] {side * (w - 0.6), NACELLE[1] + 2.6, -21.9});     // the elevator fin
			for (int a = 0; a < 4; a++) {
				double t = Math.toRadians(90 * a);
				probes.add(new double[] {side * (NACELLE[0] + NACELLE[4] + 0.3), NACELLE[1] + Math.cos(t) * 2.5, NACELLE_EYE_Z + Math.sin(t) * 2.5});
			}
			probes.add(new double[] {side * (NACELLE[0] + 1.0), NACELLE[1] - NACELLE[4] - 0.75, -16.8});   // the copper tanks
		}
		// the stern medallion
		for (int a = 0; a < 8; a++) {
			double t = Math.toRadians(45 * a);
			probes.add(new double[] {Math.sin(t) * (MEDALLION[2] + 0.3), MEDALLION[0] + Math.cos(t) * (MEDALLION[2] + 0.3), MEDALLION[1] - 0.5});
		}
		// the propeller pods and the reach of their blades
		for (double side : new double[] {-1, 1}) {
			double x = side * PROP_PODS[0];
			probes.add(new double[] {x, PROP_PODS[1], PROP_PODS[2]});
			probes.add(new double[] {x, PROP_PODS[3], PROP_PODS[4]});
			double r = PROP_PODS[5] * 0.85;
			for (double[] d : new double[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
				probes.add(new double[] {x + d[0] * r, PROP_PODS[3] - 1.4 + d[1] * r * 0.8, PROP_PODS[4] - 1.8});
			}
		}
		// the crystal platform and its crystal, the hanging crystals, the floating pods
		for (int a = 0; a < 8; a++) {
			double t = Math.toRadians(45 * a);
			probes.add(new double[] {Math.sin(t) * BOTTOM_CRYSTAL[2], BOTTOM_CRYSTAL[1], BOTTOM_CRYSTAL[0] + Math.cos(t) * BOTTOM_CRYSTAL[2]});
		}
		probes.add(new double[] {0, BOTTOM_CRYSTAL[3], BOTTOM_CRYSTAL[0]});
		probes.add(new double[] {0, -8.9 - 1.3, 10.0});
		for (double x : new double[] {-2.6, 2.6}) {
			probes.add(new double[] {x, -6.4 - 1.3, 19.3});
		}
		// the floating pods: their rings lie across the ship, their crystals point fore and aft
		for (double[] pod : new double[][] {FRONT_POD, REAR_POD}) {
			double r = POD_R * (pod == REAR_POD ? 1.25 : 1.0);
			probes.add(new double[] {pod[0], pod[1] + r, pod[2]});
			probes.add(new double[] {pod[0], pod[1] - 1.1 * r - 0.1, pod[2]});
			probes.add(new double[] {pod[0] + r, pod[1], pod[2]});
			probes.add(new double[] {pod[0] - r, pod[1], pod[2]});
			probes.add(new double[] {pod[0], pod[1], pod[2] + 0.35 + 1.05 * r});
			probes.add(new double[] {pod[0], pod[1], pod[2] - 0.35 - 1.05 * r});
		}
		return probes;
	}

	private static boolean insideBalloonOther(int skip, double x, double y, double z) {
		for (int k = 0; k < LOBES.length; k++) {
			if (k == skip) {
				continue;
			}
			double s = lobeScale(k, z);
			double w = LOBES[k][3] * s - 0.4, h = LOBES[k][4] * s - 0.4;
			if (w > 0 && h > 0 && Math.pow((x - LOBES[k][0]) / w, 2) + Math.pow((y - LOBES[k][1]) / h, 2) <= 1.0) {
				return true;
			}
		}
		return false;
	}

	/**
	 * The biggest and heaviest airship: very slow to gather way and to stop, the widest turns, slow and progressive changes
	 * of altitude (majestic), a high clearance over the ground for its autopilot.
	 */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.8;
		c.normalSpeed = 3.8;
		c.fastSpeed = 6.0;
		c.reverseSpeed = 1.0;
		c.acceleration = 0.22;
		c.braking = 0.45;
		c.waterDrag = 0.12;
		c.maxTurnRate = 5.0;
		c.minTurnFactor = 0.45;
		c.helmRate = 0.6;
		c.helmReturnRate = 0.7;
		c.turnResponse = 0.4;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 0.4;
		c.aiWaypointRadius = 18.0;
		c.aiStopRadius = 4.5;
		c.aiLookahead = 40.0;
		c.aiProbeDistance = 90.0;
		c.aiStuckSeconds = 14;
		c.aiTurnAroundSpeed = 0.45;
		c.furlSailWhenStopped = false;
		FlightConfig f = new FlightConfig();
		f.climbSpeed = 1.0;
		f.descendSpeed = 0.85;
		f.verticalAcceleration = 0.35;
		f.aiClearance = 9.0;
		f.aiApproachDistance = 52.0;
		f.aiLandingClearance = 2.0;
		f.sway = 0.5;
		c.flight = f;
		return c;
	}
}
