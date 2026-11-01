package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The medieval cannon (canon_medieval, 1.16.0): the fourth family of one-block props (group "artillery", tab
 * "Artillerie"), its geometry to scale (it fits on a rampart), collisions without invisible walls, the muzzle of the
 * future firing system, the named bones of the model, the persisted {@link CannonState}.
 */
public class CannonTest {
	private static final double EPS = 1e-6;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final TentType C = TentTypes.CANNON;

	@Test
	void theCannonIsTheArtilleryTab() {
		assertEquals("canon_medieval", C.id());
		assertEquals(TentType.ARTILLERY, C.group());
		assertTrue(C.isCannon() && C.masculine());
		assertFalse(C.isCart() || C.isWorkshop());
		assertEquals(List.of(C), TentTypes.ARTILLERY);
		assertSame(C, TentTypes.PROPS.get(TentTypes.PROPS.size() - 1), "the artillery comes last in PROPS");
		assertFalse(TentTypes.ALL.contains(C) || TentTypes.CARTS.contains(C) || TentTypes.WORKSHOPS.contains(C));
		assertEquals("canon médiéval", C.frenchName());
		assertEquals("Medieval Cannon", C.englishName());
		assertEquals("models/entity/canon_medieval.bbmodel", C.model());
		assertEquals("textures/entity/canon_medieval.png", C.texture(), "its own atlas");
		assertNull(C.decor());
		assertTrue(C.particles().isEmpty(), "no particles: nothing ticks, nothing smokes yet");
		for (String alias : new String[] {"canon_medieval", "medievalships:canon_medieval", "medieval", "canon", " Cannon "}) {
			assertSame(C, TentTypes.byId(alias), alias);
		}
		for (TentType t : TentTypes.PROPS) {
			assertEquals(t == C, t.isCannon(), t.id());
		}
	}

	@Test
	void sizeOfAFieldGunThatFitsOnARampart() {
		TentType.Box e = C.extent();
		assertEquals(0.0, e.y0(), EPS, "stands on the ground");
		// ~3.5-4 blocks long (muzzle to trail), ~2 wide (hub to hub), ~2 tall
		assertTrue(e.depth() > 3.4 && e.depth() < 4.2, "length " + e.depth());
		assertTrue(e.width() > 1.8 && e.width() < 2.6, "width " + e.width());
		assertTrue(e.height() > 1.8 && e.height() < 2.4, "height " + e.height());
		assertTrue(e.x0() > -1.5 && e.x1() < 1.5 && e.z0() > -2.5 && e.z1() < 2.5, "a 3 x 5 rampart walk holds it " + e);
	}

	@Test
	void fewTightCollisionBoxesAndRoomToWalkAround() {
		TentType.Box e = C.extent();
		List<TentType.Box> cs = C.colliders();
		assertTrue(cs.size() >= 4 && cs.size() <= 12, "a few boxes: carriage, barrel, wheels (" + cs.size() + ")");
		boolean barrel = false, wheelLeft = false, wheelRight = false, carriage = false;
		for (TentType.Box b : cs) {
			assertTrue(b.x0() >= e.x0() - EPS && b.x1() <= e.x1() + EPS && b.z0() >= e.z0() - EPS && b.z1() <= e.z1() + EPS && b.y0() >= 0
					&& b.y1() <= e.y1() + EPS, "inside the extent " + b);
			barrel |= b.y0() > 0.8 && b.depth() > 3.2 && b.width() < 1.0;
			wheelLeft |= b.x1() < -0.6 && b.y0() < 0.05 && b.height() > 1.2 && b.width() < 0.4;
			wheelRight |= b.x0() > 0.6 && b.y0() < 0.05 && b.height() > 1.2 && b.width() < 0.4;
			carriage |= b.y0() < 0.05 && Math.abs(b.x0() + b.x1()) < EPS && b.width() > 1.0 && b.width() < 1.5 && b.height() > 1.2;
		}
		assertTrue(barrel, "the barrel collides (one long box above the carriage)");
		assertTrue(wheelLeft && wheelRight, "both wheels collide");
		assertTrue(carriage, "the carriage collides");
		// no invisible wall: a player (0.6 wide) walks round it, along both sides and past both ends, just outside the extent
		for (double z = e.z0() - 0.4; z <= e.z1() + 0.4; z += 0.1) {
			assertFalse(hits(cs, e.x1() + 0.05, z), "free along the right side at z " + z);
			assertFalse(hits(cs, e.x0() - 0.65, z), "free along the left side at z " + z);
		}
		for (double x = e.x0() - 0.6; x <= e.x1() + 0.6; x += 0.1) {
			assertFalse(hits(cs, x, e.z0() - 0.65), "free in front of the muzzle at x " + x);
			assertFalse(hits(cs, x, e.z1() + 0.05), "free behind the trail at x " + x);
		}
		// the boxes turn with the facing
		for (int q = 0; q < 4; q++) {
			assertEquals(cs.size(), C.colliders(q).size());
		}
		assertEquals(e.depth(), C.extent(TentType.EAST).width(), EPS);
	}

