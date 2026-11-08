package fr.medievalships.core.bridge;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

/** The gauge decision and the automatic cycle. */
class GaugeAndCycleTest {
	// ---- gauge: water at 62, deck underside at 66 (free height 4), channel 10 wide

	private static Gauge.Envelope vessel(String label, double topAboveWater, double halfAcross) {
		return new Gauge.Envelope(0, 62, 0, 62 + topAboveWater, 5, halfAcross, 6, label, "mesuré");
	}

	@Test
	void rowboatPassesGalleyOpensWideShipWaits() {
		Gauge.Decision barque = Gauge.decide(vessel("barque", 1.0, 1.0), 66, 62, 0.5, 5);
		assertEquals(Gauge.Verdict.PASSE_DESSOUS, barque.verdict());
		assertEquals(4, barque.freeHeight(), 1e-9);
		// the same rowboat with a standing occupant: 1.0 + 1.8 = 2.8 + margin 0.5 = 3.3 <= 4: still passes
		assertEquals(Gauge.Verdict.PASSE_DESSOUS, Gauge.decide(vessel("barque chargée", 2.8, 1.0), 66, 62, 0.5, 5).verdict());
		// with a bigger margin it does not
		assertEquals(Gauge.Verdict.OUVERTURE_REQUISE, Gauge.decide(vessel("barque chargée", 2.8, 1.0), 66, 62, 1.5, 5).verdict());
		// the galley: mast 13.2 above the water
		Gauge.Decision galley = Gauge.decide(vessel("galère", 13.2, 2.55), 66, 62, 0.5, 5);
		assertTrue(galley.opens());
		assertTrue(galley.reason().contains("ouverture requise"));
		// a paddleboat 12 wide between towers 10 apart: too wide, opening does not help
		Gauge.Decision wide = Gauge.decide(vessel("vapeur", 11, 6), 66, 62, 0.5, 5);
		assertEquals(Gauge.Verdict.TROP_LARGE, wide.verdict());
		assertFalse(wide.opens());
		// exactly at the limit: top + margin == underside passes
		assertEquals(Gauge.Verdict.PASSE_DESSOUS, Gauge.decide(vessel("limite", 3.5, 1), 66, 62, 0.5, 5).verdict());
	}

	// ---- cycle

	private static final BridgeTuning T = new BridgeTuning(50, 8, 80, 160, 100, 80, 0.5, 6);

	private static final class Events implements BridgeCycle.Listener {
		final List<String> log = new ArrayList<>();

		@Override
		public void safetyWait() {
			log.add("safety");
		}

		@Override
		public void opening(boolean removeBlocks) {
			log.add(removeBlocks ? "opening+remove" : "opening");
		}

		@Override
		public void opened() {
			log.add("opened");
		}

		@Override
		public void closing() {
			log.add("closing");
		}

		@Override
		public void closed() {
			log.add("closed");
		}

		@Override
		public void reversed() {
			log.add("reversed");
		}

		@Override
		public void blocked(String why) {
			log.add("blocked:" + why);
		}

		@Override
		public void error(String why) {
			log.add("error");
		}

		@Override
		public void recovered() {
			log.add("recovered");
		}
	}

	private static void ticks(BridgeCycle c, BridgeCycle.Input in, int n, Events ev) {
		for (int i = 0; i < n; i++) {
			c.tick(in, T, ev);
		}
	}

