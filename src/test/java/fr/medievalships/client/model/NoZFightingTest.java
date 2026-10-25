package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * No two faces of a ship model lie in the same plane while overlapping: such faces flicker in game
 * (z-fighting). The renderer draws both sides of every face, so faces of either direction count.
 * The generators separate them on export ({@code tools/zfight.py}); this checks the models as the mod reads them.
 */
class NoZFightingTest {
	private static final String[] MODELS = {"galley", "galleon", "warship", "medieval_galley", "steam_paddleboat", "elven_sailboat", "steampunk_airship", "old_corsair"};
	private static final float TOL = 0.005f;

	private record Face(float[] p, float[] n, float d) {
	}

	@Test
	void noCoplanarOverlappingFaces() throws Exception {
		for (String name : MODELS) {
			BbModel model;
			try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/" + name + ".bbmodel"),
					StandardCharsets.UTF_8)) {
				model = new BbModel(r);
			}
			Map<Long, List<Face>> buckets = new HashMap<>();
			model.render(model.newPose(), (p, uv, n, glow) -> {
				float[] c = n.clone();
				float sgn = 1;
				for (float x : c) {
					if (Math.abs(x) > 1e-3f) {
						sgn = Math.signum(x);
						break;
					}
				}
				for (int i = 0; i < 3; i++) {
					c[i] *= sgn;
				}
				float d = c[0] * p[0] + c[1] * p[1] + c[2] * p[2];
				long key = ((long) Math.round(c[0] * 40) + 100) * 1_000_000L + (Math.round(c[1] * 40) + 100) * 1000L + Math.round(c[2] * 40) + 100;
				buckets.computeIfAbsent(key, k -> new ArrayList<>()).add(new Face(p.clone(), c, d));
			});
			int pairs = 0;
			String first = null;
			for (List<Face> faces : buckets.values()) {
				faces.sort((a, b) -> Float.compare(a.d, b.d));
				for (int i = 0; i < faces.size(); i++) {
					Face f = faces.get(i);
					for (int j = i + 1; j < faces.size(); j++) {
						Face g = faces.get(j);
						if (g.d - f.d > TOL) {
							break;
						}
						if (Math.abs(dot(f.n, g.n)) < 0.9995f || !overlap(f.p, g.p)) {
							continue;
						}
						pairs++;
						if (first == null) {
							first = String.format("(%.2f %.2f %.2f)", f.p[0], f.p[1], f.p[2]);
						}
					}
				}
			}
			assertEquals(0, pairs, name + ": coplanar overlapping faces, first near " + first);
		}
	}

	/** Every cube and every bone has its own uuid (Blockbench and the animations find them by it). */
	@Test
	void uniqueIds() throws Exception {
		for (String name : MODELS) {
			JsonObject m;
			try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/" + name + ".bbmodel"),
					StandardCharsets.UTF_8)) {
				m = JsonParser.parseReader(r).getAsJsonObject();
			}
			java.util.Set<String> seen = new java.util.HashSet<>();
			int dup = 0;
			for (JsonElement e : m.getAsJsonArray("elements")) {
				dup += seen.add(e.getAsJsonObject().get("uuid").getAsString()) ? 0 : 1;
			}
			java.util.ArrayDeque<JsonObject> groups = new java.util.ArrayDeque<>();
			m.getAsJsonArray("outliner").forEach(g -> groups.add(g.getAsJsonObject()));
			while (!groups.isEmpty()) {
				JsonObject g = groups.poll();
				dup += seen.add(g.get("uuid").getAsString()) ? 0 : 1;
				for (JsonElement c : g.getAsJsonArray("children")) {
					if (c.isJsonObject()) {
						groups.add(c.getAsJsonObject());
					}
				}
			}
			assertEquals(0, dup, name + ": duplicate uuids");
		}
	}

	private static float dot(float[] a, float[] b) {
		return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
	}

	/** Separating axis test on the two coplanar quads, using their edges as axes; a sliver (< 0.02) does not count. */
	private static boolean overlap(float[] a, float[] b) {
		for (float[] q : new float[][] {a, b}) {
			for (int e = 0; e < 2; e++) {
				float[] ax = {q[3 * (e + 1)] - q[3 * e], q[3 * (e + 1) + 1] - q[3 * e + 1], q[3 * (e + 1) + 2] - q[3 * e + 2]};
				float len = (float) Math.sqrt(dot(ax, ax));
				if (len < 1e-6f) {
					continue;
				}
				for (int i = 0; i < 3; i++) {
					ax[i] /= len;
				}
				float amin = Float.MAX_VALUE, amax = -Float.MAX_VALUE, bmin = Float.MAX_VALUE, bmax = -Float.MAX_VALUE;
				for (int k = 0; k < 4; k++) {
					float pa = a[3 * k] * ax[0] + a[3 * k + 1] * ax[1] + a[3 * k + 2] * ax[2];
					float pb = b[3 * k] * ax[0] + b[3 * k + 1] * ax[1] + b[3 * k + 2] * ax[2];
					amin = Math.min(amin, pa);
					amax = Math.max(amax, pa);
					bmin = Math.min(bmin, pb);
					bmax = Math.max(bmax, pb);
				}
				if (amin > bmax - 0.02f || bmin > amax - 0.02f) {
					return false;
				}
			}
		}
		return true;
	}
}
