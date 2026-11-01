package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The three cargo carts (hay, logs, barrels): wheels, bed and cargo collision boxes as in their references. */
public class CartCargoTest {
	private static int wheels(TentType t) {
		int n = 0;
		for (TentType.Box b : t.colliders()) {
			if (b.y0() < 0.05 && b.width() < 0.4 && b.height() > 0.8) {
				n++;
			}
		}
		return n;
	}

	private static boolean cargo(TentType t, double minWidth, double minDepth, double minTop) {
		for (TentType.Box b : t.colliders()) {
			if (b.width() >= minWidth && b.depth() >= minDepth && b.y0() > 0.8 && b.y1() >= minTop) {
				return true;
			}
		}
		return false;
	}

	private static void drawbarFree(TentType t, double bedFront) {
		assertTrue(t.extent().z1() > bedFront + 1.5, t.id() + " the drawbar reaches forward " + t.extent().z1());
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.z1() < bedFront + 0.2, t.id() + " the drawbar does not collide " + b);
		}
	}

	@Test
	void hayCartFourWheelsAndBales() {
		TentType t = TentTypes.CART_HAY;
		assertEquals(4, wheels(t), "a four-wheeled wagon");
		assertTrue(cargo(t, 1.6, 2.2, 1.9), "the stacked bales collide");
		assertTrue(t.extent().height() > 1.9, "two layers of bales above the sides");
		drawbarFree(t, 1.5);
	}

	@Test
	void logCartFourWheelsAndStack() {
		TentType t = TentTypes.CART_LOGS;
		assertEquals(4, wheels(t), "a four-wheeled wagon");
		assertTrue(cargo(t, 1.6, 3.0, 2.0), "the log stack collides");
		drawbarFree(t, 1.3);
	}

	@Test
	void barrelCartTwoBigWheelsBarrelsAndLantern() throws Exception {
		TentType t = TentTypes.CART_BARRELS;
		int big = 0;
		for (TentType.Box b : t.colliders()) {
			if (b.y0() < 0.05 && b.width() < 0.4 && b.height() > 1.4) {
				big++;
			}
		}
		assertEquals(2, big, "two big wheels");
		int barrels = 0;
		for (TentType.Box b : t.colliders()) {
			if (b.width() > 0.8 && b.width() < 1.2 && b.depth() > 0.8 && b.depth() < 1.2 && b.height() > 1.0) {
				barrels++;
			}
		}
		assertEquals(2, barrels, "two big standing barrels");
		drawbarFree(t, 1.05);
		try (var in = CartCargoTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			String json = new String(in.readAllBytes(), StandardCharsets.UTF_8);
			assertTrue(json.contains("\"lamp_lamp"), "the lantern on its post");
		}
		try (var in = CartCargoTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() < 600 * 6, "light model " + m.quadCount());
		}
	}
}
