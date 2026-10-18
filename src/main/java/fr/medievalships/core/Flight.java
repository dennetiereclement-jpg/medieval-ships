package fr.medievalships.core;

/**
 * Vertical side of an aircraft, on top of the horizontal {@link ShipPhysics}: no gravity while it
 * flies, a vertical speed that follows the climb / descent order with inertia, an altitude that
 * holds by itself, and the autopilot's altitude planning (terrain clearance, stops).
 */
public final class Flight {
	/** Vertical speed (blocks/s), positive = climbing. */
	public double vy;

	/** Ground (or building) top of a world column, +infinity when unknown (unloaded chunk). */
	@FunctionalInterface
	public interface Terrain {
		double groundTop(double x, double z);
	}

	/** Moves the vertical speed towards {@code desiredVy} (blocks/s) and returns the height change. */
	public double step(double desiredVy, FlightConfig f, double dt) {
		double a = f.verticalAcceleration * dt;
		vy += Math.max(-a, Math.min(a, desiredVy - vy));
		if (desiredVy == 0 && Math.abs(vy) < 0.01) {
			vy = 0;
		}
		return vy * dt;
	}

	/** Called when the climb or the descent is blocked: stop dead. */
	public void collide() {
		vy = 0;
	}

	/** Vertical speed order that brings the aircraft to {@code targetY} and holds it there. */
	public static double towards(double targetY, double y, FlightConfig f) {
		double e = targetY - y;
		if (Math.abs(e) < 0.04) {
			return 0;
		}
		// slow down early enough not to overshoot (v^2 = 2 a d), and gently in the last block
		double room = Math.sqrt(2 * f.verticalAcceleration * 0.8 * Math.abs(e));
		double v = Math.min(room, Math.abs(e) * 0.9);
		return e > 0 ? Math.min(f.climbSpeed, v) : -Math.min(f.descendSpeed, v);
	}

	/** Vertical order from the pilot's keys: +1 climb, -1 descend, 0 hold the altitude. */
	public static double manual(int input, FlightConfig f) {
		return input > 0 ? f.climbSpeed : input < 0 ? -f.descendSpeed : 0;
	}

	/**
	 * Highest ground under a corridor: from {@code back} behind to {@code ahead} in front of the
	 * aircraft along {@code yaw}, {@code halfWidth} on each side.
	 */
	public static double groundAlong(ShipPose pose, double yaw, double back, double ahead, double halfWidth, Terrain t) {
		double r = Math.toRadians(yaw);
		double fx = -Math.sin(r), fz = Math.cos(r);
		double sx = fz, sz = -fx;
		double top = Double.NEGATIVE_INFINITY;
		for (double d = -back; d <= ahead + 1e-6; d += 2.0) {
			for (double s = -halfWidth; s <= halfWidth + 1e-6; s += Math.max(1.0, halfWidth)) {
				top = Math.max(top, t.groundTop(pose.x() + fx * d + sx * s, pose.z() + fz * d + sz * s));
			}
		}
		return top;
	}

	/** Result of the autopilot's altitude planning. */
	public record Plan(double targetY, double requiredY) {
	}

	/**
	 * Altitude the autopilot flies at (origin Y): the altitude of the point it heads for (whose
	 * {@code y} is where the deck should be), but always {@code aiClearance} above the ground on the
	 * way, and only {@code aiLandingClearance} above it when coming down at a stop.
	 * {@code requiredY} is the lowest safe altitude ahead (the ship slows down until it is reached).
	 */
	public static Plan plan(Waypoint target, double distance, ShipPose pose, double speed, ShipGeometry g, FlightConfig f,
			Terrain t) {
		double keel = g.lowestY();
		double back = g.aiBack();
		double half = g.aiHalfWidth();
		double ahead = Math.max(16, g.aiReach() + 6 + Math.abs(speed) * 6);
		double desired = target.y - g.hull().mainDeckY;
		double groundAhead = groundAlong(pose, pose.yaw(), back, ahead, half, t);
		double required = groundAhead + f.aiClearance - keel;
		double y;
		if (target.isStop() && distance < f.aiApproachDistance) {
			// coming down at the stop: only the ground right under the aircraft and at the stop matters
			double here = groundAlong(pose, pose.yaw(), back, g.aiReach(), half, t);
			double minY = here + f.aiLandingClearance - keel;
			y = Math.max(desired, minY);
			required = minY;
		} else {
			y = Math.max(desired, required);
		}
		double cap = f.maxAltitude - g.topY();
		return new Plan(Math.min(y, cap), Math.min(required, cap));
	}

	/** Can the aircraft fly over this column (ground + clearance under the altitude ceiling)? */
	public static boolean flyable(double groundTop, ShipGeometry g, FlightConfig f) {
		return groundTop + f.aiClearance - g.lowestY() + g.topY() <= f.maxAltitude;
	}

