package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.function.DoubleBinaryOperator;

import org.junit.jupiter.api.Test;

import com.google.gson.Gson;

/**
 * Navigation of the two big vessels with rooms in the pure-Java simulation used by the other
 * autopilot tests: the Old Corsair follows a sea route round a rock with its wide turns, slows down
 * before its stops, waits there and leaves again; the Sky Leviathan takes off, climbs to the cruising
 * altitude of its waypoints and holds it, flies over a hill and a narrow tower off its centre line,
 * comes down to a mooring stop without touching the ground, waits facing the stop's heading and leaves.
 */
class NewVehiclesNavigationTest {
	private static final double DT = 0.05;

	/** Events and per-tick samples of a run. */
	private static final class Log implements Autopilot.Listener {
		final List<String> events = new ArrayList<>();
		final List<Integer> eventTicks = new ArrayList<>();
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
		public void stuck() {
			add("stuck");
		}

		@Override
		public void finished() {
			add("finished");
		}

		private void add(String e) {
			events.add(e);
			eventTicks.add(tick);
		}

		int tickOf(String e, int nth) {
			int seen = 0;
			for (int i = 0; i < events.size(); i++) {
				if (events.get(i).equals(e) && seen++ == nth) {
					return eventTicks.get(i);
				}
			}
			return -1;
		}
	}

	// ------------------------------------------------------------------ the Old Corsair at sea

	private static final ShipGeometry CG = Ships.OLD_CORSAIR.geometry();

	/** Open sea with a coast in the north and the south, and a rock (radius 10) on the direct line A -> B. */
	private static boolean land(double x, double z) {
		return z < -90 || z > 120 || Math.hypot(x - 150, z) < 10;
	}

