package fr.medievalships.client.render;

import org.joml.FrustumIntersection;
import org.joml.Matrix4f;
import org.joml.Matrix4fc;

import net.fabricmc.loader.api.FabricLoader;

/**
 * The view frustum of the frame being drawn, in view space (the camera at the origin, looking down -z), for the
 * mod's own culling of what vanilla cannot cull: the cells of a ship's static mesh ({@link BbModel.MeshSink#cellVisible})
 * and the props drawn outside their block ({@link TentBlockEntityRenderer}). Fed by {@code WorldRendererMixin} with the
 * projection matrix of each world render; a box is tested after its corners are transformed by the render command's
 * position matrix (ship-local or block-local to view space), with a margin of one block. Without a frustum (the mixin
 * did not apply, a frame not yet drawn) everything is visible. Switched off under Iris: its shadow pass draws the
 * entities again from the sun's point of view, where the player's frustum would cut their shadows.
 */
public final class RenderCulling {
	/** Margin around a tested box (blocks), against the rounding of the corners and the cells' tight boxes. */
	private static final float MARGIN = 1.0f;
	private static final boolean ENABLED = !FabricLoader.getInstance().isModLoaded("iris") && !FabricLoader.getInstance().isModLoaded("oculus");
	private static final FrustumIntersection FRUSTUM = new FrustumIntersection();
	private static volatile boolean ready;

	private RenderCulling() {
	}

	/** Is the mod's frustum culling in use (a frustum was given and no shader mod forbids it)? */
	public static boolean active() {
		return ENABLED && ready;
	}

	/** Start of a world render: the frustum of this frame, from its projection matrix (view space). */
	public static void frame(Matrix4fc projection) {
		if (!ENABLED || projection == null) {
			return;
		}
		FRUSTUM.set(new Matrix4f(projection), false);
		ready = true;
	}

	/**
	 * Is a box, given in the space of {@code m} (a render command's position matrix, to view space), at least partly in
	 * the frustum? True when culling is not active.
	 */
	public static boolean visible(Matrix4fc m, float minX, float minY, float minZ, float maxX, float maxY, float maxZ) {
		if (!active()) {
			return true;
		}
		float m00 = m.m00(), m01 = m.m01(), m02 = m.m02();
		float m10 = m.m10(), m11 = m.m11(), m12 = m.m12();
		float m20 = m.m20(), m21 = m.m21(), m22 = m.m22();
		float m30 = m.m30(), m31 = m.m31(), m32 = m.m32();
		float vMinX = Float.MAX_VALUE, vMinY = Float.MAX_VALUE, vMinZ = Float.MAX_VALUE;
		float vMaxX = -Float.MAX_VALUE, vMaxY = -Float.MAX_VALUE, vMaxZ = -Float.MAX_VALUE;
		for (int i = 0; i < 8; i++) {
			float x = (i & 1) == 0 ? minX : maxX;
			float y = (i & 2) == 0 ? minY : maxY;
			float z = (i & 4) == 0 ? minZ : maxZ;
			float vx = m00 * x + m10 * y + m20 * z + m30;
			float vy = m01 * x + m11 * y + m21 * z + m31;
			float vz = m02 * x + m12 * y + m22 * z + m32;
			vMinX = Math.min(vMinX, vx);
			vMinY = Math.min(vMinY, vy);
			vMinZ = Math.min(vMinZ, vz);
			vMaxX = Math.max(vMaxX, vx);
			vMaxY = Math.max(vMaxY, vy);
			vMaxZ = Math.max(vMaxZ, vz);
		}
		return FRUSTUM.testAab(vMinX - MARGIN, vMinY - MARGIN, vMinZ - MARGIN, vMaxX + MARGIN, vMaxY + MARGIN, vMaxZ + MARGIN);
	}
}
