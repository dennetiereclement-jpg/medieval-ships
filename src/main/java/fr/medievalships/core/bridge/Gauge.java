package fr.medievalships.core.bridge;

import java.util.Locale;

/**
 * Does a vessel fit under the closed deck, and between the towers? The decision uses the vessel's real envelope
 * (hull, superstructure, masts and other high parts, occupants when their heads make it higher: see
 * {@link Envelope}), the measured underside of the closed deck over the navigable band, the water surface, a
 * configurable margin, and the navigable width. Pure: the game code builds the envelopes.
 */
public final class Gauge {
	private Gauge() {
	}

	public enum Verdict {
		/** Fits under the closed deck with the margin: the bridge stays closed. */
		PASSE_DESSOUS,
		/** Higher than the free height: the leaves must rise. */
		OUVERTURE_REQUISE,
		/** Wider than the channel between the towers: opening does not help, the vessel must wait. */
		TROP_LARGE
	}

	/**
	 * A vessel as the bridge sees it, in world coordinates.
	 *
	 * @param x y z          its position (hull origin)
	 * @param topY           world height of its highest point, occupants included when they are higher
	 * @param reachAlong     half extent along the channel (from the position to the farthest part towards the bridge)
	 * @param halfAcross     half extent across the channel
	 * @param footprintRadius radius of a horizontal circle enclosing the hull (coarse checks)
	 * @param label          what to call it in messages (name or type)
	 * @param detail         how the top was found ("mât 13,2 ; occupant +0,0"), for the debug display
	 */
	public record Envelope(double x, double y, double z, double topY, double reachAlong, double halfAcross, double footprintRadius,
			String label, String detail) {
	}

	/**
	 * @param verdict        the decision
	 * @param freeHeight     free height between the water surface and the underside of the closed deck
	 * @param vesselHeight   height of the vessel's top above the water surface
	 * @param widthNeeded    the vessel's extent across the channel (full width)
	 * @param widthAvailable the navigable width between the towers
	 * @param reason         one line in French for the debug display
	 */
	public record Decision(Verdict verdict, double freeHeight, double vesselHeight, double widthNeeded, double widthAvailable, String reason) {
		public boolean opens() {
			return verdict == Verdict.OUVERTURE_REQUISE;
		}
	}

	/**
	 * @param e                 the vessel
	 * @param undersideY        world height of the lowest underside of the closed deck over the navigable band
	 * @param waterY            world height of the water surface
	 * @param margin            safety margin (blocks) kept between the vessel's top and the underside
	 * @param navigableHalfWidth half of the navigable width between the towers
	 */
	public static Decision decide(Envelope e, double undersideY, double waterY, double margin, double navigableHalfWidth) {
		double free = undersideY - waterY;
		double height = e.topY() - waterY;
		double width = 2 * e.halfAcross();
		double available = 2 * navigableHalfWidth;
		if (e.halfAcross() > navigableHalfWidth) {
			return new Decision(Verdict.TROP_LARGE, free, height, width, available, String.format(Locale.ROOT,
					"%s : largeur %.1f > chenal %.1f : ne passe pas entre les tours, même pont ouvert", e.label(), width, available));
		}
		if (e.topY() + margin > undersideY) {
			return new Decision(Verdict.OUVERTURE_REQUISE, free, height, width, available, String.format(Locale.ROOT,
					"%s : haut à %.2f au-dessus de l'eau + marge %.2f > hauteur libre %.2f : ouverture requise (%s)", e.label(), height, margin, free,
					e.detail()));
		}
		return new Decision(Verdict.PASSE_DESSOUS, free, height, width, available, String.format(Locale.ROOT,
				"%s : haut à %.2f + marge %.2f <= hauteur libre %.2f : passe sous le pont fermé (%s)", e.label(), height, margin, free, e.detail()));
	}
}
