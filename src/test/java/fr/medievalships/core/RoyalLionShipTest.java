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
 * The Royal Lion Ship: hull shape (same numbers as tools/royal_lion_shape.py: P4, the higher freeboard and the strong
 * sheer), dimensions, interior grid (the main deck, the forecastle, the quarterdeck, the captain's cabin, the royal
 * state room in the castle's upper storey, the crew quarters, the cargo hold, the stairs and companionways between
 * them, the four doors, no way out through the hull), the seats, the boarding spot and the model (bones, animations,
 * the sails with their gold lions, the shields and banners, the leaping lion figurehead).
 */
class RoyalLionShipTest {
	private static final ShipType T = Ships.ROYAL_LION_SHIP;
	private static final ShipGeometry G = T.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final InteriorGrid.State OPEN = new InteriorGrid.State(0xFFFFFFFFL, 0f);
	private static final double M = RoyalLionLayout.MAIN_DECK_Y, L = RoyalLionLayout.LOWER_FLOOR_Y, Q = RoyalLionLayout.QUARTERDECK_Y,
			C = RoyalLionLayout.CABIN_FLOOR_Y, F = RoyalLionLayout.FORECASTLE_Y, S = RoyalLionLayout.STATEROOM_FLOOR_Y;

	/** Values printed by {@code python3 tools/royal_lion_shape.py}: z, half width, rail, keel, bottom at 2 blocks out. */
	@Test
	void matchesShapeGenerator() {
		double[][] rows = {
				{-20.0, 4.610249, 7.9, -1.0, -0.903596},
				{-12.0, 5.838576, 7.132, -2.911083, -2.689486},
				{0.0, 6.0, 6.7, -3.6, -3.333333},
				{10.5, 5.352171, 7.69225, -3.113159, -2.854642},
				{17.0, 3.426553, 9.301, -1.896028, -1.45297}};
		HullShape h = T.hull();
		for (double[] r : rows) {
			assertEquals(r[1], h.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			double floor = r[0] < RoyalLionLayout.CABIN_FRONT_Z ? Q + 1.0 : r[0] > RoyalLionLayout.FORECASTLE_Z ? F + 1.0 : Double.NEGATIVE_INFINITY;
			assertEquals(Math.max(r[2], floor), h.railY(r[0]), 1e-5, "rail (the sheer, or the castle's bulwark) at " + r[0]);
			assertEquals(r[3], h.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], h.bottomY(r[0], 2.0), 1e-5, "bottom at " + r[0]);
		}
	}