	@Test
	void corsairSailsARouteAroundARockStopsWaitsAndLeaves() {
		ShipConfig cfg = Ships.OLD_CORSAIR.defaults().get();
		Route route = new Route("corsaire", "minecraft:overworld");
		route.mode = Route.Mode.PINGPONG;
		route.points.add(new Waypoint(0, 62, 0, 10, "Port A"));
		route.points.add(new Waypoint(300, 62, 0, 10, "Port B"));
		ShipPhysics ph = new ShipPhysics();
		ShipPose pose = new ShipPose(0, 62, 0, -90);
		Autopilot ap = new Autopilot();
		ap.start(route, pose, cfg, CG);
		assertEquals(Autopilot.Phase.DOCKED, ap.phase, "starts at its home port, moored");
		ShipMover.Obstacles obstacles = (x, y, z) -> land(x, z) && y < 64;
		Autopilot.Navigator nav = (x, z) -> !land(x, z);
		Log log = new Log();
		double maxSpeed = 0, speedAt60 = Double.NaN, speedAt15 = Double.NaN, minRock = Double.MAX_VALUE;
		double maxYawRate = 0;
		List<double[]> track = new ArrayList<>();
		int dockedTicksAtB = 0;
		double maxDriftAtB = 0;
		for (int t = 0; t < 20 * 60 * 6 && log.tickOf("arrive Port A", 0) < 0; t++) {
			log.tick = t;
			ShipPhysics.Controls c = ap.tick(route, pose, ph.speed, ph.yawRate, Gait.NORMAL, cfg, CG, nav, log);
			ShipPhysics.Step s = ph.step(c, cfg, DT);
			ShipMover.Result r = ShipMover.move(CG, pose, s.forward(), s.yaw(), 0, obstacles);
			ph.collide(r.forwardBlocked(), r.rotationBlocked());
			pose = r.pose();
			assertEquals(0, ShipMover.countCollisions(CG, pose, obstacles), "corsair inside the land at tick " + t + " " + pose);
			maxSpeed = Math.max(maxSpeed, ph.speed);
			maxYawRate = Math.max(maxYawRate, Math.abs(ph.yawRate));
			minRock = Math.min(minRock, Math.hypot(pose.x() - 150, pose.z()));
			boolean toB = ap.target == 1 && ap.phase == Autopilot.Phase.SAILING;
			double toStop = Math.hypot(300 - pose.x(), pose.z());
			if (toB && Double.isNaN(speedAt60) && toStop < 60) {
				speedAt60 = ph.speed;
			}
			if (toB && Double.isNaN(speedAt15) && toStop < 15) {
				speedAt15 = ph.speed;
			}
			if (ap.phase == Autopilot.Phase.DOCKED && ap.target == 1) {
				dockedTicksAtB++;
				maxDriftAtB = Math.max(maxDriftAtB, toStop);
			}
			if (t % 10 == 0 && ap.phase == Autopilot.Phase.SAILING) {
				track.add(new double[] {pose.x(), pose.z(), pose.yaw(), ph.speed});
			}
		}
		List<String> ev = log.events;
		assertTrue(ev.contains("arrive Port B"), "never reached Port B: " + ev + " at " + pose);
		assertTrue(ev.contains("arrive Port A"), "never came back to Port A: " + ev + " at " + pose);
		assertFalse(ev.contains("stuck"), "stuck: " + ev);
		assertEquals("depart Port A", ev.get(0), "leaves its home port after the wait: " + ev);
		assertTrue(log.tickOf("depart Port A", 0) >= 10 * 20 - 2, "waited 10 s at Port A before leaving: " + log.tickOf("depart Port A", 0));
		int arrB = log.tickOf("arrive Port B", 0), depB = log.tickOf("depart Port B", 0);
		assertTrue(depB - arrB >= 10 * 20 - 2 && depB - arrB <= 10 * 20 + 2, "waits 10 s at Port B: " + (depB - arrB) + " ticks");
		assertTrue(dockedTicksAtB >= 199, "moored at Port B for the whole wait: " + dockedTicksAtB);
		assertTrue(maxDriftAtB < cfg.aiStopRadius + 1.0, "stays at the quay while waiting (drift " + maxDriftAtB + ")");
		assertTrue(minRock > 10 + CG.aiHalfWidth() - 1.5, "kept clear of the rock: " + minRock);
		// cruising, then slowing down before the stop
		assertTrue(maxSpeed > cfg.normalSpeed - 0.4 && maxSpeed < cfg.normalSpeed + 0.4, "cruises at its normal speed: " + maxSpeed);
		assertTrue(speedAt60 > cfg.normalSpeed * 0.6, "still cruising 60 blocks before the stop: " + speedAt60);
		assertTrue(speedAt15 < cfg.normalSpeed * 0.6 && speedAt15 < speedAt60 - 1.0, "slowing down before the stop: " + speedAt60 + " -> " + speedAt15);
		// a big sailing ship turns slowly, on a wide circle
		assertTrue(maxYawRate <= cfg.maxTurnRate + 1e-6, "turn rate within its limit: " + maxYawRate);
		double minRadius = Double.MAX_VALUE;
		for (int i = 1; i < track.size(); i++) {
			double[] a = track.get(i - 1), b = track.get(i);
			double dYaw = Math.toRadians(Math.abs(ShipPose.wrapDegrees(b[2] - a[2])));
			double ds = Math.hypot(b[0] - a[0], b[1] - a[1]);
			if (dYaw > Math.toRadians(1.0) && b[3] > 2.5) {
				minRadius = Math.min(minRadius, ds / dYaw);
			}
		}
		assertTrue(minRadius > 20 && minRadius < Double.MAX_VALUE, "turns on a wide radius when under way: " + minRadius);
	}

