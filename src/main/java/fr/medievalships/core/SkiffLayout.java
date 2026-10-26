package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Rustic Skyskiff ({@code rustic_skiff}): an old, hand-made wooden boat turned into a small, agile flying craft.
 * A long, banana-shaped patched hull of 26 blocks (bow head to transom; 41 from the tip of the bow beam to the mouths
 * of the stern tubes), 8 wide, rising to a raised bow; the open fore deck with the lean-to over the bow; the cabin at
 * the stern (common room, bedroom) with the pilot deck on its roof under a big worn canvas roof on splayed poles; the
 * storage hold under the decks; five tubes on the transom and four canvas wings hanging under the sides. It flies like
 * the steampunk airship ({@link Flight}), more nimbly; its rooms are described by an interior grid
 * (tools/skiff_interior.py): players walk on its decks and in its rooms while it flies.
 *
 * <p>Ship-local blocks, shared with tools/skiff_shape.py (same numbers, same formulas; checked by SkiffTest):
 * x = lateral (+x = port), y = up (0 = the fore deck and the cabin floor), z = forward (+z = bow).
 */
public final class SkiffLayout {
	// ---- hull
	public static final double DECK_Y = 0.0;
	public static final double HULL_BOW_Z = 13.4;
	public static final double HULL_STERN_Z = -13.0;
	public static final double HULL_HW = 4.0;
	public static final double TRANSOM_HW = 3.3;
	private static final double[] STERN_TAPER = {-4.0, 9.0};
	private static final double BOW_ROOT_Z = 2.0;
	public static final double BOW_HW = 2.6;
	private static final double[] SHOULDER = {3.5, 6.5};
	public static final double SHEER_WAIST = 1.0;
	public static final double BOW_SHEER = 2.8;
	private static final double BOW_RISE_Z = 4.0;
	private static final double[] SECTION = {0.08, 1.8, 0.6};
	private static final double FLARE = 0.03;
	private static final double[][] KEEL_PTS = {{-13.0, -2.3}, {-12.4, -2.8}, {-11.0, -3.15}, {-8.0, -3.35}, {-4.0, -3.45}, {0.0, -3.4},
			{3.0, -3.2}, {5.5, -2.8}, {7.5, -2.3}, {9.5, -1.5}, {11.0, -0.6}, {12.2, 0.3}, {13.0, 1.2}, {13.4, 2.0}};
	private static final double[] KEEL_SLOPES = keelSlopes();
	private static final double[][] BOW_STEPS = {{10.0, 0.5}, {11.5, 1.0}};
	public static final double BOWSPRIT_TIP_Y = 2.05;
	public static final double BOWSPRIT_TIP_Z = 18.0;

	// ---- cabin, pilot deck, hold
	public static final double CABIN_FRONT_Z = -3.0;
	public static final double PILOT_Y = 3.0;
	public static final double PILOT_HW = 4.9;
	public static final double PILOT_AFT_Z = -13.45;
	public static final double PILOT_FORE_Z = -2.6;
	public static final double PARTITION_Z = -7.75;
	public static final double HOLD_Y = -2.5;
	public static final double HOLD_FORE_Z = 4.5;
	public static final double HOLD_AFT_Z = -10.5;
	public static final double HELM_Z = -4.3;
	public static final double PILOT_STAND_Z = -5.1;
	public static final double RAIL_H = 1.5;

	// ---- the canvas roof
	public static final double CANOPY_Z = -8.5;
	public static final double APEX_Y = 12.5;
	public static final double KING_TOP = 13.4;
	/** (|x|, y, z) of the corner poles' tops. */
	private static final double[][] POLE_TOPS = {{5.2, 9.5, -1.4}, {5.2, 9.5, -15.6}};
	private static final double POLE_TIP = 0.9;
	private static final double[] EAVE_HALF = {5.9, 8.4};
	private static final double EAVE_N = 3.0;
	public static final double EAVE_Y = 8.9;
	private static final double EAVE_SAG = 1.0;
	private static final double ROOF_POW = 2.0;
	/** The derricks at the stern: foot and tip (port side). */
	private static final double[][] DERRICK = {{2.9, PILOT_Y, -12.9}, {4.3, 11.6, -18.6}};

	// ---- the tubes and the wings
	/** x, y, radius of the five stern tubes. */
	public static final double[][] TUBES = {{0.95, 2.8, 0.6}, {-0.95, 2.8, 0.6}, {0.95, 1.35, 0.6}, {-0.95, 1.35, 0.6}, {0.0, 2.07, 0.42}};
	public static final double TUBE_START_Z = -12.7;
	public static final double TUBE_END_Z = -20.6;
	public static final double TUBE_CENTRE_END_Z = -21.1;
	/** The wings (port side; starboard mirrored): root on the hull, top corner, tip. */
	public static final String[] WING_NAMES = {"wing_fore", "wing_aft"};
	private static final double[][][] WINGS = {
			{{2.6, -2.2, -0.6}, {6.2, -4.6, -7.4}, {4.9, -9.0, -6.4}},
			{{2.75, -1.2, -11.9}, {5.8, -1.7, -18.6}, {5.0, -11.0, -14.2}}};
	/** The point of the keel spike under the stern box (y, z). */
	public static final double[] SKID_TIP = {-8.3, -11.75};

