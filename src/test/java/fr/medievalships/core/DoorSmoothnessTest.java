package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.SplittableRandom;

import org.junit.jupiter.api.Test;

/**
 * The smoothness of the doors as a client draws them (1.33.0), in pure Java: the clock ({@link DoorClock}) that follows
 * the server's time without the jumps of its time packets, and the track ({@link DoorTrack}) that fades a new movement
 * in from what was drawn (no jump when a packet arrives, no flip when a door turns back). The client is simulated
 * frame by frame (60 frames per second, 20 ticks per second), the server's time sent every 20 of its ticks.
 */
class DoorSmoothnessTest {
	/** A simulated client: its world's time (set again by the server's time packets) and the door clock. */
	static final class Client {
		long worldTime;
		final DoorClock clock = new DoorClock();

		void tick() {
			worldTime++;
			clock.tick(worldTime);
		}
	}

	@Test
	void theClockIsTheWorldsTimeWhenNothingJumps() {
		Client c = new Client();
		c.worldTime = 5000;
		assertFalse(c.clock.started());
		c.tick();
		assertTrue(c.clock.started());
		for (int k = 0; k < 200; k++) {
			for (double f : new double[] {0, 0.25, 0.5, 0.999}) {
				assertEquals(c.worldTime + f, c.clock.now(f), 1e-9);
			}
			c.tick();
		}
	}

	/**
	 * A server slower than the client (15 ticks a second): the world's time jumps back every second; the clock never
	 * goes back, keeps a steady pace (0.7 to 1.3 times) and stays close to the server.
	 */
	@Test
	void aSlowServerNeverMakesTheClockJumpBack() {
		run(15.0, 0, 7);
	}

	/** A faster server (a catching up after a lag: 25 ticks a second) makes the world's time jump forth. */
	@Test
	void aFastServerNeverMakesTheClockJumpForth() {
		run(25.0, 0, 7);
	}

	/** The packets arrive a tick early or late at random: the clock follows smoothly. */
	@Test
	void jitteryPacketsAreSmoothedOut() {
		run(20.0, 1, 3);
	}

	/**
	 * Simulates a minute of a server at {@code tps} ticks a second sending its time every 20 of its ticks (arriving
	 * 0.02 s later, give or take {@code jitter} ticks at random) and of a client at 20 ticks and 60 frames a second, the
	 * events in their order; checks the clock frame by frame.
	 */
	private static void run(double tps, int jitter, double maxGap) {
		Client c = new Client();
		SplittableRandom random = new SplittableRandom(7);
		double s0 = 1000;
		c.worldTime = 1000;
		int nextTick = 1; // the client's tick k comes at k / 20 s
		long nextPacket = 1020; // the server's time it sends next
		double nextPacketAt = (nextPacket - s0) / tps + 0.02 + jitter * 0.05 * (random.nextDouble() * 2 - 1);
		double lastNow = Double.NaN, lastRaw = Double.NaN;
		int rawJumps = 0;
		double minPace = 9, maxPace = 0, maxGapSeen = 0;
		for (int frame = 0; frame < 60 * 60; frame++) {
			double tf = frame / 60.0;
			while (true) {
				double tTick = nextTick / 20.0;
				if (Math.min(tTick, nextPacketAt) > tf) {
					break;
				}
				if (nextPacketAt <= tTick) {
					c.worldTime = nextPacket; // the server's time packet
					nextPacket += 20;
					nextPacketAt = (nextPacket - s0) / tps + 0.02 + jitter * 0.05 * (random.nextDouble() * 2 - 1);
				} else {
					c.tick();
					nextTick++;
				}
			}
			double f = (tf - (nextTick - 1) / 20.0) * 20;
			double now = c.clock.now(f), raw = c.worldTime + f;
			if (!Double.isNaN(lastNow)) {
				assertTrue(now >= lastNow - 1e-9, "never back: " + lastNow + " -> " + now);
				if (frame > 120) {
					double pace = (now - lastNow) * 3; // ticks of the clock per tick of the client (a frame is a third of a tick)
					minPace = Math.min(minPace, pace);
					maxPace = Math.max(maxPace, pace);
					maxGapSeen = Math.max(maxGapSeen, Math.abs(now - (s0 + (tf - 0.02) * tps)));
				}
				rawJumps += raw < lastRaw - 1e-9 || raw > lastRaw + 1 ? 1 : 0;
			}
			lastNow = now;
			lastRaw = raw;
		}
		assertTrue(minPace >= 0.69 && maxPace <= 1.31, "a steady pace: " + minPace + " .. " + maxPace);
		assertTrue(maxGapSeen <= maxGap, "close to the server: " + maxGapSeen);
		assertTrue(rawJumps > 0, "the world's time itself does jump (" + rawJumps + " times)");
	}

