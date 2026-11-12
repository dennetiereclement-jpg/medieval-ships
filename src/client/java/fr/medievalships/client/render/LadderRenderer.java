package fr.medievalships.client.render;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.SideLadder;

/**
 * Draws a vessel's side ladders ({@link SideLadder}, 1.30.0) in the ship's model space (inside {@link ShipRenderer}'s
 * transform): their quads are baked once per ship type ({@link SideLadder#mesh}, the gangplank atlas) and written as one
 * static run by a {@link MeshEmitter}, like the baked mesh of the models. Render thread only.
 */
final class LadderRenderer {
	private static final Map<String, float[]> MESHES = new HashMap<>();
	private static final MeshEmitter EMITTER = new MeshEmitter();

	private LadderRenderer() {
	}

	static void render(ShipType type, MatrixStack matrices, OrderedRenderCommandQueue queue, int light) {
		float[] mesh = MESHES.computeIfAbsent(type.id(), id -> {
			List<SideLadder.Ladder> ladders = SideLadder.of(id);
			return ladders.isEmpty() ? new float[0] : SideLadder.mesh(ladders, type.geometry().hull().waterlineY);
		});
		if (mesh.length == 0) {
			return;
		}
		int quads = mesh.length / SideLadder.QUAD_FLOATS;
		RenderLayer layer = RenderLayers.entityCutoutNoCull(ShipModels.GANGPLANK_TEXTURE);
		queue.submitCustom(matrices, layer, (entry, vertices) -> {
			MeshEmitter sink = EMITTER.begin(entry, vertices, light, light, light, false, false, true);
			sink.mesh(mesh, 0, quads, BbModel.LIGHT_WORLD, false);
		});
	}
}