	/** At its cruising speed, a full turn takes a big circle (much wider than the galleon's). */
	@Test
	void corsairTurningCircleAndStoppingDistance() {
		ShipConfig cfg = Ships.OLD_CORSAIR.defaults().get();
		ShipPhysics ph = new ShipPhysics();
		ShipPose pose = new ShipPose(0, 62, 0, 0);
		for (int i = 0; i < 20 * 40; i++) {
			ShipPhysics.Step s = ph.step(new ShipPhysics.Controls(cfg.normalSpeed, 0), cfg, DT);
			pose = pose.moved(-Math.sin(Math.toRadians(pose.yaw())) * s.forward(), 0, Math.cos(Math.toRadians(pose.yaw())) * s.forward(), s.yaw());
		}
		double minX = Double.MAX_VALUE, maxX = -Double.MAX_VALUE;
		double turned = 0;
		for (int i = 0; i < 20 * 120 && turned < 360; i++) {
			ShipPhysics.Step s = ph.step(new ShipPhysics.Controls(cfg.normalSpeed, 1), cfg, DT);
			turned += s.yaw();
			pose = pose.moved(-Math.sin(Math.toRadians(pose.yaw())) * s.forward(), 0, Math.cos(Math.toRadians(pose.yaw())) * s.forward(), s.yaw());
			minX = Math.min(minX, pose.x());
			maxX = Math.max(maxX, pose.x());
		}
		double diameter = maxX - minX;
		assertTrue(turned >= 359, "completes the turn: " + turned);
		assertTrue(diameter > 2 * 20 && diameter < 2 * 80, "turning circle diameter " + diameter);
		// stopping from cruise: a long glide
		double run = 0;
		for (int i = 0; i < 20 * 60 && ph.speed > 0.05; i++) {
			run += ph.step(new ShipPhysics.Controls(0, 0), cfg, DT).forward();
		}
		assertTrue(run > 4 && run < 60, "stopping distance from cruise " + run);
		// the probes cover the bowsprit and the boom beyond the hull, and the keel
		assertEquals(CorsairLayout.BOWSPRIT_TIP[2], CG.aiReach(), 1e-9);
		assertTrue(CG.aiBack() >= CorsairLayout.TRANSOM_Z * -1, "aiBack covers the stern: " + CG.aiBack());
		assertTrue(CG.aiHalfWidth() >= CorsairLayout.MAX_HALF_WIDTH, "aiHalfWidth covers the beam");
		assertEquals(-CorsairLayout.KEEL_DEPTH, CG.lowestY(), 1e-9);
		double front = -1e9, back = 1e9, low = 1e9;
		for (double[] p : CG.probes()) {
			front = Math.max(front, p[2]);
			back = Math.min(back, p[2]);
			low = Math.min(low, p[1]);
		}
		assertTrue(front >= CorsairLayout.BOWSPRIT_TIP[2] - 0.01 && back <= CorsairLayout.BOOM_END_Z + 0.01, "probes from " + back + " to " + front);
		assertTrue(low <= -CorsairLayout.KEEL_DEPTH + 0.6, "probes reach down to the keel: " + low);
	}

	// ------------------------------------------------------------------ the Sky Leviathan in the air

	private static final ShipGeometry LG = Ships.SKY_LEVIATHAN.geometry();

	/** Height map world: solid under ground(x, z). */
	private record World(DoubleBinaryOperator ground) implements ShipMover.Obstacles, Flight.Terrain {
		@Override
		public boolean blocked(double x, double y, double z) {
			return y < ground.applyAsDouble(Math.floor(x), Math.floor(z));
		}

		@Override
		public double groundTop(double x, double z) {
			return ground.applyAsDouble(Math.floor(x), Math.floor(z));
		}
	}

	/** Flat ground at 64, a hill 30 high across the way, and a narrow tower 6 to 10 blocks off the centre line. */
	private static double terrain(double x, double z) {
		if (z > 140 && z < 175 && Math.abs(x) < 60) {
			return 94; // hill
		}
		if (z >= 480 && z < 484 && x >= 6 && x < 10) {
			return 124; // narrow tower: between the old lateral samples of the altitude planning
		}
		return 64;
	}