	/** Does a 0.6 x 0.6 player column whose lower-left corner is at (x, z) touch a box below 1.8? */
	private static boolean hits(List<TentType.Box> cs, double x, double z) {
		for (TentType.Box b : cs) {
			if (b.x0() < x + 0.6 && b.x1() > x && b.z0() < z + 0.6 && b.z1() > z && b.y0() < 1.8) {
				return true;
			}
		}
		return false;
	}

	@Test
	void muzzleAtTheMouthPointingAwayFromThePlayer() {
		TentType.Muzzle m = C.muzzle();
		assertNotNull(m, "the cannon's JSON has a muzzle");
		TentType.Box e = C.extent();
		// the breech faces the player who placed it (+z), the mouth is at the other end (-z), barrel height
		assertTrue(m.z() < e.z0() + 0.3, "muzzle at the -z end: " + m.z() + " (extent from " + e.z0() + ")");
		assertEquals(0.0, m.x(), 0.05, "on the axis");
		assertTrue(m.y() > 1.3 && m.y() < 2.0, "barrel height " + m.y());
		assertEquals(1.0, Math.sqrt(m.dx() * m.dx() + m.dy() * m.dy() + m.dz() * m.dz()), EPS, "unit direction");
		assertTrue(m.dz() < -0.95 && m.dy() >= 0 && m.dy() < 0.3, "towards -z, slightly raised: " + m);
		// turned with the facing like the boxes: the muzzle of a cannon facing west (breech to -x) points to +x
		TentType.Muzzle w = C.muzzle(TentType.WEST);
		assertEquals(-m.z(), w.x(), EPS);
		assertEquals(m.x(), w.z(), EPS);
		assertTrue(w.dx() > 0.95, "facing west, it fires east " + w);
		assertEquals(m.dy(), w.dy(), EPS);
		TentType.Muzzle n = C.muzzle(TentType.NORTH);
		assertTrue(n.dz() > 0.95 && n.z() > 1.5, "facing north, it fires south " + n);
		// the tents have none
		assertNull(TentTypes.ADVENTURER.muzzle());
		assertNull(TentTypes.ADVENTURER.muzzle(TentType.EAST));
	}

	@Test
	void muzzleFieldParsedNormalisedOptional() {
		JsonObject root = JsonParser.parseString("""
				{"extent": [-1, 0, -2, 1, 2, 2], "colliders": [], "muzzle": [0, 1.5, -2], "muzzle_dir": [0, 0, -3]}
				""").getAsJsonObject();
		TentType t = TentType.parse(TentType.ARTILLERY, "canon_test", "canon d'essai", "Test Cannon", root);
		assertTrue(t.isCannon());
		assertEquals(-1.0, t.muzzle().dz(), EPS, "normalised");
		assertEquals(-2.0, t.muzzle().z(), EPS);
		JsonObject noDir = JsonParser.parseString("""
				{"extent": [-1, 0, -2, 1, 2, 2], "muzzle": [0, 1, 0]}
				""").getAsJsonObject();
		assertEquals(1.0, TentType.parse(TentType.ARTILLERY, "c2", "c", "C", noDir).muzzle().dz(), EPS, "default direction: the front");
		JsonObject none = JsonParser.parseString("""
				{"extent": [-1, 0, -2, 1, 2, 2]}
				""").getAsJsonObject();
		assertNull(TentType.parse(TentType.ARTILLERY, "c3", "c", "C", none).muzzle());
	}

