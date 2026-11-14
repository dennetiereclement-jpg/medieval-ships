package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The animation curve of the doors (1.33.0) in pure Java: the unlocking first, then the leaves (a push, then a glide
 * to a cushioned stop: never past it), closing a soft start, a speed growing up to the slam and a tiny damped bounce,
 * the rings rattling, the locking; the second leaf's delay, the gears following the leaves, a movement turning back
 * without a jump nor a rush, the events of the sounds on the curve.
 */
class DoorCurveTest {
	private static final double EPS = 1e-9;
	private static final DoorType[] SIZES = {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE};

	/** The speed (opening per tick) of a leaf at a progress, opening or closing (signed). */
	private static double speed(DoorType type, int leaf, boolean target, double t) {
		DoorMotion.Curve c = DoorMotion.curve(type);
		double h = 1e-4;
		double a = DoorMotion.leaf(c, type.leaves(), leaf, target, Math.max(0, t - h)), b = DoorMotion.leaf(c, type.leaves(), leaf, target, Math.min(1, t + h));
		// the progress goes up opening, down closing: per tick of the movement
		return (target ? b - a : a - b) / (Math.min(1, t + h) - Math.max(0, t - h)) / type.durationTicks();
	}

	@Test
	void durationsAndShapes() {
		assertEquals(16, DoorTypes.OAK.durationTicks());
		assertEquals(28, DoorTypes.FORTRESS.durationTicks());
		assertEquals(80, DoorTypes.CASTLE.durationTicks());
		for (DoorType t : DoorTypes.ALL) {
			DoorMotion.Curve c = DoorMotion.curve(t);
			assertTrue(c.unlock() > 0.08 && c.unlock() < 0.22, "the unlocking takes a small share of the time: " + t);
			assertEquals(t.leaves() == 2, c.delay() > 0, "a second leaf starts later: " + t);
			assertTrue(c.pushFall() >= 2, "the speed comes down to zero at the stop without a shock: " + t);
		}
		// the heavier, the longer: the leaves of a great gate take five times as long as a small door's
		assertTrue(DoorTypes.CASTLE.durationTicks() >= 4.5 * DoorTypes.OAK.durationTicks());
		assertThrows(IllegalArgumentException.class, () -> new DoorMotion.Curve(0.1, 0, 1, 2, 1.2, 0.1, 0.02, 0, 0), "it must gain speed up to the frame");
		assertThrows(IllegalArgumentException.class, () -> new DoorMotion.Curve(0.1, 0, 1, 0, 2, 0.1, 0.02, 0, 0), "no shock at the stop");
	}

