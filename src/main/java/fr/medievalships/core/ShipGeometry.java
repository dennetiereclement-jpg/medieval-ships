package fr.medievalships.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Gameplay geometry of the galley derived from {@link HullProfile}: walkable deck and
 * hull walls (as world-aligned boxes), seats, terrain probe points and ray picking.
 */
public final class ShipGeometry {
	/** Bounding radius around the hull origin, used for cheap rejection. */
	public static final double BOUNDING_RADIUS = 11.5;
	public static final double DECK_MIN_Z = -9.7;
	public static final double DECK_MAX_Z = 9.6;
	private static final double CELL = 0.5;
	private static final double WALL_STEP = 0.4;
	private static final double WALL_HALF = 0.14;

	public static final int PILOT_SEAT = 0;
	public static final List<Seat> SEATS;
	public static final double[] BENCH_Z = {-4.8, -1.6, 1.6, 4.8};
	/** Local offsets of the probe points used to detect terrain and other hulls. */
	public static final List<double[]> PROBES;

	static {
		List<Seat> seats = new ArrayList<>();
		seats.add(new Seat(PILOT_SEAT, 0.0, HullProfile.RAISED_DECK_Y + 0.28, -8.05, true));
		int i = 1;
		for (double z : BENCH_Z) {
			for (double x : new double[] {1.0, -1.0}) {
				seats.add(new Seat(i++, x, HullProfile.MAIN_DECK_Y + 0.47, z, false));
			}
		}
		SEATS = Collections.unmodifiableList(seats);

		List<double[]> probes = new ArrayList<>();
		for (double z = -9.5; z <= 9.51; z += 1.0) {
			double w = HullProfile.halfWidth(z) * 0.97;
			double keel = Math.max(HullProfile.keelY(z) + 0.2, -1.0);
			for (double side : new double[] {1, -1}) {
				probes.add(new double[] {side * w, 0.15, z});
				probes.add(new double[] {side * w, 1.2, z});
				probes.add(new double[] {side * w * 0.7, keel + 0.25, z});
			}
			if (((int) Math.round(z + 9.5)) % 2 == 0) {
				probes.add(new double[] {0, keel, z});
			}
		}
		for (double side : new double[] {1, -1}) {
			double z = side * 10.4;
			probes.add(new double[] {0, 0.15, z});
			probes.add(new double[] {0, 1.4, z});
			probes.add(new double[] {0, HullProfile.keelY(10) + 0.3, side * 10.0});
		}
		PROBES = Collections.unmodifiableList(probes);
	}

	private ShipGeometry() {
	}

	public record Seat(int index, double x, double y, double z, boolean pilot) {
		/** Where a passenger leaving this seat stands (ship-local, feet position). */
		public double[] dismountLocal() {
			if (pilot) {
				return new double[] {0.0, HullProfile.RAISED_DECK_Y + 0.02, -7.35};
			}
			return new double[] {x * 0.9, HullProfile.MAIN_DECK_Y + 0.02, z + 0.8};
		}
	}

	public interface BoxSink {
		void accept(double minX, double minY, double minZ, double maxX, double maxY, double maxZ);
	}

	/** Is this local point inside the volume where entities are carried along with the ship? */
	public static boolean inCarryVolume(double lx, double ly, double lz) {
		if (Math.abs(lz) > HullProfile.HALF_LENGTH + 0.3) {
			return false;
		}
		double w = HullProfile.halfWidth(Math.max(-9.9, Math.min(9.9, lz))) + 0.15;
		if (Math.abs(lx) > w) {
			return false;
		}
		return ly >= HullProfile.deckY(lz) - 0.7 && ly <= HullProfile.railY(lz) + 3.2;
	}

	/** Is this local point inside the solid hull (used for ship-to-ship collisions)? */
	public static boolean insideHull(double lx, double ly, double lz) {
		if (Math.abs(lz) > HullProfile.HALF_LENGTH) {
			return false;
		}
		if (Math.abs(lx) > HullProfile.halfWidth(lz)) {
			return false;
		}
		return ly >= HullProfile.keelY(lz) - 0.1 && ly <= HullProfile.railY(lz) + 0.2;
	}

