package fr.medievalships.client.render;

import java.io.Reader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.jetbrains.annotations.Nullable;

import net.minecraft.resource.Resource;
import net.minecraft.resource.ResourceManager;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;

/**
 * The tent models, read from {@code assets/medievalships/<TentType.model()>} like the ships' (reloaded with
 * resource packs); every tent draws the shared atlas {@code textures/entity/tents.png}. A tent whose model is
 * missing (not generated yet) is simply not drawn (logged once).
 */
public final class TentModels {
	public static final List<Identifier> TEXTURES = List.of(MedievalShips.id("textures/entity/tents.png"));
	private static final Map<TentType, BbModel> LOADED = new HashMap<>();

	private TentModels() {
	}

	@Nullable
	public static BbModel get(TentType type) {
		return LOADED.get(type);
	}

	public static void reload(ResourceManager manager) {
		LOADED.clear();
		for (TentType t : TentTypes.ALL) {
			Identifier id = MedievalShips.id(t.model());
			Optional<Resource> resource = manager.getResource(id);
			if (resource.isEmpty()) {
				MedievalShips.LOGGER.warn("No model for the tent {} ({}): it will not be drawn", t.id(), id);
				continue;
			}
			try (Reader reader = resource.get().getReader()) {
				BbModel m = new BbModel(reader);
				LOADED.put(t, m);
				MedievalShips.LOGGER.info("Loaded tent model {}: {} bones, {} faces", t.id(), m.bones.size(), m.quadCount());
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Could not load tent model {}", id, e);
			}
		}
	}
}
