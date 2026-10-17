package fr.medievalships.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;

import net.minecraft.resource.ResourceType;
import net.minecraft.resource.SynchronousResourceReloader;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.render.GalleyModels;
import fr.medievalships.client.render.GalleyRenderer;
import fr.medievalships.entity.ShipTracker;

public final class MedievalShipsClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		EntityRendererRegistry.register(MedievalShips.GALLEY, GalleyRenderer::new);
		ResourceLoader.get(ResourceType.CLIENT_RESOURCES).registerReloader(MedievalShips.id("galley_model"),
				(SynchronousResourceReloader) GalleyModels::reload);
		ClientTickEvents.END_WORLD_TICK.register(ClientShipEvents::endWorldTick);
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> ShipTracker.clearClientWorlds());
	}
}
