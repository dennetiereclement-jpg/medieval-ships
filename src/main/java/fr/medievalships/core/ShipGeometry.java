package fr.medievalships.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Gameplay geometry of one ship type, derived from its {@link HullShape}: solid hull and deck
 * (as world-aligned boxes), walls, masts and superstructures, seats, terrain probe points and
 * ray picking. One instance per ship type (see {@link Ships}).
 */
public final class ShipGeometry {
	public static final int PILOT_SEAT = 0;
	private static final double CELL = 0.5;
	private static final double WALL_STEP = 0.4;
	private static final double WALL_HALF = 0.14;

	public record Seat(int index, double x, double y, double z, boolean pilot, double[] dismount) {
		/** Where a passenger leaving this seat stands (ship-local, feet position). */
		public double[] dismountLocal() {
			return dismount.clone();
		}
	}

	/** Vertical pole (mast) from {@code bottom} to {@code top}. */
	public record Mast(double x, double z, double bottom, double top, double half) {
	}

	/** Solid axis-aligned box in ship-local space (cabin walls, castles, roofs...). */
	public record LocalBox(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
	}

	/**
	 * Gun port (decorative for now): muzzle position on the hull side, ship-local, and the side
	 * it fires to (+1 port, -1 starboard). Ready for a future cannon system.
	 */
	public record Gunport(int index, double x, double y, double z, int side) {
	}

	/** Everything that differs between ship types, besides the hull shape. */
	public static final class Spec {
		public List<Seat> seats = List.of();
		public LocalBox helm;
		public List<Mast> masts = List.of();
		public List<LocalBox> solids = List.of();
		/** Probe spacing along the hull. */
		public double probeStep = 1.0;
		/** Heights (above the waterline) of the side probes; castles need higher ones. */
		public double[] probeHeights = {0.15, 1.2};
		/** Boarding spots are kept between these z and away from these z (benches). */
		public double boardMinZ = -8.9;
		public double boardMaxZ = 8.9;
		public double[] avoidZ = {};
		/** Solid stem / stern posts beyond the hull ends (a transom stern has none). */
		public boolean stemPost = true;
		public boolean sternPost = true;
		public List<Gunport> gunports = List.of();
		/** Extra terrain probes (ship-local points) for parts outside the hull, e.g. a paddle box. */
		public List<double[]> extraProbes = List.of();
		/** Half width for the autopilot's clearance rays, if wider than the hull (NaN: from the hull). */
		public double aiHalfWidth = Double.NaN;
		/** An aircraft: flies instead of floating (no water, no gravity while flying). */
		public boolean flying;
		/** Parts beyond the hull (balloon, propeller...): overrides of the extents derived from the hull (NaN: from the hull). */
		public double boundingRadius = Double.NaN;
		public double aiReach = Double.NaN;
		public double aiBack = Double.NaN;
		public double lowestY = Double.NaN;
	}

	public interface BoxSink {
		void accept(double minX, double minY, double minZ, double maxX, double maxY, double maxZ);
	}

	private final HullShape hull;
	private final Spec spec;
	private final List<double[]> probes;
	private final double boundingRadius;
	private final double maxHeight;

	public ShipGeometry(HullShape hull, Spec spec) {
		this.hull = hull;
		this.spec = spec;
		List<double[]> probeList = buildProbes(hull, spec.probeStep, spec.probeHeights);
		probeList.addAll(spec.extraProbes);
		this.probes = Collections.unmodifiableList(probeList);
		this.boundingRadius = Double.isNaN(spec.boundingRadius) ? hull.tip + 0.6 : spec.boundingRadius;
		double top = 0;
		for (Mast m : spec.masts) {
			top = Math.max(top, m.top());
		}
		for (LocalBox b : spec.solids) {
			top = Math.max(top, b.maxY());
		}
		this.maxHeight = top;
	}

