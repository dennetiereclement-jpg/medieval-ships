package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

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

/**
 * The registration of the seventeen market tents of Lion Port and the other cities (1.26.0, {@link TentTypes#MARKET_TENTS}):
 * their order (the reference table's), appended last to the tents' tab, their French and English names (the same as in
 * each group's test, lower case in the code as for the other tents, capitalised in the lang files), the blockstate, item,
 * item model and icon files, the French gender of the pavilions and marquees, the short names of {@link TentTypes#byId}
 * (the older props keep theirs), and the merchant's place behind each counter (the builders' NPC_SPOT, the same as in
 * the in-game TentGameTest). Each tent's own geometry is checked by its group's test (MarketATest ... MarketFTest).
 */
public class MarketTentsTest {
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	/** id, French name (lang), English name, French masculine, (x0, z0) of the merchant's free 1 x 1 x 2.2 place. */
	private record Spec(String id, String fr, String en, boolean masculine, double npcX, double npcZ) {
	}

	private static final List<Spec> SPECS = List.of(
			new Spec("tente_lion_pavillon", "Pavillon au lion", "Lion Pavilion", true, -1.45, -0.70),
			new Spec("tente_lion_longue", "Longue tente au lion", "Long Lion Tent", false, -0.40, -0.85),
			new Spec("tente_imperiale", "Tente marchande impériale", "Imperial Merchant Tent", false, -1.85, -1.25),
			new Spec("tente_lion_drapee", "Tente drapée au lion", "Draped Lion Tent", false, 0.60, -1.98),
			new Spec("tente_lion_chapiteau", "Chapiteau royal au lion", "Royal Lion Marquee", true, 0.40, -0.12),
			new Spec("tente_balance_bleue", "Tente bleue à la balance", "Blue Scales Tent", false, 0.00, 0.38),
			new Spec("tente_balance_chapiteau", "Grand chapiteau à la balance", "Great Scales Marquee", true, -2.65, 0.25),
			new Spec("tente_balance_fer", "Pavillon à la balance et ferronnerie", "Wrought-Iron Scales Pavilion", true, -1.45, -0.62),
			new Spec("tente_balance_bourse", "Tente à la balance et à la bourse", "Scales and Purse Tent", false, 0.40, -0.55),
			new Spec("tente_balance_auvent", "Tente à la balance et à l'auvent", "Scales Tent with Awning", false, 0.75, 0.15),
			new Spec("tente_balance_pignon", "Tente à pignon à la balance", "Gabled Scales Tent", false, -0.45, -1.85),
			new Spec("tente_draperie", "Tente aux draperies rouges", "Red Drapery Tent", false, 0.30, -0.80),
			new Spec("tente_fleur_de_lys", "Tente à la fleur de lys", "Fleur-de-lis Tent", false, -0.60, -0.75),
			new Spec("tente_cordages", "Tente rouge aux cordages", "Red Rope Tent", false, 0.90, -1.05),
			new Spec("tente_frontiere", "Tente marchande de frontière", "Frontier Merchant Tent", false, 0.60, -2.73),
			new Spec("tente_sylvestre", "Tente marchande sylvestre", "Sylvan Merchant Tent", false, 0.90, -2.96),
			new Spec("tente_arsenal", "Tente marchande de l'arsenal", "Arsenal Merchant Tent", false, -0.35, -2.74));

	private static JsonObject json(String file) throws Exception {
		try (Reader r = Files.newBufferedReader(ASSETS.resolve(file), StandardCharsets.UTF_8)) {
			return JsonParser.parseReader(r).getAsJsonObject();
		}
	}

	@Test
	void seventeenTentsAppendedToTheTentsTab() {
		assertEquals(17, TentTypes.MARKET_TENTS.size());
		assertEquals(SPECS.stream().map(Spec::id).toList(), TentTypes.MARKET_TENTS.stream().map(TentType::id).toList(),
				"the order of the reference table (groups A to F)");
		assertEquals(TentTypes.MARKET_TENTS, TentTypes.ALL.subList(TentTypes.ALL.size() - 17, TentTypes.ALL.size()),
				"appended last to the tents' tab, after the military camp (1.25.0)");
		assertEquals(TentTypes.CAMP_TENTS, TentTypes.ALL.subList(22, 25));
		Set<String> french = new HashSet<>();
		for (TentType t : TentTypes.PROPS) {
			assertTrue(french.add(t.frenchName()), "French name used twice: " + t.frenchName());
		}
		for (int i = 0; i < SPECS.size(); i++) {
			Spec s = SPECS.get(i);
			TentType t = TentTypes.MARKET_TENTS.get(i);
			assertTrue(TentTypes.PROPS.contains(t), s.id());
			assertEquals(TentType.TENTS, t.group(), s.id());
			assertFalse(t.isCart() || t.isWorkshop() || t.isCannon() || t.isTraining() || t.isDecoration(), s.id());
			assertEquals(s.fr().toLowerCase(java.util.Locale.ROOT).charAt(0) + s.fr().substring(1), t.frenchName(),
					s.id() + ": lower case in the code, like the other tents");
			assertEquals(s.en(), t.englishName(), s.id());
			assertEquals(s.masculine(), t.masculine(), s.id() + (s.masculine() ? ": « posé »" : ": « posée »"));
			assertFalse(t.plural(), s.id());
			assertEquals("models/entity/" + s.id() + ".bbmodel", t.model(), s.id());
			assertEquals("textures/entity/" + s.id() + ".png", t.texture(), s.id() + ": its own atlas");
			assertTrue(t.light() == 12 || t.light() == 13, s.id() + " light " + t.light());
			assertTrue(t.seats().isEmpty() && !t.hasTargets() && !t.hasHazard() && t.muzzle() == null, s.id() + ": a static tent");
			assertEquals(t == TentTypes.MARKET_ARSENAL, !t.particles().isEmpty(), s.id() + ": only the arsenal's boiler smokes");
		}
	}

