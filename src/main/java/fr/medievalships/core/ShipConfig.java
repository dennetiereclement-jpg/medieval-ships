package fr.medievalships.core;

/**
 * Navigation settings of one ship type (one section per ship in {@code config/medievalships.json}).
 * Speeds are in blocks per second, angles in degrees.
 */
public final class ShipConfig {
	// --- allures (gaits) -------------------------------------------------------
	public double slowSpeed = 2.5;
	public double normalSpeed = 5.5;
	public double fastSpeed = 8.5;
	public double reverseSpeed = 1.8;

	// --- physics ---------------------------------------------------------------
	/** Forward acceleration (blocks/s^2). */
	public double acceleration = 0.9;
	/** Deceleration when backing the oars (blocks/s^2). */
	public double braking = 1.8;
	/** Exponential speed loss per second when coasting (inertia: lower = longer glide). */
	public double waterDrag = 0.18;
	/** Yaw rate at full helm and full speed (degrees/s). */
	public double maxTurnRate = 16.0;
	/** Fraction of the turn rate available at zero speed (the oars can pivot the hull). */
	public double minTurnFactor = 0.3;
	/** How fast the helm moves to its target and back to the centre (units/s). */
	public double helmRate = 1.6;
	public double helmReturnRate = 1.0;
	/** Response of the yaw rate to the helm (1/s): lower = more rotational inertia. */
	public double turnResponse = 1.6;
	/** Fraction of the speed lost per second during a turn at maximum yaw rate. */
	public double turnSpeedLoss = 0.22;
	/** Visual wave rocking amplitude multiplier (0 disables it). */
	public double waveRocking = 1.0;

	// --- autopilot -------------------------------------------------------------
	public double aiWaypointRadius = 7.0;
	public double aiStopRadius = 2.0;
	public double aiLookahead = 12.0;
	public double aiProbeDistance = 36.0;
	public int aiDefaultWaitSeconds = 300;
	public int aiStuckSeconds = 6;
	/** Speed kept while turning towards a target behind the ship (a big sailing ship cannot pivot). */
	public double aiTurnAroundSpeed = 0.4;
	/** Furl the sail when the ship has been stopped for a few seconds. */
	public boolean furlSailWhenStopped = true;

	// --- flight (aircraft only; absent for ships) ------------------------------
	public FlightConfig flight;

	// --- diving (submarines only; absent for the others) ----------------------
	public DiveConfig dive;

	public double gaitSpeed(Gait gait) {
		return switch (gait) {
			case SLOW -> slowSpeed;
			case NORMAL -> normalSpeed;
			case FAST -> fastSpeed;
		};
	}

	public void sanitize() {
		slowSpeed = clamp(slowSpeed, 0.2, 40);
		normalSpeed = clamp(normalSpeed, 0.2, 40);
		fastSpeed = clamp(fastSpeed, 0.2, 40);
		reverseSpeed = clamp(reverseSpeed, 0.1, 20);
		acceleration = clamp(acceleration, 0.05, 20);
		braking = clamp(braking, 0.05, 40);
		waterDrag = clamp(waterDrag, 0.0, 5);
		maxTurnRate = clamp(maxTurnRate, 1, 90);
		minTurnFactor = clamp(minTurnFactor, 0, 1);
		helmRate = clamp(helmRate, 0.1, 20);
		helmReturnRate = clamp(helmReturnRate, 0.1, 20);
		turnResponse = clamp(turnResponse, 0.1, 20);
		turnSpeedLoss = clamp(turnSpeedLoss, 0, 2);
		aiWaypointRadius = clamp(aiWaypointRadius, 1, 64);
		aiStopRadius = clamp(aiStopRadius, 0.5, 16);
		aiLookahead = clamp(aiLookahead, 2, 64);
		aiProbeDistance = clamp(aiProbeDistance, 12, 96);
		aiDefaultWaitSeconds = (int) clamp(aiDefaultWaitSeconds, 0, 86400);
		aiStuckSeconds = (int) clamp(aiStuckSeconds, 2, 120);
		aiTurnAroundSpeed = clamp(aiTurnAroundSpeed, 0.1, 10);
		if (dive != null) {
			dive.sanitize();
		}
		if (flight != null) {
			flight.sanitize();
		}
	}

	private static double clamp(double v, double lo, double hi) {
		return Double.isNaN(v) ? lo : Math.max(lo, Math.min(hi, v));
	}
}
