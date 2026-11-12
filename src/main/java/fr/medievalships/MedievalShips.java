package fr.medievalships;

import java.util.LinkedHashMap;
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
import fr.medievalships.entity.HotAirBalloonEntity;
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.MedievalGalleyEntity;
import fr.medievalships.entity.ElvenSailboatEntity;
import fr.medievalships.entity.NautilusEntity;
import fr.medievalships.entity.BlueFrigateEntity;
import fr.medievalships.entity.RoyalLionShipEntity;
import fr.medievalships.entity.GearSteamShipEntity;
import fr.medievalships.entity.OldCorsairEntity;
import fr.medievalships.entity.SkyLeviathanEntity;
import fr.medievalships.entity.CrystalAirshipEntity;
import fr.medievalships.entity.RowboatEntity;
import fr.medievalships.entity.RusticSkiffEntity;
import fr.medievalships.entity.DragonJunkEntity;
import fr.medievalships.entity.SteampunkAirshipEntity;
import fr.medievalships.entity.TradeSloopEntity;
import fr.medievalships.entity.FortressShipEntity;
import fr.medievalships.entity.SteamPaddleboatEntity;
import fr.medievalships.entity.WarshipEntity;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.mixin.ServerPlayNetworkHandlerAccessor;
import fr.medievalships.network.ServerConfigPayload;
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
	public static EntityType<RusticSkiffEntity> RUSTIC_SKIFF;
	public static Item RUSTIC_SKIFF_ITEM;
	public static EntityType<TradeSloopEntity> TRADE_SLOOP;
	public static Item TRADE_SLOOP_ITEM;
	public static EntityType<DragonJunkEntity> DRAGON_JUNK;
	public static Item DRAGON_JUNK_ITEM;
	public static EntityType<HotAirBalloonEntity> HOT_AIR_BALLOON;
	public static Item HOT_AIR_BALLOON_ITEM;
	public static EntityType<BlueFrigateEntity> BLUE_FRIGATE;
	public static Item BLUE_FRIGATE_ITEM;
	public static EntityType<FortressShipEntity> FORTRESS_SHIP;
	public static Item FORTRESS_SHIP_ITEM;
	public static EntityType<RowboatEntity> ROWBOAT;
	public static Item ROWBOAT_ITEM;
	public static EntityType<RoyalLionShipEntity> ROYAL_LION_SHIP;
	public static Item ROYAL_LION_SHIP_ITEM;
	public static EntityType<GearSteamShipEntity> GEAR_STEAMSHIP;
	public static Item GEAR_STEAMSHIP_ITEM;

	private static final Map<ShipType, EntityType<? extends ShipEntity>> ENTITY_TYPES = new LinkedHashMap<>();
	private static final Map<ShipType, Item> ITEMS = new LinkedHashMap<>();

	public static EntityType<? extends ShipEntity> entityType(ShipType type) {
		return ENTITY_TYPES.get(type);
	}

	public static Item item(ShipType type) {
		return ITEMS.get(type);
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
		RUSTIC_SKIFF = registerShip(Ships.RUSTIC_SKIFF, RusticSkiffEntity::new, 4.0f, 0.4f, 20);
		RUSTIC_SKIFF_ITEM = ITEMS.get(Ships.RUSTIC_SKIFF);
		DRAGON_JUNK = registerShip(Ships.DRAGON_JUNK, DragonJunkEntity::new, 5.0f, 0.4f, 22);
		DRAGON_JUNK_ITEM = ITEMS.get(Ships.DRAGON_JUNK);
		HOT_AIR_BALLOON = registerShip(Ships.HOT_AIR_BALLOON, HotAirBalloonEntity::new, 3.0f, 0.4f, 20);
		HOT_AIR_BALLOON_ITEM = ITEMS.get(Ships.HOT_AIR_BALLOON);
		BLUE_FRIGATE = registerShip(Ships.BLUE_FRIGATE, BlueFrigateEntity::new, 6.0f, 0.4f, 22);
		BLUE_FRIGATE_ITEM = ITEMS.get(Ships.BLUE_FRIGATE);
		ROWBOAT = registerShip(Ships.ROWBOAT, RowboatEntity::new, 1.5f, 0.5f, 10);
		ROWBOAT_ITEM = ITEMS.get(Ships.ROWBOAT);
		TRADE_SLOOP = registerShip(Ships.TRADE_SLOOP, TradeSloopEntity::new, 3.0f, 0.4f, 14);
		TRADE_SLOOP_ITEM = ITEMS.get(Ships.TRADE_SLOOP);
		ROYAL_LION_SHIP = registerShip(Ships.ROYAL_LION_SHIP, RoyalLionShipEntity::new, 6.5f, 0.4f, 22);
		ROYAL_LION_SHIP_ITEM = ITEMS.get(Ships.ROYAL_LION_SHIP);
		FORTRESS_SHIP = registerShip(Ships.FORTRESS_SHIP, FortressShipEntity::new, 6.0f, 0.4f, 24);
		FORTRESS_SHIP_ITEM = ITEMS.get(Ships.FORTRESS_SHIP);
		GEAR_STEAMSHIP = registerShip(Ships.GEAR_STEAMSHIP, GearSteamShipEntity::new, 6.0f, 0.4f, 22);
		GEAR_STEAMSHIP_ITEM = ITEMS.get(Ships.GEAR_STEAMSHIP);

		// the six tents: one block each, their items in the tab "Tentes"
		fr.medievalships.tent.Tents.register();

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, id("ships"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(GALLEY_ITEM))
				.displayName(Text.translatable("itemGroup.medievalships.ships"))
				.entries((context, entries) -> {
					ITEMS.values().forEach(entries::add);
					// the decorative rowboat beside the sailing one (it is also in the tab "Charrettes")
					entries.add(fr.medievalships.tent.Tents.item(fr.medievalships.core.TentTypes.ROWBOAT_DECO));
				})
				.build());
		ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS).register(entries -> ITEMS.values().forEach(entries::add));

		PayloadTypeRegistry.playC2S().register(ShipInteractPayload.ID, ShipInteractPayload.CODEC);
		PayloadTypeRegistry.playS2C().register(ServerConfigPayload.ID, ServerConfigPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(ShipInteractPayload.ID,
				(payload, context) -> ShipInteractions.handle(payload, context.player()));

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			ShipCommands.register(dispatcher);
			fr.medievalships.command.TentCommands.register(dispatcher);
			fr.medievalships.command.DrawbridgeCommands.register(dispatcher);
		});
		// the drawbridges (1.24.0): their data, their tick, their sync to the clients
		fr.medievalships.bridge.Drawbridges.init();

		ServerLifecycleEvents.SERVER_STARTED.register(MedievalShips::reloadFerries);
		ServerTickEvents.END_SERVER_TICK.register(MedievalShips::serverTick);
		// several players on moving decks (1.30.0): deck frames, deck positions to the other clients, back aboard at login
		fr.medievalships.entity.DeckSync.init();
		fr.medievalships.entity.DeckAnchors.init();
		// a new player entity (respawn) or another world: the last position of the old one means nothing
		net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents.AFTER_RESPAWN
				.register((oldPlayer, newPlayer, alive) -> PLAYER_POS.remove(newPlayer.getUuid()));
		net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD
				.register((player, origin, destination) -> PLAYER_POS.remove(player.getUuid()));
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
				ship = fr.medievalships.entity.DeckSync.standingOn(player);
			}
			// the spot aboard goes into the player's own data (each character of a multi-character mod has its own)
			fr.medievalships.entity.DeckAnchors.onDisconnect(player, ship, server);
			PLAYER_POS.remove(player.getUuid());
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			if (ServerPlayNetworking.canSend(handler.player, ServerConfigPayload.ID)) {
				sender.sendPacket(ServerConfigPayload.current()); // what the client shows follows this server's config
			}
			PLAYER_POS.remove(handler.player.getUuid());
			// logged out aboard a ship that may have sailed on: back on its deck, at the same spot (1.30.0)
			fr.medievalships.entity.DeckAnchors.onJoin(handler.player, server);
		});
		LOGGER.info("Medieval ships loaded");
	}

	/** Sends the settings the clients need ({@link ServerConfigPayload}) to every player, after {@code /ship reload}. */
	public static void sendConfig(MinecraftServer server) {
		ServerConfigPayload payload = ServerConfigPayload.current();
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			if (ServerPlayNetworking.canSend(player, ServerConfigPayload.ID)) {
				ServerPlayNetworking.send(player, payload);
			}
		}
	}

	private static void serverTick(MinecraftServer server) {
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			double[] last = PLAYER_POS.getOrDefault(player.getUuid(), new double[] {player.getX(), player.getY(), player.getZ()});
			PLAYER_POS.put(player.getUuid(), new double[] {player.getX(), player.getY(), player.getZ()});
			if (player.hasVehicle() || player.isSpectator() || player.getAbilities().flying) {
				continue;
			}
			// players walking on a ship are not flying, whatever the blocks under the raised decks say
			if (ShipTracker.shipUnder(player) != null || ShipTracker.onGangplank(player)
					|| fr.medievalships.bridge.DrawbridgeCollisions.standsOn(player) || fr.medievalships.entity.ShipLadders.climbing(player)) {
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
						// the clients interpolate the hull's position and never use its velocity: not sent every tick
						.alwaysUpdateVelocity(false)
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
}