	@Test
	void aBigGapIsTakenAtOnce() {
		Client c = new Client();
		c.worldTime = 100;
		c.tick();
		c.worldTime = 100000; // another world, a long freeze
		c.tick();
		assertEquals(100001, c.clock.now(0), 1e-9);
		c.clock.reset();
		assertFalse(c.clock.started());
	}

	@Test
	void theClockIsContinuousAcrossTicks() {
		Client c = new Client();
		c.worldTime = 0;
		c.tick();
		for (int k = 0; k < 100; k++) {
			if (k % 20 == 10) {
				c.worldTime += 3; // a jump forth
			}
			double before = c.clock.now(1.0);
			c.tick();
			assertEquals(before, c.clock.now(0.0), 1e-9, "no step at a tick");
		}
	}

	// ------------------------------------------------------------------ the track

	/** The largest step of a channel between two frames of {@code dt} ticks around a change at {@code at}. */
	private static double[] follow(DoorTrack track, DoorType type, double from, double to, double dt, Object[][] movements) {
		double[] maxStep = new double[DoorTrack.CHANNELS];
		double[] last = null;
		for (double now = from; now <= to; now += dt) {
			Object[] m = movements[0];
			for (Object[] mm : movements) {
				if (now >= (Double) mm[3]) {
					m = mm;
				}
			}
			track.update(type, (Boolean) m[0], (Long) m[1], (Double) m[2], now);
			for (int i = 0; i < 2; i++) {
				assertTrue(track.pose[i] >= -1e-9 && track.pose[i] <= 1 + 1e-9, "a leaf between closed and open: " + track.pose[i]);
			}
			if (last != null) {
				for (int i = 0; i < DoorTrack.CHANNELS; i++) {
					maxStep[i] = Math.max(maxStep[i], Math.abs(track.pose[i] - last[i]));
				}
			}
			last = track.pose.clone();
		}
		return maxStep;
	}

	@Test
	void withoutAChangeTheTrackIsTheServersTimeline() {
		DoorType type = DoorTypes.CASTLE;
		DoorTrack track = new DoorTrack();
		double[] raw = new double[DoorTrack.CHANNELS];
		for (double now = 0; now <= 100; now += 0.37) {
			track.update(type, true, 10, 0, now);
			DoorTrack.raw(type, true, 10, 0, now, raw);
			for (int i = 0; i < DoorTrack.CHANNELS; i++) {
				assertEquals(raw[i], track.pose[i], 1e-12);
			}
			assertEquals(DoorMotion.moving(true, DoorMotion.progress(true, 10, 0, now, type.durationTicks())), track.moving);
		}
	}

	@Test
	void aPacketThatDoesNotChangeTheMovementChangesNothing() {
		DoorType type = DoorTypes.BARN;
		DoorTrack track = new DoorTrack();
		track.update(type, true, 0, 0, 10);
		double[] a = track.pose.clone();
		track.update(type, true, 0, 0, 10); // the same movement again (a setting, a name)
		for (int i = 0; i < DoorTrack.CHANNELS; i++) {
			assertEquals(a[i], track.pose[i], 1e-12);
		}
		assertFalse(track.fading(10));
	}

