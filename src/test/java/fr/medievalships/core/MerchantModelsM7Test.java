package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The models of the poison merchant's and the butcher's stalls (1.16.0: tente_poison, tente_boucher;
 * tools/merchant/generate_tente_poison.py, generate_tente_boucher.py + props_m7.py, the gabled stall of
 * merchantlib.stall): their JSON has the model, texture, extent and collision boxes; four solid corner posts, a solid
 * counter, a free place of 1 x 1 x 2.2 blocks behind it for the merchant NPC, the front before the counter walkable;
 * the .bbmodel loads static and light, with a "detail" bone, the gabled roof (two slopes, two gable ends, the valance
 * all round), the banner, no flags and no rug, lit parts (lanterns; the poison's cauldron and potions) and each
 * stall's own goods; their mod furniture list exists.
 */
public class MerchantModelsM7Test {
	private static final double EPS = 1e-6;
	private static final List<String> IDS = List.of("tente_poison", "tente_boucher");

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM7Test.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}

	private static double[] box(JsonElement e) {
		JsonArray a = e.getAsJsonArray();
		assertEquals(6, a.size());
		double[] b = new double[6];
		for (int i = 0; i < 6; i++) {
			b[i] = a.get(i).getAsDouble();
		}
		return b;
	}

	private static boolean hits(List<double[]> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		for (double[] b : boxes) {
			if (b[0] < x1 && b[3] > x0 && b[1] < y1 && b[4] > y0 && b[2] < z1 && b[5] > z0) {
				return true;
			}
		}
		return false;
	}

	@Test
	void jsonExtentPostsCounterMerchantPlaceFrontAndDecor() throws Exception {
		for (String id : IDS) {
			JsonObject j = json("/assets/medievalships/tents/" + id + ".json");
			assertEquals("models/entity/" + id + ".bbmodel", j.get("model").getAsString());
			assertEquals("textures/entity/" + id + ".png", j.get("texture").getAsString());
			assertFalse(j.has("particles"), id + ": no permanent particles");
			double[] e = box(j.get("extent"));
			assertEquals(0.0, e[1], EPS, id + " stands on the ground");
			double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
			assertTrue(w > 6.0 && w < 9.0 && d > 5.5 && d < 8.0 && h > 4.5 && h < 7.0, id + " size " + w + " x " + h + " x " + d);
			List<double[]> cs = new ArrayList<>();
			int posts = 0;
			for (JsonElement c : j.getAsJsonArray("colliders")) {
				double[] b = box(c);
				assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], id + " box " + c);
				assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
						&& b[4] <= e[4] + 0.06, id + " inside the extent " + c);
				if (b[4] - b[1] > 3.0 && b[3] - b[0] < 0.6 && b[5] - b[2] < 0.6) {
					posts++;
				}
				cs.add(b);
			}
			assertTrue(cs.size() >= 10, id + " collision boxes " + cs.size());
			assertTrue(posts >= 4, id + " four solid corner posts (" + posts + ")");
			// the long counter along the front (x -0.6 .. 2.3, z 1.35 .. 2.05) is solid
			assertTrue(hits(cs, 0.0, 0.5, 1.5, 1.5, 0.9, 1.9), id + " the counter is solid");
			// the merchant's place behind it is free, and the front before the counter is walkable
			assertFalse(hits(cs, 0.6, 0.0, 0.3, 1.6, 2.2, 1.3), id + " a free place of 1 x 1 x 2.2 blocks behind the counter");
			assertFalse(hits(cs, -0.3, 0.0, 2.2, 1.8, 2.0, 4.5), id + " the front before the counter is walkable");
			assertTrue(j.has("decor") && !j.get("decor").isJsonNull(), id + " mod furniture");
			JsonObject decor = json(j.get("decor").getAsString());
			assertTrue(decor.getAsJsonArray("blocks").size() >= 3, id + " mod blocks");
		}
	}

	@Test
	void modelsLoadStaticLightGabledWithTheirGoods() throws Exception {
		for (String id : IDS) {
			String path = "/assets/medievalships/models/entity/" + id + ".bbmodel";
			try (InputStream in = MerchantModelsM7Test.class.getResourceAsStream(path)) {
				assertNotNull(in, path);
				BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
				assertTrue(m.quadCount() > 1000 && m.quadCount() < 900 * 6, id + " faces " + m.quadCount());
				assertTrue(m.animations.isEmpty(), id + " static");
				assertTrue(m.bonesByName.containsKey("detail"), id + " detail bone");
			}
			JsonObject model = json(path);
			List<String> names = new ArrayList<>();
			int glow = 0;
			for (JsonElement el : model.getAsJsonArray("elements")) {
				String n = el.getAsJsonObject().get("name").getAsString();
				names.add(n);
				if (n.startsWith("glow")) {
					glow++;
				}
			}
			assertTrue(names.size() <= 900, id + " cube budget " + names.size());
			assertTrue(glow >= 2, id + " lit elements " + glow);
			// the gabled stall: two roof slopes, two gable ends, the valance on the four sides, posts, the banner
			for (String part : new String[] {"roof_front_", "roof_back_", "gable_0", "gable_1", "valance_0_", "valance_1_", "valance_2_",
					"valance_3_", "ridge_pole", "post_0_cap", "post_3_cap", "banner_front_", "banner_rod", "counter_front_top", "hang_rail"}) {
				assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), id + " element " + part);
			}
			assertFalse(names.stream().anyMatch(n -> n.startsWith("flag") || n.startsWith("pennant") || n.startsWith("rug")),
					id + ": no flags, pennants or rug (as on the picture)");
			assertNotNull(MerchantModelsM7Test.class.getResource("/assets/medievalships/textures/item/" + id + ".png"), id + " icon");
			assertNotNull(MerchantModelsM7Test.class.getResource("/assets/medievalships/textures/entity/" + id + ".png"), id + " atlas");
			if (id.equals("tente_poison")) {
				for (String part : new String[] {"glow_cauldron_content", "glow_foam", "glow_cauldron_fumes", "runner_front", "c_skull",
						"herbs_rail_", "shelves_board_"}) {
					assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), id + " element " + part);
				}
				long potions = names.stream().filter(n -> n.startsWith("glow_shelf_")).count();
				assertTrue(potions >= 20, id + " lit potions on the shelves " + potions);
			} else {
				for (String part : new String[] {"ham_front_", "sausages_0_", "sausages_2_", "pork_side", "chop_block", "chop_cleaver_blade",
						"cloth_front", "steak_0", "crate_steaks_", "barrel_meat_", "knives_board"}) {
					assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), id + " element " + part);
				}
			}
		}
	}
}
