package fr.medievalships.core;

/**
 * What a client draws of one door (1.33.0, pure Java, tested in JUnit): the pose of its movement at the time of
 * {@link DoorClock}, every frame, and no jump when the movement changes. The server sends a new movement (target, start
 * tick, start progress) when the door is asked the other way or starts; the client's clock is never exactly the
 * server's, so the new movement's pose at that instant is not quite the one on the screen (and, turning back, the
 * leaves were going the other way, the second leaf and the handles were not quite where the new curve has them). The
 * track then fades from what was drawn (for the leaves, their position and their speed: a leaf slows down and turns
 * back, it never flips) to the new movement over {@link #blendTicks} ticks. A packet that does not change the
 * movement (a setting, a name) changes nothing.
 *
 * <p>Channels of {@link #pose}: the opening of each leaf (0..1), how far the bolts are out (0..1) and the angle of the
 * handles (degrees about +z), see {@link DoorMotion}.
 */
public final class DoorTrack {
	public static final int LEAF_L = 0, LEAF_R = 1, BOLTS = 2, HANDLE = 3, CHANNELS = 4;
	/** Ticks of the step used to measure the speed of what is drawn. */
	static final double H = 0.25;
	/** Most speed difference (opening per tick) a fade carries over for a leaf. */
	static final double MAX_SPEED = 0.25;

	private boolean known;
	private boolean target;
	private long startTick;
	private double startProgress;
	private double blendAt = Double.NaN, blendTicks;
	private final double[] d0 = new double[CHANNELS], v0 = new double[CHANNELS];
	private final double[] a = new double[CHANNELS], b = new double[CHANNELS];

	/** The pose drawn at the last {@link #update}. */
	public final double[] pose = new double[CHANNELS];
	/** The progress of the movement at the last update (0 closed .. 1 open). */
	public double progress;
	/** Is anything still moving (the movement, or the fade from the previous one)? */
	public boolean moving;

	/** Ticks over which a change of movement fades in: a quarter of the door's movement, 5 to 12 ticks. */
	public static double blendTicks(DoorType type) {
		return Math.max(5, Math.min(12, type.durationTicks() * 0.25));
	}

	/** The pose of a movement at a time, without any fade (the server's timeline, as {@link DoorMotion} computes it). */
	public static void raw(DoorType type, boolean target, long startTick, double startProgress, double now, double[] out) {
		DoorMotion.Curve c = DoorMotion.curve(type);
		int n = type.leaves(), d = type.durationTicks();
		double t = DoorMotion.progress(target, startTick, startProgress, now, d);
		out[LEAF_L] = DoorMotion.leafAt(c, n, 0, target, startTick, startProgress, now, d);
		out[LEAF_R] = n > 1 ? DoorMotion.leafAt(c, n, 1, target, startTick, startProgress, now, d) : out[LEAF_L];
		out[BOLTS] = DoorMotion.unlock(c, target, t);
		out[HANDLE] = DoorMotion.handleAngle(type, target, t);
	}

	/** Follows the door's movement ({@code target}, {@code startTick}, {@code startProgress}) to the time {@code now}. */
	public void update(DoorType type, boolean target, long startTick, double startProgress, double now) {
		if (known && (target != this.target || startTick != this.startTick || startProgress != this.startProgress)) {
			// a new movement: fade from what is drawn now (position and speed: the speed it had) to it (its speed from
			// now on: it may only start now)
			drawn(type, now, a);
			drawn(type, now - H, b);
			double[] na = new double[CHANNELS], nb = new double[CHANNELS];
			raw(type, target, startTick, startProgress, now, na);
			raw(type, target, startTick, startProgress, now + H, nb);
			for (int i = 0; i < CHANNELS; i++) {
				d0[i] = a[i] - na[i];
				// the leaves keep their speed (they slow down and turn back); the handles and bolts, quick and short, only
				// their position (matching a speed that changes within the fade would make them swing the wrong way)
				double dv = (a[i] - b[i]) / H - (nb[i] - na[i]) / H;
				v0[i] = i == LEAF_L || i == LEAF_R ? Math.max(-MAX_SPEED, Math.min(MAX_SPEED, dv)) : 0;
			}
			blendAt = now;
			blendTicks = blendTicks(type);
		}
		known = true;
		this.target = target;
		this.startTick = startTick;
		this.startProgress = startProgress;
		drawn(type, now, pose);
		progress = DoorMotion.progress(target, startTick, startProgress, now, type.durationTicks());
		moving = DoorMotion.moving(target, progress) || fading(now);
	}

	/** Is a fade from a previous movement still under way at {@code now}? */
	public boolean fading(double now) {
		return !Double.isNaN(blendAt) && now - blendAt < blendTicks;
	}

	/** What is drawn at {@code now} with the current movement and fade. */
	private void drawn(DoorType type, double now, double[] out) {
		raw(type, target, startTick, startProgress, now, out);
		if (fading(now)) {
			// the gap fades smoothly; the speed carried over dies out quickly (the leaf stops within a quarter of the
			// fade) and what it adds is given back slowly (a quarter of that speed at most: no rush)
			double tau = Math.max(0, now - blendAt), s = tau / blendTicks, w = 1 - DoorMotion.ease(s), k = (1 - s) * (1 - s) * (1 - s);
			for (int i = 0; i < CHANNELS; i++) {
				out[i] += d0[i] * w + v0[i] * tau * k;
			}
		}
		out[LEAF_L] = DoorMotion.clamp01(out[LEAF_L]);
		out[LEAF_R] = DoorMotion.clamp01(out[LEAF_R]);
		out[BOLTS] = DoorMotion.clamp01(out[BOLTS]);
	}
}
