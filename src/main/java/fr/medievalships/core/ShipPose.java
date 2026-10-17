package fr.medievalships.core;

/**
 * Position (of the hull origin, on the waterline) and heading of a ship.
 * Yaw follows Minecraft conventions: degrees, 0 = facing south (+Z), 90 = facing west (-X).
 */
public record ShipPose(double x, double y, double z, double yaw) {
	public double cos() {
		return Math.cos(Math.toRadians(yaw));
	}

	public double sin() {
		return Math.sin(Math.toRadians(yaw));
	}

	public double worldX(double lx, double lz) {
		double r = Math.toRadians(yaw);
		return x + lx * Math.cos(r) - lz * Math.sin(r);
	}

	public double worldZ(double lx, double lz) {
		double r = Math.toRadians(yaw);
		return z + lx * Math.sin(r) + lz * Math.cos(r);
	}

	public double[] toWorld(double lx, double ly, double lz) {
		double c = cos(), s = sin();
		return new double[] {x + lx * c - lz * s, y + ly, z + lx * s + lz * c};
	}

	public double[] toLocal(double wx, double wy, double wz) {
		double c = cos(), s = sin();
		double dx = wx - x, dz = wz - z;
		return new double[] {dx * c + dz * s, wy - y, -dx * s + dz * c};
	}

	/** Rotates a world-space direction into ship-local space. */
	public double[] dirToLocal(double dx, double dy, double dz) {
		double c = cos(), s = sin();
		return new double[] {dx * c + dz * s, dy, -dx * s + dz * c};
	}

	public double[] dirToWorld(double lx, double ly, double lz) {
		double c = cos(), s = sin();
		return new double[] {lx * c - lz * s, ly, lx * s + lz * c};
	}

	/** Forward unit vector (x, z). */
	public double forwardX() {
		return -sin();
	}

	public double forwardZ() {
		return cos();
	}

	public ShipPose moved(double dx, double dy, double dz, double dyaw) {
		return new ShipPose(x + dx, y + dy, z + dz, yaw + dyaw);
	}

	/** Moves a world point rigidly with the ship from this pose to {@code next}. */
	public double[] carry(ShipPose next, double wx, double wy, double wz) {
		double[] local = toLocal(wx, wy, wz);
		return next.toWorld(local[0], local[1], local[2]);
	}

	public static double wrapDegrees(double deg) {
		double d = deg % 360.0;
		if (d >= 180.0) {
			d -= 360.0;
		}
		if (d < -180.0) {
			d += 360.0;
		}
		return d;
	}

	/** Yaw (Minecraft convention) of a horizontal direction. */
	public static double yawOf(double dx, double dz) {
		return Math.toDegrees(Math.atan2(-dx, dz));
	}
}
