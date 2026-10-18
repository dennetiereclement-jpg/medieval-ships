package fr.medievalships.core;

/**
 * Diving settings of a submarine (the {@code dive} block of its section in
 * {@code config/medievalships.json}). Speeds in blocks per second, depths in blocks.
 */
public final class DiveConfig {
	/** Vertical speeds at full rise / full dive. */
	public double riseSpeed = 1.1;
	public double diveSpeed = 1.1;
	/** Vertical acceleration (blocks/s^2): a large hull answers its ballasts slowly. */
	public double verticalAcceleration = 0.35;
	/** Deepest dive below the surfaced position. */
	public double maxDepth = 120.0;
	/** Autopilot: water kept under the keel and above the hull on the way. */
	public double aiClearance = 3.0;
	/** Autopilot: default cruising depth (keel below the surface) of the dived legs. */
	public double aiCruiseDepth = 24.0;
	/** Autopilot: distance from a stop where it starts to come to the stop's depth. */
	public double aiApproachDistance = 40.0;

	public void sanitize() {
		riseSpeed = clamp(riseSpeed, 0.1, 10);
		diveSpeed = clamp(diveSpeed, 0.1, 10);
		verticalAcceleration = clamp(verticalAcceleration, 0.05, 20);
		maxDepth = clamp(maxDepth, 0, 400);
		aiClearance = clamp(aiClearance, 1, 32);
		aiCruiseDepth = clamp(aiCruiseDepth, 0, 400);
		aiApproachDistance = clamp(aiApproachDistance, 4, 300);
	}

	private static double clamp(double v, double lo, double hi) {
		return Double.isNaN(v) ? lo : Math.max(lo, Math.min(hi, v));
	}
}
