package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The divine forge (1.34.0): its prop (descriptor, extra models, place among the props, the models' bones), its state
 * machine (at rest / active until an end tick, restored after a restart), and the animation (gears, flipbooks) and
 * effects' pace as functions of the time. The forge crafts nothing: no recipe, no interface.
 */
public class DivineForgeTest {
	private static final double EPS = 1e-9;
	private static final Path RESOURCES = Path.of("src/main/resources");
	private static final TentType F = TentTypes.FORGE_DIVINE;

	private static JsonObject json(String s) {
		return JsonParser.parseString(s).getAsJsonObject();
	}

	// ------------------------------------------------------------------ the prop

	@Test
	void aWorkshopOfItsOwnAmongTheProps() {
		assertEquals("forge_divine", F.id());
		assertTrue(F.isWorkshop() && F.isDivineForge(), "family of the workshops, the divine forge");
		assertFalse(TentTypes.WORKSHOPS.contains(F), "the eight classic workshops stay as they are");
		assertEquals(List.of(F), TentTypes.FORGES);
		assertTrue(TentTypes.PROPS.contains(F));
		assertSame(TentTypes.CANNON, TentTypes.PROPS.get(TentTypes.PROPS.size() - 1), "the artillery stays last");
		assertSame(F, TentTypes.PROPS.get(TentTypes.PROPS.size() - 2), "the forge just before the artillery");
		assertEquals("forge_divine", F.profession(), "its profession: the key of workshopCommands and of the use event");
		assertFalse(F.masculine(), "la forge : « posée »");
		assertEquals("e", F.agreement());
		assertEquals(TentType.MAX_LIGHT, F.light(), "light 15");
		for (String alias : new String[] {"forge_divine", "medievalships:forge_divine", " Forge ", "divine_forge"}) {
			assertSame(F, TentTypes.byId(alias), alias);
		}
		for (TentType t : TentTypes.PROPS) {
			assertEquals(t == F, t.isDivineForge(), t.id());
		}
		assertFalse(F.hasHazard() || F.hasTargets() || !F.seats().isEmpty(), "nothing else");
	}

	@Test
	void descriptorWithinTheAgreedEnvelope() throws Exception {
		Path file = RESOURCES.resolve("assets/medievalships/workshops/forge_divine.json");
		assertTrue(Files.isRegularFile(file), "workshops/forge_divine.json");
		TentType.Box e = F.extent();
		assertEquals(0.0, e.y0(), EPS, "stands on the ground");
		assertTrue(e.width() <= 13.0 + EPS && e.height() <= 10.0 + EPS && e.depth() <= 6.0 + EPS, "13 x 10 x 6 at most: " + e);
		assertTrue(e.width() >= 8 && e.height() >= 6, "a great forge: " + e);
		assertTrue(e.x0() <= 0 && e.x1() >= 0 && e.z0() <= 0 && e.z1() >= 0, "the anchor inside");
		assertFalse(F.colliders().isEmpty(), "collision boxes");
		for (TentType.Box c : F.colliders()) {
			assertTrue(c.x0() >= e.x0() - EPS && c.x1() <= e.x1() + EPS && c.y0() >= e.y0() - EPS && c.y1() <= e.y1() + EPS
					&& c.z0() >= e.z0() - EPS && c.z1() <= e.z1() + EPS, "collider inside the extent: " + c);
			assertTrue(c.width() > 0 && c.height() > 0 && c.depth() > 0, "a real box: " + c);
		}
		// the platform can be walked onto: whatever covers the front edge of the footprint is no higher than a step
		double front = 0;
		for (TentType.Box c : F.colliders()) {
			if (c.z1() >= e.z1() - 0.05 && c.y0() <= 0.01) {
				front = Math.max(front, c.y1());
			}
		}
		assertTrue(front <= 0.6 + EPS, "the front edge is a step (" + front + ")");
		// nothing solid hangs under the banners (x = +-5.6, z = 0.6, between y = 2 and y = 8)
		for (TentType.Box c : F.colliders()) {
			for (double x : new double[] {-5.6, 5.6}) {
				boolean under = c.x0() < x + 0.15 && c.x1() > x - 0.15 && c.z0() < 0.75 && c.z1() > 0.45 && c.y0() < 7.8 && c.y1() > 2.2;
				assertFalse(under, "a collider under the banner at x " + x + ": " + c);
			}
		}
		assertEquals(1, F.extraModels().size(), "the statue and decor model");
		TentType.ExtraModel deco = F.extraModels().get(0);
		assertEquals("models/entity/forge_divine_deco.bbmodel", deco.model());
		assertEquals("textures/entity/forge_divine_deco.png", deco.texture());
		assertEquals("models/entity/forge_divine.bbmodel", F.model());
		assertEquals("textures/entity/forge_divine.png", F.texture());
		// the turned extents stay the same size
		for (int q = 0; q < 4; q++) {
			TentType.Box r = F.extent(q);
			assertEquals(e.width() * e.depth(), r.width() * r.depth(), 1e-6, "quarter " + q);
		}
	}

	@Test
	void extraModelsParsedForAnyProp() {
		String base = "\"extent\": [-1, 0, -1, 1, 2, 1], \"texture\": \"textures/entity/x.png\"";
		TentType none = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + "}"));
		assertTrue(none.extraModels().isEmpty(), "absent: none");
		TentType two = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + ", \"extra_models\": [{\"model\": \"models/entity/a.bbmodel\","
				+ " \"texture\": \"textures/entity/a.png\"}, \"models/entity/b.bbmodel\", {\"texture\": \"x\"}, 3, {\"model\": \" \"}]}"));
		assertEquals(2, two.extraModels().size(), "the bad entries are skipped");
		assertEquals(new TentType.ExtraModel("models/entity/a.bbmodel", "textures/entity/a.png"), two.extraModels().get(0));
		assertEquals(new TentType.ExtraModel("models/entity/b.bbmodel", "textures/entity/x.png"), two.extraModels().get(1),
				"the prop's atlas by default");
		TentType odd = TentType.parse(TentType.TENTS, "t", "t", "T", json("{" + base + ", \"extra_models\": {\"model\": \"m\"}}"));
		assertTrue(odd.extraModels().isEmpty(), "not a list: none");
	}

	@Test
	void missingDescriptorFallsBack() {
		TentType t = TentType.loadOrDefault(TentType.WORKSHOPS, "forge_absente", "forge absente", "Missing Forge",
				"{\"extent\": [-6.5, 0, -3, 6.5, 10, 3], \"light\": 15}");
		assertEquals(13.0, t.extent().width(), EPS, "the fallback is used when the file is missing");
		assertEquals(15, t.light());
	}

	/** The bones the renderer expects, when the models are in the jar (they come from tools/forge/). */
	@Test
	void modelsFollowTheBoneContract() throws Exception {
		BbModel structure = load(F.model());
		Assumptions.assumeTrue(structure != null, "the structure model is not generated in this tree");
		Set<String> names = new HashSet<>();
		for (BbModel.Bone b : structure.bones) {
			names.add(b.name);
		}
		for (String p : new String[] {"fire_f", "flow_l_f", "flow_r_f"}) {
			for (int i = 0; i < ForgeAnimation.FRAMES; i++) {
				assertTrue(names.contains(p + i), "structure: bone " + p + i);
			}
		}
		assertTrue(names.stream().anyMatch(n -> n.startsWith("gear_a_") || n.startsWith("gear_b_")), "structure: gears");
		assertTrue(structure.animations.isEmpty(), "no Blockbench animation: the renderer moves the bones");
		BbModel deco = load(F.extraModels().get(0).model());
		Assumptions.assumeTrue(deco != null, "the decor model is not generated in this tree");
		Set<String> both = new HashSet<>(names);
		for (BbModel.Bone b : deco.bones) {
			both.add(b.name);
		}
		// in one model or the other
		assertTrue(both.stream().anyMatch(n -> n.startsWith("craft_")), "craft_* (seen while active)");
		assertTrue(both.stream().anyMatch(n -> n.startsWith("fx_spark_")), "spark points");
		assertTrue(both.stream().anyMatch(n -> n.startsWith("fx_holy_")), "holy light points");
		assertTrue(deco.animations.isEmpty());
		// the effect points are empty bones (their pivot is the point)
		for (BbModel m : new BbModel[] {structure, deco}) {
			for (BbModel.Bone b : m.bones) {
				if (b.name.startsWith("fx_spark_") || b.name.startsWith("fx_steam_") || b.name.startsWith("fx_ember_") || b.name.startsWith("fx_holy_")) {
					double[] o = b.originBlocks();
					TentType.Box e = F.extent();
					assertTrue(o[0] >= e.x0() - 1 && o[0] <= e.x1() + 1 && o[1] >= -0.5 && o[1] <= e.y1() + 1.5 && o[2] >= e.z0() - 1 && o[2] <= e.z1() + 1,
							b.name + " within the forge: " + java.util.Arrays.toString(o));
				}
			}
		}
	}

	@Test
	void gearAxisFollowsTheBonesRotation() {
		// a gear on the front (no rotation): its z axis is the model's +z; one turned 90 degrees about y (on a side wall)
		// turns about the model's x axis; a child of a turned bone inherits its parent's turn
		String json = "{\"resolution\": {\"width\": 16, \"height\": 16}, \"elements\": [], \"outliner\": ["
				+ "{\"name\": \"gear_a_0\", \"origin\": [0, 16, 0], \"children\": []},"
				+ "{\"name\": \"side\", \"origin\": [0, 0, 0], \"rotation\": [0, 90, 0], \"children\": ["
				+ "{\"name\": \"gear_b_0\", \"origin\": [-16, 8, 0], \"children\": []}]}]}";
		BbModel m = new BbModel(new java.io.StringReader(json));
		double[] front = m.bonesByName.get("gear_a_0").axisBlocks(0, 0, 1);
		assertEquals(0, front[0], 1e-6);
		assertEquals(0, front[1], 1e-6);
		assertEquals(1, front[2], 1e-6);
		double[] side = m.bonesByName.get("gear_b_0").axisBlocks(0, 0, 1);
		assertEquals(1.0, Math.abs(side[0]), 1e-6, "turned to the x axis: " + java.util.Arrays.toString(side));
		assertEquals(0, side[1], 1e-6);
		assertEquals(0, side[2], 1e-6);
		double[] o = m.bonesByName.get("gear_b_0").originBlocks();
		assertEquals(1.0, o[0], 1e-9, "pivot x = -bbX / 16");
		assertEquals(0.5, o[1], 1e-9);
	}

	private static BbModel load(String path) throws Exception {
		try (InputStream in = DivineForgeTest.class.getResourceAsStream("/assets/medievalships/" + path)) {
			if (in == null) {
				return null;
			}
			try (Reader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return new BbModel(r);
			}
		}
	}

	// ------------------------------------------------------------------ the state machine

	@Test
	void activityStateMachine() {
		ForgeActivity a = new ForgeActivity();
		assertFalse(a.active());
		assertEquals(0, a.progress(100), EPS);
		assertEquals(0, a.remaining(100));
		assertFalse(a.complete(), "nothing to end at rest");
		assertTrue(a.start(1000, 200));
		assertTrue(a.active());
		assertFalse(a.start(1050, 100), "one activity at a time");
		assertEquals(1200, a.end(), "the second request changed nothing");
		assertEquals(0.25, a.progress(1050), EPS);
		assertEquals(150, a.remaining(1050));
		assertEquals(200, a.total());
		assertFalse(a.due(1199));
		assertTrue(a.due(1200));
		assertTrue(a.active(), "still active until the server ends it");
		assertEquals(1.0, a.progress(5000), EPS);
		assertEquals(0.0, a.progress(10), EPS, "a clock before the start");
		assertTrue(a.complete());
		assertFalse(a.active());
		assertEquals(0, a.total());
		assertTrue(a.start(1300, 600), "free again");
		a.endAt(1310);
		assertTrue(a.due(1310), "stopped by an administrator");
		a.endAt(1000);
		assertEquals(1300, a.end(), "never before its start");
		a.reset();
		assertTrue(a.start(0, 999_999));
		assertEquals(ForgeActivity.MAX_TICKS, a.end(), "one hour at most");
		a.reset();
		assertTrue(a.start(0, -5));
		assertEquals(1, a.end(), "at least one tick");
	}

	@Test
	void activityRestoredAfterARestart() {
		ForgeActivity a = new ForgeActivity();
		a.restore(true, 500, 900);
		assertTrue(a.active());
		assertEquals(400, a.remaining(500));
		assertEquals(500, a.start());
		a.restore(true, 900, 900);
		assertFalse(a.active(), "an end not after the start: at rest");
		a.restore(false, 500, 900);
		assertFalse(a.active());
		assertEquals(0, a.end());
	}

	// ------------------------------------------------------------------ the animation

	@Test
	void flipbookImagesCycle() {
		assertEquals(0, ForgeAnimation.frame(0.0, 4));
		assertEquals(0, ForgeAnimation.frame(0.99, 4));
		assertEquals(1, ForgeAnimation.frame(1.0, 4));
		assertEquals(3, ForgeAnimation.frame(3.5, 4));
		assertEquals(0, ForgeAnimation.frame(4.0, 4));
		assertEquals(3, ForgeAnimation.frame(-0.5, 4), "negative phases cycle too");
		assertEquals(0, ForgeAnimation.frame(Double.NaN, 4));
		assertEquals(0, ForgeAnimation.frame(7.3, 1));
		// at rest the fire shows each of its four images within a second, in order
		ForgeAnimation.Track t = new ForgeAnimation.Track();
		t.update(0, false);
		List<Integer> seen = new ArrayList<>();
		for (int tick = 1; tick <= 20; tick++) {
			t.update(tick, false);
			int f = t.fireFrame(4);
			if (seen.isEmpty() || seen.get(seen.size() - 1) != f) {
				seen.add(f);
			}
		}
		assertTrue(seen.size() >= 4, "four images or more in a second: " + seen);
		for (int i = 1; i < seen.size(); i++) {
			assertEquals((seen.get(i - 1) + 1) % 4, (int) seen.get(i), "one image after the other: " + seen);
		}
		int left = t.flowFrame(true, 4), right = t.flowFrame(false, 4);
		assertTrue(left >= 0 && left < 4 && right >= 0 && right < 4);
	}

	@Test
	void gearsTurnSlowlyAtRestFasterWhileActive() {
		ForgeAnimation.Track rest = new ForgeAnimation.Track();
		rest.update(0, false);
		for (int tick = 1; tick <= 40; tick++) {
			rest.update(tick, false);
		}
		assertEquals(ForgeAnimation.GEAR_IDLE_DPS * 2.0, rest.gear, 1e-6, "two seconds at rest");
		assertEquals(0.0, rest.intensity, EPS);
		ForgeAnimation.Track craft = new ForgeAnimation.Track();
		craft.update(0, true);
		assertEquals(1.0, craft.intensity, EPS, "a forge first seen active starts at full pace");
		for (int tick = 1; tick <= 40; tick++) {
			craft.update(tick, true);
		}
		assertEquals(ForgeAnimation.GEAR_CRAFT_DPS * 2.0, craft.gear, 1e-6);
		assertTrue(ForgeAnimation.GEAR_CRAFT_DPS > 3 * ForgeAnimation.GEAR_IDLE_DPS, "clearly faster while active");
		assertTrue(ForgeAnimation.FIRE_CRAFT_FPS > ForgeAnimation.FIRE_IDLE_FPS && ForgeAnimation.FLOW_CRAFT_FPS > ForgeAnimation.FLOW_IDLE_FPS);
		// gear_a clockwise seen from the front (negative about +z), gear_b the other way
		assertEquals(-30.0, ForgeAnimation.gearAngle(30.0, true), EPS);
		assertEquals(30.0, ForgeAnimation.gearAngle(30.0, false), EPS);
	}

	@Test
	void theChangeOfPaceIsEasedWithoutAJump() {
		ForgeAnimation.Track t = new ForgeAnimation.Track();
		t.update(0, false);
		double lastAngle = 0, lastStep = 0;
		for (int frame = 1; frame <= 400; frame++) {
			double time = frame * 0.5; // two frames per tick
			boolean active = time >= 40 && time < 120; // an activity from 2 s to 6 s
			double before = t.gear;
			t.update(time, active);
			double step = (t.gear - before + 360.0) % 360.0;
			assertTrue(step >= 0 && step < 5, "the angle only moves forward, by small steps: " + step);
			if (frame > 1) {
				assertTrue(Math.abs(step - lastStep) < 0.2, "no jump of speed at frame " + frame + ": " + lastStep + " -> " + step);
			}
			lastStep = step;
			lastAngle = t.gear;
		}
		assertTrue(lastAngle >= 0 && lastAngle < 360);
		assertTrue(t.intensity < 0.01, "back to rest after the activity");
		// a pause (the game paused, the forge far away) or another world: no jump either
		double g = t.gear;
		t.update(400 + 20 * 60, false);
		assertEquals(g, t.gear, EPS, "a long gap restarts from the current pose");
		t.update(10, false);
		assertEquals(g, t.gear, EPS, "time going back: same");
	}

	@Test
	void effectsPace() {
		assertTrue(ForgeAnimation.near(24 * 24));
		assertFalse(ForgeAnimation.near(24.1 * 24.1));
		assertTrue(ForgeAnimation.chance(ForgeAnimation.SPARK_IDLE, ForgeAnimation.SPARK_CRAFT, true) > ForgeAnimation.SPARK_IDLE);
		for (double r : new double[] {0, 0.3, 0.999999, 1.0, -1}) {
			int i = ForgeAnimation.interval(ForgeAnimation.HAMMER_MIN, ForgeAnimation.HAMMER_MAX, r);
			assertTrue(i >= ForgeAnimation.HAMMER_MIN && i <= ForgeAnimation.HAMMER_MAX, r + " -> " + i);
		}
		assertTrue(ForgeAnimation.STEAM_CRAFT_MAX < ForgeAnimation.STEAM_IDLE_MIN, "steam puffs more often while active");
	}
}
