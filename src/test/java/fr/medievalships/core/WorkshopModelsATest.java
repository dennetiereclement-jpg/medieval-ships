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

/** The four workshops modelled by tools/workshops (agent A): their model loads, their JSON is complete and sane. */
public class WorkshopModelsATest {
	private static final List<String> IDS = List.of("workshop_blacksmith", "workshop_leatherworker", "workshop_tailor", "workshop_engineer");
	private static final Set<String> PARTICLES = Set.of("flame", "small_flame", "smoke", "campfire_smoke", "enchant", "witch", "portal",
			"end_rod", "glow", "electric_spark");

	private static JsonObject json(String id) throws Exception {
		try (InputStream in = WorkshopModelsATest.class.getResourceAsStream("/assets/medievalships/workshops/" + id + ".json")) {
			assertNotNull(in, id + ".json");
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
	void modelsLoadWithADetailBoneAndALitPart() throws Exception {
		for (String id : IDS) {
			JsonObject j = json(id);
			assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
			assertEquals("textures/entity/workshops_a.png", j.get("texture").getAsString());
			assertNotNull(WorkshopModelsATest.class.getResource("/assets/medievalships/" + j.get("texture").getAsString()), id + " texture");
			assertNotNull(WorkshopModelsATest.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
			try (InputStream in = WorkshopModelsATest.class.getResourceAsStream("/assets/medievalships/" + j.get("model").getAsString())) {
				assertNotNull(in, id + " model");
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 800 && m.quadCount() < 900 * 6, id + " faces " + m.quadCount());
				assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
				assertEquals(1, m.textureCount(), id);
			}
		}
	}

	@Test
	void extentToScaleCollidersInsideAndTheAnchorCovered() throws Exception {
		for (String id : IDS) {
			JsonObject j = json(id);
			double[] e = box(j.get("extent"));
			assertEquals(0.0, e[1], 1e-9, id + " stands on the ground");
			double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
			assertTrue(w > 4.0 && w < 7.0, id + " width " + w);
			assertTrue(d > 2.5 && d < 5.0, id + " depth " + d);
			assertTrue(h > 3.0 && h < 5.0, id + " height " + h);
			JsonArray cs = j.getAsJsonArray("colliders");
			assertTrue(cs.size() >= 8, id + " collision boxes " + cs.size());
			boolean anchor = false;
			for (JsonElement c : cs) {
				double[] b = box(c);
				assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " ordered box");
				assertTrue(b[0] >= e[0] - 1e-6 && b[3] <= e[3] + 1e-6 && b[2] >= e[2] - 1e-6 && b[5] <= e[5] + 1e-6 && b[1] >= -1e-6
						&& b[4] <= e[4] + 1e-6, id + " collider inside the extent");
				if (b[0] <= -0.5 && b[3] >= 0.5 && b[2] <= -0.5 && b[5] >= 0.5 && b[1] <= 0.0 && b[4] >= 0.95) {
					anchor = true;
				}
			}
			assertTrue(anchor, id + ": the anchor block sits inside a solid part (bench / forge / loom)");
			// the player stands in front of the work face: nothing solid right in front of the anchor
			for (JsonElement c : cs) {
				double[] b = box(c);
				boolean blocks = b[0] < 0.3 && b[3] > -0.3 && b[2] < 1.6 && b[5] > 0.9 && b[1] < 1.7;
				assertTrue(!blocks, id + " the work place in front of the anchor is free " + c);
			}
		}
	}

	@Test
	void particlesAreFewAndKnown() throws Exception {
		for (String id : IDS) {
			JsonArray ps = json(id).getAsJsonArray("particles");
			assertNotNull(ps, id + " particles");
			assertTrue(ps.size() <= 4, id);
			for (JsonElement p : ps) {
				JsonObject o = p.getAsJsonObject();
				assertTrue(PARTICLES.contains(o.get("type").getAsString()), id + " " + o);
				assertEquals(3, o.getAsJsonArray("pos").size());
				double chance = o.get("chance").getAsDouble();
				assertTrue(chance > 0 && chance <= 1, id + " chance");
			}
		}
		assertTrue(json("workshop_blacksmith").getAsJsonArray("particles").size() >= 2, "the forge fire smokes and flames");
	}
}