	private static List<double[]> buildProbes(HullShape h, double step, double[] heights) {
		List<double[]> probes = new ArrayList<>();
		double zMax = h.halfLength - 0.5;
		int n = (int) Math.round(2 * zMax / step);
		for (int i = 0; i <= n; i++) {
			double z = -zMax + i * step;
			double w = h.halfWidth(z) * 0.97;
			double keel = Math.max(h.keelY(z) + 0.2, h.keelY(0) + 0.2);
			for (double side : new double[] {1, -1}) {
				for (double y : heights) {
					probes.add(new double[] {side * w, y, z});
				}
				probes.add(new double[] {side * w * 0.7, keel + 0.25, z});
			}
			if (i % 2 == 0) {
				probes.add(new double[] {0, keel, z});
			}
		}
		for (double side : new double[] {1, -1}) {
			double z = side * (h.halfLength + 0.4);
			probes.add(new double[] {0, 0.15, z});
			probes.add(new double[] {0, 1.4, z});
			if (h.waterlineY != 0) {
				probes.add(new double[] {0, h.waterlineY + 0.15, z});
			}
			probes.add(new double[] {0, h.keelY(h.halfLength) + 0.3, side * h.halfLength});
		}
		return probes;
	}

	public HullShape hull() {
		return hull;
	}

	/** Box around the helm (wheel, tiller): clicking it takes the pilot seat. */
	public LocalBox helm() {
		return spec.helm;
	}

	public List<Seat> seats() {
		return spec.seats;
	}

	public List<Gunport> gunports() {
		return spec.gunports;
	}

	public List<LocalBox> solids() {
		return spec.solids;
	}

	/** Local offsets of the probe points used to detect terrain and other hulls. */
	public List<double[]> probes() {
		return probes;
	}

	public double boundingRadius() {
		return boundingRadius;
	}

	/** How far the hull extends ahead of its origin (for the autopilot). */
	public double aiReach() {
		return Double.isNaN(spec.aiReach) ? hull.tip - 0.3 : spec.aiReach;
	}

	/** How far the ship extends behind its origin (for the autopilot of an aircraft). */
	public double aiBack() {
		return Double.isNaN(spec.aiBack) ? hull.tip - 0.3 : spec.aiBack;
	}

	/** Is this an aircraft? */
	public boolean flying() {
		return spec.flying;
	}

	/** Lowest point of the ship (keel), ship-local. */
	public double lowestY() {
		return Double.isNaN(spec.lowestY) ? hull.keelY(0) : spec.lowestY;
	}

	/** Highest point of the ship (mast top, balloon...), ship-local. */
	public double topY() {
		return Math.max(maxHeight, hull.railY(hull.halfLength));
	}

	/** Half width used by the autopilot's clearance rays. */
	public double aiHalfWidth() {
		return Double.isNaN(spec.aiHalfWidth) ? hull.maxHalfWidth - 0.15 : spec.aiHalfWidth;
	}

	/** Is this local point inside the volume where entities are carried along with the ship? */
	public boolean inCarryVolume(double lx, double ly, double lz) {
		// on or around a superstructure (castles, stern balcony beyond the hull end...)
		for (LocalBox b : spec.solids) {
			if (lx >= b.minX() - 0.3 && lx <= b.maxX() + 0.3 && lz >= b.minZ() - 0.3 && lz <= b.maxZ() + 0.3
					&& ly >= b.minY() - 0.7 && ly <= b.maxY() + 2.5) {
				return true;
			}
		}
		if (Math.abs(lz) > hull.halfLength + 0.3) {
			return false;
		}
		double zc = Math.max(-hull.halfLength + 0.1, Math.min(hull.halfLength - 0.1, lz));
		double w = hull.halfWidth(zc) + 0.15;
		if (Math.abs(lx) > w) {
			return false;
		}
		double top = hull.railY(lz) + 3.2;
		for (LocalBox b : spec.solids) {
			if (lz >= b.minZ() && lz <= b.maxZ() && lx >= b.minX() && lx <= b.maxX()) {
				top = Math.max(top, b.maxY() + 2.5);
			}
		}
		return ly >= hull.deckY(lz) - 0.7 && ly <= top;
	}

	/**
	 * Safety net used when another mod replaced the collision code: if a point (feet, local space)
	 * has sunk into the deck volume, returns the deck height to put it back on; NaN otherwise.
	 */
	public double deckRescueY(double lx, double ly, double lz) {
		// sunk into a walkable superstructure (castle floor, stairs, balcony)
		for (LocalBox b : spec.solids) {
			if (lx > b.minX() && lx < b.maxX() && lz > b.minZ() && lz < b.maxZ()
					&& ly < b.maxY() - 1e-3 && ly > b.maxY() - Math.min(1.2, b.maxY() - b.minY() + 0.05)) {
				return b.maxY();
			}
		}
		if (lz < hull.deckMinZ || lz > hull.deckMaxZ || Math.abs(lx) > hull.innerHalfWidth(lz)) {
			return Double.NaN;
		}
		double top = hull.deckY(lz);
		return ly < top - 1e-3 && ly > top - 1.2 ? top : Double.NaN;
	}

