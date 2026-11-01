package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
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
 * The models of the tatami and the sword &amp; shield training areas (1.18.0: training_area_tatami, training_area_shield;
 * tools/training/generate_&lt;id&gt;.py + props_l.py on traininglib): their JSONs (group "training") have the model,
 * texture, extent and collision boxes; the fences collide all round (1.5 high), the entrance in the middle of the front
 * is free, the yard inside is walkable (the floor plate lies on the ground and does not collide), the solid furniture
 * collides; the .bbmodels load static and light (at most 900 cubes, a "detail" bone) with the pictures' contents; the
 * three wooden dummies of the shield area wear helmets, hold their swords (the grip in the right fist) and carry their
 * round shields (the left fist against the shield's back).
 */
public class TrainingModelsLTest {
	private static final double EPS = 1e-6;
	private static final String TATAMI = "training_area_tatami", SHIELD = "training_area_shield";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = TrainingModelsLTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}

	private static double[] box(JsonElement e) {
		JsonArray a = e.getAsJsonArray();
		assertEquals(6, a.size());
		double[] b = new double[6];
		for (int i = 0; i < 6; i++) {
			b[i] = a.get(i).getAsDouble();
		}
		return b;
	}

	private static boolean hits(List<double[]> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		for (double[] b : boxes) {
			if (b[0] < x1 && b[3] > x0 && b[1] < y1 && b[4] > y0 && b[2] < z1 && b[5] > z0) {
				return true;
			}
		}
		return false;
	}

	/** Reads training/&lt;id&gt;.json: checks the paths and the extent, returns the collision boxes (all inside it). */
	private static List<double[]> colliders(String id, double minW, double maxW, double minD, double maxD) throws Exception {
		JsonObject j = json("/assets/medievalships/training/" + id + ".json");
		assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/" + id + ".png", j.get("texture").getAsString());
		double[] e = box(j.get("extent"));
		assertEquals(0.0, e[1], EPS, id + " stands on the ground");
		double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
		assertTrue(w >= minW && w <= maxW && d >= minD && d <= maxD && h > 2.5 && h < 4.5, id + " size " + w + " x " + h + " x " + d);
		List<double[]> cs = new ArrayList<>();
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			double[] b = box(c);
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, id + " inside the extent " + c);
			// no invisible step: nothing flat lies on the ground (the floor plate does not collide)
			assertFalse(b[4] <= 0.2 && (b[3] - b[0]) * (b[5] - b[2]) > 1.0, id + " no flat collision on the ground " + c);
			cs.add(b);
		}
		assertTrue(cs.size() >= 30, id + " collision boxes " + cs.size());
		if (j.has("decor") && !j.get("decor").isJsonNull()) {
			assertTrue(json(j.get("decor").getAsString()).getAsJsonArray("blocks").size() >= 1, id + " mod furniture");
		}
		return cs;
	}

	/** The four fences collide about 1.5 high, the entrance (middle of the front, z = hd) is free. */
	private static void fencesAndEntrance(String id, List<double[]> cs, double hw, double hd) {
		assertTrue(hits(cs, -hw - 0.05, 1.2, -0.3, -hw + 0.05, 1.4, 0.3), id + " left fence");
		assertTrue(hits(cs, hw - 0.05, 1.2, -0.3, hw + 0.05, 1.4, 0.3), id + " right fence");
		assertTrue(hits(cs, -0.3, 1.2, -hd - 0.05, 0.3, 1.4, -hd + 0.05), id + " back fence");
		assertTrue(hits(cs, -hw + 0.4, 1.2, hd - 0.05, -hw + 1.0, 1.4, hd + 0.05), id + " front fence (left)");
		assertTrue(hits(cs, hw - 1.0, 1.2, hd - 0.05, hw - 0.4, 1.4, hd + 0.05), id + " front fence (right)");
		assertFalse(hits(cs, -0.75, 0.0, hd - 1.2, 0.75, 2.0, hd + 0.6), id + " the entrance is free (>= 1.5 wide between the gate posts)");
	}

	private static Map<String, double[]> centres(JsonObject model, List<String> names) {
		Map<String, double[]> m = new HashMap<>();
		for (JsonElement el : model.getAsJsonArray("elements")) {
			JsonObject o = el.getAsJsonObject();
			String n = o.get("name").getAsString();
			names.add(n);
			JsonArray f = o.getAsJsonArray("from"), t = o.getAsJsonArray("to");
			double[] c = new double[3];
			for (int i = 0; i < 3; i++) {
				c[i] = (f.get(i).getAsDouble() + t.get(i).getAsDouble()) / 32.0;
			}
			m.put(n, c);
		}
		return m;
	}

	private static Map<String, double[]> model(String id, List<String> names) throws Exception {
		String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
		try (InputStream in = TrainingModelsLTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 600 && m.quadCount() < 900 * 6, id + " faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), id + " static");
			assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
		}
		Map<String, double[]> c = centres(json(path), names);
		assertTrue(names.size() <= 900, id + " cube budget " + names.size());
		assertTrue(names.stream().filter(n -> n.startsWith("glow")).count() >= 2, id + " lit lanterns");
		assertNotNull(TrainingModelsLTest.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
		assertNotNull(TrainingModelsLTest.class.getResource("/assets/medievalships/textures/entity/" + id + ".png"), id + " atlas");
		return c;
	}

	private static void has(String id, List<String> names, String... parts) {
		for (String part : parts) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), id + " element " + part);
		}
	}

	private static double dist(double[] a, double[] b) {
		return Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
	}

	@Test
	void tatamiFencesEntranceWalkableYardAndSolidFurniture() throws Exception {
		List<double[]> cs = colliders(TATAMI, 6.0, 9.0, 6.0, 9.0);
		fencesAndEntrance(TATAMI, cs, 3.4, 3.4);
		// the tatami yard: from the entrance to the back of the mats nothing stands in the way
		assertFalse(hits(cs, -2.1, 0.0, -1.9, 2.6, 2.0, 2.9), TATAMI + " the yard on the mats is free");
		// the stall's bench and shelves, the lantern posts, the flower pot, the weapon rack, the banner post collide
		assertTrue(hits(cs, -0.6, 0.2, -2.8, -0.3, 0.4, -2.6), TATAMI + " the bench is solid");
		assertTrue(hits(cs, -1.7, 0.6, -3.0, -1.4, 1.2, -2.8), TATAMI + " the left shelves are solid");
		assertTrue(hits(cs, -3.45, 2.0, -3.45, -3.35, 2.6, -3.35), TATAMI + " the left lantern post");
		assertTrue(hits(cs, 3.35, 2.0, -3.45, 3.45, 2.6, -3.35), TATAMI + " the right lantern post");
		assertTrue(hits(cs, -3.5, 0.5, 3.3, -3.3, 1.0, 3.5), TATAMI + " the flower pot's pedestal");
		assertTrue(hits(cs, -3.2, 0.5, -1.3, -2.9, 1.0, -1.0), TATAMI + " the rack of staves");
		assertTrue(hits(cs, 2.4, 1.0, -3.0, 2.5, 2.0, -2.9), TATAMI + " the banner post");
	}

	@Test
	void tatamiModelFloorStallBannersLanternsWeapons() throws Exception {
		List<String> names = new ArrayList<>();
		model(TATAMI, names);
		has(TATAMI, names, "floor", "floor_seams_seam_", "post_front_right_base", "post_back_left_cap", "bay_front_", "stall_roof_",
				"stall_valance_0", "stall_post_front_left", "stall_wall", "bench_seat", "bench_roll_0_", "bench_cushion", "shelf_0_board_",
				"shelf_1_board_", "shelf_0_jar_", "shelf_0_cloth_", "wall_sword_0_blade", "wall_staff", "banner_back_", "banner_front_",
				"banner_post", "lamp_left_post", "lamp_right_arm", "flower_pot_ped", "flower_pot_flowers_", "rack_left_up_0",
				"rack_left_staff_0", "rack_left_wsword_1_blade", "lean_left_", "lean_right_staff_0", "log_barrel", "stool_jar_0");
		assertFalse(names.stream().anyMatch(n -> n.startsWith("post_front_left")), TATAMI + ": the flower pot stands at the front-left corner");
		assertFalse(names.stream().anyMatch(n -> n.startsWith("dummy")), TATAMI + ": no dummies (as on the picture)");
	}

	@Test
	void shieldFencesEntranceWalkableYardDummiesAndRacks() throws Exception {
		List<double[]> cs = colliders(SHIELD, 7.0, 10.0, 6.0, 8.0);
		fencesAndEntrance(SHIELD, cs, 4.0, 3.15);
		// the three dummies collide, the yard between them is free
		double[][] dummies = {{-1.35, 0.85}, {0.55, -0.15}, {2.35, -1.2}};
		for (double[] d : dummies) {
			assertTrue(hits(cs, d[0] - 0.1, 1.0, d[1] - 0.1, d[0] + 0.1, 1.5, d[1] + 0.1), SHIELD + " the dummy at " + d[0] + ", " + d[1]);
		}
		assertFalse(hits(cs, -0.5, 0.0, 1.2, 0.5, 2.0, 2.9), SHIELD + " the way in from the entrance");
		assertFalse(hits(cs, 1.4, 0.0, 0.8, 3.2, 2.0, 2.5), SHIELD + " the yard at the front right");
		assertFalse(hits(cs, -0.6, 0.0, -1.6, 0.2, 2.0, -0.95), SHIELD + " the yard behind the middle dummy");
		// the stall's racks, the right sword rack, the barrel, the lantern posts on the back pillars
		assertTrue(hits(cs, -3.0, 0.3, -2.7, -2.7, 0.8, -2.5), SHIELD + " the shield rack");
		assertTrue(hits(cs, -1.8, 0.3, -2.7, -1.5, 0.8, -2.5), SHIELD + " the stall's sword rack");
		assertTrue(hits(cs, 3.55, 0.3, -1.8, 3.7, 0.8, -1.6), SHIELD + " the sword rack by the right fence");
		assertTrue(hits(cs, -3.45, 0.3, -1.4, -3.3, 0.6, -1.2), SHIELD + " the barrel");
		assertTrue(hits(cs, -4.05, 2.2, -3.2, -3.95, 2.8, -3.1), SHIELD + " the left lantern post");
		assertTrue(hits(cs, 3.95, 2.2, -3.2, 4.05, 2.8, -3.1), SHIELD + " the right lantern post");
	}

	@Test
	void shieldModelDummiesHoldSwordsAndShieldsStallBannersPillars() throws Exception {
		List<String> names = new ArrayList<>();
		Map<String, double[]> c = model(SHIELD, names);
		has(SHIELD, names, "floor", "post_front_left_pillar", "post_back_right_pcap", "bay_left_", "stall_roof_", "stall_valance_",
				"stall_wall", "shield_rack_shield_0", "shield_rack_sword_0_blade", "wall_shield_0", "stall_swords_sword_0_blade",
				"rack_right_sword_3_blade", "banner_front_0_", "banner_front_1_", "banner_stall_", "front_banner_post_0",
				"stall_banner_post", "lamp_left_post", "lamp_right_lamp", "barrel_small", "bucket");
		for (int k = 0; k < 3; k++) {
			String d = "dummy_" + k;
			has(SHIELD, names, d + "_plinth", d + "_leg_l", d + "_torso", d + "_head", d + "_helm", d + "_helm_crown", d + "_helm_slit",
					d + "_arm_r", d + "_forearm_l", d + "_sword_blade", d + "_sword_guard", d + "_shield", d + "_shield_boss");
			// the sword's grip in the right fist, the left fist against the shield's back, the helmet on the head
			assertTrue(dist(c.get(d + "_fist_r"), c.get(d + "_sword_grip")) < 0.08, d + ": the sword is held");
			double s = dist(c.get(d + "_fist_l"), c.get(d + "_shield"));
			assertTrue(s > 0.08 && s < 0.16, d + ": the shield is strapped on the forearm (" + s + ")");
			assertTrue(dist(c.get(d + "_head"), c.get(d + "_helm")) < 0.15, d + ": the helmet sits on the head");
			assertTrue(c.get(d + "_helm")[1] > 1.6 && c.get(d + "_helm")[1] < 2.0, d + ": the helmet's height");
		}
	}
}
