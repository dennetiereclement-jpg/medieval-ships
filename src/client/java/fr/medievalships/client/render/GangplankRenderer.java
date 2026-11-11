package fr.medievalships.client.render;

import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.RotationAxis;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.Gangplank;

/**
 * Draws a vessel's boarding gangplank in the ship's model space (inside {@link ShipRenderer}'s transform, so a stowed
 * plank follows the hull): the telescoping, folding plank model {@code gangplank_<id>}, each segment's strip, wings and
 * handrails placed by the fold pose ({@link Gangplank#foldPose} and {@link Gangplank#plankPoint}, the mapping of
 * {@link Gangplank}'s class doc: a small flat hull-coloured pack against the hull side when stowed, opening and sliding
 * out while it deploys, straight once deployed; nested segments are skipped), the deck lever with its handle flipped by
 * the state, the two support chains / ropes (stretched thin boxes) from the chain anchor, or from a pair of gallows posts
 * at the hinge that telescope out of the rail, to the plank's tip (retracted while stowed), and the inboard stairs while
 * the plank is out. Everything comes from synced state; the stowed pose is computed once per vessel, a moving one into
 * a scratch array, and the parts go through {@link BbModel#renderPart} (cached quads) and one reused sink.
 */
final class GangplankRenderer {
	private static final float CHAIN = 0.05f;
	private static final float POST = 0.13f;
	/** Bone names of the segments, their wings and their handrails (no string built per frame). */
	private static final String[] SEG = new String[Gangplank.MAX_SEGMENTS];
	private static final String[][] WING = new String[Gangplank.MAX_SEGMENTS][2];
	private static final String[][] RAIL = new String[Gangplank.MAX_SEGMENTS][2];
	/** Scratch pose of a moving plank and of the chains' end (render thread only; each command fills them before use). */
	private static final double[] POSE = new double[Gangplank.poseLength(Gangplank.MAX_SEGMENTS)];
	private static final double[] TIP = new double[3];
	private static final double[] FROM = new double[3];
	private static final FoldSink FOLD = new FoldSink();

	static {
		for (int k = 0; k < Gangplank.MAX_SEGMENTS; k++) {
			SEG[k] = "seg_" + k;
			for (int side = 0; side < 2; side++) {
				WING[k][side] = "wing_" + k + "_" + side;
				RAIL[k][side] = "rail_" + k + "_" + side;
			}
		}
	}

	private GangplankRenderer() {
	}

