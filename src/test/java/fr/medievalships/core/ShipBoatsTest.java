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
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The ships' boats (1.30.0): which ships carry one, the deco boat's bone in each model (split from the deck where it
 * shares a bone, the picture unchanged), where the Rowboat goes on the water (the player's side first, clear of the
 * hull on its whole length), how far it may be to be hoisted back, the click box, and the warship's deck box dropped
 * while its boat is away.
 */
class ShipBoatsTest {
	private static final Set<String> CARRIERS = Set.of("galleon", "warship", "old_corsair", "nautilus");

	private static BbModel load(String id, BbModel.Split split) throws Exception {
		Path path = Path.of("src/main/resources/assets/medievalships/models/entity/" + id + ".bbmodel");
		try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
			return new BbModel(r, split);
		}
	}

	private static BbModel.Split split(ShipBoats.Spec spec) {
		return spec.splitParent() == null ? null : new BbModel.Split(spec.splitParent(), spec.bone(), ShipBoats.SPLIT_PREFIX, ShipBoats.SPLIT_KEEP);
	}

	@Test
	void theShipsThatCarryABoat() {
		assertEquals(CARRIERS, ShipBoats.all().keySet());
		for (ShipBoats.Spec spec : ShipBoats.all().values()) {
			assertNotNull(Ships.byId(spec.shipId()), spec.shipId());
			assertEquals(spec, ShipBoats.of(spec.shipId()));
			assertTrue(spec.the().equals("la chaloupe") || spec.the().equals("le canot"), spec.the());
		}
		for (ShipType t : Ships.ALL) {
			assertEquals(CARRIERS.contains(t.id()), ShipBoats.of(t.id()) != null, t.id());
		}
		assertNull(ShipBoats.of("rowboat"), "the rowboat carries no boat");
		assertEquals("La chaloupe", ShipBoats.of("galleon").The());
		assertEquals("le", ShipBoats.of("nautilus").it());
		assertEquals(Ships.NautilusLayout.LIFEBOAT_AWAY, ShipBoats.AWAY_BIT, "the Nautilus' saved lifeboat bit is kept");
	}

	/** Every quad of a model as rounded corner positions, sorted (the picture, whatever the bones). */
	private static List<String> picture(BbModel m) {
		List<String> out = new ArrayList<>();
		m.render(m.newPose(), (p, uv, n, glow) -> {
			long[] k = new long[12];
			for (int i = 0; i < 12; i++) {
				k[i] = Math.round(p[i] * 1000);
			}
			out.add(Arrays.toString(k));
		});
		out.sort(null);
		return out;
	}

	/** {minX, minY, minZ, maxX, maxY, maxZ} of a bone's quads at rest, and their count in [6]. */
	private static double[] bounds(BbModel m, String bone) {
		double[] b = {1e9, 1e9, 1e9, -1e9, -1e9, -1e9, 0};
		m.renderPart(m.newPose(), bone, (p, uv, n, glow) -> {
			for (int c = 0; c < 4; c++) {
				for (int a = 0; a < 3; a++) {
					b[a] = Math.min(b[a], p[c * 3 + a]);
					b[a + 3] = Math.max(b[a + 3], p[c * 3 + a]);
				}
			}
			b[6]++;
		});
		return b;
	}

	@Test
	void theDecoBoatHasABoneOfItsOwnAndThePictureIsUnchanged() throws Exception {
		for (ShipBoats.Spec spec : ShipBoats.all().values()) {
			BbModel m = load(spec.shipId(), split(spec));
			assertTrue(m.hasBone(spec.bone()), spec.shipId() + ": bone " + spec.bone());
			double[] b = bounds(m, spec.bone());
			assertTrue(b[6] > 100, spec.shipId() + ": the deco boat has its faces (" + b[6] + ")");
			ShipGeometry.LocalBox d = spec.deco();
			double m2 = 0.35;
			assertTrue(b[0] >= d.minX() - m2 && b[3] <= d.maxX() + m2 && b[1] >= d.minY() - m2 && b[4] <= d.maxY() + m2
					&& b[2] >= d.minZ() - m2 && b[5] <= d.maxZ() + m2, spec.shipId() + ": the click box covers the deco boat " + Arrays.toString(b));
			double cx = (b[0] + b[3]) / 2, cy = (b[1] + b[4]) / 2, cz = (b[2] + b[5]) / 2;
			assertTrue(cx > d.minX() && cx < d.maxX() && cy > d.minY() && cy < d.maxY() && cz > d.minZ() && cz < d.maxZ(), spec.shipId());
			if (spec.splitParent() != null) {
				BbModel plain = load(spec.shipId(), null);
				assertFalse(plain.hasBone(spec.bone()), spec.shipId() + ": the bone is made at loading");
				assertEquals(plain.quadCount(), m.quadCount(), spec.shipId());
				assertEquals(picture(plain), picture(m), spec.shipId() + ": the same picture with the boat in a bone of its own");
				// its chocks stay on the deck when the boat is away
				double[] parent = bounds(m, spec.splitParent());
				assertTrue(parent[6] > 0, spec.shipId());
			}
		}
	}

	@Test
	void theRowboatGoesOnTheWaterClearOfTheHullOnThePlayersSide() {
		for (ShipBoats.Spec spec : ShipBoats.all().values()) {
			ShipGeometry g = Ships.byId(spec.shipId()).geometry();
			HullShape hull = g.hull();
			for (int side : new int[] {1, -1}) {
				List<double[]> cs = ShipBoats.launchCandidates(spec, hull, side);
				assertEquals(18, cs.size(), spec.shipId());
				assertEquals(side, (int) cs.get(0)[2], spec.shipId() + ": the player's side first");
				assertEquals(spec.launchZ(), cs.get(0)[1], 1e-9, spec.shipId() + ": abreast of its chocks");
				assertEquals(-side, (int) cs.get(cs.size() - 1)[2], spec.shipId() + ": then the other side");
				for (double[] c : cs) {
					assertEquals(Math.signum(c[0]), c[2], 1e-9);
					// the whole boat, from post to post, keel to gunwale, is out of the hull with its clearance
					for (double z = -RowboatLayout.TIP; z <= RowboatLayout.TIP + 1e-9; z += 0.25) {
						double hw = RowboatLayout.halfWidth(Math.max(-RowboatLayout.HALF_LENGTH, Math.min(RowboatLayout.HALF_LENGTH, z)));
						for (double x : new double[] {-hw, 0, hw}) {
							double lx = c[0] + x, lz = c[1] + z;
							assertTrue(Math.abs(lx) >= hull.halfWidth(lz) + ShipBoats.CLEARANCE - 1e-9,
									String.format("%s: boat at x %.2f z %.2f against the hull (half width %.2f)", spec.shipId(), lx, lz, hull.halfWidth(lz)));
							for (double y = RowboatLayout.keelY(0); y <= RowboatLayout.railY(z) + 0.2; y += 0.2) {
								assertFalse(g.insideHull(lx, hull.waterlineY + y, lz),
										String.format("%s: boat point %.2f %.2f %.2f inside the hull", spec.shipId(), lx, hull.waterlineY + y, lz));
							}
						}
					}
				}
				// right after the launch it is within reach of its chocks; far out it is not
				double[] first = cs.get(0);
				assertTrue(ShipBoats.inReach(spec, hull, first[0], hull.waterlineY, first[1]), spec.shipId());
				assertTrue(ShipBoats.inReach(spec, hull, cs.get(8)[0], hull.waterlineY, cs.get(8)[1]), spec.shipId() + ": every spot tried is in reach");
				assertFalse(ShipBoats.inReach(spec, hull, first[0] + side * (ShipBoats.RECOVER_MARGIN + 3), hull.waterlineY, first[1]), spec.shipId());
				assertFalse(ShipBoats.inReach(spec, hull, first[0], hull.waterlineY, first[1] + ShipBoats.reach(spec, hull) + 1), spec.shipId());
				assertFalse(ShipBoats.inReach(spec, hull, first[0], hull.waterlineY + ShipBoats.RECOVER_HEIGHT + 1, first[1]), spec.shipId());
			}
			double off = ShipBoats.sideOffset(hull, spec.launchZ());
			assertTrue(off >= hull.halfWidth(spec.launchZ()) + RowboatLayout.MAX_HALF_WIDTH + ShipBoats.CLEARANCE, spec.shipId());
			assertTrue(off < hull.maxHalfWidth + 2.0, spec.shipId() + ": not far out " + off);
		}
	}

	@Test
	void theSideOfThePlayer() {
		assertEquals(1, ShipBoats.sideOf(2.0));
		assertEquals(-1, ShipBoats.sideOf(-2.0));
		assertEquals(1, ShipBoats.sideOf(0.0), "on the middle line: port");
		assertEquals(1, ShipBoats.sideOf(-0.2));
	}

	@Test
	void theClickOnTheDecoBoat() {
		for (ShipBoats.Spec spec : ShipBoats.all().values()) {
			ShipGeometry.LocalBox d = spec.deco();
			double cx = (d.minX() + d.maxX()) / 2, cz = (d.minZ() + d.maxZ()) / 2;
			double t = ShipBoats.pick(spec, new double[] {cx + 3, d.maxY() + 2, cz}, normal(-3, -2.5, 0), 8);
			assertTrue(t > 0, spec.shipId() + ": seen from the deck beside it");
			assertEquals(-1, ShipBoats.pick(spec, new double[] {cx + 3, d.maxY() + 2, cz}, normal(-3, -2.5, 0), 1.0), 1e-9, "out of reach");
			assertEquals(-1, ShipBoats.pick(spec, new double[] {cx + 3, d.maxY() + 2, cz}, normal(1, 0, 0), 8), 1e-9, "looking away");
			assertEquals(-1, ShipBoats.pick(spec, new double[] {cx, (d.minY() + d.maxY()) / 2, cz}, normal(1, 0, 0), 8), 1e-9,
					"never from inside its box (standing where it sits while it is away)");
			assertTrue(ShipBoats.nearDeco(spec, cx, d.maxY(), cz));
			assertFalse(ShipBoats.nearDeco(spec, cx + 5, d.maxY(), cz));
		}
	}

	private static double[] normal(double x, double y, double z) {
		double l = Math.sqrt(x * x + y * y + z * z);
		return new double[] {x / l, y / l, z / l};
	}

	@Test
	void theWarshipsDeckBoxOfItsBoatGoesWithIt() {
		ShipBoats.Spec spec = ShipBoats.of("warship");
		assertNotNull(spec.solid());
		ShipGeometry g = Ships.WARSHIP.geometry();
		assertTrue(g.solids().contains(spec.solid()), "the very box of the deck collisions");
		for (double yaw : new double[] {0, 37, 90, 211}) {
			ShipPose pose = new ShipPose(100.3, 62, -40.7, yaw);
			int[] n = {0, 0};
			ShipGeometry.emitLocal(pose, spec.solid().minX(), spec.solid().minY(), spec.solid().minZ(), spec.solid().maxX(), spec.solid().maxY(),
					spec.solid().maxZ(), (a, b, c, d, e, f) -> {
						n[0]++;
						n[1] += ShipBoats.solidCell(spec, pose, a, b, c, d, e, f) ? 1 : 0;
					});
			assertTrue(n[0] > 0 && n[0] == n[1], "every cell of the boat's box is recognised at yaw " + yaw);
			// the deck under it, the masts and the rest of the waist are not
			double[] w = pose.toWorld(0, Ships.WarshipLayout.MAIN_DECK_Y, 8.0);
			int[] other = {0, 0};
			g.collectBoxes(pose, w[0] - 4, w[1] - 3, w[2] - 4, w[0] + 4, w[1] + 4, w[2] + 4, (a, b, c, d, e, f) -> {
				boolean cell = ShipBoats.solidCell(spec, pose, a, b, c, d, e, f);
				other[cell ? 1 : 0]++;
			});
			assertTrue(other[0] > 20 && other[1] > 0, "deck boxes kept (" + other[0] + "), the boat's dropped (" + other[1] + ")");
		}
		assertFalse(ShipBoats.solidCell(ShipBoats.of("galleon"), new ShipPose(0, 0, 0, 0), -0.1, 1.0, 5.9, 0.1, 2.0, 6.1), "no box for the galleon's");
	}
}
