package fr.medievalships.command;

import java.util.Locale;
import java.util.Map;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;

import net.minecraft.command.CommandSource;
import net.minecraft.command.argument.Vec3ArgumentType;
import net.minecraft.entity.Entity;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.Destination;
import fr.medievalships.core.GotoRoutes;
import fr.medievalships.core.Route;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipTracker;

/**
 * Destinations for the autopilot, on top of the routes (see docs/COMMANDES.md):
 * <ul>
 * <li>{@code /ship goto <x y z>}, {@code /ship goto destination <name>}, {@code /ship goto visee}, {@code /ship goto
 * stop} (admins, the targeted vessel);</li>
 * <li>{@code /ship destination add|remove <name>}, {@code /ship destination list} (admins: saved destinations);</li>
 * <li>{@code /pilote goto ...}, {@code /pilote stop}, {@code /pilote destinations} (any player aboard a vessel,
 * if {@code playerDestinations} is on): never for a ferry on an administrator's route, never against the player at
 * the helm, at most {@code playerDestinationMaxDistance} blocks away.</li>
 * </ul>
 */
final class DestinationCommands {
	private static final double LOOK_RANGE = 512.0;

	private DestinationCommands() {
	}

	private static final SuggestionProvider<ServerCommandSource> DESTINATIONS = (ctx, builder) ->
			CommandSource.suggestMatching(ShipData.get(ctx.getSource().getServer()).destinations().keySet().stream(), builder);

	static void register(CommandDispatcher<ServerCommandSource> dispatcher, LiteralArgumentBuilder<ServerCommandSource> ship) {
		ship.then(gotoNode(true));
		ship.then(CommandManager.literal("destination")
				.then(CommandManager.literal("add")
						.then(CommandManager.argument("name", StringArgumentType.word()).executes(DestinationCommands::add)))
				.then(CommandManager.literal("remove")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(DESTINATIONS)
								.executes(DestinationCommands::remove)))
				.then(CommandManager.literal("list").executes(DestinationCommands::list)));

