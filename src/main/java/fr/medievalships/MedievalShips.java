package fr.medievalships;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
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
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;
import fr.medievalships.item.ShipItem;
import fr.medievalships.entity.GalleonEntity;
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.MedievalGalleyEntity;
import fr.medievalships.entity.ElvenSailboatEntity;
import fr.medievalships.entity.NautilusEntity;
import fr.medievalships.entity.OldCorsairEntity;
import fr.medievalships.entity.SkyLeviathanEntity;
import fr.medievalships.entity.CrystalAirshipEntity;
import fr.medievalships.entity.SteampunkAirshipEntity;
import fr.medievalships.entity.SteamPaddleboatEntity;
import fr.medievalships.entity.WarshipEntity;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.mixin.ServerPlayNetworkHandlerAccessor;
import fr.medievalships.network.ShipInteractPayload;
import fr.medievalships.network.ShipInteractions;

public final class MedievalShips implements ModInitializer {
	public static final String MOD_ID = "medievalships";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public static EntityType<GalleyEntity> GALLEY;
	public static Item GALLEY_ITEM;
	public static EntityType<GalleonEntity> GALLEON;
	public static Item GALLEON_ITEM;
	public static EntityType<WarshipEntity> WARSHIP;
	public static Item WARSHIP_ITEM;
	public static EntityType<MedievalGalleyEntity> MEDIEVAL_GALLEY;
	public static Item MEDIEVAL_GALLEY_ITEM;
	public static EntityType<SteamPaddleboatEntity> STEAM_PADDLEBOAT;
	public static Item STEAM_PADDLEBOAT_ITEM;
	public static EntityType<ElvenSailboatEntity> ELVEN_SAILBOAT;
	public static Item ELVEN_SAILBOAT_ITEM;
	public static EntityType<SteampunkAirshipEntity> STEAMPUNK_AIRSHIP;
	public static Item STEAMPUNK_AIRSHIP_ITEM;
	public static EntityType<NautilusEntity> NAUTILUS;
	public static Item NAUTILUS_ITEM;
	public static EntityType<OldCorsairEntity> OLD_CORSAIR;
	public static Item OLD_CORSAIR_ITEM;
	public static EntityType<SkyLeviathanEntity> SKY_LEVIATHAN;
	public static Item SKY_LEVIATHAN_ITEM;
	public static EntityType<CrystalAirshipEntity> CRYSTAL_AIRSHIP;
	public static Item CRYSTAL_AIRSHIP_ITEM;

	private static final Map<ShipType, EntityType<? extends ShipEntity>> ENTITY_TYPES = new LinkedHashMap<>();
	private static final Map<ShipType, Item> ITEMS = new LinkedHashMap<>();

	public static EntityType<? extends ShipEntity> entityType(ShipType type) {
		return ENTITY_TYPES.get(type);
	}

	public static Item item(ShipType type) {
		return ITEMS.get(type);
	}

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