	/**
	 * Emits world-space boxes (deck floor, hull walls, mast) intersecting the given world query box.
	 * Boxes are axis aligned in the world; each one covers a small rotated cell of the hull,
	 * so the union follows the hull shape for any heading.
	 */
	public static void collectBoxes(ShipPose pose, double qMinX, double qMinY, double qMinZ,
									double qMaxX, double qMaxY, double qMaxZ, BoxSink sink) {
		double cx = (qMinX + qMaxX) / 2, cz = (qMinZ + qMaxZ) / 2;
		double rx = (qMaxX - qMinX) / 2, rz = (qMaxZ - qMinZ) / 2;
		double dx = cx - pose.x(), dz = cz - pose.z();
		double reach = BOUNDING_RADIUS + rx + rz;
		if (dx * dx + dz * dz > reach * reach) {
			return;
		}
		if (qMaxY < pose.y() - 2.0 || qMinY > pose.y() + HullProfile.MAST_TOP + 1) {
			return;
		}
		// query box -> local bounds (conservative)
		double c = pose.cos(), s = pose.sin();
		double ac = Math.abs(c), as = Math.abs(s);
		double[] lc = pose.toLocal(cx, 0, cz);
		double lrx = rx * ac + rz * as + 0.8;
		double lrz = rx * as + rz * ac + 0.8;
		double lxMin = lc[0] - lrx, lxMax = lc[0] + lrx;
		double lzMin = lc[2] - lrz, lzMax = lc[2] + lrz;
		double lyMin = qMinY - pose.y(), lyMax = qMaxY - pose.y();
		double cellHalf = CELL / 2 * (ac + as) + 1e-4;

		// deck floor
		int iz0 = (int) Math.floor(Math.max(lzMin, DECK_MIN_Z) / CELL);
		int iz1 = (int) Math.floor(Math.min(lzMax, DECK_MAX_Z) / CELL);
		for (int iz = iz0; iz <= iz1; iz++) {
			double zc = (iz + 0.5) * CELL;
			if (zc < DECK_MIN_Z || zc > DECK_MAX_Z) {
				continue;
			}
			double top = HullProfile.deckY(zc);
			if (lyMax < top - 0.5 || lyMin > top) {
				continue;
			}
			double w = HullProfile.innerHalfWidth(zc) + 0.12;
			int ix0 = (int) Math.floor(Math.max(lxMin, -w) / CELL);
			int ix1 = (int) Math.floor(Math.min(lxMax, w) / CELL);
			for (int ix = ix0; ix <= ix1; ix++) {
				double xc = (ix + 0.5) * CELL;
				if (Math.abs(xc) - CELL / 2 > w) {
					continue;
				}
				double wx = pose.x() + xc * c - zc * s;
				double wz = pose.z() + xc * s + zc * c;
				sink.accept(wx - cellHalf, pose.y() + top - 0.5, wz - cellHalf,
						wx + cellHalf, pose.y() + top, wz + cellHalf);
			}
		}

		// hull walls (from keel to rail): keep walkers on deck and swimmers out of the hull
		double wallHalf = WALL_HALF * (ac + as) + 1e-4;
		int jz0 = (int) Math.floor(Math.max(lzMin, -9.9) / WALL_STEP);
		int jz1 = (int) Math.ceil(Math.min(lzMax, 9.9) / WALL_STEP);
		for (int jz = jz0; jz <= jz1; jz++) {
			double zc = jz * WALL_STEP;
			if (zc < -9.9 || zc > 9.9) {
				continue;
			}
			double bottom = HullProfile.keelY(zc);
			double top = HullProfile.railY(zc) + 0.1;
			if (lyMax < bottom || lyMin > top) {
				continue;
			}
			double w = HullProfile.halfWidth(zc) - 0.06;
			for (double side : new double[] {1, -1}) {
				double xc = side * w;
				if (xc < lxMin - 0.3 || xc > lxMax + 0.3) {
					continue;
				}
				double wx = pose.x() + xc * c - zc * s;
				double wz = pose.z() + xc * s + zc * c;
				sink.accept(wx - wallHalf, pose.y() + bottom, wz - wallHalf,
						wx + wallHalf, pose.y() + top, wz + wallHalf);
			}
		}
		// bow and stern posts close the ends
		for (double side : new double[] {1, -1}) {
			for (double zc = 10.0; zc <= 10.61; zc += 0.3) {
				double z = side * zc;
				if (z < lzMin - 0.5 || z > lzMax + 0.5) {
					continue;
				}
				double bottom = HullProfile.keelY(10.0);
				double top = HullProfile.railY(10.0) + 0.6;
				double wx = pose.x() - z * s;
				double wz = pose.z() + z * c;
				double h = 0.3 * (ac + as) + 1e-4;
				sink.accept(wx - h, pose.y() + bottom, wz - h, wx + h, pose.y() + top, wz + h);
			}
		}
		// mast
		if (lxMin < 0.3 && lxMax > -0.3 && lzMin < HullProfile.MAST_Z + 0.3 && lzMax > HullProfile.MAST_Z - 0.3) {
			double wx = pose.x() - HullProfile.MAST_Z * s;
			double wz = pose.z() + HullProfile.MAST_Z * c;
			double h = 0.2 * (ac + as);
			sink.accept(wx - h, pose.y() + HullProfile.MAIN_DECK_Y, wz - h, wx + h, pose.y() + HullProfile.MAST_TOP, wz + h);
		}
	}

