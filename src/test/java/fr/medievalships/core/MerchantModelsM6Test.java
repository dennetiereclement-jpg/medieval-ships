package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The model of the armour merchant's tent (tente_armures: tools/merchant/generate_tente_armures.py + props_m6.py):
 * its JSON has the model, texture, extent and collision boxes; the merchant's place behind the counter (right) is free
 * (1 x 1 x 2.2 blocks); the rug in front is walkable; the .bbmodel loads static and light, with a "detail" bone, lit
 * lanterns, four armour stands of different styles, helmets of several shapes and the eagle shield; its mod furniture
 * list exists.
 */
public class MerchantModelsM6Test {
	private static final double EPS = 1e-6;
	private static final String ID = "tente_armures";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM6Test.class.getResourceAsStream(path)) {
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

	@Test
	void jsonExtentCollidersMerchantPlaceAndDecor() throws Exception {
		JsonObject j = json("/assets/medievalships/tents/" + ID + ".json");
		assertEquals("models/entity/" + ID + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/" + ID + ".png", j.get("texture").getAsString());
		double[] e = box(j.get("extent"));
		assertEquals(0.0, e[1], EPS, "stands on the ground");
		double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
		assertTrue(w > 6.0 && w < 10.0 && d > 6.0 && d < 10.0 && h > 6.0 && h < 10.0, "size " + w + " x " + h + " x " + d);
		List<double[]> cs = new ArrayList<>();
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			double[] b = box(c);
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], "box " + c);
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, "inside the extent " + c);
			cs.add(b);
		}
		assertTrue(cs.size() >= 15, "collision boxes " + cs.size());
		// the counter on the right (x 1.4 .. 2.8, z -0.25 .. 0.45) is solid, the merchant's place behind it is free
		assertTrue(hits(cs, 1.6, 0.5, -0.1, 2.6, 0.9, 0.3), "the counter is solid");
		assertFalse(hits(cs, 1.75, 0.0, -1.8, 2.75, 2.2, -0.8), "a free place of 1 x 1 x 2.2 blocks behind the counter");
		// the armour stands are solid, the front (the rug before the stands) is walkable
		assertTrue(hits(cs, -0.4, 0.5, -1.1, -0.1, 1.5, -0.8), "the middle armour stand is solid");
		assertFalse(hits(cs, -0.7, 0.0, 0.75, 1.95, 2.0, 4.6), "nothing solid on the rug");
		assertTrue(j.has("decor") && !j.get("decor").isJsonNull(), "mod furniture");
		JsonObject decor = json(j.get("decor").getAsString());
		assertTrue(decor.getAsJsonArray("blocks").size() >= 5, "mod blocks");
	}

	@Test
	void modelLoadsLightWithDetailGlowAndItsArmours() throws Exception {
		String path = "/assets/medievalships/models/entity/" + ID + ".bbmodel";
		try (InputStream in = MerchantModelsM6Test.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 1000 && m.quadCount() < 950 * 6, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "static");
			assertTrue(m.bonesByName.containsKey("detail"), "detail bone");
		}
		JsonObject model = json(path);
		int glow = 0, cubes = 0;
		List<String> names = new ArrayList<>();
		for (JsonElement el : model.getAsJsonArray("elements")) {
			String n = el.getAsJsonObject().get("name").getAsString();
			names.add(n);
			cubes++;
			if (n.startsWith("glow")) {
				glow++;
			}
		}
		assertTrue(cubes <= 950, "cube budget " + cubes);
		assertTrue(glow >= 2, "lit elements " + glow);
		for (String part : new String[] {"knight_chest", "fantasy_chest", "heavy_chest", "soldier_chest", "heavy_helm_visor",
				"eagle_shield", "rug", "banner_front", "counter_top", "chest_l_lid"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), "element " + part);
		}
		long helmets = names.stream().filter(n -> n.contains("helm") && (n.endsWith("_body") || n.endsWith("_l0_0"))).count();
		assertTrue(helmets >= 10, "helmets " + helmets);
		assertNotNull(MerchantModelsM6Test.class.getResource("/assets/medievalships/textures/item/" + ID + ".png"), "icon");
		assertNotNull(MerchantModelsM6Test.class.getResource("/assets/medievalships/textures/entity/" + ID + ".png"), "atlas");
	}
}
