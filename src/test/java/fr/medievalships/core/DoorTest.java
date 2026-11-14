package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The doors of 1.31.0 in pure Java: the ten types, their cells and orientation, the movement and its collisions, the
 * access rules and the logical OR of what asks a door to be open.
 */
class DoorTest {
	private static final double EPS = 1e-9;

	// ------------------------------------------------------------------ the ten doors

	@Test
	void tenDoorsWithTheIdsSizesAndLeavesOfTheBrief() {
		assertEquals(10, DoorTypes.ALL.size());
		String[] small = {"porte_chene", "porte_prison", "porte_vapeur"};
		String[] medium = {"porte_grange", "porte_forteresse", "porte_industrielle", "porte_marchande"};
		String[] large = {"porte_chateau", "porte_vapeur_grande", "porte_entrepot"};
		for (String id : small) {
			DoorType t = DoorTypes.byId(id);
			assertNotNull(t, id);
			assertEquals(2, t.height());
			assertEquals(1, t.width());
			assertEquals(1, t.leaves());
			assertEquals(DoorType.Size.SMALL, t.size());
			assertEquals(DoorTypes.SMALL_TICKS, t.durationTicks());
		}
		for (String id : medium) {
			DoorType t = DoorTypes.byId(id);
			assertNotNull(t, id);
			assertEquals(4, t.height());
			assertEquals(2, t.width());
			assertEquals(2, t.leaves());
			assertEquals(1, t.leafWidth());
			assertEquals(DoorTypes.MEDIUM_TICKS, t.durationTicks());
		}
		for (String id : large) {
			DoorType t = DoorTypes.byId(id);
			assertNotNull(t, id);
			assertEquals(6, t.height());
			assertEquals(4, t.width());
			assertEquals(2, t.leaves());
			assertEquals(2, t.leafWidth());
			assertEquals(DoorTypes.LARGE_TICKS, t.durationTicks());
			assertTrue(t.durationTicks() > DoorTypes.MEDIUM_TICKS, "the great gates are slow");
		}
		Set<String> ids = new HashSet<>();
		for (DoorType t : DoorTypes.ALL) {
			assertTrue(ids.add(t.id()), "unique id " + t.id());
			assertTrue(t.id().matches("[a-z_]+"));
			assertEquals("models/entity/" + t.id() + ".bbmodel", t.model());
			assertEquals("textures/entity/" + t.id() + ".png", t.texture());
			assertEquals("textures/item/" + t.id() + ".png", t.itemTexture());
			assertFalse(t.nameFr().isBlank());
			assertFalse(t.nameEn().isBlank());
			assertTrue(t.hingeX() > 0 && t.hingeX() <= t.width() / 2.0, t.id() + " hinge inside the opening");
		}
		assertEquals(DoorTypes.CASTLE, DoorTypes.byId("medievalships:PORTE_CHATEAU"));
		assertNull(DoorTypes.byId("oak_door"));
		assertNull(DoorTypes.byId(null));
	}

	@Test
	void materialsSteamAndPitch() {
		assertEquals(DoorType.Material.WOOD, DoorTypes.OAK.material());
		assertEquals(DoorType.Material.METAL, DoorTypes.PRISON.material());
		assertEquals(DoorType.Material.STEAM, DoorTypes.STEAM.material());
		assertTrue(DoorTypes.STEAM.steam() && DoorTypes.GREAT_STEAM.steam() && DoorTypes.INDUSTRIAL.steam());
		assertFalse(DoorTypes.OAK.steam() || DoorTypes.CASTLE.steam() || DoorTypes.PRISON.steam());
		assertTrue(DoorTypes.CASTLE.soundPitch() < DoorTypes.BARN.soundPitch() && DoorTypes.BARN.soundPitch() < DoorTypes.OAK.soundPitch(),
				"the bigger, the deeper");
		// the real hinges of the models (measured by the integrator): small 0.40625, great 1.625
		assertEquals(0.40625, DoorTypes.OAK.hingeX(), EPS);
		assertEquals(0.8125, DoorTypes.OAK.leafSpan(), EPS);
		assertEquals(1.625, DoorTypes.CASTLE.hingeX(), EPS);
		assertEquals(1.625, DoorTypes.CASTLE.leafSpan(), EPS);
	}

