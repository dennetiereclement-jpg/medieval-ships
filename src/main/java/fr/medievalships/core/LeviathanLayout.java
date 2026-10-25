package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Sky Leviathan ({@code sky_leviathan}): a huge steampunk pirate airship, an egg-shaped balloon
 * 52 blocks long (65 with its spikes and fins) carrying a 36 block pirate ship on chains and ropes 8 blocks
 * under it. It flies like the steampunk airship ({@link Flight}); its rooms are described by an interior
 * grid (tools/leviathan_interior.py) like the Nautilus: players walk on its decks and in its rooms while it
 * flies, and climb a ladder in the central tower up through the balloon to the observation deck on top.
 *
 * <p>Ship-local blocks, shared with tools/leviathan_shape.py (same numbers, same formulas; checked by
 * LeviathanTest): x = lateral (+x = port), y = up (0 = the ship's main deck), z = forward (+z = bow).
 */
public final class LeviathanLayout {
	// ---- balloon
	public static final double BALLOON_Y = 17.8;
	public static final double BALLOON_Z = -0.6;
	public static final double BALLOON_FRONT = 26.0;
	public static final double BALLOON_REAR = 26.0;
	public static final double BALLOON_HW = 12.2;
	public static final double BALLOON_HH = 9.8;
	private static final double[] BALLOON_FORE = {2.6, 0.55};
	private static final double[] BALLOON_AFT = {2.4, 0.6};
	public static final double NOSE_Z = BALLOON_Z + BALLOON_FRONT;
	public static final double TAIL_Z = BALLOON_Z - BALLOON_REAR;
	public static final double NOSE_SPIKE_Z = 32.2;
	public static final double TAIL_SPIKE_Z = -33.2;
	public static final double TOP_DECK_Y = 28.0;
	public static final double TOP_DECK_Z0 = -14.0;
	public static final double TOP_DECK_Z1 = 10.0;
	public static final double TOP_DECK_HALF = 5.5;
	public static final double MAST_Z = 1.5;
	public static final double MAST_TOP = 36.8;

	// ---- the hanging ship
	public static final double MAIN_DECK_Y = 0.0;
	public static final double HULL_HW = 5.0;
	public static final double HULL_BOW_Z = 16.0;
	public static final double HULL_STERN_Z = -19.8;
	private static final double[] BOW_PLAN = {16.4, 2.4, 0.62};
	private static final double[] STERN_PLAN = {27.0, 2.6, 0.5};
	private static final double[][] KEEL_PTS = {{-19.8, -2.6}, {-18.5, -4.2}, {-17.0, -5.3}, {-15.5, -5.95}, {-10.0, -6.25}, {-4.0, -6.3},
			{2.0, -6.28}, {6.0, -6.1}, {9.0, -5.6}, {12.0, -4.5}, {14.3, -3.2}, {16.0, -1.5}};
	private static final double[] KEEL_SLOPES = keelSlopes();
	public static final double SHEER_WAIST = 1.0;
	public static final double TUMBLE = 0.025;
	public static final double FORECASTLE_Y = 3.0;
	public static final double FORECASTLE_Z = 9.0;
	public static final double QUARTERDECK_Y = 3.0;
	public static final double QUARTERDECK_Z = -7.5;
	public static final double POOP_Y = 5.5;
	public static final double POOP_Z = -15.0;
	public static final double LOWER_DECK_Y = -3.0;
	public static final double HOLD_Y = -5.5;
	public static final double BOWSPRIT_TIP_Z = 24.9;
	public static final double BOWSPRIT_TIP_Y = 5.3;
	/** The central tower (its ladder shaft climbs to the observation deck). */
	public static final double TOWER_X = 1.5;
	public static final double TOWER_Z0 = -3.0;
	public static final double TOWER_Z1 = 0.0;
	public static final double SHAFT_X = 1.0;
	public static final double SHAFT_Z0 = -2.5;
	public static final double SHAFT_Z1 = -0.5;
	public static final double HELM_Z = -10.75;
	public static final double PILOT_Z = -11.6;
	/** Boiler of the engine room (x, z), for its sounds and steam. */
	public static final double BOILER_X = 0.0;
	public static final double BOILER_Z = -14.2;

	// ---- fins: name, azimuth (deg from the top), z of the leading root, radial distance of the root (NaN: on
	// the balloon), span Lq, rake (deg); the chord is FIN_CHORD * Lq
	public static final double FIN_CHORD = 0.85;
	public static final double[] FIN_TIP = {0.92, 1.0};
	public static final String[] FIN_NAMES = {"fin_dorsal", "fin_upper_p", "fin_upper_s", "fin_side_p", "fin_side_s", "fin_lower"};
	private static final double[][] FINS = {
			{0.0, -15.6, Double.NaN, 5.9, 12.3},
			{30.0, -26.5, 1.6, 9.0, 4.6},
			{-30.0, -26.5, 1.6, 9.0, 4.6},
			{115.0, -26.5, 1.6, 10.0, 2.2},
			{-115.0, -26.5, 1.6, 10.0, 2.2},
			{180.0, -26.5, 1.6, 9.4, -12.0}};
	/** The ventral fin under the keel: z and y of its leading root, span, rake. */
	private static final double[] KEEL_FIN = {7.7, -5.9, 7.75, 16.9};

	// ---- interior
	public static final String GRID = "/assets/medievalships/interiors/sky_leviathan.grid";
	public static final String DECOR = "/assets/medievalships/interiors/sky_leviathan_decor.json";
	/** Doors of the interior grid (tools/leviathan_interior.py DOORS). */
	public static final int TOWER_DOOR = 0;
	public static final int TOP_HATCH = 1;
	public static final int CAPTAIN_DOOR = 2;
	public static final int ENGINE_UPPER_DOOR = 9;
	public static final int HOLD_HATCH = 11;

	private LeviathanLayout() {
	}

	// ------------------------------------------------------------------ shape (as in leviathan_shape.py)

	public static double balloonScale(double z) {
		double t = (z - BALLOON_Z) / (z >= BALLOON_Z ? BALLOON_FRONT : BALLOON_REAR);
		double[] ab = t >= 0 ? BALLOON_FORE : BALLOON_AFT;
		t = Math.abs(t);
		return t >= 1.0 ? 0.0 : Math.pow(1.0 - Math.pow(t, ab[0]), ab[1]);
	}

	public static double balloonHalfWidth(double z) {
		return BALLOON_HW * balloonScale(z);
	}

	public static double balloonHalfHeight(double z) {
		return BALLOON_HH * balloonScale(z);
	}

	/** Point of the balloon surface at z and azimuth (degrees from the top, + towards port). */
	public static double[] balloonPoint(double z, double azimuthDeg) {
		double a = Math.toRadians(azimuthDeg);
		return new double[] {Math.sin(a) * balloonHalfWidth(z), BALLOON_Y + Math.cos(a) * balloonHalfHeight(z), z};
	}

	public static double hullHalfWidth(double z) {
		double[] p = z >= 0 ? BOW_PLAN : STERN_PLAN;
		double t = Math.abs(z) / p[0];
		if (z > HULL_BOW_Z || z < HULL_STERN_Z || t >= 1.0) {
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

	/** Bottom of the hull at z (monotone cubic through the keel line of the reference). */
	public static double keelY(double z) {
		double[][] p = KEEL_PTS;
		if (z <= p[0][0]) {
			return p[0][1];
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

	public static double deckY(double z) {
		if (z >= FORECASTLE_Z) {
			return FORECASTLE_Y;
		}
		if (z <= POOP_Z) {
			return POOP_Y;
		}
		if (z <= QUARTERDECK_Z) {
			return QUARTERDECK_Y;
		}
		return MAIN_DECK_Y;
	}

	private static double smooth(double t) {
		t = Math.max(0.0, Math.min(1.0, t));
		return t * t * (3 - 2 * t);
	}

	/** Top of the hull planking (the waist bulwark, the castle decks, the walls under the poop). */
	public static double sheerY(double z) {
		double y = SHEER_WAIST;
		y += (FORECASTLE_Y - SHEER_WAIST) * smooth((z - (FORECASTLE_Z - 1.2)) / 1.2);
		y += (QUARTERDECK_Y - SHEER_WAIST) * smooth(((QUARTERDECK_Z + 1.2) - z) / 1.2);
		y += (POOP_Y - QUARTERDECK_Y) * smooth(((POOP_Z + 1.0) - z) / 1.0);
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
			double eta = (y - k) / (SHEER_WAIST - k);
			return w * (0.12 + 0.88 * Math.pow(1.0 - Math.pow(1.0 - eta, 3), 0.5));
		}
		return w * (1.0 - TUMBLE * (y - SHEER_WAIST));
	}

	/** A point of fin k (index in {@link #FIN_NAMES}) at (u, v) of its outline, or of the keel fin for k = -1. */
	public static double[] finPoint(int k, double u, double v) {
		double[] o, chord, span;
		double lq;
		if (k < 0) {
			double r = Math.toRadians(KEEL_FIN[3]);
			o = new double[] {0.0, KEEL_FIN[1], KEEL_FIN[0]};
			span = new double[] {0.0, -Math.cos(r), -Math.sin(r)};
			chord = new double[] {0.0, Math.sin(r), -Math.cos(r)};
			lq = KEEL_FIN[2];
		} else {
			double[] f = FINS[k];
			double a = Math.toRadians(f[0]);
			double[] rad = {Math.sin(a), Math.cos(a), 0.0};
			if (Double.isNaN(f[2])) {
				o = balloonPointOut(f[1], f[0], -0.15);
			} else {
				o = new double[] {rad[0] * f[2], BALLOON_Y + rad[1] * f[2], f[1]};
			}
			double r = Math.toRadians(f[4]);
			double[] back = {0.0, 0.0, -1.0};
			span = new double[3];
			chord = new double[3];
			for (int i = 0; i < 3; i++) {
				span[i] = Math.cos(r) * rad[i] + Math.sin(r) * back[i];
				chord[i] = Math.cos(r) * back[i] - Math.sin(r) * rad[i];
			}
			lq = f[3];
		}
		double lp = FIN_CHORD * lq;
		return new double[] {o[0] + chord[0] * u * lp + span[0] * v * lq, o[1] + chord[1] * u * lp + span[1] * v * lq,
				o[2] + chord[2] * u * lp + span[2] * v * lq};
	}

	/** Balloon point pushed out along the normal of the section (as balloon_point(z, az, out) in Python). */
	static double[] balloonPointOut(double z, double azDeg, double out) {
		double a = Math.toRadians(azDeg);
		double w = balloonHalfWidth(z), h = balloonHalfHeight(z);
		double x = Math.sin(a) * w, y = Math.cos(a) * h;
		double nx = x / Math.pow(Math.max(w, 1e-6), 2), ny = y / Math.pow(Math.max(h, 1e-6), 2);
		double n = Math.hypot(nx, ny);
		if (n > 1e-9) {
			x += nx / n * out;
			y += ny / n * out;
		}
		return new double[] {x, BALLOON_Y + y, z};
	}

	/** Lowest point: the tip of the ventral fin. */
	public static double lowestY() {
		return finPoint(-1, FIN_TIP[0], FIN_TIP[1])[1] - 0.1;
	}

	/** Farthest point aft: the tip of a side fin. */
	public static double tailEndZ() {
		double z = TAIL_SPIKE_Z;
		for (int k = 0; k < FINS.length; k++) {
			z = Math.min(z, finPoint(k, FIN_TIP[0], FIN_TIP[1])[2]);
		}
		return z;
	}

	// ------------------------------------------------------------------ the ship type

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HULL_BOW_Z;
		p.tip = NOSE_SPIKE_Z;
		p.maxHalfWidth = HULL_HW;
		p.foreScale = BOW_PLAN[0];
		p.forePowA = BOW_PLAN[1];
		p.forePowB = BOW_PLAN[2];
		p.aftScale = STERN_PLAN[0];
		p.aftPowA = STERN_PLAN[1];
		p.aftPowB = STERN_PLAN[2];
		// keelY(0) under the whole grid, so the collision query never cuts the hold
		p.keelDepth = 7.5;
		p.keelRise = 0.0;
		p.keelPow = 2.0;
		p.railBase = SHEER_WAIST;
		p.railRiseFore = 0.0;
		p.railRiseAft = 0.0;
		p.waterlineY = 0.0;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = QUARTERDECK_Z;
		p.deckMaxZ = FORECASTLE_Z;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		spec.flying = true;
		spec.hullProbes = false;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		double qd = QUARTERDECK_Y;
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, qd + 0.28, PILOT_Z, true, new double[] {1.3, qd + 0.02, PILOT_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, qd + 0.5, HELM_Z - 0.6, 0.8, qd + 2.0, HELM_Z + 0.3);
		// not solid (the grid is): the tower keeps boarding spots off it, the flag mast gives the height
		spec.masts = List.of(new ShipGeometry.Mast(0.0, (TOWER_Z0 + TOWER_Z1) / 2, MAIN_DECK_Y, BALLOON_Y, 1.5),
				new ShipGeometry.Mast(0.0, MAST_Z, TOP_DECK_Y, MAST_TOP, 0.2));
		spec.extraProbes = List.copyOf(probes());
		spec.boundingRadius = Math.hypot(-tailEndZ(), 11.0) + 1.0;
		spec.aiReach = NOSE_SPIKE_Z;
		spec.aiBack = -tailEndZ();
		spec.aiHalfWidth = BALLOON_HW + 1.0;
		spec.lowestY = lowestY();
		spec.boardMinZ = QUARTERDECK_Z + 1.5;
		spec.boardMaxZ = FORECASTLE_Z - 3.5;
		spec.boardHalfWidth = 0.6;
		spec.avoidZ = new double[] {};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("sky_leviathan", "Léviathan des Cieux", new ShipGeometry(hull, spec), LeviathanLayout::config);
	}

	/** Terrain probes: rings round the balloon, its spikes, the fins, the hull's sections, the castles, the mast. */
	static List<double[]> probes() {
		List<double[]> probes = new ArrayList<>();
		for (double z = TAIL_Z + 1.0; z <= NOSE_Z - 0.5 + 1e-6; z += 2.5) {
			for (int k = 0; k < 12; k++) {
				probes.add(balloonPoint(z, 30 * k));
			}
		}
		for (double z = NOSE_Z; z <= NOSE_SPIKE_Z + 1e-6; z += 1.5) {
			probes.add(new double[] {0, BALLOON_Y, z});
		}
		probes.add(new double[] {0, BALLOON_Y, NOSE_SPIKE_Z});
		for (double z = TAIL_Z; z >= TAIL_SPIKE_Z - 1e-6; z -= 1.5) {
			probes.add(new double[] {0, BALLOON_Y, z});
		}
		probes.add(new double[] {0, BALLOON_Y, TAIL_SPIKE_Z});
		for (int k = -1; k < FINS.length; k++) {
			for (double[] uv : new double[][] {{0.92, 1.0}, {0.5, 0.5}, {0.35, 0.85}, {0.75, 0.6}, {0.15, 0.3}}) {
				probes.add(finPoint(k, uv[0], uv[1]));
			}
		}
		for (double z = HULL_STERN_Z + 0.2; z <= HULL_BOW_Z - 0.3 + 1e-6; z += 2.0) {
			double k = keelY(z);
			probes.add(new double[] {0, k + 0.1, z});
			double top = sheerY(z) + (deckY(z) > MAIN_DECK_Y ? 1.0 : 0.0);
			for (double y : new double[] {k + 1.2, (k + SHEER_WAIST) / 2, SHEER_WAIST - 0.1, top - 0.1}) {
				double x = hullX(z, Math.min(y, top)) - 0.05;
				probes.add(new double[] {x, y, z});
				probes.add(new double[] {-x, y, z});
			}
		}
		probes.add(new double[] {0, 1.2, 20.8});
		probes.add(new double[] {0, 3.6, 22.4});
		probes.add(new double[] {0, BOWSPRIT_TIP_Y, BOWSPRIT_TIP_Z});
		probes.add(new double[] {0, MAST_TOP + 0.5, MAST_Z});
		for (double z : new double[] {TOP_DECK_Z0 + 1.0, TOP_DECK_Z1 - 1.0}) {
			for (double x : new double[] {-TOP_DECK_HALF + 0.5, TOP_DECK_HALF - 0.5}) {
				probes.add(new double[] {x, TOP_DECK_Y + 1.0, z});
			}
		}
		return probes;
	}

	/**
	 * A very big, heavy airship: slow to gather way and to stop, very wide turns, slow and progressive
	 * changes of altitude, a high clearance over the ground for its autopilot.
	 */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 2.0;
		c.normalSpeed = 4.2;
		c.fastSpeed = 6.8;
		c.reverseSpeed = 1.2;
		c.acceleration = 0.3;
		c.braking = 0.6;
		c.waterDrag = 0.15;
		c.maxTurnRate = 6.5;
		c.minTurnFactor = 0.5;
		c.helmRate = 0.8;
		c.helmReturnRate = 0.8;
		c.turnResponse = 0.5;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 0.5;
		c.aiWaypointRadius = 16.0;
		c.aiStopRadius = 4.0;
		c.aiLookahead = 36.0;
		c.aiProbeDistance = 80.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 0.5;
		c.furlSailWhenStopped = false;
		FlightConfig f = new FlightConfig();
		f.climbSpeed = 1.2;
		f.descendSpeed = 1.0;
		f.verticalAcceleration = 0.45;
		f.aiClearance = 8.0;
		f.aiApproachDistance = 48.0;
		f.aiLandingClearance = 2.0;
		f.sway = 0.6;
		c.flight = f;
		return c;
	}
}
