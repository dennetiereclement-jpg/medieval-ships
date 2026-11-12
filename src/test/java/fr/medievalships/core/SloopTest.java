package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The trade sloop: hull shape (same numbers as tools/sloop_shape.py), dimensions of the reference, the seats and
 * the tiller on the decks, the cargo solid and clear of the pilot, a laden small boat's handling, and the model's
 * bones, animations and extent.
 */
class SloopTest {
	private static final ShipType TYPE = Ships.TRADE_SLOOP;
	private static final ShipGeometry G = TYPE.geometry();
	private static final HullShape H = TYPE.hull();

	/** Values printed by {@code python3 tools/sloop_shape.py}: z, half width, rail, keel, bottom at 1.2, deck. */
	@Test
	void matchesModelGenerator() {
		double[][] expected = {
				{-7.0, 1.220323, 2.314793, -0.580634, -0.087095, 1.100000},
				{-5.0, 1.978045, 2.202456, -1.116685, -0.830077, 1.100000},
				{-3.0, 2.239660, 2.133302, -1.398434, -1.138611, 0.600000},
				{0.0, 2.300000, 2.100000, -1.500000, -1.242391, 0.600000},
				{3.0, 2.043931, 2.286492, -1.398434, -1.066860, 0.600000},
				{6.0, 1.217033, 2.956892, -0.884218, -0.132633, 0.600000},
				{7.0, 0.766386, 3.302843, -0.580634, -0.087095, 0.600000}};
		for (double[] e : expected) {
			assertEquals(e[1], H.halfWidth(e[0]), 1e-5, "half width at " + e[0]);
			assertEquals(e[2], H.railY(e[0]), 1e-5, "rail at " + e[0]);
			assertEquals(e[3], H.keelY(e[0]), 1e-5, "keel at " + e[0]);
			assertEquals(e[4], H.bottomY(e[0], 1.2), 1e-5, "bottom at " + e[0]);
			assertEquals(e[5], H.deckY(e[0]), 1e-9, "deck at " + e[0]);
		}
	}

	/** About 15 blocks of hull (20 with the bowsprit), 4.6 wide, a raised bow, a 14 block mast. */
	@Test
	void dimensions() {
		assertEquals(4.6, 2 * H.maxHalfWidth, 1e-9);
		assertEquals(15.0, 2 * H.halfLength, 1e-9);
		double overall = SloopLayout.overallLength();
		assertTrue(overall > 19.5 && overall < 21.0, "overall " + overall);
		// the bow rises well above the waist, the stern a little
		assertTrue(H.railY(7.0) - H.railY(0) > 1.0, "bow sheer " + (H.railY(7.0) - H.railY(0)));
		assertTrue(H.railY(-7.0) - H.railY(0) > 0.15 && H.railY(-7.0) < H.railY(7.0));
		// freeboard of a chunky little laden merchant (1.30.0: 0.6 deeper, it was 2.6): 2 blocks at the waist, the water
		// just under the blue band, a draught of 1.6
		assertEquals(2.0, H.railY(0) - H.waterlineY, 0.05);
		assertTrue(H.keelY(0) - H.waterlineY > -1.7);
		assertTrue(H.mainDeckY - H.waterlineY >= 0.5, "the deck half a block above the water");
		double total = SloopLayout.MAST_TOP - H.keelY(0);
		assertTrue(total > 15 && total < 16.5, "total height " + total);
		// the bulwark stays at least knee high around the stern platform
		for (double z = -6.5; z < -3.6; z += 0.5) {
			assertTrue(H.railY(z) - H.deckY(z) >= SloopLayout.RAIL_ABOVE_DECK - 1e-9, "rail over the stern platform at " + z);
		}
	}