	@Test
	void dimensionsAndRegistration() {
		assertTrue(RoyalLionLayout.FORE_MAST_Z > 0 && RoyalLionLayout.MAIN_MAST_Z < 0.5 && RoyalLionLayout.MIZZEN_Z < RoyalLionLayout.CABIN_FRONT_Z,
				"fore mast forward, main mast amidships, mizzen on the quarterdeck");
		assertTrue(RoyalLionLayout.MAIN_MAST_TOP > RoyalLionLayout.FORE_MAST_TOP && RoyalLionLayout.FORE_MAST_TOP > RoyalLionLayout.MIZZEN_TOP,
				"the main mast is the tallest, the mizzen the shortest");
		assertEquals(T, Ships.byId("royal_lion_ship"));
		assertTrue(Ships.ALL.contains(T));
		assertNotNull(GRID);
		assertNotNull(G.decor());
		assertFalse(G.submarine());
		assertFalse(G.flying());
		assertEquals(40.0, 2 * RoyalLionLayout.HALF_LENGTH, 1e-9, "hull length");
		double overall = RoyalLionLayout.BOWSPRIT_TIP[2] - RoyalLionLayout.TRANSOM_Z;
		assertTrue(overall > 48 && overall < 54, "length with the bowsprit " + overall);
		assertEquals(12.0, 2 * RoyalLionLayout.MAX_HALF_WIDTH, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 32 && height < 36, "height from the keel to the main masthead " + height);
		assertTrue(RoyalLionLayout.MAIN_MAST_TOP >= 30 && RoyalLionLayout.MAIN_MAST_TOP <= 36, "masts about 30-36 high");
		assertTrue(G.boundingRadius() > RoyalLionLayout.BOWSPRIT_TIP[2]);
		// bigger than the frigate, smaller than the great warship
		assertTrue(T.hull().halfLength > Ships.BLUE_FRIGATE.hull().halfLength && T.hull().halfLength < Ships.WARSHIP.hull().halfLength);
		ShipConfig c = T.defaults().get(), frigate = Ships.BLUE_FRIGATE.defaults().get();
		assertTrue(c.dive == null && c.flight == null, "a sailing ship");
		assertTrue(c.maxTurnRate <= frigate.maxTurnRate && c.acceleration <= frigate.acceleration && c.waterDrag <= frigate.waterDrag,
				"at least as heavy as the frigate");
		boolean bowsprit = false, stern = false, lion = false, paw = false, headRail = false, yard = false;
		for (double[] p : G.probes()) {
			bowsprit |= p[2] > RoyalLionLayout.BOWSPRIT_TIP[2] - 0.5;
			stern |= p[2] < RoyalLionLayout.STERN_REACH_Z + 0.3;
			lion |= Math.abs(p[2] - RoyalLionLayout.FIGUREHEAD_PROBE[2]) < 0.1 && Math.abs(p[1] - RoyalLionLayout.FIGUREHEAD_PROBE[1]) < 0.1;
			paw |= Math.abs(p[2] - RoyalLionLayout.FIGUREHEAD_PAW_PROBE[2]) < 0.1;
			headRail |= Math.abs(p[2] - RoyalLionLayout.HEAD_RAIL_PROBE[2]) < 0.1;
			yard |= Math.abs(p[0]) > RoyalLionLayout.YARD_HALF * 0.8;
		}
		assertTrue(bowsprit && stern && lion && paw && headRail && yard, "probes at the bowsprit, the stern, the lion, the head rail, the yard arms");
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
		room("main deck (waist)", -1.4, 1.4, M, 1.0, 5.0, false);
		room("main deck (aft of the main mast)", 0.0, 1.8, M, -4.0, -1.6, false);
		room("main deck (forward)", -1.6, 1.6, M, 7.0, 10.5, false);
		room("forecastle", -1.6, 1.6, F, 14.0, 17.0, false);
		room("quarterdeck (by the wheel)", -1.8, 1.8, Q, -10.6, -9.9, false);
		room("quarterdeck (beside the mizzen)", 1.2, 2.4, Q, -11.6, -9.0, false);
		room("quarterdeck (beside the mizzen, starboard)", -2.4, -1.2, Q, -11.6, -9.0, false);
		room("captain's cabin (middle)", -0.8, 0.8, C, -18.0, -9.0, true);
		room("royal state room (beside the table, port)", 1.8, 2.4, S, -17.6, -14.4, true);
		room("royal state room (beside the table, starboard)", -2.4, -1.8, S, -17.6, -14.4, true);
		room("royal state room (by the doors)", -2.4, 2.4, S, -13.2, -13.0, true);
		room("crew quarters (beside the companionway)", -0.1, 1.4, L, -14.0, -3.5, true);
		room("crew quarters (aft of the companionway)", -1.8, 1.4, L, -13.5, -8.0, true);
		room("cargo hold (centre line)", -0.8, 0.8, L, -2.0, -1.8, true);
		room("cargo hold (forward)", -0.8, 0.8, L, 0.5, 11.0, true);
		room("cargo hold (before the fore mast)", -0.8, 0.8, L, 13.4, 13.6, true);
		assertTrue(RoyalLionLayout.ROUNDHOUSE_FRONT_Z - RoyalLionLayout.TRANSOM_Z >= 7.9, "the castle's upper storey is about 8 blocks long");
		assertTrue(RoyalLionLayout.CABIN_FRONT_Z - RoyalLionLayout.TRANSOM_Z >= 11.9, "the stern castle is 12 blocks long");
		assertTrue(RoyalLionLayout.FORE_MAST_Z - RoyalLionLayout.MAIN_MAST_Z >= 12.5, "the fore and main masts are spread as on the pictures");
		assertTrue(T.hull().railY(19.9) - T.hull().railY(0) > 3.0, "the strong sheer rising to the bow");
		assertFalse(fits(-3.4, C, -15.0, CLOSED), "the captain's desk is solid");
		assertFalse(fits(-4.2, L, 4.5, CLOSED), "a crate in the hold");
		// outside the hull: the sea, not carried; the hull sides and the bottom are solid
		assertFalse(GRID.dryAt(8.0, -1.0, 0, CLOSED));
		assertFalse(G.inCarryVolume(8.0, M + 0.5, 0));
		assertTrue(GRID.solidAt(5.8, 0.0, 0, CLOSED), "hull side");
		assertTrue(GRID.solidAt(0.0, -3.0, 0, CLOSED), "keel");
		assertTrue(G.insideHull(0, -1.0, 0));
		// the bulwarks keep the walkers aboard
		assertFalse(fits(5.4, M, 0, CLOSED), "bulwark");
		assertFalse(fits(4.6, F, 16.0, CLOSED), "forecastle bulwark");
		assertFalse(fits(4.8, Q, -12.0, CLOSED), "quarterdeck bulwark");
		double rf = RoyalLionLayout.ROUNDHOUSE_FRONT_Z - 0.25;
		for (double x : new double[] {1.75, -1.75}) {
			assertFalse(fits(x, Q, rf, CLOSED), "the state room's closed door at " + x);
			assertTrue(fits(x, Q, rf, OPEN), "the state room's open door at " + x);
		}
		assertFalse(fits(3.6, Q, rf, CLOSED), "the state room's front wall");
		assertFalse(fits(0, Q, rf, OPEN), "the state room's front wall behind the mizzen");
		assertFalse(fits(0, S, -19.8, CLOSED), "the stern wall");
		// the masts stop the walkers: the fore and main masts on deck and through the hold, the mizzen on the quarterdeck
		assertFalse(fits(0, M, RoyalLionLayout.FORE_MAST_Z, CLOSED), "fore mast on deck");
		assertFalse(fits(0, L, RoyalLionLayout.FORE_MAST_Z, CLOSED), "fore mast through the hold");
		assertFalse(fits(0, M, RoyalLionLayout.MAIN_MAST_Z, CLOSED), "main mast on deck");
		assertFalse(fits(0, L, RoyalLionLayout.MAIN_MAST_Z, CLOSED), "main mast through the hold");
		assertFalse(fits(0, Q, RoyalLionLayout.MIZZEN_Z, CLOSED), "mizzen on the quarterdeck");
		assertTrue(fits(0, C, RoyalLionLayout.MIZZEN_Z, CLOSED), "the cabin under the mizzen stays clear");
		assertFalse(fits(0, M, RoyalLionLayout.FORE_MAST_Z, CLOSED), "fore mast at the forecastle's break");
		// the bulkhead between the crew quarters and the hold, its door
		assertFalse(fits(2.5, L, -2.75, CLOSED), "the bulkhead");
		assertFalse(fits(0, L, -2.75, CLOSED), "the bulkhead's closed door");
		assertTrue(fits(0, L, -2.75, OPEN), "the bulkhead's open door");
	}

