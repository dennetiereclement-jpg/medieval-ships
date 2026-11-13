package fr.medievalships.client.render;

import org.jetbrains.annotations.Nullable;

import net.minecraft.client.render.LightmapTextureManager;
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
import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorMotion;
import fr.medievalships.core.DoorType;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.door.DoorBlockEntity;

/**
 * Draws a door (1.31.0) from its controller block: the model turned to the block's facing, its origin at the middle
 * of the bottom of the opening. Closed and still, the whole model is the baked static mesh in one go; otherwise the
 * fixed parts (the {@code frame}...) still come baked, and each moving part is drawn baked too, under its own matrix:
 * the leaves turned about their hinge, the gears turning about their axis (only while the door moves), the bolts and
 * the piston rods slid. The progress is computed here between two ticks from the state the server sent (target,
 * start tick, start progress): no packet per tick. Glowing cubes are full bright, the {@code detail} bones are
 * hidden beyond {@code doorDetailDistance}, nothing is drawn beyond {@code doorRenderDistance} or out of the view.
 * Drawn outside its block (a door is up to 4 x 6): never cut when the controller's section leaves the view.
 */
public class DoorRenderer implements BlockEntityRenderer<DoorBlockEntity, DoorRenderer.State> {
	public static class State extends BlockEntityRenderState {
		@Nullable
		DoorType door;
		int quarter;
		double progress;
		boolean moving;
		boolean backward;
		double squaredDistance;
	}

	/** Writes the model's quads to the vertex consumer (reused by every command of this renderer, render thread). */
	private final MeshEmitter emitter = new MeshEmitter();

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void updateRenderState(DoorBlockEntity be, State state, float tickProgress, Vec3d cameraPos,
			@Nullable ModelCommandRenderer.CrumblingOverlayCommand crumblingOverlay) {
		BlockEntityRenderState.updateBlockEntityRenderState(be, state, crumblingOverlay);
		state.door = be.doorType();
		state.quarter = be.quarter();
		state.backward = be.backward();
		double now = be.getWorld() == null ? 0 : be.getWorld().getTime() + tickProgress;
		state.progress = be.progressAt(now);
		state.moving = DoorMotion.moving(be.target(), state.progress);
		double[] o = be.origin();
		double h = state.door == null ? 1 : state.door.height() / 2.0;
		state.squaredDistance = cameraPos.squaredDistanceTo(o[0], o[1] + h, o[2]);
	}

	@Override
	public boolean rendersOutsideBoundingBox() {
		return true;
	}

	@Override
	public int getRenderDistance() {
		return (int) Math.ceil(ConfigManager.server().doorRenderDistance) + 4;
	}

	@Override
	public void render(State state, MatrixStack matrices, OrderedRenderCommandQueue queue, CameraRenderState cameraState) {
		DoorType type = state.door;
		if (type == null || RenderStats.skip) {
			return;
		}
		double far = ConfigManager.server().doorRenderDistance;
		if (state.squaredDistance > far * far) {
			return;
		}
		DoorModels.Loaded loaded = DoorModels.get(type);
		if (loaded == null) {
			return;
		}
		BbModel model = loaded.model;
		double near = ConfigManager.server().doorDetailDistance;
		boolean detailed = state.squaredDistance < near * near;
		int light = state.lightmapCoordinates;
		int glow = LightmapTextureManager.MAX_LIGHT_COORDINATE;
		matrices.push();
		matrices.translate(0.5, 0, 0.5);
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-90f * state.quarter));
		matrices.translate((type.width() - 1) / 2.0, 0, 0);
		// out of the view (vanilla never culls a block entity drawn outside its block): nothing is submitted
		float hw = type.width() / 2f, reach = 0.5f + type.leafWidth(); // the leaves swing at most their share of the opening
		RenderStats.cells++;
		if (!RenderCulling.visible(matrices.peek().getPositionMatrix(), -hw, 0, -reach, hw, type.height(), reach)) {
			RenderStats.cellsCulled++;
			matrices.pop();
			return;
		}
		RenderLayer layer = RenderLayers.entityCutoutNoCull(loaded.texture);
		double p = state.progress;
		if (!state.moving && p <= 0) {
			// closed and still: the rest pose, the whole baked mesh in one go
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose pose = model.scratchPose();
				if (!detailed) {
					model.hideAll(pose, "detail");
				}
				model.render(pose, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
			});
			matrices.pop();
			return;
		}
		boolean gears = state.moving;
		int n = loaded.parts.size();
		boolean[] active = new boolean[n];
		for (int i = 0; i < n; i++) {
			DoorModels.Kind k = loaded.parts.get(i).kind;
			active[i] = gears || (k != DoorModels.Kind.GEAR_A && k != DoorModels.Kind.GEAR_B);
		}
		// the fixed parts: everything but the moving parts that hang from no other moving part
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			BbModel.Pose pose = model.scratchPose();
			for (int i = 0; i < n; i++) {
				DoorModels.Part part = loaded.parts.get(i);
				if (active[i] && topmost(part, active)) {
					model.hide(pose, part.bone);
				}
			}
			if (!detailed) {
				model.hideAll(pose, "detail");
			}
			model.render(pose, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
		});
		double eased = DoorMotion.ease(p);
		for (int i = 0; i < n; i++) {
			if (!active[i]) {
				continue;
			}
			DoorModels.Part part = loaded.parts.get(i);
			matrices.push();
			for (int a : part.ancestors) {
				if (active[a]) {
					transform(matrices, loaded.parts.get(a), type, state.backward, p, eased);
				}
			}
			transform(matrices, part, type, state.backward, p, eased);
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose pose = model.scratchPose();
				for (int d : part.descendants) {
					if (active[d]) {
						model.hide(pose, loaded.parts.get(d).bone);
					}
				}
				if (!detailed) {
					model.hideAll(pose, "detail");
				}
				model.renderPart(pose, part.bone, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
			});
			matrices.pop();
		}
		matrices.pop();
	}

	/** Does this moving part hang from no other moving part drawn on its own? */
	private static boolean topmost(DoorModels.Part part, boolean[] active) {
		for (int a : part.ancestors) {
			if (active[a]) {
				return false;
			}
		}
		return true;
	}

	/** The motion of one moving part at a progress, about its pivot, in model-local blocks. */
	private static void transform(MatrixStack m, DoorModels.Part part, DoorType type, boolean backward, double p, double eased) {
		switch (part.kind) {
			case LEAF_L, LEAF_R -> {
				float angle = DoorLayout.leafAngle(part.kind == DoorModels.Kind.LEAF_L, backward, eased);
				m.translate(part.px, part.py, part.pz);
				m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(angle));
				m.translate(-part.px, -part.py, -part.pz);
			}
			case GEAR_A, GEAR_B -> {
				// seen from the front (+z), a positive turn about +z is anticlockwise: gear_a turns the other way
				float angle = (float) DoorMotion.gearAngle(p, type.gearTurns()) * (part.kind == DoorModels.Kind.GEAR_A ? -1f : 1f);
				m.translate(part.px, part.py, part.pz);
				m.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(angle));
				m.translate(-part.px, -part.py, -part.pz);
			}
			case BOLT -> m.translate(part.boltSign * DoorMotion.boltOffset(p), 0, 0);
			case PISTON -> m.translate(0, DoorMotion.pistonOffset(eased), 0);
		}
	}
}
