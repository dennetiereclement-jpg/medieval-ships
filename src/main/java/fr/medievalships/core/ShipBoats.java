package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * The ships' boats (1.30.0): every vessel that carries a boat on its deck (the great galleon, the great warship, the Old
 * Corsair, the Nautilus) puts a real Rowboat ({@link RowboatLayout}) on the water beside its hull and takes it back
 * aboard. Pure description and geometry, shared by the server (launching, recovering), the client (the click on the
 * boat, the hidden deco) and the tests.
 *
 * <p>Ship-local blocks as everywhere: x = lateral (+x = port), y = up, z = forward. The water level used for a launch is
 * the hull's own {@link HullShape#waterlineY}, read at run time (never copied here).
 */
public final class ShipBoats {
	/** Bit of {@code ShipEntity#toggle} set while the boat is away (the Nautilus' historic lifeboat bit, shared by all). */
	public static final int AWAY_BIT = Ships.NautilusLayout.LIFEBOAT_AWAY;
	/** Command tag of a launched ship's boat (also the Nautilus' historic one). */
	public static final String TAG = "medievalships_lifeboat";
	/** Free water kept between the hull and the launched boat's side (blocks). */
	public static final double CLEARANCE = 0.8;
	/** Further out, then along the hull, when the first spot is taken (a quay, another hull, a rock). */
	private static final double[] OUT_STEPS = {0.0, 1.0, 2.0};
	private static final double[] ALONG_STEPS = {0.0, 2.5, -2.5};
	/** The boat is taken back aboard within the hull's half width plus this much of its chocks, measured on the water. */
	public static final double RECOVER_MARGIN = 7.0;
	/** ...and at most this far above or below the ship's water line. */
	public static final double RECOVER_HEIGHT = 6.0;
	/** After a launch or a recovery the boat cannot be worked again for this long (two players clicking at once). */
	public static final int BUSY_TICKS = 40;
	/** The prefix of the boat's elements in a model where they share a bone with the deck, and what stays (its chocks). */
	public static final String SPLIT_PREFIX = "boat_";
	public static final List<String> SPLIT_KEEP = List.of("boat_chock", "boat_skid");

	/**
	 * A ship's boat.
	 *
	 * @param shipId      the ship type
	 * @param noun        its name in French ("chaloupe", "canot")
	 * @param feminine    for the articles and agreements of the messages
	 * @param bone        the bone of the deco boat hidden while it is away
	 * @param splitParent the bone whose {@link #SPLIT_PREFIX} elements make that bone when the model is loaded, or null
	 *                    when the model has the bone already
	 * @param deco        the deco boat on its chocks: the box a player clicks
	 * @param launchZ     where along the hull it is put on the water
	 * @param solid       the deck collision box of the deco boat (one can stand on it), dropped while it is away; or null
	 */
	public record Spec(String shipId, String noun, boolean feminine, String bone, String splitParent,
			ShipGeometry.LocalBox deco, double launchZ, ShipGeometry.LocalBox solid) {
		/** "la chaloupe", "le canot". */
		public String the() {
			return (feminine ? "la " : "le ") + noun;
		}

		/** "La chaloupe", "Le canot". */
		public String The() {
			return (feminine ? "La " : "Le ") + noun;
		}

		/** The pronoun: "la", "le". */
		public String it() {
			return feminine ? "la" : "le";
		}

		/** Agreement of a past participle: "e" or "". */
		public String e() {
			return feminine ? "e" : "";
		}
	}

	private static final Map<String, Spec> SPECS = Map.of(
			// the ship's boat stowed on chocks over the fore hatch (tools/generate_galleon.py, g_boat)
			"galleon", new Spec("galleon", "chaloupe", true, "deco_boat", "deck",
					new ShipGeometry.LocalBox(-0.85, 1.0, 4.2, 0.85, 2.1, 7.95), 6.0, null),
			// on its skids in the waist, between the main and fore masts; one walks on it
			"warship", new Spec("warship", "chaloupe", true, "deco_boat", "ship_boat",
					new ShipGeometry.LocalBox(-1.35, Ships.WarshipLayout.MAIN_DECK_Y, Ships.WarshipLayout.BOAT_Z0 - 0.2, 1.35,
							Ships.WarshipLayout.BOAT_TOP + 0.4, Ships.WarshipLayout.BOAT_Z1 + 0.5),
					(Ships.WarshipLayout.BOAT_Z0 + Ships.WarshipLayout.BOAT_Z1) / 2,
					new ShipGeometry.LocalBox(-Ships.WarshipLayout.BOAT_HALF, Ships.WarshipLayout.MAIN_DECK_Y, Ships.WarshipLayout.BOAT_Z0,
							Ships.WarshipLayout.BOAT_HALF, Ships.WarshipLayout.BOAT_TOP, Ships.WarshipLayout.BOAT_Z1)),
			// on two chocks on the quarterdeck (tools/generate_corsair.py, f_boat); launched along the quarter, clear of
			// the stern gallery
			"old_corsair", new Spec("old_corsair", "canot", false, "deco_boat", "sterncastle",
					new ShipGeometry.LocalBox(-0.8, CorsairLayout.QUARTERDECK_Y - 0.05, -20.4, 0.8, CorsairLayout.QUARTERDECK_Y + 1.1, -17.05),
					-15.0, null),
			// in its recess on the casing (bone "lifeboat" of the model)
			"nautilus", new Spec("nautilus", "canot", false, "lifeboat", null,
					new ShipGeometry.LocalBox(-1.3, Ships.NautilusLayout.LIFEBOAT_Y - 0.5, Ships.NautilusLayout.LIFEBOAT_Z - 3.45, 1.3,
							Ships.NautilusLayout.LIFEBOAT_Y + 0.75, Ships.NautilusLayout.LIFEBOAT_Z + 3.45),
					Ships.NautilusLayout.LIFEBOAT_Z, null));

