package fr.medievalships.core;

/**
 * Flight settings of an aircraft (the {@code flight} block of its section in
 * {@code config/medievalships.json}). Speeds in blocks per second, heights in blocks.
 */
public final class FlightConfig {
	/** Vertical speeds at full climb / full descent. */
	public double climbSpeed = 1.6;
	public double descendSpeed = 1.3;
	/** Vertical acceleration (blocks/s^2): low values give the slow, heavy feel of an airship. */
	public double verticalAcceleration = 0.9;
	/** Highest altitude the top of the aircraft may reach (world Y). */
	public double maxAltitude = 300.0;
	/** Autopilot: height kept between the keel and the ground or buildings on the way. */
	public double aiClearance = 5.0;
	/** Autopilot: distance from a stop where it starts to come down to the stop's altitude. */
	public double aiApproachDistance = 26.0;
	/** Autopilot: height kept under the keel when coming down at a stop. */
	public double aiLandingClearance = 1.2;
	/** Visual sway of the gondola (multiplier, 0 disables it). */
	public double sway = 1.0;

	public void sanitize() {
		climbSpeed = clamp(climbSpeed, 0.1, 10);
		descendSpeed = clamp(descendSpeed, 0.1, 10);
		verticalAcceleration = clamp(verticalAcceleration, 0.05, 20);
		maxAltitude = clamp(maxAltitude, -32, 2000);
		aiClearance = clamp(aiClearance, 1, 64);
		aiApproachDistance = clamp(aiApproachDistance, 4, 200);
		aiLandingClearance = clamp(aiLandingClearance, 0.2, 16);
		sway = clamp(sway, 0, 5);
	}

	private static double clamp(double v, double lo, double hi) {
		return Double.isNaN(v) ? lo : Math.max(lo, Math.min(hi, v));
	}
}
