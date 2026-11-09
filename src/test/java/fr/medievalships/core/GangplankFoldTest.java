package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The compact stowed gangplank (1.23.2, {@link Gangplank#foldPose}): a centre strip with two side wings folded over
 * it and telescoping segments nested in segment 0. For every equipped vessel, from the real plank model and the real
 * ship model: the stowed pack is small (its footprint on the hull at most 40 % of the 1.23.1 accordion pack's, half
 * the plank wide), under the hinge, thin (at most 0.35 block out of the hull), flat against the ship model's surface
 * without ever entering it, showing only its hull-coloured camouflage outboard; nothing sticks out (handrails
 * telescoped inside the pack, chains retracted, gallows posts sunk, nested segments hidden); the motion is continuous
 * (wings, then segments one at a time, then the handrails) and ends exactly as the one-piece plank of 1.23.0 (same
 * points, same collision boxes).
 */
class GangplankFoldTest {
	static final double EPS = 1e-6;

	/** The 1.23.1 accordion pack of each vessel (measured on its models): width along the hull, height, protrusion. */
	static final Map<String, double[]> ACCORDION = Map.ofEntries(
			Map.entry("galley", new double[] {2.144, 1.323, 1.272}),
			Map.entry("galleon", new double[] {2.144, 1.531, 1.708}),
			Map.entry("warship", new double[] {2.544, 1.656, 2.506}),
			Map.entry("medieval_galley", new double[] {2.144, 1.156, 1.696}),
			Map.entry("steam_paddleboat", new double[] {2.144, 1.531, 1.708}),
			Map.entry("elven_sailboat", new double[] {2.344, 1.490, 1.272}),
			Map.entry("old_corsair", new double[] {3.144, 1.756, 2.082}),
			Map.entry("blue_frigate", new double[] {3.144, 1.585, 2.892}),
			Map.entry("royal_lion_ship", new double[] {3.144, 1.585, 2.892}), // (no 1.23.1 pack: the frigate's, same plank width)
			Map.entry("crystal_airship", new double[] {3.644, 1.531, 1.708}),
			Map.entry("sky_leviathan", new double[] {3.144, 1.531, 1.708}),
			Map.entry("dragon_junk", new double[] {3.144, 1.531, 1.708}),
			Map.entry("steampunk_airship", new double[] {3.144, 1.656, 1.272}),
			// 1.27.0: the city ships never had the accordion pack; the size it would have had (plank width + 0.144, a 1.6 segment)
			Map.entry("fortress_ship", new double[] {3.144, 1.6, 2.4}),
			// (1.27.0, never had the accordion pack: the size the 1.23.1 rule gives its 2.4 x 8.0 plank, 5 segments of 1.6)
			Map.entry("gear_steamship", new double[] {2.544, 1.656, 2.1}));

	static List<String> equipped() {
		List<String> ids = new ArrayList<>(GangplankSpecsTest.SHIPS);
		ids.add("steampunk_airship");
		return ids;
	}

	interface QuadOut {
		/** A quad of segment k, part 0 (strip) or -1 / +1 (wing), rail: a wing's handrail; corners model-local. */
		void quad(int k, int part, boolean rail, float[] p, float[] uv, float[] n);
	}

	/** Every quad of the plank model, by segment, part and handrail. */
	static void quads(BbModel plank, int n, QuadOut out) {
		BbModel.Pose strips = plank.newPose(), wings = plank.newPose(), all = plank.newPose();
		for (int k = 0; k < n; k++) {
			for (int s = 0; s < 2; s++) {
				plank.hide(strips, "wing_" + k + "_" + s);
				plank.hide(wings, "rail_" + k + "_" + s);
			}
		}
		for (int k = 0; k < n; k++) {
			int kk = k;
			plank.renderPart(strips, "seg_" + k, (p, uv, nn, glow) -> out.quad(kk, 0, false, p, uv, nn));
			for (int s = 0; s < 2; s++) {
				int part = s == 0 ? -1 : 1;
				plank.renderPart(wings, "wing_" + k + "_" + s, (p, uv, nn, glow) -> out.quad(kk, part, false, p, uv, nn));
				plank.renderPart(all, "rail_" + k + "_" + s, (p, uv, nn, glow) -> out.quad(kk, part, true, p, uv, nn));
			}
		}
	}

	/** Ship-local corner c of a quad of the plank in a pose (handrails telescoped by the pose), into q. */
	static void place(Gangplank.Spec s, Gangplank.Fold f, double[] pose, int k, int part, boolean rail, float[] p, int c, double[] q) {
		double u = p[c * 3], v = p[c * 3 + 1], w = p[c * 3 + 2];
		if (rail) {
			double[] r = new double[3];
			Gangplank.railPoint(pose[Gangplank.POSE_RAIL], u, v, w, r);
			v = r[1];
		}
		Gangplank.plankPoint(s, f, pose, k, part, u, v, w, q);
	}

	@Test
	void segmentCountAndModelBones() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			int n = Gangplank.segments(s);
			int expect = s.segments() > 0 ? s.segments() : Math.max(2, (int) Math.ceil(s.length() / Gangplank.SEGMENT - 1e-9));
			assertEquals(expect, n, id + ": segments");
			double seg = s.length() / n;
			assertTrue(seg >= 0.5 && seg <= Gangplank.SEGMENT + 1e-9, id + ": segment length " + seg);
			Gangplank.Fold f = Gangplank.fold(s);
			assertEquals(n, f.n(), id);
			assertEquals(seg, f.seg(), EPS, id);
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			for (int k = 0; k < n; k++) {
				double[] o = plank.origin("seg_" + k);
				assertNotNull(o, id + ": bone seg_" + k);
				assertEquals(k * seg, o[0], 1e-3, id + ": seg_" + k + " origin at its inner end");
				for (int side = 0; side < 2; side++) {
					int sg = side == 0 ? -1 : 1;
					double[] w = plank.origin("wing_" + k + "_" + side);
					assertNotNull(w, id + ": wing_" + k + "_" + side);
					assertEquals(Gangplank.WING_PIVOT, w[1], 1e-3, id + ": wing hinge axis height");
					assertEquals(sg * Gangplank.wingPivot(s), w[2], 1e-3, id + ": wing hinge axis");
					double[] r = plank.origin("rail_" + k + "_" + side);
					assertNotNull(r, id + ": rail_" + k + "_" + side);
					assertEquals(sg * (s.width() / 2 - Gangplank.RAIL_INSET), r[2], 1e-3, id + ": handrail on the wing's outer edge");
				}
			}
			assertFalse(plank.hasBone("seg_" + n), id + ": no extra segment");
			// each part lies in its own stretch: the segment along the plank, the strip / wings across it
			int[] count = new int[n];
			double hc = Gangplank.stripHalf(s);
			quads(plank, n, (k, part, rail, p, uv, nn) -> {
				count[k]++;
				for (int c = 0; c < 4; c++) {
					double u = p[c * 3], w = p[c * 3 + 2];
					// (a handrail's rope reaches back to the previous segment's post)
					double from = rail ? (k - 1) * seg : k * seg;
					assertTrue(u >= from - 0.08 && u <= (k + 1) * seg + 0.08, id + ": seg_" + k + (rail ? " rail" : "") + " vertex at u " + u);
					if (part == 0) {
						assertTrue(Math.abs(w) <= hc + 0.08, id + ": strip vertex at w " + w);
					} else {
						assertTrue(part * w >= hc - 0.07 && part * w <= s.width() / 2 + 0.035, id + ": wing vertex at w " + w);
					}
				}
			});
			for (int k = 0; k < n; k++) {
				assertTrue(count[k] > 60, id + ": seg_" + k + " has geometry");
			}
		}
	}

	@Test
	void stowedPackIsSmallFlushAndCamouflaged() throws Exception {
		StringBuilder table = new StringBuilder();
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			double[] pose = f.stowed();
			int o = s.o();
			assertEquals(180.0, pose[Gangplank.POSE_WING], EPS, id + ": wings folded over the strip");
			assertEquals(0.0, pose[Gangplank.POSE_RAIL], EPS, id + ": handrails telescoped down");
			assertEquals(0.0, pose[Gangplank.POSE_CHAIN], EPS, id + ": chains retracted");
			assertTrue(Gangplank.postHeight(pose[Gangplank.POSE_CHAIN]) <= 0.1, id + ": gallows posts sunk into the rail");
			assertTrue(Gangplank.visible(pose, 0) && Gangplank.railVisible(pose, 0));
			for (int k = 1; k < f.n(); k++) {
				assertFalse(Gangplank.visible(pose, k), id + ": segment " + k + " nested in segment 0");
			}
			assertFalse(Double.isNaN(s.stowOffset()), id + ": stow_offset measured on the model");
			assertEquals(s.stowOffset() + Gangplank.STOW_CLEARANCE, f.standoff(), 1e-9, id);
			assertEquals(Gangplank.HANG - s.stowTilt(), f.hang(), 1e-9, id);
			double tan = Math.tan(Math.toRadians(s.stowTilt()));
			double top = s.hy() - s.stowDrop();
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			double[] lo = {1e9, 1e9, 1e9}, hi = {-1e9, -1e9, -1e9};
			double[] in = {1e9}, outMax = {-1e9}, prot = {-1e9};
			double[] q = new double[3];
			List<double[]> outward = new ArrayList<>();
			quads(plank, f.n(), (k, part, rail, p, uv, nn) -> {
				if (!Gangplank.visible(pose, k) || rail && !Gangplank.railVisible(pose, k)) {
					return;
				}
				double qmin = 1e9;
				for (int c = 0; c < 4; c++) {
					place(s, f, pose, k, part, rail, p, c, q);
					for (int a = 0; a < 3; a++) {
						lo[a] = Math.min(lo[a], q[a]);
						hi[a] = Math.max(hi[a], q[a]);
					}
					// outboard of the hull surface line the pack lies on (stow_offset at its top, leaning by stow_tilt)
					double depth = Math.max(0, top - q[1]);
					double rel = o * (q[0] - s.hx()) - (s.stowOffset() + depth * tan);
					in[0] = Math.min(in[0], rel);
					prot[0] = Math.max(prot[0], rel);
					outMax[0] = Math.max(outMax[0], o * (q[0] - s.hx()) - depth * tan);
					qmin = Math.min(qmin, o * (q[0] - s.hx()) - depth * tan);
					String at = String.format(Locale.ROOT, "%s seg %d part %d%s at %.2f %.2f %.2f", id, k, part, rail ? " rail" : "", q[0], q[1], q[2]);
					assertTrue(q[1] <= s.hy() - 0.02, at + ": above the hinge (rail top) " + s.hy());
				}
				// faces looking outboard (normal turned by the wing fold and the hang)
				double nx = nn[0], ny = nn[1], nz = nn[2];
				if (part != 0) {
					double ph = Math.toRadians(pose[Gangplank.POSE_WING]);
					double rz = nz * Math.cos(ph) - part * ny * Math.sin(ph);
					ny = part * nz * Math.sin(ph) + ny * Math.cos(ph);
					nz = rz;
				}
				double a = Math.toRadians(pose[Gangplank.POSE_A]);
				double mx = nx * Math.cos(a) + ny * Math.sin(a);
				if (mx > 0.9) {
					outward.add(new double[] {qmin, uv[1], uv[3], uv[5], uv[7], part});
				}
			});
			double width = hi[2] - lo[2], height = hi[1] - lo[1];
			double[] old = ACCORDION.get(id);
			double area = width * height, oldArea = old[0] * old[1];
			table.append(String.format(Locale.ROOT, "%s: %.2f x %.2f x %.2f (1.23.1: %.2f x %.2f x %.2f), area %.0f %%%n", id, width, height, prot[0],
					old[0], old[1], old[2], 100 * area / oldArea));
			// small: half the plank wide, a segment high, at most 40 % of the accordion pack's footprint
			assertTrue(width <= s.width() / 2 + 0.2, id + ": pack " + width + " wide along the hull (plank " + s.width() + ")");
			assertTrue(height <= f.seg() + 0.12, id + ": pack " + height + " high (segment " + f.seg() + ")");
			assertTrue(area <= 0.40 * oldArea, id + ": footprint " + area + " > 40 % of the 1.23.1 pack's " + oldArea);
			// flat against the hull: touching (STOW_CLEARANCE), thin (<= 0.35 block out of it)
			assertEquals(Gangplank.STOW_CLEARANCE, in[0], 0.005, id + ": inner face off the hull surface line");
			assertTrue(prot[0] <= 0.36, id + ": protrudes " + prot[0] + " out of the hull");
			assertEquals(f.thickness(), outMax[0] - (f.standoff()), 0.03, id + ": pack thickness");
			// camouflage: what faces outboard at the pack's outer surface is the hull-coloured skin and trim
			int camo = 0, total = 0;
			for (double[] fc : outward) {
				// the outermost layer: the skin and its trim strips (the boards behind them are hidden)
				if (fc[0] < outMax[0] - 0.015) {
					continue;
				}
				total++;
				if (Math.min(Math.min(fc[1], fc[2]), Math.min(fc[3], fc[4])) >= 0.5 - 1e-6) {
					camo++;
				}
			}
			assertTrue(total >= 4, id + ": outer faces found " + total);
			assertTrue(camo >= 0.9 * total, id + ": outer faces in the camouflage cells " + camo + " / " + total);
		}
		System.out.print(table);
	}

	/** Triangles (x0 y0 z0 x1 y1 z1 x2 y2 z2) of a ship model at rest. */
	static List<float[]> triangles(BbModel m) {
		List<float[]> out = new ArrayList<>();
		m.render(m.newPose(), (p, uv, n, glow) -> {
			out.add(new float[] {p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8]});
			out.add(new float[] {p[0], p[1], p[2], p[6], p[7], p[8], p[9], p[10], p[11]});
		});
		return out;
	}

	/** Outermost x (times o) where a ray from far outboard at (y, z) towards the hull meets the model, or NaN. */
	static double outerFace(List<float[]> tris, int o, double y, double z) {
		double best = Double.NaN;
		for (float[] t : tris) {
			// project on the (y, z) plane: point in triangle, then x by barycentrics
			double y0 = t[1], z0 = t[2], y1 = t[4], z1 = t[5], y2 = t[7], z2 = t[8];
			double d = (y1 - y0) * (z2 - z0) - (y2 - y0) * (z1 - z0);
			if (Math.abs(d) < 1e-12) {
				continue;
			}
			double b1 = ((y - y0) * (z2 - z0) - (y2 - y0) * (z - z0)) / d;
			double b2 = ((y1 - y0) * (z - z0) - (y - y0) * (z1 - z0)) / d;
			if (b1 < 0 || b2 < 0 || b1 + b2 > 1) {
				continue;
			}
			double x = t[0] + b1 * (t[3] - t[0]) + b2 * (t[6] - t[0]);
			if (Double.isNaN(best) || o * x > best) {
				best = o * x;
			}
		}
		return best;
	}

	@Test
	void stowedPackLiesOnTheShipModelWithoutEnteringIt() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			double[] pose = f.stowed();
			int o = s.o();
			BbModel ship = GangplankSpecsTest.load(id);
			List<float[]> tris = new ArrayList<>();
			double reach = Gangplank.wingPivot(s) + 0.1;
			for (float[] t : triangles(ship)) {
				// only what lies near the pack (outboard half, around the hinge)
				double zmin = Math.min(t[2], Math.min(t[5], t[8])), zmax = Math.max(t[2], Math.max(t[5], t[8]));
				double ymin = Math.min(t[1], Math.min(t[4], t[7])), ymax = Math.max(t[1], Math.max(t[4], t[7]));
				double xo = Math.max(o * t[0], Math.max(o * t[3], o * t[6]));
				if (zmax >= s.hz() - reach && zmin <= s.hz() + reach && ymax >= s.hy() - s.stowDrop() - f.seg() - 0.2 && ymin <= s.hy()
						&& xo >= o * s.hx() - 1.5) {
					tris.add(t);
				}
			}
			// sample the pack's inner face (the strip's underside) and outer face (the folded wings' skin) over its footprint,
			// row by row: never inside the model at any point; at most 0.5 out of the row's outermost surface (0.35 out of the side plus its relief: planking, mouldings, shields
			// the eye sees; holes such as oar ports go deeper)
			double[] a = new double[3], b = new double[3];
			double hc = Gangplank.stripHalf(s);
			double worstGap = 0, worstOut = 0, worstRowGap = 0;
			int samples = 0;
			for (int i = 1; i < 10; i++) {
				double u = f.seg() * i / 10.0;
				double rowHull = Double.NaN, rowIn = Double.NaN, rowOut = Double.NaN;
				for (int j = -3; j <= 3; j++) {
					double w = (hc - 0.08) * j / 3.0;
					Gangplank.plankPoint(s, f, pose, 0, 0, u, -Gangplank.STRIP_DEPTH + 0.012, w, a);
					double hull = outerFace(tris, o, a[1], a[2]);
					if (Double.isNaN(hull)) {
						continue;
					}
					samples++;
					String at = String.format(Locale.ROOT, "%s at y %.2f z %.2f", id, a[1], a[2]);
					double gap = o * a[0] - hull;
					assertTrue(gap >= 0.0, at + ": the pack enters the ship model (" + gap + ")");
					// the outer face over that point: the skin of the wing folded over it (mirrored about its hinge axis)
					int part = w >= 0 ? 1 : -1;
					Gangplank.plankPoint(s, f, pose, 0, part, u, -Gangplank.WING_DEPTH + 0.012, 2 * part * Gangplank.wingPivot(s) - w, b);
					rowHull = Double.isNaN(rowHull) ? hull : Math.max(rowHull, hull);
					rowIn = Double.isNaN(rowIn) ? o * a[0] : Math.min(rowIn, o * a[0]);
					rowOut = Double.isNaN(rowOut) ? o * b[0] : Math.max(rowOut, o * b[0]);
				}
				if (Double.isNaN(rowHull)) {
					continue;
				}
				worstGap = Math.max(worstGap, rowIn - rowHull);
				worstOut = Math.max(worstOut, rowOut - rowHull);
				String at = String.format(Locale.ROOT, "%s row %d (y %.2f)", id, i, a[1]);
				assertTrue(rowOut - rowHull <= 0.5, at + ": the pack stands " + (rowOut - rowHull) + " out of the ship's side");
				worstRowGap = Math.max(worstRowGap, rowIn - rowHull);
			}
			assertTrue(samples >= 10, id + ": the ship model was found behind the pack (" + samples + " samples; open railings let rays through)");
			// flat against it: the inner face within 0.25 of the side everywhere (it follows the tilt), touching somewhere
			assertTrue(worstRowGap <= 0.25, id + ": the pack stands off the ship's side by " + worstRowGap);
			System.out.printf(Locale.ROOT, "%s: inner face <= %.3f off the side, outer face <= %.3f out of it%n", id, worstGap, worstOut);
		}
	}

	@Test
	void deployedIsTheOnePiecePlankOf1230() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			double[] pose = new double[Gangplank.poseLength(f.n())];
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			for (double target : new double[] {s.minAngle(), 0.0, 12.5, s.maxAngle()}) {
				Gangplank.foldPose(f, 1.0, target, pose);
				assertEquals(target, pose[Gangplank.POSE_A], EPS, id);
				assertEquals(0.0, pose[Gangplank.POSE_X], EPS, id);
				assertEquals(0.0, pose[Gangplank.POSE_Y], EPS, id);
				assertEquals(0.0, pose[Gangplank.POSE_WING], EPS, id + ": wings flat");
				assertEquals(1.0, pose[Gangplank.POSE_RAIL], EPS, id + ": handrails up");
				assertEquals(1.0, pose[Gangplank.POSE_CHAIN], EPS, id + ": chains out");
				for (int k = 0; k < f.n(); k++) {
					assertEquals(1.0, pose[Gangplank.POSE_EXT + k], EPS, id + ": segment " + k + " out");
					assertTrue(Gangplank.visible(pose, k) && Gangplank.railVisible(pose, k));
				}
				double[] st = Gangplank.foldPose(s, Gangplank.State.DEPLOYED, 0, target, new double[pose.length]);
				for (int i = 0; i < pose.length; i++) {
					assertEquals(pose[i], st[i], EPS, id);
				}
				// every vertex of the model (strips, wings, handrails) where the one-piece plank put it
				double[] q = new double[3];
				quads(plank, f.n(), (k, part, rail, p, uv, nn) -> {
					for (int c = 0; c < 4; c++) {
						place(s, f, pose, k, part, rail, p, c, q);
						double[] e = s.point(target, p[c * 3], p[c * 3 + 1], p[c * 3 + 2]);
						for (int ax = 0; ax < 3; ax++) {
							assertEquals(e[ax], q[ax], 1e-5, id + " vertex");
						}
					}
				});
				// the same collision boxes as 1.23.0
				List<Gangplank.Box> boxes = Gangplank.deployedBoxes(s, target);
				List<Gangplank.Box> ref = new ArrayList<>(plankBoxes1230(s, target));
				ref.addAll(Gangplank.stairBoxes(s));
				assertEquals(ref, boxes, id + ": deployed boxes at " + target);
			}
			// the walking surface keeps its wood: the boards' tops are in the style's cells (upper half of the atlas)
			int[] wood = new int[2];
			quads(plank, f.n(), (k, part, rail, p, uv, nn) -> {
				if (!rail && nn[1] > 0.99 && Math.abs(p[1]) < 0.006 && Math.abs(p[4]) < 0.006) {
					wood[1]++;
					if (Math.max(Math.max(uv[1], uv[3]), Math.max(uv[5], uv[7])) <= 0.5 + 1e-6) {
						wood[0]++;
					}
				}
			});
			assertTrue(wood[1] > 0 && wood[0] == wood[1], id + ": walking surface in the style's wood " + wood[0] + " / " + wood[1]);
		}
	}

	/** Gangplank.plankBoxes as released in 1.23.0 (reference copy). */
	static List<Gangplank.Box> plankBoxes1230(Gangplank.Spec spec, double a) {
		double r = Math.toRadians(a), c = Math.cos(r), s = Math.sin(r);
		double L = spec.length();
		int n = Math.max(2, (int) Math.ceil(L * Math.abs(s) / 0.25 - 1e-9));
		n = Math.max(n, (int) Math.ceil(L * c / 1.0));
		List<Gangplank.Box> out = new ArrayList<>();
		double z0 = spec.hz() - spec.width() / 2, z1 = spec.hz() + spec.width() / 2;
		for (int k = 0; k < n; k++) {
			double u0 = L * k / n, u1 = L * (k + 1) / n;
			double top = spec.hy() - Math.min(u0 * s, u1 * s);
			double x0 = spec.hx() + spec.o() * (k == 0 ? -0.3 : u0 * c);
			double x1 = spec.hx() + spec.o() * u1 * c;
			out.add(Gangplank.Box.of(x0, top - 0.3, z0, x1, top, z1));
		}
		return out;
	}

	@Test
	void motionIsSmoothInOrderAndEndsStraight() {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			int n = f.n();
			int len = Gangplank.poseLength(n);
			for (double target : new double[] {s.minAngle(), 15.0, s.maxAngle()}) {
				double[] prev = new double[len], cur = new double[len];
				Gangplank.foldPose(f, 0.0, target, prev);
				for (int i = 0; i < len; i++) {
					assertEquals(f.stowed()[i], prev[i], EPS, id + ": starts from the stowed pack");
				}
				double[] a = new double[3], b = new double[3];
				int steps = 1200;
				for (int i = 1; i <= steps; i++) {
					double p = (double) i / steps;
					Gangplank.foldPose(f, p, target, cur);
					assertTrue(Math.abs(cur[Gangplank.POSE_A] - prev[Gangplank.POSE_A]) < 4.0, id + ": plank jumps at p " + p);
					assertTrue(Math.abs(cur[Gangplank.POSE_WING] - prev[Gangplank.POSE_WING]) < 4.0, id + ": wings jump at p " + p);
					assertTrue(Math.abs(cur[Gangplank.POSE_RAIL] - prev[Gangplank.POSE_RAIL]) < 0.05, id + ": handrails jump at p " + p);
					int sliding = 0;
					for (int k = 1; k < n; k++) {
						double e = cur[Gangplank.POSE_EXT + k];
						assertTrue(e >= prev[Gangplank.POSE_EXT + k] - EPS, id + ": segment " + k + " slides back while deploying");
						if (e > 0 && e < 1) {
							sliding++;
						}
						if (e > 0) {
							assertEquals(0.0, cur[Gangplank.POSE_WING], 1e-9, id + ": wings open before the segments slide out");
							assertEquals(1.0, cur[Gangplank.POSE_EXT + k - 1], 1e-9, id + ": segment " + k + " before " + (k - 1) + " is out");
						}
					}
					assertTrue(sliding <= 1, id + ": one segment slides at a time (p " + p + ")");
					if (cur[Gangplank.POSE_RAIL] > 0) {
						assertEquals(1.0, cur[Gangplank.POSE_EXT + n - 1], 1e-9, id + ": handrails rise once the plank is all out");
					}
					// every drawn segment's ends move a little at a time (strip and wing tip corners)
					for (int k = 0; k < n; k++) {
						if (!Gangplank.visible(prev, k) || !Gangplank.visible(cur, k)) {
							continue;
						}
						for (double u : new double[] {k * f.seg(), (k + 1) * f.seg()}) {
							for (int part = -1; part <= 1; part++) {
								double w = part == 0 ? 0 : part * s.width() / 2;
								Gangplank.plankPoint(s, f, cur, k, part, u, 0, w, a);
								Gangplank.plankPoint(s, f, prev, k, part, u, 0, w, b);
								double d = Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
								assertTrue(d < 0.25, id + ": seg " + k + " part " + part + " jumps " + d + " at p " + p);
							}
						}
					}
					// a segment appears where it was hidden: inside the previous one (its outer end within it)
					for (int k = 1; k < n; k++) {
						if (!Gangplank.visible(prev, k) && Gangplank.visible(cur, k)) {
							Gangplank.plankPoint(s, f, cur, k, 0, (k + 1) * f.seg(), 0, 0, a);
							Gangplank.plankPoint(s, f, cur, k - 1, 0, k * f.seg(), 0, 0, b);
							assertTrue(Math.hypot(a[0] - b[0], a[1] - b[1]) < 0.1, id + ": segment " + k + " appears outside segment " + (k - 1));
						}
					}
					// the wing stays on its hinge axis, segment 0 on the ship's hinge once lifted out
					if (p >= 0.4) {
						Gangplank.plankPoint(s, f, cur, 0, 0, 0, 0, 0, a);
						assertEquals(s.hx(), a[0], 1e-9, id);
						assertEquals(s.hy(), a[1], 1e-9, id);
					}
					System.arraycopy(cur, 0, prev, 0, len);
				}
			}
			// states: a deploy starts stowed and ends straight, a retraction the reverse
			double[] sc = new double[len];
			assertSame(f.stowed(), Gangplank.foldPose(s, Gangplank.State.RETRACTED, 5, 10, sc));
			double[] d0 = Gangplank.foldPose(s, Gangplank.State.DEPLOYING, 0, 10, sc).clone();
			double[] r1 = Gangplank.foldPose(s, Gangplank.State.RETRACTING, Gangplank.DURATION, 10, sc).clone();
			double[] d1 = Gangplank.foldPose(s, Gangplank.State.DEPLOYING, Gangplank.DURATION, 10, sc).clone();
			for (int i = 0; i < len; i++) {
				assertEquals(f.stowed()[i], d0[i], EPS, id);
				assertEquals(f.stowed()[i], r1[i], EPS, id);
			}
			assertEquals(10.0, d1[Gangplank.POSE_A], EPS, id);
			assertEquals(1.0, d1[Gangplank.POSE_EXT + n - 1], EPS, id);
		}
	}

	@Test
	void specFields() {
		String base = "{\"side\":\"port\",\"hinge\":[2,1.5,0],\"width\":2,\"length\":5,\"lever\":[1,0.5,1]";
		Gangplank.Spec auto = Gangplank.parse("t", JsonParser.parseString(base + "}").getAsJsonObject());
		assertEquals(7, Gangplank.segments(auto));
		assertTrue(Double.isNaN(auto.stowOffset()), "no stow_offset: from the hull shape");
		assertEquals(Gangplank.STOW_DROP, auto.stowDrop(), 0);
		assertEquals(0.0, auto.stowTilt(), 0);
		Gangplank.Fold af = Gangplank.fold(auto, null);
		assertEquals(Gangplank.STOW_CLEARANCE, af.standoff(), EPS, "no hull, no stow_offset: against the hinge line");
		Gangplank.Spec six = Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":9,\"stow_offset\":-0.1,\"stow_drop\":0.4,\"stow_tilt\":12}")
				.getAsJsonObject());
		assertEquals(9, Gangplank.segments(six));
		Gangplank.Fold f = Gangplank.fold(six, null);
		assertEquals(-0.1 + Gangplank.STOW_CLEARANCE, f.standoff(), EPS);
		assertEquals(5.0 / 9, f.seg(), EPS);
		assertEquals(78.0, f.hang(), EPS);
		// the strip's underside passes through (standoff, -stow_drop) at the pack's top, leaning out by the tilt
		double[] q = new double[3];
		Gangplank.plankPoint(six, f, f.stowed(), 0, 0, 0, -Gangplank.STRIP_DEPTH, 0, q);
		assertEquals(six.hx() + six.o() * f.standoff(), q[0], EPS);
		assertEquals(six.hy() - 0.4, q[1], EPS);
		Gangplank.plankPoint(six, f, f.stowed(), 0, 0, 1, -Gangplank.STRIP_DEPTH, 0, q);
		assertEquals(Math.cos(Math.toRadians(78)), six.o() * (q[0] - six.hx()) - f.standoff(), EPS);
		Gangplank.Spec shortPlank = Gangplank.parse("t", JsonParser.parseString(
				"{\"side\":\"port\",\"hinge\":[2,1.5,0],\"width\":2,\"length\":1.2,\"lever\":[1,0.5,1]}").getAsJsonObject());
		assertEquals(2, Gangplank.segments(shortPlank), "at least 2 segments");
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":1}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":21}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"stow_offset\":-1}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"stow_tilt\":50}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"stow_drop\":2}").getAsJsonObject()));
	}
}
