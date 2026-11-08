package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The tents: geometry files, the facing rotation of extents and collision boxes, the decor file, the model. */
public class TentTest {
	private static final double EPS = 1e-9;

	@Test
	void sixTypesLoad() {
		assertEquals(6 + 6 + 5 + 2 + 2 + 1 + 3, TentTypes.ALL.size(),
				"six camp tents, six merchant tents, the five of 1.15.0, the two of 1.16.0, the two of 1.17.0, the jeweller's of 1.21.0, the military camp of 1.25.0");
		assertEquals(TentTypes.MERCHANTS, TentTypes.ALL.subList(6, 12), "the merchant tents come after the camp tents");
		assertEquals(TentTypes.MERCHANTS2, TentTypes.ALL.subList(12, 17), "then the merchant tents II (1.15.0)");
		assertEquals(TentTypes.MERCHANTS3, TentTypes.ALL.subList(17, 19), "then the merchant tents III (1.16.0)");
		assertEquals(TentTypes.MERCHANTS4, TentTypes.ALL.subList(19, 21), "then the merchant tents IV (1.17.0)");
		assertEquals(TentTypes.MERCHANTS5, TentTypes.ALL.subList(21, 22), "then the jeweller's tent (1.21.0)");
		assertEquals(TentTypes.CAMP_TENTS, TentTypes.ALL.subList(22, 25), "then the military camp tents (1.25.0)");
		for (TentType t : TentTypes.ALL) {
			assertTrue(t.id().startsWith("tent_") || t.id().startsWith("tente_"), t.id());
			assertNotNull(t.extent());
			assertTrue(t.extent().x1() > t.extent().x0() && t.extent().y1() > t.extent().y0() && t.extent().z1() > t.extent().z0(), t.id());
			assertFalse(t.frenchName().isBlank());
			assertFalse(t.englishName().isBlank());
		}
		assertEquals(TentTypes.ADVENTURER, TentTypes.byId("tent_adventurer"));
		assertEquals(TentTypes.ADVENTURER, TentTypes.byId("adventurer"));
		assertEquals(TentTypes.CHIEF, TentTypes.byId("medievalships:tent_chief"));
		assertNull(TentTypes.byId("yurt"));
	}

	@Test
	void rotationFollowsTheFacing() {
		// the tent's front (+z) goes to the facing: south, west, north, east
		assertArrayEquals(new double[] {0, 1}, TentType.rotate(0, 1, TentType.SOUTH));
		assertArrayEquals(new double[] {-1, 0}, TentType.rotate(0, 1, TentType.WEST));
		assertArrayEquals(new double[] {0, -1}, TentType.rotate(0, 1, TentType.NORTH));
		assertArrayEquals(new double[] {1, 0}, TentType.rotate(0, 1, TentType.EAST));
		// a proper rotation, not a mirror: +x goes to -z when the front goes to -x
		assertArrayEquals(new double[] {0, 1}, TentType.rotate(1, 0, TentType.WEST));
		// four quarters are the identity
		assertArrayEquals(new double[] {2.5, -1.25}, TentType.rotate(2.5, -1.25, 4));
	}

	@Test
	void rotatedBoxesKeepTheirSize() {
		TentType.Box b = new TentType.Box(1.0, 0.0, 2.0, 1.5, 3.0, 2.8);
		for (int q = 0; q < 4; q++) {
			TentType.Box r = TentType.rotate(b, q);
			assertEquals(b.height(), r.height(), EPS);
			assertEquals(b.width() * b.depth(), r.width() * r.depth(), EPS);
			assertTrue(r.x1() >= r.x0() && r.z1() >= r.z0());
		}
		TentType.Box w = TentType.rotate(b, TentType.WEST);
		// (x, z) -> (-z, x): the box ahead on the right goes to the left and ahead
		assertEquals(-2.8, w.x0(), EPS);
		assertEquals(-2.0, w.x1(), EPS);
		assertEquals(1.0, w.z0(), EPS);
		assertEquals(1.5, w.z1(), EPS);
		TentType.Box n = TentType.rotate(b, TentType.NORTH);
		assertEquals(-1.5, n.x0(), EPS);
		assertEquals(-2.8, n.z0(), EPS);
	}

