package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The Fortress Ship: hull shape (same numbers as tools/fortress_shape.py), dimensions, interior grid (the waist, the
 * forecastle, the quarterdeck, the keep's roof, the turret, the captain's cabin, the officers' room, the crew's mess,
 * the cargo hold, the crew quarters, the stairs between them, the five doors, no way out through the hull), the seats,
 * the boarding spot and the model (bones, animations, the two atlases).
 */
class FortressShipTest {
	private static final ShipType T = Ships.FORTRESS_SHIP;
	private static final ShipGeometry G = T.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final InteriorGrid.State OPEN = new InteriorGrid.State(0xFFFFFFFFL, 0f);
	private static final double M = FortressLayout.MAIN_DECK_Y, L = FortressLayout.LOWER_FLOOR_Y, F = FortressLayout.FORECASTLE_Y,
			Q = FortressLayout.QUARTERDECK_Y, K = FortressLayout.KEEP_Y, C = FortressLayout.CABIN_FLOOR_Y;

	/** Values printed by {@code python3 tools/fortress_shape.py}: z, half width, rail (NaN: a castle's rail floor), keel, bottom 2 blocks out. */
	@Test
	void matchesShapeGenerator() {
		double[][] rows = {
				{-19.5, 4.62539, Double.NaN, -0.837914, -0.750959},
				{-11.0, 6.266782, Double.NaN, -2.611897, -2.41184},
				{0.0, 6.5, 5.5, -3.0, -2.778462},
				{9.5, 5.651443, Double.NaN, -2.75, -2.516431},
				{16.0, 3.044251, Double.NaN, -1.805657, -1.252387}};
		HullShape h = T.hull();
		for (double[] r : rows) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			if (!Double.isNaN(r[2])) {
				assertEquals(r[2], h.railY(r[0]), 1e-5, "rail at " + r[0]);
			}
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], h.bottomY(r[0], 2.0), 1e-5, "bottom at " + r[0]);
		}
		// the castles' bulwarks and parapets
		assertEquals(FortressLayout.KEEP_WALL, h.railY(-16.0), 1e-9);
		assertEquals(FortressLayout.QD_WALL, h.railY(-11.0), 1e-9);
		assertEquals(FortressLayout.FC_WALL, h.railY(10.0), 1e-9);
	}

	@Test
	void dimensionsAndRegistration() {
		assertTrue(FortressLayout.FORE_MAST_Z > FortressLayout.FC_FRONT_Z && FortressLayout.MAIN_MAST_Z < 0
				&& FortressLayout.MIZZEN_Z < FortressLayout.CABIN_FRONT_Z && FortressLayout.MIZZEN_Z > FortressLayout.KEEP_FRONT_Z,
				"fore mast on the forecastle, main mast amidships, mizzen on the open quarterdeck before the keep");
		assertTrue(FortressLayout.MAIN_MAST_TOP > FortressLayout.MIZZEN_TOP && FortressLayout.MIZZEN_TOP >= FortressLayout.FORE_MAST_TOP,
				"the main mast is the tallest");
		assertEquals(T, Ships.byId("fortress_ship"));
		assertTrue(Ships.ALL.contains(T));
		assertNotNull(GRID);
		assertNotNull(G.decor());
		assertFalse(G.submarine());
		assertFalse(G.flying());
		double hull = FortressLayout.STEM_HEAD_Z + 0.5 - FortressLayout.TRANSOM_Z;
		assertTrue(hull > 41 && hull < 44, "length over the raked stem and the castle " + hull);
		double overall = FortressLayout.BOWSPRIT_TIP[2] - FortressLayout.TRANSOM_Z;
		assertTrue(overall > 46 && overall < 49, "length with the bowsprit " + overall);
		assertEquals(13.0, 2 * FortressLayout.MAX_HALF_WIDTH, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 29 && height < 33, "height from the keel to the main masthead " + height);
		assertNotNull(T.defaults().get());
		assertTrue(T.defaults().get().dive == null && T.defaults().get().flight == null, "a sailing ship");
		ShipConfig c = T.defaults().get(), frigate = Ships.BLUE_FRIGATE.defaults().get();
		assertTrue(c.maxTurnRate < frigate.maxTurnRate && c.acceleration < frigate.acceleration && c.normalSpeed < frigate.normalSpeed,
				"heavier and slower than the frigate");
		boolean bowsprit = false, beak = false, yard = false, stern = false;
		for (double[] p : G.probes()) {
			bowsprit |= p[2] > FortressLayout.BOWSPRIT_TIP[2] - 0.5;
			beak |= Math.abs(p[2] - FortressLayout.BEAK_PROBE[2]) < 0.1 && Math.abs(p[1] - FortressLayout.BEAK_PROBE[1]) < 0.1;
			stern |= p[2] < FortressLayout.STERN_REACH_Z + 0.3;
			yard |= Math.abs(p[0]) > FortressLayout.YARD_HALF * 0.7;
		}
		assertTrue(bowsprit && beak && yard && stern, "probes at the bowsprit end, the beak, the rudder and the yard arms");
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
		room("waist (aft)", -2.2, 2.2, M, -8.4, -6.0, false);
		room("waist (forward)", -2.0, 2.0, M, 0.4, 3.0, false);
		room("forecastle", -1.6, 1.6, F, 9.2, 13.0, false);
		room("quarterdeck (port of the mizzen)", 1.2, 2.6, Q, -12.4, -10.0, false);
		room("keep's roof (before the turret)", -1.5, 1.5, K, -14.6, -13.9, false);
		room("turret", -0.6, 0.6, K, -17.8, -15.9, true);
		room("captain's cabin (door to the desk)", -0.8, 0.8, C, -16.1, -10.0, true);
		room("captain's cabin (behind the desk)", -0.6, 2.0, C, -18.6, -18.4, true);
		room("officers' room (beside the war table)", 0.0, 1.8, Q, -18.5, -14.2, true);
		room("crew's mess", -1.5, 1.5, M, 9.0, 11.8, true);
		room("cargo hold (aft)", -0.8, 0.8, L, -14.0, -2.0, true);
		room("cargo hold (forward)", -0.8, 0.8, L, 0.0, 4.8, true);
		room("crew quarters", -1.2, 1.2, L, 9.0, 13.4, true);
		assertFalse(fits(0.0, C, -17.3, CLOSED), "the captain's desk is solid");
		assertFalse(fits(3.4, C, -17.2, CLOSED), "the captain's bed is solid");
		assertFalse(fits(-1.9, Q, -16.4, CLOSED), "the war table is solid");
		assertFalse(fits(0.0, M, 14.0, CLOSED), "the mess table is solid");
		assertFalse(fits(3.95, L, 12.05, CLOSED), "a bunk is solid");
		assertFalse(fits(-4.85, L, -6.75, CLOSED), "the cargo is solid");
		// outside the hull: the sea, not carried; the hull sides and the bottom are solid
		assertFalse(GRID.dryAt(8.0, -1.0, 0, CLOSED));
		assertFalse(G.inCarryVolume(8.0, M + 0.5, 0));
		assertTrue(GRID.solidAt(6.2, 0.0, 0, CLOSED), "hull side");
		assertTrue(GRID.solidAt(0.0, -2.5, 0, CLOSED), "keel");
		assertTrue(G.insideHull(0, -1.0, 0));
		// the bulwarks and the parapets keep the walkers aboard
		assertFalse(fits(5.6, M, 0, CLOSED), "waist bulwark");
		assertFalse(fits(-5.3, Q, -11.0, CLOSED), "quarterdeck parapet");
		assertFalse(fits(4.8, F, 12.0, CLOSED), "forecastle bulwark");
		assertFalse(fits(0, K, -13.35, CLOSED), "the keep's front parapet");
		assertFalse(fits(0, C, -19.2, CLOSED), "transom");
		// the masts stop the walkers
		assertFalse(fits(0, F, FortressLayout.FORE_MAST_Z, CLOSED), "fore mast on the forecastle");
		assertFalse(fits(0, L, FortressLayout.FORE_MAST_Z, CLOSED), "fore mast through the crew quarters");
		assertFalse(fits(0, M, FortressLayout.MAIN_MAST_Z, CLOSED), "main mast on deck");
		assertFalse(fits(0, L, FortressLayout.MAIN_MAST_Z, CLOSED), "main mast through the hold");
		assertFalse(fits(0, Q, FortressLayout.MIZZEN_Z, CLOSED), "mizzen on the quarterdeck");
		assertTrue(fits(0, C, FortressLayout.MIZZEN_Z, CLOSED), "the cabin under the mizzen stays clear");
	}

	/** No cell of the rooms (and nothing under the main deck) opens on the sea: the hull is closed all round. */
	@Test
	void noWayOutThroughTheHull() {
		for (double z = -18.5; z <= 15.0; z += 0.5) {
			for (double y = L; y <= M - 0.5; y += 0.5) {
				boolean out = false;
				for (double x = 0.0; x <= 7.0; x += 0.5) {
					boolean dry = GRID.dryAt(x, y, z, CLOSED) || GRID.dryAt(-x, y, z, CLOSED);
					boolean solid = GRID.solidAt(x, y, z, CLOSED) && GRID.solidAt(-x, y, z, CLOSED);
					if (!dry && !solid) {
						out = true;
					}
					assertFalse(out && dry, "a dry cell beyond the hull at x " + x + " y " + y + " z " + z);
				}
			}
		}
		for (double z = -12.0; z <= 12.0; z += 2.0) {
			for (double y = -2.5; y < L; y += 0.5) {
				assertTrue(GRID.solidAt(0.0, y, z, CLOSED) || y < T.hull().keelY(z), "solid under the lower deck at y " + y + " z " + z);
			}
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
		double qx = (FortressLayout.QD_STAIR_X[0] + FortressLayout.QD_STAIR_X[1]) / 2;
		stair("quarterdeck stair (port)", qx, FortressLayout.QD_STAIR_Z[0] + 0.5, FortressLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		stair("quarterdeck stair (starboard)", -qx, FortressLayout.QD_STAIR_Z[0] + 0.5, FortressLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		double fx = (FortressLayout.FC_STAIR_X[0] + FortressLayout.FC_STAIR_X[1]) / 2;
		stair("forecastle stair (port)", fx, FortressLayout.FC_STAIR_Z[0] - 0.5, FortressLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		stair("forecastle stair (starboard)", -fx, FortressLayout.FC_STAIR_Z[0] - 0.5, FortressLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		double cx = (FortressLayout.COMPANION_X[0] + FortressLayout.COMPANION_X[1]) / 2;
		stair("companionway to the lower deck", cx, FortressLayout.COMPANION_Z[1] + 0.75, FortressLayout.COMPANION_Z[0] - 0.5, M, L, CLOSED);
		assertEquals(L, floorUnder(1.5, L, FortressLayout.COMPANION_Z[0] - 0.5, CLOSED), 1e-9);
		assertTrue(fits(1.5, L, FortressLayout.COMPANION_Z[0] - 0.5, CLOSED));
		double kx = (FortressLayout.KEEP_STAIR_X[0] + FortressLayout.KEEP_STAIR_X[1]) / 2;
		stair("the keep's stair to its roof", kx, FortressLayout.KEEP_STAIR_Z[0] + 0.75, FortressLayout.KEEP_STAIR_Z[1] - 0.75, Q, K, CLOSED);
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = {
				{FortressLayout.CABIN_DOOR, C, FortressLayout.CABIN_FRONT_Z - 0.25},
				{FortressLayout.KEEP_DOOR, Q, FortressLayout.KEEP_FRONT_Z - 0.25},
				{FortressLayout.MESS_DOOR, M, FortressLayout.FC_FRONT_Z + 0.25},
				{FortressLayout.CREW_DOOR, L, FortressLayout.CREW_BULKHEAD_Z + 0.25},
				{FortressLayout.TURRET_DOOR, K, FortressLayout.TURRET_Z[1] - 0.25}};
		for (double[] d : doors) {
			assertFalse(fits(0, d[1], d[2], CLOSED), "door " + (int) d[0] + " closed");
			assertTrue(fits(0, d[1], d[2], OPEN), "door " + (int) d[0] + " open");
			assertNotNull(GRID.doorCenter((int) d[0]), "door " + (int) d[0]);
		}
		double[] c = GRID.doorCenter(FortressLayout.CABIN_DOOR);
		ShipGeometry.Pick p = G.pick(ORIGIN, c[0], c[1], c[2] + 2.0, 0, 0, -1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DOOR, p.kind());
		assertEquals(FortressLayout.CABIN_DOOR, p.seat());
	}

	@Test
	void helmAndSeats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertEquals(Q + 0.28, pilot.y(), 1e-9, "the pilot stands on the quarterdeck");
		assertTrue(Math.abs(pilot.z() - FortressLayout.HELM_Z) < 1.2, "behind the wheel");
		assertTrue(fits(pilot.x(), Q, pilot.z(), CLOSED), "room for the pilot between the wheel and the mizzen");
		assertTrue(G.seats().size() >= 8, "the pilot and several passengers: " + G.seats().size());
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1], d[2], CLOSED), "free stand-up spot of seat " + s.index());
			double floor = floorUnder(d[0], d[1], d[2], CLOSED);
			assertTrue(d[1] - floor < 0.1 && d[1] - floor >= 0, "seat " + s.index() + " stands up on a floor (" + floor + ")");
		}
		// the helm is picked from the quarterdeck's front
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, Q + 1.6, FortressLayout.HELM_Z + 2.0, 0, -0.25, -1, 4);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	/** Decor blocks whose bottom-centre lies in the box (x0..x1, y0..y1, z0..z1). */
	private static long blocksIn(double x0, double x1, double y0, double y1, double z0, double z1) {
		return G.decor().blocks().stream().filter(b -> b.x() >= x0 && b.x() <= x1 && b.y() >= y0 && b.y() <= y1 && b.z() >= z0 && b.z() <= z1)
				.count();
	}

	/**
	 * The decoration: every room furnished with the mods' blocks (the captain's cabin, the council room in the keep, the
	 * turret, the mess and its galley, the crew quarters, the hold, the deck cargo), lanterns that glow, a seat for many
	 * passengers (the captain's chair, the war council's seven chairs, the benches of the mess...); nothing stands in the
	 * walls, the decks or the hull, nor beyond the sides; the seats are in the rooms; the solid furniture keeps the walkers
	 * out (the desk, the war table, the mess table, the bunks, the racks, the cargo) while the ways through stay free.
	 */
	@Test
	void furnishedRooms() {
		InteriorDecor d = G.decor();
		assertTrue(d.blocks().size() >= 120, "decor blocks " + d.blocks().size());
		assertTrue(G.seats().size() >= 20, "seats " + G.seats().size());
		assertTrue(d.blocks().stream().filter(InteriorDecor.Block::glow).count() >= 10, "glowing lanterns");
		assertTrue(blocksIn(-6, 6, C - 0.1, C + 1.5, -19.5, -9.0) >= 15, "the captain's cabin is furnished");
		assertTrue(blocksIn(-6, 6, Q - 0.1, Q + 1.5, -19.5, -13.0) >= 10, "the council room is furnished");
		assertTrue(blocksIn(-3, 3, K - 0.1, K + 3.5, -19.0, -15.0) >= 3, "the turret is furnished");
		assertTrue(blocksIn(-6, 6, M - 0.1, M + 1.5, 6.0, 17.0) >= 20, "the mess and its galley are furnished");
		assertTrue(blocksIn(-6, 6, L - 0.1, L + 3.0, 6.0, 14.0) >= 4, "the crew quarters are furnished");
		assertTrue(blocksIn(-6, 6, L - 0.1, L + 1.5, -15.0, 5.5) >= 40, "the hold is full of provisions");
		assertTrue(blocksIn(-6, 6, M - 0.1, M + 1.5, -9.0, 6.0) >= 15, "cargo on the main deck");
		for (InteriorDecor.Block b : d.blocks()) {
			byte k = GRID.kindAt(b.x(), b.y() + 0.05, b.z());
			assertTrue(k != 1, "decor block in a wall, a deck or the hull: " + b.block() + " at " + b.x() + ", " + b.y() + ", " + b.z());
			assertTrue(Math.abs(b.x()) < T.hull().halfWidth(b.z()) - 0.4, "decor block beyond the side: " + b.block() + " at " + b.x() + ", " + b.z());
		}
		for (ShipGeometry.Seat s : G.seats()) {
			assertTrue(GRID.kindAt(s.x(), s.y() - 0.2, s.z()) != 1, "seat " + s.index() + " in a wall");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " aboard");
		}
		assertFalse(fits(4.0, L, -13.25, CLOSED), "the casks of the hold are solid");
		assertFalse(fits(-5.0, M, -3.6, CLOSED), "deck cargo is solid");
		assertFalse(fits(-4.2, K, -14.2, CLOSED), "the signal brazier is solid");
		// the ways through: from the cabin's door to the desk, from the keep's door to its stair, the hold's centre line,
		// the companionway's foot, the gangplank's stairs, the boarding strip of the waist
		assertTrue(fits(0.0, C, -10.2, CLOSED) && fits(0.0, C, -16.1, CLOSED), "the way from the cabin's door to the desk");
		assertTrue(fits(1.2, Q, -14.0, CLOSED) && fits(3.25, Q, -14.4, CLOSED), "the way from the keep's door to its stair");
		assertTrue(fits(3.25, L, -5.8, CLOSED), "the companionway's foot");
		for (double z = -14.0; z <= 4.5; z += 0.5) {
			if (Math.abs(z - FortressLayout.MAIN_MAST_Z) > 0.9) {
				assertTrue(fits(0.0, L, z, CLOSED), "the hold's centre line at " + z);
			}
		}
		for (double z = -7.5; z <= 4.0; z += 0.5) {
			for (double x : new double[] {-2.0, 2.0}) {
				assertTrue(fits(x, M, z, CLOSED), "the waist's boarding strip at " + x + ", " + z);
			}
		}
	}

	@Test
	void boardingSpotIsOnTheMainDeck() {
		for (double z = -7; z <= 4; z += 3) {
			double[] b = G.boardingSpot(6.5, z);
			assertEquals(M + 0.02, b[1], 1e-9, "boarding at " + z);
			assertTrue(fits(b[0], b[1], b[2], CLOSED), "free boarding spot at " + z);
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 1.0, M + 1.6, -6.0, 0, -1, 0.2, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DECK, p.kind());
		p = G.pick(ORIGIN, 10.0, 1.0, 0, -1, 0, 0, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	private static BbModel load() throws Exception {
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/fortress_ship.bbmodel"),
				StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void model() throws Exception {
		BbModel m = load();
		for (String bone : new String[] {"hull", "sterncastle", "turret", "rooms", "furniture", "fittings", "detail", "helm_wheel", "rudder",
				"mast_fore", "mast_main", "mast_mizzen", "sail_fore_course", "sail_fore_topsail", "sail_main_course", "sail_main_topsail",
				"sail_mizzen_course", "sail_jibs", "flag_fore", "flag_fore_tip", "flag_main", "flag_mizzen", "flag_mizzen_tip", "lantern_stern_p",
				"lantern_stern_s", "lantern_waist_p0", "lantern_crane_load", "banner_stern", "banner_fc_p", "banner_bowsprit", "door_0_a", "door_4_b",
				"rope_slack_fore_brace_p", "rope_slack_main_topmast_stay"}) {
			assertNotNull(m.bonesByName.get(bone), "bone " + bone);
		}
		assertEquals(3, m.bonesByName.keySet().stream().filter(b -> b.startsWith("mast_")).count(), "three masts");
		for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "rope_sway", "door_0", "door_1", "door_2",
				"door_3", "door_4"}) {
			assertNotNull(m.animations.get(anim), "animation " + anim);
		}
		assertEquals(2, m.textureCount(), "the hull atlas and the sail atlas");
		int[] n = {0};
		int[] sailFaces = {0};
		m.render(m.newPose(), 1, (p, uv, nn, glow) -> sailFaces[0]++);
		m.render(m.newPose(), (p, uv, nn, glow) -> n[0]++);
		assertTrue(n[0] > 8000 && n[0] < 60000, "faces " + n[0]);
		assertTrue(sailFaces[0] > 400, "the sails are drawn with the sail atlas: " + sailFaces[0]);
		for (InteriorDecor.Block b : G.decor().blocks()) {
			assertNotNull(m.bonesByName.get(b.fallback()), "stand-in of " + b.block());
		}
	}

	private static float[] vertices(BbModel m, String anim, float t) {
		BbModel.Pose pose = m.newPose();
		if (anim != null) {
			m.apply(pose, anim, t, 1f);
		}
		java.util.List<float[]> quads = new java.util.ArrayList<>();
		m.render(pose, (p, uv, n, glow) -> quads.add(p.clone()));
		float[] v = new float[quads.size() * 12];
		for (int i = 0; i < quads.size(); i++) {
			System.arraycopy(quads.get(i), 0, v, i * 12, 12);
		}
		return v;
	}

	private static double[] moved(float[] a, float[] b) {
		assertEquals(a.length, b.length);
		double max = 0;
		int n = 0;
		for (int i = 0; i < a.length; i += 3) {
			double d = Math.sqrt(Math.pow(a[i] - b[i], 2) + Math.pow(a[i + 1] - b[i + 1], 2) + Math.pow(a[i + 2] - b[i + 2], 2));
			max = Math.max(max, d);
			n += d > 1e-4 ? 1 : 0;
		}
		return new double[] {max, n};
	}

	/** The slack ropes swing about their ends, the looping animations join up when they wrap, the helm, the sails, the doors. */
	@Test
	void animations() throws Exception {
		BbModel m = load();
		String[] slack = {"fore_brace_p", "fore_brace_s", "main_brace_p", "main_brace_s", "main_topmast_stay", "mizzen_topmast_stay"};
		for (String r : slack) {
			assertNotNull(m.bonesByName.get("rope_slack_" + r), "slack rope " + r);
		}
		float[] rest = vertices(m, null, 0f);
		for (float t : new float[] {0.6f, 1.2f, 2.4f, 3.6f}) {
			double[] d = moved(rest, vertices(m, "rope_sway", t));
			assertTrue(d[1] > 60 && d[1] <= slack.length * 8 * 24, "rope_sway at " + t + " moves " + d[1] + " vertices");
			assertTrue(d[0] > 0.04 && d[0] < 0.3, "rope_sway at " + t + ": swing " + d[0]);
		}
		for (String anim : new String[] {"sail_wind", "flag_wave", "lantern_sway", "rope_sway"}) {
			float len = m.animations.get(anim).length;
			float[] start = vertices(m, anim, 0f);
			assertTrue(moved(start, vertices(m, anim, len - 1e-3f))[0] < 0.02, anim + " jumps when it wraps");
			assertTrue(moved(start, vertices(m, anim, 1e-3f))[0] < 0.02, anim + " jumps at its start");
		}
		assertTrue(moved(rest, vertices(m, "flag_wave", 0.6f))[0] > 0.3, "the pennants wave");
		assertTrue(moved(rest, vertices(m, "lantern_sway", 0.6f))[0] > 0.02, "the lanterns and the banners swing");
		double wind = moved(rest, vertices(m, "sail_wind", 0.9f))[0];
		assertTrue(wind > 0.08 && wind < 1.2, "the sails fill and slacken in the wind, a little: " + wind);
		assertTrue(moved(vertices(m, "steer", 1f), vertices(m, "steer", 2f))[0] > 0.5, "the wheel and the rudder turn");
		assertTrue(moved(rest, vertices(m, "sail_furl", 0.5f))[0] > 2, "the sails furl");
		assertTrue(vertices(m, "sail_furl", 1f).length < rest.length, "the furled jib is not drawn");
		for (int d = 0; d < 5; d++) {
			assertTrue(moved(rest, vertices(m, "door_" + d, 1f))[0] > 0.5, "door " + d + " opens");
		}
	}
}
