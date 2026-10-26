package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Crystal Airship ({@code crystal_airship}, "Le Grand Dirigeable de Cristal"): a huge and luxurious steampunk airship,
 * a cluster of seven cream balloon lobes (a big central egg, a fore and an aft lobe on the axis, four side lobes at the
 * corners) over the big golden ring and a 49 block hull of brown wood and dark green planks, a three-storey stern castle
 * with the cockpit, engine nacelles on its aft sides, a round stern engine, propeller pods and glowing blue crystals.
 * It flies like the steampunk airship and the Sky Leviathan ({@link Flight}), slower and heavier; its rooms are described
 * by an interior grid (tools/crystal_interior.py): players walk on its decks and in its rooms (cockpit, officers' mess,
 * lounge, storeroom, hold, engine room) while it flies.
 *
 * <p>Ship-local blocks, shared with tools/crystal_shape.py (same numbers, same formulas; checked by CrystalTest):
 * x = lateral (+x = port), y = up (0 = the main deck), z = forward (+z = bow).
 */
public final class CrystalLayout {
	// ---- balloon lobes: centre x, y, z, half width, half height, half length, a, b (sections scaled by (1 - |t|^a)^b)
	public static final double CY = 16.2;
	public static final String[] LOBE_NAMES = {"c", "f", "r", "fp", "fs", "rp", "rs"};
	static final double[][] LOBES = {
			{0.0, CY, -0.3, 7.6, 6.6, 15.8, 2.2, 0.5},
			{0.0, CY + 3.3, 14.6, 4.0, 3.55, 6.6, 2.2, 0.5},
			{0.0, CY + 3.6, -12.0, 4.8, 4.3, 8.6, 2.2, 0.5},
			{5.9, CY + 1.1, 9.6, 4.0, 4.2, 5.4, 2.2, 0.5},
			{-5.9, CY + 1.1, 9.6, 4.0, 4.2, 5.4, 2.2, 0.5},
			{5.9, CY + 1.1, -9.8, 4.1, 4.3, 6.0, 2.2, 0.5},
			{-5.9, CY + 1.1, -9.8, 4.1, 4.3, 6.0, 2.2, 0.5}};
	public static final double MAST_Z = -0.3;
	public static final double MAST_BASE = CY + 6.6;
	public static final double MAST_TOP = 27.4;

	// ---- the golden ring over the main deck
	public static final double RING_Y = 5.5;
	public static final double RING_Z = -0.3;
	public static final double RING_R = 4.1;

	// ---- hull
	public static final double MAIN_DECK_Y = 0.0;
	public static final double HULL_HW = 6.0;
	public static final double BOW_Z = 25.6;
	public static final double STERN_Z = -23.0;
	private static final double[] BOW_PLAN = {26.6, 2.0, 0.6};
	private static final double[] STERN_PLAN = {40.0, 2.5, 0.5};
	public static final double SHEER_WAIST = 1.0;
	private static final double SECTION_P = 2.6;
	private static final double TUMBLE = 0.02;
	private static final double[][] KEEL_PTS = {{-23.0, -4.4}, {-21.5, -5.8}, {-19.2, -7.0}, {-15.3, -8.9}, {-10.0, -9.9}, {-5.0, -9.6},
			{0.0, -9.0}, {5.1, -7.9}, {11.6, -6.4}, {15.9, -5.6}, {19.2, -4.5}, {22.3, -2.6}, {24.3, -1.0}, {25.4, 0.4}, {26.1, 1.6}};
	private static final double[] KEEL_SLOPES = keelSlopes();
	public static final double BEAK_TIP_Z = 28.0;
	public static final double FORECASTLE_Y = 2.0;
	public static final double FORECASTLE_Z = 13.3;
	public static final double RAIL_H = 1.0;