	@Test
	void adventurerGeometry() {
		TentType t = TentTypes.ADVENTURER;
		TentType.Box e = t.extent();
		assertTrue(e.width() > 6 && e.width() < 10, "width " + e.width());
		assertTrue(e.height() > 3 && e.height() < 5, "height " + e.height());
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(t.colliders().size() >= 10, "collision boxes " + t.colliders().size());
		// the front legs stand in front of the anchor (+z), inside the extent
		boolean frontPost = false;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS, "inside the extent " + b);
			if (b.z0() > 1.5 && b.y0() < 0.2 && b.height() > 0.8) {
				frontPost = true;
			}
		}
		assertTrue(frontPost, "a front leg from the ground");
		// turned to the west, the front legs are on the -x side
		boolean westPost = false;
		for (TentType.Box b : t.colliders(TentType.WEST)) {
			if (b.x1() < -1.5 && b.y0() < 0.2 && b.height() > 0.8) {
				westPost = true;
			}
		}
		assertTrue(westPost);
		assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
	}

	@Test
	void adventurerDecorAndModel() throws Exception {
		TentType t = TentTypes.ADVENTURER;
		assertNotNull(t.decor());
		InteriorDecor decor = InteriorDecor.load(t.decor());
		assertTrue(decor.blocks().size() >= 5, "furniture " + decor.blocks().size());
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("_crate")), "a crate");
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("_barrel")), "a barrel");
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("lantern") && b.glow()), "a glowing lantern");
		assertTrue(decor.blocks().stream().anyMatch(b -> "minecraft:barrel".equals(b.alt())), "a vanilla alternative");
		for (InteriorDecor.Block b : decor.blocks()) {
			assertTrue(b.fallback().startsWith("fallback_"), b.fallback());
			assertTrue(b.block().contains(":"), b.block());
		}
		try (var in = TentTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			assertNotNull(in, "model " + t.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 300, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "a tent has no animation");
			for (InteriorDecor.Block b : decor.blocks()) {
				assertTrue(m.bonesByName.containsKey(b.fallback()), "stand-in bone " + b.fallback());
			}
			assertTrue(m.bonesByName.containsKey("detail"));
			assertTrue(m.bonesByName.containsKey("furniture"));
		}
	}

	@Test
	void commandGeometryAndDecor() throws Exception {
		TentType t = TentTypes.COMMAND;
		TentType.Box e = t.extent();
		assertTrue(e.width() > 9 && e.width() < 12, "width " + e.width());
		assertTrue(e.height() > 7 && e.height() < 9, "height " + e.height());
		assertTrue(e.depth() > 7 && e.depth() < 10, "depth " + e.depth());
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(t.colliders().size() >= 30, "collision boxes " + t.colliders().size());
		int cornerPosts = 0;
		boolean platform = false;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS, "inside the extent " + b);
			if (b.y0() < 0.1 && Math.abs(b.x0() + b.x1()) > 6 && Math.abs(b.z0() + b.z1()) > 5) {
				cornerPosts++;
			}
			if (b.width() > 8 && b.depth() > 6 && b.y1() < 1.0) {
				platform = true;
			}
		}
		assertEquals(4, cornerPosts, "the four corner posts stand on the ground");
		assertTrue(platform, "the platform");
		assertEquals(t.colliders().size(), t.colliders(TentType.NORTH).size());
		InteriorDecor decor = InteriorDecor.load(t.decor());
		assertTrue(decor.blocks().size() >= 10, "furniture " + decor.blocks().size());
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().equals("farmhouse_decorations:desk")), "the strategy table");
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("_chair") || b.block().endsWith("_stool")), "seats");
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("lantern") && b.glow()), "a glowing lantern");
		try (var in = TentTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			assertNotNull(in, "model " + t.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 1000 && m.quadCount() < 12000, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty());
			for (InteriorDecor.Block b : decor.blocks()) {
				assertTrue(m.bonesByName.containsKey(b.fallback()), "stand-in bone " + b.fallback());
			}
			assertTrue(m.bonesByName.containsKey("canvas") && m.bonesByName.containsKey("detail") && m.bonesByName.containsKey("furniture"));
		}
	}

	private static void assertArrayEquals(double[] expected, double[] actual) {
		assertEquals(expected.length, actual.length);
		for (int i = 0; i < expected.length; i++) {
			assertEquals(expected[i], actual[i], EPS, "component " + i);
		}
	}
}
