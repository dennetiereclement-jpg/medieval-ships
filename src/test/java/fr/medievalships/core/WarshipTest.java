package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.WarshipLayout;

/** Gameplay geometry and handling of the great warship. */
class WarshipTest {
	private static final ShipGeometry G = Ships.WARSHIP.geometry();
	private static final HullShape H = G.hull();
	private static final double DT = 0.05;
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);

	private static boolean intersectsSolid(double x, double y, double z, double hx, double h, double hz) {
		boolean[] hit = {false};
		G.collectBoxes(ORIGIN, x - hx, y, z - hz, x + hx, y + h, z + hz, (a, b, c, d, e, f) -> {
			if (a < x + hx - 1e-6 && d > x - hx + 1e-6 && b < y + h - 1e-6 && e > y + 1e-6 && c < z + hz - 1e-6 && f > z - hz + 1e-6) {
				hit[0] = true;
			}
		});
		return hit[0];
	}

	private static double support(double x, double y, double z) {
		double[] top = {Double.NEGATIVE_INFINITY};
		G.collectBoxes(ORIGIN, x - 0.3, y - 8, z - 0.3, x + 0.3, y + 0.1, z + 0.3, (a, b, c, d, e, f) -> {
			if (x + 0.3 > a && x - 0.3 < d && z + 0.3 > c && z - 0.3 < f && e <= y + 1e-3) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
	}

	private static void assertStandable(double[] feet, String what) {
		assertTrue(support(feet[0], feet[1], feet[2]) > feet[1] - 0.1, what + ": nothing to stand on at " + str(feet));
		assertFalse(intersectsSolid(feet[0], feet[1] + 0.03, feet[2], 0.3, 1.8, 0.3), what + ": inside a wall at " + str(feet));
	}

	private static String str(double[] p) {
		return String.format(java.util.Locale.ROOT, "(%.2f, %.2f, %.2f)", p[0], p[1], p[2]);
	}

	@Test
	void dimensions() {
		assertEquals(55.0, 2 * H.halfLength, 1e-9);
		assertEquals(13.0, 2 * H.maxHalfWidth, 1e-9);
		double hullHeight = H.railY(-H.halfLength + 0.5) - H.keelY(0);
		assertTrue(hullHeight > 10 && hullHeight < 13, "hull height " + hullHeight);
		assertTrue(WarshipLayout.MAIN_MAST_TOP - H.keelY(0) > 41, "too short");
		assertTrue(G.aiReach() > Ships.GALLEON.geometry().aiReach() + 8);
	}

	@Test
	void hullMatchesModelGenerator() {
		// values computed by tools/warship_shape.py
		double[][] expected = WarshipShapeReference.VALUES;
		for (double[] e : expected) {
			assertEquals(e[1], H.halfWidth(e[0]), 1e-5);
			assertEquals(e[2], H.railY(e[0]), 1e-5);
			assertEquals(e[3], H.keelY(e[0]), 1e-5);
			assertEquals(e[4], H.bottomY(e[0], 2.0), 1e-5);
		}
	}

	@Test
	void twentyFourSeats() {
		List<ShipGeometry.Seat> seats = G.seats();
		assertEquals(24, seats.size());
		for (int i = 0; i < seats.size(); i++) {
			ShipGeometry.Seat s = seats.get(i);
			assertEquals(i, s.index());
			assertEquals(i == ShipGeometry.PILOT_SEAT, s.pilot());
			assertStandable(s.dismountLocal(), "dismount of seat " + i);
			assertFalse(intersectsSolid(s.x(), s.y() + 0.05, s.z(), 0.25, 1.2, 0.25), "seat " + i + " inside a solid");
		}
	}

	@Test
	void decksAreWalkableAtAnyHeading() {
		for (double yaw = 0; yaw < 360; yaw += 30) {
			ShipPose pose = new ShipPose(100.3, 62.9, -40.7, yaw);
			for (double z = H.deckMinZ + 0.5; z <= H.deckMaxZ - 0.5; z += 0.61) {
				double w = H.innerHalfWidth(z) - 0.3;
				for (double x = -w; x <= w; x += 0.53) {
					double[] p = pose.toWorld(x, H.deckY(z), z);
					double[] best = {Double.NEGATIVE_INFINITY};
					G.collectBoxes(pose, p[0] - 0.3, p[1] - 0.5, p[2] - 0.3, p[0] + 0.3, p[1] + 1.8, p[2] + 0.3,
							(a, b, c, d, e, f) -> {
								if (p[0] > a && p[0] < d && p[2] > c && p[2] < f && e <= p[1] + 1e-6) {
									best[0] = Math.max(best[0], e);
								}
							});
					assertTrue(best[0] > p[1] - 0.05, "no deck under " + x + "," + z + " yaw " + yaw);
				}
			}
		}
	}

	@Test
	void wallsHaveNoPlayerSizedGaps() {
		for (double yaw = 0; yaw < 360; yaw += 22.5) {
			ShipPose pose = new ShipPose(0, 62, 0, yaw);
			for (double z = -H.halfLength + 0.5; z <= H.halfLength - 0.5; z += 0.3) {
				for (double side : new double[] {1, -1}) {
					double x = side * (H.halfWidth(z) - 0.06);
					double[] p = pose.toWorld(x, H.deckY(z) + 0.5, z);
					boolean[] hit = {false};
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

	@Test
	void boardingSpots() {
		for (double z = -H.halfLength; z <= H.halfLength; z += 0.35) {
			for (double x = -7; x <= 7; x += 0.7) {
				double[] spot = G.boardingSpot(x, z);
				assertStandable(spot, "boarding spot for " + x + "," + z);
				assertTrue(spot[2] > WarshipLayout.POOP_START, "boarding onto the closed poop structure");
			}
		}
	}

	private static void climb(double x, double zFrom, double zTo, double from, double to) {
		double last = from;
		double step = zTo > zFrom ? 0.1 : -0.1;
		for (double z = zFrom; step > 0 ? z <= zTo : z >= zTo; z += step) {
			double top = support(x, to + 1, z);
			assertTrue(top - last <= 0.6 + 1e-9, "step too high at x=" + x + " z=" + z + ": " + last + " -> " + top);
			last = Math.max(last, top);
		}
		assertEquals(to, last, 1e-9);
	}

	@Test
	void stairsAreClimbable() {
		for (double side : new double[] {1, -1}) {
			climb(side * (WarshipLayout.QD_STAIR_X0 + WarshipLayout.QD_STAIR_X1) / 2, WarshipLayout.QD_STAIR_START + 0.4,
					WarshipLayout.QUARTERDECK_START - 1.0, WarshipLayout.MAIN_DECK_Y, WarshipLayout.QUARTERDECK_Y);
			climb(side * (WarshipLayout.POOP_STAIR_X0 + WarshipLayout.POOP_STAIR_X1) / 2, WarshipLayout.POOP_STAIR_START + 0.4,
					WarshipLayout.POOP_START - 1.0, WarshipLayout.QUARTERDECK_Y, WarshipLayout.POOP_Y);
			climb(side * (WarshipLayout.FC_STAIR_X0 + WarshipLayout.FC_STAIR_X1) / 2, WarshipLayout.FC_STAIR_START - 0.4,
					WarshipLayout.FORECASTLE_START + 0.5, WarshipLayout.MAIN_DECK_Y, WarshipLayout.FORECASTLE_Y);
		}
	}

	@Test
	void greatCabinIsAccessible() {
		double y = WarshipLayout.MAIN_DECK_Y + 0.01;
		for (double z = WarshipLayout.QUARTERDECK_START + 1.0; z >= -25.0; z -= 0.2) {
			double x = Math.abs(z - WarshipLayout.MIZZEN_Z) < 1.0 ? 1.4 : 0; // around the mizzen mast foot
			assertFalse(intersectsSolid(x, y, z, 0.3, 1.8, 0.3), "cabin path blocked at z=" + z);
			assertTrue(support(x, y, z) > y - 0.1);
		}
		assertTrue(intersectsSolid(2.5, y, WarshipLayout.QUARTERDECK_START - 0.15, 0.3, 1.8, 0.3), "bulkhead");
		assertTrue(intersectsSolid(0, y + 1.0, -16, 0.3, 2.0, 0.3), "cabin roof");
	}

	@Test
	void picking() {
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, WarshipLayout.QUARTERDECK_Y + 1.6, -8.5, 0, -0.3, -1, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
		p = G.pick(ORIGIN, 12, 3.0, 0, -1, 0, 0, 10);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	@Test
	void gunports() {
		assertEquals(58, G.gunports().size());
		for (ShipGeometry.Gunport g : G.gunports()) {
			assertEquals(Math.signum(g.x()), g.side(), 0);
			assertTrue(g.y() > 0.5 && g.y() < H.railY(g.z()), "gun port above the rail at " + g.z());
		}
	}

	@Test
	void rescueOntoUpperDecks() {
		assertEquals(WarshipLayout.QUARTERDECK_Y, G.deckRescueY(0, WarshipLayout.QUARTERDECK_Y - 0.3, WarshipLayout.PILOT_Z), 1e-9);
		assertEquals(WarshipLayout.POOP_Y, G.deckCrossingY(0, -23, WarshipLayout.POOP_Y + 0.5, WarshipLayout.POOP_Y - 1.5, 1e-3, true), 1e-9);
		assertTrue(Double.isNaN(G.deckRescueY(0, WarshipLayout.MAIN_DECK_Y, -16)));
	}

	@Test
	void heaviestOfTheThree() {
		ShipConfig galleon = Ships.GALLEON.defaults().get(), warship = Ships.WARSHIP.defaults().get();
		assertTrue(warship.acceleration < galleon.acceleration);
		assertTrue(warship.waterDrag < galleon.waterDrag);
		assertTrue(warship.maxTurnRate < galleon.maxTurnRate);
		ShipPhysics ph = new ShipPhysics();
		int t = 0;
		while (ph.speed < warship.normalSpeed * 0.95 && t < 20 * 120) {
			ph.step(new ShipPhysics.Controls(warship.normalSpeed, 0), warship, DT);
			t++;
		}
		assertTrue(t * DT > 15, "accelerates too fast: " + t * DT + " s");
		double glide = 0;
		for (int i = 0; i < 20 * 60; i++) {
			glide += ph.step(ShipPhysics.Controls.COAST, warship, DT).forward();
		}
		assertTrue(glide > 40, "not enough inertia: " + glide);
	}

	// ------------------------------------------------------------------ autopilot

	private static boolean land(double x, double z) {
		if (z < -170 || z > 170) {
			return true;
		}
		return Math.hypot(x - 300, z - 8) < 45;
	}

	private List<String> simulate(Route route, ShipPose start, int maxTicks, int stopAfterArrivals, ShipPose[] end) {
		ShipConfig cfg = Ships.WARSHIP.defaults().get();
		ShipPhysics ph = new ShipPhysics();
		Autopilot ap = new Autopilot();
		ap.start(route, start, cfg, G);
		List<String> events = new ArrayList<>();
		ShipMover.Obstacles obstacles = (x, y, z) -> land(x, z) && y < 64;
		Autopilot.Navigator nav = (x, z) -> !land(x, z);
		int[] arrivals = {0};
		ShipPose[] cur = {start};
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
				events.add("stuck@" + str(new double[] {cur[0].x(), cur[0].yaw(), cur[0].z()}));
			}
		};
		ShipPose pose = start;
		for (int t = 0; t < maxTicks && arrivals[0] < stopAfterArrivals; t++) {
			ShipPhysics.Controls c = ap.tick(route, pose, ph.speed, ph.yawRate, Gait.NORMAL, cfg, G, nav, listener);
			ShipPhysics.Step s = ph.step(c, cfg, DT);
			ShipMover.Result r = ShipMover.move(G, pose, s.forward(), s.yaw(), 0, obstacles);
			ph.collide(r.forwardBlocked(), r.rotationBlocked());
			pose = r.pose();
			cur[0] = pose;
			assertEquals(0, ShipMover.countCollisions(G, pose, obstacles), "hull inside the land at tick " + t);
		}
		end[0] = pose;
		return events;
	}

	@Test
	void imperialRoundTrip() {
		Route route = new Route("imperial", "minecraft:overworld");
		route.mode = Route.Mode.PINGPONG;
		route.points.add(new Waypoint(0, 62, 0, 20, "Port imperial"));
		route.points.add(new Waypoint(600, 62, 0, 20, "Forteresse"));
		ShipPose[] end = new ShipPose[1];
		List<String> events = simulate(route, new ShipPose(0, 62, 0, -90), 20 * 60 * 15, 3, end);
		assertTrue(events.contains("arrive Forteresse"), "never reached: " + events + " at " + end[0]);
		assertTrue(events.indexOf("arrive Forteresse") < events.lastIndexOf("arrive Port imperial"), "did not come back: " + events);
		assertFalse(events.toString().contains("stuck"), events.toString());
	}

	@Test
	void routeWithTurnsStopsOnTheQuay() {
		Route route = new Route("tour", "minecraft:overworld");
		route.mode = Route.Mode.ONCE;
		route.points.add(new Waypoint(0, 62, 0, 0, "start"));
		route.points.add(new Waypoint(140, 62, 110, 0, null));
		route.points.add(new Waypoint(220, 62, -120, 0, null));
		route.points.add(new Waypoint(470, 62, -120, 0, null));
		route.points.add(new Waypoint(500, 62, 90, 10, "Port militaire"));
		ShipPose[] end = new ShipPose[1];
		List<String> events = simulate(route, new ShipPose(-40, 62, 0, -90), 20 * 60 * 12, 1, end);
		assertTrue(events.contains("arrive Port militaire"), "route not completed: " + events + " " + end[0]);
		assertTrue(Math.hypot(end[0].x() - 500, end[0].z() - 90) < 6, "stopped at " + end[0]);
	}
}
