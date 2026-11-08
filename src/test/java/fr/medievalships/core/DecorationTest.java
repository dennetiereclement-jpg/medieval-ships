package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The street decorations (1.20.0): eight one-block props of two posts (one for the lantern and the banner, four for the
 * shade sails) with cloth, ropes, a net, herbs, a banner or a lantern (group "decorations", tab "Décorations", one shared
 * atlas textures/entity/decorations.png, tools/deco/decolib.py). Each loads, stands on the ground, is 1 to 8 blocks wide
 * and at most 6 high; only its posts (and stone footings) collide, as thin boxes inside the drawn model, and the passage
 * between two posts is free (cloth, ropes, nets, lanterns never block a player); the JSON's "light" gives the anchor
 * block's luminance (the hanging lantern 15, the bunting 12, the others 0), clamped to 0-15. The checks hold for the
 * stub copies of the bunting that stand for D2's four ids until their models arrive.
 */
public class DecorationTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("deco_guirlande", "deco_etendoir", "deco_draperie", "deco_filet", "deco_sechoir",
			"deco_lanterne", "deco_banniere", "deco_ombrage", "pieu_defensif");
	/** The eight street decorations with posts (the defensive stake of 1.24.0, the ninth, has its own checks: StakeTest). */
	private static final List<TentType> STREET = TentTypes.DECORATIONS.subList(0, 8);

	@Test
	void eightDecorationsInTheirOwnTab() {
		assertEquals(9, TentTypes.DECORATIONS.size(), "the eight street decorations, then the defensive stake (1.24.0)");
		assertSame(TentTypes.STAKE, TentTypes.DECORATIONS.get(8));
		assertEquals(TentTypes.DECORATIONS, TentTypes.PROPS.subList(46, 55), "after the training areas, before the cannon");
		assertSame(TentTypes.CANNON, TentTypes.PROPS.get(TentTypes.PROPS.size() - 1), "the artillery stays last");
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.DECORATIONS.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.DECORATIONS, t.group());
			assertTrue(t.isDecoration(), t.id());
			assertFalse(t.isCart() || t.isWorkshop() || t.isCannon() || t.isTraining(), t.id());
			assertFalse(TentTypes.ALL.contains(t), t.id() + " not in the tents' tab");
			assertEquals("models/entity/" + t.id() + ".bbmodel", t.model());
			assertEquals(t == TentTypes.STAKE ? "textures/entity/pieu_defensif.png" : "textures/entity/decorations.png", t.texture(),
					t.id() + " the shared atlas (the stake: its own small one)");
			assertEquals(t == TentTypes.STAKE, t.hasHazard(), t.id() + " only the stake hurts");
			assertEquals(null, t.decor(), t.id() + " no furniture of the decoration mods");
			assertEquals(null, t.muzzle(), t.id());
			assertTrue(t.seats().isEmpty() && !t.hasTargets(), t.id());
		}
		for (TentType t : TentTypes.PROPS) {
			assertEquals(TentTypes.DECORATIONS.contains(t), t.isDecoration(), t.id());
		}
		assertSame(TentTypes.DECO_BUNTING, TentTypes.byId("deco_guirlande"));
		assertSame(TentTypes.DECO_BUNTING, TentTypes.byId("medievalships:deco_guirlande"));
		assertSame(TentTypes.DECO_BUNTING, TentTypes.byId(" Guirlande "));
		assertSame(TentTypes.DECO_NET, TentTypes.byId("filet"));
		assertSame(TentTypes.DECO_LANTERN, TentTypes.byId("lanterne"));
		assertSame(TentTypes.MARKET, TentTypes.byId("market"), "the other props keep their short names");
	}

	@Test
	void frenchGenderAndNumber() {
		// "Étendoir à linge posé", "Guirlande festive posée", "Toiles d'ombrage posées"
		assertEquals("", TentTypes.DECO_CLOTHESLINE.agreement());
		assertEquals("", TentTypes.DECO_NET.agreement());
		assertEquals("", TentTypes.DECO_HERBS.agreement());
		assertEquals("e", TentTypes.DECO_BUNTING.agreement());
		assertEquals("e", TentTypes.DECO_DRAPERY.agreement());
		assertEquals("e", TentTypes.DECO_LANTERN.agreement());
		assertEquals("e", TentTypes.DECO_BANNER.agreement());
		assertEquals("es", TentTypes.DECO_SHADE.agreement());
		assertTrue(TentTypes.DECO_SHADE.plural() && !TentTypes.DECO_SHADE.masculine());
		assertTrue(TentTypes.DECO_CLOTHESLINE.masculine() && !TentTypes.DECO_CLOTHESLINE.plural());
		// the other families keep their own rule
		assertTrue(TentTypes.CANNON.masculine() && TentTypes.WORKSHOP_COOK.masculine() && !TentTypes.ADVENTURER.masculine());
		assertEquals("e", TentTypes.ADVENTURER.agreement());
	}

	@Test
	void smallStreetPropsOnTheGround() {
		for (TentType t : TentTypes.DECORATIONS) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, t.id() + " stands on the ground");
			double wide = Math.max(e.width(), e.depth());
			assertTrue(wide >= 1.0 && wide <= 8.0, t.id() + " 1 to 8 blocks wide: " + wide);
			assertTrue(e.height() >= 1.5 && e.height() <= 6.0, t.id() + " at most 6 high: " + e.height());
			assertTrue(e.x0() < 0 && e.x1() > 0 && e.z0() < 0.5 && e.z1() > -0.5, t.id() + " round its anchor block " + e);
		}
	}

	@Test
	void onlyThePostsCollideAsThinBoxes() {
		for (TentType t : STREET) {
			TentType.Box e = t.extent();
			List<TentType.Box> cs = t.colliders();
			assertFalse(cs.isEmpty(), t.id() + " its posts collide");
			int posts = 0;
			for (TentType.Box b : cs) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, t.id() + " no invisible wall: inside the extent " + b);
				assertTrue(b.width() <= 0.9 && b.depth() <= 0.9, t.id() + " a thin box (a post or its footing) " + b);
				if (b.y0() < 1.0 && b.y1() > 2.0) { // from the ground or from its stone footing
					posts++;
				}
			}
			assertTrue(posts >= 1, t.id() + " at least one tall post collides (" + posts + ")");
			assertEquals(cs.size(), t.colliders(TentType.EAST).size());
		}
	}

	@Test
	void theWayBetweenThePostsIsFree() {
		for (TentType t : STREET) {
			List<TentType.Box> posts = new ArrayList<>();
			for (TentType.Box b : t.colliders()) {
				// a post stands on the ground or on its stone footing (the hanging lantern's body is not a post)
				if (b.y1() > 2.0 && b.y0() < 1.0) {
					posts.add(b);
				}
			}
			if (posts.size() >= 2) {
				// a player (0.6 wide, 1.8 high) walks through between the two posts farthest apart, front to back
				TentType.Box a = posts.get(0), b = posts.get(0);
				double best = -1;
				for (TentType.Box p : posts) {
					for (TentType.Box q : posts) {
						double d = Math.hypot(cx(p) - cx(q), cz(p) - cz(q));
						if (d > best) {
							best = d;
							a = p;
							b = q;
						}
					}
				}
				double mx = (cx(a) + cx(b)) / 2, mz = (cz(a) + cz(b)) / 2;
				for (double z = mz - 1.5; z <= mz + 1.5; z += 0.1) {
					assertTrue(free(t, mx, z, 0.3, 1.8), t.id() + " the way between the posts is free at z " + z);
				}
				assertTrue(best >= 2.0, t.id() + " posts at least 2 blocks apart (" + best + ")");
			} else {
				// one post: a player can stand right in front of it and beside it (the arm, the banner, the lantern do not collide)
				TentType.Box p = posts.get(0);
				assertTrue(free(t, cx(p), p.z1() + 0.45, 0.3, 1.8), t.id() + " free in front of the post");
				assertTrue(free(t, p.x1() + 0.75, cz(p), 0.3, 1.8) || free(t, p.x0() - 0.75, cz(p), 0.3, 1.8), t.id() + " free beside the post");
			}
		}
	}

	private static double cx(TentType.Box b) {
		return (b.x0() + b.x1()) / 2;
	}

	private static double cz(TentType.Box b) {
		return (b.z0() + b.z1()) / 2;
	}

	/** Is a player box (half width r, height h) standing at (x, 0, z) clear of every collision box? */
	private static boolean free(TentType t, double x, double z, double r, double h) {
		for (TentType.Box b : t.colliders()) {
			if (x + r > b.x0() && x - r < b.x1() && z + r > b.z0() && z - r < b.z1() && h > b.y0() && 0.0 < b.y1()) {
				return false;
			}
		}
		return true;
	}

	@Test
	void lightOfTheLanterns() {
		assertEquals(12, TentTypes.DECO_BUNTING.light(), "the bunting's two small lanterns");
		assertEquals(15, TentTypes.DECO_LANTERN.light(), "the hanging lantern lights like a torch");
		for (TentType t : TentTypes.DECORATIONS) {
			assertTrue(t.light() >= 0 && t.light() <= TentType.MAX_LIGHT, t.id());
			if (t != TentTypes.DECO_BUNTING && t != TentTypes.DECO_LANTERN) {
				assertEquals(0, t.light(), t.id() + " gives no light");
			}
		}
		for (TentType t : TentTypes.PROPS) {
			if (t == TentTypes.MERCHANT_JEWELLER) {
				assertEquals(12, t.light(), "the jeweller's tent (1.21.0) lights its stall (lanterns, glowing gems)");
			} else if (TentTypes.CAMP_TENTS.contains(t)) {
				assertTrue(t.light() >= 0 && t.light() <= TentType.MAX_LIGHT, t.id() + " the military camp (1.24.0): lit or not, its builder decides");
			} else if (!t.isDecoration()) {
				assertEquals(0, t.light(), t.id() + " the older props give no light");
			}
		}
		assertEquals(15, TentType.parseLight(json("{\"light\": 20}")), "clamped to 15");
		assertEquals(0, TentType.parseLight(json("{\"light\": -3}")), "clamped to 0");
		assertEquals(0, TentType.parseLight(json("{}")), "absent: none");
		assertEquals(0, TentType.parseLight(json("{\"light\": null}")));
		assertEquals(0, TentType.parseLight(json("{\"light\": \"bright\"}")), "not a number: none");
		assertEquals(7, TentType.parseLight(json("{\"light\": 7}")));
		TentType parsed = TentType.parse(TentType.DECORATIONS, "deco_test", "décoration de test", "Test Decoration",
				json("{\"extent\": [-1, 0, -1, 1, 2, 1], \"colliders\": [], \"light\": 9}"));
		assertEquals(9, parsed.light());
		assertTrue(parsed.isDecoration());
	}

	private static JsonObject json(String s) {
		return JsonParser.parseString(s).getAsJsonObject();
	}

	@Test
	void modelsLoadStaticAndLight() throws Exception {
		for (TentType t : TentTypes.DECORATIONS) {
			try (var in = DecorationTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 60 && m.quadCount() <= 250 * 6, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a decoration has no animation");
				assertTrue(m.bonesByName.containsKey("detail"), t.id() + ": small things under the bone 'detail' (hidden far away)");
			}
			JsonObject model;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve(t.model()), StandardCharsets.UTF_8)) {
				model = JsonParser.parseReader(r).getAsJsonObject();
			}
			int cubes = 0, glow = 0;
			for (JsonElement el : model.getAsJsonArray("elements")) {
				cubes++;
				if (el.getAsJsonObject().get("name").getAsString().startsWith("glow")) {
					glow++;
				}
			}
			assertTrue(cubes <= 250, t.id() + " a light model (" + cubes + " cubes): hundreds stand in a city");
			if (t.light() > 0) {
				assertTrue(glow >= 1, t.id() + " gives light: its lantern glass is drawn full bright (" + glow + ")");
			}
		}
		assertTrue(Files.isRegularFile(ASSETS.resolve("textures/entity/decorations.png")), "the shared atlas");
		var img = javax.imageio.ImageIO.read(ASSETS.resolve("textures/entity/decorations.png").toFile());
		assertEquals(512, img.getWidth());
		assertEquals(512, img.getHeight());
	}

	@Test
	void namesAndItemFiles() throws Exception {
		JsonObject fr;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/fr_fr.json"), StandardCharsets.UTF_8)) {
			fr = JsonParser.parseReader(r).getAsJsonObject();
		}
		JsonObject en;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/en_us.json"), StandardCharsets.UTF_8)) {
			en = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals("Décorations", fr.get("itemGroup.medievalships.decorations").getAsString());
		assertEquals("Decorations", en.get("itemGroup.medievalships.decorations").getAsString());
		for (TentType t : TentTypes.DECORATIONS) {
			String key = "block.medievalships." + t.id();
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1), fr.get(key).getAsString(),
					"same French name in the commands and the lang file");
			assertEquals(t.englishName(), en.get(key).getAsString());
			for (String file : new String[] {"decorations/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
					"models/item/" + t.id() + ".json", "textures/item/" + t.id() + ".png", t.model(), t.texture()}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), t.id() + ": " + file);
			}
			JsonObject states;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("blockstates/" + t.id() + ".json"), StandardCharsets.UTF_8)) {
				states = JsonParser.parseReader(r).getAsJsonObject().getAsJsonObject("variants");
			}
			for (String f : new String[] {"north", "south", "west", "east"}) {
				assertTrue(states.has("facing=" + f), t.id() + " blockstate facing=" + f);
			}
			JsonObject item;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("models/item/" + t.id() + ".json"), StandardCharsets.UTF_8)) {
				item = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertEquals("medievalships:item/" + t.id(), item.getAsJsonObject("textures").get("layer0").getAsString());
		}
	}
}
