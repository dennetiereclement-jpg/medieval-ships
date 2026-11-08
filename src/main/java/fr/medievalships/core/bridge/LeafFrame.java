package fr.medievalships.core.bridge;

/**
 * The frame of one leaf (vantail) of a bascule drawbridge: its hinge line and the direction it swings in. Pure
 * geometry, shared by the server (collisions, safety checks), the clients (drawing, collisions) and the tests.
 *
 * <p>World coordinates throughout. The hinge line passes through {@code (hx, hy, hz)} and runs along the unit
 * vector {@code u = (ux, 0, uz)}, which is the direction of the waterway (the leaves pivot about axes parallel to
 * the channel, their free ends rising over the water). {@code v = (vx, 0, vz)} is the unit vector perpendicular to
 * {@code u}, pointing from the hinge towards the middle of the channel (inward, along the span of the bridge).
 *
 * <p>Leaf-local coordinates of a world point: {@code a} along the hinge ({@code u}), {@code b} inward ({@code v}),
 * {@code c} up. The leaf raised by {@code angle} degrees (0 = closed, horizontal; positive = raised, its free end
 * going up over the channel) maps a local point to
 * <pre>
 *   world = H + a u + (b cos θ - c sin θ) v + (b sin θ + c cos θ) up
 * </pre>
 * which is the rotation about the axis {@code n = v × up = (-vz, 0, vx)} by {@code θ} (what the renderer applies
 * with {@code RotationAxis.of(n).rotationDegrees(θ)} after translating to the hinge).
 */
public record LeafFrame(double hx, double hy, double hz, double ux, double uz, double vx, double vz) {

	/**
	 * A frame from a hinge point, the channel direction (any horizontal vector along the water) and the side the
	 * channel is on: {@code inwardX, inwardZ} is any horizontal vector from the hinge towards the channel (only its
	 * component perpendicular to the channel direction is kept).
	 */
	public static LeafFrame of(double hx, double hy, double hz, double dirX, double dirZ, double inwardX, double inwardZ) {
		double len = Math.hypot(dirX, dirZ);
		if (len < 1e-9) {
			throw new IllegalArgumentException("channel direction must not be zero");
		}
		double ux = dirX / len, uz = dirZ / len;
		// the perpendicular on the channel's side
		double px = -uz, pz = ux;
		if (px * inwardX + pz * inwardZ < 0) {
			px = -px;
			pz = -pz;
		}
		if (Math.abs(px * inwardX + pz * inwardZ) < 1e-9) {
			throw new IllegalArgumentException("the inward direction must not be along the channel");
		}
		return new LeafFrame(hx, hy, hz, ux, uz, px, pz);
	}

	/** Leaf-local coordinates {a (along the hinge), b (inward), c (up)} of a world point. */
	public double[] toLocal(double x, double y, double z) {
		double dx = x - hx, dz = z - hz;
		return new double[] {dx * ux + dz * uz, dx * vx + dz * vz, y - hy};
	}

	/** World point of a leaf-local point with the leaf raised by {@code angleDeg}. */
	public double[] toWorld(double a, double b, double c, double angleDeg) {
		double r = Math.toRadians(angleDeg), cos = Math.cos(r), sin = Math.sin(r);
		double bb = b * cos - c * sin, cc = b * sin + c * cos;
		return new double[] {hx + a * ux + bb * vx, hy + cc, hz + a * uz + bb * vz};
	}

	/** The axis the renderer rotates about (a unit vector), see the class doc: {@code v × up}. */
	public double[] rotationAxis() {
		return new double[] {-vz, 0, vx};
	}

	/**
	 * World axis-aligned box covering a leaf-local box ({@code a0..a1, b0..b1, c0..c1}) raised by {@code angleDeg}:
	 * the eight corners are rotated and enclosed (conservative; exact at 0 and 90 degrees for a leaf along an axis).
	 * Returns {minX, minY, minZ, maxX, maxY, maxZ}.
	 */
	public double[] rotatedBox(double a0, double b0, double c0, double a1, double b1, double c1, double angleDeg) {
		double minX = Double.MAX_VALUE, minY = Double.MAX_VALUE, minZ = Double.MAX_VALUE;
		double maxX = -Double.MAX_VALUE, maxY = -Double.MAX_VALUE, maxZ = -Double.MAX_VALUE;
		for (int i = 0; i < 8; i++) {
			double a = (i & 1) == 0 ? a0 : a1, b = (i & 2) == 0 ? b0 : b1, c = (i & 4) == 0 ? c0 : c1;
			double[] w = toWorld(a, b, c, angleDeg);
			minX = Math.min(minX, w[0]);
			minY = Math.min(minY, w[1]);
			minZ = Math.min(minZ, w[2]);
			maxX = Math.max(maxX, w[0]);
			maxY = Math.max(maxY, w[1]);
			maxZ = Math.max(maxZ, w[2]);
		}
		return new double[] {minX, minY, minZ, maxX, maxY, maxZ};
	}

	/** Leaf-local box ({a0, b0, c0, a1, b1, c1}) of a world axis-aligned box (its eight corners enclosed). */
	public double[] localBox(double x0, double y0, double z0, double x1, double y1, double z1) {
		double a0 = Double.MAX_VALUE, b0 = Double.MAX_VALUE, c0 = Double.MAX_VALUE;
		double a1 = -Double.MAX_VALUE, b1 = -Double.MAX_VALUE, c1 = -Double.MAX_VALUE;
		for (int i = 0; i < 8; i++) {
			double[] l = toLocal((i & 1) == 0 ? x0 : x1, (i & 2) == 0 ? y0 : y1, (i & 4) == 0 ? z0 : z1);
			a0 = Math.min(a0, l[0]);
			b0 = Math.min(b0, l[1]);
			c0 = Math.min(c0, l[2]);
			a1 = Math.max(a1, l[0]);
			b1 = Math.max(b1, l[1]);
			c1 = Math.max(c1, l[2]);
		}
		return new double[] {a0, b0, c0, a1, b1, c1};
	}

	/** Same frame, its hinge moved to another point. */
	public LeafFrame withHinge(double x, double y, double z) {
		return new LeafFrame(x, y, z, ux, uz, vx, vz);
	}
}
