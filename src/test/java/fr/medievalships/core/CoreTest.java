package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

class CoreTest {
	private static final ShipGeometry G = Ships.GALLEY.geometry();
	private static final double DT = 0.05;

	@Test
	void poseRoundTripAndForward() {
		ShipPose p = new ShipPose(10, 62, -5, 37);
		double[] w = p.toWorld(1.5, 2, -3);
		double[] l = p.toLocal(w[0], w[1], w[2]);
		assertEquals(1.5, l[0], 1e-9);
		assertEquals(2, l[1], 1e-9);
		assertEquals(-3, l[2], 1e-9);
		// local +z is the Minecraft facing direction
		ShipPose south = new ShipPose(0, 0, 0, 0);
		assertEquals(1, south.toWorld(0, 0, 1)[2], 1e-9);
		ShipPose west = new ShipPose(0, 0, 0, 90);
		assertEquals(-1, west.toWorld(0, 0, 1)[0], 1e-9);
		assertEquals(90, ShipPose.yawOf(-1, 0), 1e-9);
	}

	@Test
	void hullProfileMatchesModelGenerator() {
		// values computed by tools/hull_profile.py
		assertEquals(2.55, HullProfile.halfWidth(0), 1e-9);
		assertEquals(0.0, HullProfile.halfWidth(10.3), 1e-9);
		assertTrue(HullProfile.halfWidth(9.9) < 0.6);
		assertEquals(1.6, HullProfile.railY(0), 1e-9);
		assertEquals(2.6, HullProfile.railY(10), 1e-9);
		assertEquals(-1.2, HullProfile.keelY(0), 1e-9);
	}

	/** Every deck point must be supported by a collision box, at any heading. */
	@Test
	void deckIsWalkableAtAnyHeading() {
		for (double yaw = 0; yaw < 360; yaw += 7.5) {
			ShipPose pose = new ShipPose(100.3, 62.9, -40.7, yaw);
			for (double z = -9.0; z <= 9.0; z += 0.37) {
				double w = HullProfile.innerHalfWidth(z) - 0.3;
				for (double x = -w; x <= w; x += 0.29) {
					double[] p = pose.toWorld(x, HullProfile.deckY(z), z);
					// a player-sized box resting on the deck
					double[] support = {Double.NEGATIVE_INFINITY};
					G.collectBoxes(pose, p[0] - 0.3, p[1] - 0.5, p[2] - 0.3, p[0] + 0.3, p[1] + 1.8, p[2] + 0.3,
							(a, b, c, d, e, f) -> {
								if (p[0] > a && p[0] < d && p[2] > c && p[2] < f && e <= p[1] + 1e-6) {
									support[0] = Math.max(support[0], e);
								}
							});
					assertTrue(support[0] > p[1] - 0.05, "no deck under " + x + "," + z + " yaw " + yaw);
				}
			}
		}
	}

	/** The hull walls must leave no gap a player (0.6 wide) could walk through. */
	@Test
	void wallsHaveNoPlayerSizedGaps() {
		for (double yaw = 0; yaw < 360; yaw += 11.25) {
			ShipPose pose = new ShipPose(0, 62, 0, yaw);
			for (double z = -9.5; z <= 9.5; z += 0.2) {
				for (double side : new double[] {1, -1}) {
					double x = side * (HullProfile.halfWidth(z) - 0.06);
					double[] p = pose.toWorld(x, HullProfile.deckY(z) + 0.5, z);
					boolean[] hit = {false};
					// a 0.6 x 0.6 player box centred on the wall line must intersect a wall box
					G.collectBoxes(pose, p[0] - 0.3, p[1], p[2] - 0.3, p[0] + 0.3, p[1] + 0.2, p[2] + 0.3,
							(a, b, c, d, e, f) -> {
								if (a < p[0] + 0.3 && d > p[0] - 0.3 && c < p[2] + 0.3 && f > p[2] - 0.3
										&& b < p[1] + 0.2 && e > p[1] && e - b > 1.0) {
									hit[0] = true;
								}
							});
					assertTrue(hit[0], "gap in wall at z=" + z + " yaw " + yaw);
				}
			}
		}
	}