	// ---- stern castle
	public static final double CASTLE_Z = -10.1;
	public static final double L1_TOP = 3.0;
	public static final double L2_Z = -14.0;
	public static final double L2_Y = 3.0;
	public static final double L2_TOP = 5.8;
	public static final double ROOF_Z0 = -23.8;
	public static final double ROOF_Z1 = -14.4;
	public static final double ROOF_TOP = 7.6;
	private static final double CASTLE_FLARE = 0.25;
	public static final double HELM_Z = -15.9;
	public static final double PILOT_Z = -16.8;

	// ---- the rooms' levels
	public static final double LOUNGE_Y = -4.0;
	public static final double HOLD_Y = -7.5;
	public static final double ENGINE_FLOOR_Y = -7.5;

	// ---- engines and crystals
	/** Side nacelles: x (both sides), y, z0, z1, radius of the drum. */
	public static final double[] NACELLE = {8.4, -2.3, -23.6, -9.2, 3.6};
	private static final double[] NACELLE_NOSE = {2.5, -14.6, -15.8};
	public static final double NACELLE_EYE_Z = -18.7;
	/** Stern engine: y, z of its face, z of its rim, radius. */
	public static final double[] REAR_ENGINE = {-3.6, -23.0, -25.2, 3.6};
	/** Propeller pods under the stern: x (both sides), root (y, z), hub (y, z), blade length. */
	public static final double[] PROP_PODS = {7.0, -6.6, -5.0, -10.0, -10.4, 4.2};
	/** The crystal platform under the keel: z, platform y, radius, tip y. */
	public static final double[] BOTTOM_CRYSTAL = {0.3, -12.0, 3.1, -15.0};
	public static final double[] FRONT_POD = {0.0, 9.6, 24.6};
	public static final double[] REAR_POD = {0.0, 14.8, -24.6};
	public static final double POD_R = 2.0;
	/** The crystal engine in the engine room (x, z): its glow and its sounds. */
	public static final double ENGINE_X = 0.0;
	public static final double ENGINE_Z = -16.6;

	// ---- interior
	public static final String GRID = "/assets/medievalships/interiors/crystal_airship.grid";
	public static final String DECOR = "/assets/medievalships/interiors/crystal_airship_decor.json";
	/** Doors of the interior grid (tools/crystal_interior.py DOORS). */
	public static final int CASTLE_DOOR = 0;
	public static final int ENGINE_DOOR = 1;
	public static final int STORE_DOOR = 2;
	public static final int HOLD_HATCH = 3;

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