	@Test
	void badDoorsAreRefused() {
		assertThrows(IllegalArgumentException.class, () -> new DoorType("x", "x", "x", 7, 1, 1, 10, DoorType.Material.WOOD, false, 0.4));
		assertThrows(IllegalArgumentException.class, () -> new DoorType("x", "x", "x", 2, 3, 2, 10, DoorType.Material.WOOD, false, 0.4));
		assertThrows(IllegalArgumentException.class, () -> new DoorType("x", "x", "x", 2, 1, 1, 10, DoorType.Material.WOOD, false, 0.6));
	}

	// ------------------------------------------------------------------ cells and orientation

	@Test
	void frontAndRightOfTheFourFacings() {
		// south, west, north, east
		assertArrayEquals(new int[] {0, 1}, DoorLayout.front(0));
		assertArrayEquals(new int[] {-1, 0}, DoorLayout.front(1));
		assertArrayEquals(new int[] {0, -1}, DoorLayout.front(2));
		assertArrayEquals(new int[] {1, 0}, DoorLayout.front(3));
		// seen from the front, the right: east for a door facing south (the viewer looks north)
		assertArrayEquals(new int[] {1, 0}, DoorLayout.right(0));
		assertArrayEquals(new int[] {0, 1}, DoorLayout.right(1));
		assertArrayEquals(new int[] {-1, 0}, DoorLayout.right(2));
		assertArrayEquals(new int[] {0, -1}, DoorLayout.right(3));
		for (int q = 0; q < 4; q++) {
			int[] f = DoorLayout.front(q), r = DoorLayout.right(q);
			assertEquals(0, f[0] * r[0] + f[1] * r[1], "right is across the front");
			// the model is drawn turned by -90 x q degrees about y: model +z must land on the front, model +x on the right
			double a = Math.toRadians(-90.0 * q);
			assertEquals(f[0], Math.round(Math.sin(a) * 1), "model +z -> front x (q " + q + ")");
			assertEquals(f[1], Math.round(Math.cos(a) * 1), "model +z -> front z (q " + q + ")");
			assertEquals(r[0], Math.round(Math.cos(a)), "model +x -> right x (q " + q + ")");
			assertEquals(r[1], Math.round(-Math.sin(a)), "model +x -> right z (q " + q + ")");
		}
		assertEquals(0, DoorLayout.quarterOf("sud"));
		assertEquals(1, DoorLayout.quarterOf("OUEST"));
		assertEquals(2, DoorLayout.quarterOf("north"));
		assertEquals(3, DoorLayout.quarterOf("est"));
		assertEquals(-1, DoorLayout.quarterOf("haut"));
	}

	@Test
	void theOpeningIsCentredOnTheAimedCell() {
		assertEquals(0, DoorLayout.startColumn(1));
		assertEquals(0, DoorLayout.startColumn(2));
		assertEquals(-1, DoorLayout.startColumn(4));
		// facing south (right = east): a 4-wide gate aimed at x 10 spans x 9..12
		int[] c = DoorLayout.controllerFromTarget(10, 64, 5, 0, 4);
		assertArrayEquals(new int[] {9, 64, 5}, c);
		int[][] cells = DoorLayout.cells(c[0], c[1], c[2], 0, 4, 6);
		assertEquals(24, cells.length);
		int minX = Integer.MAX_VALUE, maxX = Integer.MIN_VALUE, maxY = Integer.MIN_VALUE;
		for (int[] cell : cells) {
			minX = Math.min(minX, cell[0]);
			maxX = Math.max(maxX, cell[0]);
			maxY = Math.max(maxY, cell[1]);
			assertEquals(5, cell[2]);
		}
		assertEquals(9, minX);
		assertEquals(12, maxX);
		assertEquals(69, maxY);
		// a 2-wide door facing north (right = west): the aimed cell and the one to its right (x - 1)
		int[] c2 = DoorLayout.controllerFromTarget(0, 0, 0, 2, 2);
		assertArrayEquals(new int[] {0, 0, 0}, c2);
		assertArrayEquals(new int[] {-1, 3, 0}, DoorLayout.cell(0, 0, 0, 2, 1, 3));
		// facing west (right = south), 4 wide aimed at z 0: z -1..2
		int[] c3 = DoorLayout.controllerFromTarget(0, 0, 0, 1, 4);
		assertArrayEquals(new int[] {0, 0, -1}, c3);
		assertArrayEquals(new int[] {0, 0, 2}, DoorLayout.cell(c3[0], c3[1], c3[2], 1, 3, 0));
	}

