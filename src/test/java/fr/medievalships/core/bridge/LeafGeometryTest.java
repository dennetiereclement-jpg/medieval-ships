package fr.medievalships.core.bridge;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

/** The leaf frame and shape: rotation about the hinge, boxes, swept volume, underside. */
class LeafGeometryTest {
	/** A channel running along +z at x = 0; the west leaf's hinge at x = -6, the leaf reaching to x = 0 (inward = +x). */
	private static LeafFrame westFrame() {
		return LeafFrame.of(-6, 70, 0, 0, 1, 1, 0);
	}

	/** Cubes covering x in [-6, 0), y in [69, 70), z in [-2, 2): a 6 x 1 x 4 half deck. */
	private static List<double[]> westDeck() {
		List<double[]> boxes = new ArrayList<>();
		for (int x = -6; x < 0; x++) {
			for (int z = -2; z < 2; z++) {
				boxes.add(new double[] {x, 69, z, x + 1, 70, z + 1});
			}
		}
		return boxes;
	}

	@Test
	void frameAxesAndRoundTrip() {
		LeafFrame f = westFrame();
		assertEquals(0, f.ux(), 1e-12);
		assertEquals(1, f.uz(), 1e-12);
		assertEquals(1, f.vx(), 1e-12);
		assertEquals(0, f.vz(), 1e-12);
		double[] l = f.toLocal(-3, 71.5, 1.25);
		assertEquals(1.25, l[0], 1e-12); // along the hinge (z)
		assertEquals(3, l[1], 1e-12); // inward (x from -6)
		assertEquals(1.5, l[2], 1e-12); // up
		double[] w = f.toWorld(l[0], l[1], l[2], 0);
		assertEquals(-3, w[0], 1e-12);
		assertEquals(71.5, w[1], 1e-12);
		assertEquals(1.25, w[2], 1e-12);
	}

	@Test
	void raisingLiftsTheFreeEnd() {
		LeafFrame f = westFrame();
		// the free end (b = 6, c = 0) at 90 degrees stands 6 above the hinge, over it
		double[] w = f.toWorld(0, 6, 0, 90);
		assertEquals(-6, w[0], 1e-9);
		assertEquals(76, w[1], 1e-9);
		// at 45 degrees it is half way up and half way in
		double[] h = f.toWorld(0, 6, 0, 45);
		assertEquals(-6 + 6 * Math.cos(Math.PI / 4), h[0], 1e-9);
		assertEquals(70 + 6 * Math.sin(Math.PI / 4), h[1], 1e-9);
		// the axis the renderer rotates about: v x up = (-vz, 0, vx) = (0, 0, 1) here
		double[] n = f.rotationAxis();
		assertEquals(0, n[0], 1e-12);
		assertEquals(1, n[2], 1e-12);
		// the east leaf (hinge at +6, inward = -x) rises the same way, its axis opposite
		LeafFrame e = LeafFrame.of(6, 70, 0, 0, 1, -1, 0);
		double[] we = e.toWorld(0, 6, 0, 90);
		assertEquals(6, we[0], 1e-9);
		assertEquals(76, we[1], 1e-9);
		assertEquals(-1, e.rotationAxis()[2], 1e-12);
	}

	@Test
	void closedBoxesAreTheBlocksAndRaisedOnesStandUp() {
		LeafShape s = new LeafShape(westFrame(), westDeck());
		assertEquals(24, s.boxes().size());
		List<double[]> closed = s.worldBoxes(0);
		for (int i = 0; i < closed.size(); i++) {
			for (int k = 0; k < 6; k++) {
				assertEquals(westDeck().get(i)[k], closed.get(i)[k], 1e-9, "box " + i + " component " + k);
			}
		}
		assertEquals(-2, s.minA(), 1e-9);
		assertEquals(2, s.maxA(), 1e-9);
		assertEquals(0, s.minB(), 1e-9);
		assertEquals(6, s.maxB(), 1e-9);
		assertEquals(-1, s.minC(), 1e-9);
		assertEquals(0, s.maxC(), 1e-9);
		double[] up = s.bounds(90);
		// upright: a slab 1 thick (the deck's thickness, now along x, from the hinge towards the channel), 6 high
		assertEquals(-6, up[0], 1e-9);
		assertEquals(-5, up[3], 1e-9);
		assertEquals(70, up[1], 1e-9);
		assertEquals(76, up[4], 1e-9);
		assertEquals(-2, up[2], 1e-9);
		assertEquals(2, up[5], 1e-9);
		// the channel's middle (x = -0.5, just under the former deck) is free when raised
		assertTrue(s.contains(0, -0.5, 69.5, 0));
		assertFalse(s.contains(90, -0.5, 69.5, 0));
		assertFalse(s.contains(80, -0.5, 69.5, 0));
		// the swept volume covers the arc between closed and upright
		List<double[]> swept = s.sweptBoxes(0, 90);
		assertTrue(LeafShape.intersectsAny(swept, -3.1, 72, -0.5, -2.9, 73, 0.5), "a point on the 45 degree arc");
		assertFalse(LeafShape.intersectsAny(swept, 2, 72, -0.5, 3, 73, 0.5), "beyond the hinge side of the channel");
		double[] sb = s.sweptBounds(0, 90);
		assertEquals(-6, sb[0], 1e-9);
		// the thickness of the deck swings a little past the free end while rising (sqrt(37) - 6 at most)
		assertTrue(sb[3] >= 0 && sb[3] <= Math.sqrt(37) - 6 + 1e-9, "swept max x " + sb[3]);
		assertEquals(69, sb[1], 1e-9);
		assertEquals(76, sb[4], 1e-9);
	}

	@Test
	void undersideOverTheChannel() {
		ChannelZones zones = ChannelZones.of(0, 0, 0, 1, 4, 2, 50, 8);
		List<double[]> boxes = westDeck();
		boxes.add(new double[] {-2, 67.5, -1, -1, 69, 0}); // a lantern hanging under the deck, over the channel
		boxes.add(new double[] {-6, 66, -1, -5, 69, 0}); // a support against the tower, outside the band
		LeafShape s = new LeafShape(westFrame(), boxes);
		assertEquals(67.5, s.undersideOver(zones::across, 4), 1e-9);
		assertEquals(69, new LeafShape(westFrame(), westDeck()).undersideOver(zones::across, 4), 1e-9);
	}

	@Test
	void collectOnlyNearTheQuery() {
		LeafShape s = new LeafShape(westFrame(), westDeck());
		List<double[]> out = new ArrayList<>();
		s.collect(0, -3.2, 68, -0.5, -2.8, 71, 0.5, out);
		assertEquals(4, out.size()); // the cells at x in [-4, -3) and [-3, -2), z in [-1, 0) and [0, 1)
		out.clear();
		s.collect(0, 10, 68, 10, 11, 71, 11, out);
		assertTrue(out.isEmpty());
	}
}
