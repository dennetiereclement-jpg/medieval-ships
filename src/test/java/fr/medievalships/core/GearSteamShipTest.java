package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The Gear Steamship: hull shape (same numbers as tools/gear_steam_shape.py), dimensions, interior grid (the waist,
 * the forecastle, the engine house roof, the poop deck, the bridge, the stern gallery, the engine room, the crew
 * quarters, the captain's cabin, the hold, the stairs and ladders between them, the doors, no way out through the
 * hull), the seats, the probes, the model (bones, animations, the turning gears, the sails' atlas) and its gangplank.
 */
class GearSteamShipTest {
	private static final ShipType T = Ships.GEAR_STEAMSHIP;
	private static final ShipGeometry G = T.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final InteriorGrid.State OPEN = new InteriorGrid.State(0xFFFFFFFFL, 0f);
	private static final double M = GearSteamLayout.MAIN_DECK_Y, H = GearSteamLayout.HOLD_FLOOR_Y, P = GearSteamLayout.POOP_Y,
			F = GearSteamLayout.FORECASTLE_Y, E = GearSteamLayout.ENGINE_ROOF_Y, B = GearSteamLayout.BRIDGE_Y;

	/** Values printed by {@code python3 tools/gear_steam_shape.py}: z, half width, rail (NaN under a castle), keel, bottom 2 out. */
	@Test
	void matchesShapeGenerator() {
		double[][] rows = {
				{-19.0, 3.627958, Double.NaN, 0.057853, 0.050259},
				{-11.0, 4.789645, Double.NaN, -2.406619, -2.245831},
				{0.0, 5.0, Double.NaN, -3.0, -2.808},
				{9.5, 4.373053, 5.616385, -2.617768, -2.426212},
				{16.0, 2.471448, Double.NaN, -1.173937, -0.716991}};
		HullShape h = T.hull();
		for (double[] r : rows) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			if (!Double.isNaN(r[2])) {
				assertEquals(r[2], h.railY(r[0]), 1e-5, "rail at " + r[0]);
			}
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], h.bottomY(r[0], 2.0), 1e-5, "bottom at " + r[0]);
		}
		// the castles' bulwarks: the poop, the engine house's roof railing, the forecastle
		assertEquals(P + 1.0, h.railY(-11.0), 1e-9);
		assertEquals(E + 1.0, h.railY(0.0), 1e-9);
		assertEquals(F + 1.5, h.railY(16.0), 1e-9);
	}

	@Test
	void dimensionsAndRegistration() {
		assertEquals(T, Ships.byId("gear_steamship"));
		assertTrue(Ships.ALL.contains(T));
		assertNotNull(GRID);
		assertNotNull(G.decor());
		assertFalse(G.submarine());
		assertFalse(G.flying());
		double hull = GearSteamLayout.STEM_HEAD[2] - GearSteamLayout.GALLERY_Z;
		assertTrue(hull >= 38 && hull <= 44, "length from the stern gallery to the stem head " + hull);
		double overall = GearSteamLayout.BOOM_TIP[2] - GearSteamLayout.GALLERY_Z;
		assertTrue(overall > 44 && overall < 47, "length with the bow boom " + overall);
		assertEquals(10.0, 2 * GearSteamLayout.MAX_HALF_WIDTH, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 22 && height < 25, "height from the keel to the main masthead " + height);
		assertTrue(GearSteamLayout.MAIN_MAST_Z > GearSteamLayout.ENGINE_FRONT_Z && GearSteamLayout.MIZZEN_Z < GearSteamLayout.DECKHOUSE_Z[0],
				"the main mast on the waist, the mizzen on the poop deck aft of the deckhouse");
		assertTrue(GearSteamLayout.FUNNEL_Z + GearSteamLayout.FUNNEL_R <= GearSteamLayout.DOME_Z - GearSteamLayout.DOME_R,
				"the funnel aft of the dome on the engine house");
		assertTrue(G.boundingRadius() >= -GearSteamLayout.STERN_REACH_Z);
		ShipConfig c = T.defaults().get(), frigate = Ships.BLUE_FRIGATE.defaults().get(), corsair = Ships.OLD_CORSAIR.defaults().get();
		assertTrue(c.dive == null && c.flight == null, "a ship");
		assertTrue(c.acceleration < corsair.acceleration && c.maxTurnRate < corsair.maxTurnRate && c.normalSpeed >= frigate.normalSpeed,
				"a heavy steamer: slower to answer than the corsair, as fast as the frigate");
		// the boom, its lantern, the crane and its crate, the stern gallery, the rudder and the yard arms are probed
		boolean boom = false, crate = false, gallery = false, yard = false, rudder = false;
		for (double[] p : G.probes()) {
			boom |= p[2] > GearSteamLayout.BOOM_TIP[2] - 0.3;
			crate |= p[2] < GearSteamLayout.CRANE_TIP[2] + 0.1 && p[1] < GearSteamLayout.CRATE_Y[1];
			gallery |= Math.abs(p[2] - (GearSteamLayout.GALLERY_Z - 0.5)) < 0.1 && Math.abs(p[0]) > 3.0;
			yard |= Math.abs(p[1] - GearSteamLayout.MAIN_YARD_Y) > 0.5 && p[1] > GearSteamLayout.MAIN_YARD_Y - 3 && Math.abs(p[0]) > 2.0;
			rudder |= p[1] < 0 && p[2] < -17.0;
		}
		assertTrue(boom && crate && gallery && yard && rudder, "probes " + boom + crate + gallery + yard + rudder);
		// the yard arms: braced round (the starboard arm aft) and peaked (higher)
		double[] s = GearSteamLayout.yardArm(-1, GearSteamLayout.MAIN_YARD_Y, GearSteamLayout.MAIN_MAST_Z, 0.675, GearSteamLayout.MAIN_YARD_HALF);
		assertTrue(s[2] < GearSteamLayout.MAIN_MAST_Z - 2 && s[1] > GearSteamLayout.MAIN_YARD_Y + 1, "the starboard yard arm aft and high");
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
		room("waist (starboard of the mast)", -2.0, -1.0, M, 6.0, 9.5, false);
		room("waist (before the mast)", -1.0, 1.0, M, 8.6, 9.8, false);
		room("forecastle", -1.5, 1.5, F, 12.5, 17.0, false);
		room("engine house roof (beside the dome)", 3.35, 3.65, E, -3.0, 4.0, false);
		room("poop deck (aft of the deckhouse)", 0.95, 1.85, P, -15.5, -13.0, false);
		room("poop deck (over the gallery)", 0.85, 1.6, P, GearSteamLayout.OVERHANG_Z + 0.85, GearSteamLayout.TRANSOM_Z - 0.4, false);
		room("poop side deck (port)", 3.4, 3.9, P, -13.5, -8.0, false);
		room("bridge", -1.8, 1.8, B, GearSteamLayout.DECKHOUSE_Z[0] + 0.9, GearSteamLayout.HELM_Z - 0.85, false);
		room("stern gallery", -2.4, 2.4, M, -19.5, -18.0, false);
		room("engine room (port of the boiler)", 2.0, 3.8, M, -5.4, 0.0, true);
		room("engine room (forward)", -1.0, 1.0, M, -2.5, 3.8, true);
		room("crew quarters (aft of the table)", -1.0, 0.9, M, GearSteamLayout.TRANSOM_Z + 1.0, -14.4, true);
		room("crew quarters (beside the table)", 1.65, 2.15, M, -13.6, -10.4, true);
		room("captain's cabin", -0.6, 0.6, P, GearSteamLayout.DECKHOUSE_Z[0] + 1.0, -9.4, true);
		room("hold (centre line)", -0.8, 0.8, H, -14.5, 5.0, true);
		room("hold (forward)", -0.8, 0.8, H, 10.0, 13.5, true);
		// the boiler and the furniture are solid
		assertFalse(fits(0, M, GearSteamLayout.FUNNEL_Z + 0.5, CLOSED), "the boiler");
		assertFalse(fits(0, M, -13.0, CLOSED), "the mess table");
		assertFalse(fits(3.0, M, 1.7, CLOSED), "the steam engine");
		assertFalse(fits(-3.2, M, -5.3, CLOSED), "the coal bunker of the engine room");
		assertFalse(fits(0, F, 17.9, CLOSED), "the windlass");
		// the engine room is 4 blocks high, the cabins 2.5 and 3, the hold 3
		assertTrue(fits(0, M + 1.9, 1.0, CLOSED), "the engine room's head room");
		// outside the hull: the sea, not carried; the hull sides and the bottom are solid
		assertFalse(GRID.dryAt(7.0, -1.0, 0, CLOSED));
		assertFalse(G.inCarryVolume(7.0, M + 0.5, 0));
		assertTrue(GRID.solidAt(4.85, 0.0, 0, CLOSED), "hull side");
		assertTrue(GRID.solidAt(0.0, -2.8, 0, CLOSED), "keel");
		// the bulwarks and railings keep the walkers aboard
		assertFalse(fits(-4.3, M, 10.5, CLOSED), "waist bulwark");
		assertFalse(fits(3.1, F, 15.0, CLOSED), "forecastle bulwark (the raked bow is 3.5 wide there)");
		assertFalse(fits(4.3, P, -12.0, CLOSED), "poop bulwark");
		assertFalse(fits(4.4, E, 0.0, CLOSED), "engine house roof railing");
		assertFalse(fits(2.8, B, -11.0, CLOSED), "bridge railing");
		assertFalse(fits(2.0, P, GearSteamLayout.OVERHANG_Z + 0.2, CLOSED), "taffrail over the gallery");
		// the stern gallery's aft part stands out beyond the poop deck, open to the sky; the stepped counter under it is solid
		assertTrue(fits(0, M, GearSteamLayout.GALLERY_Z + 0.5, CLOSED) && fits(0, M + 2.5, GearSteamLayout.GALLERY_Z + 0.5, CLOSED),
				"the gallery open above its aft part");
		assertTrue(GRID.solidAt(0, 2.0, GearSteamLayout.GALLERY_Z + 1.0, CLOSED) && !GRID.solidAt(0, 0.5, GearSteamLayout.GALLERY_Z + 0.5, CLOSED)
				&& GRID.solidAt(0, 0.5, GearSteamLayout.TRANSOM_Z - 0.2, CLOSED), "the stepped counter under the gallery");
		// the funnel rises through the fore part of the deckhouse: the cabin's front wall is its casing, the bridge is closed before it
		assertFalse(fits(0, P, GearSteamLayout.CABIN_FRONT_Z + 0.2, CLOSED), "the cabin's front wall (the funnel casing)");
		assertFalse(fits(2.0, B, GearSteamLayout.CABIN_FRONT_Z + 0.4, CLOSED), "the bridge closed before the funnel casing");
		assertTrue(GearSteamLayout.DECKHOUSE_Z[1] > GearSteamLayout.FUNNEL_Z && GearSteamLayout.DECKHOUSE_Z[1] < GearSteamLayout.FUNNEL_Z + GearSteamLayout.FUNNEL_R,
				"the funnel stands at the deckhouse's fore end, rising through it");
		assertFalse(fits(3.2, M, -19.0, CLOSED), "stern gallery bulwark");
		// the masts, the funnel and the dome stop the walkers
		assertFalse(fits(0, M, GearSteamLayout.MAIN_MAST_Z, CLOSED), "main mast on the waist");
		assertFalse(fits(0, H, GearSteamLayout.MAIN_MAST_Z, CLOSED), "main mast through the hold");
		assertFalse(fits(0, P, GearSteamLayout.MIZZEN_Z, CLOSED), "mizzen on the poop deck");
		assertFalse(fits(0, E, GearSteamLayout.FUNNEL_Z, CLOSED), "funnel");
		assertFalse(fits(0, E, GearSteamLayout.DOME_Z, CLOSED), "dome");
		assertFalse(fits(0, P, GearSteamLayout.CRANE_Z, CLOSED), "crane post");
	}

	/** No cell of the rooms (and nothing under the main deck) opens on the sea: the hull is closed all round. */
	@Test
	void noWayOutThroughTheHull() {
		for (double z = -17.0; z <= 15.0; z += 0.5) {
			for (double y = H; y <= M - 0.5; y += 0.5) {
				boolean out = false;
				for (double x = 0.0; x <= 6.0; x += 0.5) {
					boolean dry = GRID.dryAt(x, y, z, CLOSED) || GRID.dryAt(-x, y, z, CLOSED);
					boolean solid = GRID.solidAt(x, y, z, CLOSED) && GRID.solidAt(-x, y, z, CLOSED);
					if (!dry && !solid) {
						out = true;
					}
					assertFalse(out && dry, "a dry cell beyond the hull at x " + x + " y " + y + " z " + z);
				}
			}
		}
		for (double z = -8.0; z <= 10.0; z += 2.0) {
			for (double y = -2.8; y < H; y += 0.5) {
				assertTrue(GRID.solidAt(0.0, y, z, CLOSED) || y < T.hull().keelY(z), "solid under the hold at y " + y + " z " + z);
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
	void stairsAndLaddersLinkTheLevels() {
		double fx = (GearSteamLayout.FC_STAIR_X[0] + GearSteamLayout.FC_STAIR_X[1]) / 2;
		stair("forecastle stair (port)", fx, GearSteamLayout.FC_STAIR_Z[0] - 0.75, GearSteamLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		stair("forecastle stair (starboard)", -fx, GearSteamLayout.FC_STAIR_Z[0] - 0.75, GearSteamLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		double cx = (GearSteamLayout.COMPANION_X[0] + GearSteamLayout.COMPANION_X[1]) / 2;
		stair("companion to the hold", cx, GearSteamLayout.COMPANION_Z[0] - 0.5, GearSteamLayout.COMPANION_Z[1] + 0.5, M, H, CLOSED);
		double ex = (GearSteamLayout.ENGINE_STAIR_X[0] + GearSteamLayout.ENGINE_STAIR_X[1]) / 2;
		stair("engine room stair to the hold", ex, GearSteamLayout.ENGINE_STAIR_Z[0] + 0.75, GearSteamLayout.ENGINE_STAIR_Z[1] - 0.5, M, H, CLOSED);
		double px = (GearSteamLayout.POOP_STEP_X[0] + GearSteamLayout.POOP_STEP_X[1]) / 2 - 0.1;
		stair("steps down to the poop deck (port)", px, GearSteamLayout.POOP_FRONT_Z + 0.5, GearSteamLayout.POOP_FRONT_Z - 2.0, E, P, CLOSED);
		stair("steps down to the poop deck (starboard)", -px, GearSteamLayout.POOP_FRONT_Z + 0.5, GearSteamLayout.POOP_FRONT_Z - 2.0, E, P,
				CLOSED);
		// the ladders: climbable columns from the deck to the level above, with a gap in the railing at the top
		ladder("ladder to the engine house roof (port)", (GearSteamLayout.ROOF_LADDER_X[0] + GearSteamLayout.ROOF_LADDER_X[1]) / 2,
				(GearSteamLayout.ROOF_LADDER_Z[0] + GearSteamLayout.ROOF_LADDER_Z[1]) / 2, M, E, -1);
		ladder("ladder to the engine house roof (starboard)", -(GearSteamLayout.ROOF_LADDER_X[0] + GearSteamLayout.ROOF_LADDER_X[1]) / 2,
				(GearSteamLayout.ROOF_LADDER_Z[0] + GearSteamLayout.ROOF_LADDER_Z[1]) / 2, M, E, -1);
		ladder("ladder to the bridge", (GearSteamLayout.BRIDGE_LADDER_X[0] + GearSteamLayout.BRIDGE_LADDER_X[1]) / 2,
				(GearSteamLayout.BRIDGE_LADDER_Z[0] + GearSteamLayout.BRIDGE_LADDER_Z[1]) / 2, P, B, 1);
	}

	/** A ladder column at (x, z) from y0 up to y1, the top giving onto the floor at y1 a block towards dz. */
	private static void ladder(String name, double x, double z, double y0, double y1, int dz) {
		for (double y = y0 + 0.25; y < y1 + 0.5; y += 0.5) {
			assertTrue(GRID.ladderAt(x, y, z), name + ": climbable at y " + y);
		}
		double zt = z + dz * 0.9;
		assertEquals(y1, floorUnder(x, y1 + 0.1, zt, CLOSED), 1e-9, name + ": floor at the top");
		assertTrue(fits(x, y1, zt, CLOSED), name + ": free at the top");
	}

	@Test
	void doors() {
		double[][] at = {
				{0, M, GearSteamLayout.ENGINE_FRONT_Z - 0.25, GearSteamLayout.ENGINE_DOOR},
				{3.0, M, GearSteamLayout.POOP_FRONT_Z, GearSteamLayout.CREW_DOOR},
				{0, M, GearSteamLayout.TRANSOM_Z + 0.25, GearSteamLayout.GALLERY_DOOR},
				{-0.5, P, GearSteamLayout.DECKHOUSE_Z[0] + 0.25, GearSteamLayout.CABIN_DOOR}};
		for (double[] d : at) {
			int k = (int) d[3];
			assertFalse(fits(d[0], d[1], d[2], CLOSED), "door " + k + " closed");
			assertTrue(fits(d[0], d[1], d[2], OPEN), "door " + k + " open");
			assertNotNull(GRID.doorCenter(k), "door " + k);
		}
		double[] c = GRID.doorCenter(GearSteamLayout.ENGINE_DOOR);
		ShipGeometry.Pick p = G.pick(ORIGIN, c[0], c[1], c[2] + 2.0, 0, 0, -1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DOOR, p.kind());
		assertEquals(GearSteamLayout.ENGINE_DOOR, p.seat());
	}

	/**
	 * The furniture (phase 2): the decoration mods' blocks first, every room furnished, enough seats, nothing poking
	 * through the hull or the walls (every block's centre is in an open cell: a room, a deck or its own furniture
	 * cell, inside the hull side under the main deck), the solid pieces in the grid.
	 */
	@Test
	void furniture() {
		InteriorDecor d = G.decor();
		assertTrue(d.blocks().size() >= 100, "furniture of the decoration mods " + d.blocks().size());
		assertTrue(d.seats().size() >= 18, "seats " + d.seats().size());
		for (String mod : new String[] {"farmhouse_decorations:", "furnish:", "farmersdelight:", "landsoficaria:"}) {
			assertTrue(d.blocks().stream().anyMatch(b -> b.block().startsWith(mod)), "uses " + mod);
		}
		// every room has its furniture: a few blocks whose centre lies in each room's box
		double[][] rooms = {{-2.5, 2.5, P, P + 3, GearSteamLayout.DECKHOUSE_Z[0] + 0.5, GearSteamLayout.CABIN_FRONT_Z},
				{-4.5, 4.5, M, P, GearSteamLayout.TRANSOM_Z + 0.5, -7.0}, {-4.5, 4.5, M, E, -6.0, 4.5},
				{-4.5, 4.5, H, M, -15.5, 15.0}};
		String[] names = {"captain's cabin", "crew quarters", "engine room", "hold"};
		int[] least = {8, 20, 4, 30};
		for (int r = 0; r < rooms.length; r++) {
			double[] b = rooms[r];
			long n = d.blocks().stream().filter(k -> k.x() > b[0] && k.x() < b[1] && k.y() >= b[2] - 0.01 && k.y() < b[3] && k.z() > b[4]
					&& k.z() < b[5]).count();
			assertTrue(n >= least[r], names[r] + ": " + n + " pieces of furniture");
		}
		for (InteriorDecor.Block b : d.blocks()) {
			int i = (int) Math.floor((b.x() - GRID.x0) / GRID.cell);
			int j = (int) Math.floor((b.y() + 0.1 - GRID.y0) / GRID.cell);
			int k = (int) Math.floor((b.z() - GRID.z0) / GRID.cell);
			byte kind = GRID.kind(i, j, k);
			assertTrue(kind != InteriorGrid.SOLID, b.block() + " at " + b.x() + ", " + b.y() + ", " + b.z() + " stands in the hull or a wall");
			if (b.y() < M) {
				assertTrue(Math.abs(b.x()) < T.hull().halfWidth(b.z()) - 0.4, b.block() + " inside the hull at z " + b.z());
			}
		}
		int furniture = 0;
		for (int i = 0; i < GRID.nx; i++) {
			for (int j = 0; j < GRID.ny; j++) {
				for (int k = 0; k < GRID.nz; k++) {
					furniture += GRID.kind(i, j, k) == InteriorGrid.FURNITURE ? 1 : 0;
				}
			}
		}
		assertTrue(furniture > 600, "solid furniture cells " + furniture);
	}

	/**
	 * With the furniture in place, every room, deck and seat is still reached from the waist by walking, climbing the
	 * stairs and the ladders with every door open (standing places of a 1 x 1 block footprint and 2 blocks of head
	 * room, as tools/gear_steam_interior.walkable_report checks).
	 */
	@Test
	void furnishedRoomsAreConnected() {
		int nx = GRID.nx, ny = GRID.ny, nz = GRID.nz;
		boolean[] pass = new boolean[nx * ny * nz];
		boolean[] lad = new boolean[nx * ny * nz];
		for (int i = 0; i < nx; i++) {
			for (int j = 0; j < ny; j++) {
				for (int k = 0; k < nz; k++) {
					byte kind = GRID.kind(i, j, k);
					int idx = (i * ny + j) * nz + k;
					pass[idx] = kind == InteriorGrid.OUT || kind == InteriorGrid.DRY || kind == InteriorGrid.LADDER || kind >= InteriorGrid.DOOR;
					lad[idx] = kind == InteriorGrid.LADDER;
				}
			}
		}
		int[] start = {cellX(-2.0), (int) Math.round((M - GRID.y0) / GRID.cell), cellZ(6.0)};
		assertTrue(stand(pass, lad, start[0], start[1], start[2]), "start on the waist");
		Set<Long> seen = new HashSet<>();
		ArrayDeque<int[]> q = new ArrayDeque<>();
		q.add(start);
		seen.add(key(start[0], start[1], start[2]));
		while (!q.isEmpty()) {
			int[] c = q.poll();
			boolean onLadder = any(lad, c[0], c[1], c[2], 2, 2, 2);
			for (int[] mv : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}, {0, 0}}) {
				boolean step = mv[0] != 0 || mv[1] != 0;
				int[] dys = step ? new int[] {-1, 0, 1, -2, -3, -4, -5, -6} : new int[] {};
				if (onLadder) {
					dys = java.util.stream.IntStream.concat(java.util.Arrays.stream(dys), java.util.stream.IntStream.of(1, -1)).toArray();
				}
				for (int dy : dys) {
					int i = c[0] + mv[0], j = c[1] + dy, k = c[2] + mv[1];
					if (!seen.contains(key(i, j, k)) && stand(pass, lad, i, j, k)) {
						seen.add(key(i, j, k));
						q.add(new int[] {i, j, k});
					}
				}
			}
		}
		double[][] places = {{0.0, F, 14.0}, {3.6, E, 1.0}, {1.5, P, -14.0}, {0.0, B, -10.0}, {3.0, M, -2.0}, {0.0, M, -9.0}, {0.0, M, -14.8},
				{0.0, P, -9.8}, {0.0, H, -12.0}, {0.0, H, 12.0}, {0.0, M, -18.8}, {-2.75, M, -0.5}, {-2.75, H, -5.2}, {1.2, P, -17.0}};
		String[] where = {"forecastle", "engine house roof", "poop deck", "bridge", "engine room (by the aft door)", "crew quarters (forward)",
				"crew quarters (by the galley)", "captain's cabin", "hold (aft)", "hold (forward)", "stern gallery", "engine room stair's head",
				"engine room stair's foot in the hold", "poop deck over the gallery"};
		for (int p = 0; p < places.length; p++) {
			assertTrue(reached(seen, places[p][0], places[p][1], places[p][2], 2), where[p] + " reached from the waist");
		}
		for (InteriorDecor.SeatSpot s : G.decor().seats()) {
			assertTrue(reached(seen, s.dismountX(), s.dismountY() - 0.02, s.dismountZ(), 1),
					"the stand-up spot of the seat at " + s.x() + ", " + s.y() + ", " + s.z() + " reached from the waist");
		}
		assertTrue(seen.size() > 2000, "standing places " + seen.size());
	}

	private static int cellX(double x) {
		return (int) Math.floor((x - 0.5 - GRID.x0) / GRID.cell) + 1;
	}

	private static int cellZ(double z) {
		return (int) Math.floor((z - 0.5 - GRID.z0) / GRID.cell) + 1;
	}

	/** A standing place (its footprint's min corner cell) within r cells of the point (x, floor, z). */
	private static boolean reached(Set<Long> seen, double x, double floor, double z, int r) {
		int j = (int) Math.round((floor - GRID.y0) / GRID.cell);
		int i0 = (int) Math.floor((x - GRID.x0) / GRID.cell) - 1, k0 = (int) Math.floor((z - GRID.z0) / GRID.cell) - 1;
		for (int di = -r; di <= r + 1; di++) {
			for (int dk = -r; dk <= r + 1; dk++) {
				if (seen.contains(key(i0 + di, j, k0 + dk))) {
					return true;
				}
			}
		}
		return false;
	}

	private static long key(int i, int j, int k) {
		return ((long) i * 4096 + j) * 4096 + k;
	}

	private static boolean any(boolean[] m, int i0, int j0, int k0, int di, int dj, int dk) {
		for (int i = i0; i < i0 + di; i++) {
			for (int j = j0; j < j0 + dj; j++) {
				for (int k = k0; k < k0 + dk; k++) {
					if (i >= 0 && j >= 0 && k >= 0 && i < GRID.nx && j < GRID.ny && k < GRID.nz && m[(i * GRID.ny + j) * GRID.nz + k]) {
						return true;
					}
				}
			}
		}
		return false;
	}

	/** A 1 x 1 block footprint (2 x 2 cells from (i, k)) with 2 blocks of head room, on a floor or a ladder. */
	private static boolean stand(boolean[] pass, boolean[] lad, int i, int j, int k) {
		if (i < 0 || k < 0 || i + 1 >= GRID.nx || k + 1 >= GRID.nz || j < 1 || j + 4 > GRID.ny) {
			return false;
		}
		for (int a = i; a < i + 2; a++) {
			for (int b = j; b < j + 4; b++) {
				for (int c = k; c < k + 2; c++) {
					if (!pass[(a * GRID.ny + b) * GRID.nz + c]) {
						return false;
					}
				}
			}
		}
		if (any(lad, i, j - 1, k, 2, 2, 2)) {
			return true;
		}
		for (int a = i; a < i + 2; a++) {
			for (int c = k; c < k + 2; c++) {
				if (!pass[(a * GRID.ny + j - 1) * GRID.nz + c]) {
					return true;
				}
			}
		}
		return false;
	}

	@Test
	void helmAndSeats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertEquals(B + 0.28, pilot.y(), 1e-9, "the pilot stands on the bridge");
		assertTrue(Math.abs(pilot.z() - GearSteamLayout.HELM_Z) < 1.2, "behind the wheel");
		assertTrue(G.seats().size() >= 19, "the pilot and the passengers: " + G.seats().size());
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1], d[2], CLOSED), "free stand-up spot of seat " + s.index());
			double floor = floorUnder(d[0], d[1], d[2], CLOSED);
			assertTrue(d[1] - floor < 0.1 && d[1] - floor >= 0, "seat " + s.index() + " stands up on a floor (" + floor + ")");
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, B + 1.6, GearSteamLayout.HELM_Z - 2.0, 0, -0.2, 1, 4);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	@Test
	void boardingSpotIsOnTheWaist() {
		for (double z = 5.0; z <= 11.0; z += 1.5) {
			double[] b = G.boardingSpot(5.5, z);
			assertEquals(M + 0.02, b[1], 1e-9, "boarding at " + z);
			assertTrue(fits(b[0], b[1], b[2], CLOSED), "free boarding spot at " + z);
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 9.0, 1.0, 0, -1, 0, 0, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	@Test
	void gangplank() {
		Gangplank.Spec s = Gangplank.load("gear_steamship");
		assertNotNull(s, "gangplanks/gear_steamship.json");
		assertEquals(GearSteamLayout.WAIST_BULWARK_TOP, s.hy(), 1e-9, "hinged on the waist bulwark");
		assertTrue(s.hx() < 0 && s.hz() > GearSteamLayout.ENGINE_FRONT_Z && s.hz() < GearSteamLayout.FORECASTLE_Z,
				"on the starboard waist");
	}

	private static BbModel load() throws Exception {
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/gear_steamship.bbmodel"),
				StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void model() throws Exception {
		BbModel m = load();
		for (String bone : new String[] {"hull", "upperworks", "deck", "bow", "rooms", "furniture", "fittings", "detail", "helm_wheel", "rudder",
				"mast_main", "mast_mizzen", "sail_main_sail", "sail_mizzen_sail", "gear_big_p", "gear_big_s", "gear_bow_p", "gear_bow_s",
				"gear_funnel_a_p", "lantern_bow", "lantern_dome", "lantern_gallery_s", "crate_hang", "door_0_a", "door_3_b", "gear_flywheel",
				"piston_0", "piston_1"}) {
			assertNotNull(m.bonesByName.get(bone), "bone " + bone);
		}
		for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "lantern_sway", "engine", "door_0", "door_1", "door_2", "door_3"}) {
			assertNotNull(m.animations.get(anim), "animation " + anim);
		}
		assertEquals(2, m.textureCount(), "the hull atlas and the sail atlas");
		int[] n = {0};
		int[] sailFaces = {0};
		m.render(m.newPose(), 1, (p, uv, nn, glow) -> sailFaces[0]++);
		m.render(m.newPose(), (p, uv, nn, glow) -> n[0]++);
		assertTrue(n[0] > 8000 && n[0] < 60000, "faces " + n[0]);
		assertTrue(sailFaces[0] > 150, "the sails are drawn with the sail atlas: " + sailFaces[0]);
		for (InteriorDecor.Block b : G.decor().blocks()) {
			assertNotNull(m.bonesByName.get(b.fallback()), "stand-in of " + b.block());
		}
	}

	/** Every vertex of the model with one animation applied at time t (none if null). */
	private static float[] vertices(BbModel m, String anim, float t) {
		BbModel.Pose pose = m.newPose();
		if (anim != null) {
			m.apply(pose, anim, t, 1f);
		}
		java.util.List<float[]> quads = new java.util.ArrayList<>();
		m.render(pose, (p, uv, nn, glow) -> quads.add(p.clone()));
		float[] v = new float[quads.size() * 12];
		for (int i = 0; i < quads.size(); i++) {
			System.arraycopy(quads.get(i), 0, v, i * 12, 12);
		}
		return v;
	}

	private static double maxMove(float[] a, float[] b) {
		double max = 0;
		for (int i = 0; i + 2 < Math.min(a.length, b.length); i += 3) {
			max = Math.max(max, Math.sqrt(Math.pow(a[i] - b[i], 2) + Math.pow(a[i + 1] - b[i + 1], 2) + Math.pow(a[i + 2] - b[i + 2], 2)));
		}
		return max;
	}

	/** The gears turn with the engine (and join up when the loop wraps), the helm turns the wheel and the rudder. */
	@Test
	void animations() throws Exception {
		BbModel m = load();
		float[] rest = vertices(m, null, 0);
		double turn = maxMove(rest, vertices(m, "engine", 1.0f));
		assertTrue(turn > 0.5 && turn < 6.0, "the gears turn: " + turn);
		assertTrue(maxMove(vertices(m, "engine", 0f), vertices(m, "engine", 4.0f)) < 1e-3, "the engine loop joins up");
		assertTrue(maxMove(vertices(m, "engine", 0.5f), vertices(m, "engine", 1.5f)) > 0.3, "the engine room's flywheel and pistons run");
		assertTrue(maxMove(rest, vertices(m, "steer", 2.0f)) > 0.3, "the helm turns the wheel and the rudder");
		float[] furled = vertices(m, "sail_furl", 1.0f);
		assertTrue(furled.length < rest.length || maxMove(rest, furled) > 2.0, "the sails furl");
	}
}
