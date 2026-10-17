package fr.medievalships.core;

/**
 * Moves a hull while respecting obstacles. The hull is sampled by {@link ShipGeometry#PROBES};
 * a move is accepted when no probe ends up inside an obstacle. When the hull is already
 * overlapping something (spawned badly, pushed by another mod...), moves that do not make the
 * overlap worse are allowed so the ship can always work itself free.
 */
public final class ShipMover {
	private ShipMover() {
	}

	@FunctionalInterface
	public interface Obstacles {
		/** True if the world point is inside a solid obstacle (terrain, quay, another hull...). */
		boolean blocked(double wx, double wy, double wz);
	}

	public record Result(ShipPose pose, boolean forwardBlocked, boolean rotationBlocked, int collisions) {
	}

	public static int countCollisions(ShipGeometry geometry, ShipPose pose, Obstacles obstacles) {
		int n = 0;
		double c = pose.cos(), s = pose.sin();
		for (double[] p : geometry.probes()) {
			double wx = pose.x() + p[0] * c - p[2] * s;
			double wz = pose.z() + p[0] * s + p[2] * c;
			if (obstacles.blocked(wx, pose.y() + p[1], wz)) {
				n++;
			}
		}
		return n;
	}

	public static Result move(ShipGeometry geometry, ShipPose from, double forward, double dyaw, double dy, Obstacles obstacles) {
		double midYaw = Math.toRadians(from.yaw() + dyaw / 2);
		double dx = -Math.sin(midYaw) * forward;
		double dz = Math.cos(midYaw) * forward;
		boolean moving = Math.abs(forward) > 1e-6;
		boolean turning = Math.abs(dyaw) > 1e-6;
		if (!moving && !turning) {
			return new Result(from.moved(0, dy, 0, 0), false, false, 0);
		}
		int c0 = countCollisions(geometry, from, obstacles);

		double[][] candidates = {
				{dx, dz, dyaw},
				{dx, dz, 0},
				{0, 0, dyaw},
				{dx, 0, 0},
				{0, dz, 0},
		};
		int bestIndex = -1;
		int bestCount = Integer.MAX_VALUE;
		for (int i = 0; i < candidates.length; i++) {
			double[] m = candidates[i];
			boolean hasMove = Math.abs(m[0]) + Math.abs(m[1]) > 1e-6 || Math.abs(m[2]) > 1e-6;
			if (!hasMove) {
				continue;
			}
			if (i >= 3 && Math.abs(m[0]) + Math.abs(m[1]) < Math.abs(forward) * 0.25) {
				continue; // sliding along an obstacle only when it keeps a useful part of the motion
			}
			int c = countCollisions(geometry, from.moved(m[0], 0, m[1], m[2]), obstacles);
			if (c0 == 0) {
				if (c == 0) {
					bestIndex = i;
					bestCount = 0;
					break;
				}
			} else if (c <= c0 && c < bestCount && (c < c0
					|| countCollisions(geometry, from.moved(m[0] * 3, 0, m[1] * 3, m[2] * 3), obstacles) <= c0)) {
				// already overlapping: only accept moves that do not dig further in
				bestIndex = i;
				bestCount = c;
				if (c == 0) {
					break;
				}
			}
		}
		if (bestIndex < 0) {
			return new Result(from.moved(0, dy, 0, 0), moving, turning, c0);
		}
		double[] m = candidates[bestIndex];
		boolean fwdBlocked = moving && (bestIndex == 2 || bestIndex >= 3);
		boolean rotBlocked = turning && bestIndex != 0 && bestIndex != 2;
		return new Result(from.moved(m[0], dy, m[1], m[2]), fwdBlocked, rotBlocked, bestCount);
	}
}