	@Test
	void leviathanTakesOffClimbsHoldsAltitudeMoorsAndLeaves() {
		World w = new World(NewVehiclesNavigationTest::terrain);
		ShipConfig cfg = Ships.SKY_LEVIATHAN.defaults().get();
		FlightConfig f = cfg.flight;
		double keel = LG.lowestY();
		double cruise = 125;
		Route route = new Route("leviathan", "minecraft:overworld");
		route.air = true;
		route.mode = Route.Mode.PINGPONG;
		// a mooring stop at the deck height of a quay on the ground: far lower than the hanging ventral fin allows
		Waypoint a = new Waypoint(0, 64 - keel + 3, 0, 5, "Mouillage A");
		Waypoint w1 = new Waypoint(0, cruise, 250, 0, null);
		Waypoint w2 = new Waypoint(0, cruise, 400, 0, null);
		Waypoint b = new Waypoint(0, 66, 650, 40, "Mouillage B");
		b.yaw = 90.0;
		route.points.add(a);
		route.points.add(w1);
		route.points.add(w2);
		route.points.add(b);
		ShipPhysics ph = new ShipPhysics();
		Flight flight = new Flight();
		ShipPose pose = new ShipPose(0, a.y, 0, 0);
		Autopilot ap = new Autopilot();
		ap.start(route, pose, cfg, LG);
		assertEquals(Autopilot.Phase.DOCKED, ap.phase, "starts moored at its first stop");
		Log log = new Log();
		int collisions = 0;
		double minClear = Double.MAX_VALUE, maxDevW1W2 = 0, yAtW1 = Double.NaN, maxY = -1e9, overHill = -1e9, overTower = -1e9;
		double maxDock = 0;
		boolean stuck = false;
		double dockedYMin = Double.MAX_VALUE, dockedYMax = -Double.MAX_VALUE;
		int t;
		for (t = 0; t < 20 * 60 * 8 && log.tickOf("depart Mouillage B", 0) < 0; t++) {
			log.tick = t;
			Flight.Orders o = Flight.autopilot(ap, route, pose, ph, Gait.NORMAL, cfg, LG, w, log);
			Flight.Result r = Flight.tick(LG, pose, ph, flight, o.controls(), o.desiredVy(), cfg, w, DT);
			pose = r.pose();
			collisions = Math.max(collisions, ShipMover.countCollisions(LG, pose, w));
			maxY = Math.max(maxY, pose.y());
			double ground = Flight.groundAlong(pose, pose.yaw(), LG.aiBack(), LG.aiReach(), LG.aiHalfWidth(), w);
			minClear = Math.min(minClear, pose.y() + keel - ground);
			if (pose.z() > 140 && pose.z() < 175) {
				overHill = Math.max(overHill, pose.y());
			}
			if (Math.abs(pose.z() - 482) < 3) {
				overTower = Math.max(overTower, pose.y());
			}
			if (ap.target == 2 && ap.phase == Autopilot.Phase.SAILING) {
				if (Double.isNaN(yAtW1)) {
					yAtW1 = pose.y();
				}
				if (pose.z() > 270 && pose.z() < 380) {
					maxDevW1W2 = Math.max(maxDevW1W2, Math.abs(pose.y() + LG.hull().mainDeckY - cruise));
				}
			}
			if (ap.phase == Autopilot.Phase.DOCKED && ap.target == 3) {
				maxDock = Math.max(maxDock, Math.hypot(pose.x() - b.x, pose.z() - b.z));
				if (log.tickOf("arrive Mouillage B", 0) >= 0 && t > log.tickOf("arrive Mouillage B", 0) + 60) {
					dockedYMin = Math.min(dockedYMin, pose.y());
					dockedYMax = Math.max(dockedYMax, pose.y());
				}
			}
			stuck |= log.events.contains("stuck");
		}
		List<String> ev = log.events;
		assertFalse(stuck, "stuck: " + ev + " at " + pose);
		assertTrue(ev.contains("arrive Mouillage B"), "never moored at B: " + ev + " at " + pose + " phase " + ap.phase + " target " + ap.target);
		assertEquals(0, collisions, "never inside the ground, the hill or the tower");
		assertTrue(log.tickOf("depart Mouillage A", 0) >= 5 * 20 - 2, "waited at A before leaving");
		// climbed to the cruising altitude and held it between the two cruise waypoints
		assertTrue(maxY + LG.hull().mainDeckY > cruise - 1.5, "climbed to the cruising altitude: " + maxY);
		assertTrue(maxDevW1W2 < 1.5, "holds the cruising altitude between the waypoints: deviation " + maxDevW1W2);
		assertTrue(overHill + keel > 94 + 1, "over the hill: lowest point " + (overHill + keel));
		assertTrue(overTower + keel > 124, "over the narrow tower beside its centre line: lowest point " + (overTower + keel));
		// came down to the mooring stop, but never lower than its landing clearance
		assertTrue(minClear > 0.5, "never touches the ground: clearance " + minClear);
		int arrB = log.tickOf("arrive Mouillage B", 0), depB = log.tickOf("depart Mouillage B", 0);
		assertTrue(depB - arrB >= 40 * 20 - 2, "waited 40 s at B: " + (depB - arrB));
		assertTrue(maxDock < cfg.aiStopRadius + 1.0, "stays over the stop while waiting: " + maxDock);
		double landed = 64 + f.aiLandingClearance - keel;
		assertEquals(landed, dockedYMin, 0.6, "moored at its landing clearance over the ground (fin tip " + (dockedYMin + keel) + ")");
		assertTrue(dockedYMax - dockedYMin < 0.6, "holds its altitude while waiting: " + dockedYMin + " .. " + dockedYMax);
		assertEquals(90, ShipPose.wrapDegrees(pose.yaw()), 6, "turned to the stop's heading while waiting");
		// leaves again: climbs back towards the cruise waypoint
		double y0 = pose.y(), z0 = pose.z();
		for (int i = 0; i < 20 * 60; i++) {
			Flight.Orders o = Flight.autopilot(ap, route, pose, ph, Gait.NORMAL, cfg, LG, w, log);
			Flight.Result r = Flight.tick(LG, pose, ph, flight, o.controls(), o.desiredVy(), cfg, w, DT);
			pose = r.pose();
			collisions = Math.max(collisions, ShipMover.countCollisions(LG, pose, w));
		}
		assertEquals(0, collisions, "never inside anything after leaving");
		assertTrue(pose.y() - y0 > 10 && z0 - pose.z() > 20, "leaves B: climbs and heads back (" + y0 + " -> " + pose.y() + ", z " + z0 + " -> "
				+ pose.z() + ")");
	}

