package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * D2's four street decorations (1.20.0, tools/deco/generate_&lt;id&gt;.py + props_d2.py + atlas_d2.py on decolib): the herb
 * drying rack, the hanging lantern, the crown banner and the shade sails. Their JSONs (group "decorations") have the
 * model, the shared atlas, a sane extent, the collision boxes (the posts collide, the cloth, ropes and bundles do not:
 * the passages stay free) and the light (15 for the lantern); the .bbmodels load static and light (at most 250 cubes,
 * a "detail" bone) with the pictures' contents where they belong.
 */
public class DecorationModelsD2Test {
	private static final double EPS = 1e-6;
	private static final String SECHOIR = "deco_sechoir", LANTERNE = "deco_lanterne", BANNIERE = "deco_banniere", OMBRAGE = "deco_ombrage";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = DecorationModelsD2Test.class.getResourceAsStream(path)) {
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

	/** decorations/&lt;id&gt;.json: paths, extent (width along x, depth along z, height), light; the collision boxes. */
	private static List<double[]> colliders(String id, double minW, double maxW, double maxD, double minH, double maxH, int light)
			throws Exception {
		JsonObject j = json("/assets/medievalships/decorations/" + id + ".json");
		assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/decorations.png", j.get("texture").getAsString());
		assertTrue(!j.has("decor") || j.get("decor").isJsonNull(), id + " no mod furniture");
		assertEquals(light, j.get("light").getAsInt(), id + " light");
		double[] e = box(j.get("extent"));
		assertEquals(0.0, e[1], EPS, id + " stands on the ground");
		double w = e[3] - e[0], d = e[5] - e[2], h = e[4] - e[1];
		assertTrue(w >= minW && w <= maxW && d <= maxD && h >= minH && h <= maxH && h <= 6.0, id + " size " + w + " x " + h + " x " + d);
		assertTrue(e[0] < 0.5 && e[3] > -0.5 && e[2] < 0.5 && e[5] > -0.5, id + " the anchor block is inside the extent");
		List<double[]> cs = new ArrayList<>();
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			double[] b = box(c);
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, id + " inside the extent " + c);
			// thin posts, not walls
			assertTrue(Math.min(b[3] - b[0], b[5] - b[2]) <= 0.95, id + " thin collision box " + c);
			cs.add(b);
		}
		return cs;
	}

	/** Element name -&gt; centre in prop-local blocks (x and z negated back from Blockbench; rotations ignored). */
	private static Map<String, double[]> model(String id) throws Exception {
		String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
		int[] glow = {0};
		try (InputStream in = DecorationModelsD2Test.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.animations.isEmpty(), id + " static");
			assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
			assertTrue(m.quadCount() > 60, id + " faces " + m.quadCount());
			m.render(m.newPose(), (p, uv, n, g) -> glow[0] += g ? 1 : 0);
		}
		Map<String, double[]> c = new LinkedHashMap<>();
		for (JsonElement el : json(path).getAsJsonArray("elements")) {
			JsonObject o = el.getAsJsonObject();
			JsonArray f = o.getAsJsonArray("from"), t = o.getAsJsonArray("to");
			double[] p = new double[3];
			for (int i = 0; i < 3; i++) {
				p[i] = (f.get(i).getAsDouble() + t.get(i).getAsDouble()) / 32.0 * (i == 1 ? 1 : -1);
			}
			c.put(o.get("name").getAsString(), p);
		}
		assertTrue(c.size() >= 25 && c.size() <= 250, id + " cube budget " + c.size());
		assertNotNull(DecorationModelsD2Test.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
		assertNotNull(DecorationModelsD2Test.class.getResource("/assets/medievalships/textures/entity/decorations.png"), id + " atlas");
		if (LANTERNE.equals(id)) {
			assertTrue(glow[0] >= 6, id + " the lantern's glass is lit (" + glow[0] + " full-bright faces)");
		}
		return c;
	}

	private static List<double[]> named(Map<String, double[]> m, String prefix) {
		List<double[]> out = new ArrayList<>();
		m.forEach((n, p) -> {
			if (n.startsWith(prefix)) {
				out.add(p);
			}
		});
		return out;
	}

	@Test
	void herbRackPostsOnFootingsBeamFourBundlesFreePassage() throws Exception {
		List<double[]> cs = colliders(SECHOIR, 4.3, 5.0, 1.5, 3.8, 4.8, 0);
		assertTrue(hits(cs, -2.0, 1.5, -0.1, -1.8, 2.5, 0.1), "left post");
		assertTrue(hits(cs, 1.8, 1.5, -0.1, 2.0, 2.5, 0.1), "right post");
		assertTrue(hits(cs, -2.25, 0.2, -0.35, -2.15, 0.6, 0.35) && hits(cs, 2.15, 0.2, -0.35, 2.25, 0.6, 0.35), "stone footings");
		assertFalse(hits(cs, -1.45, 0.0, -0.7, 1.45, 3.5, 0.7), "the bundles and the passage under the beam do not collide");
		Map<String, double[]> m = model(SECHOIR);
		double[] beam = m.get("beam");
		assertNotNull(beam, "beam");
		assertTrue(beam[1] > 3.3 && beam[1] < 4.2, "beam high across the posts " + beam[1]);
		assertNotNull(m.get("brace"), "angled brace");
		assertTrue(m.containsKey("post_l_footing") && m.containsKey("post_r_footing"), "stone footings drawn");
		double lastX = -9;
		for (int k = 0; k < 4; k++) {
			List<double[]> bunch = named(m, "bundle_" + k + "_bunch_");
			assertTrue(bunch.size() >= 3, "bundle " + k + " crossed planes");
			double[] c = bunch.get(0);
			assertTrue(c[0] > lastX && Math.abs(c[0]) < 1.65, "bundle " + k + " between the posts, left to right: x " + c[0]);
			assertTrue(c[1] > 1.4 && c[1] < beam[1] - 0.4, "bundle " + k + " hangs under the beam: y " + c[1]);
			assertTrue(m.containsKey("bundle_" + k + "_tie") && m.containsKey("bundle_" + k + "_rope_0") && m.containsKey("bundle_" + k + "_loop"),
					"bundle " + k + " tied on a rope looped over the beam");
			lastX = c[0];
		}
	}

	@Test
	void lanternPostArmBraceAndLitLanternOnItsChain() throws Exception {
		List<double[]> cs = colliders(LANTERNE, 1.8, 2.6, 1.4, 3.4, 4.0, 15);
		assertTrue(hits(cs, -0.1, 0.3, -0.1, 0.1, 3.2, 0.1), "the post collides at the anchor");
		assertTrue(hits(cs, 1.1, 1.7, -0.1, 1.3, 2.2, 0.1), "the lantern's body collides");
		assertFalse(hits(cs, -1.0, 0.0, 0.5, 2.0, 3.0, 1.5), "nothing collides in front");
		assertFalse(hits(cs, 0.3, 0.0, -0.4, 1.7, 1.25, 0.4), "free under the lantern");
		Map<String, double[]> m = model(LANTERNE);
		double[] glass = m.get("glow_lantern_glass");
		assertNotNull(glass, "lit glass");
		assertTrue(Math.abs(glass[0] - 1.2) < 0.15 && Math.abs(glass[2]) < 0.05, "the lantern hangs at the arm's end: x " + glass[0]);
		assertTrue(glass[1] > 1.5 && glass[1] < 2.6, "the lantern hangs at head height: y " + glass[1]);
		assertTrue(named(m, "chain_link_").size() >= 2, "a chain");
		for (double[] l : named(m, "chain_link_")) {
			assertTrue(Math.abs(l[0] - glass[0]) < 0.05 && l[1] > glass[1] + 0.4, "chain links above the lantern");
		}
		assertNotNull(m.get("arm"), "arm");
		assertTrue(m.get("arm")[1] > 3.0, "arm at the top");
		assertNotNull(m.get("brace"), "brace");
		assertTrue(named(m, "lantern_post_").size() == 4 && m.containsKey("lantern_cap") && m.containsKey("lantern_base"), "framed lantern");
		assertTrue(m.containsKey("sleeve") && m.containsKey("post_band_0"), "sleeve and iron band on the post");
	}

	@Test
	void crownBannerHangsFromAGoldRodBesideThePost() throws Exception {
		List<double[]> cs = colliders(BANNIERE, 1.9, 2.6, 1.0, 3.8, 4.3, 0);
		assertTrue(hits(cs, -0.1, 0.5, -0.1, 0.1, 3.8, 0.1), "the post collides at the anchor");
		assertFalse(hits(cs, 0.45, 0.0, -0.3, 2.0, 3.2, 0.3), "the banner does not collide");
		Map<String, double[]> m = model(BANNIERE);
		List<double[]> cloth = new ArrayList<>();
		m.forEach((n, p) -> {
			if (n.matches("banner_\\d+_\\d+")) {
				cloth.add(p);
			}
		});
		assertTrue(cloth.size() >= 3, "banner cloth strips");
		for (double[] p : cloth) {
			assertTrue(p[0] > 0.6 && p[0] < 1.5 && p[1] > 0.6 && p[1] < 3.2, "banner beside the post, under the arm: " + p[0] + ", " + p[1]);
		}
		double[] rod = m.get("banner_rod");
		assertNotNull(rod, "gold rod");
		assertTrue(rod[1] < m.get("arm")[1] && rod[1] > 2.9, "the rod hangs under the arm");
		assertTrue(m.containsKey("arm_ring_0") && m.containsKey("arm_ring_1") && m.containsKey("finial"), "gold rings and finial");
		assertTrue(m.containsKey("collar") && m.containsKey("top_block"), "collars of the post");
	}

	@Test
	void shadeSailsFourPostsTwoSailsAboveHeadsOpenShelter() throws Exception {
		List<double[]> cs = colliders(OMBRAGE, 4.8, 5.5, 4.4, 3.5, 4.2, 0);
		for (int sx = -1; sx <= 1; sx += 2) {
			for (int sz = -1; sz <= 1; sz += 2) {
				double x = 2.3 * sx, z = 1.75 * sz;
				assertTrue(hits(cs, x - 0.05, 1.0, z - 0.05, x + 0.05, 2.0, z + 0.05), "post at " + x + ", " + z);
			}
		}
		assertFalse(hits(cs, -2.0, 0.0, -1.45, 2.0, 3.6, 1.45), "the shelter is open: nothing collides inside");
		Map<String, double[]> m = model(OMBRAGE);
		List<double[]> upper = named(m, "sail_upper_"), lower = named(m, "sail_lower_");
		assertTrue(upper.size() >= 20 && lower.size() >= 20, "two sails");
		double minUpper = 9, minLower = 9;
		for (double[] p : upper) {
			if (Math.abs(p[0]) < 1.8 && Math.abs(p[2]) < 1.3) {
				minUpper = Math.min(minUpper, p[1]);
			}
		}
		for (double[] p : lower) {
			if (Math.abs(p[0]) < 1.8 && Math.abs(p[2]) < 1.3) {
				minLower = Math.min(minLower, p[1]);
			}
		}
		assertTrue(minLower >= 1.85, "the lower sail stays above head height: " + minLower);
		assertTrue(minUpper > minLower, "the upper sail is above the lower one");
		// tilted opposite ways: the upper sail rises to the right at the front, the lower one falls to the right
		double[] ul = m.get("sail_upper_0_0"), ur = m.get("sail_upper_5_0"), ll = m.get("sail_lower_0_0"), lr = m.get("sail_lower_5_0");
		assertTrue(ur[1] > ul[1] + 0.3 && lr[1] < ll[1] - 0.2, "the sails cross: upper " + ul[1] + " -> " + ur[1] + ", lower " + ll[1] + " -> " + lr[1]);
		assertTrue(named(m, "post_bl_footing").size() == 1 && named(m, "post_br_footing").size() == 1, "stone footings at the back");
		assertTrue(named(m, "post_fr_bind_").size() >= 6, "rope bindings where the sails are tied");
	}
}
