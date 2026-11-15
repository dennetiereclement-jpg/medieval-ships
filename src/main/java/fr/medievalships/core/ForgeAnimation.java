package fr.medievalships.core;

/**
 * How the divine forge moves (1.34.0), as pure functions of the time: the gears ({@code gear_a_*} clockwise seen from
 * the front, {@code gear_b_*} the other way) turning slowly at rest and faster while the forge is active
 * ({@link ForgeActivity}), and the flipbooks (the fire {@code fire_f0..3}, the heat columns {@code flow_l_f*} /
 * {@code flow_r_f*}: one image at a time) running faster while active. The change of pace is eased
 * ({@link #EASE_SECONDS}): a {@link Track} integrates the angle and the images from frame to frame, so nothing jumps when
 * an activity starts or ends. Also the pace of the client-side effects
 * (particles, sounds) and the distance within which they play. The client keeps one track per forge.
 */
public final class ForgeAnimation {
	private ForgeAnimation() {
	}

	/** Gear speed (degrees per second) at rest and while active. */
	public static final double GEAR_IDLE_DPS = 9.0, GEAR_CRAFT_DPS = 48.0;
	/** Images per second of the fire's flipbook at rest and while active. */
	public static final double FIRE_IDLE_FPS = 6.0, FIRE_CRAFT_FPS = 11.0;
	/** Images per second of the heat columns' flipbooks at rest and while active. */
	public static final double FLOW_IDLE_FPS = 4.0, FLOW_CRAFT_FPS = 9.0;
	/** Time constant of the change of pace (seconds): about 95 % of the new pace after three of them. */
	public static final double EASE_SECONDS = 0.8;
	/** The effects (particles, sounds) play only for a player within this distance of the forge (blocks). */
	public static final double EFFECTS_DISTANCE = 24.0;
	/** Images in each flipbook of the contract (fire_f0..f3, flow_l_f0..f3, flow_r_f0..f3). */
	public static final int FRAMES = 4;

	/** Speed of the gears (degrees per second) for an intensity from 0 (rest) to 1 (active). */
	public static double gearSpeed(double intensity) {
		return lerp(GEAR_IDLE_DPS, GEAR_CRAFT_DPS, intensity);
	}

	public static double fireRate(double intensity) {
		return lerp(FIRE_IDLE_FPS, FIRE_CRAFT_FPS, intensity);
	}

	public static double flowRate(double intensity) {
		return lerp(FLOW_IDLE_FPS, FLOW_CRAFT_FPS, intensity);
	}

	/** The image shown for a flipbook phase (images elapsed, fractional): 0 to {@code frames - 1}, cycling. */
	public static int frame(double phase, int frames) {
		if (frames <= 1 || Double.isNaN(phase) || Double.isInfinite(phase)) {
			return 0;
		}
		long f = (long) Math.floor(phase);
		return (int) Math.floorMod(f, (long) frames);
	}

	/**
	 * The signed angle (degrees about the gear's own z axis, positive anticlockwise seen from that axis' end) of a gear
	 * for the track's angle: {@code gear_a} clockwise seen from the front (negative), {@code gear_b} anticlockwise.
	 */
	public static double gearAngle(double trackAngle, boolean clockwise) {
		return clockwise ? -trackAngle : trackAngle;
	}

	/**
	 * The eased pace of one forge, integrated from frame to frame (client side, render thread): the gears' angle in
	 * degrees (wrapped to [0, 360)), the flipbooks' phases in images, and the intensity (0 rest, 1 active).
	 * A time step longer than {@link #MAX_STEP_SECONDS} (the game paused, the forge out of view for a while) or backwards
	 * (another world) restarts from the current pace without a jump.
	 */
	public static final class Track {
		public static final double MAX_STEP_SECONDS = 1.0;
		public double gear;
		public double fire;
		public double flowLeft;
		public double flowRight = 1.5; // the two columns out of step
		public double intensity;
		private double last = Double.NaN;

		/** Advances to {@code timeTicks} (game ticks, fractional), active or not. */
		public void update(double timeTicks, boolean active) {
			double target = active ? 1.0 : 0.0;
			if (Double.isNaN(last) || timeTicks < last || (timeTicks - last) / 20.0 > MAX_STEP_SECONDS) {
				if (Double.isNaN(last)) {
					intensity = target;
				}
				last = timeTicks;
				return;
			}
			double dt = (timeTicks - last) / 20.0;
			last = timeTicks;
			double k = 1.0 - Math.exp(-dt / EASE_SECONDS);
			intensity += (target - intensity) * k;
			gear = (gear + gearSpeed(intensity) * dt) % 360.0;
			fire = (fire + fireRate(intensity) * dt) % 1_000_000.0;
			double flow = flowRate(intensity) * dt;
			flowLeft = (flowLeft + flow) % 1_000_000.0;
			flowRight = (flowRight + flow) % 1_000_000.0;
		}

		public int fireFrame(int frames) {
			return frame(fire, frames);
		}

		public int flowFrame(boolean left, int frames) {
			return frame(left ? flowLeft : flowRight, frames);
		}
	}

	// ---- the pace of the client-side effects (chances per tick of a forge near the player)

	/** Chance per tick of a spark at each spark point (rest, active). */
	public static final double SPARK_IDLE = 0.02, SPARK_CRAFT = 0.10;
	/** Chance per tick of an ember at each ember point. */
	public static final double EMBER_IDLE = 0.04, EMBER_CRAFT = 0.12;
	/** Chance per tick of a mote of holy light at each holy point. */
	public static final double HOLY_IDLE = 0.03, HOLY_CRAFT = 0.15;
	/** Ticks between two puffs of steam (random within the range), at rest and while active. */
	public static final int STEAM_IDLE_MIN = 140, STEAM_IDLE_MAX = 300, STEAM_CRAFT_MIN = 60, STEAM_CRAFT_MAX = 120;
	/** Ticks between two crackles of the fire, two machine noises, two hammer blows (while active only). */
	public static final int CRACKLE_MIN = 50, CRACKLE_MAX = 110, MACHINE_MIN = 120, MACHINE_MAX = 260, HAMMER_MIN = 14, HAMMER_MAX = 24;

	/** A chance per tick between rest and activity. */
	public static double chance(double idle, double craft, boolean active) {
		return active ? craft : idle;
	}

	/** Ticks until the next event of a range, from a random number in [0, 1). */
	public static int interval(int min, int max, double random) {
		return min + (int) Math.floor(Math.max(0, Math.min(0.999999, random)) * (max - min + 1));
	}

	/** Is a player at this squared distance close enough for the effects? */
	public static boolean near(double squaredDistance) {
		return squaredDistance <= EFFECTS_DISTANCE * EFFECTS_DISTANCE;
	}

	private static double lerp(double a, double b, double t) {
		double c = Math.max(0, Math.min(1, t));
		return a + (b - a) * c;
	}
}
