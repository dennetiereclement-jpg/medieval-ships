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
 * its block, so the big model is not cut when the anchor's chunk section leaves the view.
 */
public class TentBlockEntityRenderer implements BlockEntityRenderer<TentBlockEntity, TentBlockEntityRenderer.State> {
	public static class State extends BlockEntityRenderState {
		@Nullable
		TentType tent;
		int quarter;
		double squaredDistance;
	}

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
		if (type == null) {
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
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-90f * state.quarter));
		RenderLayer layer = RenderLayers.entityCutoutNoCull(TentModels.texture(type));
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			BbModel.Pose pose = model.newPose();
			if (decor != null) {
				for (String bone : decor.hidden) {
					model.hide(pose, bone);
				}
			}
			if (!detailed) {
				model.hide(pose, "detail");
				model.hide(pose, "furniture");
			}
			model.render(pose, (p, uv, n, isGlow) -> {
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
				matrices.pop();
			}
		}
		matrices.pop();
	}
}