	/** Five places: the pilot standing at the tiller on the stern platform, four passengers on the decks, all inside the hull. */
	@Test
	void seats() {
		assertEquals(5, G.seats().size());
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertEquals(SloopLayout.PILOT_Z, pilot.z(), 1e-9);
		assertEquals(SloopLayout.AFT_DECK_Y + 0.28, pilot.y(), 1e-9);
		assertTrue(pilot.z() < SloopLayout.AFT_DECK_START, "the pilot stands on the stern platform");
		for (ShipGeometry.Seat s : G.seats()) {
			double deck = H.deckY(s.z());
			assertTrue(s.y() > deck && s.y() < deck + 1.0, "seat " + s.index() + " on its deck");
			assertTrue(Math.abs(s.x()) < H.innerHalfWidth(s.z()), "seat " + s.index() + " inside the hull");
			double[] d = s.dismountLocal();
			assertTrue(Math.abs(d[0]) < H.innerHalfWidth(d[2]) && d[2] > H.deckMinZ && d[2] < H.deckMaxZ, "dismount " + s.index() + " on deck");
			assertEquals(H.deckY(d[2]) + 0.02, d[1], 1e-9, "dismount " + s.index() + " at deck level");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " carried");
		}
		// the tiller sweeps over the stern platform, within reach of the pilot
		ShipGeometry.LocalBox helm = G.helm();
		assertNotNull(helm);
		assertTrue(helm.minY() > SloopLayout.AFT_DECK_Y && helm.maxZ() < SloopLayout.AFT_DECK_START);
		assertTrue(helm.minZ() < SloopLayout.PILOT_Z && helm.maxZ() > SloopLayout.PILOT_Z - 1.5);
	}

	/** Crates and barrels are solid, stand on their deck inside the bulwarks, and leave the pilot's spot and the gangway free. */
	@Test
	void cargo() {
		assertEquals(SloopLayout.CRATES.length + SloopLayout.BARRELS.length, G.solids().size());
		for (ShipGeometry.LocalBox b : G.solids()) {
			double zc = (b.minZ() + b.maxZ()) / 2;
			assertEquals(H.deckY(zc), b.minY(), 1e-9, "cargo on its deck at " + zc);
			assertTrue(b.maxY() - b.minY() >= 0.5 && b.maxY() - b.minY() <= 0.85);
			assertTrue(Math.abs(b.minX()) < H.innerHalfWidth(b.minZ()) + 0.05 && Math.abs(b.maxX()) < H.innerHalfWidth(b.maxZ()) + 0.05,
					"cargo inside the bulwarks at " + zc);
			assertFalse(b.minX() < 0.35 && b.maxX() > -0.35 && b.minZ() < SloopLayout.PILOT_Z + 0.4 && b.maxZ() > SloopLayout.PILOT_Z - 0.4,
					"the pilot's spot is clear");
			assertFalse(b.minX() < 0.4 && b.maxX() > -0.4 && b.minZ() < 2.0 && b.maxZ() > -3.5, "the gangway amidships is clear");
		}
		// walking: the main deck and the stern platform are carried, one step between them; the water is not
		assertTrue(G.inCarryVolume(0, SloopLayout.MAIN_DECK_Y + 0.3, 0) && G.inCarryVolume(0, SloopLayout.AFT_DECK_Y + 0.3, -5.0));
		assertFalse(G.inCarryVolume(3.5, SloopLayout.MAIN_DECK_Y + 0.3, 0));
		assertEquals(0.5, SloopLayout.AFT_DECK_Y - SloopLayout.MAIN_DECK_Y, 1e-9, "one easy step up to the stern platform");
	}

	/** A laden little boat: progressive, slower than the elven racer, lighter than the galleon, rocks more, furls at rest. */
	@Test
	void handling() {
		ShipConfig c = TYPE.defaults().get(), elf = Ships.ELVEN_SAILBOAT.defaults().get(), galleon = Ships.GALLEON.defaults().get();
		assertTrue(c.acceleration < elf.acceleration && c.fastSpeed < elf.fastSpeed && c.maxTurnRate > galleon.maxTurnRate);
		assertTrue(c.acceleration > galleon.acceleration && c.fastSpeed > galleon.fastSpeed);
		assertTrue(c.waveRocking > galleon.waveRocking && c.waveRocking > elf.waveRocking);
		assertTrue(c.furlSailWhenStopped);
		assertTrue(c.aiWaypointRadius < galleon.aiWaypointRadius && c.aiStopRadius > 1.0);
		assertFalse(G.flying());
		assertSame(TYPE, Ships.byId("trade_sloop"));
		assertTrue(Ships.ALL.contains(TYPE));
		assertEquals("trade_sloop", TYPE.id());
	}

	/** The model as the mod reads it: sails, rudder with its tiller, lanterns, a swaying rope; the spars where the layout says. */
	@Test
	void model() throws Exception {
		BbModel m;
		try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/trade_sloop.bbmodel"),
				StandardCharsets.UTF_8)) {
			m = new BbModel(r);
		}
		for (String bone : new String[] {"sail_main", "sail_jib", "rudder", "lantern_0", "lantern_1", "lantern_bow", "rope_slack_0", "mast"}) {
			assertNotNull(m.bonesByName.get(bone), "bone " + bone);
		}
		for (String anim : new String[] {"sail_wind", "sail_furl", "steer", "lantern_sway", "rope_sway"}) {
			assertNotNull(m.animations.get(anim), "animation " + anim);
		}
		float[] lo = {1e9f, 1e9f, 1e9f}, hi = {-1e9f, -1e9f, -1e9f};
		int[] faces = {0};
		m.render(m.newPose(), (p, uv, n, glow) -> {
			faces[0]++;
			for (int i = 0; i < 12; i += 3) {
				for (int k = 0; k < 3; k++) {
					lo[k] = Math.min(lo[k], p[i + k]);
					hi[k] = Math.max(hi[k], p[i + k]);
				}
			}
		});
		assertTrue(faces[0] > 2000 && faces[0] < 12000, "a small, optimised model: " + faces[0] + " faces");
		// extent: the bowsprit tip and the boom end, the keel and the mast truck, within half a block of the layout
		assertEquals(SloopLayout.BOWSPRIT_TIP[1], hi[2], 0.6, "bowsprit tip");
		assertEquals(SloopLayout.BOOM_END_Z, lo[2], 0.9, "boom end");
		assertEquals(SloopLayout.MAST_TOP, hi[1], 0.6, "mast truck");
		assertEquals(H.keelY(0), lo[1], 0.5, "keel");
		assertEquals(H.maxHalfWidth, hi[0], 0.4, "beam");
	}
}