	/**
	 * Safety net for fast falls: if a point went from above a walkable surface (deck, castle floor)
	 * to below it during one tick (local heights {@code yBefore} then {@code yAfter}), returns that
	 * surface height; NaN otherwise. {@code minDepth} is how far below it must have gone.
	 */
	public double deckCrossingY(double lx, double lz, double yBefore, double yAfter, double minDepth, boolean solids) {
		double best = Double.NaN;
		if (lz >= hull.deckMinZ && lz <= hull.deckMaxZ && Math.abs(lx) <= hull.innerHalfWidth(lz)) {
			double top = hull.deckY(lz);
			if (yBefore >= top - 0.05 && yAfter < top - minDepth) {
				best = top;
			}
		}
		if (solids) {
			for (LocalBox b : spec.solids) {
				if (lx > b.minX() && lx < b.maxX() && lz > b.minZ() && lz < b.maxZ()
						&& yBefore >= b.maxY() - 0.05 && yAfter < b.maxY() - minDepth && !(best >= b.maxY())) {
					best = b.maxY();
				}
			}
		}
		return best;
	}

	/** Is this local point inside the solid hull (used for ship-to-ship collisions)? */
	public boolean insideHull(double lx, double ly, double lz) {
		if (Math.abs(lz) > hull.halfLength) {
			return false;
		}
		if (Math.abs(lx) > hull.halfWidth(lz)) {
			return false;
		}
		return ly >= hull.keelY(lz) - 0.1 && ly <= hull.railY(lz) + 0.2;
	}

