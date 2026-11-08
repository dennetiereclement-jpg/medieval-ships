package fr.medievalships.client.bridge;

import java.util.Collection;
import java.util.List;

import org.joml.Vector3f;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.client.render.ShipModels;
import fr.medievalships.core.Gangplank;
import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.LeafFrame;
import fr.medievalships.core.bridge.LeafShape;

/**
 * Draws the drawbridges whose leaves are out of the world: every captured block of a leaf, as the game draws a
 * block, turned about the hinge by the angle the client computes from the synced motion and the world time (the
 * same angle as the collision boxes), lit from where it is now; a chain stretched across each end of the deck while
 * the leaves are out (the barrier players feel); and, for the administrator who asked for it, the preview: the two
 * selections, the hinge lines, the arcs the free ends sweep, the raised leaves, the approach zones on both sides of
 * the channel, the passage and the free height. Runs after the entities ({@code WorldRenderEvents.AFTER_ENTITIES}).
 */
public final class DrawbridgeRenderer {
	private static final double DRAW_DISTANCE = 192.0;
	private static final int[] CORD = Gangplank.region("dark_wood", "cord");
	private static final float CHAIN = 0.07f;
	private static final float LINE_WIDTH = 2.5f;

	private DrawbridgeRenderer() {
	}

	public static void render(WorldRenderContext context) {
		MinecraftClient mc = MinecraftClient.getInstance();
		ClientWorld world = mc.world;
		if (world == null || mc.gameRenderer == null || mc.gameRenderer.getCamera() == null) {
			return;
		}
		Collection<DrawbridgeClient.ClientBridge> bridges = DrawbridgeClient.bridges(world);
		if (bridges.isEmpty()) {
			return;
		}
		Vec3d cam = mc.gameRenderer.getCamera().getCameraPos();
		double now = world.getTime() + mc.getRenderTickCounter().getTickProgress(false);
		MatrixStack matrices = context.matrices();
		OrderedRenderCommandQueue queue = context.commandQueue();
		for (DrawbridgeClient.ClientBridge b : bridges) {
			if (!near(b, cam)) {
				continue;
			}
			if (b.leavesOut()) {
				leaves(b, now, cam, world, matrices, queue);
				chains(b, cam, world, matrices, queue);
			}
			if (b.preview) {
				preview(b, cam, matrices, queue);
			}
		}
	}

	private static boolean near(DrawbridgeClient.ClientBridge b, Vec3d cam) {
		double x, z;
		if (b.zones != null) {
			x = b.zones.cx();
			z = b.zones.cz();
		} else if (b.frames[0] != null) {
			x = b.frames[0].hx();
			z = b.frames[0].hz();
		} else if (b.selections[0] != null) {
			x = b.selections[0][0];
			z = b.selections[0][2];
		} else {
			return false;
		}
		double dx = cam.x - x, dz = cam.z - z;
		return dx * dx + dz * dz < DRAW_DISTANCE * DRAW_DISTANCE;
	}

	/** The blocks of both leaves, turned about their hinges. */
	private static void leaves(DrawbridgeClient.ClientBridge b, double now, Vec3d cam, ClientWorld world, MatrixStack matrices,
			OrderedRenderCommandQueue queue) {
		double angle = b.angle(now);
		for (int i = 0; i < 2; i++) {
			LeafFrame f = b.frames[i];
			List<DrawbridgeClient.RenderBlock> blocks = b.blocks.get(i);
			if (f == null || blocks.isEmpty()) {
				continue;
			}
			double[] axis = f.rotationAxis();
			matrices.push();
			matrices.translate(f.hx() - cam.x, f.hy() - cam.y, f.hz() - cam.z);
			matrices.multiply(RotationAxis.of(new Vector3f((float) axis[0], (float) axis[1], (float) axis[2])).rotationDegrees((float) angle));
			for (DrawbridgeClient.RenderBlock rb : blocks) {
				// lit from where the block is now (its centre carried by the rotation)
				double[] l = f.toLocal(rb.x() + 0.5, rb.y() + 0.5, rb.z() + 0.5);
				double[] w = f.toWorld(l[0], l[1], l[2], angle);
				int light = WorldRenderer.getLightmapCoordinates(world, BlockPos.ofFloored(w[0], w[1], w[2]));
				matrices.push();
				matrices.translate(rb.x() - f.hx(), rb.y() - f.hy(), rb.z() - f.hz());
				queue.submitBlock(matrices, rb.state(), light, OverlayTexture.DEFAULT_UV, 0);
				matrices.pop();
			}
			matrices.pop();
		}
	}

