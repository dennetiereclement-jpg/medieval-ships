package fr.medievalships.core;

/**
 * NPC helmsman. Follows administrator-defined waypoints with pure-pursuit steering,
 * anticipates turns, slows down before stops, waits at ports, avoids obstacles detected by
 * short local probes (no ocean-wide path finding) and backs off when stuck.
 *
 * <p>Runs on the server only; its state is saved with the ship.
 */
public final class Autopilot {
	public enum Phase { IDLE, SAILING, DOCKED, RECOVERING, FINISHED }

	/** Answers whether a world column (x, z) is open water the hull can sail through. */
	@FunctionalInterface
	public interface Navigator {
		boolean navigable(double x, double z);
	}

	/** Receives the events the ship turns into chat / action bar messages. */
	public interface Listener {
		default void departing(Waypoint from, Waypoint next, int nextIndex) {
		}

		default void arrived(Waypoint stop, int index) {
		}

		default void countdown(int secondsLeft, Waypoint nextStop) {
		}

		default void stuck() {
		}

		default void finished() {
		}
	}

	private static final int PROBE_INTERVAL = 5;
	private static final double[] AVOID_STEPS = {15, 30, 45, 60, 80, 100};
	private static final double HULL_REACH = 10.6;
	private static final double HULL_HALF_WIDTH = 2.4;
	/** Without getting 2 blocks closer to its target for this long, the helmsman gives up on it. */
	private static final int STALL_SECONDS = 50;
	/** Probe evaluations (every {@link #PROBE_INTERVAL} ticks) before giving up on the chosen side. */
	private static final int SIDE_SWITCH_EVALUATIONS = 24;

	// ---- persistent state
	public int target;
	public int direction = 1;
	public Phase phase = Phase.IDLE;
	public int waitTicks;
	public double legStartX;
	public double legStartZ;
	public int failures;
	public int recoverTicks;

	// ---- transient state
	private double avoidOffset;
	private int probeCooldown;
	private double clearance = Double.MAX_VALUE;
	private double progressX = Double.NaN;
	private double progressZ;
	private int progressTicks;
	private double lastError;
	private boolean stuckReported;
	private double bestDist = Double.MAX_VALUE;
	private int stallTicks;
	private int blockedEvaluations;

	/** Starts (or restarts) the route from the ship's current position. */
	public void start(Route route, ShipPose pose, ShipConfig cfg) {
		failures = 0;
		recoverTicks = 0;
		avoidOffset = 0;
		stuckReported = false;
		progressX = Double.NaN;
		resetProgress();
		if (route == null || route.size() == 0) {
			phase = Phase.IDLE;
			return;
		}
		int nearest = 0;
		double best = Double.MAX_VALUE;
		for (int i = 0; i < route.size(); i++) {
			Waypoint w = route.get(i);
			double d = Math.hypot(w.x - pose.x(), w.z - pose.z());
			if (d < best) {
				best = d;
				nearest = i;
			}
		}
		target = nearest;
		direction = route.mode == Route.Mode.PINGPONG && nearest == route.size() - 1 && route.size() > 1 ? -1 : 1;
		legStartX = pose.x();
		legStartZ = pose.z();
		Waypoint w = route.get(nearest);
		if (w.isStop() && best < 16.0) {
			phase = Phase.DOCKED;
			waitTicks = w.waitSeconds * 20;
		} else {
			phase = Phase.SAILING;
		}
	}

	private void resetProgress() {
		bestDist = Double.MAX_VALUE;
		stallTicks = 0;
	}

	public void stop() {
		phase = Phase.IDLE;
	}

	/** Skips the remaining waiting time at a stop. */
	public void departNow() {
		if (phase == Phase.DOCKED) {
			waitTicks = 0;
		}
	}

	/** Index after {@code i} in travel direction {@code dir}; returns {index, dir} or null at the end of a ONCE route. */
	public static int[] next(Route route, int i, int dir) {
		int n = route.size();
		if (n <= 1) {
			return null;
		}
		int j = i + dir;
		if (j >= 0 && j < n) {
			return new int[] {j, dir};
		}
		return switch (route.mode) {
			case ONCE -> null;
			case LOOP -> new int[] {Math.floorMod(j, n), dir};
			case PINGPONG -> new int[] {i - dir, -dir};
		};
	}

	public Waypoint currentTarget(Route route) {
		return route == null || route.size() == 0 ? null : route.get(target);
	}

