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
 * The three market tents of group F (1.26.0; tools/market/generate_tente_frontiere.py, generate_tente_sylvestre.py,
 * generate_tente_arsenal.py on merchantlib + props_f), the bottom row and top right of the board "065": the Frontier
 * Merchant Tent (red canvas under furs and hides, a horned skull on the ridge), the Sylvan Merchant Tent (green elven
 * pavilion on living branches, wisteria, glowing crystals) and the Arsenal Merchant Tent (steampunk marquee, gears,
 * copper pipes, a boiler). Each JSON is loaded directly with {@link TentType#load} (the registration in TentTypes is
 * the integrator's): own atlas, light, the model loads and is static with a "detail" bone and lit lanterns, the mod
 * blocks have stand-ins in the model, the extent is sane, the posts collide, the entrance is open, the front walkable,
 * and the merchant's 1 x 1 x 2.2 place behind the counter is free and reachable on foot from the front.
 */
public class MarketFTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/**
	 * One tent: its id and names, the (x0, z0) of the merchant's place (the generator's NPC_SPOT), an entrance strip
	 * (x0..x1 for z beyond ez) where nothing solid stands below 2.2, the minimum number of posts, and mod blocks its decor
	 * must hold.
	 */
	private record Spec(String id, String fr, String en, double npcX, double npcZ, double ex0, double ex1, double ez, int posts, String... mods) {
		TentType type() {
			return TentType.load(id, fr, en);
		}
	}

	private static final List<Spec> TENTS = List.of(
			new Spec("tente_frontiere", "Tente marchande de frontière", "Frontier Merchant Tent", 0.6, -2.73, -1.0, 1.0, 0.0, 6,
					"furnish:spruce_crate", "landsoficaria:loaded_cypress_barrel", "farmhouse_decorations:pile_of_books", "farmersdelight:rice_bag"),
			new Spec("tente_sylvestre", "Tente marchande sylvestre", "Sylvan Merchant Tent", 0.9, -2.96, -1.0, 1.0, 0.0, 4,
					"farmhouse_decorations:pile_of_books", "furnish:spruce_crate", "farmersdelight:wooden_basket", "landsoficaria:green_storage_vase",
					"minecraft:amethyst_cluster"),
			new Spec("tente_arsenal", "Tente marchande de l'arsenal", "Arsenal Merchant Tent", -0.35, -2.74, -1.0, 1.0, 0.0, 4,
					"mebahelcreaturesdwarven:dwemer_chest", "mebahelcreaturesdwarven:dwemer_metal_pipe_gear", "farmhouse_decorations:workbench",
					"farmhouse_decorations:tool_board", "farmhouse_decorations:kerosene_lantern", "furnish:spruce_crate"));

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
	void onlyTheArsenalsBoilerSmokes() {
		for (Spec s : TENTS) {
			TentType t = s.type();
			if (!s.id().equals("tente_arsenal")) {
				assertTrue(t.particles().isEmpty(), s.id() + ": no particles");
				continue;
			}
			assertEquals(1, t.particles().size(), "one smoke source, the boiler's chimney");
			TentType.Particle p = t.particles().get(0);
			assertTrue(p.known() && p.type().equals("smoke"), "vanilla smoke " + p);
			assertTrue(p.chance() > 0.0 && p.chance() <= 0.2 && p.count() <= 2, "a rare puff, not a stream " + p);
			assertTrue(p.y() > 5.5 && p.x() > 1.5, "above the roof, at the chimney on the right slope " + p);
		}
	}

	@Test
	void modelsAreStaticLightAndLit() throws Exception {
		for (Spec s : TENTS) {
			TentType t = s.type();
			try (var in = MarketFTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 250 * 4 && m.quadCount() <= 1000 * 6, s.id() + ": at most about 1000 cubes: faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), s.id() + ": static, no animation");
				assertTrue(m.hasBone("detail"), s.id() + ": small things under the bone \"detail\" (hidden far away)");
				for (InteriorDecor.Block b : InteriorDecor.load(t.decor()).blocks()) {
					assertTrue(m.hasBone(b.fallback()), s.id() + ": the stand-in of " + b.block() + " is in the model");
				}
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
			assertTrue(posts >= s.posts(), s.id() + ": the posts collide (" + posts + ")");
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
