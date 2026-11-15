package fr.medievalships.command;

import java.util.Collection;
import java.util.List;
import java.util.Locale;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;

import net.minecraft.command.argument.BlockPosArgumentType;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.recipe.RecipeEntry;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.ForgeCraft;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.forge.DivineForgeBlockEntity;
import fr.medievalships.forge.DivineForgeRecipe;
import fr.medievalships.forge.ForgeRecipes;

/**
 * {@code /forge} (1.34.0, administrators): the divine forge for the server's own profession systems.
 * <ul>
 * <li>{@code /forge animer [x y z] <secondes>}: plays the crafting animation (nothing is handed over at the end);</li>
 * <li>{@code /forge arreter [x y z]}: ends the crafting under way now (a player's result is handed over early);</li>
 * <li>{@code /forge etat [x y z]}: at rest or crafting (what, for whom, time left), the results kept;</li>
 * <li>{@code /forge recettes}: the forge recipes loaded from the data packs;</li>
 * <li>{@code /forge ouvrir <joueurs> [x y z]}: opens the forge's interface to players standing by it (an NPC's action).</li>
 * </ul>
 * Without a position, the nearest forge within {@value #RADIUS} blocks of the command's position; a position may be any
 * block of the forge.
 */
public final class ForgeCommands {
	/** How far the nearest forge is looked for when no position is given (blocks). */
	public static final int RADIUS = 48;

