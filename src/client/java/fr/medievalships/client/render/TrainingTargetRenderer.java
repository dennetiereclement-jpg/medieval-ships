package fr.medievalships.client.render;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.state.EntityRenderState;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.Entity;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.TargetMotion;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TrainingTarget;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.training.TrainingTargetEntity;

/**
 * Draws a training target (1.19.0): the subtree of its bone {@code target_<i>} from its area's model
 * ({@link BbModel#renderSubtree}), placed and turned exactly like the area's static model (from the anchor block,
 * turned to its facing, the same atlas, render layer and light: at rest it is the very image the area drew before),
 * each bone ({@link TargetMotion#ROOT}... {@link TargetMotion#SWORD}) turned by the target's reaction while it moves.
 *
 * <p>The static renderer of the area (TentBlockEntityRenderer) leaves out the target bones that a target entity draws:
 * {@link #drawnMask} tells it which. A target with no entity on this client (out of the server's tracking range, not
 * spawned yet) is drawn at rest by the static renderer, so the area never shows a hole.
 */
public class TrainingTargetRenderer extends EntityRenderer<TrainingTargetEntity, TrainingTargetRenderer.State> {
	/** The target entities this client knows (client entity load / unload events). */
	private static final Set<TrainingTargetEntity> LOADED = Collections.newSetFromMap(new IdentityHashMap<>());
	private static final String[] NONE = {};

	public static class State extends EntityRenderState {
		@Nullable
		TentType type;
		@Nullable
		TrainingTarget target;
		BlockPos anchor = BlockPos.ORIGIN;
		int quarter;
		int anchorLight;
		boolean moving;
		/** Blockbench degrees per bone, {@link TargetMotion#ROOT}... {@link TargetMotion#SWORD}. */
		final float[][] rot = new float[TargetMotion.BONES][3];
	}

	public TrainingTargetRenderer(EntityRendererFactory.Context context) {
		super(context);
		this.shadowRadius = 0f;
	}

	/** Client entity load event. */
	public static void loaded(Entity entity) {
		if (entity instanceof TrainingTargetEntity t) {
			LOADED.add(t);
		}
	}

	/** Client entity unload event. */
	public static void unloaded(Entity entity) {
		if (entity instanceof TrainingTargetEntity t) {
			LOADED.remove(t);
		}
	}

	/** On disconnect. */
	public static void clear() {
		LOADED.clear();
	}

	/** The targets of the area of {@code type} at {@code anchor} that have an entity on this client: bit i = target i. */
	public static long drawnMask(@Nullable World world, BlockPos anchor, TentType type) {
		if (LOADED.isEmpty() || world == null) {
			return 0;
		}
		long mask = 0;
		for (TrainingTargetEntity t : LOADED) {
			if (!t.isRemoved() && t.getEntityWorld() == world && t.prop() == type && anchor.equals(t.anchor()) && t.index() < 64) {
				mask |= 1L << t.index();
			}
		}
		return mask;
	}

	/** The prop-local origins of a target's bones in the area's model (for its reaction), null for missing bones. */
	public static double[][] joints(TentType type, TrainingTarget target) {
		BbModel model = TentModels.get(type);
		if (model == null) {
			return null;
		}
		String[] bones = bones(target);
		double[][] out = new double[TargetMotion.BONES][];
		for (int b = 0; b < TargetMotion.BONES; b++) {
			out[b] = model.origin(bones[b]);
		}
		return out;
	}

