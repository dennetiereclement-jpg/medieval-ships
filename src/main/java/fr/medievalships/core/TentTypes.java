package fr.medievalships.core;

import java.util.List;


/** The six tents. One line per tent: its id (block, item, model, decor and tents JSON are all named after it) and its names. */
public final class TentTypes {
	public static final TentType COMMAND = TentType.load("tent_command", "grande tente de commandement", "Command Tent");
	public static final TentType ADVENTURER = TentType.load("tent_adventurer", "petite tente d'aventurier", "Adventurer Tent");
	public static final TentType MARKET = TentType.load("tent_market", "grand abri de marché", "Market Awning");
	public static final TentType CAMP = TentType.load("tent_camp", "tente triangulaire de campement", "Camp Tent");
	public static final TentType DWELLING = TentType.load("tent_dwelling", "tente d'habitation", "Dwelling Tent");
	public static final TentType CHIEF = TentType.load("tent_chief", "grande tente de chef", "Chief's Pavilion");
	public static final List<TentType> ALL = List.of(COMMAND, ADVENTURER, MARKET, CAMP, DWELLING, CHIEF);

	private TentTypes() {
	}

	public static TentType byId(String id) {
		if (id == null) {
			return null;
		}
		String s = id.trim().toLowerCase(java.util.Locale.ROOT);
		if (s.startsWith("medievalships:")) {
			s = s.substring("medievalships:".length());
		}
		for (TentType t : ALL) {
			if (t.id().equals(s) || t.id().equals("tent_" + s)) {
				return t;
			}
		}
		return null;
	}
}
