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
		ClientTickEvents.END_WORLD_TICK.register(ClientShipEvents::endWorldTick);
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
			ShipTracker.clearClientWorlds();
			SyncedConfig.clear();
		});
		// the server's settings that change what this client shows (preview, bank, pilot's panel)
		ClientPlayNetworking.registerGlobalReceiver(ServerConfigPayload.ID, (payload, context) -> SyncedConfig.receive(payload));
		// the ghost of the vessel whose item the player holds, and the pilot's panel
		WorldRenderEvents.BEFORE_ENTITIES.register(PlacementPreview::render);
		HudElementRegistry.attachElementBefore(VanillaHudElements.CHAT, MedievalShips.id("pilot_panel"), PilotHudOverlay::render);
	}
}
