package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** A named itinerary made of waypoints, created by administrators. */
public final class Route {
	public enum Mode {
		/** Goes to the last point and stops there. */
		ONCE,
		/** Goes from the last point back to the first one, forever. */
		LOOP,
		/** Aller-retour: first -> last -> first -> ... */
		PINGPONG;

		public static Mode byName(String s) {
			for (Mode m : values()) {
				if (m.name().equalsIgnoreCase(s)) {
					return m;
				}
			}
			return switch (s.toLowerCase(Locale.ROOT)) {
				case "allerretour", "aller-retour", "ferry" -> PINGPONG;
				case "boucle" -> LOOP;
				case "simple", "aller" -> ONCE;
				default -> null;
			};
		}
	}

	public String name;
	/** Dimension id, e.g. "minecraft:overworld". */
	public String dimension = "minecraft:overworld";
	public Mode mode = Mode.PINGPONG;
	public List<Waypoint> points = new ArrayList<>();

	public Route() {
	}

	public Route(String name, String dimension) {
		this.name = name;
		this.dimension = dimension;
	}

	public int size() {
		return points.size();
	}

	public Waypoint get(int i) {
		return points.get(Math.max(0, Math.min(points.size() - 1, i)));
	}

	public double totalLength() {
		double len = 0;
		for (int i = 1; i < points.size(); i++) {
			Waypoint a = points.get(i - 1), b = points.get(i);
			len += Math.hypot(b.x - a.x, b.z - a.z);
		}
		return len;
	}
}
