package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The eight carts: the second family of one-block props (same TentType machinery as the tents). */
public class CartTest {
	private static final double EPS = 1e-9;
	private static final List<String> IDS = List.of("cart_covered_white", "cart_hay", "cart_merchant_wagon", "cart_market", "cart_logs",
			"cart_open", "cart_covered_teal", "cart_barrels");

	@Test
	void eightCartsLoadBesideTheSixTents() {
		assertEquals(8, TentTypes.CARTS.size());
		assertEquals(6 + 6, TentTypes.ALL.size(), "the tents' list: six camp tents and six merchant tents");
		assertEquals(6 + 6 + 8 + 7, TentTypes.PROPS.size()); // tents, merchant tents, carts, workshops
		Set<String> ids = new HashSet<>();
		for (TentType t : TentTypes.CARTS) {
			assertTrue(IDS.contains(t.id()), t.id());
			assertTrue(ids.add(t.id()));
			assertEquals(TentType.CARTS, t.group());
			assertTrue(t.isCart());
			assertEquals("textures/entity/carts.png", t.texture());
			assertEquals("models/entity/" + t.id() + ".bbmodel", t.model());
			assertFalse(t.frenchName().isBlank());
			assertFalse(t.englishName().isBlank());
		}
		for (TentType t : TentTypes.ALL) {
			assertEquals(TentType.TENTS, t.group());
			if (TentTypes.MERCHANTS.contains(t)) {
				assertTrue(t.texture().startsWith("textures/entity/tente_"), t.id() + ": a merchant tent has its own atlas " + t.texture());
			} else {
				assertEquals(TentType.DEFAULT_TEXTURE, t.texture(), t.id());
			}
		}
		assertSame(TentTypes.CART_OPEN, TentTypes.byId("cart_open"));
		assertSame(TentTypes.CART_OPEN, TentTypes.byId("open"));
		assertSame(TentTypes.CART_HAY, TentTypes.byId("medievalships:cart_hay"));
		assertSame(TentTypes.CAMP, TentTypes.byId("camp"));
	}

	@Test
	void extentsToScaleAndCollidersInside() {
		for (TentType t : TentTypes.CARTS) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), EPS, t.id() + " stands on the ground");
			assertTrue(e.depth() > 3.0 && e.depth() < 8.0, t.id() + " length " + e.depth());
			assertTrue(e.width() > 1.8 && e.width() < 4.0, t.id() + " width " + e.width());
			assertTrue(e.height() > 1.4 && e.height() < 4.0, t.id() + " height " + e.height());
			assertTrue(t.colliders().size() >= 3, t.id() + " collision boxes " + t.colliders().size());
			boolean wheel = false;
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS
						&& b.y1() <= e.y1() + EPS, t.id() + " inside the extent " + b);
				if (b.y0() < 0.05 && b.width() < 0.4 && b.height() > 0.8) {
					wheel = true;
				}
			}
			assertTrue(wheel, t.id() + " a wheel on the ground collides");
		}
	}

	@Test
	void rotationTurnsExtentAndColliders() {
		for (TentType t : TentTypes.CARTS) {
			TentType.Box s = t.extent(TentType.SOUTH), w = t.extent(TentType.WEST), n = t.extent(TentType.NORTH);
			assertEquals(s.width(), w.depth(), 1e-6, t.id());
			assertEquals(s.depth(), w.width(), 1e-6, t.id());
			// the drawbar (+z, front) goes to -x when facing west, to -z when facing north
			assertEquals(-s.z1(), w.x0(), 1e-6, t.id());
			assertEquals(-s.z1(), n.z0(), 1e-6, t.id());
			assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
		}
	}

	@Test
	void openCartGeometry() {
		TentType t = TentTypes.CART_OPEN;
		TentType.Box e = t.extent();
		assertTrue(e.z1() > 2.5, "the drawbar reaches forward " + e.z1());
		int wheels = 0;
		boolean bed = false;
		for (TentType.Box b : t.colliders()) {
			if (b.y0() < 0.05 && b.width() < 0.4 && b.height() > 1.2) {
				wheels++;
			}
			if (b.width() > 1.5 && b.depth() > 2.0 && b.y1() > 0.8 && b.y1() < 1.2) {
				bed = true;
			}
			assertTrue(b.z1() < 1.3, "the drawbar does not collide " + b);
		}
		assertEquals(2, wheels, "two big wheels");
		assertTrue(bed, "the bed");
	}

	@Test
	void modelsLoadLight() throws Exception {
		for (TentType t : TentTypes.CARTS) {
			try (var in = CartTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 200 && m.quadCount() < 600 * 6, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), "a cart has no animation");
				assertTrue(m.bonesByName.containsKey("detail"), t.id() + " detail bone");
			}
		}
	}
}
