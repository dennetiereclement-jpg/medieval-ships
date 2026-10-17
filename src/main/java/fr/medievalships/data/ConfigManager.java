package fr.medievalships.data;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import net.fabricmc.loader.api.FabricLoader;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipConfig;

/** Loads / writes {@code config/medievalships.json}. */
public final class ConfigManager {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static ShipConfig config = new ShipConfig();

	private ConfigManager() {
	}

	public static ShipConfig get() {
		return config;
	}

	public static Path path() {
		return FabricLoader.getInstance().getConfigDir().resolve(MedievalShips.MOD_ID + ".json");
	}

	public static void load() {
		Path path = path();
		ShipConfig loaded = null;
		if (Files.exists(path)) {
			try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
				loaded = GSON.fromJson(r, ShipConfig.class);
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Invalid {}, using defaults", path, e);
			}
		}
		config = loaded != null ? loaded : new ShipConfig();
		config.sanitize();
		// rewrite so new options appear with their default value
		try {
			Files.createDirectories(path.getParent());
			try (Writer w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
				GSON.toJson(config, w);
			}
		} catch (IOException e) {
			MedievalShips.LOGGER.warn("Could not write {}", path, e);
		}
	}
}
