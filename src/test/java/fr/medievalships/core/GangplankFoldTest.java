package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonParser;

import fr.medievalships.client.model.BbModel;

/**
 * The accordion folding of the gangplanks (1.23.1, {@link Gangplank#foldPose}): segment count and model bones, the
 * stowed pack of every equipped vessel (each segment and its folded handrails, from the real model) below the hinge
 * (the rail top) and outside the hull shape, the ship's solids and the fittings measured under the hinge, layers that
 * never cross, joints that stay connected during the whole motion, a smooth motion that starts from the stowed pack
 * and ends exactly as the one-piece plank of 1.23.0 (same points, same collision boxes).
 */
class GangplankFoldTest {
	static final double EPS = 1e-6;

	static List<String> equipped() {
		List<String> ids = new ArrayList<>(GangplankSpecsTest.SHIPS);
		ids.add("steampunk_airship");
		return ids;
	}

	interface PointSink {
		void point(int segment, int side, double u, double v, double w);
	}

	/** Every vertex of the plank model: segment k, handrail side (0: none, -1 / +1), model-local (u, v, w). */
	static void vertices(BbModel plank, int n, PointSink out) {
		BbModel.Pose body = plank.newPose();
		for (int k = 0; k < n; k++) {
			plank.hide(body, "rail_" + k + "_0");
			plank.hide(body, "rail_" + k + "_1");
		}
		BbModel.Pose all = plank.newPose();
		for (int k = 0; k < n; k++) {
			int kk = k;
			plank.renderPart(body, "seg_" + k, (p, uv, nn, glow) -> {
				for (int c = 0; c < 4; c++) {
					out.point(kk, 0, p[c * 3], p[c * 3 + 1], p[c * 3 + 2]);
				}
			});
			for (int side = 0; side < 2; side++) {
				int sd = side == 0 ? -1 : 1;
				plank.renderPart(all, "rail_" + k + "_" + side, (p, uv, nn, glow) -> {
					for (int c = 0; c < 4; c++) {
						out.point(kk, sd, p[c * 3], p[c * 3 + 1], p[c * 3 + 2]);
					}
				});
			}
		}
	}

