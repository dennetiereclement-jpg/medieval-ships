package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

/**
 * A recipe of the divine forge (1.34.0) as written in a data pack ({@code data/<ns>/recipe/<name>.json}, type
 * {@value #TYPE}), read with Gson: everything but what needs the game's registries (the items, tags and data components
 * are resolved by {@code fr.medievalships.forge.DivineForgeRecipe}, which reads the same JSON through this class).
 *
 * <pre>{@code
 * {
 *   "type": "medievalships:forge_divine",
 *   "categorie": "armes_legendaires",
 *   "duree": 200,
 *   "ingredients": [
 *     {"item": "minecraft:gold_ingot", "count": 4},
 *     {"tag": "minecraft:planks", "count": 2},
 *     {"item": "minecraft:paper", "count": 1, "components": {"minecraft:custom_model_data": {"floats": [7]}}},
 *     {"item": "minecraft:emerald", "count": 3, "predicates": {"minecraft:custom_data": {"monnaie": "couronne"}}}
 *   ],
 *   "result": {"id": "minecraft:golden_sword", "count": 1, "components": {"minecraft:custom_name": "Lame divine"}},
 *   "metier": "forgeron", "niveau": 10, "tag": "recette_lame", "permission": 0,
 *   "commande": "scoreboard players add @s forgeron_xp 25",
 *   "nom": "Lame divine", "description": "Forgée dans le feu sacré.", "ordre": 0, "essai": false
 * }
 * }</pre>
 *
 * <ul>
 * <li>{@code ingredients} (1 to {@value #MAX_INGREDIENTS}): an item ({@code "item"}, alias {@code "id"}) or an item tag
 * ({@code "tag"}, with or without {@code #}), a quantity ({@code "count"}, alias {@code "quantite"}, 1 by default), and
 * optionally the data components the stack must have exactly ({@code "components"}) or match partly
 * ({@code "predicates"}, e.g. a part of {@code minecraft:custom_data}), in the formats of the vanilla item predicates:
 * the server's currencies and special items (items with components) are recognised that way.</li>
 * <li>{@code result}: an item stack in the vanilla format ({@code "id"}, {@code "count"}, {@code "components"}: name,
 * lore, enchantments...), or just an item id.</li>
 * <li>{@code duree} (alias {@code durée}): the crafting time in ticks (20 = 1 s), {@value #DEFAULT_DURATION} by
 * default, {@value #MIN_DURATION} to {@value #MAX_DURATION}.</li>
 * <li>{@code categorie} (alias {@code catégorie}): one of {@link ForgeCategory}; an unknown or missing one is read as
 * {@code objets_rares} ({@link #categoryKnown()} tells it apart).</li>
 * <li>optional requirements: {@code metier} (a scoreboard objective: the server's profession) and {@code niveau} (the
 * minimum score, 1 when only the profession is given), {@code tag} (a command tag the player must have: a recipe
 * unlocked by a quest), {@code permission} (an operator level, 0 to 4).</li>
 * <li>{@code commande}: one command or a list, run as the player (permission level 2) when the crafted item is handed
 * over, e.g. to give the profession's experience.</li>
 * <li>{@code nom} (the name shown in the list; the result's own name otherwise), {@code description}, {@code ordre}
 * (sorting within the category), {@code essai} (a trial recipe: hidden when the server setting
 * {@code forgeTestRecipe} is false).</li>
 * </ul>
 */
public final class ForgeRecipeSpec {
	/** The recipe type (its serializer's id): the {@code "type"} of a recipe file. */
	public static final String TYPE = "medievalships:forge_divine";
	public static final int DEFAULT_DURATION = 200, MIN_DURATION = 1, MAX_DURATION = 72_000;
	public static final int MAX_INGREDIENTS = 12;
	/** The most of one ingredient a recipe may ask (a full inventory of stacks of 64). */
	public static final int MAX_COUNT = 36 * 64;
	public static final int MAX_RESULT_COUNT = 99;
	public static final int MAX_COMMANDS = 8;

	/** A recipe file this class refuses: the message says why (French, for the server's administrator). */
	public static final class Invalid extends Exception {
		public Invalid(String message) {
			super(message);
		}
	}

