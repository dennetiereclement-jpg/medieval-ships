package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.Gson;

/**
 * The route features scripted quests and NPCs rely on (see docs/COMMANDES.md, "Scénarios de quêtes / PNJ"): stops
 * held until the order to leave, the end of a {@code once} route where the vessel waits and then vanishes, the
 * {@code return} mode (one round trip), the arrival commands kept with the route, the vessel selectors of
 * {@code /ship as} and {@code /ship test}, and where the passengers are landed beside a moored vessel.
 */
class QuestCommandsTest {
	private static final double DT = 0.05;
	private static final ShipGeometry G = Ships.GALLEY.geometry();

	/** Events of a run. */
	private static final class Log implements Autopilot.Listener {
		final List<String> events = new ArrayList<>();
		final List<Integer> ticks = new ArrayList<>();
		int tick;

		@Override
		public void departing(Waypoint from, Waypoint next, int nextIndex) {
			add("depart " + from.label(0));
		}

		@Override
		public void arrived(Waypoint stop, int index) {
			add("arrive " + stop.label(index));
		}

		@Override
		public void countdown(int secondsLeft, Waypoint nextStop) {
			add("countdown " + secondsLeft);
		}

		@Override
		public void countdownToEnd(int secondsLeft) {
			add("end-countdown " + secondsLeft);
		}

		@Override
		public void finished() {
			add("finished");
		}

		private void add(String e) {
			events.add(e);
			ticks.add(tick);
		}

		boolean has(String e) {
			return events.contains(e);
		}

		int tickOf(String e) {
			int i = events.indexOf(e);
			return i < 0 ? -1 : ticks.get(i);
		}
	}

	/** A straight sea route: A (first stop) -> B (second stop), 80 blocks apart. */
	private static Route route(Route.Mode mode, int waitA, int waitB) {
		Route r = new Route("quete", "minecraft:overworld");
		r.mode = mode;
		r.points.add(new Waypoint(0, 62, 0, waitA, "Quai"));
		r.points.add(new Waypoint(0, 62, 80, waitB, "Port"));
		return r;
	}

	/** Runs the galley on the route with the pure-Java physics; returns the final pose. */
	private static ShipPose run(Route route, Autopilot ap, ShipPose start, int ticks, Log log, Runnable[] atTick) {
		ShipConfig cfg = Ships.GALLEY.defaults().get();
		ShipPhysics physics = new ShipPhysics();
		ShipPose pose = start;
		for (int t = 0; t < ticks; t++) {
			log.tick = t;
			if (atTick != null && t < atTick.length && atTick[t] != null) {
				atTick[t].run();
			}
			ShipPhysics.Controls c = ap.tick(route, pose, physics.speed, physics.yawRate, Gait.NORMAL, cfg, G, (x, z) -> true, log);
			ShipPhysics.Step step = physics.step(c, cfg, DT);
			double r = Math.toRadians(pose.yaw());
			pose = pose.moved(-Math.sin(r) * step.forward(), 0, Math.cos(r) * step.forward(), step.yaw());
		}
		return pose;
	}

	// ------------------------------------------------------------------ hold stops

	@Test
	void waypointHoldIsAStopWithoutATime() {
		Waypoint w = new Waypoint(0, 0, 0, Waypoint.HOLD, "Quai");
		assertTrue(w.isStop());
		assertTrue(w.holds());
		assertEquals(Autopilot.HOLD_TICKS, w.dockTicks());
		Waypoint timed = new Waypoint(0, 0, 0, 12, null);
		assertTrue(timed.isStop());
		assertFalse(timed.holds());
		assertEquals(240, timed.dockTicks());
		Waypoint pass = new Waypoint(0, 0, 0, 0, null);
		assertFalse(pass.isStop());
		assertEquals(20, pass.dockTicks(), "a plain point reached as the end of a route counts one second");
	}