	public ShipPhysics.Controls tick(Route route, ShipPose pose, double speed, double yawRate, Gait cruise,
									 ShipConfig cfg, Navigator nav, Listener listener) {
		if (route == null || route.size() == 0) {
			phase = Phase.IDLE;
		}
		if (target >= (route == null ? 0 : route.size())) {
			target = 0;
		}
		switch (phase) {
			case IDLE, FINISHED:
				return new ShipPhysics.Controls(0.0, 0.0);
			case DOCKED:
				return docked(route, cfg, listener);
			case RECOVERING:
				return recovering(cfg);
			default:
				return sailing(route, pose, speed, yawRate, cruise, cfg, nav, listener);
		}
	}

	private ShipPhysics.Controls docked(Route route, ShipConfig cfg, Listener listener) {
		Waypoint here = route.get(target);
		int[] nx = next(route, target, direction);
		if (nx == null) {
			phase = Phase.FINISHED;
			listener.finished();
			return new ShipPhysics.Controls(0.0, 0.0);
		}
		if (waitTicks > 0) {
			waitTicks--;
			if (waitTicks % 20 == 0) {
				int s = waitTicks / 20;
				if (s == 60 || s == 30 || s == 10 || (s <= 5 && s > 0)) {
					listener.countdown(s, nextStop(route, nx[0], nx[1]));
				}
			}
			return new ShipPhysics.Controls(0.0, 0.0);
		}
		legStartX = here.x;
		legStartZ = here.z;
		target = nx[0];
		direction = nx[1];
		phase = Phase.SAILING;
		progressX = Double.NaN;
		resetProgress();
		listener.departing(here, route.get(target), target);
		return new ShipPhysics.Controls(0.0, 0.0);
	}

	private ShipPhysics.Controls recovering(ShipConfig cfg) {
		recoverTicks--;
		if (recoverTicks <= 0) {
			if (failures > 6) {
				failures = 3;
			}
			phase = Phase.SAILING;
			progressX = Double.NaN;
			probeCooldown = 0;
			return new ShipPhysics.Controls(0.0, 0.0);
		}
		if (failures > 6) {
			// give up for a while instead of grinding against the coast
			return new ShipPhysics.Controls(0.0, 0.0);
		}
		double helm = lastError >= 0 ? -1 : 1;
		return new ShipPhysics.Controls(-cfg.reverseSpeed * 0.8, helm);
	}

	/** First stop reachable from index i going in direction dir (or the route end). */
	private static Waypoint nextStop(Route route, int i, int dir) {
		int idx = i, d = dir;
		for (int guard = 0; guard < route.size() * 2; guard++) {
			Waypoint w = route.get(idx);
			if (w.isStop()) {
				return w;
			}
			int[] nx = next(route, idx, d);
			if (nx == null) {
				return w;
			}
			idx = nx[0];
			d = nx[1];
		}
		return route.get(i);
	}

