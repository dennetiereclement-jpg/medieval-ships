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
import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The jeweller's tent (1.21.0, {@link TentTypes#MERCHANTS5}): a merchant tent like the fifteen of 1.14.0 - 1.17.0 (group
 * "tents", tab "Tentes", its own atlas, tools/merchant/generate_tente_joaillier.py on merchantlib.stall + props_m10.py),
 * about 8 x 5.5 blocks with its raised pointed roof centre, open at the front, a walkable middle, a free place of
 * 1 x 1 x 2.2 blocks behind the right counter for a merchant NPC, a lit anchor block, no seats.
 */
public class JoaillierTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final TentType T = TentTypes.MERCHANT_JEWELLER;

	@Test
	void loadsLastInTheTentsTab() {
		assertEquals(1, TentTypes.MERCHANTS5.size());
		assertSame(T, TentTypes.MERCHANTS5.get(0));
		assertEquals(TentTypes.MERCHANTS5, TentTypes.ALL.subList(21, 22), "after the merchant tents I to IV");
		assertEquals("tente_joaillier", T.id());
		assertEquals(TentType.TENTS, T.group());
		assertFalse(T.isCart() || T.isWorkshop() || T.isCannon() || T.isTraining() || T.isDecoration());
		assertTrue(TentTypes.PROPS.contains(T));
		assertEquals("tente du joaillier", T.frenchName());
		assertEquals("Jeweller's Tent", T.englishName());
		assertFalse(T.masculine(), "une tente");
		assertEquals("models/entity/tente_joaillier.bbmodel", T.model());
		assertEquals("textures/entity/tente_joaillier.png", T.texture(), "its own atlas");
		assertEquals(null, T.muzzle());
		assertSame(T, TentTypes.byId("tente_joaillier"));
		assertSame(T, TentTypes.byId("medievalships:tente_joaillier"));
		assertSame(T, TentTypes.byId(" Joaillier "));
	}

	@Test
	void jsonModelDecorAndNames() throws Exception {
		for (String file : new String[] {"tents/tente_joaillier.json", "blockstates/tente_joaillier.json", "items/tente_joaillier.json",
				"models/item/tente_joaillier.json", "textures/item/tente_joaillier.png", T.model(), T.texture(),
				"interiors/tente_joaillier_decor.json"}) {
			assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
		}
		JsonObject root;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("tents/tente_joaillier.json"), StandardCharsets.UTF_8)) {
			root = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals(12, root.get("light").getAsInt(), "the JSON light of the anchor block");
		assertEquals(12, T.light(), "the anchor block lights the tent (lanterns, glowing gems)");
		for (String lang : new String[] {"fr_fr", "en_us"}) {
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang + ".json"), StandardCharsets.UTF_8)) {
				JsonObject names = JsonParser.parseReader(r).getAsJsonObject();
				assertEquals(lang.equals("fr_fr") ? "Tente du joaillier" : "Jeweller's Tent", names.get("block.medievalships.tente_joaillier").getAsString());
			}
		}
		try (var in = JoaillierTest.class.getResourceAsStream("/assets/medievalships/" + T.model())) {
			assertNotNull(in, T.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 1000 && m.quadCount() <= 1000 * 6, "at most about 1000 cubes: faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "static: no animation");
		}
		assertTrue(T.particles().isEmpty(), "no particles, nothing ticks");
		assertTrue(T.seats().isEmpty(), "no seats");
		InteriorDecor decor = InteriorDecor.load(T.decor());
		Set<String> ids = new HashSet<>();
		for (InteriorDecor.Block b : decor.blocks()) {
			ids.add(b.block());
			assertFalse(b.fallback().isEmpty(), b.block() + " has a stand-in");
		}
		assertTrue(ids.contains("minecraft:amethyst_cluster") && ids.contains("furnish:spruce_crate")
				&& ids.contains("farmhouse_decorations:chained_kerosene_lantern"), "mod / vanilla blocks " + ids);
		assertTrue(decor.seats().isEmpty());
	}

	@Test
	void scalePostsOpenFrontAndTheMerchantsPlace() {
		TentType.Box e = T.extent();
		assertEquals(0.0, e.y0(), 1e-9, "stands on the ground");
		assertTrue(e.width() > 7.5 && e.width() < 11.0, "wider than deep, about 8 blocks + the hipped left end: " + e.width());
		assertTrue(e.depth() > 5.5 && e.depth() < 7.5, "about 5.5 blocks deep + the crates outside: " + e.depth());
		assertTrue(e.width() > e.depth());
		assertTrue(e.height() > 6.0 && e.height() < 8.5, "the raised pointed centre and its finial: " + e.height());
		int posts = 0;
		for (TentType.Box b : T.colliders()) {
			assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
					"inside the extent " + b);
			if (b.height() > 3.0 && b.width() < 0.7 && b.depth() < 0.7) {
				posts++;
			}
			// the open front and the middle stay free: nothing solid in x -1 .. 1 from the middle to the front
			boolean blocks = b.x0() < 1.0 && b.x1() > -1.0 && b.z1() > -0.5 && b.y0() < 2.0;
			assertFalse(blocks, "the entrance and the middle are free " + b);
			// no invisible wall above the counters: nothing solid between 1.2 and 3 blocks high away from the walls and posts
			boolean wall = b.width() < 0.2 || b.depth() < 0.2;
			boolean post = b.height() > 3.0 && b.width() < 0.7 && b.depth() < 0.7;
			assertTrue(wall || post || b.y1() <= 2.0, "only posts and the curtain walls rise high (counters, vitrine, shelves at most 2) " + b);
		}
		assertEquals(4, posts, "four solid posts");
		// the merchant's place behind the right counter: 1 x 1 x 2.2 free
		double x0 = 1.6, z0 = -2.2;
		for (TentType.Box b : T.colliders()) {
			assertFalse(b.x0() < x0 + 1.0 && b.x1() > x0 && b.z0() < z0 + 1.0 && b.z1() > z0 && b.y0() < 2.2, "the NPC place is free " + b);
		}
		assertTrue(Merchant2Test.freeSpot(T));
		assertTrue(Merchant4Test.walkIn(T), "a player walks from the front to a free 1 x 1 x 2.2 place in the back half");
		assertEquals(T.colliders().size(), T.colliders(TentType.WEST).size());
	}
}
