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
 * The market tents of group E (1.26.0; tools/market/generate_tente_draperie.py, generate_tente_fleur_de_lys.py,
 * generate_tente_cordages.py on merchantlib + props_e.py): the red drapery tent, the fleur-de-lis tent and the red rope
 * tent. Each JSON is loaded directly with {@link TentType#load} (the registration in TentTypes is the integrator's):
 * its own atlas and light, the model and the decor load, the extent is sane (about 6-12 wide and deep, at most about
 * 10 high), at most about 1000 cubes, a static model with a "detail" bone and lit lanterns, the posts collide, the front
 * is open and walkable, and the merchant's free place of 1 x 1 x 2.2 behind the counter is reached on foot from the
 * front.
 */
public class MarketETest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/** One tent: its type, the merchant's place (x0, z0), the front aisle that must stay free (x0, z0, x1, z1), the
	 * least number of lanterns, the mod blocks it must use. */
	private record Tent(TentType type, double npcX, double npcZ, double[] aisle, int lanterns, String[] mods) {
	}

	private static final List<Tent> TENTS = List.of(
			new Tent(TentType.load("tente_draperie", "Tente aux draperies rouges", "Red Drapery Tent"), 0.3, -0.8,
					new double[] {-0.3, 2.45, 2.6, 4.5}, 5, new String[] {"furnish:spruce_crate", "landsoficaria:cypress_barrel"}),
			new Tent(TentType.load("tente_fleur_de_lys", "Tente à la fleur de lys", "Fleur-de-lis Tent"), -0.6, -0.75,
					new double[] {-0.45, 2.05, 1.95, 4.15}, 4, new String[] {"farmhouse_decorations:kerosene_lantern", "farmhouse_decorations:wine_bottle"}),
			new Tent(TentType.load("tente_cordages", "Tente rouge aux cordages", "Red Rope Tent"), 0.9, -1.05,
					new double[] {-0.3, 2.15, 2.55, 3.95}, 4, new String[] {"furnish:spruce_crate", "farmersdelight:wooden_basket"}));

	@Test
	void jsonModelAndDecor() throws Exception {
		for (Tent t : TENTS) {
			TentType T = t.type();
			String id = T.id();
			for (String file : new String[] {"tents/" + id + ".json", "textures/item/" + id + ".png", T.model(), T.texture(),
					"interiors/" + id + "_decor.json"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
			}
			assertEquals(TentType.TENTS, T.group(), id);
			assertEquals("models/entity/" + id + ".bbmodel", T.model());
			assertEquals("textures/entity/" + id + ".png", T.texture(), id + ": its own atlas");
			JsonObject root;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("tents/" + id + ".json"), StandardCharsets.UTF_8)) {
				root = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertEquals(13, root.get("light").getAsInt(), id);
			assertEquals(13, T.light(), id + ": the anchor block lights the tent (lanterns)");
			assertTrue(T.particles().isEmpty(), id + ": no particles, nothing ticks");
			assertTrue(T.seats().isEmpty(), id + ": no seats");
			InteriorDecor decor = InteriorDecor.load(T.decor());
			Set<String> ids = new HashSet<>();
			for (InteriorDecor.Block b : decor.blocks()) {
				ids.add(b.block());
				assertFalse(b.fallback().isEmpty(), id + ": " + b.block() + " has a stand-in");
			}
			for (String m : t.mods()) {
				assertTrue(ids.contains(m), id + " uses " + m + ": " + ids);
			}
		}
	}

	@Test
	void modelsAreStaticLightAndLit() throws Exception {
		Set<Integer> sizes = new HashSet<>();
		for (Tent t : TENTS) {
			String id = t.type().id();
			try (var in = MarketETest.class.getResourceAsStream("/assets/medievalships/" + t.type().model())) {
				assertNotNull(in, t.type().model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				int cubes = m.quadCount() / 6;
				assertTrue(m.quadCount() > 400 * 6 / 2 && m.quadCount() <= 1000 * 6, id + ": at most about 1000 cubes: faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), id + ": static, no animation");
				assertTrue(m.hasBone("detail"), id + ": small things under the bone detail (hidden far away)");
				int[] glow = {0};
				m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
				assertTrue(glow[0] >= t.lanterns() * 4, id + ": the lanterns' glass is lit (" + glow[0] + " full-bright faces)");
				sizes.add(cubes);
			}
		}
		assertEquals(TENTS.size(), sizes.size(), "three different models, not one tent recoloured");
	}

	@Test
	void sizeWithinTheBrief() {
		for (Tent t : TENTS) {
			TentType T = t.type();
			TentType.Box e = T.extent();
			String id = T.id();
			assertEquals(0.0, e.y0(), 1e-9, id + " stands on the ground");
			assertTrue(e.width() > 6.0 && e.width() < 12.0, id + ": about 6-12 wide: " + e.width());
			assertTrue(e.depth() > 6.0 && e.depth() < 12.0, id + ": about 6-12 deep: " + e.depth());
			assertTrue(e.height() > 5.0 && e.height() <= 10.0, id + ": at most about 10 high: " + e.height());
			for (TentType.Box b : T.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
						id + ": inside the extent " + b);
			}
			assertEquals(T.colliders().size(), T.colliders(TentType.WEST).size());
		}
	}

	@Test
	void postsCollideTheFrontIsOpen() {
		for (Tent t : TENTS) {
			TentType T = t.type();
			String id = T.id();
			int posts = 0;
			double[] a = t.aisle();
			for (TentType.Box b : T.colliders()) {
				if (b.height() >= 3.0 && b.width() < 0.75 && b.depth() < 0.75) {
					posts++;
				}
				boolean inAisle = b.x0() < a[2] && b.x1() > a[0] && b.z0() < a[3] && b.z1() > a[1] && b.y0() < 2.2;
				assertFalse(inAisle, id + ": the entrance and the rug in front stay free up to 2.2 high " + b);
			}
			assertTrue(posts >= 4, id + ": the four main posts collide (" + posts + ")");
		}
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		for (Tent t : TENTS) {
			String id = t.type().id();
			double cx = t.npcX() + 0.5, cz = t.npcZ() + 0.5;
			assertTrue(free(t.type(), cx, cz, 0.5, 2.2), id + ": 1 x 1 x 2.2 free behind the counter");
			boolean counterInFront = false;
			for (TentType.Box b : t.type().colliders()) {
				if (b.z0() > t.npcZ() + 1.0 && b.z0() < t.npcZ() + 3.0 && b.x0() < cx && b.x1() > cx && b.y1() > 0.85 && b.y1() < 1.3) {
					counterInFront = true;
				}
			}
			assertTrue(counterInFront, id + ": the counter stands in front of the merchant");
			assertTrue(walkIn(t.type(), cx, cz), id + ": a player walks from the front, round the counter, to the merchant's place");
		}
	}

	/** Flood fill of a 0.6-wide, 1.8-high player from the front edge; true once it reaches (tx, tz). */
	private static boolean walkIn(TentType T, double tx, double tz) {
		TentType.Box e = T.extent();
		double step = 0.1, x0 = e.x0() - 1.0, z0 = e.z0() - 1.0;
		int nx = (int) Math.ceil((e.width() + 2.0) / step), nz = (int) Math.ceil((e.depth() + 2.0) / step);
		boolean[][] seen = new boolean[nx][nz];
		ArrayDeque<int[]> todo = new ArrayDeque<>();
		for (int i = 0; i < nx; i++) {
			if (free(T, x0 + i * step, z0 + (nz - 1) * step, 0.3, 1.8)) {
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
				if (i >= 0 && k >= 0 && i < nx && k < nz && !seen[i][k] && free(T, x0 + i * step, z0 + k * step, 0.3, 1.8)) {
					seen[i][k] = true;
					todo.add(new int[] {i, k});
				}
			}
		}
		return false;
	}

	private static boolean free(TentType T, double x, double z, double half, double h) {
		for (TentType.Box b : T.colliders()) {
			if (b.x0() < x + half && b.x1() > x - half && b.z0() < z + half && b.z1() > z - half && b.y0() < h) {
				return false;
			}
		}
		return true;
	}
}
