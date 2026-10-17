package fr.medievalships.client.render;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.GalleyEntity;

/**
 * Renders the Blockbench model with its animations: rowing (speed dependent, fading out when
 * the ship stops), wind in the sail, sail furled at rest, steering oars, flag and streamer,
 * plus a light rocking on the waves. All animation inputs come from synced entity state, so
 * every player sees the same thing.
 */
public class GalleyRenderer extends EntityRenderer<GalleyEntity, GalleyRenderState> {
	public GalleyRenderer(EntityRendererFactory.Context context) {
		super(context);
		this.shadowRadius = 0f;
	}

	@Override
	public GalleyRenderState createRenderState() {
		return new GalleyRenderState();
	}

	@Override
	public void updateRenderState(GalleyEntity entity, GalleyRenderState state, float tickProgress) {
		super.updateRenderState(entity, state, tickProgress);
		state.yaw = MathHelper.lerpAngleDegrees(tickProgress, entity.lastTickYaw(), entity.getYaw());
		state.oarTime = MathHelper.lerp(tickProgress, entity.lastOarPhase, entity.oarPhase);
		state.oarWeight = MathHelper.lerp(tickProgress, entity.lastOarWeight, entity.oarWeight);
		state.sailOpen = MathHelper.lerp(tickProgress, entity.lastSailOpen, entity.sailOpen);
		state.helm = MathHelper.lerp(tickProgress, entity.lastHelmVisual, entity.helmVisual);
		state.speed = entity.syncedSpeed();
		state.rockTime = entity.rockTime + tickProgress * 0.05f;
	}

	@Override
	protected Box getBoundingBox(GalleyEntity entity) {
		// the entity box is tiny; cull with the whole hull and mast
		return entity.getBoundingBox().expand(12, 16, 12);
	}

	@Override
	public void render(GalleyRenderState state, MatrixStack matrices, OrderedRenderCommandQueue queue, CameraRenderState cameraState) {
		BbModel model = GalleyModels.galley();
		if (model != null) {
			matrices.push();
			matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-state.yaw));
			double rock = ConfigManager.get().waveRocking;
			float t = state.rockTime;
			float heel = state.helm * Math.min(1f, Math.abs(state.speed) / 6f) * 2.5f;
			matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees((float) (Math.sin(t * 0.9) * 0.45 * rock)));
			matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees((float) (Math.sin(t * 0.63) * 0.9 * rock) + heel));
			matrices.translate(0, Math.sin(t * 1.1) * 0.03 * rock, 0);

			float oarTime = state.oarTime, oarWeight = state.oarWeight, sail = state.sailOpen;
			float helm = state.helm, age = state.age / 20f;
			int light = state.light;
			queue.submitCustom(matrices, RenderLayers.entityCutoutNoCull(GalleyModels.TEXTURE), (entry, vertices) -> {
				BbModel.Pose pose = model.newPose();
				model.apply(pose, "row", oarTime, oarWeight);
				model.apply(pose, "sail_wind", age, sail);
				model.apply(pose, "sail_furl", 1f - sail, 1f);
				model.apply(pose, "steer", helm + 1f, 1f);
				model.apply(pose, "flag_wave", age, 1f);
				model.apply(pose, "streamer_wave", age, 1f);
				model.render(pose, (p, uv, n, glow) -> {
					int l = glow ? LightmapTextureManager.MAX_LIGHT_COORDINATE : light;
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
		super.render(state, matrices, queue, cameraState);
	}
}
