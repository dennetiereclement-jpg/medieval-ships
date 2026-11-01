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
 * The model of the fishmonger's stall (1.17.0: tente_poissonnier; tools/merchant/generate_tente_poissonnier.py +
 * props_m9.py, the longer gabled stall of merchantlib.stall): its JSON has the model, texture, extent and collision
 * boxes, no permanent particles; four solid corner posts, a solid counter, a free place of 1 x 1 x 2.2 blocks behind
 * it for the merchant NPC, the front before the counter walkable, a way in on the right side; the .bbmodel loads
 * static and light, with a "detail" bone, the gabled roof, two banners (one per front post), the lit lanterns, no flags
 * and no rug, and the fish stall's goods (hanging fish, the net, the ice display, the lobster trap, the anchor, crabs,
 * lobsters, seaweed, the cutting board's fillet and cleaver); its mod furniture list exists.
 */
public class MerchantModelsM9Test {
	private static final double EPS = 1e-6;
	private static final String ID = "tente_poissonnier";

	private static JsonObject json(String path) throws Exception {
		try (InputStream in = MerchantModelsM9Test.class.getResourceAsStream(path)) {
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
		JsonObject j = json("/assets/medievalships/tents/" + ID + ".json");
		assertEquals("models/entity/" + ID + ".bbmodel", j.get("model").getAsString());
		assertEquals("textures/entity/" + ID + ".png", j.get("texture").getAsString());
		assertFalse(j.has("particles"), "no permanent particles");
		double[] e = box(j.get("extent"));
		assertEquals(0.0, e[1], EPS, "stands on the ground");
		double w = e[3] - e[0], h = e[4] - e[1], d = e[5] - e[2];
		// the longer stall: 6.6 blocks between the posts, the barrels, the anchor and the trap outside them
		assertTrue(w > 8.0 && w < 11.0 && d > 5.5 && d < 8.0 && h > 4.5 && h < 7.0, "size " + w + " x " + h + " x " + d);
		List<double[]> cs = new ArrayList<>();
		int posts = 0;
		for (JsonElement c : j.getAsJsonArray("colliders")) {
			double[] b = box(c);
			assertTrue(b[0] < b[3] && b[1] < b[4] && b[2] < b[5], "box " + c);
			assertTrue(b[0] >= e[0] - 0.06 && b[3] <= e[3] + 0.06 && b[2] >= e[2] - 0.06 && b[5] <= e[5] + 0.06 && b[1] >= -EPS
					&& b[4] <= e[4] + 0.06, "inside the extent " + c);
			if (b[4] - b[1] > 3.0 && b[3] - b[0] < 0.6 && b[5] - b[2] < 0.6) {
				posts++;
			}
			cs.add(b);
		}
		assertTrue(cs.size() >= 15, "collision boxes " + cs.size());
		assertTrue(posts >= 4, "four solid corner posts (" + posts + ")");
		// the long counter along the front (x -2.4 .. 2.45, z 1.35 .. 2.05) is solid
		assertTrue(hits(cs, 0.0, 0.5, 1.5, 1.5, 0.9, 1.9), "the counter is solid");
		assertTrue(hits(cs, -2.0, 0.5, 1.5, -1.0, 0.9, 1.9), "the counter under the ice display is solid");
		// the merchant's place behind it is free, the front before the counter is walkable, the way in on the right side
		assertFalse(hits(cs, 0.6, 0.0, 0.3, 1.6, 2.2, 1.3), "a free place of 1 x 1 x 2.2 blocks behind the counter");
		assertFalse(hits(cs, -0.3, 0.0, 2.2, 1.8, 2.0, 4.5), "the front before the counter is walkable");
		assertFalse(hits(cs, 2.6, 0.0, -0.3, 4.4, 2.0, 1.4), "the way in on the right side is free");
		assertFalse(hits(cs, -2.8, 0.0, -0.3, 2.8, 2.0, 1.2), "inside, behind the counter, the floor is free");
		assertTrue(j.has("decor") && !j.get("decor").isJsonNull(), "mod furniture");
		JsonObject decor = json(j.get("decor").getAsString());
		JsonArray blocks = decor.getAsJsonArray("blocks");
		assertTrue(blocks.size() >= 3, "mod blocks");
		boolean board = false;
		for (JsonElement b : blocks) {
			board |= b.getAsJsonObject().get("block").getAsString().equals("farmersdelight:cutting_board");
		}
		assertTrue(board, "the cutting board (Farmer's Delight)");
	}

	@Test
	void modelLoadsStaticLightGabledWithTheFish() throws Exception {
		String path = "/assets/medievalships/models/entity/" + ID + ".bbmodel";
		try (InputStream in = MerchantModelsM9Test.class.getResourceAsStream(path)) {
			assertNotNull(in, path);
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.quadCount() > 1000 && m.quadCount() < 900 * 6, "faces " + m.quadCount());
			assertTrue(m.animations.isEmpty(), "static");
			assertTrue(m.bonesByName.containsKey("detail"), "detail bone");
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
		assertTrue(names.size() <= 900, "cube budget " + names.size());
		assertTrue(glow >= 2, "lit lanterns " + glow);
		// the gabled stall: two roof slopes, two gable ends, the valance on the four sides, posts, TWO banners, the rail
		for (String part : new String[] {"roof_front_", "roof_back_", "gable_0", "gable_1", "valance_0_", "valance_1_", "valance_2_",
				"valance_3_", "ridge_pole", "post_0_cap", "post_3_cap", "banner_front_l_", "banner_front_r_", "banner_rod_l", "banner_rod_r",
				"counter_front_top", "hang_rail", "glow_lamp_0", "glow_lamp_1", "post_rope_0"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), "element " + part);
		}
		assertFalse(names.stream().anyMatch(n -> n.startsWith("flag") || n.startsWith("pennant") || n.startsWith("rug")),
				"no flags, pennants or rug (as on the picture)");
		// the fish stall's goods
		for (String part : new String[] {"net_0_", "net_1_", "net_2_", "ice", "ice_cube_", "ice_salmon_0", "ice_fish_2", "tray_front",
				"sign_0", "fillet", "cleaver_blade", "trap_dome_", "trap_hoop_", "trap_lobster", "anchor_shank", "anchor_stock", "anchor_fluke_0",
				"anchor_fluke_1", "crab_0", "lob_0", "kelp_", "crate_fl_content", "crate_crabs_content", "barrel_fl_content", "jar_",
				"shelf_fish_"}) {
			assertTrue(names.stream().anyMatch(n -> n.startsWith(part)), "element " + part);
		}
		long hanging = names.stream().filter(n -> n.matches("hfish_\\d+")).count();
		assertTrue(hanging >= 7, "fish hanging on chains " + hanging);
		long kelp = names.stream().filter(n -> n.startsWith("kelp_")).count();
		assertTrue(kelp >= 10, "seaweed strips " + kelp);
		assertNotNull(MerchantModelsM9Test.class.getResource("/assets/medievalships/textures/item/" + ID + ".png"), "icon");
		assertNotNull(MerchantModelsM9Test.class.getResource("/assets/medievalships/textures/entity/" + ID + ".png"), "atlas");
	}
}
