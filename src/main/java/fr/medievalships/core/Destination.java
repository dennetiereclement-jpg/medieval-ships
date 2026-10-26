package fr.medievalships.core;

/**
 * A saved destination ({@code /ship destination add <name>}): a named place in a dimension, where a vessel sent
 * there with {@code /ship goto destination <name>} or {@code /pilote goto destination <name>} stops. For an aircraft
 * {@code y} is the height of its main deck there (as for the points of an air route).
 */
public final class Destination {
	public String name;
	public String dimension = "minecraft:overworld";
	public double x;
	public double y;
	public double z;

	public Destination() {
	}

	public Destination(String name, String dimension, double x, double y, double z) {
		this.name = name;
		this.dimension = dimension;
		this.x = x;
		this.y = y;
		this.z = z;
	}
}