	@Test
	void langBlockstatesItemsAndIcons() throws Exception {
		JsonObject fr = json("lang/fr_fr.json"), en = json("lang/en_us.json");
		for (Spec s : SPECS) {
			String key = "block.medievalships." + s.id();
			assertEquals(s.fr(), fr.get(key).getAsString(), key);
			assertEquals(s.en(), en.get(key).getAsString(), key);
			for (String file : new String[] {"tents/" + s.id() + ".json", "blockstates/" + s.id() + ".json", "items/" + s.id() + ".json",
					"models/item/" + s.id() + ".json", "textures/item/" + s.id() + ".png", "models/entity/" + s.id() + ".bbmodel",
					"textures/entity/" + s.id() + ".png", "interiors/" + s.id() + "_decor.json"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), s.id() + ": " + file);
			}
			assertTrue(Files.isRegularFile(Path.of("blockbench/" + s.id() + ".bbmodel")), s.id() + ": the Blockbench copy");
			assertTrue(Files.isRegularFile(Path.of("tools/market/generate_" + s.id() + ".py")), s.id() + ": its generator");
			JsonObject variants = json("blockstates/" + s.id() + ".json").getAsJsonObject("variants");
			for (String f : new String[] {"north", "south", "west", "east"}) {
				assertEquals("medievalships:block/tent", variants.getAsJsonObject("facing=" + f).get("model").getAsString(),
						s.id() + ": the invisible anchor block, facing " + f);
			}
			assertEquals("medievalships:item/" + s.id(), json("items/" + s.id() + ".json").getAsJsonObject("model").get("model").getAsString());
			JsonObject item = json("models/item/" + s.id() + ".json");
			assertEquals("minecraft:item/generated", item.get("parent").getAsString());
			assertEquals("medievalships:item/" + s.id(), item.getAsJsonObject("textures").get("layer0").getAsString());
			byte[] png = Files.readAllBytes(ASSETS.resolve("textures/item/" + s.id() + ".png"));
			int w = (png[16] & 0xff) << 24 | (png[17] & 0xff) << 16 | (png[18] & 0xff) << 8 | png[19] & 0xff;
			int h = (png[20] & 0xff) << 24 | (png[21] & 0xff) << 16 | (png[22] & 0xff) << 8 | png[23] & 0xff;
			assertTrue(w == 16 && h == 16, s.id() + ": a 16 x 16 icon (" + w + " x " + h + ")");
		}
	}

	@Test
	void shortNamesAndTheOlderPropsKeepTheirs() {
		for (TentType t : TentTypes.MARKET_TENTS) {
			assertSame(t, TentTypes.byId(t.id()));
			assertSame(t, TentTypes.byId("medievalships:" + t.id()));
			if (t != TentTypes.MARKET_DRAPERY) {
				assertSame(t, TentTypes.byId(" " + t.id().substring("tente_".length()).toUpperCase(java.util.Locale.ROOT) + " "), t.id());
			}
		}
		assertSame(TentTypes.DECO_DRAPERY, TentTypes.byId("draperie"), "the street drapery (1.20.0) keeps its short name");
		assertSame(TentTypes.DECO_DRAPERY, TentTypes.byId("deco_draperie"));
		assertSame(TentTypes.MARKET_DRAPERY, TentTypes.byId("tente_draperie"));
		assertSame(TentTypes.CAMP_MERCHANT, TentTypes.byId("marchande"), "the camp's merchant tent (1.25.0) keeps its short name");
		assertSame(TentTypes.MARKET_ARSENAL, TentTypes.byId("arsenal"));
		assertSame(TentTypes.MARKET_LION_PAVILION, TentTypes.byId("lion_pavillon"));
	}

	@Test
	void theMerchantsPlaceIsFreeAndTheTentsFitTheTestPlatform() {
		for (Spec s : SPECS) {
			TentType t = TentTypes.byId(s.id());
			double cx = s.npcX() + 0.5, cz = s.npcZ() + 0.5;
			assertTrue(cx - 0.5 >= t.extent().x0() && cx + 0.5 <= t.extent().x1() && cz - 0.5 >= t.extent().z0() && cz + 0.5 <= t.extent().z1(),
					s.id() + ": the merchant's place is inside the tent");
			for (TentType.Box b : t.colliders()) {
				assertFalse(cx + 0.5 > b.x0() && cx - 0.5 < b.x1() && cz + 0.5 > b.z0() && cz - 0.5 < b.z1() && 2.2 > b.y0() && 0.0 < b.y1(),
						s.id() + ": the merchant's 1 x 1 x 2.2 place is clear of " + b);
			}
			// the in-game test's platform: 29 x 29 blocks of stone, 12 of air above, the anchor at its centre
			for (int f = 0; f < 4; f++) {
				TentType.Box e = t.extent(f);
				assertTrue(e.x0() > -14 && e.x1() < 14 && e.z0() > -14 && e.z1() < 14 && e.y1() < 12, s.id() + " facing " + f + ": " + e);
			}
		}
	}
}
