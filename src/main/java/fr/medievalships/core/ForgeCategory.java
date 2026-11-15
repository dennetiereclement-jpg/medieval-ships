package fr.medievalships.core;

import java.text.Normalizer;
import java.util.Locale;

/**
 * The five categories of the divine forge's recipes (1.34.0, JSON {@code "categorie"}), in the order of the forge's
 * interface: legendary weapons, divine armours, steampunk, rare items, upgrades. The id is what a recipe file names;
 * the label is what the interface shows.
 */
public enum ForgeCategory {
	ARMES_LEGENDAIRES("armes_legendaires", "Armes légendaires"),
	ARMURES_DIVINES("armures_divines", "Armures divines"),
	STEAMPUNK("steampunk", "Steampunk"),
	OBJETS_RARES("objets_rares", "Objets rares"),
	AMELIORATIONS("ameliorations", "Améliorations");

	private final String id;
	private final String label;

	ForgeCategory(String id, String label) {
		this.id = id;
		this.label = label;
	}

	/** The id written in a recipe ({@code armes_legendaires}...). */
	public String id() {
		return id;
	}

	/** The French label of the interface ({@code Armes légendaires}...). */
	public String label() {
		return label;
	}

	/**
	 * The category of an id, forgiving about case, accents, spaces and hyphens ({@code "Armes légendaires"},
	 * {@code "armes-legendaires"} and {@code "ARMES_LEGENDAIRES"} all give {@link #ARMES_LEGENDAIRES}); null when none.
	 */
	public static ForgeCategory byId(String id) {
		if (id == null) {
			return null;
		}
		String s = Normalizer.normalize(id.trim(), Normalizer.Form.NFD).replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT)
				.replace(' ', '_').replace('-', '_');
		for (ForgeCategory c : values()) {
			if (c.id.equals(s)) {
				return c;
			}
		}
		return null;
	}

	/** The category at an index (its ordinal), or {@link #OBJETS_RARES} for an index out of range (a bad packet). */
	public static ForgeCategory byIndex(int i) {
		ForgeCategory[] all = values();
		return i >= 0 && i < all.length ? all[i] : OBJETS_RARES;
	}
}
