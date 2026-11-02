package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The eight crafting workshops (the jeweller's workbench of 1.22.0 the eighth): the third family of one-block props
 * (same TentType machinery as the tents and carts), their files and names, and the optional particle sources of their JSON (parsed, turned with the facing).
 */
public class WorkshopTest {
	private static final double EPS = 1e-9;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("workshop_blacksmith", "workshop_leatherworker", "workshop_tailor", "workshop_engineer",
			"workshop_cook", "workshop_alchemist", "workshop_enchanter", "workshop_jeweler");

	@Test
	void eightWorkshopsLoadAfterTheTentsAndCarts() {
		assertEquals(8, TentTypes.WORKSHOPS.size(), "the seven workshops of 1.13.0 and the jeweller's workbench (1.22.0)");
		assertEquals(6 + 6 + 5 + 2 + 2 + 1, TentTypes.ALL.size(),
				"the tents' list: six camp tents, merchant tents I (6), II (5), III (2), IV (2) and V (1, the jeweller's)");
		assertEquals(10, TentTypes.CARTS.size(), "the carts' list: the eight carts, the nomad tavern, the decorative rowboat (1.19.0)");
		assertEquals(TentTypes.WORKSHOPS, TentTypes.PROPS.subList(32, 40), "the workshops come after the tents and carts in PROPS");
		assertEquals(TentTypes.TRAINING, TentTypes.PROPS.subList(40, 43), "then the training areas (1.18.0)");
		assertEquals(TentTypes.DECORATIONS, TentTypes.PROPS.subList(43, 51), "then the street decorations (1.20.0)");
		assertEquals(TentTypes.ARTILLERY, TentTypes.PROPS.subList(51, 52), "then the artillery, last");
		Set<String> ids = new HashSet<>();
		for (TentType t : TentTypes.PROPS) {
			assertTrue(ids.add(t.id()), "id used twice: " + t.id());
		}
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.WORKSHOPS.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.WORKSHOPS, t.group());
			assertTrue(t.isWorkshop());
			assertFalse(t.isCart());
			assertTrue(t.frenchName().startsWith("atelier ") || t.frenchName().startsWith("établi "), t.frenchName());
			assertTrue(t.englishName().endsWith("Workshop") || t.englishName().endsWith("Workbench"), t.englishName());
			assertTrue(t.masculine(), t.id() + ": l'atelier, l'établi");
		}
		for (TentType t : TentTypes.ALL) {
			assertFalse(t.isWorkshop(), t.id());
		}
		for (TentType t : TentTypes.CARTS) {
			assertFalse(t.isWorkshop(), t.id());
		}
		assertSame(TentTypes.WORKSHOP_BLACKSMITH, TentTypes.byId("workshop_blacksmith"));
		assertSame(TentTypes.WORKSHOP_ENCHANTER, TentTypes.byId("medievalships:workshop_enchanter"));
		assertSame(TentTypes.WORKSHOP_COOK, TentTypes.byId("cook"));
		assertSame(TentTypes.WORKSHOP_ALCHEMIST, TentTypes.byId(" Alchemist "));
		assertSame(TentTypes.WORKSHOP_JEWELER, TentTypes.byId("jeweler"));
		assertSame(TentTypes.WORKSHOP_JEWELER, TentTypes.WORKSHOPS.get(7), "the jeweller's workbench is the eighth, after the enchanter");
		assertEquals("établi du joaillier", TentTypes.WORKSHOP_JEWELER.frenchName());
		assertEquals("Jeweller's Workbench", TentTypes.WORKSHOP_JEWELER.englishName());
		assertSame(TentTypes.MARKET, TentTypes.byId("market"), "the tents and carts keep their short names");
	}

	@Test
	void geometryToScaleAndCollidersInside() {
		for (TentType t : TentTypes.WORKSHOPS) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), EPS, t.id() + " stands on the ground");
			assertTrue(e.width() > 1.0 && e.width() < 12.0, t.id() + " width " + e.width());
			assertTrue(e.depth() > 1.0 && e.depth() < 12.0, t.id() + " depth " + e.depth());
			assertTrue(e.height() > 1.0 && e.height() < 10.0, t.id() + " height " + e.height());
			assertFalse(t.colliders().isEmpty(), t.id() + " has collision boxes");
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y1() <= e.y1() + 0.05, t.id() + " inside the extent " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
			assertEquals(t.particles().size(), t.particles(TentType.NORTH).size());
		}
	}

	@Test
	void particlesOfTheShippedFilesAreValid() {
		for (TentType t : TentTypes.WORKSHOPS) {
			TentType.Box e = t.extent();
			for (TentType.Particle p : t.particles()) {
				assertTrue(p.known(), t.id() + " unknown particle type " + p.type() + " (known: " + TentType.PARTICLE_TYPES + ")");
				assertTrue(p.chance() > 0 && p.chance() <= 1, t.id() + " chance " + p.chance());
				assertTrue(p.count() >= 1 && p.count() <= 16, t.id() + " count " + p.count());
				assertTrue(p.x() >= e.x0() - 0.5 && p.x() <= e.x1() + 0.5 && p.z() >= e.z0() - 0.5 && p.z() <= e.z1() + 0.5
						&& p.y() >= 0 && p.y() <= e.y1() + 3, t.id() + " particle source near the workshop " + p);
			}
		}
		for (TentType t : TentTypes.ALL.subList(0, 6)) {
			assertTrue(t.particles().isEmpty(), t.id() + ": the camp tents have no particles");
		}
	}

	@Test
	void particleFieldParsedAndTurnedWithTheFacing() {
		JsonObject root = JsonParser.parseString("""
				{"extent": [-2, 0, -1.5, 2, 3, 1.5], "colliders": [[-1, 0, -1, 1, 1, 1]],
				 "particles": [
				   {"type": "minecraft:FLAME", "pos": [1.0, 2.0, 0.5], "chance": 0.25, "count": 3},
				   {"type": "campfire_smoke", "pos": [-1.5, 3.2, 1.0]},
				   {"type": "enchant", "pos": [0, 1, 0], "chance": 7, "count": 99},
				   {"type": "fireworks", "pos": [0, 1, 0]}
				 ]}""").getAsJsonObject();
		TentType t = TentType.parse(TentType.WORKSHOPS, "workshop_test", "atelier d'essai", "Test Workshop", root);
		assertTrue(t.isWorkshop());
		assertEquals("models/entity/workshop_test.bbmodel", t.model(), "default model path");
		List<TentType.Particle> ps = t.particles();
		assertEquals(4, ps.size());
		TentType.Particle flame = ps.get(0);
		assertEquals("flame", flame.type(), "minecraft: prefix and case removed");
		assertTrue(flame.known());
		assertEquals(0.25, flame.chance(), EPS);
		assertEquals(3, flame.count());
		assertEquals(1.0, ps.get(1).chance(), EPS, "chance defaults to 1");
		assertEquals(1, ps.get(1).count(), "count defaults to 1");
		assertEquals(1.0, ps.get(2).chance(), EPS, "chance clamped to 1");
		assertEquals(16, ps.get(2).count(), "count clamped to 16");
		assertFalse(ps.get(3).known(), "an unknown type is kept but ignored in game");
		// turned like the collision boxes: the source on the right (+x) in front (+z) goes front-left when facing west
		TentType.Particle w = t.particles(TentType.WEST).get(0);
		assertArrayEquals(TentType.rotate(1.0, 0.5, TentType.WEST), new double[] {w.x(), w.z()}, EPS);
		assertEquals(2.0, w.y(), EPS, "height unchanged");
		TentType.Particle n = t.particles(TentType.NORTH).get(0);
		assertEquals(-1.0, n.x(), EPS);
		assertEquals(-0.5, n.z(), EPS);
		assertEquals(flame, t.particles(TentType.SOUTH).get(0));
		// a prop without the field has none
		JsonObject plain = JsonParser.parseString("{\"extent\": [-1, 0, -1, 1, 2, 1]}").getAsJsonObject();
		assertTrue(TentType.parse(TentType.CARTS, "cart_x", "x", "X", plain).particles().isEmpty());
	}

	@Test
	void namesAndItemFiles() throws Exception {
		for (String lang : new String[] {"en_us", "fr_fr"}) {
			JsonObject names;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang + ".json"), StandardCharsets.UTF_8)) {
				names = JsonParser.parseReader(r).getAsJsonObject();
			}
			assertTrue(names.has("itemGroup.medievalships.workshops"), lang + ": tab name");
			for (TentType t : TentTypes.WORKSHOPS) {
				String key = "block.medievalships." + t.id();
				assertTrue(names.has(key) && !names.get(key).getAsString().isBlank(), lang + ": " + key);
			}
		}
		JsonObject fr;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/fr_fr.json"), StandardCharsets.UTF_8)) {
			fr = JsonParser.parseReader(r).getAsJsonObject();
		}
		assertEquals("Ateliers", fr.get("itemGroup.medievalships.workshops").getAsString());
		for (TentType t : TentTypes.WORKSHOPS) {
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1),
					fr.get("block.medievalships." + t.id()).getAsString(), "same French name in the commands and the lang file");
			for (String file : new String[] {"workshops/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
					"models/item/" + t.id() + ".json", "textures/item/" + t.id() + ".png", t.model(), t.texture()}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), t.id() + ": " + file);
			}
			JsonObject states;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("blockstates/" + t.id() + ".json"), StandardCharsets.UTF_8)) {
				states = JsonParser.parseReader(r).getAsJsonObject().getAsJsonObject("variants");
			}
			for (String f : new String[] {"north", "south", "west", "east"}) {
				assertTrue(states.has("facing=" + f), t.id() + " blockstate facing=" + f);
			}
		}
	}

	@Test
	void modelsLoadStatic() throws Exception {
		for (TentType t : TentTypes.WORKSHOPS) {
			try (var in = WorkshopTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 0, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a workshop has no animation");
			}
		}
	}
}