	private ShipPhysics.Controls sailing(Route route, ShipPose pose, double speed, double yawRate, Gait cruise,
										 ShipConfig cfg, Navigator nav, Listener listener) {
		Waypoint tgt = route.get(target);
		double dist = Math.hypot(tgt.x - pose.x(), tgt.z - pose.z());
		int[] nx = next(route, target, direction);

		// ---- waypoint transitions
		if (tgt.isStop() || nx == null) {
			if (dist < cfg.aiStopRadius && Math.abs(speed) < 0.7) {
				if (nx == null && !tgt.isStop()) {
					phase = Phase.FINISHED;
					listener.finished();
					return new ShipPhysics.Controls(0.0, 0.0);
				}
				phase = Phase.DOCKED;
				waitTicks = Math.max(1, tgt.waitSeconds) * 20;
				failures = 0;
				listener.arrived(tgt, target);
				return new ShipPhysics.Controls(0.0, 0.0);
			}
		} else {
			double lx = tgt.x - legStartX, lz = tgt.z - legStartZ;
			boolean passed = (pose.x() - tgt.x) * lx + (pose.z() - tgt.z) * lz > 0 && dist < cfg.aiWaypointRadius * 3;
			if (dist < cfg.aiWaypointRadius || passed) {
				legStartX = tgt.x;
				legStartZ = tgt.z;
				target = nx[0];
				direction = nx[1];
				resetProgress();
				return sailing(route, pose, speed, yawRate, cruise, cfg, nav, listener);
			}
		}

		// ---- progress towards the target: local avoidance cannot solve every coastline
		if (dist < bestDist - 2.0) {
			bestDist = dist;
			stallTicks = 0;
		} else if (++stallTicks > STALL_SECONDS * 20) {
			resetProgress();
			if (!tgt.isStop() && nx != null) {
				// unreachable intermediate point (inside land, behind a closed bay...): skip it
				legStartX = pose.x();
				legStartZ = pose.z();
				target = nx[0];
				direction = nx[1];
				return new ShipPhysics.Controls(0.0, 0.0);
			}
			if (!stuckReported) {
				stuckReported = true;
				listener.stuck();
			}
			phase = Phase.RECOVERING;
			failures = 7;
			recoverTicks = 600;
			return new ShipPhysics.Controls(0.0, 0.0);
		}

		// ---- pure pursuit on the current leg, spilling over onto the next one to anticipate turns
		double ax = tgt.x, az = tgt.z;
		double legX = tgt.x - legStartX, legZ = tgt.z - legStartZ;
		double legLen = Math.hypot(legX, legZ);
		if (legLen > 1e-3) {
			double ux = legX / legLen, uz = legZ / legLen;
			double t = (pose.x() - legStartX) * ux + (pose.z() - legStartZ) * uz;
			double look = t + cfg.aiLookahead;
			if (look < legLen) {
				ax = legStartX + ux * look;
				az = legStartZ + uz * look;
			} else if (!tgt.isStop() && nx != null) {
				Waypoint n2 = route.get(nx[0]);
				double over = look - legLen;
				double l2x = n2.x - tgt.x, l2z = n2.z - tgt.z;
				double l2 = Math.hypot(l2x, l2z);
				if (l2 > 1e-3) {
					over = Math.min(over, l2);
					ax = tgt.x + l2x / l2 * over;
					az = tgt.z + l2z / l2 * over;
				}
			}
		}
		double desiredYaw = ShipPose.yawOf(ax - pose.x(), az - pose.z());

		// ---- local obstacle avoidance
		double probe = Math.max(cfg.aiProbeDistance, 16 + 5 * Math.abs(speed));
		double need = Math.min(probe, dist + HULL_REACH);
		boolean approachingStop = tgt.isStop() && dist < 18;
		if (--probeCooldown <= 0) {
			probeCooldown = PROBE_INTERVAL;
			if (approachingStop) {
				avoidOffset = 0;
				clearance = Double.MAX_VALUE;
			} else {
				chooseAvoidance(pose, desiredYaw, need, nav);
			}
		}
		double heading = desiredYaw + avoidOffset;
		double err = ShipPose.wrapDegrees(heading - pose.yaw());
		lastError = err;
		double helm = clamp(err / 22.0 - yawRate * 0.045, -1, 1);

		// ---- speed planning
		Gait gait = cruise;
		if (tgt.gait != null && Gait.byName(tgt.gait) != null) {
			gait = Gait.byName(tgt.gait);
		}
		double v = cfg.gaitSpeed(gait);
		double dStop = distanceToNextStop(route, pose, dist);
		if (!Double.isNaN(dStop)) {
			double room = Math.max(0, dStop - cfg.aiStopRadius * 0.5);
			v = Math.min(v, Math.max(dStop < cfg.aiStopRadius ? 0.0 : 0.5, Math.sqrt(2 * 0.45 * cfg.braking * room)));
		}
		if (!tgt.isStop() && nx != null && dist < 30) {
			Waypoint n2 = route.get(nx[0]);
			double a1 = ShipPose.yawOf(tgt.x - legStartX, tgt.z - legStartZ);
			double a2 = ShipPose.yawOf(n2.x - tgt.x, n2.z - tgt.z);
			double turn = Math.abs(ShipPose.wrapDegrees(a2 - a1));
			double f = 1 - 0.6 * (turn / 180.0) * (1 - dist / 30.0);
			v = Math.min(v, Math.max(cfg.slowSpeed, cfg.gaitSpeed(gait) * f));
		}
		double absErr = Math.abs(err);
		if (absErr > 100) {
			v = Math.min(v, 0.4);
		} else if (absErr > 40) {
			v = Math.min(v, Math.max(0.8, v * (1 - absErr / 120)));
		}
		if (clearance < need) {
			double free = clearance - HULL_REACH;
			v = Math.min(v, Math.max(0.0, free / 12.0 * v));
		}

		// ---- stuck detection
		if (Double.isNaN(progressX)) {
			progressX = pose.x();
			progressZ = pose.z();
			progressTicks = 0;
		} else if (++progressTicks >= cfg.aiStuckSeconds * 20) {
			double moved = Math.hypot(pose.x() - progressX, pose.z() - progressZ);
			progressX = pose.x();
			progressZ = pose.z();
			progressTicks = 0;
			if (moved < 1.0 && v > 0.3) {
				failures++;
				phase = Phase.RECOVERING;
				recoverTicks = failures > 6 ? 600 : 50;
				if (failures % 3 == 0) {
					// repeated failures on the same side: try the other way around
					avoidOffset = -avoidOffset;
					blockedEvaluations = 0;
				}
				if (failures > 6 && !stuckReported) {
					stuckReported = true;
					listener.stuck();
				}
				return new ShipPhysics.Controls(0.0, 0.0);
			} else if (moved >= 1.0) {
				failures = Math.max(0, failures - 1);
				stuckReported = false;
			}
		}
		return new ShipPhysics.Controls(v, helm);
	}

