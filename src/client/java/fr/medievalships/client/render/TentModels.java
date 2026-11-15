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
 * resource packs); every tent draws the shared atlas {@code textures/entity/tents.png}, every cart
 * {@code textures/entity/carts.png} ({@link TentType#texture()}). A prop whose model is missing (not generated yet)
 * is simply not drawn (logged once). 1.34.0: the models a prop draws with its main one ({@link TentType#extraModels()},
 * the divine forge's statue and decor), each with its own atlas ({@link #extras}); a missing one is left out.
 */
public final class TentModels {
	public static final List<Identifier> TEXTURES = List.of(MedievalShips.id("textures/entity/tents.png"));
	private static final Map<TentType, BbModel> LOADED = new HashMap<>();
	/** A model drawn with a prop's main one (1.34.0, JSON "extra_models"): the model and its atlas. */
	public record Extra(BbModel model, Identifier texture) {
	}

	private static final Map<TentType, List<Extra>> EXTRAS = new HashMap<>();
	private static final Map<String, Identifier> ATLASES = new HashMap<>();

	private TentModels() {
	}

	@Nullable
	public static BbModel get(TentType type) {
		return LOADED.get(type);
	}

	/** The models drawn with a prop's main one, same transform (empty for most props, or when they are missing). */
	public static List<Extra> extras(TentType type) {
		return EXTRAS.getOrDefault(type, List.of());
	}

	/** The atlas a prop's model is drawn with. */
	public static Identifier texture(TentType type) {
		return ATLASES.computeIfAbsent(type.texture(), MedievalShips::id);
	}

	public static void reload(ResourceManager manager) {
		LOADED.clear();
		EXTRAS.clear();
		for (TentType t : TentTypes.PROPS) {
			for (TentType.ExtraModel extra : t.extraModels()) {
				Identifier eid = MedievalShips.id(extra.model());
				Optional<Resource> er = manager.getResource(eid);
				if (er.isEmpty()) {
					MedievalShips.LOGGER.warn("No extra model for the prop {} ({}): it will not be drawn", t.id(), eid);
					continue;
				}
				try (Reader reader = er.get().getReader()) {
					BbModel m = new BbModel(reader);
					EXTRAS.computeIfAbsent(t, k -> new java.util.ArrayList<>()).add(new Extra(m, ATLASES.computeIfAbsent(extra.texture(), MedievalShips::id)));
					MedievalShips.LOGGER.info("Loaded extra model {} of {}: {} bones, {} faces", extra.model(), t.id(), m.bones.size(), m.quadCount());
				} catch (Exception e) {
					MedievalShips.LOGGER.error("Could not load the extra model {}", eid, e);
				}
			}
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
