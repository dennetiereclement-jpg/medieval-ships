package fr.medievalships.core;

/**
 * The state of one divine forge (1.34.0): at rest, or active from a start tick to an end tick (game time,
 * {@code World#getTime}: it goes on across a restart and stands still while the server is stopped). Only the animation
 * depends on it (the fire and the heat columns brighter, the gears faster, the hammer blows): the forge crafts nothing by
 * itself. An activity is started by {@code /forge animer} or {@code DivineForgeApi}, one at a time ({@link #start}
 * refuses while active); once its end tick is reached it is {@link #due} and the server ends it ({@link #complete}),
 * which brings the forge back to rest. The block entity persists these fields; this class is the pure machine (JUnit).
 */
public final class ForgeActivity {
	/** Longest activity accepted (ticks): one hour; longer requests are cut to it. */
	public static final int MAX_TICKS = 72_000;

	private boolean active;
	private long start, end;

	/** Active (a new activity refused), even past its end until the server ends it. */
	public boolean active() {
		return active;
	}

	/** Has the activity reached its end (the server must end it)? */
	public boolean due(long now) {
		return active && now >= end;
	}

	public long start() {
		return start;
	}

	public long end() {
		return end;
	}

	/** Ticks left (0 at rest or once due). */
	public long remaining(long now) {
		return active ? Math.max(0, end - now) : 0;
	}

	/** Ticks the whole activity lasts (0 at rest). */
	public long total() {
		return active ? Math.max(1, end - start) : 0;
	}

	/** How far it is, 0 to 1 (0 at rest; clamped when the clock is before the start or after the end). */
	public double progress(long now) {
		if (!active) {
			return 0;
		}
		return Math.max(0, Math.min(1, (now - start) / (double) Math.max(1, end - start)));
	}

	/** Starts an activity of {@code ticks} (1 to {@link #MAX_TICKS}, clamped) at {@code now}. False (nothing changes) while active. */
	public boolean start(long now, int ticks) {
		if (active) {
			return false;
		}
		int t = Math.max(1, Math.min(MAX_TICKS, ticks));
		active = true;
		start = now;
		end = now + t;
		return true;
	}

	/** Moves the end of the activity (an administrator stopping it now: {@code endAt(now)}); nothing at rest. */
	public void endAt(long tick) {
		if (active) {
			end = Math.max(start, tick);
		}
	}

	/** Ends the activity (due or not) and goes back to rest: true when the forge was active. */
	public boolean complete() {
		if (!active) {
			return false;
		}
		reset();
		return true;
	}

	/** Back to rest. */
	public void reset() {
		active = false;
		start = end = 0;
	}

	/** Restores a saved state (the block entity's data): an end not after the start, or not active, gives the rest. */
	public void restore(boolean active, long start, long end) {
		reset();
		if (active && end > start) {
			this.active = true;
			this.start = start;
			this.end = end;
		}
	}
}
