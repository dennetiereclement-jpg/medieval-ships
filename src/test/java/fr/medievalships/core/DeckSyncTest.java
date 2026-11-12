package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;

import org.junit.jupiter.api.Test;

/**
 * Players on moving decks in multiplayer (1.30.0): deck frames ({@link DeckFrame}), the deck interpolation of the other
 * players, and the anchor that brings a player back aboard ({@link DeckAnchor}).
 */
class DeckSyncTest {
	private static final ShipGeometry GALLEON = Ships.GALLEON.geometry();

	/** A ship under way and turning: pose at server tick t. */
	private static ShipPose serverPose(int t) {
		double yaw = 10 + 0.9 * t; // turning 18 degrees per second
		double x = 0, z = 0, y = 62;
		for (int i = 0; i < t; i++) {
			double r = Math.toRadians(10 + 0.9 * i);
			x += -Math.sin(r) * 0.3; // 6 blocks per second
			z += Math.cos(r) * 0.3;
		}
		return new ShipPose(x, y + 0.05 * t, z, yaw); // and climbing 1 block per second (an airship)
	}

	@Test
	void roundTripAndReframe() {
		ShipPose a = new ShipPose(100.5, 64, -20.25, 37);
		double[] out = new double[3];
		DeckFrame.toWorld(a, 1.5, 2, -3, out);
		double[] ref = a.toWorld(1.5, 2, -3);
		assertEquals(ref[0], out[0], 1e-12);
		assertEquals(ref[1], out[1], 1e-12);
		assertEquals(ref[2], out[2], 1e-12);
		DeckFrame.toLocal(a, out[0], out[1], out[2], out);
		assertEquals(1.5, out[0], 1e-9);
		assertEquals(2, out[1], 1e-9);
		assertEquals(-3, out[2], 1e-9);
		// the same local spot on another pose
		ShipPose b = new ShipPose(110, 66, -18, 80);
		double[] w = a.toWorld(0.5, 1, 4);
		DeckFrame.reframe(a, b, w[0], w[1], w[2], out);
		double[] expected = b.toWorld(0.5, 1, 4);
		assertEquals(expected[0], out[0], 1e-9);
		assertEquals(expected[1], out[1], 1e-9);
		assertEquals(expected[2], out[2], 1e-9);
		assertEquals(120 + 43, DeckFrame.reframeYaw(a, b, 120), 1e-4);
		// across the +-180 wrap
		assertEquals(170 + 20, DeckFrame.reframeYaw(new ShipPose(0, 0, 0, 170), new ShipPose(0, 0, 0, -170), 170), 1e-4);
	}

	@Test
	void plausibleFramesOnly() {
		ShipPose s = new ShipPose(0, 64, 0, 0);
		assertTrue(DeckFrame.plausible(new ShipPose(5, 64, -3, 12), s));
		assertFalse(DeckFrame.plausible(new ShipPose(60, 64, 0, 0), s), "a hull drawn far from the server's one is not believed");
		assertFalse(DeckFrame.plausible(new ShipPose(Double.NaN, 64, 0, 0), s));
		assertFalse(DeckFrame.plausible(new ShipPose(0, 64, 0, Double.POSITIVE_INFINITY), s));
	}

