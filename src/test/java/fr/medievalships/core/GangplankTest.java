package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.io.Reader;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonParser;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/** The boarding gangplank: frame, animation, walkable steps, stairs, landing search, clearance, spec files. */
class GangplankTest {
	private static final double EPS = 1e-9;

	private static Gangplank.Spec spec(String side, double width, double length, double minA, double maxA, double maxDrop) {
		String json = "{\"side\":\"" + side + "\",\"hinge\":[" + ("port".equals(side) ? "2.0" : "-2.0") + ",2.0,1.0],\"width\":" + width
				+ ",\"length\":" + length + ",\"style\":\"wood\",\"lever\":[0.5,0.6,0.0],\"step\":["
				+ ("port".equals(side) ? "0.8,0.6,0.1,1.9,2.0,1.9" : "-1.9,0.6,0.1,-0.8,2.0,1.9") + "],\"angles\":[" + minA + "," + maxA
				+ "],\"max_drop\":" + maxDrop + "}";
		return Gangplank.parse("test", JsonParser.parseString(json).getAsJsonObject());
	}

	// ------------------------------------------------------------------ frame

	@Test
	void frameMapsThePlankOutboardAndDown() {
		for (String side : new String[] {"port", "starboard"}) {
			Gangplank.Spec s = spec(side, 2, 4, -15, 35, 3);
			int o = s.o();
			assertEquals("port".equals(side) ? 1 : -1, o);
			double[] h = s.point(20, 0, 0, 0);
			assertArrayEquals(new double[] {s.hx(), s.hy(), s.hz()}, h, "hinge");
			// horizontal: the tip is `length` outboard, at hinge height
			double[] tip0 = s.point(0, 4, 0, 0);
			assertArrayEquals(new double[] {s.hx() + o * 4, s.hy(), s.hz()}, tip0, "flat tip");
			// down 30 degrees: the tip is lower and nearer
			double[] tip = s.point(30, 4, 0, 0);
			assertEquals(s.hy() - 2.0, tip[1], 1e-9);
			assertEquals(s.hx() + o * 4 * Math.cos(Math.toRadians(30)), tip[0], 1e-9);
			// stowed upright: the tip straight above the hinge, the walking surface facing inboard
			double[] up = s.point(-90, 4, 0, 0);
			assertEquals(s.hx(), up[0], 1e-9);
			assertEquals(s.hy() + 4, up[1], 1e-9);
			double[] above = s.point(-90, 2, 0.5, 0);
			assertEquals(-o * 0.5, above[0] - s.hx(), 1e-9, "the top surface faces inboard when raised");
			// w runs along the keel, mirrored on the starboard side (the model turned 180 degrees)
			assertEquals(s.hz() + o * 0.7, s.point(10, 1, 0, 0.7)[2], 1e-9);
		}
	}

	/** The renderer's transform (translate to the hinge, turn 180 degrees about y for starboard, rotate -a about z) is the spec's formula. */
	@Test
	void rendererTransformMatchesTheFormula() {
		for (String side : new String[] {"port", "starboard"}) {
			Gangplank.Spec s = spec(side, 2.5, 4.5, -15, 35, 3);
			for (double a : new double[] {-90, -40, 0, 17, 33}) {
				for (double[] m : new double[][] {{0, 0, 0}, {4.5, 0, 1.2}, {2.0, 0.8, -1.25}, {3.3, -0.2, 0.4}}) {
					// rotate about +z by -a (right handed): x' = x cos t - y sin t, y' = x sin t + y cos t
					double t = Math.toRadians(-a);
					double x = m[0] * Math.cos(t) - m[1] * Math.sin(t), y = m[0] * Math.sin(t) + m[1] * Math.cos(t), z = m[2];
					if (s.o() < 0) { // rotation of 180 degrees about +y
						x = -x;
						z = -z;
					}
					double[] r = {s.hx() + x, s.hy() + y, s.hz() + z};
					assertArrayEquals(s.point(a, m[0], m[1], m[2]), r, side + " a=" + a);
				}
			}
		}
	}

	private static void assertArrayEquals(double[] exp, double[] act, String msg) {
		for (int i = 0; i < exp.length; i++) {
			assertEquals(exp[i], act[i], 1e-9, msg + " [" + i + "]");
		}
	}

	// ------------------------------------------------------------------ animation

