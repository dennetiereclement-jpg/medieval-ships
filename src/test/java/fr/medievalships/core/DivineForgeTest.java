package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.OptionalInt;
import java.util.Set;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The divine forge (1.34.0): its prop (descriptor, extra models, place among the props), its recipes read from a data
 * pack (fields, aliases, refusals), the requirements of the server's professions, the exact payment of the ingredients
 * on a simulated inventory, the crafting state machine, and the animation (gears, flipbooks) as functions of the time.
 */
public class DivineForgeTest {
	private static final double EPS = 1e-9;
	private static final Path RESOURCES = Path.of("src/main/resources");
	private static final TentType F = TentTypes.FORGE_DIVINE;

	private static JsonObject json(String s) {
		return JsonParser.parseString(s).getAsJsonObject();
	}

	private static ForgeRecipeSpec recipe(String s) throws ForgeRecipeSpec.Invalid {
		return ForgeRecipeSpec.parse(json(s));
	}

	// ------------------------------------------------------------------ the prop

	@Test
	void aWorkshopOfItsOwnAmongTheProps() {
		assertEquals("forge_divine", F.id());
		assertTrue(F.isWorkshop() && F.isDivineForge(), "family of the workshops, the divine forge");
		assertFalse(TentTypes.WORKSHOPS.contains(F), "the eight classic workshops stay as they are");
		assertEquals(List.of(F), TentTypes.FORGES);
		assertTrue(TentTypes.PROPS.contains(F));
		assertSame(TentTypes.CANNON, TentTypes.PROPS.get(TentTypes.PROPS.size() - 1), "the artillery stays last");
		assertSame(F, TentTypes.PROPS.get(TentTypes.PROPS.size() - 2), "the forge just before the artillery");
		assertEquals("forge_divine", F.profession(), "its profession: the key of workshopCommands and of the use event");
		assertFalse(F.masculine(), "la forge : « posée »");
		assertEquals("e", F.agreement());
		assertEquals(TentType.MAX_LIGHT, F.light(), "light 15");
		for (String alias : new String[] {"forge_divine", "medievalships:forge_divine", " Forge ", "divine_forge"}) {
			assertSame(F, TentTypes.byId(alias), alias);
		}
		for (TentType t : TentTypes.PROPS) {
			assertEquals(t == F, t.isDivineForge(), t.id());
		}
		assertFalse(F.hasHazard() || F.hasTargets() || !F.seats().isEmpty(), "nothing else");
	}

	@Test
	void descriptorWithinTheAgreedEnvelope() throws Exception {
		Path file = RESOURCES.resolve("assets/medievalships/workshops/forge_divine.json");
		assertTrue(Files.isRegularFile(file), "workshops/forge_divine.json");
		TentType.Box e = F.extent();
		assertEquals(0.0, e.y0(), EPS, "stands on the ground");
		assertTrue(e.width() <= 13.0 + EPS && e.height() <= 10.0 + EPS && e.depth() <= 6.0 + EPS, "13 x 10 x 6 at most: " + e);
		assertTrue(e.width() >= 8 && e.height() >= 6, "a great forge: " + e);
		assertTrue(e.x0() <= 0 && e.x1() >= 0 && e.z0() <= 0 && e.z1() >= 0, "the anchor inside");
		assertFalse(F.colliders().isEmpty(), "collision boxes");
		for (TentType.Box c : F.colliders()) {
			assertTrue(c.x0() >= e.x0() - EPS && c.x1() <= e.x1() + EPS && c.y0() >= e.y0() - EPS && c.y1() <= e.y1() + EPS
					&& c.z0() >= e.z0() - EPS && c.z1() <= e.z1() + EPS, "collider inside the extent: " + c);
			assertTrue(c.width() > 0 && c.height() > 0 && c.depth() > 0, "a real box: " + c);
		}
		// the platform can be walked onto: whatever covers the front edge of the footprint is no higher than a step
		double front = 0;
		for (TentType.Box c : F.colliders()) {
			if (c.z1() >= e.z1() - 0.05 && c.y0() <= 0.01) {
				front = Math.max(front, c.y1());
			}
		}
		assertTrue(front <= 0.6 + EPS, "the front edge is a step (" + front + ")");
		// nothing solid hangs under the banners (x = +-5.6, z = 0.6, between y = 2 and y = 8)
		for (TentType.Box c : F.colliders()) {
			for (double x : new double[] {-5.6, 5.6}) {
				boolean under = c.x0() < x + 0.3 && c.x1() > x - 0.3 && c.z0() < 0.9 && c.z1() > 0.3 && c.y0() < 8.0 && c.y1() > 2.0;
				assertFalse(under, "a collider under the banner at x " + x + ": " + c);
			}
		}
		assertEquals(1, F.extraModels().size(), "the statue and decor model");
		TentType.ExtraModel deco = F.extraModels().get(0);
		assertEquals("models/entity/forge_divine_deco.bbmodel", deco.model());
		assertEquals("textures/entity/forge_divine_deco.png", deco.texture());
		assertEquals("models/entity/forge_divine.bbmodel", F.model());
		assertEquals("textures/entity/forge_divine.png", F.texture());
		// the turned extents stay the same size
		for (int q = 0; q < 4; q++) {
			TentType.Box r = F.extent(q);
			assertEquals(e.width() * e.depth(), r.width() * r.depth(), 1e-6, "quarter " + q);
		}
	}