		dispatcher.register(CommandManager.literal("pilote")
				.requires(source -> ConfigManager.server().playerDestinations || ShipPermissions.isAdmin(source))
				.then(gotoNode(false))
				.then(CommandManager.literal("stop").executes(ctx -> stop(ctx, false)))
				.then(CommandManager.literal("destinations").executes(DestinationCommands::list)));
	}

	/** {@code goto <x y z> | goto destination <name> | goto visee | goto stop}. */
	private static LiteralArgumentBuilder<ServerCommandSource> gotoNode(boolean admin) {
		return CommandManager.literal("goto")
				.then(CommandManager.literal("stop").executes(ctx -> stop(ctx, admin)))
				.then(CommandManager.literal("destination")
						.then(CommandManager.argument("name", StringArgumentType.word()).suggests(DESTINATIONS)
								.executes(ctx -> gotoSaved(ctx, admin))))
				.then(CommandManager.literal("visee").executes(ctx -> gotoLook(ctx, admin)))
				.then(CommandManager.argument("pos", Vec3ArgumentType.vec3(false))
						.executes(ctx -> {
							Vec3d p = Vec3ArgumentType.getVec3(ctx, "pos");
							ShipEntity ship = vessel(ctx, admin);
							boolean air = ship.geometry().flying();
							return go(ctx, ship, admin, p.x, p.y, p.z, GotoRoutes.label(p.x, p.y, p.z, air));
						}));
	}

	// ------------------------------------------------------------------ which vessel

	/**
	 * The vessel a goto applies to: for an admin, the targeted one (as every /ship command); for a player, the one he
	 * rides or stands on, and only if he may give it a destination.
	 */
	private static ShipEntity vessel(CommandContext<ServerCommandSource> ctx, boolean admin) throws CommandSyntaxException {
		if (admin) {
			return ShipCommands.target(ctx);
		}
		ServerPlayerEntity player = ctx.getSource().getPlayerOrThrow();
		ShipEntity ship = player.getVehicle() instanceof ShipEntity riding ? riding : ShipTracker.shipUnder(player);
		if (ship == null) {
			throw ShipCommands.error("Montez à bord du navire (à la barre, sur le pont ou dans une cabine) pour lui donner une destination.");
		}
		if (ShipPermissions.isAdmin(player)) {
			return ship;
		}
		if (ship.isAutopilotEnabled() && !ship.onGoto()) {
			throw ShipCommands.error("Ce navire suit l'itinéraire " + ship.routeName() + " : seul un administrateur peut changer sa route.");
		}
		Entity pilot = ship.passengerInSeat(ShipGeometry.PILOT_SEAT);
		if (pilot != null && pilot != player) {
			throw ShipCommands.error(pilot instanceof ServerPlayerEntity other
					? "C'est " + other.getName().getString() + " qui tient la barre : lui seul peut choisir la destination."
					: "Un capitaine tient la barre : seul un administrateur peut changer la destination.");
		}
		return ship;
	}

	// ------------------------------------------------------------------ goto

	private static int gotoSaved(CommandContext<ServerCommandSource> ctx, boolean admin) throws CommandSyntaxException {
		String name = StringArgumentType.getString(ctx, "name");
		Destination d = ShipData.get(ctx.getSource().getServer()).destination(name);
		if (d == null) {
			throw ShipCommands.error("Destination inconnue : " + name + " (/" + (admin ? "ship destination list" : "pilote destinations") + ").");
		}
		ShipEntity ship = vessel(ctx, admin);
		if (!d.dimension.equals(ship.getEntityWorld().getRegistryKey().getValue().toString())) {
			throw ShipCommands.error("La destination " + name + " est dans une autre dimension (" + d.dimension + ").");
		}
		return go(ctx, ship, admin, d.x, d.y, d.z, d.name);
	}

	/** To the block the player looks at (up to 512 blocks, in loaded chunks): an aircraft lands on it. */
	private static int gotoLook(CommandContext<ServerCommandSource> ctx, boolean admin) throws CommandSyntaxException {
		Entity source = ctx.getSource().getEntity();
		if (source == null) {
			throw ShipCommands.error("Seul un joueur peut viser une destination.");
		}
		HitResult hit = source.raycast(LOOK_RANGE, 1f, true);
		if (hit.getType() == HitResult.Type.MISS) {
			throw ShipCommands.error("Aucun bloc visé (à moins de " + (int) LOOK_RANGE + " blocs, dans les zones chargées).");
		}
		ShipEntity ship = vessel(ctx, admin);
		Vec3d p = hit.getPos();
		ShipGeometry g = ship.geometry();
		// an aircraft: its deck as high above the target as its keel is under the deck, plus its landing clearance
		double y = g.flying() ? p.y + (g.hull().mainDeckY - g.lowestY()) + ship.config().flight.aiLandingClearance : p.y;
		return go(ctx, ship, admin, p.x, y, p.z, GotoRoutes.label(p.x, p.y, p.z, g.flying()));
	}

	private static int go(CommandContext<ServerCommandSource> ctx, ShipEntity ship, boolean admin, double x, double y, double z, String label)
			throws CommandSyntaxException {
		double dist = Math.hypot(x - ship.getX(), z - ship.getZ());
		boolean privileged = admin || ShipPermissions.isAdmin(ctx.getSource());
		double max = ConfigManager.server().playerDestinationMaxDistance;
		if (!privileged && dist > max) {
			throw ShipCommands.error(String.format(Locale.ROOT, "Destination trop lointaine (%.0f blocs, %.0f au plus).", dist, max));
		}
		if (ship.geometry().submarine()) {
			throw ShipCommands.error("Le Nautilus suit des itinéraires sous-marins (/ship route), pas une destination directe.");
		}
		boolean air = ship.geometry().flying();
		if (!air) {
			y = ship.getY() + ship.geometry().hull().mainDeckY; // a ship stays on the water
		}
		String dim = ship.getEntityWorld().getRegistryKey().getValue().toString();
		Route route = GotoRoutes.build(GotoRoutes.routeName(ship.getUuidAsString()), dim, air, label, x, y, z);
		ship.startGoto(route);
		String msg = String.format(Locale.ROOT, "%s : cap sur %s (%.0f blocs). Le pilote automatique tient la barre ; "
				+ "clic droit sur la barre ou /pilote stop pour reprendre la main.", ShipCommands.describe(ship), label, dist);
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GREEN), privileged);
		return 1;
	}

	private static int stop(CommandContext<ServerCommandSource> ctx, boolean admin) throws CommandSyntaxException {
		ShipEntity ship = vessel(ctx, admin);
		if (!ship.cancelGoto()) {
			if (admin && ship.isAutopilotEnabled()) {
				throw ShipCommands.error("Ce navire suit l'itinéraire " + ship.routeName() + " : /ship ai disable pour l'arrêter.");
			}
			throw ShipCommands.error("Ce navire n'a pas de destination.");
		}
		ShipCommands.ok(ctx, ShipCommands.describe(ship) + " : destination annulée, le navire s'arrête"
				+ (ship.geometry().flying() ? " et reste en vol stationnaire." : "."));
		return 1;
	}

	// ------------------------------------------------------------------ saved destinations

	private static int add(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String name = StringArgumentType.getString(ctx, "name");
		ServerCommandSource source = ctx.getSource();
		Vec3d p = source.getPosition();
		String dim = source.getWorld().getRegistryKey().getValue().toString();
		Destination d = new Destination(name, dim, Math.round(p.x * 10) / 10.0, Math.round(p.y * 10) / 10.0, Math.round(p.z * 10) / 10.0);
		ShipData data = ShipData.get(source.getServer());
		boolean replaced = data.destination(name) != null;
		data.putDestination(d);
		ShipCommands.ok(ctx, String.format(Locale.ROOT, "Destination %s %s : %.1f %.1f %.1f (%s). Un dirigeable y amène son pont à cette hauteur.",
				name, replaced ? "remplacée" : "enregistrée", d.x, d.y, d.z, dim));
		return 1;
	}

	private static int remove(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String name = StringArgumentType.getString(ctx, "name");
		if (!ShipData.get(ctx.getSource().getServer()).removeDestination(name)) {
			throw ShipCommands.error("Destination inconnue : " + name);
		}
		ShipCommands.ok(ctx, "Destination " + name + " supprimée.");
		return 1;
	}

	private static int list(CommandContext<ServerCommandSource> ctx) {
		Map<String, Destination> all = ShipData.get(ctx.getSource().getServer()).destinations();
		if (all.isEmpty()) {
			ctx.getSource().sendFeedback(() -> Text.literal("Aucune destination enregistrée (/ship destination add <nom>)."), false);
			return 0;
		}
		Vec3d here = ctx.getSource().getPosition();
		for (Destination d : all.values()) {
			String line = String.format(Locale.ROOT, "- %s : %.0f %.0f %.0f (%s), à %.0f blocs", d.name, d.x, d.y, d.z, d.dimension,
					Math.hypot(d.x - here.x, d.z - here.z));
			ctx.getSource().sendFeedback(() -> Text.literal(line), false);
		}
		return all.size();
	}
}
