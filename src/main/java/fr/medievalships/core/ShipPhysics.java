package fr.medievalships.core;

/**
 * Server-side navigation model: progressive acceleration, inertia (coasting),
 * helm with progressive return, rotational inertia and speed loss in turns.
 * All quantities use blocks, seconds and degrees.
 */
public final class ShipPhysics {
	/** Forward speed (blocks/s), negative when going astern. */
	public double speed;
	/** Yaw rate (degrees/s), positive = turning to starboard (right). */
	public double yawRate;
	/** Helm position in [-1, 1], positive = starboard. */
	public double helm;

	/**
	 * Controls for one tick.
	 *
	 * @param targetSpeed desired speed in blocks/s, or {@link Double#NaN} to coast (no oars)
	 * @param helmTarget  desired helm in [-1, 1]; 0 lets the helm return to the centre
	 */
	public record Controls(double targetSpeed, double helmTarget) {
		public static final Controls COAST = new Controls(Double.NaN, 0.0);
	}

	public record Step(double forward, double yaw) {
	}

	public Step step(Controls controls, ShipConfig cfg, double dt) {
		// --- speed
		double target = controls.targetSpeed();
		if (Double.isNaN(target)) {
			speed *= Math.exp(-cfg.waterDrag * dt);
			if (Math.abs(speed) < 0.02) {
				speed = 0;
			}
		} else if (target > speed) {
			double rate = speed < 0 ? cfg.braking : cfg.acceleration;
			speed = Math.min(target, speed + rate * dt);
		} else if (target < speed) {
			double rate = speed > 0 ? cfg.braking : cfg.acceleration;
			// a ship above its gait limit slows down gently (coasting), it does not slam the brakes
			if (target > 0) {
				rate = Math.max(cfg.acceleration, speed * cfg.waterDrag * 2);
			}
			speed = Math.max(target, speed - rate * dt);
		}

		// --- helm
		double ht = Math.max(-1, Math.min(1, controls.helmTarget()));
		double rate = Math.abs(ht) < 1e-3 ? cfg.helmReturnRate : cfg.helmRate;
		if (helm < ht) {
			helm = Math.min(ht, helm + rate * dt);
		} else if (helm > ht) {
			helm = Math.max(ht, helm - rate * dt);
		}

		// --- yaw
		double speedFactor = Math.min(1.0, Math.abs(speed) / Math.max(0.1, cfg.normalSpeed));
		double effectiveness = cfg.minTurnFactor + (1 - cfg.minTurnFactor) * speedFactor;
		double direction = speed < -0.05 ? -1 : 1;
		double targetRate = helm * cfg.maxTurnRate * effectiveness * direction;
		yawRate += (targetRate - yawRate) * (1 - Math.exp(-cfg.turnResponse * dt));
		if (Math.abs(yawRate) < 1e-3 && Math.abs(helm) < 1e-3) {
			yawRate = 0;
		}

		// --- turning costs speed
		double turnShare = Math.min(1.0, Math.abs(yawRate) / cfg.maxTurnRate);
		speed *= 1 - cfg.turnSpeedLoss * turnShare * dt;

		return new Step(speed * dt, yawRate * dt);
	}

	/** Called when the hull hits something: stop dead with a small rebound. */
	public void collide(boolean forwardBlocked, boolean rotationBlocked) {
		if (forwardBlocked) {
			speed = -speed * 0.15;
		}
		if (rotationBlocked) {
			yawRate = 0;
		}
	}
}
