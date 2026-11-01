package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The market awning: a big open hipped awning on eight posts, stalls and goods of the decoration mods. */
public class TentMarketTest {
	private static final double EPS = 1e-9;

	@Test
	void marketGeometry() {
		TentType t = TentTypes.byId("tent_market");
		assertNotNull(t);
		TentType.Box e = t.extent();
		assertTrue(e.width() > 10 && e.width() < 13, "width " + e.width());
		assertTrue(e.height() > 5 && e.height() < 7, "height " + e.height());
		assertTrue(e.depth() > 8 && e.depth() < 12, "depth " + e.depth());
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(t.colliders().size() >= 30, "collision boxes " + t.colliders().size());
		int postsFront = 0, postsBack = 0, stalls = 0;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS, "inside the extent " + b);
			if (b.y0() < 0.2 && b.height() > 0.8 && b.width() < 0.6) {
				if (b.z0() > 2.5) {
					postsFront++;
				} else if (b.z1() < -2.5) {
					postsBack++;
				}
			}
			if (b.width() > 3 && b.height() > 0.8 && b.height() < 1.2 && b.z0() > 0.5) {
				stalls++;
			}
		}
		assertTrue(postsFront >= 4, "front posts " + postsFront);
		assertTrue(postsBack >= 4, "back posts " + postsBack);
		assertEquals(2, stalls, "the two stalls");
		// nothing blocks the entrance between the two stalls at ground level
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x1() < -0.6 || b.x0() > 0.6 || b.z1() < 1.0 || b.z0() > 2.5 || b.y0() > 2.5, "the entrance is free " + b);
		}
		assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
	}

	@Test
	void marketDecorAndModel() throws Exception {
		TentType t = TentTypes.byId("tent_market");
		assertNotNull(t.decor());
		InteriorDecor d = InteriorDecor.load(t.decor());
		assertTrue(d.blocks().size() >= 25, "mod blocks " + d.blocks().size());
		Set<String> mods = new HashSet<>();
		boolean lantern = false;
		for (InteriorDecor.Block b : d.blocks()) {
			mods.add(b.block().substring(0, b.block().indexOf(':')));
			assertNotNull(b.fallback(), b.block());
			lantern |= b.glow();
		}
		assertTrue(lantern, "a glowing lantern");
		assertTrue(mods.contains("farmersdelight") && mods.contains("furnish") && mods.contains("landsoficaria") && mods.contains("farmhouse_decorations"), mods.toString());
		try (var in = TentMarketTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			assertNotNull(in, "model " + t.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 600 && m.quadCount() < 9000, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "a tent has no animation");
			for (int i = 0; i < d.blocks().size(); i++) {
				assertTrue(m.bonesByName.containsKey("fallback_" + i), "stand-in bone fallback_" + i);
			}
			for (String bone : new String[] {"frame", "canvas", "detail", "furniture"}) {
				assertTrue(m.bonesByName.containsKey(bone), bone);
			}
		}
	}
}