	@Test
	void everyCellFindsItsController() {
		for (int q = 0; q < 4; q++) {
			for (DoorType t : DoorTypes.ALL) {
				int[] c = {100, 70, -40};
				Set<String> seen = new HashSet<>();
				for (int[] cell : DoorLayout.cells(c[0], c[1], c[2], q, t.width(), t.height())) {
					assertTrue(seen.add(cell[0] + " " + cell[1] + " " + cell[2]), "distinct cells");
					assertArrayEquals(c, DoorLayout.controllerFromCell(cell[0], cell[1], cell[2], q, cell[3], cell[4]));
				}
				assertEquals(t.cells(), seen.size());
			}
		}
	}

	@Test
	void modelOriginAndWorldBoxes() {
		// a 4-wide gate facing south, controller at x 9: the middle of the opening is x 11 (9..13), z 5.5
		assertEquals(11.0, DoorLayout.originX(9, 0, 4), EPS);
		assertEquals(5.5, DoorLayout.originZ(5, 0, 4), EPS);
		// a small door: the centre of its block
		assertEquals(0.5, DoorLayout.originX(0, 1, 1), EPS);
		assertEquals(0.5, DoorLayout.originZ(0, 1, 1), EPS);
		// facing east (right = north): a 2-wide door's middle is half a block north of the controller's centre
		assertEquals(0.0, DoorLayout.originZ(0, 3, 2), EPS);
		// the model front (+z) is the world front
		double[] p = DoorLayout.toWorld(0, 0, 0, 3, 1, 0, 0, 0.5);
		assertEquals(1.0, p[0], EPS);
		// the opening's box covers its cells exactly
		double[] b = DoorLayout.worldBox(9, 64, 5, 0, 4, -2, 0, -0.5, 2, 6, 0.5);
		assertArrayEquals(new double[] {9, 64, 5, 13, 70, 6}, b, EPS);
		// the volume a closing gate sweeps: the opening plus its leaves' quarter circles behind it (backward), or in front
		double[] back = DoorLayout.sweptWorld(DoorTypes.CASTLE, 9, 64, 5, 0, true);
		assertEquals(5.5 - 1.625, back[2], EPS);
		assertEquals(6.0, back[5], EPS);
		double[] front = DoorLayout.sweptWorld(DoorTypes.CASTLE, 9, 64, 5, 0, false);
		assertEquals(5.0, front[2], EPS);
		assertEquals(5.5 + 1.625, front[5], EPS);
	}

	@Test
	void leavesTurnAwayFromThePlayerByDefault() {
		// model frame: a right-handed rotation about y maps (x, z) to (x cos + z sin, -x sin + z cos)
		for (boolean backward : new boolean[] {true, false}) {
			double al = Math.toRadians(DoorLayout.leafAngle(true, backward, 1.0));
			double ar = Math.toRadians(DoorLayout.leafAngle(false, backward, 1.0));
			// the free edge of the left leaf is to its right (+x of its hinge), of the right leaf to its left
			double zl = -1 * Math.sin(al), zr = 1 * Math.sin(ar);
			if (backward) {
				assertTrue(zl < -0.99 && zr < -0.99, "both leaves swing behind the door (-z)");
			} else {
				assertTrue(zl > 0.99 && zr > 0.99, "both leaves swing in front (+z)");
			}
		}
		assertEquals(0f, DoorLayout.leafAngle(true, true, 0), 1e-6);
		assertEquals(-DoorTypes.CASTLE.hingeX(), DoorLayout.hingeX(DoorTypes.CASTLE, true), EPS);
	}

