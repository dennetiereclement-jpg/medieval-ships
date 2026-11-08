package fr.medievalships.core.bridge;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** The approach zones on both ends of the channel, the passage, the band, the vessels' reach. */
class ChannelZonesTest {
	/** Channel along +z through (100, 200); 10 wide; deck 3 thick along z; approach 50, hysteresis 8. */
	private static final ChannelZones Z = ChannelZones.of(100, 200, 0, 7, 5, 1.5, 50, 8);

	@Test
	void alongAcrossAndSides() {
		assertEquals(0, Z.dx(), 1e-12);
		assertEquals(1, Z.dz(), 1e-12);
		assertEquals(30, Z.along(100, 230), 1e-12);
		assertEquals(-30, Z.along(100, 170), 1e-12);
		assertEquals(1, Z.side(100, 230));
		assertEquals(-1, Z.side(100, 170));
		assertEquals(-3, Z.across(103, 200), 1e-12); // +x is the right bank looking along +z: across = -(dx)*dz ... sign only matters squared
		assertEquals(3, Math.abs(Z.across(97, 200)), 1e-12);
	}

	@Test
	void bothEndsOfTheChannelTrigger() {
		// a hull whose nearest part is 48 from the deck edge, coming from the north (-z)
		double d = Z.distanceToDeck(100, 200 - 1.5 - 48 - 10, 10);
		assertEquals(48, d, 1e-9);
		assertTrue(Z.inApproach(d));
		// the same from the south (+z)
		assertTrue(Z.inApproach(Z.distanceToDeck(100, 200 + 1.5 + 48 + 10, 10)));
		// 51 away: not yet; 55 away: still in the keep zone (hysteresis 8)
		assertFalse(Z.inApproach(Z.distanceToDeck(100, 200 + 1.5 + 51 + 10, 10)));
		assertTrue(Z.inKeepZone(Z.distanceToDeck(100, 200 + 1.5 + 55 + 10, 10)));
		assertFalse(Z.inKeepZone(Z.distanceToDeck(100, 200 + 1.5 + 59 + 10, 10)));
		// the bow counts, not only the centre: a 30 block ship whose centre is 60 away is 48 away
		assertTrue(Z.inApproach(Z.distanceToDeck(100, 260 + 1.5, 12)));
		// in the passage: its footprint reaches the deck
		assertTrue(Z.inPassage(Z.distanceToDeck(100, 210, 10)));
		assertFalse(Z.inPassage(Z.distanceToDeck(100, 215, 10)));
	}

	@Test
	void bandIgnoresBoatsOnTheBanks() {
		// a boat moored 9 blocks off the axis, 1 wide: outside the 5 + 1 band
		assertFalse(Z.inBand(109, 230, 0.5));
		// a wide ship whose side reaches the band
		assertTrue(Z.inBand(108, 230, 3));
		assertTrue(Z.inBand(100, 230, 0.5));
	}

	@Test
	void reachOfAnOrientedHull() {
		// a hull 10 ahead, 10 behind, 2.5 half wide, sailing along the channel (yaw 0 = facing +z)
		assertEquals(10, Z.reachAlong(0, 10, 10, 2.5), 1e-9);
		assertEquals(2.5, Z.reachAcross(0, 10, 10, 2.5), 1e-9);
		// across the channel (yaw 90 = facing -x): its length is now across
		assertEquals(2.5, Z.reachAlong(90, 10, 10, 2.5), 1e-9);
		assertEquals(10, Z.reachAcross(90, 10, 10, 2.5), 1e-9);
		// at 45 degrees both grow
		double a = Z.reachAlong(45, 10, 10, 2.5);
		assertEquals((10 + 2.5) * Math.sqrt(0.5), a, 1e-9);
	}

	@Test
	void boxesOfTheZones() {
		double[] north = Z.approachBox(-1, 190, 220);
		assertEquals(94, north[0], 1e-9);
		assertEquals(106, north[3], 1e-9);
		assertEquals(200 - 1.5 - 58, north[2], 1e-9);
		assertEquals(200 - 1.5, north[5], 1e-9);
		double[] south = Z.approachBox(1, 190, 220);
		assertEquals(200 + 1.5, south[2], 1e-9);
		assertEquals(200 + 1.5 + 58, south[5], 1e-9);
		double[] passage = Z.passageBox(190, 220);
		assertEquals(198.5, passage[2], 1e-9);
		assertEquals(201.5, passage[5], 1e-9);
		double[] all = Z.detectionBox(190, 220);
		assertEquals(north[2], all[2], 1e-9);
		assertEquals(south[5], all[5], 1e-9);
		// a diagonal channel: the box encloses the rotated rectangle
		ChannelZones diag = ChannelZones.of(0, 0, 1, 1, 5, 2, 50, 0);
		double[] b = diag.passageBox(0, 1);
		assertTrue(b[3] - b[0] > 7 && b[5] - b[2] > 7);
	}
}