	/** No cell of the rooms (and nothing under the main deck) opens on the sea: the hull is closed all round. */
	@Test
	void noWayOutThroughTheHull() {
		for (double z = -19.5; z <= 14.5; z += 0.5) {
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
			for (double y = -3.0; y < L; y += 0.5) {
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
		double qx = (RoyalLionLayout.QD_STAIR_X[0] + RoyalLionLayout.QD_STAIR_X[1]) / 2;
		stair("quarterdeck stair (port)", qx, RoyalLionLayout.QD_STAIR_Z[0] + 0.5, RoyalLionLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		stair("quarterdeck stair (starboard)", -qx, RoyalLionLayout.QD_STAIR_Z[0] + 0.5, RoyalLionLayout.QD_STAIR_Z[1] - 0.75, M, Q, CLOSED);
		double fx = (RoyalLionLayout.FC_STAIR_X[0] + RoyalLionLayout.FC_STAIR_X[1]) / 2;
		stair("forecastle stair (port)", fx, RoyalLionLayout.FC_STAIR_Z[0] - 0.5, RoyalLionLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		stair("forecastle stair (starboard)", -fx, RoyalLionLayout.FC_STAIR_Z[0] - 0.5, RoyalLionLayout.FC_STAIR_Z[1] + 0.75, M, F, CLOSED);
		double cx = (RoyalLionLayout.CREW_STAIR_X[0] + RoyalLionLayout.CREW_STAIR_X[1]) / 2;
		stair("companionway to the crew quarters", cx, RoyalLionLayout.CREW_STAIR_Z[1] + 0.75, RoyalLionLayout.CREW_STAIR_Z[0] - 0.5, M, L, CLOSED);
		double hx = (RoyalLionLayout.HOLD_STAIR_X[0] + RoyalLionLayout.HOLD_STAIR_X[1]) / 2;
		stair("companionway to the hold", hx, RoyalLionLayout.HOLD_STAIR_Z[1] + 0.75, RoyalLionLayout.HOLD_STAIR_Z[0] - 0.5, M, L, CLOSED);
		assertEquals(L, floorUnder(0.5, L, RoyalLionLayout.HOLD_STAIR_Z[0] - 0.5, CLOSED), 1e-9);
		assertTrue(fits(0.5, L, RoyalLionLayout.HOLD_STAIR_Z[0] - 0.5, CLOSED));
	}

	@Test
	void doors() {
		double z = RoyalLionLayout.CABIN_FRONT_Z - 0.25;
		assertFalse(fits(0, C, z, CLOSED), "the closed cabin door");
		assertTrue(fits(0, C, z, OPEN), "the open cabin door");
		for (int d : new int[] {RoyalLionLayout.CABIN_DOOR, RoyalLionLayout.STATEROOM_DOOR, RoyalLionLayout.BULKHEAD_DOOR,
				RoyalLionLayout.STATEROOM_DOOR_S}) {
			assertNotNull(GRID.doorCenter(d), "door " + d);
		}
		double[] c = GRID.doorCenter(RoyalLionLayout.CABIN_DOOR);
		ShipGeometry.Pick p = G.pick(ORIGIN, c[0], c[1], c[2] + 2.0, 0, 0, -1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DOOR, p.kind());
		assertEquals(RoyalLionLayout.CABIN_DOOR, p.seat());
		for (int d : new int[] {RoyalLionLayout.STATEROOM_DOOR, RoyalLionLayout.STATEROOM_DOOR_S}) {
			c = GRID.doorCenter(d);
			assertTrue(Math.abs(c[0]) > 1.0 && Math.abs(c[0]) < 2.5, "the state room's doors on each side of the mizzen");
			p = G.pick(ORIGIN, c[0], c[1], c[2] + 1.1, 0, 0, -1, 5);
			assertNotNull(p);
			assertEquals(ShipGeometry.PickKind.DOOR, p.kind());
			assertEquals(d, p.seat());
		}
	}

	@Test
	void helmAndSeats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertEquals(Q + 0.28, pilot.y(), 1e-9, "the pilot stands on the quarterdeck");
		assertTrue(Math.abs(pilot.z() - RoyalLionLayout.HELM_Z) < 1.2, "behind the wheel");
		assertTrue(G.seats().size() >= 8, "the pilot and several passengers: " + G.seats().size());
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1], d[2], CLOSED), "free stand-up spot of seat " + s.index());
			double floor = floorUnder(d[0], d[1], d[2], CLOSED);
			assertTrue(d[1] - floor < 0.1 && d[1] - floor >= 0, "seat " + s.index() + " stands up on a floor (" + floor + ")");
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, Q + 1.6, RoyalLionLayout.HELM_Z - 1.0, 0, -0.2, 1, 4);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	/** Decor blocks whose bottom-centre lies in the box (x0..x1, y0..y1, z0..z1). */
	private static long blocksIn(double x0, double x1, double y0, double y1, double z0, double z1) {
		return G.decor().blocks().stream().filter(b -> b.x() >= x0 && b.x() <= x1 && b.y() >= y0 && b.y() <= y1 && b.z() >= z0 && b.z() <= z1)
				.count();
	}

