package fr.medievalships.client.render;

import java.util.ArrayList;
import java.util.List;

import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;

import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.render.block.entity.state.BlockEntityRenderState;
import net.minecraft.client.render.command.ModelCommandRenderer;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.ForgeAnimation;
import fr.medievalships.core.TentType;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.forge.DivineForgeBlockEntity;

/**
 * Draws the divine forge (1.34.0) from its anchor block: its two models (the structure, then the statue and decor of
 * {@link TentType#extraModels()}), turned to the block's facing like every prop. Everything that does not move comes from
 * the baked static mesh, in one go per model; on top of it, each gear is drawn baked too under its own matrix, turned
 * about its own z axis through its pivot ({@link ForgeRig}: {@code gear_a_*} clockwise seen from the front,
 * {@code gear_b_*} the other way), slowly at rest and faster while the forge is active. The flipbooks (the fire, the heat
 * columns) show one image at a time, the {@code craft_*} bones only while active, the {@code idle_*} bones only at rest;
 * the pace is the forge's eased {@link ForgeAnimation.Track} (nothing jumps when an activity starts or ends), integrated here
 * every frame from the game time. Glowing cubes are full bright, the {@code detail} bones hidden beyond
 * {@code tentDecorDistance}, nothing drawn beyond {@code tentRenderDistance} or out of the view; drawn outside its block
 * (13 x 10 x 6), never cut when the anchor's section leaves the view. A missing model is simply not drawn.
 */
public class DivineForgeRenderer implements BlockEntityRenderer<DivineForgeBlockEntity, DivineForgeRenderer.State> {
	public static class State extends BlockEntityRenderState {
		@Nullable
		TentType type;
		int quarter;
		double squaredDistance;
		boolean active;
		float gear;
		/** The track's flipbook phases (images elapsed): the fire (and the flipbooks of other names), the two columns. */
		double fire, flowLeft, flowRight;
	}

	/** One model of the forge with its atlas. */
	private record Part(BbModel model, Identifier texture) {
	}

	private final MeshEmitter emitter = new MeshEmitter();
	private final List<Part> parts = new ArrayList<>(2);

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void updateRenderState(DivineForgeBlockEntity be, State state, float tickProgress, Vec3d cameraPos,
			@Nullable ModelCommandRenderer.CrumblingOverlayCommand crumblingOverlay) {
		BlockEntityRenderState.updateBlockEntityRenderState(be, state, crumblingOverlay);
		state.type = be.tentType();
		state.quarter = be.quarter();
		state.squaredDistance = cameraPos.squaredDistanceTo(be.getPos().getX() + 0.5, be.getPos().getY() + 3.0, be.getPos().getZ() + 0.5);
		state.active = be.active();
		// the doors' smoothed clock (1.33.0): the server's time packets never make the gears or the fire jump
		double now = DoorClientClock.now(be.getWorld(), tickProgress);
		ForgeAnimation.Track t = be.track;
		t.update(now, state.active);
		state.gear = (float) t.gear;
		state.fire = t.fire;
		state.flowLeft = t.flowLeft;
		state.flowRight = t.flowRight;
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
		TentType type = state.type;
		if (type == null || RenderStats.skip) {
			return;
		}
		double far = ConfigManager.server().tentRenderDistance;
		if (state.squaredDistance > far * far) {
			return;
		}
		parts.clear();
		BbModel main = TentModels.get(type);
		if (main != null) {
			parts.add(new Part(main, TentModels.texture(type)));
		}
		for (TentModels.Extra e : TentModels.extras(type)) {
			parts.add(new Part(e.model(), e.texture()));
		}
		if (parts.isEmpty()) {
			return;
		}
		double near = ConfigManager.server().tentDecorDistance;
		boolean detailed = state.squaredDistance < near * near;
		matrices.push();
		matrices.translate(0.5, 0, 0.5);
		TentType.Box extent = type.extent(state.quarter);
		RenderStats.cells++;
		if (!RenderCulling.visible(matrices.peek().getPositionMatrix(), (float) extent.x0(), (float) extent.y0(), (float) extent.z0(),
				(float) extent.x1(), (float) extent.y1(), (float) extent.z1())) {
			RenderStats.cellsCulled++;
			matrices.pop();
			return;
		}
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-90f * state.quarter));
		for (Part p : parts) {
			draw(p.model(), p.texture(), state, matrices, queue, detailed);
		}
		matrices.pop();
	}

	/** The image of each of the rig's flipbooks for this frame (the fire, the left and right columns, others with the fire). */
	private static int[] frames(ForgeRig rig, State s) {
		int[] f = new int[rig.flipbooks.size()];
		for (int i = 0; i < f.length; i++) {
			ForgeRig.Flipbook b = rig.flipbooks.get(i);
			double phase = switch (b.name) {
				case "flow_l" -> s.flowLeft;
				case "flow_r" -> s.flowRight;
				default -> s.fire;
			};
			f[i] = ForgeAnimation.frame(phase, b.size());
		}
		return f;
	}

	private void draw(BbModel model, Identifier texture, State state, MatrixStack matrices, OrderedRenderCommandQueue queue, boolean detailed) {
		ForgeRig rig = ForgeRig.of(model);
		RenderLayer layer = RenderLayers.entityCutoutNoCull(texture);
		int light = state.lightmapCoordinates;
		int glow = LightmapTextureManager.MAX_LIGHT_COORDINATE;
		boolean active = state.active;
		int[] frame = frames(rig, state);
		List<ForgeRig.Gear> gears = rig.gears;
		// everything but the gears: the baked mesh, the images and states not shown hidden
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			long t0 = System.nanoTime();
			BbModel.Pose pose = model.scratchPose();
			rig.hideState(model, pose, active, frame, detailed);
			for (ForgeRig.Gear g : gears) {
				model.hide(pose, g.bone);
			}
			model.render(pose, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
			RenderStats.emitNanos += System.nanoTime() - t0;
		});
		// each gear under its own matrix (with the gears it hangs from), baked too
		for (int i = 0; i < gears.size(); i++) {
			ForgeRig.Gear g = gears.get(i);
			matrices.push();
			for (int a : g.ancestors) {
				turn(matrices, gears.get(a), state.gear);
			}
			turn(matrices, g, state.gear);
			queue.submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose pose = model.scratchPose();
				rig.hideState(model, pose, active, frame, detailed);
				for (int d : g.descendants) {
					model.hide(pose, gears.get(d).bone);
				}
				model.renderPart(pose, g.bone, emitter.begin(entry, vertices, light, light, glow, false, RenderCulling.active(), true));
			});
			matrices.pop();
		}
	}

	/** A gear's turn about its own z axis through its pivot (model-local blocks). */
	private static void turn(MatrixStack m, ForgeRig.Gear g, float trackAngle) {
		float angle = (float) ForgeAnimation.gearAngle(trackAngle, g.clockwise);
		m.translate(g.px, g.py, g.pz);
		m.multiply(RotationAxis.of(new Vector3f(g.ax, g.ay, g.az)).rotationDegrees(angle));
		m.translate(-g.px, -g.py, -g.pz);
	}
}