		GALLEY = registerShip(Ships.GALLEY, GalleyEntity::new, 3.0f, 0.4f, 12);
		GALLEY_ITEM = ITEMS.get(Ships.GALLEY);
		GALLEON = registerShip(Ships.GALLEON, GalleonEntity::new, 4.0f, 0.4f, 16);
		GALLEON_ITEM = ITEMS.get(Ships.GALLEON);
		WARSHIP = registerShip(Ships.WARSHIP, WarshipEntity::new, 5.0f, 0.4f, 20);
		WARSHIP_ITEM = ITEMS.get(Ships.WARSHIP);
		MEDIEVAL_GALLEY = registerShip(Ships.MEDIEVAL_GALLEY, MedievalGalleyEntity::new, 3.0f, 0.4f, 14);
		MEDIEVAL_GALLEY_ITEM = ITEMS.get(Ships.MEDIEVAL_GALLEY);
		STEAM_PADDLEBOAT = registerShip(Ships.STEAM_PADDLEBOAT, SteamPaddleboatEntity::new, 4.0f, 0.4f, 14);
		STEAM_PADDLEBOAT_ITEM = ITEMS.get(Ships.STEAM_PADDLEBOAT);
		ELVEN_SAILBOAT = registerShip(Ships.ELVEN_SAILBOAT, ElvenSailboatEntity::new, 3.0f, 0.4f, 16);
		ELVEN_SAILBOAT_ITEM = ITEMS.get(Ships.ELVEN_SAILBOAT);
		STEAMPUNK_AIRSHIP = registerShip(Ships.STEAMPUNK_AIRSHIP, SteampunkAirshipEntity::new, 3.0f, 0.4f, 20);
		STEAMPUNK_AIRSHIP_ITEM = ITEMS.get(Ships.STEAMPUNK_AIRSHIP);
		NAUTILUS = registerShip(Ships.NAUTILUS, NautilusEntity::new, 6.0f, 0.4f, 24);
		NAUTILUS_ITEM = ITEMS.get(Ships.NAUTILUS);
		OLD_CORSAIR = registerShip(Ships.OLD_CORSAIR, OldCorsairEntity::new, 6.0f, 0.4f, 22);
		OLD_CORSAIR_ITEM = ITEMS.get(Ships.OLD_CORSAIR);
		SKY_LEVIATHAN = registerShip(Ships.SKY_LEVIATHAN, SkyLeviathanEntity::new, 6.0f, 0.4f, 24);
		SKY_LEVIATHAN_ITEM = ITEMS.get(Ships.SKY_LEVIATHAN);
		CRYSTAL_AIRSHIP = registerShip(Ships.CRYSTAL_AIRSHIP, CrystalAirshipEntity::new, 6.0f, 0.4f, 24);
		CRYSTAL_AIRSHIP_ITEM = ITEMS.get(Ships.CRYSTAL_AIRSHIP);

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, id("ships"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(GALLEY_ITEM))
				.displayName(Text.translatable("itemGroup.medievalships.ships"))
				.entries((context, entries) -> ITEMS.values().forEach(entries::add))
				.build());
		ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS).register(entries -> ITEMS.values().forEach(entries::add));

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
			ShipEntity ship = null;
			if (player.getVehicle() instanceof ShipEntity riding) {
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
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			double[] last = PLAYER_POS.getOrDefault(player.getUuid(), new double[] {player.getX(), player.getY(), player.getZ()});
			PLAYER_POS.put(player.getUuid(), new double[] {player.getX(), player.getY(), player.getZ()});
			if (player.hasVehicle() || player.isSpectator() || player.getAbilities().flying) {
				continue;
			}
			// players walking on a ship are not flying, whatever the blocks under the raised decks say
			if (ShipTracker.shipUnder(player) != null) {
				((ServerPlayNetworkHandlerAccessor) player.networkHandler).medievalships$setFloatingTicks(0);
			}
			// a real fall, not a teleport: moving down at most at terminal speed, barely sideways
			double drop = last[1] - player.getY();
			if (drop > 0.05 && drop < 4.2 && Math.hypot(player.getX() - last[0], player.getZ() - last[2]) < 1.5) {
				catchFallingPlayer(player, last[1]);
			}
		}
		if (server.getTicks() % 1200 == 0) {
			PLAYER_POS.keySet().removeIf(id -> server.getPlayerManager().getPlayer(id) == null);
		}
		// keep the chunks of autopilot ships that are not loaded yet (after a restart) loaded until
		// the entity appears and takes over its own tickets
		if (server.getTicks() % 200 == 0) {
			reloadFerries(server);
		}
	}

	/** Server position of each player at the previous tick (fall-through detection). */
	private static final Map<UUID, double[]> PLAYER_POS = new java.util.HashMap<>();

	/**
	 * Server-side safety net: players are moved by their own client, which collides them with the
	 * hulls. If the client could not (another mod replacing the collision code on that client) and
	 * the player falls through a deck, put him back on it. The depth threshold is larger than the
	 * small deck steps, so the slight lag between the client's and the server's hull never triggers it.
	 */
	private static void catchFallingPlayer(ServerPlayerEntity player, double lastY) {
		for (ShipEntity ship : ShipTracker.ships(player.getEntityWorld())) {
			if (ship.isRemoved()) {
				continue;
			}
			fr.medievalships.core.ShipPose pose = ship.pose();
			double[] l = pose.toLocal(player.getX(), player.getY(), player.getZ());
			double top = ship.geometry().deckCrossingY(l[0], l[2], lastY - pose.y(), l[1], 0.6, false, ship.interiorState());
			if (!Double.isNaN(top)) {
				player.requestTeleport(player.getX(), pose.y() + top + 0.01, player.getZ());
				player.fallDistance = 0;
				PLAYER_POS.put(player.getUuid(), new double[] {player.getX(), pose.y() + top + 0.01, player.getZ()});
				return;
			}
		}
	}

	/** Registers the entity type ({@code medievalships:<id>}) and the item of a ship type. */
	private static <T extends ShipEntity> EntityType<T> registerShip(ShipType type, EntityType.EntityFactory<T> factory,
			float width, float height, int trackingRange) {
		RegistryKey<EntityType<?>> entityKey = RegistryKey.of(RegistryKeys.ENTITY_TYPE, id(type.id()));
		EntityType<T> entityType = Registry.register(Registries.ENTITY_TYPE, entityKey,
				EntityType.Builder.create(factory, SpawnGroup.MISC)
						.dimensions(width, height)
						.maxTrackingRange(trackingRange)
						.trackingTickInterval(1)
						.makeFireImmune()
						.build(entityKey));
		ENTITY_TYPES.put(type, entityType);
		RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, id(type.id()));
		ITEMS.put(type, Registry.register(Registries.ITEM, itemKey, new ShipItem(type, new Item.Settings().registryKey(itemKey).maxCount(1))));
		return entityType;
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
			world.getChunkManager().addTicket(ChunkTicketType.PORTAL, chunk, ConfigManager.server().chunkLoadRadius);
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
				if (e instanceof ShipEntity ship && world == player.getEntityWorld()) {
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