	private static String[] bones(TrainingTarget t) {
		return new String[] {t.bone(), t.head(), t.armLeft(), t.armRight(), t.shield(), t.sword()};
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void updateRenderState(TrainingTargetEntity entity, State state, float tickProgress) {
		super.updateRenderState(entity, state, tickProgress);
		state.type = entity.prop();
		state.target = entity.localTarget();
		state.anchor = entity.anchor();
		state.quarter = entity.quarter();
		state.anchorLight = WorldRenderer.getLightmapCoordinates(entity.getEntityWorld(), state.anchor);
		TargetMotion motion = entity.motion();
		state.moving = motion != null && motion.moving();
		if (state.moving) {
			float[] r = new float[3];
			for (int b = 0; b < TargetMotion.BONES; b++) {
				motion.rotation(b, tickProgress, r);
				// prop-local rotation vector (radians) -> Blockbench Euler degrees (x = -X, y = Y, z = -Z)
				state.rot[b][0] = (float) Math.toDegrees(-r[0]);
				state.rot[b][1] = (float) Math.toDegrees(r[1]);
				state.rot[b][2] = (float) Math.toDegrees(-r[2]);
			}
		}
	}

	/** Culled with a box that holds the whole target at any swing: its box grown by a block, down to its pivot. */
	@Override
	protected Box getBoundingBox(TrainingTargetEntity entity) {
		Box b = entity.getBoundingBox();
		TrainingTarget t = entity.target();
		if (t != null) {
			BlockPos a = entity.anchor();
			b = b.union(new Box(a.getX() + 0.5 + t.px(), a.getY() + t.py(), a.getZ() + 0.5 + t.pz(), a.getX() + 0.5 + t.px(),
					a.getY() + t.py(), a.getZ() + 0.5 + t.pz()));
		}
		return b.expand(1.0);
	}

	@Override
	public void render(State state, MatrixStack matrices, OrderedRenderCommandQueue queue, CameraRenderState cameraState) {
		TentType type = state.type;
		TrainingTarget target = state.target;
		if (type == null || target == null) {
			return;
		}
		BbModel model = TentModels.get(type);
		if (model == null || !model.hasBone(target.bone())) {
			return;
		}
		// the same distances as the area's static renderer (measured to the anchor like it)
		BlockPos a = state.anchor;
		Vec3d cam = cameraState.pos;
		double dx = cam.x - (a.getX() + 0.5), dy = cam.y - (a.getY() + 1.0), dz = cam.z - (a.getZ() + 0.5);
		double d2 = dx * dx + dy * dy + dz * dz;
		double far = ConfigManager.server().tentRenderDistance;
		if (d2 > far * far) {
			return;
		}
		double near = ConfigManager.server().tentDecorDistance;
		boolean detailed = d2 < near * near;
		EmbeddedDecor decor = detailed ? EmbeddedDecor.of(type) : null;
		String[] hidden = decor != null ? decor.hidden.toArray(NONE) : NONE;
		int light = state.anchorLight;
		int glow = LightmapTextureManager.MAX_LIGHT_COORDINATE;
		String[] bones = bones(target);
		float[][] rot = state.moving ? state.rot : null;
		matrices.push();
		// from the entity to the anchor block, then the area's facing: the area's own frame
		matrices.translate(a.getX() + 0.5 - state.x, a.getY() - state.y, a.getZ() + 0.5 - state.z);
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-90f * state.quarter));
		RenderLayer layer = RenderLayers.entityCutoutNoCull(TentModels.texture(type));
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			BbModel.Pose pose = model.newPose();
			for (String bone : hidden) {
				model.hide(pose, bone);
			}
			if (!detailed) {
				model.hide(pose, "detail");
				model.hide(pose, "furniture");
			}
			if (rot != null) {
				for (int b = 0; b < TargetMotion.BONES; b++) {
					model.rotate(pose, bones[b], rot[b][0], rot[b][1], rot[b][2]);
				}
			}
			model.renderSubtree(pose, target.bone(), (p, uv, n, isGlow) -> {
				int l = isGlow ? glow : light;
				for (int k = 0; k < 4; k++) {
					vertices.vertex(entry, p[k * 3], p[k * 3 + 1], p[k * 3 + 2])
							.color(0xFFFFFFFF)
							.texture(uv[k * 2], uv[k * 2 + 1])
							.overlay(OverlayTexture.DEFAULT_UV)
							.light(l)
							.normal(entry, n[0], n[1], n[2]);
				}
			});
		});
		matrices.pop();
	}
}
