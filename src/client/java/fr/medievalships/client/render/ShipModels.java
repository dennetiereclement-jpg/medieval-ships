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
import fr.medievalships.core.Ships.AirshipLayout;
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
	 * @param hover      slow up-and-down bob of the drawn model while it floats in the air, in blocks (0: none;
	 *                   only the drawing moves, never the collisions)
	 */
	public record Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
			double cullRadius, double cullHeight, boolean bowWake, @Nullable Engine engine, @Nullable Propeller propeller, float hover) {
		public Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
				double cullRadius, double cullHeight, boolean bowWake) {
			this(type, model, textures, rocking, cullRadius, cullHeight, bowWake, null, null, 0f);
		}

		public Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
				double cullRadius, double cullHeight, boolean bowWake, @Nullable Engine engine) {
			this(type, model, textures, rocking, cullRadius, cullHeight, bowWake, engine, null, 0f);
		}

		public Visual(ShipType type, Identifier model, List<Identifier> textures, float rocking,
				double cullRadius, double cullHeight, boolean bowWake, @Nullable Engine engine, @Nullable Propeller propeller) {
			this(type, model, textures, rocking, cullRadius, cullHeight, bowWake, engine, propeller, 0f);
		}
	}

	/**
	 * Airship effects (client only): the propeller hums and the wind blows faster with the speed,
	 * puffs of smoke from the exhaust, the creak of the gondola. Ship-local blocks.
	 *
	 * @param hub     propeller hub (x, y, z)
	 * @param exhaust mouth of the exhaust pipe (x, y, z)
	 */
	public record Propeller(double[] hub, double[] exhaust) {
	}

	/**
	 * Steam engine effects of a ship (client only): smoke from the funnel tops, foam and spray at the
	 * paddle wheel, the beat of the engine. Ship-local blocks.
	 *
	 * @param funnels    funnel mouths (x, y, z)
	 * @param wheels     paddle wheels: centre (x, y, z) and radius of each
	 */
	public record Engine(double[][] funnels, double[][] wheels) {
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
					new double[][] {
							{(PaddleboatLayout.WHEEL_X0 + PaddleboatLayout.WHEEL_X1) / 2, PaddleboatLayout.WHEEL_Y, PaddleboatLayout.WHEEL_Z,
									PaddleboatLayout.WHEEL_R},
							{-(PaddleboatLayout.WHEEL_X0 + PaddleboatLayout.WHEEL_X1) / 2, PaddleboatLayout.WHEEL_Y, PaddleboatLayout.WHEEL_Z,
									PaddleboatLayout.WHEEL_R}}));
	public static final Visual ELVEN_SAILBOAT = new Visual(Ships.ELVEN_SAILBOAT, model("elven_sailboat"),
			List.of(texture("elven_sailboat")), 0.85f, 18, 22, true);
	public static final Visual STEAMPUNK_AIRSHIP = new Visual(Ships.STEAMPUNK_AIRSHIP, model("steampunk_airship"),
			List.of(texture("steampunk_airship")), 1f, 20, 20, false, null, new Propeller(
					new double[] {0, AirshipLayout.BALLOON_Y, AirshipLayout.PROP_Z},
					new double[] {0, 4.85, AirshipLayout.ENGINE_Z0 - 1.0}));
	public static final Visual NAUTILUS = new Visual(Ships.NAUTILUS, model("nautilus"), List.of(texture("nautilus")), 0.2f, 50, 24, true);
	public static final Visual OLD_CORSAIR = new Visual(Ships.OLD_CORSAIR, model("old_corsair"), List.of(texture("old_corsair")), 0.5f, 34, 40, true);
	public static final Visual SKY_LEVIATHAN = new Visual(Ships.SKY_LEVIATHAN, model("sky_leviathan"),
			List.of(texture("sky_leviathan"), texture("sky_leviathan_interior")), 0.3f, 40, 40,
			false, null, null, 0.07f);
	public static final Visual CRYSTAL_AIRSHIP = new Visual(Ships.CRYSTAL_AIRSHIP, model("crystal_airship"),
			List.of(texture("crystal_airship"), texture("crystal_airship_interior")), 0.25f, 42, 42,
			false, null, null, 0.09f);
	/** The Rustic Skyskiff: the hum of its tubes and puffs of smoke from an upper tube's mouth; a light bob in the air. */
	public static final Visual RUSTIC_SKIFF = new Visual(Ships.RUSTIC_SKIFF, model("rustic_skiff"), List.of(texture("rustic_skiff")), 0.8f, 26, 22,
			false, null, new Propeller(fr.medievalships.core.SkiffLayout.TUBE_HUB, fr.medievalships.core.SkiffLayout.TUBE_EXHAUST), 0.06f);
	/** The Dragon Junk: its rooms' atlas and its great sail are textures of their own; a light bob in the air. */
	public static final Visual DRAGON_JUNK = new Visual(Ships.DRAGON_JUNK, model("dragon_junk"),
			List.of(texture("dragon_junk"), texture("dragon_junk_interior"), texture("dragon_junk_sail")), 0.45f, 30, 26, false, null, null, 0.06f);
	/** The hot-air balloon: sways and bobs softly in the air (its burner, smoke and sounds: {@code BalloonEffects}). */
	public static final Visual HOT_AIR_BALLOON = new Visual(Ships.HOT_AIR_BALLOON, model("hot_air_balloon"), List.of(texture("hot_air_balloon")), 1f,
			12, 24, false, null, null, 0.1f);
	/** The Blue-Sailed Frigate: its sails (with their fleurs-de-lis) are a texture of their own; foam at the bow. */
	public static final Visual BLUE_FRIGATE = new Visual(Ships.BLUE_FRIGATE, model("blue_frigate"),
			List.of(texture("blue_frigate"), texture("blue_frigate_sails")), 0.45f, 32, 36, true);
	/** The Rowboat: a very light rocking; its splashes and oar sounds come from {@code RowboatEffects}. */
	public static final Visual ROWBOAT = new Visual(Ships.ROWBOAT, model("rowboat"), List.of(texture("rowboat")), 0.6f, 5, 4, false);
	/** The trade sloop: a small boat that rocks on the waves, foam at its bow under way. */
	public static final Visual TRADE_SLOOP = new Visual(Ships.TRADE_SLOOP, model("trade_sloop"), List.of(texture("trade_sloop")), 1.1f, 14, 18, true);
	/** The Royal Lion Ship: its sails (with their gold lions) and its pennants are a texture of their own; foam at the bow. */
	public static final Visual ROYAL_LION_SHIP = new Visual(Ships.ROYAL_LION_SHIP, model("royal_lion_ship"),
			List.of(texture("royal_lion_ship"), texture("royal_lion_ship_sails")), 0.4f, 34, 36, true);
	/** The Fortress Ship: its sails (with their castle towers) are a texture of their own; heavy, it rocks little; foam at the bow. */
	public static final Visual FORTRESS_SHIP = new Visual(Ships.FORTRESS_SHIP, model("fortress_ship"),
			List.of(texture("fortress_ship"), texture("fortress_ship_sails")), 0.35f, 34, 36, true);
	/** The Gear Steamship: its sails (the gold gear) are a texture of their own; foam at the bow (smoke, engine: GearSteamEffects). */
	public static final Visual GEAR_STEAMSHIP = new Visual(Ships.GEAR_STEAMSHIP, model("gear_steamship"),
			List.of(texture("gear_steamship"), texture("gear_steamship_sails")), 0.45f, 32, 30, true);
	public static final List<Visual> ALL = List.of(GALLEY, GALLEON, WARSHIP, MEDIEVAL_GALLEY, STEAM_PADDLEBOAT, ELVEN_SAILBOAT,
			STEAMPUNK_AIRSHIP, NAUTILUS, OLD_CORSAIR, SKY_LEVIATHAN, CRYSTAL_AIRSHIP,
			RUSTIC_SKIFF, DRAGON_JUNK, HOT_AIR_BALLOON, BLUE_FRIGATE, ROWBOAT, TRADE_SLOOP, ROYAL_LION_SHIP,
			FORTRESS_SHIP, GEAR_STEAMSHIP);

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

	/** Gangplank plank models by ship id ({@code gangplank_<id>.bbmodel}) and lever models by style. */
	private static final Map<String, BbModel> GANGPLANKS = new java.util.HashMap<>();
	private static final Map<String, BbModel> LEVERS = new java.util.HashMap<>();
	/** The shared atlas of every gangplank and lever (tools/gangplank/gangplanklib.py). */
	public static final Identifier GANGPLANK_TEXTURE = texture("gangplank");

	/** The plank model of a ship type with a gangplank, or null. */
	@Nullable
	public static BbModel gangplank(String shipId) {
		return GANGPLANKS.get(shipId);
	}

	/**
	 * Reused poses of each plank model: [0] its wings hidden (the segments' centre strips), [1] its handrails hidden (the
	 * wings), [2] nothing hidden (the handrails).
	 */
	private static final Map<String, BbModel.Pose[]> GANGPLANK_POSES = new java.util.HashMap<>();

	/** The two poses the renderer draws a plank model with (see {@link #GANGPLANK_POSES}), or null. */
	@Nullable
	public static BbModel.Pose[] gangplankPoses(String shipId) {
		return GANGPLANK_POSES.get(shipId);
	}

	/** The deck lever model of a gangplank style, or null. */
	@Nullable
	public static BbModel lever(String style) {
		return LEVERS.get(style);
	}

	@Nullable
	private static BbModel load(ResourceManager manager, Identifier id) {
		Optional<Resource> resource = manager.getResource(id);
		if (resource.isEmpty()) {
			return null;
		}
		try (Reader reader = resource.get().getReader()) {
			return new BbModel(reader);
		} catch (Exception e) {
			MedievalShips.LOGGER.error("Could not load model {}", id, e);
			return null;
		}
	}

	/** The ship's boat stowed among the deck's elements gets a bone of its own, hidden while it is away (1.30.0). */
	@Nullable
	private static BbModel.Split boatSplit(String shipId) {
		fr.medievalships.core.ShipBoats.Spec boat = fr.medievalships.core.ShipBoats.of(shipId);
		return boat == null || boat.splitParent() == null ? null
				: new BbModel.Split(boat.splitParent(), boat.bone(), fr.medievalships.core.ShipBoats.SPLIT_PREFIX, fr.medievalships.core.ShipBoats.SPLIT_KEEP);
	}

	public static void reload(ResourceManager manager) {
		GANGPLANKS.clear();
		GANGPLANK_POSES.clear();
		LEVERS.clear();
		for (Visual v : ALL) {
			fr.medievalships.core.Gangplank.Spec spec = fr.medievalships.core.Gangplank.of(v.type().id());
			if (spec == null) {
				continue;
			}
			BbModel plank = load(manager, model("gangplank_" + v.type().id()));
			if (plank == null) {
				MedievalShips.LOGGER.error("Missing gangplank model for {}", v.type().id());
			} else {
				GANGPLANKS.put(v.type().id(), plank);
				BbModel.Pose strips = plank.newPose();
				BbModel.Pose wings = plank.newPose();
				for (int k = 0; k < fr.medievalships.core.Gangplank.MAX_SEGMENTS; k++) {
					for (int side = 0; side < 2; side++) {
						plank.hide(strips, "wing_" + k + "_" + side);
						plank.hide(wings, "rail_" + k + "_" + side);
					}
				}
				GANGPLANK_POSES.put(v.type().id(), new BbModel.Pose[] {strips, wings, plank.newPose()});
			}
			if (!LEVERS.containsKey(spec.style())) {
				BbModel lever = load(manager, model("gangplank_lever_" + spec.style()));
				if (lever != null) {
					LEVERS.put(spec.style(), lever);
				}
			}
		}
		LOADED.clear();
		for (Visual v : ALL) {
			Optional<Resource> resource = manager.getResource(v.model());
			if (resource.isEmpty()) {
				MedievalShips.LOGGER.error("Missing ship model {}", v.model());
				continue;
			}
			try (Reader reader = resource.get().getReader()) {
				BbModel m = new BbModel(reader, boatSplit(v.type().id()));
				LOADED.put(v, m);
				MedievalShips.LOGGER.info("Loaded ship model {}: {} bones, {} faces, {} animations",
						v.type().id(), m.bones.size(), m.quadCount(), m.animations.size());
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Could not load ship model {}", v.model(), e);
			}
		}
	}
}
