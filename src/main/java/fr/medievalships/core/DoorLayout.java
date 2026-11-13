package fr.medievalships.core;

/**
 * Where a door's cells are and how its model is placed (pure Java, tested in JUnit). The facing is given in quarter
 * turns like the props' ({@link TentType}): 0 = the front faces south (+z), 1 = west (-x), 2 = north (-z), 3 = east
 * (+x); the front faces the player who placed the door. Seen from the front, the columns go to the right
 * ({@link #right}: east for a door facing south) and the rows up; the controller block is column 0, row 0 (bottom
 * left seen from the front). The opening is centred on the aimed cell: a door 2 wide takes the aimed cell and the
 * one to its right, a door 4 wide the cells -1 to +2 ({@link #startColumn}).
 *
 * <p>The model is drawn turned like a prop ({@code -90 x quarter} degrees about y, so that model +z is the front and
 * model +x the right), its origin at the middle of the bottom of the opening: {@link #originX} / {@link #originZ}.
 */
public final class DoorLayout {
	private DoorLayout() {
	}

	/** Unit vector (x, z) of the front of a door of this facing. */
	public static int[] front(int quarter) {
		return switch (Math.floorMod(quarter, 4)) {
			case 0 -> new int[] {0, 1};
			case 1 -> new int[] {-1, 0};
			case 2 -> new int[] {0, -1};
			default -> new int[] {1, 0};
		};
	}

	/** Unit vector (x, z) to the right seen from the front (the direction of the columns). */
	public static int[] right(int quarter) {
		int[] f = front(quarter);
		return new int[] {f[1], -f[0]};
	}

	/** Column of the aimed cell's left neighbour that becomes column 0: 0 for widths 1 and 2, -1 for width 4. */
	public static int startColumn(int width) {
		return -((width - 1) / 2);
	}

	/** The controller block (column 0, row 0) of a door placed with the aimed cell {@code (x, y, z)}. */
	public static int[] controllerFromTarget(int x, int y, int z, int quarter, int width) {
		int[] r = right(quarter);
		int s = startColumn(width);
		return new int[] {x + r[0] * s, y, z + r[1] * s};
	}

	/** The block of column {@code col}, row {@code row} of a door whose controller is at {@code (cx, cy, cz)}. */
	public static int[] cell(int cx, int cy, int cz, int quarter, int col, int row) {
		int[] r = right(quarter);
		return new int[] {cx + r[0] * col, cy + row, cz + r[1] * col};
	}

	/** The controller of the door whose cell (column {@code col}, row {@code row}) is at {@code (x, y, z)}. */
	public static int[] controllerFromCell(int x, int y, int z, int quarter, int col, int row) {
		int[] r = right(quarter);
		return new int[] {x - r[0] * col, y - row, z - r[1] * col};
	}

	/** Every cell of a door, column by column, bottom up: {x, y, z, col, row} each. */
	public static int[][] cells(int cx, int cy, int cz, int quarter, int width, int height) {
		int[][] out = new int[width * height][];
		int i = 0;
		for (int col = 0; col < width; col++) {
			for (int row = 0; row < height; row++) {
				int[] c = cell(cx, cy, cz, quarter, col, row);
				out[i++] = new int[] {c[0], c[1], c[2], col, row};
			}
		}
		return out;
	}

	/** World x of the model origin (middle of the bottom of the opening) of a door whose controller is at cx. */
	public static double originX(int cx, int quarter, int width) {
		return cx + 0.5 + right(quarter)[0] * (width - 1) / 2.0;
	}

	/** World z of the model origin. */
	public static double originZ(int cz, int quarter, int width) {
		return cz + 0.5 + right(quarter)[1] * (width - 1) / 2.0;
	}

	/** A model-local point (lx right, ly up, lz front) in the world: {x, y, z}. */
	public static double[] toWorld(int cx, int cy, int cz, int quarter, int width, double lx, double ly, double lz) {
		int[] r = right(quarter), f = front(quarter);
		return new double[] {originX(cx, quarter, width) + r[0] * lx + f[0] * lz, cy + ly, originZ(cz, quarter, width) + r[1] * lx + f[1] * lz};
	}

	/**
	 * The world box {minX, minY, minZ, maxX, maxY, maxZ} of a model-local box (x0..x1 right, y0..y1 up, z0..z1 front)
	 * of a door whose controller is at {@code (cx, cy, cz)}.
	 */
	public static double[] worldBox(int cx, int cy, int cz, int quarter, int width, double x0, double y0, double z0, double x1, double y1, double z1) {
		double[] a = toWorld(cx, cy, cz, quarter, width, x0, y0, z0);
		double[] b = toWorld(cx, cy, cz, quarter, width, x1, y1, z1);
		return new double[] {Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.min(a[2], b[2]), Math.max(a[0], b[0]), Math.max(a[1], b[1]),
				Math.max(a[2], b[2])};
	}

	/**
	 * The model-local box {x0, y0, z0, x1, y1, z1} a closing door may hit: the opening (its whole thickness) and the
	 * quarter circles its leaves sweep, behind it ({@code backward}) or in front of it.
	 */
	public static double[] sweptLocal(DoorType type, boolean backward) {
		double hw = type.width() / 2.0, lw = type.leafSpan();
		return backward ? new double[] {-hw, 0, -lw, hw, type.height(), 0.5} : new double[] {-hw, 0, -0.5, hw, type.height(), lw};
	}

	/** The world box of {@link #sweptLocal}. */
	public static double[] sweptWorld(DoorType type, int cx, int cy, int cz, int quarter, boolean backward) {
		double[] l = sweptLocal(type, backward);
		return worldBox(cx, cy, cz, quarter, type.width(), l[0], l[1], l[2], l[3], l[4], l[5]);
	}

	/**
	 * The angle (degrees, a right-handed rotation about the model's y axis through the leaf's hinge) of a leaf at an
	 * eased progress 0..1: the left leaf turns +90 to open backwards (its free edge goes to -z), the right leaf -90;
	 * forwards, the other way.
	 */
	public static float leafAngle(boolean left, boolean backward, double eased) {
		double a = 90.0 * eased;
		return (float) ((left == backward) ? a : -a);
	}

	/** The hinge x (model-local) of the left or right leaf (the server's value; the renderer reads the model's pivots). */
	public static double hingeX(DoorType type, boolean left) {
		return left ? -type.hingeX() : type.hingeX();
	}

	/** Parses a French or English facing word (nord, sud, est, ouest / north...) into a quarter, or -1. */
	public static int quarterOf(String word) {
		if (word == null) {
			return -1;
		}
		return switch (word.trim().toLowerCase(java.util.Locale.ROOT)) {
			case "sud", "south", "s" -> 0;
			case "ouest", "west", "o", "w" -> 1;
			case "nord", "north", "n" -> 2;
			case "est", "east", "e" -> 3;
			default -> -1;
		};
	}

	/** French name of a facing. */
	public static String facingFr(int quarter) {
		return switch (Math.floorMod(quarter, 4)) {
			case 0 -> "sud";
			case 1 -> "ouest";
			case 2 -> "nord";
			default -> "est";
		};
	}
}
