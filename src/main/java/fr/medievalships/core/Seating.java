package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The geometry of sitting on a prop's seats ({@link TentType.Seat}, 1.19.0), shared by the server (validation of a sit
 * request, the seat entity, where the player stands up) and the client (picking a seat with the crosshair). Pure math,
 * no Minecraft class: unit tested.
 *
 * <p>A sitting player rides an invisible seat entity placed exactly at the seat's surface; the passenger attachment
 * point is that surface, so the player's feet go {@link #PLAYER_RIDING_DROP} below it (Minecraft's vehicle attachment
 * of a player) and the vanilla sitting pose puts the thighs on the surface: the hip joint is 0.70 above the feet and
 * the thigh 0.12 thick, so the underside of the thighs is 0.59 above the feet, one hundredth of a block below the
 * surface, like the benches of the ships ({@code ShipEntity}: seat point = bench top).
 */
public final class Seating {
	/** The client picks a seat at most this far from the player's eyes (blocks). */
	public static final double PICK_RANGE = 4.0;
	/**
	 * The server accepts a sit request at most this far, from the player's eyes to the centre of the seat's surface:
	 * the pick range plus the pick box's half-diagonal (the client measures to where the ray enters the box).
	 */
	public static final double SERVER_REACH = PICK_RANGE + 0.5;
	/** Half-width of the box a seat is picked by, and how far it reaches below and above the seat's surface. */
	public static final double PICK_HALF = 0.3, PICK_BELOW = 0.45, PICK_ABOVE = 0.12;
	/** The player's feet are this far below the vehicle's attachment point (vanilla {@code PlayerLikeEntity.VEHICLE_ATTACHMENT}). */
	public static final double PLAYER_RIDING_DROP = 0.6;
	/** A sitter can turn his head this far from the seat's yaw (degrees), his body stays square to the seat (like a boat's). */
	public static final float HEAD_TURN = 105f;
	/** How far from the seat's centre a player getting up stands (the near ring first, then the far one). */
	public static final double[] STAND_DISTANCES = {0.85, 1.3};
	/** The directions tried, in degrees from the seat's facing: in front first, then the front corners, the sides, behind last. */
	public static final double[] STAND_ANGLES = {0, 45, -45, 90, -90, 135, -135, 180};

	private Seating() {
	}

	/** World point of a turned seat's surface centre, the anchor block at (ax, ay, az) (its centre on the ground). */
	public static double[] world(int ax, int ay, int az, TentType.Seat turned) {
		return new double[] {ax + 0.5 + turned.x(), ay + turned.y(), az + 0.5 + turned.z()};
	}

	/** The horizontal unit vector of a yaw (Minecraft: 0 = +z, 90 = -x): {dx, dz}. */
	public static double[] facing(double yawDegrees) {
		double r = Math.toRadians(yawDegrees);
		return new double[] {-Math.sin(r), Math.cos(r)};
	}

	/**
	 * The horizontal offsets from a seat's centre where a player getting up may stand, in the order they are tried: for
	 * each distance of {@link #STAND_DISTANCES}, each direction of {@link #STAND_ANGLES} turned from the seat's yaw.
	 */
	public static List<double[]> standOffsets(double yawDegrees) {
		List<double[]> out = new ArrayList<>();
		for (double d : STAND_DISTANCES) {
			for (double a : STAND_ANGLES) {
				double[] f = facing(yawDegrees + a);
				out.add(new double[] {f[0] * d, f[1] * d});
			}
		}
		return out;
	}

	/** The pick box of a seat whose surface centre is at (x, y, z): {x0, y0, z0, x1, y1, z1}. */
	public static double[] pickBox(double x, double y, double z) {
		return new double[] {x - PICK_HALF, y - PICK_BELOW, z - PICK_HALF, x + PICK_HALF, y + PICK_ABOVE, z + PICK_HALF};
	}

	/**
	 * Distance along a ray (origin o, unit direction d) to where it enters an axis-aligned box {x0, y0, z0, x1, y1, z1}
	 * (slab method), or NaN if it misses the box within {@code max} (0 when the origin is inside).
	 */
	public static double rayBox(double ox, double oy, double oz, double dx, double dy, double dz, double[] b, double max) {
		double tMin = 0, tMax = max;
		double[] o = {ox, oy, oz}, d = {dx, dy, dz};
		for (int i = 0; i < 3; i++) {
			double lo = b[i], hi = b[i + 3];
			if (Math.abs(d[i]) < 1e-12) {
				if (o[i] < lo || o[i] > hi) {
					return Double.NaN;
				}
				continue;
			}
			double t0 = (lo - o[i]) / d[i], t1 = (hi - o[i]) / d[i];
			if (t0 > t1) {
				double t = t0;
				t0 = t1;
				t1 = t;
			}
			tMin = Math.max(tMin, t0);
			tMax = Math.min(tMax, t1);
			if (tMin > tMax) {
				return Double.NaN;
			}
		}
		return tMin;
	}

	/** The signed difference a - b of two yaws, in (-180, 180]. */
	public static double yawDifference(double a, double b) {
		double d = (a - b) % 360.0;
		if (d > 180.0) {
			d -= 360.0;
		} else if (d <= -180.0) {
			d += 360.0;
		}
		return d;
	}
}
