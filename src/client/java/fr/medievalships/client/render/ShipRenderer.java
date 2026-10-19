package fr.medievalships.client.render;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.Ships;
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
	/** Block light of the rooms of a vessel (its electric lamps). */
	private static final int INTERIOR_BLOCK_LIGHT = 13;
	/** The furniture of the rooms is drawn within this distance of the camera. */
	private static final double DECOR_DISTANCE = 48.0;
	/** The rooms (walls, furniture, fittings) are drawn within this distance; beyond, only the hull. */
	private static final double INTERIOR_DISTANCE = 48.0;
	/** Small exterior details (rivets, rails, windows) are drawn within this distance. */
	private static final double DETAIL_DISTANCE = 80.0;
	private static final String[] INTERIOR_BONES = {"rooms", "furniture", "fittings"};
	/** Animation of door k of a vessel with rooms: {@code door_<k>}, played from 0 (closed) to 1 (open). */
	private static final String[] DOOR_ANIMATIONS = new String[fr.medievalships.core.InteriorGrid.MAX_DOORS];

	static {
		for (int k = 0; k < DOOR_ANIMATIONS.length; k++) {
			DOOR_ANIMATIONS[k] = "door_" + k;
		}
	}
	/**
	 * The murky sea seen through the glass from the rooms of a submerged vessel: veils of sea water,
	 * one behind the other, outside the hull (only drawn while the camera is in its dry rooms under
	 * the water). Each veil: x0, x1, y0, y1, z0, z1 (ship-local), the planes along x on both sides and
	 * across z ahead of the wheelhouse.
	 */
	private static final int MURK_LAYERS = 6;
	private static final float MURK_STEP = 2.5f;
	private static final int MURK_COLOR = 0x1C3CC8; // the clear blue of the sea seen by a swimmer
	private static final int MURK_ALPHA = 26;
	/** The plain white texel of the Nautilus texture (region "murk" of tools/nautilus_texture.py). */
	private static final float MURK_U = 420f / 512f, MURK_V = 100f / 512f;
	/** A painting is drawn this far in front of the centre of its frame's canvas. */
	private static final float PAINTING_OFFSET = 0.062f;
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
		state.interiorLight = entity.geometry().interior() != null;
		if (state.interiorLight) {
			for (int k = 0; k < state.doors.length; k++) {
				state.doors[k] = MathHelper.lerp(tickProgress, entity.lastDoorVisual[k], entity.doorVisual[k]);
			}
			state.shutters = MathHelper.lerp(tickProgress, entity.lastShutterVisual, entity.shutterVisual);
			state.airlockWater = MathHelper.lerp(tickProgress, entity.lastAirlockVisual, entity.airlockVisual);
			state.floodlight = entity.toggle(Ships.NautilusLayout.FLOODLIGHT_ON);
			state.lightsOff = entity.toggle(Ships.NautilusLayout.LIGHTS_OFF);
			state.lifeboatAway = entity.toggle(Ships.NautilusLayout.LIFEBOAT_AWAY);
			net.minecraft.client.render.Camera camera = net.minecraft.client.MinecraftClient.getInstance().gameRenderer.getCamera();
			state.murk = camera != null && entity.squaredDistanceTo(camera.getCameraPos()) < 80 * 80 && ShipFog.inDryRoomUnderWater(camera);
		}
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
			float[] doors = state.interiorLight ? state.doors : null;
			EmbeddedDecor decor = state.interiorLight ? EmbeddedDecor.of(visual.type()) : null;
			boolean decorDrawn = decor != null && state.squaredDistanceToCamera < DECOR_DISTANCE * DECOR_DISTANCE;
			boolean farInterior = state.interiorLight && state.squaredDistanceToCamera > INTERIOR_DISTANCE * INTERIOR_DISTANCE;
			boolean farDetail = state.squaredDistanceToCamera > DETAIL_DISTANCE * DETAIL_DISTANCE;
			int light = state.light;
			// the rooms of a vessel are lit by its own lamps, even deep under the sea (unless they are switched off)
			boolean lampsOn = state.interiorLight && !state.lightsOff;
			int lit = lampsOn
					? LightmapTextureManager.pack(Math.max(INTERIOR_BLOCK_LIGHT, LightmapTextureManager.getBlockLightCoordinates(light)),
							LightmapTextureManager.getSkyLightCoordinates(light))
					: light;
			int glowLight = state.interiorLight && state.lightsOff ? light : LightmapTextureManager.MAX_LIGHT_COORDINATE;
			float shutters = state.shutters, airlockWater = state.airlockWater;
			boolean floodlight = state.floodlight, lifeboatAway = state.lifeboatAway;
			boolean effects = state.interiorLight && model.hasEffects();
			// pass 0: the model; pass 1: its translucent effects (projector beam, water of the airlock)
			for (int pass = 0; pass < (effects ? 2 : 1); pass++) {
			boolean fx = pass == 1;
			for (int tex = 0; tex < model.textureCount() && tex < visual.textures().size(); tex++) {
				int texture = tex;
				RenderLayer layer = fx ? RenderLayers.entityTranslucent(visual.textures().get(tex))
						: RenderLayers.entityCutoutNoCull(visual.textures().get(tex));
				queue.submitCustom(matrices, layer, (entry, vertices) -> {
					BbModel.Pose pose = model.newPose();
					pose.fxPass = fx;
					model.apply(pose, "row", oarTime, oarWeight);
					model.apply(pose, "paddle", wheel, 1f);
					model.apply(pose, "sail_wind", age, sail);
					model.apply(pose, "sail_furl", 1f - sail, 1f);
					model.apply(pose, "steer", helm + 1f, 1f);
					model.apply(pose, "flag_wave", age, 1f);
					model.apply(pose, "streamer_wave", age, 1f);
					model.apply(pose, "lantern_sway", age, 1f);
					model.apply(pose, "propeller", wheel, 1f);
					model.apply(pose, "engine", wheel, 1f);
					model.apply(pose, "elevator", climb + 1f, 1f);
					if (doors != null) {
						for (int k = 0; k < doors.length; k++) {
							model.apply(pose, DOOR_ANIMATIONS[k], doors[k], 1f);
						}
					}
					if (decorDrawn) {
						for (String bone : decor.hidden) {
							model.hide(pose, bone);
						}
					}
					if (farInterior) {
						for (String bone : INTERIOR_BONES) {
							model.hide(pose, bone);
						}
						if (decor != null) {
							for (fr.medievalships.core.InteriorDecor.Block blk : decor.blocks) {
								model.hide(pose, blk.fallback());
							}
						}
					}
					if (farDetail) {
						model.hide(pose, "detail");
					}
					if (doors != null) {
						model.apply(pose, "shutters", shutters, 1f);
						model.apply(pose, "airlock_water", airlockWater, 1f);
						model.hide(pose, floodlight ? "lens_off" : "fx_beam");
						if (!floodlight) {
							model.hide(pose, "fx_lens");
						}
						if (airlockWater < 0.01f) {
							model.hide(pose, "fx_airlock");
						}
						if (lifeboatAway) {
							model.hide(pose, "lifeboat");
						}
					}
					model.render(pose, visual.textures().size() > 1 ? texture : -1, new BbModel.QuadSink() {
						@Override
						public void quad(float[] p, float[] uv, float[] n, boolean glow) {
							quad(p, uv, n, glow, false);
						}

						@Override
						public void quad(float[] p, float[] uv, float[] n, boolean glow, boolean litFace) {
							int l = glow ? (fx ? LightmapTextureManager.MAX_LIGHT_COORDINATE : glowLight) : litFace ? lit : light;
							for (int k = 0; k < 4; k++) {
								vertices.vertex(entry, p[k * 3], p[k * 3 + 1], p[k * 3 + 2])
										.color(0xFFFFFFFF)
										.texture(uv[k * 2], uv[k * 2 + 1])
										.overlay(OverlayTexture.DEFAULT_UV)
										.light(l)
										.normal(entry, n[0], n[1], n[2]);
							}
						}
					});
				});
			}
			}
			// the murky sea behind the glass, seen from the rooms under water
			if (state.murk && !visual.textures().isEmpty()) {
				submitMurk(matrices, queue, visual.textures().get(0), LightmapTextureManager.MAX_LIGHT_COORDINATE);
			}
			// vanilla paintings in their gilded frames
			if (decorDrawn) {
				for (fr.medievalships.core.InteriorDecor.Painting p : decor.paintings) {
					submitPainting(matrices, queue, p, lit);
				}
			}
			// furniture from the decoration mods, drawn where it stands in the rooms
			if (decorDrawn) {
				for (int i = 0; i < decor.states.length; i++) {
					if (decor.states[i] == null) {
						continue;
					}
					fr.medievalships.core.InteriorDecor.Block b = decor.blocks.get(i);
					matrices.push();
					matrices.translate(b.x(), b.y(), b.z());
					matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(b.yaw()));
					if (b.scale() != 1f) {
						matrices.scale(b.scale(), b.scale(), b.scale());
					}
					matrices.translate(-0.5, 0, -0.5);
					queue.submitBlock(matrices, decor.states[i], lit, OverlayTexture.DEFAULT_UV, 0);
					matrices.pop();
				}
			}
			matrices.pop();
		}
		super.render(state, matrices, queue, cameraState);
	}

	/** Veils of murky sea water outside the hull, along both sides and ahead of the wheelhouse. */
	private static void submitMurk(MatrixStack matrices, OrderedRenderCommandQueue queue, Identifier texture, int light) {
		RenderLayer layer = RenderLayers.entityTranslucent(texture);
		int color = (MURK_ALPHA << 24) | MURK_COLOR;
		float casing = (float) Ships.NautilusLayout.CASING_TOP_Y;
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			for (int k = 0; k < MURK_LAYERS; k++) {
				float d = k * MURK_STEP;
				for (int side = -1; side <= 1; side += 2) {
					float x = side * (7.4f + d);
					murkQuad(entry, vertices, color, light, new float[] {x, -8, -48}, new float[] {x, -8, 48}, new float[] {x, 16, 48},
							new float[] {x, 16, -48}, side);
				}
				float z = 23.2f + d;
				murkQuad(entry, vertices, color, light, new float[] {-8, casing + 0.1f, z}, new float[] {8, casing + 0.1f, z},
						new float[] {8, casing + 8, z}, new float[] {-8, casing + 8, z}, 0);
			}
		});
	}

	private static void murkQuad(MatrixStack.Entry entry, net.minecraft.client.render.VertexConsumer vertices, int color, int light,
			float[] a, float[] b, float[] c, float[] d, int side) {
		for (float[] p : new float[][] {a, b, c, d, d, c, b, a}) { // both windings: seen from either side
			vertices.vertex(entry, p[0], p[1], p[2])
					.color(color)
					.texture(MURK_U, MURK_V)
					.overlay(OverlayTexture.DEFAULT_UV)
					.light(light)
					.normal(entry, side == 0 ? 0f : -side, 0f, side == 0 ? -1f : 0f);
		}
	}

	/** A vanilla painting: its texture on the canvas, just in front of the canvas of its frame. */
	private static void submitPainting(MatrixStack matrices, OrderedRenderCommandQueue queue, fr.medievalships.core.InteriorDecor.Painting p,
			int light) {
		float nx = (float) p.nx(), nz = (float) p.nz();
		float rx = nz, rz = -nx; // to the right of someone facing the wall
		float hw = (float) p.w() / 2f, hh = (float) p.h() / 2f;
		float cx = (float) p.x() + nx * PAINTING_OFFSET, cy = (float) p.y(), cz = (float) p.z() + nz * PAINTING_OFFSET;
		float[] xs = {cx - rx * hw, cx + rx * hw, cx + rx * hw, cx - rx * hw};
		float[] ys = {cy - hh, cy - hh, cy + hh, cy + hh};
		float[] zs = {cz - rz * hw, cz + rz * hw, cz + rz * hw, cz - rz * hw};
		float[] us = {0f, 1f, 1f, 0f};
		float[] vs = {1f, 1f, 0f, 0f};
		RenderLayer layer = RenderLayers.entityCutoutNoCull(Identifier.ofVanilla("textures/painting/" + p.motive() + ".png"));
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			for (int k = 0; k < 4; k++) {
				vertices.vertex(entry, xs[k], ys[k], zs[k])
						.color(0xFFFFFFFF)
						.texture(us[k], vs[k])
						.overlay(OverlayTexture.DEFAULT_UV)
						.light(light)
						.normal(entry, nx, 0f, nz);
			}
		});
	}
}
