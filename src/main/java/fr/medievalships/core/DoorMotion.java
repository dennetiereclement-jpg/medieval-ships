package fr.medievalships.core;

/**
 * The movement of a door (pure Java, tested in JUnit). The server keeps only the target (open or closed), the game
 * tick the current movement started at and the progress it started from; the progress at any time follows
 * ({@link #progress}), on the server for the collisions and on every client, between two ticks, for the drawing
 * (nothing is sent per tick). 0 = closed, 1 = open; the drawing uses the smooth curve {@link #ease}.
 *
 * <p>The collisions ({@link #solidAfter}): a closed door is solid; opening, it stays solid until half way; once it
 * is no longer solid it becomes solid again only when it is fully closed (closing, the passage stays free until the
 * end; a closing that turns back to opening does not make it solid again).
 */
public final class DoorMotion {
	/** Progress at which an opening door stops being solid. */
	public static final double HALF = 0.5;
	/** Distance (blocks) a bolt slides, and the share of the movement it takes. */
	public static final double BOLT_TRAVEL = 0.25, BOLT_SHARE = 0.2;
	/** Distance (blocks) a piston rod slides over the whole movement. */
	public static final double PISTON_TRAVEL = 0.25;

	private DoorMotion() {
	}

	/**
	 * Progress 0..1 at time {@code now} (ticks, fractional on a client) of a movement towards {@code target} that
	 * started at {@code startTick} from {@code startProgress} and takes {@code duration} ticks for a full stroke.
	 */
	public static double progress(boolean target, long startTick, double startProgress, double now, int duration) {
		double elapsed = Math.max(0, now - startTick);
		double step = elapsed / Math.max(1, duration);
		double p = target ? startProgress + step : startProgress - step;
		return Math.max(0, Math.min(1, p));
	}

	/** Is the door still moving at this progress? */
	public static boolean moving(boolean target, double progress) {
		return target ? progress < 1 : progress > 0;
	}

	/** Ticks left before the movement ends. */
	public static int ticksLeft(boolean target, double progress, int duration) {
		return (int) Math.ceil((target ? 1 - progress : progress) * duration - 1e-9);
	}

	/** The smooth curve of the drawing: slow start, slow end (smoothstep). */
	public static double ease(double p) {
		p = Math.max(0, Math.min(1, p));
		return p * p * (3 - 2 * p);
	}

	/** Is the door solid after this step, given whether it was before, its target and its progress? */
	public static boolean solidAfter(boolean solidBefore, boolean target, double progress) {
		if (!target && progress <= 0) {
			return true; // fully closed
		}
		if (target && progress >= HALF) {
			return false; // half open
		}
		return solidBefore;
	}

	/** Angle (degrees) of the gears at a progress: {@code turns} full turns over the whole movement. */
	public static double gearAngle(double progress, int turns) {
		return 360.0 * turns * progress;
	}

	/** How far (blocks) the bolts have slid at a progress: all their travel over the first fifth of the opening. */
	public static double boltOffset(double progress) {
		return BOLT_TRAVEL * Math.max(0, Math.min(1, progress / BOLT_SHARE));
	}

	/** How far (blocks) the piston rods have slid at a progress. */
	public static double pistonOffset(double progress) {
		return PISTON_TRAVEL * Math.max(0, Math.min(1, progress));
	}
}
