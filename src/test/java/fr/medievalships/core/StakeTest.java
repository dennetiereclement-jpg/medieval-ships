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
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The defensive stake (1.25.0, pieu_defensif: tools/deco/generate_pieu_defensif.py on its own atlas): its JSON loads in
 * the decorations' family (ninth, tab "Décorations"), a light static model (at most about 120 cubes, the bone "detail"),
 * one block across so stakes stand side by side, a few stepped collision boxes along the trunk (none on the point), the
 * hazard box at the point only, far from the foot, turning with the facing like the colliders, its direction outward;
 * the hazard JSON parsing (bounds, defaults) and the server settings "stake" (defaults, parsing, clamps).
 */
public class StakeTest {
	private static final double EPS = 1e-9;
	private static final TentType S = TentTypes.STAKE;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	private static JsonObject json(String s) {
		return JsonParser.parseString(s).getAsJsonObject();
	}

	@Test
	void loadsAsTheNinthDecoration() throws Exception {
		assertEquals("pieu_defensif", S.id());
		assertSame(S, TentTypes.DECORATIONS.get(8));
		assertSame(S, TentTypes.byId("pieu_defensif"));
		assertSame(S, TentTypes.byId("medievalships:pieu_defensif"));
		assertSame(S, TentTypes.byId("pieu"));
		assertSame(S, TentTypes.byId("stake"));
		assertTrue(S.isDecoration() && TentTypes.PROPS.contains(S) && !TentTypes.ALL.contains(S));
		assertEquals("pieu défensif", S.frenchName());
		assertEquals("Defensive Stake", S.englishName());
		assertTrue(S.masculine() && !S.plural(), "« Pieu défensif posé »");
		assertEquals("", S.agreement());
		assertEquals("textures/entity/pieu_defensif.png", S.texture());
		assertEquals(0, S.light());
		assertNull(S.decor());
		try (InputStream in = StakeTest.class.getResourceAsStream("/assets/medievalships/decorations/pieu_defensif.json")) {
			assertNotNull(in);
		}
		var img = javax.imageio.ImageIO.read(ASSETS.resolve(S.texture()).toFile());
		assertEquals(64, img.getWidth(), "a small atlas of its own");
		assertTrue(Files.isRegularFile(ASSETS.resolve("textures/item/pieu_defensif.png")));
		// only the stake hurts: every other prop stays without ticker
		for (TentType t : TentTypes.PROPS) {
			assertEquals(t == S, t.hasHazard(), t.id());
		}
	}

