package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.function.DoubleBinaryOperator;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The steampunk hot-air balloon: shape, places, model, and its soft flight (hover, take-off, landing, placement). */
class BalloonTest {
	private static final ShipType TYPE = Ships.HOT_AIR_BALLOON;
	private static final ShipGeometry G = TYPE.geometry();
	private static final double DT = 0.05;

	/** Values printed by {@code python3 tools/balloon_shape.py}. */
	@Test
	void matchesModelGenerator() {
		HullShape h = TYPE.hull();
		double[][] hull = {
				{-3.5, 1.344230, 1.208289, -0.750024},
				{-2.0, 1.737799, 1.060811, -1.120416},
				{0.0, 1.850000, 1.000000, -1.300000},
				{2.0, 1.737799, 1.060811, -1.120416},
				{3.5, 1.344230, 1.208289, -0.750024}};
		for (double[] r : hull) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			assertEquals(r[2], h.railY(r[0]), 1e-5, "rail at " + r[0]);
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
		}
		double[][] balloon = {{5.0, 2.345000}, {7.0, 3.937260}, {10.0, 5.811220}, {13.0, 6.694258}, {16.0, 6.265442}, {18.5, 4.077046},
				{19.3, 0.596379}};
		for (double[] r : balloon) {
			assertEquals(r[1], BalloonLayout.balloonRadius(r[0]), 1e-5, "balloon radius at " + r[0]);
		}
		assertEquals(0.0, BalloonLayout.balloonRadius(BalloonLayout.TOP_Y), 1e-9);
		assertEquals(BalloonLayout.MOUTH_R, BalloonLayout.balloonRadius(BalloonLayout.MOUTH_Y), 1e-9);
	}

	@Test
	void aRoundEnvelopeSlightlyTallerThanWideOverASmallBasket() {
		assertTrue(G.flying());
		assertTrue(Ships.ALL.contains(TYPE));
		double width = 2 * BalloonLayout.R, height = BalloonLayout.TOP_Y - BalloonLayout.MOUTH_Y;
		assertTrue(height / width > 1.02 && height / width < 1.15, "slightly taller than wide: " + height / width);
		// genuinely round: the widest ring is near the middle, the profile is smooth (no step larger than a quarter block per
		// tenth of a block of height, except where the crown closes over the top like a sphere's pole)
		double widest = 0, widestY = 0, last = BalloonLayout.balloonRadius(BalloonLayout.MOUTH_Y);
		for (double y = BalloonLayout.MOUTH_Y; y <= BalloonLayout.TOP_Y; y += 0.1) {
			double r = BalloonLayout.balloonRadius(y);
			double step = y < BalloonLayout.fy(0.9) ? 0.26 : 1.2;
			assertTrue(Math.abs(r - last) < step, "smooth profile at " + y + ": " + last + " -> " + r);
			last = r;
			if (r > widest) {
				widest = r;
				widestY = y;
			}
		}
		assertEquals(BalloonLayout.R, widest, 0.05);
		double f = (widestY - BalloonLayout.MOUTH_Y) / height;
		assertTrue(f > 0.45 && f < 0.65, "widest a little above the middle: " + f);
		assertEquals(20, BalloonLayout.GORES);
		// the basket: a small boat hull, the balloon well clear above it
		assertEquals(10.2, 2 * TYPE.hull().tip, 1e-9, "basket length");
		assertTrue(2 * TYPE.hull().maxHalfWidth < 4.0, "a small basket");
		assertTrue(BalloonLayout.MOUTH_Y - TYPE.hull().railY(0) > 3.5, "the mouth hangs well above the rail");
		double total = G.topY() - G.lowestY();
		assertTrue(total > 20 && total < 23, "overall height " + total);
		assertTrue(G.boundingRadius() >= BalloonLayout.R, "the envelope is inside the bounding radius");
		assertTrue(G.lowestY() <= TYPE.hull().keelY(0) - 0.1, "the keel bar is the lowest point");
	}

	@Test
	void placesAndControls() {
		assertEquals(4, G.seats().size(), "the pilot and three passengers");
		assertTrue(G.seats().get(ShipGeometry.PILOT_SEAT).pilot());
		HullShape h = TYPE.hull();
		for (ShipGeometry.Seat s : G.seats()) {
			assertTrue(Math.abs(s.x()) < h.halfWidth(s.z()) - 0.3, "seat " + s.index() + " inside the basket");
			assertTrue(s.z() > h.deckMinZ && s.z() < h.deckMaxZ, "seat " + s.index() + " on the deck");
			double[] d = s.dismountLocal();
			assertTrue(Math.abs(d[0]) < h.halfWidth(d[2]) && Math.abs(d[1] - h.mainDeckY) < 0.1, "seat " + s.index() + " steps off onto the deck");
		}
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertEquals(BalloonLayout.PILOT_Z, pilot.z(), 1e-9);
		assertTrue(G.helm() != null && G.helm().maxZ() > pilot.z(), "the burner's valves are in front of the pilot");
		ShipConfig c = TYPE.defaults().get();
		c.sanitize();
		assertNotNull(c.flight, "it flies");
		ShipConfig airship = Ships.STEAMPUNK_AIRSHIP.defaults().get();
		airship.sanitize();
		assertTrue(c.normalSpeed < airship.normalSpeed && c.acceleration < airship.acceleration, "slower and lighter than the airship");
		assertTrue(c.flight.climbSpeed < airship.flight.climbSpeed && c.flight.verticalAcceleration < airship.flight.verticalAcceleration,
				"a soft, slow climb");
		assertTrue(c.flight.sway > airship.flight.sway, "sways more than the airship");
		assertTrue(c.flight.bankAngle > 0 && Flight.bankLimit(G, c.flight) > 0);
	}

	/** The model as the mod reads it: the burner's flame flares with the climb, the wheel turns, the lanterns hang in their bones. */
	@Test
	void modelBonesAndAnimations() throws Exception {
		BbModel model;
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/hot_air_balloon.bbmodel"),
				StandardCharsets.UTF_8)) {
			model = new BbModel(r);
		}
		for (String bone : new String[] {"burner_flame", "burner_core", "helm_wheel", "side_wheel", "pinion", "lantern_bow_p", "lantern_bow_s",
				"lantern_stern_p", "lantern_stern_s"}) {
			assertNotNull(model.bonesByName.get(bone), "bone " + bone);
		}
		for (String anim : new String[] {"steer", "elevator", "flag_wave", "engine", "lantern_sway"}) {
			assertNotNull(model.animations.get(anim), "animation " + anim);
		}
		assertTrue(flameTop(model, 2f) > flameTop(model, 1f) + 0.5, "the flame flares while climbing");
		assertTrue(flameTop(model, 0f) < flameTop(model, 1f) - 0.2, "and shrinks while descending");
		assertTrue(flameTop(model, 1f) > BalloonLayout.BURNER_Y + 0.8, "the flame rises above the burner");
	}

	/** Highest point of the glowing flame quads at this climb (elevator 0..2). */
	private static float flameTop(BbModel model, float climb) {
		BbModel.Pose pose = model.newPose();
		model.apply(pose, "elevator", climb, 1f);
		float[] top = {Float.NEGATIVE_INFINITY};
		model.render(pose, (p, uv, n, glow) -> {
			if (!glow) {
				return;
			}
			for (int k = 1; k < p.length; k += 3) {
				// only the flame, over the burner (the lit windows and the lanterns are lower)
				if (p[k] > BalloonLayout.BURNER_Y && Math.abs(p[k - 1]) < 1.2 && Math.abs(p[k + 1]) < 1.2) {
					top[0] = Math.max(top[0], p[k]);
				}
			}
		});
		return top[0];
	}

	// ------------------------------------------------------------------ flight

	/** A world with a height map: everything under ground(x, z) is solid. */
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

	private static final class Sim {
		final ShipConfig cfg = TYPE.defaults().get();
		final ShipPhysics physics = new ShipPhysics();
		final Flight flight = new Flight();
		ShipPose pose;
		int collisions;

		Sim(double y) {
			cfg.sanitize();
			pose = new ShipPose(0, y, 0, 0);
		}

		void tick(ShipPhysics.Controls c, double vy, World w) {
			Flight.Result r = Flight.tick(G, pose, physics, flight, c, vy, cfg, w, DT);
			pose = r.pose();
			collisions = Math.max(collisions, ShipMover.countCollisions(G, pose, w));
		}
	}

	@Test
	void hoversWithoutFalling() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(90);
		for (int i = 0; i < 400; i++) {
			s.tick(ShipPhysics.Controls.COAST, 0, flat);
		}
		assertEquals(90, s.pose.y(), 1e-9, "no gravity: it stays where it is");
		assertEquals(0, s.collisions);
	}

	@Test
	void takesOffProgressivelyAndLandsSoftly() {
		World flat = new World((x, z) -> 64);
		Sim s = new Sim(64 + 1.0 - G.lowestY());
		FlightConfig f = s.cfg.flight;
		double start = s.pose.y();
		for (int i = 0; i < 20; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(1, f), flat);
		}
		assertTrue(s.flight.vy < f.climbSpeed * 0.4, "after one second it is still gathering way: " + s.flight.vy);
		assertTrue(s.pose.y() - start < 0.4, "a gentle lift-off: " + (s.pose.y() - start));
		for (int i = 0; i < 100; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(1, f), flat);
		}
		assertEquals(f.climbSpeed, s.flight.vy, 1e-9, "full climb after six seconds");
		double climbed = s.pose.y() - start;
		assertTrue(climbed > 3.5 && climbed < 6.0, "climbed slowly: " + climbed);
		for (int i = 0; i < 80; i++) {
			s.tick(ShipPhysics.Controls.COAST, 0, flat);
		}
		assertEquals(0, s.flight.vy, 1e-9, "valves closed: it holds the altitude");
		double held = s.pose.y();
		// coming down: it slows before the ground and settles on it without sinking or bouncing
		for (int i = 0; i < 600; i++) {
			s.tick(ShipPhysics.Controls.COAST, Flight.manual(-1, f), flat);
		}
		double keel = s.pose.y() + G.lowestY();
		assertTrue(keel >= 64 - 0.06 && keel < 64.3, "rests on the ground: keel at " + keel);
		assertTrue(s.pose.y() < held, "came down");
		assertEquals(0, s.collisions, "never into the ground");
		assertEquals(0, s.flight.vy, 1e-9, "stopped by the ground");
	}

	@Test
	void fitsInTheAirAboveTheGroundButNotInIt() {
		World flat = new World((x, z) -> 64);
		ShipPose aloft = new ShipPose(10, 64 + 1.0 - G.lowestY(), 10, 30);
		assertFalse(ShipMover.collides(G, aloft, flat), "placed a block above the ground: inside nothing");
		ShipPose low = new ShipPose(10, 64 - 0.5 - G.lowestY(), 10, 30);
		assertTrue(ShipMover.collides(G, low, flat), "its keel in the ground: refused");
		// a tree beside it touches the envelope, not the basket
		World tree = new World((x, z) -> x >= 14 && x < 15 && z >= 10 && z < 11 ? 80 : 64);
		assertTrue(ShipMover.collides(G, aloft, tree), "the envelope hits a tall tree beside the basket");
		assertEquals(0, ShipMover.countCollisions(G, aloft, flat));
	}

	@Test
	void autopilotKeepsItsClearanceOverAHill() {
		World hills = new World((x, z) -> x > 30 && x < 50 ? 84 : 64);
		ShipConfig cfg = TYPE.defaults().get();
		cfg.sanitize();
		Waypoint wp = new Waypoint(80, 70, 0, 0, "Colline");
		ShipPose pose = new ShipPose(20, 70, 0, -90); // heading +x
		Flight.Plan plan = Flight.plan(wp, 60, pose, cfg.normalSpeed, G, cfg.flight, hills);
		assertTrue(plan.requiredY() + G.lowestY() >= 84 + cfg.flight.aiClearance - 1e-6, "climbs over the hill with its clearance: " + plan.requiredY());
		assertTrue(plan.targetY() >= plan.requiredY() - 1e-9);
	}
}
