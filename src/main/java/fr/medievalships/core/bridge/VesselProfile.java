package fr.medievalships.core.bridge;

/**
 * How a kind of vessel is measured for the drawbridges when its native data are not enough, or to correct them
 * ({@code "drawbridges": {"profiles": {...}}} in {@code config/medievalships.json}, one entry per ship type id such as
 * {@code "galley"}, per entity type id such as {@code "minecraft:oak_boat"}, or {@code "vanilla_boat"} for every
 * vanilla boat and raft). Every field is optional.
 */
public final class VesselProfile {
	/** Height of the top above the water, blocks, replacing the measured one (null: measured from the model). */
	public Double height;
	/** Added to the measured (or given) height: a mast the hitbox does not know, a figurehead... */
	public double heightOffset;
	/** Full width across, blocks, replacing the measured one (null: measured). */
	public Double width;
	/** Add the occupants' heads (seated passengers, people standing on deck) to the height. */
	public boolean occupants = true;
	/** Never opens the bridge nor is held by it (a decorative vehicle, a kind that always passes). */
	public boolean ignore;

	public VesselProfile() {
	}

	public VesselProfile(Double height, double heightOffset, Double width, boolean occupants, boolean ignore) {
		this.height = height;
		this.heightOffset = heightOffset;
		this.width = width;
		this.occupants = occupants;
		this.ignore = ignore;
	}

	public void sanitize() {
		if (height != null && (height.isNaN() || height < 0 || height > 256)) {
			height = null;
		}
		if (Double.isNaN(heightOffset)) {
			heightOffset = 0;
		}
		heightOffset = Math.max(-64, Math.min(64, heightOffset));
		if (width != null && (width.isNaN() || width <= 0 || width > 256)) {
			width = null;
		}
	}

	/** The top above the water of a vessel measured at {@code measured} blocks, by this profile. */
	public double height(double measured) {
		return (height != null ? height : measured) + heightOffset;
	}

	/** The full width of a vessel measured at {@code measured} blocks, by this profile. */
	public double width(double measured) {
		return width != null ? width : measured;
	}
}
