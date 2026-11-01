package fr.medievalships.core;

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
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The five merchant tents II (1.15.0): bard, gunsmith, archery, mage, armour. Tents like the six of 1.14.0 (group
 * "tents", tab "Tentes", the shared pavilion of tools/merchant/merchantlib.py, each with its own atlas), big enough
 * for a merchant NPC: a free spot of at least 1 x 1 x 2.2 blocks inside the tent, an open entrance and nothing solid
 * on the rug in front.
 */
public class Merchant2Test {
	private static final double EPS = 1e-9;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("tente_barde", "tente_fusils", "tente_archer", "tente_mage", "tente_armures");

	@Test
	void fiveMerchantTentsLoadInTheTentsTab() {
		assertEquals(5, TentTypes.MERCHANTS2.size());
		assertEquals(TentTypes.MERCHANTS2, TentTypes.ALL.subList(12, 17), "after the camp tents and the six merchant tents of 1.14.0");
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.MERCHANTS2.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.TENTS, t.group());
			assertFalse(t.isCart());
			assertFalse(t.isWorkshop());
			assertFalse(TentTypes.MERCHANTS.contains(t));
			assertTrue(TentTypes.ALL.contains(t) && TentTypes.PROPS.contains(t), t.id() + " in the tents' tab and the props");
			assertTrue(t.frenchName().startsWith("tente du vendeur "), t.frenchName());
			assertTrue(t.englishName().endsWith("Merchant Tent"), t.englishName());
			assertTrue(t.model().startsWith("models/entity/tente_") && t.model().endsWith(".bbmodel"), t.id() + " model " + t.model());
			assertTrue(t.texture().startsWith("textures/entity/tente_"), t.id() + " its own atlas " + t.texture());
		}
		assertSame(TentTypes.MERCHANT_BARD, TentTypes.byId("tente_barde"));
		assertSame(TentTypes.MERCHANT_GUNSMITH, TentTypes.byId("medievalships:tente_fusils"));
		assertSame(TentTypes.MERCHANT_ARCHERY, TentTypes.byId("archer"));
		assertSame(TentTypes.MERCHANT_MAGE, TentTypes.byId(" Mage "));
		assertSame(TentTypes.MERCHANT_ARMOUR, TentTypes.byId("armures"));
		assertSame(TentTypes.MERCHANT_ARMOURER, TentTypes.byId("armurier"), "the 1.14.0 armourer keeps its short name");
	}

	@Test
	void geometryToScaleCollidersInsideAndRoomForAMerchant() {
		for (TentType t : TentTypes.MERCHANTS2) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), EPS, t.id() + " stands on the ground");
			assertTrue(e.width() > 6.0 && e.width() < 11.0, t.id() + " width " + e.width());
			assertTrue(e.depth() > 6.0 && e.depth() < 11.0, t.id() + " depth " + e.depth());
			assertTrue(e.height() > 5.0 && e.height() < 10.0, t.id() + " height " + e.height());
			assertTrue(e.z1() > 4.5, t.id() + " the rug lies in front: extent to z " + e.z1());
			assertTrue(t.colliders().size() >= 4, t.id() + " collision boxes " + t.colliders().size());
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, t.id() + " inside the extent " + b);
				if (b.height() > 3.0 && b.width() < 0.6 && b.depth() < 0.6) {
					posts++;
				}
			}
			assertTrue(posts >= 4, t.id() + " four solid corner posts (" + posts + ")");
			for (TentType.Box b : t.colliders()) {
				// the front stays open: nothing solid across the entrance in the middle of the front
				boolean blocksEntrance = b.x0() < 0.3 && b.x1() > -0.3 && b.z1() > 2.2 && b.z0() < 3.0 && b.y0() < 1.5;
				assertFalse(blocksEntrance, t.id() + " the entrance is free " + b);
				// the rug in front is walkable: nothing solid on its middle strip
				boolean onRug = b.x0() < 1.0 && b.x1() > -1.0 && b.z1() > 3.4 && b.y0() < 1.5;
				assertFalse(onRug, t.id() + " nothing solid on the rug " + b);
			}
			assertTrue(freeSpot(t), t.id() + " a free spot of 1 x 1 x 2.2 blocks inside the tent for a merchant NPC");
			assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
		}
	}

	/** Is there a 1 x 1 column, 2.2 high, inside the posts (between the back wall and the front line) free of collisions? */
	static boolean freeSpot(TentType t) {
		for (double x = -2.5; x <= 1.5 + EPS; x += 0.1) {
			for (double z = -2.6; z <= 1.6 + EPS; z += 0.1) {
				boolean free = true;
				for (TentType.Box b : t.colliders()) {
					if (b.x0() < x + 1.0 && b.x1() > x && b.z0() < z + 1.0 && b.z1() > z && b.y0() < 2.2) {
						free = false;
						break;
					}
				}
				if (free) {
					return true;
				}
			}
		}
		return false;
	}

	@Test
	void namesAndItemFiles() throws Exception {
		JsonObject fr = null;
		for (String lang : new String[] {"en_us", "fr_fr"}) {
			JsonObject names;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang + ".json"), StandardCharsets.UTF_8)) {
				names = JsonParser.parseReader(r).getAsJsonObject();
			}
			for (TentType t : TentTypes.MERCHANTS2) {
				String key = "block.medievalships." + t.id();
				assertTrue(names.has(key) && !names.get(key).getAsString().isBlank(), lang + ": " + key);
			}
			if (lang.equals("fr_fr")) {
				fr = names;
			}
		}
		assertNotNull(fr);
		for (TentType t : TentTypes.MERCHANTS2) {
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1),
					fr.get("block.medievalships." + t.id()).getAsString(), "same French name in the commands and the lang file");
			for (String file : new String[] {"tents/" + t.id() + ".json", "blockstates/" + t.id() + ".json", "items/" + t.id() + ".json",
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
	void modelsLoadStaticWithoutParticles() throws Exception {
		for (TentType t : TentTypes.MERCHANTS2) {
			try (var in = Merchant2Test.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a tent has no animation");
			}
			assertTrue(t.particles().isEmpty(), t.id() + ": no permanent particles");
			if (t.decor() != null) {
				InteriorDecor.load(t.decor());
			}
		}
	}
}