	/**
	 * The whole chain on a ship under way, turning and climbing: a client draws the hull 5 ticks behind the server (its
	 * delay and interpolation), carries its player standing on the deck, reports his world position and its frame; the
	 * server puts him on its own hull; another client, 3 ticks behind, draws him at the deck position the server sends.
	 * The player stays at the same deck spot everywhere, at every tick; without the frame the server copy lagged
	 * behind on the deck by more than a block.
	 */
	@Test
	void playerStaysOnTheSameDeckSpotEverywhere() {
		double[] spot = {1.2, GalleonDeck.Y, -3.5};
		double[] out = new double[3];
		double worstServer = 0, worstObserver = 0, worstOld = 0;
		for (int t = 10; t < 200; t++) {
			ShipPose server = serverPose(t);
			ShipPose client = serverPose(t - 5);
			// the client carries its player with the hull it draws: his world position on that client
			double[] world = client.toWorld(spot[0], spot[1], spot[2]);
			// with the frame: the same spot of the server's hull
			DeckFrame.reframe(client, server, world[0], world[1], world[2], out);
			double[] l = server.toLocal(out[0], out[1], out[2]);
			worstServer = Math.max(worstServer, dist(l, spot));
			// the deck position sent to the others, drawn on their own (later) hull
			ShipPose observer = serverPose(t - 3);
			double[] drawn = observer.toWorld(l[0], l[1], l[2]);
			worstObserver = Math.max(worstObserver, dist(observer.toLocal(drawn[0], drawn[1], drawn[2]), spot));
			// before 1.30.0: the server took the client's world position as it came
			worstOld = Math.max(worstOld, dist(server.toLocal(world[0], world[1], world[2]), spot));
		}
		assertTrue(worstServer < 1e-9, "server copy on the deck spot (off by " + worstServer + ")");
		assertTrue(worstObserver < 1e-9, "drawn on the deck spot by the other clients (off by " + worstObserver + ")");
		assertTrue(worstOld > 1.0, "without the frame the server copy lagged behind (" + worstOld + ")");
	}

	/** The galleon's main deck height (local), from its layout. */
	private static final class GalleonDeck {
		static final double Y = Ships.GalleonLayout.MAIN_DECK_Y;
	}

	private static double dist(double[] a, double[] b) {
		return Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
	}

	@Test
	void deckPositionSentOnlyWhenItChanges() {
		double[] last = {1, 2, 3, 10, 20, 5};
		assertFalse(DeckFrame.changed(last, 1, 2, 3, 10, 20, 5));
		assertFalse(DeckFrame.changed(last, 1.001, 2, 3, 10.2, 20, 5), "below the thresholds");
		assertTrue(DeckFrame.changed(last, 1.01, 2, 3, 10, 20, 5));
		assertTrue(DeckFrame.changed(last, 1, 2, 3, 11, 20, 5));
		assertTrue(DeckFrame.changed(last, 1, 2, 3, 10, 20, 6));
		// the yaw wraps: 179.9 and -179.9 are 0.2 degrees apart
		double[] wrap = {0, 0, 0, 179.9, 0, 0};
		assertFalse(DeckFrame.changed(wrap, 0, 0, 0, -179.9, 0, 0));
	}

	@Test
	void deckInterpolationReachesTheTargetInThreeSteps() {
		DeckFrame.Lerp l = new DeckFrame.Lerp();
		assertFalse(l.started());
		l.start(0, 1, 0, 170, 170, 0);
		l.target(3, 1, -3, -170, -160, 30);
		l.step();
		assertEquals(1, l.x, 1e-9);
		assertEquals(0, l.lastX, 1e-9);
		l.step();
		l.step();
		assertEquals(3, l.x, 1e-9);
		assertEquals(-3, l.z, 1e-9);
		assertEquals(30, l.pitch, 1e-4);
		// the short way across the wrap: 170 -> 190 (= -170), never through 0
		assertEquals(-170, DeckFrame.wrap(l.yaw), 1e-3);
		assertEquals(-160, DeckFrame.wrap(l.head), 1e-3);
		l.step(); // no target: stays
		assertEquals(3, l.x, 1e-9);
		assertEquals(3, l.lastX, 1e-9);
	}

	@Test
	void anchorChangesOnlyBeyondThresholds() {
		UUID ship = UUID.randomUUID();
		DeckAnchor a = new DeckAnchor(ship, "minecraft:overworld", 1, 1, 1, 0);
		assertTrue(a.differs(null));
		assertFalse(a.differs(new DeckAnchor(ship, "minecraft:overworld", 1.1, 1, 1, 5)));
		assertTrue(a.differs(new DeckAnchor(ship, "minecraft:overworld", 1.4, 1, 1, 0)));
		assertTrue(a.differs(new DeckAnchor(ship, "minecraft:overworld", 1, 1, 1, 30)));
		assertTrue(a.differs(new DeckAnchor(UUID.randomUUID(), "minecraft:overworld", 1, 1, 1, 0)), "another ship");
		assertTrue(a.differs(new DeckAnchor(ship, "minecraft:the_nether", 1, 1, 1, 0)));
	}

