package fr.medievalships.command;

import java.util.Collection;
import java.util.Locale;
import java.util.Map;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import org.jetbrains.annotations.Nullable;

import net.minecraft.command.CommandSource;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Gait;
import fr.medievalships.core.Route;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Waypoint;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.NautilusFittings;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipPlacement;
import fr.medievalships.entity.ShipTracker;

/** {@code /ship ...} administration commands. See docs/COMMANDES.md. */
public final class ShipCommands {
	private ShipCommands() {
	}

	private static final SuggestionProvider<ServerCommandSource> ROUTES = (ctx, builder) ->
			CommandSource.suggestMatching(ShipData.get(ctx.getSource().getServer()).routes().keySet().stream(), builder);
	private static final SuggestionProvider<ServerCommandSource> GAITS = (ctx, builder) ->
			CommandSource.suggestMatching(new String[] {"lente", "normale", "rapide"}, builder);
	private static final SuggestionProvider<ServerCommandSource> MODES = (ctx, builder) ->
			CommandSource.suggestMatching(new String[] {"pingpong", "loop", "once"}, builder);

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		LiteralArgumentBuilder<ServerCommandSource> root = CommandManager.literal("ship")
				.requires(ShipPermissions::isAdmin);

		// /ship give [type] [targets]   /ship spawn [type]   (type: galley | galleon, galley by default)
		var give = CommandManager.literal("give")
				.executes(ctx -> give(ctx, Ships.GALLEY, java.util.List.of(ctx.getSource().getPlayerOrThrow())))
				.then(CommandManager.argument("targets", EntityArgumentType.players())
						.executes(ctx -> give(ctx, Ships.GALLEY, EntityArgumentType.getPlayers(ctx, "targets"))));
		var spawn = CommandManager.literal("spawn").executes(ctx -> spawn(ctx, Ships.GALLEY));
		for (ShipType type : Ships.ALL) {
			give.then(CommandManager.literal(type.id())
					.executes(ctx -> give(ctx, type, java.util.List.of(ctx.getSource().getPlayerOrThrow())))
					.then(CommandManager.argument("targets", EntityArgumentType.players())
							.executes(ctx -> give(ctx, type, EntityArgumentType.getPlayers(ctx, "targets")))));
			spawn.then(CommandManager.literal(type.id()).executes(ctx -> spawn(ctx, type)));
		}
		for (java.util.Map.Entry<String, ShipType> alias : Ships.ALIASES.entrySet()) {
			ShipType type = alias.getValue();
			give.then(CommandManager.literal(alias.getKey())
					.executes(ctx -> give(ctx, type, java.util.List.of(ctx.getSource().getPlayerOrThrow())))
					.then(CommandManager.argument("targets", EntityArgumentType.players())
							.executes(ctx -> give(ctx, type, EntityArgumentType.getPlayers(ctx, "targets")))));
			spawn.then(CommandManager.literal(alias.getKey()).executes(ctx -> spawn(ctx, type)));
		}
		root.then(give);
		root.then(spawn);
		root.then(CommandManager.literal("remove").executes(ShipCommands::remove));
		root.then(CommandManager.literal("list").executes(ShipCommands::list));
		root.then(CommandManager.literal("info").executes(ShipCommands::info));
		root.then(CommandManager.literal("unstuck").executes(ShipCommands::unstuck));
		root.then(CommandManager.literal("reload").executes(ctx -> {
			ConfigManager.load();
			ok(ctx, "Configuration rechargée (" + ConfigManager.path().getFileName() + ").");
			return 1;
		}));
		root.then(CommandManager.literal("name")
				.then(CommandManager.argument("name", StringArgumentType.greedyString()).executes(ctx -> {
					ShipEntity ship = target(ctx);
					String name = StringArgumentType.getString(ctx, "name");
					ship.setCustomName(Text.literal(name));
					ok(ctx, "Navire renommé : " + name);
					return 1;
				})));
		root.then(CommandManager.literal("speed")
				.then(CommandManager.literal("reset").executes(ctx -> {
					target(ctx).setSpeedLimit(-1);
					ok(ctx, "Vitesse : allures de la configuration.");
					return 1;
				}))
				.then(CommandManager.argument("gait", StringArgumentType.word()).suggests(GAITS).executes(ShipCommands::gait))
				.then(CommandManager.argument("blocksPerSecond", DoubleArgumentType.doubleArg(0.1, 40)).executes(ctx -> {
					double v = DoubleArgumentType.getDouble(ctx, "blocksPerSecond");
					target(ctx).setSpeedLimit(v);
					ok(ctx, String.format(Locale.ROOT, "Vitesse maximale du navire : %.1f blocs/s.", v));
					return 1;
				})));
		root.then(CommandManager.literal("ai")
				.then(CommandManager.literal("enable").executes(ctx -> setAi(ctx, true)))
				.then(CommandManager.literal("disable").executes(ctx -> setAi(ctx, false))));
		root.then(CommandManager.literal("captain")
				.then(CommandManager.literal("add").executes(ShipCommands::captainAdd))
				.then(CommandManager.literal("remove").executes(ShipCommands::captainRemove)));

