package fr.medievalships.core;

/**
 * The saved data of a door across versions (pure Java, tested in JUnit). Since 1.32.0 a door's block entity carries
 * the version of its data ({@link #VERSION}); the doors placed in 1.31.0 have none (version 0).
 *
 * <p>The automatic closing: 1.32.0 closes every door by itself one minute after a click, a key or a command without a
 * duration opened it ({@link #AUTO_CLOSE_DEFAULT}). In 1.31.0 the default was "never" (0, not even saved): a door
 * saved by 1.31.0 whose closing is still that old default takes the new one; a door an administrator gave another
 * closing time keeps it. A door saved by 1.32.0 keeps exactly what it saved, 0 ("never") included.
 */
public final class DoorData {
	/** Version of the data written by 1.32.0. */
	public static final int VERSION = 2;
	/** Seconds after which a door opened by hand, by a key or by a command without a duration closes by itself. */
	public static final int AUTO_CLOSE_DEFAULT = 60;
	/** The closing of the doors saved by 1.31.0 when nobody changed it (never). */
	public static final int AUTO_CLOSE_1_31 = 0;
	/** The longest automatic closing (seconds), as {@code /porte fermeture} accepts it. */
	public static final int AUTO_CLOSE_MAX = 3600;

	private DoorData() {
	}

	/**
	 * The automatic closing of a door read from its data: {@code savedVersion} the version found (0: none, 1.31.0),
	 * {@code saved} the seconds found, or -1 when there were none.
	 */
	public static int autoClose(int savedVersion, int saved) {
		if (savedVersion < VERSION) {
			return saved < 0 || saved == AUTO_CLOSE_1_31 ? AUTO_CLOSE_DEFAULT : clamp(saved);
		}
		return saved < 0 ? AUTO_CLOSE_DEFAULT : clamp(saved);
	}

	/** The closing time an administrator may set (0 = never, up to {@link #AUTO_CLOSE_MAX}). */
	public static int clamp(int seconds) {
		return Math.max(0, Math.min(AUTO_CLOSE_MAX, seconds));
	}
}
