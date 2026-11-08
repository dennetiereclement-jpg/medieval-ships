package fr.medievalships.core.bridge;

/**
 * The waterway through a drawbridge and the zones around it, in world coordinates: the channel's axis through the
 * middle of the bridge (unit direction {@code d}, the way the boats sail), its navigable half width across, the deck's
 * half extent along the axis (the "passage"), and the two approach zones of {@code approach} blocks beyond each side
 * of the deck, extended by the hysteresis for a vessel already taken into account. "Both sides" are the two ends of
 * the channel the boats come from, not the two banks. Pure geometry.
 */
public record ChannelZones(double cx, double cz, double dx, double dz, double halfWidth, double halfSpan, double approach,
		double hysteresis) {

	/** Margin (blocks) added to the navigable half width when deciding whether a vessel is in the channel band. */
	public static final double LATERAL_MARGIN = 1.0;

	public static ChannelZones of(double cx, double cz, double dirX, double dirZ, double halfWidth, double halfSpan, double approach,
			double hysteresis) {
		double len = Math.hypot(dirX, dirZ);
		if (len < 1e-9) {
			throw new IllegalArgumentException("channel direction must not be zero");
		}
		return new ChannelZones(cx, cz, dirX / len, dirZ / len, halfWidth, halfSpan, approach, hysteresis);
	}

	/** Signed distance of a point along the channel from the middle of the bridge (positive on the +d side). */
	public double along(double x, double z) {
		return (x - cx) * dx + (z - cz) * dz;
	}

	/** Signed distance of a point across the channel from its axis. */
	public double across(double x, double z) {
		return -(x - cx) * dz + (z - cz) * dx;
	}

	/** The side of the bridge a point is on: +1 or -1 (the two ends of the channel). */
	public int side(double x, double z) {
		return along(x, z) >= 0 ? 1 : -1;
	}

	/**
	 * How far the nearest part of a vessel is from the edge of the deck along the channel: its centre's distance along
	 * minus the deck's half span and the vessel's own reach along the channel. Zero or negative: the vessel is in the
	 * passage (under or against the bridge).
	 */
	public double distanceToDeck(double x, double z, double reachAlong) {
		return Math.abs(along(x, z)) - halfSpan - reachAlong;
	}

	/** Is the vessel (its centre and half width across) within the channel band, where a passage is possible at all? */
	public boolean inBand(double x, double z, double halfAcross) {
		return Math.abs(across(x, z)) - halfAcross <= halfWidth + LATERAL_MARGIN;
	}

	/** Within the approach zone (either side) or the passage: triggers an opening. */
	public boolean inApproach(double distanceToDeck) {
		return distanceToDeck <= approach;
	}

	/** Within the approach extended by the hysteresis: keeps a vessel already taken into account. */
	public boolean inKeepZone(double distanceToDeck) {
		return distanceToDeck <= approach + hysteresis;
	}

	/** In the passage itself (the vessel's footprint reaches the deck's extent along the channel). */
	public boolean inPassage(double distanceToDeck) {
		return distanceToDeck <= 0;
	}

	/**
	 * Extent of an oriented rectangle (a hull: {@code reachFwd} ahead of its origin, {@code reachBack} behind, half
	 * width {@code halfWidthHull}) along a unit direction {@code (ex, ez)}: the largest projection of its corners.
	 *
	 * @param yawDeg Minecraft yaw of the hull (0 = facing +z, 90 = facing -x)
	 */
	public static double extentAlong(double yawDeg, double reachFwd, double reachBack, double halfWidthHull, double ex, double ez) {
		double r = Math.toRadians(yawDeg);
		double fx = -Math.sin(r), fz = Math.cos(r);
		double sx = fz, sz = -fx;
		double f = Math.abs(fx * ex + fz * ez), s = Math.abs(sx * ex + sz * ez);
		return f * Math.max(reachFwd, reachBack) + s * halfWidthHull;
	}

	/** Extent of such a hull along the channel. */
	public double reachAlong(double yawDeg, double reachFwd, double reachBack, double halfWidthHull) {
		return extentAlong(yawDeg, reachFwd, reachBack, halfWidthHull, dx, dz);
	}

	/** Extent of such a hull across the channel (its half width as seen by the towers). */
	public double reachAcross(double yawDeg, double reachFwd, double reachBack, double halfWidthHull) {
		return extentAlong(yawDeg, reachFwd, reachBack, halfWidthHull, -dz, dx);
	}

	/**
	 * World box ({minX, minY, minZ, maxX, maxY, maxZ}) of one approach zone (side +1 or -1) between two heights:
	 * from the deck edge to {@code approach + hysteresis} blocks away, the navigable width plus its margin.
	 */
	public double[] approachBox(int side, double y0, double y1) {
		double from = halfSpan, to = halfSpan + approach + hysteresis;
		return boxAlong(side * from, side * to, halfWidth + LATERAL_MARGIN, y0, y1);
	}

	/** World box of the passage (the deck's extent along the channel) over the navigable width. */
	public double[] passageBox(double y0, double y1) {
		return boxAlong(-halfSpan, halfSpan, halfWidth + LATERAL_MARGIN, y0, y1);
	}

	/** World box enclosing both approach zones and the passage. */
	public double[] detectionBox(double y0, double y1) {
		double to = halfSpan + approach + hysteresis;
		return boxAlong(-to, to, halfWidth + LATERAL_MARGIN, y0, y1);
	}

	/** World box enclosing the part of the channel between two signed distances along it and a half width across. */
	public double[] boxAlong(double s0, double s1, double half, double y0, double y1) {
		double minX = Double.MAX_VALUE, minZ = Double.MAX_VALUE, maxX = -Double.MAX_VALUE, maxZ = -Double.MAX_VALUE;
		for (double s : new double[] {s0, s1}) {
			for (double t : new double[] {-half, half}) {
				double x = cx + s * dx - t * dz, z = cz + s * dz + t * dx;
				minX = Math.min(minX, x);
				minZ = Math.min(minZ, z);
				maxX = Math.max(maxX, x);
				maxZ = Math.max(maxZ, z);
			}
		}
		return new double[] {minX, Math.min(y0, y1), minZ, maxX, Math.max(y0, y1), maxZ};
	}

	/** The four corners (x, z) of the rectangle between two signed distances along and a half width across. */
	public double[][] corners(double s0, double s1, double half) {
		return new double[][] {
				{cx + s0 * dx + half * dz, cz + s0 * dz - half * dx},
				{cx + s1 * dx + half * dz, cz + s1 * dz - half * dx},
				{cx + s1 * dx - half * dz, cz + s1 * dz + half * dx},
				{cx + s0 * dx - half * dz, cz + s0 * dz + half * dx}};
	}
}