	/**
	 * One ingredient: an item id or a tag id (namespaced, lower case; exactly one of the two), a quantity, and the
	 * data components the stack must carry: {@code components} (exact values) and {@code predicates} (partial), both
	 * null when the item alone is enough.
	 */
	public record Ingredient(String item, String tag, int count, JsonObject components, JsonObject predicates) {
		public boolean isTag() {
			return tag != null;
		}

		/** {@code minecraft:gold_ingot} or {@code #minecraft:planks}. */
		public String id() {
			return isTag() ? "#" + tag : item;
		}

		/** Must the stack carry particular data components? */
		public boolean hasComponents() {
			return components != null && !components.isEmpty() || predicates != null && !predicates.isEmpty();
		}
	}

	private ForgeCategory category = ForgeCategory.OBJETS_RARES;
	private boolean categoryKnown;
	private int duration = DEFAULT_DURATION;
	private final List<Ingredient> ingredients = new ArrayList<>();
	private JsonObject result;
	private String resultItem;
	private int resultCount = 1;
	private String profession;
	private int level;
	private String tag;
	private int permission;
	private final List<String> commands = new ArrayList<>();
	private boolean trial;
	private String name;
	private String description;
	private int order;

	private ForgeRecipeSpec() {
	}

	public ForgeCategory category() {
		return category;
	}

	/** Was the category one of the five? (else the recipe is filed under {@code objets_rares}) */
	public boolean categoryKnown() {
		return categoryKnown;
	}

	/** Crafting time in ticks. */
	public int duration() {
		return duration;
	}

	public List<Ingredient> ingredients() {
		return ingredients;
	}

	/** The result as written (an object with at least {@code "id"}), for the game's item stack codec. */
	public JsonObject result() {
		return result;
	}

	public String resultItem() {
		return resultItem;
	}

	public int resultCount() {
		return resultCount;
	}

	/** The scoreboard objective of the required profession, or null. */
	public String profession() {
		return profession;
	}

	/** The minimum score in {@link #profession()} (0 when there is no profession). */
	public int level() {
		return level;
	}

	/** The command tag the player must have, or null. */
	public String tag() {
		return tag;
	}

	/** The operator level the player must have (0: anybody). */
	public int permission() {
		return permission;
	}

	/** The commands run as the player when the item is handed over (often empty). */
	public List<String> commands() {
		return commands;
	}

	/** A trial recipe ({@code "essai": true}): hidden when {@code forgeTestRecipe} is false. */
	public boolean trial() {
		return trial;
	}

	/** The name shown in the interface, or null (the result's own name). */
	public String name() {
		return name;
	}

	/** A line of text shown under the recipe in the interface, or null. */
	public String description() {
		return description;
	}

	public int order() {
		return order;
	}

	/** Has the recipe any requirement besides its ingredients? */
	public boolean hasRequirements() {
		return profession != null || tag != null || permission > 0;
	}

