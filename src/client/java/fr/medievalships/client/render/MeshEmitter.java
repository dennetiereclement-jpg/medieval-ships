package fr.medievalships.client.render;

import org.joml.Matrix3f;
import org.joml.Matrix4f;

import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.util.math.MatrixStack;

import fr.medievalships.client.model.BbModel;

/**
 * Writes a model's quads to a vertex consumer with the least work per vertex (1.29.0): the runs of the static mesh
 * ({@link BbModel.MeshSink#mesh}) and the quads of the animated bones alike go through the one-call
 * {@link VertexConsumer#vertex(float, float, float, int, float, float, int, int, float, float, float)} that the vanilla
 * buffer builder (and Sodium's) writes straight to memory, the positions and the face normal transformed here from the
 * command's matrices (no vector allocated, the normal once per face). A cell of the static mesh is skipped when it is
 * out of the frame's view ({@link RenderCulling}), and a face whose cube has the face opposite to it is skipped when it
 * is seen from behind (that face hides it; the two-sided faces are never skipped): the same picture with fewer vertices.
 * One instance per renderer, filled before each command runs ({@link #begin}); render thread only.
 *
 * <p>1.32.0: an emitter for closed models ({@link #MeshEmitter(boolean)}, the doors) skips every face seen from behind,
 * the two-sided ones too: in a closed model the back of a face is never what should be seen, and two coplanar faces of
 * opposite directions (touching cubes) no longer fight for the same pixels.
 *
 * <p>The corners come counter-clockwise seen from the normal's side ({@link BbModel.QuadSink}, 1.30.0) and are written in
 * that order: the entity layers with per-face lighting light the front of a face by its normal, its back by the reversed
 * normal, so a top face is lit as a top (it was lit as a bottom, dark, while the corners came clockwise).
 */
final class MeshEmitter implements BbModel.MeshSink {
	/** Back faces of the cubes skipped (benchmark toggle; the furled sails and effects keep both faces anyway). */
	static volatile boolean cullBackFaces = true;
	private static final int COLOR = 0xFFFFFFFF;
	private VertexConsumer vertices;
	private Matrix4f position;
	private float m00, m01, m02, m10, m11, m12, m20, m21, m22, m30, m31, m32;
	private float n00, n01, n02, n10, n11, n12, n20, n21, n22;
	private float shineX, shineY, shineZ;
	private int lightWorld, lightLamps, lightGlow;
	private boolean shine, cull, backCull;
	/** Closed models: the two-sided faces are culled from behind too. */
	private final boolean closedModels;

	MeshEmitter() {
		this(false);
	}

	/** @param closedModels every face seen from behind is skipped, even when its cube has no opposite face (closed models) */
	MeshEmitter(boolean closedModels) {
		this.closedModels = closedModels;
	}

	/**
	 * @param lightWorld lightmap of the faces lit by the world, {@code lightLamps} of the {@code lit} faces (a vessel's
	 *                   rooms), {@code lightGlow} of the {@code glow} faces
	 * @param shine      the glowing faces take an up normal (full entity shading whatever way they face)
	 * @param cull       cells of the static mesh out of view are skipped
	 * @param backCull   faces seen from behind are skipped (when their cube has the opposite face)
	 */
	MeshEmitter begin(MatrixStack.Entry entry, VertexConsumer vertices, int lightWorld, int lightLamps, int lightGlow, boolean shine, boolean cull,
			boolean backCull) {
		this.vertices = vertices;
		this.position = entry.getPositionMatrix();
		Matrix4f m = position;
		m00 = m.m00();
		m01 = m.m01();
		m02 = m.m02();
		m10 = m.m10();
		m11 = m.m11();
		m12 = m.m12();
		m20 = m.m20();
		m21 = m.m21();
		m22 = m.m22();
		m30 = m.m30();
		m31 = m.m31();
		m32 = m.m32();
		Matrix3f n = entry.getNormalMatrix();
		n00 = n.m00();
		n01 = n.m01();
		n02 = n.m02();
		n10 = n.m10();
		n11 = n.m11();
		n12 = n.m12();
		n20 = n.m20();
		n21 = n.m21();
		n22 = n.m22();
		// the up normal of the shining faces, in view space
		float sx = n10, sy = n11, sz = n12;
		float sl = (float) Math.sqrt(sx * sx + sy * sy + sz * sz);
		sl = sl > 1e-8f ? sl : 1f;
		shineX = sx / sl;
		shineY = sy / sl;
		shineZ = sz / sl;
		this.lightWorld = lightWorld;
		this.lightLamps = lightLamps;
		this.lightGlow = lightGlow;
		this.shine = shine;
		this.cull = cull;
		this.backCull = backCull && cullBackFaces;
		return this;
	}

