package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The models of two merchant tents (the blacksmith's and the food merchant's: tools/merchant/generate_tente_*.py):
 * each JSON (assets/medievalships/tents/&lt;id&gt;.json) has its model, texture, extent and collision boxes, its
 * .bbmodel loads static and light, with a "detail" bone and lit (glow) elements, and its mod furniture list exists.
 */
public class MerchantModelsM2Test {
	private static final double EPS = 1e-6;
	private static final List<String> IDS = List.of("tente_forgeron", "tente_nourriture");

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM2Test.class.getResourceAsStream(path)) {
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

	@Test
	void jsonHasExtentAndColliders() throws Exception {
		for (String id : IDS) {
			JsonObject j = json("/assets/medievalships/tents/" + id + ".json");
			assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
			assertEquals("textures/entity/" + id + ".png", j.get("texture").getAsString());
			double[] e = box(j.get("extent"));
			assertEquals(0.0, e[1], EPS, id + " stands on the ground");
			double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
			assertTrue(w > 5.5 && w < 10.0 && d > 5.5 && d < 11.0 && h > 5.5 && h < 10.0, id + " size " + w + " x " + h + " x " + d);
			JsonArray cs = j.getAsJsonArray("colliders");
			assertTrue(cs.size() >= 10, id + " collision boxes " + cs.size());
			for (JsonElement c : cs) {
				double[] b = box(c);
				assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
				assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
						&& b[4] <= e[4] + 0.06, id + " inside the extent " + c);
			}
			assertTrue(j.has("decor") && !j.get("decor").isJsonNull(), id + " has mod furniture");
			JsonObject decor = json(j.get("decor").getAsString());
			assertTrue(decor.getAsJsonArray("blocks").size() >= 3, id + " mod blocks");
		}
	}

	@Test
	void modelsLoadLightWithDetailAndGlow() throws Exception {
		for (String id : IDS) {
			String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
			try (InputStream in = MerchantModelsM2Test.class.getResourceAsStream(path)) {
				assertNotNull(in, path);
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 600 && m.quadCount() < 1100 * 6, id + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), id + " is static");
				assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
			}
			JsonObject model = json(path);
			int glow = 0;
			for (JsonElement el : model.getAsJsonArray("elements")) {
				if (el.getAsJsonObject().get("name").getAsString().startsWith("glow")) {
					glow++;
				}
			}
			assertTrue(glow >= 2, id + " lit elements " + glow);
			assertNotNull(MerchantModelsM2Test.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
			assertNotNull(MerchantModelsM2Test.class.getResource("/assets/medievalships/textures/entity/" + id + ".png"), id + " atlas");
		}
	}
}