	static void render(ShipRenderState state, String shipId, MatrixStack matrices, OrderedRenderCommandQueue queue, int light, boolean far) {
		Gangplank.Spec spec = state.gangplank;
		BbModel plank = ShipModels.gangplank(shipId);
		RenderLayer layer = RenderLayers.entityCutoutNoCull(ShipModels.GANGPLANK_TEXTURE);
		Gangplank.State gp = state.gangplankState;
		double ticks = state.gangplankTicks;
		double target = state.gangplankTarget;
		// ---- the plank: each segment's strip, wings and handrails by the fold pose, about the hinge
		BbModel.Pose[] poses = ShipModels.gangplankPoses(shipId);
		if (plank != null && poses != null) {
			matrices.push();
			matrices.translate(spec.hx(), spec.hy(), spec.hz());
			if (spec.o() < 0) {
				matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(180f));
			}
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				Gangplank.Fold fold = Gangplank.fold(spec);
				int n = fold.n();
				double[] f = Gangplank.foldPose(spec, gp, ticks, target, POSE);
				FoldSink sink = FOLD.begin(entry, vertices, light, spec, f);
				for (int k = 0; k < n; k++) {
					if (!Gangplank.visible(f, k)) {
						continue; // nested inside the previous segment
					}
					sink.segment(fold, k, 0, false);
					plank.renderPart(poses[0], SEG[k], sink);
					for (int side = 0; side < 2; side++) {
						sink.segment(fold, k, side == 0 ? -1 : 1, false);
						plank.renderPart(poses[1], WING[k][side], sink);
						if (!far && Gangplank.railVisible(f, k)) {
							sink.segment(fold, k, side == 0 ? -1 : 1, true);
							plank.renderPart(poses[2], RAIL[k][side], sink);
						}
					}
				}
			});
			matrices.pop();
		}
		if (far) {
			return;
		}
		// ---- the lever: base, then the handle tilted about its pivot
		BbModel lever = ShipModels.lever(spec.style());
		if (lever != null) {
			matrices.push();
			matrices.translate(spec.leverX(), spec.leverY(), spec.leverZ());
			matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees((float) spec.leverYawOrDefault()));
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose pose = lever.scratchPose();
				lever.hide(pose, "handle");
				lever.render(pose, sink(entry, vertices, light));
			});
			double[] pivot = lever.origin("handle");
			if (pivot != null) {
				matrices.translate(pivot[0], pivot[1], pivot[2]);
				// stowed: pulled back (towards -x); deployed: pushed over towards the model's +x
				matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(32f - 64f * state.gangplankLever));
				matrices.translate(-pivot[0], -pivot[1], -pivot[2]);
				queue.submitCustom(matrices, layer, (entry, vertices) -> {
					BbModel.Pose pose = lever.scratchPose();
					lever.renderSubtree(pose, "handle", sink(entry, vertices, light));
				});
			}
			matrices.pop();
		}
		// ---- chains (or ropes), their posts, and the stairs while the plank is out (ship-local boxes)
		int[] cord = Gangplank.region(spec.style(), "cord");
		int[] rail = Gangplank.region(spec.style(), "rail");
		int[] metal = Gangplank.region(spec.style(), "metal");
		int[] board = Gangplank.region(spec.style(), "board");
		int[] plankTop = Gangplank.region(spec.style(), "plank");
		boolean out = state.gangplankOut;
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			Gangplank.Fold fold = Gangplank.fold(spec);
			int n = fold.n();
			double[] f = Gangplank.foldPose(spec, gp, ticks, target, POSE);
			double chain = f[Gangplank.POSE_CHAIN];
			double ph = Gangplank.postHeight(chain);
			for (int side = -1; side <= 1; side += 2) {
				double w = side * (spec.width() / 2 - Gangplank.EYE_INSET);
				double[] from = FROM;
				if (spec.hasChainAnchor()) {
					from = spec.chainAnchor(w);
				} else {
					// a gallows post at each end of the hinge (sunk into the rail while stowed), a sheave on top
					double px = spec.hx() - spec.o() * 0.12, pz = spec.hz() + spec.o() * side * (spec.width() / 2 + 0.12);
					box(entry, vertices, light, rail, px - POST / 2, spec.hy() - 0.1, pz - POST / 2, px + POST / 2, spec.hy() + ph, pz + POST / 2);
					box(entry, vertices, light, metal, px - 0.1, spec.hy() + ph - 0.2, pz - 0.1, px + 0.1, spec.hy() + ph + 0.04, pz + 0.1);
					FROM[0] = px;
					FROM[1] = spec.hy() + ph - 0.08;
					FROM[2] = pz;
				}
				if (chain <= 0) {
					continue; // retracted onto the sheave
				}
				// the eye on the last segment's wing, wherever the folding put it; the chain pays out towards it
				Gangplank.plankPoint(spec, fold, f, n - 1, side, spec.length() - 0.25, 0.05, w, TIP);
				for (int a = 0; a < 3; a++) {
					TIP[a] = from[a] + (TIP[a] - from[a]) * chain;
				}
				beam(entry, vertices, light, cord, from, TIP, CHAIN);
			}
			if (out) {
				for (Gangplank.Box b : Gangplank.stairBoxes(spec)) {
					stair(entry, vertices, light, plankTop, board, b);
				}
			}
		});
	}

	/**
	 * Emits model-local quads of one part of a segment (its strip, a wing or a wing's handrail) placed by the fold pose,
	 * relative to the hinge frame, exactly as {@link Gangplank#plankPoint} (and {@link Gangplank#railPoint}) map them:
	 * the handrail's posts scaled along v, the wing turned about its hinge axis, the segment slid back (lower and narrower
	 * while nested), then (u, v, w) to (cx + u cos a + v sin a, cy - u sin a + v cos a, w). One instance, reused.
	 */
	private static final class FoldSink implements BbModel.QuadSink {
		private MatrixStack.Entry entry;
		private VertexConsumer vertices;
		private int light;
		private float ca, sa, cx, cy;
		/** The part: wing turn (cos, sin, pivot v / w, side), slide back, nesting, handrail scale. */
		private float cw, sw, pv, pz, shift, drop, shrink, railK;
		private int part;
		private boolean rail;
		private Gangplank.Spec spec;
		private double[] pose;

		FoldSink begin(MatrixStack.Entry entry, VertexConsumer vertices, int light, Gangplank.Spec spec, double[] pose) {
			this.entry = entry;
			this.vertices = vertices;
			this.light = light;
			this.spec = spec;
			this.pose = pose;
			double r = Math.toRadians(pose[Gangplank.POSE_A]);
			ca = (float) Math.cos(r);
			sa = (float) Math.sin(r);
			cx = (float) pose[Gangplank.POSE_X];
			cy = (float) pose[Gangplank.POSE_Y];
			double ph = Math.toRadians(pose[Gangplank.POSE_WING]);
			cw = (float) Math.cos(ph);
			sw = (float) Math.sin(ph);
			pv = (float) Gangplank.WING_PIVOT;
			railK = (float) Gangplank.railScale(pose[Gangplank.POSE_RAIL]);
			return this;
		}

		/** The next quads are segment k's part (0 strip, -1 / +1 wing), a wing's handrail if {@code isRail}. */
		void segment(Gangplank.Fold fold, int k, int part, boolean isRail) {
			this.part = part;
			this.rail = isRail;
			pz = (float) (part * Gangplank.wingPivot(spec));
			shift = (float) Gangplank.nestShift(fold, pose, k);
			double nest = Gangplank.nestOffset(pose, k);
			drop = (float) (Gangplank.NEST_DROP * nest);
			shrink = (float) (1.0 - (1.0 - Gangplank.NEST_SHRINK) * nest);
		}

		@Override
		public void quad(float[] p, float[] uv, float[] n, boolean glow) {
			float nx = n[0], ny = n[1], nz = n[2];
			if (part != 0) {
				float rz = nz * cw - part * ny * sw, ry = part * nz * sw + ny * cw;
				ny = ry;
				nz = rz;
			}
			float mx = nx * ca + ny * sa, my = -nx * sa + ny * ca;
			for (int k = 0; k < 4; k++) {
				float x = p[k * 3], y = p[k * 3 + 1], z = p[k * 3 + 2];
				if (rail) {
					y *= railK;
				}
				if (part != 0) {
					float dv = y - pv, dw = z - pz;
					z = pz + dw * cw - part * dv * sw;
					y = pv + part * dw * sw + dv * cw;
				}
				x -= shift;
				y -= drop;
				z *= shrink;
				vertices.vertex(entry, cx + x * ca + y * sa, cy - x * sa + y * ca, z)
						.color(0xFFFFFFFF)
						.texture(uv[k * 2], uv[k * 2 + 1])
						.overlay(OverlayTexture.DEFAULT_UV)
						.light(light)
						.normal(entry, mx, my, nz);
			}
		}
	}

	private static BbModel.QuadSink sink(MatrixStack.Entry entry, VertexConsumer vertices, int light) {
		return new BbModel.QuadSink() {
			@Override
			public void quad(float[] p, float[] uv, float[] n, boolean glow) {
				for (int k = 0; k < 4; k++) {
					vertices.vertex(entry, p[k * 3], p[k * 3 + 1], p[k * 3 + 2])
							.color(0xFFFFFFFF)
							.texture(uv[k * 2], uv[k * 2 + 1])
							.overlay(OverlayTexture.DEFAULT_UV)
							.light(light)
							.normal(entry, n[0], n[1], n[2]);
				}
			}
		};
	}

	/** A stair: its top in plank boards, its sides in board. */
	private static void stair(MatrixStack.Entry e, VertexConsumer v, int light, int[] top, int[] side, Gangplank.Box b) {
		box(e, v, light, side, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY() - 0.06, b.maxZ());
		box(e, v, light, top, b.minX() - 0.02, b.maxY() - 0.06, b.minZ() - 0.02, b.maxX() + 0.02, b.maxY(), b.maxZ() + 0.02);
	}

	/** A thin square beam from p0 to p1 (a chain or a rope), the texture's u along it. */
	private static void beam(MatrixStack.Entry e, VertexConsumer v, int light, int[] region, double[] p0, double[] p1, float th) {
		double dx = p1[0] - p0[0], dy = p1[1] - p0[1], dz = p1[2] - p0[2];
		double len = Math.sqrt(dx * dx + dy * dy + dz * dz);
		if (len < 1e-4) {
			return;
		}
		double[] d = {dx / len, dy / len, dz / len};
		double[] up = Math.abs(d[1]) > 0.95 ? new double[] {1, 0, 0} : new double[] {0, 1, 0};
		double[] s1 = norm(cross(d, up));
		double[] s2 = cross(s1, d);
		double h = th / 2;
		float u0 = region[0] / (float) Gangplank.ATLAS, v0 = region[1] / (float) Gangplank.ATLAS;
		float u1 = (region[0] + region[2]) / (float) Gangplank.ATLAS;
		float vw = region[3] / (float) Gangplank.ATLAS;
		// repeat the 16 px tile every 0.5 block along the chain (rounded to whole tiles)
		int reps = Math.max(1, (int) Math.round(len / 0.5));
		for (int r = 0; r < reps; r++) {
			double t0 = (double) r / reps, t1 = (double) (r + 1) / reps;
			double[] a = lerp(p0, p1, t0), b = lerp(p0, p1, t1);
			for (int k = 0; k < 4; k++) {
				double[] n = k == 0 ? s1 : k == 1 ? s2 : k == 2 ? neg(s1) : neg(s2);
				double[] m = k == 0 ? s2 : k == 1 ? neg(s1) : k == 2 ? neg(s2) : s1;
				double[] c0 = add(a, n, h, m, -h), c1 = add(b, n, h, m, -h), c2 = add(b, n, h, m, h), c3 = add(a, n, h, m, h);
				quad(e, v, light, n, c0, c1, c2, c3, u0, v0, u1, v0 + vw * 0.5f);
			}
		}
	}

	/** An axis aligned box (ship-local), each face showing the whole region. */
	private static void box(MatrixStack.Entry e, VertexConsumer v, int light, int[] region, double x0, double y0, double z0, double x1, double y1,
			double z1) {
		float u0 = region[0] / (float) Gangplank.ATLAS, v0 = region[1] / (float) Gangplank.ATLAS;
		float u1 = (region[0] + region[2]) / (float) Gangplank.ATLAS, v1 = (region[1] + region[3]) / (float) Gangplank.ATLAS;
		double[][] c = {{x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0}, {x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}};
		quad(e, v, light, new double[] {0, 0, -1}, c[1], c[0], c[3], c[2], u0, v0, u1, v1);
		quad(e, v, light, new double[] {0, 0, 1}, c[4], c[5], c[6], c[7], u0, v0, u1, v1);
		quad(e, v, light, new double[] {-1, 0, 0}, c[0], c[4], c[7], c[3], u0, v0, u1, v1);
		quad(e, v, light, new double[] {1, 0, 0}, c[5], c[1], c[2], c[6], u0, v0, u1, v1);
		quad(e, v, light, new double[] {0, 1, 0}, c[3], c[7], c[6], c[2], u0, v0, u1, v1);
		quad(e, v, light, new double[] {0, -1, 0}, c[0], c[1], c[5], c[4], u0, v0, u1, v1);
	}

	/** One quad: corners a b c d (counter-clockwise seen from outside), u from a to b, v from d to a. */
	private static void quad(MatrixStack.Entry e, VertexConsumer v, int light, double[] n, double[] a, double[] b, double[] c, double[] d,
			float u0, float v0, float u1, float v1) {
		vertex(e, v, light, n, a, u0, v1);
		vertex(e, v, light, n, b, u1, v1);
		vertex(e, v, light, n, c, u1, v0);
		vertex(e, v, light, n, d, u0, v0);
	}

	private static void vertex(MatrixStack.Entry e, VertexConsumer v, int light, double[] n, double[] p, float u, float w) {
		v.vertex(e, (float) p[0], (float) p[1], (float) p[2]).color(0xFFFFFFFF).texture(u, w).overlay(OverlayTexture.DEFAULT_UV).light(light)
				.normal(e, (float) n[0], (float) n[1], (float) n[2]);
	}

	private static double[] cross(double[] a, double[] b) {
		return new double[] {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
	}

	private static double[] norm(double[] a) {
		double l = Math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
		return l < 1e-9 ? new double[] {1, 0, 0} : new double[] {a[0] / l, a[1] / l, a[2] / l};
	}

	private static double[] neg(double[] a) {
		return new double[] {-a[0], -a[1], -a[2]};
	}

	private static double[] lerp(double[] a, double[] b, double t) {
		return new double[] {a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t};
	}

	private static double[] add(double[] p, double[] n, double kn, double[] m, double km) {
		return new double[] {p[0] + n[0] * kn + m[0] * km, p[1] + n[1] * kn + m[1] * km, p[2] + n[2] * kn + m[2] * km};
	}
}
