package fr.medievalships.core;

/**
 * Vertical side of a submarine, on top of the horizontal {@link ShipPhysics}: on the surface it
 * floats like a ship; it dives and rises with the ballasts (a vertical speed that follows the
 * order with a lot of inertia), holds its depth by itself, never rises above its surfaced position
 * and never goes into the sea bed (vertical moves are refused like the horizontal ones).
 */
public final class Dive {
	/** Vertical speed (blocks/s), positive = rising. */
	public double vy;

	/** Within this distance of the surfaced position, the hull rides the surface like a ship. */
	public static final double SURFACED = 0.5;

	/** Moves the vertical speed towards {@code desiredVy} and returns the height change. */
	public double step(double desiredVy, DiveConfig f, double dt) {
		double a = f.verticalAcceleration * dt;
		vy += Math.max(-a, Math.min(a, desiredVy - vy));
		if (desiredVy == 0 && Math.abs(vy) < 0.01) {
			vy = 0;
		}
		return vy * dt;
	}

	/** The rise or the dive is blocked: stop dead. */
	public void collide() {
		vy = 0;
	}

	/** Vertical speed order that brings the hull to {@code targetY} and holds it there. */
	public static double towards(double targetY, double y, DiveConfig f) {
		double e = targetY - y;
		if (Math.abs(e) < 0.03) {
			return 0;
		}
		double room = Math.sqrt(2 * f.verticalAcceleration * 0.8 * Math.abs(e));
		double v = Math.min(room, Math.abs(e) * 0.9);
		return e > 0 ? Math.min(f.riseSpeed, v) : -Math.min(f.diveSpeed, v);
	}

	/** Order from the pilot's keys: +1 rise, -1 dive, 0 hold the depth (or ride the surface). */
	public static double manual(int input, double y, double surfacedY, DiveConfig f) {
		if (input > 0) {
			return f.riseSpeed;
		}
		if (input < 0) {
			return -f.diveSpeed;
		}
		return hold(y, surfacedY, f);
	}

	/** No order: on (or just under) the surface it rides the surface, below it holds its depth. */
	public static double hold(double y, double surfacedY, DiveConfig f) {
		if (Double.isNaN(surfacedY)) {
			return 0;
		}
		return surfacedY - y < SURFACED ? towards(surfacedY, y, f) : 0;
	}

	/** Depth of the hull below its surfaced position (0 on the surface). */
	public static double depth(double y, double surfacedY) {
		return Double.isNaN(surfacedY) ? 0 : Math.max(0, surfacedY - y);
	}

	/** Pose and collision flags after one tick. */
	public record Result(ShipPose pose, boolean forwardBlocked, boolean verticalBlocked) {
	}

	/**
	 * One tick: horizontal motion (physics + collisions, as on the surface), then the vertical
	 * motion, kept between the surfaced position and the deepest dive, and refused if it would push
	 * the hull into the sea bed or anything solid. {@code surfacedY} is the origin height at which
	 * the hull floats on the surface here (NaN: no water: it falls until something holds it).
	 */
	public static Result tick(ShipGeometry g, ShipPose before, ShipPhysics physics, Dive dive, ShipPhysics.Controls controls,
			double desiredVy, double surfacedY, ShipConfig cfg, ShipMover.Obstacles obstacles, double dt) {
		DiveConfig f = cfg.dive;
		ShipPhysics.Step step = physics.step(controls, cfg, dt);
		ShipMover.Result moved = ShipMover.move(g, before, step.forward(), step.yaw(), 0, obstacles);
		physics.collide(moved.forwardBlocked(), moved.rotationBlocked());
		ShipPose pose = moved.pose();
		double dy;
		if (Double.isNaN(surfacedY)) {
			// out of the water (drained, placed on land): fall like a stone
			dive.vy = Math.max(-6.0, dive.vy - 9.8 * dt);
			dy = dive.vy * dt;
		} else {
			double v = desiredVy;
			if (pose.y() > surfacedY + 0.02) {
				v = towards(surfacedY, pose.y(), f); // a wave went down, or rising too fast: back onto the surface
			} else if (v > 0) {
				v = Math.min(v, towards(surfacedY, pose.y(), f) + 0.05);
			} else if (v < 0 && surfacedY - pose.y() >= f.maxDepth) {
				v = 0;
			}
			dy = dive.step(v, f, dt);
			if (dy > 0 && pose.y() + dy > surfacedY && pose.y() <= surfacedY) {
				dy = surfacedY - pose.y();
			}
		}
		boolean vBlocked = false;
		if (dy != 0) {
			ShipPose moved2 = pose.moved(0, dy, 0, 0);
			int now = ShipMover.countCollisions(g, pose, obstacles);
			int then = ShipMover.countCollisions(g, moved2, obstacles);
			// never into the sea bed; already touching it (resting on the bottom), only away from it
			if (then > now || (then > 0 && then == now && dy < 0)) {
				dive.collide();
				vBlocked = true;
			} else {
				pose = moved2;
			}
		}
		return new Result(pose, moved.forwardBlocked(), vBlocked);
	}
}
