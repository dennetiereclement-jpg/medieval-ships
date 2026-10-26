package fr.medievalships.core;

/**
 * "Go there": a destination given to one vessel ({@code /ship goto}, {@code /pilote goto}) is flown or sailed by the
 * existing autopilot, as a one-point route of its own ({@code goto-<first 8 characters of the vessel's UUID>},
 * mode once). The autopilot then does everything it does on a route: it heads there avoiding the obstacles, an
 * aircraft keeps its clearance over the relief and the buildings and climbs over them, it slows down near the
 * point, stops on it and holds its position (an aircraft comes down to its landing clearance over the ground).
 * Taking the helm cancels it, and so does a destination the vessel cannot reach (the autopilot reports it stuck).
 *
 * <p>Who gave it matters: an administrator's destination ({@code /ship goto}) is run like a ferry (its chunks kept
 * loaded, reloaded after a restart); a player's ({@code /pilote goto}) only while players are aboard: it loads no
 * chunks, and it is cancelled once nobody has been aboard for {@link #UNATTENDED_TICKS} ticks.
 */
public final class GotoRoutes {
	public static final String PREFIX = "goto-";
	/** A player's destination is cancelled once nobody has been aboard for this long (10 s). */
	public static final int UNATTENDED_TICKS = 200;

	private GotoRoutes() {
	}

	/** Name of the route of a vessel's destination. */
	public static String routeName(String vesselUuid) {
		String id = vesselUuid == null ? "" : vesselUuid.replace("-", "");
		return PREFIX + (id.length() > 8 ? id.substring(0, 8) : id);
	}

	/**
	 * Is this the route of a destination (rather than an administrator's route, a ferry)? The prefix is reserved:
	 * {@code /ship route create} refuses it and {@code /ship route assign} never gives such a route to a vessel.
	 */
	public static boolean isGoto(String routeName) {
		return routeName != null && routeName.toLowerCase(java.util.Locale.ROOT).startsWith(PREFIX);
	}

	/** Why a destination is refused (the commands turn it into a French message). */
	public enum Refusal {
		/** The vessel follows an administrator's route (a ferry). */
		FERRY,
		/** The vessel is assigned an administrator's route whose autopilot is paused ({@code /ship ai disable}). */
		PAUSED_FERRY,
		/** Someone else holds the helm. */
		HELM_TAKEN,
		/** Farther than {@code playerDestinationMaxDistance}. */
		TOO_FAR,
		/** The Nautilus follows underwater routes only. */
		SUBMARINE
	}

	/**
	 * May a player give this vessel a destination ({@code /pilote goto}, {@code /pilote stop})? Admins always may.
	 * Never a vessel on an administrator's route, even paused (its assignment would be lost), never against someone
	 * else at the helm.
	 *
	 * @param autopilotOn the vessel's autopilot is on
	 * @param routeName the route the vessel is assigned (null: none)
	 * @param otherPilot someone (another player, a captain) is at the helm
	 * @return null if he may
	 */
	public static Refusal vesselRefusal(boolean admin, boolean autopilotOn, String routeName, boolean otherPilot) {
		if (admin) {
			return null;
		}
		if (autopilotOn && !isGoto(routeName)) {
			return Refusal.FERRY;
		}
		if (routeName != null && !isGoto(routeName)) {
			return Refusal.PAUSED_FERRY;
		}
		return otherPilot ? Refusal.HELM_TAKEN : null;
	}

	/**
	 * May this destination be given? Never to a submarine; for a player who is not an admin, at most
	 * {@code maxDistance} blocks away (horizontally).
	 *
	 * @return null if it may
	 */
	public static Refusal destinationRefusal(boolean privileged, double distance, double maxDistance, boolean submarine) {
		if (submarine) {
			return Refusal.SUBMARINE;
		}
		return !privileged && distance > maxDistance ? Refusal.TOO_FAR : null;
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