	/** Reads a recipe file (the {@code "type"} key is ignored here: the game dispatched on it already). */
	public static ForgeRecipeSpec parse(JsonObject json) throws Invalid {
		if (json == null) {
			throw new Invalid("recette vide");
		}
		ForgeRecipeSpec r = new ForgeRecipeSpec();
		String cat = string(json, "categorie", "catégorie", "category");
		if (cat != null) {
			ForgeCategory c = ForgeCategory.byId(cat);
			r.categoryKnown = c != null;
			r.category = c != null ? c : ForgeCategory.OBJETS_RARES;
		}
		JsonElement d = first(json, "duree", "durée", "duration");
		if (d != null && !d.isJsonNull()) {
			int ticks = integer(d, "duree");
			if (ticks < MIN_DURATION || ticks > MAX_DURATION) {
				throw new Invalid("duree hors limites (" + ticks + " ticks ; de " + MIN_DURATION + " à " + MAX_DURATION + ")");
			}
			r.duration = ticks;
		}
		JsonElement ing = first(json, "ingredients", "ingrédients");
		if (ing == null || !ing.isJsonArray() || ing.getAsJsonArray().isEmpty()) {
			throw new Invalid("il faut au moins un ingrédient (\"ingredients\": [...])");
		}
		JsonArray list = ing.getAsJsonArray();
		if (list.size() > MAX_INGREDIENTS) {
			throw new Invalid("trop d'ingrédients (" + list.size() + ", au plus " + MAX_INGREDIENTS + ")");
		}
		for (int i = 0; i < list.size(); i++) {
			r.ingredients.add(ingredient(list.get(i), i + 1));
		}
		JsonElement res = first(json, "result", "resultat", "résultat");
		if (res == null || res.isJsonNull()) {
			throw new Invalid("il manque le résultat (\"result\": {\"id\": ...})");
		}
		if (res.isJsonPrimitive() && res.getAsJsonPrimitive().isString()) {
			JsonObject o = new JsonObject();
			o.addProperty("id", res.getAsString());
			res = o;
		}
		if (!res.isJsonObject()) {
			throw new Invalid("\"result\" doit être un objet {\"id\": ..., \"count\": ...} ou un id d'objet");
		}
		JsonObject result = res.getAsJsonObject().deepCopy();
		String rid = string(result, "id", "item");
		if (rid == null) {
			throw new Invalid("\"result\" n'a pas d'\"id\"");
		}
		r.resultItem = identifier(rid, "result.id");
		result.remove("item");
		result.addProperty("id", r.resultItem);
		if (result.has("count")) {
			int n = integer(result.get("count"), "result.count");
			if (n < 1 || n > MAX_RESULT_COUNT) {
				throw new Invalid("result.count hors limites (" + n + ")");
			}
			r.resultCount = n;
		}
		r.result = result;
		String prof = string(json, "metier", "métier", "profession");
		if (prof != null) {
			r.profession = word(prof, "metier");
			JsonElement lv = first(json, "niveau", "level");
			r.level = lv == null || lv.isJsonNull() ? 1 : integer(lv, "niveau");
			if (r.level < 0) {
				throw new Invalid("niveau négatif (" + r.level + ")");
			}
		} else if (first(json, "niveau", "level") != null) {
			throw new Invalid("\"niveau\" sans \"metier\" (l'objectif de scoreboard du métier)");
		}
		String t = string(json, "tag");
		if (t != null) {
			r.tag = word(t, "tag");
		}
		JsonElement p = first(json, "permission");
		if (p != null && !p.isJsonNull()) {
			int lvl = integer(p, "permission");
			if (lvl < 0 || lvl > 4) {
				throw new Invalid("permission hors limites (" + lvl + " ; niveau d'opérateur de 0 à 4)");
			}
			r.permission = lvl;
		}
		JsonElement cmd = first(json, "commande", "commandes", "command");
		if (cmd != null && !cmd.isJsonNull()) {
			if (cmd.isJsonArray()) {
				for (JsonElement e : cmd.getAsJsonArray()) {
					addCommand(r.commands, e);
				}
			} else {
				addCommand(r.commands, cmd);
			}
			if (r.commands.size() > MAX_COMMANDS) {
				throw new Invalid("trop de commandes (" + r.commands.size() + ", au plus " + MAX_COMMANDS + ")");
			}
		}
		JsonElement trial = first(json, "essai", "trial");
		if (trial != null && trial.isJsonPrimitive()) {
			r.trial = trial.getAsJsonPrimitive().isBoolean() ? trial.getAsBoolean() : "true".equalsIgnoreCase(trial.getAsString());
		}
		r.name = blankToNull(string(json, "nom", "name"));
		r.description = blankToNull(string(json, "description"));
		JsonElement o = first(json, "ordre", "order");
		if (o != null && !o.isJsonNull()) {
			r.order = integer(o, "ordre");
		}
		return r;
	}

