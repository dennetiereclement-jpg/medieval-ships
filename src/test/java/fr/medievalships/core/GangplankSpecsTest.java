package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The per-vessel gangplank specs (assets/medievalships/gangplanks/<id>.json, tools/gangplank/ships_g2.py): every
 * listed ship and large airship has one, its values are sane, the hinge is on the hull's side at the top of its rail
 * or bulwark, the stairs climb from the deck to the hinge through free space, the lever stands on the deck within
 * reach, the plank clears the vessel's own solids at every allowed angle and stowed, and its model has the spec's size.
 */
class GangplankSpecsTest {
	/** The vessels equipped by tools/gangplank/ships_g2.py. */
	static final List<String> SHIPS = List.of("galley", "galleon", "warship", "medieval_galley", "steam_paddleboat", "elven_sailboat",
			"old_corsair", "blue_frigate", "crystal_airship", "sky_leviathan", "dragon_junk", "gear_steamship");
	/** The two reference vessels (specs written with the system itself); checked the same way when present. */
	static final List<String> REFERENCE = List.of(); // the airship's spec is checked by GangplankTest
	/** Vessels without a gangplank (see docs): boarded by a click, a basket, their own boarding staircase. */
	static final List<String> EXCLUDED = List.of("rowboat", "trade_sloop", "nautilus", "hot_air_balloon", "rustic_skiff");
	static final Set<String> STYLES = Set.of("wood", "dark_wood", "worn", "elven", "copper", "crystal", "jade", "steel");
	static final double STAIR_RISE = 0.45;

	static List<String> checked() {
		List<String> ids = new ArrayList<>(SHIPS);
		for (String id : REFERENCE) {
			if (Gangplank.load(id) != null) {
				ids.add(id);
			}
		}
		return ids;
	}

	static Gangplank.Spec spec(String id) {
		Gangplank.Spec s = Gangplank.load(id);
		assertNotNull(s, id + ": no gangplanks/" + id + ".json");
		return s;
	}

	static ShipType type(String id) {
		ShipType t = Ships.byId(id);
		assertNotNull(t, id);
		return t;
	}

	static boolean solidAt(ShipGeometry g, double x, double y, double z) {
		if (g.interior() != null && g.interior().solidAt(x, y, z, InteriorGrid.State.CLOSED)) {
			return true;
		}
		for (ShipGeometry.LocalBox b : g.solids()) {
			if (x > b.minX() && x < b.maxX() && y > b.minY() && y < b.maxY() && z > b.minZ() && z < b.maxZ()) {
				return true;
			}
		}
		return false;
	}

	/** Walkable floor height under (x, z) at about y (open deck, or top of a solid grid cell), NaN if none within 0.6. */
	static double floorAt(ShipType t, double x, double y, double z) {
		ShipGeometry g = t.geometry();
		if (g.interior() == null) {
			HullShape h = t.hull();
			return Math.abs(x) <= h.innerHalfWidth(z) + 0.15 && Math.abs(h.deckY(z) - y) < 0.6 ? h.deckY(z) : Double.NaN;
		}
		InteriorGrid gr = g.interior();
		for (double yy = y + 0.6; yy >= y - 0.6; yy -= 0.01) {
			if (solidAt(g, x, yy - 0.005, z) && !solidAt(g, x, yy + 0.005, z)) {
				return Math.round(yy / gr.cell * 4) * gr.cell / 4; // cell tops are on the grid
			}
		}
		return Double.NaN;
	}

	@Test
	void everyListedVesselHasASpecAndTheExcludedNone() {
		for (String id : SHIPS) {
			spec(id);
			assertNotNull(Gangplank.of(id), id);
		}
		for (String id : EXCLUDED) {
			assertNull(Gangplank.load(id), id + " has no gangplank (see docs)");
		}
		for (ShipType t : Ships.ALL) {
			if (!EXCLUDED.contains(t.id())) {
				assertTrue(SHIPS.contains(t.id()) || REFERENCE.contains(t.id()) || "steampunk_airship".equals(t.id()), t.id() + " is neither equipped nor excluded");
			}
		}
	}