	@Test
	void segmentCountAndModelBones() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			int n = Gangplank.segments(s);
			int expect = s.segments() > 0 ? s.segments() : Math.max(2, (int) Math.ceil(s.length() / Gangplank.SEGMENT - 1e-9));
			assertEquals(expect, n, id + ": segments");
			double seg = s.length() / n;
			assertTrue(seg >= 0.95 && seg <= 1.8, id + ": segment length " + seg);
			Gangplank.Fold f = Gangplank.fold(s);
			assertEquals(n, f.n(), id);
			assertEquals(seg, f.seg(), EPS, id);
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			for (int k = 0; k < n; k++) {
				assertTrue(plank.hasBone("seg_" + k), id + ": bone seg_" + k);
				double[] o = plank.origin("seg_" + k);
				assertEquals(k * seg, o[0], 1e-3, id + ": seg_" + k + " origin at its inner end");
				assertEquals(0.0, o[1], 1e-3, id);
				for (int side = 0; side < 2; side++) {
					double[] r = plank.origin("rail_" + k + "_" + side);
					assertNotNull(r, id + ": handrail rail_" + k + "_" + side);
					assertEquals(Gangplank.RAIL_PIVOT_V, r[1], 1e-3, id + ": handrail pivot height");
					assertEquals((side == 0 ? -1 : 1) * (s.width() / 2 - Gangplank.RAIL_PIVOT_INSET), r[2], 1e-3, id + ": handrail pivot line");
				}
			}
			assertFalse(plank.hasBone("seg_" + n), id + ": no extra segment");
			// each segment's geometry lies in its own stretch of the plank (its hinge plates reach round the pivot)
			int[] count = new int[n];
			vertices(plank, n, (k, side, u, v, w) -> {
				count[k]++;
				assertTrue(u >= k * seg - 0.2 && u <= (k + 1) * seg + 0.2, id + ": seg_" + k + " vertex at u " + u);
			});
			for (int k = 0; k < n; k++) {
				assertTrue(count[k] > 40, id + ": seg_" + k + " has geometry");
			}
		}
	}

	@Test
	void stowedPackHangsBelowTheRailOutsideTheHull() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			ShipType t = GangplankSpecsTest.type(id);
			ShipGeometry g = t.geometry();
			HullShape h = t.hull();
			Gangplank.Fold f = Gangplank.fold(s);
			// the measured fittings cover the hull shape too (tools/gangplank/ships_g2.py renders with stow_offset alone)
			assertTrue(s.stowOffset() >= Gangplank.hullStandoff(s, h) - 1e-9, id + ": stow_offset under the hull's standoff");
			assertEquals(s.stowOffset() + Gangplank.STOW_CLEARANCE, f.standoff(), 1e-9, id);
			double[] pose = f.stowed();
			double fold = pose[3 * f.n()];
			assertEquals(90.0, fold, EPS, id + ": handrails folded flat");
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			double[] top = {-1e9};
			double[] q = new double[3], r = new double[3];
			int o = s.o();
			vertices(plank, f.n(), (k, side, u, v, w) -> {
				double uu = u, vv = v, ww = w;
				if (side != 0) {
					Gangplank.railPoint(s, side, fold, u, v, w, r);
					uu = r[0];
					vv = r[1];
					ww = r[2];
					// flat on the walking surface, inside the segment's layer
					assertTrue(vv >= -0.01 && vv <= Gangplank.FOLD_OVER + 1e-3, id + ": seg " + k + " folded handrail at v " + vv);
				}
				Gangplank.foldPoint(s, pose, k, uu, vv, ww, q);
				String at = String.format(java.util.Locale.ROOT, "%s seg %d (%s) at %.2f %.2f %.2f", id, k, side == 0 ? "plank" : "handrail", q[0], q[1], q[2]);
				top[0] = Math.max(top[0], q[1]);
				assertTrue(q[1] <= s.hy() - 0.01, at + ": above the hinge (rail top) " + s.hy());
				double out = o * q[0];
				assertTrue(out >= h.halfWidth(q[2]) + 0.02, at + ": not outside the hull (" + h.halfWidth(q[2]) + ")");
				assertTrue(out - o * s.hx() >= s.stowOffset() + 0.02, at + ": on the fittings under the hinge (stow_offset " + s.stowOffset() + ")");
				assertFalse(GangplankSpecsTest.solidAt(g, q[0], q[1], q[2]), at + ": inside a ship solid");
				if (g.interior() == null) {
					assertFalse(g.insideHull(q[0], q[1], q[2]), at + ": inside the hull");
				}
			});
			assertTrue(top[0] <= s.hy() - Gangplank.STOW_DROP + 0.1, id + ": the pack's top " + top[0] + " just under the hinge " + s.hy());
			// compact: one segment high, n layers thick
			double thick = f.thickness();
			assertEquals(f.n() * (Gangplank.FOLD_UNDER + Gangplank.FOLD_OVER), thick, EPS);
			assertTrue(thick <= 3.0, id + ": pack " + thick + " thick");
		}
	}

	@Test
	void layersStackWithoutCrossing() {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			double[] p = f.stowed();
			double prevMax = -1e9;
			for (int k = 0; k < f.n(); k++) {
				double a = p[3 * k];
				// segment k hangs straight down (even) or points straight up (odd)
				assertEquals(0.0, Math.cos(Math.toRadians(a)), 1e-9, id + ": seg " + k + " vertical");
				assertEquals(k % 2 == 0 ? -1.0 : 1.0, -Math.sin(Math.toRadians(a)), 1e-9, id + ": seg " + k + " direction");
				double x0 = p[3 * k + 1] - Gangplank.FOLD_UNDER * Math.sin(Math.toRadians(a));
				double x1 = p[3 * k + 1] + Gangplank.FOLD_OVER * Math.sin(Math.toRadians(a));
				double lo = Math.min(x0, x1), hi = Math.max(x0, x1);
				assertEquals(Gangplank.FOLD_UNDER + Gangplank.FOLD_OVER, hi - lo, 1e-9);
				assertTrue(lo >= prevMax - 1e-9, id + ": layer " + k + " crosses layer " + (k - 1));
				if (k == 0) {
					assertEquals(f.standoff(), lo, 1e-9, id + ": inner face at the standoff");
				} else {
					assertEquals(prevMax, lo, 1e-9, id + ": layers touch");
				}
				prevMax = hi;
				// one segment high, its top STOW_DROP under the hinge
				double y0 = p[3 * k + 2] - k * f.seg() * Math.sin(Math.toRadians(a));
				double y1 = p[3 * k + 2] - (k + 1) * f.seg() * Math.sin(Math.toRadians(a));
				assertEquals(-Gangplank.STOW_DROP, Math.max(y0, y1), 1e-9, id + ": seg " + k + " top");
				assertEquals(-Gangplank.STOW_DROP - f.seg(), Math.min(y0, y1), 1e-9, id + ": seg " + k + " bottom");
			}
		}
	}

	@Test
	void deployedIsTheOnePiecePlankOf1230() throws Exception {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			double[] pose = new double[3 * f.n() + 1];
			BbModel plank = GangplankSpecsTest.load("gangplank_" + id);
			for (double target : new double[] {s.minAngle(), 0.0, 12.5, s.maxAngle()}) {
				Gangplank.foldPose(f, 1.0, target, pose);
				for (int k = 0; k < f.n(); k++) {
					assertEquals(target, pose[3 * k], EPS, id + ": seg " + k + " angle");
					assertEquals(0.0, pose[3 * k + 1], EPS, id + ": seg " + k + " straight");
					assertEquals(0.0, pose[3 * k + 2], EPS, id + ": seg " + k + " straight");
				}
				assertEquals(0.0, pose[3 * f.n()], EPS, id + ": handrails upright");
				double[] st = Gangplank.foldPose(s, Gangplank.State.DEPLOYED, 0, target, new double[3 * f.n() + 1]);
				for (int i = 0; i < pose.length; i++) {
					assertEquals(pose[i], st[i], EPS, id);
				}
				// every vertex of the model where the one-piece plank put it
				double[] q = new double[3];
				vertices(plank, f.n(), (k, side, u, v, w) -> {
					Gangplank.foldPoint(s, pose, k, u, v, w, q);
					double[] e = s.point(target, u, v, w);
					for (int a = 0; a < 3; a++) {
						assertEquals(e[a], q[a], 1e-5, id + " vertex");
					}
				});
				// the same collision boxes as 1.23.0
				List<Gangplank.Box> boxes = Gangplank.deployedBoxes(s, target);
				List<Gangplank.Box> ref = new ArrayList<>(plankBoxes1230(s, target));
				ref.addAll(Gangplank.stairBoxes(s));
				assertEquals(ref, boxes, id + ": deployed boxes at " + target);
			}
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
	void motionIsSmoothAndJointsStayConnected() {
		for (String id : equipped()) {
			Gangplank.Spec s = GangplankSpecsTest.spec(id);
			Gangplank.Fold f = Gangplank.fold(s);
			int n = f.n();
			for (double target : new double[] {s.minAngle(), 15.0, s.maxAngle()}) {
				double[] prev = new double[3 * n + 1], cur = new double[3 * n + 1];
				Gangplank.foldPose(f, 0.0, target, prev);
				for (int i = 0; i < prev.length; i++) {
					assertEquals(f.stowed()[i], prev[i], EPS, id + ": starts from the stowed pack");
				}
				double[] a = new double[3], b = new double[3];
				int steps = 1200;
				for (int i = 1; i <= steps; i++) {
					double p = (double) i / steps;
					Gangplank.foldPose(f, p, target, cur);
					for (int k = 0; k < n; k++) {
						assertTrue(Math.abs(cur[3 * k] - prev[3 * k]) < 4.0, id + ": seg " + k + " jumps at p " + p);
						// both ends of the segment (its walking surface and its underside) move a little at a time
						for (double u : new double[] {k * f.seg(), (k + 1) * f.seg()}) {
							for (double v : new double[] {-Gangplank.FOLD_UNDER, Gangplank.FOLD_OVER}) {
								Gangplank.foldPoint(s, cur, k, u, v, 0, a);
								Gangplank.foldPoint(s, prev, k, u, v, 0, b);
								assertTrue(Math.hypot(a[0] - b[0], a[1] - b[1]) < 0.15, id + ": seg " + k + " jumps at p " + p);
							}
						}
					}
					assertTrue(Math.abs(cur[3 * n] - prev[3 * n]) < 4.0, id + ": handrails jump at p " + p);
					// every joint's pivot is the same point on both segments
					for (int j = 1; j < n; j++) {
						double pv = (j % 2 == 1) ? Gangplank.FOLD_OVER : -Gangplank.FOLD_UNDER;
						Gangplank.foldPoint(s, cur, j - 1, j * f.seg(), pv, 0, a);
						Gangplank.foldPoint(s, cur, j, j * f.seg(), pv, 0, b);
						assertEquals(0.0, Math.hypot(a[0] - b[0], a[1] - b[1]), 1e-9, id + ": joint " + j + " torn at p " + p);
					}
					// segment 0 stays on its hinge once the pack has lifted out
					if (p >= 0.4) {
						Gangplank.foldPoint(s, cur, 0, 0, 0, 0, a);
						assertEquals(s.hx(), a[0], 1e-9, id);
						assertEquals(s.hy(), a[1], 1e-9, id);
					}
					System.arraycopy(cur, 0, prev, 0, cur.length);
				}
				// the handrails stand up only once the plank is straight
				double[] late = new double[3 * n + 1];
				Gangplank.foldPose(f, 0.76, target, late);
				assertEquals(90.0, late[3 * n], EPS, id + ": handrails still flat while unfolding");
				for (int k = 1; k < n; k++) {
					assertEquals(late[0], late[3 * k], 1e-6, id + ": unfolded before the handrails rise");
				}
			}
			// states: a deploy starts stowed and ends straight, a retraction the reverse
			double[] sc = new double[3 * n + 1];
			assertSame(f.stowed(), Gangplank.foldPose(s, Gangplank.State.RETRACTED, 5, 10, sc));
			double[] d0 = Gangplank.foldPose(s, Gangplank.State.DEPLOYING, 0, 10, sc).clone();
			double[] r1 = Gangplank.foldPose(s, Gangplank.State.RETRACTING, Gangplank.DURATION, 10, sc).clone();
			double[] d1 = Gangplank.foldPose(s, Gangplank.State.DEPLOYING, Gangplank.DURATION, 10, sc).clone();
			for (int i = 0; i < sc.length; i++) {
				assertEquals(f.stowed()[i], d0[i], EPS, id);
				assertEquals(f.stowed()[i], r1[i], EPS, id);
			}
			assertEquals(10.0, d1[3 * (n - 1)], EPS, id);
			assertEquals(0.0, d1[3 * (n - 1) + 1], EPS, id);
		}
	}

	@Test
	void segmentsAndStowOffsetFields() {
		String base = "{\"side\":\"port\",\"hinge\":[2,1.5,0],\"width\":2,\"length\":5,\"lever\":[1,0.5,1]";
		Gangplank.Spec auto = Gangplank.parse("t", JsonParser.parseString(base + "}").getAsJsonObject());
		assertEquals(4, Gangplank.segments(auto));
		assertEquals(0.0, auto.stowOffset(), 0);
		Gangplank.Spec four = Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":6,\"stow_offset\":0.4}").getAsJsonObject());
		assertEquals(6, Gangplank.segments(four));
		Gangplank.Fold f = Gangplank.fold(four, null);
		assertEquals(0.4 + Gangplank.STOW_CLEARANCE, f.standoff(), EPS);
		assertEquals(5.0 / 6, f.seg(), EPS);
		Gangplank.Spec shortPlank = Gangplank.parse("t", JsonParser.parseString(
				"{\"side\":\"port\",\"hinge\":[2,1.5,0],\"width\":2,\"length\":1.5,\"lever\":[1,0.5,1]}").getAsJsonObject());
		assertEquals(2, Gangplank.segments(shortPlank), "at least 2 segments");
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":1}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"segments\":13}").getAsJsonObject()));
		assertThrows(IllegalArgumentException.class, () -> Gangplank.parse("t", JsonParser.parseString(base + ",\"stow_offset\":-1}").getAsJsonObject()));
	}
}
