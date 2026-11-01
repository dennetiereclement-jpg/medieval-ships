package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The Rowboat: shape (same numbers as tools/rowboat_shape.py), size, seats (two, seated players dry), the whole boat as
 * its "helm", floating on a single block of water, oars, and a lighter handling than the galleys.
 */
class RowboatTest {
	private static final ShipType TYPE = Ships.ROWBOAT;
	private static final ShipGeometry G = TYPE.geometry();
	private static final HullShape H = G.hull();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);

	/** Values printed by {@code python3 tools/rowboat_shape.py}: z, half width, rail, keel, bottom at 0.6. */
	@Test
	void matchesModelGenerator() {
		double[][] expected = {
				{-2.5, 0.254522, 1.040000, -0.080000, -0.012000},
				{-2.0, 0.629707, 0.925548, -0.173104, -0.032961},
				{-1.0, 0.933021, 0.804007, -0.288030, -0.203616},
				{0.0, 1.000000, 0.780000, -0.320000, -0.240000},
				{1.0, 0.937343, 0.810470, -0.288030, -0.204470},
				{2.0, 0.649425, 0.964734, -0.173104, -0.044745},
				{2.5, 0.278833, 1.110000, -0.080000, -0.012000}};
		for (double[] r : expected) {
			assertEquals(r[1], H.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			assertEquals(r[1], RowboatLayout.halfWidth(r[0]), 1e-5, "layout half width at " + r[0]);
			assertEquals(r[2], H.railY(r[0]), 1e-5, "rail at " + r[0]);
			assertEquals(r[2], RowboatLayout.railY(r[0]), 1e-5, "layout rail at " + r[0]);
			assertEquals(r[3], H.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[3], RowboatLayout.keelY(r[0]), 1e-5, "layout keel at " + r[0]);
			assertEquals(r[4], H.bottomY(r[0], 0.6), 1e-5, "bottom at " + r[0]);
		}
		double[] pivot = RowboatLayout.oarPivot(1);
		assertEquals(1.074415, pivot[0], 1e-5);
		assertEquals(0.941988, pivot[1], 1e-5);
		assertEquals(0.35, pivot[2], 1e-9);
		assertEquals(-1.074415, RowboatLayout.oarPivot(-1)[0], 1e-5);
	}

	@Test
	void dimensions() {
		assertEquals(TYPE, Ships.byId("rowboat"));
		assertTrue(Ships.ALL.contains(TYPE));
		assertFalse(G.flying());
		assertFalse(G.submarine());
		assertEquals(5.0, 2 * H.halfLength, 1e-9, "hull length");
		assertEquals(5.44, 2 * H.tip, 1e-9, "post to post");
		assertEquals(2.0, 2 * H.maxHalfWidth, 1e-9, "beam");
		assertTrue(2 * H.halfLength / (2 * H.maxHalfWidth) > 2.3 && 2 * H.halfLength / (2 * H.maxHalfWidth) < 2.8, "an elongated oval");
		assertEquals(0.0, H.waterlineY, 1e-9, "the origin is the water surface");
		assertTrue(H.railY(0) > 0.7 && H.railY(0) < 0.85, "freeboard amidships " + H.railY(0));
		assertTrue(H.railY(2.5) > H.railY(0) + 0.25 && H.railY(-2.5) > H.railY(0) + 0.2, "the bow and the stern rise");
		assertTrue(H.railY(2.5) > H.railY(-2.5), "the bow a little higher than the stern");
		assertTrue(H.keelY(0) < -0.25 && H.keelY(0) > -0.4, "draught " + H.keelY(0));
		assertTrue(H.keelY(2.5) > H.keelY(0) + 0.2, "rocker: the keel rises to the ends");
		assertTrue(H.mainDeckY < 0 && H.mainDeckY > H.keelY(0), "the floorboards lie under the water surface, above the keel");
		assertTrue(G.topY() < 1.6, "a low boat: " + G.topY());
		assertTrue(G.boundingRadius() > H.tip && G.boundingRadius() < 4.0);
		assertTrue(G.aiHalfWidth() > 0.7 && G.aiHalfWidth() < 1.0);
		// the round section: the bilge turns well inside the beam at the keel's depth
		assertTrue(H.bottomY(0, 0.45) < -0.25 && H.bottomY(0, 0.97) > -0.08, "round bilge");
	}

	@Test
	void floatsOnOneBlockOfWater() {
		assertTrue(G.probes().size() > 40 && G.probes().size() < 160, "probes " + G.probes().size());
		for (double[] p : G.probes()) {
			assertTrue(p[1] > -0.45, "every probe stays in the top water block: " + p[1]);
			assertTrue(Math.abs(p[2]) <= H.tip + 0.5 && Math.abs(p[0]) <= H.maxHalfWidth + 0.1, "probe inside the boat's footprint");
		}
		// ... and nothing hangs under the keel
		assertEquals(H.keelY(0), G.lowestY(), 1e-9);
	}

	@Test
	void twoSeatsHighAndDry() {
		assertEquals(2, G.seats().size(), "the rower and one passenger");
		ShipGeometry.Seat rower = G.seats().get(ShipGeometry.PILOT_SEAT), passenger = G.seats().get(1);
		assertTrue(rower.pilot());
		assertFalse(passenger.pilot());
		assertEquals(RowboatLayout.THWART_Z[1], rower.z(), 1e-9, "the rower on the middle thwart");
		assertEquals(RowboatLayout.THWART_Z[2], passenger.z(), 1e-9, "the passenger on the aft thwart");
		for (ShipGeometry.Seat s : G.seats()) {
			assertEquals(0.0, s.x(), 1e-9, "on the centre line");
			assertEquals(RowboatLayout.THWART_TOP, s.y(), 1e-9, "sitting on the thwart's top");
			// a seated player's position is 0.6 under his seat point: his feet must stay out of the water
			assertTrue(s.y() - 0.6 >= 0.0, "seat " + s.index() + " keeps a seated player dry");
			assertTrue(s.y() < H.railY(s.z()), "the thwart is under the gunwale");
			assertTrue(s.y() > H.railY(s.z()) - 0.3, "the thwart just under the gunwale, as on the reference");
			// leaving the boat: beside it, in the water (the entity looks for ground first)
			double[] off = s.dismountLocal();
			assertTrue(Math.abs(off[0]) > H.halfWidth(off[2]) + 0.4, "dismount spot outside the hull");
			assertEquals(0.0, off[1], 1e-9, "at the water surface");
		}
	}

	@Test
	void aClickAnywhereTakesTheOars() {
		// from the side, at mid height, from above the stern thwart, from ahead of the bow: all pick the "helm"
		double[][] rays = {{4, 0.4, 0, -1, 0, 0}, {0, 4, -1.15, 0, -1, 0}, {0, 0.6, 6, 0, 0, -1}, {-3, 2.5, 1.0, 1, -0.7, 0},
				{0.5, 3, 0.05, 0, -1, 0}};
		for (double[] r : rays) {
			ShipGeometry.Pick pick = G.pick(ORIGIN, r[0], r[1], r[2], r[3], r[4], r[5], 8.0);
			assertNotNull(pick, "a ray at the boat hits it");
			assertEquals(ShipGeometry.PickKind.HELM, pick.kind(), "a click on the boat seats the player");
		}
		assertTrue(G.pick(ORIGIN, 4, 2.0, 0, -1, 0, 0, 8.0) == null || G.pick(ORIGIN, 4, 2.0, 0, -1, 0, 0, 8.0).kind() != ShipGeometry.PickKind.HELM,
				"a ray well above the boat misses it");
	}

	@Test
	void oars() {
		double[] pivot = RowboatLayout.oarPivot(1);
		assertTrue(pivot[0] > H.halfWidth(RowboatLayout.OARLOCK_Z) && pivot[0] < H.halfWidth(RowboatLayout.OARLOCK_Z) + 0.15, "pivot on the gunwale");
		assertTrue(pivot[1] > H.railY(RowboatLayout.OARLOCK_Z), "pivot above the rail");
		assertTrue(RowboatLayout.OARLOCK_Z > RowboatLayout.PILOT_Z && RowboatLayout.OARLOCK_Z < RowboatLayout.PILOT_Z + 0.5, "the tholepins by the rower's thwart");
		assertEquals(RowboatLayout.OAR_IN + RowboatLayout.OAR_OUT, 3.55, 1e-9, "oar length");
		assertTrue(RowboatLayout.OAR_IN + RowboatLayout.OAR_OUT > 1.6 * 2 * H.maxHalfWidth, "an oar is longer than 1.6 beams");
		// the blade at the catch: well outboard, forward of the pivot, in the water; lifted on the recovery: out of it
		double[] in = RowboatLayout.oarBlade(1, 22, -8), out = RowboatLayout.oarBlade(1, -24, 12), rest = RowboatLayout.oarBlade(1, 0, 0);
		assertTrue(in[0] > pivot[0] + 1.8 && in[2] > pivot[2] + 0.6 && in[1] < 0.0, "catch " + in[0] + " " + in[1] + " " + in[2]);
		assertTrue(out[1] > 0.4 && out[2] < pivot[2] - 0.6, "release " + out[1] + " " + out[2]);
		assertTrue(rest[1] > 0.0 && rest[1] < 0.3, "at rest the blades skim the water: " + rest[1]);
		double[] star = RowboatLayout.oarBlade(-1, 22, -8);
		assertEquals(-in[0], star[0], 1e-9);
		assertEquals(in[2], star[2], 1e-9);
	}

	@Test
	void lightAndNimble() {
		ShipConfig c = TYPE.defaults().get(), galley = Ships.MEDIEVAL_GALLEY.defaults().get();
		assertTrue(c.flight == null && c.dive == null);
		assertTrue(c.normalSpeed < galley.normalSpeed && c.fastSpeed < galley.fastSpeed, "slower than a galley");
		assertTrue(c.acceleration > galley.acceleration && c.braking > galley.braking, "gathers way and stops quickly");
		assertTrue(c.waterDrag > galley.waterDrag, "little inertia");
		assertTrue(c.maxTurnRate > 2 * galley.maxTurnRate && c.minTurnFactor > galley.minTurnFactor, "turns on the spot");
		assertTrue(c.aiWaypointRadius < galley.aiWaypointRadius && c.aiStopRadius < galley.aiStopRadius, "tight autopilot radii");
		assertFalse(c.furlSailWhenStopped, "no sail");
		c.sanitize();
		assertEquals(3.5, c.normalSpeed, 1e-9, "the defaults are within the config bounds");
		assertEquals(45.0, c.maxTurnRate, 1e-9);
	}

	@Test
	void hullCollisionsHoldAStandingMob() {
		// the floorboards carry whatever is put in the boat (an item, a mob); the sides stop it (a box each side)
		double[] spot = G.boardingSpot(0.0, 0.5);
		assertTrue(spot[1] > H.mainDeckY && spot[1] < H.mainDeckY + 0.1, "standing on the floorboards");
		boolean[] floor = {false}, wall = {false};
		G.collectBoxes(ORIGIN, -0.2, -1, 0.3, 0.2, 1, 0.7, (a, b, c, d, e, f) -> {
			if (e > H.mainDeckY - 1e-3 && e < H.mainDeckY + 1e-3) {
				floor[0] = true;
			}
		});
		G.collectBoxes(ORIGIN, 0.7, 0.2, -0.2, 1.3, 0.6, 0.2, (a, b, c, d, e, f) -> {
			if (a > 0.7 && e > 0.6) {
				wall[0] = true;
			}
		});
		assertTrue(floor[0], "floor boxes under the boarding spot");
		assertTrue(wall[0], "the planking's side wall");
	}
}