	// ------------------------------------------------------------------ the movement

	@Test
	void progressFromTargetStartTickAndStartProgress() {
		int d = 20;
		assertEquals(0.0, DoorMotion.progress(true, 100, 0, 100, d), EPS);
		assertEquals(0.5, DoorMotion.progress(true, 100, 0, 110, d), EPS);
		assertEquals(0.525, DoorMotion.progress(true, 100, 0, 110.5, d), EPS); // between two ticks on a client
		assertEquals(1.0, DoorMotion.progress(true, 100, 0, 500, d), EPS);
		// reversing half way: closing from 0.5 takes 10 ticks
		assertEquals(0.25, DoorMotion.progress(false, 200, 0.5, 205, d), EPS);
		assertEquals(0.0, DoorMotion.progress(false, 200, 0.5, 210, d), EPS);
		// a client slightly behind the server's clock never goes backwards
		assertEquals(0.5, DoorMotion.progress(false, 200, 0.5, 198, d), EPS);
		assertTrue(DoorMotion.moving(true, 0.99));
		assertFalse(DoorMotion.moving(true, 1));
		assertFalse(DoorMotion.moving(false, 0));
		assertEquals(10, DoorMotion.ticksLeft(false, 0.5, d));
		assertEquals(0, DoorMotion.ticksLeft(true, 1, d));
	}

	@Test
	void smoothCurve() {
		assertEquals(0, DoorMotion.ease(0), EPS);
		assertEquals(0.5, DoorMotion.ease(0.5), EPS);
		assertEquals(1, DoorMotion.ease(1), EPS);
		assertTrue(DoorMotion.ease(0.1) < 0.1 && DoorMotion.ease(0.9) > 0.9, "slow start, slow end");
		double last = -1;
		for (int i = 0; i <= 100; i++) {
			double e = DoorMotion.ease(i / 100.0);
			assertTrue(e >= last, "monotonic");
			last = e;
		}
		assertEquals(1, DoorMotion.ease(3), EPS);
	}

	@Test
	void solidChronology() {
		for (DoorType type : new DoorType[] {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE}) {
			DoorMotion.Curve c = DoorMotion.curve(type);
			int d = type.durationTicks(), n = type.leaves();
			boolean solid = true; // closed
			// opening: solid until every leaf is half open (the same curve as the drawing)
			for (int t = 0; t <= d; t++) {
				double p = DoorMotion.progress(true, 0, 0, t, d);
				solid = DoorMotion.solidAfter(c, n, solid, true, p);
				assertEquals(DoorMotion.leastOpen(c, n, p) < DoorMotion.HALF, solid, type + " opening at " + p);
			}
			assertFalse(solid);
			// closing: the passage stays free until the leaves are closed and still, their bounce over (the locking is
			// done solid)
			for (int t = 0; t <= d; t++) {
				double p = DoorMotion.progress(false, 100, 1, 100 + t, d);
				solid = DoorMotion.solidAfter(c, n, solid, false, p);
				assertEquals(p <= c.unlock() + 1e-9, solid, type + " closing at " + p);
				if (!solid) {
					assertTrue(p > c.unlock());
				} else {
					for (int leaf = 0; leaf < n; leaf++) {
						assertEquals(0, DoorMotion.leaf(c, n, leaf, false, p), 1e-9, "solid: every leaf is shut");
					}
				}
			}
			assertTrue(solid);
			// a closing that turns back to opening (something in the way) never becomes solid again on the way
			solid = false;
			solid = DoorMotion.solidAfter(c, n, solid, false, 0.5);
			assertFalse(solid);
			solid = DoorMotion.solidAfter(c, n, solid, true, 0.5);
			assertFalse(solid, "reopening from 0.5: still free");
			solid = DoorMotion.solidAfter(c, n, solid, true, 0.9);
			assertFalse(solid);
		}
	}

