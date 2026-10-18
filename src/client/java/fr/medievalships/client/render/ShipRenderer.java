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
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.client.render.ShipModels.Visual;

/**
 * Renders the Blockbench model of a ship type with its animations: rowing (speed dependent,
 * fading out when the ship stops), wind in the sails, sails furled at rest, rudder / steering
 * oars, flags and streamers, plus a light rocking on the waves. Animations a model does not
 * have are skipped. All animation inputs come from synced entity state, so
 * every player sees the same thing.
 */
public class ShipRenderer extends EntityRenderer<ShipEntity, ShipRenderState> {
	private final Visual visual;

	public ShipRenderer(EntityRendererFactory.Context context, Visual visual) {
		super(context);
		this.visual = visual;
		this.shadowRadius = 0f;
	}

	@Override
	public ShipRenderState createRenderState() {
		return new ShipRenderState();
	}

	@Override
	public void updateRenderState(ShipEntity entity, ShipRenderState state, float tickProgress) {
		super.updateRenderState(entity, state, tickProgress);
		state.yaw = MathHelper.lerpAngleDegrees(tickProgress, entity.lastTickYaw(), entity.getYaw());
		state.oarTime = MathHelper.lerp(tickProgress, entity.lastOarPhase, entity.oarPhase);
		state.oarWeight = MathHelper.lerp(tickProgress, entity.lastOarWeight, entity.oarWeight);
		state.wheelTime = MathHelper.lerp(tickProgress, entity.lastWheelPhase, entity.wheelPhase);
		state.sailOpen = MathHelper.lerp(tickProgress, entity.lastSailOpen, entity.sailOpen);
		state.helm = MathHelper.lerp(tickProgress, entity.lastHelmVisual, entity.helmVisual);
		state.speed = entity.syncedSpeed();
		state.rockTime = entity.rockTime + tickProgress * 0.05f;
		state.rockScale = entity.config().waveRocking * visual.rocking() * (entity.config().flight != null ? entity.config().flight.sway : 1.0);
		state.climb = MathHelper.lerp(tickProgress, entity.lastClimbVisual, entity.climbVisual);
	}

	@Override
	protected Box getBoundingBox(ShipEntity entity) {
		// the entity box is tiny; cull with the whole hull and masts
		return entity.getBoundingBox().expand(visual.cullRadius(), visual.cullHeight(), visual.cullRadius());
	}

	@Override
	public void render(ShipRenderState state, MatrixStack matrices, OrderedRenderCommandQueue queue, CameraRenderState cameraState) {
		BbModel model = ShipModels.get(visual);
		if (model != null) {
			matrices.push();
			matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-state.yaw));
			double rock = state.rockScale;
			float t = state.rockTime;
			float heel = state.helm * Math.min(1f, Math.abs(state.speed) / 6f) * 2.5f;
			matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees((float) (Math.sin(t * 0.9) * 0.45 * rock)));
			matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees((float) (Math.sin(t * 0.63) * 0.9 * rock) + heel));
			matrices.translate(0, Math.sin(t * 1.1) * 0.03 * rock, 0);

			float oarTime = state.oarTime, oarWeight = state.oarWeight, sail = state.sailOpen, wheel = state.wheelTime;
			float helm = state.helm, age = state.age / 20f, climb = state.climb;
			int light = state.light;
			for (int tex = 0; tex < model.textureCount() && tex < visual.textures().size(); tex++) {
				int texture = tex;
				queue.submitCustom(matrices, RenderLayers.entityCutoutNoCull(visual.textures().get(tex)), (entry, vertices) -> {
					BbModel.Pose pose = model.newPose();
					model.apply(pose, "row", oarTime, oarWeight);
					model.apply(pose, "paddle", wheel, 1f);
					model.apply(pose, "sail_wind", age, sail);
					model.apply(pose, "sail_furl", 1f - sail, 1f);
					model.apply(pose, "steer", helm + 1f, 1f);
					model.apply(pose, "flag_wave", age, 1f);
					model.apply(pose, "streamer_wave", age, 1f);
					model.apply(pose, "lantern_sway", age, 1f);
					model.apply(pose, "propeller", wheel, 1f);
					model.apply(pose, "elevator", climb + 1f, 1f);
					model.render(pose, visual.textures().size() > 1 ? texture : -1, (p, uv, n, glow) -> {
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
			}
			matrices.pop();
		}
		super.render(state, matrices, queue, cameraState);
	}
}
