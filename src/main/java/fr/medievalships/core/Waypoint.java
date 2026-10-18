package fr.medievalships.core;

/**
 * A route point. {@code waitSeconds > 0} makes it a stop (port, quay): the ship stops there
 * and waits before leaving. {@code gait} optionally overrides the cruising gait on the leg
 * leading to this point.
 */
public final class Waypoint {
	public double x;
	public double y;
	public double z;
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

	public Waypoint() {
	}

	public Waypoint(double x, double y, double z, int waitSeconds, String name) {
		this.x = x;
		this.y = y;
		this.z = z;
		this.waitSeconds = waitSeconds;
		this.name = name;
	}

	public boolean isStop() {
		return waitSeconds > 0;
	}

	public String label(int index) {
		return name != null && !name.isBlank() ? name : "point " + (index + 1);
	}
}