	@Test
	void movingPartsOnlyMoveWithTheDoor() {
		DoorMotion.Curve c = DoorMotion.curve(DoorTypes.CASTLE);
		assertEquals(0, DoorMotion.gearAngle(0, 1), EPS);
		assertEquals(360, DoorMotion.gearAngle(1, 1), EPS); // a whole turn: at rest the gear looks the same
		assertEquals(720, DoorMotion.gearAngle(1, DoorTypes.CASTLE.gearTurns()), EPS);
		assertEquals(0, DoorMotion.boltOffset(c, true, 0), EPS);
		assertEquals(0.25, DoorMotion.boltOffset(c, true, c.unlock()), EPS);
		assertEquals(0.25, DoorMotion.boltOffset(c, true, 1), EPS);
		assertEquals(0.125, DoorMotion.boltOffset(c, true, c.unlock() / 2), EPS);
		// closing: still out while the leaves move and when they come to rest, back in at the end of the locking
		assertEquals(0.25, DoorMotion.boltOffset(c, false, 0.6), EPS);
		assertEquals(0.25, DoorMotion.boltOffset(c, false, c.unlock()), EPS);
		assertEquals(0, DoorMotion.boltOffset(c, false, 0), EPS);
		assertEquals(0, DoorMotion.pistonOffset(0), EPS);
		assertEquals(0.25, DoorMotion.pistonOffset(1), EPS);
		assertEquals(0.25, DoorMotion.pistonOffset(1.03), EPS, "the rods do not follow the settling past the stop");
	}

	// ------------------------------------------------------------------ access and demands

	@Test
	void accessRules() {
		Set<String> none = Set.of();
		Set<String> tagged = Set.of("donjon_ouvert");
		assertEquals(DoorAccess.Click.OK, DoorAccess.LIBRE.click(true, none, ""));
		assertEquals(DoorAccess.Click.MANUAL_OFF, DoorAccess.LIBRE.click(false, none, ""));
		assertEquals(DoorAccess.Click.LOCKED, DoorAccess.VERROUILLEE.click(true, tagged, ""));
		assertEquals(DoorAccess.Click.LEVER_ONLY, DoorAccess.LEVIER.click(true, none, ""));
		assertEquals(DoorAccess.Click.ADMIN_ONLY, DoorAccess.ADMIN.click(true, tagged, "donjon_ouvert"));
		assertEquals(DoorAccess.Click.QUEST_MISSING, DoorAccess.QUETE.click(true, none, "donjon_ouvert"));
		assertEquals(DoorAccess.Click.OK, DoorAccess.QUETE.click(true, tagged, "donjon_ouvert"));
		assertEquals(DoorAccess.Click.QUEST_MISSING, DoorAccess.QUETE.click(true, tagged, ""));
		assertEquals(DoorAccess.Click.MANUAL_OFF, DoorAccess.QUETE.click(false, tagged, "donjon_ouvert"));
		for (DoorAccess.Click c : DoorAccess.Click.values()) {
			assertEquals(c == DoorAccess.Click.OK, c.message("x") == null);
		}
		// redstone next to the door: not for a locked door nor an admin one; the linked levers: all but admin
		assertTrue(DoorAccess.LIBRE.redstoneAccepted(true));
		assertFalse(DoorAccess.LIBRE.redstoneAccepted(false));
		assertFalse(DoorAccess.VERROUILLEE.redstoneAccepted(true));
		assertTrue(DoorAccess.VERROUILLEE.leversAccepted(true));
		assertTrue(DoorAccess.LEVIER.redstoneAccepted(true));
		assertTrue(DoorAccess.QUETE.redstoneAccepted(true));
		assertFalse(DoorAccess.ADMIN.redstoneAccepted(true));
		assertFalse(DoorAccess.ADMIN.leversAccepted(true));
		assertFalse(DoorAccess.LEVIER.leversAccepted(false));
		assertTrue(DoorAccess.LIBRE.free());
		assertFalse(DoorAccess.QUETE.free());
		assertEquals(DoorAccess.VERROUILLEE, DoorAccess.parse("Verrouillée"));
		assertEquals(DoorAccess.QUETE, DoorAccess.parse("quête"));
		assertEquals(DoorAccess.ADMIN, DoorAccess.parse("admin"));
		assertEquals(DoorAccess.CLE, DoorAccess.parse("clef"));
		assertNull(DoorAccess.parse("porte"));
		for (DoorAccess a : DoorAccess.values()) {
			assertEquals(a, DoorAccess.parse(a.word()));
		}
		assertTrue(DoorAccess.validTag("quete.donjon-1"));
		assertFalse(DoorAccess.validTag("deux mots"));
		assertFalse(DoorAccess.validTag(""));
	}

