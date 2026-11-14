package fr.medievalships.core;

/**
 * The clock a client draws the doors with (1.33.0, pure Java, tested in JUnit): the server's game time, followed
 * smoothly. A client's world time ({@code getTime()}) advances one tick per client tick, but the server sets it again
 * every second (its time packet): when the server runs slower or faster than the client, or a packet comes late, the
 * time jumps (back or forth) and a door drawn with it would jump too. This clock counts the client's own ticks (never
 * set again: monotonic) and adds an offset that follows the world time gently (at most {@link #MAX_SLEW} tick per
 * tick, with a learnt drift for a server that keeps a different pace), the offset interpolated within a tick so that
 * nothing steps at a tick either. Only a gap larger than {@link #SNAP_TICKS} (joining a world, a long freeze) is
 * taken at once.
 *
 * <p>{@link #tick} once per client tick in which the world's time advanced (after it), {@link #now} every frame.
 */
public final class DoorClock {
	/** A gap (ticks) beyond which the clock is set at once instead of followed. */
	public static final double SNAP_TICKS = 40;
	/** Most the offset moves in one tick (the drawing runs between 0.7 and 1.3 times its pace meanwhile). */
	public static final double MAX_SLEW = 0.3;
	/** Share of the gap caught up per tick, and share of it learnt as a lasting drift. */
	public static final double GAIN = 0.08, DRIFT_GAIN = 0.004;

	private long ticks;
	private double offPrev, offCur, drift;
	private boolean started;

	/** A tick of the client's world: {@code worldTime} is the world's time after it. */
	public void tick(long worldTime) {
		ticks++;
		double raw = worldTime - ticks;
		offPrev = offCur;
		if (!started || Math.abs(raw - offCur) > SNAP_TICKS) {
			offPrev = offCur = raw;
			drift = 0;
			started = true;
			return;
		}
		double err = raw - offCur;
		drift = clamp(drift + DRIFT_GAIN * err, MAX_SLEW);
		offCur += clamp(drift + GAIN * err, MAX_SLEW);
	}

	/** Has it seen a tick since it was (re)set? */
	public boolean started() {
		return started;
	}

	/** The time to draw with (ticks, fractional): {@code tickProgress} is the share of the tick gone by (0..1). */
	public double now(double tickProgress) {
		double f = tickProgress < 0 ? 0 : tickProgress > 1 ? 1 : tickProgress;
		return ticks + f + offPrev + (offCur - offPrev) * f;
	}

	/** Forgets everything (another world). */
	public void reset() {
		ticks = 0;
		offPrev = offCur = drift = 0;
		started = false;
	}

	private static double clamp(double v, double m) {
		return v < -m ? -m : v > m ? m : v;
	}
}
