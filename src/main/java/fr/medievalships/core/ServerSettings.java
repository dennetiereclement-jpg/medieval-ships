package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Settings shared by every ship ({@code "server"} section of {@code config/medievalships.json}). */
public final class ServerSettings {
	/** Announce departures / arrivals to players aboard and near the ship. */
	public boolean announceDepartures = true;
	public double announceRadius = 40.0;
	/** Keep the chunks around autopilot ships loaded so ferries run without players nearby. */
	public boolean chunkLoadAutopilotShips = true;
	public int chunkLoadRadius = 2;
	/** Permission level for /ship and for picking ships up. */
	public int adminPermissionLevel = 2;
	/** If true, only admins can place a ship with the item. */
	public boolean placeRequiresAdmin = false;
	/**
	 * Vessels (type ids, e.g. {@code "sky_leviathan"}) that only admins may place with the item, even when
	 * {@link #placeRequiresAdmin} is false.
	 */
	public List<String> placeAdminOnly = new ArrayList<>();
	/**
	 * Players (names or UUIDs, any case) who may place every vessel with the item although they are not admins: the
	 * "allowed players" of a server where placing is otherwise reserved to the admins.
	 */
	public List<String> placeAllowedPlayers = new ArrayList<>();
	/**
	 * Players aboard a vessel may give it a destination with {@code /pilote goto} (its autopilot flies or sails
	 * there). Never for a vessel on an administrator's route (a ferry), never against the player at the helm.
	 */
	public boolean playerDestinations = true;
	/** Farthest destination (blocks, horizontally) a player who is not an admin may give with {@code /pilote goto}. */
	public double playerDestinationMaxDistance = 5000.0;

	public void sanitize() {
		announceRadius = Math.max(0, Math.min(512, Double.isNaN(announceRadius) ? 40 : announceRadius));
		chunkLoadRadius = Math.max(2, Math.min(4, chunkLoadRadius)); // below 2 the centre chunk does not tick entities
		adminPermissionLevel = Math.max(0, Math.min(4, adminPermissionLevel));
		placeAdminOnly = clean(placeAdminOnly);
		placeAllowedPlayers = clean(placeAllowedPlayers);
		playerDestinationMaxDistance = Double.isNaN(playerDestinationMaxDistance) ? 5000
				: Math.max(16, Math.min(1_000_000, playerDestinationMaxDistance));
	}

	private static List<String> clean(List<String> in) {
		List<String> out = new ArrayList<>();
		if (in != null) {
			for (String s : in) {
				if (s != null && !s.isBlank()) {
					out.add(s.trim());
				}
			}
		}
		return out;
	}

	/**
	 * May this player place this vessel with its item? Admins always may. Otherwise the vessel must not be reserved
	 * to the admins ({@link #placeRequiresAdmin} for every vessel, {@link #placeAdminOnly} for some), or the player
	 * must be one of {@link #placeAllowedPlayers}.
	 */
	public boolean mayPlace(String typeId, boolean admin, String playerName, String playerUuid) {
		if (admin) {
			return true;
		}
		boolean reserved = placeRequiresAdmin || contains(placeAdminOnly, typeId);
		return !reserved || contains(placeAllowedPlayers, playerName) || contains(placeAllowedPlayers, playerUuid);
	}

	private static boolean contains(List<String> list, String value) {
		if (list == null || value == null) {
			return false;
		}
		String v = value.trim().toLowerCase(Locale.ROOT);
		for (String s : list) {
			if (s != null && s.trim().toLowerCase(Locale.ROOT).equals(v)) {
				return true;
			}
		}
		return false;
	}
}
