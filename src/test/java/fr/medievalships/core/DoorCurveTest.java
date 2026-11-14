package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The animation curve of the doors (1.32.0) in pure Java: the unlocking first, then the leaves (slow start,
 * acceleration, slowing down, settling past the stop at the end of an opening, a small bounce at the end of a
 * closing), the second leaf's delay, the gears following the leaves, a movement turning back without a jump, the
 * events of the sounds.
 */
class DoorCurveTest {
	private static final double EPS = 1e-9;
	private static final DoorType[] SIZES = {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE};

	@Test
	void durations() {
		assertEquals(12, DoorTypes.OAK.durationTicks());
		assertEquals(24, DoorTypes.FORTRESS.durationTicks());
		assertEquals(70, DoorTypes.CASTLE.durationTicks());
		for (DoorType t : DoorTypes.ALL) {
			DoorMotion.Curve c = DoorMotion.curve(t);
			assertTrue(c.unlock() > 0.1 && c.unlock() < 0.2, "about 15 % of the time unlocks: " + t);
			assertEquals(t.leaves() == 2, c.delay() > 0, "a second leaf starts later: " + t);
		}
	}

	@Test
	void boundsAndRest() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves();
			for (int leaf = 0; leaf < n; leaf++) {
				for (boolean opening : new boolean[] {true, false}) {
					assertEquals(0, DoorMotion.leaf(c, n, leaf, opening, 0), EPS, "closed at 0");
					assertEquals(1, DoorMotion.leaf(c, n, leaf, opening, 1), EPS, "open at 1");
					for (int i = 0; i <= 1000; i++) {
						double v = DoorMotion.leaf(c, n, leaf, opening, i / 1000.0);
						assertTrue(v >= -EPS, "never into the frame");
						assertTrue(v <= 1 + c.overshoot() + EPS, "at most a little past the stop");
					}
				}
			}
			assertEquals(0, DoorMotion.unlock(c, 0), EPS);
			assertEquals(1, DoorMotion.unlock(c, 1), EPS);
			assertEquals(0, DoorMotion.handle(c, 0), EPS);
			assertEquals(0, DoorMotion.handle(c, 1), EPS, "the handle is back at rest when the door is open");
		}
	}

	@Test
	void phasesUnlockThenLeaves() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves();
			// unlocking: the bolts slide, the handle turns, the leaves wait
			for (int i = 0; i <= 100; i++) {
				double t = c.unlock() * i / 100.0;
				for (int leaf = 0; leaf < n; leaf++) {
					assertEquals(0, DoorMotion.leaf(c, n, leaf, true, t), EPS, "leaves still while unlocking");
				}
			}
			assertEquals(1, DoorMotion.unlock(c, c.unlock()), EPS, "unlocked when the leaves start");
			assertTrue(DoorMotion.unlock(c, c.unlock() / 2) > 0.2 && DoorMotion.unlock(c, c.unlock() / 2) < 0.8);
			assertTrue(DoorMotion.handle(c, c.unlock() * 0.7) > 0.99, "the handle turned while unlocking");
			assertFalse(DoorMotion.leavesMoving(c, c.unlock() / 2));
			assertTrue(DoorMotion.leavesMoving(c, 0.5));
			// slow start, faster in the middle, slow end: the inertia of a heavy leaf (not linear)
			double s0 = DoorMotion.leafPhase(c, c.unlock() + 0.02), s1 = DoorMotion.leafPhase(c, 0.55);
			double early = DoorMotion.leaf(c, n, 0, true, c.unlock() + 0.04) - DoorMotion.leaf(c, n, 0, true, c.unlock() + 0.02);
			double middle = DoorMotion.leaf(c, n, 0, true, 0.57) - DoorMotion.leaf(c, n, 0, true, 0.55);
			assertTrue(s0 < s1);
			assertTrue(middle > 3 * early, "accelerates (" + early + " then " + middle + ")");
			assertTrue(middle > 0.02 / (1 - c.unlock()), "faster than linear in the middle");
		}
	}

	@Test
	void monotoneButTheSettlingAndTheBounce() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves();
			for (int leaf = 0; leaf < n; leaf++) {
				// opening: rises to its peak (a little past the stop), then only settles back down to 1
				double last = 0, peak = 0, peakT = 0;
				for (int i = 0; i <= 2000; i++) {
					double t = i / 2000.0, v = DoorMotion.leaf(c, n, leaf, true, t);
					if (v > peak) {
						peak = v;
						peakT = t;
					}
				}
				assertTrue(peak > 1 + c.overshoot() * 0.5, type + ": the opening leaf runs past its stop (" + peak + ")");
				for (int i = 0; i <= 2000; i++) {
					double t = i / 2000.0, v = DoorMotion.leaf(c, n, leaf, true, t);
					if (t <= peakT) {
						assertTrue(v >= last - EPS, type + " opening rises until its peak at " + t);
					} else {
						assertTrue(v <= last + EPS && v >= 1 - EPS, type + " then settles back to the stop at " + t);
					}
					last = v;
				}
				// closing (the progress going down): falls to the frame, bounces a little, rests
				last = 1;
				boolean hit = false;
				double bounce = 0;
				for (int i = 2000; i >= 0; i--) {
					double t = i / 2000.0, v = DoorMotion.leaf(c, n, leaf, false, t);
					if (DoorMotion.leafShare(c, n, leaf, DoorMotion.leafPhase(c, t)) <= c.pause()) {
						hit = true; // it reached the frame (between two samples)
					}
					if (!hit) {
						assertTrue(v <= last + EPS, type + " closing falls at " + t);
					} else {
						bounce = Math.max(bounce, v);
						assertTrue(v <= c.rebound() + EPS, "a small bounce only");
					}
					last = v;
				}
				assertTrue(hit && bounce > c.rebound() * 0.5, type + ": it hits the frame and bounces back a little (" + bounce + ")");
			}
		}
	}

	@Test
	void handlesTurnClockwiseWhileUnlocking() {
		for (DoorType t : DoorTypes.ALL) {
			DoorMotion.Curve c = DoorMotion.curve(t);
			double max = 0;
			for (int i = 0; i <= 1000; i++) {
				double a = DoorMotion.handleAngle(t, i / 1000.0);
				assertTrue(a <= EPS, "clockwise seen from the front (negative about +z): " + t);
				max = Math.max(max, -a);
			}
			if (t.steam()) {
				assertEquals(DoorMotion.WHEEL_ANGLE, max, 1e-6, "a steam door's wheel turns freely");
			} else {
				assertTrue(max <= 30 + EPS && max > 29, "a ring turns about 30° at most: " + max);
			}
			assertEquals(0, DoorMotion.handleAngle(t, 0), EPS);
			assertEquals(0, DoorMotion.handleAngle(t, 1), EPS);
			assertTrue(-DoorMotion.handleAngle(t, c.unlock()) > max * 0.99, "turned when the unlocking ends");
		}
	}

	@Test
	void theClosingLeafHitsTheFrameStillMoving() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.CASTLE);
		double u = c.pause() + 1e-4, v = DoorMotion.leafCurve(c, false, u);
		double speed = v / 1e-4 * (1 - c.pause()); // per unit of the stroke after the pause
		assertTrue(speed > 0.3, "a slam, not a soft stop: " + speed);
		double open = DoorMotion.leafCurve(c, true, u) / 1e-4 * (1 - c.pause());
		assertTrue(open < 0.01, "an opening starts softly: " + open);
	}

	@Test
	void theSecondLeafStartsLater() {
		for (DoorType type : new DoorType[] {DoorTypes.BARN, DoorTypes.CASTLE}) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			double firstStarts = -1, secondStarts = -1;
			for (int i = 0; i <= 1000; i++) {
				double t = i / 1000.0;
				if (firstStarts < 0 && DoorMotion.leaf(c, 2, 0, true, t) > 1e-6) {
					firstStarts = t;
				}
				if (secondStarts < 0 && DoorMotion.leaf(c, 2, 1, true, t) > 1e-6) {
					secondStarts = t;
				}
				assertTrue(DoorMotion.leaf(c, 2, 1, true, t) <= DoorMotion.leaf(c, 2, 0, true, t) + c.overshoot() + EPS);
			}
			assertTrue(secondStarts > firstStarts + 0.04, type + ": " + firstStarts + " then " + secondStarts);
			// closing, the second leaf shuts first and the first one laps over it
			double secondShut = -1, firstShut = -1;
			for (int i = 1000; i >= 0; i--) {
				double t = i / 1000.0;
				if (secondShut < 0 && DoorMotion.leafShare(c, 2, 1, DoorMotion.leafPhase(c, t)) <= c.pause()) {
					secondShut = t;
				}
				if (firstShut < 0 && DoorMotion.leafShare(c, 2, 0, DoorMotion.leafPhase(c, t)) <= c.pause()) {
					firstShut = t;
				}
			}
			assertTrue(secondShut > firstShut, type + ": the second leaf shuts first");
		}
		// one leaf: no delay
		DoorMotion.Curve s = DoorMotion.curve(DoorTypes.OAK);
		assertEquals(DoorMotion.leaf(s, 1, 0, true, 0.6), DoorMotion.leafCurve(s, true, DoorMotion.leafPhase(s, 0.6)), EPS);
	}

	@Test
	void theGearsFollowTheLeaves() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.GREAT_STEAM);
		double a0 = DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, c.unlock() + 0.01), 2) - DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, c.unlock()), 2);
		double a1 = DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 0.51), 2) - DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 0.5), 2);
		assertTrue(a1 > 5 * Math.max(a0, 1e-9), "faster when the leaves are faster (" + a0 + ", " + a1 + ")");
		assertEquals(0, DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 0.1), 2), EPS, "still while the door unlocks");
		assertEquals(720, DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 1), 2), EPS, "whole turns at rest");
	}

	@Test
	void turningBackHalfWayHasNoJump() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves(), d = type.durationTicks();
			for (double at : new double[] {0.2, 0.3, 0.5, 0.8, 0.95}) {
				for (boolean target : new boolean[] {true, false}) {
					for (int leaf = 0; leaf < n; leaf++) {
						// the movement towards !target reached {@code at}; it turns back towards target at tick 100
						double before = DoorMotion.leaf(c, n, leaf, !target, at);
						double after = DoorMotion.leafAt(c, n, leaf, target, 100, at, 100, d);
						assertEquals(before, after, 1e-9, type + " turning back at " + at);
						// and then it goes on smoothly (no step bigger than a regular one)
						double prev = after;
						for (int k = 1; k <= 40; k++) {
							double v = DoorMotion.leafAt(c, n, leaf, target, 100, at, 100 + k * 0.25, d);
							assertTrue(Math.abs(v - prev) < 0.06, type + " smooth after turning back at " + at + ": " + prev + " -> " + v);
							prev = v;
						}
					}
				}
			}
		}
	}

	@Test
	void eventsOfTheSounds() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.CASTLE);
		int d = DoorTypes.CASTLE.durationTicks();
		int starts = 0, opened = 0, creaks = 0;
		for (int k = 1; k <= d + 2; k++) {
			double prev = DoorMotion.progress(true, 0, 0, k - 1, d), t = DoorMotion.progress(true, 0, 0, k, d);
			int e = DoorMotion.events(c, 2, true, prev, t, k);
			starts += (e & DoorMotion.EV_LEAVES_START) != 0 ? 1 : 0;
			opened += (e & DoorMotion.EV_OPENED) != 0 ? 1 : 0;
			creaks += (e & DoorMotion.EV_CREAK) != 0 ? 1 : 0;
			assertEquals(0, e & (DoorMotion.EV_IMPACT | DoorMotion.EV_LOCKED), "no closing event while opening");
		}
		assertEquals(1, starts, "the leaves start once");
		assertEquals(1, opened);
		assertTrue(creaks >= 2 && creaks <= 5, "a few spaced creaks: " + creaks);
		int impacts = 0, second = 0, locked = 0;
		for (int k = 1; k <= d + 2; k++) {
			double prev = DoorMotion.progress(false, 0, 1, k - 1, d), t = DoorMotion.progress(false, 0, 1, k, d);
			int e = DoorMotion.events(c, 2, false, prev, t, k);
			impacts += (e & DoorMotion.EV_IMPACT) != 0 ? 1 : 0;
			second += (e & DoorMotion.EV_SECOND_IMPACT) != 0 ? 1 : 0;
			locked += (e & DoorMotion.EV_LOCKED) != 0 ? 1 : 0;
		}
		assertEquals(1, impacts);
		assertEquals(1, second);
		assertEquals(1, locked);
		// a small door never creaks
		DoorMotion.Curve s = DoorMotion.curve(DoorTypes.OAK);
		for (int k = 1; k <= 12; k++) {
			assertEquals(0, DoorMotion.events(s, 1, true, (k - 1) / 12.0, k / 12.0, k) & DoorMotion.EV_CREAK);
		}
	}
}
