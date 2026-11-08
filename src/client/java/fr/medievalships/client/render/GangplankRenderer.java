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
 * plank follows the hull): the plank model {@code gangplank_<id>} turned about its hinge by the animated angle (the
 * mapping of {@link Gangplank}'s class doc), the deck lever with its handle flipped by the state, the two support
 * chains / ropes (stretched thin boxes) from the chain anchor, or from a pair of small gallows posts at the hinge, to
 * the plank's outer corners, and the inboard stairs while the plank is out. Everything comes from synced state.
 */
final class GangplankRenderer {
	private static final float CHAIN = 0.05f;
	private static final float POST = 0.13f;
	private static final float POST_HEIGHT = 2.5f;

	private GangplankRenderer() {
	}

	static void render(ShipRenderState state, String shipId, MatrixStack matrices, OrderedRenderCommandQueue queue, int light, boolean far) {
		Gangplank.Spec spec = state.gangplank;
		BbModel plank = ShipModels.gangplank(shipId);
		RenderLayer layer = RenderLayers.entityCutoutNoCull(ShipModels.GANGPLANK_TEXTURE);
		double a = state.gangplankAngle;
		// ---- the plank, about its hinge
		if (plank != null) {
			matrices.push();
			matrices.translate(spec.hx(), spec.hy(), spec.hz());
			if (spec.o() < 0) {
				matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(180f));
			}
			matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees((float) -a));
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose pose = plank.newPose();
				if (far) {
					plank.hide(pose, "detail");
				}
				plank.render(pose, sink(entry, vertices, light));
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
				BbModel.Pose pose = lever.newPose();
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
					BbModel.Pose pose = lever.newPose();
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
			double hw = spec.width() / 2 - 0.08;
			for (double w : new double[] {-hw, hw}) {
				double[] corner = spec.point(a, spec.length() - 0.25, 0.06, w);
				double[] from;
				if (spec.hasChainAnchor()) {
					from = spec.chainAnchor(w);
				} else {
					// a small gallows post at each end of the hinge, a sheave on top
					double px = spec.hx() - spec.o() * 0.12, pz = spec.hz() + spec.o() * (w + Math.signum(w) * 0.2);
					box(entry, vertices, light, rail, px - POST / 2, spec.hy() - 0.1, pz - POST / 2, px + POST / 2, spec.hy() + POST_HEIGHT, pz + POST / 2);
					box(entry, vertices, light, metal, px - 0.1, spec.hy() + POST_HEIGHT - 0.2, pz - 0.1, px + 0.1, spec.hy() + POST_HEIGHT + 0.04,
							pz + 0.1);
					from = new double[] {px, spec.hy() + POST_HEIGHT - 0.08, pz};
				}
				beam(entry, vertices, light, cord, from, corner, CHAIN);
			}
			if (out) {
				for (Gangplank.Box b : Gangplank.stairBoxes(spec)) {
					stair(entry, vertices, light, plankTop, board, b);
				}
			}
		});
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
