package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The camp tent (tent_camp): geometry, furniture of the decoration mods and the model written by its generator. */
public class TentCampTest {
	private static final double EPS = 1e-9;

	@Test
	void campGeometry() {
		TentType t = TentTypes.CAMP;
		TentType.Box e = t.extent();
		assertTrue(e.width() > 6 && e.width() < 10, "width " + e.width());
		assertTrue(e.height() > 3.5 && e.height() < 5, "height " + e.height());
		assertTrue(e.depth() > 6 && e.depth() < 10, "depth " + e.depth());
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(t.colliders().size() >= 15, "collision boxes " + t.colliders().size());
		boolean frontPost = false, floor = false, leftProp = false;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS, "inside the extent " + b);
			if (b.z0() > 1.8 && b.y0() < 0.2 && b.height() > 0.8 && Math.abs(b.x0()) < 0.5) {
				frontPost = true;    // the tall front post through the ridge
			}
			if (b.width() > 3.5 && b.depth() > 4 && b.height() < 0.4) {
				floor = true;        // the plank floor
			}
			if (b.x1() < -2.0 && b.y0() < 0.2 && b.z0() > 1.5) {
				leftProp = true;     // the leaning prop of the left flap, front
			}
		}
		assertTrue(frontPost, "the front post from the ground");
		assertTrue(floor, "the plank floor");
		assertTrue(leftProp, "the front prop of the flap");
		assertEquals(t.colliders().size(), t.colliders(TentType.NORTH).size());
	}

	@Test
	void campDecorAndModel() throws Exception {
		TentType t = TentTypes.CAMP;
		assertNotNull(t.decor());
		InteriorDecor decor = InteriorDecor.load(t.decor());
		assertTrue(decor.blocks().size() >= 6, "furniture " + decor.blocks().size());
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("_crate")), "a crate");
		assertTrue(decor.blocks().stream().anyMatch(b -> b.block().endsWith("lantern") && b.glow()), "a glowing lantern");
		assertTrue(decor.blocks().stream().anyMatch(b -> "minecraft:barrel".equals(b.alt())), "a vanilla alternative");
		try (var in = TentCampTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			assertNotNull(in, "model " + t.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 300, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "a tent has no animation");
			for (InteriorDecor.Block b : decor.blocks()) {
				assertTrue(b.fallback().startsWith("fallback_"), b.fallback());
				assertTrue(m.bonesByName.containsKey(b.fallback()), "stand-in bone " + b.fallback());
			}
			assertTrue(m.bonesByName.containsKey("detail"));
			assertTrue(m.bonesByName.containsKey("furniture"));
		}
	}
}
