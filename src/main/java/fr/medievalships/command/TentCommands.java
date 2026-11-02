package fr.medievalships.command;

import java.util.Collection;
import java.util.List;
import java.util.Locale;

import com.mojang.brigadier.CommandDispatcher;
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
 * {@code /tent list}, {@code /tent types}. Admin only, like {@code /ship}. Every prop id (tents, carts and workshops,
 * {@link TentTypes#PROPS}, the cannon included) is accepted, also by {@code /ship give}; {@code /cart} is the same command under another name.
 * {@code /workshop} (alias {@code /atelier}) is the same tree for the workshops only ({@link TentTypes#WORKSHOPS}): its
 * {@code remove} and {@code list} only see workshops; {@code /training} the same for the training areas (1.19.0).
 */
public final class TentCommands {
	private TentCommands() {
	}

	private static final String[] FACINGS = {"south", "west", "north", "east"};

	/**
	 * The props a command tree handles and the French words of its messages: {@code e} is the agreement of the past
	 * participles ("posée" for a tent, "posé" for a workshop).
	 */
	private record Family(List<TentType> types, boolean onlyThese, String e, String noneLoaded, String noneAt, String listed) {
		boolean accepts(TentType t) {
			return !onlyThese || types.contains(t);
		}
	}

	private static final Family PROPS = new Family(TentTypes.PROPS, false, "e", "Aucune tente chargée dans ce monde.", "Pas de tente en ",
			"%d tente(s) chargée(s) :");
	private static final Family WORKSHOPS = new Family(TentTypes.WORKSHOPS, true, "", "Aucun atelier chargé dans ce monde.",
			"Pas d'atelier en ", "%d atelier(s) chargé(s) :");
	/** {@code /training}: the training areas only (1.19.0; unbreakable in survival, removed by an admin with this or /tent remove). */
	private static final Family TRAINING = new Family(TentTypes.TRAINING, true, "e", "Aucune aire d'entraînement chargée dans ce monde.",
			"Pas d'aire d'entraînement en ", "%d aire(s) d'entraînement chargée(s) :");

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		dispatcher.register(tree("tent", PROPS));
		dispatcher.register(tree("cart", PROPS));
		dispatcher.register(tree("workshop", WORKSHOPS));
		dispatcher.register(tree("atelier", WORKSHOPS));
		dispatcher.register(tree("training", TRAINING));
	}

	private static LiteralArgumentBuilder<ServerCommandSource> tree(String name, Family family) {
		LiteralArgumentBuilder<ServerCommandSource> root = CommandManager.literal(name).requires(ShipPermissions::isAdmin);
		var give = CommandManager.literal("give");
		var place = CommandManager.literal("place");
		for (TentType type : family.types()) {
			give.then(CommandManager.literal(type.id())
					.executes(ctx -> give(ctx, type, List.of(ctx.getSource().getPlayerOrThrow()), family))
					.then(CommandManager.argument("targets", EntityArgumentType.players())
							.executes(ctx -> give(ctx, type, EntityArgumentType.getPlayers(ctx, "targets"), family))));
			var at = CommandManager.argument("pos", BlockPosArgumentType.blockPos())
					.executes(ctx -> place(ctx, type, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"), null, family));
			for (String f : FACINGS) {
				at.then(CommandManager.literal(f).executes(ctx -> place(ctx, type, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"), f, family)));
			}
			var typed = CommandManager.literal(type.id()).executes(ctx -> place(ctx, type, null, null, family)).then(at);
			for (String f : FACINGS) {
				typed.then(CommandManager.literal(f).executes(ctx -> place(ctx, type, null, f, family)));
			}
			place.then(typed);
		}
		root.then(give);
		root.then(place);
		root.then(CommandManager.literal("remove").executes(ctx -> remove(ctx, null, family))
				.then(CommandManager.literal("nearest").executes(ctx -> remove(ctx, null, family)))
				.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
						.executes(ctx -> remove(ctx, BlockPosArgumentType.getLoadedBlockPos(ctx, "pos"), family))));
		root.then(CommandManager.literal("list").executes(ctx -> list(ctx, family)));
		root.then(CommandManager.literal("types").executes(ctx -> {
			for (TentType t : family.types()) {
				ok(ctx, t.id() + " : " + t.frenchName());
			}
			return family.types().size();
		}));
		return root;
	}

	private static int give(CommandContext<ServerCommandSource> ctx, TentType type, Collection<ServerPlayerEntity> players, Family family) {
		for (ServerPlayerEntity p : players) {
			p.getInventory().offerOrDrop(new ItemStack(Tents.item(type)));
		}
		ok(ctx, capitalize(type.frenchName()) + " donné" + (type.masculine() ? "" : family.e()) + " à " + players.size() + " joueur(s).");
		return players.size();
	}

	/** The anchor goes at the given block (or the command's position), the entrance towards the facing (or the source's). */
	private static int place(CommandContext<ServerCommandSource> ctx, TentType type, BlockPos pos, String facingName, Family family)
			throws CommandSyntaxException {
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
		ok(ctx, String.format(Locale.ROOT, "%s posé%s en %s, %s vers %s.", capitalize(type.frenchName()), type.masculine() ? "" : family.e(),
				pos.toShortString(), type.isWorkshop() ? "avant" : type.isCannon() ? "culasse" : "entrée", facing.asString()));
		return 1;
	}

	private static int remove(CommandContext<ServerCommandSource> ctx, BlockPos pos, Family family) throws CommandSyntaxException {
		ServerCommandSource source = ctx.getSource();
		ServerWorld world = source.getWorld();
		TentCollisions.Placed target = null;
		if (pos != null) {
			target = TentCollisions.at(world, pos);
			if (target == null || !family.accepts(target.type())) {
				throw error(family.noneAt() + pos.toShortString() + ".");
			}
		} else {
			Vec3d p = source.getPosition();
			double best = Double.MAX_VALUE;
			for (TentCollisions.Placed t : TentCollisions.all(world)) {
				double d = t.pos().getSquaredDistance(p);
				if (d < best && family.accepts(t.type())) {
					best = d;
					target = t;
				}
			}
			if (target == null) {
				throw error(family.noneLoaded());
			}
		}
		world.breakBlock(target.pos(), false);
		TentCollisions.remove(world, target.pos());
		ok(ctx, capitalize(target.type().frenchName()) + " retiré" + (target.type().masculine() ? "" : family.e()) + " en "
				+ target.pos().toShortString() + ".");
		return 1;
	}

	private static int list(CommandContext<ServerCommandSource> ctx, Family family) {
		ServerWorld world = ctx.getSource().getWorld();
		Vec3d p = ctx.getSource().getPosition();
		List<TentCollisions.Placed> all = TentCollisions.all(world);
		all.removeIf(t -> !family.accepts(t.type()));
		all.sort((a, b) -> Double.compare(a.pos().getSquaredDistance(p), b.pos().getSquaredDistance(p)));
		if (all.isEmpty()) {
			ok(ctx, family.noneLoaded());
			return 0;
		}
		ok(ctx, String.format(Locale.ROOT, family.listed(), all.size()));
		int n = 0;
		for (TentCollisions.Placed t : all) {
			if (n++ >= 20) {
				ok(ctx, "...");
				break;
			}
			ok(ctx, String.format(Locale.ROOT, "- %s [%s] %s vers %s, à %.0f m", capitalize(t.type().frenchName()), t.pos().toShortString(),
					t.type().isWorkshop() ? "avant" : t.type().isCannon() ? "culasse" : "entrée", FACINGS[t.quarter() & 3],
					Math.sqrt(t.pos().getSquaredDistance(p))));
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
