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
 * The merchant tents III (1.16.0): the poison merchant's and the butcher's gabled stalls. Tents like the eleven of
 * 1.14.0 / 1.15.0 (group "tents", tab "Tentes", each with its own atlas, tools/merchant/merchantlib.py), big enough
 * for a merchant NPC (a free 1 x 1 x 2.2 spot inside), open at the front. The checks hold for a gabled stall (a ridge
 * roof, lower than a pavilion's point, four posts) as well as for the stub copies they start from.
 */
public class Merchant3Test {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("tente_poison", "tente_boucher");

	@Test
	void twoMerchantTentsLoadInTheTentsTab() {
		assertEquals(2, TentTypes.MERCHANTS3.size());
		assertEquals(TentTypes.MERCHANTS3, TentTypes.ALL.subList(17, 19), "after the camp tents and the merchant tents I and II");
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.MERCHANTS3.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.TENTS, t.group());
			assertFalse(t.isCart() || t.isWorkshop() || t.isCannon(), t.id());
			assertFalse(t.masculine(), t.id() + ": une tente");
			assertFalse(TentTypes.MERCHANTS.contains(t) || TentTypes.MERCHANTS2.contains(t) || TentTypes.MERCHANTS4.contains(t), t.id());
			assertTrue(TentTypes.ALL.contains(t) && TentTypes.PROPS.contains(t), t.id() + " in the tents' tab and the props");
			assertTrue(t.frenchName().startsWith("tente du "), t.frenchName());
			assertTrue(t.englishName().endsWith("Tent"), t.englishName());
			assertTrue(t.model().startsWith("models/entity/tente_") && t.model().endsWith(".bbmodel"), t.id() + " model " + t.model());
			assertTrue(t.texture().startsWith("textures/entity/tente_"), t.id() + " its own atlas " + t.texture());
			assertEquals(null, t.muzzle(), t.id() + ": a tent has no muzzle");
		}
		assertEquals("tente du vendeur de poisons", TentTypes.MERCHANT_POISON.frenchName());
		assertEquals("Poison Merchant Tent", TentTypes.MERCHANT_POISON.englishName());
		assertEquals("tente du boucher", TentTypes.MERCHANT_BUTCHER.frenchName());
		assertEquals("Butcher's Tent", TentTypes.MERCHANT_BUTCHER.englishName());
		assertSame(TentTypes.MERCHANT_POISON, TentTypes.byId("tente_poison"));
		assertSame(TentTypes.MERCHANT_POISON, TentTypes.byId("medievalships:tente_poison"));
		assertSame(TentTypes.MERCHANT_POISON, TentTypes.byId("poison"));
		assertSame(TentTypes.MERCHANT_BUTCHER, TentTypes.byId(" Boucher "));
	}

	@Test
	void geometryToScaleCollidersInsideAndRoomForAMerchant() {
		for (TentType t : TentTypes.MERCHANTS3) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), 1e-9, t.id() + " stands on the ground");
			assertTrue(e.width() > 5.0 && e.width() < 11.0, t.id() + " width " + e.width());
			assertTrue(e.depth() > 5.0 && e.depth() < 11.0, t.id() + " depth " + e.depth());
			// a gabled stall is lower than a pavilion (no pointed roof), still well above a player's head
			assertTrue(e.height() > 4.0 && e.height() < 10.0, t.id() + " height " + e.height());
			assertTrue(t.colliders().size() >= 4, t.id() + " collision boxes " + t.colliders().size());
			int posts = 0;
			for (TentType.Box b : t.colliders()) {
				assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
						&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, t.id() + " inside the extent " + b);
				if (b.height() > 2.5 && b.width() < 0.6 && b.depth() < 0.6) {
					posts++;
				}
				// the front edge is walkable: nothing solid on the middle of the last half block before the front
				boolean blocksFront = b.x0() < 0.5 && b.x1() > -0.5 && b.z1() > e.z1() - 0.5 && b.y0() < 1.5;
				assertFalse(blocksFront, t.id() + " the front is walkable " + b);
			}
			assertTrue(posts >= 4, t.id() + " four solid posts (" + posts + ")");
			assertTrue(Merchant2Test.freeSpot(t), t.id() + " a free spot of 1 x 1 x 2.2 blocks inside the tent for a merchant NPC");
			assertEquals(t.colliders().size(), t.colliders(TentType.WEST).size());
		}
	}

	@Test
	void namesAndItemFiles() throws Exception {
		JsonObject fr;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/fr_fr.json"), StandardCharsets.UTF_8)) {
			fr = JsonParser.parseReader(r).getAsJsonObject();
		}
		JsonObject en;
		try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/en_us.json"), StandardCharsets.UTF_8)) {
			en = JsonParser.parseReader(r).getAsJsonObject();
		}
		for (TentType t : TentTypes.MERCHANTS3) {
			String key = "block.medievalships." + t.id();
			assertEquals(Character.toUpperCase(t.frenchName().charAt(0)) + t.frenchName().substring(1), fr.get(key).getAsString(),
					"same French name in the commands and the lang file");
			assertEquals(t.englishName(), en.get(key).getAsString());
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
	void modelsLoadStaticWithAtMostARareParticle() throws Exception {
		for (TentType t : TentTypes.MERCHANTS3) {
			try (var in = Merchant3Test.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a tent has no animation");
			}
			// the poison cauldron may give off a rare, discreet particle; nothing permanent
			for (TentType.Particle p : t.particles()) {
				assertTrue(p.known() && p.chance() <= 0.15 && p.count() <= 2, t.id() + " a rare discreet particle only " + p);
			}
			if (t.decor() != null) {
				InteriorDecor.load(t.decor());
			}
		}
	}
}
