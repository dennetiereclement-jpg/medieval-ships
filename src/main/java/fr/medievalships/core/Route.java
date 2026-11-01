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
		PINGPONG,
		/** One round trip: first -> last (waits there) -> back to the first point, and stops there. */
		RETURN;

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
				case "retour", "aller-retour-simple" -> RETURN;
				default -> null;
			};
		}
	}

	/** What becomes of the vessel when a {@link Mode#ONCE} or {@link Mode#RETURN} route ends. */
	public enum End {
		/** Stays moored at the last point (the autopilot is finished). */
		STAY,
		/** Waits the last stop's time (or the order to leave), lands the players, then vanishes. */
		DESPAWN,
		/** Like {@link #DESPAWN}, leaving its item on the spot. */
		DESPAWN_ITEM;

		public static End byName(String s) {
			for (End e : values()) {
				if (e.name().equalsIgnoreCase(s)) {
					return e;
				}
			}
			return switch (s.toLowerCase(Locale.ROOT)) {
				case "reste", "rester" -> STAY;
				case "disparait", "disparaît", "vanish" -> DESPAWN;
				case "despawn-item", "despawnitem", "item", "objet" -> DESPAWN_ITEM;
				default -> null;
			};
		}

		/** Does the vessel vanish at the end of its trip? */
		public boolean despawns() {
			return this != STAY;
		}
	}

	public String name;
	/** Dimension id, e.g. "minecraft:overworld". */
	public String dimension = "minecraft:overworld";
	public Mode mode = Mode.PINGPONG;
	/** Air route (for aircraft: the points' heights matter) or sea route (for ships). */
	public boolean air;
	/** End of the trip ({@link Mode#ONCE}, {@link Mode#RETURN}): stay there or vanish. Saves made before 1.10 have none: stay. */
	public End end = End.STAY;
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

	/** The end behaviour, {@link End#STAY} for a route saved without one. */
	public End end() {
		return end == null ? End.STAY : end;
	}

	/** Index of the first stop (where a vessel put on this route starts from), or 0 when there is no stop. */
	public int firstStop() {
		for (int i = 0; i < points.size(); i++) {
			if (points.get(i).isStop()) {
				return i;
			}
		}
		return 0;
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
