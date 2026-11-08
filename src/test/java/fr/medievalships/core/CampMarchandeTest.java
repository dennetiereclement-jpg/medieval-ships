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
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The merchant tent of the military camp (1.25.0, tente_marchande, TentTypes.CAMP_TENTS; tools/tents/
 * generate_tente_marchande.py on merchantlib): a big red-and-cream striped merchant pavilion about 9 x 7.5 blocks (its two
 * side extensions and the carpet included), the flag top at about 7, open at the front, the counter, the shelves, a free
 * place of 1 x 1 x 2.2 behind the counter for a merchant NPC reached by the gap beside the counter, lit lanterns, static.
 * The JSON is loaded directly with {@link TentType#load} (the registration in TentTypes is the core branch's).
 */
public class CampMarchandeTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final TentType T = TentType.load("tente_marchande", "tente marchande", "Merchant Tent");
	/** (x0, z0) of the merchant's 1 x 1 x 2.2 place behind the counter (the generator's NPC_SPOT). */
	private static final double NPC_X = -0.2, NPC_Z = -1.25;

	@Test
	void jsonModelAndDecor() throws Exception {
		for (String file : new String[] {"tents/tente_marchande.json", "textures/item/tente_marchande.png", T.model(), T.texture(),
				"interiors/tente_marchande_decor.json"}) {
			assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
		}
		assertEquals("tente_marchande", T.id());
		assertEquals(TentType.TENTS, T.group());
		assertEquals("models/entity/tente_marchande.bbmodel", T.model());
		assertEquals("textures/entity/tente_marchande.png", T.texture(), "its own atlas");
		JsonObject root;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("tents/tente_marchande.json"), StandardCharsets.UTF_8)) {
			root = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals(13, root.get("light").getAsInt());
		assertEquals(13, T.light(), "the anchor block lights the tent (lanterns)");
		assertTrue(T.particles().isEmpty(), "no particles, nothing ticks");
		assertTrue(T.seats().isEmpty(), "no seats");
		InteriorDecor decor = InteriorDecor.load(T.decor());
		Set<String> ids = new HashSet<>();
		for (InteriorDecor.Block b : decor.blocks()) {
			ids.add(b.block());
			assertFalse(b.fallback().isEmpty(), b.block() + " has a stand-in");
		}
		assertTrue(ids.contains("furnish:spruce_crate") && ids.contains("landsoficaria:cypress_barrel"), "mod blocks " + ids);
	}

	@Test
	void modelIsStaticLightAndLit() throws Exception {
		try (var in = CampMarchandeTest.class.getResourceAsStream("/assets/medievalships/" + T.model())) {
			assertNotNull(in, T.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 400 * 6 / 2 && m.quadCount() <= 1000 * 6, "at most about 1000 cubes: faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "static: no animation");
			int[] glow = {0};
			m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
			assertTrue(glow[0] >= 4 * 4, "the four lanterns' glass is lit (" + glow[0] + " full-bright faces)");
		}
	}

	@Test
	void sizeWithinTheBrief() {
		TentType.Box e = T.extent();
		assertEquals(0.0, e.y0(), 1e-9, "stands on the ground");
		assertTrue(e.width() > 8.0 && e.width() < 10.5, "about 8-9 wide (the two side extensions, the sign beam): " + e.width());
		assertTrue(e.depth() > 6.5 && e.depth() < 8.5, "about 7-8 deep (the carpet in front included): " + e.depth());
		assertTrue(e.height() > 6.5 && e.height() < 7.8, "the flag top at about 7: " + e.height());
		for (TentType.Box b : T.colliders()) {
			assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05 && b.y0() >= 0.0,
					"inside the extent " + b);
		}
		assertEquals(T.colliders().size(), T.colliders(TentType.WEST).size());
	}

	@Test
	void postsAndWallsCollideTheFrontIsOpen() {
		int posts = 0, smallPosts = 0;
		boolean backWall = false;
		for (TentType.Box b : T.colliders()) {
			if (b.height() >= 3.3 && b.width() < 0.7 && b.depth() < 0.7) {
				posts++;
			} else if (b.height() >= 2.2 && b.width() < 0.5 && b.depth() < 0.5) {
				smallPosts++;
			}
			if (b.width() > 5.0 && b.depth() < 0.2 && b.z1() < -2.0 && b.height() > 2.5) {
				backWall = true;
			}
			// the entrance and the aisle in front of the counter: nothing solid up to 2.2 high from the counter to the front
			boolean aisle = b.x0() < 1.9 && b.x1() > -1.1 && b.z1() > 2.15 && b.y0() < 2.2;
			assertFalse(aisle, "the front is open and walkable up to the counter " + b);
			// no invisible wall above the counter and the goods: only posts and walls rise above 2.0 inside
			boolean wall = b.width() < 0.2 || b.depth() < 0.2;
			boolean post = b.width() < 0.7 && b.depth() < 0.7 && b.height() >= 2.2;
			boolean shelves = b.depth() < 0.65 && b.z1() < -1.6;
			assertTrue(wall || post || shelves || b.y1() <= 1.6, "only posts, walls and the back shelves rise high " + b);
		}
		assertEquals(4, posts, "the four big posts of the main tent");
		assertEquals(4, smallPosts, "the four posts of the side extensions");
		assertTrue(backWall, "the striped back wall collides");
	}

	@Test
	void theMerchantsPlaceIsFreeAndReachable() {
		assertTrue(free(NPC_X + 0.5, NPC_Z + 0.5, 0.5, 2.2), "1 x 1 x 2.2 free behind the counter");
		// the place is behind the counter (between it and the shelves)
		boolean counterInFront = false;
		for (TentType.Box b : T.colliders()) {
			if (b.z0() > NPC_Z + 1.0 && b.z0() < NPC_Z + 3.0 && b.x0() < NPC_X + 0.5 && b.x1() > NPC_X + 0.5 && b.y1() > 0.9 && b.y1() < 1.3) {
				counterInFront = true;
			}
		}
		assertTrue(counterInFront, "the counter stands in front of the merchant");
		assertTrue(walkIn(), "a player walks from the front, round the counter, to the merchant's place");
	}

	/** Flood fill of a 0.6-wide, 1.8-high player from the front edge; true once it reaches the merchant's place. */
	private static boolean walkIn() {
		TentType.Box e = T.extent();
		double step = 0.1, x0 = e.x0() - 1.0, z0 = e.z0() - 1.0;
		int nx = (int) Math.ceil((e.width() + 2.0) / step), nz = (int) Math.ceil((e.depth() + 2.0) / step);
		boolean[][] seen = new boolean[nx][nz];
		ArrayDeque<int[]> todo = new ArrayDeque<>();
		for (int i = 0; i < nx; i++) {
			if (free(x0 + i * step, z0 + (nz - 1) * step, 0.3, 1.8)) {
				seen[i][nz - 1] = true;
				todo.add(new int[] {i, nz - 1});
			}
		}
		while (!todo.isEmpty()) {
			int[] c = todo.poll();
			double x = x0 + c[0] * step, z = z0 + c[1] * step;
			if (Math.abs(x - (NPC_X + 0.5)) < 0.15 && Math.abs(z - (NPC_Z + 0.5)) < 0.15) {
				return true;
			}
			for (int[] d : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
				int i = c[0] + d[0], k = c[1] + d[1];
				if (i >= 0 && k >= 0 && i < nx && k < nz && !seen[i][k] && free(x0 + i * step, z0 + k * step, 0.3, 1.8)) {
					seen[i][k] = true;
					todo.add(new int[] {i, k});
				}
			}
		}
		return false;
	}

	private static boolean free(double x, double z, double half, double h) {
		for (TentType.Box b : T.colliders()) {
			if (b.x0() < x + half && b.x1() > x - half && b.z0() < z + half && b.z1() > z - half && b.y0() < h) {
				return false;
			}
		}
		return true;
	}
}
