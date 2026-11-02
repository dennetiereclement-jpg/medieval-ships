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
 * The model of the nomad tavern (1.19.0: taverne_nomade, group "carts", tools/tavern/generate_taverne_nomade.py on
 * tavernlib): its JSON parses as a cart TentType with its atlas, decor, about 13 x 9 blocks, collision boxes inside the
 * extent (wagon body, wheels, counter, tables, low stools, barrels, fire ring, posts) and a walkable terrace between the
 * tables; its "seats" (contract B: the centre of the seat surface, the yaw the sitter faces) sit on top of a stool's
 * collision box where a furnish:spruce_stool stands in the decor (with a stand-in stool bone in the model), nothing
 * above the sitter, each sitter facing a table or the counter; its particles are known types inside the extent (the
 * chimney's smoke, the camp fire); the .bbmodel loads static and within budget (at most 1500 cubes, a "detail" bone)
 * with the picture's contents: round wheels, a rounded canvas roof, the chimney, the counter, the mug banners and sign,
 * the awning, the tables, the rug, the camp fire and the cauldron.
 */
public class TavernModelTest {
	private static final double EPS = 1e-6;
	private static final String ID = "taverne_nomade";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = TavernModelTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}

	private static double[] arr(JsonElement e, int n) {
		JsonArray a = e.getAsJsonArray();
		assertEquals(n, a.size());
		double[] b = new double[n];
		for (int i = 0; i < n; i++) {
			b[i] = a.get(i).getAsDouble();
		}
		return b;
	}

	private static List<double[]> colliders(JsonObject j) {
		List<double[]> cs = new ArrayList<>();
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			cs.add(arr(c, 6));
		}
		return cs;
	}

	private static List<double[]> hits(List<double[]> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		List<double[]> out = new ArrayList<>();
		for (double[] b : boxes) {
			if (b[0] < x1 && b[3] > x0 && b[1] < y1 && b[4] > y0 && b[2] < z1 && b[5] > z0) {
				out.add(b);
			}
		}
		return out;
	}

	private static boolean hit(List<double[]> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		return !hits(boxes, x0, y0, z0, x1, y1, z1).isEmpty();
	}

	@Test
	void jsonParsesAsACartWithExtentAndColliders() throws Exception {
		JsonObject j = json("/assets/medievalships/carts/" + ID + ".json");
		assertEquals("models/entity/" + ID + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/" + ID + ".png", j.get("texture").getAsString());
		TentType t = TentType.parse(TentType.CARTS, ID, "taverne nomade", "Nomad Tavern", j);
		assertTrue(t.isCart());
		double[] e = arr(j.get("extent"), 6);
		assertEquals(0.0, e[1], EPS, "stands on the ground");
		double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
		assertTrue(w >= 12.0 && w <= 14.5 && d >= 8.5 && d <= 10.5 && h >= 4.5 && h <= 6.5, "size " + w + " x " + h + " x " + d);
		List<double[]> cs = colliders(j);
		assertTrue(cs.size() >= 40, "collision boxes " + cs.size());
		for (double[] b : cs) {
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], "box " + java.util.Arrays.toString(b));
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, "inside the extent " + java.util.Arrays.toString(b));
		}
		// the decor: stools, wine bottles, the tapped barrel (mod blocks with stand-ins)
		JsonArray blocks = json(j.get("decor").getAsString()).getAsJsonArray("blocks");
		assertTrue(blocks.size() >= 15, "mod furniture " + blocks.size());
	}

	@Test
	void solidPartsCollideAndTheTerraceIsWalkable() throws Exception {
		List<double[]> cs = colliders(json("/assets/medievalships/carts/" + ID + ".json"));
		assertTrue(hit(cs, -2.0, 1.5, -3.0, -1.0, 2.5, -2.0), "the wagon body");
		assertTrue(hit(cs, -1.5, 3.4, -2.8, -1.0, 4.2, -2.2), "the canvas roof");
		for (double[] w : new double[][] {{-3.75, -0.8}, {-3.75, -4.2}, {1.05, -0.8}, {1.05, -4.2}}) {
			assertTrue(hit(cs, w[0] - 0.05, 0.9, w[1] - 0.05, w[0] + 0.05, 1.0, w[1] + 0.05), "the wheel at " + w[0] + ", " + w[1]);
		}
		assertTrue(hit(cs, -1.5, 1.95, -0.9, -1.4, 2.0, -0.8), "the counter board");
		for (double[] t : new double[][] {{-5.05, 2.6}, {-1.15, 2.25}, {2.9, 0.5}, {1.65, 2.85}, {3.35, -1.85}}) {
			assertTrue(hit(cs, t[0] - 0.05, 0.7, t[1] - 0.05, t[0] + 0.05, 0.8, t[1] + 0.05), "the table at " + t[0] + ", " + t[1]);
		}
		assertTrue(hit(cs, 5.6 - 0.65, 0.1, 0.95 - 0.05, 5.6 - 0.55, 0.2, 0.95 + 0.05), "the fire's stone ring");
		assertTrue(hit(cs, 4.25, 2.0, -0.35, 4.35, 2.5, -0.25), "the sign post");
		assertTrue(hit(cs, -5.05, 0.3, 0.5, -4.95, 0.6, 0.6), "the barrel by the steps");
		// the steps up to the porch: each step low enough to walk up
		for (double x : new double[] {-6.7, -6.4, -6.2, -5.9}) {
			double top = 0;
			for (double[] b : hits(cs, x - 0.01, 0.0, -2.8, x + 0.01, 2.0, -2.7)) {
				top = Math.max(top, b[4]);
			}
			assertTrue(top > 0.1 && top < 1.06, "a step at x " + x + ": " + top);
		}
		// walkable lanes (nothing taller than a step between 0.7 and 1.8): in from the front between the left and the
		// centre tables, between the centre table and the front-right tables, along the front, in front of the counter
		// ledge, under the awning
		assertFalse(hit(cs, -3.7, 0.7, 1.2, -3.1, 1.8, 4.4), "the lane left of the centre table");
		assertFalse(hit(cs, 0.45, 0.7, -0.1, 1.05, 1.8, 4.4), "the lane right of the centre table");
		assertFalse(hit(cs, -6.0, 0.7, 3.85, 3.0, 1.8, 4.4), "the front of the terrace");
		assertFalse(hit(cs, -2.6, 0.7, -0.05, 0.0, 1.8, 0.6), "in front of the counter's ledge");
		assertFalse(hit(cs, 2.5, 0.7, -0.95, 4.0, 2.2, -0.45), "under the awning");
		// no flat invisible step on the ground (the pavers and the rug do not collide)
		for (double[] b : cs) {
			assertFalse(b[4] <= 0.2 && (b[3] - b[0]) * (b[5] - b[2]) > 1.0, "no flat collision on the ground " + java.util.Arrays.toString(b));
		}
	}

	@Test
	void seatsSitOnStoolsAndFaceTheTables() throws Exception {
		JsonObject j = json("/assets/medievalships/carts/" + ID + ".json");
		double[] e = arr(j.get("extent"), 6);
		List<double[]> cs = colliders(j);
		JsonArray seats = j.getAsJsonArray("seats");
		assertNotNull(seats, "seats");
		assertTrue(seats.size() >= 15, "seats " + seats.size());
		JsonArray blocks = json(j.get("decor").getAsString()).getAsJsonArray("blocks");
		Map<String, Boolean> bones = new HashMap<>();
		JsonObject model = json("/assets/medievalships/models/entity/" + ID + ".bbmodel");
		collectBones(model.getAsJsonArray("outliner"), bones);
		int bar = 0;
		for (JsonElement el : seats) {
			JsonObject s = el.getAsJsonObject();
			double[] p = arr(s.get("pos"), 3);
			double yaw = s.get("yaw").getAsDouble();
			String at = "seat " + java.util.Arrays.toString(p);
			assertTrue(p[0] >= e[0] && p[0] <= e[3] && p[1] >= e[1] && p[1] <= e[4] && p[2] >= e[2] && p[2] <= e[5], at + " inside the extent");
			assertTrue(yaw >= 0 && yaw < 360 && Math.abs(yaw / 90.0 - Math.rint(yaw / 90.0)) < EPS, at + " yaw " + yaw);
			// on top of a stool: a small low box whose top is the seat surface
			boolean onStool = false;
			for (double[] b : cs) {
				if (Math.abs(b[4] - p[1]) < 0.01 && b[0] <= p[0] && b[3] >= p[0] && b[2] <= p[2] && b[5] >= p[2] && b[3] - b[0] < 0.8
						&& b[5] - b[2] < 0.8 && b[4] - b[1] < 0.6) {
					onStool = true;
				}
			}
			assertTrue(onStool, at + " on top of a stool's collision box");
			// a furnish stool stands there in the decor, with its stand-in bone in the model
			boolean decor = false;
			for (int i = 0; i < blocks.size(); i++) {
				JsonObject b = blocks.get(i).getAsJsonObject();
				if (b.get("block").getAsString().equals("furnish:spruce_stool") && Math.abs(b.get("x").getAsDouble() - p[0]) < EPS
						&& Math.abs(b.get("z").getAsDouble() - p[2]) < EPS && Math.abs(b.get("y").getAsDouble() + 0.5625 - p[1]) < EPS) {
					decor = true;
					assertTrue(bones.containsKey(b.get("fallback").getAsString()), at + " stand-in bone " + b.get("fallback"));
				}
			}
			assertTrue(decor, at + " a furnish:spruce_stool in the decor");
			// nothing where the sitter's body is
			assertFalse(hit(cs, p[0] - 0.2, p[1] + 0.05, p[2] - 0.2, p[0] + 0.2, p[1] + 1.2, p[2] + 0.2), at + " room for the sitter");
			// the sitter faces a table top or the counter board (0.2-0.6 above the seat), 0.4-0.75 ahead
			double a = Math.toRadians(yaw);
			boolean faces = false;
			for (double ahead : new double[] {0.4, 0.55, 0.75}) {
				double fx = p[0] - Math.sin(a) * ahead, fz = p[2] + Math.cos(a) * ahead;
				for (double[] b : cs) {
					if (b[0] <= fx && b[3] >= fx && b[2] <= fz && b[5] >= fz && b[4] - p[1] > 0.2 && b[4] - p[1] < 0.6) {
						faces = true;
					}
				}
			}
			assertTrue(faces, at + " faces a table (yaw " + yaw + ")");
			if (p[1] > 1.0) {
				bar++;
			}
		}
		assertEquals(3, bar, "the three bar stools on the ledge");
	}

	private static void collectBones(JsonArray outliner, Map<String, Boolean> bones) {
		for (JsonElement el : outliner) {
			if (el.isJsonObject()) {
				JsonObject o = el.getAsJsonObject();
				bones.put(o.get("name").getAsString(), true);
				if (o.has("children")) {
					collectBones(o.getAsJsonArray("children"), bones);
				}
			}
		}
	}

	@Test
	void particlesAreKnownAndInside() throws Exception {
		JsonObject j = json("/assets/medievalships/carts/" + ID + ".json");
		TentType t = TentType.parse(TentType.CARTS, ID, "taverne nomade", "Nomad Tavern", j);
		TentType.Box e = t.extent();
		assertTrue(t.particles().size() >= 2, "particles");
		boolean smoke = false, fire = false;
		for (TentType.Particle p : t.particles()) {
			assertTrue(p.known(), p.type());
			assertTrue(p.chance() > 0 && p.chance() <= 0.4, p + " rare");
			assertTrue(p.x() >= e.x0() && p.x() <= e.x1() && p.y() >= e.y0() && p.y() <= e.y1() + 0.5 && p.z() >= e.z0() && p.z() <= e.z1(),
					p + " inside");
			smoke |= p.type().equals("campfire_smoke") && p.y() > 5.0;
			fire |= p.type().equals("flame") && p.y() < 1.0;
		}
		assertTrue(smoke, "the chimney's smoke");
		assertTrue(fire, "the camp fire's flames");
	}

	@Test
	void modelLoadsWithThePicturesContents() throws Exception {
		String path = "/assets/medievalships/models/entity/" + ID + ".bbmodel";
		try (InputStream in = TavernModelTest.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.animations.isEmpty(), "static");
			assertTrue(m.bonesByName.containsKey("detail"), "detail bone");
			assertTrue(m.quadCount() > 3000, "faces " + m.quadCount());
		}
		assertNotNull(TavernModelTest.class.getResource("/assets/medievalships/textures/item/" + ID + ".png"), "icon");
		assertNotNull(TavernModelTest.class.getResource("/assets/medievalships/textures/entity/" + ID + ".png"), "atlas");
		JsonObject model = json(path);
		List<String> names = new ArrayList<>();
		Map<String, double[]> c = new HashMap<>();
		for (JsonElement el : model.getAsJsonArray("elements")) {
			JsonObject o = el.getAsJsonObject();
			String n = o.get("name").getAsString();
			names.add(n);
			double[] f = arr(o.get("from"), 3), to = arr(o.get("to"), 3);
			c.put(n, new double[] {(f[0] + to[0]) / 32.0, (f[1] + to[1]) / 32.0, (f[2] + to[2]) / 32.0});
		}
		assertTrue(names.size() <= 1500, "cube budget " + names.size());
		assertTrue(names.stream().filter(n -> n.startsWith("glow")).count() >= 10, "lit lanterns, windows and fire");
		for (String part : new String[] {"wheel_0_0_rim_", "wheel_1_1_spoke_", "canvas_0_", "canvas_1_", "canvas_2_", "rim_l_", "ivy_roof_",
				"chimney", "chest", "roof_crate", "banner_front_0", "banner_front_1", "banner_end", "door", "glow_door_window",
				"glow_side_window", "step_", "rail_post_", "hand_rope_", "board", "shelf_", "bottles_", "keg_0_", "keg_big_", "bar_mug_",
				"glow_bar_lamp_", "ledge", "cloth_", "valance_front_", "valance_side_", "sign_post", "sign_arm", "sign_board",
				"sign_board_chain_", "t_centre_top", "t_left_top", "t_right_top", "t_front_top", "t_back_top", "mug_t_centre_", "rug",
				"pavers_", "campfire_ring_", "glow_campfire_fire_flame", "trestle_bar", "trestle_pot_stave_", "trestle_chain_", "sack",
				"barrel_steps_stave_"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), "element " + part);
		}
		// round wheels: the 16 rim segments at the same distance from the hub
		double[] hub = c.get("wheel_0_0_hub_0");
		assertNotNull(hub, "hub");
		for (int k = 0; k < 16; k++) {
			double[] r = c.get("wheel_0_0_rim_" + k);
			assertNotNull(r, "rim " + k);
			double dist = Math.hypot(r[0] - hub[0], r[1] - hub[1]);
			assertEquals(0.87, dist, 0.06, "rim segment " + k + " on the circle");
			assertEquals(hub[2], r[2], 0.02, "rim segment " + k + " in the wheel's plane");
		}
		// a rounded roof, not a box: canvas strips from the eaves (about 3) to the ridge (about 4.5), the middle ones high
		double lo = 99, hi = -99;
		for (String n : names) {
			if (n.startsWith("canvas_1_")) {
				lo = Math.min(lo, c.get(n)[1]);
				hi = Math.max(hi, c.get(n)[1]);
			}
		}
		assertTrue(lo < 3.4 && hi > 4.2, "the canvas arch from " + lo + " to " + hi);
		assertTrue(c.get("chimney")[1] > 4.0, "the chimney stands above the roof");
	}
}