	@Test
	void animationGoesFromStowedToTargetAndBack() {
		Gangplank.Spec s = spec("starboard", 2, 4, -15, 35, 3);
		double target = 22;
		assertEquals(s.stowedAngle(), Gangplank.angle(s, Gangplank.State.RETRACTED, 999, target), EPS);
		assertEquals(target, Gangplank.angle(s, Gangplank.State.DEPLOYED, 0, target), EPS);
		assertEquals(s.stowedAngle(), Gangplank.angle(s, Gangplank.State.DEPLOYING, 0, target), EPS);
		assertEquals(target, Gangplank.angle(s, Gangplank.State.DEPLOYING, Gangplank.DURATION, target), EPS);
		assertEquals(target, Gangplank.angle(s, Gangplank.State.RETRACTING, 0, target), EPS);
		assertEquals(s.stowedAngle(), Gangplank.angle(s, Gangplank.State.RETRACTING, Gangplank.DURATION, target), EPS);
		// 2 to 4 seconds, and the swing stays between the end angles (a few degrees of unlock and settle)
		assertTrue(Gangplank.DURATION >= 40 && Gangplank.DURATION <= 80);
		double last = -1e9;
		for (int k = 0; k <= Gangplank.DURATION * 4; k++) {
			double a = Gangplank.angle(s, Gangplank.State.DEPLOYING, k / 4.0, target);
			assertTrue(a >= s.stowedAngle() - 3.5 && a <= target + 0.01, "angle " + a);
			double p = k / (Gangplank.DURATION * 4.0);
			if (p > 0.12 && p < 0.86) {
				assertTrue(a >= last - 1e-9, "the swing goes one way");
			}
			last = a;
		}
		// the lever flips at the start of a move
		assertEquals(0, Gangplank.leverPosition(Gangplank.State.RETRACTED, 0), EPS);
		assertEquals(1, Gangplank.leverPosition(Gangplank.State.DEPLOYING, 10), EPS);
		assertEquals(0, Gangplank.leverPosition(Gangplank.State.RETRACTING, 10), EPS);
	}

	// ------------------------------------------------------------------ collisions

	@Test
	void stepsFollowTheSlopeAndAreWalkableBothWays() {
		for (String side : new String[] {"port", "starboard"}) {
			for (double a : new double[] {-15, -5, 0, 8, 20, 30, 35}) {
				Gangplank.Spec s = spec(side, 2, 4, -15, 35, 3);
				List<Gangplank.Box> boxes = Gangplank.plankBoxes(s, a);
				assertTrue(boxes.size() >= 2);
				double sin = Math.sin(Math.toRadians(a));
				assertTrue(boxes.get(0).maxY() >= s.hy() - EPS && boxes.get(0).maxY() <= s.hy() + Gangplank.STEP_RISE + EPS,
						"first step at the hinge height");
				for (int k = 0; k < boxes.size(); k++) {
					Gangplank.Box b = boxes.get(k);
					assertEquals(s.hz() - 1, b.minZ(), EPS);
					assertEquals(s.hz() + 1, b.maxZ(), EPS);
					assertTrue(b.maxY() - b.minY() <= Gangplank.BOX_THICKNESS + EPS, "thin");
					if (k > 0) {
						Gangplank.Box p = boxes.get(k - 1);
						assertTrue(Math.abs(b.maxY() - p.maxY()) <= Gangplank.STEP_RISE + 1e-9, "rise " + (b.maxY() - p.maxY()));
						// contiguous along the plank (no gap to fall through)
						double gap = s.o() > 0 ? b.minX() - p.maxX() : p.minX() - b.maxX();
						assertTrue(Math.abs(gap) < 1e-9, "gap " + gap);
					}
					// every step's top lies on the slope or one step above it, never below the walking surface
					double uMid = Math.abs((b.minX() + b.maxX()) / 2 - s.hx()) / Math.cos(Math.toRadians(a));
					double surf = s.hy() - uMid * sin;
					assertTrue(b.maxY() >= surf - 1e-9 && b.maxY() <= surf + Gangplank.STEP_RISE + 1e-9, "on the slope");
				}
				// from the quay: the landing surface is TIP_LIFT under the tip; stepping onto the last box is a small step
				double tipTop = s.hy() - 4 * sin;
				double last = boxes.get(boxes.size() - 1).maxY();
				assertTrue(last - (tipTop - Gangplank.TIP_LIFT) <= 0.5 + 1e-9, "step from the quay " + (last - tipTop));
				// the first box reaches over the bulwark, inboard of the hinge
				Gangplank.Box first = boxes.get(0);
				assertTrue(s.o() > 0 ? first.minX() <= s.hx() - Gangplank.INBOARD + EPS : first.maxX() >= s.hx() + Gangplank.INBOARD - EPS);
			}
		}
	}

