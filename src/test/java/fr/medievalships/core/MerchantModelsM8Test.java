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
 * The model of the baker's stall (1.17.0: tente_boulanger; tools/merchant/generate_tente_boulanger.py + props_m8.py,
 * the gabled stall of merchantlib.stall with a banner on each front post): its JSON has the model, texture, extent,
 * collision boxes and at most a rare wisp of smoke at the oven; four solid corner posts, the solid counter and oven, a
 * free place of 1 x 1 x 2.2 blocks between them for the merchant NPC, the front before the counter walkable; the
 * .bbmodel loads static and light, with the gabled roof, the two banners, no flags and no rug, the lit lanterns and
 * oven fire, and the baker's goods; its mod furniture list exists.
 */
public class MerchantModelsM8Test {
	private static final double EPS = 1e-6;
	private static final String ID = "tente_boulanger";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM8Test.class.getResourceAsStream(path)) {
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
	void jsonExtentPostsCounterOvenMerchantPlaceFrontAndDecor() throws Exception {
		JsonObject j = json("/assets/medievalships/tents/" + ID + ".json");
		assertEquals("models/entity/" + ID + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/" + ID + ".png", j.get("texture").getAsString());
		double[] e = box(j.get("extent"));
		assertEquals(0.0, e[1], EPS, ID + " stands on the ground");
		double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
		assertTrue(w > 6.0 && w < 9.0 && d > 5.5 && d < 8.0 && h > 4.5 && h < 7.0, ID + " size " + w + " x " + h + " x " + d);
		List<double[]> cs = new ArrayList<>();
		int posts = 0;
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			double[] b = box(c);
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], ID + " box " + c);
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, ID + " inside the extent " + c);
			if (b[4] - b[1] > 3.0 && b[3] - b[0] < 0.6 && b[5] - b[2] < 0.6) {
				posts++;
			}
			cs.add(b);
		}
		assertTrue(cs.size() >= 10, ID + " collision boxes " + cs.size());
		assertTrue(posts >= 4, ID + " four solid corner posts (" + posts + ")");
		// the long counter along the front (x -0.35 .. 2.3, z 1.35 .. 2.05) and the oven at the back are solid
		assertTrue(hits(cs, 0.0, 0.5, 1.5, 1.5, 0.9, 1.9), ID + " the counter is solid");
		assertTrue(hits(cs, -0.5, 0.5, -2.0, 0.5, 2.0, -1.5), ID + " the oven is solid");
		// the merchant's place between them is free, the way in at the left of the counter, the front walkable
		assertFalse(hits(cs, -0.5, 0.0, -0.9, 0.5, 2.2, 0.1), ID + " a free place of 1 x 1 x 2.2 blocks behind the counter");
		assertFalse(hits(cs, -1.1, 0.0, 1.0, -0.45, 1.8, 2.3), ID + " the way in between the low table and the counter");
		assertFalse(hits(cs, -0.3, 0.0, 2.2, 1.8, 2.0, 4.5), ID + " the front before the counter is walkable");
		// a rare wisp of smoke from the oven at most
		if (j.has("particles")) {
			JsonArray ps = j.getAsJsonArray("particles");
			assertTrue(ps.size() <= 1, ID + " one particle source at most");
			for (JsonElement p : ps) {
				assertTrue(p.getAsJsonObject().get("chance").getAsDouble() <= 0.15, ID + " rare smoke");
			}
		}
		assertTrue(j.has("decor") && !j.get("decor").isJsonNull(), ID + " mod furniture");
		JsonObject decor = json(j.get("decor").getAsString());
		List<String> blocks = new ArrayList<>();
		for (JsonElement b : decor.getAsJsonArray("blocks")) {
			blocks.add(b.getAsJsonObject().get("block").getAsString());
		}
		assertTrue(blocks.size() >= 5, ID + " mod blocks " + blocks);
		for (String b : new String[] {"farmersdelight:sweet_berry_cheesecake", "landsoficaria:strawberry_cake", "farmersdelight:rice_bag",
				"furnish:spruce_crate"}) {
			assertTrue(blocks.contains(b), ID + " mod block " + b);
		}
	}

	@Test
	void modelLoadsStaticLightGabledWithTheBakersGoods() throws Exception {
		String path = "/assets/medievalships/models/entity/" + ID + ".bbmodel";
		try (InputStream in = MerchantModelsM8Test.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 1000 && m.quadCount() < 900 * 6, ID + " faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), ID + " static");
			assertTrue(m.bonesByName.containsKey("detail"), ID + " detail bone");
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
		assertTrue(names.size() <= 900, ID + " cube budget " + names.size());
		assertTrue(glow >= 6, ID + " lit elements (lanterns, the oven's fire and loaves) " + glow);
		// the gabled stall with a banner on each front post
		for (String part : new String[] {"roof_front_", "roof_back_", "gable_0", "gable_1", "valance_0_", "valance_3_", "ridge_pole",
				"post_0_cap", "post_1_cap", "banner_front_l_", "banner_front_r_", "banner_rod_l", "banner_rod_r", "counter_front_top",
				"hang_rail"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), ID + " element " + part);
		}
		assertFalse(names.stream().anyMatch(n -> n.startsWith("flag") || n.startsWith("pennant") || n.startsWith("rug")),
				ID + ": no flags, pennants or rug (as on the picture)");
		// the baker's goods: the oven and its fire, loaves, buns, baguettes, flour sacks, wheat, garlic, the peel, the cloth
		for (String part : new String[] {"oven_plinth", "oven_crown", "oven_vous_4", "oven_hood_0", "oven_flue", "glow_oven_fire",
				"glow_oven_loaf_0", "loaf_0", "bun_0", "loaf_long_c", "shelf_loaf_", "baguette_0", "flour_0", "flour_1_heap", "wheat_sack_ears_",
				"sheaf_", "garlic_", "peel_blade", "jar_0", "cloth_front", "tray_buns_", "barrel_l0", "basket_bag"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), ID + " element " + part);
		}
		assertNotNull(MerchantModelsM8Test.class.getResource("/assets/medievalships/textures/item/" + ID + ".png"), ID + " icon");
		assertNotNull(MerchantModelsM8Test.class.getResource("/assets/medievalships/textures/entity/" + ID + ".png"), ID + " atlas");
	}
}