	private ForgeCommands() {
	}

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		dispatcher.register(CommandManager.literal("forge").requires(ShipPermissions::isAdmin)
				.then(CommandManager.literal("animer")
						.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, ForgeCraft.MAX_TICKS / 20))
								.executes(ctx -> animate(ctx, null)))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, ForgeCraft.MAX_TICKS / 20))
										.executes(ctx -> animate(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"))))))
				.then(CommandManager.literal("arreter").executes(ctx -> stop(ctx, null))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.executes(ctx -> stop(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos")))))
				.then(CommandManager.literal("etat").executes(ctx -> state(ctx, null))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.executes(ctx -> state(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos")))))
				.then(CommandManager.literal("recettes").executes(ForgeCommands::recipes))
				.then(CommandManager.literal("ouvrir")
						.then(CommandManager.argument("joueurs", EntityArgumentType.players())
								.executes(ctx -> open(ctx, EntityArgumentType.getPlayers(ctx, "joueurs"), null))
								.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
										.executes(ctx -> open(ctx, EntityArgumentType.getPlayers(ctx, "joueurs"),
												BlockPosArgumentType.getLoadedBlockPos(ctx, "pos")))))));
	}

	/** The forge at a position (any of its blocks), or the nearest one. */
	private static DivineForgeBlockEntity forge(ServerCommandSource source, BlockPos pos) throws CommandSyntaxException {
		ServerWorld world = source.getWorld();
		DivineForgeBlockEntity f = pos != null ? ForgeRecipes.find(world, pos) : ForgeRecipes.nearest(world, source.getPosition(), RADIUS);
		if (f == null) {
			throw error(pos != null ? "Pas de forge divine en " + pos.toShortString() + "."
					: "Aucune forge divine à moins de " + RADIUS + " blocs.");
		}
		return f;
	}

	private static int animate(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		int seconds = IntegerArgumentType.getInteger(ctx, "secondes");
		if (!f.startAnimation(ctx.getSource().getWorld(), seconds * 20)) {
			throw error("La forge est occupée (encore " + (f.remainingTicks() + 19) / 20 + " s) : /forge arreter d'abord.");
		}
		ok(ctx, "Forge divine en " + f.getPos().toShortString() + " : animation de fabrication pendant " + seconds + " s.");
		return 1;
	}

	private static int stop(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		String what = f.craft().label();
		boolean anim = f.craft().animationOnly();
		if (!f.stop(ctx.getSource().getWorld())) {
			throw error("La forge divine en " + f.getPos().toShortString() + " est déjà au repos.");
		}
		ok(ctx, "Forge divine en " + f.getPos().toShortString() + " arrêtée" + (anim ? "." : " : « " + what + " » remis à son joueur."));
		return 1;
	}

	private static int state(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		ForgeCraft c = f.craft();
		long now = ctx.getSource().getWorld().getTime();
		if (!c.crafting()) {
			ok(ctx, "Forge divine en " + f.getPos().toShortString() + " : au repos.");
		} else {
			String who = c.playerName() != null ? " pour " + c.playerName() : "";
			ok(ctx, String.format(Locale.ROOT, "Forge divine en %s : en fabrication (%s%s), encore %d s (%d %%).", f.getPos().toShortString(),
					c.animationOnly() ? "animation" : "« " + c.label() + " »", who, (c.remaining(now) + 19) / 20, Math.round(c.progress(now) * 100)));
		}
		List<DivineForgeBlockEntity.Pending> kept = f.pending();
		if (!kept.isEmpty()) {
			StringBuilder sb = new StringBuilder(kept.size() + " résultat(s) gardé(s) pour des joueurs absents :");
			for (DivineForgeBlockEntity.Pending p : kept) {
				sb.append(' ').append(p.name().isEmpty() ? p.player().toString() : p.name()).append(" (").append(p.stack().getName().getString())
						.append(')');
			}
			ok(ctx, sb.toString());
		}
		return c.crafting() ? 1 : 0;
	}

	private static int recipes(CommandContext<ServerCommandSource> ctx) {
		List<RecipeEntry<DivineForgeRecipe>> all = ForgeRecipes.all(ctx.getSource().getServer());
		ok(ctx, all.size() + " recette(s) de forge divine chargée(s)" + (ConfigManager.server().forgeTestRecipe ? ""
				: " (recettes d'essai masquées : forgeTestRecipe = false)") + " :");
		for (RecipeEntry<DivineForgeRecipe> e : all) {
			DivineForgeRecipe r = e.value();
			StringBuilder sb = new StringBuilder("- ").append(e.id().getValue()).append(" : ").append(ForgeRecipes.name(r)).append(" [")
					.append(r.spec().category().label()).append(", ").append(ForgeRecipes.seconds(r.spec().duration())).append("]");
			if (r.spec().trial()) {
				sb.append(" (essai)");
			}
			if (r.spec().profession() != null) {
				sb.append(" métier ").append(r.spec().profession()).append(" ").append(r.spec().level());
			}
			if (r.spec().tag() != null) {
				sb.append(" tag ").append(r.spec().tag());
			}
			if (r.spec().permission() > 0) {
				sb.append(" permission ").append(r.spec().permission());
			}
			ok(ctx, sb.toString());
		}
		return all.size();
	}

	private static int open(CommandContext<ServerCommandSource> ctx, Collection<ServerPlayerEntity> players, BlockPos pos) throws CommandSyntaxException {
		int n = 0;
		for (ServerPlayerEntity p : players) {
			DivineForgeBlockEntity f = pos != null ? ForgeRecipes.find(p.getEntityWorld(), pos) : ForgeRecipes.nearest(p.getEntityWorld(), p.getEntityPos(), RADIUS);
			if (f != null && ForgeRecipes.inReach(p, f)) {
				f.deliverPending(p);
				ForgeRecipes.open(p, f);
				n++;
			}
		}
		if (n == 0) {
			throw error("Aucun de ces joueurs n'est près d'une forge divine (à moins de " + (int) ForgeRecipes.REACH + " blocs).");
		}
		ok(ctx, "Interface de la forge divine ouverte à " + n + " joueur(s).");
		return n;
	}

	private static void ok(CommandContext<ServerCommandSource> ctx, String msg) {
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GREEN), true);
	}

	private static CommandSyntaxException error(String msg) {
		return new SimpleCommandExceptionType(Text.literal(msg)).create();
	}
}