	@Test
	void extraModelsParsedForAnyProp() {
		String base = "\"extent\": [-1, 0, -1, 1, 2, 1], \"texture\": \"textures/entity/x.png\"";
		TentType none = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + "}"));
		assertTrue(none.extraModels().isEmpty(), "absent: none");
		TentType two = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + ", \"extra_models\": [{\"model\": \"models/entity/a.bbmodel\","
				+ " \"texture\": \"textures/entity/a.png\"}, \"models/entity/b.bbmodel\", {\"texture\": \"x\"}, 3, {\"model\": \" \"}]}"));
		assertEquals(2, two.extraModels().size(), "the bad entries are skipped");
		assertEquals(new TentType.ExtraModel("models/entity/a.bbmodel", "textures/entity/a.png"), two.extraModels().get(0));
		assertEquals(new TentType.ExtraModel("models/entity/b.bbmodel", "textures/entity/x.png"), two.extraModels().get(1),
				"the prop's atlas by default");
		TentType odd = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + ", \"extra_models\": {\"model\": \"m\"}}"));
		assertTrue(odd.extraModels().isEmpty(), "not a list: none");
	}

	@Test
	void missingDescriptorFallsBack() {
		TentType t = TentType.loadOrDefault(TentType.WORKSHOPS, "forge_absente", "forge absente", "Missing Forge",
				"{\"extent\": [-6.5, 0, -3, 6.5, 10, 3], \"light\": 15}");
		assertEquals(13.0, t.extent().width(), EPS, "the fallback is used when the file is missing");
		assertEquals(15, t.light());
	}

	/** The bones the renderer expects, when the models are in the jar (they come from tools/forge/). */
	@Test
	void modelsFollowTheBoneContract() throws Exception {
		BbModel structure = load(F.model());
		Assumptions.assumeTrue(structure != null, "the structure model is not generated in this tree");
		Set<String> names = new HashSet<>();
		for (BbModel.Bone b : structure.bones) {
			names.add(b.name);
		}
		for (String p : new String[] {"fire_f", "flow_l_f", "flow_r_f"}) {
			for (int i = 0; i < ForgeAnimation.FRAMES; i++) {
				assertTrue(names.contains(p + i), "structure: bone " + p + i);
			}
		}
		assertTrue(names.stream().anyMatch(n -> n.startsWith("gear_a_") || n.startsWith("gear_b_")), "structure: gears");
		assertTrue(names.stream().anyMatch(n -> n.startsWith("craft_")), "structure: craft_* (seen while crafting)");
		assertTrue(names.stream().anyMatch(n -> n.startsWith("fx_spark_")), "structure: spark points");
		assertTrue(structure.animations.isEmpty(), "no Blockbench animation: the renderer moves the bones");
		BbModel deco = load(F.extraModels().get(0).model());
		Assumptions.assumeTrue(deco != null, "the decor model is not generated in this tree");
		Set<String> decoNames = new HashSet<>();
		for (BbModel.Bone b : deco.bones) {
			decoNames.add(b.name);
		}
		assertTrue(decoNames.stream().anyMatch(n -> n.startsWith("fx_holy_")), "decor: holy light points");
		assertTrue(deco.animations.isEmpty());
	}

	@Test
	void gearAxisFollowsTheBonesRotation() {
		// a gear on the front (no rotation): its z axis is the model's +z; one turned 90 degrees about y (on a side wall)
		// turns about the model's x axis; a child of a turned bone inherits its parent's turn
		String json = "{\"resolution\": {\"width\": 16, \"height\": 16}, \"elements\": [], \"outliner\": ["
				+ "{\"name\": \"gear_a_0\", \"origin\": [0, 16, 0], \"children\": []},"
				+ "{\"name\": \"side\", \"origin\": [0, 0, 0], \"rotation\": [0, 90, 0], \"children\": ["
				+ "{\"name\": \"gear_b_0\", \"origin\": [-16, 8, 0], \"children\": []}]}]}";
		BbModel m = new BbModel(new java.io.StringReader(json));
		double[] front = m.bonesByName.get("gear_a_0").axisBlocks(0, 0, 1);
		assertEquals(0, front[0], 1e-6);
		assertEquals(0, front[1], 1e-6);
		assertEquals(1, front[2], 1e-6);
		double[] side = m.bonesByName.get("gear_b_0").axisBlocks(0, 0, 1);
		assertEquals(1.0, Math.abs(side[0]), 1e-6, "turned to the x axis: " + java.util.Arrays.toString(side));
		assertEquals(0, side[1], 1e-6);
		assertEquals(0, side[2], 1e-6);
		double[] o = m.bonesByName.get("gear_b_0").originBlocks();
		assertEquals(1.0, o[0], 1e-9, "pivot x = -bbX / 16");
		assertEquals(0.5, o[1], 1e-9);
	}

	private static BbModel load(String path) throws Exception {
		try (InputStream in = DivineForgeTest.class.getResourceAsStream("/assets/medievalships/" + path)) {
			if (in == null) {
				return null;
			}
			try (Reader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return new BbModel(r);
			}
		}
	}

	// ------------------------------------------------------------------ the recipes

	@Test
	void theTrialRecipeOfTheJar() throws Exception {
		Path file = RESOURCES.resolve("data/medievalships/recipe/forge_divine_essai.json");
		assertTrue(Files.isRegularFile(file));
		JsonObject root;
		try (Reader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
			root = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals(ForgeRecipeSpec.TYPE, root.get("type").getAsString());
		ForgeRecipeSpec r = ForgeRecipeSpec.parse(root);
		assertTrue(r.trial(), "marked as a trial recipe (hidden with forgeTestRecipe false)");
		assertEquals(ForgeCategory.ARMES_LEGENDAIRES, r.category());
		assertEquals(2, r.ingredients().size());
		assertEquals("minecraft:gold_ingot", r.ingredients().get(0).item());
		assertEquals(4, r.ingredients().get(0).count());
		assertEquals("minecraft:diamond", r.ingredients().get(1).item());
		assertEquals(1, r.ingredients().get(1).count());
		assertEquals("minecraft:golden_sword", r.resultItem());
		assertEquals("Lame divine (essai)", r.name());
		assertTrue(r.result().getAsJsonObject("components").has("minecraft:custom_name"));
		assertFalse(r.hasRequirements(), "anybody may forge it");
		assertTrue(r.duration() >= 20 && r.duration() <= 600, "a short wait: " + r.duration());
	}

	@Test
	void everyFieldRead() throws Exception {
		ForgeRecipeSpec r = recipe("{\"type\": \"medievalships:forge_divine\", \"catégorie\": \"Armures divines\", \"durée\": 600,"
				+ " \"ingredients\": [\"iron_ingot\", \"#minecraft:planks\", {\"id\": \"Minecraft:Emerald\", \"quantite\": 3,"
				+ " \"predicates\": {\"minecraft:custom_data\": {\"monnaie\": \"couronne\"}}}, {\"tag\": \"#c:gems\", \"count\": \"2\","
				+ " \"components\": {\"minecraft:rarity\": \"epic\"}}],"
				+ " \"result\": \"netherite_chestplate\", \"metier\": \"forgeron\", \"niveau\": 12, \"tag\": \"quete_armure\", \"permission\": 1,"
				+ " \"commande\": [\"/scoreboard players add @s forgeron_xp 40\", \"  \", \"tellraw @s \\\"ok\\\"\"], \"nom\": \"Cuirasse\","
				+ " \"description\": \" Bénie. \", \"ordre\": -2, \"essai\": \"true\"}");
		assertEquals(ForgeCategory.ARMURES_DIVINES, r.category());
		assertTrue(r.categoryKnown());
		assertEquals(600, r.duration());
		assertEquals(4, r.ingredients().size());
		ForgeRecipeSpec.Ingredient a = r.ingredients().get(0), b = r.ingredients().get(1), c = r.ingredients().get(2), d = r.ingredients().get(3);
		assertEquals("minecraft:iron_ingot", a.item());
		assertEquals(1, a.count());
		assertFalse(a.isTag() || a.hasComponents());
		assertTrue(b.isTag());
		assertEquals("minecraft:planks", b.tag());
		assertEquals("#minecraft:planks", b.id());
		assertEquals("minecraft:emerald", c.item(), "lower case");
		assertEquals(3, c.count());
		assertTrue(c.hasComponents() && c.predicates().has("minecraft:custom_data") && c.components() == null);
		assertEquals("c:gems", d.tag());
		assertEquals(2, d.count(), "a number written as text");
		assertTrue(d.components().has("minecraft:rarity"));
		assertEquals("minecraft:netherite_chestplate", r.resultItem());
		assertEquals("minecraft:netherite_chestplate", r.result().get("id").getAsString(), "an id alone becomes {\"id\": ...}");
		assertEquals(1, r.resultCount());
		assertEquals("forgeron", r.profession());
		assertEquals(12, r.level());
		assertEquals("quete_armure", r.tag());
		assertEquals(1, r.permission());
		assertEquals(List.of("scoreboard players add @s forgeron_xp 40", "tellraw @s \"ok\""), r.commands(), "slash removed, blanks dropped");
		assertEquals("Cuirasse", r.name());
		assertEquals("Bénie.", r.description());
		assertEquals(-2, r.order());
		assertTrue(r.trial());
		assertTrue(r.hasRequirements());
	}

	@Test
	void defaults() throws Exception {
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"item\": \"stone\"}], \"result\": {\"id\": \"stone\", \"count\": 4}}");
		assertEquals(ForgeRecipeSpec.DEFAULT_DURATION, r.duration());
		assertEquals(ForgeCategory.OBJETS_RARES, r.category());
		assertFalse(r.categoryKnown());
		assertEquals(4, r.resultCount());
		assertNull(r.profession());
		assertEquals(0, r.level());
		assertNull(r.tag());
		assertEquals(0, r.permission());
		assertTrue(r.commands().isEmpty());
		assertFalse(r.trial());
		assertNull(r.name());
		assertFalse(r.hasRequirements());
		ForgeRecipeSpec onlyJob = recipe("{\"ingredients\": [\"stone\"], \"result\": \"stone\", \"metier\": \"mineur\"}");
		assertEquals(1, onlyJob.level(), "a profession without a level: score 1 at least");
		ForgeRecipeSpec typo = recipe("{\"ingredients\": [\"stone\"], \"result\": \"stone\", \"categorie\": \"armes\"}");
		assertEquals(ForgeCategory.OBJETS_RARES, typo.category(), "an unknown category: filed under the rare items");
		assertFalse(typo.categoryKnown());
	}

	@Test
	void categories() {
		assertEquals(5, ForgeCategory.values().length);
		assertSame(ForgeCategory.ARMES_LEGENDAIRES, ForgeCategory.byId("Armes Légendaires"));
		assertSame(ForgeCategory.ARMURES_DIVINES, ForgeCategory.byId("armures-divines"));
		assertSame(ForgeCategory.STEAMPUNK, ForgeCategory.byId(" STEAMPUNK "));
		assertSame(ForgeCategory.OBJETS_RARES, ForgeCategory.byId("objets_rares"));
		assertSame(ForgeCategory.AMELIORATIONS, ForgeCategory.byId("améliorations"));
		assertNull(ForgeCategory.byId("armes"));
		assertNull(ForgeCategory.byId(null));
		assertEquals("Armes légendaires", ForgeCategory.ARMES_LEGENDAIRES.label());
		assertSame(ForgeCategory.OBJETS_RARES, ForgeCategory.byIndex(99));
		assertSame(ForgeCategory.STEAMPUNK, ForgeCategory.byIndex(2));
	}

	@Test
	void badRecipesRefused() {
		String ok = "\"result\": \"stone\"";
		String[] bad = {
				"{" + ok + "}", // no ingredient
				"{\"ingredients\": [], " + ok + "}",
				"{\"ingredients\": [{\"item\": \"stone\", \"tag\": \"minecraft:logs\"}], " + ok + "}", // both
				"{\"ingredients\": [{\"count\": 2}], " + ok + "}", // neither
				"{\"ingredients\": [{\"item\": \"stone\", \"count\": 0}], " + ok + "}",
				"{\"ingredients\": [{\"item\": \"stone\", \"count\": 1.5}], " + ok + "}",
				"{\"ingredients\": [{\"item\": \"Stone Bricks\"}], " + ok + "}", // a space in the id
				"{\"ingredients\": [\"stone\"]}", // no result
				"{\"ingredients\": [\"stone\"], \"result\": {\"count\": 1}}",
				"{\"ingredients\": [\"stone\"], \"result\": {\"id\": \"stone\", \"count\": 0}}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"duree\": 0}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"duree\": 72001}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"niveau\": 3}", // a level without a profession
				"{\"ingredients\": [\"stone\"], " + ok + ", \"metier\": \"forge ron\"}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"metier\": \"forgeron\", \"niveau\": -1}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"permission\": 5}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"tag\": \"a b\"}",
				"{\"ingredients\": [\"stone\"], " + ok + ", \"commande\": 3}",
				"{\"ingredients\": [\"stone\"," + "\"stone\",".repeat(12) + "\"stone\"], " + ok + "}", // 14 ingredients
		};
		for (String s : bad) {
			assertThrows(ForgeRecipeSpec.Invalid.class, () -> recipe(s), s);
		}
	}

	// ------------------------------------------------------------------ the requirements

	/** A player for the requirement checks. */
	private record Player(Map<String, Integer> scores, Set<String> objectives, Set<String> tags, int level) implements ForgeRequirements.Subject {
		@Override
		public boolean objectiveExists(String objective) {
			return objectives.contains(objective);
		}

		@Override
		public OptionalInt score(String objective) {
			Integer s = scores.get(objective);
			return s == null ? OptionalInt.empty() : OptionalInt.of(s);
		}

		@Override
		public boolean hasTag(String tag) {
			return tags.contains(tag);
		}

		@Override
		public int permissionLevel() {
			return level;
		}
	}

	@Test
	void requirementsOfTheServersProfessions() throws Exception {
		ForgeRecipeSpec r = recipe("{\"ingredients\": [\"stone\"], \"result\": \"stone\", \"metier\": \"forgeron\", \"niveau\": 10,"
				+ " \"tag\": \"quete_lame\", \"permission\": 2}");
		Player nobody = new Player(Map.of(), Set.of(), Set.of(), 0);
		List<String> why = ForgeRequirements.unmet(r, nobody);
		assertEquals(3, why.size(), why.toString());
		assertTrue(why.get(0).contains("forgeron") && why.get(0).contains("10") && why.get(0).contains("inconnu"), why.get(0));
		assertTrue(why.get(1).contains("quete_lame"), why.get(1));
		assertTrue(why.get(2).contains("2"), why.get(2));
		Player apprentice = new Player(Map.of("forgeron", 4), Set.of("forgeron"), Set.of("quete_lame"), 2);
		List<String> low = ForgeRequirements.unmet(r, apprentice);
		assertEquals(1, low.size());
		assertTrue(low.get(0).contains("vous : 4"), low.get(0));
		Player noScore = new Player(Map.of(), Set.of("forgeron"), Set.of("quete_lame"), 4);
		assertTrue(ForgeRequirements.unmet(r, noScore).get(0).contains("vous : 0"), "no score counts as 0");
		Player master = new Player(Map.of("forgeron", 10), Set.of("forgeron"), Set.of("quete_lame"), 2);
		assertTrue(ForgeRequirements.unmet(r, master).isEmpty(), "level 10 exactly is enough");
		ForgeRecipeSpec free = recipe("{\"ingredients\": [\"stone\"], \"result\": \"stone\"}");
		assertTrue(ForgeRequirements.unmet(free, nobody).isEmpty());
	}

	// ------------------------------------------------------------------ paying the ingredients

	/** A stack of the simulated inventory: an item, a count, a few "components" (key -> value). */
	private record Stack(String item, int count, Map<String, String> components) {
		static Stack of(String item, int count) {
			return new Stack(item, count, Map.of());
		}
	}

	private static final Map<String, Set<String>> TAGS = Map.of("minecraft:planks", Set.of("minecraft:oak_planks", "minecraft:spruce_planks"),
			"c:ingots", Set.of("minecraft:gold_ingot", "minecraft:iron_ingot"));

	/** An inventory of stacks matched against a recipe's ingredients (item or tag; "components" must all be equal). */
	private static ForgeIngredients.Slots inventory(List<Stack> stacks, ForgeRecipeSpec r) {
		return new ForgeIngredients.Slots() {
			@Override
			public int size() {
				return stacks.size();
			}

			@Override
			public int count(int slot) {
				return stacks.get(slot) == null ? 0 : stacks.get(slot).count();
			}

			@Override
			public boolean matches(int ingredient, int slot) {
				Stack s = stacks.get(slot);
				ForgeRecipeSpec.Ingredient in = r.ingredients().get(ingredient);
				if (s == null) {
					return false;
				}
				boolean item = in.isTag() ? TAGS.getOrDefault(in.tag(), Set.of()).contains(s.item()) : in.item().equals(s.item());
				if (!item) {
					return false;
				}
				if (in.components() != null) {
					for (String k : in.components().keySet()) {
						if (!in.components().get(k).getAsString().equals(s.components().get(k))) {
							return false;
						}
					}
				}
				return true;
			}
		};
	}

	private static List<Integer> required(ForgeRecipeSpec r) {
		List<Integer> out = new ArrayList<>();
		r.ingredients().forEach(i -> out.add(i.count()));
		return out;
	}

	/** Removes what the plan says; checks it never takes more than a stack holds, nor more than the recipe needs. */
	private static List<Stack> pay(List<Stack> stacks, ForgeRecipeSpec r, ForgeIngredients.Plan plan) {
		List<Stack> after = new ArrayList<>();
		int need = required(r).stream().mapToInt(Integer::intValue).sum();
		assertEquals(need, plan.total(), "exactly what the recipe asks, no more");
		for (int s = 0; s < stacks.size(); s++) {
			Stack st = stacks.get(s);
			int take = plan.take()[s];
			assertTrue(take >= 0 && (st == null ? take == 0 : take <= st.count()), "slot " + s);
			after.add(st == null || st.count() == take ? null : new Stack(st.item(), st.count() - take, st.components()));
		}
		return after;
	}

	private static int count(List<Stack> stacks, String item) {
		return stacks.stream().filter(s -> s != null && s.item().equals(item)).mapToInt(Stack::count).sum();
	}

	@Test
	void exactPaymentOverSeveralStacks() throws Exception {
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"item\": \"gold_ingot\", \"count\": 4}, {\"item\": \"diamond\"}], \"result\": \"stone\"}");
		List<Stack> inv = new ArrayList<>(List.of(Stack.of("minecraft:gold_ingot", 3), Stack.of("minecraft:dirt", 64), Stack.of("minecraft:gold_ingot", 2),
				Stack.of("minecraft:diamond", 2)));
		inv.add(null);
		ForgeIngredients.Plan plan = ForgeIngredients.plan(required(r), inventory(inv, r));
		assertTrue(plan.complete());
		assertEquals(5, plan.owned()[0], "owned gold for the interface");
		assertEquals(2, plan.owned()[1]);
		List<Stack> after = pay(inv, r, plan);
		assertEquals(1, count(after, "minecraft:gold_ingot"), "5 - 4");
		assertEquals(1, count(after, "minecraft:diamond"), "2 - 1");
		assertEquals(64, count(after, "minecraft:dirt"), "untouched");
	}

	@Test
	void missingIngredientsReported() throws Exception {
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"item\": \"gold_ingot\", \"count\": 4}, {\"item\": \"diamond\"}], \"result\": \"stone\"}");
		List<Stack> inv = List.of(Stack.of("minecraft:gold_ingot", 3));
		ForgeIngredients.Plan plan = ForgeIngredients.plan(required(r), inventory(inv, r));
		assertFalse(plan.complete());
		assertEquals(1, plan.missing()[0]);
		assertEquals(1, plan.missing()[1]);
		assertEquals(3, plan.owned()[0]);
		assertEquals(0, plan.owned()[1]);
	}

	@Test
	void sharedStacksBetweenATagAndOneOfItsItems() throws Exception {
		// 3 gold ingots for the item, 2 of any ingot for the tag: 3 gold + 2 iron pays it, the gold going to the item
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"tag\": \"c:ingots\", \"count\": 2}, {\"item\": \"gold_ingot\", \"count\": 3}], \"result\": \"stone\"}");
		List<Stack> inv = List.of(Stack.of("minecraft:gold_ingot", 3), Stack.of("minecraft:iron_ingot", 2));
		ForgeIngredients.Plan plan = ForgeIngredients.plan(required(r), inventory(inv, r));
		assertTrue(plan.complete(), "a share-out exists (a greedy one taking the gold for the tag would fail)");
		List<Stack> after = pay(inv, r, plan);
		assertEquals(0, count(after, "minecraft:gold_ingot"));
		assertEquals(0, count(after, "minecraft:iron_ingot"));
		// with only 4 ingots in all it cannot be paid
		List<Stack> poor = List.of(Stack.of("minecraft:gold_ingot", 3), Stack.of("minecraft:iron_ingot", 1));
		ForgeIngredients.Plan p2 = ForgeIngredients.plan(required(r), inventory(poor, r));
		assertFalse(p2.complete());
		assertEquals(1, p2.missing()[0] + p2.missing()[1], "one ingot short");
	}

	@Test
	void componentsTellCurrenciesApart() throws Exception {
		// the server's coin: an emerald with a component; plain emeralds do not pay for it
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"item\": \"emerald\", \"count\": 5, \"components\": {\"monnaie\": \"couronne\"}},"
				+ " {\"item\": \"emerald\", \"count\": 2}], \"result\": \"stone\"}");
		Stack coins = new Stack("minecraft:emerald", 6, Map.of("monnaie", "couronne"));
		List<Stack> inv = List.of(Stack.of("minecraft:emerald", 1), coins);
		ForgeIngredients.Plan plan = ForgeIngredients.plan(required(r), inventory(inv, r));
		assertTrue(plan.complete(), "5 coins for the first, 1 plain + 1 coin for the second");
		List<Stack> after = pay(inv, r, plan);
		assertEquals(0, count(after, "minecraft:emerald"));
		List<Stack> plain = List.of(Stack.of("minecraft:emerald", 64));
		ForgeIngredients.Plan p2 = ForgeIngredients.plan(required(r), inventory(plain, r));
		assertFalse(p2.complete());
		assertEquals(5, p2.missing()[0], "plain emeralds are no coins");
		assertEquals(0, p2.missing()[1]);
	}

	@Test
	void largeQuantitiesAcrossTheWholeInventory() throws Exception {
		ForgeRecipeSpec r = recipe("{\"ingredients\": [{\"tag\": \"minecraft:planks\", \"count\": 300}], \"result\": \"stone\"}");
		List<Stack> inv = new ArrayList<>();
		for (int i = 0; i < 41; i++) {
			inv.add(Stack.of(i % 2 == 0 ? "minecraft:oak_planks" : "minecraft:spruce_planks", 10));
		}
		ForgeIngredients.Plan plan = ForgeIngredients.plan(required(r), inventory(inv, r));
		assertTrue(plan.complete());
		List<Stack> after = pay(inv, r, plan);
		assertEquals(410 - 300, count(after, "minecraft:oak_planks") + count(after, "minecraft:spruce_planks"));
		Map<Integer, Integer> unused = new HashMap<>();
		for (int s = 0; s < inv.size(); s++) {
			unused.put(s, inv.get(s).count() - plan.take()[s]);
		}
		assertEquals(110, unused.values().stream().mapToInt(Integer::intValue).sum());
	}

	// ------------------------------------------------------------------ the crafting state machine

	@Test
	void craftingStateMachine() {
		ForgeCraft c = new ForgeCraft();
		assertFalse(c.busy() || c.crafting());
		assertEquals(0, c.progress(100), EPS);
		assertNull(c.complete(), "nothing to complete at rest");
		assertTrue(c.start(1000, 200, "medievalships:forge_divine_essai", "uuid-1", "Alice", "Lame divine (essai)"));
		assertTrue(c.busy() && c.crafting() && !c.animationOnly());
		assertFalse(c.start(1050, 100, "x:y", "uuid-2", "Bob", "Autre"), "one crafting at a time: the forge is busy");
		assertEquals("uuid-1", c.player(), "the second request changed nothing");
		assertEquals(1200, c.end());
		assertEquals(0.25, c.progress(1050), EPS);
		assertEquals(150, c.remaining(1050));
		assertFalse(c.due(1199));
		assertTrue(c.due(1200));
		assertTrue(c.busy(), "still busy until the server completes it");
		assertEquals(1.0, c.progress(5000), EPS);
		assertEquals(0.0, c.progress(10), EPS, "a clock before the start");
		ForgeCraft.Finished f = c.complete();
		assertNotNull(f);
		assertEquals("medievalships:forge_divine_essai", f.recipe());
		assertEquals("uuid-1", f.player());
		assertEquals("Alice", f.playerName());
		assertFalse(f.animationOnly());
		assertFalse(c.busy());
		assertNull(c.label());
		assertTrue(c.start(1300, 60, null, "uuid-3", "Carol", "Animation"), "free again");
		assertTrue(c.animationOnly());
		assertNull(c.player(), "an animation is crafted for nobody");
		c.endAt(1310);
		assertTrue(c.due(1310), "stopped by an administrator");
		assertTrue(c.complete().animationOnly());
		assertTrue(c.start(0, 999_999, null, null, null, "Animation"));
		assertEquals(ForgeCraft.MAX_TICKS, c.end(), "one hour at most");
		c.reset();
		assertTrue(c.start(0, -5, null, null, null, null));
		assertEquals(1, c.end(), "at least one tick");
	}

	@Test
	void craftingStateRestoredAfterARestart() {
		ForgeCraft c = new ForgeCraft();
		c.restore(true, 500, 900, "ns:r", "uuid", "Alice", "Lame");
		assertTrue(c.crafting());
		assertEquals(400, c.remaining(500));
		assertEquals("ns:r", c.recipe());
		assertEquals("Alice", c.playerName());
		c.restore(true, 900, 900, "ns:r", "uuid", "Alice", "Lame");
		assertFalse(c.crafting(), "an end not after the start: at rest");
		c.restore(false, 500, 900, "ns:r", "uuid", "Alice", "Lame");
		assertFalse(c.crafting());
		c.restore(true, 500, 900, "", "uuid", "Alice", "");
		assertTrue(c.animationOnly(), "an empty recipe: an animation");
		assertNull(c.player());
		assertNull(c.label());
	}

	// ------------------------------------------------------------------ the animation

	@Test
	void flipbookImagesCycle() {
		assertEquals(0, ForgeAnimation.frame(0.0, 4));
		assertEquals(0, ForgeAnimation.frame(0.99, 4));
		assertEquals(1, ForgeAnimation.frame(1.0, 4));
		assertEquals(3, ForgeAnimation.frame(3.5, 4));
		assertEquals(0, ForgeAnimation.frame(4.0, 4));
		assertEquals(3, ForgeAnimation.frame(-0.5, 4), "negative phases cycle too");
		assertEquals(0, ForgeAnimation.frame(Double.NaN, 4));
		assertEquals(0, ForgeAnimation.frame(7.3, 1));
		// at rest the fire shows each of its four images within a second, in order
		ForgeAnimation.Track t = new ForgeAnimation.Track();
		t.update(0, false);
		List<Integer> seen = new ArrayList<>();
		for (int tick = 1; tick <= 20; tick++) {
			t.update(tick, false);
			int f = t.fireFrame(4);
			if (seen.isEmpty() || seen.get(seen.size() - 1) != f) {
				seen.add(f);
			}
		}
		assertTrue(seen.size() >= 4, "four images or more in a second: " + seen);
		for (int i = 1; i < seen.size(); i++) {
			assertEquals((seen.get(i - 1) + 1) % 4, (int) seen.get(i), "one image after the other: " + seen);
		}
		int left = t.flowFrame(true, 4), right = t.flowFrame(false, 4);
		assertTrue(left >= 0 && left < 4 && right >= 0 && right < 4);
	}

	@Test
	void gearsTurnSlowlyAtRestFasterWhileCrafting() {
		ForgeAnimation.Track rest = new ForgeAnimation.Track();
		rest.update(0, false);
		for (int tick = 1; tick <= 40; tick++) {
			rest.update(tick, false);
		}
		assertEquals(ForgeAnimation.GEAR_IDLE_DPS * 2.0, rest.gear, 1e-6, "two seconds at rest");
		assertEquals(0.0, rest.intensity, EPS);
		ForgeAnimation.Track craft = new ForgeAnimation.Track();
		craft.update(0, true);
		assertEquals(1.0, craft.intensity, EPS, "a forge first seen crafting starts at full pace");
		for (int tick = 1; tick <= 40; tick++) {
			craft.update(tick, true);
		}
		assertEquals(ForgeAnimation.GEAR_CRAFT_DPS * 2.0, craft.gear, 1e-6);
		assertTrue(ForgeAnimation.GEAR_CRAFT_DPS > 3 * ForgeAnimation.GEAR_IDLE_DPS, "clearly faster while crafting");
		assertTrue(ForgeAnimation.FIRE_CRAFT_FPS > ForgeAnimation.FIRE_IDLE_FPS && ForgeAnimation.FLOW_CRAFT_FPS > ForgeAnimation.FLOW_IDLE_FPS);
		// gear_a clockwise seen from the front (negative about +z), gear_b the other way
		assertEquals(-30.0, ForgeAnimation.gearAngle(30.0, true), EPS);
		assertEquals(30.0, ForgeAnimation.gearAngle(30.0, false), EPS);
	}

	@Test
	void theChangeOfPaceIsEasedWithoutAJump() {
		ForgeAnimation.Track t = new ForgeAnimation.Track();
		t.update(0, false);
		double lastAngle = 0, lastStep = 0;
		for (int frame = 1; frame <= 400; frame++) {
			double time = frame * 0.5; // two frames per tick
			boolean crafting = time >= 40 && time < 120; // a crafting from 2 s to 6 s
			double before = t.gear;
			t.update(time, crafting);
			double step = (t.gear - before + 360.0) % 360.0;
			assertTrue(step >= 0 && step < 5, "the angle only moves forward, by small steps: " + step);
			if (frame > 1) {
				assertTrue(Math.abs(step - lastStep) < 0.2, "no jump of speed at frame " + frame + ": " + lastStep + " -> " + step);
			}
			lastStep = step;
			lastAngle = t.gear;
		}
		assertTrue(lastAngle >= 0 && lastAngle < 360);
		assertTrue(t.intensity < 0.01, "back to rest after the crafting");
		// a pause (the game paused, the forge far away) or another world: no jump either
		double g = t.gear;
		t.update(400 + 20 * 60, false);
		assertEquals(g, t.gear, EPS, "a long gap restarts from the current pose");
		t.update(10, false);
		assertEquals(g, t.gear, EPS, "time going back: same");
	}

	@Test
	void effectsPace() {
		assertTrue(ForgeAnimation.near(24 * 24));
		assertFalse(ForgeAnimation.near(24.1 * 24.1));
		assertTrue(ForgeAnimation.chance(ForgeAnimation.SPARK_IDLE, ForgeAnimation.SPARK_CRAFT, true) > ForgeAnimation.SPARK_IDLE);
		for (double r : new double[] {0, 0.3, 0.999999, 1.0, -1}) {
			int i = ForgeAnimation.interval(ForgeAnimation.HAMMER_MIN, ForgeAnimation.HAMMER_MAX, r);
			assertTrue(i >= ForgeAnimation.HAMMER_MIN && i <= ForgeAnimation.HAMMER_MAX, r + " -> " + i);
		}
		assertTrue(ForgeAnimation.STEAM_CRAFT_MAX < ForgeAnimation.STEAM_IDLE_MIN, "steam puffs more often while crafting");
	}
}
