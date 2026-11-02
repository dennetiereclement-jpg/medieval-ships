package fr.medievalships.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

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
	 * Vessels (type ids, e.g. {@code "sky_leviathan"}, or their aliases such as {@code "grand_warship"}) that only
	 * admins may place with the item, even when {@link #placeRequiresAdmin} is false. {@link #sanitize} turns the
	 * aliases into the ids; {@link #unknownVessels} lists what matches no vessel.
	 */
	public List<String> placeAdminOnly = new ArrayList<>();
	/**
	 * Players (names or UUIDs, any case) who may place every vessel with the item although they are not admins: the
	 * "allowed players" of a server where placing is otherwise reserved to the admins.
	 */
	public List<String> placeAllowedPlayers = new ArrayList<>();
	/**
	 * Players aboard a vessel may give it a destination with {@code /pilote goto} (its autopilot flies or sails
	 * there). Never for a vessel on an administrator's route (a ferry), never against the player at the helm. Such a
	 * trip loads no chunks and stops once nobody has been aboard for 10 s (see {@link GotoRoutes}).
	 */
	public boolean playerDestinations = true;
	/** Farthest destination (blocks, horizontally) a player who is not an admin may give with {@code /pilote goto}. */
	public double playerDestinationMaxDistance = DEFAULT_PLAYER_DESTINATION_MAX_DISTANCE;
	public static final double DEFAULT_PLAYER_DESTINATION_MAX_DISTANCE = 1000.0;
	/** Tents (client drawing): the furniture and small details are drawn within this distance (blocks)... */
	public double tentDecorDistance = 32.0;
	/** ...and the tent itself within this one; beyond, nothing is drawn. */
	public double tentRenderDistance = 64.0;
	/**
	 * The crafting workshops' hook (1.22.0): a server command per profession id ({@code "jeweler"}, {@code "blacksmith"}...,
	 * see {@link TentType#profession()}; a workshop id such as {@code "workshop_jeweler"} is accepted too), run as the
	 * player who right-clicks a workshop of that profession, at their position, e.g.
	 * {@code {"jeweler": "trigger jeweler_menu"}}: an existing crafting / MMO interface opened by a command, without Java.
	 * Empty by default (a right click then only shows a short message). {@link #sanitize} trims the entries, lower-cases
	 * the keys, removes a leading {@code /} and drops blank entries.
	 */
	public Map<String, String> workshopCommands = new LinkedHashMap<>();

	public void sanitize() {
		announceRadius = Math.max(0, Math.min(512, Double.isNaN(announceRadius) ? 40 : announceRadius));
		chunkLoadRadius = Math.max(2, Math.min(4, chunkLoadRadius)); // below 2 the centre chunk does not tick entities
		adminPermissionLevel = Math.max(0, Math.min(4, adminPermissionLevel));
		placeAdminOnly = canonicalVessels(clean(placeAdminOnly));
		placeAllowedPlayers = clean(placeAllowedPlayers);
		workshopCommands = cleanCommands(workshopCommands);
		tentDecorDistance = Double.isNaN(tentDecorDistance) ? 32.0 : Math.max(0, Math.min(256, tentDecorDistance));
		tentRenderDistance = Double.isNaN(tentRenderDistance) ? 64.0 : Math.max(8, Math.min(512, tentRenderDistance));
		playerDestinationMaxDistance = Double.isNaN(playerDestinationMaxDistance) ? DEFAULT_PLAYER_DESTINATION_MAX_DISTANCE
				: Math.max(16, Math.min(1_000_000, playerDestinationMaxDistance));
	}

	/** The vessel ids of a list ({@code "grand_warship"} becomes {@code "warship"}); unknown entries are kept as they are. */
	private static List<String> canonicalVessels(List<String> in) {
		List<String> out = new ArrayList<>();
		for (String s : in) {
			ShipType t = Ships.byId(s);
			String id = t == null ? s : t.id();
			if (!out.contains(id)) {
				out.add(id);
			}
		}
		return out;
	}

	/** The key of {@link #workshopCommands} for a profession or workshop id: trimmed, lower case, without "workshop_". */
	public static String professionKey(String id) {
		if (id == null) {
			return "";
		}
		String k = id.trim().toLowerCase(Locale.ROOT);
		if (k.startsWith("medievalships:")) {
			k = k.substring("medievalships:".length());
		}
		return k.startsWith("workshop_") ? k.substring("workshop_".length()) : k;
	}

	private static Map<String, String> cleanCommands(Map<String, String> in) {
		Map<String, String> out = new LinkedHashMap<>();
		if (in != null) {
			for (Map.Entry<String, String> e : in.entrySet()) {
				String key = professionKey(e.getKey());
				String cmd = e.getValue() == null ? "" : e.getValue().trim();
				while (cmd.startsWith("/")) {
					cmd = cmd.substring(1).trim();
				}
				if (!key.isEmpty() && !cmd.isEmpty()) {
					out.put(key, cmd);
				}
			}
		}
		return out;
	}

	/** The command configured for a profession ({@link #workshopCommands}), or null when there is none. */
	public String workshopCommand(String profession) {
		if (workshopCommands == null || profession == null) {
			return null;
		}
		String cmd = workshopCommands.get(professionKey(profession));
		return cmd == null || cmd.isBlank() ? null : cmd;
	}

	/**
	 * Sets (or, with a null or blank command, removes) the command of a profession, cleaned as {@link #sanitize} does:
	 * the API for code and tests (the config file is the usual way). Lasts until the config is loaded again.
	 */
	public void setWorkshopCommand(String profession, String command) {
		Map<String, String> map = new LinkedHashMap<>(workshopCommands == null ? Map.of() : workshopCommands);
		map.remove(professionKey(profession));
		if (command != null) {
			map.put(profession, command);
		}
		workshopCommands = cleanCommands(map);
	}

	/** Entries of {@link #placeAdminOnly} that are no vessel of this version (a typo reserves nothing: worth a warning). */
	public List<String> unknownVessels() {
		List<String> out = new ArrayList<>();
		for (String s : placeAdminOnly == null ? List.<String>of() : placeAdminOnly) {
			if (Ships.byId(s) == null) {
				out.add(s);
			}
		}
		return out;
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
