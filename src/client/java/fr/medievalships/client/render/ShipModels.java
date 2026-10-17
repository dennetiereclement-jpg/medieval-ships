package fr.medievalships.client.render;

import java.io.Reader;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.jetbrains.annotations.Nullable;

import net.minecraft.resource.Resource;
import net.minecraft.resource.ResourceManager;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/**
 * Holds the ship models, read directly from the Blockbench files
 * {@code assets/medievalships/models/entity/<ship>.bbmodel} (reloaded with resource packs, F3+T).
 * Texture {@code i} of a model is {@code textures/entity/<textures[i]>.png}, so a resource pack
 * can replace any of them (the galleon flag emblem is its second texture).
 */
public final class ShipModels {
	/**
	 * Client look of a ship type.
	 *
	 * @param rocking    wave rocking amplitude of this hull (multiplied by the config value)
	 * @param cullRadius horizontal / vertical half extent of the render culling box
	 */
	public record Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
			double cullRadius, double cullHeight) {
	}

	public static final Visual GALLEY = new Visual(Ships.GALLEY, model("galley"), List.of(texture("galley")), 1f, 12, 16);
	public static final Visual GALLEON = new Visual(Ships.GALLEON, model("galleon"),
			List.of(texture("galleon"), texture("galleon_flag")), 0.55f, 24, 30);
	public static final List<Visual> ALL = List.of(GALLEY, GALLEON);

	private static final Map<Visual, BbModel> LOADED = new LinkedHashMap<>();

	private ShipModels() {
	}

	private static Identifier model(String name) {
		return MedievalShips.id("models/entity/" + name + ".bbmodel");
	}

	private static Identifier texture(String name) {
		return MedievalShips.id("textures/entity/" + name + ".png");
	}

	@Nullable
	public static BbModel get(Visual visual) {
		return LOADED.get(visual);
	}

	public static void reload(ResourceManager manager) {
		LOADED.clear();
		for (Visual v : ALL) {
			Optional<Resource> resource = manager.getResource(v.model());
			if (resource.isEmpty()) {
				MedievalShips.LOGGER.error("Missing ship model {}", v.model());
				continue;
			}
			try (Reader reader = resource.get().getReader()) {
				BbModel m = new BbModel(reader);
				LOADED.put(v, m);
				MedievalShips.LOGGER.info("Loaded ship model {}: {} bones, {} faces, {} animations",
						v.type().id(), m.bones.size(), m.quadCount(), m.animations.size());
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Could not load ship model {}", v.model(), e);
			}
		}
	}
}
