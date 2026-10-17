package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.GalleonLayout;

/** Gameplay geometry and handling of the great galleon. */
class GalleonTest {
	private static final ShipGeometry G = Ships.GALLEON.geometry();
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

	/** Highest collision surface under a player footprint at this point (or -inf). */
	private static double support(double x, double y, double z) {
		double[] top = {Double.NEGATIVE_INFINITY};
		G.collectBoxes(ORIGIN, x - 0.3, y - 8, z - 0.3, x + 0.3, y + 0.1, z + 0.3, (a, b, c, d, e, f) -> {
			if (x + 0.3 > a && x - 0.3 < d && z + 0.3 > c && z - 0.3 < f && e <= y + 1e-3) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
	}

	/** A player (0.6 x 1.8) can stand at this feet position: supported and not inside anything. */
	private static void assertStandable(double[] feet, String what) {
		assertTrue(support(feet[0], feet[1], feet[2]) > feet[1] - 0.1, what + ": nothing to stand on at " + str(feet));
		assertFalse(intersectsSolid(feet[0], feet[1] + 0.03, feet[2], 0.3, 1.8, 0.3), what + ": inside a wall at " + str(feet));
	}

	private static String str(double[] p) {
		return String.format(java.util.Locale.ROOT, "(%.2f, %.2f, %.2f)", p[0], p[1], p[2]);
	}

	@Test
	void dimensions() {
		assertEquals(35.0, 2 * H.halfLength, 1e-9);
		assertEquals(9.0, 2 * H.maxHalfWidth, 1e-9);
		double hullHeight = H.railY(-H.halfLength + 0.5) - H.keelY(0);
		assertTrue(hullHeight > 5.8 && hullHeight < 7, "hull height " + hullHeight);
		assertTrue(GalleonLayout.MAIN_MAST_TOP - H.keelY(0) > 26, "too short");
		assertTrue(G.boundingRadius() > 18 && G.aiReach() > 17);
	}

	@Test
	void sixteenSeats() {
		List<ShipGeometry.Seat> seats = G.seats();
		assertEquals(16, seats.size());
		for (int i = 0; i < seats.size(); i++) {
			assertEquals(i, seats.get(i).index());
			assertEquals(i == ShipGeometry.PILOT_SEAT, seats.get(i).pilot());
			assertStandable(seats.get(i).dismountLocal(), "dismount of seat " + i);
			// the seated passenger is not inside a wall or a mast
			ShipGeometry.Seat s = seats.get(i);
			assertFalse(intersectsSolid(s.x(), s.y() + 0.05, s.z(), 0.25, 1.2, 0.25), "seat " + i + " inside a solid");
		}
	}

	@Test
	void deckIsWalkableAtAnyHeading() {
		for (double yaw = 0; yaw < 360; yaw += 15) {
			ShipPose pose = new ShipPose(100.3, 62.9, -40.7, yaw);
			for (double z = H.deckMinZ + 0.5; z <= H.deckMaxZ - 0.5; z += 0.43) {
				double w = H.innerHalfWidth(z) - 0.3;
				for (double x = -w; x <= w; x += 0.37) {
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

	/** Every boarding spot (clicking the hull anywhere) is a free standing place, never in the cabin walls. */
	@Test
	void boardingSpots() {
		for (double z = -H.halfLength; z <= H.halfLength; z += 0.25) {
			for (double x = -5; x <= 5; x += 0.5) {
				double[] spot = G.boardingSpot(x, z);
				assertStandable(spot, "boarding spot for " + x + "," + z);
				assertTrue(spot[1] < GalleonLayout.POOP_WALL_TOP, "boarding onto the poop roof");
			}
		}
	}

	/** Main deck -> quarterdeck and forecastle with steps a player auto-climbs (<= 0.6). */
	@Test
	void stairsAreClimbable() {
		double x = (GalleonLayout.STAIR_X0 + GalleonLayout.STAIR_X1) / 2;
		for (double side : new double[] {1, -1}) {
			double last = GalleonLayout.MAIN_DECK_Y;
			for (double z = GalleonLayout.QD_STAIR_START + 0.4; z >= GalleonLayout.BULKHEAD_Z - 1.5; z -= 0.1) {
				double top = support(side * x, 6, z);
				assertTrue(top - last <= 0.6 + 1e-9, "step too high at z=" + z + ": " + last + " -> " + top);
				last = Math.max(last, top);
			}
			assertEquals(GalleonLayout.QUARTERDECK_Y, last, 1e-9);
			last = GalleonLayout.MAIN_DECK_Y;
			for (double z = GalleonLayout.FC_STAIR_START - 0.4; z <= GalleonLayout.FORECASTLE_START + 0.5; z += 0.1) {
				double top = support(side * x, 6, z);
				assertTrue(top - last <= 0.6 + 1e-9, "step too high at z=" + z + ": " + last + " -> " + top);
				last = Math.max(last, top);
			}
			assertEquals(GalleonLayout.FORECASTLE_Y, last, 1e-9);
		}
	}

	/** The great cabin can be entered through the door, under the quarterdeck. */
	@Test
	void cabinIsAccessible() {
		double y = GalleonLayout.MAIN_DECK_Y + 0.01;
		for (double z = GalleonLayout.BULKHEAD_Z + 1.0; z >= -15.5; z -= 0.2) {
			double x = z < GalleonLayout.MIZZEN_Z + 1.2 ? 1.2 : 0; // around the mizzen mast foot
			assertFalse(intersectsSolid(x, y, z, 0.3, 1.8, 0.3), "cabin path blocked at z=" + z);
			assertTrue(support(x, y, z) > y - 0.1);
		}
		// and it is closed: walls left and right of the door, roof above
		assertTrue(intersectsSolid(2.0, y, GalleonLayout.BULKHEAD_Z - 0.15, 0.3, 1.8, 0.3));
		assertTrue(intersectsSolid(0, y + 1.0, -12, 0.3, 2.0, 0.3));
	}

	@Test
	void picking() {
		// looking at the wheel from the quarterdeck
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, GalleonLayout.QUARTERDECK_Y + 1.6, -7.5, 0, -0.3, -1, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
		// clicking the hull from the water boards the ship
		p = G.pick(ORIGIN, 9, 1.5, 0, -1, 0, 0, 8);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	@Test
	void carryVolumeCoversCastlesAndCabin() {
		assertTrue(G.inCarryVolume(0, GalleonLayout.MAIN_DECK_Y, -12));
		assertTrue(G.inCarryVolume(0, GalleonLayout.QUARTERDECK_Y, -12));
		assertTrue(G.inCarryVolume(0, GalleonLayout.POOP_WALL_TOP + 1, -15));
		assertTrue(G.inCarryVolume(0, GalleonLayout.FORECASTLE_Y, 14));
		assertFalse(G.inCarryVolume(0, GalleonLayout.MAIN_DECK_Y, 21));
	}

	// ------------------------------------------------------------------ handling

	@Test
	void heavierThanTheGalley() {
		ShipConfig galley = Ships.GALLEY.defaults().get(), galleon = Ships.GALLEON.defaults().get();
		assertTrue(galleon.acceleration < galley.acceleration);
		assertTrue(galleon.waterDrag < galley.waterDrag);
		assertTrue(galleon.maxTurnRate < galley.maxTurnRate);
		// time to reach cruising speed, and glide distance once the sails are struck
		ShipPhysics ph = new ShipPhysics();
		int t = 0;
		while (ph.speed < galleon.normalSpeed * 0.95 && t < 20 * 120) {
			ph.step(new ShipPhysics.Controls(galleon.normalSpeed, 0), galleon, DT);
			t++;
		}
		assertTrue(t * DT > 10, "accelerates too fast: " + t * DT + " s");
		double glide = 0;
		for (int i = 0; i < 20 * 60; i++) {
			glide += ph.step(ShipPhysics.Controls.COAST, galleon, DT).forward();
		}
		assertTrue(glide > 30, "not enough inertia: " + glide);
	}

	private static boolean land(double x, double z) {
		if (z < -120 || z > 120) {
			return true;
		}
		return Math.hypot(x - 200, z - 6) < 30;
	}

	private List<String> simulate(Route route, ShipPose start, int maxTicks, int stopAfterArrivals, ShipPose[] end) {
		ShipConfig cfg = Ships.GALLEON.defaults().get();
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
	void ferryAroundTheIslandAndBack() {
		Route route = new Route("galion", "minecraft:overworld");
		route.mode = Route.Mode.PINGPONG;
		route.points.add(new Waypoint(0, 62, 0, 20, "Port A"));
		route.points.add(new Waypoint(400, 62, 0, 20, "Port B"));
		ShipPose[] end = new ShipPose[1];
		List<String> events = simulate(route, new ShipPose(0, 62, 0, -90), 20 * 60 * 10, 3, end);
		assertTrue(events.contains("arrive Port B"), "never reached B: " + events + " at " + end[0]);
		assertTrue(events.indexOf("arrive Port B") < events.lastIndexOf("arrive Port A"), "did not come back: " + events);
		assertFalse(events.toString().contains("stuck"), events.toString());
	}

	@Test
	void routeWithTurnsStopsOnTheQuay() {
		Route route = new Route("tour", "minecraft:overworld");
		route.mode = Route.Mode.ONCE;
		route.points.add(new Waypoint(0, 62, 0, 0, "start"));
		route.points.add(new Waypoint(90, 62, 70, 0, null));
		route.points.add(new Waypoint(150, 62, -80, 0, null));
		route.points.add(new Waypoint(330, 62, -80, 0, null));
		route.points.add(new Waypoint(350, 62, 60, 10, "Quai"));
		ShipPose[] end = new ShipPose[1];
		List<String> events = simulate(route, new ShipPose(-30, 62, 0, -90), 20 * 60 * 8, 1, end);
		assertTrue(events.contains("arrive Quai"), "route not completed: " + events + " " + end[0]);
		assertTrue(Math.hypot(end[0].x() - 350, end[0].z() - 60) < 5, "stopped at " + end[0]);
	}
}