	// ---- interior
	public static final String GRID = "/assets/medievalships/interiors/rustic_skiff.grid";
	public static final String DECOR = "/assets/medievalships/interiors/rustic_skiff_decor.json";
	/** Doors of the interior grid (tools/skiff_interior.py DOORS). */
	public static final int CABIN_DOOR = 0;
	public static final int BEDROOM_DOOR = 1;
	public static final int GRATE_HATCH = 2;

	private SkiffLayout() {
	}

	// ------------------------------------------------------------------ shape (as in skiff_shape.py)

	private static double smooth(double t) {
		t = Math.max(0.0, Math.min(1.0, t));
		return t * t * (3 - 2 * t);
	}

	static double bodyHalfWidth(double z) {
		return HULL_HW - (HULL_HW - TRANSOM_HW) * smooth((STERN_TAPER[0] - z) / STERN_TAPER[1]);
	}

	static double bowHalfWidth(double z) {
		double t = (z - BOW_ROOT_Z) / (HULL_BOW_Z - BOW_ROOT_Z);
		if (t >= 1.0) {
			return 0.0;
		}
		if (t <= 0.0) {
			return BOW_HW;
		}
		return BOW_HW * Math.pow(1.0 - t * t, 0.6);
	}

	/** Half beam at z (at the waist): the body blending into the narrow raised bow over the shoulder. */
	public static double hullHalfWidth(double z) {
		if (z > HULL_BOW_Z || z < HULL_STERN_Z) {
			return 0.0;
		}
		double s = smooth((z - SHOULDER[0]) / (SHOULDER[1] - SHOULDER[0]));
		return bodyHalfWidth(z) * (1.0 - s) + bowHalfWidth(z) * s;
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

	/** Bottom of the hull at z (monotone cubic through the keel line). */
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

	/** Top of the hull planking: the fore deck's bulwark sweeping up to the bow head, the cabin walls aft. */
	public static double sheerY(double z) {
		if (z <= CABIN_FRONT_Z) {
			return PILOT_Y;
		}
		return SHEER_WAIST + (BOW_SHEER - SHEER_WAIST) * Math.pow(smooth((z - BOW_RISE_Z) / (HULL_BOW_Z - BOW_RISE_Z)), 1.25);
	}

	/** The walkable floor of the open fore deck at z (it steps up twice under the bow's lean-to). */
	public static double deckY(double z) {
		double y = DECK_Y;
		for (double[] s : BOW_STEPS) {
			if (z > s[0]) {
				y = s[1];
			}
		}
		return y;
	}

	static double waistY(double z) {
		return Math.max(SHEER_WAIST, keelY(z) + 0.6);
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
		double top = waistY(z);
		if (y <= top) {
			double eta = (y - k) / (top - k);
			return w * (SECTION[0] + (1.0 - SECTION[0]) * Math.pow(1.0 - Math.pow(1.0 - eta, SECTION[1]), SECTION[2]));
		}
		return w * (1.0 + FLARE * (y - top));
	}

	// ------------------------------------------------------------------ the canvas roof

	static double eaveRadius(double theta) {
		double c = Math.abs(Math.cos(theta)), s = Math.abs(Math.sin(theta));
		return 1.0 / Math.pow(Math.pow(c / EAVE_HALF[0], EAVE_N) + Math.pow(s / EAVE_HALF[1], EAVE_N), 1.0 / EAVE_N);
	}

	static double[] cornerAngles() {
		double[] out = new double[4];
		int k = 0;
		for (double sx : new double[] {1, -1}) {
			for (double[] p : POLE_TOPS) {
				out[k++] = Math.atan2(p[2] - CANOPY_Z, sx * p[0]);
			}
		}
		return out;
	}

	static double eaveDrop(double theta) {
		double two = 2 * Math.PI;
		double[] angs = cornerAngles();
		for (int i = 0; i < angs.length; i++) {
			angs[i] = ((angs[i] % two) + two) % two;
		}
		java.util.Arrays.sort(angs);
		double t = ((theta % two) + two) % two;
		for (int i = 0; i < angs.length; i++) {
			double a0 = angs[i];
			double a1 = angs[(i + 1) % angs.length] + (i == angs.length - 1 ? two : 0.0);
			double tt = t >= a0 ? t : t + two;
			if (a0 <= tt && tt <= a1) {
				double f = (tt - a0) / (a1 - a0);
				return EAVE_SAG * Math.pow(Math.sin(Math.PI * f), 1.5);
			}
		}
		return 0.0;
	}

	/** Point of the canvas roof at azimuth theta (0 = port, pi/2 = bow) and fraction t from the apex to the eaves. */
	public static double[] roofPoint(double theta, double t) {
		double r = eaveRadius(theta) * t;
		double ye = EAVE_Y - eaveDrop(theta);
		double y = ye + (APEX_Y - ye) * Math.pow(1.0 - t, ROOF_POW);
		return new double[] {r * Math.cos(theta), y, CANOPY_Z + r * Math.sin(theta)};
	}

	// ------------------------------------------------------------------ wings

	/** Root, top corner and tip of wing k (index in {@link #WING_NAMES}) on a side (+1 port, -1 starboard). */
	public static double[][] wing(int k, int side) {
		double[][] w = WINGS[k];
		double[][] out = new double[3][];
		for (int i = 0; i < 3; i++) {
			out[i] = new double[] {side * w[i][0], w[i][1], w[i][2]};
		}
		return out;
	}

	/** The lowest point: the tip of a rear wing (its spike), lower than the keel spike. */
	public static double lowestY() {
		double y = SKID_TIP[0];
		for (double[][] w : WINGS) {
			y = Math.min(y, w[2][1] - 0.25);
		}
		return y;
	}

	// ------------------------------------------------------------------ the ship type

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HULL_BOW_Z;
		p.tip = BOWSPRIT_TIP_Z;
		p.maxHalfWidth = HULL_HW;
		p.foreScale = 14.0;
		p.forePowA = 2.4;
		p.forePowB = 0.6;
		p.aftScale = 16.0;
		p.aftPowA = 3.0;
		p.aftPowB = 0.5;
		// keelY(0) under the whole grid, so the collision query never cuts the hold
		p.keelDepth = 4.5;
		p.keelRise = 0.0;
		p.keelPow = 2.0;
		p.railBase = SHEER_WAIST;
		p.railRiseFore = 0.0;
		p.railRiseAft = 0.0;
		p.waterlineY = 0.0;
		p.mainDeckY = DECK_Y;
		p.deckMinZ = CABIN_FRONT_Z;
		p.deckMaxZ = 9.5;
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		spec.flying = true;
		spec.hullProbes = false;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the wheel on the pilot deck, facing the bow
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, PILOT_Y + 0.28, PILOT_STAND_Z, true,
				new double[] {1.3, PILOT_Y + 0.02, PILOT_STAND_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, PILOT_Y + 1.0, HELM_Z - 0.3, 0.8, PILOT_Y + 2.5, HELM_Z + 0.6);
		// not solid (the grid is): the king post of the canvas roof gives the height
		spec.masts = List.of(new ShipGeometry.Mast(0.0, CANOPY_Z, PILOT_Y, KING_TOP + 0.8, 0.21));
		spec.extraProbes = List.copyOf(probes());
		spec.boundingRadius = Math.hypot(-TUBE_CENTRE_END_Z, 6.5) + 1.0;
		spec.aiReach = BOWSPRIT_TIP_Z;
		spec.aiBack = -TUBE_CENTRE_END_Z;
		spec.aiHalfWidth = 6.6;
		spec.lowestY = lowestY();
		spec.boardMinZ = -1.5;
		spec.boardMaxZ = 6.5;
		spec.boardHalfWidth = 0.8;
		spec.avoidZ = new double[] {};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("rustic_skiff", "Navire Volant Rustique", new ShipGeometry(hull, spec), SkiffLayout::config);
	}

