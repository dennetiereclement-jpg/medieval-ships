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
import fr.medievalships.core.Waypoint;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.GalleyEntity;
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

		root.then(CommandManager.literal("give")
				.executes(ctx -> give(ctx, java.util.List.of(ctx.getSource().getPlayerOrThrow())))
				.then(CommandManager.argument("targets", EntityArgumentType.players())
						.executes(ctx -> give(ctx, EntityArgumentType.getPlayers(ctx, "targets")))));

		root.then(CommandManager.literal("spawn").executes(ShipCommands::spawn));
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
					GalleyEntity ship = target(ctx);
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
								.executes(ctx -> routeCreate(ctx, "pingpong"))
								.then(CommandManager.argument("mode", StringArgumentType.word()).suggests(MODES)
										.executes(ctx -> routeCreate(ctx, StringArgumentType.getString(ctx, "mode"))))))
				.then(CommandManager.literal("addpoint")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ctx -> addPoint(ctx, 0, null))))
				.then(CommandManager.literal("addstop")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(ROUTES)
								.executes(ctx -> addPoint(ctx, ConfigManager.get().aiDefaultWaitSeconds, null))
								.then(CommandManager.argument("seconds", IntegerArgumentType.integer(1, 86400))
										.executes(ctx -> addPoint(ctx, IntegerArgumentType.getInteger(ctx, "seconds"), null))
										.then(CommandManager.argument("label", StringArgumentType.greedyString())
												.executes(ctx -> addPoint(ctx, IntegerArgumentType.getInteger(ctx, "seconds"),
														StringArgumentType.getString(ctx, "label")))))))
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
				.then(CommandManager.literal("stop").executes(ctx -> setAi(ctx, false)))
				.then(CommandManager.literal("depart").executes(ctx -> {
					GalleyEntity ship = target(ctx);
					ship.autopilot().departNow();
					ok(ctx, "Départ immédiat.");
					return 1;
				})));

		dispatcher.register(root);
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
	private static GalleyEntity target(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		ServerWorld world = source.getWorld();
		Entity entity = source.getEntity();
		if (entity != null) {
			if (entity.getVehicle() instanceof GalleyEntity ship) {
				return ship;
			}
			GalleyEntity under = ShipTracker.shipUnder(entity);
			if (under != null) {
				return under;
			}
			Vec3d eye = entity.getEyePos();
			Vec3d look = entity.getRotationVector();
			GalleyEntity best = null;
			double bestDist = 64;
			for (GalleyEntity ship : ShipTracker.ships(world)) {
				ShipGeometry.Pick pick = ShipGeometry.pick(ship.pose(), eye.x, eye.y, eye.z, look.x, look.y, look.z, 64);
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
		GalleyEntity nearest = null;
		double nd = 32 * 32;
		for (GalleyEntity ship : ShipTracker.ships(world)) {
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

	private static String describe(GalleyEntity ship) {
		String name = ship.hasCustomName() ? ship.getCustomName().getString() : "Galère";
		return String.format(Locale.ROOT, "%s [%d %d %d]", name, (int) ship.getX(), (int) ship.getY(), (int) ship.getZ());
	}

	// ------------------------------------------------------------------ ships

	private static int give(CommandContext<ServerCommandSource> ctx, Collection<ServerPlayerEntity> players) {
		for (ServerPlayerEntity p : players) {
			p.getInventory().offerOrDrop(new ItemStack(MedievalShips.GALLEY_ITEM));
		}
		ok(ctx, "Galère donnée à " + players.size() + " joueur(s).");
		return players.size();
	}

	private static int spawn(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		Vec3d pos = source.getPosition();
		float yaw = source.getRotation().y;
		GalleyEntity ship = ShipPlacement.place(source.getWorld(), pos.x, pos.y, pos.z, yaw, false);
		if (ship == null) {
			throw error("Pas assez d'eau libre ici (il faut ~24 x 6 blocs d'eau profonde de 2 blocs).");
		}
		ok(ctx, "Navire mis à l'eau : " + describe(ship));
		return 1;
	}

	private static int remove(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		GalleyEntity ship = target(ctx);
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
			for (GalleyEntity ship : ShipTracker.ships(world)) {
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
		GalleyEntity ship = target(ctx);
		String limit = Double.isNaN(ship.speedLimit()) ? "allures" : String.format(Locale.ROOT, "%.1f blocs/s", ship.speedLimit());
		String text = String.format(Locale.ROOT,
				"%s%nvitesse %.2f blocs/s, cap %.0f, barre %.2f, allure %s, limite %s%npilote auto %s, itinéraire %s, phase %s, cible %d, attente %d s%npassagers %d/%d",
				describe(ship), ship.physics().speed, ship.getYaw(), ship.physics().helm, ship.gait().frenchName(), limit,
				ship.isAutopilotEnabled() ? "oui" : "non", ship.routeName(), ship.autopilot().phase,
				ship.autopilot().target + 1, ship.autopilot().waitTicks / 20,
				ship.getPassengerList().size(), ShipGeometry.SEATS.size());
		ctx.getSource().sendFeedback(() -> Text.literal(text), false);
		return 1;
	}

	private static int unstuck(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		GalleyEntity ship = target(ctx);
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
		GalleyEntity ship = target(ctx);
		ship.setGait(g);
		ship.setSpeedLimit(-1);
		ok(ctx, "Allure " + g.frenchName() + String.format(Locale.ROOT, " (%.1f blocs/s).", ConfigManager.get().gaitSpeed(g)));
		return 1;
	}

	private static int setAi(CommandContext<ServerCommandSource> ctx, boolean enabled) throws CommandSyntaxException {
		GalleyEntity ship = target(ctx);
		if (enabled && ship.routeName() == null) {
			throw error("Ce navire n'a pas d'itinéraire : /ship route start <nom>.");
		}
		ship.setAutopilot(enabled);
		ok(ctx, enabled ? "Pilote automatique activé (" + ship.routeName() + ")." : "Pilote automatique désactivé, le navire s'arrête.");
		return 1;
	}

	private static int captainAdd(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		GalleyEntity ship = target(ctx);
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
		GalleyEntity ship = target(ctx);
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

	private static int routeCreate(CommandContext<ServerCommandSource> ctx, String modeName) throws CommandSyntaxException {
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
		data.putRoute(route);
		ok(ctx, "Itinéraire " + name + " créé (" + mode.name().toLowerCase(Locale.ROOT)
				+ "). Ajoutez des points avec /ship route addstop|addpoint " + name);
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
		route.points.add(w);
		ShipData.get(source.getServer()).putRoute(route);
		int idx = route.size();
		ok(ctx, String.format(Locale.ROOT, "Point %d ajouté à %s : %.1f %.1f%s", idx, route.name, w.x, w.z,
				w.isStop() ? " (escale " + (label == null ? "" : label + ", ") + waitSeconds + " s)" : ""));
		return idx;
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
			String line = String.format(Locale.ROOT, "- %s : %d points, %.0f blocs, %s, %s", r.name, r.size(), r.totalLength(),
					r.mode.name().toLowerCase(Locale.ROOT), r.dimension);
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
			String line = String.format(Locale.ROOT, " %d. %.1f %.1f %.1f%s", i + 1, w.x, w.y, w.z,
					w.isStop() ? " escale " + w.label(i) + " (" + w.waitSeconds + " s)" : "");
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
					world.spawnParticles(ParticleTypes.END_ROD, a.x + (w.x - a.x) * f, a.y + 1, a.z + (w.z - a.z) * f, 1, 0, 0, 0, 0);
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
		GalleyEntity ship = target(ctx);
		if (!ship.getEntityWorld().getRegistryKey().getValue().toString().equals(route.dimension)) {
			throw error("Le navire n'est pas dans la dimension de l'itinéraire.");
		}
		ship.startRoute(route);
		ok(ctx, describe(ship) + " suit maintenant l'itinéraire " + route.name + " (" + ship.autopilot().phase + ").");
		return 1;
	}
}
