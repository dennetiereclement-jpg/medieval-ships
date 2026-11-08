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
 * The training areas (1.18.0): three fenced yards of about 7 x 7 blocks (group "training", tab "Entraînement", each with
 * its own atlas, tools/training/traininglib.py). Each loads, stands on the ground, is 6 to 11 blocks wide and deep; its
 * fence collides (about 1.5 high, like vanilla fences) along the four sides except an entrance at least 1.5 blocks wide,
 * through which a player walks into the yard; the floor plate does not collide (the yard is walkable); no collision box
 * lies outside the drawn model (no invisible walls). The checks hold for the stub copies of the dummy area as well.
 */
public class TrainingTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("training_area_dummy", "training_area_tatami", "training_area_shield");

	@Test
	void threeAreasLoadInTheirOwnTab() {
		assertEquals(3, TentTypes.TRAINING.size());
		assertEquals(TentTypes.TRAINING, TentTypes.PROPS.subList(43, 46), "after the tents, the carts and the workshops, before the cannon");
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.TRAINING.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.TRAINING, t.group());
			assertTrue(t.isTraining(), t.id());
			assertFalse(t.isCart() || t.isWorkshop() || t.isCannon(), t.id());
			assertFalse(t.masculine(), t.id() + ": une aire");
			assertFalse(TentTypes.ALL.contains(t), t.id() + " not in the tents' tab");
			assertTrue(TentTypes.PROPS.contains(t), t.id() + " in the props (commands, models)");
			assertTrue(t.frenchName().startsWith("aire d'entraînement "), t.frenchName());
			assertTrue(t.englishName().endsWith("Training Area"), t.englishName());
			assertEquals("models/entity/" + t.id() + ".bbmodel", t.model());
			assertEquals("textures/entity/" + t.id() + ".png", t.texture(), t.id() + " its own atlas");
			assertEquals(null, t.muzzle(), t.id());
		}
		for (TentType t : TentTypes.PROPS) {
			assertEquals(TentTypes.TRAINING.contains(t), t.isTraining(), t.id());
		}
		assertEquals("aire d'entraînement aux frappes", TentTypes.TRAINING_DUMMY.frenchName());
		assertEquals("Strike Training Area", TentTypes.TRAINING_DUMMY.englishName());
		assertEquals("aire d'entraînement aux tatamis", TentTypes.TRAINING_TATAMI.frenchName());
		assertEquals("Tatami Training Area", TentTypes.TRAINING_TATAMI.englishName());
		assertEquals("aire d'entraînement épée et bouclier", TentTypes.TRAINING_SHIELD.frenchName());
		assertEquals("Sword & Shield Training Area", TentTypes.TRAINING_SHIELD.englishName());
		assertSame(TentTypes.TRAINING_DUMMY, TentTypes.byId("training_area_dummy"));
		assertSame(TentTypes.TRAINING_DUMMY, TentTypes.byId("medievalships:training_area_dummy"));
		assertSame(TentTypes.TRAINING_DUMMY, TentTypes.byId(" Dummy "));
		assertSame(TentTypes.TRAINING_TATAMI, TentTypes.byId("tatami"));
		assertSame(TentTypes.TRAINING_SHIELD, TentTypes.byId("shield"));
		assertSame(TentTypes.MARKET, TentTypes.byId("market"), "the other props keep their short names");
	}

	@Test
	void smallSquareYardsOnTheGround() {
		for (TentType t : TentTypes.TRAINING) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, t.id() + " stands on the ground");
			assertTrue(e.width() >= 6.0 && e.width() <= 11.0, t.id() + " width " + e.width());
			assertTrue(e.depth() >= 6.0 && e.depth() <= 11.0, t.id() + " depth " + e.depth());
			assertTrue(e.height() > 1.5 && e.height() < 5.0, t.id() + " height " + e.height());
			assertTrue(t.colliders().size() >= 12, t.id() + " collision boxes " + t.colliders().size());
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, t.id() + " no invisible wall: inside the extent " + b);
				assertTrue(b.y1() > 0.3, t.id() + " no flat floor collision (the floor plate lies on the ground) " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	@Test
	void fencesCollideOnFourSidesWithAWideEntrance() {
		for (TentType t : TentTypes.TRAINING) {
			TentType.Box e = t.extent();
			double[] cover = new double[4];
			for (int side = 0; side < 4; side++) {
				cover[side] = fenceCover(t, side);
				assertTrue(cover[side] >= 0.55, t.id() + " side " + side + " fenced (" + cover[side] + " of its length blocks a player)");
			}
			assertTrue(cover[0] >= 0.8 || cover[1] >= 0.8 || cover[2] >= 0.8 || cover[3] >= 0.8, t.id() + " mostly closed sides");
			// a player walks in from outside (0.6 wide), and so does a 1.4-wide body: the entrance is at least 1.5 wide
			assertTrue(walkIn(t, 0.3), t.id() + " a player walks into the yard through the entrance");
			assertTrue(walkIn(t, 0.7), t.id() + " the entrance is at least 1.5 blocks wide");
			// the inside is walkable: most of the yard (1.2 blocks inside the extent) is free for a standing player
			int free = 0, all = 0;
			for (double x = e.x0() + 1.2; x <= e.x1() - 1.2; x += 0.25) {
				for (double z = e.z0() + 1.2; z <= e.z1() - 1.2; z += 0.25) {
					all++;
					if (free(t, x, z, 0.3, 1.8, 0.6)) {
						free++;
					}
				}
			}
			assertTrue(free > all * 0.35, t.id() + " the yard is walkable (" + free + " / " + all + " free spots)");
		}
	}

	/**
	 * The share of one side's length (0 front +z, 1 right +x, 2 back -z, 3 left -x) that a fence blocks, taken on the
	 * line (within 1.2 blocks of that edge of the extent) where it blocks the most: a box at least 1.4 high from the
	 * ground.
	 */
	static double fenceCover(TentType t, int side) {
		TentType.Box e = t.extent();
		double best = 0;
		for (double d = 0.0; d <= 1.2; d += 0.05) {
			int hit = 0, n = 0;
			boolean alongX = side == 0 || side == 2;
			double a0 = (alongX ? e.x0() : e.z0()) + 0.6, a1 = (alongX ? e.x1() : e.z1()) - 0.6;
			for (double a = a0; a <= a1; a += 0.1) {
				double x = alongX ? a : side == 1 ? e.x1() - d : e.x0() + d;
				double z = alongX ? (side == 0 ? e.z1() - d : e.z0() + d) : a;
				n++;
				for (TentType.Box b : t.colliders()) {
					if (b.y0() < 0.3 && b.y1() >= 1.4 && b.x0() <= x && b.x1() >= x && b.z0() <= z && b.z1() >= z) {
						hit++;
						break;
					}
				}
			}
			best = Math.max(best, hit / (double) n);
		}
		return best;
	}

	/** Can a body of half width `half` (1.8 high, stepping over 0.6) walk from outside the extent to the middle of the yard? */
	static boolean walkIn(TentType t, double half) {
		double over = 0.6;
		TentType.Box e = t.extent();
		double step = 0.1, x0 = e.x0() - 1.0, z0 = e.z0() - 1.0;
		int nx = (int) Math.ceil((e.width() + 2.0) / step) + 1, nz = (int) Math.ceil((e.depth() + 2.0) / step) + 1;
		boolean[][] seen = new boolean[nx][nz];
		ArrayDeque<int[]> todo = new ArrayDeque<>();
		for (int i = 0; i < nx; i++) {
			for (int k = 0; k < nz; k++) {
				if (i == 0 || k == 0 || i == nx - 1 || k == nz - 1) {
					seen[i][k] = true;
					todo.add(new int[] {i, k});
				}
			}
		}
		while (!todo.isEmpty()) {
			int[] c = todo.poll();
			double x = x0 + c[0] * step, z = z0 + c[1] * step;
			if (x > e.x0() + 1.4 && x < e.x1() - 1.4 && z > e.z0() + 1.4 && z < e.z1() - 1.4) {
				return true;
			}
			for (int[] d : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
				int i = c[0] + d[0], k = c[1] + d[1];
				if (i >= 0 && k >= 0 && i < nx && k < nz && !seen[i][k] && free(t, x0 + i * step, z0 + k * step, half, 1.8, over)) {
					seen[i][k] = true;
					todo.add(new int[] {i, k});
				}
			}
		}
		return false;
	}

	private static boolean free(TentType t, double x, double z, double half, double h, double over) {
		for (TentType.Box b : t.colliders()) {
			if (b.x0() < x + half && b.x1() > x - half && b.z0() < z + half && b.z1() > z - half && b.y0() < h && b.y1() > over) {
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
		assertEquals("Entraînement", fr.get("itemGroup.medievalships.training").getAsString());
		assertEquals("Training", en.get("itemGroup.medievalships.training").getAsString());
		for (TentType t : TentTypes.TRAINING) {
			String key = "block.medievalships." + t.id();
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1), fr.get(key).getAsString(),
					"same French name in the commands and the lang file");
			assertEquals(t.englishName(), en.get(key).getAsString());
			for (String file : new String[] {"training/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
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
	void modelsLoadStaticWithinTheBudget() throws Exception {
		for (TentType t : TentTypes.TRAINING) {
			try (var in = TrainingTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 600 && m.quadCount() <= 900 * 6, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a training area has no animation");
			}
			for (TentType.Particle p : t.particles()) {
				assertTrue(p.known() && p.chance() <= 0.15 && p.count() <= 2, t.id() + " a rare discreet particle only " + p);
			}
			if (t.decor() != null) {
				InteriorDecor.load(t.decor());
			}
		}
	}
}