	@Test
	void stairsClimbFromTheDeckToTheHinge() {
		for (String side : new String[] {"port", "starboard"}) {
			Gangplank.Spec s = spec(side, 2, 4, -15, 35, 3);
			List<Gangplank.Box> stairs = Gangplank.stairBoxes(s);
			assertTrue(stairs.size() >= 3, "1.4 of rise: at least 3 stairs");
			double prev = s.step().minY();
			for (Gangplank.Box b : stairs) {
				assertTrue(b.maxY() - prev <= Gangplank.STAIR_RISE + EPS && b.maxY() > prev);
				assertEquals(s.step().minY(), b.minY(), EPS);
				// each stair reaches the hull side
				assertEquals(s.o() > 0 ? s.step().maxX() : s.step().minX(), s.o() > 0 ? b.maxX() : b.minX(), EPS);
				prev = b.maxY();
			}
			assertEquals(s.step().maxY(), prev, EPS);
			assertEquals(s.hy(), prev, EPS, "the top stair is level with the plank");
			// the stairs rise towards the hull side: the lowest is the widest
			Gangplank.Box low = stairs.get(0), high = stairs.get(stairs.size() - 1);
			assertTrue(high.maxX() - high.minX() < low.maxX() - low.minX());
		}
		assertTrue(Gangplank.stairBoxes(Gangplank.parse("x", JsonParser.parseString(
				"{\"side\":\"port\",\"hinge\":[2,1,0],\"width\":2,\"length\":3,\"lever\":[0,0,0]}").getAsJsonObject())).isEmpty());
	}

	// ------------------------------------------------------------------ landing and clearance

	/** A fake world: ground (a quay) of height {@code quay} for x beyond {@code edge} (outboard), solid cells listed. */
	private static final class FakeWorld implements Gangplank.Terrain {
		final double quay;
		final double edge;
		final int o;
		final List<double[]> cells = new ArrayList<>();

		FakeWorld(double quay, double edge, int o) {
			this.quay = quay;
			this.edge = edge;
			this.o = o;
		}

		boolean onQuay(double lx) {
			return o > 0 ? lx >= edge : lx <= edge;
		}

		@Override
		public double surface(double lx, double lz, double yMin, double yMax) {
			double best = Double.NaN;
			if (onQuay(lx) && quay >= yMin && quay <= yMax) {
				best = quay;
			}
			for (double[] c : cells) {
				if (lx >= c[0] && lx < c[0] + 1 && lz >= c[2] && lz < c[2] + 1 && c[1] + 1 >= yMin && c[1] + 1 <= yMax && !(c[1] + 1 <= best)) {
					best = c[1] + 1;
				}
			}
			return best;
		}

		@Override
		public boolean solid(double lx, double ly, double lz) {
			if (onQuay(lx) && ly < quay) {
				return true;
			}
			for (double[] c : cells) {
				if (lx >= c[0] && lx < c[0] + 1 && ly >= c[1] && ly < c[1] + 1 && lz >= c[2] && lz < c[2] + 1) {
					return true;
				}
			}
			return false;
		}
	}

	@Test
	void landingFindsTheQuayAndRestsTheTipOnIt() {
		for (String side : new String[] {"port", "starboard"}) {
			Gangplank.Spec s = spec(side, 2, 4, -15, 35, 3);
			int o = s.o();
			for (double quay : new double[] {0.0, 0.6, 1.2, 1.9, 2.6}) {
				// a quay higher than the hinge must have its edge near the tip (else the rising plank would hit its edge)
				FakeWorld w = new FakeWorld(quay, s.hx() + o * (quay > s.hy() ? 3.6 : 2.0), o);
				Gangplank.Landing l = Gangplank.findLanding(s, w);
				assertTrue(l.ok(), side + " quay " + quay + ": " + l.refusal());
				assertEquals(quay, l.surfaceY(), 1e-9);
				double[] tip = s.point(l.angle(), 4, 0, 0);
				assertEquals(quay + Gangplank.TIP_LIFT, tip[1], 1e-6, "the tip rests on the quay");
				assertTrue(l.angle() >= -15 && l.angle() <= 35);
				assertNull(Gangplank.clearance(s, l.angle(), w), "clear swing");
			}
		}
	}

