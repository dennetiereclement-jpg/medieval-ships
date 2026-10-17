package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/** The ship types of the mod. */
public final class Ships {
	private Ships() {
	}

	// ------------------------------------------------------------------ medieval galley

	/** Medieval galley: 20 blocks, one lateen sail, 16 oars, 9 seats. Values must never change. */
	public static final ShipType GALLEY = galley();

	private static ShipType galley() {
		HullShape.Params p = new HullShape.Params(); // the defaults are the galley
		p.raisedDecks = List.of(
				new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, HullProfile.AFT_DECK_START, HullProfile.RAISED_DECK_Y),
				new HullShape.RaisedDeck(HullProfile.FORE_DECK_START, Double.POSITIVE_INFINITY, HullProfile.RAISED_DECK_Y));
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, HullProfile.RAISED_DECK_Y + 0.28, -8.05, true,
				new double[] {0.0, HullProfile.RAISED_DECK_Y + 0.02, -7.35}));
		double[] benchZ = {-4.8, -1.6, 1.6, 4.8};
		int i = 1;
		for (double z : benchZ) {
			for (double x : new double[] {1.0, -1.0}) {
				seats.add(new ShipGeometry.Seat(i++, x, HullProfile.MAIN_DECK_Y + 0.47, z, false,
						new double[] {x * 0.9, HullProfile.MAIN_DECK_Y + 0.02, z + 0.8}));
			}
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.5, HullProfile.RAISED_DECK_Y + 0.1, -8.6, 0.5, HullProfile.RAISED_DECK_Y + 1.1, -7.4);
		spec.masts = List.of(new ShipGeometry.Mast(0, HullProfile.MAST_Z, HullProfile.MAIN_DECK_Y, HullProfile.MAST_TOP, 0.2));
		spec.avoidZ = benchZ;
		return new ShipType("galley", "galère", new ShipGeometry(hull, spec), ShipConfig::new);
	}

	public static final List<ShipType> ALL = List.of(GALLEY);

	public static ShipType byId(String id) {
		for (ShipType t : ALL) {
			if (t.id().equalsIgnoreCase(id)) {
				return t;
			}
		}
		return null;
	}
}
