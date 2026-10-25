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
 * Models of the ships added after the warship, as read by the mod: animated bones, animations, and the same
 * geometry as the Python reference ({@code tools/reference_quads.py}, written next to each model test resource).
 */
class NewShipModelsTest {
	/** Model name, its animated bones and its animations. */
	private record Expected(String name, String[] bones, String[] animations) {
	}

	private static final List<Expected> MODELS = List.of(
			new Expected("medieval_galley",
					new String[] {"oar_l1", "oar_l12", "oar_r1", "oar_r12", "sail", "rudder", "flag", "flag_tip", "dragon_bow_head",
							"dragon_tail", "shields"},
					new String[] {"row", "sail_wind", "sail_furl", "steer", "flag_wave"}),
			new Expected("steam_paddleboat",
					new String[] {"paddle_wheel", "paddle_wheel_port", "helm_wheel", "rudder", "flag", "flag_tip", "funnels", "paddle_box", "guns"},
					new String[] {"paddle", "steer", "flag_wave"}),
			new Expected("elven_sailboat",
					new String[] {"sail_main", "sail_jib", "sail_top", "helm_wheel", "rudder", "flag", "flag_tip", "lantern_prow", "lantern_stern",
							"lantern_0", "lantern_3"},
					new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway"}),
			new Expected("steampunk_airship",
					new String[] {"propeller", "fin_top", "fin_port", "fin_starboard", "helm_wheel", "balloon", "net", "tail", "gondola", "engine",
							"suspension"},
					new String[] {"propeller", "steer", "elevator"}),
			new Expected("sky_leviathan",
					new String[] {"helm_wheel", "rudder", "fin_dorsal", "fin_lower", "fin_side_p", "fin_side_s", "fin_keel", "flag", "flag_tip",
							"tower_gear_0", "engine_gear_0", "engine_piston_0", "engine_boiler", "swag_p0", "black_sail_p0", "door_0_a", "door_1",
							"balloon", "hoops", "hull", "rooms", "furniture", "fittings"},
					new String[] {"steer", "elevator", "flag_wave", "engine", "lantern_sway", "streamer_wave", "door_0", "door_1", "door_11"}));

	private static BbModel load(String name) throws Exception {
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/" + name + ".bbmodel"),
				StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void bonesAndAnimations() throws Exception {
		for (Expected e : MODELS) {
			BbModel model = load(e.name());
			for (String bone : e.bones()) {
				assertNotNull(model.bonesByName.get(bone), e.name() + " bone " + bone);
			}
			for (String anim : e.animations()) {
				assertNotNull(model.animations.get(anim), e.name() + " animation " + anim);
			}
			int[] all = {0};
			model.render(model.newPose(), (p, uv, n, glow) -> {
				all[0]++;
				for (float f : uv) {
					assertTrue(f >= -1e-4 && f <= 1 + 1e-4, "uv out of range");
				}
			});
			assertTrue(all[0] > 500, e.name() + ": " + all[0] + " faces");
		}
	}

	@Test
	void matchesPythonReference() throws Exception {
		for (Expected e : MODELS) {
			BbModel model = load(e.name());
			JsonObject ref;
			try (Reader r = new InputStreamReader(NewShipModelsTest.class.getResourceAsStream("/" + e.name() + "_reference_quads.json"),
					StandardCharsets.UTF_8)) {
				ref = JsonParser.parseReader(r).getAsJsonObject();
			}
			BbModel.Pose pose = model.newPose();
			for (Map.Entry<String, JsonElement> a : ref.getAsJsonObject("anim").entrySet()) {
				model.apply(pose, a.getKey(), a.getValue().getAsFloat(), 1f);
			}
			List<float[]> java = new ArrayList<>();
			for (int t = 0; t < model.textureCount(); t++) {
				int tex = t;
				model.render(pose, model.textureCount() > 1 ? t : -1, (p, uv, n, glow) -> java.add(concat(p, uv, tex)));
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
			assertEquals(python.size(), java.size(), e.name());
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
			assertEquals(0, unmatched, e.name());
		}
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