	/** The hull is solid from the keel to the deck: nothing can swim under the deck or inside the hull. */
	@Test
	void hullIsSolidBelowTheDeck() {
		for (double yaw = 0; yaw < 360; yaw += 15) {
			ShipPose pose = new ShipPose(10.2, 62.9, -7.3, yaw);
			for (double z = -9.0; z <= 9.0; z += 0.45) {
				double w = HullProfile.innerHalfWidth(z) - 0.2;
				for (double x = -w; x <= w; x += 0.4) {
					double bottom = HullProfile.bottomY(z, Math.abs(x) + 0.26) + 0.05;
					for (double y = bottom; y < HullProfile.deckY(z) - 0.05; y += 0.3) {
						double[] p = pose.toWorld(x, y, z);
						boolean[] inside = {false};
						G.collectBoxes(pose, p[0] - 0.01, p[1] - 0.01, p[2] - 0.01, p[0] + 0.01, p[1] + 0.01, p[2] + 0.01,
								(a, b, c, d, e, f) -> {
									if (p[0] >= a && p[0] <= d && p[1] >= b && p[1] <= e && p[2] >= c && p[2] <= f) {
										inside[0] = true;
									}
								});
						assertTrue(inside[0], "hollow hull at " + x + "," + y + "," + z + " yaw " + yaw);
					}
				}
			}
		}
	}

	/** The collision volume must not stick out under the rounded hull bottom (no invisible walls in the water). */
	@Test
	void hullBoxesStayInsideTheHullBottom() {
		ShipPose pose = new ShipPose(0, 62, 0, 0);
		G.collectBoxes(pose, -4, 60, -11, 4, 66, 11, (a, b, c, d, e, f) -> {
			double cx = (a + d) / 2, cz = (c + f) / 2;
			double bottomHere = HullProfile.bottomY(cz, Math.min(HullProfile.halfWidth(cz), Math.abs(cx) + 0.4));
			assertTrue(b - 62 >= HullProfile.keelY(cz) - 0.3, "box below the keel at " + cx + "," + cz);
			assertTrue(b - 62 >= Math.min(bottomHere, HullProfile.keelY(cz)) - 0.6, "box below the hull bottom at " + cx + "," + cz);
		});
	}

	/** The galley must behave exactly as before the multi-ship refactor (snapshot of 1.1.1). */
	@Test
	void galleyGeometryUnchanged() throws Exception {
		String expected;
		try (var in = CoreTest.class.getResourceAsStream("/galley_snapshot.txt")) {
			expected = new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
		}
		String actual = GalleySnapshot.dump();
		String[] e = expected.split("\n"), a = actual.split("\n");
		assertEquals(e.length, a.length, "snapshot length");
		for (int i = 0; i < e.length; i++) {
			assertEquals(e[i], a[i], "snapshot line " + (i + 1));
		}
	}

	@Test
	void farQueryReturnsNothing() {
		int[] n = {0};
		G.collectBoxes(new ShipPose(0, 62, 0, 30), 50, 60, 50, 51, 62, 51, (a, b, c, d, e, f) -> n[0]++);
		assertEquals(0, n[0]);
	}

	@Test
	void carryVolume() {
		assertTrue(G.inCarryVolume(0, 0.5, 0));
		assertTrue(G.inCarryVolume(1.5, 2.5, -3)); // jumping above the deck
		assertFalse(G.inCarryVolume(3.2, 0.5, 0)); // in the water beside the hull
		assertFalse(G.inCarryVolume(0, -1.5, 0)); // under the hull
	}

	@Test
	void seatsAndPicking() {
		assertEquals(9, G.seats().size());
		assertTrue(G.seats().get(0).pilot());
		ShipPose pose = new ShipPose(0, 62, 0, 0);
		// player standing on deck at z=-6, looking aft at the helm
		ShipGeometry.Pick pick = G.pick(pose, 0, 62 + 0.45 + 1.62, -6, 0, -0.25, -1, 5);
		assertNotNull(pick);
		assertEquals(ShipGeometry.PickKind.HELM, pick.kind());
		// from outside, looking at the hull
		pick = G.pick(pose, 6, 63.5, 0, -1, -0.2, 0, 6);
		assertNotNull(pick);
		assertEquals(ShipGeometry.PickKind.HULL, pick.kind());
		// on deck the hull is not pickable (no accidental boarding): looking over the rail hits nothing
		pick = G.pick(pose, 0, 62 + 0.45 + 1.62, 3, 1, 0.05, 0, 5);
		assertNull(pick);
		// looking down at the deck hits the deck, not the water below
		pick = G.pick(pose, 0, 62 + 0.45 + 1.62, 3, 0.3, -1, 0.2, 5);
		assertNotNull(pick);
		assertEquals(ShipGeometry.PickKind.DECK, pick.kind());
		double[] spot = G.boardingSpot(5, 0);
		assertTrue(Math.abs(spot[0]) < HullProfile.innerHalfWidth(0));
	}

