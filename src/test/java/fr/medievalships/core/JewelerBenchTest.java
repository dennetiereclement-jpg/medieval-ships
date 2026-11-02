package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The jeweller's workbench (1.22.0, workshop_jeweler: tools/workshops/generate_workshop_jeweler.py on its own atlas
 * workshops_c.png) and the workshops' interaction hook: the profession ids (JSON "profession", default from the id) and
 * the server setting "workshopCommands" (parsed, cleaned, looked up by profession).
 */
public class JewelerBenchTest {
	private static final double EPS = 1e-6;
	private static final TentType J = TentTypes.WORKSHOP_JEWELER;

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = JewelerBenchTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}

	@Test
	void professionIdsOfTheEightWorkshops() {
		assertEquals(List.of("blacksmith", "leatherworker", "tailor", "engineer", "cook", "alchemist", "enchanter", "jeweler"),
				TentTypes.WORKSHOPS.stream().map(TentType::profession).toList());
		for (TentType t : TentTypes.PROPS) {
			if (!t.isWorkshop()) {
				assertNull(t.profession(), t.id() + " is no workshop: no profession");
			}
		}
		assertEquals("jeweler", TentType.defaultProfession("workshop_jeweler"));
		assertEquals("smith", TentType.defaultProfession("smith"));
	}

	@Test
	void professionFieldParsed() {
		String extent = "\"extent\": [-1, 0, -0.5, 1, 1.4, 0.5]";
		TentType given = TentType.parse(TentType.WORKSHOPS, "workshop_x", "atelier x", "X Workshop",
				JsonParser.parseString("{" + extent + ", \"profession\": \"  Goldsmith \"}").getAsJsonObject());
		assertEquals("goldsmith", given.profession(), "trimmed, lower case");
		TentType blank = TentType.parse(TentType.WORKSHOPS, "workshop_x", "atelier x", "X Workshop",
				JsonParser.parseString("{" + extent + ", \"profession\": \"  \"}").getAsJsonObject());
		assertEquals("x", blank.profession(), "blank: the id without workshop_");
		TentType absent = TentType.parse(TentType.WORKSHOPS, "workshop_x", "atelier x", "X Workshop",
				JsonParser.parseString("{" + extent + "}").getAsJsonObject());
		assertEquals("x", absent.profession());
		TentType cart = TentType.parse(TentType.CARTS, "cart_x", "charrette x", "X Cart",
				JsonParser.parseString("{" + extent + ", \"profession\": \"carter\"}").getAsJsonObject());
		assertNull(cart.profession(), "only the workshops have a profession");
	}

	@Test
	void workshopCommandsParsedAndCleaned() {
		ServerSettings defaults = new ServerSettings();
		defaults.sanitize();
		assertTrue(defaults.workshopCommands.isEmpty(), "empty by default");
		assertNull(defaults.workshopCommand("jeweler"));

		ServerSettings s = new Gson().fromJson("""
				{"workshopCommands": {" Jeweler ": "/trigger jeweler_menu", "workshop_blacksmith": "  function mmo:forge ",
				 "cook": "   ", "": "say nobody", "tailor": null}}""", ServerSettings.class);
		s.sanitize();
		assertEquals(Map.of("jeweler", "trigger jeweler_menu", "blacksmith", "function mmo:forge"), s.workshopCommands);
		assertEquals("trigger jeweler_menu", s.workshopCommand("jeweler"));
		assertEquals("trigger jeweler_menu", s.workshopCommand("workshop_jeweler"), "a workshop id works too");
		assertEquals("trigger jeweler_menu", s.workshopCommand(J.profession()));
		assertEquals("function mmo:forge", s.workshopCommand(TentTypes.WORKSHOP_BLACKSMITH.profession()));
		assertNull(s.workshopCommand("cook"), "a blank command is no command");
		assertNull(s.workshopCommand(null));

		ServerSettings old = new Gson().fromJson("{\"adminPermissionLevel\": 3}", ServerSettings.class);
		old.sanitize();
		assertTrue(old.workshopCommands.isEmpty(), "a config file of an older version");
		ServerSettings nulls = new Gson().fromJson("{\"workshopCommands\": null}", ServerSettings.class);
		nulls.sanitize();
		assertTrue(nulls.workshopCommands.isEmpty());
		assertNull(nulls.workshopCommand("jeweler"));

		// the API (as the in-game test uses it): set, replace, remove
		s.setWorkshopCommand("Jeweler", "/tag @s add used_jeweler");
		assertEquals("tag @s add used_jeweler", s.workshopCommand("jeweler"));
		s.setWorkshopCommand("workshop_jeweler", "trigger other");
		assertEquals("trigger other", s.workshopCommand("jeweler"));
		assertEquals(2, s.workshopCommands.size());
		s.setWorkshopCommand("jeweler", null);
		assertNull(s.workshopCommand("jeweler"));
		s.setWorkshopCommand("jeweler", " ");
		assertNull(s.workshopCommand("jeweler"));
		assertEquals("function mmo:forge", s.workshopCommand("blacksmith"), "the others are kept");

		// written back as an object (the config file shows the key, empty by default)
		JsonObject tree = new Gson().toJsonTree(defaults).getAsJsonObject();
		assertTrue(tree.has("workshopCommands") && tree.get("workshopCommands").isJsonObject());
		Map<String, String> m = new LinkedHashMap<>();
		m.put("jeweler", "trigger jeweler_menu");
		assertEquals("trigger jeweler_menu", new Gson().fromJson(new Gson().toJson(Map.of("workshopCommands", m)), ServerSettings.class)
				.workshopCommand("jeweler"));
	}

	@Test
	void benchSizeCollidersAndFiles() throws Exception {
		JsonObject j = json("/assets/medievalships/workshops/workshop_jeweler.json");
		assertEquals("models/entity/workshop_jeweler.bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/workshops_c.png", j.get("texture").getAsString(), "its own atlas");
		assertEquals("jeweler", j.get("profession").getAsString());
		TentType.Box e = J.extent();
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(e.width() > 1.9 && e.width() < 2.3, "about 2 blocks wide: " + e.width());
		assertTrue(e.depth() > 0.95 && e.depth() < 1.3, "about 1 block deep: " + e.depth());
		assertTrue(e.height() > 1.3 && e.height() < 1.5, "top at 1.0, the machine up to ~1.4: " + e.height());
		assertEquals(2, J.colliders().size(), "one box for the bench, one for the machine");
		TentType.Box bench = J.colliders().get(0);
		assertEquals(1.0, bench.y1(), 0.01, "the bench's top");
		assertTrue(bench.x0() <= 0 && bench.x1() >= 0 && bench.z0() <= 0 && bench.z1() >= 0, "the anchor block under the bench");
		TentType.Box machine = J.colliders().get(1);
		assertTrue(machine.y0() >= 0.99 && machine.y1() > 1.3 && machine.y1() <= e.y1() + EPS, "the machine above the top " + machine);
		assertTrue(J.particles().isEmpty(), "no particles: only the gems glow");
		assertNotNull(JewelerBenchTest.class.getResource("/assets/medievalships/textures/entity/workshops_c.png"));
		assertNotNull(JewelerBenchTest.class.getResource("/assets/medievalships/textures/item/workshop_jeweler.png"));
	}

	@Test
	void modelHasEveryElementOfTheReference() throws Exception {
		String path = "/assets/medievalships/models/entity/workshop_jeweler.bbmodel";
		try (InputStream in = JewelerBenchTest.class.getResourceAsStream(path)) {
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.animations.isEmpty(), "static");
			assertTrue(m.bonesByName.containsKey("detail"), "the small props are hidden at a distance");
		}
		JsonArray elements = json(path).getAsJsonArray("elements");
		assertTrue(elements.size() >= 120 && elements.size() <= 250, "cube budget " + elements.size());
		Set<String> names = new HashSet<>();
		int glow = 0;
		for (JsonElement el : elements) {
			String n = el.getAsJsonObject().get("name").getAsString();
			names.add(n);
			if (n.startsWith("glow_")) {
				glow++;
				assertTrue(n.contains("gem") || n.contains("stone"), "only the gems are lit: " + n);
			}
		}
		assertTrue(glow >= 20, "lit gems " + glow);
		String[][] parts = {
				{"leg_", "thick legs"}, {"stretcher_", "stretchers"}, {"brace_", "side braces"}, {"top_plank_", "plank top"},
				{"edge_front", "thick front edge"}, {"corner_iron_", "iron corner fittings"}, {"drawer_0", "left drawer"},
				{"drawer_1", "right drawer"}, {"drawer_pull_", "drawer pulls"}, {"shelf_", "lower shelf"}, {"shelf_ingot_", "gold on the shelf"},
				{"glow_shelf_gem_", "gems on the shelf"}, {"runner_top", "purple runner"}, {"runner_hang", "runner hanging at the front"},
				{"machine_base", "machine base"}, {"frame_", "cast-iron frame"}, {"disc", "polishing disc"}, {"hand_wheel", "hand wheel"},
				{"crank_grip", "crank"}, {"clamp_", "clamp"}, {"held_ring_", "the held gold ring"}, {"glow_held_gem", "its blue gem"},
				{"ingot_", "gold ingots"}, {"glow_gem_", "scattered gems"}, {"tray", "stone tray"}, {"glow_tray_gem_", "gems in the tray"},
				{"ring_a_", "a ring"}, {"glow_ring_a_stone", "a ring's stone"}, {"ring_b_", "another ring"}, {"hammer_head", "precision hammer"},
				{"pliers_jaw_", "pliers"}, {"stand_prong_", "prong stand"}, {"loupe_lens", "loupe"}, {"hook_", "hooks"},
				{"hung_pliers_", "hanging pliers"}, {"hung_hammer_", "hanging hammer"}};
		for (String[] p : parts) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(p[0])), p[1] + " (" + p[0] + "*)");
		}
		assertEquals(5, names.stream().filter(n -> n.matches("ingot_(top_)?\\d+")).count(), "five gold ingots on the left");
	}
}