	public static double hullHalfWidth(double z) {
		if (z > BOW_Z + 0.75 || z < STERN_Z) {
			return 0.0;
		}
		double[] p = z >= 0 ? BOW_PLAN : STERN_PLAN;
		double t = Math.abs(z) / p[0];
		if (t >= 1.0) {
			return 0.0;
		}
		return HULL_HW * Math.pow(1.0 - Math.pow(t, p[1]), p[2]);
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

	/** Top of the hull planking: the waist bulwark, the forecastle's bulwark. */
	public static double sheerY(double z) {
		return SHEER_WAIST + (FORECASTLE_Y + RAIL_H - SHEER_WAIST) * smooth((z - (FORECASTLE_Z - 0.6)) / 0.9);
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

	/** Half width of the outside of the stern castle's walls. */
	public static double castleX(double z) {
		return hullX(z, SHEER_WAIST) + CASTLE_FLARE;
	}

	/** Top of the castle's walls at z (0 where there is no castle). */
	public static double castleTop(double z) {
		if (z > CASTLE_Z || z < STERN_Z) {
			return 0.0;
		}
		return z > L2_Z ? L1_TOP : L2_TOP;
	}

	/** Radius of a side nacelle at z. */
	public static double nacelleR(double z) {
		double z0 = NACELLE[2], z1 = NACELLE[3], r = NACELLE[4];
		double rn = NACELLE_NOSE[0], zb = NACELLE_NOSE[1], zd = NACELLE_NOSE[2];
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
		if (z > z0 + 1.6) {
			return r - 0.6 * smooth((z0 + 2.6 - z) / 1.0);
		}
		return r * 0.62;
	}

	/** Lowest point: the tip of the crystal under the keel. */
	public static double lowestY() {
		return BOTTOM_CRYSTAL[3] - 0.1;
	}

	/** Farthest point aft: the floating crystal pod behind the aft lobe. */
	public static double tailEndZ() {
		return REAR_POD[2] - 0.6;
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
		spec.boundingRadius = Math.hypot(BEAK_TIP_Z + 0.5, NACELLE[0] + NACELLE[4]) + 1.0;
		spec.aiReach = BEAK_TIP_Z + 0.5;
		spec.aiBack = -tailEndZ();
		spec.aiHalfWidth = NACELLE[0] + NACELLE[4] + 0.6;
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
	 * Terrain probes over the whole volume: rings round every balloon lobe, the mast, the ring, the hull's sections, the
	 * castle and its roof, the nacelles, the stern engine, the propeller pods and their blades, the crystals and pods.
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
			double top = sheerY(z) + (deckY(z) > MAIN_DECK_Y ? 0.0 : 0.0);
			for (double y : new double[] {k + 1.0, (k + SHEER_WAIST) / 2, SHEER_WAIST - 0.1, top - 0.1}) {
				double x = hullX(z, Math.min(y, top)) - 0.05;
				if (x > 0.1) {
					probes.add(new double[] {x, y, z});
					probes.add(new double[] {-x, y, z});
				}
			}
		}
		probes.add(new double[] {0, 0.75, BEAK_TIP_Z});
		// the castle and its roof
		for (double z = STERN_Z + 0.2; z <= CASTLE_Z - 0.2 + 1e-6; z += 2.0) {
			double x = castleX(z) - 0.05;
			double top = castleTop(z);
			probes.add(new double[] {x, top - 0.1, z});
			probes.add(new double[] {-x, top - 0.1, z});
		}
		for (double z : new double[] {ROOF_Z0 + 0.2, ROOF_Z1 - 0.2}) {
			for (double x : new double[] {-castleX(-19.0) - 0.4, 0.0, castleX(-19.0) + 0.4}) {
				probes.add(new double[] {x, L2_TOP + 0.1, z});
			}
			probes.add(new double[] {0, ROOF_TOP, z + (z < -19 ? 1.6 : -1.6)});
		}
		for (double x : new double[] {-2.6, 2.6}) {
			probes.add(new double[] {x, ROOF_TOP + 2.8, ROOF_Z1 - 2.2});
		}
		// the nacelles
		for (double side : new double[] {-1, 1}) {
			for (double z = NACELLE[2] + 0.2; z <= NACELLE[3] + 1.2 + 1e-6; z += 1.5) {
				double r = Math.max(0.3, nacelleR(Math.min(z, NACELLE[3] - 0.05)));
				for (int a = 0; a < 8; a++) {
					double t = Math.toRadians(45 * a);
					probes.add(new double[] {side * (NACELLE[0] + Math.sin(t) * r), NACELLE[1] + Math.cos(t) * r, z});
				}
			}
		}
		// the stern engine
		for (int a = 0; a < 8; a++) {
			double t = Math.toRadians(45 * a);
			probes.add(new double[] {Math.sin(t) * REAR_ENGINE[3], REAR_ENGINE[0] + Math.cos(t) * REAR_ENGINE[3], REAR_ENGINE[2] + 0.2});
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
		for (double[] pod : new double[][] {FRONT_POD, REAR_POD}) {
			double r = POD_R * 1.25;
			probes.add(new double[] {pod[0], pod[1] + r, pod[2]});
			probes.add(new double[] {pod[0], pod[1] - r, pod[2]});
			probes.add(new double[] {pod[0] + r, pod[1], pod[2]});
			probes.add(new double[] {pod[0] - r, pod[1], pod[2]});
			probes.add(new double[] {pod[0], pod[1], pod[2] + (pod[2] > 0 ? 1.8 : -1.8)});
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
