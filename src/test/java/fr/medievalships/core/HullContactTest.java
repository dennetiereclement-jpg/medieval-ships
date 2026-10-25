package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

/**
 * {@link HullContact}: a hull box the moving box already overlaps by a hair still stops it. The Sky Leviathan's
 * tower: a player pressed against the aft wall of its ladder shaft while the airship still turns walked through it
 * with the vanilla rule (a collider already overlapped is ignored), fell out of the tower onto the main deck and never
 * reached the observation deck (in-game test, after the turn added in phase 3).
 */
class HullContactTest {
	private static final double EPS = 1e-9;

	@Test
	void cutsBackAHairlineOverlapOnly() {
		double[] body = {0, 0, 0, 1, 1.8, 1};
		// a wall behind (low z side), 0.01 inside the body: its face goes back to the body's face
		assertArrayEquals(new double[] {0, 0, -0.5, 1, 1.8, 0}, HullContact.clip(body, new double[] {0, 0, -0.5, 1, 1.8, 0.01}), EPS);
		// a wall in front (high x side)
		assertArrayEquals(new double[] {1, 0, 0, 1.5, 1.8, 1}, HullContact.clip(body, new double[] {0.98, 0, 0, 1.5, 1.8, 1}), EPS);
		// a floor 0.02 above the feet: its top goes down to the feet
		assertArrayEquals(new double[] {-1, -0.5, -1, 2, 0, 2}, HullContact.clip(body, new double[] {-1, -0.5, -1, 2, 0.02, 2}), EPS);
		// a ceiling touching the head from above
		assertArrayEquals(new double[] {-1, 1.8, -1, 2, 2.3, 2}, HullContact.clip(body, new double[] {-1, 1.75, -1, 2, 2.3, 2}), EPS);
		// deeper than DEPTH (a door shut on him): unchanged, so he can get out
		double[] deep = {0, 0, -0.5, 1, 1.8, 0.3};
		assertSame(deep, HullContact.clip(body, deep));
		assertArrayEquals(new double[] {0, 0, -0.5, 1, 1.8, 0.3}, deep, EPS);
		// touching or apart: an ordinary collider
		double[] touching = {0, 0, -0.5, 1, 1.8, 0};
		assertArrayEquals(new double[] {0, 0, -0.5, 1, 1.8, 0}, HullContact.clip(body, touching), EPS);
		double[] apart = {3, 0, 0, 4, 1, 1};
		assertSame(apart, HullContact.clip(body, apart));
		assertSame(apart, HullContact.clip(null, apart));
		// a sliver just inside the body's face: dropped
		assertNull(HullContact.clip(body, new double[] {0, 0, 0.9995, 1, 1.8, 1.0005}));
	}

	@Test
	void theTowerShaftHoldsAPlayerPushingAgainstItWhileTheLeviathanTurns() {
		ShipGeometry g = Ships.SKY_LEVIATHAN.geometry();
		// still: the wall holds either way; turning (steadily, or the hull's small swings on a client): the vanilla rule
		// lets him through the wall, the contact never does
		assertEquals(0, throughTheWall(g, 0.0, false));
		for (double turn : new double[] {-0.1, 0.1, 0.3}) {
			assertTrue(throughTheWall(g, turn, false) > 0, "vanilla rule, turning " + turn + " deg/tick: through somewhere");
			assertEquals(0, throughTheWall(g, turn, true), "with the contact, turning " + turn + " deg/tick");
		}
	}

	/**
	 * A player on the ladder of the tower, pushing aft (0.1 block per tick) against the aft wall of the shaft (local z
	 * -2.5) for 3 s, carried by the airship as it turns {@code turn} degrees per tick (alternately, for a swing): at how
	 * many headings of a sweep of 26 does he end up inside or beyond the wall?
	 */
	private static int throughTheWall(ShipGeometry g, double turn, boolean contact) {
		int through = 0;
		for (double yaw0 = -2; yaw0 >= -40; yaw0 -= 1.5) {
			double yaw = yaw0;
			double[] l = {-0.24, 6.0, -2.0};
			for (int t = 0; t < 60; t++) {
				ShipPose p = new ShipPose(0.5, 64, 0.5, yaw);
				double[] c = p.toWorld(l[0], l[1], l[2]);
				double[] body = {c[0] - 0.3, c[1], c[2] - 0.3, c[0] + 0.3, c[1] + 1.8, c[2] + 0.3};
				double[] push = p.dirToWorld(0, 0, -0.1);
				for (int axis : new int[] {0, 2}) {
					double m = sweep(body, boxes(g, p, body, contact), axis, push[axis]);
					body[axis] += m;
					body[axis + 3] += m;
				}
				l = p.toLocal((body[0] + body[3]) / 2, body[1], (body[2] + body[5]) / 2);
				yaw += turn > 0.2 ? (t % 2 == 0 ? turn : -turn) : turn;
			}
			if (l[2] < -2.6) {
				through++;
			}
		}
		return through;
	}

	@Test
	void standingOnTheQuarterdeckWhileItClimbs() {
		// a player standing on the deck sunk by a hundredth stays on it (the floor is not ignored)
		ShipGeometry g = Ships.SKY_LEVIATHAN.geometry();
		ShipPose p = new ShipPose(0.5, 64, 0.5, -12);
		double[] c = p.toWorld(1.3, LeviathanLayout.QUARTERDECK_Y - 0.01, -11.6);
		double[] body = {c[0] - 0.3, c[1], c[2] - 0.3, c[0] + 0.3, c[1] + 1.8, c[2] + 0.3};
		assertTrue(sweep(body, boxes(g, p, body, false), 1, -1.0) < -0.9, "vanilla: falls through");
		assertEquals(0.0, sweep(body, boxes(g, p, body, true), 1, -1.0), 1e-6, "with the contact: stands");
	}

	private static List<double[]> boxes(ShipGeometry g, ShipPose pose, double[] body, boolean contact) {
		List<double[]> out = new ArrayList<>();
		g.collectBoxes(pose, InteriorGrid.State.CLOSED, body[0] - 2, body[1] - 2, body[2] - 2, body[3] + 2, body[4] + 2, body[5] + 2,
				(a, b, cc, d, e, f) -> {
					double[] k = new double[] {a, b, cc, d, e, f};
					k = contact ? HullContact.clip(body, k) : k;
					if (k != null) {
						out.add(k);
					}
				});
		return out;
	}

	/** How far the body moves along one axis (wanted: {@code want}) with the vanilla rule: colliders it overlaps are ignored. */
	private static double sweep(double[] body, List<double[]> boxes, int axis, double want) {
		double reach = want;
		int a1 = axis == 0 ? 1 : 0, a2 = axis == 2 ? 1 : 2;
		for (double[] k : boxes) {
			if (k[a1 + 3] - body[a1] <= 1e-7 || body[a1 + 3] - k[a1] <= 1e-7 || k[a2 + 3] - body[a2] <= 1e-7 || body[a2 + 3] - k[a2] <= 1e-7) {
				continue; // beside the path
			}
			if (want < 0 && body[axis] >= k[axis + 3] - 1e-7) {
				reach = Math.max(reach, k[axis + 3] - body[axis]);
			} else if (want > 0 && body[axis + 3] <= k[axis] + 1e-7) {
				reach = Math.min(reach, k[axis] - body[axis + 3]);
			}
		}
		return reach;
	}
}
