package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The military tent (camp militaire, 1.24.0, tools/tents/generate_tente_militaire.py): an olive ridge tent about 6 wide
 * x 8 long, ridge at 4.7, open under its front gable (+z). Loaded straight from its JSON (TentType.load), so the check
 * does not depend on where TentTypes lists it: size, cube budget, solid posts, solid canvas walls but an open entrance
 * and a walkable centre aisle (nothing across it up to 2.2), two free 1 x 1 x 2.2 spots for NPCs, a lit lantern, static.
 */
public class CampMilitaireTest {
	private static final String ID = "tente_militaire";
	/** x0, z0, x1, z1 of the NPC spots (as NPC_SPOTS in the generator). */
	private static final double[][] NPC_SPOTS = {{-0.5, -2.7, 0.5, -1.7}, {-0.5, -0.6, 0.5, 0.4}};

	private static TentType tent() {
		return TentType.load(TentType.TENTS, ID, "tente militaire", "Military Tent");
	}

	private static JsonObject model() throws Exception {
		try (var in = CampMilitaireTest.class.getResourceAsStream("/assets/medievalships/models/entity/" + ID + ".bbmodel")) {
			assertNotNull(in, "model of " + ID);
			try (Reader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return JsonParser.parseReader(r).getAsJsonObject();
			}
		}
	}

	@Test
	void loadsToScaleWithItsOwnAtlasAndLight() {
		TentType t = tent();
		assertEquals(TentType.TENTS, t.group());
		assertEquals("models/entity/" + ID + ".bbmodel", t.model());
		assertEquals("textures/entity/" + ID + ".png", t.texture(), "its own atlas");
		TentType.Box e = t.extent();
		assertEquals(0.0, e.y0(), 1e-9, "stands on the ground");
		// the tent itself is ~6.3 x 7.9 (ridge 4.7, ridge-end posts above it); ropes, pegs and the sacks outside add a little
		assertTrue(e.width() > 6.0 && e.width() < 9.0, "width " + e.width());
		assertTrue(e.depth() > 7.0 && e.depth() < 10.0, "depth " + e.depth());
		assertTrue(e.height() > 4.5 && e.height() < 6.2, "height " + e.height());
		assertTrue(t.light() >= 12 && t.light() <= 15, "the lantern lights the tent: " + t.light());
		assertEquals(null, t.muzzle());
		assertTrue(t.particles().isEmpty(), "no particles");
		assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
	}

	@Test
	void postsAndWallsCollideButTheEntranceAndAisleAreOpen() {
		TentType t = tent();
		TentType.Box e = t.extent();
		int posts = 0;
		boolean left = false, right = false, back = false;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
					&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, "inside the extent " + b);
			if (b.height() > 2.0 && b.width() < 0.6 && b.depth() < 0.6) {
				posts++;
			}
			left |= b.x1() < -2.8 && b.depth() > 6.5 && b.height() >= 1.9;
			right |= b.x0() > 2.8 && b.depth() > 6.5 && b.height() >= 1.9;
			back |= b.z1() < -3.4 && b.width() > 5.5 && b.height() >= 1.9;
			// the centre aisle, from the back wall out past the entrance: nothing up to 2.2 high
			boolean aisle = b.x0() < 0.6 && b.x1() > -0.6 && b.z1() > -3.5 && b.z0() < e.z1() && b.y0() < 2.2;
			assertFalse(aisle, "the entrance and the centre aisle are open " + b);
		}
		assertTrue(posts >= 6, "solid posts: " + posts);
		assertTrue(left && right && back, "the canvas side walls and the back wall are solid");
		assertTrue(Merchant4Test.walkIn(t), "a player walks in from the front to a free 1 x 1 x 2.2 spot in the back half");
	}

	@Test
	void twoFreeNpcSpotsWithStandingRoom() {
		TentType t = tent();
		for (double[] s : NPC_SPOTS) {
			assertEquals(1.0, s[2] - s[0], 1e-9);
			assertEquals(1.0, s[3] - s[1], 1e-9);
			for (TentType.Box b : t.colliders()) {
				boolean hit = b.x0() < s[2] && b.x1() > s[0] && b.z0() < s[3] && b.z1() > s[1] && b.y0() < 2.2;
				assertFalse(hit, "NPC spot " + s[0] + "," + s[1] + " is free of " + b);
			}
		}
	}

	@Test
	void modelIsLightStaticAndLit() throws Exception {
		JsonObject m = model();
		JsonArray elements = m.getAsJsonArray("elements");
		assertTrue(elements.size() > 200 && elements.size() <= 700, "cubes " + elements.size());
		int glow = 0;
		for (JsonElement el : elements) {
			if (el.getAsJsonObject().get("name").getAsString().startsWith("glow")) {
				glow++;
			}
		}
		assertTrue(glow >= 1, "the lantern's glass is drawn full bright (" + glow + ")");
		try (var in = CampMilitaireTest.class.getResourceAsStream("/assets/medievalships/models/entity/" + ID + ".bbmodel")) {
			BbModel bb = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(bb.animations.isEmpty(), "a tent has no animation");
			assertTrue(bb.hasBone("detail"), "small things under the bone 'detail' (hidden far away)");
			assertTrue(bb.quadCount() > 1000, "faces " + bb.quadCount());
		}
		TentType t = tent();
		assertNotNull(t.decor());
		InteriorDecor.load(t.decor());
	}
}