	private double distanceToNextStop(Route route, ShipPose pose, double distToTarget) {
		double acc = distToTarget;
		int idx = target, dir = direction;
		for (int guard = 0; guard < route.size() + 1; guard++) {
			Waypoint w = route.get(idx);
			if (w.isStop()) {
				return acc;
			}
			int[] nx = next(route, idx, dir);
			if (nx == null) {
				return acc; // end of a ONCE route: stop there
			}
			Waypoint n = route.get(nx[0]);
			acc += Math.hypot(n.x - w.x, n.z - w.z);
			if (acc > 200) {
				return Double.NaN;
			}
			idx = nx[0];
			dir = nx[1];
		}
		return Double.NaN;
	}

	private void chooseAvoidance(ShipPose pose, double desiredYaw, double need, Navigator nav) {
		double straight = clearanceAlong(pose, desiredYaw, need, nav);
		if (straight >= need) {
			avoidOffset = 0;
			blockedEvaluations = 0;
			clearance = straight;
			return;
		}
		// pick a side once, then stick to it: hesitating between two ways around an
		// obstacle is what drives a ship into it
		double side;
		if (avoidOffset == 0) {
			double[] port = firstClear(pose, desiredYaw, need, nav, -1);
			double[] starboard = firstClear(pose, desiredYaw, need, nav, 1);
			if (port[0] != starboard[0]) {
				side = port[0] < starboard[0] ? -1 : 1;
			} else {
				side = port[1] >= starboard[1] ? -1 : 1;
			}
		} else {
			side = Math.signum(avoidOffset);
		}
		double[] best = firstClear(pose, desiredYaw, need, nav, side);
		if (best[1] < need) {
			// switch sides only after this side has stayed blocked for a while
			if (++blockedEvaluations >= SIDE_SWITCH_EVALUATIONS) {
				double[] other = firstClear(pose, desiredYaw, need, nav, -side);
				if (other[1] >= need) {
					best = other;
					side = -side;
					blockedEvaluations = 0;
				}
			}
		} else {
			blockedEvaluations = 0;
		}
		avoidOffset = best[0] * side;
		clearance = Math.max(best[1], straight);
	}

	/** {offset, clearance} of the smallest deviation on one side that is clear (or the best one found). */
	private static double[] firstClear(ShipPose pose, double desiredYaw, double need, Navigator nav, double side) {
		double bestOff = AVOID_STEPS[AVOID_STEPS.length - 1], bestClear = -1;
		for (double off : AVOID_STEPS) {
			double c = clearanceAlong(pose, desiredYaw + off * side, need, nav);
			if (c >= need) {
				return new double[] {off, c};
			}
			if (c > bestClear) {
				bestClear = c;
				bestOff = off;
			}
		}
		return new double[] {bestOff, bestClear};
	}

	/** Free distance from the hull centre along a heading, checking the centre line and both sides. */
	static double clearanceAlong(ShipPose pose, double yaw, double need, Navigator nav) {
		double r = Math.toRadians(yaw);
		double fx = -Math.sin(r), fz = Math.cos(r);
		double sx = fz, sz = -fx; // lateral
		for (double d = 4; d <= need; d += 2) {
			double cx = pose.x() + fx * d, cz = pose.z() + fz * d;
			if (!nav.navigable(cx, cz)
					|| !nav.navigable(cx + sx * HULL_HALF_WIDTH, cz + sz * HULL_HALF_WIDTH)
					|| !nav.navigable(cx - sx * HULL_HALF_WIDTH, cz - sz * HULL_HALF_WIDTH)) {
				return d;
			}
		}
		return need;
	}

	public double avoidOffset() {
		return avoidOffset;
	}

	private static double clamp(double v, double lo, double hi) {
		return Math.max(lo, Math.min(hi, v));
	}
}