	/** Orders of the airship's helmsman for one tick: helm and speed, and the vertical speed. */
	public record Orders(ShipPhysics.Controls controls, double desiredVy) {
	}

	/**
	 * Autopilot of an aircraft: the ship autopilot steers and sets the speed along the route (in
	 * plan view, the "navigable" columns being those it can fly over), this adds the altitude: it
	 * climbs over what lies ahead before going on (slowing down, or hovering while it climbs), comes
	 * down at the stops to their altitude, and while waiting there turns to the stop's heading.
	 */
	public static Orders autopilot(Autopilot ap, Route route, ShipPose pose, ShipPhysics physics, Gait gait, ShipConfig cfg,
			ShipGeometry g, Terrain t, Autopilot.Listener listener) {
		FlightConfig f = cfg.flight;
		Waypoint wp = ap.currentTarget(route);
		Plan plan = null;
		if (wp != null && ap.phase == Autopilot.Phase.SAILING) {
			double dist = Math.hypot(wp.x - pose.x(), wp.z - pose.z());
			plan = plan(wp, dist, pose, physics.speed, g, f, t);
			ap.altitudeError = plan.targetY() - pose.y();
		} else {
			ap.altitudeError = 0;
		}
		Autopilot.Navigator nav = (x, z) -> flyable(t.groundTop(x, z), g, f);
		ShipPhysics.Controls c = ap.tick(route, pose, physics.speed, physics.yawRate, gait, cfg, g, nav, listener);
		double vy;
		if (plan != null && ap.phase == Autopilot.Phase.SAILING) {
			vy = towards(plan.targetY(), pose.y(), f);
			double gap = plan.requiredY() - pose.y();
			if (gap > 2 && !Double.isNaN(c.targetSpeed())) {
				// something higher ahead: climb first (hover if it is much higher)
				double v = gap > 7 ? 0 : Math.max(0.0, c.targetSpeed() * (1 - (gap - 2) / 5));
				c = new ShipPhysics.Controls(Math.min(c.targetSpeed(), v), c.helmTarget());
			}
		} else if ((ap.phase == Autopilot.Phase.DOCKED || ap.phase == Autopilot.Phase.FINISHED) && wp != null) {
			vy = towards(wp.y - g.hull().mainDeckY, pose.y(), f);
			if (wp.yaw != null) {
				double err = ShipPose.wrapDegrees(wp.yaw - pose.yaw());
				double helm = Math.abs(err) < 1.5 ? 0 : Math.max(-1, Math.min(1, err / 25.0 - physics.yawRate * 0.05));
				c = new ShipPhysics.Controls(0.0, helm);
			}
		} else {
			vy = 0; // idle, finished, recovering: hold the altitude
		}
		return new Orders(c, vy);
	}

	/** Never climbs the top of the aircraft above the altitude ceiling. */
	public static double ceiling(double desiredVy, double y, ShipGeometry g, FlightConfig f) {
		double cap = f.maxAltitude - g.topY();
		if (desiredVy > 0 && y + desiredVy * 0.6 > cap) {
			return towards(cap, y, f);
		}
		return desiredVy;
	}

	/** Pose and collision flags after one flight tick. */
	public record Result(ShipPose pose, boolean forwardBlocked, boolean verticalBlocked) {
	}

	/**
	 * One tick of flight: horizontal motion (physics + collisions, as on water), then the vertical
	 * motion, refused if it would push the aircraft into an obstacle.
	 */
	public static Result tick(ShipGeometry g, ShipPose before, ShipPhysics physics, Flight flight, ShipPhysics.Controls controls,
			double desiredVy, ShipConfig cfg, ShipMover.Obstacles obstacles, double dt) {
		ShipPhysics.Step step = physics.step(controls, cfg, dt);
		ShipMover.Result moved = ShipMover.move(g, before, step.forward(), step.yaw(), 0, obstacles);
		physics.collide(moved.forwardBlocked(), moved.rotationBlocked());
		ShipPose pose = moved.pose();
		double dy = flight.step(ceiling(desiredVy, pose.y(), g, cfg.flight), cfg.flight, dt);
		boolean vBlocked = false;
		double cap = cfg.flight.maxAltitude - g.topY();
		if (dy > 0 && pose.y() + dy > cap) {
			dy = Math.max(0, cap - pose.y());
			flight.collide();
		}
		if (dy != 0) {
			ShipPose up = pose.moved(0, dy, 0, 0);
			int now = ShipMover.countCollisions(g, pose, obstacles);
			int then = ShipMover.countCollisions(g, up, obstacles);
			// never into an obstacle; already touching one (resting on the ground), only away from it
			if (then > now || (then > 0 && then == now && dy < 0)) {
				flight.collide();
				vBlocked = true;
			} else {
				pose = up;
			}
		}
		return new Result(pose, moved.forwardBlocked(), vBlocked);
	}
}