	@Test
	void thePushIsTheIncompleteBetaFunction() {
		for (int i = 0; i <= 100; i++) {
			double x = i / 100.0;
			assertEquals(6 * x * x - 8 * x * x * x + 3 * x * x * x * x, DoorMotion.push(1, 2, x), 1e-12);
		}
		for (int[] ab : new int[][] {{1, 2}, {1, 3}, {2, 4}}) {
			// its speed integrates to it, from 0 to 1
			double sum = 0;
			int n = 20000;
			for (int i = 0; i < n; i++) {
				sum += DoorMotion.pushSpeed(ab[0], ab[1], (i + 0.5) / n) / n;
				if (i % 1000 == 999) {
					assertEquals(DoorMotion.push(ab[0], ab[1], (i + 1.0) / n), sum, 1e-6);
				}
			}
			assertEquals(1, sum, 1e-6);
			assertEquals(0, DoorMotion.push(ab[0], ab[1], 0), EPS);
			assertEquals(1, DoorMotion.push(ab[0], ab[1], 1), EPS);
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
					for (int i = 0; i <= 2000; i++) {
						double v = DoorMotion.leaf(c, n, leaf, opening, i / 2000.0);
						assertTrue(v >= -EPS, "never into the frame");
						assertTrue(v <= 1 + EPS, "never past the stop (no overshoot that looks like a bug): " + v);
					}
				}
			}
			for (boolean target : new boolean[] {true, false}) {
				assertEquals(0, DoorMotion.unlock(c, target, 0), EPS);
				assertEquals(1, DoorMotion.unlock(c, target, 1), EPS);
				assertEquals(0, DoorMotion.handle(c, target, 0), EPS);
				assertEquals(0, DoorMotion.handle(c, target, 1), EPS, "the handle is back at rest at both ends");
			}
		}
	}

	@Test
	void openingUnlocksThenPushesThenGlidesToACushionedStop() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves();
			// unlocking: the handle turns, then the bolts slide, the leaves wait
			for (int i = 0; i <= 100; i++) {
				double t = c.unlock() * i / 100.0;
				for (int leaf = 0; leaf < n; leaf++) {
					assertEquals(0, DoorMotion.leaf(c, n, leaf, true, t), EPS, "leaves still while unlocking");
				}
			}
			assertEquals(1, DoorMotion.handle(c, true, c.unlock() * DoorMotion.HANDLE_UP), EPS, "the handle is turned first");
			assertEquals(0, DoorMotion.unlock(c, true, c.unlock() * DoorMotion.BOLTS_FROM), EPS, "the bolts wait for the handle");
			assertEquals(1, DoorMotion.unlock(c, true, c.unlock() * DoorMotion.BOLTS_OUT), EPS, "the bolts are out before the leaves start");
			assertFalse(DoorMotion.leavesMoving(c, c.unlock() / 2));
			assertTrue(DoorMotion.leavesMoving(c, 0.5));
			// the first leaf: from rest, its speed rises quickly (the push), peaks early, then falls slowly (the glide)
			// and comes down to zero at the stop (cushioned), the opening only ever rising
			double peak = 0, peakAt = 0, last = 0;
			double start = c.unlock(), end = c.unlock() + (1 - c.unlock()) * (n > 1 ? 1 - c.delay() : 1);
			for (int i = 0; i <= 1000; i++) {
				double t = start + (end - start) * i / 1000.0;
				double v = DoorMotion.leaf(c, n, 0, true, t);
				assertTrue(v >= last - EPS, type + ": the opening only rises");
				last = v;
				double sp = speed(type, 0, true, t);
				if (sp > peak) {
					peak = sp;
					peakAt = i / 1000.0;
				}
			}
			assertTrue(peakAt > 0.15 && peakAt < 0.45, type + ": the speed peaks early in the stroke (" + peakAt + ")");
			assertTrue(speed(type, 0, true, start + (end - start) * 0.985) < 0.03 * peak, type + ": cushioned at the stop");
			assertTrue(speed(type, 0, true, start + (end - start) * 0.75) > 0.08 * peak, type + ": still gliding at three quarters");
			assertTrue(speed(type, 0, true, start + 1e-3) < 0.05 * peak, type + ": it starts from rest");
		}
		// the heavier, the slower it gets going (in shares of its own peak speed) and the longer it glides from its peak
		// speed to the stop (in ticks)
		double[] early = new double[3], glide = new double[3];
		for (int i = 0; i < 3; i++) {
			DoorMotion.Curve c = DoorMotion.curve(SIZES[i]);
			double peakAt = c.pushRise() / (double) (c.pushRise() + c.pushFall());
			early[i] = DoorMotion.pushSpeed(c.pushRise(), c.pushFall(), 0.05) / DoorMotion.pushSpeed(c.pushRise(), c.pushFall(), peakAt);
			glide[i] = (1 - peakAt) * (1 - c.unlock()) * (1 - c.delay()) * SIZES[i].durationTicks();
		}
		assertTrue(early[2] < early[1] && early[1] <= early[0], "the great gate gets going the most slowly: " + java.util.Arrays.toString(early));
		assertTrue(glide[2] > 2 * glide[1] && glide[1] > glide[0], "and glides the longest (ticks): " + java.util.Arrays.toString(glide));
	}

	@Test
	void closingStartsSoftlySlamsAndBouncesATinyDampedBounce() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves();
			for (int leaf = 0; leaf < n; leaf++) {
				// the time runs with the progress going down; the leaf's own stroke u from 1 (open) to 0
				double lastSpeed = 0, last = 1, hitAt = -1;
				int arcs = 0;
				boolean rising = false;
				double highest = 0, second = 0;
				for (int i = 2000; i >= 0; i--) {
					double t = i / 2000.0, v = DoorMotion.leaf(c, n, leaf, false, t);
					double u = DoorMotion.leafShare(c, n, leaf, DoorMotion.leafPhase(c, t));
					assertTrue(v >= -EPS, "never into the frame");
					if (hitAt < 0 && u > c.bounce()) {
						assertTrue(v <= last + EPS, type + " closing only falls until the slam (" + t + ")");
						if (u < 1 - 1e-3 && u > c.bounce() + 1e-3) {
							double sp = -speed(type, leaf, false, t);
							assertTrue(sp >= lastSpeed - 1e-6, type + " it keeps gaining speed up to the frame (" + t + ")");
							lastSpeed = sp;
						}
					} else if (hitAt < 0) {
						hitAt = t;
					} else {
						// the bounces: arcs off the frame, each lower than the last, then rest
						if (v > last + EPS && !rising) {
							rising = true;
							arcs++;
						} else if (v < last - EPS) {
							rising = false;
						}
						if (arcs == 1) {
							highest = Math.max(highest, v);
						} else if (arcs == 2) {
							second = Math.max(second, v);
						}
					}
					last = v;
				}
				assertTrue(hitAt > 0, type + ": it hits the frame");
				assertEquals(2, arcs, type + ": one small bounce and a tinier one, nothing that trembles");
				assertTrue(highest <= c.rebound() + EPS && highest > 0.9 * c.rebound(), type + ": a bounce of " + highest);
				assertTrue(c.rebound() * 90 <= 2.5, "a very small bounce (degrees): " + c.rebound() * 90);
				assertTrue(second < 0.2 * highest && second > 0, type + ": damped (" + second + " after " + highest + ")");
				// the slam: the speed at the frame is the highest of the closing, well above its mean
				double mean = 1 / ((1 - c.bounce()) * (1 - c.unlock()) * (n > 1 ? 1 - c.delay() : 1) * type.durationTicks());
				assertTrue(lastSpeed > 1.4 * mean, type + ": a slam (" + lastSpeed + " vs a mean of " + mean + ")");
			}
			// a soft start: the leaf that starts first leaves the open stop with no speed
			double t0 = 1 - 1e-3;
			assertTrue(-speed(type, n - 1, false, t0) < 0.02, type + ": a soft start");
			// at rest, then the locking: the handle turns, the bolts slide back in
			for (int leaf = 0; leaf < n; leaf++) {
				assertEquals(0, DoorMotion.leaf(c, n, leaf, false, c.unlock()), EPS, "the leaves rest before the locking");
			}
			assertEquals(1, DoorMotion.unlock(c, false, c.unlock()), EPS, "the bolts still out when the leaves rest");
			assertEquals(1, DoorMotion.handle(c, false, c.unlock() * (1 - DoorMotion.LOCK_TURNED)), EPS, "the handle turned to lock");
			assertEquals(0, DoorMotion.unlock(c, false, c.unlock() * (1 - DoorMotion.LOCK_BOLTS_IN)), EPS, "the bolts back in");
		}
	}

	@Test
	void theRingsRattleAtTheSlamAndSettle() {
		for (DoorType t : DoorTypes.ALL) {
			DoorMotion.Curve c = DoorMotion.curve(t);
			double max = 0, slam = DoorMotion.impactProgress(c, t.leaves());
			boolean both = false;
			double min = 0;
			for (int i = 0; i <= 4000; i++) {
				double p = i / 4000.0;
				double j = DoorMotion.jiggle(c, t.leaves(), false, p);
				assertEquals(0, DoorMotion.jiggle(c, t.leaves(), true, p), EPS, "no rattle opening");
				if (p > slam + 1e-9 || p < c.unlock() - 1e-9) {
					assertEquals(0, j, 1e-9, t + ": a rattle only after the slam, before the locking (" + p + ")");
				}
				max = Math.max(max, j);
				min = Math.min(min, j);
			}
			both = max > 0 && min < 0;
			assertTrue(max <= c.jiggle() + EPS, "a few degrees: " + max);
			assertTrue(both, t + ": the ring rattles both ways");
			// a steam door's wheel does not rattle
			for (int i = 0; i <= 400; i++) {
				double p = i / 400.0;
				double a = DoorMotion.handleAngle(t, false, p) + (t.steam() ? DoorMotion.WHEEL_ANGLE : DoorMotion.HANDLE_ANGLE) * DoorMotion.handle(c, false, p);
				if (t.steam()) {
					assertEquals(0, a, 1e-9, "the wheel only turns with the locking");
				}
			}
		}
	}

	@Test
	void handlesTurnClockwiseWhileUnlocking() {
		for (DoorType t : DoorTypes.ALL) {
			DoorMotion.Curve c = DoorMotion.curve(t);
			double max = 0;
			for (int i = 0; i <= 1000; i++) {
				double a = DoorMotion.handleAngle(t, true, i / 1000.0);
				assertTrue(a <= EPS, "clockwise seen from the front (negative about +z): " + t);
				max = Math.max(max, -a);
			}
			if (t.steam()) {
				assertEquals(DoorMotion.WHEEL_ANGLE, max, 1e-6, "a steam door's wheel turns freely");
			} else {
				assertTrue(max <= 30 + EPS && max > 29, "a ring turns about 30° at most: " + max);
			}
			for (boolean target : new boolean[] {true, false}) {
				assertEquals(0, DoorMotion.handleAngle(t, target, 0), EPS);
				assertEquals(0, DoorMotion.handleAngle(t, target, 1), EPS);
			}
			assertTrue(-DoorMotion.handleAngle(t, true, c.unlock()) > max * 0.99, "turned when the unlocking ends");
		}
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
				assertTrue(DoorMotion.leaf(c, 2, 1, true, t) <= DoorMotion.leaf(c, 2, 0, true, t) + EPS);
			}
			assertTrue(secondStarts > firstStarts + 0.04, type + ": " + firstStarts + " then " + secondStarts);
			// closing, the second leaf shuts first and the first one laps over it
			double secondShut = -1, firstShut = -1;
			for (int i = 1000; i >= 0; i--) {
				double t = i / 1000.0;
				if (secondShut < 0 && DoorMotion.leafShare(c, 2, 1, DoorMotion.leafPhase(c, t)) <= c.bounce()) {
					secondShut = t;
				}
				if (firstShut < 0 && DoorMotion.leafShare(c, 2, 0, DoorMotion.leafPhase(c, t)) <= c.bounce()) {
					firstShut = t;
				}
			}
			assertTrue(secondShut > firstShut, type + ": the second leaf shuts first");
			assertEquals(DoorMotion.impactProgress(c, 2), firstShut, 2e-3, "the last slam");
		}
		// one leaf: no delay
		DoorMotion.Curve s = DoorMotion.curve(DoorTypes.OAK);
		assertEquals(DoorMotion.leaf(s, 1, 0, true, 0.6), DoorMotion.leafCurve(s, true, DoorMotion.leafPhase(s, 0.6)), EPS);
	}

	@Test
	void theGearsFollowTheLeaves() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.GREAT_STEAM);
		double t0 = c.unlock() + 0.01, tm = 0.45;
		double a0 = DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, t0 + 0.01), 2) - DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, t0), 2);
		double a1 = DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, tm + 0.01), 2) - DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, tm), 2);
		assertTrue(a1 > 5 * Math.max(a0, 1e-9), "faster when the leaves are faster (" + a0 + ", " + a1 + ")");
		assertEquals(0, DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 0.1), 2), EPS, "still while the door unlocks");
		assertEquals(720, DoorMotion.gearAngle(DoorMotion.leaf(c, 2, 0, true, 1), 2), EPS, "whole turns at rest");
	}

	@Test
	void turningBackHalfWayGoesOnFromWhereTheLeavesAreWithoutARush() {
		for (DoorType type : SIZES) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int n = type.leaves(), d = type.durationTicks();
			// the most a normal movement moves the leaves (on average) in any one tick, either way
			double fastest = 0;
			for (int k = 0; k <= 1000; k++) {
				double a = k / 1000.0, b = Math.min(1, a + 1.0 / d);
				for (boolean target : new boolean[] {true, false}) {
					fastest = Math.max(fastest, Math.abs(DoorMotion.meanLeaf(c, n, target, b) - DoorMotion.meanLeaf(c, n, target, a)));
				}
			}
			for (double at : new double[] {0.05, 0.2, 0.3, 0.5, 0.8, 0.95}) {
				for (boolean target : new boolean[] {true, false}) {
					// the movement towards !target reached {@code at}; it turns back towards target
					double p = DoorMotion.turnBack(c, n, target, at);
					assertTrue(p >= 0 && p <= 1);
					if (at <= c.unlock()) {
						assertEquals(at, p, EPS, "unlocking or locking: the progress is kept");
					}
					double before = DoorMotion.meanLeaf(c, n, !target, at), after = DoorMotion.meanLeaf(c, n, target, p);
					assertEquals(before, after, Math.max(2e-3, c.rebound() * 1.01), type + " turning back at " + at + ": the leaves go on from where they are");
					// and then it goes on at the pace of a normal movement (no rush)
					double prev = DoorMotion.meanLeaf(c, n, target, p);
					for (int k = 1; k <= d; k++) {
						double v = DoorMotion.meanLeaf(c, n, target, DoorMotion.progress(target, 0, p, k, d));
						assertTrue(Math.abs(v - prev) <= fastest + 1e-9, type + " no rush after turning back at " + at + ": " + prev + " -> " + v);
						prev = v;
					}
				}
			}
		}
	}

	@Test
	void eventsOfTheSoundsOnTheCurve() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.CASTLE);
		int d = DoorTypes.CASTLE.durationTicks();
		int unlatch = -1, start = -1, opened = -1, lastCreak = -100;
		int creaks = 0;
		for (int k = 1; k <= d + 2; k++) {
			double prev = DoorMotion.progress(true, 0, 0, k - 1, d), t = DoorMotion.progress(true, 0, 0, k, d);
			int e = DoorMotion.events(c, 2, true, prev, t);
			unlatch = (e & DoorMotion.EV_UNLATCH) != 0 ? k : unlatch;
			start = (e & DoorMotion.EV_LEAVES_START) != 0 ? k : start;
			opened = (e & DoorMotion.EV_OPENED) != 0 ? k : opened;
			if ((e & DoorMotion.EV_CREAK) != 0) {
				creaks++;
				assertTrue(k - lastCreak >= 8, "spaced creaks (" + lastCreak + ", " + k + ")");
				lastCreak = k;
			}
			assertEquals(0, e & (DoorMotion.EV_IMPACT | DoorMotion.EV_LOCKED | DoorMotion.EV_LATCHED), "no closing event while opening");
			if ((e & DoorMotion.EV_LEAVES_START) != 0) {
				assertTrue(DoorMotion.leaf(c, 2, 0, true, prev) == 0 && DoorMotion.leaf(c, 2, 0, true, t) > 0, "heard as the first leaf leaves the frame");
			}
		}
		assertTrue(unlatch > 0 && start > unlatch, "the latch clicks, then the leaves start (" + unlatch + ", " + start + ")");
		assertEquals(d, opened, "fully open at the end");
		assertEquals(c.creaks(), creaks, "the creaks along the stroke");
		int impact = -1, second = -1, latched = -1, locked = -1;
		creaks = 0;
		for (int k = 1; k <= d + 2; k++) {
			double prev = DoorMotion.progress(false, 0, 1, k - 1, d), t = DoorMotion.progress(false, 0, 1, k, d);
			int e = DoorMotion.events(c, 2, false, prev, t);
			impact = (e & DoorMotion.EV_IMPACT) != 0 ? k : impact;
			second = (e & DoorMotion.EV_SECOND_IMPACT) != 0 ? k : second;
			latched = (e & DoorMotion.EV_LATCHED) != 0 ? k : latched;
			locked = (e & DoorMotion.EV_LOCKED) != 0 ? k : locked;
			creaks += (e & DoorMotion.EV_CREAK) != 0 ? 1 : 0;
			if ((e & DoorMotion.EV_CREAK) != 0) {
				assertTrue(t > DoorMotion.impactProgress(c, 2) + 0.05, "never a creak on the slam");
			}
			if ((e & DoorMotion.EV_IMPACT) != 0) {
				// the slam is heard on the tick the leaf reaches the frame
				assertTrue(prev > DoorMotion.impactProgress(c, 2) && t <= DoorMotion.impactProgress(c, 2));
			}
		}
		assertTrue(second > 0 && impact > second, "the second leaf shuts first, then the slam (" + second + ", " + impact + ")");
		assertTrue(latched > impact && locked > latched, "the latch once the bounce is over, then the bolts (" + latched + ", " + locked + ")");
		assertTrue(locked < d, "the bolts clack before the end of the locking");
		assertEquals(c.creaks(), creaks);
		// a small door never creaks and has one slam
		DoorMotion.Curve s = DoorMotion.curve(DoorTypes.OAK);
		int slams = 0;
		for (int k = 1; k <= 16; k++) {
			assertEquals(0, DoorMotion.events(s, 1, true, (k - 1) / 16.0, k / 16.0) & DoorMotion.EV_CREAK);
			int e = DoorMotion.events(s, 1, false, 1 - (k - 1) / 16.0, 1 - k / 16.0);
			slams += (e & DoorMotion.EV_IMPACT) != 0 ? 1 : 0;
			assertEquals(0, e & DoorMotion.EV_SECOND_IMPACT);
		}
		assertEquals(1, slams);
	}
}
