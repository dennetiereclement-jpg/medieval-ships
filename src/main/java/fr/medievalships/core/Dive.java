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

	// ------------------------------------------------------------------ autopilot

	/** The sea around a submarine, for its autopilot. */
	public interface Sea {
		/** World height of the water surface in this column, NaN without open water (land, ice, unloaded). */
		double surface(double x, double z);

		/** World height of the top of the sea bed in this column (the first solid block under the surface). */
		double bed(double x, double z);
	}

	/**
	 * Can the submarine pass over this column at all: water deep enough for the hull to float on the
	 * surface with {@code aiClearance} under its keel? (Shallower water, reefs, land: it goes round.)
	 */
	public static boolean navigable(Sea sea, double x, double z, ShipGeometry g, DiveConfig f) {
		double s = sea.surface(x, z);
		if (Double.isNaN(s)) {
			return false;
		}
		return s - g.hull().waterlineY >= sea.bed(x, z) + f.aiClearance - g.lowestY();
	}

	/** Depth the autopilot keeps on the leg towards {@code wp} (0 = on the surface). */
	public static double legDepth(Waypoint wp, double distance, DiveConfig f) {
		if (wp.depth != null) {
			return Math.max(0, Math.min(f.maxDepth, wp.depth));
		}
		if (wp.isStop() && distance < f.aiApproachDistance) {
			return 0; // comes up at the stops
		}
		return Math.min(f.maxDepth, f.aiCruiseDepth);
	}

	/**
	 * Highest sea bed under a corridor: from {@code back} behind to {@code ahead} in front of the hull
	 * along {@code yaw}, {@code halfWidth} on each side (columns without water are skipped: the
	 * horizontal autopilot keeps away from them).
	 */
	public static double bedAlong(ShipPose pose, double yaw, double back, double ahead, double halfWidth, Sea sea) {
		double r = Math.toRadians(yaw);
		double fx = -Math.sin(r), fz = Math.cos(r);
		double sx = fz, sz = -fx;
		double top = Double.NEGATIVE_INFINITY;
		for (double d = -back; d <= ahead + 1e-6; d += 2.0) {
			for (double s = -halfWidth; s <= halfWidth + 1e-6; s += Math.max(1.0, halfWidth)) {
				double x = pose.x() + fx * d + sx * s, z = pose.z() + fz * d + sz * s;
				if (!Double.isNaN(sea.surface(x, z))) {
					top = Math.max(top, sea.bed(x, z));
				}
			}
		}
		return top;
	}

	/** Height (origin Y) the autopilot sails at, and the lowest safe height over the sea bed ahead. */
	public record Plan(double targetY, double requiredY) {
	}

	/**
	 * The autopilot's depth: the leg's depth below the surface here, but always {@code aiClearance}
	 * over the highest sea bed on the way (it rises over a ridge before reaching it) and never above
	 * the surface.
	 */
	public static Plan plan(Waypoint target, double distance, ShipPose pose, double speed, double surfacedY, ShipGeometry g, DiveConfig f,
			Sea sea) {
		double ahead = Math.max(16, g.aiReach() + 6 + Math.abs(speed) * 6);
		double bed = bedAlong(pose, pose.yaw(), g.aiBack(), ahead, g.aiHalfWidth(), sea);
		double required = bed + f.aiClearance - g.lowestY();
		double depth = legDepth(target, distance, f);
		double y = depth < SURFACED ? surfacedY : surfacedY - depth;
		y = Math.min(Math.max(y, required), surfacedY);
		return new Plan(y, Math.min(required, surfacedY));
	}

	/** Orders of the submarine's helmsman for one tick: helm and speed, and the vertical speed. */
	public record Orders(ShipPhysics.Controls controls, double desiredVy) {
	}

	/**
	 * Autopilot of a submarine: the ship autopilot steers and sets the speed along the route (the
	 * navigable columns being those deep enough for the hull, so it goes round shoals, reefs and
	 * passages too narrow or too shallow), this adds the depth: the depth of each leg, rising over
	 * the sea bed ahead (slowing down, or stopping while it rises), surfacing at the stops.
	 */
	public static Orders autopilot(Autopilot ap, Route route, ShipPose pose, ShipPhysics physics, Gait gait, ShipConfig cfg, ShipGeometry g,
			Sea sea, double surfacedY, Autopilot.Listener listener) {
		DiveConfig f = cfg.dive;
		Waypoint wp = ap.currentTarget(route);
		Plan plan = null;
		if (wp != null && ap.phase == Autopilot.Phase.SAILING && !Double.isNaN(surfacedY)) {
			double dist = Math.hypot(wp.x - pose.x(), wp.z - pose.z());
			plan = plan(wp, dist, pose, physics.speed, surfacedY, g, f, sea);
			// at a stop it docks only once at the stop's depth
			ap.altitudeError = wp.isStop() ? plan.targetY() - pose.y() : 0;
		} else {
			ap.altitudeError = 0;
		}
		Autopilot.Navigator nav = (x, z) -> navigable(sea, x, z, g, f);
		ShipPhysics.Controls c = ap.tick(route, pose, physics.speed, physics.yawRate, gait, cfg, g, nav, listener);
		double vy;
		if (plan != null && ap.phase == Autopilot.Phase.SAILING) {
			vy = towards(plan.targetY(), pose.y(), f);
			double gap = plan.requiredY() - pose.y();
			if (gap > 1.5 && !Double.isNaN(c.targetSpeed())) {
				// the sea bed rises ahead: come up first (stop if it is much higher)
				double v = gap > 6 ? 0 : Math.max(0.0, c.targetSpeed() * (1 - (gap - 1.5) / 4.5));
				c = new ShipPhysics.Controls(Math.min(c.targetSpeed(), v), c.helmTarget());
			}
		} else if ((ap.phase == Autopilot.Phase.DOCKED || ap.phase == Autopilot.Phase.FINISHED) && wp != null && !Double.isNaN(surfacedY)) {
			double depth = wp.depth == null ? 0 : Math.min(f.maxDepth, wp.depth);
			vy = towards(depth < SURFACED ? surfacedY : surfacedY - depth, pose.y(), f);
		} else {
			vy = hold(pose.y(), surfacedY, f);
		}
		return new Orders(c, vy);
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