	private static Ingredient ingredient(JsonElement e, int n) throws Invalid {
		String where = "ingrédient " + n;
		if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isString()) {
			String s = e.getAsString().trim();
			return s.startsWith("#") ? new Ingredient(null, identifier(s.substring(1), where), 1, null, null)
					: new Ingredient(identifier(s, where), null, 1, null, null);
		}
		if (!e.isJsonObject()) {
			throw new Invalid(where + " : un objet {\"item\" ou \"tag\", \"count\"} est attendu");
		}
		JsonObject o = e.getAsJsonObject();
		String item = string(o, "item", "id");
		String tag = string(o, "tag");
		if (item != null && item.trim().startsWith("#") && tag == null) {
			tag = item.trim().substring(1);
			item = null;
		}
		if ((item == null) == (tag == null)) {
			throw new Invalid(where + " : il faut \"item\" OU \"tag\" (un seul des deux)");
		}
		if (tag != null && tag.trim().startsWith("#")) {
			tag = tag.trim().substring(1);
		}
		int count = 1;
		JsonElement c = first(o, "count", "quantite", "quantité");
		if (c != null && !c.isJsonNull()) {
			count = integer(c, where + ".count");
		}
		if (count < 1 || count > MAX_COUNT) {
			throw new Invalid(where + " : quantité hors limites (" + count + ", de 1 à " + MAX_COUNT + ")");
		}
		JsonObject components = object(o, "components", where);
		JsonObject predicates = object(o, "predicates", where);
		return new Ingredient(item == null ? null : identifier(item, where), tag == null ? null : identifier(tag, where), count, components, predicates);
	}

	private static JsonObject object(JsonObject o, String key, String where) throws Invalid {
		if (!o.has(key) || o.get(key).isJsonNull()) {
			return null;
		}
		if (!o.get(key).isJsonObject()) {
			throw new Invalid(where + " : \"" + key + "\" doit être un objet");
		}
		return o.getAsJsonObject(key).deepCopy();
	}

	private static void addCommand(List<String> out, JsonElement e) throws Invalid {
		if (!e.isJsonPrimitive() || !e.getAsJsonPrimitive().isString()) {
			throw new Invalid("\"commande\" doit être un texte ou une liste de textes");
		}
		String s = e.getAsString().trim();
		while (s.startsWith("/")) {
			s = s.substring(1).trim();
		}
		if (!s.isEmpty()) {
			out.add(s);
		}
	}

	/** A namespaced id, lower case, {@code minecraft:} added when it has none. */
	static String identifier(String raw, String where) throws Invalid {
		String s = raw.trim().toLowerCase(Locale.ROOT);
		if (s.isEmpty()) {
			throw new Invalid(where + " : id vide");
		}
		if (!s.contains(":")) {
			s = "minecraft:" + s;
		}
		int colon = s.indexOf(':');
		String ns = s.substring(0, colon), path = s.substring(colon + 1);
		if (ns.isEmpty() || path.isEmpty() || !ns.matches("[a-z0-9_.-]+") || !path.matches("[a-z0-9_./-]+")) {
			throw new Invalid(where + " : id invalide « " + raw + " »");
		}
		return s;
	}

	/** A scoreboard objective or a command tag: no spaces, at most 64 characters (the game's limit for tags). */
	private static String word(String raw, String key) throws Invalid {
		String s = raw.trim();
		if (s.isEmpty() || s.length() > 64 || !s.matches("[A-Za-z0-9_.+\\-]+")) {
			throw new Invalid("\"" + key + "\" invalide « " + raw + " » (lettres, chiffres, _ . + -)");
		}
		return s;
	}

	private static String blankToNull(String s) {
		return s == null || s.isBlank() ? null : s.trim();
	}

	private static JsonElement first(JsonObject o, String... keys) {
		for (String k : keys) {
			if (o.has(k)) {
				return o.get(k);
			}
		}
		return null;
	}

	private static String string(JsonObject o, String... keys) throws Invalid {
		JsonElement e = first(o, keys);
		if (e == null || e.isJsonNull()) {
			return null;
		}
		if (!e.isJsonPrimitive()) {
			throw new Invalid("\"" + keys[0] + "\" doit être un texte");
		}
		return e.getAsString();
	}

	private static int integer(JsonElement e, String key) throws Invalid {
		if (e.isJsonPrimitive()) {
			JsonPrimitive p = e.getAsJsonPrimitive();
			try {
				double v = p.isNumber() ? p.getAsDouble() : Double.parseDouble(p.getAsString().trim());
				if (v == Math.rint(v) && Math.abs(v) <= Integer.MAX_VALUE) {
					return (int) v;
				}
			} catch (NumberFormatException ignored) {
				// falls through
			}
		}
		throw new Invalid("\"" + key + "\" doit être un nombre entier");
	}
}
