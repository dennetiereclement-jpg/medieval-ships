package fr.medievalships.core;

import java.util.function.Supplier;

/**
 * A kind of ship: its id (used for entities, items, models and config sections), its geometry and
 * its default navigation settings.
 */
public record ShipType(String id, String frenchName, ShipGeometry geometry, Supplier<ShipConfig> defaults) {
	public HullShape hull() {
		return geometry.hull();
	}
}