	/** A chain stretched across each end of the deck, at hip height: where the barrier stands. */
	private static void chains(DrawbridgeClient.ClientBridge b, Vec3d cam, ClientWorld world, MatrixStack matrices, OrderedRenderCommandQueue queue) {
		RenderLayer layer = RenderLayers.entityCutoutNoCull(ShipModels.GANGPLANK_TEXTURE);
		matrices.push();
		matrices.translate(-cam.x, -cam.y, -cam.z);
		for (int i = 0; i < 2; i++) {
			LeafShape s = b.shapes[i];
			if (s == null || s.isEmpty()) {
				continue;
			}
			LeafFrame f = s.frame();
			double bb = s.minB() - 0.32, cc = s.maxC() + 1.05;
			double[] p0 = f.toWorld(s.minA() - 0.3, bb, cc, 0), p1 = f.toWorld(s.maxA() + 0.3, bb, cc, 0);
			double[] mid = f.toWorld((s.minA() + s.maxA()) / 2, bb, cc, 0);
			int light = WorldRenderer.getLightmapCoordinates(world, BlockPos.ofFloored(mid[0], mid[1], mid[2]));
			// the chain sags a little in the middle
			double[] sag = {mid[0], mid[1] - 0.25, mid[2]};
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				beam(entry, vertices, light, p0, sag, CHAIN);
				beam(entry, vertices, light, sag, p1, CHAIN);
			});
		}
		matrices.pop();
	}

	/** The administrator's preview: wireframes in the world. */
	private static void preview(DrawbridgeClient.ClientBridge b, Vec3d cam, MatrixStack matrices, OrderedRenderCommandQueue queue) {
		matrices.push();
		matrices.translate(-cam.x, -cam.y, -cam.z);
		queue.submitCustom(matrices, RenderLayers.lines(), (entry, vertices) -> {
			int[] colors = {0xFF50FF60, 0xFF5090FF};
			for (int i = 0; i < 2; i++) {
				int[] sel = b.selections[i];
				if (sel != null) {
					box(entry, vertices, sel[0], sel[1], sel[2], sel[3] + 1, sel[4] + 1, sel[5] + 1, colors[i]);
				}
				LeafShape s = b.shapes[i];
				LeafFrame f = b.frames[i];
				if (f == null) {
					continue;
				}
				double a0 = s == null || s.isEmpty() ? -2 : s.minA() - 1, a1 = s == null || s.isEmpty() ? 2 : s.maxA() + 1;
				double[] h0 = f.toWorld(a0, 0, 0, 0), h1 = f.toWorld(a1, 0, 0, 0);
				line(entry, vertices, h0[0], h0[1], h0[2], h1[0], h1[1], h1[2], 0xFFFFE040);
				if (s != null && !s.isEmpty() && b.openAngle > 0) {
					// the arcs of the free end's two corners, and the raised leaf
					for (double a : new double[] {s.minA(), s.maxA()}) {
						double[] prev = null;
						for (double t = 0; t <= b.openAngle + 1e-9; t += 5) {
							double[] p = f.toWorld(a, s.maxB(), s.maxC(), Math.min(t, b.openAngle));
							if (prev != null) {
								line(entry, vertices, prev[0], prev[1], prev[2], p[0], p[1], p[2], 0xFFFF9030);
							}
							prev = p;
						}
					}
					double[] up = s.bounds(b.openAngle);
					box(entry, vertices, up[0], up[1], up[2], up[3], up[4], up[5], 0xFFFF9030);
					double[] bar = s.barrierBox();
					box(entry, vertices, bar[0], bar[1], bar[2], bar[3], bar[4], bar[5], 0xFFFF4040);
				}
			}
			ChannelZones z = b.zones;
			if (z != null) {
				double y = b.waterY + 0.05;
				for (int side : new int[] {1, -1}) {
					rect(entry, vertices, z.corners(side * z.halfSpan(), side * (z.halfSpan() + z.approach()), z.halfWidth() + ChannelZones.LATERAL_MARGIN), y, 0xFF40E0FF);
					rect(entry, vertices, z.corners(side * (z.halfSpan() + z.approach()), side * (z.halfSpan() + z.approach() + z.hysteresis()),
							z.halfWidth() + ChannelZones.LATERAL_MARGIN), y, 0xFF2090A0);
				}
				rect(entry, vertices, z.corners(-z.halfSpan(), z.halfSpan(), z.halfWidth() + ChannelZones.LATERAL_MARGIN), y, 0xFFFF4040);
				rect(entry, vertices, z.corners(-z.halfSpan(), z.halfSpan(), z.halfWidth()), b.undersideY, 0xFFE040FF);
				line(entry, vertices, z.cx(), y, z.cz(), z.cx(), b.undersideY, z.cz(), 0xFFE040FF);
			}
		});
		matrices.pop();
	}

	// ------------------------------------------------------------------ drawing helpers

	private static void line(MatrixStack.Entry e, VertexConsumer v, double x0, double y0, double z0, double x1, double y1, double z1, int color) {
		double dx = x1 - x0, dy = y1 - y0, dz = z1 - z0;
		double len = Math.sqrt(dx * dx + dy * dy + dz * dz);
		if (len < 1e-6) {
			return;
		}
		float nx = (float) (dx / len), ny = (float) (dy / len), nz = (float) (dz / len);
		// the lines layer of 1.21.11 wants position, colour, normal and a line width for every vertex
		v.vertex(e, (float) x0, (float) y0, (float) z0).color(color).normal(e, nx, ny, nz).lineWidth(LINE_WIDTH);
		v.vertex(e, (float) x1, (float) y1, (float) z1).color(color).normal(e, nx, ny, nz).lineWidth(LINE_WIDTH);
	}

	private static void box(MatrixStack.Entry e, VertexConsumer v, double x0, double y0, double z0, double x1, double y1, double z1, int color) {
		line(e, v, x0, y0, z0, x1, y0, z0, color);
		line(e, v, x1, y0, z0, x1, y0, z1, color);
		line(e, v, x1, y0, z1, x0, y0, z1, color);
		line(e, v, x0, y0, z1, x0, y0, z0, color);
		line(e, v, x0, y1, z0, x1, y1, z0, color);
		line(e, v, x1, y1, z0, x1, y1, z1, color);
		line(e, v, x1, y1, z1, x0, y1, z1, color);
		line(e, v, x0, y1, z1, x0, y1, z0, color);
		line(e, v, x0, y0, z0, x0, y1, z0, color);
		line(e, v, x1, y0, z0, x1, y1, z0, color);
		line(e, v, x1, y0, z1, x1, y1, z1, color);
		line(e, v, x0, y0, z1, x0, y1, z1, color);
	}

	/** A horizontal rectangle from its four (x, z) corners at a height. */
	private static void rect(MatrixStack.Entry e, VertexConsumer v, double[][] c, double y, int color) {
		for (int i = 0; i < 4; i++) {
			double[] a = c[i], b = c[(i + 1) % 4];
			line(e, v, a[0], y, a[1], b[0], y, b[1], color);
		}
	}

	/** A thin square beam from p0 to p1 textured as a chain (the gangplank atlas's cord). */
	private static void beam(MatrixStack.Entry e, VertexConsumer v, int light, double[] p0, double[] p1, float th) {
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
		float u0 = CORD[0] / (float) Gangplank.ATLAS, v0 = CORD[1] / (float) Gangplank.ATLAS;
		float u1 = (CORD[0] + CORD[2]) / (float) Gangplank.ATLAS;
		float vw = CORD[3] / (float) Gangplank.ATLAS;
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