	@Test
	void physicsInertia() {
		ShipConfig cfg = new ShipConfig();
		ShipPhysics ph = new ShipPhysics();
		ShipPhysics.Controls full = new ShipPhysics.Controls(cfg.normalSpeed, 0);
		int ticks = 0;
		while (ph.speed < cfg.normalSpeed - 1e-6 && ticks < 2000) {
			ph.step(full, cfg, DT);
			ticks++;
		}
		// progressive acceleration: several seconds to reach cruising speed
		assertTrue(ticks > 60, "accelerated too fast: " + ticks);
		// release the oars: the ship glides
		double distance = 0;
		for (int i = 0; i < 100; i++) {
			distance += ph.step(ShipPhysics.Controls.COAST, cfg, DT).forward();
		}
		assertTrue(distance > 15, "no inertia, glided only " + distance);
		assertTrue(ph.speed < cfg.normalSpeed * 0.5);
		// helm returns progressively to the centre
		ph.helm = 1;
		ph.step(new ShipPhysics.Controls(Double.NaN, 0), cfg, DT);
		assertTrue(ph.helm > 0.9 && ph.helm < 1);
	}

	@Test
	void turningSlowsTheShip() {
		ShipConfig cfg = new ShipConfig();
		ShipPhysics straight = new ShipPhysics();
		ShipPhysics turning = new ShipPhysics();
		straight.speed = turning.speed = cfg.normalSpeed;
		for (int i = 0; i < 200; i++) {
			straight.step(new ShipPhysics.Controls(Double.NaN, 0), cfg, DT);
			turning.step(new ShipPhysics.Controls(Double.NaN, 1), cfg, DT);
		}
		assertTrue(turning.speed < straight.speed * 0.9);
	}

	@Test
	void moverStopsAtTheCoastAndCanBackOff() {
		// land for x > 30
		ShipMover.Obstacles land = (x, y, z) -> x > 30 && y < 66;
		ShipPose pose = new ShipPose(0, 62, 0, -90); // facing east (+x)
		boolean blocked = false;
		for (int i = 0; i < 200; i++) {
			ShipMover.Result r = ShipMover.move(G, pose, 0.4, 0, 0, land);
			pose = r.pose();
			if (r.forwardBlocked()) {
				blocked = true;
				break;
			}
		}
		assertTrue(blocked);
		assertTrue(pose.x() + 10.9 > 29 && pose.x() + 10.4 <= 30.5, "stopped at " + pose.x());
		assertEquals(0, ShipMover.countCollisions(G, pose, land));
		// reversing is always possible
		ShipMover.Result back = ShipMover.move(G, pose, -0.3, 0, 0, land);
		assertFalse(back.forwardBlocked());
	}

	@Test
	void moverEscapesWhenSpawnedInsideTerrain() {
		ShipMover.Obstacles land = (x, y, z) -> x > 5 && y < 66;
		ShipPose pose = new ShipPose(0, 62, 0, -90); // bow already in the land
		int before = ShipMover.countCollisions(G, pose, land);
		assertTrue(before > 0);
		ShipMover.Result fwd = ShipMover.move(G, pose, 0.3, 0, 0, land);
		assertTrue(fwd.forwardBlocked(), "must not dig further into the land");
		ShipPose p = pose;
		for (int i = 0; i < 60; i++) {
			p = ShipMover.move(G, p, -0.3, 0, 0, land).pose();
		}
		assertEquals(0, ShipMover.countCollisions(G, p, land));
	}

	@Test
	void otherHullIsAnObstacle() {
		ShipPose other = new ShipPose(0, 62, 30, 90);
		ShipMover.Obstacles obstacles = (x, y, z) -> {
			double[] l = other.toLocal(x, y, z);
			return G.insideHull(l[0], l[1], l[2]);
		};
		ShipPose pose = new ShipPose(0, 62, 0, 0); // heading south (+z) towards the other ship
		ShipMover.Result r = null;
		for (int i = 0; i < 200; i++) {
			r = ShipMover.move(G, pose, 0.4, 0, 0, obstacles);
			pose = r.pose();
			if (r.forwardBlocked()) {
				break;
			}
		}
		assertTrue(r.forwardBlocked());
		assertTrue(pose.z() < 30 - 2.5 - 9.5, "hulls overlap: " + pose.z());
	}

