package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
 * The archery and the mage merchant tents (tools/merchant/generate_tente_archer.py and generate_tente_mage.py): each
 * JSON (assets/medievalships/tents/&lt;id&gt;.json) names its own model and atlas, has a sane extent standing on the
 * ground and collision boxes inside it, and its .bbmodel loads static and light (at most ~900 cubes), with a "detail"
 * bone, lit (glow) elements and no particles; the archer's has its round training target in front at the left, the
 * mage's its staffs, glowing crystals and orb.
 */
public class MerchantModelsM5Test {
	private static final double EPS = 1e-6;
	private static final List<String> IDS = List.of("tente_archer", "tente_mage");

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM5Test.class.getResourceAsStream(path)) {
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
	void jsonHasModelTextureExtentAndColliders() throws Exception {
		for (String id : IDS) {
			JsonObject j = json("/assets/medievalships/tents/" + id + ".json");
			assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
			assertEquals("textures/entity/" + id + ".png", j.get("texture").getAsString());
			assertFalse(j.has("particles"), id + " has no permanent particles");
			double[] e = box(j.get("extent"));
			assertTrue(Math.abs(e[1]) < 0.06, id + " stands on the ground " + e[1]);
			double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
			assertTrue(w > 6.0 && w < 11.0 && d > 6.0 && d < 11.0 && h > 5.5 && h < 10.0, id + " size " + w + " x " + h + " x " + d);
			JsonArray cs = j.getAsJsonArray("colliders");
			assertTrue(cs.size() >= 10, id + " collision boxes " + cs.size());
			boolean target = false;
			for (JsonElement c : cs) {
				double[] b = box(c);
				assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
				assertTrue(b[0] >= e[0] - EPS && b[3] <= e[3] + EPS && b[2] >= e[2] - EPS && b[5] <= e[5] + EPS && b[1] >= -0.06
						&& b[4] <= e[4] + EPS, id + " inside the extent " + c);
				// the training target: a solid easel in front of the tent, left of the left front post
				if (b[0] < -3.8 && b[2] > 2.9 && b[4] > 1.6) {
					target = true;
				}
			}
			assertEquals(id.equals("tente_archer"), target, id + " the round training target stands in front at the left");
			String dp = j.get("decor").getAsString();
			JsonObject decor = json(dp.startsWith("/") ? dp : "/assets/medievalships/" + dp);
			assertTrue(decor.getAsJsonArray("blocks").size() >= 3, id + " furniture");
		}
	}

	@Test
	void modelsLoadStaticWithDetailAndGlow() throws Exception {
		for (String id : IDS) {
			String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
			try (InputStream in = MerchantModelsM5Test.class.getResourceAsStream(path)) {
				assertNotNull(in, path);
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000 && m.quadCount() < 950 * 6, id + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), id + " is static");
				assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
			}
			JsonObject model = json(path);
			JsonArray els = model.getAsJsonArray("elements");
			assertTrue(els.size() <= 900, id + " cubes " + els.size());
			int glow = 0, target = 0, staffs = 0, bows = 0;
			for (JsonElement el : els) {
				String n = el.getAsJsonObject().get("name").getAsString();
				if (n.startsWith("glow")) {
					glow++;
				}
				if (n.startsWith("target_")) {
					target++;
				}
				if (n.startsWith("glow_staff_")) {
					staffs++;
				}
				if (n.startsWith("wall_bow_")) {
					bows++;
				}
			}
			if (id.equals("tente_archer")) {
				assertTrue(target >= 15, "the target: face, back, rim, easel " + target);
				assertTrue(bows >= 40, "recurve bows on the back wall " + bows);
				assertTrue(glow >= 2, id + " lit lanterns " + glow);
			} else {
				assertTrue(staffs >= 12, "four staffs with crystal heads " + staffs);
				assertTrue(glow >= 40, id + " lit crystals, orb and potions " + glow);
			}
			assertNotNull(MerchantModelsM5Test.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
			assertNotNull(MerchantModelsM5Test.class.getResource("/assets/medievalships/textures/entity/" + id + ".png"), id + " atlas");
		}
	}
}
