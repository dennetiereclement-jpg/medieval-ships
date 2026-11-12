package fr.medievalships.core;

import java.util.UUID;

/**
 * Where a player stood (or sat) aboard a ship (1.30.0): the ship, the dimension it was in, the feet position and the
 * yaw in that ship's local frame. Kept in the player's own data (a persistent data attachment of the player entity), so
 * that it follows each character of a multi-character mod (Nexus Characters swaps the whole player file): a character
 * that logged out, or was switched away, on a deck that then sailed on comes back on that deck, at the same spot.
 *
 * @param ship      UUID of the ship entity
 * @param dimension the ship's world when the anchor was taken ({@code minecraft:overworld}...)
 * @param x         local feet position (ship space, see {@link ShipPose#toLocal})
 * @param yaw       the player's yaw relative to the ship's
 */
public record DeckAnchor(UUID ship, String dimension, double x, double y, double z, float yaw) {
	/** Smallest move on the deck (blocks) or turn (degrees) worth storing again. */
	public static final double MOVE_EPSILON = 0.25;
	public static final double TURN_EPSILON = 15.0;

	/** Is {@code other} (same ship) different enough from this anchor to replace it? */
	public boolean differs(DeckAnchor other) {
		if (other == null || !ship.equals(other.ship) || !dimension.equals(other.dimension)) {
			return true;
		}
		double dx = x - other.x, dy = y - other.y, dz = z - other.z;
		return dx * dx + dy * dy + dz * dz > MOVE_EPSILON * MOVE_EPSILON || Math.abs(ShipPose.wrapDegrees(yaw - other.yaw)) > TURN_EPSILON;
	}

	/**
	 * The local spot to put the player back on: the anchor itself when it is still a place of the deck volume (lifted
	 * onto the deck if it sank into it), else the nearest standing spot of the deck. Never inside the hull nor in the sea.
	 */
	public static double[] restoreSpot(ShipGeometry geometry, InteriorGrid.State state, double lx, double ly, double lz) {
		if (Double.isFinite(lx) && Double.isFinite(ly) && Double.isFinite(lz) && geometry.inCarryVolume(lx, ly, lz)) {
			double top = geometry.deckRescueY(lx, ly, lz, state);
			return new double[] {lx, (Double.isNaN(top) ? ly : top) + 0.01, lz};
		}
		double[] spot = geometry.boardingSpot(Double.isFinite(lx) ? lx : 0, Double.isFinite(lz) ? lz : 0);
		return new double[] {spot[0], spot[1], spot[2]};
	}

	/** Dry ground of a world column: the height to stand at, or NaN (water, lava, void, unloaded...). */
	@FunctionalInterface
	public interface Column {
		double surface(int x, int z);
	}

	/**
	 * Nearest dry standing place around a point, searching square rings outwards (ends as soon as no farther ring can
	 * hold a nearer one), up to {@code radius} blocks. Returns {x, y, z} (block centre) or null.
	 */
	public static double[] nearestDry(int cx, int cz, int radius, Column column) {
		double[] best = {Double.MAX_VALUE};
		double[][] found = {null};
		for (int r = 0; r <= radius; r++) {
			if (found[0] != null && r > Math.sqrt(best[0])) {
				break; // every column of this ring and beyond is farther than the one found
			}
			if (r == 0) {
				probe(cx, cz, 0, 0, column, best, found);
				continue;
			}
			for (int d = -r; d <= r; d++) {
				probe(cx, cz, d, -r, column, best, found);
				probe(cx, cz, d, r, column, best, found);
				if (d > -r && d < r) {
					probe(cx, cz, -r, d, column, best, found);
					probe(cx, cz, r, d, column, best, found);
				}
			}
		}
		return found[0];
	}

	private static void probe(int cx, int cz, int dx, int dz, Column column, double[] best, double[][] found) {
		double d = (double) dx * dx + (double) dz * dz;
		if (d >= best[0]) {
			return;
		}
		double y = column.surface(cx + dx, cz + dz);
		if (!Double.isNaN(y)) {
			best[0] = d;
			found[0] = new double[] {cx + dx + 0.5, y, cz + dz + 0.5};
		}
	}
}