	/** Nearest standing spot on the deck to a local point (feet position, local space). */
	public static double[] boardingSpot(double lx, double lz) {
		double z = Math.max(-8.9, Math.min(8.9, lz));
		for (double bz : BENCH_Z) {
			if (Math.abs(z - bz) < 0.45) {
				z = bz + (z >= bz ? 0.55 : -0.55);
			}
		}
		double w = Math.max(0.0, HullProfile.innerHalfWidth(z) - 0.55);
		double x = Math.max(-w, Math.min(w, lx));
		if (Math.abs(z - HullProfile.MAST_Z) < 0.6 && Math.abs(x) < 0.55) {
			x = x >= 0 ? 0.6 : -0.6;
		}
		return new double[] {x, HullProfile.deckY(z) + 0.02, z};
	}

	// ------------------------------------------------------------------ picking

	public enum PickKind { HELM, SEAT, HULL, DECK }

	public record Pick(PickKind kind, int seat, double distance, double lx, double ly, double lz) {
	}

	/**
	 * Casts a world-space ray against the interactive parts of the ship.
	 * The hull itself is only pickable from outside (to board the ship).
	 */
	public static Pick pick(ShipPose pose, double ox, double oy, double oz, double dx, double dy, double dz, double maxDist) {
		double[] o = pose.toLocal(ox, oy, oz);
		double[] d = pose.dirToLocal(dx, dy, dz);
		Pick best = null;
		double t = rayBox(o, d, -0.5, HullProfile.RAISED_DECK_Y + 0.1, -8.6, 0.5, HullProfile.RAISED_DECK_Y + 1.1, -7.4);
		if (t >= 0 && t <= maxDist) {
			best = hit(PickKind.HELM, PILOT_SEAT, t, o, d);
		}
		for (Seat seat : SEATS) {
			if (seat.pilot()) {
				continue;
			}
			t = rayBox(o, d, seat.x() - 0.45, seat.y() - 0.35, seat.z() - 0.3, seat.x() + 0.45, seat.y() + 0.15, seat.z() + 0.3);
			if (t >= 0 && t <= maxDist && (best == null || t < best.distance())) {
				best = hit(PickKind.SEAT, seat.index(), t, o, d);
			}
		}
		// the deck itself: clicking it must not reach the water or the sea bed under the hull
		for (double z0 = DECK_MIN_Z; z0 < DECK_MAX_Z; z0 += 0.5) {
			double zm = z0 + 0.25;
			double w = HullProfile.innerHalfWidth(zm) + 0.1;
			double top = HullProfile.deckY(zm);
			t = rayBox(o, d, -w, top - 0.2, z0, w, top, z0 + 0.5);
			if (t >= 0 && t <= maxDist && (best == null || t < best.distance())) {
				best = hit(PickKind.DECK, -1, t, o, d);
			}
		}
		if (!inCarryVolume(o[0], o[1], o[2])) {
			for (double z0 = -10.0; z0 < 10.0; z0 += 1.0) {
				double zm = z0 + 0.5;
				double w = HullProfile.halfWidth(zm) + 0.1;
				t = rayBox(o, d, -w, HullProfile.keelY(zm), z0, w, HullProfile.railY(zm) + 0.2, z0 + 1.0);
				if (t >= 0 && t <= maxDist && (best == null || t < best.distance())) {
					best = hit(PickKind.HULL, -1, t, o, d);
				}
			}
		}
		return best;
	}

	private static Pick hit(PickKind kind, int seat, double t, double[] o, double[] d) {
		return new Pick(kind, seat, t, o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t);
	}

	/** Slab test; returns the entry distance, 0 if the origin is inside, or -1. */
	static double rayBox(double[] o, double[] d, double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
		double tMin = 0, tMax = Double.MAX_VALUE;
		double[] mn = {minX, minY, minZ}, mx = {maxX, maxY, maxZ};
		for (int a = 0; a < 3; a++) {
			if (Math.abs(d[a]) < 1e-9) {
				if (o[a] < mn[a] || o[a] > mx[a]) {
					return -1;
				}
			} else {
				double t1 = (mn[a] - o[a]) / d[a], t2 = (mx[a] - o[a]) / d[a];
				if (t1 > t2) {
					double tmp = t1;
					t1 = t2;
					t2 = tmp;
				}
				tMin = Math.max(tMin, t1);
				tMax = Math.min(tMax, t2);
				if (tMin > tMax) {
					return -1;
				}
			}
		}
		return tMin;
	}
}