	/**
	 * Emits world-space boxes (solid hull and deck, hull walls, posts, masts, superstructures)
	 * intersecting the given world query box. Boxes are axis aligned in the world; each one covers
	 * a small rotated cell of the hull, so the union follows the hull shape for any heading.
	 */
	public void collectBoxes(ShipPose pose, double qMinX, double qMinY, double qMinZ,
							 double qMaxX, double qMaxY, double qMaxZ, BoxSink sink) {
		double cx = (qMinX + qMaxX) / 2, cz = (qMinZ + qMaxZ) / 2;
		double rx = (qMaxX - qMinX) / 2, rz = (qMaxZ - qMinZ) / 2;
		double dx = cx - pose.x(), dz = cz - pose.z();
		double reach = boundingRadius + rx + rz;
		if (dx * dx + dz * dz > reach * reach) {
			return;
		}
		if (qMaxY < pose.y() + Math.min(-2.0, hull.keelY(0) - 0.8) || qMinY > pose.y() + maxHeight + 1) {
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

		// solid hull: deck on top, hull bottom underneath. Nothing can get under the deck or
		// inside the hull, from above or from the water.
		int iz0 = (int) Math.floor(Math.max(lzMin, hull.deckMinZ) / CELL);
		int iz1 = (int) Math.floor(Math.min(lzMax, hull.deckMaxZ) / CELL);
		for (int iz = iz0; iz <= iz1; iz++) {
			double zc = (iz + 0.5) * CELL;
			if (zc < hull.deckMinZ || zc > hull.deckMaxZ) {
				continue;
			}
			double top = hull.deckY(zc);
			if (lyMax < hull.keelY(zc) || lyMin > top) {
				continue;
			}
			double w = hull.innerHalfWidth(zc) + 0.12;
			int ix0 = (int) Math.floor(Math.max(lxMin, -w) / CELL);
			int ix1 = (int) Math.floor(Math.min(lxMax, w) / CELL);
			for (int ix = ix0; ix <= ix1; ix++) {
				double xc = (ix + 0.5) * CELL;
				if (Math.abs(xc) - CELL / 2 > w) {
					continue;
				}
				// bottom of the hull under the centre of the cell, so the box barely sticks
				// out below the rounded hull
				double bottom = Math.min(top - 0.5, hull.bottomY(zc, Math.min(w, Math.abs(xc))));
				if (lyMax < bottom) {
					continue;
				}
				double wx = pose.x() + xc * c - zc * s;
				double wz = pose.z() + xc * s + zc * c;
				sink.accept(wx - cellHalf, pose.y() + bottom, wz - cellHalf,
						wx + cellHalf, pose.y() + top, wz + cellHalf);
			}
		}

		// hull walls (from the hull bottom to the rail): keep walkers on deck, swimmers out
		double wallHalf = WALL_HALF * (ac + as) + 1e-4;
		double wallZ = hull.halfLength - 0.1;
		int jz0 = (int) Math.floor(Math.max(lzMin, -wallZ) / WALL_STEP);
		int jz1 = (int) Math.ceil(Math.min(lzMax, wallZ) / WALL_STEP);
		for (int jz = jz0; jz <= jz1; jz++) {
			double zc = jz * WALL_STEP;
			if (zc < -wallZ || zc > wallZ) {
				continue;
			}
			double bottom = hull.bottomY(zc, hull.halfWidth(zc));
			double top = hull.railY(zc) + 0.1;
			if (lyMax < bottom || lyMin > top) {
				continue;
			}
			double w = hull.halfWidth(zc) - 0.06;
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
			if (side > 0 ? !spec.stemPost : !spec.sternPost) {
				continue;
			}
			for (double zc = hull.halfLength; zc <= hull.tip - 0.29; zc += 0.3) {
				double z = side * zc;
				if (z < lzMin - 0.5 || z > lzMax + 0.5) {
					continue;
				}
				double bottom = hull.keelY(hull.halfLength);
				double top = hull.railY(hull.halfLength) + 0.6;
				double wx = pose.x() - z * s;
				double wz = pose.z() + z * c;
				double h = 0.3 * (ac + as) + 1e-4;
				sink.accept(wx - h, pose.y() + bottom, wz - h, wx + h, pose.y() + top, wz + h);
			}
		}
		// masts
		for (Mast m : spec.masts) {
			if (lxMin < m.x() + 0.3 && lxMax > m.x() - 0.3 && lzMin < m.z() + 0.3 && lzMax > m.z() - 0.3) {
				double wx = pose.x() + m.x() * c - m.z() * s;
				double wz = pose.z() + m.x() * s + m.z() * c;
				double h = m.half() * (ac + as);
				sink.accept(wx - h, pose.y() + m.bottom(), wz - h, wx + h, pose.y() + m.top(), wz + h);
			}
		}
		// superstructures (castles, cabin walls and roof...)
		for (LocalBox b : spec.solids) {
			if (b.maxX() < lxMin || b.minX() > lxMax || b.maxZ() < lzMin || b.minZ() > lzMax
					|| b.maxY() < lyMin || b.minY() > lyMax) {
				continue;
			}
			emitLocalBox(pose, b, c, s, ac, as, sink);
		}
	}

	/** Covers a rotated local box with small world-aligned boxes (exact union cover). */
	private static void emitLocalBox(ShipPose pose, LocalBox b, double c, double s, double ac, double as, BoxSink sink) {
		double sx = b.maxX() - b.minX(), sz = b.maxZ() - b.minZ();
		int nx = Math.max(1, (int) Math.ceil(sx / CELL)), nz = Math.max(1, (int) Math.ceil(sz / CELL));
		double cellX = sx / nx, cellZ = sz / nz;
		double hx = cellX / 2 * ac + cellZ / 2 * as + 1e-4;
		double hz = cellX / 2 * as + cellZ / 2 * ac + 1e-4;
		for (int i = 0; i < nx; i++) {
			double xc = b.minX() + (i + 0.5) * cellX;
			for (int j = 0; j < nz; j++) {
				double zc = b.minZ() + (j + 0.5) * cellZ;
				double wx = pose.x() + xc * c - zc * s;
				double wz = pose.z() + xc * s + zc * c;
				sink.accept(wx - hx, pose.y() + b.minY(), wz - hz, wx + hx, pose.y() + b.maxY(), wz + hz);
			}
		}
	}

	/** Nearest standing spot on the deck to a local point (feet position, local space). */
	public double[] boardingSpot(double lx, double lz) {
		double z = Math.max(spec.boardMinZ, Math.min(spec.boardMaxZ, lz));
		for (double bz : spec.avoidZ) {
			if (Math.abs(z - bz) < 0.45) {
				z = bz + (z >= bz ? 0.55 : -0.55);
			}
		}
		// not against the front of a castle deck too high to step onto
		if (hull.deckY(z + 0.3) - hull.deckY(z) > 0.6) {
			z -= 0.32;
		} else if (hull.deckY(z - 0.3) - hull.deckY(z) > 0.6) {
			z += 0.32;
		}
		double w = Math.max(0.0, hull.innerHalfWidth(z) - 0.55);
		double x = Math.max(-w, Math.min(w, lx));
		for (Mast m : spec.masts) {
			double clear = Math.max(0.6, m.half() + 0.35);
			if (Math.abs(z - m.z()) < clear && Math.abs(x - m.x()) < Math.max(0.55, m.half() + 0.33)) {
				x = x >= m.x() ? m.x() + clear : m.x() - clear;
			}
		}
		double y = hull.deckY(z);
		// standing spot inside or just under a superstructure (stairs, castle floor): stand on top
		// of it, never in a closed space
		for (boolean moved = true; moved; ) {
			moved = false;
			for (LocalBox b : spec.solids) {
				// whole player footprint (0.6 x 0.6)
				if (x > b.minX() - 0.31 && x < b.maxX() + 0.31 && z > b.minZ() - 0.31 && z < b.maxZ() + 0.31
						&& b.minY() <= y + 2.6 && b.maxY() > y + 1e-6) {
					y = b.maxY();
					moved = true;
				}
			}
		}
		return new double[] {x, y + 0.02, z};
	}

	// ------------------------------------------------------------------ picking

	public enum PickKind { HELM, SEAT, HULL, DECK }

	public record Pick(PickKind kind, int seat, double distance, double lx, double ly, double lz) {
	}

	/**
	 * Casts a world-space ray against the interactive parts of the ship.
	 * The hull itself is only pickable from outside (to board the ship).
	 */
	public Pick pick(ShipPose pose, double ox, double oy, double oz, double dx, double dy, double dz, double maxDist) {
		double[] o = pose.toLocal(ox, oy, oz);
		double[] d = pose.dirToLocal(dx, dy, dz);
		Pick best = null;
		LocalBox helm = spec.helm;
		double t = rayBox(o, d, helm.minX(), helm.minY(), helm.minZ(), helm.maxX(), helm.maxY(), helm.maxZ());
		if (t >= 0 && t <= maxDist) {
			best = hit(PickKind.HELM, PILOT_SEAT, t, o, d);
		}
		for (Seat seat : spec.seats) {
			if (seat.pilot()) {
				continue;
			}
			t = rayBox(o, d, seat.x() - 0.45, seat.y() - 0.35, seat.z() - 0.3, seat.x() + 0.45, seat.y() + 0.15, seat.z() + 0.3);
			if (t >= 0 && t <= maxDist && (best == null || t < best.distance())) {
				best = hit(PickKind.SEAT, seat.index(), t, o, d);
			}
		}
		// the deck itself: clicking it must not reach the water or the sea bed under the hull
		for (double z0 = hull.deckMinZ; z0 < hull.deckMaxZ; z0 += 0.5) {
			double zm = z0 + 0.25;
			double w = hull.innerHalfWidth(zm) + 0.1;
			double top = hull.deckY(zm);
			t = rayBox(o, d, -w, top - 0.2, z0, w, top, z0 + 0.5);
			if (t >= 0 && t <= maxDist && (best == null || t < best.distance())) {
				best = hit(PickKind.DECK, -1, t, o, d);
			}
		}
		for (LocalBox b : spec.solids) {
			t = rayBox(o, d, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ());
			if (t > 0 && t <= maxDist && (best == null || t < best.distance())) {
				best = hit(PickKind.DECK, -1, t, o, d);
			}
		}
		if (!inCarryVolume(o[0], o[1], o[2])) {
			for (double z0 = -hull.halfLength; z0 < hull.halfLength; z0 += 1.0) {
				double zm = z0 + 0.5;
				double w = hull.halfWidth(zm) + 0.1;
				t = rayBox(o, d, -w, hull.keelY(zm), z0, w, hull.railY(zm) + 0.2, z0 + 1.0);
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
