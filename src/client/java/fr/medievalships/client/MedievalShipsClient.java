package fr.medievalships.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;

import net.minecraft.resource.ResourceType;
import net.minecraft.resource.SynchronousResourceReloader;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.render.ShipModels;
import fr.medievalships.client.render.ShipRenderer;
import fr.medievalships.data.SyncedConfig;
import fr.medievalships.entity.ShipTracker;
import fr.medievalships.network.ServerConfigPayload;

public final class MedievalShipsClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		for (ShipModels.Visual visual : ShipModels.ALL) {
			EntityRendererRegistry.register(MedievalShips.entityType(visual.type()), ctx -> new ShipRenderer(ctx, visual));
		}
		ResourceLoader.get(ResourceType.CLIENT_RESOURCES).registerReloader(MedievalShips.id("galley_model"),
				(SynchronousResourceReloader) ShipModels::reload);
		// the tents: drawn from their anchor block, their collision boxes known while their chunks are loaded
		net.minecraft.client.render.block.entity.BlockEntityRendererFactories.register(fr.medievalships.tent.Tents.BLOCK_ENTITY,
				ctx -> new fr.medievalships.client.render.TentBlockEntityRenderer());
		// the cannon has its own block entity type (its persisted state) but is drawn exactly like the tents
		net.minecraft.client.render.block.entity.BlockEntityRendererFactories
				.<fr.medievalships.tent.TentBlockEntity, fr.medievalships.client.render.TentBlockEntityRenderer.State>register(
						fr.medievalships.tent.Tents.CANNON_BLOCK_ENTITY, ctx -> new fr.medievalships.client.render.TentBlockEntityRenderer());
		ResourceLoader.get(ResourceType.CLIENT_RESOURCES).registerReloader(MedievalShips.id("tent_models"),
				(SynchronousResourceReloader) fr.medievalships.client.render.TentModels::reload);
		net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, world) -> {
			if (be instanceof fr.medievalships.tent.TentBlockEntity tent && tent.tentType() != null) {
				fr.medievalships.tent.TentCollisions.add(world, be.getPos(), tent.tentType(), tent.quarter());
			}
		});
		net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientBlockEntityEvents.BLOCK_ENTITY_UNLOAD.register((be, world) -> {
			if (be instanceof fr.medievalships.tent.TentBlockEntity) {
				fr.medievalships.tent.TentCollisions.remove(world, be.getPos());
			}
		});
		// the invisible seat a player sits on (1.19.0): nothing to draw
		EntityRendererRegistry.register(fr.medievalships.tent.Seats.SEAT, net.minecraft.client.render.entity.EmptyEntityRenderer::new);
		// the training targets (1.19.0): drawn by their entity from the area's model, their reaction read from it
		EntityRendererRegistry.register(fr.medievalships.training.TrainingTargets.TYPE, fr.medievalships.client.render.TrainingTargetRenderer::new);
		fr.medievalships.training.TrainingTargetEntity.joints = fr.medievalships.client.render.TrainingTargetRenderer::joints;
		net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents.ENTITY_LOAD
				.register((entity, world) -> fr.medievalships.client.render.TrainingTargetRenderer.loaded(entity));
		net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents.ENTITY_UNLOAD
				.register((entity, world) -> fr.medievalships.client.render.TrainingTargetRenderer.unloaded(entity));
		ClientTickEvents.END_WORLD_TICK.register(ClientShipEvents::endWorldTick);
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
			ShipTracker.clearClientWorlds();
			fr.medievalships.tent.TentCollisions.clearClientWorlds();
			fr.medievalships.client.bridge.DrawbridgeClient.clear();
			fr.medievalships.bridge.DrawbridgeCollisions.clearClientWorlds();
			fr.medievalships.client.render.TrainingTargetRenderer.clear();
			SyncedConfig.clear();
		});
		// the server's settings that change what this client shows (preview, bank, pilot's panel)
		ClientPlayNetworking.registerGlobalReceiver(ServerConfigPayload.ID, (payload, context) -> SyncedConfig.receive(payload));
		// the ghost of the vessel whose item the player holds, and the pilot's panel
		WorldRenderEvents.BEFORE_ENTITIES.register(PlacementPreview::render);
		// the drawbridges (1.24.0): what the server sends, drawn and solid on this client
		ClientPlayNetworking.registerGlobalReceiver(fr.medievalships.network.DrawbridgeSyncPayload.ID,
				(payload, context) -> fr.medievalships.client.bridge.DrawbridgeClient.receive(payload, context.client().world));
		WorldRenderEvents.AFTER_ENTITIES.register(fr.medievalships.client.bridge.DrawbridgeRenderer::render);
		HudElementRegistry.attachElementBefore(VanillaHudElements.CHAT, MedievalShips.id("pilot_panel"), PilotHudOverlay::render);
	}
}
