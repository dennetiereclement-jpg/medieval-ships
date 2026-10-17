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
import fr.medievalships.core.Ships.PaddleboatLayout;

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
			double cullRadius, double cullHeight, boolean bowWake, @Nullable Engine engine) {
		public Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
				double cullRadius, double cullHeight, boolean bowWake) {
			this(type, model, textures, rocking, cullRadius, cullHeight, bowWake, null);
		}
	}

	/**
	 * Steam engine effects of a ship (client only): smoke from the funnel tops, foam and spray at the
	 * paddle wheel, the beat of the engine. Ship-local blocks.
	 *
	 * @param funnels    funnel mouths (x, y, z)
	 * @param wheel      paddle wheel: centre (x, y, z) and radius
	 */
	public record Engine(double[][] funnels, double[] wheel) {
	}

	public static final Visual GALLEY = new Visual(Ships.GALLEY, model("galley"), List.of(texture("galley")), 1f, 12, 16, false);
	public static final Visual GALLEON = new Visual(Ships.GALLEON, model("galleon"),
			List.of(texture("galleon"), texture("galleon_flag")), 0.55f, 24, 30, false);
	public static final Visual WARSHIP = new Visual(Ships.WARSHIP, model("warship"),
			List.of(texture("warship"), texture("warship_flag")), 0.4f, 42, 48, true);
	public static final Visual MEDIEVAL_GALLEY = new Visual(Ships.MEDIEVAL_GALLEY, model("medieval_galley"),
			List.of(texture("medieval_galley")), 0.9f, 16, 18, false);
	public static final Visual STEAM_PADDLEBOAT = new Visual(Ships.STEAM_PADDLEBOAT, model("steam_paddleboat"),
			List.of(texture("steam_paddleboat")), 0.7f, 14, 14, true, new Engine(
					new double[][] {{0, PaddleboatLayout.FUNNEL_TOP + 0.3, PaddleboatLayout.FUNNEL_Z[0]},
							{0, PaddleboatLayout.FUNNEL_TOP + 0.3, PaddleboatLayout.FUNNEL_Z[1]}},
					new double[] {-(PaddleboatLayout.WHEEL_X0 + PaddleboatLayout.WHEEL_X1) / 2, PaddleboatLayout.WHEEL_Y,
							PaddleboatLayout.WHEEL_Z, PaddleboatLayout.WHEEL_R}));
	public static final Visual ELVEN_SAILBOAT = new Visual(Ships.ELVEN_SAILBOAT, model("elven_sailboat"),
			List.of(texture("elven_sailboat")), 0.85f, 18, 22, true);
	public static final List<Visual> ALL = List.of(GALLEY, GALLEON, WARSHIP, MEDIEVAL_GALLEY, STEAM_PADDLEBOAT, ELVEN_SAILBOAT);

	@Nullable
	public static Visual of(ShipType type) {
		for (Visual v : ALL) {
			if (v.type() == type) {
				return v;
			}
		}
		return null;
	}

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
