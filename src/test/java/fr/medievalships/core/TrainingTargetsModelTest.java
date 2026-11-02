package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The interactive training targets of the training areas as the models give them (1.19.0, tools/training/traininglib.py
 * Target): in training/&lt;id&gt;.json the field "targets" lists every dummy and punching bag ({kind, bone, pivot, hitbox,
 * shield_box for a shield dummy}); in the .bbmodel each one is a TOP-LEVEL bone "target_&lt;i&gt;" (origin = the pivot)
 * holding only the moving parts, with its child bones (head at the neck, arms at the shoulders, the shield under the
 * left arm, the sword under the right arm), while the fixed parts (foot, plinth, gallows, beam, hook) stay in the
 * static bones; pivots and hitboxes lie inside the extent, the moving cubes inside their hitbox. The tatami area's
 * bench has its two seats ("seats", on top of the bench).
 */
public class TrainingTargetsModelTest {
	private static final double EPS = 1e-6;

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = TrainingTargetsModelTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}

	private static double[] vec(JsonElement e, int n) {
		JsonArray a = e.getAsJsonArray();
		assertEquals(n, a.size());
		double[] v = new double[n];
		for (int i = 0; i < n; i++) {
			v[i] = a.get(i).getAsDouble();
		}
		return v;
	}

	private static boolean inside(double[] box, double x, double y, double z, double tol) {
		return x >= box[0] - tol && x <= box[3] + tol && y >= box[1] - tol && y <= box[4] + tol && z >= box[2] - tol && z <= box[5] + tol;
	}

	private static boolean inside(double[] outer, double[] in, double tol) {
		return inside(outer, in[0], in[1], in[2], tol) && inside(outer, in[3], in[4], in[5], tol);
	}

	/** Blockbench pixels -> prop-local blocks (x and z mirrored). */
	private static double[] blocks(double[] bb) {
		return new double[] {-bb[0] / 16.0, bb[1] / 16.0, -bb[2] / 16.0};
	}

	/** A group of the outliner and what it holds. */
	private record Group(JsonObject json, Group parent, List<Group> children, List<String> cubes) {
		String name() {
			return json.get("name").getAsString();
		}

		double[] origin() {
			return blocks(vec(json.get("origin"), 3));
		}

		void allCubes(List<String> out) {
			out.addAll(cubes);
			for (Group c : children) {
				c.allCubes(out);
			}
		}
	}

	private static Group read(JsonObject g, Group parent, Map<String, Group> byName) {
		Group out = new Group(g, parent, new ArrayList<>(), new ArrayList<>());
		byName.put(out.name(), out);
		for (JsonElement c : g.getAsJsonArray("children")) {
			if (c.isJsonObject()) {
				out.children.add(read(c.getAsJsonObject(), out, byName));
			} else {
				out.cubes.add(c.getAsString());
			}
		}
		return out;
	}

	/** One area: its JSON, its model (outliner groups by name, top-level groups, elements by uuid). */
	private static final class Area {
		final String id;
		final JsonObject data;
		final double[] extent;
		final Map<String, Group> groups = new HashMap<>();
		final List<Group> top = new ArrayList<>();
		final Map<String, JsonObject> elements = new HashMap<>();
		final BbModel model;

		Area(String id) throws Exception {
			this.id = id;
			data = json("/assets/medievalships/training/" + id + ".json");
			extent = vec(data.get("extent"), 6);
			String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
			JsonObject m = json(path);
			for (JsonElement e : m.getAsJsonArray("elements")) {
				elements.put(e.getAsJsonObject().get("uuid").getAsString(), e.getAsJsonObject());
			}
			for (JsonElement g : m.getAsJsonArray("outliner")) {
				top.add(read(g.getAsJsonObject(), null, groups));
			}
			try (InputStream in = TrainingTargetsModelTest.class.getResourceAsStream(path)) {
				model = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			}
		}

		JsonArray targets() {
			return data.has("targets") ? data.getAsJsonArray("targets") : new JsonArray();
		}

		/** Names and centres (prop-local blocks) of the cubes under a group (with its children). */
		Map<String, double[]> cubes(Group g) {
			List<String> uuids = new ArrayList<>();
			g.allCubes(uuids);
			Map<String, double[]> out = new HashMap<>();
			for (String u : uuids) {
				JsonObject e = elements.get(u);
				double[] f = vec(e.get("from"), 3), t = vec(e.get("to"), 3);
				out.put(e.get("name").getAsString(), blocks(new double[] {(f[0] + t[0]) / 2, (f[1] + t[1]) / 2, (f[2] + t[2]) / 2}));
			}
			return out;
		}

		/** The static part: everything but the target bones. */
		Map<String, double[]> staticCubes() {
			Map<String, double[]> out = new HashMap<>();
			for (Group g : top) {
				if (!g.name().startsWith("target_")) {
					out.putAll(cubes(g));
				}
			}
			return out;
		}
	}

	/** Checks every target of an area against the contract; returns the kinds in order. */
	private static List<String> checkTargets(Area a) {
		List<String> kinds = new ArrayList<>();
		JsonArray ts = a.targets();
		for (int i = 0; i < ts.size(); i++) {
			JsonObject t = ts.get(i).getAsJsonObject();
			String kind = t.get("kind").getAsString(), bone = t.get("bone").getAsString(), at = a.id + " " + bone;
			kinds.add(kind);
			assertTrue(kind.equals("dummy") || kind.equals("shield_dummy") || kind.equals("bag"), at + " kind " + kind);
			assertEquals("target_" + i, bone, a.id + " target " + i);
			double[] pivot = vec(t.get("pivot"), 3), hit = vec(t.get("hitbox"), 6);
			assertTrue(inside(a.extent, pivot[0], pivot[1], pivot[2], EPS), at + " pivot inside the extent");
			assertTrue(hit[0] < hit[3] && hit[1] < hit[4] && hit[2] < hit[5], at + " hitbox " + t.get("hitbox"));
			assertTrue(inside(a.extent, hit, EPS), at + " hitbox inside the extent");
			assertTrue(hit[3] - hit[0] < 1.6 && hit[5] - hit[2] < 1.6 && hit[4] - hit[1] < 2.2, at + " hitbox size");
			// the bone: top level, origin = the pivot, drawn by the model
			Group g = a.groups.get(bone);
			assertNotNull(g, at + " bone");
			assertNull(g.parent(), at + " is a top-level bone");
			assertTrue(a.top.contains(g), at + " in the outliner's top level");
			assertTrue(a.model.bonesByName.containsKey(bone), at + " loaded by BbModel");
			double[] o = g.origin();
			assertTrue(Math.abs(o[0] - pivot[0]) < 1e-3 && Math.abs(o[1] - pivot[1]) < 1e-3 && Math.abs(o[2] - pivot[2]) < 1e-3,
					at + " bone origin = pivot");
			assertFalse(g.cubes().isEmpty(), at + " has its own cubes");
			// the pivot is at the bottom of a dummy (the hitbox above it) and at the top of a bag (the bag under it)
			double cx = (hit[0] + hit[3]) / 2, cz = (hit[2] + hit[5]) / 2;
			assertTrue(Math.abs(pivot[0] - cx) < 0.35 && Math.abs(pivot[2] - cz) < 0.35, at + " pivot above / under the hitbox");
			if (kind.equals("bag")) {
				assertTrue(pivot[1] > hit[4] && pivot[1] - hit[4] < 0.8, at + " the chain's top above the bag");
				assertTrue(g.children().isEmpty(), at + " a bag has no child bones");
			} else {
				assertTrue(pivot[1] <= hit[1] + 0.15 && pivot[1] < 0.5, at + " the pivot at the base of the dummy");
				Group head = a.groups.get(bone + "_head"), armL = a.groups.get(bone + "_arm_l"), armR = a.groups.get(bone + "_arm_r");
				assertNotNull(head, at + " head bone");
				assertNotNull(armL, at + " left arm bone");
				assertNotNull(armR, at + " right arm bone");
				for (Group c : List.of(head, armL, armR)) {
					assertTrue(c.parent() == g, c.name() + " child of " + bone);
					assertFalse(c.cubes().isEmpty(), c.name() + " has cubes");
					assertTrue(a.model.bonesByName.containsKey(c.name()), c.name() + " loaded");
				}
				double[] neck = head.origin(), sl = armL.origin(), sr = armR.origin();
				assertTrue(neck[1] > sl[1] && neck[1] > sr[1] && neck[1] < hit[4], at + " the neck above the shoulders");
				assertTrue(Math.abs(sl[1] - sr[1]) < 0.05, at + " shoulders level");
				double span = Math.hypot(sl[0] - sr[0], sl[2] - sr[2]);
				assertTrue(span > 0.3 && span < 0.9, at + " shoulders apart " + span);
				assertTrue(Math.hypot(neck[0] - pivot[0], neck[2] - pivot[2]) < 0.05, at + " the head above the pivot");
				// the arms are on their own side: left = the dummy's +x (its yaw: Minecraft convention, 0 = +z)
				double yaw = Math.toRadians(t.get("yaw").getAsDouble());
				double lx = Math.cos(yaw), lz = Math.sin(yaw);     // the dummy's local +x in prop space
				assertTrue((sl[0] - sr[0]) * lx + (sl[2] - sr[2]) * lz > 0.3, at + " arm_l on the dummy's +x side");
				// the moving cubes lie inside the hitbox (but the sword)
				Map<String, double[]> moving = a.cubes(g);
				Group sword = a.groups.get(bone + "_sword");
				if (sword != null) {
					moving.keySet().removeAll(a.cubes(sword).keySet());
				}
				for (Map.Entry<String, double[]> e : moving.entrySet()) {
					double[] p = e.getValue();
					assertTrue(inside(hit, p[0], p[1], p[2], 0.02), at + " cube " + e.getKey() + " inside the hitbox");
				}
				if (kind.equals("shield_dummy")) {
					Group shield = a.groups.get(bone + "_shield");
					assertNotNull(shield, at + " shield bone");
					assertNotNull(sword, at + " sword bone");
					assertTrue(shield.parent() == armL, at + " the shield under the left arm");
					assertTrue(sword.parent() == armR, at + " the sword under the right arm");
					assertTrue(a.cubes(shield).keySet().stream().anyMatch(n -> n.endsWith("_shield")), at + " the shield's disc");
					assertTrue(a.cubes(sword).keySet().stream().anyMatch(n -> n.endsWith("_sword_blade")), at + " the sword's blade");
					assertTrue(t.has("shield_box"), at + " shield_box");
					double[] sb = vec(t.get("shield_box"), 6);
					assertTrue(sb[0] < sb[3] && sb[1] < sb[4] && sb[2] < sb[5], at + " shield_box " + t.get("shield_box"));
					assertTrue(inside(hit, sb, 1e-3), at + " the shield inside the hitbox");
					assertTrue(sb[1] > 0.5 && sb[4] < 1.7, at + " the shield at arm height");
					// grips: the shield's origin on its back near the left fist, the sword's in the right fist
					Map<String, double[]> armLc = a.cubes(armL), armRc = a.cubes(armR);
					double[] fistL = armLc.entrySet().stream().filter(e -> e.getKey().endsWith("_fist_l")).findFirst().orElseThrow().getValue();
					double[] fistR = armRc.entrySet().stream().filter(e -> e.getKey().endsWith("_fist_r")).findFirst().orElseThrow().getValue();
					assertTrue(dist(shield.origin(), fistL) < 0.15, at + " shield grip at the left fist");
					assertTrue(dist(sword.origin(), fistR) < 0.02, at + " sword grip in the right fist");
				} else {
					assertFalse(t.has("shield_box"), at + " no shield_box");
				}
			}
		}
		return kinds;
	}

	private static double dist(double[] a, double[] b) {
		return Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
	}

	@Test
	void strikeAreaHasThreeStrawDummiesAndThePunchingBag() throws Exception {
		Area a = new Area("training_area_dummy");
		List<String> kinds = checkTargets(a);
		assertEquals(3, kinds.stream().filter("dummy"::equals).count(), "three straw dummies " + kinds);
		assertEquals(1, kinds.stream().filter("bag"::equals).count(), "one punching bag " + kinds);
		assertEquals(4, kinds.size());
		// the fixed parts stay static: the dummies' feet, the gallows, its beam and hook; nothing that moves is left there
		Map<String, double[]> st = a.staticCubes();
		for (String d : List.of("dummy_l", "dummy_r", "dummy_f")) {
			assertTrue(st.containsKey(d + "_foot_a") && st.containsKey(d + "_foot_c"), d + " foot static");
			for (String part : List.of("_post", "_body", "_head", "_arms_l", "_arms_r", "_neck", "_skirt")) {
				assertFalse(st.containsKey(d + part), d + part + " not static");
			}
		}
		assertTrue(st.containsKey("bag_beam") && st.containsKey("bag_hook") && st.containsKey("bag_post_0"), "gallows static");
		assertFalse(st.keySet().stream().anyMatch(n -> n.startsWith("bag_bag") || n.startsWith("bag_chain") || n.startsWith("bag_sling")),
				"the bag and its chain move");
		// the straw arm bar is cut in two arms (one per arm bone), the bag hangs in its bone
		for (int i = 0; i < 4; i++) {
			String b = "target_" + i;
			if (a.targets().get(i).getAsJsonObject().get("kind").getAsString().equals("bag")) {
				assertTrue(a.cubes(a.groups.get(b)).keySet().stream().anyMatch(n -> n.startsWith("bag_bag")), b + " bag");
			} else {
				assertTrue(a.cubes(a.groups.get(b + "_arm_l")).keySet().stream().anyMatch(n -> n.endsWith("_arms_l")), b + " left arm");
				assertTrue(a.cubes(a.groups.get(b + "_arm_r")).keySet().stream().anyMatch(n -> n.endsWith("_arms_r")), b + " right arm");
				assertTrue(a.cubes(a.groups.get(b + "_head")).keySet().stream().anyMatch(n -> n.endsWith("_head")), b + " head");
			}
		}
	}

	@Test
	void swordAndShieldAreaHasThreeShieldDummies() throws Exception {
		Area a = new Area("training_area_shield");
		List<String> kinds = checkTargets(a);
		assertEquals(List.of("shield_dummy", "shield_dummy", "shield_dummy"), kinds);
		Map<String, double[]> st = a.staticCubes();
		for (int k = 0; k < 3; k++) {
			String d = "dummy_" + k;
			assertTrue(st.containsKey(d + "_plinth"), d + " plinth static");
			for (String part : List.of("_torso", "_head", "_helm", "_arm_l", "_arm_r", "_shield", "_sword_blade", "_leg_l")) {
				assertFalse(st.containsKey(d + part), d + part + " not static");
			}
		}
	}

	@Test
	void tatamiBenchHasTwoSeatsAndNoTarget() throws Exception {
		Area a = new Area("training_area_tatami");
		assertEquals(0, a.targets().size(), "no dummy in the tatami area");
		assertFalse(a.groups.keySet().stream().anyMatch(n -> n.startsWith("target_")), "no target bone");
		JsonArray seats = a.data.getAsJsonArray("seats");
		assertNotNull(seats, "seats");
		assertEquals(2, seats.size(), "the bench's two places");
		List<double[]> colliders = new ArrayList<>();
		for (JsonElement c : a.data.getAsJsonArray("colliders")) {
			colliders.add(vec(c, 6));
		}
		double[] prev = null;
		for (JsonElement e : seats) {
			JsonObject s = e.getAsJsonObject();
			double[] p = vec(s.get("pos"), 3);
			double yaw = s.get("yaw").getAsDouble();
			assertTrue(yaw >= 0 && yaw < 360, "yaw " + yaw);
			assertEquals(0.0, yaw, EPS, "the bench faces the front (+z)");
			assertTrue(inside(a.extent, p[0], p[1], p[2], EPS), "seat inside the extent");
			assertTrue(p[1] > 0.4 && p[1] < 0.7, "sitting height " + p[1]);
			// on top of the bench: a collider right under the seat surface, nothing solid above it
			boolean onBench = false;
			for (double[] c : colliders) {
				if (inside(new double[] {c[0], 0, c[2], c[3], 10, c[5]}, p[0], 1, p[2], 0)) {
					if (c[4] <= p[1] + EPS && p[1] - c[4] < 0.15) {
						onBench = true;
					}
					assertFalse(c[1] < p[1] + 1.2 && c[4] > p[1] + 0.05, "nothing solid on the seat " + p[0] + "," + p[2]);
				}
			}
			assertTrue(onBench, "seat on the bench " + p[0] + "," + p[2]);
			if (prev != null) {
				assertTrue(Math.abs(p[0] - prev[0]) > 0.5, "two places side by side");
				assertEquals(prev[2], p[2], 1e-3, "on the same bench");
			}
			prev = p;
		}
	}
}
