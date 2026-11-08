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

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The three "scales" market tents of group C (1.26.0, tools/market/generate_tente_balance_*.py on merchantlib and
 * tools/market/props_c.py): the great red-and-cream scales marquee with its orange side awning (048), the
 * wrought-iron scales pavilion with its banner post and sign post (050), the scales-and-purse tent with its lintel,
 * porch and gallows sign (154). Each JSON is loaded directly with {@link TentType#load} (the registration in TentTypes
 * is the integrator's): its own atlas, light, mod blocks with stand-ins; the model is static, light, lit; the extent
 * is sane; the posts collide; the entrance and the front are walkable; the merchant's 1 x 1 x 2.2 place behind the
 * counter is free and reachable on foot.
 */
public class MarketCTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/** One tent of the group: its NPC place (x0, z0), an aisle box (x0, z0, x1, z1) that must stay free up to 2.2, the
	 * expected light, lanterns and mod blocks. */
	private record Spec(String id, String fr, String en, double npcX, double npcZ, double[] aisle, int light, int lanterns, String[] mods) {
		TentType type() {
			return TentType.load(id, fr, en);
		}
	}

	private static final List<Spec> TENTS = List.of(
			new Spec("tente_balance_chapiteau", "Grand chapiteau à la balance", "Great Scales Marquee", -2.65, 0.25,
					new double[] {-0.6, 0.6, 1.1, 4.4}, 13, 5,
					new String[] {"furnish:spruce_crate", "landsoficaria:cypress_barrel", "farmersdelight:rice_bag", "furnish:book_pile"}),
			new Spec("tente_balance_fer", "Pavillon à la balance et ferronnerie", "Wrought-Iron Scales Pavilion", -1.45, -0.62,
					new double[] {-0.3, -0.3, 0.8, 4.4}, 12, 3,
					new String[] {"furnish:spruce_crate", "farmersdelight:rice_bag", "farmhouse_decorations:pile_of_books"}),
			new Spec("tente_balance_bourse", "Tente à la balance et à la bourse", "Scales and Purse Tent", 0.4, -0.55,
					new double[] {0.0, 1.65, 2.0, 4.3}, 13, 5,
					new String[] {"furnish:spruce_crate", "furnish:book_pile", "farmhouse_decorations:pile_of_books"}));

	@Test
	void jsonAtlasLightAndDecor() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			for (String file : new String[] {"tents/" + s.id + ".json", "textures/item/" + s.id + ".png", t.model(), t.texture(),
					"interiors/" + s.id + "_decor.json"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
			}
			assertTrue(Files.isRegularFile(Path.of("blockbench/" + s.id + ".bbmodel")), "the Blockbench copy of " + s.id);
			assertEquals(s.id, t.id());
			assertEquals(TentType.TENTS, t.group());
			assertEquals("models/entity/" + s.id + ".bbmodel", t.model());
			assertEquals("textures/entity/" + s.id + ".png", t.texture(), "its own atlas");
			JsonObject root;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("tents/" + s.id + ".json"), StandardCharsets.UTF_8)) {
				root = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertEquals(s.light, root.get("light").getAsInt(), s.id);
			assertEquals(s.light, t.light(), s.id + ": the anchor block lights the tent");
			assertTrue(t.particles().isEmpty(), s.id + ": no particles, nothing ticks");
			assertTrue(t.seats().isEmpty(), s.id + ": no seats");
			InteriorDecor decor = InteriorDecor.load(t.decor());
			Set<String> ids = new HashSet<>();
			for (InteriorDecor.Block b : decor.blocks()) {
				ids.add(b.block());
				assertFalse(b.fallback().isEmpty(), b.block() + " has a stand-in");
				assertTrue(b.block().matches("[a-z_]+:[a-z0-9_]+"), b.block());
			}
			for (String m : s.mods) {
				assertTrue(ids.contains(m), s.id + " uses " + m + " " + ids);
			}
		}
	}

	@Test
	void modelsAreStaticLightAndLit() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			try (var in = MarketCTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 300 * 3 && m.quadCount() <= 1000 * 6, s.id + ": at most about 1000 cubes: faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), s.id + ": static, no animation");
				assertTrue(m.hasBone("detail"), s.id + ": small things under the bone \"detail\" (hidden far away)");
				int[] glow = {0};
				m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
				assertTrue(glow[0] >= s.lanterns * 6, s.id + ": the lanterns' glass is lit (" + glow[0] + " full-bright faces)");
			}
			JsonObject bb;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve(t.model()), StandardCharsets.UTF_8)) {
				bb = JsonParser.parseReader(r).getAsJsonObject();
			}
			int cubes = bb.getAsJsonArray("elements").size();
			assertTrue(cubes >= 400 && cubes <= 1000, s.id + ": cubes " + cubes);
		}
	}

	@Test
	void extentsAreSaneAndDifferent() {
		Set<String> sizes = new HashSet<>();
		for (Spec s : TENTS) {
			TentType t = s.type();
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, s.id + " stands on the ground");
			assertTrue(e.width() >= 6.0 && e.width() <= 12.0, s.id + " width " + e.width());
			assertTrue(e.depth() >= 6.0 && e.depth() <= 12.0, s.id + " depth " + e.depth());
			assertTrue(e.height() >= 5.5 && e.height() <= 10.0, s.id + " height " + e.height());
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
						s.id + " collider inside the extent " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
			sizes.add(String.format("%.1f/%.1f/%.1f", e.width(), e.depth(), e.height()));
		}
		assertEquals(TENTS.size(), sizes.size(), "three different silhouettes " + sizes);
	}

	@Test
	void postsCollideAndTheFrontIsOpen() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				if (b.height() >= 2.7 && b.width() < 0.8 && b.depth() < 0.8) {
					posts++;
				}
				double[] a = s.aisle;
				boolean inAisle = b.x0() < a[2] && b.x1() > a[0] && b.z0() < a[3] && b.z1() > a[1] && b.y0() < 2.2;
				assertFalse(inAisle, s.id + ": the entrance and the front are walkable, nothing solid in " + java.util.Arrays.toString(a) + ": " + b);
			}
			assertTrue(posts >= 4, s.id + ": the posts collide (" + posts + ")");
		}
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			assertTrue(free(t, s.npcX + 0.5, s.npcZ + 0.5, 0.5, 2.2), s.id + ": 1 x 1 x 2.2 free for the merchant");
			boolean counterInFront = false;
			for (TentType.Box b : t.colliders()) {
				if (b.z0() > s.npcZ + 0.95 && b.z0() < s.npcZ + 3.0 && b.x0() < s.npcX + 0.5 && b.x1() > s.npcX + 0.5 && b.y1() > 0.9 && b.y1() < 1.3) {
					counterInFront = true;
				}
			}
			assertTrue(counterInFront, s.id + ": the counter stands in front of the merchant");
			assertTrue(walkIn(t, s.npcX + 0.5, s.npcZ + 0.5), s.id + ": a player walks from the front to the merchant's place");
		}
	}

	/** Flood fill of a 0.6-wide, 1.8-high player from the front edge; true once it reaches (tx, tz). */
	private static boolean walkIn(TentType t, double tx, double tz) {
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
			if (Math.abs(x - tx) < 0.15 && Math.abs(z - tz) < 0.15) {
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
