package fr.medievalships.core;

/**
 * A route point. {@code waitSeconds > 0} makes it a stop (port, quay): the ship stops there
 * and waits before leaving; {@link #HOLD} ({@code -1}) makes it a stop where the ship waits
 * until it is told to leave ({@code /ship route depart}, a quest script). {@code gait}
 * optionally overrides the cruising gait on the leg leading to this point.
 */
public final class Waypoint {
	/** {@link #waitSeconds} of a stop where the vessel waits for the order to leave, however long it takes. */
	public static final int HOLD = -1;

	public double x;
	public double y;
	public double z;
	/** Seconds waited at this stop; 0 = a point passed without stopping; {@link #HOLD} = until told to leave. */
	public int waitSeconds;
	public String name;
	public String gait;
	/** Optional speed (blocks/s) on the leg leading to this point, instead of the gait. */
	public Double speed;
	/** Optional heading (degrees, Minecraft yaw) the ship turns to while waiting at this stop (aircraft). */
	public Double yaw;
	/**
	 * Optional depth (blocks below the surface) of a submarine on the leg leading to this point and
	 * at this stop: 0 = on the surface. Without it, a submarine cruises at its configured depth and
	 * comes up at the stops.
	 */
	public Double depth;
	/**
	 * Optional command the server runs when a vessel arrives at this stop ({@code /ship route onarrive}), as the
	 * vessel (it is {@code @s}, the position is its own), with the permission level of the administrators.
	 */
	public String onArrive;

	public Waypoint() {
	}

	public Waypoint(double x, double y, double z, int waitSeconds, String name) {
		this.x = x;
		this.y = y;
		this.z = z;
		this.waitSeconds = waitSeconds;
		this.name = name;
	}

	/** A stop (the vessel stops and waits there), timed or held. */
	public boolean isStop() {
		return waitSeconds != 0;
	}

	/** A stop where the vessel waits for the order to leave rather than for a time. */
	public boolean holds() {
		return waitSeconds < 0;
	}

	/** Ticks the vessel waits once moored here: negative = until told to leave. */
	public int dockTicks() {
		return holds() ? Autopilot.HOLD_TICKS : Math.max(1, waitSeconds) * 20;
	}

	public String label(int index) {
		return name != null && !name.isBlank() ? name : "point " + (index + 1);
	}
}