	@Override
	public boolean cellVisible(float minX, float minY, float minZ, float maxX, float maxY, float maxZ) {
		RenderStats.cells++;
		if (!cull) {
			return true;
		}
		boolean visible = RenderCulling.visible(position, minX, minY, minZ, maxX, maxY, maxZ);
		if (!visible) {
			RenderStats.cellsCulled++;
		}
		return visible;
	}

	@Override
	public void mesh(float[] d, int from, int to, int lightClass, boolean twoSided) {
		int light = lightClass == BbModel.LIGHT_GLOW ? lightGlow : lightClass == BbModel.LIGHT_LAMPS ? lightLamps : lightWorld;
		boolean override = lightClass == BbModel.LIGHT_GLOW && shine;
		boolean skipBack = backCull && (!twoSided || closedModels);
		VertexConsumer vc = vertices;
		int overlay = OverlayTexture.DEFAULT_UV;
		int o = from * BbModel.QUAD_FLOATS;
		long drawn = 0;
		for (int q = from; q < to; q++, o += BbModel.QUAD_FLOATS) {
			float lx = d[o + 20], ly = d[o + 21], lz = d[o + 22];
			float nx = n00 * lx + n10 * ly + n20 * lz;
			float ny = n01 * lx + n11 * ly + n21 * lz;
			float nz = n02 * lx + n12 * ly + n22 * lz;
			float x = d[o], y = d[o + 1], z = d[o + 2];
			float vx = m00 * x + m10 * y + m20 * z + m30;
			float vy = m01 * x + m11 * y + m21 * z + m31;
			float vz = m02 * x + m12 * y + m22 * z + m32;
			boolean behind = nx * vx + ny * vy + nz * vz > 0f;
			if (skipBack && behind) {
				continue; // seen from behind: the opposite face of its cube is in front of it
			}
			if (override) {
				// seen from behind (a two-sided face), OpenGL lights its back with the normal reversed: the down normal then
				float s = behind ? -1f : 1f;
				nx = shineX * s;
				ny = shineY * s;
				nz = shineZ * s;
			} else {
				float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
				if (len > 1e-8f) {
					nx /= len;
					ny /= len;
					nz /= len;
				}
			}
			drawn++;
			vc.vertex(vx, vy, vz, COLOR, d[o + 3], d[o + 4], overlay, light, nx, ny, nz);
			for (int k = 1; k < 4; k++) {
				int c = o + k * 5;
				x = d[c];
				y = d[c + 1];
				z = d[c + 2];
				vc.vertex(m00 * x + m10 * y + m20 * z + m30, m01 * x + m11 * y + m21 * z + m31, m02 * x + m12 * y + m22 * z + m32, COLOR, d[c + 3],
						d[c + 4], overlay, light, nx, ny, nz);
			}
		}
		RenderStats.quads += drawn;
	}

	@Override
	public void quad(float[] p, float[] uv, float[] n, boolean glow) {
		quad(p, uv, n, glow, false, true);
	}

	@Override
	public void quad(float[] p, float[] uv, float[] n, boolean glow, boolean lit) {
		quad(p, uv, n, glow, lit, true);
	}

	@Override
	public void quad(float[] p, float[] uv, float[] n, boolean glow, boolean lit, boolean twoSided) {
		int light = glow ? lightGlow : lit ? lightLamps : lightWorld;
		float lx = n[0], ly = n[1], lz = n[2];
		float nx = n00 * lx + n10 * ly + n20 * lz;
		float ny = n01 * lx + n11 * ly + n21 * lz;
		float nz = n02 * lx + n12 * ly + n22 * lz;
		float x = p[0], y = p[1], z = p[2];
		float vx = m00 * x + m10 * y + m20 * z + m30;
		float vy = m01 * x + m11 * y + m21 * z + m31;
		float vz = m02 * x + m12 * y + m22 * z + m32;
		boolean behind = nx * vx + ny * vy + nz * vz > 0f;
		if (backCull && (!twoSided || closedModels) && behind) {
			return;
		}
		if (glow && shine) {
			float s = behind ? -1f : 1f;
			nx = shineX * s;
			ny = shineY * s;
			nz = shineZ * s;
		} else {
			float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
			if (len > 1e-8f) {
				nx /= len;
				ny /= len;
				nz /= len;
			}
		}
		RenderStats.quads++;
		VertexConsumer vc = vertices;
		int overlay = OverlayTexture.DEFAULT_UV;
		vc.vertex(vx, vy, vz, COLOR, uv[0], uv[1], overlay, light, nx, ny, nz);
		for (int k = 1; k < 4; k++) {
			x = p[k * 3];
			y = p[k * 3 + 1];
			z = p[k * 3 + 2];
			vc.vertex(m00 * x + m10 * y + m20 * z + m30, m01 * x + m11 * y + m21 * z + m31, m02 * x + m12 * y + m22 * z + m32, COLOR, uv[k * 2],
					uv[k * 2 + 1], overlay, light, nx, ny, nz);
		}
	}
}
