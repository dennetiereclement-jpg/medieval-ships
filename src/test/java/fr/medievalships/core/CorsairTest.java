package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The Old Corsair: hull shape (same numbers as tools/corsair_shape.py), dimensions, interior grid
 * (the main deck, the quarterdeck, the captain's cabin, the lower deck rooms, the hold below the
 * waterline, the stairs between them, the doors), the seats and the model.
 */
class CorsairTest {
	private static final ShipType T = Ships.OLD_CORSAIR;
	private static final ShipGeometry G = T.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final InteriorGrid.State OPEN = new InteriorGrid.State(0xFFFFFFFFL, 0f);
	private static final double M = CorsairLayout.MAIN_DECK_Y, L = CorsairLayout.LOWER_FLOOR_Y, H = CorsairLayout.HOLD_FLOOR_Y,
			Q = CorsairLayout.QUARTERDECK_Y, C = CorsairLayout.CABIN_FLOOR_Y;

	/** Values printed by {@code python3 tools/corsair_shape.py}: z, half width, rail, keel, bottom at 2 blocks out. */
	@Test
	void matchesShapeGenerator() {
		double[][] rows = {
				{-21.0, 3.981362, Double.NaN, -1.2, -1.017191},
				{-13.0, 4.863788, 5.704445, -2.878091, -2.615096},
				{0.0, 5.0, 5.6, -3.4, -3.097778},
				{11.5, 4.589544, 6.044581, -3.038708, -2.744444},
				{19.0, 2.601701, 7.413457, -1.770608, -1.029205}};
		HullShape h = T.hull();
		for (double[] r : rows) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			if (!Double.isNaN(r[2])) {
				assertEquals(r[2], h.railY(r[0]), 1e-5, "rail at " + r[0]);
			}
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], h.bottomY(r[0], 2.0), 1e-5, "bottom at " + r[0]);
		}
	}

	@Test
	void dimensionsAndRegistration() {
		assertTrue(CorsairLayout.FORE_MAST_Z > 0 && CorsairLayout.MAIN_MAST_Z < 0, "fore mast forward, main mast aft of the middle");
		assertTrue(CorsairLayout.MAIN_MAST_TOP >= CorsairLayout.FORE_MAST_TOP, "the main mast is the tallest");
		assertEquals(T, Ships.byId("old_corsair"));
		assertTrue(Ships.ALL.contains(T));
		assertNotNull(GRID);
		assertNotNull(G.decor());
		assertFalse(G.submarine());
		assertFalse(G.flying());
		assertEquals(42.0, 2 * CorsairLayout.HALF_LENGTH, 1e-9, "hull length");
		double overall = CorsairLayout.BOWSPRIT_TIP[2] - CorsairLayout.TRANSOM_Z;
		assertTrue(overall > 50 && overall < 54, "length with the bowsprit " + overall);
		assertEquals(10.0, 2 * CorsairLayout.MAX_HALF_WIDTH, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 37 && height < 39.5, "height from the keel to the main masthead " + height);
		double hull = T.hull().railY(0) - G.lowestY();
		assertTrue(hull > 8.5 && hull < 9.5, "hull height " + hull);
		assertTrue(G.boundingRadius() > CorsairLayout.BOWSPRIT_TIP[2]);
		assertNotNull(T.defaults().get());
		assertTrue(T.defaults().get().dive == null && T.defaults().get().flight == null, "a sailing ship");
		assertTrue(T.defaults().get().maxTurnRate < Ships.GALLEY.defaults().get().maxTurnRate, "wide turns");
	}

	private static double floorUnder(double x, double y, double z, InteriorGrid.State s) {
		double[] top = {Double.NEGATIVE_INFINITY};
		G.collectBoxes(ORIGIN, s, x - 0.3, y - 3, z - 0.3, x + 0.3, y + 0.01, z + 0.3, (a, b, c, d, e, f) -> {
			if (e <= y + 0.01 && a < x + 0.3 && d > x - 0.3 && c < z + 0.3 && f > z - 0.3) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
	}

	private static boolean fits(double x, double y, double z, InteriorGrid.State s) {
		boolean[] hit = {false};
		G.collectBoxes(ORIGIN, s, x - 0.3, y + 0.01, z - 0.3, x + 0.3, y + 1.8, z + 0.3, (a, b, c, d, e, f) -> {
			if (a < x + 0.3 && d > x - 0.3 && b < y + 1.8 && e > y + 0.01 && c < z + 0.3 && f > z - 0.3) {
				hit[0] = true;
			}
		});
		return !hit[0];
	}

	private static void room(String name, double x0, double x1, double y, double z0, double z1, boolean dry) {
		for (double z = z0; z <= z1 + 1e-9; z += 0.7) {
			for (double x = x0; x <= x1 + 1e-9; x += 0.6) {
				assertEquals(y, floorUnder(x, y, z, CLOSED), 1e-9, name + ": floor at " + x + ", " + z);
				assertTrue(fits(x, y, z, CLOSED), name + ": head room at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 0.5, z), name + ": carried at " + x + ", " + z);
				if (dry) {
					assertTrue(GRID.dryAt(x, y + 0.2, z, CLOSED) && GRID.dryAt(x, y + 1.6, z, CLOSED), name + ": dry at " + x + ", " + z);
				}
			}
		}
	}

	@Test
	void decksAndRooms() {
		room("main deck (waist)", -3.4, 3.4, M, -6.6, -5.2, false);
		room("main deck (forward)", -2.2, 2.2, M, 14.0, 16.5, false);
		room("quarterdeck (by the wheel)", -2.2, 2.2, Q, -16.6, -14.6, false);
		room("quarterdeck (beside the boat)", 1.4, 2.6, Q, -19.8, -17.0, false);
		assertFalse(fits(0, Q, -18.8, CLOSED), "the ship's boat on the quarterdeck is solid");
		room("captain's cabin", -1.6, 1.6, C, -16.5, -14.8, true);
		room("coursive", -0.6, 0.6, L, -13.0, -2.0, true);
		room("crew port", 2.0, 2.6, L, -8.6, -3.0, true);
		room("crew starboard", -2.6, -2.0, L, -8.6, -3.0, true);
		room("common room (aisle)", -0.5, 1.6, L, 0.0, 4.2, true);
		room("common room (beside the fore mast)", 0.9, 1.6, L, 4.6, 7.4, true);
		room("kitchen", -1.4, 1.4, L, 9.0, 10.2, true);
		// the work table stands aside (starboard): the way to the hearth is clear, the fire in view from the door
		room("kitchen (before the hearth)", 0.0, 1.8, L, 10.4, 12.4, true);
		assertFalse(fits(-1.2, L, 11.6, CLOSED), "the kitchen work table is solid");
		// solid furniture standing over cell boundaries is solid all over (pillars, chests, the dining table)
		for (double z : new double[] {-10.5, -5.5, -0.5}) {
			assertFalse(fits(2.75, H, z, CLOSED), "hold pillar (port) at z " + z);
			assertFalse(fits(-2.75, H, z, CLOSED), "hold pillar (starboard) at z " + z);
		}
		assertFalse(fits(-3.0, H, -1.9, CLOSED), "the hold's starboard chest");
		assertFalse(fits(3.97, L, -0.45, CLOSED), "the common room's sea chest");
		for (double z = 0.0; z <= 5.5; z += 0.25) {
			assertFalse(fits(-2.5, L, z, CLOSED), "the dining table at z " + z);
		}
		room("hold", -1.8, 1.8, H, -12.0, 1.4, true);
		// the hold lies below the waterline, and stays dry
		assertTrue(H < CorsairLayout.WATERLINE_Y - 1.5);
		// outside the hull: the sea, not carried
		assertFalse(GRID.dryAt(7.0, -1.0, 0, CLOSED));
		assertFalse(G.inCarryVolume(7.0, M + 0.5, 0));
		assertTrue(GRID.solidAt(4.85, 0.0, 0, CLOSED), "hull side");
		assertTrue(G.insideHull(0, -1.0, 0));
		// the bulwarks keep the walkers aboard
		assertFalse(fits(4.6, M, 0, CLOSED), "bulwark");
		// the two masts stop the walkers: the fore mast on deck and through the common room and the hold,
		// the main mast on deck (stepped on the main deck: the coursive under it stays clear)
		assertFalse(fits(0, M, CorsairLayout.FORE_MAST_Z, CLOSED), "fore mast on deck");
		assertFalse(fits(0, L, CorsairLayout.FORE_MAST_Z, CLOSED), "fore mast through the common room");
		assertFalse(fits(0, H, CorsairLayout.FORE_MAST_Z, CLOSED), "fore mast through the hold");
		assertFalse(fits(0, M, CorsairLayout.MAIN_MAST_Z, CLOSED), "main mast on deck");
		assertTrue(fits(0, L, CorsairLayout.MAIN_MAST_Z, CLOSED), "the coursive under the main mast");
		// a brig: nothing else stands on the centre line of the main deck between the bow and the castle
		for (double z = -13.0; z <= 17.0; z += 0.5) {
			boolean mast = Math.abs(z - CorsairLayout.FORE_MAST_Z) < 0.9 || Math.abs(z - CorsairLayout.MAIN_MAST_Z) < 0.9;
			assertTrue(mast || fits(0, M, z, CLOSED), "free main deck on the centre line at z " + z);
		}
	}

	/** Walks a straight stair: every step at most 0.5 above the previous, ending at the given height. */
	private static void stair(String name, double x, double zFrom, double zTo, double yFrom, double yTo, InteriorGrid.State s) {
		double y = yFrom;
		double dz = Math.signum(zTo - zFrom) * 0.25;
		for (double z = zFrom; Math.abs(z - zTo) > 1e-6; z += dz) {
			double up = floorUnder(x, y + 0.55, z, s);
			assertTrue(up >= y - 0.55 && up <= y + 0.51, name + ": step at z " + z + " from " + y + " to " + up);
			y = up;
			assertTrue(fits(x, y, z, s), name + ": head room on the step at z " + z + " (y " + y + ")");
		}
		assertTrue(y >= yTo - 1e-9 && y <= yTo + 0.51, name + ": arrives at " + y + " (" + yTo + ")");
	}

	@Test
	void stairsLinkTheLevels() {
		double qx = (CorsairLayout.QD_STAIR_X[0] + CorsairLayout.QD_STAIR_X[1]) / 2;
		stair("quarterdeck stair (port)", qx, CorsairLayout.QD_STAIR_Z[0] + 0.5, CorsairLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		stair("quarterdeck stair (starboard)", -qx, CorsairLayout.QD_STAIR_Z[0] + 0.5, CorsairLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		double cx = (CorsairLayout.COMPANION_X[0] + CorsairLayout.COMPANION_X[1]) / 2;
		stair("companionway", cx, CorsairLayout.COMPANION_Z[1] + 0.75, CorsairLayout.COMPANION_Z[0] - 0.5, M, L, CLOSED);
		stair("hold stair", 0, CorsairLayout.HOLD_STAIR_Z[1] + 0.75, CorsairLayout.HOLD_STAIR_Z[0] + 0.25, L, H, CLOSED);
		// from the foot of the stairs, a step aside into the hold
		assertEquals(H, floorUnder(1.35, H, CorsairLayout.HOLD_STAIR_Z[0] + 1.0, CLOSED), 1e-9);
		assertTrue(fits(1.35, H, CorsairLayout.HOLD_STAIR_Z[0] + 1.0, CLOSED));
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = {{0, C, CorsairLayout.CABIN_FRONT_Z - 0.4}, {0, L, -1.25}, {0, L, 8.25}};
		for (double[] d : doors) {
			assertFalse(fits(d[0], d[1], d[2], CLOSED), "a closed door at z " + d[2]);
			assertTrue(fits(d[0], d[1], d[2], OPEN), "an open door at z " + d[2]);
		}
		assertNotNull(GRID.doorCenter(CorsairLayout.CABIN_DOOR));
		assertNotNull(GRID.doorCenter(CorsairLayout.CREW_PORT_DOOR));
		assertNotNull(GRID.doorCenter(CorsairLayout.CREW_STBD_DOOR));
		// clicking the cabin door from the main deck picks it
		double[] c = GRID.doorCenter(CorsairLayout.CABIN_DOOR);
		ShipGeometry.Pick p = G.pick(ORIGIN, c[0], c[1], c[2] + 2.0, 0, 0, -1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DOOR, p.kind());
		assertEquals(CorsairLayout.CABIN_DOOR, p.seat());
	}

	@Test
	void helmAndSeats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertEquals(Q + 0.28, pilot.y(), 1e-9, "the pilot stands on the quarterdeck");
		assertTrue(Math.abs(pilot.z() - CorsairLayout.HELM_Z) < 1.2, "behind the wheel");
		assertTrue(G.seats().size() >= 13, "about twelve passengers and the pilot: " + G.seats().size());
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1], d[2], CLOSED), "free stand-up spot of seat " + s.index());
			double floor = floorUnder(d[0], d[1], d[2], CLOSED);
			assertTrue(d[1] - floor < 0.1 && d[1] - floor >= 0, "seat " + s.index() + " stands up on a floor (" + floor + ")");
		}
		// the helm is picked from the quarterdeck
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, Q + 1.6, CorsairLayout.HELM_Z - 2.0, 0, -0.2, 1, 4);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	@Test
	void clickingTheDeckDoesNotBoardAgain() {
		// from the main deck, looking down at it or at a mast: DECK, never HULL (which would board again)
		ShipGeometry.Pick p = G.pick(ORIGIN, 1.0, M + 1.6, -5.0, 0, -1, 0.2, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DECK, p.kind());
		p = G.pick(ORIGIN, 1.5, M + 1.6, CorsairLayout.MAIN_MAST_Z, -1, -0.3, 0, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DECK, p.kind());
		// from the sea, the hull boards
		p = G.pick(ORIGIN, 9.0, 1.0, 0, -1, 0, 0, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	@Test
	void boardingSpotIsOnTheMainDeck() {
		for (double z = -12; z <= 18; z += 3) {
			double[] b = G.boardingSpot(5.5, z);
			assertEquals(M + 0.02, b[1], 1e-9, "boarding at " + z);
			assertTrue(fits(b[0], b[1], b[2], CLOSED), "free boarding spot at " + z);
		}
	}

	@Test
	void model() throws Exception {
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/old_corsair.bbmodel"),
				StandardCharsets.UTF_8)) {
			BbModel m = new BbModel(r);
			for (String bone : new String[] {"hull", "sterncastle", "rooms", "furniture", "fittings", "detail", "helm_wheel", "rudder",
					"mast_fore", "mast_main", "sail_fore_course", "sail_fore_topsail", "sail_fore_topgallant", "sail_main_topsail",
					"sail_main_topgallant", "brace_main_yard", "sail_spanker", "sail_jibs", "sail_staysail", "flag_gaff", "flag_gaff_tip",
					"flag_stern", "flag_stern_tip", "lantern_fore_course_0", "lantern_fore_course_3", "door_0_a", "door_1_a", "door_3",
					"lantern_jibboom"}) {
				assertNotNull(m.bonesByName.get(bone), "bone " + bone);
			}
			// two masts, as on the reference: no mizzen, no main course (its yard is bare)
			assertEquals(2, m.bonesByName.keySet().stream().filter(b -> b.startsWith("mast_")).count(), "masts");
			assertNull(m.bonesByName.get("sail_main_course"));
			for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "door_0", "door_4"}) {
				assertNotNull(m.animations.get(anim), "animation " + anim);
			}
			int[] n = {0};
			m.render(m.newPose(), (p, uv, nn, glow) -> n[0]++);
			assertTrue(n[0] > 10000, "faces " + n[0]);
			for (InteriorDecor.Block b : G.decor().blocks()) {
				assertNotNull(m.bonesByName.get(b.fallback()), "stand-in of " + b.block());
			}
		}
	}
}