	/**
	 * Terrain probes over the whole volume: the hull's sections (keel, sides, bulwark), the bow head and its beam, the
	 * stern box and its spike, the cabin and the pilot deck, the canvas roof (eaves, apex, pole tips), the derricks, the
	 * tubes and the four wings.
	 */
	static List<double[]> probes() {
		List<double[]> probes = new ArrayList<>();
		for (double z = HULL_STERN_Z + 0.2; z <= HULL_BOW_Z - 0.2 + 1e-6; z += 1.5) {
			double k = keelY(z);
			probes.add(new double[] {0, k + 0.1, z});
			double top = sheerY(z);
			for (double y : new double[] {k + 0.8, (k + SHEER_WAIST) / 2, SHEER_WAIST - 0.1, top - 0.1}) {
				double yy = Math.min(y, top - 0.05);
				if (yy < k + 0.05) {
					continue;
				}
				double x = hullX(z, yy) - 0.05;
				probes.add(new double[] {x, yy, z});
				probes.add(new double[] {-x, yy, z});
			}
		}
		probes.add(new double[] {0, 3.2, 13.5});
		for (double t = 0.25; t <= 1.0 + 1e-9; t += 0.25) {
			probes.add(new double[] {0, 2.6 + (BOWSPRIT_TIP_Y - 2.6) * t, 12.9 + (BOWSPRIT_TIP_Z - 12.9) * t});
		}
		// the stern box and its spike
		probes.add(new double[] {0, -4.8, -11.2});
		probes.add(new double[] {0, (SKID_TIP[0] - 4.85) / 2, (SKID_TIP[1] - 11.3) / 2});
		probes.add(new double[] {0, SKID_TIP[0] + 0.05, SKID_TIP[1]});
		// the pilot deck's edges and its balustrade
		for (double z : new double[] {PILOT_AFT_Z + 0.1, (PILOT_AFT_Z + PILOT_FORE_Z) / 2, PILOT_FORE_Z - 0.1}) {
			for (double x : new double[] {-PILOT_HW + 0.1, PILOT_HW - 0.1}) {
				probes.add(new double[] {x, PILOT_Y - 0.4, z});
				probes.add(new double[] {x, PILOT_Y + RAIL_H, z});
			}
		}
		// the canvas roof: the eaves all round, half way up, the apex and the king post's finial, the poles' tips
		for (int i = 0; i < 16; i++) {
			double a = 2 * Math.PI * i / 16;
			probes.add(roofPoint(a, 1.0));
			probes.add(roofPoint(a, 0.55));
		}
		probes.add(new double[] {0, KING_TOP + 0.7, CANOPY_Z});
		for (double sx : new double[] {1, -1}) {
			for (double[] t : POLE_TOPS) {
				probes.add(new double[] {sx * t[0] * 1.03, t[1] + POLE_TIP, t[2] + Math.signum(t[2] - CANOPY_Z) * 0.15});
			}
			// the derricks' tips and the middle of their length
			double[] f = DERRICK[0], d = DERRICK[1];
			probes.add(new double[] {sx * d[0], d[1] + 0.4, d[2] - 0.3});
			probes.add(new double[] {sx * (f[0] + d[0]) / 2, (f[1] + d[1]) / 2, (f[2] + d[2]) / 2});
		}
		// the tubes' mouths and middles
		for (double[] t : TUBES) {
			double end = t[2] < 0.5 ? TUBE_CENTRE_END_Z : TUBE_END_Z;
			probes.add(new double[] {t[0], t[1], end});
			probes.add(new double[] {t[0] + Math.signum(t[0]) * t[2], t[1] + Math.signum(t[1] - 2.0) * t[2], (TUBE_START_Z + end) / 2});
		}
		// the wings: root, top corner, tip and points of their canvas
		for (int k = 0; k < WINGS.length; k++) {
			for (int side : new int[] {1, -1}) {
				double[][] w = wing(k, side);
				double[] r = w[0], t = w[1], p = w[2];
				probes.add(t);
				probes.add(new double[] {p[0], p[1] - 0.2, p[2]});
				for (double[] uv : new double[][] {{0.5, 0.5}, {0.8, 0.2}, {0.8, 0.8}, {0.3, 0.5}}) {
					double s = uv[0], f = uv[1];
					probes.add(new double[] {r[0] + s * (t[0] + f * (p[0] - t[0]) - r[0]), r[1] + s * (t[1] + f * (p[1] - t[1]) - r[1]),
							r[2] + s * (t[2] + f * (p[2] - t[2]) - r[2])});
				}
			}
		}
		return probes;
	}

