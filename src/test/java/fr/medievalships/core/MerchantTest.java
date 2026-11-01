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
 * The six merchant tents (1.14.0): tents like the others (group "tents", tab "Tentes"), each with its own atlas, the
 * shared pavilion of tools/merchant/merchantlib.py (about 6.5 x 6 blocks, eave 3.4, apex 6.6, a rug in front).
 */
public class MerchantTest {
	private static final double EPS = 1e-9;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	private static final List<String> IDS = List.of("tente_armurier", "tente_alchimiste", "tente_herboriste", "tente_forgeron",
			"tente_nourriture", "tente_tissus");

	@Test
	void sixMerchantTentsLoadInTheTentsTab() {
		assertEquals(6, TentTypes.MERCHANTS.size());
		for (int i = 0; i < IDS.size(); i++) {
			TentType t = TentTypes.MERCHANTS.get(i);
			assertEquals(IDS.get(i), t.id());
			assertEquals(TentType.TENTS, t.group());
			assertFalse(t.isCart());
			assertFalse(t.isWorkshop());
			assertTrue(TentTypes.ALL.contains(t) && TentTypes.PROPS.contains(t), t.id() + " in the tents' tab and the props");
			assertTrue(t.frenchName().startsWith("tente "), t.frenchName());
			assertTrue(t.englishName().endsWith("Tent"), t.englishName());
			assertTrue(t.model().startsWith("models/entity/tente_") && t.model().endsWith(".bbmodel"), t.id() + " model " + t.model());
		}
		assertSame(TentTypes.MERCHANT_ARMOURER, TentTypes.byId("tente_armurier"));
		assertSame(TentTypes.MERCHANT_ARMOURER, TentTypes.byId("medievalships:tente_armurier"));
		assertSame(TentTypes.MERCHANT_CLOTH, TentTypes.byId("tissus"));
		assertSame(TentTypes.MERCHANT_FOOD, TentTypes.byId(" Nourriture "));
		assertSame(TentTypes.CHIEF, TentTypes.byId("chief"), "the camp tents keep their short names");
	}

	@Test
	void geometryToScaleAndCollidersInside() {
		for (TentType t : TentTypes.MERCHANTS) {
			TentType.Box e = t.extent();
			assertEquals(0.0, e.y0(), EPS, t.id() + " stands on the ground");
			assertTrue(e.width() > 6.0 && e.width() < 11.0, t.id() + " width " + e.width());
			assertTrue(e.depth() > 6.0 && e.depth() < 11.0, t.id() + " depth " + e.depth());
			assertTrue(e.height() > 6.0 && e.height() < 10.0, t.id() + " height " + e.height());
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
			// the front stays open: nothing solid across the entrance in the middle of the front
			for (TentType.Box b : t.colliders()) {
				boolean blocksEntrance = b.x0() < 0.3 && b.x1() > -0.3 && b.z1() > 2.2 && b.z0() < 3.0 && b.y0() < 1.5;
				assertFalse(blocksEntrance, t.id() + " the entrance is free " + b);
			}
			assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
		}
	}

	@Test
	void namesAndItemFiles() throws Exception {
		JsonObject fr = null;
		for (String lang : new String[] {"en_us", "fr_fr"}) {
			JsonObject names;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang + ".json"), StandardCharsets.UTF_8)) {
				names = JsonParser.parseReader(r).getAsJsonObject();
			}
			for (TentType t : TentTypes.MERCHANTS) {
				String key = "block.medievalships." + t.id();
				assertTrue(names.has(key) && !names.get(key).getAsString().isBlank(), lang + ": " + key);
			}
			if (lang.equals("fr_fr")) {
				fr = names;
			}
		}
		assertNotNull(fr);
		for (TentType t : TentTypes.MERCHANTS) {
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
	void modelsLoadStatic() throws Exception {
		for (TentType t : TentTypes.MERCHANTS) {
			try (var in = MerchantTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
				assertNotNull(in, "model " + t.model());
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000, t.id() + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), t.id() + ": a tent has no animation");
			}
		}
	}

	@Test
	void armourerDecorAndModel() throws Exception {
		TentType t = TentTypes.MERCHANT_ARMOURER;
		assertEquals("models/entity/tente_armurier.bbmodel", t.model());
		assertEquals("textures/entity/tente_armurier.png", t.texture());
		assertTrue(t.particles().isEmpty(), "no particles");
		assertNotNull(t.decor(), "furniture of the decoration mods");
		InteriorDecor d = InteriorDecor.load(t.decor());
		assertTrue(d.blocks().size() >= 4, "mod blocks " + d.blocks().size());
	}
}
