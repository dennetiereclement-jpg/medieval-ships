package fr.medievalships.core;

import java.util.List;


/**
 * The twenty-two tents (six camp tents, sixteen merchant tents), the eight carts and the nomad tavern, the seven crafting
 * workshops, the three training areas and the medieval cannon. One line per prop: its id (block, item, model, decor and
 * tents / carts / workshops / artillery JSON are all named after it) and its names. {@link #ALL} = the tents only (their tab "Tentes": the six camp tents, the six
 * {@link #MERCHANTS}, the five {@link #MERCHANTS2}, the two {@link #MERCHANTS3}, the two {@link #MERCHANTS4}, then the jeweller's
 * {@link #MERCHANTS5}),
 * {@link #CARTS} = the carts (tab "Charrettes"), {@link #WORKSHOPS} = the workshops (tab "Ateliers"),
 * {@link #ARTILLERY} = the cannon (tab "Artillerie"), {@link #TRAINING} = the training areas (tab "Entraînement"),
 * {@link #DECORATIONS} = the eight street decorations (tab "Décorations", 1.20.0), {@link #PROPS} = all six (registration,
 * commands, models).
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

	public static final TentType MERCHANT_BARD = TentType.load("tente_barde", "tente du vendeur de barde", "Bard Merchant Tent");
	public static final TentType MERCHANT_GUNSMITH = TentType.load("tente_fusils", "tente du vendeur de fusils", "Gunsmith Merchant Tent");
	public static final TentType MERCHANT_ARCHERY = TentType.load("tente_archer", "tente du vendeur d'archerie", "Archery Merchant Tent");
	public static final TentType MERCHANT_MAGE = TentType.load("tente_mage", "tente du vendeur de mage", "Mage Merchant Tent");
	public static final TentType MERCHANT_ARMOUR = TentType.load("tente_armures", "tente du vendeur d'armures", "Armour Merchant Tent");
	/** The merchant tents II (1.15.0): five more pavilions of tools/merchant/merchantlib.py, group "tents", each with its own atlas. */
	public static final List<TentType> MERCHANTS2 = List.of(MERCHANT_BARD, MERCHANT_GUNSMITH, MERCHANT_ARCHERY, MERCHANT_MAGE, MERCHANT_ARMOUR);

	public static final TentType MERCHANT_POISON = TentType.load("tente_poison", "tente du vendeur de poisons", "Poison Merchant Tent");
	public static final TentType MERCHANT_BUTCHER = TentType.load("tente_boucher", "tente du boucher", "Butcher's Tent");
	/** The merchant tents III (1.16.0): two gabled stalls of tools/merchant/merchantlib.py, group "tents", each with its own atlas. */
	public static final List<TentType> MERCHANTS3 = List.of(MERCHANT_POISON, MERCHANT_BUTCHER);

	public static final TentType MERCHANT_BAKER = TentType.load("tente_boulanger", "tente du boulanger", "Baker's Stall");
	public static final TentType MERCHANT_FISHMONGER = TentType.load("tente_poissonnier", "tente du poissonnier", "Fishmonger's Stall");
	/**
	 * The merchant tents IV (1.17.0): the baker's and the (longer) fishmonger's gabled stalls of
	 * tools/merchant/merchantlib.py, group "tents", each with its own atlas.
	 */
	public static final List<TentType> MERCHANTS4 = List.of(MERCHANT_BAKER, MERCHANT_FISHMONGER);

	public static final TentType MERCHANT_JEWELLER = TentType.load("tente_joaillier", "tente du joaillier", "Jeweller's Tent");
	/**
	 * The merchant tents V (1.21.0): the jeweller's tent (the gabled stall of tools/merchant/merchantlib.py with the raised
	 * pointed centre, the hipped left end and the curtain walls of tools/merchant/props_m10.py), group "tents", its own
	 * atlas, its anchor block lit (JSON "light").
	 */
	public static final List<TentType> MERCHANTS5 = List.of(MERCHANT_JEWELLER);

	/**
	 * The tents only (tab "Tentes"): the six camp tents, the six merchant tents, the five of 1.15.0, the two of 1.16.0,
	 * the two of 1.17.0, then the jeweller's of 1.21.0.
	 */
	public static final List<TentType> ALL = java.util.stream.Stream.of(List.of(COMMAND, ADVENTURER, MARKET, CAMP, DWELLING, CHIEF), MERCHANTS,
			MERCHANTS2, MERCHANTS3, MERCHANTS4, MERCHANTS5).flatMap(List::stream).toList();

	public static final TentType CART_COVERED_WHITE = cart("cart_covered_white", "charrette couverte blanche", "White Covered Wagon");
	public static final TentType CART_HAY = cart("cart_hay", "charrette de foin", "Hay Cart");
	public static final TentType CART_MERCHANT_WAGON = cart("cart_merchant_wagon", "roulotte de marchand", "Merchant Wagon");
	public static final TentType CART_MARKET = cart("cart_market", "charrette de marché", "Market Cart");
	public static final TentType CART_LOGS = cart("cart_logs", "charrette de bûcheron", "Log Cart");
	public static final TentType CART_OPEN = cart("cart_open", "charrette de transport", "Open Cart");
	public static final TentType CART_COVERED_TEAL = cart("cart_covered_teal", "charrette couverte turquoise", "Teal Covered Wagon");
	public static final TentType CART_BARRELS = cart("cart_barrels", "charrette à tonneaux", "Barrel Cart");
	/**
	 * The nomad tavern (1.19.0): a big wagon with its counter, terrace, tables and stools (about 13 x 10 blocks, its own
	 * atlas), group "carts"; its JSON lists the stools' {@link TentType.Seat seats}, where a player can sit down.
	 */
	public static final TentType TAVERN = cart("taverne_nomade", "taverne nomade", "Nomad Tavern");
	/**
	 * The decorative rowboat (1.19.0): an exact copy of the sailing rowboat's model (tools/props/generate_barque_deco.py),
	 * lifted onto the ground, static; its two thwarts are seats. The sailing rowboat (an entity) stays as it is.
	 */
	public static final TentType ROWBOAT_DECO = cart("barque_deco", "barque (décor)", "Rowboat (Decoration)");
	/** The carts (tab "Charrettes"): the eight carts of 1.12.0, the nomad tavern, then the decorative rowboat. */
	public static final List<TentType> CARTS = List.of(CART_COVERED_WHITE, CART_HAY, CART_MERCHANT_WAGON, CART_MARKET, CART_LOGS, CART_OPEN,
			CART_COVERED_TEAL, CART_BARRELS, TAVERN, ROWBOAT_DECO);

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

	/**
	 * The medieval cannon (1.16.0): a prop like the others (one block, static model, collision boxes) on a CannonBlock
	 * whose block entity keeps a {@link CannonState} for the future firing system; its JSON has a muzzle point.
	 */
	public static final TentType CANNON = TentType.load(TentType.ARTILLERY, "canon_medieval", "canon médiéval", "Medieval Cannon");
	/** The artillery (tab "Artillerie"). */
	public static final List<TentType> ARTILLERY = List.of(CANNON);

	/**
	 * The training areas (1.18.0): fenced yards of about 7 x 7 blocks drawn as one static model (tools/training/traininglib.py),
	 * group "training", each with its own atlas, tab "Entraînement".
	 */
	public static final TentType TRAINING_DUMMY = training("training_area_dummy", "aire d'entraînement aux frappes", "Strike Training Area");
	public static final TentType TRAINING_TATAMI = training("training_area_tatami", "aire d'entraînement aux tatamis", "Tatami Training Area");
	public static final TentType TRAINING_SHIELD = training("training_area_shield", "aire d'entraînement épée et bouclier",
			"Sword & Shield Training Area");
	/** The training areas (tab "Entraînement"). */
	public static final List<TentType> TRAINING = List.of(TRAINING_DUMMY, TRAINING_TATAMI, TRAINING_SHIELD);

	/**
	 * The street decorations (1.20.0): static props of two posts (or one) with cloth, ropes, a net, herbs or a lantern,
	 * drawn as one model each (tools/deco/generate_&lt;id&gt;.py on decolib.py), group "decorations", one shared atlas
	 * (textures/entity/decorations.png), tab "Décorations". The hanging lantern and the bunting light the area round their
	 * foot (JSON "light", {@link TentType#light()}).
	 */
	public static final TentType DECO_BUNTING = decoration("deco_guirlande", "guirlande festive", "Festive Bunting", false, false);
	public static final TentType DECO_CLOTHESLINE = decoration("deco_etendoir", "étendoir à linge", "Clothesline", true, false);
	public static final TentType DECO_DRAPERY = decoration("deco_draperie", "draperie rouge", "Red Drapery", false, false);
	public static final TentType DECO_NET = decoration("deco_filet", "filet suspendu", "Hanging Net", true, false);
	public static final TentType DECO_HERBS = decoration("deco_sechoir", "séchoir à herbes", "Herb Drying Rack", true, false);
	public static final TentType DECO_LANTERN = decoration("deco_lanterne", "lanterne suspendue", "Hanging Lantern", false, false);
	public static final TentType DECO_BANNER = decoration("deco_banniere", "bannière de la Couronne", "Crown Banner", false, false);
	public static final TentType DECO_SHADE = decoration("deco_ombrage", "toiles d'ombrage", "Shade Sails", false, true);
	/** The street decorations (tab "Décorations"), in the order of the reference sheet. */
	public static final List<TentType> DECORATIONS = List.of(DECO_BUNTING, DECO_CLOTHESLINE, DECO_DRAPERY, DECO_NET, DECO_HERBS, DECO_LANTERN,
			DECO_BANNER, DECO_SHADE);

	/** Every one-block prop: the tents, then the carts, the workshops, the training areas, the decorations, the artillery (last). */
	public static final List<TentType> PROPS = java.util.stream.Stream.of(ALL, CARTS, WORKSHOPS, TRAINING, DECORATIONS, ARTILLERY)
			.flatMap(List::stream).toList();

	private static TentType cart(String id, String frenchName, String englishName) {
		return TentType.load(TentType.CARTS, id, frenchName, englishName);
	}

	private static TentType workshop(String id, String frenchName, String englishName) {
		return TentType.load(TentType.WORKSHOPS, id, frenchName, englishName);
	}

	private static TentType training(String id, String frenchName, String englishName) {
		return TentType.load(TentType.TRAINING, id, frenchName, englishName);
	}

	private static TentType decoration(String id, String frenchName, String englishName, boolean masculine, boolean plural) {
		return TentType.load(TentType.DECORATIONS, id, frenchName, englishName).withGender(masculine, plural);
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
					|| t.id().equals("workshop_" + s) || t.id().equals("canon_" + s) || t.id().equals("training_area_" + s)
					|| t.id().equals("deco_" + s)
					|| t.isCannon() && (s.equals("canon") || s.equals("cannon")) || t == TAVERN && (s.equals("taverne") || s.equals("tavern"))) {
				return t;
			}
		}
		return null;
	}
}
