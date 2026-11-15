package fr.medievalships.command;

import java.util.Locale;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;

import net.minecraft.command.argument.BlockPosArgumentType;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.ForgeActivity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.forge.DivineForge;
import fr.medievalships.forge.DivineForgeBlockEntity;

/**
 * {@code /forge} (1.34.0, administrators): neutral tools to animate the divine forge from the server's own systems
 * (the forge itself crafts nothing and is linked to nothing).
 * <ul>
 * <li>{@code /forge animer [x y z] <secondes>}: the forge becomes active for that long (its activity animation, then the
 * magic sound);</li>
 * <li>{@code /forge arreter [x y z]}: ends the activity now;</li>
 * <li>{@code /forge etat [x y z]}: at rest or active (time left).</li>
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
						.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, ForgeActivity.MAX_TICKS / 20))
								.executes(ctx -> animate(ctx, null)))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, ForgeActivity.MAX_TICKS / 20))
										.executes(ctx -> animate(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"))))))
				.then(CommandManager.literal("arreter").executes(ctx -> stop(ctx, null))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.executes(ctx -> stop(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos")))))
				.then(CommandManager.literal("etat").executes(ctx -> state(ctx, null))
						.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
								.executes(ctx -> state(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"))))));
	}

	/** The forge at a position (any of its blocks), or the nearest one. */
	private static DivineForgeBlockEntity forge(ServerCommandSource source, BlockPos pos) throws CommandSyntaxException {
		ServerWorld world = source.getWorld();
		DivineForgeBlockEntity f = pos != null ? DivineForge.find(world, pos) : DivineForge.nearest(world, source.getPosition(), RADIUS);
		if (f == null) {
			throw error(pos != null ? "Pas de forge divine en " + pos.toShortString() + "."
					: "Aucune forge divine à moins de " + RADIUS + " blocs.");
		}
		return f;
	}

	private static int animate(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		int seconds = IntegerArgumentType.getInteger(ctx, "secondes");
		if (!f.startActivity(ctx.getSource().getWorld(), seconds * 20)) {
			throw error("La forge divine est déjà en activité (encore " + (f.remainingTicks() + 19) / 20 + " s) : /forge arreter d'abord.");
		}
		ok(ctx, "Forge divine en " + f.getPos().toShortString() + " : en activité pendant " + seconds + " s.");
		return 1;
	}

	private static int stop(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		if (!f.stop(ctx.getSource().getWorld())) {
			throw error("La forge divine en " + f.getPos().toShortString() + " est déjà au repos.");
		}
		ok(ctx, "Forge divine en " + f.getPos().toShortString() + " : activité arrêtée.");
		return 1;
	}

	private static int state(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		DivineForgeBlockEntity f = forge(ctx.getSource(), pos);
		ForgeActivity a = f.activity();
		long now = ctx.getSource().getWorld().getTime();
		if (!a.active()) {
			ok(ctx, "Forge divine en " + f.getPos().toShortString() + " : au repos.");
			return 0;
		}
		ok(ctx, String.format(Locale.ROOT, "Forge divine en %s : en activité, encore %d s (%d %%).", f.getPos().toShortString(),
				(a.remaining(now) + 19) / 20, Math.round(a.progress(now) * 100)));
		return 1;
	}

	private static void ok(CommandContext<ServerCommandSource> ctx, String msg) {
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GREEN), true);
	}

	private static CommandSyntaxException error(String msg) {
		return new SimpleCommandExceptionType(Text.literal(msg)).create();
	}
}
