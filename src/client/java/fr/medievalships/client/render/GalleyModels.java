package fr.medievalships.client.render;

import java.io.Reader;
import java.util.Optional;

import org.jetbrains.annotations.Nullable;

import net.minecraft.resource.Resource;
import net.minecraft.resource.ResourceManager;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.model.BbModel;

/**
 * Holds the galley model, read directly from the Blockbench file
 * {@code assets/medievalships/models/entity/galley.bbmodel} (reloaded with resource packs, F3+T).
 */
public final class GalleyModels {
	public static final Identifier MODEL = MedievalShips.id("models/entity/galley.bbmodel");
	public static final Identifier TEXTURE = MedievalShips.id("textures/entity/galley.png");
	@Nullable
	private static BbModel galley;

	private GalleyModels() {
	}

	@Nullable
	public static BbModel galley() {
		return galley;
	}

	public static void reload(ResourceManager manager) {
		Optional<Resource> resource = manager.getResource(MODEL);
		if (resource.isEmpty()) {
			MedievalShips.LOGGER.error("Missing ship model {}", MODEL);
			galley = null;
			return;
		}
		try (Reader reader = resource.get().getReader()) {
			galley = new BbModel(reader);
			MedievalShips.LOGGER.info("Loaded ship model: {} bones, {} faces, {} animations",
					galley.bones.size(), galley.quadCount(), galley.animations.size());
		} catch (Exception e) {
			MedievalShips.LOGGER.error("Could not load ship model {}", MODEL, e);
			galley = null;
		}
	}
}