	@Test
	void modelHasTheNamedBonesOfTheFutureAnimation() throws Exception {
		BbModel m;
		try (var in = CannonTest.class.getResourceAsStream("/assets/medievalships/" + C.model())) {
			assertNotNull(in, "model " + C.model());
			m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
		}
		assertTrue(m.quadCount() > 1000 && m.quadCount() < 6000, "faces " + m.quadCount());
		assertTrue(m.animations.isEmpty(), "static for now (the recoil comes with the firing)");
		for (String bone : new String[] {"carriage", "barrel", "wheel_left", "wheel_right", "detail", "furniture"}) {
			assertTrue(m.bonesByName.containsKey(bone), "bone " + bone);
		}
		// the pivots (Blockbench origin = (-x, y, -z) * 16): the barrel turns about its trunnions, the wheels about their hubs
		Map<String, double[]> pivots = new HashMap<>();
		JsonObject json;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve(C.model()), StandardCharsets.UTF_8)) {
			json = JsonParser.parseReader(r).getAsJsonObject();
		}
		Set<String> names = new HashSet<>();
		for (JsonElement g : json.getAsJsonArray("outliner")) {
			collect(g.getAsJsonObject(), pivots, names);
		}
		double[] barrel = pivots.get("barrel"), left = pivots.get("wheel_left"), right = pivots.get("wheel_right");
		assertTrue(barrel[1] > 1.2 && barrel[1] < 1.8 && Math.abs(barrel[0]) < EPS, "trunnion axis " + barrel[1]);
		assertEquals(left[1], right[1], EPS, "one axle");
		assertEquals(left[2], right[2], EPS, "one axle");
		assertTrue(left[0] < -0.6 && right[0] > 0.6, "left (-x) and right (+x) wheels, seen from behind the breech");
		assertTrue(left[1] > 0.6 && left[1] < 0.9, "hub height = wheel radius " + left[1]);
		assertTrue(m.bonesByName.get("barrel").index != m.bonesByName.get("carriage").index);
	}

	private static void collect(JsonObject g, Map<String, double[]> pivots, Set<String> names) {
		String name = g.get("name").getAsString();
		var o = g.getAsJsonArray("origin");
		pivots.put(name, new double[] {-o.get(0).getAsDouble() / 16, o.get(1).getAsDouble() / 16, -o.get(2).getAsDouble() / 16});
		names.add(name);
		for (JsonElement c : g.getAsJsonArray("children")) {
			if (c.isJsonObject()) {
				collect(c.getAsJsonObject(), pivots, names);
			}
		}
	}

	@Test
	void filesNamesAndTab() throws Exception {
		for (String file : new String[] {"artillery/canon_medieval.json", "blockstates/canon_medieval.json", "items/canon_medieval.json",
				"models/item/canon_medieval.json", "textures/item/canon_medieval.png", "models/block/cannon.json", C.model(), C.texture()}) {
			assertTrue(Files.isRegularFile(ASSETS.resolve(file)), file);
		}
		JsonObject states;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("blockstates/canon_medieval.json"), StandardCharsets.UTF_8)) {
			states = JsonParser.parseReader(r).getAsJsonObject().getAsJsonObject("variants");
		}
		for (String f : new String[] {"north", "south", "west", "east"}) {
			assertTrue(states.has("facing=" + f), "blockstate facing=" + f);
		}
		for (String[] lang : new String[][] {{"fr_fr", "Canon médiéval", "Artillerie"}, {"en_us", "Medieval Cannon", "Artillery"}}) {
			JsonObject names;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang[0] + ".json"), StandardCharsets.UTF_8)) {
				names = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertEquals(lang[1], names.get("block.medievalships.canon_medieval").getAsString(), lang[0]);
			assertEquals(lang[2], names.get("itemGroup.medievalships.artillery").getAsString(), lang[0]);
		}
	}

	@Test
	void cannonStateDefaultsClampsAndFires() {
		CannonState s = CannonState.EMPTY;
		assertTrue(s.isEmpty() && !s.loaded() && s.powder() == 0 && !s.lit() && !s.ready());
		assertEquals(CannonState.NEVER, s.lastShotTime());
		CannonState loaded = s.withLoaded(true).withPowder(2);
		assertTrue(loaded.ready() && !loaded.isEmpty());
		assertEquals(CannonState.MAX_POWDER, s.withPowder(99).powder(), "clamped");
		assertEquals(0, s.withPowder(-4).powder());
		assertEquals(CannonState.MAX_FUSE_TICKS, s.withFuseTicks(100000).fuseTicks());
		assertTrue(loaded.withFuseTicks(40).lit());
		assertEquals(CannonState.NEVER, s.withLastShotTime(-123).lastShotTime());
		CannonState shot = loaded.withFuseTicks(1).fired(5000L);
		assertFalse(shot.loaded() || shot.lit() || shot.powder() > 0);
		assertEquals(5000L, shot.lastShotTime());
		assertNotEquals(CannonState.EMPTY, shot, "a fired cannon remembers it");
		assertEquals(4, Set.of(CannonState.KEY_LOADED, CannonState.KEY_POWDER, CannonState.KEY_FUSE, CannonState.KEY_LAST_SHOT).size());
		assertEquals(new CannonState(true, 1, 0, 7L), new CannonState(true, 1, 0, 7L), "a value");
	}
}
