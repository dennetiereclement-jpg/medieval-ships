package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The military command tent (camp militaire, 1.24.0): tents/tente_commandement.json read directly through
 * {@link TentType#load} (independent of its registration in {@link TentTypes}), written by
 * tools/tents/generate_tente_commandement.py. A big olive marquee (posts 9.8 x 11.8 blocks, ridge 6.9) with guy ropes,
 * anchor stones and the camp furniture outside; its posts and walls collide, the entrance is open, the aisle from the
 * entrance to the strategy table is walkable, four or more 1 x 1 x 2.2 spots inside are free for NPCs.
 */
public class CampCommandementTest {
	private static final String ID = "tente_commandement";
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");
	/** The free NPC spots inside (x0, z0 of a 1 x 1 block square, 2.2 high), as the generator's NPC_SPOTS. */
	private static final double[][] NPC_SPOTS = {{-3.5, 0.0}, {2.5, 0.0}, {-3.5, 2.5}, {2.5, 2.5}, {-0.5, -1.2}};
	private static final double HW = 4.9, HD = 5.9, DOOR = 2.2;

	private static TentType tent() {
		return TentType.load(ID, "tente de commandement militaire", "Military Command Tent");
	}

	@Test
	void loadsAsATentWithItsOwnAtlasAndLight() {
		TentType t = tent();
		assertEquals(ID, t.id());
		assertEquals(TentType.TENTS, t.group());
		assertFalse(t.isCart() || t.isWorkshop() || t.isCannon() || t.isTraining() || t.isDecoration());
		assertEquals("models/entity/" + ID + ".bbmodel", t.model());
		assertEquals("textures/entity/" + ID + ".png", t.texture(), "its own atlas");
		assertEquals("/assets/medievalships/interiors/" + ID + "_decor.json", t.decor());
		assertTrue(t.light() >= 12 && t.light() <= 15, "a lit tent: light " + t.light());
		assertEquals(null, t.muzzle());
		assertTrue(t.particles().isEmpty() && t.seats().isEmpty() && !t.hasTargets(), "static: no particles, seats or targets");
		for (String f : new String[] {"tents/" + ID + ".json", t.model(), t.texture(), "textures/item/" + ID + ".png",
				"interiors/" + ID + "_decor.json"}) {
			assertTrue(Files.isRegularFile(ASSETS.resolve(f)), f);
		}
		assertTrue(Files.isRegularFile(Path.of("blockbench/" + ID + ".bbmodel")), "the Blockbench copy");
		InteriorDecor.load(t.decor());
	}

	@Test
	void extentToScale() {
		TentType.Box e = tent().extent();
		assertEquals(0.0, e.y0(), 1e-9, "stands on the ground");
		// the marquee ~10.7 x 12.5 (cloth), plus the guy ropes, anchor stones and the camp furniture outside
		assertTrue(e.width() > 10.5 && e.width() < 14.0, "width " + e.width());
		assertTrue(e.depth() > 12.5 && e.depth() < 16.0, "depth " + e.depth());
		assertTrue(e.height() > 7.0 && e.height() < 9.5, "height (ridge 6.9, flag pole above) " + e.height());
		assertTrue(e.z1() > HD + 1.5, "the camp table and crates stand in front of the entrance");
	}

	@Test
	void postsAndWallsCollideTheEntranceIsOpenTheAisleWalkable() {
		TentType t = tent();
		TentType.Box e = t.extent();
		int posts = 0;
		boolean left = false, right = false, back = false, frontLeft = false, frontRight = false;
		for (TentType.Box b : t.colliders()) {
			assertTrue(b.x0() >= e.x0() - 0.05 && b.x1() <= e.x1() + 0.05 && b.z0() >= e.z0() - 0.05 && b.z1() <= e.z1() + 0.05
					&& b.y0() >= 0.0 && b.y1() <= e.y1() + 0.05, "inside the extent " + b);
			if (b.height() > 2.5 && b.width() < 0.6 && b.depth() < 0.6) {
				posts++;
			}
			if (b.height() >= 3.0 && b.depth() > 2 * HD - 0.5 && b.width() < 0.5) {
				left |= b.x1() < -HW + 0.3;
				right |= b.x0() > HW - 0.3;
			}
			if (b.height() >= 3.0 && b.width() > 2 * HW - 0.5 && b.depth() < 0.5 && b.z1() < -HD + 0.3) {
				back = true;
			}
			if (b.height() >= 3.0 && b.depth() < 0.5 && b.z0() > HD - 0.3 && b.width() > 2.0) {
				frontLeft |= b.x1() <= -DOOR + 0.01;
				frontRight |= b.x0() >= DOOR - 0.01;
			}
			// the entrance: nothing solid across the opening up to 2.2 blocks high
			boolean inDoor = b.x0() < 1.6 && b.x1() > -1.6 && b.z0() < HD + 0.4 && b.z1() > HD - 0.4 && b.y0() < 2.2;
			assertFalse(inDoor, "the entrance is open " + b);
			// the aisle from before the entrance to the strategy table (x 0.0..0.8, z -1.3..HD + 1.6)
			boolean inAisle = b.x0() < 0.8 && b.x1() > 0.0 && b.z0() < HD + 1.6 && b.z1() > -1.3 && b.y0() < 2.2;
			assertFalse(inAisle, "the aisle is walkable " + b);
		}
		assertTrue(posts >= 10, "corner, side and entrance posts collide (" + posts + ")");
		assertTrue(left && right && back && frontLeft && frontRight, "the canvas walls collide where solid");
		assertEquals(t.colliders().size(), t.colliders(TentType.EAST).size());
	}

	@Test
	void freeSpotsForNpcs() {
		TentType t = tent();
		int free = 0;
		for (double[] s : NPC_SPOTS) {
			assertTrue(s[0] > -HW + 0.2 && s[0] + 1.0 < HW - 0.2 && s[1] > -HD + 0.2 && s[1] + 1.0 < HD - 0.2, "inside the tent");
			boolean ok = true;
			for (TentType.Box b : t.colliders()) {
				if (b.x0() < s[0] + 1.0 && b.x1() > s[0] && b.z0() < s[1] + 1.0 && b.z1() > s[1] && b.y0() < 2.2) {
					ok = false;
				}
			}
			assertTrue(ok, "free NPC spot at " + s[0] + ", " + s[1]);
			free++;
		}
		assertTrue(free >= 4, ">= 4 free spots of 1 x 1 x 2.2 inside");
		assertTrue(Merchant2Test.freeSpot(t), "the merchant tents' free-spot check holds too");
	}

	@Test
	void modelStaticLightAndGlowingLanterns() throws Exception {
		TentType t = tent();
		JsonObject json;
		try (InputStream in = CampCommandementTest.class.getResourceAsStream("/assets/medievalships/" + t.model())) {
			assertNotNull(in, "model " + t.model());
			BbModel m = new BbModel(new InputStreamReader(in, StandardCharsets.UTF_8));
			assertTrue(m.animations.isEmpty(), "a tent has no animation");
			assertTrue(m.hasBone("detail"), "small things under the bone \"detail\" (hidden far away)");
			assertTrue(m.quadCount() > 1500, "faces " + m.quadCount());
		}
		try (Reader r = Files.newBufferedReader(ASSETS.resolve(t.model()), StandardCharsets.UTF_8)) {
			json = JsonParser.parseReader(r).getAsJsonObject();
		}
		int cubes = json.getAsJsonArray("elements").size();
		assertTrue(cubes >= 400 && cubes <= 1200, "a light model: " + cubes + " cubes");
		int glow = 0;
		for (JsonElement el : json.getAsJsonArray("elements")) {
			if (el.getAsJsonObject().get("name").getAsString().startsWith("glow")) {
				glow++;
			}
		}
		assertTrue(glow >= 4, "the lanterns glow (two at the entrance, the hanging one, the table's): " + glow);
	}
}
