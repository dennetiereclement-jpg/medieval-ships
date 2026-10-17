package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

class BbModelTest {
	private static final Path MODEL = Path.of("src/main/resources/assets/medievalships/models/entity/galley.bbmodel");

	private static BbModel load() throws Exception {
		try (Reader r = Files.newBufferedReader(MODEL, StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void requiredBonesAndAnimationsExist() throws Exception {
		BbModel model = load();
		for (String bone : new String[] {"sail", "yard", "rudder_p", "rudder_s", "flag", "oar_l1", "oar_r8"}) {
			assertNotNull(model.bonesByName.get(bone), bone);
		}
		for (String a : new String[] {"row", "sail_wind", "sail_furl", "steer", "flag_wave", "streamer_wave"}) {
			assertNotNull(model.animations.get(a), a);
		}
		assertTrue(model.quadCount() > 1000);
	}

	/** Same geometry as the Python reference renderer (tools/preview.py) for an animated pose. */
	@Test
	void matchesPythonReference() throws Exception {
		BbModel model = load();
		JsonObject ref;
		try (Reader r = new InputStreamReader(BbModelTest.class.getResourceAsStream("/reference_quads.json"), StandardCharsets.UTF_8)) {
			ref = JsonParser.parseReader(r).getAsJsonObject();
		}
		BbModel.Pose pose = model.newPose();
		for (Map.Entry<String, JsonElement> e : ref.getAsJsonObject("anim").entrySet()) {
			model.apply(pose, e.getKey(), e.getValue().getAsFloat(), 1f);
		}
		List<float[]> java = new ArrayList<>();
		model.render(pose, (p, uv, n, glow) -> java.add(concat(p, uv)));
		List<float[]> python = new ArrayList<>();
		for (JsonElement q : ref.getAsJsonArray("quads")) {
			JsonArray a = q.getAsJsonArray();
			float[] v = new float[20];
			for (int i = 0; i < 12; i++) {
				v[i] = a.get(0).getAsJsonArray().get(i).getAsFloat();
			}
			for (int i = 0; i < 8; i++) {
				v[12 + i] = a.get(1).getAsJsonArray().get(i).getAsFloat();
			}
			python.add(v);
		}
		assertEquals(python.size(), java.size());
		// greedy matching with tolerance (positions in blocks, uv normalised)
		boolean[] used = new boolean[python.size()];
		int unmatched = 0;
		for (float[] j : java) {
			boolean found = false;
			for (int i = 0; i < python.size() && !found; i++) {
				if (!used[i] && close(j, python.get(i))) {
					used[i] = true;
					found = true;
				}
			}
			if (!found) {
				unmatched++;
			}
		}
		assertEquals(0, unmatched);
	}

	private static float[] concat(float[] p, float[] uv) {
		float[] v = new float[20];
		System.arraycopy(p, 0, v, 0, 12);
		System.arraycopy(uv, 0, v, 12, 8);
		return v;
	}

	private static boolean close(float[] a, float[] b) {
		for (int i = 0; i < 20; i++) {
			if (Math.abs(a[i] - b[i]) > (i < 12 ? 2e-3f : 1e-4f)) {
				return false;
			}
		}
		return true;
	}

	@Test
	void furlCollapsesTheSail() throws Exception {
		BbModel model = load();
		float[] extent = new float[2];
		for (float furl : new float[] {0f, 1f}) {
			BbModel.Pose pose = model.newPose();
			model.apply(pose, "sail_furl", furl, 1f);
			float[] minMax = {Float.MAX_VALUE, -Float.MAX_VALUE};
			model.render(pose, (p, uv, n, glow) -> {
				// the sail texture region starts at v = 160/256
				if (uv[1] >= 160f / 256 - 1e-4) {
					for (int k = 0; k < 4; k++) {
						minMax[0] = Math.min(minMax[0], p[k * 3 + 1]);
						minMax[1] = Math.max(minMax[1], p[k * 3 + 1]);
					}
				}
			});
			extent[furl == 0 ? 0 : 1] = minMax[1] - minMax[0];
		}
		assertTrue(extent[0] > 9, "deployed sail height " + extent[0]);
		assertTrue(extent[1] < extent[0] * 0.6, "furled " + extent[1] + " vs " + extent[0]);
	}
}