	@Test
	void theDoorStaysOpenWhileAnythingAsksForIt() {
		DoorDemands d = new DoorDemands();
		long now = 1000;
		assertFalse(d.wanted(now, true, true));
		d.redstone = true;
		assertTrue(d.wanted(now, true, true));
		assertFalse(d.wanted(now, false, true), "redstone ignored");
		assertEquals("la redstone", d.holder(now, true, true));
		d.manual = true;
		d.redstone = false;
		assertTrue(d.wanted(now, false, false), "a hand or a command always counts");
		assertNull(d.holder(now, true, true));
		d.manual = false;
		d.lever = true;
		assertTrue(d.wanted(now, true, true));
		assertFalse(d.wanted(now, true, false));
		d.lever = false;
		d.timedUntil = now + 40;
		assertTrue(d.wanted(now, false, false));
		assertTrue(d.wanted(now + 39, false, false));
		assertFalse(d.wanted(now + 40, false, false), "the timed opening ends");
		// OR: the redstone goes off while a lever still holds it: still open
		d.timedUntil = 0;
		d.redstone = true;
		d.lever = true;
		assertTrue(d.wanted(now, true, true));
		d.redstone = false;
		assertTrue(d.wanted(now, true, true));
		d.lever = false;
		assertFalse(d.wanted(now, true, true));
		d.manual = true;
		d.clear();
		assertFalse(d.wanted(now, true, true));
	}

	// ------------------------------------------------------------------ the model helpers the renderer uses

	private static final String MODEL = """
			{"resolution": {"width": 16, "height": 16},
			 "elements": [
			  {"uuid": "a", "name": "post", "from": [-8, 0, -1], "to": [-6, 32, 1], "faces": {"north": {"uv": [0,0,2,16], "texture": 0}}},
			  {"uuid": "b", "name": "plank", "from": [-6, 0, -1], "to": [6, 32, 1], "faces": {"north": {"uv": [0,0,12,16], "texture": 0}}},
			  {"uuid": "c", "name": "cog", "from": [-1, 15, 1], "to": [1, 17, 2], "faces": {"south": {"uv": [0,0,2,2], "texture": 0}}},
			  {"uuid": "d", "name": "rivet", "from": [0, 1, 1], "to": [1, 2, 2], "faces": {"south": {"uv": [0,0,1,1], "texture": 0}}},
			  {"uuid": "e", "name": "rivet2", "from": [0, 3, 1], "to": [1, 4, 2], "faces": {"south": {"uv": [0,0,1,1], "texture": 0}}}
			 ],
			 "outliner": [
			  {"name": "porte_x", "origin": [0, 0, 0], "children": [
			   {"name": "frame", "origin": [0, 0, 0], "children": ["a", {"name": "detail", "origin": [0, 0, 0], "children": ["d"]}]},
			   {"name": "leaf_l", "origin": [6, 0, 0], "children": ["b",
			     {"name": "gear_a_1", "origin": [0, 16, 0], "children": ["c"]},
			     {"name": "detail", "origin": [0, 0, 0], "children": ["e"]}]}
			  ]}
			 ]}
			""";

