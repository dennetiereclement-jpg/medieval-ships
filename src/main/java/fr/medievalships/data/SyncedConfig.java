package fr.medievalships.data;

import java.util.HashMap;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.player.PlayerEntity;

import fr.medievalships.core.ServerSettings;
import fr.medievalships.core.ShipType;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.network.ServerConfigPayload;

/**
 * Client side: the server's settings that change what the client shows ({@link ServerConfigPayload}), so that a
 * dedicated server's {@code medievalships.json} applies to every player, whatever is in his own config file: the
 * placement permission and the altitude ceiling of the preview, the bank angle drawn in the turns, the gait speeds of
 * the pilot's panel. Until the server has sent them (and in a solo world, where they are the same) the local config
 * is used.
 */
public final class SyncedConfig {
	@Nullable
	private static volatile ServerSettings settings;
	private static volatile Map<String, ServerConfigPayload.Vessel> vessels = Map.of();

	private SyncedConfig() {
	}

	/** The settings sent by the server (client thread). */
	public static void receive(ServerConfigPayload p) {
		ServerSettings s = new ServerSettings();
		s.adminPermissionLevel = p.adminPermissionLevel();
		s.placeRequiresAdmin = p.placeRequiresAdmin();
		s.placeAdminOnly = new java.util.ArrayList<>(p.placeAdminOnly());
		s.placeAllowedPlayers = new java.util.ArrayList<>(p.placeAllowedPlayers());
		Map<String, ServerConfigPayload.Vessel> map = new HashMap<>();
		for (ServerConfigPayload.Vessel v : p.vessels()) {
			map.put(v.id(), v);
		}
		vessels = Map.copyOf(map);
		settings = s;
	}

	/** Disconnected: back to the local config. */
	public static void clear() {
		settings = null;
		vessels = Map.of();
	}

	/** Has the server sent its settings? */
	public static boolean received() {
		return settings != null;
	}

	/** The server's values for this vessel (the local config's until they are received). */
	public static ServerConfigPayload.Vessel vessel(ShipType type) {
		ServerConfigPayload.Vessel v = vessels.get(type.id());
		return v != null ? v : ServerConfigPayload.Vessel.of(type, ConfigManager.ship(type));
	}

	/** May this (local) player place this vessel with its item, by the server's rules? */
	public static boolean mayPlace(PlayerEntity player, ShipType type) {
		ServerSettings s = settings;
		if (s == null) {
			return ShipPermissions.mayPlace(player, type);
		}
		boolean admin = ShipPermissions.level(player.getPermissions()) >= s.adminPermissionLevel;
		return s.mayPlace(type.id(), admin, player.getGameProfile().name(), player.getUuidAsString());
	}
}