	@Test
	void fullCycle() {
		BridgeCycle c = new BridgeCycle();
		Events ev = new Events();
		BridgeCycle.Input quiet = BridgeCycle.Input.QUIET;
		ticks(c, quiet, 10, ev);
		assertEquals(BridgeCycle.State.FERME, c.state());
		assertTrue(ev.log.isEmpty());

		BridgeCycle.Input demand = quiet.withDemand(true);
		c.tick(demand, T, ev);
		assertEquals(BridgeCycle.State.ATTENTE_SECURITE, c.state());
		assertEquals(List.of("safety"), ev.log);
		// the warning time (80 ticks after entering the wait): nothing moves
		ticks(c, demand, 79, ev);
		assertEquals(BridgeCycle.State.ATTENTE_SECURITE, c.state());
		assertEquals(0, c.angle(), 1e-9);
		c.tick(demand, T, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		assertEquals("opening+remove", ev.log.get(ev.log.size() - 1));
		assertFalse(c.blocksInWorld());
		// 160 ticks to 80 degrees, slow at both ends (smoothstep): 40 degrees at half time, nearly there one tick before
		ticks(c, demand, 80, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		assertEquals(40, c.angle(), 1e-9);
		ticks(c, demand, 79, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		assertTrue(c.angle() < 80 && c.angle() > 79.9, "angle " + c.angle());
		c.tick(demand, T, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		assertEquals(80, c.angle(), 1e-9);
		assertEquals("opened", ev.log.get(ev.log.size() - 1));
		// stays open while the demand lasts
		ticks(c, demand, 500, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		// the vessel is gone: closing delay of 100 ticks, then closing
		ticks(c, quiet, 100, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		c.tick(quiet, T, ev);
		assertEquals(BridgeCycle.State.FERMETURE, c.state());
		assertEquals("closing", ev.log.get(ev.log.size() - 1));
		ticks(c, quiet, 160, ev);
		assertEquals(BridgeCycle.State.FERME, c.state());
		assertEquals(0, c.angle(), 1e-9);
		assertTrue(c.blocksInWorld());
		assertEquals("closed", ev.log.get(ev.log.size() - 1));
	}

	private static BridgeCycle openBridge(Events ev) {
		BridgeCycle c = new BridgeCycle();
		BridgeCycle.Input demand = BridgeCycle.Input.QUIET.withDemand(true);
		ticks(c, demand, 80 + 1 + 160, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		return c;
	}

	@Test
	void newVesselDuringClosingReversesSmoothly() {
		Events ev = new Events();
		BridgeCycle c = openBridge(ev);
		BridgeCycle.Input quiet = BridgeCycle.Input.QUIET;
		ticks(c, quiet, 101, ev);
		assertEquals(BridgeCycle.State.FERMETURE, c.state());
		ticks(c, quiet, 60, ev);
		double mid = c.angle();
		assertTrue(mid > 40 && mid < 80);
		c.tick(quiet.withDemand(true), T, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		assertEquals("reversed", ev.log.get(ev.log.size() - 1));
		assertEquals(mid, c.angle(), 1e-9); // no jump
		c.tick(quiet.withDemand(true), T, ev);
		assertTrue(c.angle() > mid);
		// the way back up takes a time proportional to the way to go, eased again
		int up = 0;
		while (c.state() == BridgeCycle.State.OUVERTURE && up < 400) {
			c.tick(quiet.withDemand(true), T, ev);
			up++;
		}
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		assertEquals(Math.round(160 * (80 - mid) / 80) - 1, up, 1);
		// an obstacle under the leaves while closing does the same
		BridgeCycle c2 = openBridge(new Events());
		ticks(c2, quiet, 130, new Events());
		assertEquals(BridgeCycle.State.FERMETURE, c2.state());
		Events ev2 = new Events();
		c2.tick(new BridgeCycle.Input(false, false, true, false, true, true), T, ev2);
		assertEquals(BridgeCycle.State.OUVERTURE, c2.state());
		assertEquals(List.of("reversed"), ev2.log);
	}

	@Test
	void vesselStoppedInThePassageKeepsItOpen() {
		Events ev = new Events();
		BridgeCycle c = openBridge(ev);
		BridgeCycle.Input inPassage = new BridgeCycle.Input(false, true, true, true, true, true);
		ticks(c, inPassage, 2000, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		// a manual close is refused while it is there
		c.requestClose();
		ticks(c, inPassage, 5, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		assertTrue(ev.log.stream().anyMatch(s -> s.startsWith("blocked:un navire occupe le passage")));
	}

	@Test
	void someoneOnTheDeckHoldsTheOpening() {
		Events ev = new Events();
		BridgeCycle c = new BridgeCycle();
		BridgeCycle.Input occupied = new BridgeCycle.Input(true, false, false, true, true, true);
		ticks(c, occupied, 80 + 150, ev);
		assertEquals(BridgeCycle.State.ATTENTE_SECURITE, c.state());
		assertTrue(c.blocksInWorld());
		long diagnostics = ev.log.stream().filter(s -> s.startsWith("blocked:quelqu'un")).count();
		assertTrue(diagnostics >= 1 && diagnostics <= 3, "diagnostic repeated every 5 s: " + diagnostics);
		// he leaves: the leaves rise
		c.tick(new BridgeCycle.Input(true, false, true, true, true, true), T, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		// the demand vanishes during the wait: back to closed without moving
		BridgeCycle c2 = new BridgeCycle();
		Events ev2 = new Events();
		ticks(c2, occupied, 30, ev2);
		c2.tick(BridgeCycle.Input.QUIET, T, ev2);
		assertEquals(BridgeCycle.State.FERME, c2.state());
		assertEquals(List.of("safety"), ev2.log);
	}

	@Test
	void blockInTheFootprintGivesAnErrorThenRecovers() {
		Events ev = new Events();
		BridgeCycle c = openBridge(ev);
		BridgeCycle.Input blockedFootprint = new BridgeCycle.Input(false, false, true, true, false, true);
		ticks(c, blockedFootprint, 101 + 160, ev);
		assertEquals(BridgeCycle.State.ERREUR, c.state());
		assertEquals(0, c.angle(), 1e-9);
		assertFalse(c.blocksInWorld());
		assertEquals("error", ev.log.get(ev.log.size() - 1));
		ticks(c, blockedFootprint, 120, ev);
		assertEquals(BridgeCycle.State.ERREUR, c.state());
		// the block is removed: the deck comes back at the next retry
		ticks(c, BridgeCycle.Input.QUIET, 60, ev);
		assertEquals(BridgeCycle.State.FERME, c.state());
		assertTrue(c.blocksInWorld());
		assertEquals(List.of("recovered", "closed"), ev.log.subList(ev.log.size() - 2, ev.log.size()));
		// a demand in ERREUR reopens through the safety wait, without removing blocks that are not there
		BridgeCycle c3 = openBridge(new Events());
		Events ev3 = new Events();
		ticks(c3, blockedFootprint, 101 + 160, ev3);
		assertEquals(BridgeCycle.State.ERREUR, c3.state());
		ticks(c3, blockedFootprint.withDemand(true), 1 + 80, ev3);
		assertEquals(BridgeCycle.State.OUVERTURE, c3.state());
		assertEquals("opening", ev3.log.get(ev3.log.size() - 1));
	}

	@Test
	void suspendedAndManualOrders() {
		Events ev = new Events();
		BridgeCycle c = new BridgeCycle();
		c.setSuspended(true);
		ticks(c, BridgeCycle.Input.QUIET.withDemand(true), 200, ev);
		assertEquals(BridgeCycle.State.FERME, c.state());
		c.requestOpen();
		ticks(c, BridgeCycle.Input.QUIET, 81 + 160, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		// suspended: it stays open forever without the demand
		ticks(c, BridgeCycle.Input.QUIET, 1000, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		c.requestClose();
		ticks(c, BridgeCycle.Input.QUIET.withDemand(true), 101, ev); // the demand is ignored by a manual close
		assertEquals(BridgeCycle.State.FERMETURE, c.state());
		// but an entity in the swept volume is not
		c.tick(new BridgeCycle.Input(false, false, true, false, true, true), T, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
	}

	@Test
	void unloadedChunksFreezeEverything() {
		Events ev = new Events();
		BridgeCycle c = openBridge(ev);
		ticks(c, BridgeCycle.Input.QUIET, 101 + 50, ev);
		assertEquals(BridgeCycle.State.FERMETURE, c.state());
		double a = c.angle();
		ticks(c, new BridgeCycle.Input(false, false, true, true, true, false), 500, ev);
		assertEquals(BridgeCycle.State.FERMETURE, c.state());
		assertEquals(a, c.angle(), 1e-9);
	}

	@Test
	void easing() {
		assertEquals(0, BridgeCycle.ease(0), 1e-12);
		assertEquals(1, BridgeCycle.ease(1), 1e-12);
		assertEquals(0.5, BridgeCycle.ease(0.5), 1e-12);
		assertTrue(BridgeCycle.ease(0.1) < 0.1 && BridgeCycle.ease(0.9) > 0.9, "slow at both ends");
		double prev = 0;
		for (int i = 1; i <= 100; i++) {
			double e = BridgeCycle.ease(i / 100.0);
			assertTrue(e >= prev, "monotonic");
			prev = e;
		}
		assertEquals(10, BridgeCycle.angleOf(10, 80, 0, 5), 1e-12); // no move set up yet
		assertEquals(45, BridgeCycle.angleOf(10, 80, 100, 50), 1e-9);
	}

	@Test
	void restoreAndTuning() {
		BridgeCycle c = new BridgeCycle();
		c.restore(BridgeCycle.State.OUVERTURE, 33, false, false);
		assertEquals(33, c.angle(), 1e-9);
		assertFalse(c.blocksInWorld());
		Events ev = new Events();
		ticks(c, BridgeCycle.Input.QUIET, 1, ev);
		assertTrue(c.angle() > 33);
		// the rest of the way (47 of 80 degrees) takes 94 ticks in all
		ticks(c, BridgeCycle.Input.QUIET, 92, ev);
		assertEquals(BridgeCycle.State.OUVERTURE, c.state());
		c.tick(BridgeCycle.Input.QUIET, T, ev);
		assertEquals(BridgeCycle.State.OUVERT, c.state());
		assertEquals(80, c.angle(), 1e-9);
		BridgeTuning t = T.withOpenAngle(200).withDurationTicks(1);
		assertEquals(90, t.openAngle(), 1e-9);
		assertEquals(10, t.durationTicks());
		assertEquals(9, t.step(), 1e-9);
		DrawbridgeConfig cfg = new DrawbridgeConfig();
		cfg.sanitize();
		assertEquals(160, cfg.defaults().durationTicks());
		assertEquals(100, cfg.defaults().closeDelayTicks());
		assertTrue(cfg.profile("VANILLA_BOAT").occupants);
		assertEquals(2.3, cfg.profile(DrawbridgeConfig.VANILLA_BOAT).height(0.56) + 1.7, 1e-9);
	}
}
