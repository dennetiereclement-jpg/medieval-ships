package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The interactive training targets (1.19.0): the {@code "targets"} field of a training area's JSON
 * ({@link TrainingTarget}, read by {@link TentType}), its rotation with the facing, the hit geometry (ray against a box,
 * strength), and the reaction played on the clients ({@link TargetMotion}): a dummy tilts away from the hit and comes
 * back to rest (then stops computing), a bag swings away from the hit like a pendulum and a new hit adds to its swing, a
 * sword-and-shield dummy's shield arm recoils when the shield is hit and its sword rings when the body is. With the real
 * areas: every target's bone is a top-level bone of the area's model (with the child bones the contract names when the
 * model has them), and its pivot and hitbox lie in the area's extent.
 */
public class TrainingTargetTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	private static JsonObject json(String s) {
		return JsonParser.parseString(s).getAsJsonObject();
	}

	private static final String AREA = """
			{"extent": [-3.5, 0, -3.5, 3.5, 3, 3.5],
			 "targets": [
			   {"kind": "dummy", "bone": "target_0", "pivot": [-1.0, 0.1, -1.5], "hitbox": [-0.7, 0.8, -1.3, -1.3, 1.9, -1.7]},
			   {"kind": "shield_dummy", "bone": "target_1", "pivot": [1.0, 0.1, -1.5], "hitbox": [0.75, 0.8, -1.7, 1.25, 1.9, -1.3],
			    "shield_box": [0.6, 0.9, -1.25, 1.1, 1.6, -1.15]},
			   {"kind": "bag", "pivot": [0.0, 2.6, 1.0], "hitbox": [-0.25, 0.9, 0.75, 0.25, 1.9, 1.25], "shield_box": [0, 0, 0, 1, 1, 1]},
			   {"kind": "dummy", "pivot": [0, 0, 0]},
			   {"kind": "Punching-Bag", "bone": "target_9", "pivot": [2, 2.5, 2], "hitbox": [1.8, 1, 1.8, 2.2, 2, 2.2]}
			 ]}""";

	private static TentType area() {
		return TentType.parse(TentType.TRAINING, "test_area", "aire de test", "Test Area", json(AREA));
	}

	@Test
	void targetsAreParsed() {
		TentType t = area();
		assertTrue(t.hasTargets());
		List<TrainingTarget> list = t.targets();
		assertEquals(4, list.size(), "the entry without a hitbox is skipped");
		TrainingTarget d = list.get(0);
		assertEquals(TrainingTarget.Kind.DUMMY, d.kind());
		assertEquals("target_0", d.bone());
		assertEquals(-1.0, d.px());
		assertEquals(0.1, d.py());
		assertEquals(-1.5, d.pz());
		// corners in any order are sorted
		assertEquals(new TentType.Box(-1.3, 0.8, -1.7, -0.7, 1.9, -1.3), d.hitbox());
		assertNull(d.shieldBox());
		assertFalse(d.hasShield());
		assertEquals(d.hitbox(), d.reach());
		assertEquals("target_0_head", d.head());
		assertEquals("target_0_arm_l", d.armLeft());
		assertEquals("target_0_arm_r", d.armRight());
		assertEquals("target_0_shield", d.shield());
		assertEquals("target_0_sword", d.sword());

		TrainingTarget s = list.get(1);
		assertEquals(TrainingTarget.Kind.SHIELD_DUMMY, s.kind());
		assertTrue(s.hasShield());
		assertEquals(new TentType.Box(0.6, 0.8, -1.7, 1.25, 1.9, -1.15), s.reach(), "the shield is part of the box that can be hit");

		TrainingTarget b = list.get(2);
		assertEquals(TrainingTarget.Kind.BAG, b.kind());
		assertEquals("target_2", b.bone(), "a missing bone is target_<i>");
		assertNull(b.shieldBox(), "only a shield dummy has a shield");
		assertEquals(TrainingTarget.Kind.BAG, list.get(3).kind(), "lenient kind names");
		assertEquals("target_9", list.get(3).bone());

		// props without the field: no targets
		assertFalse(TentTypes.ADVENTURER.hasTargets());
		assertTrue(TentTypes.CART_OPEN.targets().isEmpty());
		assertTrue(TentType.parse("x", "x", "x", json("{\"extent\": [0,0,0,1,1,1], \"targets\": 3}")).targets().isEmpty());
	}

	@Test
	void targetsTurnWithTheFacing() {
		TentType t = area();
		for (int q = 0; q < 4; q++) {
			for (int i = 0; i < t.targets().size(); i++) {
				TrainingTarget a = t.targets().get(i), r = t.targets(q).get(i);
				double[] p = TentType.rotate(a.px(), a.pz(), q);
				assertEquals(p[0], r.px(), 1e-12);
				assertEquals(a.py(), r.py(), 1e-12);
				assertEquals(p[1], r.pz(), 1e-12);
				assertEquals(TentType.rotate(a.hitbox(), q), r.hitbox(), "the hitbox turns like a collider");
				assertEquals(a.kind(), r.kind());
				assertEquals(a.bone(), r.bone());
				double[] back = TrainingTarget.unrotate(r.px(), r.pz(), q);
				assertEquals(a.px(), back[0], 1e-12);
				assertEquals(a.pz(), back[1], 1e-12);
			}
		}
		// a quarter turn (west): local +z goes to -x, the shield box with it
		TrainingTarget s = t.targets(TentType.WEST).get(1);
		assertEquals(TentType.rotate(new TentType.Box(0.6, 0.9, -1.25, 1.1, 1.6, -1.15), TentType.WEST), s.shieldBox());
		assertEquals(90f, TrainingTarget.rotateYaw(0f, 1));
		assertEquals(0f, TrainingTarget.rotateYaw(270f, 1));
		assertEquals(180f, TrainingTarget.rotateYaw(0f, 2));
	}

	@Test
	void rayAgainstBox() {
		TentType.Box b = new TentType.Box(0, 0, 0, 1, 1, 1);
		assertEquals(2.0, TrainingTarget.rayBox(b, -2, 0.5, 0.5, 1, 0, 0), 1e-12);
		assertEquals(1.0, TrainingTarget.rayBox(b, -2, 0.5, 0.5, 2, 0, 0), 1e-12, "t in units of the direction");
		assertEquals(0.0, TrainingTarget.rayBox(b, 0.5, 0.5, 0.5, 1, 0, 0), 1e-12, "from inside");
		assertTrue(Double.isInfinite(TrainingTarget.rayBox(b, -2, 2, 0.5, 1, 0, 0)), "passes above");
		assertTrue(Double.isInfinite(TrainingTarget.rayBox(b, 3, 0.5, 0.5, 1, 0, 0)), "behind");
		assertTrue(Double.isInfinite(TrainingTarget.rayBox(b, -2, 0.5, 2, 1, 0, 0)), "parallel, outside");
		// a shield in front of the body is met first from the front, the body first from behind
		TentType.Box body = new TentType.Box(-0.3, 0.8, -0.3, 0.3, 1.9, 0.3), shield = new TentType.Box(-0.25, 0.9, 0.3, 0.25, 1.6, 0.4);
		assertTrue(TrainingTarget.rayBox(shield, 0, 1.3, 3, 0, 0, -1) < TrainingTarget.rayBox(body, 0, 1.3, 3, 0, 0, -1));
		assertTrue(TrainingTarget.rayBox(body, 0, 1.3, -3, 0, 0, 1) < TrainingTarget.rayBox(shield, 0, 1.3, -3, 0, 0, 1));
	}

	@Test
	void strengthGrowsWithTheDamage() {
		assertEquals(0.25f, TrainingTarget.strength(0f));
		assertEquals(0.35f, TrainingTarget.strength(1f), 1e-6, "a fist");
		assertEquals(0.95f, TrainingTarget.strength(7f), 1e-6, "an iron sword");
		assertEquals(1f, TrainingTarget.strength(40f));
		assertEquals(0.25f, TrainingTarget.strength(Float.NaN));
		assertTrue(TrainingTarget.strength(3f) < TrainingTarget.strength(6f));
	}

	private static TrainingTarget dummy() {
		return area().targets().get(0);
	}

	private static double peak(TargetMotion m, int bone, int axis, int ticks) {
		double best = 0;
		for (int i = 0; i < ticks; i++) {
			m.tick();
			double a = m.angle(bone, axis);
			if (Math.abs(a) > Math.abs(best)) {
				best = a;
			}
		}
		return best;
	}

	@Test
	void restingTargetComputesNothing() {
		TargetMotion m = new TargetMotion(dummy(), null);
		assertFalse(m.moving());
		m.tick();
		assertFalse(m.moving());
		float[] r = new float[3];
		m.rotation(TargetMotion.ROOT, 0.5f, r);
		assertEquals(0f, r[0]);
		// a zero-strength or directionless hit does not start it
		m.hit(0, 0, 1, TrainingTarget.PART_BODY, Double.NaN, Double.NaN, Double.NaN, 1);
		m.hit(0, 1, 0, TrainingTarget.PART_BODY, Double.NaN, Double.NaN, Double.NaN, 1);
		assertFalse(m.moving());
	}

	@Test
	void dummyTiltsAwayAndSettles() {
		TrainingTarget d = dummy();
		TargetMotion m = new TargetMotion(d, null);
		TentType.Box h = d.hitbox();
		// hit from the front (the attacker at +z, pushing towards -z) on the middle of the body
		m.hit(0, -1, 1.0, TrainingTarget.PART_BODY, (h.x0() + h.x1()) / 2, (h.y0() + h.y1()) / 2, h.z1(), 7);
		assertTrue(m.moving());
		m.tick();
		// the top moves towards -z: a rotation about -x
		assertTrue(m.angle(TargetMotion.ROOT, 0) < 0, "tilts back, away from the hit: " + m.angle(TargetMotion.ROOT, 0));
		double peak = peak(m, TargetMotion.ROOT, 0, 20);
		assertTrue(Math.abs(peak) > Math.toRadians(4) && Math.abs(peak) <= 0.35 + 1e-9, "a visible tilt, within its limit: " + Math.toDegrees(peak));
		// the head nods, the arms swing (driven by the body)
		assertTrue(Math.abs(m.angle(TargetMotion.HEAD, 0)) > 1e-4 || peak(m, TargetMotion.HEAD, 0, 5) != 0, "the head follows");
		assertNotNull(m.target());
		int ticks = 25;
		while (m.moving() && ticks < 400) {
			m.tick();
			ticks++;
		}
		assertFalse(m.moving(), "it comes back to rest");
		assertTrue(ticks < 200, "within 10 s (" + ticks + " ticks)");
		for (int b = 0; b < TargetMotion.BONES; b++) {
			for (int a = 0; a < 3; a++) {
				assertEquals(0.0, m.angle(b, a), "exactly at rest, bone " + b);
			}
		}
		// a weak hit (a fist) tilts it less than a strong one (a sword)
		TargetMotion weak = new TargetMotion(d, null), strong = new TargetMotion(d, null);
		weak.hit(1, 0, TrainingTarget.strength(1), TrainingTarget.PART_BODY, -1, 1.3, -1.5, 3);
		strong.hit(1, 0, TrainingTarget.strength(7), TrainingTarget.PART_BODY, -1, 1.3, -1.5, 3);
		// pushed towards +x: the top goes to +x, a rotation about -z
		double pw = peak(weak, TargetMotion.ROOT, 2, 20), ps = peak(strong, TargetMotion.ROOT, 2, 20);
		assertTrue(pw < 0 && ps < 0, pw + " " + ps);
		assertTrue(Math.abs(ps) > 1.8 * Math.abs(pw), Math.toDegrees(pw) + " vs " + Math.toDegrees(ps));
	}

	@Test
	void bagSwingsLikeAPendulum() {
		TrainingTarget bag = area().targets().get(2);
		TargetMotion m = new TargetMotion(bag, null);
		// pushed towards +x at the bag's middle: it swings to +x (a rotation about +z for a point below the pivot)
		m.hit(1, 0, 0.6, TrainingTarget.PART_BODY, 0, 1.4, 1.0, 11);
		m.tick();
		assertTrue(m.angle(TargetMotion.ROOT, 2) > 0, "swings away from the hit: " + m.angle(TargetMotion.ROOT, 2));
		// half a period later it is on the other side; the period is about 2 pi sqrt(L / g)
		double length = 2.6 - 1.4;
		double period = 2 * Math.PI * Math.sqrt(length / 9.81);
		int crossing = -1;
		for (int i = 1; i < 80 && crossing < 0; i++) {
			m.tick();
			if (m.angle(TargetMotion.ROOT, 2) < 0) {
				crossing = i;
			}
		}
		assertTrue(crossing > 0, "it swings back");
		double half = (crossing + 1) * TargetMotion.TICK;
		assertTrue(Math.abs(half - period / 2) < 0.2, "half a swing " + half + " s, expected about " + period / 2);
		// a new hit in the swing's direction adds to it
		TargetMotion one = new TargetMotion(bag, null), two = new TargetMotion(bag, null);
		one.hit(1, 0, 0.5, TrainingTarget.PART_BODY, 0, 1.4, 1.0, 1);
		two.hit(1, 0, 0.5, TrainingTarget.PART_BODY, 0, 1.4, 1.0, 1);
		two.hit(1, 0, 0.5, TrainingTarget.PART_BODY, 0, 1.4, 1.0, 2);
		assertTrue(peak(two, TargetMotion.ROOT, 2, 15) > peak(one, TargetMotion.ROOT, 2, 15) * 1.5);
		// a bag has no child bones moving
		assertEquals(0.0, two.angle(TargetMotion.HEAD, 0));
		assertEquals(0.0, two.angle(TargetMotion.SWORD, 0));
		// it settles too (slowly)
		int ticks = 0;
		while (one.moving() && ticks < TargetMotion.MAX_TICKS + 10) {
			one.tick();
			ticks++;
		}
		assertFalse(one.moving());
		assertTrue(ticks < 600, "settled after " + ticks + " ticks");
	}

	@Test
	void shieldAndSwordReact() {
		TrainingTarget s = area().targets().get(1);
		double[][] joints = new double[TargetMotion.BONES][];
		joints[TargetMotion.ARM_L] = new double[] {0.75, 1.65, -1.5};
		// the shield is hit (at +z, pushed to -z): the shield arm recoils, the body barely moves, the shield wobbles
		TargetMotion shield = new TargetMotion(s, joints);
		shield.hit(0, -1, 1.0, TrainingTarget.PART_SHIELD, 0.85, 1.25, -1.15, 5);
		double arm = peak(shield, TargetMotion.ARM_L, 0, 6);
		TargetMotion body = new TargetMotion(s, joints);
		body.hit(0, -1, 1.0, TrainingTarget.PART_BODY, 1.0, 1.35, -1.3, 5);
		assertTrue(Math.abs(arm) > Math.toRadians(5), "the shield arm recoils: " + Math.toDegrees(arm));
		TargetMotion shield2 = new TargetMotion(s, joints);
		shield2.hit(0, -1, 1.0, TrainingTarget.PART_SHIELD, 0.85, 1.25, -1.15, 5);
		double rootShield = peak(shield2, TargetMotion.ROOT, 0, 20);
		double rootBody = peak(body, TargetMotion.ROOT, 0, 20);
		assertTrue(Math.abs(rootShield) < 0.6 * Math.abs(rootBody), "the shield takes the hit: " + rootShield + " vs " + rootBody);
		TargetMotion wobble = new TargetMotion(s, joints);
		wobble.hit(0, -1, 1.0, TrainingTarget.PART_SHIELD, 0.85, 1.25, -1.15, 5);
		assertTrue(Math.abs(peak(wobble, TargetMotion.SHIELD, 0, 6)) > Math.toRadians(1), "the shield wobbles");
		// the body is hit: the sword rings (fast: it changes sign within a few ticks), the shield arm only follows
		TargetMotion ring = new TargetMotion(s, joints);
		ring.hit(0, -1, 1.0, TrainingTarget.PART_BODY, 1.0, 1.35, -1.3, 5);
		List<Double> sword = new ArrayList<>();
		for (int i = 0; i < 10; i++) {
			ring.tick();
			sword.add(ring.angle(TargetMotion.SWORD, 0));
		}
		boolean crosses = false;
		for (int i = 1; i < sword.size(); i++) {
			crosses |= Math.signum(sword.get(i)) != Math.signum(sword.get(i - 1));
		}
		assertTrue(crosses, "the sword vibrates: " + sword);
		// a plain dummy has no sword nor shield moving
		TargetMotion d = new TargetMotion(dummy(), joints);
		d.hit(0, -1, 1.0, TrainingTarget.PART_SHIELD, -1, 1.3, -1.3, 5);
		peak(d, TargetMotion.ROOT, 0, 5);
		assertEquals(0.0, d.angle(TargetMotion.SWORD, 0));
		assertEquals(0.0, d.angle(TargetMotion.SHIELD, 0));
	}

	@Test
	void realAreasTargetsMatchTheirModels() throws Exception {
		for (TentType t : TentTypes.TRAINING) {
			if (!t.hasTargets()) {
				continue; // the models of 1.18.0 (before the target bones)
			}
			BbModel model;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve(t.model()), StandardCharsets.UTF_8)) {
				model = new BbModel(r);
			}
			TentType.Box e = t.extent();
			for (TrainingTarget g : t.targets()) {
				assertTrue(model.hasBone(g.bone()), t.id() + ": bone " + g.bone());
				double[] o = model.origin(g.bone());
				assertEquals(g.px(), o[0], 0.02, t.id() + " " + g.bone() + ": the bone's origin is the pivot (x)");
				assertEquals(g.py(), o[1], 0.02, t.id() + " " + g.bone() + ": the bone's origin is the pivot (y)");
				assertEquals(g.pz(), o[2], 0.02, t.id() + " " + g.bone() + ": the bone's origin is the pivot (z)");
				TentType.Box h = g.reach();
				assertTrue(h.x0() >= e.x0() && h.x1() <= e.x1() && h.z0() >= e.z0() && h.z1() <= e.z1() && h.y0() >= 0 && h.y1() <= e.y1(),
						t.id() + " " + g.bone() + ": the hitbox lies in the extent");
				// the reaction finds its joints (when the model has the bones) and plays
				double[][] joints = new double[TargetMotion.BONES][];
				String[] names = {g.bone(), g.head(), g.armLeft(), g.armRight(), g.shield(), g.sword()};
				for (int b = 0; b < names.length; b++) {
					joints[b] = model.origin(names[b]);
				}
				if (g.kind() == TrainingTarget.Kind.SHIELD_DUMMY) {
					assertTrue(model.hasBone(g.shield()) && model.hasBone(g.sword()), t.id() + ": the shield dummy's shield and sword bones");
				}
				TargetMotion m = new TargetMotion(g, joints);
				m.hit(0, -1, 1, TrainingTarget.PART_BODY, Double.NaN, Double.NaN, Double.NaN, 1);
				m.tick();
				assertTrue(m.moving(), t.id() + " " + g.bone());
				// at rest, the target's subtree drawn alone is exactly what the whole model draws for it
				List<float[]> alone = new ArrayList<>(), whole = new ArrayList<>(), rest = new ArrayList<>();
				model.renderSubtree(model.newPose(), g.bone(), (p, uv, n, glow) -> alone.add(p.clone()));
				model.render(model.newPose(), (p, uv, n, glow) -> whole.add(p.clone()));
				BbModel.Pose without = model.newPose();
				model.hide(without, g.bone());
				model.render(without, (p, uv, n, glow) -> rest.add(p.clone()));
				assertFalse(alone.isEmpty(), t.id() + " " + g.bone() + " draws something");
				assertEquals(whole.size(), alone.size() + rest.size(), t.id() + " " + g.bone() + ": the static renderer leaves exactly the target out");
			}
		}
	}
}
