package fr.medievalships.core;

/**
 * One of the ten doors of 1.31.0 (pure Java, tested in JUnit): its id (block, item, model and texture are all named
 * after it), its opening (height x width in blocks, the cells the door occupies), its leaves (one, or two of half the
 * width), the duration of a full movement, the material of its sounds, whether it lets out steam, and its names.
 *
 * <p>Model frame (the contract of the generators, tools/doors): model-local blocks, the origin at the middle of the
 * bottom of the opening, in the middle of its thickness; x = width (+x = to the right seen from the front), y = up
 * (0 to {@link #height}), z = thickness (+z = the front, towards the player who placed the door). Bones {@code frame},
 * {@code leaf_l} (pivot on its hinge edge, x = -width / 2), {@code leaf_r} (x = +width / 2), the animated children
 * {@code gear_a_*}, {@code gear_b_*}, {@code bolt_*}, {@code piston_*}, the full-bright cubes {@code glow*} and the
 * small {@code detail} bone.
 */
public final class DoorType {
	/** What a door sounds like: a wooden door, an iron door, an iron door with a piston and gears. */
	public enum Material {
		WOOD, METAL, STEAM
	}

	/** The three sizes of the contract. */
	public enum Size {
		SMALL, MEDIUM, LARGE
	}

	private final String id;
	private final String nameFr;
	private final String nameEn;
	private final int height;
	private final int width;
	private final int leaves;
	private final int durationTicks;
	private final Material material;
	private final boolean steam;
	private final double hingeX;

	public DoorType(String id, String nameFr, String nameEn, int height, int width, int leaves, int durationTicks, Material material, boolean steam,
			double hingeX) {
		if (height < 1 || height > 6 || width < 1 || width > 4 || (leaves != 1 && leaves != 2) || width % leaves != 0 || durationTicks < 1
				|| hingeX <= 0 || hingeX > width / 2.0) {
			throw new IllegalArgumentException("bad door " + id);
		}
		this.id = id;
		this.nameFr = nameFr;
		this.nameEn = nameEn;
		this.height = height;
		this.width = width;
		this.leaves = leaves;
		this.durationTicks = durationTicks;
		this.material = material;
		this.steam = steam;
		this.hingeX = hingeX;
	}

	public String id() {
		return id;
	}

	/** French name, lower case ("porte de prison"). */
	public String nameFr() {
		return nameFr;
	}

	public String nameEn() {
		return nameEn;
	}

	/** Height of the opening (blocks, rows). */
	public int height() {
		return height;
	}

	/** Width of the opening (blocks, columns). */
	public int width() {
		return width;
	}

	/** Number of leaves: 1 ({@code leaf_l} only) or 2 ({@code leaf_l} and {@code leaf_r}). */
	public int leaves() {
		return leaves;
	}

	/** Width of one leaf's share of the opening (blocks). */
	public int leafWidth() {
		return width / leaves;
	}

	/** Distance (blocks) of the hinges from the middle of the opening: the pivot x of {@code leaf_l} is -hingeX, of {@code leaf_r} +hingeX. */
	public double hingeX() {
		return hingeX;
	}

	/** Width of a leaf itself (blocks): from its hinge to the middle (two leaves) or to the other side (one leaf). */
	public double leafSpan() {
		return leaves == 1 ? 2 * hingeX : hingeX;
	}

	/** Ticks of a full movement (closed to open or back). */
	public int durationTicks() {
		return durationTicks;
	}

	public Material material() {
		return material;
	}

	/** Does it let out a few puffs of steam when it starts and stops moving? */
	public boolean steam() {
		return steam;
	}

	public Size size() {
		return width >= 4 ? Size.LARGE : width >= 2 ? Size.MEDIUM : Size.SMALL;
	}

	/** Cells of the opening (width x height): the controller block and the parts. */
	public int cells() {
		return width * height;
	}

	/** Pitch of its sounds: the bigger the door, the deeper. */
	public float soundPitch() {
		return switch (size()) {
			case SMALL -> 1.0f;
			case MEDIUM -> 0.8f;
			case LARGE -> 0.6f;
		};
	}

	/** Its model, relative to {@code assets/medievalships/}. */
	public String model() {
		return "models/entity/" + id + ".bbmodel";
	}

	/** Its texture (its own, one per door), relative to {@code assets/medievalships/}. */
	public String texture() {
		return "textures/entity/" + id + ".png";
	}

	/** Its 16 x 16 item icon, relative to {@code assets/medievalships/}. */
	public String itemTexture() {
		return "textures/item/" + id + ".png";
	}

	/** Full turns of the gears over a whole movement (the big gates' gears turn more). */
	public int gearTurns() {
		return size() == Size.LARGE ? 2 : 1;
	}

	@Override
	public String toString() {
		return id;
	}
}
