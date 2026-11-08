package fr.medievalships.client.bridge;

import java.util.Collection;
import java.util.List;

import org.joml.Vector3f;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.LeafFrame;
import fr.medievalships.core.bridge.LeafShape;

/**
 * Draws the drawbridges. For a converted bridge, whatever its state: the hinge of each leaf (an iron axle along the
 * hinge line, a bearing at each end) and, unless the bridge's {@code chaines} option is off, its mechanism: a winch
 * beam over the hinge, from tower to tower, two drums on it, and from each drum a chain down to a shackle at the
 * corner of the leaf's free end, drawn as the game draws its chain block (two crossed strips, the link pattern every
 * block, counted from the shackle so that a chain which shortens winds its links into the drum). While the leaves
 * are out of the world: every captured block of a leaf, as the game draws a block, turned about the hinge by the
 * angle the client computes from the synced motion and the world time (the same angle as the collision boxes), lit
 * from where it is now (a lantern keeps its own light); and across each end of the deck two posts and a sagging
 * chain, where the barrier players feel stands. For the administrator who asked for it, the preview: the two
 * selections, the hinge lines, the arcs the free ends sweep, the raised leaves, the approach zones on both sides of
 * the channel, the passage and the free height. Runs after the entities ({@code WorldRenderEvents.AFTER_ENTITIES}).
 */