	/** A door starts while this client's clock is 2 ticks ahead of the server's: no jump of the handles or bolts. */
	@Test
	void aMovementArrivingLateFadesInWithoutAJump() {
		for (DoorType type : new DoorType[] {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE}) {
			DoorTrack track = new DoorTrack();
			double dt = 1 / 3.0;
			// closed for a while; the opening started at tick 100, seen at 102 by a client ahead
			double[] steps = follow(track, type, 90, 102 + type.durationTicks(), dt,
					new Object[][] {{false, -1000L, 0.0, 0.0}, {true, 100L, 0.0, 102.0}});
			double[] raw = new double[DoorTrack.CHANNELS];
			double worst = 0;
			for (double now = 100; now + dt <= 100 + type.durationTicks(); now += dt) {
				double[] a = new double[DoorTrack.CHANNELS];
				DoorTrack.raw(type, true, 100, 0, now, a);
				DoorTrack.raw(type, true, 100, 0, now + dt, raw);
				worst = Math.max(worst, Math.abs(raw[DoorTrack.BOLTS] - a[DoorTrack.BOLTS]));
			}
			assertTrue(steps[DoorTrack.BOLTS] <= worst * 1.6 + 1e-9, type + ": the bolts step no more than their own pace (" + steps[DoorTrack.BOLTS]
					+ " vs " + worst + ")");
			assertTrue(steps[DoorTrack.HANDLE] <= 12, type + ": the handle turns smoothly (" + steps[DoorTrack.HANDLE] + "° per frame)");
		}
	}

	/** Turning back half way (the server goes on from where the leaves are): no jump, and the leaf slows down, then comes back. */
	@Test
	void turningBackHasNoJumpNorFlip() {
		for (DoorType type : new DoorType[] {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE}) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int d = type.durationTicks();
			long back = d / 2;
			double p = DoorMotion.turnBack(c, type.leaves(), false, DoorMotion.progress(true, 0, 0, back, d));
			for (double ahead : new double[] {0, 1.5, -1.5}) {
				DoorTrack track = new DoorTrack();
				double dt = 1 / 3.0;
				Object[][] moves = {{true, 0L, 0.0, -10.0}, {false, back, p, back + ahead}};
				double[] steps = follow(track, type, -2, back + d + 4, dt, moves);
				// a normal closing's largest move in any frame (a third of a tick), as a yardstick: turning back may be a
				// little quicker while the leaf gives back what it ran on (a quarter of its speed at most), never a jump
				double own = 0;
				double[] ra = new double[DoorTrack.CHANNELS], rb = new double[DoorTrack.CHANNELS];
				for (double now = 0; now <= d; now += 0.01) {
					DoorTrack.raw(type, false, 0, 1, now, ra);
					DoorTrack.raw(type, false, 0, 1, now + dt, rb);
					own = Math.max(own, Math.abs(rb[0] - ra[0]));
				}
				// with exact clocks, at most a little quicker; with a client 1.5 tick off, the gap it must make up is faded in
				// (drawn straight from the server's movement, the leaf would jump it in one frame)
				double bound = ahead == 0 ? 1.6 : 2.5;
				assertTrue(steps[DoorTrack.LEAF_L] <= own * bound, type + " ahead " + ahead + ": no jump (" + steps[DoorTrack.LEAF_L] + " vs " + own + ")");
				if (ahead != 0) {
					double[] o = new double[DoorTrack.CHANNELS], q = new double[DoorTrack.CHANNELS];
					DoorTrack.raw(type, true, 0, 0, back + ahead - dt, o);
					DoorTrack.raw(type, false, back, p, back + ahead, q);
					assertTrue(Math.abs(q[0] - o[0]) > 1.5 * steps[DoorTrack.LEAF_L], type + ": without the track it would jump (" + Math.abs(q[0] - o[0])
							+ " in one frame, the track's largest step " + steps[DoorTrack.LEAF_L] + ")");
				}
				// the leaf's speed just before and just after the change are the same: it slows down and turns back
				DoorTrack t2 = new DoorTrack();
				double at = back + ahead;
				double h = 0.05;
				t2.update(type, true, 0, 0, at - 2 * h);
				double a0 = t2.pose[0];
				t2.update(type, true, 0, 0, at - h);
				double a1 = t2.pose[0];
				t2.update(type, false, back, p, at);
				double a2 = t2.pose[0];
				t2.update(type, false, back, p, at + h);
				double a3 = t2.pose[0];
				double before = (a1 - a0) / h, after = (a3 - a2) / h, across = (a2 - a1) / h;
				assertTrue(Math.abs(across - before) < 0.02 && Math.abs(after - before) < 0.03, type + " ahead " + ahead + ": the speed goes on (" + before
						+ ", " + across + ", " + after + ")");
				// at the end, exactly the server's pose, at rest
				track.update(type, false, back, p, back + d + 20);
				assertEquals(0, track.pose[0], 1e-12);
				assertFalse(track.moving);
			}
		}
	}
}
