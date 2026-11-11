package fr.medievalships.client.render;

import org.jetbrains.annotations.Nullable;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.render.block.entity.state.BlockEntityRenderState;
import net.minecraft.client.render.command.ModelCommandRenderer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.InteriorDecor;
import fr.medievalships.core.TentType;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.tent.TentBlockEntity;

/**
 * Draws a tent from its anchor block: the ship renderer's static path (every bone of a tent model is static, so
 * {@link BbModel} uses its cached matrices), lanterns full bright ("glow" elements), the furniture of the
 * decoration mods drawn in place ({@link EmbeddedDecor}, stand-in bones hidden), turned to the block's facing.
 * Levels of detail by distance (config: {@code tentDecorDistance}, {@code tentRenderDistance}): the furniture and
 * the "detail" bone within the first, nothing beyond the second. The renderer is registered as drawing outside
 * its block, so the big model is not cut when the anchor's chunk section leaves the view. The training areas' targets
 * (bones {@code target_<i>}, 1.19.0) are left to their entities (TrainingTargetRenderer) when this client has them.
 */
public class TentBlockEntityRenderer implements BlockEntityRenderer<TentBlockEntity, TentBlockEntityRenderer.State> {
	public static class State extends BlockEntityRenderState {
		@Nullable
		TentType tent;
		int quarter;
		double squaredDistance;
		/** Training areas (1.19.0): the targets drawn by their own entity (bit i = target i), left out here. */
		long targetsDrawn;
	}

	/** Writes the model's quads to the vertex consumer (reused by every command of this renderer, render thread). */
	private final MeshEmitter emitter = new MeshEmitter();

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void updateRenderState(TentBlockEntity be, State state, float tickProgress, Vec3d cameraPos,
			@Nullable ModelCommandRenderer.CrumblingOverlayCommand crumblingOverlay) {
		BlockEntityRenderState.updateBlockEntityRenderState(be, state, crumblingOverlay);
		state.tent = be.tentType();
		state.quarter = be.quarter();
		state.squaredDistance = cameraPos.squaredDistanceTo(be.getPos().getX() + 0.5, be.getPos().getY() + 1.0, be.getPos().getZ() + 0.5);
		state.targetsDrawn = state.tent != null && state.tent.hasTargets() ? TrainingTargetRenderer.drawnMask(be.getWorld(), be.getPos(), state.tent) : 0;
	}

	@Override
	public boolean rendersOutsideBoundingBox() {
		return true;
	}

	@Override
	public int getRenderDistance() {
		return (int) Math.ceil(ConfigManager.server().tentRenderDistance);
	}

	@Override
	public void render(State state, MatrixStack matrices, OrderedRenderCommandQueue queue, CameraRenderState cameraState) {
		TentType type = state.tent;
		if (type == null || RenderStats.skip) {
			return;
		}
		double far = ConfigManager.server().tentRenderDistance;
		if (state.squaredDistance > far * far) {
			return;
		}
		BbModel model = TentModels.get(type);
		if (model == null) {
			return;
		}
		double near = ConfigManager.server().tentDecorDistance;
		boolean detailed = state.squaredDistance < near * near;
		EmbeddedDecor decor = detailed ? EmbeddedDecor.of(type) : null;
		int light = state.lightmapCoordinates;
		int glow = LightmapTextureManager.MAX_LIGHT_COORDINATE;
		matrices.push();
		matrices.translate(0.5, 0, 0.5);
		// out of the view (vanilla never culls a block entity drawn outside its block): nothing is submitted (1.29.0)
		TentType.Box extent = type.extent(state.quarter);
		RenderStats.cells++;
		if (!RenderCulling.visible(matrices.peek().getPositionMatrix(), (float) extent.x0(), (float) extent.y0(), (float) extent.z0(),
				(float) extent.x1(), (float) extent.y1(), (float) extent.z1())) {
			RenderStats.cellsCulled++;
			matrices.pop();
			return;
		}
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-90f * state.quarter));
		RenderLayer layer = RenderLayers.entityCutoutNoCull(TentModels.texture(type));
		long targetsDrawn = state.targetsDrawn;
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			long t0 = System.nanoTime();
			BbModel.Pose pose = model.scratchPose();
			// the training targets that their entity draws (moving, TrainingTargetRenderer); the others stay here, at rest
			for (int i = 0; targetsDrawn != 0 && i < type.targets().size() && i < 64; i++) {
				if ((targetsDrawn >> i & 1) != 0) {
					model.hide(pose, type.targets().get(i).bone());
				}
			}
			if (decor != null) {
				for (String bone : decor.hidden) {
					model.hide(pose, bone);
				}
			}
			if (!detailed) {
				model.hide(pose, "detail");
				model.hide(pose, "furniture");
			}
			// every bone of a prop is static: the baked mesh, its cells out of view and its back faces skipped
			model.render(pose, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
			RenderStats.staticQuadsBaked = BbModel.bakedQuads;
			RenderStats.emitNanos += System.nanoTime() - t0;
		});
		if (decor != null) {
			for (int i = 0; i < decor.states.length; i++) {
				if (decor.states[i] == null) {
					continue;
				}
				InteriorDecor.Block b = decor.blocks.get(i);
				matrices.push();
				matrices.translate(b.x(), b.y(), b.z());
				matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(b.yaw()));
				if (b.scale() != 1f) {
					matrices.scale(b.scale(), b.scale(), b.scale());
				}
				matrices.translate(-0.5, 0, -0.5);
				queue.submitBlock(matrices, decor.states[i], b.glow() ? glow : light, OverlayTexture.DEFAULT_UV, 0);
				RenderStats.decorBlocks++;
				matrices.pop();
			}
		}
		matrices.pop();
	}
}
