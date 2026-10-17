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

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * The warship model as read by the mod: bones, animations, two textures, same geometry as the Python reference
 * ({@code tools/reference_quads.py}; the preview only interpolates linearly, so catmullrom animations are left out).
 */
class WarshipModelTest {
	private static final Path MODEL = Path.of("src/main/resources/assets/medievalships/models/entity/warship.bbmodel");

	private static BbModel load() throws Exception {
		try (Reader r = Files.newBufferedReader(MODEL, StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void bonesAnimationsAndTextures() throws Exception {
		BbModel model = load();
		assertEquals(2, model.textureCount());
		for (String bone : new String[] {"helm_wheel", "rudder", "sail_main_course", "sail_main_topsail", "sail_main_topgallant",
				"sail_fore_course", "sail_fore_topsail", "sail_fore_topgallant", "sail_mizzen_topsail", "sail_mizzen", "sail_sprit", "jib",
				"flag_main", "flag_fore", "flag_mizzen", "flag_stern", "flag_stern_tip", "cannon_l1", "cannon_l29", "cannon_r1", "cannon_r29",
				"cabin", "stern"}) {
			assertNotNull(model.bonesByName.get(bone), bone);
		}
		for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave"}) {
			assertNotNull(model.animations.get(anim), anim);
		}
		// every face of the flag texture uses only texture #1, the others texture #0
		int[] counts = new int[2];
		BbModel.Pose pose = model.newPose();
		for (int t = 0; t < 2; t++) {
			int tex = t;
			model.render(pose, t, (p, uv, n, glow) -> {
				counts[tex]++;
				for (float f : uv) {
					assertTrue(f >= -1e-4 && f <= 1 + 1e-4, "uv out of range");
				}
			});
		}
		assertTrue(counts[1] > 0 && counts[0] > 5000);
		assertTrue(model.bonesByName.get("cannon_l30") == null, "exactly 29 guns per side");
		int[] all = {0};
		model.render(pose, (p, uv, n, glow) -> all[0]++);
		assertEquals(counts[0] + counts[1], all[0]);
	}

	@Test
	void matchesPythonReference() throws Exception {
		BbModel model = load();
		JsonObject ref;
		try (Reader r = new InputStreamReader(WarshipModelTest.class.getResourceAsStream("/warship_reference_quads.json"),
				StandardCharsets.UTF_8)) {
			ref = JsonParser.parseReader(r).getAsJsonObject();
		}
		BbModel.Pose pose = model.newPose();
		for (Map.Entry<String, JsonElement> e : ref.getAsJsonObject("anim").entrySet()) {
			model.apply(pose, e.getKey(), e.getValue().getAsFloat(), 1f);
		}
		List<float[]> java = new ArrayList<>();
		for (int t = 0; t < 2; t++) {
			int tex = t;
			model.render(pose, t, (p, uv, n, glow) -> java.add(concat(p, uv, tex)));
		}
		List<float[]> python = new ArrayList<>();
		for (JsonElement q : ref.getAsJsonArray("quads")) {
			JsonArray a = q.getAsJsonArray();
			float[] v = new float[21];
			for (int i = 0; i < 12; i++) {
				v[i] = a.get(0).getAsJsonArray().get(i).getAsFloat();
			}
			for (int i = 0; i < 8; i++) {
				v[12 + i] = a.get(1).getAsJsonArray().get(i).getAsFloat();
			}
			v[20] = a.get(3).getAsInt();
			python.add(v);
		}
		assertEquals(python.size(), java.size());
		// bucket by rounded first corner to keep the matching fast
		Map<Long, List<Integer>> buckets = new java.util.HashMap<>();
		for (int i = 0; i < python.size(); i++) {
			buckets.computeIfAbsent(key(python.get(i)), k -> new ArrayList<>()).add(i);
		}
		boolean[] used = new boolean[python.size()];
		int unmatched = 0;
		for (float[] j : java) {
			boolean found = false;
			for (long k : neighbours(j)) {
				for (int i : buckets.getOrDefault(k, List.of())) {
					if (!used[i] && close(j, python.get(i))) {
						used[i] = true;
						found = true;
						break;
					}
				}
				if (found) {
					break;
				}
			}
			if (!found) {
				unmatched++;
			}
		}
		assertEquals(0, unmatched);
	}

	private static long key(float[] v) {
		return key(Math.round(v[0] * 10), Math.round(v[1] * 10), Math.round(v[2] * 10));
	}

	private static long key(long x, long y, long z) {
		return ((x + 100000) << 40) ^ ((y + 100000) << 20) ^ (z + 100000);
	}

	private static long[] neighbours(float[] v) {
		long x = Math.round(v[0] * 10), y = Math.round(v[1] * 10), z = Math.round(v[2] * 10);
		long[] out = new long[27];
		int n = 0;
		for (int dx = -1; dx <= 1; dx++) {
			for (int dy = -1; dy <= 1; dy++) {
				for (int dz = -1; dz <= 1; dz++) {
					out[n++] = key(x + dx, y + dy, z + dz);
				}
			}
		}
		return out;
	}

	private static float[] concat(float[] p, float[] uv, int tex) {
		float[] v = new float[21];
		System.arraycopy(p, 0, v, 0, 12);
		System.arraycopy(uv, 0, v, 12, 8);
		v[20] = tex;
		return v;
	}

	private static boolean close(float[] a, float[] b) {
		for (int i = 0; i < 21; i++) {
			if (Math.abs(a[i] - b[i]) > (i < 12 ? 2e-3f : 1e-4f)) {
				return false;
			}
		}
		return true;
	}
}