	/**
	 * The decoration: every room furnished with the mods' blocks (the cabin, the state room, the crew quarters, the
	 * hold, the deck cargo), lanterns that glow, vanilla paintings on the walls, a seat for many passengers; nothing
	 * stands in the walls, the decks or the hull, nor beyond the sides; the seats are in the rooms; the solid furniture
	 * keeps the walkers out (the desk, the bed, the dining table, the bunks, the crates).
	 */
	@Test
	void furnishedRooms() {
		InteriorDecor d = G.decor();
		assertTrue(d.blocks().size() >= 120, "decor blocks " + d.blocks().size());
		assertTrue(d.paintings().size() >= 3, "paintings " + d.paintings().size());
		assertTrue(G.seats().size() >= 20, "seats " + G.seats().size());
		assertTrue(d.blocks().stream().filter(InteriorDecor.Block::glow).count() >= 12, "glowing lanterns");
		assertTrue(blocksIn(-5, 5, C - 0.1, C + 1.5, -19.5, -8.5) >= 15, "the captain's cabin is furnished");
		assertTrue(blocksIn(-5, 5, S - 0.1, S + 1.5, -19.5, -12.5) >= 15, "the state room is furnished");
		assertTrue(blocksIn(-6, 6, L - 0.1, L + 1.5, -15.0, -3.0) >= 15, "the crew quarters are furnished");
		assertTrue(blocksIn(-6, 6, L - 0.1, L + 1.5, -2.5, 14.5) >= 25, "the hold is furnished");
		assertTrue(blocksIn(-6, 6, M - 0.1, M + 1.5, -8.0, 13.0) >= 15, "cargo on the main deck");
		for (InteriorDecor.Block b : d.blocks()) {
			byte k = GRID.kindAt(b.x(), b.y() + 0.05, b.z());
			assertTrue(k != 1, "decor block in a wall, a deck or the hull: " + b.block() + " at " + b.x() + ", " + b.y() + ", " + b.z());
			assertTrue(Math.abs(b.x()) < T.hull().halfWidth(b.z()) - 0.4, "decor block beyond the side: " + b.block() + " at " + b.x() + ", " + b.z());
		}
		for (InteriorDecor.Painting p : d.paintings()) {
			assertTrue(GRID.solidAt(p.x() - p.nx() * 0.3, p.y(), p.z() - p.nz() * 0.3, CLOSED), "painting on a wall: " + p.motive());
			assertFalse(GRID.solidAt(p.x() + p.nx() * 0.3, p.y(), p.z() + p.nz() * 0.3, CLOSED), "painting facing the room: " + p.motive());
		}
		for (ShipGeometry.Seat s : G.seats()) {
			assertTrue(GRID.kindAt(s.x(), s.y() - 0.2, s.z()) != 1, "seat " + s.index() + " in a wall");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " aboard");
		}
		assertFalse(fits(3.45, C, -17.0, CLOSED), "the captain's bed is solid");
		assertFalse(fits(0.0, S, -16.0, CLOSED), "the state room's table is solid");
		assertFalse(fits(4.4, L, -13.2, CLOSED), "a crew bunk is solid");
		assertFalse(fits(-4.35, M, -3.1, CLOSED), "deck cargo is solid");
		double sz = RoyalLionLayout.QD_STAIR_Z[0] + 0.4;
		assertTrue(fits(0.0, M, sz, CLOSED) && fits(3.25, M, sz, CLOSED) && fits(-3.25, M, sz, CLOSED), "the way to the quarterdeck stairs stays clear");
	}

	@Test
	void boardingSpotIsOnTheMainDeck() {
		for (double z = -3; z <= 11; z += 2.0) {
			for (double x : new double[] {7.0, -7.0}) {
				double[] b = G.boardingSpot(x, z);
				assertEquals(M + 0.02, b[1], 1e-9, "boarding at " + x + ", " + z);
				assertTrue(fits(b[0], b[1], b[2], CLOSED), "free boarding spot at " + x + ", " + z);
				assertEquals(M, floorUnder(b[0], b[1], b[2], CLOSED), 1e-9, "boarding spot on the deck (not in a hatch) at " + x + ", " + z);
			}
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 1.0, M + 1.6, 1.0, 0, -1, 0.2, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.DECK, p.kind());
		p = G.pick(ORIGIN, 10.0, 1.0, 0, -1, 0, 0, 6);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HULL, p.kind());
	}

	private static BbModel load() throws Exception {
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/royal_lion_ship.bbmodel"),
				StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	@Test
	void model() throws Exception {
		BbModel m = load();
		for (String bone : new String[] {"hull", "sterncastle", "deck", "bow", "rooms", "furniture", "fittings", "detail", "helm_wheel", "rudder",
				"mast_fore", "mast_main", "mast_mizzen", "sail_fore_course", "sail_fore_topsail", "sail_main_course", "sail_main_topsail",
				"sail_mizzen_course", "sail_jibs", "flag_fore", "flag_fore_tip", "flag_main", "flag_mizzen", "flag_stern", "flag_stern_tip",
				"lantern_stern_p", "lantern_stern_s", "lantern_bow", "lantern_hull_p0", "door_0_a", "door_0_b", "door_1_a", "door_2_b", "door_3_a",
				"rope_slack_fore_brace_p", "rope_slack_main_topmast_stay"}) {
			assertNotNull(m.bonesByName.get(bone), "bone " + bone);
		}
		assertEquals(3, m.bonesByName.keySet().stream().filter(b -> b.startsWith("mast_")).count(), "three masts");
		for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "rope_sway", "door_0", "door_1", "door_2",
				"door_3"}) {
			assertNotNull(m.animations.get(anim), "animation " + anim);
		}
		assertEquals(2, m.textureCount(), "the hull atlas and the sail atlas");
		int[] n = {0};
		int[] sailFaces = {0};
		m.render(m.newPose(), 1, (p, uv, nn, glow) -> sailFaces[0]++);
		m.render(m.newPose(), (p, uv, nn, glow) -> n[0]++);
		assertTrue(n[0] > 8000 && n[0] < 70000, "faces " + n[0]);
		assertTrue(sailFaces[0] > 400, "the sails are drawn with the sail atlas: " + sailFaces[0]);
		for (InteriorDecor.Block b : G.decor().blocks()) {
			assertNotNull(m.bonesByName.get(b.fallback()), "stand-in of " + b.block());
		}
		// the figurehead reaches the probed point, nothing of the hull goes beyond the bowsprit, the stern reach
		float[] ext = {Float.MAX_VALUE, -Float.MAX_VALUE};
		m.render(m.newPose(), (p, uv, nn, glow) -> {
			for (int i = 0; i < 12; i += 3) {
				ext[0] = Math.min(ext[0], p[i + 2]);
				ext[1] = Math.max(ext[1], p[i + 2]);
			}
		});
		assertTrue(ext[1] <= RoyalLionLayout.BOWSPRIT_TIP[2] + 1.0, "nothing beyond the jib-boom: " + ext[1]);
		assertTrue(ext[0] >= RoyalLionLayout.STERN_REACH_Z - 0.3, "nothing aft of the stern reach: " + ext[0]);
	}

	/** Every vertex of the model with one animation applied at time t (none if null). */
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

	/** The looping animations join up when they wrap; the helm turns the wheel and the rudder; the sails fill and furl. */
	@Test
	void animations() throws Exception {
		BbModel m = load();
		float[] rest = vertices(m, null, 0f);
		for (String anim : new String[] {"sail_wind", "flag_wave", "lantern_sway", "rope_sway"}) {
			float len = m.animations.get(anim).length;
			float[] start = vertices(m, anim, 0f);
			assertTrue(moved(start, vertices(m, anim, len - 1e-3f))[0] < 0.02, anim + " jumps when it wraps");
			assertTrue(moved(start, vertices(m, anim, 1e-3f))[0] < 0.02, anim + " jumps at its start");
		}
		assertTrue(moved(rest, vertices(m, "flag_wave", 0.6f))[0] > 0.3, "the pennants wave");
		assertTrue(moved(rest, vertices(m, "lantern_sway", 0.6f))[0] > 0.02, "the lanterns swing");
		double wind = moved(rest, vertices(m, "sail_wind", 0.9f))[0];
		assertTrue(wind > 0.08 && wind < 1.2, "the sails fill and slacken in the wind, a little: " + wind);
		assertTrue(moved(vertices(m, "steer", 1f), vertices(m, "steer", 2f))[0] > 0.5, "the wheel and the rudder turn");
		assertTrue(moved(rest, vertices(m, "sail_furl", 0.5f))[0] > 2, "the sails furl");
		double rope = moved(rest, vertices(m, "rope_sway", 1.2f))[0];
		assertTrue(rope > 0.04 && rope < 0.4, "the slack ropes swing a little: " + rope);
	}
}
