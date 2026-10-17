package fr.medievalships;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerWorldEvents;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemGroups;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.command.ShipCommands;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.ShipTracker;
import fr.medievalships.item.GalleyItem;
import fr.medievalships.mixin.ServerPlayNetworkHandlerAccessor;
import fr.medievalships.network.ShipInteractPayload;
import fr.medievalships.network.ShipInteractions;

public final class MedievalShips implements ModInitializer {
	public static final String MOD_ID = "medievalships";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public static EntityType<GalleyEntity> GALLEY;
	public static Item GALLEY_ITEM;

	/** Players who logged out aboard a ship: put back on deck shortly after they join. */
	private static final List<PendingRejoin> REJOINS = new ArrayList<>();

	private record PendingRejoin(UUID player, UUID ship, int[] delay) {
	}

	public static Identifier id(String path) {
		return Identifier.of(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		ConfigManager.load();

		RegistryKey<EntityType<?>> entityKey = RegistryKey.of(RegistryKeys.ENTITY_TYPE, id("galley"));
		GALLEY = Registry.register(Registries.ENTITY_TYPE, entityKey,
				EntityType.Builder.<GalleyEntity>create(GalleyEntity::new, SpawnGroup.MISC)
						.dimensions(3.0f, 0.4f)
						.maxTrackingRange(12)
						.trackingTickInterval(1)
						.makeFireImmune()
						.build(entityKey));

		RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, id("galley"));
		GALLEY_ITEM = Registry.register(Registries.ITEM, itemKey, new GalleyItem(new Item.Settings().registryKey(itemKey).maxCount(1)));

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, id("ships"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(GALLEY_ITEM))
				.displayName(Text.translatable("itemGroup.medievalships.ships"))
				.entries((context, entries) -> entries.add(GALLEY_ITEM))
				.build());
		ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS).register(entries -> entries.add(GALLEY_ITEM));

		PayloadTypeRegistry.playC2S().register(ShipInteractPayload.ID, ShipInteractPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(ShipInteractPayload.ID,
				(payload, context) -> ShipInteractions.handle(payload, context.player()));

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> ShipCommands.register(dispatcher));

		ServerLifecycleEvents.SERVER_STARTED.register(MedievalShips::reloadFerries);
		ServerTickEvents.END_SERVER_TICK.register(MedievalShips::processRejoins);
		ServerTickEvents.END_SERVER_TICK.register(MedievalShips::serverTick);
		ServerWorldEvents.UNLOAD.register((server, world) -> ShipTracker.clear(world));

		// a player logging out while seated would otherwise take the whole ship (and the other
		// passengers) into his player file: vanilla saves the mount with the player
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			ServerPlayerEntity player = handler.player;
			GalleyEntity ship = null;
			if (player.getVehicle() instanceof GalleyEntity riding) {
				ship = riding;
				Vec3d spot = riding.updatePassengerForDismount(player);
				player.stopRiding();
				player.refreshPositionAndAngles(spot.x, spot.y, spot.z, player.getYaw(), player.getPitch());
			} else {
				ship = ShipTracker.shipUnder(player);
			}
			ShipData.get(server).setPlayerShip(player.getUuid(), ship == null ? null : ship.getUuid());
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			UUID shipId = ShipData.get(server).playerShip(handler.player.getUuid());
			if (shipId != null) {
				REJOINS.add(new PendingRejoin(handler.player.getUuid(), shipId, new int[] {20}));
			}
		});
		LOGGER.info("Medieval ships loaded");
	}

	private static void serverTick(MinecraftServer server) {
		// players walking on a ship are not flying, whatever the blocks under the raised decks say
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			if (!player.hasVehicle() && ShipTracker.shipUnder(player) != null) {
				((ServerPlayNetworkHandlerAccessor) player.networkHandler).medievalships$setFloatingTicks(0);
			}
		}
		// keep the chunks of autopilot ships that are not loaded yet (after a restart) loaded until
		// the entity appears and takes over its own tickets
		if (server.getTicks() % 200 == 0) {
			reloadFerries(server);
		}
	}

	/** After a restart, load the chunks of autopilot ships so ferries resume their routes. */
	private static void reloadFerries(MinecraftServer server) {
		ShipData data = ShipData.get(server);
		int n = 0;
		for (Map.Entry<String, ShipData.FerryRecord> e : data.ferries().entrySet()) {
			ShipData.FerryRecord rec = e.getValue();
			ServerWorld world = server.getWorld(RegistryKey.of(RegistryKeys.WORLD, Identifier.of(rec.dimension)));
			if (world == null || world.getEntity(UUID.fromString(e.getKey())) != null) {
				continue;
			}
			ChunkPos chunk = new ChunkPos(BlockPos.ofFloored(rec.x, 64, rec.z));
			world.getChunkManager().addTicket(ChunkTicketType.PORTAL, chunk, ConfigManager.get().chunkLoadRadius);
			n++;
		}
		if (n > 0) {
			LOGGER.info("Loading the chunks of {} autopilot ship(s)", n);
		}
	}

	private static void processRejoins(MinecraftServer server) {
		if (REJOINS.isEmpty()) {
			return;
		}
		Iterator<PendingRejoin> it = REJOINS.iterator();
		while (it.hasNext()) {
			PendingRejoin r = it.next();
			if (--r.delay()[0] > 0) {
				continue;
			}
			it.remove();
			ServerPlayerEntity player = server.getPlayerManager().getPlayer(r.player());
			if (player == null) {
				continue;
			}
			ShipData.get(server).setPlayerShip(r.player(), null);
			for (ServerWorld world : server.getWorlds()) {
				Entity e = world.getEntity(r.ship());
				if (e instanceof GalleyEntity ship && world == player.getEntityWorld()) {
					if (ShipTracker.shipUnder(player) == ship) {
						break; // still on deck
					}
					// the ship sailed on while the player was away: put him back aboard
					Vec3d spot = ship.boardingPosition(ship.getX(), ship.getZ() + 0.01);
					player.requestTeleport(spot.x, spot.y, spot.z);
					break;
				}
			}
		}
	}
}
