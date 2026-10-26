package fr.medievalships.core;

/**
 * "Go there": a destination given to one vessel ({@code /ship goto}, {@code /pilote goto}) is flown or sailed by the
 * existing autopilot, as a one-point route of its own ({@code goto-<first 8 characters of the vessel's UUID>},
 * mode once). The autopilot then does everything it does on a route: it heads there avoiding the obstacles, an
 * aircraft keeps its clearance over the relief and the buildings and climbs over them, it slows down near the
 * point, stops on it and holds its position (an aircraft comes down to its landing clearance over the ground);
 * the route is kept with the world, so the trip goes on after a restart. Taking the helm cancels it.
 */
public final class GotoRoutes {
	public static final String PREFIX = "goto-";

	private GotoRoutes() {
	}

	/** Name of the route of a vessel's destination. */
	public static String routeName(String vesselUuid) {
		String id = vesselUuid == null ? "" : vesselUuid.replace("-", "");
		return PREFIX + (id.length() > 8 ? id.substring(0, 8) : id);
	}

	/** Is this the route of a destination (rather than an administrator's route, a ferry)? */
	public static boolean isGoto(String routeName) {
		return routeName != null && routeName.startsWith(PREFIX);
	}

	/**
	 * The route to a destination: one point, at {@code (x, y, z)}, where the vessel stops for good. For an aircraft
	 * {@code y} is the height of its main deck there; a point under the ground is fine, the aircraft stops at its
	 * landing clearance over it.
	 */
	public static Route build(String routeName, String dimension, boolean air, String label, double x, double y, double z) {
		Route r = new Route(routeName, dimension);
		r.mode = Route.Mode.ONCE;
		r.air = air;
		r.points.add(new Waypoint(round(x), round(y), round(z), 0, label));
		return r;
	}

	/** Label of a destination given by its coordinates. */
	public static String label(double x, double y, double z, boolean air) {
		return air ? String.format(java.util.Locale.ROOT, "%d %d %d", Math.round(x), Math.round(y), Math.round(z))
				: String.format(java.util.Locale.ROOT, "%d %d", Math.round(x), Math.round(z));
	}

	private static double round(double v) {
		return Math.round(v * 10) / 10.0;
	}
}