	/** The altitude planning sees a narrow (4 block) tower anywhere under the 26 block wide balloon, not only on 3 lines. */
	@Test
	void leviathanAltitudePlanningCoversItsWholeWidth() {
		ShipPose pose = new ShipPose(0, 100, 0, 0);
		double half = LG.aiHalfWidth();
		assertTrue(half >= LeviathanLayout.BALLOON_HW, "aiHalfWidth covers the balloon: " + half);
		for (double x0 = Math.floor(-half) + 1; x0 + 4 <= Math.ceil(half); x0 += 1.0) {
			double px = x0;
			Flight.Terrain tower = (gx, gz) -> Math.floor(gx) >= px && Math.floor(gx) < px + 4 && Math.floor(gz) >= 20 && Math.floor(gz) < 24 ? 90 : 64;
			double top = Flight.groundAlong(pose, 0, LG.aiBack(), 30, half, tower);
			assertEquals(90, top, 1e-9, "a 4 block tower at x=" + px + ".." + (px + 4) + " is seen");
		}
		// the probes cover the balloon top and sides, the spikes, the fins and the keel of the hanging ship
		double front = -1e9, back = 1e9, low = 1e9, top = -1e9, side = 0;
		for (double[] p : LG.probes()) {
			front = Math.max(front, p[2]);
			back = Math.min(back, p[2]);
			low = Math.min(low, p[1]);
			top = Math.max(top, p[1]);
			side = Math.max(side, Math.abs(p[0]));
		}
		assertTrue(front >= LeviathanLayout.NOSE_SPIKE_Z - 0.01, "nose spike probed: " + front);
		assertTrue(back <= LeviathanLayout.TAIL_SPIKE_Z + 0.01, "tail probed: " + back);
		assertTrue(top >= LeviathanLayout.BALLOON_Y + LeviathanLayout.BALLOON_HH - 0.2, "balloon top probed: " + top);
		assertTrue(side >= LeviathanLayout.BALLOON_HW - 0.2, "balloon sides probed: " + side);
		assertTrue(low <= LG.lowestY() + 0.5, "lowest point (ventral fin) probed: " + low + " / " + LG.lowestY());
		assertTrue(LG.aiReach() >= front - 0.01 && LG.aiBack() >= -back - 0.01, "aiReach / aiBack cover the probes");
		// the ceiling uses topY (the masthead); the flag finial probe is half a block above it
		assertTrue(LG.topY() >= top - 0.6, "topY covers the probes: " + LG.topY() + " / " + top);
	}

	/** Routes are saved as JSON in the world data (ShipData): every waypoint option survives. */
	@Test
	void routesSurviveTheirJsonRoundTrip() {
		Route r = new Route("ciel", "minecraft:overworld");
		r.air = true;
		r.mode = Route.Mode.LOOP;
		Waypoint s = new Waypoint(10.5, 120.0, -3.5, 30, "Port");
		s.yaw = 90.0;
		s.speed = 3.0;
		s.gait = "slow";
		r.points.add(s);
		r.points.add(new Waypoint(200, 140, 50, 0, null));
		Gson gson = new Gson();
		Route back = gson.fromJson(gson.toJson(r), Route.class);
		assertEquals("ciel", back.name);
		assertTrue(back.air);
		assertEquals(Route.Mode.LOOP, back.mode);
		assertEquals(2, back.size());
		Waypoint s2 = back.get(0);
		assertEquals(120.0, s2.y, 1e-9);
		assertEquals(30, s2.waitSeconds);
		assertEquals(90.0, s2.yaw, 1e-9);
		assertEquals(3.0, s2.speed, 1e-9);
		assertEquals("slow", s2.gait);
		assertEquals("Port", s2.name);
		assertFalse(back.get(1).isStop());
	}
}
