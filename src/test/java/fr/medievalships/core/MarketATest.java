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
 * The three blue Lion Port market tents of group A (1.26.0; tools/market/generate_tente_lion_pavillon.py,
 * generate_tente_lion_longue.py, generate_tente_imperiale.py on merchantlib + props_a): the Lion Pavilion, the Long Lion
 * Tent and the Imperial Merchant Tent. Each JSON is loaded directly with {@link TentType#load} (the registration in
 * TentTypes is the integrator's): own atlas, light, the model loads and is static with a "detail" bone and lit lanterns,
 * the extent is sane, the posts collide, the entrance is open, the front walkable, and the merchant's 1 x 1 x 2.2 place
 * behind the counter is free and reachable on foot from the front.
 */
public class MarketATest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/**
	 * One tent: its id and names, the (x0, z0) of the merchant's place (the generator's NPC_SPOT), an entrance strip
	 * (x0..x1 for z beyond ez) where nothing solid stands below 2.2, and mod blocks its decor must hold.
	 */
	private record Spec(String id, String fr, String en, double npcX, double npcZ, double ex0, double ex1, double ez, String... mods) {
		TentType type() {
			return TentType.load(id, fr, en);
		}
	}

	private static final List<Spec> TENTS = List.of(
			new Spec("tente_lion_pavillon", "Pavillon au lion", "Lion Pavilion", -1.45, -0.7, -0.25, 0.75, 0.0,
					"mebahelcreaturesdwarven:dwemer_chest", "furnish:spruce_crate", "furnish:book_pile"),
			new Spec("tente_lion_longue", "Longue tente au lion", "Long Lion Tent", -0.4, -0.85, 1.1, 1.85, 0.0,
					"furnish:spruce_crate", "mebahelcreaturesdwarven:dwemer_chest", "farmhouse_decorations:pile_of_books"),
			new Spec("tente_imperiale", "Tente marchande impériale", "Imperial Merchant Tent", -1.85, -1.25, -0.5, 0.5, -1.0,
					"furnish:dark_oak_crate", "landsoficaria:blue_storage_vase"));

	@Test
	void jsonModelAndDecor() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			for (String file : new String[] {"tents/" + s.id() + ".json", "textures/item/" + s.id() + ".png", t.model(), t.texture(),
					"interiors/" + s.id() + "_decor.json"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
			}
			assertEquals(s.id(), t.id());
			assertEquals(TentType.TENTS, t.group());
			assertEquals("models/entity/" + s.id() + ".bbmodel", t.model());
			assertEquals("textures/entity/" + s.id() + ".png", t.texture(), "its own atlas");
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
				assertFalse(b.fallback().isEmpty(), b.block() + " has a stand-in");
			}
			for (String m : s.mods()) {
				assertTrue(ids.contains(m), s.id() + " uses " + m + ": " + ids);
			}
		}
	}

	@Test
	void modelsAreStaticLightAndLit() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			try (var in = MarketATest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 250 * 4 && m.quadCount() <= 1000 * 6, s.id() + ": at most about 1000 cubes: faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), s.id() + ": static, no animation");
				assertTrue(m.hasBone("detail"), s.id() + ": small things under the bone \"detail\" (hidden far away)");
				int[] glow = {0};
				m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
				assertTrue(glow[0] >= 4 * 4, s.id() + ": the lanterns' glass is lit (" + glow[0] + " full-bright faces)");
			}
		}
	}

	@Test
	void extentsAreSane() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, s.id() + " stands on the ground");
			assertTrue(e.width() > 6.0 && e.width() < 12.0, s.id() + ": about 6-12 wide " + e.width());
			assertTrue(e.depth() > 6.0 && e.depth() < 12.0, s.id() + ": about 6-12 deep " + e.depth());
			assertTrue(e.height() > 5.5 && e.height() <= 10.0, s.id() + ": at most about 10 high " + e.height());
			assertTrue(e.x0() < -2.5 && e.x1() > 2.5 && e.z0() < -2.0 && e.z1() > 2.5, s.id() + ": round the anchor block " + e);
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
						s.id() + ": inside the extent " + b);
				assertTrue(b.height() >= 0.2, s.id() + ": no flat box (the rug and the cloth do not collide) " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	@Test
	void postsCollideAndTheEntranceIsOpen() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				if (b.y0() == 0.0 && b.height() >= 2.6 && b.width() < 0.7 && b.depth() < 0.7) {
					posts++;
				}
				boolean inEntrance = b.x0() < s.ex1() && b.x1() > s.ex0() && b.z1() > s.ez() && b.y0() < 2.2;
				assertFalse(inEntrance, s.id() + ": the entrance is open up to 2.2 " + b);
			}
			assertTrue(posts >= 4, s.id() + ": the posts collide (" + posts + ")");
		}
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			double cx = s.npcX() + 0.5, cz = s.npcZ() + 0.5;
			assertTrue(free(t, cx, cz, 0.5, 2.2), s.id() + ": 1 x 1 x 2.2 free behind the counter");
			boolean counterInFront = false;
			for (TentType.Box b : t.colliders()) {
				if (b.z0() > s.npcZ() + 1.0 && b.z0() < s.npcZ() + 2.5 && b.x0() < cx && b.x1() > cx && b.y1() > 0.9 && b.y1() < 1.3) {
					counterInFront = true;
				}
			}
			assertTrue(counterInFront, s.id() + ": the counter stands in front of the merchant");
			assertTrue(walkIn(t, cx, cz), s.id() + ": a player walks from the front to the merchant's place");
			TentType.Box e = t.extent();
			assertTrue(cx > e.x0() + 1.0 && cx < e.x1() - 1.0 && cz > e.z0() + 0.8 && cz < e.z1() - 2.0, s.id() + ": the place is inside the tent");
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