	// ------------------------------------------------------------------ navigation simulation

	/** Synthetic sea: island in the middle, coast north and south. */
	private static boolean land(double x, double z) {
		if (z < -60 || z > 60) {
			return true;
		}
		return Math.hypot(x - 100, z - 3) < 18;
	}

	private record SimResult(List<String> events, ShipPose pose, int ticks) {
	}

	private SimResult simulate(Route route, ShipPose start, int maxTicks, int stopAfterArrivals) {
		ShipConfig cfg = new ShipConfig();
		ShipPhysics ph = new ShipPhysics();
		Autopilot ap = new Autopilot();
		ap.start(route, start, cfg, G);
		List<String> events = new ArrayList<>();
		ShipMover.Obstacles obstacles = (x, y, z) -> land(x, z) && y < 64;
		Autopilot.Navigator nav = (x, z) -> !land(x, z);
		int[] arrivals = {0};
		Autopilot.Listener listener = new Autopilot.Listener() {
			@Override
			public void departing(Waypoint from, Waypoint next, int nextIndex) {
				events.add("depart " + from.name);
			}

			@Override
			public void arrived(Waypoint stop, int index) {
				events.add("arrive " + stop.name);
				arrivals[0]++;
			}

			@Override
			public void stuck() {
				events.add("stuck");
			}
		};
		ShipPose pose = start;
		int t;
		for (t = 0; t < maxTicks && arrivals[0] < stopAfterArrivals; t++) {
			ShipPhysics.Controls c = ap.tick(route, pose, ph.speed, ph.yawRate, Gait.NORMAL, cfg, G, nav, listener);
			ShipPhysics.Step s = ph.step(c, cfg, DT);
			ShipMover.Result r = ShipMover.move(G, pose, s.forward(), s.yaw(), 0, obstacles);
			ph.collide(r.forwardBlocked(), r.rotationBlocked());
			pose = r.pose();
			assertEquals(0, ShipMover.countCollisions(G, pose, obstacles), "hull inside the land at tick " + t);
		}
		return new SimResult(events, pose, t);
	}

	@Test
	void ferryGoesAroundTheIslandAndComesBack() {
		Route route = new Route("ferry", "minecraft:overworld");
		route.mode = Route.Mode.PINGPONG;
		route.points.add(new Waypoint(0, 62, 0, 20, "Port A"));
		route.points.add(new Waypoint(200, 62, 0, 20, "Port B"));
		SimResult r = simulate(route, new ShipPose(0, 62, 0, -90), 20 * 60 * 6, 3);
		assertTrue(r.events().contains("arrive Port B"), "never reached B: " + r.events() + " at " + r.pose());
		assertTrue(r.events().indexOf("arrive Port B") < r.events().lastIndexOf("arrive Port A"),
				"did not come back: " + r.events());
		assertFalse(r.events().contains("stuck"));
	}

	@Test
	void routeWithWaypointsAndTurns() {
		Route route = new Route("tour", "minecraft:overworld");
		route.mode = Route.Mode.ONCE;
		route.points.add(new Waypoint(0, 62, 0, 0, "start"));
		route.points.add(new Waypoint(40, 62, 30, 0, null));
		route.points.add(new Waypoint(70, 62, -35, 0, null));
		route.points.add(new Waypoint(160, 62, -40, 0, null));
		route.points.add(new Waypoint(170, 62, 30, 10, "Quai"));
		SimResult r = simulate(route, new ShipPose(-20, 62, 0, -90), 20 * 60 * 5, 1);
		assertTrue(r.events().contains("arrive Quai"), "route not completed: " + r.events() + " " + r.pose());
		assertTrue(Math.hypot(r.pose().x() - 170, r.pose().z() - 30) < 3.5);
	}

	@Test
	void nextIndexModes() {
		Route r = new Route("x", "o");
		for (int i = 0; i < 3; i++) {
			r.points.add(new Waypoint(i, 0, 0, 0, null));
		}
		r.mode = Route.Mode.PINGPONG;
		int[] n = Autopilot.next(r, 2, 1);
		assertEquals(1, n[0]);
		assertEquals(-1, n[1]);
		r.mode = Route.Mode.LOOP;
		assertEquals(0, Autopilot.next(r, 2, 1)[0]);
		r.mode = Route.Mode.ONCE;
		assertNull(Autopilot.next(r, 2, 1));
	}
}