	@Test
	void lightStaticModel() throws Exception {
		try (var in = StakeTest.class.getResourceAsStream("/assets/medievalships/" + S.model())) {
			assertNotNull(in, S.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.animations.isEmpty(), "static");
			assertTrue(m.bonesByName.containsKey("detail"), "small things under 'detail' (hidden beyond 32 blocks)");
		}
		JsonObject model;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve(S.model()), StandardCharsets.UTF_8)) {
			model = JsonParser.parseReader(r).getAsJsonObject();
		}
		int cubes = 0;
		for (JsonElement ignored : model.getAsJsonArray("elements")) {
			cubes++;
		}
		assertTrue(cubes >= 30 && cubes <= 125, "a light model: " + cubes + " cubes");
	}

	@Test
	void oneBlockAcrossLeaningBackwards() {
		TentType.Box e = S.extent();
		assertEquals(0.0, e.y0(), EPS);
		assertTrue(e.x0() > -0.5 && e.x1() < 0.5, "one block across: a row of stakes one block apart " + e);
		assertTrue(e.z0() < -1.8 && e.z1() < 1.0, "the point leans towards the back (-z, away from the player who planted it) " + e);
		assertTrue(e.height() > 1.6 && e.height() < 2.2, "the tip about 1.5-2 high: " + e.height());
		assertTrue(e.depth() > 2.4 && e.depth() < 3.6, "about 3 blocks long on the ground: " + e.depth());
	}

	@Test
	void steppedBoxesAlongTheTrunk() {
		List<TentType.Box> cs = S.colliders();
		assertTrue(cs.size() >= 2 && cs.size() <= 5, "a few boxes, not one big box: " + cs.size());
		TentType.Box e = S.extent();
		double prevY = -1, prevZ = 99;
		for (TentType.Box b : cs) {
			assertTrue(b.width() <= 0.7 && b.depth() <= 0.9 && b.height() <= 1.0, "a small box along the trunk " + b);
			assertTrue(b.x0() >= e.x0() && b.x1() <= e.x1() && b.z0() >= e.z0() && b.z1() <= e.z1() && b.y1() <= e.y1(), "inside the extent " + b);
			assertTrue(b.y1() > prevY && b.z0() < prevZ, "stepping up and back along the trunk " + b);
			prevY = b.y1();
			prevZ = b.z0();
		}
		assertEquals(0.0, cs.get(0).y0(), EPS, "the first box stands on the ground (the trunk's foot)");
		assertTrue(cs.get(0).y1() > 0.6, "too high to step onto");
		// nothing on the point: its last block is free of collision boxes
		TentType.Hazard h = S.hazard();
		double tipZ = h.box().z0() + 0.15;
		for (TentType.Box b : cs) {
			assertTrue(b.z0() > tipZ + 0.4, "no box on the point " + b);
		}
		assertEquals(cs.size(), S.colliders(TentType.EAST).size());
	}

	@Test
	void hazardAtTheTipOnly() {
		TentType.Hazard h = S.hazard();
		assertNotNull(h, "the stake's JSON has a hazard");
		assertEquals(4.0, h.damage(), EPS);
		assertEquals(0.4, h.knockback(), EPS);
		assertEquals(20, h.cooldown());
		TentType.Box b = h.box();
		TentType.Box e = S.extent();
		assertTrue(b.depth() <= 1.4 && b.height() <= 1.3 && b.width() <= 0.8, "a small box (the point's last block) " + b);
		assertTrue(b.z0() <= e.z0() + 0.1 && b.z0() >= e.z0() - 0.2, "reaching the tip " + b);
		assertTrue(b.y1() >= e.y1() - 0.1, "up to the tip's height " + b);
		assertTrue(b.z1() < -1.0, "far from the foot (z ~ 0): " + b.z1());
		assertTrue(b.y0() > 0.7, "above the ground: a mob at the foot is not hurt " + b.y0());
		// the point's direction: outward, towards the back
		assertEquals(0.0, h.dirX(), 1e-6);
		assertEquals(-1.0, h.dirZ(), 1e-6);
		// a zombie (0.6 x 1.95) standing at the tip touches it; one at the foot or beside the trunk does not, even pressed
		// against the trunk: at the foot against the front face of the first box (z1 0.236 + 0.3 + 0.02), against the side
		// at mid-length beside the second box (x 0.29 + 0.3 + 0.02, z -0.6), the places StakeGameTest puts its zombies
		assertTrue(touches(h.box(), 0, -1.9), "a mob at the point");
		double[][] nearTrunk = {{0, 0.556}, {0.61, -0.6}, {-0.61, -0.6}};
		for (double[] p : nearTrunk) {
			assertFalse(touches(h.box(), p[0], p[1]), "a mob against the trunk (" + p[0] + ", " + p[1] + ") is not at the point");
			// meaningful places: inside the stake's extent (a hazard as big as the whole stake would hurt it), free of
			// collision but within a few hundredths of a trunk box (it can stand there, pressed against the trunk)
			assertTrue(touches(e, p[0], p[1]), "a mob against the trunk is within the stake's extent " + p[0] + ", " + p[1]);
			boolean pressed = false;
			for (TentType.Box c : S.colliders()) {
				assertFalse(overlap(c, p[0], p[1]), "a mob against the trunk is not inside a collision box " + c);
				pressed |= overlap(new TentType.Box(c.x0() - 0.05, c.y0(), c.z0() - 0.05, c.x1() + 0.05, c.y1(), c.z1() + 0.05), p[0], p[1]);
			}
			assertTrue(pressed, "a mob against the trunk nearly touches a trunk box " + p[0] + ", " + p[1]);
		}
		assertFalse(touches(h.box(), -1.0, -1.5), "a mob beside the point, one block aside");
		// and the zombie at the point is not inside a collision box (it can stand there)
		for (TentType.Box c : S.colliders()) {
			assertFalse(overlap(c, 0, -1.9), "the place at the point is free of collision " + c);
		}
	}

	private static boolean touches(TentType.Box b, double x, double z) {
		return x + 0.3 > b.x0() && x - 0.3 < b.x1() && z + 0.3 > b.z0() && z - 0.3 < b.z1() && 1.95 > b.y0() && 0.0 < b.y1();
	}

	private static boolean overlap(TentType.Box b, double x, double z) {
		return touches(b, x, z);
	}

	@Test
	void hazardTurnsWithTheFacing() {
		TentType.Hazard s = S.hazard(TentType.SOUTH);
		for (int q = 0; q < 4; q++) {
			TentType.Hazard h = S.hazard(q);
			assertEquals(TentType.rotate(s.box(), q), h.box(), "the box turns like the colliders");
			double[] d = TentType.rotate(s.dirX(), s.dirZ(), q);
			assertEquals(d[0], h.dirX(), 1e-9);
			assertEquals(d[1], h.dirZ(), 1e-9);
			assertEquals(s.box().height(), h.box().height(), EPS);
		}
		// facing north (the player looked south when planting it): the point goes south (+z), away from the player
		TentType.Hazard n = S.hazard(TentType.NORTH);
		assertTrue(n.box().z0() > 1.0 && Math.abs(n.dirZ() - 1.0) < 1e-9, "north-facing stake: point to +z " + n.box());
		TentType.Hazard w = S.hazard(TentType.WEST);
		assertTrue(w.box().x0() > 1.0 && Math.abs(w.dirX() - 1.0) < 1e-9, "west-facing stake: point to +x " + w.box());
		TentType.Hazard east = S.hazard(TentType.EAST);
		assertTrue(east.box().x1() < -1.0 && Math.abs(east.dirX() + 1.0) < 1e-9, "east-facing stake: point to -x " + east.box());
	}

	@Test
	void hazardJsonParsing() {
		String extent = "\"extent\": [-0.5, 0, -1, 0.5, 2, 1]";
		assertNull(TentType.parseHazard(json("{" + extent + "}")), "absent: no hazard");
		assertNull(TentType.parseHazard(json("{\"hazard\": 3}")));
		assertNull(TentType.parseHazard(json("{\"hazard\": {\"damage\": 5}}")), "no box: no hazard");
		assertNull(TentType.parseHazard(json("{\"hazard\": {\"box\": [0, 0, 0, 1, 1]}}")), "five numbers: no hazard");
		assertNull(TentType.parseHazard(json("{\"hazard\": {\"box\": [0, 0, 0, 1, 1, \"x\"]}}")));
		TentType.Hazard d = TentType.parseHazard(json("{\"hazard\": {\"box\": [0.3, 2, -1, -0.3, 1, -2]}}"));
		assertEquals(new TentType.Box(-0.3, 1, -2, 0.3, 2, -1), d.box(), "corners sorted");
		assertEquals(4.0, d.damage(), EPS);
		assertEquals(0.4, d.knockback(), EPS);
		assertEquals(20, d.cooldown());
		TentType.Hazard c = TentType.parseHazard(json("{\"hazard\": {\"box\": [1, 0, -0.2, 2, 1, 0.2], \"damage\": 900, \"knockback\": -1, \"cooldown\": 0}}"));
		assertEquals(TentType.MAX_HAZARD_DAMAGE, c.damage(), EPS, "clamped");
		assertEquals(0.0, c.knockback(), EPS);
		assertEquals(TentType.MIN_HAZARD_COOLDOWN, c.cooldown());
		assertEquals(1.0, c.dirX(), 1e-9, "the direction from the anchor to the box: +x");
		TentType.Hazard centred = TentType.parseHazard(json("{\"hazard\": {\"box\": [-0.5, 0, -0.5, 0.5, 1, 0.5], \"cooldown\": 99999}}"));
		assertEquals(-1.0, centred.dirZ(), 1e-9, "a centred box points to the back");
		assertEquals(TentType.MAX_HAZARD_COOLDOWN, centred.cooldown());
		TentType parsed = TentType.parse(TentType.DECORATIONS, "deco_x", "décoration x", "X", json("{" + extent
				+ ", \"hazard\": {\"box\": [-0.2, 1, -2, 0.2, 2, -1], \"damage\": 6}}"));
		assertTrue(parsed.hasHazard());
		assertEquals(6.0, parsed.hazard().damage(), EPS);
		assertEquals(TentType.rotate(parsed.hazard().box(), TentType.EAST), parsed.hazard(TentType.EAST).box());
		assertFalse(TentType.parse(TentType.DECORATIONS, "deco_y", "décoration y", "Y", json("{" + extent + "}")).hasHazard());
		assertTrue(d.contains(0, 1.5, -1.5) && !d.contains(0, 0.5, -1.5));
	}

	@Test
	void stakeSettingsDefaultsParsingAndClamps() {
		ServerSettings defaults = new ServerSettings();
		defaults.sanitize();
		assertNotNull(defaults.stake);
		assertEquals(4.0, defaults.stake.damage, EPS);
		assertEquals(0.4, defaults.stake.knockback, EPS);
		assertEquals(20, defaults.stake.cooldownTicks);
		assertFalse(defaults.stake.damagePlayers, "players are spared by default");
		// the model's JSON and the config have the same defaults
		assertEquals(S.hazard().damage(), defaults.stake.damage, EPS);
		assertEquals(S.hazard().knockback(), defaults.stake.knockback, EPS);
		assertEquals(S.hazard().cooldown(), defaults.stake.cooldownTicks);

		ServerSettings s = new Gson().fromJson("{\"stake\": {\"damage\": 7.5, \"knockback\": 0.8, \"cooldownTicks\": 40, \"damagePlayers\": true}}",
				ServerSettings.class);
		s.sanitize();
		assertEquals(7.5, s.stake.damage, EPS);
		assertEquals(0.8, s.stake.knockback, EPS);
		assertEquals(40, s.stake.cooldownTicks);
		assertTrue(s.stake.damagePlayers);

		ServerSettings partial = new Gson().fromJson("{\"stake\": {\"damage\": 2}}", ServerSettings.class);
		partial.sanitize();
		assertEquals(2.0, partial.stake.damage, EPS);
		assertEquals(0.4, partial.stake.knockback, EPS, "missing keys keep their defaults");
		assertEquals(20, partial.stake.cooldownTicks);

		ServerSettings wild = new Gson().fromJson("{\"stake\": {\"damage\": -3, \"knockback\": 50, \"cooldownTicks\": 0}}", ServerSettings.class);
		wild.sanitize();
		assertEquals(0.0, wild.stake.damage, EPS, "clamped to 0");
		assertEquals(StakeSettings.MAX_KNOCKBACK, wild.stake.knockback, EPS);
		assertEquals(StakeSettings.MIN_COOLDOWN_TICKS, wild.stake.cooldownTicks);
		ServerSettings big = new Gson().fromJson("{\"stake\": {\"damage\": 1e9, \"cooldownTicks\": 99999}}", ServerSettings.class);
		big.sanitize();
		assertEquals(StakeSettings.MAX_DAMAGE, big.stake.damage, EPS);
		assertEquals(StakeSettings.MAX_COOLDOWN_TICKS, big.stake.cooldownTicks);

		ServerSettings old = new Gson().fromJson("{\"adminPermissionLevel\": 3}", ServerSettings.class);
		old.sanitize();
		assertEquals(4.0, old.stake.damage, EPS, "a config file of an older version");
		ServerSettings nulls = new Gson().fromJson("{\"stake\": null}", ServerSettings.class);
		nulls.sanitize();
		assertNotNull(nulls.stake);
		assertFalse(nulls.stake.damagePlayers);
		StakeSettings nan = new StakeSettings();
		nan.damage = Double.NaN;
		nan.knockback = Double.NaN;
		nan.sanitize();
		assertEquals(StakeSettings.DEFAULT_DAMAGE, nan.damage, EPS);
		assertEquals(StakeSettings.DEFAULT_KNOCKBACK, nan.knockback, EPS);
		// written back: the keys appear in the config file
		JsonObject written = new Gson().toJsonTree(defaults).getAsJsonObject().getAsJsonObject("stake");
		for (String k : new String[] {"damage", "knockback", "cooldownTicks", "damagePlayers"}) {
			assertTrue(written.has(k), k);
		}
	}

	@Test
	void namesDeathMessagesAndDamageType() throws Exception {
		JsonObject fr, en;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/fr_fr.json"), StandardCharsets.UTF_8)) {
			fr = JsonParser.parseReader(r).getAsJsonObject();
		}
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/en_us.json"), StandardCharsets.UTF_8)) {
			en = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals("Pieu défensif", fr.get("block.medievalships.pieu_defensif").getAsString());
		assertEquals("Defensive Stake", en.get("block.medievalships.pieu_defensif").getAsString());
		assertEquals("%1$s s'est empalé sur un pieu", fr.get("death.attack.medievalships.stake").getAsString());
		assertEquals("%1$s was impaled on a stake", en.get("death.attack.medievalships.stake").getAsString());
		assertTrue(fr.has("death.attack.medievalships.stake.player") && en.has("death.attack.medievalships.stake.player"));
		Path data = Path.of("src/main/resources/data");
		JsonObject type;
		try (Reader r = Files.newBufferedReader(data.resolve("medievalships/damage_type/stake.json"), StandardCharsets.UTF_8)) {
			type = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals("medievalships.stake", type.get("message_id").getAsString(), "death.attack.<message_id>");
		assertTrue(List.of("never", "always", "when_caused_by_living_non_player").contains(type.get("scaling").getAsString()));
		assertTrue(type.has("exhaustion"));
		JsonObject tag;
		try (Reader r = Files.newBufferedReader(data.resolve("minecraft/tags/damage_type/no_knockback.json"), StandardCharsets.UTF_8)) {
			tag = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertFalse(tag.has("replace") && tag.get("replace").getAsBoolean(), "added to the vanilla tag, never replacing it");
		assertTrue(tag.getAsJsonArray("values").toString().contains("medievalships:stake"), "the push outward is the stake's own");
	}

	@Test
	void campTentsRegistered() throws Exception {
		assertEquals(List.of("tente_militaire", "tente_commandement", "tente_marchande"), TentTypes.CAMP_TENTS.stream().map(TentType::id).toList());
		assertEquals(TentTypes.CAMP_TENTS, TentTypes.ALL.subList(22, 25), "appended to the tents' tab (the market tents of 1.26.0 after them)");
		assertSame(TentTypes.CAMP_MILITARY, TentTypes.byId("militaire"));
		assertSame(TentTypes.CAMP_COMMAND, TentTypes.byId("commandement"));
		assertSame(TentTypes.CAMP_MERCHANT, TentTypes.byId("marchande"));
		assertSame(TentTypes.COMMAND, TentTypes.byId("command"), "the older command tent keeps its short name");
		assertSame(TentTypes.MARKET, TentTypes.byId("market"));
		JsonObject fr, en;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/fr_fr.json"), StandardCharsets.UTF_8)) {
			fr = JsonParser.parseReader(r).getAsJsonObject();
		}
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/en_us.json"), StandardCharsets.UTF_8)) {
			en = JsonParser.parseReader(r).getAsJsonObject();
		}
		for (TentType t : TentTypes.CAMP_TENTS) {
			assertEquals(TentType.TENTS, t.group());
			assertFalse(t.hasHazard());
			String key = "block.medievalships." + t.id();
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1), fr.get(key).getAsString());
			assertEquals(t.englishName(), en.get(key).getAsString());
			for (String file : new String[] {"tents/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
					"models/item/" + t.id() + ".json", "textures/item/" + t.id() + ".png", t.model(), t.texture()}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), t.id() + ": " + file);
			}
		}
		assertEquals("Tente de commandement militaire", fr.get("block.medievalships.tente_commandement").getAsString());
		assertEquals("Military Command Tent", en.get("block.medievalships.tente_commandement").getAsString());
	}
}
