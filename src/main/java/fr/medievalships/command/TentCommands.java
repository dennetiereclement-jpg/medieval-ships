package fr.medievalships.command;

import java.util.Collection;
import java.util.List;
import java.util.Locale;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;

import net.minecraft.block.BlockState;
import net.minecraft.command.argument.BlockPosArgumentType;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.item.ItemStack;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.tent.TentItem;
import fr.medievalships.tent.Tents;

/**
 * {@code /tent give <id> [players]}, {@code /tent place <id> [x y z] [facing]}, {@code /tent remove [nearest|x y z]},
 * {@code /tent list}. Admin only, like {@code /ship}. The ids also work with {@code /ship give}.
 */
public final class TentCommands {
	private TentCommands() {
	}

	private static final String[] FACINGS = {"south", "west", "north", "east"};

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		LiteralArgumentBuilder<ServerCommandSource> root = CommandManager.literal("tent").requires(ShipPermissions::isAdmin);
		var give = CommandManager.literal("give");
		var place = CommandManager.literal("place");
		for (TentType type : TentTypes.ALL) {
			give.then(CommandManager.literal(type.id())
					.executes(ctx -> give(ctx, type, List.of(ctx.getSource().getPlayerOrThrow())))
					.then(CommandManager.argument("targets", EntityArgumentType.players())
							.executes(ctx -> give(ctx, type, EntityArgumentType.getPlayers(ctx, "targets")))));
			var at = CommandManager.argument("pos", BlockPosArgumentType.blockPos())
					.executes(ctx -> place(ctx, type, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"), null));
			for (String f : FACINGS) {
				at.then(CommandManager.literal(f).executes(ctx -> place(ctx, type, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"), f)));
			}
			var typed = CommandManager.literal(type.id()).executes(ctx -> place(ctx, type, null, null)).then(at);
			for (String f : FACINGS) {
				typed.then(CommandManager.literal(f).executes(ctx -> place(ctx, type, null, f)));
			}
			place.then(typed);
		}
		root.then(give);
		root.then(place);
		root.then(CommandManager.literal("remove").executes(ctx -> remove(ctx, null))
				.then(CommandManager.literal("nearest").executes(ctx -> remove(ctx, null)))
				.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
						.executes(ctx -> remove(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos")))));
		root.then(CommandManager.literal("list").executes(TentCommands::list));
		root.then(CommandManager.literal("types").executes(ctx -> {
			for (TentType t : TentTypes.ALL) {
				ok(ctx, t.id() + " : " + t.frenchName());
			}
			return TentTypes.ALL.size();
		}));
		dispatcher.register(root);
	}

	private static int give(CommandContext<ServerCommandSource> ctx, TentType type, Collection<ServerPlayerEntity> players) {
		for (ServerPlayerEntity p : players) {
			p.getInventory().offerOrDrop(new ItemStack(Tents.item(type)));
		}
		ok(ctx, capitalize(type.frenchName()) + " donnée à " + players.size() + " joueur(s).");
		return players.size();
	}

	/** The anchor goes at the given block (or the command's position), the entrance towards the facing (or the source's). */
	private static int place(CommandContext<ServerCommandSource> ctx, TentType type, BlockPos pos, String facingName) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		ServerWorld world = source.getWorld();
		if (pos == null) {
			Vec3d p = source.getPosition();
			pos = BlockPos.ofFloored(p);
		}
		Direction facing;
		if (facingName != null) {
			facing = Direction.byId(facingName);
			if (facing == null || facing.getAxis().isVertical()) {
				facing = Direction.SOUTH;
			}
		} else {
			facing = Direction.fromHorizontalDegrees(source.getRotation().y + 180.0);
		}
		if (!TentItem.coverable(world.getBlockState(pos))) {
			throw error("Le bloc " + pos.toShortString() + " n'est pas libre.");
		}
		String problem = TentItem.freeAreaProblem(world, pos, type, facing.getHorizontalQuarterTurns());
		if (problem != null) {
			throw error(problem);
		}
		BlockState state = Tents.block(type).getDefaultState().with(TentBlock.FACING, facing);
		world.setBlockState(pos, state, 3);
		Tents.block(type).onPlaced(world, pos, state, null, ItemStack.EMPTY);
		ok(ctx, String.format(Locale.ROOT, "%s posée en %s, entrée vers %s.", capitalize(type.frenchName()), pos.toShortString(), facing.asString()));
		return 1;
	}

	private static int remove(CommandContext<ServerCommandSource> ctx, BlockPos pos) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		ServerWorld world = source.getWorld();
		TentCollisions.Placed target = null;
		if (pos != null) {
			target = TentCollisions.at(world, pos);
			if (target == null) {
				throw error("Pas de tente en " + pos.toShortString() + ".");
			}
		} else {
			Vec3d p = source.getPosition();
			double best = Double.MAX_VALUE;
			for (TentCollisions.Placed t : TentCollisions.all(world)) {
				double d = t.pos().getSquaredDistance(p);
				if (d < best) {
					best = d;
					target = t;
				}
			}
			if (target == null) {
				throw error("Aucune tente chargée dans ce monde.");
			}
		}
		world.breakBlock(target.pos(), false);
		TentCollisions.remove(world, target.pos());
		ok(ctx, capitalize(target.type().frenchName()) + " retirée en " + target.pos().toShortString() + ".");
		return 1;
	}

	private static int list(CommandContext<ServerCommandSource> ctx) {
		ServerWorld world = ctx.getSource().getWorld();
		Vec3d p = ctx.getSource().getPosition();
		List<TentCollisions.Placed> all = TentCollisions.all(world);
		all.sort((a, b) -> Double.compare(a.pos().getSquaredDistance(p), b.pos().getSquaredDistance(p)));
		if (all.isEmpty()) {
			ok(ctx, "Aucune tente chargée dans ce monde.");
			return 0;
		}
		ok(ctx, all.size() + " tente(s) chargée(s) :");
		int n = 0;
		for (TentCollisions.Placed t : all) {
			if (n++ >= 20) {
				ok(ctx, "...");
				break;
			}
			ok(ctx, String.format(Locale.ROOT, "- %s [%s] entrée vers %s, à %.0f m", capitalize(t.type().frenchName()), t.pos().toShortString(),
					FACINGS[t.quarter() & 3], Math.sqrt(t.pos().getSquaredDistance(p))));
		}
		return all.size();
	}

	private static void ok(CommandContext<ServerCommandSource> ctx, String msg) {
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(Formatting.GREEN), true);
	}

	private static CommandSyntaxException error(String msg) {
		return new SimpleCommandExceptionType(Text.literal(msg)).create();
	}

	private static String capitalize(String s) {
		return s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1);
	}
}
