package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Animations of the Sky Leviathan as the mod plays them (phase 3): the engine (gears, pistons, the boiler shaking)
 * moves with its phase and only then, the rudder / elevator fins follow the helm / the climb, the sails, swags,
 * banners and fins move in the wind; only small bones are animated (the rest is drawn from the static cache).
 */
class LeviathanAnimationTest {
	private static final Path MODEL = Path.of("src/main/resources/assets/medievalships/models/entity/sky_leviathan.bbmodel");
	private static BbModel model;
	private static JsonObject json;

	@BeforeAll
	static void load() throws Exception {
		try (Reader r = Files.newBufferedReader(MODEL, StandardCharsets.UTF_8)) {
			model = new BbModel(r);
		}
		try (Reader r = Files.newBufferedReader(MODEL, StandardCharsets.UTF_8)) {
			json = JsonParser.parseReader(r).getAsJsonObject();
		}
	}

	/** Quads of the model (positions only) in a pose made of the given animations at the given times. */
	private static List<float[]> quads(Object... animTimes) {
		BbModel.Pose pose = model.newPose();
		for (int i = 0; i < animTimes.length; i += 2) {
			model.apply(pose, (String) animTimes[i], ((Number) animTimes[i + 1]).floatValue(), 1f);
		}
		List<float[]> out = new ArrayList<>();
		model.render(pose, (p, uv, n, glow) -> out.add(p.clone()));
		return out;
	}

	/** Number of quads that moved more than eps between two poses. */
	private static int moved(List<float[]> a, List<float[]> b, float eps) {
		assertEquals(a.size(), b.size());
		int n = 0;
		for (int i = 0; i < a.size(); i++) {
			for (int k = 0; k < 12; k++) {
				if (Math.abs(a.get(i)[k] - b.get(i)[k]) > eps) {
					n++;
					break;
				}
			}
		}
		return n;
	}

	private static float maxMove(List<float[]> a, List<float[]> b) {
		float m = 0;
		for (int i = 0; i < a.size(); i++) {
			for (int k = 0; k < 12; k++) {
				m = Math.max(m, Math.abs(a.get(i)[k] - b.get(i)[k]));
			}
		}
		return m;
	}

	@Test
	void animationsAndBones() {
		for (String a : new String[] {"engine", "steer", "elevator", "flag_wave", "lantern_sway", "streamer_wave"}) {
			assertNotNull(model.animations.get(a), "animation " + a);
		}
		Map<String, String[]> tracks = Map.of(
				"engine", new String[] {"tower_gear_0", "tower_gear_1", "engine_gear_0", "engine_gear_1", "engine_gear_4", "engine_piston_0",
						"engine_piston_1", "engine_boiler"},
				"steer", new String[] {"helm_wheel", "rudder", "fin_dorsal", "fin_lower"},
				"elevator", new String[] {"fin_side_p", "fin_side_s"},
				"flag_wave", new String[] {"flag", "flag_tip"},
				"streamer_wave", new String[] {"pennants_p0", "pennants_s4", "black_sail_p0", "black_sail_s1", "swag_p0", "swag_s2", "fin_dorsal",
						"fin_upper_p", "fin_upper_s", "fin_side_p", "fin_side_s", "fin_lower"});
		for (Map.Entry<String, String[]> e : tracks.entrySet()) {
			BbModel.Animation anim = model.animations.get(e.getKey());
			for (String bone : e.getValue()) {
				assertNotNull(model.bonesByName.get(bone), "bone " + bone);
				assertTrue(anim.tracks.containsKey(bone), e.getKey() + " moves " + bone);
			}
		}
	}

	@Test
	void onlySmallBonesAreAnimated() {
		// the big parts are drawn from the static cache
		for (String bone : new String[] {"sky_leviathan", "balloon", "hoops", "hull", "decks", "rooms", "furniture", "fittings", "tower", "suspension",
				"rigging", "top_deck", "beakhead", "nose", "tail", "detail"}) {
			assertFalse(model.bonesByName.get(bone).animated, bone + " is static");
		}
		int[] all = {0};
		model.render(model.newPose(), (p, uv, n, glow) -> all[0]++);
		int animated = 0, outside = 0;
		for (BbModel.Bone b : model.bones) {
			if (b.animated) {
				animated += b.quads.size();
				if (!under(b, "fittings") && !b.name.startsWith("door_")) {
					outside += b.quads.size();
				}
			}
		}
		// the engine room (boiler, engine, gears: children of the fittings) is only drawn within 48 blocks
		assertTrue(animated < all[0] * 0.2, "animated faces " + animated + " of " + all[0]);
		assertTrue(outside < all[0] * 0.14, "animated faces drawn from afar " + outside + " of " + all[0]);
	}

	private static boolean under(BbModel.Bone b, String name) {
		for (BbModel.Bone p = b; p != null; p = p.parent) {
			if (p.name.equals(name)) {
				return true;
			}
		}
		return false;
	}

