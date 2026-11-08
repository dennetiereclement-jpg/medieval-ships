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
 * The market tents of group D (1.26.0, tools/market/generate_tente_balance_auvent.py and
 * generate_tente_balance_pignon.py on props_d / merchantlib): two red-and-cream tents of the scales merchants.
 * <ul>
 * <li>{@code tente_balance_auvent}: a hipped main tent on a short ridge between two ridge posts, its left wall closed with
 * a scales banner, and a long red patterned awning on posts over the front right; the counter runs front to back under
 * the awning, its front facing the carpet (-x); the merchant stands behind it (+x).</li>
 * <li>{@code tente_balance_pignon}: a gabled pavilion with four tall corner posts rising above the roof, a raised middle
 * carrying the big scales banner, and two side awnings sweeping out of the gable ends; the counter runs along the front;
 * the merchant stands behind it, in front of the shelves.</li>
 * </ul>
 * Each JSON is loaded directly with {@link TentType#load} (the registration in TentTypes is the integrator's).
 */
public class MarketDTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/**
	 * What the test knows of one tent: names, light, lanterns, size bounds, the free place of the merchant (x0, z0 of its
	 * 1 x 1 column), the side the counter stands on from there, an aisle in front that must stay free up to 2.2 (x0, x1,
	 * z0, z1), the posts (count, minimum height and width of the main ones, then count and minimum height of the others),
	 * the mod blocks.
	 */
	record Spec(String id, String fr, String en, int light, int lanterns, double npcX, double npcZ, String counterSide, double[] aisle,
			int mainPosts, double mainPostH, double mainPostW, int smallPosts, double smallPostH, Set<String> mods) {
		TentType type() {
			return TentType.load(id, fr, en);
		}
	}

	static final Spec AUVENT = new Spec("tente_balance_auvent", "Tente à la balance et à l'auvent", "Scales Tent with Awning", 13, 4, 0.6, 1.0,
			"-x", new double[] {-1.7, -0.6, 0.2, 4.2}, 4, 3.2, 0.45, 3, 2.7,
			Set.of("farmersdelight:tomato_crate", "farmersdelight:cabbage_crate", "farmersdelight:rice_bag", "furnish:spruce_crate",
					"furnish:book_pile"));
	static final Spec PIGNON = new Spec("tente_balance_pignon", "Tente à pignon à la balance", "Gabled Scales Tent", 12, 2, -0.45, -1.85,
			"+z", new double[] {-1.0, 1.6, 0.6, 3.35}, 4, 3.6, 0.6, 4, 3.8,
			Set.of("farmersdelight:tomato_crate", "farmersdelight:cabbage_crate", "farmersdelight:rice_bag", "furnish:spruce_crate",
					"mebahelcreaturesdwarven:dwemer_chest", "farmhouse_decorations:pile_of_books"));
	static final List<Spec> ALL = List.of(AUVENT, PIGNON);

	@Test
	void jsonModelAndDecor() throws Exception {
		for (Spec s : ALL) {
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
			assertEquals(s.light, t.light(), s.id + ": the anchor block lights the tent (lanterns)");
			assertTrue(t.particles().isEmpty(), s.id + ": no particles, nothing ticks");
			assertTrue(t.seats().isEmpty(), s.id + ": no seats");
			InteriorDecor decor = InteriorDecor.load(t.decor());
			Set<String> ids = new HashSet<>();
			for (InteriorDecor.Block b : decor.blocks()) {
				ids.add(b.block());
				assertTrue(b.block().matches("[a-z_]+:[a-z0-9_]+"), b.block());
				assertFalse(b.fallback().isEmpty(), b.block() + " has a stand-in");
			}
			assertEquals(s.mods, ids, s.id + ": the decoration mods' blocks");
		}
	}

	@Test
	void modelIsStaticLightAndLit() throws Exception {
		for (Spec s : ALL) {
			TentType t = s.type();
			try (var in = MarketDTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 300 * 6 / 2 && m.quadCount() <= 1000 * 6, s.id + ": at most about 1000 cubes, faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), s.id + ": static, no animation");
				assertTrue(m.hasBone("detail"), s.id + ": small things under the bone 'detail' (hidden far away)");
				int[] glow = {0};
				m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
				assertTrue(glow[0] >= s.lanterns * 4, s.id + ": the lanterns' glass is lit (" + glow[0] + " full-bright faces)");
			}
		}
	}

	@Test
	void sizeWithinTheBrief() {
		for (Spec s : ALL) {
			TentType t = s.type();
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, s.id + " stands on the ground");
			assertTrue(e.width() >= 6.0 && e.width() <= 12.0, s.id + ": about 6-12 wide " + e.width());
			assertTrue(e.depth() >= 6.0 && e.depth() <= 12.0, s.id + ": about 6-12 deep " + e.depth());
			assertTrue(e.height() > 5.0 && e.height() <= 10.0, s.id + ": at most about 10 high " + e.height());
			assertTrue(Math.abs(e.x0() + e.x1()) < 0.3 && Math.abs(e.z0() + e.z1()) < 0.3, s.id + ": centred on the anchor block " + e);
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1(), s.id + ": inside the extent " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	@Test
	void postsCollideAndTheFrontIsOpen() {
		for (Spec s : ALL) {
			TentType t = s.type();
			int main = 0, small = 0;
			for (TentType.Box b : t.colliders()) {
				boolean thin = b.width() < 0.75 && b.depth() < 0.75;
				if (thin && b.height() >= s.mainPostH && b.width() >= s.mainPostW) {
					main++;
				} else if (thin && b.height() >= s.smallPostH) {
					small++;
				}
				double[] a = s.aisle;
				boolean inAisle = b.x0() < a[1] && b.x1() > a[0] && b.z0() < a[3] && b.z1() > a[2] && b.y0() < 2.2;
				assertFalse(inAisle, s.id + ": the entrance and the aisle in front are open up to 2.2 " + b);
			}
			assertTrue(main >= s.mainPosts, s.id + ": the main tent's posts collide (" + main + ")");
			assertTrue(small >= s.smallPosts, s.id + ": the awning posts collide (" + small + ")");
		}
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		for (Spec s : ALL) {
			TentType t = s.type();
			double cx = s.npcX + 0.5, cz = s.npcZ + 0.5;
			assertTrue(free(t, cx, cz, 0.5, 2.2), s.id + ": 1 x 1 x 2.2 free for the merchant");
			boolean counter = false;
			for (TentType.Box b : t.colliders()) {
				boolean top = b.y1() > 0.9 && b.y1() < 1.3;
				if ("-x".equals(s.counterSide)) {
					counter |= top && b.x1() < s.npcX + 0.05 && b.x1() > s.npcX - 1.0 && b.z0() < cz && b.z1() > cz;
				} else {
					counter |= top && b.z0() > s.npcZ + 0.95 && b.z0() < s.npcZ + 2.5 && b.x0() < cx && b.x1() > cx;
				}
			}
			assertTrue(counter, s.id + ": the counter stands in front of the merchant");
			assertTrue(walkIn(t, cx, cz), s.id + ": a player walks from the front to the merchant's place");
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
