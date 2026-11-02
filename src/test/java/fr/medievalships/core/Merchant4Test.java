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
import java.util.ArrayDeque;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The merchant tents IV (1.17.0): the baker's and the fishmonger's gabled stalls (the fishmonger's longer). Tents like
 * the thirteen of 1.14.0 - 1.16.0 (group "tents", tab "Tentes", each with its own atlas, tools/merchant/merchantlib.py
 * stall()), open at the front, with a free spot of 1 x 1 x 2.2 blocks behind the counter for a merchant NPC that a
 * player can walk to from the front. The checks hold for the stub copies they start from as well.
 */
public class Merchant4Test {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("tente_boulanger", "tente_poissonnier");

	@Test
	void twoStallsLoadInTheTentsTabAfterTheOthers() {
		assertEquals(2, TentTypes.MERCHANTS4.size());
		assertEquals(TentTypes.MERCHANTS4, TentTypes.ALL.subList(19, 21), "after the camp tents and the merchant tents I, II and III");
		assertEquals(22, TentTypes.ALL.size(), "the merchant stalls IV, then the jeweller's tent (1.21.0) in the tents' tab");
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.MERCHANTS4.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.TENTS, t.group());
			assertFalse(t.isCart() || t.isWorkshop() || t.isCannon(), t.id());
			assertFalse(t.masculine(), t.id() + ": une tente");
			assertFalse(TentTypes.MERCHANTS.contains(t) || TentTypes.MERCHANTS2.contains(t) || TentTypes.MERCHANTS3.contains(t), t.id());
			assertTrue(TentTypes.ALL.contains(t) && TentTypes.PROPS.contains(t), t.id() + " in the tents' tab and the props");
			assertTrue(t.frenchName().startsWith("tente du "), t.frenchName());
			assertTrue(t.englishName().endsWith("'s Stall"), t.englishName());
			assertEquals("models/entity/" + t.id() + ".bbmodel", t.model());
			assertEquals("textures/entity/" + t.id() + ".png", t.texture(), t.id() + " its own atlas");
			assertEquals(null, t.muzzle(), t.id() + ": a tent has no muzzle");
		}
		assertEquals("tente du boulanger", TentTypes.MERCHANT_BAKER.frenchName());
		assertEquals("Baker's Stall", TentTypes.MERCHANT_BAKER.englishName());
		assertEquals("tente du poissonnier", TentTypes.MERCHANT_FISHMONGER.frenchName());
		assertEquals("Fishmonger's Stall", TentTypes.MERCHANT_FISHMONGER.englishName());
		assertSame(TentTypes.MERCHANT_BAKER, TentTypes.byId("tente_boulanger"));
		assertSame(TentTypes.MERCHANT_BAKER, TentTypes.byId("medievalships:tente_boulanger"));
		assertSame(TentTypes.MERCHANT_BAKER, TentTypes.byId(" Boulanger "));
		assertSame(TentTypes.MERCHANT_FISHMONGER, TentTypes.byId("poissonnier"));
		assertSame(TentTypes.MERCHANT_POISON, TentTypes.byId("poison"), "the poison merchant keeps its short id");
	}

	@Test
	void geometryToScaleCollidersInsidePostsAndAWalkInMerchantSpot() {
		for (TentType t : TentTypes.MERCHANTS4) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, t.id() + " stands on the ground");
			assertTrue(e.width() > 5.0 && e.width() < 12.5, t.id() + " width " + e.width());
			assertTrue(e.depth() > 5.0 && e.depth() < 11.0, t.id() + " depth " + e.depth());
			assertTrue(e.height() > 4.0 && e.height() < 10.0, t.id() + " height " + e.height());
			assertTrue(t.colliders().size() >= 4, t.id() + " collision boxes " + t.colliders().size());
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, t.id() + " inside the extent " + b);
				if (b.height() > 2.5 && b.width() < 0.6 && b.depth() < 0.6) {
					posts++;
				}
				// the front edge is walkable: nothing solid on the middle of the last half block before the front
				boolean blocksFront = b.x0() < 0.5 && b.x1() > -0.5 && b.z1() > e.z1() - 0.5 && b.y0() < 1.5;
				assertFalse(blocksFront, t.id() + " the front is walkable " + b);
			}
			assertTrue(posts >= 4, t.id() + " four solid posts (" + posts + ")");
			assertTrue(Merchant2Test.freeSpot(t), t.id() + " a free spot of 1 x 1 x 2.2 blocks inside the tent for a merchant NPC");
			assertTrue(walkIn(t), t.id() + " a player walks from the front to a free 1 x 1 x 2.2 spot in the back half of the stall");
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	/** May a player (0.6 x 0.6 x 1.8, stepping over 0.6) walk from before the front to a free 1 x 1 x 2.2 spot behind z = 0? */
	static boolean walkIn(TentType t) {
		TentType.Box e = t.extent();
		double step = 0.1, x0 = e.x0() - 1.0, z0 = e.z0() - 0.5;
		int nx = (int) Math.ceil((e.width() + 2.0) / step), nz = (int) Math.ceil((e.depth() + 2.5) / step);
		boolean[][] seen = new boolean[nx][nz];
		ArrayDeque<int[]> todo = new ArrayDeque<>();
		for (int i = 0; i < nx; i++) {
			int k = nz - 1;
			if (free(t, x0 + i * step, z0 + k * step, 0.3, 1.8)) {
				seen[i][k] = true;
				todo.add(new int[] {i, k});
			}
		}
		while (!todo.isEmpty()) {
			int[] c = todo.poll();
			double x = x0 + c[0] * step, z = z0 + c[1] * step;
			if (z < 0.0 && free(t, x, z, 0.5, 2.2)) {
				return true;
			}
			for (int[] d : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
				int i = c[0] + d[0], k = c[1] + d[1];
				if (i >= 0 && k >= 0 && i < nx && k < nz && !seen[i][k] && free(t, x0 + i * step, z0 + k * step, 0.3, 1.8)) {
					seen[i][k] = true;
					todo.add(new int[] {i, k});
				}
			}
		}
		return false;
	}

	private static boolean free(TentType t, double x, double z, double half, double h) {
		for (TentType.Box b : t.colliders()) {
			if (b.x0() < x + half && b.x1() > x - half && b.z0() < z + half && b.z1() > z - half && b.y0() < h && b.y1() > 0.6) {
				return false;
			}
		}
		return true;
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
		for (TentType t : TentTypes.MERCHANTS4) {
			String key = "block.medievalships." + t.id();
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1), fr.get(key).getAsString(),
					"same French name in the commands and the lang file");
			assertEquals(t.englishName(), en.get(key).getAsString());
			for (String file : new String[] {"tents/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
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

	@Test
	void modelsLoadStaticWithAtMostARareParticle() throws Exception {
		for (TentType t : TentTypes.MERCHANTS4) {
			try (var in = Merchant4Test.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000 && m.quadCount() < 900 * 6, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a tent has no animation");
			}
			// the baker's oven may give off a rare wisp of smoke; nothing permanent
			for (TentType.Particle p : t.particles()) {
				assertTrue(p.known() && p.chance() <= 0.15 && p.count() <= 2, t.id() + " a rare discreet particle only " + p);
			}
			if (t.decor() != null) {
				InteriorDecor.load(t.decor());
			}
		}
	}
}
