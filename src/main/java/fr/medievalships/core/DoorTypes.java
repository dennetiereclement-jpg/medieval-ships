package fr.medievalships.core;

import java.util.List;
import java.util.Locale;

import fr.medievalships.core.DoorType.Material;

/**
 * The ten doors of 1.31.0 (one block and one item each, {@code medievalships:<id>}, tab "Portes"): three small ones
 * (2 high, 1 wide, one leaf, 10 ticks), four medium ones (4 high, 2 wide, two leaves, 20 ticks) and three great gates
 * (6 high, 4 wide, two leaves of 2, 60 ticks: slow and heavy). {@link #ALL} in the order of the creative tab.
 */
public final class DoorTypes {
	public static final int SMALL_TICKS = 10;
	public static final int MEDIUM_TICKS = 20;
	public static final int LARGE_TICKS = 60;
	/**
	 * Hinges' distance from the middle (the pivots of the models): small doors 0.40625 (a leaf of 13 px in a 1 block
	 * opening), medium doors 0.75 (two leaves of 0.75 in 2 blocks), great gates 1.625 (two leaves of 1.625 in 4 blocks).
	 */
	public static final double SMALL_HINGE = 0.40625, MEDIUM_HINGE = 0.75, LARGE_HINGE = 1.625;

	public static final DoorType OAK = small("porte_chene", "porte en chêne", "Medieval Oak Door", Material.WOOD, false);
	public static final DoorType PRISON = small("porte_prison", "porte de prison", "Prison Door", Material.METAL, false);
	public static final DoorType STEAM = small("porte_vapeur", "porte à vapeur", "Steam Door", Material.STEAM, true);

	public static final DoorType BARN = medium("porte_grange", "porte de grange", "Barn Door", Material.WOOD, false);
	public static final DoorType FORTRESS = medium("porte_forteresse", "porte de forteresse", "Fortress Door", Material.WOOD, false);
	public static final DoorType INDUSTRIAL = medium("porte_industrielle", "porte industrielle", "Industrial Door", Material.STEAM, true);
	public static final DoorType MERCHANT = medium("porte_marchande", "porte marchande", "Merchant Door", Material.WOOD, false);

	public static final DoorType CASTLE = large("porte_chateau", "porte de château", "Castle Gate", Material.WOOD, false);
	public static final DoorType GREAT_STEAM = large("porte_vapeur_grande", "grande porte à vapeur", "Great Steam Gate", Material.STEAM, true);
	public static final DoorType WAREHOUSE = large("porte_entrepot", "porte d'entrepôt", "Warehouse Gate", Material.WOOD, false);

	/** The ten doors, in the order of the creative tab. */
	public static final List<DoorType> ALL = List.of(OAK, PRISON, STEAM, BARN, FORTRESS, INDUSTRIAL, MERCHANT, CASTLE, GREAT_STEAM, WAREHOUSE);

	private DoorTypes() {
	}

	private static DoorType small(String id, String fr, String en, Material material, boolean steam) {
		return new DoorType(id, fr, en, 2, 1, 1, SMALL_TICKS, material, steam, SMALL_HINGE);
	}

	private static DoorType medium(String id, String fr, String en, Material material, boolean steam) {
		return new DoorType(id, fr, en, 4, 2, 2, MEDIUM_TICKS, material, steam, MEDIUM_HINGE);
	}

	private static DoorType large(String id, String fr, String en, Material material, boolean steam) {
		return new DoorType(id, fr, en, 6, 4, 2, LARGE_TICKS, material, steam, LARGE_HINGE);
	}

	/** The door of an id ({@code "porte_chene"}, {@code "medievalships:porte_chene"}, any case), or null. */
	public static DoorType byId(String id) {
		if (id == null) {
			return null;
		}
		String k = id.trim().toLowerCase(Locale.ROOT);
		if (k.startsWith("medievalships:")) {
			k = k.substring("medievalships:".length());
		}
		for (DoorType t : ALL) {
			if (t.id().equals(k)) {
				return t;
			}
		}
		return null;
	}
}
