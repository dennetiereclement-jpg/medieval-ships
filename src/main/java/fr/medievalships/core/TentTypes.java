package fr.medievalships.core;

import java.util.List;


/**
 * The twelve tents (six camp tents, six merchant tents), the eight carts and the seven crafting workshops. One line per
 * prop: its id (block, item, model, decor and tents / carts / workshops JSON are all named after it) and its names.
 * {@link #ALL} = the tents only (their tab "Tentes": the six camp tents then the six {@link #MERCHANTS}),
 * {@link #CARTS} = the carts (tab "Charrettes"), {@link #WORKSHOPS} = the workshops (tab "Ateliers"), {@link #PROPS} =
 * all three (registration, commands, models).
 */
public final class TentTypes {
	public static final TentType COMMAND = TentType.load("tent_command", "grande tente de commandement", "Command Tent");
	public static final TentType ADVENTURER = TentType.load("tent_adventurer", "petite tente d'aventurier", "Adventurer Tent");
	public static final TentType MARKET = TentType.load("tent_market", "grand abri de marché", "Market Awning");
	public static final TentType CAMP = TentType.load("tent_camp", "tente triangulaire de campement", "Camp Tent");
	public static final TentType DWELLING = TentType.load("tent_dwelling", "tente d'habitation", "Dwelling Tent");
	public static final TentType CHIEF = TentType.load("tent_chief", "grande tente de chef", "Chief's Pavilion");

	public static final TentType MERCHANT_ARMOURER = TentType.load("tente_armurier", "tente du marchand d'armes et d'armures",
			"Weapon & Armour Merchant Tent");
	public static final TentType MERCHANT_ALCHEMIST = TentType.load("tente_alchimiste", "tente du marchand d'alchimie", "Alchemy Merchant Tent");
	public static final TentType MERCHANT_HERBALIST = TentType.load("tente_herboriste", "tente de l'herboriste", "Herbalist Tent");
	public static final TentType MERCHANT_BLACKSMITH = TentType.load("tente_forgeron", "tente du forgeron", "Blacksmith Merchant Tent");
	public static final TentType MERCHANT_FOOD = TentType.load("tente_nourriture", "tente du marchand de nourriture", "Food Merchant Tent");
	public static final TentType MERCHANT_CLOTH = TentType.load("tente_tissus", "tente du marchand de tissus", "Cloth Merchant Tent");
	/** The six merchant tents (1.14.0): group "tents", each with its own atlas (textures/entity/<id>.png). */
	public static final List<TentType> MERCHANTS = List.of(MERCHANT_ARMOURER, MERCHANT_ALCHEMIST, MERCHANT_HERBALIST, MERCHANT_BLACKSMITH,
			MERCHANT_FOOD, MERCHANT_CLOTH);

	/** The tents only (tab "Tentes"): the six camp tents, then the six merchant tents. */
	public static final List<TentType> ALL = java.util.stream.Stream.of(List.of(COMMAND, ADVENTURER, MARKET, CAMP, DWELLING, CHIEF), MERCHANTS)
			.flatMap(List::stream).toList();

	public static final TentType CART_COVERED_WHITE = cart("cart_covered_white", "charrette couverte blanche", "White Covered Wagon");
	public static final TentType CART_HAY = cart("cart_hay", "charrette de foin", "Hay Cart");
	public static final TentType CART_MERCHANT_WAGON = cart("cart_merchant_wagon", "roulotte de marchand", "Merchant Wagon");
	public static final TentType CART_MARKET = cart("cart_market", "charrette de marché", "Market Cart");
	public static final TentType CART_LOGS = cart("cart_logs", "charrette de bûcheron", "Log Cart");
	public static final TentType CART_OPEN = cart("cart_open", "charrette de transport", "Open Cart");
	public static final TentType CART_COVERED_TEAL = cart("cart_covered_teal", "charrette couverte turquoise", "Teal Covered Wagon");
	public static final TentType CART_BARRELS = cart("cart_barrels", "charrette à tonneaux", "Barrel Cart");
	public static final List<TentType> CARTS = List.of(CART_COVERED_WHITE, CART_HAY, CART_MERCHANT_WAGON, CART_MARKET, CART_LOGS, CART_OPEN,
			CART_COVERED_TEAL, CART_BARRELS);

	public static final TentType WORKSHOP_BLACKSMITH = workshop("workshop_blacksmith", "atelier du forgeron", "Blacksmith's Workshop");
	public static final TentType WORKSHOP_LEATHERWORKER = workshop("workshop_leatherworker", "atelier du tailleur de cuir", "Leatherworker's Workshop");
	public static final TentType WORKSHOP_TAILOR = workshop("workshop_tailor", "atelier du tailleur de lin", "Tailor's Workshop");
	public static final TentType WORKSHOP_ENGINEER = workshop("workshop_engineer", "atelier de l'ingénieur", "Engineer's Workshop");
	public static final TentType WORKSHOP_COOK = workshop("workshop_cook", "atelier du cuisinier", "Cook's Workshop");
	public static final TentType WORKSHOP_ALCHEMIST = workshop("workshop_alchemist", "atelier de l'alchimiste", "Alchemist's Workshop");
	public static final TentType WORKSHOP_ENCHANTER = workshop("workshop_enchanter", "atelier de l'enchanteur", "Enchanter's Workshop");
	/** The crafting workshops (tab "Ateliers"); placeable props only for now (the crafting itself comes later). */
	public static final List<TentType> WORKSHOPS = List.of(WORKSHOP_BLACKSMITH, WORKSHOP_LEATHERWORKER, WORKSHOP_TAILOR, WORKSHOP_ENGINEER,
			WORKSHOP_COOK, WORKSHOP_ALCHEMIST, WORKSHOP_ENCHANTER);

	/** Every one-block prop: the tents, then the carts, then the workshops. */
	public static final List<TentType> PROPS = java.util.stream.Stream.of(ALL, CARTS, WORKSHOPS).flatMap(List::stream).toList();

	private static TentType cart(String id, String frenchName, String englishName) {
		return TentType.load(TentType.CARTS, id, frenchName, englishName);
	}

	private static TentType workshop(String id, String frenchName, String englishName) {
		return TentType.load(TentType.WORKSHOPS, id, frenchName, englishName);
	}

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
		for (TentType t : PROPS) {
			if (t.id().equals(s) || t.id().equals("tent_" + s) || t.id().equals("tente_" + s) || t.id().equals("cart_" + s)
					|| t.id().equals("workshop_" + s)) {
				return t;
			}
		}
		return null;
	}
}