	@Test
	void engineTurnsWithItsPhaseOnly() {
		List<float[]> rest = quads("engine", 0f);
		List<float[]> later = quads("engine", 0.5f);
		int n = moved(rest, later, 1e-3f);
		assertTrue(n > 200, "gears, pistons, boiler move: " + n);
		// the same phase gives the same picture (a parked airship's engine phase does not change: still)
		assertEquals(0, moved(rest, quads("engine", 0f), 0f));
		// one turn of the flywheel later, everything is back in place (the loop is seamless)
		assertTrue(maxMove(rest, quads("engine", 2.0f)) < 2e-3f);
		// the boiler shakes only a little
		BbModel.Pose pose = model.newPose();
		float shake = 0;
		for (float t = 0; t < 2f; t += 0.025f) {
			pose.reset();
			model.apply(pose, "engine", t, 1f);
			int b = model.bonesByName.get("engine_boiler").index;
			for (int k = 0; k < 3; k++) {
				shake = Math.max(shake, Math.abs(pose.pos[b][k]) / 16f);
			}
		}
		assertTrue(shake > 0.004f && shake < 0.03f, "boiler shake " + shake + " blocks");
	}

	/** The big gears on the sides of the tower turn in their own plane (about their axles, across the ship). */
	@Test
	void towerGearsTurnInTheirPlane() {
		List<float[]> a = quads("engine", 0f);
		List<float[]> b = quads("engine", 0.7f);
		int moving = 0;
		for (int i = 0; i < a.size(); i++) {
			float[] p = a.get(i), q = b.get(i);
			float cx = (p[0] + p[3] + p[6] + p[9]) / 4, cy = (p[1] + p[4] + p[7] + p[10]) / 4, cz = (p[2] + p[5] + p[8] + p[11]) / 4;
			// around the gear on either side of the tower: centre (+-1.9, 4.4, -1.5), radius 1.8, its pinion above
			if (Math.abs(Math.abs(cx) - 1.9f) > 0.5f || Math.hypot(cy - 5.0f, cz + 1.5f) > 3.2f) {
				continue;
			}
			boolean moved = false;
			for (int k = 0; k < 12; k++) {
				moved |= Math.abs(p[k] - q[k]) > 1e-3f;
			}
			if (moved) {
				moving++;
				for (int k = 0; k < 4; k++) {
					assertEquals(p[k * 3], q[k * 3], 2e-3f, "a tower gear face leaves its plane");
				}
			}
		}
		assertTrue(moving > 100, "tower gears and pinions turn: " + moving);
	}

	@Test
	void finsFollowHelmAndClimb() {
		List<float[]> centre = quads("steer", 1f, "elevator", 1f);
		int steer = moved(centre, quads("steer", 2f, "elevator", 1f), 0.05f);
		int climb = moved(centre, quads("steer", 1f, "elevator", 2f), 0.05f);
		assertTrue(steer > 100, "helm over: rudder fins and wheel move (" + steer + ")");
		assertTrue(climb > 100, "climbing: elevator fins move (" + climb + ")");
		// the deflection of a fin tip stays slight: a few blocks at most
		assertTrue(maxMove(centre, quads("steer", 2f, "elevator", 2f)) < 3.5f);
	}

	@Test
	void windMovesSlightly() {
		List<float[]> a = quads("streamer_wave", 0f);
		List<float[]> b = quads("streamer_wave", 1.1f);
		int n = moved(a, b, 0.01f);
		assertTrue(n > 300, "sails, swags, banners, fins move in the wind: " + n);
		// only slightly (the longest pennant strings, ten blocks long, swing by about a block at their far end)
		assertTrue(maxMove(a, b) < 1.5f, "but only slightly: " + maxMove(a, b));
		assertTrue(maxMove(a, quads("streamer_wave", 3f)) < 2e-3f, "seamless loop");
	}

	/** The sheets and slings of the black sails stay on the rail and the balloon (not in the swinging bones). */
	@Test
	void sailRopesStayPut() {
		Map<String, String> names = new HashMap<>();
		for (JsonElement e : json.getAsJsonArray("elements")) {
			JsonObject o = e.getAsJsonObject();
			names.put(o.get("uuid").getAsString(), o.get("name").getAsString());
		}
		List<String> inSails = new ArrayList<>();
		collect(json.getAsJsonArray("outliner"), false, names, inSails);
		assertTrue(inSails.stream().anyMatch(n -> n.startsWith("black_sail_")), "the sails' cloth");
		assertTrue(inSails.stream().noneMatch(n -> n.startsWith("sail_sheet") || n.startsWith("sail_sling")), "no rope in a sail bone");
	}

	private static void collect(com.google.gson.JsonArray children, boolean inSail, Map<String, String> names, List<String> out) {
		for (JsonElement c : children) {
			if (c.isJsonObject()) {
				JsonObject g = c.getAsJsonObject();
				boolean sail = inSail || g.get("name").getAsString().startsWith("black_sail_");
				collect(g.getAsJsonArray("children"), sail, names, out);
			} else if (inSail) {
				out.add(names.getOrDefault(c.getAsString(), ""));
			}
		}
	}
}
