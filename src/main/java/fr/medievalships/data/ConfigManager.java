package fr.medievalships.data;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.fabricmc.loader.api.FabricLoader;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ServerSettings;
import fr.medievalships.core.ShipConfig;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/**
 * Loads / writes {@code config/medievalships.json}:
 * <pre>{ "server": {...}, "ships": { "galley": {...}, "galleon": {...} } }</pre>
 * The flat file of version 1.0/1.1 (galley values at the top level) is migrated automatically.
 */
public final class ConfigManager {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static ServerSettings server = new ServerSettings();
	private static final Map<String, ShipConfig> SHIPS = new LinkedHashMap<>();

	private ConfigManager() {
	}

	public static ServerSettings server() {
		return server;
	}

	public static ShipConfig ship(ShipType type) {
		return SHIPS.computeIfAbsent(type.id(), id -> {
			ShipConfig c = type.defaults().get();
			c.sanitize();
			return c;
		});
	}

	public static Path path() {
		return FabricLoader.getInstance().getConfigDir().resolve(MedievalShips.MOD_ID + ".json");
	}

	/** 2 (1.5.2): the elven sailboat keeps its sails set when stopped. */
	public static final int CONFIG_VERSION = 2;

	public static void load() {
		Path path = path();
		JsonObject root = null;
		if (Files.exists(path)) {
			try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
				JsonElement e = JsonParser.parseReader(r);
				root = e.isJsonObject() ? e.getAsJsonObject() : null;
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Invalid {}, using defaults", path, e);
			}
		}
		apply(root);
		try {
			Files.createDirectories(path.getParent());
			try (Writer w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
				GSON.toJson(toJson(), w); // rewrite so new options appear with their default value
			}
		} catch (IOException e) {
			MedievalShips.LOGGER.warn("Could not write {}", path, e);
		}
	}

	/** Reads a config tree (null = defaults). Public for tests. */
	public static void apply(JsonObject root) {
		SHIPS.clear();
		server = new ServerSettings();
		if (root != null) {
			boolean legacy = !root.has("ships") && root.has("normalSpeed");
			if (legacy) {
				// 1.0 / 1.1: one flat object holding the galley and the server settings
				server = GSON.fromJson(root, ServerSettings.class);
				SHIPS.put(Ships.GALLEY.id(), merge(Ships.GALLEY, root));
				MedievalShips.LOGGER.info("Migrated the old medievalships.json format (galley settings kept)");
			} else {
				if (root.has("server") && root.get("server").isJsonObject()) {
					server = GSON.fromJson(root.get("server"), ServerSettings.class);
				}
				if (root.has("ships") && root.get("ships").isJsonObject()) {
					JsonObject ships = root.getAsJsonObject("ships");
					for (ShipType t : Ships.ALL) {
						if (ships.has(t.id()) && ships.get(t.id()).isJsonObject()) {
							SHIPS.put(t.id(), merge(t, ships.getAsJsonObject(t.id())));
						}
					}
				}
				int version = root.has("configVersion") && root.get("configVersion").isJsonPrimitive()
						? root.get("configVersion").getAsInt() : 1;
				if (version < 2 && SHIPS.containsKey(Ships.ELVEN_SAILBOAT.id())) {
					// 1.5.x wrote furlSailWhenStopped = true for the elven sailboat; it now keeps its sails set
					SHIPS.get(Ships.ELVEN_SAILBOAT.id()).furlSailWhenStopped = false;
					MedievalShips.LOGGER.info("medievalships.json: the elven sailboat now keeps its sails set when stopped");
				}
			}
		}
		if (server == null) {
			server = new ServerSettings();
		}
		server.sanitize();
		for (ShipType t : Ships.ALL) {
			ship(t);
		}
	}

	/** Type defaults overridden by the values present in the file. */
	private static ShipConfig merge(ShipType type, JsonObject values) {
		JsonObject base = GSON.toJsonTree(type.defaults().get()).getAsJsonObject();
		for (Map.Entry<String, JsonElement> e : values.entrySet()) {
			if (base.has(e.getKey())) {
				base.add(e.getKey(), e.getValue());
			}
		}
		ShipConfig c = GSON.fromJson(base, ShipConfig.class);
		c.sanitize();
		return c;
	}

	public static JsonObject toJson() {
		JsonObject root = new JsonObject();
		root.addProperty("configVersion", CONFIG_VERSION);
		root.add("server", GSON.toJsonTree(server));
		JsonObject ships = new JsonObject();
		for (ShipType t : Ships.ALL) {
			ships.add(t.id(), GSON.toJsonTree(ship(t)));
		}
		root.add("ships", ships);
		return root;
	}
}