		root.then(CommandManager.literal("route")
				.then(CommandManager.literal("create")
						.then(CommandManager.argument("name", StringArgumentType.word())
								.executes(ctx -> routeCreate(ctx, "pingpong", false))
								.then(CommandManager.literal("air").executes(ctx -> routeCreate(ctx, "pingpong", true)))
								.then(CommandManager.argument("mode", StringArgumentType.word()).suggests(MODES)
										.executes(ctx -> routeCreate(ctx, StringArgumentType.getString(ctx, "mode"), false))
										.then(CommandManager.literal("air")
												.executes(ctx -> routeCreate(ctx, StringArgumentType.getString(ctx, "mode"), true))))))
				.then(CommandManager.literal("addpoint")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ctx -> addPoint(ctx, 0, null))))
				.then(CommandManager.literal("addstop")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ctx -> addPoint(ctx, ConfigManager.ship(Ships.GALLEY).aiDefaultWaitSeconds, null))
								.then(CommandManager.argument("seconds", IntegerArgumentType.integer(1, 86400))
										.executes(ctx -> addPoint(ctx, IntegerArgumentType.getInteger(ctx, "seconds"), null))
										.then(CommandManager.argument("label", StringArgumentType.greedyString())
												.executes(ctx -> addPoint(ctx, IntegerArgumentType.getInteger(ctx, "seconds"),
														StringArgumentType.getString(ctx, "label")))))))
				.then(CommandManager.literal("edit")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.then(CommandManager.argument("index", IntegerArgumentType.integer(1))
										.then(CommandManager.literal("yaw")
												.then(CommandManager.argument("degrees", DoubleArgumentType.doubleArg(-360, 360))
														.executes(ctx -> editPoint(ctx, "yaw", DoubleArgumentType.getDouble(ctx, "degrees"))))
												.then(CommandManager.literal("here").executes(ctx -> editPoint(ctx, "yaw",
														ctx.getSource().getRotation().y))))
										.then(CommandManager.literal("speed")
												.then(CommandManager.argument("blocksPerSecond", DoubleArgumentType.doubleArg(0.1, 40))
														.executes(ctx -> editPoint(ctx, "speed", DoubleArgumentType.getDouble(ctx, "blocksPerSecond")))))
										.then(CommandManager.literal("altitude")
												.then(CommandManager.argument("y", DoubleArgumentType.doubleArg(-64, 2000))
														.executes(ctx -> editPoint(ctx, "altitude", DoubleArgumentType.getDouble(ctx, "y")))))
										.then(CommandManager.literal("profondeur")
												.then(CommandManager.argument("blocks", DoubleArgumentType.doubleArg(0, 256))
														.executes(ctx -> editPoint(ctx, "depth", DoubleArgumentType.getDouble(ctx, "blocks")))))
										.then(CommandManager.literal("depth")
												.then(CommandManager.argument("blocks", DoubleArgumentType.doubleArg(0, 256))
														.executes(ctx -> editPoint(ctx, "depth", DoubleArgumentType.getDouble(ctx, "blocks")))))
										.then(CommandManager.literal("wait")
												.then(CommandManager.argument("seconds", IntegerArgumentType.integer(0, 86400))
														.executes(ctx -> editPoint(ctx, "wait", IntegerArgumentType.getInteger(ctx, "seconds")))))
										.then(CommandManager.literal("clear").executes(ctx -> editPoint(ctx, "clear", 0))))))
				.then(CommandManager.literal("removepoint")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.then(CommandManager.argument("index", IntegerArgumentType.integer(1))
										.executes(ShipCommands::removePoint))))
				.then(CommandManager.literal("mode")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.then(CommandManager.argument("mode", StringArgumentType.word()).suggests(MODES)
										.executes(ShipCommands::routeMode))))
				.then(CommandManager.literal("delete")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ShipCommands::routeDelete)))
				.then(CommandManager.literal("list").executes(ShipCommands::routeList))
				.then(CommandManager.literal("info")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ShipCommands::routeInfo)))
				.then(CommandManager.literal("show")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ShipCommands::routeShow)))
				.then(CommandManager.literal("start")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ShipCommands::routeStart)))
				.then(CommandManager.literal("assign")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ShipCommands::routeStart)))
				.then(CommandManager.literal("stop").executes(ctx -> setAi(ctx, false)))
				.then(CommandManager.literal("depart").executes(ctx -> {
					ShipEntity ship = target(ctx);
					ship.autopilot().departNow();
					ok(ctx, "Départ immédiat.");
					return 1;
				})));

		// /ship nautilus ...: depth, ballasts, lights, projector, shutters, airlock, lifeboat
		var nautilus = CommandManager.literal("nautilus");
		for (String word : new String[] {"profondeur", "depth"}) {
			nautilus.then(CommandManager.literal(word)
					.then(CommandManager.literal("surface").executes(ctx -> depth(ctx, 0)))
					.then(CommandManager.literal("libre").executes(ctx -> depth(ctx, Double.NaN)))
					.then(CommandManager.argument("blocks", DoubleArgumentType.doubleArg(0, 256))
							.executes(ctx -> depth(ctx, DoubleArgumentType.getDouble(ctx, "blocks")))));
		}
		for (String word : new String[] {"ballasts", "ballast"}) {
			nautilus.then(CommandManager.literal(word)
					.then(CommandManager.literal("remplir").executes(ctx -> depth(ctx, Double.POSITIVE_INFINITY)))
					.then(CommandManager.literal("fill").executes(ctx -> depth(ctx, Double.POSITIVE_INFINITY)))
					.then(CommandManager.literal("vider").executes(ctx -> depth(ctx, 0)))
					.then(CommandManager.literal("empty").executes(ctx -> depth(ctx, 0))));
		}
		for (String[] t : new String[][] {{"lumieres", "lights"}, {"projecteur", "floodlight"}, {"volets", "shutters"}}) {
			for (String word : t) {
				nautilus.then(CommandManager.literal(word)
						.then(CommandManager.literal("on").executes(ctx -> fitting(ctx, t[1], true)))
						.then(CommandManager.literal("off").executes(ctx -> fitting(ctx, t[1], false))));
			}
		}
		nautilus.then(CommandManager.literal("sas")
				.then(CommandManager.literal("remplir").executes(ctx -> airlock(ctx, true)))
				.then(CommandManager.literal("vider").executes(ctx -> airlock(ctx, false))));
		nautilus.then(CommandManager.literal("canot")
				.then(CommandManager.literal("lancer").executes(ctx -> lifeboat(ctx, 0)))
				.then(CommandManager.literal("rembarquer").executes(ctx -> lifeboat(ctx, 1)))
				.then(CommandManager.literal("remplacer").executes(ctx -> lifeboat(ctx, 2))));
		nautilus.then(CommandManager.literal("porte")
				.then(CommandManager.argument("index", IntegerArgumentType.integer(0, 31))
						.then(CommandManager.literal("ouvrir").executes(ctx -> door(ctx, true)))
						.then(CommandManager.literal("fermer").executes(ctx -> door(ctx, false)))));
		nautilus.then(CommandManager.literal("etat").executes(ShipCommands::nautilusState));
		root.then(nautilus);

		dispatcher.register(root);
	}

	// ------------------------------------------------------------------ nautilus

	private static ShipEntity submarine(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		if (!ship.geometry().submarine() || ship.geometry().interior() == null) {
			throw error("Ce navire n'est pas le Nautilus.");
		}
		return ship;
	}

	private static void report(CommandContext<ServerCommandSource> ctx, @Nullable Text msg, String fallback) {
		Text m = msg == null ? Text.literal(fallback).formatted(Formatting.GREEN) : msg;
		ctx.getSource().sendFeedback(() -> m, true);
	}

	/** NaN: no ordered depth (the pilot's keys); infinity: ballasts full (down to the bottom or the deepest dive). */
	private static int depth(CommandContext<ServerCommandSource> ctx, double depth) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		double max = ship.config().dive.maxDepth;
		double d = Double.isInfinite(depth) ? max : Double.isNaN(depth) ? Double.NaN : Math.min(depth, max);
		ship.setTargetDepth(d);
		if (d > 0 && (ship.doorOpen(Ships.NautilusLayout.HATCH_DOOR) || ship.doorOpen(Ships.NautilusLayout.BOAT_HATCH_DOOR))) {
			ok(ctx, "Ordre noté, mais un panneau est ouvert : le Nautilus ne plongera qu'une fois fermé.");
			return 1;
		}
		ok(ctx, Double.isNaN(d) ? "Profondeur libre : le pilote commande les ballasts."
				: d == 0 ? "Ballasts vidés : le Nautilus remonte à la surface."
				: Double.isInfinite(depth) ? String.format(Locale.ROOT, "Ballasts remplis : le Nautilus descend jusqu'au fond (au plus %.0f m).", d)
				: String.format(Locale.ROOT, "Profondeur ordonnée : %.0f m.", d));
		return 1;
	}

	private static int fitting(CommandContext<ServerCommandSource> ctx, String what, boolean on) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		switch (what) {
			case "lights" -> ship.setToggle(Ships.NautilusLayout.LIGHTS_OFF, !on);
			case "floodlight" -> ship.setToggle(Ships.NautilusLayout.FLOODLIGHT_ON, on);
			default -> ship.setToggle(Ships.NautilusLayout.SHUTTERS_CLOSED, !on);
		}
		ok(ctx, switch (what) {
			case "lights" -> on ? "Lumières allumées." : "Lumières éteintes.";
			case "floodlight" -> on ? "Projecteur allumé." : "Projecteur éteint.";
			default -> on ? "Panneaux des baies ouverts." : "Panneaux des baies fermés.";
		});
		return 1;
	}

	private static int airlock(CommandContext<ServerCommandSource> ctx, boolean fill) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		report(ctx, fill ? NautilusFittings.fill(ship) : NautilusFittings.pump(ship), "");
		return 1;
	}

	private static int lifeboat(CommandContext<ServerCommandSource> ctx, int what) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		ServerWorld world = ctx.getSource().getWorld();
		boolean away = ship.toggle(Ships.NautilusLayout.LIFEBOAT_AWAY);
		if (what == 0 && away) {
			throw error("Le canot est déjà à l'eau.");
		}
		if (what == 1 && !away) {
			throw error("Le canot est déjà dans son logement.");
		}
		report(ctx, what == 0 ? NautilusFittings.launchLifeboat(ship, world) : NautilusFittings.recoverLifeboat(ship, world, what == 2), "");
		return 1;
	}

	private static int door(CommandContext<ServerCommandSource> ctx, boolean open) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		int k = IntegerArgumentType.getInteger(ctx, "index");
		if (ship.geometry().interior().doorCenter(k) == null) {
			throw error("Pas de porte " + k + ".");
		}
		if (ship.doorOpen(k) == open) {
			ok(ctx, open ? "Déjà ouverte." : "Déjà fermée.");
			return 1;
		}
		report(ctx, ship.toggleDoor(k), open ? "Porte " + k + " ouverte." : "Porte " + k + " fermée.");
		return 1;
	}

	private static int nautilusState(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = submarine(ctx);
		StringBuilder open = new StringBuilder();
		for (int k = 0; k < fr.medievalships.core.InteriorGrid.MAX_DOORS; k++) {
			if (ship.doorOpen(k)) {
				open.append(open.length() == 0 ? "" : ",").append(k);
			}
		}
		String msg = String.format(Locale.ROOT,
				"Profondeur %.1f m (ordre : %s) - sas %d %% - portes ouvertes : %s - lumières %s - projecteur %s - panneaux %s - canot %s",
				ship.syncedDepth(), Double.isNaN(ship.targetDepth()) ? "libre" : String.format(Locale.ROOT, "%.0f m", ship.targetDepth()),
				Math.round(ship.airlockLevel() * 100), open.length() == 0 ? "aucune" : open,
				ship.toggle(Ships.NautilusLayout.LIGHTS_OFF) ? "éteintes" : "allumées",
				ship.toggle(Ships.NautilusLayout.FLOODLIGHT_ON) ? "allumé" : "éteint",
				ship.toggle(Ships.NautilusLayout.SHUTTERS_CLOSED) ? "fermés" : "ouverts",
				ship.toggle(Ships.NautilusLayout.LIFEBOAT_AWAY) ? "à l'eau" : "à bord");
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GOLD), false);
		return 1;
	}

	// ------------------------------------------------------------------ helpers

	private static void ok(CommandContext<ServerCommandSource> ctx, String msg) {
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GREEN), true);
	}

	private static CommandSyntaxException error(String msg) {
		return new com.mojang.brigadier.exceptions.SimpleCommandExceptionType(Text.literal(msg)).create();
	}

	/**
	 * The ship the command applies to: the one the player rides or stands on, else the one
	 * he looks at, else the nearest one within 32 blocks.
	 */
	private static ShipEntity target(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		ServerWorld world = source.getWorld();
		Entity entity = source.getEntity();
		if (entity != null) {
			if (entity.getVehicle() instanceof ShipEntity ship) {
				return ship;
			}
			ShipEntity under = ShipTracker.shipUnder(entity);
			if (under != null) {
				return under;
			}
			Vec3d eye = entity.getEyePos();
			Vec3d look = entity.getRotationVector();
			ShipEntity best = null;
			double bestDist = 64;
			for (ShipEntity ship : ShipTracker.ships(world)) {
				ShipGeometry.Pick pick = ship.geometry().pick(ship.pose(), eye.x, eye.y, eye.z, look.x, look.y, look.z, 64);
				if (pick != null && pick.distance() < bestDist) {
					best = ship;
					bestDist = pick.distance();
				}
			}
			if (best != null) {
				return best;
			}
		}
		Vec3d pos = source.getPosition();
		ShipEntity nearest = null;
		double nd = 32 * 32;
		for (ShipEntity ship : ShipTracker.ships(world)) {
			double d = ship.squaredDistanceTo(pos);
			if (d < nd) {
				nd = d;
				nearest = ship;
			}
		}
		if (nearest == null) {
			throw error("Aucun navire ciblé : montez à bord, regardez-en un ou approchez-vous (32 blocs).");
		}
		return nearest;
	}

	private static Route route(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String name = StringArgumentType.getString(ctx, "name");
		Route r = ShipData.get(ctx.getSource().getServer()).route(name);
		if (r == null) {
			throw error("Itinéraire inconnu : " + name);
		}
		return r;
	}

	private static String describe(ShipEntity ship) {
		String name = ship.hasCustomName() ? ship.getCustomName().getString() : capitalize(ship.shipType().frenchName());
		return String.format(Locale.ROOT, "%s [%d %d %d]", name, (int) ship.getX(), (int) ship.getY(), (int) ship.getZ());
	}

	// ------------------------------------------------------------------ ships

	private static int give(CommandContext<ServerCommandSource> ctx, ShipType type, Collection<ServerPlayerEntity> players) {
		for (ServerPlayerEntity p : players) {
			p.getInventory().offerOrDrop(new ItemStack(MedievalShips.item(type)));
		}
		ok(ctx, capitalize(type.frenchName()) + " donné(e) à " + players.size() + " joueur(s).");
		return players.size();
	}

	private static String capitalize(String s) {
		return s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1);
	}

	private static int spawn(CommandContext<ServerCommandSource> ctx, ShipType type) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		Vec3d pos = source.getPosition();
		float yaw = source.getRotation().y;
		ShipEntity ship = ShipPlacement.place(source.getWorld(), type, pos.x, pos.y, pos.z, yaw, false);
		if (ship == null) {
			throw error(String.format(Locale.ROOT, "Pas assez d'eau libre ici pour %s (il faut ~%d x %d blocs d'eau profonde de 2 blocs).",
					type.frenchName(), (int) Math.ceil(2 * type.hull().tip + 3), (int) Math.ceil(2 * type.hull().maxHalfWidth + 1)));
		}
		ok(ctx, "Navire mis à l'eau : " + describe(ship));
		return 1;
	}

	private static int remove(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		String d = describe(ship);
		ship.removeAllPassengers();
		ship.discard();
		ok(ctx, "Navire supprimé : " + d);
		return 1;
	}

	private static int list(CommandContext<ServerCommandSource> ctx) {
		ServerCommandSource source = ctx.getSource();
		int n = 0;
		for (ServerWorld world : source.getServer().getWorlds()) {
			for (ShipEntity ship : ShipTracker.ships(world)) {
				n++;
				String ai = ship.isAutopilotEnabled() ? " pilote auto: " + ship.routeName() + " (" + ship.autopilot().phase + ")" : "";
				String line = "- " + describe(ship) + " " + world.getRegistryKey().getValue() + ai;
				source.sendFeedback(() -> Text.literal(line), false);
			}
		}
		Map<String, ShipData.FerryRecord> ferries = ShipData.get(source.getServer()).ferries();
		for (Map.Entry<String, ShipData.FerryRecord> e : ferries.entrySet()) {
			ShipData.FerryRecord r = e.getValue();
			String line = String.format(Locale.ROOT, "  (navire automatique %s, dernière position %d %d, itinéraire %s)",
					e.getKey().substring(0, 8), (int) r.x, (int) r.z, r.route);
			source.sendFeedback(() -> Text.literal(line).formatted(Formatting.GRAY), false);
		}
		int total = n;
		source.sendFeedback(() -> Text.literal(total + " navire(s) chargé(s).").formatted(Formatting.GREEN), false);
		return n;
	}

	private static int info(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		String limit = Double.isNaN(ship.speedLimit()) ? "allures" : String.format(Locale.ROOT, "%.1f blocs/s", ship.speedLimit());
		String text = String.format(Locale.ROOT,
				"%s%nvitesse %.2f blocs/s, cap %.0f, barre %.2f, allure %s, limite %s%npilote auto %s, itinéraire %s, phase %s, cible %d, attente %d s%npassagers %d/%d",
				describe(ship), ship.physics().speed, ship.getYaw(), ship.physics().helm, ship.gait().frenchName(), limit,
				ship.isAutopilotEnabled() ? "oui" : "non", ship.routeName(), ship.autopilot().phase,
				ship.autopilot().target + 1, ship.autopilot().waitTicks / 20,
				ship.getPassengerList().size(), ship.geometry().seats().size());
		ctx.getSource().sendFeedback(() -> Text.literal(text), false);
		return 1;
	}

	private static int unstuck(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		if (!ShipPlacement.unstuck(ship)) {
			throw error("Aucune eau libre trouvée dans un rayon de 24 blocs.");
		}
		ok(ctx, "Navire dégagé : " + describe(ship));
		return 1;
	}

	private static int gait(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Gait g = Gait.byName(StringArgumentType.getString(ctx, "gait"));
		if (g == null) {
			throw error("Allure inconnue (lente, normale, rapide).");
		}
		ShipEntity ship = target(ctx);
		ship.setGait(g);
		ship.setSpeedLimit(-1);
		ok(ctx, "Allure " + g.frenchName() + String.format(Locale.ROOT, " (%.1f blocs/s).", ship.config().gaitSpeed(g)));
		return 1;
	}

	private static int setAi(CommandContext<ServerCommandSource> ctx, boolean enabled) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		if (enabled && ship.routeName() == null) {
			throw error("Ce navire n'a pas d'itinéraire : /ship route start <nom>.");
		}
		ship.setAutopilot(enabled);
		ok(ctx, enabled ? "Pilote automatique activé (" + ship.routeName() + ")." : "Pilote automatique désactivé, le navire s'arrête.");
		return 1;
	}

	private static int captainAdd(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		if (ship.passengerInSeat(ShipGeometry.PILOT_SEAT) != null) {
			throw error("La barre est déjà occupée.");
		}
		MobEntity captain = EntityType.VILLAGER.create(ctx.getSource().getWorld(), SpawnReason.COMMAND);
		if (captain == null) {
			throw error("Impossible de créer le capitaine.");
		}
		captain.refreshPositionAndAngles(ship.getX(), ship.getY() + 1, ship.getZ(), ship.getYaw(), 0);
		captain.setAiDisabled(true);
		captain.setInvulnerable(true);
		captain.setSilent(true);
		captain.setPersistent();
		captain.setCustomName(Text.literal("Capitaine"));
		captain.addCommandTag("medievalships_captain");
		ctx.getSource().getWorld().spawnEntity(captain);
		if (!ship.seat(captain, ShipGeometry.PILOT_SEAT)) {
			captain.discard();
			throw error("Impossible d'installer le capitaine.");
		}
		ok(ctx, "Capitaine PNJ installé à la barre.");
		return 1;
	}

	private static int captainRemove(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ShipEntity ship = target(ctx);
		Entity pilot = ship.passengerInSeat(ShipGeometry.PILOT_SEAT);
		if (pilot == null || pilot instanceof ServerPlayerEntity) {
			throw error("Pas de capitaine PNJ à bord.");
		}
		pilot.stopRiding();
		if (pilot.getCommandTags().contains("medievalships_captain")) {
			pilot.discard();
		}
		ok(ctx, "Capitaine retiré.");
		return 1;
	}

	// ------------------------------------------------------------------ routes

	private static int routeCreate(CommandContext<ServerCommandSource> ctx, String modeName, boolean air) throws CommandSyntaxException {
		String name = StringArgumentType.getString(ctx, "name");
		ShipData data = ShipData.get(ctx.getSource().getServer());
		if (data.route(name) != null) {
			throw error("L'itinéraire " + name + " existe déjà (/ship route delete " + name + ").");
		}
		Route.Mode mode = Route.Mode.byName(modeName);
		if (mode == null) {
			throw error("Mode inconnu : pingpong (aller-retour), loop (boucle), once (aller simple).");
		}
		Route route = new Route(name, ctx.getSource().getWorld().getRegistryKey().getValue().toString());
		route.mode = mode;
		route.air = air;
		data.putRoute(route);
		ok(ctx, "Itinéraire " + (air ? "aérien " : "") + name + " créé (" + mode.name().toLowerCase(Locale.ROOT)
				+ "). Ajoutez des points avec /ship route addstop|addpoint " + name
				+ (air ? " (à l'endroit et à la hauteur où doit se trouver le pont de la nacelle)" : ""));
		return 1;
	}

	private static int addPoint(CommandContext<ServerCommandSource> ctx, int waitSeconds, @Nullable String label) throws CommandSyntaxException {
		Route route = route(ctx);
		ServerCommandSource source = ctx.getSource();
		String dim = source.getWorld().getRegistryKey().getValue().toString();
		if (!dim.equals(route.dimension)) {
			throw error("Cet itinéraire est dans la dimension " + route.dimension);
		}
		Vec3d p = source.getPosition();
		Waypoint w = new Waypoint(Math.round(p.x * 10) / 10.0, Math.round(p.y * 10) / 10.0, Math.round(p.z * 10) / 10.0, waitSeconds, label);
		if (route.air && waitSeconds > 0) {
			// an airship turns to the heading the administrator faced when creating the stop
			w.yaw = (double) Math.round(source.getRotation().y);
		}
		route.points.add(w);
		ShipData.get(source.getServer()).putRoute(route);
		int idx = route.size();
		ok(ctx, String.format(Locale.ROOT, route.air ? "Point %d ajouté à %s : %.1f %.1f %.1f%s" : "Point %d ajouté à %s : %.1f %.1f%s",
				route.air ? new Object[] {idx, route.name, w.x, w.y, w.z, w.isStop() ? " (escale " + (label == null ? "" : label + ", ")
						+ waitSeconds + " s, cap " + Math.round(w.yaw) + ")" : ""} : new Object[] {idx, route.name, w.x, w.z,
				w.isStop() ? " (escale " + (label == null ? "" : label + ", ") + waitSeconds + " s)" : ""}));
		return idx;
	}

	/** Options of one point: heading at the stop, speed of the leg, altitude, waiting time. */
	private static int editPoint(CommandContext<ServerCommandSource> ctx, String what, double value) throws CommandSyntaxException {
		Route route = route(ctx);
		int index = IntegerArgumentType.getInteger(ctx, "index");
		if (index > route.size()) {
			throw error("L'itinéraire n'a que " + route.size() + " point(s).");
		}
		Waypoint w = route.points.get(index - 1);
		String msg;
		switch (what) {
			case "yaw" -> {
				w.yaw = (double) Math.round(ShipPose.wrapDegrees(value));
				msg = "cap à l'escale " + Math.round(w.yaw) + "°";
			}
			case "speed" -> {
				w.speed = value;
				msg = String.format(Locale.ROOT, "vitesse %.1f blocs/s jusqu'à ce point", value);
			}
			case "altitude" -> {
				w.y = value;
				msg = String.format(Locale.ROOT, "altitude du pont %.1f", value);
			}
			case "depth" -> {
				w.depth = value;
				msg = value < 0.5 ? "sous-marin : en surface jusqu'à ce point" : String.format(Locale.ROOT, "sous-marin : %.0f m de profondeur jusqu'à ce point", value);
			}
			case "wait" -> {
				w.waitSeconds = (int) value;
				msg = value > 0 ? "escale de " + (int) value + " s" : "simple point de passage";
			}
			default -> {
				w.yaw = null;
				w.speed = null;
				w.depth = null;
				msg = "cap, vitesse et profondeur effacés";
			}
		}
		ShipData.get(ctx.getSource().getServer()).putRoute(route);
		ok(ctx, "Point " + index + " de " + route.name + " : " + msg + ".");
		return 1;
	}

	private static int removePoint(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		int index = IntegerArgumentType.getInteger(ctx, "index");
		if (index > route.size()) {
			throw error("L'itinéraire n'a que " + route.size() + " point(s).");
		}
		route.points.remove(index - 1);
		ShipData.get(ctx.getSource().getServer()).putRoute(route);
		ok(ctx, "Point " + index + " supprimé.");
		return 1;
	}

	private static int routeMode(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		Route.Mode mode = Route.Mode.byName(StringArgumentType.getString(ctx, "mode"));
		if (mode == null) {
			throw error("Mode inconnu : pingpong, loop, once.");
		}
		route.mode = mode;
		ShipData.get(ctx.getSource().getServer()).putRoute(route);
		ok(ctx, "Mode de " + route.name + " : " + mode.name().toLowerCase(Locale.ROOT));
		return 1;
	}

	private static int routeDelete(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		ShipData.get(ctx.getSource().getServer()).removeRoute(route.name);
		ok(ctx, "Itinéraire " + route.name + " supprimé.");
		return 1;
	}

	private static int routeList(CommandContext<ServerCommandSource> ctx) {
		Map<String, Route> routes = ShipData.get(ctx.getSource().getServer()).routes();
		if (routes.isEmpty()) {
			ctx.getSource().sendFeedback(() -> Text.literal("Aucun itinéraire."), false);
		}
		for (Route r : routes.values()) {
			String line = String.format(Locale.ROOT, "- %s%s : %d points, %.0f blocs, %s, %s", r.name, r.air ? " (aérien)" : "", r.size(),
					r.totalLength(), r.mode.name().toLowerCase(Locale.ROOT), r.dimension);
			ctx.getSource().sendFeedback(() -> Text.literal(line), false);
		}
		return routes.size();
	}

	private static int routeInfo(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		ctx.getSource().sendFeedback(() -> Text.literal(String.format(Locale.ROOT, "%s (%s, %s, %.0f blocs)", route.name,
				route.mode.name().toLowerCase(Locale.ROOT), route.dimension, route.totalLength())).formatted(Formatting.GOLD), false);
		for (int i = 0; i < route.size(); i++) {
			Waypoint w = route.get(i);
			String line = String.format(Locale.ROOT, " %d. %.1f %.1f %.1f%s%s%s%s", i + 1, w.x, w.y, w.z,
					w.isStop() ? " escale " + w.label(i) + " (" + w.waitSeconds + " s)" : "",
					w.yaw != null ? " cap " + Math.round(w.yaw) + "°" : "",
					w.speed != null ? String.format(Locale.ROOT, " %.1f blocs/s", w.speed) : "",
					w.depth != null ? String.format(Locale.ROOT, " profondeur %.0f m", w.depth) : "");
			ctx.getSource().sendFeedback(() -> Text.literal(line), false);
		}
		return route.size();
	}

	private static int routeShow(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		ServerWorld world = ctx.getSource().getWorld();
		for (int i = 0; i < route.size(); i++) {
			Waypoint w = route.get(i);
			world.spawnParticles(w.isStop() ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.END_ROD, w.x, w.y + 1, w.z, 40, 0.3, 2, 0.3, 0.01);
			if (i > 0) {
				Waypoint a = route.get(i - 1);
				double len = Math.hypot(w.x - a.x, w.z - a.z);
				for (double t = 0; t < len; t += 2) {
					double f = t / len;
					world.spawnParticles(ParticleTypes.END_ROD, a.x + (w.x - a.x) * f, a.y + (w.y - a.y) * f + 1, a.z + (w.z - a.z) * f, 1, 0, 0, 0, 0);
				}
			}
		}
		ok(ctx, "Itinéraire " + route.name + " affiché.");
		return 1;
	}

	private static int routeStart(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Route route = route(ctx);
		if (route.size() < 2) {
			throw error("Il faut au moins 2 points (de préférence des escales aux extrémités).");
		}
		ShipEntity ship = target(ctx);
		if (route.air != ship.geometry().flying()) {
			throw error(route.air ? "C'est un itinéraire aérien : seul un dirigeable peut le suivre."
					: "C'est un itinéraire maritime : un dirigeable a besoin d'un itinéraire aérien (/ship route create <nom> [mode] air).");
		}
		if (!ship.getEntityWorld().getRegistryKey().getValue().toString().equals(route.dimension)) {
			throw error("Le navire n'est pas dans la dimension de l'itinéraire.");
		}
		ship.startRoute(route);
		ok(ctx, describe(ship) + " suit maintenant l'itinéraire " + route.name + " (" + ship.autopilot().phase + ").");
		return 1;
	}
}