	/**
	 * A small, light craft: quick to gather way and to stop, tight turns, quick changes of altitude - more nimble than
	 * the steampunk airship.
	 */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 3.0;
		c.normalSpeed = 6.2;
		c.fastSpeed = 9.5;
		c.reverseSpeed = 2.2;
		c.acceleration = 1.1;
		c.braking = 1.6;
		c.waterDrag = 0.3;
		c.maxTurnRate = 20.0;
		c.minTurnFactor = 0.6;
		c.helmRate = 2.0;
		c.helmReturnRate = 1.6;
		c.turnResponse = 1.5;
		c.turnSpeedLoss = 0.08;
		c.waveRocking = 0.8;
		c.aiWaypointRadius = 7.0;
		c.aiStopRadius = 2.5;
		c.aiLookahead = 18.0;
		c.aiProbeDistance = 44.0;
		c.aiStuckSeconds = 8;
		c.aiTurnAroundSpeed = 1.0;
		c.furlSailWhenStopped = false;
		FlightConfig f = new FlightConfig();
		f.climbSpeed = 2.4;
		f.descendSpeed = 2.0;
		f.verticalAcceleration = 1.8;
		f.aiClearance = 5.0;
		f.aiApproachDistance = 24.0;
		f.aiLandingClearance = 1.0;
		f.sway = 0.9;
		c.flight = f;
		return c;
	}
}
