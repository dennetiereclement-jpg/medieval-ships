package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.function.DoubleBinaryOperator;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.AirshipLayout;

/** The steampunk airship: shape, places, and flight (hover, climb, ceiling, landing, autopilot in 3D). */
class AirshipTest {
	private static final ShipType AIRSHIP = Ships.STEAMPUNK_AIRSHIP;
	private static final double DT = 0.05;

	/** Values printed by {@code python3 tools/airship_shape.py}. */
	@Test
	void matchesModelGenerator() {
		HullShape h = AIRSHIP.hull();
		double[][] hull = {
				{-6.0, 1.061405, 1.926105, -0.444898},
				{-2.0, 1.754349, 1.082603, -1.293878},
				{0.0, 1.800000, 1.000000, -1.400000},
				{3.0, 1.585258, 1.263572, -1.161224},
				{6.0, 0.865558, 2.211061, -0.444898}};
		for (double[] r : hull) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			assertEquals(r[2], h.railY(r[0]), 1e-5, "rail at " + r[0]);
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
		}
		double[][] balloon = {{-9.0, 2.225671}, {-5.0, 3.839759}, {-1.1, 4.25}, {3.0, 3.957091}, {7.5, 1.959077}};
		for (double[] r : balloon) {
			assertEquals(r[1], AirshipLayout.balloonRadius(r[0]), 1e-5, "balloon radius at " + r[0]);
		}
	}

	@Test
	void dimensionsAndPlaces() {
		ShipGeometry g = AIRSHIP.geometry();
		assertTrue(g.flying());
		assertFalse(Ships.GALLEY.geometry().flying());
		double balloonLength = AirshipLayout.BALLOON_HALF * (1 + AirshipLayout.BALLOON_REAR_T);
		assertEquals(18.2, balloonLength, 0.5, "balloon length");
		assertEquals(8.5, 2 * AirshipLayout.BALLOON_R, 1e-9, "balloon diameter");
		double length = AirshipLayout.NOSE_ROD_Z - (AirshipLayout.PROP_Z - 0.3);
		assertTrue(length > 24 && length < 28, "overall length " + length);
		assertEquals(15.2, 2 * AIRSHIP.hull().tip, 1e-9, "gondola length");
		double height = g.topY() - g.lowestY();
		assertTrue(height > 15 && height < 20, "overall height " + height);
		// gondola hangs 5 blocks under the balloon
		double gap = AirshipLayout.BALLOON_Y - AirshipLayout.BALLOON_R - AIRSHIP.hull().railY(0);
		assertEquals(5.15, gap, 0.2);
		assertEquals(6, g.seats().size(), "pilot + 5 passengers");
		assertTrue(g.seats().get(ShipGeometry.PILOT_SEAT).pilot());
		assertTrue(g.boundingRadius() >= 17.5, "the propeller is inside the bounding radius");
		assertTrue(g.aiReach() >= AirshipLayout.NOSE_ROD_Z);
		assertNotNull(AIRSHIP.defaults().get().flight);
		assertEquals(null, Ships.GALLEON.defaults().get().flight, "ships have no flight settings");
	}

	// ------------------------------------------------------------------ flight simulation

	/** A world with a height map: everything under ground(x, z) is solid, plus an optional roof. */
	private record World(DoubleBinaryOperator ground, double roofY, double roofMinX, double roofMaxX)
			implements ShipMover.Obstacles, Flight.Terrain {
		World(DoubleBinaryOperator ground) {
			this(ground, Double.NaN, 0, 0);
		}

		@Override
		public boolean blocked(double x, double y, double z) {
			if (y < ground.applyAsDouble(Math.floor(x), Math.floor(z))) {
				return true;
			}
			return !Double.isNaN(roofY) && x >= roofMinX && x <= roofMaxX && y >= roofY && y < roofY + 1;
		}

		@Override
		public double groundTop(double x, double z) {
			return ground.applyAsDouble(Math.floor(x), Math.floor(z));
		}
	}

	private static final class Sim {
		final ShipGeometry g = AIRSHIP.geometry();
		final ShipConfig cfg = AIRSHIP.defaults().get();
		final ShipPhysics physics = new ShipPhysics();
		final Flight flight = new Flight();
		ShipPose pose;
		int collisions;

		Sim(double x, double y, double z, double yaw) {
			pose = new ShipPose(x, y, z, yaw);
		}

		void tick(ShipPhysics.Controls c, double vy, World w) {
			Flight.Result r = Flight.tick(g, pose, physics, flight, c, vy, cfg, w, DT);
			pose = r.pose();
			collisions = Math.max(collisions, ShipMover.countCollisions(g, pose, w));
		}
	}

	@Test
	void hoversWithoutFalling() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(0, 90, 0, 0);
		for (int i = 0; i < 400; i++) {
			s.tick(ShipPhysics.Controls.COAST, 0, flat);
		}
		assertEquals(90, s.pose.y(), 1e-9, "no gravity: it stays where it is");
	}

	@Test
	void climbsAndDescendsSlowlyWithInertia() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(0, 90, 0, 0);
		FlightConfig f = s.cfg.flight;
		s.tick(ShipPhysics.Controls.COAST, Flight.manual(1, f), flat);
		assertTrue(s.flight.vy < f.climbSpeed * 0.1, "progressive climb");
		for (int i = 0; i < 100; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(1, f), flat);
		}
		assertEquals(f.climbSpeed, s.flight.vy, 1e-9);
		double top = s.pose.y();
		assertTrue(top > 96 && top < 100, "climbed about 7 blocks in 5 s: " + top);
		for (int i = 0; i < 60; i++) {
			s.tick(ShipPhysics.Controls.COAST, 0, flat);
		}
		assertEquals(0, s.flight.vy, 1e-9, "keys released: it stops and holds the altitude");
		double held = s.pose.y();
		assertTrue(held - top < 2.0, "smooth stop");
		for (int i = 0; i < 100; i++) {
			s.tick(ShipPhysics.Controls.COAST, 0, flat);
		}
		assertEquals(held, s.pose.y(), 1e-9);
	}

	@Test
	void landsOnTheGroundWithoutSinking() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(0, 72, 0, 0);
		for (int i = 0; i < 400; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(-1, s.cfg.flight), flat);
		}
		double keel = s.pose.y() + s.g.lowestY();
		assertTrue(keel >= 64 - 0.06 && keel < 64.2, "rests on the ground: keel at " + keel);
		assertEquals(0, s.collisions);
	}

	@Test
	void respectsTheCeilingAndRoofs() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(0, 270, 0, 0);
		for (int i = 0; i < 1000; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(1, s.cfg.flight), flat);
		}
		double top = s.pose.y() + s.g.topY();
		assertTrue(top <= s.cfg.flight.maxAltitude + 0.01 && top > s.cfg.flight.maxAltitude - 0.5, "top at " + top);
		// a roof over the balloon stops the climb
		World roof = new World((x, z) -> 64, 110, -20, 20);
		Sim r = new Sim(0, 90, 0, 0);
		for (int i = 0; i < 400; i++) {
			r.tick(ShipPhysics.Controls.COAST, Flight.manual(1, r.cfg.flight), roof);
		}
		assertTrue(r.pose.y() + r.g.topY() <= 110.01, "stopped under the roof");
		assertEquals(0, r.collisions);
	}

	@Test
	void fliesForwardAndTurnsGently() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(0, 90, 0, 0);
		for (int i = 0; i < 200; i++) {
			s.tick(new ShipPhysics.Controls(s.cfg.normalSpeed, 0), 0, flat);
		}
		assertTrue(s.pose.z() > 25, "went forward: " + s.pose.z());
		assertEquals(90, s.pose.y(), 1e-9, "level flight");
		double yaw0 = s.pose.yaw();
		for (int i = 0; i < 20; i++) {
			s.tick(new ShipPhysics.Controls(s.cfg.normalSpeed, 1), 0, flat);
		}
		double turned = Math.abs(ShipPose.wrapDegrees(s.pose.yaw() - yaw0));
		assertTrue(turned < 6, "no sharp turn in one second: " + turned);
	}

	@Test
	void blockedByAMountainItStops() {
		// a wall of rock 40 blocks ahead, too high to fly over manually at this altitude
		World wall = new World((x, z) -> z >= 40 ? 200 : 64);
		Sim s = new Sim(0, 90, 0, 0);
		for (int i = 0; i < 600; i++) {
			s.tick(new ShipPhysics.Controls(s.cfg.fastSpeed, 0), 0, wall);
		}
		assertEquals(0, s.collisions, "never inside the rock");
		assertTrue(s.pose.z() + s.g.aiReach() < 41, "stopped in front of it: nose at " + (s.pose.z() + s.g.aiReach()));
	}

	/** Autopilot: take-off from a stop, climb over a hill, come down at the other stop and wait. */
	@Test
	void autopilotFliesARouteIn3d() {
		// hill 30 blocks high between the two stops
		World hill = new World((x, z) -> z > 70 && z < 110 ? 94 : 64);
		Route route = new Route("air", "minecraft:overworld");
		route.air = true;
		route.mode = Route.Mode.ONCE;
		Waypoint a = new Waypoint(0, 70, 0, 5, "Capitale");
		Waypoint b = new Waypoint(0, 75, 180, 30, "Ville marchande");
		b.yaw = 90.0;
		route.points.add(a);
		route.points.add(b);
		Sim s = new Sim(0, 70, 0, 0);
		Autopilot ap = new Autopilot();
		ap.start(route, s.pose, s.cfg, s.g);
		double maxY = s.pose.y(), minClear = Double.MAX_VALUE;
		boolean arrived = false;
		Autopilot.Listener listener = new Autopilot.Listener() {
		};
		for (int i = 0; i < 20 * 300 && !arrived; i++) {
			Flight.Orders o = Flight.autopilot(ap, route, s.pose, s.physics, Gait.NORMAL, s.cfg, s.g, hill, listener);
			s.tick(o.controls(), o.desiredVy(), hill);
			maxY = Math.max(maxY, s.pose.y());
			double keel = s.pose.y() + s.g.lowestY();
			for (double dz = -10; dz <= 10; dz += 2) {
				minClear = Math.min(minClear, keel - hill.groundTop(s.pose.x(), s.pose.z() + dz));
			}
			arrived = ap.phase == Autopilot.Phase.DOCKED && ap.target == 1;
		}
		assertTrue(arrived, "docked at the second stop; at " + s.pose + " phase " + ap.phase);
		assertEquals(0, s.collisions, "never inside the hill");
		assertTrue(maxY + s.g.lowestY() > 94 + 3, "climbed over the hill: highest keel " + (maxY + s.g.lowestY()));
		assertTrue(minClear > 0.5, "always above the ground: " + minClear);
		assertEquals(75, s.pose.y() + s.g.hull().mainDeckY, 1.0, "came down to the stop's altitude");
		assertTrue(Math.hypot(s.pose.x() - b.x, s.pose.z() - b.z) < s.cfg.aiStopRadius + 0.5);
		// while waiting it turns to the stop's heading and holds its altitude
		for (int i = 0; i < 20 * 20; i++) {
			Flight.Orders o = Flight.autopilot(ap, route, s.pose, s.physics, Gait.NORMAL, s.cfg, s.g, hill, listener);
			s.tick(o.controls(), o.desiredVy(), hill);
		}
		assertEquals(90, s.pose.yaw(), 3, "faces the stop's heading");
		assertEquals(75, s.pose.y(), 0.2);
	}
}