	@Test
	void restoredOnTheDeckNeverInTheSea() {
		InteriorGrid.State closed = InteriorGrid.State.CLOSED;
		double deck = Ships.GalleonLayout.MAIN_DECK_Y;
		// the anchor itself while it is a place of the deck
		double[] s = DeckAnchor.restoreSpot(GALLEON, closed, 1.0, deck, -2.0);
		assertEquals(1.0, s[0], 1e-9);
		assertEquals(deck + 0.01, s[1], 1e-9);
		assertEquals(-2.0, s[2], 1e-9);
		// sunk a little into the deck: lifted onto it
		s = DeckAnchor.restoreSpot(GALLEON, closed, 1.0, deck - 0.3, -2.0);
		assertEquals(deck + 0.01, s[1], 1e-6);
		// out of the deck volume (beside the hull, garbage): the nearest standing spot, aboard
		for (double[] bad : new double[][] {{12, deck, 0}, {0, -6, 0}, {Double.NaN, 0, 3}, {0, 0, 400}}) {
			s = DeckAnchor.restoreSpot(GALLEON, closed, bad[0], bad[1], bad[2]);
			assertTrue(GALLEON.inCarryVolume(s[0], s[1], s[2]), "aboard: " + s[0] + " " + s[1] + " " + s[2]);
			assertTrue(Double.isFinite(s[0]) && Double.isFinite(s[1]) && Double.isFinite(s[2]));
		}
		// every ship type: a few anchors around and on the hull land aboard
		Random rnd = new Random(7);
		for (ShipType type : Ships.ALL) {
			ShipGeometry g = type.geometry();
			for (int i = 0; i < 20; i++) {
				double lx = (rnd.nextDouble() - 0.5) * 20, ly = (rnd.nextDouble() - 0.5) * 12, lz = (rnd.nextDouble() - 0.5) * 60;
				s = DeckAnchor.restoreSpot(g, closed, lx, ly, lz);
				assertTrue(g.inCarryVolume(s[0], s[1], s[2]), type.id() + ": restored aboard from " + lx + " " + ly + " " + lz);
			}
		}
	}

	@Test
	void nearestDryGround() {
		// a sea with two islands: the nearest one wins, the far one is ignored
		DeckAnchor.Column sea = (x, z) -> (x >= 10 && x <= 12 && z >= -1 && z <= 1) ? 64 : (x <= -20 ? 70 : Double.NaN);
		double[] d = DeckAnchor.nearestDry(0, 0, 64, sea);
		assertNotNull(d);
		assertEquals(10.5, d[0], 1e-9);
		assertEquals(64, d[1], 1e-9);
		assertEquals(0.5, d[2], 1e-9);
		assertNull(DeckAnchor.nearestDry(0, 0, 8, sea), "nothing within 8 blocks");
		assertNotNull(DeckAnchor.nearestDry(0, 0, 0, (x, z) -> x == 0 && z == 0 ? 1 : Double.NaN));
		// matches a brute force search on random maps
		Random rnd = new Random(3);
		for (int k = 0; k < 50; k++) {
			List<int[]> land = new ArrayList<>();
			for (int i = 0; i < 6; i++) {
				land.add(new int[] {rnd.nextInt(61) - 30, rnd.nextInt(61) - 30});
			}
			DeckAnchor.Column col = (x, z) -> {
				for (int[] p : land) {
					if (p[0] == x && p[1] == z) {
						return 1;
					}
				}
				return Double.NaN;
			};
			double best = Double.MAX_VALUE;
			for (int[] p : land) {
				best = Math.min(best, Math.hypot(p[0], p[1]));
			}
			double[] f = DeckAnchor.nearestDry(0, 0, 40, col);
			assertNotNull(f);
			assertEquals(best, Math.hypot(f[0] - 0.5, f[2] - 0.5), 1e-9);
		}
	}
}