	private ShipBoats() {
	}

	/** The boat of a ship type, or null if it carries none. */
	public static Spec of(String shipId) {
		return shipId == null ? null : SPECS.get(shipId);
	}

	/** Every ship's boat, by ship type id. */
	public static Map<String, Spec> all() {
		return SPECS;
	}

	/**
	 * Lateral distance from the keel line to the middle of a boat launched at {@code z}: the widest part of the hull
	 * along the boat's whole length, the boat's half beam and the clearance.
	 */
	public static double sideOffset(HullShape hull, double z) {
		double tip = RowboatLayout.TIP + 0.3;
		double w = 0;
		for (double zz = z - tip; zz <= z + tip + 1e-9; zz += 0.25) {
			w = Math.max(w, hull.halfWidth(zz));
		}
		return w + RowboatLayout.MAX_HALF_WIDTH + CLEARANCE;
	}

	/** The side a player is on (+1 port, -1 starboard) from his ship-local x; port when he stands on the middle line. */
	public static int sideOf(double localX) {
		return localX < -0.3 ? -1 : 1;
	}

	/**
	 * Where the boat may go on the water, in order of preference: {x, z, side} ship-local. The player's side first,
	 * abreast of the deco boat, then a bit further out, then a bit along the hull; then the other side the same way.
	 */
	public static List<double[]> launchCandidates(Spec spec, HullShape hull, int preferredSide) {
		int first = preferredSide < 0 ? -1 : 1;
		List<double[]> out = new ArrayList<>();
		for (int side : new int[] {first, -first}) {
			for (double o : OUT_STEPS) {
				for (double a : ALONG_STEPS) {
					double z = spec.launchZ() + a;
					out.add(new double[] {side * (sideOffset(hull, z) + o), z, side});
				}
			}
		}
		return out;
	}

	/** How far from its chocks (horizontally) the boat may be and still be taken back aboard. */
	public static double reach(Spec spec, HullShape hull) {
		return sideOffset(hull, spec.launchZ()) + RECOVER_MARGIN;
	}

	/** Is a boat at this ship-local point close enough to be hoisted aboard? */
	public static boolean inReach(Spec spec, HullShape hull, double lx, double ly, double lz) {
		double dx = lx - (spec.deco().minX() + spec.deco().maxX()) / 2, dz = lz - spec.launchZ();
		double r = reach(spec, hull);
		return dx * dx + dz * dz <= r * r && Math.abs(ly - hull.waterlineY) <= RECOVER_HEIGHT;
	}

	/**
	 * Ray (ship-local origin and direction) against the deco boat: the distance, or -1; never from inside its box (a
	 * player standing where the boat sits while it is away does not click it with every click).
	 */
	public static double pick(Spec spec, double[] o, double[] d, double maxDist) {
		ShipGeometry.LocalBox b = spec.deco();
		if (o[0] > b.minX() && o[0] < b.maxX() && o[1] > b.minY() && o[1] < b.maxY() && o[2] > b.minZ() && o[2] < b.maxZ()) {
			return -1;
		}
		double t = ShipGeometry.rayBox(o, d, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ());
		return t >= 0 && t <= maxDist ? t : -1;
	}

	/** Server check of a click: is the clicked point (ship-local) on or right next to the deco boat? */
	public static boolean nearDeco(Spec spec, double lx, double ly, double lz) {
		ShipGeometry.LocalBox b = spec.deco();
		double m = 1.0;
		return lx >= b.minX() - m && lx <= b.maxX() + m && ly >= b.minY() - m && ly <= b.maxY() + m && lz >= b.minZ() - m && lz <= b.maxZ() + m;
	}

	/**
	 * Is a world collision box one of the cells of the deco boat's solid (see {@link ShipGeometry#emitLocal})? Those
	 * are dropped while the boat is away: its middle is inside the solid's footprint and its height is the solid's.
	 * No allocation (the movement hook calls it for every box of the ship).
	 */
	public static boolean solidCell(Spec spec, ShipPose pose, double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
		ShipGeometry.LocalBox b = spec.solid();
		if (b == null || minY < pose.y() + b.minY() - 1e-3 || maxY > pose.y() + b.maxY() + 1e-3) {
			return false;
		}
		double c = pose.cos(), s = pose.sin();
		double dx = (minX + maxX) / 2 - pose.x(), dz = (minZ + maxZ) / 2 - pose.z();
		double lx = dx * c + dz * s, lz = -dx * s + dz * c;
		return lx > b.minX() && lx < b.maxX() && lz > b.minZ() && lz < b.maxZ();
	}
}
