package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Shape checks of the four wagons (two covered wagons, the merchant wagon and the market cart). */
class WagonCartsTest {
	private static int groundWheels(TentType t) {
		int n = 0;
		for (TentType.Box b : t.colliders()) {
			if (b.y0() < 0.05 && b.width() < 0.4 && b.height() > 0.8) {
				n++;
			}
		}
		return n;
	}

	private static double top(TentType t) {
		double y = 0;
		for (TentType.Box b : t.colliders()) {
			y = Math.max(y, b.y1());
		}
		return y;
	}

	@Test
	void fourWheelsEach() {
		for (TentType t : new TentType[] {TentTypes.CART_COVERED_WHITE, TentTypes.CART_COVERED_TEAL, TentTypes.CART_MERCHANT_WAGON,
				TentTypes.CART_MARKET}) {
			assertEquals(4, groundWheels(t), t.id() + " four wheels on the ground");
		}
	}

	@Test
	void coversAndRoofsAreTallAndSolid() {
		assertTrue(top(TentTypes.CART_COVERED_WHITE) > 3.0, "white cover top " + top(TentTypes.CART_COVERED_WHITE));
		assertTrue(top(TentTypes.CART_COVERED_TEAL) > 2.6, "teal cover top " + top(TentTypes.CART_COVERED_TEAL));
		assertTrue(top(TentTypes.CART_MERCHANT_WAGON) > 2.9, "merchant roof top " + top(TentTypes.CART_MERCHANT_WAGON));
		assertTrue(top(TentTypes.CART_MARKET) > 2.7, "market awning top " + top(TentTypes.CART_MARKET));
		// the big white wagon is longer and taller than the teal one
		TentType.Box w = TentTypes.CART_COVERED_WHITE.extent(), t = TentTypes.CART_COVERED_TEAL.extent();
		assertTrue(w.depth() > t.depth() && w.height() > t.height(), "white wagon bigger than the teal one");
	}

	@Test
	void merchantWagonStepsAtTheDoor() {
		int steps = 0;
		for (TentType.Box b : TentTypes.CART_MERCHANT_WAGON.colliders()) {
			if (b.y0() < 0.05 && b.y1() < 0.9 && b.z0() > 1.2 && b.width() > 0.6) {
				steps++;
			}
		}
		assertEquals(3, steps, "three steps in front of the door");
	}
}