public final class DrawbridgeRenderer {
	private static final double DRAW_DISTANCE = 192.0;
	/** The game's chain block texture (named iron_chain since the copper chains): two strips of 3 px in 16. */
	private static final Identifier CHAIN_TEXTURE = Identifier.ofVanilla("textures/block/iron_chain.png");
	private static final Identifier IRON_TEXTURE = Identifier.ofVanilla("textures/block/iron_block.png");
	private static final Identifier WOOD_TEXTURE = Identifier.ofVanilla("textures/block/stripped_dark_oak_log.png");
	private static final float CHAIN_HALF = 1.5f / 16f;
	/** The iron block darkened to wrought iron. */
	private static final int IRON = 0xFF55555C;
	private static final int WOOD = 0xFFFFFFFF;
	private static final int WHITE = 0xFFFFFFFF;
	private static final float LINE_WIDTH = 2.5f;
	/** Set back of the winch beam's axis from the hinge line, towards the shore. */
	private static final double BEAM_BACK = -0.45;

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
			boolean out = b.leavesOut();
			double angle = out ? b.angle(now) : 0;
			if (out) {
				leaves(b, angle, cam, world, matrices, queue);
				barrier(b, cam, world, matrices, queue);
			}
			if (b.converted) {
				hinges(b, cam, world, matrices, queue);
				if (b.chains) {
					mechanism(b, angle, cam, world, matrices, queue);
				}
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
	private static void leaves(DrawbridgeClient.ClientBridge b, double angle, Vec3d cam, ClientWorld world, MatrixStack matrices,
			OrderedRenderCommandQueue queue) {
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
				int luminance = rb.state().getLuminance();
				if (luminance > 0) {
					// a lantern or a torch of the deck no longer lights the world while it is out of it: keep its own light
					light = LightmapTextureManager.pack(Math.max(LightmapTextureManager.getBlockLightCoordinates(light), luminance),
							LightmapTextureManager.getSkyLightCoordinates(light));
				}
				matrices.push();
				matrices.translate(rb.x() - f.hx(), rb.y() - f.hy(), rb.z() - f.hz());
				queue.submitBlock(matrices, rb.state(), light, OverlayTexture.DEFAULT_UV, 0);
				matrices.pop();
			}
			matrices.pop();
		}
	}

	/** The hinge of each leaf: an iron axle along the hinge line, a bearing just past each side of the deck. */
	private static void hinges(DrawbridgeClient.ClientBridge b, Vec3d cam, ClientWorld world, MatrixStack matrices, OrderedRenderCommandQueue queue) {
		RenderLayer iron = RenderLayers.entityCutoutNoCull(IRON_TEXTURE);
		matrices.push();
		matrices.translate(-cam.x, -cam.y, -cam.z);
		for (int i = 0; i < 2; i++) {
			LeafShape s = b.shapes[i];
			if (s == null || s.isEmpty()) {
				continue;
			}
			LeafFrame f = s.frame();
			int light = light(world, f.toWorld((s.minA() + s.maxA()) / 2, 0.3, -0.3, 0));
			queue.submitCustom(matrices, iron, (e, v) -> {
				prism(e, v, light, IRON, f, s.minA() - 0.45, s.maxA() + 0.45, 0, 0, 0.1);
				box(e, v, light, IRON, f, 0, s.minA() - 0.42, s.minA() - 0.12, -0.22, 0.22, -0.18, 0.18, PLAIN);
				box(e, v, light, IRON, f, 0, s.maxA() + 0.12, s.maxA() + 0.42, -0.22, 0.22, -0.18, 0.18, PLAIN);
			});
		}
		matrices.pop();
	}

	/**
	 * The mechanism of each leaf: the winch beam over the hinge (from half a block past one side of the deck to half
	 * a block past the other: into the towers that flank the deck), a drum for each chain, the two chains down to the
	 * corners of the free end and the shackles there. The drums' height is the leaf's length plus 1.5 by default, or
	 * the bridge's setting.
	 */
	private static void mechanism(DrawbridgeClient.ClientBridge b, double angle, Vec3d cam, ClientWorld world, MatrixStack matrices,
			OrderedRenderCommandQueue queue) {
		RenderLayer chainLayer = RenderLayers.entityCutoutNoCull(CHAIN_TEXTURE);
		RenderLayer iron = RenderLayers.entityCutoutNoCull(IRON_TEXTURE);
		RenderLayer wood = RenderLayers.entityCutoutNoCull(WOOD_TEXTURE);
		matrices.push();
		matrices.translate(-cam.x, -cam.y, -cam.z);
		for (int i = 0; i < 2; i++) {
			LeafShape s = b.shapes[i];
			if (s == null || s.isEmpty()) {
				continue;
			}
			LeafFrame f = s.frame();
			double length = s.maxB() - Math.min(0, s.minB());
			double height = b.chainHeight > 0 ? b.chainHeight : length + 1.5;
			double inset = Math.min(0.5, (s.maxA() - s.minA()) / 4);
			double[] drums = {s.minA() + inset, s.maxA() - inset};
			int beamLight = light(world, f.toWorld((s.minA() + s.maxA()) / 2, 0.4, height - 0.5, 0));
			queue.submitCustom(matrices, wood, (e, v) -> box(e, v, beamLight, WOOD, f, 0, s.minA() - 0.5, s.maxA() + 0.5, BEAM_BACK - 0.2, BEAM_BACK + 0.2,
					height - 0.2, height + 0.2, ALONG_A));
			queue.submitCustom(matrices, iron, (e, v) -> {
				for (double a : drums) {
					prism(e, v, beamLight, IRON, f, a - 0.28, a + 0.28, BEAM_BACK, height, 0.27);
					// the flanges of the drum
					prism(e, v, beamLight, IRON, f, a - 0.32, a - 0.28, BEAM_BACK, height, 0.31);
					prism(e, v, beamLight, IRON, f, a + 0.28, a + 0.32, BEAM_BACK, height, 0.31);
				}
			});
			for (double a : drums) {
				double[] drum = f.toWorld(a, BEAM_BACK, height, 0);
				double[] shackle = f.toWorld(a, s.maxB() - 0.25, s.maxC() + 0.05, angle);
				int light = light(world, lerp(shackle, drum, 0.5));
				queue.submitCustom(matrices, chainLayer, (e, v) -> chain(e, v, light, shackle, drum, 0));
				queue.submitCustom(matrices, iron, (e, v) -> box(e, v, light, IRON, f, angle, a - 0.1, a + 0.1, s.maxB() - 0.36, s.maxB() - 0.14,
						s.maxC() - 0.06, s.maxC() + 0.16, PLAIN));
			}
		}
		matrices.pop();
	}

	/** Two posts and a sagging chain across each end of the deck, where the barrier stands while the leaves are out. */
	private static void barrier(DrawbridgeClient.ClientBridge b, Vec3d cam, ClientWorld world, MatrixStack matrices, OrderedRenderCommandQueue queue) {
		RenderLayer chainLayer = RenderLayers.entityCutoutNoCull(CHAIN_TEXTURE);
		RenderLayer iron = RenderLayers.entityCutoutNoCull(IRON_TEXTURE);
		RenderLayer wood = RenderLayers.entityCutoutNoCull(WOOD_TEXTURE);
		matrices.push();
		matrices.translate(-cam.x, -cam.y, -cam.z);
		for (int i = 0; i < 2; i++) {
			LeafShape s = b.shapes[i];
			if (s == null || s.isEmpty()) {
				continue;
			}
			LeafFrame f = s.frame();
			double bb = s.minB() - 0.32, top = s.maxC() + 1.05;
			// the posts stand on the shore, level with the deck's floor (the layer over the hinge)
			double foot = Math.min(1.0, s.maxC()) - 0.02;
			double a0 = s.minA() + 0.14, a1 = s.maxA() - 0.14;
			int light = light(world, f.toWorld((a0 + a1) / 2, bb, top, 0));
			queue.submitCustom(matrices, wood, (e, v) -> {
				for (double a : new double[] {a0, a1}) {
					box(e, v, light, WOOD, f, 0, a - 0.09, a + 0.09, bb - 0.09, bb + 0.09, foot, top + 0.1, ALONG_C);
				}
			});
			queue.submitCustom(matrices, iron, (e, v) -> {
				for (double a : new double[] {a0, a1}) {
					box(e, v, light, IRON, f, 0, a - 0.11, a + 0.11, bb - 0.11, bb + 0.11, top + 0.08, top + 0.2, PLAIN);
				}
			});
			queue.submitCustom(matrices, chainLayer, (e, v) -> {
				int pieces = 10;
				double at = 0;
				double[] prev = null;
				for (int k = 0; k <= pieces; k++) {
					double t = (double) k / pieces;
					double[] p = f.toWorld(a0 + (a1 - a0) * t, bb, top - 0.3 * 4 * t * (1 - t), 0);
					if (prev != null) {
						at = chain(e, v, light, prev, p, at);
					}
					prev = p;
				}
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
					wireBox(entry, vertices, sel[0], sel[1], sel[2], sel[3] + 1, sel[4] + 1, sel[5] + 1, colors[i]);
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
					wireBox(entry, vertices, up[0], up[1], up[2], up[3], up[4], up[5], 0xFFFF9030);
					double[] bar = s.barrierBox();
					wireBox(entry, vertices, bar[0], bar[1], bar[2], bar[3], bar[4], bar[5], 0xFFFF4040);
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

	// ------------------------------------------------------------------ textured solids

	private static int light(ClientWorld world, double[] p) {
		return WorldRenderer.getLightmapCoordinates(world, BlockPos.ofFloored(p[0], p[1], p[2]));
	}

	/**
	 * A chain from {@code p0} to {@code p1}, as the game draws its chain block: two crossed strips 3/16 wide, the
	 * link pattern repeating every block, counted from {@code p0} ({@code from} blocks into the pattern there) so
	 * that a chain which shortens at {@code p1} winds its links in there. Returns the count reached at {@code p1}.
	 */
	private static double chain(MatrixStack.Entry e, VertexConsumer v, int light, double[] p0, double[] p1, double from) {
		double dx = p1[0] - p0[0], dy = p1[1] - p0[1], dz = p1[2] - p0[2];
		double len = Math.sqrt(dx * dx + dy * dy + dz * dz);
		if (len < 1e-4) {
			return from;
		}
		double[] d = {dx / len, dy / len, dz / len};
		double[] up = Math.abs(d[1]) > 0.95 ? new double[] {1, 0, 0} : new double[] {0, 1, 0};
		double[] s1 = norm(cross(d, up));
		double[] s2 = cross(s1, d);
		double done = 0;
		while (done < len - 1e-6) {
			// each piece stays inside one repeat of the texture (no wrapping needed)
			double phase = (from + done) % 1.0;
			double step = Math.min(len - done, 1.0 - phase);
			if (step < 1e-6) {
				step = Math.min(len - done, 1.0);
				phase = 0;
			}
			double[] a = lerp(p0, p1, done / len), c = lerp(p0, p1, (done + step) / len);
			strip(e, v, light, a, c, s1, s2, 0f, 3f / 16f, (float) phase, (float) (phase + step));
			strip(e, v, light, a, c, s2, s1, 3f / 16f, 6f / 16f, (float) phase, (float) (phase + step));
			done += step;
		}
		return from + len;
	}

	/** One strip of a chain between two points, {@code w} across it (unit), lit along {@code n}. */
	private static void strip(MatrixStack.Entry e, VertexConsumer v, int light, double[] a, double[] c, double[] w, double[] n, float u0, float u1,
			float v0, float v1) {
		double h = CHAIN_HALF;
		vertex(e, v, light, WHITE, n, add(a, w, -h), u0, v0);
		vertex(e, v, light, WHITE, n, add(c, w, -h), u0, v1);
		vertex(e, v, light, WHITE, n, add(c, w, h), u1, v1);
		vertex(e, v, light, WHITE, n, add(a, w, h), u1, v0);
	}

	/** No grain: every face shows the whole texture. */
	private static final int PLAIN = -1;
	/** The texture's vertical runs along the hinge direction and repeats every block (a beam). */
	private static final int ALONG_A = 0;
	/** The texture's vertical runs upward and repeats every block (a post). */
	private static final int ALONG_C = 2;

	/**
	 * A box given in a leaf's local frame ({@code a} along the hinge, {@code b} inward, {@code c} up), turned about
	 * the hinge by {@code angle}. {@code grain} is {@link #PLAIN}, {@link #ALONG_A} or {@link #ALONG_C}.
	 */
	private static void box(MatrixStack.Entry e, VertexConsumer v, int light, int color, LeafFrame f, double angle, double a0, double a1, double b0,
			double b1, double c0, double c1, int grain) {
		double[] lo = {a0, b0, c0}, hi = {a1, b1, c1};
		double[] centre = f.toWorld((a0 + a1) / 2, (b0 + b1) / 2, (c0 + c1) / 2, angle);
		int l = grain < 0 ? 0 : grain, p = (l + 1) % 3, q = (l + 2) % 3;
		double[][][][] k = new double[2][2][2][];
		double[] at = new double[3];
		double start = lo[l];
		boolean first = true;
		while (first || start < hi[l] - 1e-9) {
			double end = grain < 0 ? hi[l] : Math.min(hi[l], start + 1.0);
			float vEnd = grain < 0 ? 1f : (float) (end - start);
			for (int i = 0; i < 2; i++) {
				for (int j = 0; j < 2; j++) {
					for (int m = 0; m < 2; m++) {
						at[l] = i == 0 ? start : end;
						at[p] = j == 0 ? lo[p] : hi[p];
						at[q] = m == 0 ? lo[q] : hi[q];
						k[i][j][m] = f.toWorld(at[0], at[1], at[2], angle);
					}
				}
			}
			// the four faces along the length: texture v along it
			for (int j = 0; j < 2; j++) {
				face(e, v, light, color, centre, k[0][j][0], k[1][j][0], k[1][j][1], k[0][j][1], 0f, 0f, 1f, vEnd);
				face(e, v, light, color, centre, k[0][0][j], k[1][0][j], k[1][1][j], k[0][1][j], 0f, 0f, 1f, vEnd);
			}
			if (first) {
				face(e, v, light, color, centre, k[0][0][0], k[0][0][1], k[0][1][1], k[0][1][0], 0f, 0f, 1f, 1f);
			}
			if (end >= hi[l] - 1e-9) {
				face(e, v, light, color, centre, k[1][0][0], k[1][0][1], k[1][1][1], k[1][1][0], 0f, 0f, 1f, 1f);
			}
			first = false;
			start = end;
		}
	}

	/** An octagonal prism along a leaf's hinge direction, from {@code a0} to {@code a1}, axis at ({@code b}, {@code c}), unturned. */
	private static void prism(MatrixStack.Entry e, VertexConsumer v, int light, int color, LeafFrame f, double a0, double a1, double b, double c,
			double r) {
		double[] centre = f.toWorld((a0 + a1) / 2, b, c, 0);
		double[][] ring0 = new double[8][], ring1 = new double[8][];
		double start = a0;
		boolean first = true;
		while (first || start < a1 - 1e-9) {
			double end = Math.min(a1, start + 1.0);
			float vEnd = (float) (end - start);
			for (int k = 0; k < 8; k++) {
				double t = Math.toRadians(22.5 + 45 * k);
				ring0[k] = f.toWorld(start, b + r * Math.cos(t), c + r * Math.sin(t), 0);
				ring1[k] = f.toWorld(end, b + r * Math.cos(t), c + r * Math.sin(t), 0);
			}
			for (int k = 0; k < 8; k++) {
				int n = (k + 1) % 8;
				face(e, v, light, color, centre, ring0[k], ring1[k], ring1[n], ring0[n], k / 8f, 0f, (k + 1) / 8f, vEnd);
			}
			if (first) {
				face(e, v, light, color, centre, ring0[0], ring0[1], ring0[2], ring0[3], 0f, 0f, 0.5f, 0.5f);
				face(e, v, light, color, centre, ring0[0], ring0[3], ring0[4], ring0[5], 0f, 0.5f, 0.5f, 1f);
				face(e, v, light, color, centre, ring0[0], ring0[5], ring0[6], ring0[7], 0.5f, 0.5f, 1f, 1f);
			}
			if (end >= a1 - 1e-9) {
				face(e, v, light, color, centre, ring1[0], ring1[1], ring1[2], ring1[3], 0f, 0f, 0.5f, 0.5f);
				face(e, v, light, color, centre, ring1[0], ring1[3], ring1[4], ring1[5], 0f, 0.5f, 0.5f, 1f);
				face(e, v, light, color, centre, ring1[0], ring1[5], ring1[6], ring1[7], 0.5f, 0.5f, 1f, 1f);
			}
			first = false;
			start = end;
		}
	}

	/** A quad whose normal is made to point away from {@code centre} (the solid's middle), so it is lit as an outer face. */
	private static void face(MatrixStack.Entry e, VertexConsumer v, int light, int color, double[] centre, double[] p0, double[] p1, double[] p2,
			double[] p3, float u0, float v0, float u1, float v1) {
		double[] n = norm(cross(sub(p1, p0), sub(p3, p0)));
		double[] m = {(p0[0] + p2[0]) / 2 - centre[0], (p0[1] + p2[1]) / 2 - centre[1], (p0[2] + p2[2]) / 2 - centre[2]};
		if (n[0] * m[0] + n[1] * m[1] + n[2] * m[2] < 0) {
			n = neg(n);
		}
		vertex(e, v, light, color, n, p0, u0, v0);
		vertex(e, v, light, color, n, p1, u0, v1);
		vertex(e, v, light, color, n, p2, u1, v1);
		vertex(e, v, light, color, n, p3, u1, v0);
	}

	private static void vertex(MatrixStack.Entry e, VertexConsumer v, int light, int color, double[] n, double[] p, float u, float w) {
		v.vertex(e, (float) p[0], (float) p[1], (float) p[2]).color(color).texture(u, w).overlay(OverlayTexture.DEFAULT_UV).light(light)
				.normal(e, (float) n[0], (float) n[1], (float) n[2]);
	}

	// ------------------------------------------------------------------ wireframes

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

	private static void wireBox(MatrixStack.Entry e, VertexConsumer v, double x0, double y0, double z0, double x1, double y1, double z1, int color) {
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

	// ------------------------------------------------------------------ vectors

	private static double[] cross(double[] a, double[] b) {
		return new double[] {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
	}

	private static double[] sub(double[] a, double[] b) {
		return new double[] {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
	}

	private static double[] norm(double[] a) {
		double l = Math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
		return l < 1e-9 ? new double[] {0, 1, 0} : new double[] {a[0] / l, a[1] / l, a[2] / l};
	}

	private static double[] neg(double[] a) {
		return new double[] {-a[0], -a[1], -a[2]};
	}

	private static double[] lerp(double[] a, double[] b, double t) {
		return new double[] {a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t};
	}

	private static double[] add(double[] p, double[] n, double k) {
		return new double[] {p[0] + n[0] * k, p[1] + n[1] * k, p[2] + n[2] * k};
	}
}
