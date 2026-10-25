package fr.medievalships.core;

/**
 * A hull box as a collider for an entity whose box already overlaps it by a hair.
 * <p>
 * The cells of a hull are given to the collision code as world boxes covering the rotated cells: when the ship
 * turns they change shape (wider towards 45 degrees), and its yaw on a client moves by small steps; a player pressed
 * against a wall, or standing on a floor, can then end up a hundredth of a block inside it. The vanilla collision code
 * ignores a collider the moving box already overlaps: he would walk through that wall (the shaft of the Sky
 * Leviathan's tower while it still turned after a turn) or sink through that floor. So the box is cut back to his side
 * along the axis of the smallest overlap, and keeps stopping him. Deeper overlaps (a door shut on him...) are left as
 * they are, so he can always get out.
 */
public final class HullContact {
	/** Deepest overlap still taken for a contact (blocks). */
	public static final double DEPTH = 0.1;

	private HullContact() {
	}

	/**
	 * @param body the moving entity's box (minX, minY, minZ, maxX, maxY, maxZ), or null
	 * @param box  the hull box, same order
	 * @return the box to collide with (the same array, possibly cut back), or null for a sliver to drop
	 */
	public static double[] clip(double[] body, double[] box) {
		if (body == null) {
			return box;
		}
		double m = Double.MAX_VALUE;
		int axis = -1;
		for (int a : new int[] {1, 0, 2}) {   // on a tie, a floor or a ceiling rather than a wall
			double o = Math.min(box[a + 3], body[a + 3]) - Math.max(box[a], body[a]);
			if (o <= 1e-7) {
				return box; // not overlapping: an ordinary collider
			}
			if (o < m) {
				m = o;
				axis = a;
			}
		}
		if (m > DEPTH) {
			return box;
		}
		if (body[axis] + body[axis + 3] > box[axis] + box[axis + 3]) {
			box[axis + 3] = body[axis]; // the box is on the low side of the body
		} else {
			box[axis] = body[axis + 3];
		}
		return box[axis + 3] - box[axis] < 1e-3 ? null : box;
	}
}
