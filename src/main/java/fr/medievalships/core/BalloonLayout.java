package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The steampunk hot-air balloon ({@code hot_air_balloon}): a big round envelope of twenty olive-green and beige
 * gores, slightly taller than wide (13.4 x 14.4 blocks), with a brass load band round its lower belly, gold chains
 * down its skirt to a load ring at the mouth and from there to a small dark green-stained wooden basket (a 10 block
 * boat hull with dark rims, lit windows along its sides, lanterns under its ends); in the basket a copper and brass
 * burner column with a square platform half way up, the burner head whose flame rises into the mouth, a black boiler
 * with its stack and a big wooden gear wheel on the port side. It flies like the steampunk airship ({@link Flight}),
 * slowly and softly; 4 places (the pilot standing at the burner's valves, three on the benches).
 *
 * <p>Ship-local blocks, shared with tools/balloon_shape.py (same numbers, same formulas; checked by BalloonTest):
 * x = lateral (+x = port), y = up (0 = the basket's deck), z = forward (+z = bow). The envelope is a body of
 * revolution about the vertical axis x = z = 0, its radius given by {@link #balloonRadius} between the mouth and
 * the crown.
 */
public final class BalloonLayout {
	// ---- the basket: a small boat hull with raised ends
	public static final double HALF_LENGTH = 4.6;
	public static final double TIP = 5.1;
	public static final double MAX_HALF_WIDTH = 1.85;
	public static final double MAIN_DECK_Y = 0.0;
	public static final double DECK_MIN_Z = -4.2;
	public static final double DECK_MAX_Z = 4.2;
	public static final double LANTERN_Z = 3.7;
	public static final double LANTERN_DROP = 1.3;
	public static final double LOWEST_Y = -1.5;

	// ---- the envelope
	public static final double R = 6.7;
	public static final double MOUTH_Y = 5.0;
	public static final double TOP_Y = 19.4;
	/** (height fraction, r / R) of the profile, Catmull-Rom between them (as in balloon_shape.py). */
	private static final double[][] PROFILE = {{0.0, 0.35}, {0.08, 0.5}, {0.2, 0.68}, {0.32, 0.84}, {0.45, 0.95}, {0.56, 1.0},
			{0.66, 0.99}, {0.77, 0.93}, {0.87, 0.8}, {0.94, 0.6}, {0.98, 0.32}, {1.0, 0.0}};
	public static final double CROWN_F = 0.975;
	public static final double BAND_F = 0.4;
	public static final int GORES = 20;
	public static final double MOUTH_R = R * 0.35;

	// ---- the burner column, the platform, the machinery, the places
	public static final double COLUMN_Z = 0.0;
	public static final double PLATFORM_Y = 2.5;
	public static final double PLATFORM_HALF = 0.85;
	public static final double BURNER_Y = 4.05;
	public static final double FLAME_TOP = 5.9;
	public static final double BOILER_Z = -2.4;
	public static final double BOILER_X = 0.45;
	public static final double STACK_TOP = 3.9;
	public static final double WHEEL_Z = -2.4;
	public static final double WHEEL_R = 1.4;
	public static final double WHEEL_Y = 2.3;
	public static final int WHEEL_SIDE = 1;
	public static final double WHEEL_X = WHEEL_SIDE * (MAX_HALF_WIDTH + 0.42);
	public static final double HELM_Z = -1.3;
	public static final double PILOT_Z = -2.1;
	public static final double BENCH_Z = 1.9;
	public static final double BOW_SEAT_Z = 3.5;
	/** Where the burner's flame and the stack's smoke are (ship-local), for the client effects. */
	public static final double[] BURNER = {0.0, BURNER_Y + 0.3, COLUMN_Z};
	public static final double[] STACK = {BOILER_X, STACK_TOP + 0.1, BOILER_Z - 0.05};

	private BalloonLayout() {
	}

	// ------------------------------------------------------------------ shape (as in balloon_shape.py)

	private static double cr(double p0, double p1, double p2, double p3, double t) {
		return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t);
	}

	/** r / R of the envelope at the height fraction f (0 = mouth, 1 = crown). */
	public static double profile(double f) {
		if (f <= 0.0) {
			return PROFILE[0][1];
		}
		if (f >= 1.0) {
			return 0.0;
		}
		int n = PROFILE.length;
		int i = 0;
		while (i < n - 2 && f >= PROFILE[i + 1][0]) {
			i++;
		}
		double f0 = PROFILE[i][0], r0 = PROFILE[i][1];
		double f1 = PROFILE[i + 1][0], r1 = PROFILE[i + 1][1];
		double t = (f - f0) / (f1 - f0);
		double rm = PROFILE[Math.max(0, i - 1)][1];
		double rp = PROFILE[Math.min(n - 1, i + 2)][1];
		return Math.max(0.0, cr(rm, r0, r1, rp, t));
	}

	/** Radius of the envelope at the height y (0 outside the mouth .. crown range). */
	public static double balloonRadius(double y) {
		return R * profile((y - MOUTH_Y) / (TOP_Y - MOUTH_Y));
	}

	/** Height of the height fraction f. */
	public static double fy(double f) {
		return MOUTH_Y + (TOP_Y - MOUTH_Y) * f;
	}

	// ------------------------------------------------------------------ the type

	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 5.15;
		p.forePowA = 2.6;
		p.forePowB = 0.7;
		p.aftScale = 5.15;
		p.aftPowA = 2.6;
		p.aftPowB = 0.7;
		p.keelDepth = 1.3;
		p.keelRise = 0.95;
		p.keelPow = 2.0;
		p.railBase = 1.0;
		p.railRiseFore = 0.38;
		p.railRiseAft = 0.38;
		p.railPow = 2.2;
		p.waterlineY = 0.0;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = DECK_MIN_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.55, 0.9}, {0.88, 0.55}, {0.99, 0.12}};
		HullShape hull = new HullShape(p);

		double main = MAIN_DECK_Y;
		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the burner's valves, facing the bow; the benches face inwards, the bow bench aft
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, main + 0.28, PILOT_Z, true, new double[] {-0.9, main + 0.02, PILOT_Z + 0.3}));
		for (double x : new double[] {1.05, -1.05}) {
			seats.add(new ShipGeometry.Seat(seats.size(), x, main + 0.47, BENCH_Z, false, new double[] {x * 0.3, main + 0.02, BENCH_Z - 0.9}));
		}
		seats.add(new ShipGeometry.Seat(seats.size(), 0.0, main + 0.47, BOW_SEAT_Z, false, new double[] {0.0, main + 0.02, BOW_SEAT_Z - 0.9}));
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.45, main + 0.3, HELM_Z - 0.45, 0.45, main + 1.6, HELM_Z + 0.35);
		// the column (one walks round it) and the crown finial (the highest point)
		spec.masts = List.of(new ShipGeometry.Mast(0.0, COLUMN_Z, main, BURNER_Y, 0.3));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		// the platform frame round the column, the boiler, the gear wheel outside the port side
		solids.add(new ShipGeometry.LocalBox(-PLATFORM_HALF - 0.1, main, COLUMN_Z - PLATFORM_HALF - 0.1, PLATFORM_HALF + 0.1, PLATFORM_Y + 0.75,
				COLUMN_Z + PLATFORM_HALF + 0.1));
		solids.add(new ShipGeometry.LocalBox(BOILER_X - 0.5, main, BOILER_Z - 0.5, BOILER_X + 0.5, main + 2.0, BOILER_Z + 0.5));
		solids.add(new ShipGeometry.LocalBox(Math.min(WHEEL_X - 0.15, WHEEL_X + 0.15), WHEEL_Y - WHEEL_R - 0.3, WHEEL_Z - WHEEL_R - 0.3,
				Math.max(WHEEL_X - 0.15, WHEEL_X + 0.15), WHEEL_Y + WHEEL_R + 0.3, WHEEL_Z + WHEEL_R + 0.3));
		// the envelope, in one block slabs (players cannot walk through it, picking hits it), and the crown
		for (double y0 = MOUTH_Y; y0 < TOP_Y - 0.2; y0 += 1.0) {
			double y1 = Math.min(TOP_Y, y0 + 1.0);
			double r = Math.min(balloonRadius(y0), balloonRadius(y1)) * 0.82;
			if (r < 0.4) {
				continue;
			}
			solids.add(new ShipGeometry.LocalBox(-r, y0, -r, r, y1, r));
		}
		solids.add(new ShipGeometry.LocalBox(-0.8, fy(CROWN_F), -0.8, 0.8, TOP_Y + 0.5, 0.8));
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.15, 0.9};
		spec.extraProbes = List.copyOf(probes());
		spec.flying = true;
		spec.boundingRadius = R + 0.6;
		spec.aiReach = R + 0.5;
		spec.aiBack = R + 0.5;
		spec.aiHalfWidth = R + 0.5;
		spec.lowestY = LOWEST_Y;
		spec.boardMinZ = -3.9;
		spec.boardMaxZ = 4.1;
		spec.avoidZ = new double[] {BENCH_Z, BOW_SEAT_Z, COLUMN_Z, BOILER_Z};
		spec.stemPost = false;
		spec.sternPost = false;
		return new ShipType("hot_air_balloon", "Montgolfière steampunk", new ShipGeometry(hull, spec), BalloonLayout::config);
	}

	/** Terrain probes for everything outside the basket: the envelope, the crown, the wheel, the stack, the lanterns, the keel. */
	static List<double[]> probes() {
		List<double[]> probes = new ArrayList<>();
		for (double f : new double[] {0.04, 0.14, 0.26, BAND_F, 0.54, 0.68, 0.82, 0.92}) {
			double r = R * profile(f) + 0.15, y = fy(f);
			for (int k = 0; k < 12; k++) {
				double a = Math.toRadians(30 * k + (f > 0.5 ? 15 : 0));
				probes.add(new double[] {Math.sin(a) * r, y, Math.cos(a) * r});
			}
		}
		probes.add(new double[] {0, TOP_Y + 0.5, 0});
		probes.add(new double[] {0, MOUTH_Y - 0.5, 0});
		for (int k = 0; k < 8; k++) {
			double a = Math.toRadians(45 * k);
			probes.add(new double[] {WHEEL_X, WHEEL_Y + Math.cos(a) * (WHEEL_R + 0.3), WHEEL_Z + Math.sin(a) * (WHEEL_R + 0.3)});
		}
		probes.add(new double[] {BOILER_X, STACK_TOP + 0.4, BOILER_Z});
		for (double z : new double[] {LANTERN_Z, -LANTERN_Z}) {
			for (double x : new double[] {MAX_HALF_WIDTH * 0.75 + 0.3, -MAX_HALF_WIDTH * 0.75 - 0.3}) {
				probes.add(new double[] {x, -0.8, z});
			}
		}
		for (double z = -4.0; z <= 4.0; z += 1.0) {
			probes.add(new double[] {0, LOWEST_Y + 0.05, z});
		}
		return probes;
	}

	/** Light and floaty: slow, long to gather way, gentle turns, a soft climb and a soft landing, a slight sway. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.2;
		c.normalSpeed = 2.6;
		c.fastSpeed = 4.0;
		c.reverseSpeed = 0.8;
		c.acceleration = 0.3;
		c.braking = 0.35;
		c.waterDrag = 0.1;
		c.maxTurnRate = 9.0;
		c.minTurnFactor = 0.6;
		c.helmRate = 0.9;
		c.helmReturnRate = 0.8;
		c.turnResponse = 0.6;
		c.turnSpeedLoss = 0.04;
		c.waveRocking = 0.8;
		c.aiWaypointRadius = 7.0;
		c.aiStopRadius = 2.5;
		c.aiLookahead = 14.0;
		c.aiProbeDistance = 36.0;
		c.aiStuckSeconds = 10;
		c.aiTurnAroundSpeed = 0.6;
		c.furlSailWhenStopped = false;
		FlightConfig f = new FlightConfig();
		f.climbSpeed = 1.2;
		f.descendSpeed = 1.0;
		f.verticalAcceleration = 0.35;
		f.aiClearance = 6.0;
		f.aiApproachDistance = 24.0;
		f.aiLandingClearance = 1.0;
		f.sway = 1.6;
		f.bankAngle = 3.0;
		c.flight = f;
		return c;
	}
}
