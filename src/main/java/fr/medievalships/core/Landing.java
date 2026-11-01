package fr.medievalships.core;

/**
 * Where the passengers step off a moored vessel ({@code /ship disembark}, a vessel vanishing at the end of its
 * trip): the nearest spot beside the hull where someone can stand, a quay or the shore (a solid block with two
 * free blocks above it, not water, outside the hull), at about the deck's height; an aircraft moored over the
 * ground lands them under it. Pure search, the game code answers what each block is.
 */
public final class Landing {
	/** What a block is, for the search. */
	public enum Block { FREE, SOLID, LIQUID }

	/** The world's blocks. */
	@FunctionalInterface
	public interface Probe {
		Block at(int x, int y, int z);
	}

	/** Searched this far beyond the hull's bounding radius (blocks). */
	public static final int MARGIN = 6;
	/** Searched this far above the main deck (a quay one climbs onto) and below the keel (the ground under an aircraft), blocks. */
	public static final int ABOVE = 4;
	public static final int BELOW = 4;

	private Landing() {
	}

	/**
	 * A standing spot beside the vessel (world coordinates, the feet), or null when there is none around (open sea:
	 * the passengers are left aboard). Nearest to the hull first, then nearest to the deck's height.
	 */
	public static double[] find(ShipGeometry g, ShipPose pose, Probe probe) {
		HullShape hull = g.hull();
		int radius = (int) Math.ceil(g.boundingRadius() + MARGIN);
		int cx = (int) Math.floor(pose.x()), cz = (int) Math.floor(pose.z());
		double deckY = pose.y() + hull.mainDeckY;
		int yMax = (int) Math.floor(deckY + ABOVE), yMin = (int) Math.floor(pose.y() + g.lowestY() - BELOW);
		double[] best = null;
		double bestScore = Double.MAX_VALUE;
		for (int dx = -radius; dx <= radius; dx++) {
			for (int dz = -radius; dz <= radius; dz++) {
				double wx = cx + dx + 0.5, wz = cz + dz + 0.5;
				double[] l = pose.toLocal(wx, deckY, wz);
				// not on the vessel itself, nor against its side (someone there would be in the water or in the hull)
				if (Math.abs(l[0]) < hull.maxHalfWidth + 1.0 && Math.abs(l[2]) < hull.tip + 1.0) {
					continue;
				}
				double horizontal = Math.hypot(dx, dz);
				if (horizontal - 1.5 > bestScore) {
					continue; // cannot beat the best spot whatever its height
				}
				for (int y = yMax; y >= yMin; y--) {
					if (probe.at(cx + dx, y - 1, cz + dz) != Block.SOLID || probe.at(cx + dx, y, cz + dz) != Block.FREE
							|| probe.at(cx + dx, y + 1, cz + dz) != Block.FREE) {
						continue;
					}
					double score = horizontal + 0.3 * Math.abs(y - deckY);
					if (score < bestScore) {
						bestScore = score;
						best = new double[] {wx, y, wz};
					}
					break; // the highest standing spot of this column is the one
				}
			}
		}
		return best;
	}
}
