package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The market tents of group B (1.26.0, Lion Port blue and cream; tools/market/generate_tente_lion_drapee.py,
 * generate_tente_lion_chapiteau.py, generate_tente_balance_bleue.py on merchantlib + props_b): the draped lion tent (a
 * pointed four-sided roof with a flag pole, two side awnings, a plank floor), the royal lion marquee (one long rounded roof
 * up to an oval crown with a gold finial, a curtained left part, the tall banner post) and the blue scales tent (a short ridge on two
 * ridge posts, a left awning, the gallows sign). Each one: its JSON loads with {@link TentType#load} (the registration in
 * TentTypes is the integrator's), its own atlas and light, the model loads, static, about 6-12 wide and deep and at most
 * about 10 high, at most about 1000 cubes, a bone "detail", lit lanterns; the posts collide, the entrance and the aisle in
 * front of the counter are free, and the merchant's 1 x 1 x 2.2 place behind the counter is free and reachable on foot.
 */
public class MarketBTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/** One tent: its names, the merchant's place (x0, z0) of a 1 x 1 cell, the open aisle (x0, x1, z0) up to the front,
	 * its minimum number of tall posts and the mod blocks it must use. */
	private record Spec(String id, String fr, String en, double npcX, double npcZ, double aisleX0, double aisleX1, double aisleZ0,
			int posts, Set<String> mods) {
		TentType type() {
			return TentType.load(id, fr, en);
		}
	}

	private static final List<Spec> TENTS = List.of(
			new Spec("tente_lion_drapee", "Tente drapée au lion", "Draped Lion Tent", 0.6, -1.98, -0.8, 1.2, -0.2, 8,
					Set.of("furnish:spruce_crate", "farmersdelight:cabbage_crate", "farmersdelight:rice_bag")),
			new Spec("tente_lion_chapiteau", "Chapiteau royal au lion", "Royal Lion Marquee", 0.4, -0.12, 0.0, 2.4, 1.65, 5,
					Set.of("furnish:spruce_crate", "farmhouse_decorations:pile_of_books")),
			new Spec("tente_balance_bleue", "Tente bleue à la balance", "Blue Scales Tent", 0.0, 0.38, -0.5, 1.4, 2.15, 8,
					Set.of("furnish:spruce_crate", "landsoficaria:cypress_barrel", "farmersdelight:cabbage_crate")));

	@Test
	void jsonAtlasLightAndDecor() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			for (String file : new String[] {"tents/" + s.id() + ".json", "textures/item/" + s.id() + ".png", t.model(), t.texture(),
					"interiors/" + s.id() + "_decor.json", "../../../../../blockbench/" + s.id() + ".bbmodel"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), s.id() + ": " + file);
			}
			assertEquals(s.id(), t.id());
			assertEquals(TentType.TENTS, t.group(), s.id());
			assertEquals("models/entity/" + s.id() + ".bbmodel", t.model());
			assertEquals("textures/entity/" + s.id() + ".png", t.texture(), s.id() + ": its own atlas");
			JsonObject root;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("tents/" + s.id() + ".json"), StandardCharsets.UTF_8)) {
				root = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertEquals(13, root.get("light").getAsInt(), s.id());
			assertEquals(13, t.light(), s.id() + ": the anchor block lights the tent (lanterns)");
			assertTrue(t.particles().isEmpty(), s.id() + ": no particles, nothing ticks");
			assertTrue(t.seats().isEmpty(), s.id() + ": no seats");
			InteriorDecor decor = InteriorDecor.load(t.decor());
			Set<String> ids = new HashSet<>();
			for (InteriorDecor.Block b : decor.blocks()) {
				ids.add(b.block());
				assertFalse(b.fallback().isEmpty(), s.id() + ": " + b.block() + " has a stand-in");
				assertTrue(b.block().matches("[a-z_]+:[a-z0-9_]+"), b.block());
			}
			assertTrue(ids.containsAll(s.mods()), s.id() + ": mod blocks " + ids);
		}
	}

	@Test
	void modelsAreStaticLightAndLit() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			try (var in = MarketBTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 350 * 6 / 2 && m.quadCount() <= 1000 * 6, s.id() + ": at most about 1000 cubes, faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), s.id() + ": static, no animation");
				assertTrue(m.hasBone("detail"), s.id() + ": small things under the bone \"detail\" (hidden far away)");
				int[] glow = {0};
				m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
				assertTrue(glow[0] >= 3 * 4, s.id() + ": the lanterns' glass is lit (" + glow[0] + " full-bright faces)");
			}
			JsonObject bb;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve(t.model()), StandardCharsets.UTF_8)) {
				bb = JsonParser.parseReader(r).getAsJsonObject();
			}
			int elements = bb.getAsJsonArray("elements").size();
			assertTrue(elements <= 1000, s.id() + ": " + elements + " cubes");
			int glowing = 0;
			for (JsonElement el : bb.getAsJsonArray("elements")) {
				if (el.getAsJsonObject().get("name").getAsString().startsWith("glow")) {
					glowing++;
				}
			}
			assertTrue(glowing >= 3, s.id() + ": lit lanterns and potions (" + glowing + ")");
		}
	}

	@Test
	void sizeWithinTheBrief() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, s.id() + ": stands on the ground");
			assertTrue(e.width() >= 6.0 && e.width() <= 12.0, s.id() + ": about 6-12 wide " + e.width());
			assertTrue(e.depth() >= 6.0 && e.depth() <= 12.0, s.id() + ": about 6-12 deep " + e.depth());
			assertTrue(e.height() >= 5.0 && e.height() <= 10.0, s.id() + ": at most about 10 high " + e.height());
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
						s.id() + ": inside the extent " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	@Test
	void postsCollideTheEntranceIsOpen() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				if (b.height() >= 2.4 && b.width() < 0.75 && b.depth() < 0.75) {
					posts++;
				}
				// the entrance and the aisle in front of the counter: nothing solid up to 2.2 high
				boolean aisle = b.x0() < s.aisleX1() && b.x1() > s.aisleX0() && b.z1() > s.aisleZ0() && b.y0() < 2.2;
				assertFalse(aisle, s.id() + ": the front is open and walkable up to the counter " + b);
			}
			assertTrue(posts >= s.posts(), s.id() + ": the posts collide (" + posts + ")");
		}
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			assertTrue(free(t, s.npcX() + 0.5, s.npcZ() + 0.5, 0.5, 2.2), s.id() + ": 1 x 1 x 2.2 free behind the counter");
			boolean counterInFront = false;
			for (TentType.Box b : t.colliders()) {
				if (b.z0() >= s.npcZ() + 1.0 - 1e-6 && b.z0() < s.npcZ() + 3.0 && b.x0() < s.npcX() + 0.5 && b.x1() > s.npcX() + 0.5 && b.y1() > 0.9
						&& b.y1() < 1.3) {
					counterInFront = true;
				}
			}
			assertTrue(counterInFront, s.id() + ": the counter stands in front of the merchant");
			assertTrue(walkIn(t, s), s.id() + ": a player walks from the front, round the counter, to the merchant's place");
		}
	}

	/** Flood fill of a 0.6-wide, 1.8-high player from the front edge; true once it reaches the merchant's place. */
	private static boolean walkIn(TentType t, Spec s) {
		TentType.Box e = t.extent();
		double step = 0.1, x0 = e.x0() - 1.0, z0 = e.z0() - 1.0;
		int nx = (int) Math.ceil((e.width() + 2.0) / step), nz = (int) Math.ceil((e.depth() + 2.0) / step);
		boolean[][] seen = new boolean[nx][nz];
		ArrayDeque<int[]> todo = new ArrayDeque<>();
		for (int i = 0; i < nx; i++) {
			if (free(t, x0 + i * step, z0 + (nz - 1) * step, 0.3, 1.8)) {
				seen[i][nz - 1] = true;
				todo.add(new int[] {i, nz - 1});
			}
		}
		while (!todo.isEmpty()) {
			int[] c = todo.poll();
			double x = x0 + c[0] * step, z = z0 + c[1] * step;
			if (Math.abs(x - (s.npcX() + 0.5)) < 0.15 && Math.abs(z - (s.npcZ() + 0.5)) < 0.15) {
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
			if (b.x0() < x + half && b.x1() > x - half && b.z0() < z + half && b.z1() > z - half && b.y0() < h) {
				return false;
			}
		}
		return true;
	}
}