	@Test
	void boneHelpersOfTheModel() {
		BbModel m = new BbModel(new StringReader(MODEL));
		BbModel.Bone leaf = m.bonesByName.get("leaf_l");
		BbModel.Bone gear = m.bonesByName.get("gear_a_1");
		assertEquals(leaf, gear.parent());
		assertEquals("porte_x", leaf.parent().name);
		assertNull(leaf.parent().parent());
		// pivots in model-local blocks: x = -bbX / 16
		assertArrayEquals(new double[] {-6 / 16.0, 0, 0}, leaf.originBlocks(), EPS);
		assertArrayEquals(new double[] {0, 1, 0}, gear.originBlocks(), EPS);
		// two bones named "detail": hideAll hides both
		int all = count(m, m.newPose(), null);
		BbModel.Pose pose = m.newPose();
		m.hideAll(pose, "detail");
		assertEquals(all - 2, count(m, pose, null));
		// the leaf drawn alone, its gear hidden (drawn on its own, turning)
		pose = m.newPose();
		m.hide(pose, gear);
		assertEquals(2, count(m, pose, leaf)); // the plank and its rivet
		pose = m.newPose();
		assertEquals(1, count(m, pose, gear));
		// translate: sets an extra position on a bone (like rotate), unknown names ignored
		pose = m.newPose();
		m.translate(pose, "gear_a_1", 0, 16, 0);
		m.translate(pose, "nothing", 1, 1, 1);
		List<float[]> moved = new ArrayList<>();
		m.renderSubtree(pose, "gear_a_1", (p, uv, n, glow) -> moved.add(p.clone()));
		List<float[]> still = new ArrayList<>();
		m.renderSubtree(m.newPose(), "gear_a_1", (p, uv, n, glow) -> still.add(p.clone()));
		assertEquals(1, moved.size());
		assertEquals(still.get(0)[1] + 1.0, moved.get(0)[1], 1e-5, "16 px up = 1 block up");
	}

	/** The ten models of the generators: their leaves' pivots are the hinges the server sweeps with (DoorType#hingeX). */
	@Test
	void theModelsHingesAreTheServersHinges() throws Exception {
		for (DoorType t : DoorTypes.ALL) {
			java.nio.file.Path path = java.nio.file.Path.of("src/main/resources/assets/medievalships", t.model());
			if (!java.nio.file.Files.exists(path)) {
				continue; // a model not generated yet: drawn by nothing, checked once it exists
			}
			BbModel m;
			try (java.io.Reader r = java.nio.file.Files.newBufferedReader(path, java.nio.charset.StandardCharsets.UTF_8)) {
				m = new BbModel(r);
			}
			assertTrue(m.hasBone("frame"), t.id() + " has a frame");
			double[] l = m.origin("leaf_l");
			assertNotNull(l, t.id() + " has leaf_l");
			assertEquals(-t.hingeX(), l[0], 1e-3, t.id() + " leaf_l hinge");
			assertEquals(0, l[2], 0.05, t.id() + " leaf_l hinge in the middle of the thickness");
			double[] r = m.origin("leaf_r");
			if (t.leaves() == 2) {
				assertNotNull(r, t.id() + " has leaf_r");
				assertEquals(t.hingeX(), r[0], 1e-3, t.id() + " leaf_r hinge");
			} else {
				assertNull(r, t.id() + " has one leaf only");
			}
		}
	}

	private static int count(BbModel m, BbModel.Pose pose, BbModel.Bone part) {
		int[] n = {0};
		if (part == null) {
			m.render(pose, (p, uv, nn, glow) -> n[0]++);
		} else {
			m.renderPart(pose, part, (p, uv, nn, glow) -> n[0]++);
		}
		return n[0];
	}
}