	@Test
	void neverIntoTheVoidNorOutOfRange() {
		Gangplank.Spec s = spec("starboard", 2, 4, -15, 35, 3);
		int o = s.o();
		// nothing under the tip: open sea or the void under an airship
		Gangplank.Landing none = Gangplank.findLanding(s, new FakeWorld(-100, s.hx() + o * 2.0, o));
		assertFalse(none.ok());
		assertEquals(Gangplank.NO_LANDING, none.refusal());
		// a quay just beyond the reach (too low): refused
		// (35 degrees on 4 blocks: 2.29 of drop at most; the quay 2.9 under the hinge)
		Gangplank.Landing low = Gangplank.findLanding(s, new FakeWorld(s.hy() - 2.9, s.hx() + o * 2.0, o));
		assertFalse(low.ok());
		assertEquals(Gangplank.TOO_LOW, low.refusal());
		// a quay higher than the -15 degrees allow
		Gangplank.Landing high = Gangplank.findLanding(s, new FakeWorld(s.hy() + 1.6, s.hx() + o * 3.6, o));
		assertFalse(high.ok());
		assertEquals(Gangplank.TOO_HIGH, high.refusal());
		// the quay too far from the hull: the tip finds nothing
		Gangplank.Landing far = Gangplank.findLanding(s, new FakeWorld(0.5, s.hx() + o * 6.0, o));
		assertFalse(far.ok());
		// max_drop limits an airship's reach below the hinge
		Gangplank.Spec air = spec("port", 3, 4.5, -20, 30, 1.0);
		assertFalse(Gangplank.findLanding(air, new FakeWorld(air.hy() - 1.8, air.hx() + 2.0, 1)).ok());
		assertTrue(Gangplank.findLanding(air, new FakeWorld(air.hy() - 0.8, air.hx() + 2.0, 1)).ok());
	}

	@Test
	void clearanceRefusesABlockInTheSwingOrOnTheWalkway() {
		Gangplank.Spec s = spec("starboard", 2, 4, -15, 35, 3);
		int o = s.o();
		FakeWorld w = new FakeWorld(0.6, s.hx() + o * 2.0, o);
		Gangplank.Landing l = Gangplank.findLanding(s, w);
		assertTrue(l.ok());
		// a block in the arc the plank sweeps (2 blocks out, 2 up)
		double[] mid = s.point(-45, 2.8, 0, 0);
		w.cells.add(new double[] {Math.floor(mid[0]), Math.floor(mid[1]), Math.floor(mid[2])});
		assertEquals(Gangplank.SWING_BLOCKED, Gangplank.clearance(s, l.angle(), w));
		w.cells.clear();
		// a block a player would bump into, a little above the deployed walkway
		double[] walk = s.point(l.angle(), 2.0, 0, 0);
		w.cells.add(new double[] {Math.floor(walk[0]), Math.floor(walk[1] + 1.4), Math.floor(walk[2])});
		String why = Gangplank.clearance(s, l.angle(), w);
		assertNotNull(why);
		w.cells.clear();
		assertNull(Gangplank.clearance(s, l.angle(), w));
	}

	@Test
	void leverPickAndBoxes() {
		Gangplank.Spec s = spec("starboard", 2, 4, -15, 35, 3);
		double[] o = {s.leverX() + 2, s.leverY() + 0.5, s.leverZ()};
		double[] d = {-1, 0, 0};
		double t = Gangplank.pickLever(s, o, d, 5);
		assertEquals(2 - 0.32, t, 1e-9);
		assertEquals(-1, Gangplank.pickLever(s, o, new double[] {1, 0, 0}, 5), EPS);
		List<Gangplank.Box> all = Gangplank.deployedBoxes(s, 20);
		assertEquals(Gangplank.plankBoxes(s, 20).size() + Gangplank.stairBoxes(s).size(), all.size());
		Gangplank.Box b = all.get(1);
		assertTrue(Gangplank.intersects(all, b.minX() + 0.1, b.maxY() - 0.1, b.minZ() + 0.1, b.minX() + 0.2, b.maxY() + 1, b.minZ() + 0.2));
		assertFalse(Gangplank.intersects(all, 50, 50, 50, 51, 51, 51));
	}

	// ------------------------------------------------------------------ the spec files