	@Test
	void aHeldStopWaitsForTheOrderToLeave() {
		Route route = route(Route.Mode.ONCE, Waypoint.HOLD, 5);
		Autopilot ap = new Autopilot();
		ap.start(route, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		assertEquals(Autopilot.Phase.DOCKED, ap.phase, "moored at the quay");
		assertTrue(ap.holding(), "held");
		Log log = new Log();
		// ten minutes: nothing happens
		ShipPose pose = run(route, ap, new ShipPose(0, 62, 0, 0), 12_000, log, null);
		assertEquals(Autopilot.Phase.DOCKED, ap.phase, "still moored after ten minutes");
		assertTrue(ap.holding());
		assertTrue(log.events.isEmpty(), "no countdown, no departure: " + log.events);
		assertEquals(0.0, Math.hypot(pose.x(), pose.z()), 1e-9, "has not moved");
		// the order: it leaves at once and reaches the port
		ap.departNow();
		assertFalse(ap.holding());
		pose = run(route, ap, pose, 1200, log, null);
		assertTrue(log.has("depart Quai"), "leaves on the order: " + log.events);
		assertEquals(0, log.tickOf("depart Quai"), "at the very next tick");
		assertTrue(log.has("arrive Port"), "reaches the port: " + log.events);
		assertTrue(Math.abs(pose.z() - 80) < Ships.GALLEY.defaults().get().aiStopRadius + 0.5, "moored at the port, z=" + pose.z());
	}

	@Test
	void holdWhileSailingHoldsAtTheNextStop() {
		// a ferry: the port is not a terminus (a once route's terminus where the vessel stays is finished at once)
		Route route = route(Route.Mode.PINGPONG, 1, 5);
		Autopilot ap = new Autopilot();
		ap.start(route, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		assertTrue(ap.hold(), "moored: held");
		assertTrue(ap.holding());
		ap.departNow();
		Log log = new Log();
		ShipPose pose = run(route, ap, new ShipPose(0, 62, 0, 0), 40, log, null);
		assertEquals(Autopilot.Phase.SAILING, ap.phase);
		assertFalse(ap.hold(), "sailing: not held now, but at the next stop");
		assertFalse(ap.holding());
		run(route, ap, pose, 1200, log, null);
		assertTrue(log.has("arrive Port"));
		assertEquals(Autopilot.Phase.DOCKED, ap.phase);
		assertTrue(ap.holding(), "held at the port instead of waiting its 5 s");
	}

	// ------------------------------------------------------------------ end of the trip

	@Test
	void onceRouteThatStaysIsFinishedOnArrivalAsBefore() {
		Route route = route(Route.Mode.ONCE, 1, 30);
		assertEquals(Route.End.STAY, route.end());
		Autopilot ap = new Autopilot();
		ap.start(route, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		Log log = new Log();
		run(route, ap, new ShipPose(0, 62, 0, 0), 1400, log, null);
		assertTrue(log.has("arrive Port"), log.events.toString());
		assertTrue(log.has("finished"), log.events.toString());
		assertEquals(log.tickOf("arrive Port") + 1, log.tickOf("finished"), "finished right after arriving, the 30 s are not waited");
		assertEquals(Autopilot.Phase.FINISHED, ap.phase);
	}

	@Test
	void onceRouteThatDespawnsWaitsTheLastStopThenFinishes() {
		Route route = route(Route.Mode.ONCE, 1, 8);
		route.end = Route.End.DESPAWN;
		Autopilot ap = new Autopilot();
		ap.start(route, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		Log log = new Log();
		run(route, ap, new ShipPose(0, 62, 0, 0), 1400, log, null);
		int arrive = log.tickOf("arrive Port"), finished = log.tickOf("finished");
		assertTrue(arrive >= 0 && finished >= 0, log.events.toString());
		assertEquals(8 * 20, finished - arrive, 2, "the 8 s of the last stop are waited before the end (the players get off)");
		assertTrue(log.has("end-countdown 5") && log.has("end-countdown 1"), "the last seconds are announced: " + log.events);
		assertFalse(log.has("countdown 5"), "not as a departure: " + log.events);
		assertEquals(Autopilot.Phase.FINISHED, ap.phase);
	}

	@Test
	void despawnAtAHeldTerminusWaitsForTheOrder() {
		Route route = route(Route.Mode.ONCE, 1, Waypoint.HOLD);
		route.end = Route.End.DESPAWN_ITEM;
		Autopilot ap = new Autopilot();
		ap.start(route, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		Log log = new Log();
		ShipPose pose = run(route, ap, new ShipPose(0, 62, 0, 0), 1400, log, null);
		assertTrue(log.has("arrive Port"), log.events.toString());
		assertFalse(log.has("finished"), "held at the terminus: " + log.events);
		assertEquals(Autopilot.Phase.DOCKED, ap.phase);
		assertTrue(ap.holding());
		run(route, ap, pose, 2400, log, null);
		assertFalse(log.has("finished"), "two more minutes: still held");
		ap.departNow();
		run(route, ap, pose, 5, log, null);
		assertTrue(log.has("finished"), "the order ends the trip: " + log.events);
		assertEquals(Autopilot.Phase.FINISHED, ap.phase);
	}

	@Test
	void returnModeMakesOneRoundTrip() {
		Route r = route(Route.Mode.RETURN, 1, 1);
		r.points.add(1, new Waypoint(0, 62, 40, 0, null));
		assertArrayEquals(new int[] {1, 1}, Autopilot.next(r, 0, 1));
		assertArrayEquals(new int[] {2, 1}, Autopilot.next(r, 1, 1));
		assertArrayEquals(new int[] {1, -1}, Autopilot.next(r, 2, 1), "turns round at the far end");
		assertArrayEquals(new int[] {0, -1}, Autopilot.next(r, 1, -1));
		assertNull(Autopilot.next(r, 0, -1), "ends back at the first point");
		// and the pingpong route still turns round at both ends
		Route p = route(Route.Mode.PINGPONG, 1, 1);
		assertArrayEquals(new int[] {0, -1}, Autopilot.next(p, 1, 1));
		assertArrayEquals(new int[] {1, 1}, Autopilot.next(p, 0, -1));

		Autopilot ap = new Autopilot();
		ap.start(r, new ShipPose(0, 62, 0, 0), Ships.GALLEY.defaults().get(), G);
		Log log = new Log();
		ShipPose pose = run(r, ap, new ShipPose(0, 62, 0, 0), 3600, log, null);
		assertTrue(log.has("depart Quai"), log.events.toString());
		assertTrue(log.has("arrive Port"), log.events.toString());
		assertTrue(log.has("depart Port"), "leaves the port again: " + log.events);
		assertTrue(log.has("arrive Quai"), "comes back to the quay: " + log.events);
		assertTrue(log.has("finished"), "and ends there: " + log.events);
		assertTrue(log.tickOf("arrive Quai") > log.tickOf("arrive Port"));
		assertEquals(Autopilot.Phase.FINISHED, ap.phase);
		assertTrue(Math.hypot(pose.x(), pose.z()) < Ships.GALLEY.defaults().get().aiStopRadius + 0.5, "moored at the quay again: " + pose);
	}

	// ------------------------------------------------------------------ saved with the world

	@Test
	void routeKeepsItsEndHoldsAndArrivalCommandsInJson() {
		Route r = route(Route.Mode.RETURN, Waypoint.HOLD, 12);
		r.end = Route.End.DESPAWN_ITEM;
		r.points.get(1).onArrive = "say Le navire est au port";
		Gson gson = new Gson();
		Route back = gson.fromJson(gson.toJson(r), Route.class);
		assertEquals(Route.Mode.RETURN, back.mode);
		assertEquals(Route.End.DESPAWN_ITEM, back.end());
		assertTrue(back.get(0).holds());
		assertEquals(12, back.get(1).waitSeconds);
		assertEquals("say Le navire est au port", back.get(1).onArrive);
		assertNull(back.get(0).onArrive);
		assertEquals(0, back.firstStop());
		// a route saved by an older version has no end and no arrival commands: it stays
		Route old = gson.fromJson("{\"name\":\"ferry\",\"dimension\":\"minecraft:overworld\",\"mode\":\"PINGPONG\",\"air\":false,"
				+ "\"points\":[{\"x\":1,\"y\":62,\"z\":2,\"waitSeconds\":300},{\"x\":1,\"y\":62,\"z\":80,\"waitSeconds\":0}]}", Route.class);
		assertEquals(Route.End.STAY, old.end());
		assertFalse(old.end().despawns());
		assertNull(old.get(0).onArrive);
		assertEquals(0, old.firstStop());
		Route noStop = gson.fromJson("{\"name\":\"n\",\"points\":[{\"x\":0,\"y\":0,\"z\":0,\"waitSeconds\":0},{\"x\":0,\"y\":0,\"z\":9,\"waitSeconds\":5}]}",
				Route.class);
		assertEquals(1, noStop.firstStop());
	}

	@Test
	void modeAndEndNames() {
		assertEquals(Route.Mode.RETURN, Route.Mode.byName("return"));
		assertEquals(Route.Mode.RETURN, Route.Mode.byName("retour"));
		assertEquals(Route.Mode.PINGPONG, Route.Mode.byName("aller-retour"));
		assertNull(Route.Mode.byName("zigzag"));
		assertEquals(Route.End.DESPAWN, Route.End.byName("despawn"));
		assertEquals(Route.End.DESPAWN_ITEM, Route.End.byName("despawn_item"));
		assertEquals(Route.End.DESPAWN_ITEM, Route.End.byName("despawn-item"));
		assertEquals(Route.End.STAY, Route.End.byName("stay"));
		assertEquals(Route.End.STAY, Route.End.byName("reste"));
		assertNull(Route.End.byName("explode"));
	}

	// ------------------------------------------------------------------ vessel selectors

	private static ShipSelector.Candidate c(String name, String uuid, String type, double dist, boolean same) {
		return new ShipSelector.Candidate(name, uuid, type, dist, same);
	}

	@Test
	void selectorMatchesNameThenUuidThenType() {
		List<ShipSelector.Candidate> ships = List.of(
				c("La Sirène", "0a1b2c3d-0000-4000-8000-000000000001", "galley", 50, true),
				c(null, "ffee0011-0000-4000-8000-000000000002", "galleon", 10, true),
				c("Albatros", "0a1b2c99-0000-4000-8000-000000000003", "galley", 5, true),
				c("La Sirène", "77777777-0000-4000-8000-000000000004", "warship", 2, false));
		assertEquals(0, ShipSelector.match("La Sirène", ships), "the name, in the command's dimension first even if farther");
		assertEquals(0, ShipSelector.match("la sirène", ships), "names are matched whatever the case");
		assertEquals(3, ShipSelector.match("77777777", ships), "a UUID prefix");
		assertEquals(1, ShipSelector.match("ffee0011-0000-4000-8000-000000000002", ships), "a whole UUID");
		assertEquals(0, ShipSelector.match("0a1b2c3d", ships), "a prefix that tells two UUIDs apart");
		assertEquals(2, ShipSelector.match("galley", ships), "a type: the nearest one");
		assertEquals(1, ShipSelector.match("galleon", ships));
		assertEquals(3, ShipSelector.match("grand_warship", ships), "an alias of a type");
		assertEquals(-1, ShipSelector.match("Le Fantôme", ships));
		assertEquals(-1, ShipSelector.match("", ships));
		assertEquals(-1, ShipSelector.match("galley", List.of()));
		assertTrue(ShipSelector.isNearest("nearest"));
		assertTrue(ShipSelector.isNearest("NEAREST"));
		assertFalse(ShipSelector.isNearest("galley"));
	}

	@Test
	void selectorIsQuotedForScriptsWhenItHasSpaces() {
		assertEquals("Albatros", ShipSelector.quote("Albatros"));
		assertEquals("\"La Sirène\"", ShipSelector.quote("La Sirène"));
		assertEquals("\"Dit \\\"Le Rapide\\\"\"", ShipSelector.quote("Dit \"Le Rapide\""));
		assertEquals("", ShipSelector.quote(null));
	}

	// ------------------------------------------------------------------ landing beside the vessel

	/** A galley moored heading north (+z) at x=0, with a stone quay east of it from x=6 to x=12, top at y=62. */
	private static Landing.Block world(int x, int y, int z, int quayTop, boolean quay) {
		if (y <= 59) {
			return Landing.Block.SOLID; // the sea bed
		}
		if (quay && x >= 6 && x <= 12 && y <= quayTop) {
			return Landing.Block.SOLID;
		}
		if (y <= 62) {
			return Landing.Block.LIQUID; // water up to y=62
		}
		return Landing.Block.FREE;
	}

	@Test
	void landingSpotIsTheNearestQuaySquareBesideTheHull() {
		ShipPose pose = new ShipPose(0.5, 62.0 - G.hull().waterlineY, 10.5, 0);
		double[] spot = Landing.find(G, pose, (x, y, z) -> world(x, y, z, 62, true));
		assertNotNull(spot, "a quay beside the galley is found");
		assertEquals(6.5, spot[0], 1e-9, "the quay's edge nearest to the hull");
		assertEquals(63, spot[1], 1e-9, "standing on top of the quay");
		assertEquals(10.5, spot[2], 1e-9, "level with the hull's middle");
	}

	@Test
	void landingSpotPrefersTheDeckHeightAndNeverTheWaterOrTheHull() {
		ShipPose pose = new ShipPose(0.5, 62.0 - G.hull().waterlineY, 10.5, 0);
		// a high quay (one stands on it ABOVE blocks over the deck's block) and a low shore (y=62) farther away: the
		// nearer quay wins; one higher than the search window would not be a landing spot
		int deckBlock = (int) Math.floor(pose.y() + G.hull().mainDeckY);
		int highTop = deckBlock + Landing.ABOVE - 1;
		double[] spot = Landing.find(G, pose, (x, y, z) -> {
			if (y <= 59) {
				return Landing.Block.SOLID;
			}
			if (x >= 6 && x <= 12 && y <= highTop) {
				return Landing.Block.SOLID;
			}
			if (x <= -9 && y <= 62) {
				return Landing.Block.SOLID;
			}
			return y <= 62 ? Landing.Block.LIQUID : Landing.Block.FREE;
		});
		assertNotNull(spot);
		assertEquals(6.5, spot[0], 1e-9, "the nearer quay, even higher");
		assertEquals(highTop + 1, spot[1], 1e-9);
		double[] tooHigh = Landing.find(G, pose, (x, y, z) -> {
			if (y <= 59) {
				return Landing.Block.SOLID;
			}
			if (x >= 6 && x <= 12 && y <= highTop + 1) {
				return Landing.Block.SOLID;
			}
			if (x <= -9 && y <= 62) {
				return Landing.Block.SOLID;
			}
			return y <= 62 ? Landing.Block.LIQUID : Landing.Block.FREE;
		});
		assertNotNull(tooHigh);
		assertEquals(-8.5, tooHigh[0], 1e-9, "a wall too high to climb: the shore on the other side");
		assertEquals(63, tooHigh[1], 1e-9);
		// open sea: nowhere to land
		assertNull(Landing.find(G, pose, (x, y, z) -> world(x, y, z, 62, false)));
		// the hull itself is never a landing spot: a "solid" block exactly under the deck is ignored
		double[] onlyHull = Landing.find(G, pose, (x, y, z) -> Math.abs(x) <= 1 && z >= 8 && z <= 13 && y == 62 ? Landing.Block.SOLID
				: world(x, y, z, 62, false));
		assertNull(onlyHull, "a spot inside the hull's footprint is not a quay");
	}
}
