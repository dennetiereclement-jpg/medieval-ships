package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The models of three workshops (cook, alchemist, enchanter: tools/workshops/generate_workshop_*.py): each JSON
 * (assets/medievalships/workshops/&lt;id&gt;.json) has its model, texture, extent, collision boxes and particles, and
 * its .bbmodel loads light, with a "detail" bone and lit (glow) elements.
 */
public class WorkshopModelsBTest {
	private static final double EPS = 1e-6;
	private static final List<String> IDS = List.of("workshop_cook", "workshop_alchemist", "workshop_enchanter");
	private static final Set<String> PARTICLES = Set.of("flame", "small_flame", "smoke", "campfire_smoke", "enchant", "witch", "portal",
			"end_rod", "glow");

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = WorkshopModelsBTest.class.getResourceAsStream(path)) {
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
	void jsonHasExtentCollidersAndParticles() throws Exception {
		for (String id : IDS) {
			JsonObject j = json("/assets/medievalships/workshops/" + id + ".json");
			assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
			assertEquals("textures/entity/workshops_b.png", j.get("texture").getAsString());
			double[] e = box(j.get("extent"));
			assertEquals(0.0, e[1], EPS, id + " stands on the ground");
			double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
			assertTrue(w > 4.0 && w < 9.0 && d > 2.5 && d < 7.0 && h > 3.0 && h < 6.0, id + " size " + w + " x " + h + " x " + d);
			JsonArray cs = j.getAsJsonArray("colliders");
			assertTrue(cs.size() >= 8, id + " collision boxes " + cs.size());
			boolean anchor = false;
			for (JsonElement c : cs) {
				double[] b = box(c);
				assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
				assertTrue(b[0] >= e[0] - EPS && b[3] <= e[3] + EPS && b[2] >= e[2] - EPS && b[5] <= e[5] + EPS && b[1] >= -EPS
						&& b[4] <= e[4] + EPS, id + " inside the extent " + c);
				anchor |= b[0] <= 0 && b[3] >= 0 && b[2] <= 0 && b[5] >= 0 && b[1] <= 0.25 && b[4] >= 0.25;
			}
			assertTrue(anchor, id + ": the anchor block is inside the bench / hearth / platform");
			JsonArray ps = j.getAsJsonArray("particles");
			assertTrue(ps.size() >= 1 && ps.size() <= 4, id + " particles " + ps.size());
			for (JsonElement p : ps) {
				JsonObject o = p.getAsJsonObject();
				assertTrue(PARTICLES.contains(o.get("type").getAsString()), id + " particle " + o);
				assertEquals(3, o.getAsJsonArray("pos").size());
				double chance = o.get("chance").getAsDouble();
				assertTrue(chance > 0 && chance <= 1, id + " chance " + chance);
			}
		}
	}

	@Test
	void modelsLoadLightWithDetailAndGlow() throws Exception {
		for (String id : IDS) {
			String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
			try (InputStream in = WorkshopModelsBTest.class.getResourceAsStream(path)) {
				assertNotNull(in, path);
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				int max = id.equals("workshop_enchanter") ? 1500 : 900;
				assertTrue(m.quadCount() > 200 && m.quadCount() < max * 6, id + " faces " + m.quadCount());
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
			assertTrue(glow >= 3, id + " lit elements " + glow);
			assertNotNull(WorkshopModelsBTest.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
		}
		assertNotNull(WorkshopModelsBTest.class.getResource("/assets/medievalships/textures/entity/workshops_b.png"));
	}
}