	@Test
	void valuesAreSane() {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			ShipType t = type(id);
			boolean flying = t.geometry().flying();
			assertTrue(s.o() * s.hx() > 0, id + ": the hinge is on the " + s.side() + " side");
			assertTrue(STYLES.contains(s.style()), id + ": style " + s.style());
			assertTrue(s.width() >= 1.8 && s.width() <= 4.0, id + ": width " + s.width());
			if (flying) {
				assertTrue(s.width() >= 3.0, id + ": a large airship's plank is 3 to 4 wide");
			} else if (t.hull().halfLength >= 15) {
				assertTrue(s.width() >= 2.0, id + ": a large ship's plank is at least 2 wide");
			}
			assertTrue(s.length() >= 3.0 && s.length() <= 12.0, id + ": length " + s.length());
			assertTrue(s.minAngle() < 0 && s.maxAngle() > 0 && s.maxAngle() <= 50, id + ": angles " + s.minAngle() + ".." + s.maxAngle());
			double reach = s.length() * Math.sin(Math.toRadians(s.maxAngle()));
			assertTrue(s.maxDrop() > 0 && s.maxDrop() <= reach + 1e-6, id + ": max drop " + s.maxDrop() + " within reach " + reach);
			if (flying) {
				assertTrue(s.maxDrop() >= 2.5, id + ": an airship reaches a platform a few blocks under its deck");
			} else {
				// a quay one block above the water is reachable, and one level with the rail too (min angle < 0)
				double quay = t.hull().waterlineY + 1.0;
				assertTrue(s.maxDrop() >= s.hy() - quay - 0.05, id + ": reaches a quay one block above the water (drop " + (s.hy() - quay) + ")");
			}
			assertEquals(Gangplank.STOWED_ANGLE, s.stowedAngle(), 1e-9, id + ": the clearance check sweeps from upright (rules of 1.23.0)");
		}
	}

	@Test
	void hingeIsOnTheHullSideAtTheTopOfItsRail() {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			ShipType t = type(id);
			ShipGeometry g = t.geometry();
			HullShape h = t.hull();
			int o = s.o();
			for (double w : new double[] {-s.width() / 2 + 0.1, 0, s.width() / 2 - 0.1}) {
				double z = s.hz() + w;
				String at = id + " at z " + z;
				if (g.interior() == null) {
					assertEquals(h.halfWidth(z), Math.abs(s.hx()), 0.45, at + ": hinge on the hull's outer face");
				} else {
					assertTrue(Math.abs(s.hx()) <= h.maxHalfWidth + 0.4, at + ": hinge within the beam");
					// the bulwark (or the casing's floor) is just inboard of the hinge, its top at most 0.6 under it
					double top = Double.NaN;
					for (double y = s.hy() + 0.01; y >= s.hy() - 0.6; y -= 0.01) {
						if (solidAt(g, s.hx() - o * 0.45, y, z)) {
							top = y;
							break;
						}
					}
					assertFalse(Double.isNaN(top), at + ": no bulwark under the hinge");
				}
				// open outboard of the hinge and above the opening (head room over the rail where one walks)
				for (double y = s.hy() + 0.05; y <= s.hy() + 1.8; y += 0.1) {
					assertFalse(solidAt(g, s.hx() + o * 0.1, y, z), at + ": solid outboard of the hinge at y " + y);
					assertFalse(solidAt(g, s.hx() - o * 0.45, y, z), at + ": no head room over the rail at y " + y);
				}
			}
			if (g.interior() == null) {
				double rail = h.railY(s.hz());
				assertTrue(s.hy() >= rail - 0.05 && s.hy() <= rail + 0.45, id + ": hinge at the top of the rail (" + rail + "), not " + s.hy());
			}
		}
	}

	@Test
	void stairsClimbFromTheDeckToTheHingeThroughFreeSpace() {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			ShipType t = type(id);
			ShipGeometry g = t.geometry();
			Gangplank.Box st = s.step();
			int o = s.o();
			if (st == null) {
				// no stairs: the walking floor reaches the hinge's height right inboard of it
				double f = floorAt(t, s.hx() - o * 0.5, s.hy(), s.hz());
				assertEquals(s.hy(), f, 0.1, id + ": floor level with the hinge");
				continue;
			}
			assertEquals(s.hy(), st.maxY(), 1e-6, id + ": the stairs' top is the hinge height");
			double rise = st.maxY() - st.minY();
			int n = Math.max(1, (int) Math.ceil(rise / STAIR_RISE - 1e-9));
			assertTrue(rise / n <= 0.5, id + ": stair rise " + rise / n);
			assertTrue((st.maxX() - st.minX()) / n >= 0.3, id + ": stair tread " + (st.maxX() - st.minX()) / n);
			assertEquals(s.hz() - s.width() / 2, st.minZ(), 0.3, id + ": stairs as wide as the plank");
			assertEquals(s.hz() + s.width() / 2, st.maxZ(), 0.3, id + ": stairs as wide as the plank");
			double outboard = o > 0 ? st.maxX() : st.minX(), inboard = o > 0 ? st.minX() : st.maxX();
			assertTrue(Math.abs(outboard) < Math.abs(s.hx()) && Math.abs(s.hx()) - Math.abs(outboard) <= 0.9,
					id + ": the stairs reach the bulwark under the hinge");
			for (double z = st.minZ() + 0.1; z <= st.maxZ() - 0.1; z += 0.25) {
				// they start on the deck, with a free landing inboard of the lowest stair
				double f = floorAt(t, inboard - o * 0.3, st.minY(), z);
				assertEquals(st.minY(), f, 0.06, id + ": the stairs start on the deck at z " + z);
				for (double y = st.minY() + 0.05; y <= st.minY() + 1.8; y += 0.1) {
					assertFalse(solidAt(g, inboard - o * 0.3, y, z), id + ": landing blocked at z " + z + " y " + y);
				}
				// nothing of the ship inside the stairs (their outboard edge may touch the bulwark)
				for (double x = inboard + o * 0.05; o * (outboard - o * 0.2 - x) >= 0; x += o * 0.1) {
					for (double y = st.minY() + 0.05; y <= st.maxY() + 1.8; y += 0.1) {
						assertFalse(solidAt(g, x, y, z), id + ": ship solid in the stairs (or over them) at " + x + ", " + y + ", " + z);
					}
				}
			}
		}
	}

	@Test
	void leverStandsOnTheDeckWithinReach() {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			ShipType t = type(id);
			ShipGeometry g = t.geometry();
			double lx = s.leverX(), ly = s.leverY(), lz = s.leverZ();
			assertTrue(s.o() * lx > 0, id + ": lever on the plank's side of the deck");
			assertEquals(ly, floorAt(t, lx, ly, lz), 0.06, id + ": lever on the deck");
			for (double dx : new double[] {-0.2, 0, 0.2}) {
				for (double dz : new double[] {-0.2, 0, 0.2}) {
					for (double y = ly + 0.05; y <= ly + 1.0; y += 0.1) {
						assertFalse(solidAt(g, lx + dx, y, lz + dz), id + ": lever inside a ship solid");
					}
				}
			}
			Gangplank.Box st = s.step();
			if (st != null) {
				boolean inStairs = lx > st.minX() - 0.15 && lx < st.maxX() + 0.15 && lz > st.minZ() - 0.15 && lz < st.maxZ() + 0.15;
				assertFalse(inStairs, id + ": lever on the stairs");
			}
			double d = Math.hypot(lx - s.hx(), lz - s.hz());
			assertTrue(d <= 4.0, id + ": lever " + d + " from the hinge");
		}
	}

	@Test
	void plankClearsTheVesselAtEveryAngle() {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			ShipGeometry g = type(id).geometry();
			HullShape h = type(id).hull();
			List<Double> angles = new ArrayList<>(List.of(s.minAngle(), 0.0, s.maxAngle(), s.stowedAngle()));
			for (double a = s.stowedAngle(); a < s.maxAngle(); a += 10) {
				angles.add(a); // the swing
			}
			for (double a : angles) {
				for (double u = 0.5; u <= s.length() + 1e-9; u += 0.25) {
					for (double w = -s.width() / 2 + 0.05; w <= s.width() / 2 - 0.05 + 1e-9; w += (s.width() - 0.1) / 4) {
						for (double v : new double[] {-0.2, 0.02, 0.8}) {
							double[] p = s.point(a, u, v, w);
							String at = id + " at angle " + a + ", u " + u + ", w " + w + ", v " + v;
							assertFalse(solidAt(g, p[0], p[1], p[2]), at + ": inside the ship");
							if (g.interior() == null && v < 0.5) {
								assertFalse(g.insideHull(p[0], p[1], p[2]) && Math.abs(p[0]) < h.halfWidth(p[2]) - 0.05, at + ": inside the hull");
							}
						}
					}
				}
			}
		}
	}

	@Test
	void modelsMatchTheSpecs() throws Exception {
		for (String id : checked()) {
			Gangplank.Spec s = spec(id);
			BbModel plank = load("gangplank_" + id);
			assertNotNull(load("gangplank_lever_" + s.style()), id + ": lever model of style " + s.style());
			double[] lo = {1e9, 1e9, 1e9}, hi = {-1e9, -1e9, -1e9};
			plank.render(plank.newPose(), (p, uv, n, glow) -> {
				for (int k = 0; k < 4; k++) {
					for (int a = 0; a < 3; a++) {
						lo[a] = Math.min(lo[a], p[k * 3 + a]);
						hi[a] = Math.max(hi[a], p[k * 3 + a]);
					}
				}
			});
			assertEquals(0.0, lo[0], 0.15, id + ": the plank starts at its hinge (model x 0)");
			assertEquals(s.length(), hi[0], 0.15, id + ": plank model length");
			assertEquals(s.width(), hi[2] - lo[2], 0.15, id + ": plank model width");
			assertEquals(0.0, (hi[2] + lo[2]) / 2, 0.05, id + ": plank model centred on its hinge line");
			assertTrue(hi[1] <= 0.95 && hi[1] >= 0.0, id + ": handrails at most a little under a block high");
		}
	}

	static BbModel load(String name) throws Exception {
		try (InputStream in = GangplankSpecsTest.class.getResourceAsStream("/assets/medievalships/models/entity/" + name + ".bbmodel")) {
			assertNotNull(in, name + ".bbmodel");
			try (Reader r = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return new BbModel(r);
			}
		}
	}
}