	@Test
	void everySpecFileLoadsWithItsModels() throws Exception {
		URL dir = Gangplank.class.getResource(Gangplank.DIR);
		assertNotNull(dir, "gangplanks directory on the classpath");
		File[] files = new File(dir.toURI()).listFiles((f, n) -> n.endsWith(".json"));
		assertNotNull(files);
		assertTrue(files.length >= 2, "at least the two reference vessels");
		for (File f : files) {
			String id = f.getName().substring(0, f.getName().length() - 5);
			Gangplank.Spec s;
			try (Reader r = new FileReader(f, StandardCharsets.UTF_8)) {
				s = Gangplank.parse(id, JsonParser.parseReader(r).getAsJsonObject());
			}
			assertEquals(s, Gangplank.of(id), id);
			assertTrue(Gangplank.STYLES.contains(s.style()), id + " style " + s.style());
			assertTrue(s.width() >= 1.5 && s.width() <= 4.0, id + " width");
			assertTrue(s.minAngle() < s.maxAngle(), id + " angles");
			assertTrue(s.maxDrop() > 0.3, id + " max_drop");
			// the plank model and the lever of its style, readable by the mod's loader
			BbModel plank = model("/assets/medievalships/models/entity/gangplank_" + id + ".bbmodel");
			assertTrue(plank.quadCount() > 100, id + " plank model");
			assertTrue(plank.hasBone("seg_0") && plank.hasBone("seg_" + (Gangplank.segments(s) - 1)) && plank.hasBone("rail_0_1"), id + " folding segments and handrails bones");
			BbModel lever = model("/assets/medievalships/models/entity/gangplank_lever_" + s.style() + ".bbmodel");
			assertTrue(lever.hasBone("handle"), id + " lever handle");
			// the stairs (if any) climb at most STAIR_RISE each to the hinge height
			if (s.step() != null) {
				assertEquals(s.hy(), s.step().maxY(), 0.05, id + " stairs reach the hinge");
			}
		}
		// a ship without a file has no gangplank
		assertNull(Gangplank.of("rowboat"));
	}

	private static BbModel model(String path) throws Exception {
		var in = GangplankTest.class.getResourceAsStream(path);
		assertNotNull(in, path);
		try (Reader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	/** The two reference vessels: hinge on the hull side at the rail, stairs from the deck, lever on the deck, clear of the furniture. */
	@Test
	void referenceVesselsFitTheirHull() {
		for (ShipType type : new ShipType[] {Ships.STEAMPUNK_AIRSHIP}) {
			Gangplank.Spec s = Gangplank.of(type.id());
			assertNotNull(s, type.id());
			HullShape h = type.geometry().hull();
			assertEquals(h.halfWidth(s.hz()), Math.abs(s.hx()), 0.12, type.id() + " hinge on the hull side");
			assertEquals(Math.signum(s.hx()), s.o(), type.id() + " side");
			assertTrue(s.hy() >= h.railY(s.hz()) - 0.05 && s.hy() <= h.railY(s.hz()) + 0.2, type.id() + " hinge at the rail top");
			assertEquals(h.deckY(s.hz()), s.step().minY(), 0.02, type.id() + " stairs from the deck");
			assertEquals(h.deckY(s.leverZ()), s.leverY(), 0.02, type.id() + " lever on the deck");
			assertTrue(Math.abs(s.leverX()) < h.innerHalfWidth(s.leverZ()) - 0.3, type.id() + " lever inboard");
			assertTrue(s.hasRailGap() && s.railGapZ0() <= s.hz() - s.width() / 2 + 0.06 && s.railGapZ1() >= s.hz() + s.width() / 2 - 0.06);
			// nothing solid of the ship (cabin, crates, engine) in the stairs or at the lever
			List<Gangplank.Box> mine = new ArrayList<>(Gangplank.stairBoxes(s));
			mine.add(Gangplank.leverBox(s));
			for (ShipGeometry.LocalBox b : type.geometry().solids()) {
				assertFalse(Gangplank.intersects(mine, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ()),
						type.id() + " solid in the way " + b);
			}
			for (ShipGeometry.Mast m : type.geometry().masts()) {
				assertFalse(Gangplank.intersects(mine, m.x() - m.half(), m.bottom(), m.z() - m.half(), m.x() + m.half(), m.top(), m.z() + m.half()),
						type.id() + " mast in the way");
			}
			ShipGeometry.LocalBox helm = type.geometry().helm();
			assertFalse(Gangplank.intersects(mine, helm.minX(), helm.minY(), helm.minZ(), helm.maxX(), helm.maxY(), helm.maxZ()), type.id() + " helm");
			// seats are not covered by the stairs
			for (ShipGeometry.Seat seat : type.geometry().seats()) {
				assertFalse(Gangplank.intersects(Gangplank.stairBoxes(s), seat.x() - 0.3, seat.y() - 0.3, seat.z() - 0.3, seat.x() + 0.3, seat.y(),
						seat.z() + 0.3), type.id() + " seat " + seat.index());
			}
		}
	}
}
