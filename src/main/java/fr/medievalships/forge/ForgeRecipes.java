package fr.medievalships.forge;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.OptionalInt;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory;

import net.minecraft.command.permission.LeveledPermissionPredicate;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.recipe.RecipeEntry;
import net.minecraft.scoreboard.ReadableScoreboardScore;
import net.minecraft.scoreboard.ScoreboardObjective;
import net.minecraft.scoreboard.ServerScoreboard;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ForgeCraft;
import fr.medievalships.core.ForgeIngredients;
import fr.medievalships.core.ForgeRequirements;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.tent.TentCollisions;

/**
 * The server side of the divine forge's crafting (1.34.0): the recipes the server has loaded ({@link #all}), the
 * requirements and ingredients of a player ({@link #menu}), a click on "Forger" ({@link #tryCraft}: everything checked
 * again, the ingredients removed exactly, the crafting started), the reward commands ({@link #runCommands}), and
 * finding a forge from a block ({@link #find}).
 */
public final class ForgeRecipes {
	/** The order the player's stacks pay in: the main inventory, then the hotbar, then the off hand. */
	static final int[] SLOTS = slots();
	/** How far from the forge's extent a player may use its interface (blocks). */
	public static final double REACH = 6.0;

	private ForgeRecipes() {
	}

	private static int[] slots() {
		int[] s = new int[PlayerInventory.MAIN_SIZE + 1];
		int k = 0;
		for (int i = 9; i < PlayerInventory.MAIN_SIZE; i++) {
			s[k++] = i;
		}
		for (int i = 0; i < 9; i++) {
			s[k++] = i;
		}
		s[k] = PlayerInventory.OFF_HAND_SLOT;
		return s;
	}

	/**
	 * The forge recipes the server has loaded (data packs), sorted by category, order and name; the trial recipes left out
	 * when the server setting {@code forgeTestRecipe} is false.
	 */
	@SuppressWarnings("unchecked")
	public static List<RecipeEntry<DivineForgeRecipe>> all(MinecraftServer server) {
		List<RecipeEntry<DivineForgeRecipe>> out = new ArrayList<>();
		boolean trials = ConfigManager.server().forgeTestRecipe;
		for (RecipeEntry<?> e : server.getRecipeManager().values()) {
			if (e.value() instanceof DivineForgeRecipe r && (trials || !r.spec().trial())) {
				out.add((RecipeEntry<DivineForgeRecipe>) e);
			}
		}
		out.sort(Comparator.<RecipeEntry<DivineForgeRecipe>>comparingInt(e -> e.value().spec().category().ordinal())
				.thenComparingInt(e -> e.value().spec().order())
				.thenComparing(e -> name(e.value()).toLowerCase(Locale.ROOT))
				.thenComparing(e -> e.id().getValue().toString()));
		return out;
	}

	/** The recipe of this id among {@link #all}, or null (unknown, removed by a reload, or a trial recipe switched off). */
	@Nullable
	public static RecipeEntry<DivineForgeRecipe> byId(MinecraftServer server, String id) {
		for (RecipeEntry<DivineForgeRecipe> e : all(server)) {
			if (e.id().getValue().toString().equals(id)) {
				return e;
			}
		}
		return null;
	}

	/** The name a recipe shows: its {@code "nom"}, else its result's name. */
	public static String name(DivineForgeRecipe r) {
		return r.spec().name() != null ? r.spec().name() : r.result().getName().getString();
	}

	/** The player's stacks in the paying order ({@link #SLOTS}). */
	static List<ItemStack> stacks(ServerPlayerEntity player) {
		PlayerInventory inv = player.getInventory();
		List<ItemStack> out = new ArrayList<>(SLOTS.length);
		for (int s : SLOTS) {
			out.add(inv.getStack(s));
		}
		return out;
	}

	/** The requirement checks answered from the server's scoreboard and the player. */
	static ForgeRequirements.Subject subject(ServerPlayerEntity player) {
		ServerScoreboard board = player.getEntityWorld().getServer().getScoreboard();
		return new ForgeRequirements.Subject() {
			@Override
			public boolean objectiveExists(String objective) {
				return board.getNullableObjective(objective) != null;
			}

			@Override
			public OptionalInt score(String objective) {
				ScoreboardObjective o = board.getNullableObjective(objective);
				if (o == null) {
					return OptionalInt.empty();
				}
				ReadableScoreboardScore s = board.getScore(player, o);
				return s == null ? OptionalInt.empty() : OptionalInt.of(s.getScore());
			}

			@Override
			public boolean hasTag(String tag) {
				return player.getCommandTags().contains(tag);
			}

			@Override
			public int permissionLevel() {
				return ShipPermissions.level(player.getPermissions());
			}
		};
	}

	/** What the interface shows this player at this forge, with a line of news ({@code notice}, "" for none). */
	public static ForgeMenu menu(ServerPlayerEntity player, DivineForgeBlockEntity forge, String notice) {
		MinecraftServer server = player.getEntityWorld().getServer();
		long now = forge.getWorld() == null ? 0 : forge.getWorld().getTime();
		ForgeCraft c = forge.craft();
		boolean busy = c.busy();
		boolean mine = busy && player.getUuidAsString().equals(c.player());
		List<ItemStack> inv = stacks(player);
		ForgeRequirements.Subject who = subject(player);
		List<ForgeMenu.Entry> entries = new ArrayList<>();
		for (RecipeEntry<DivineForgeRecipe> e : all(server)) {
			DivineForgeRecipe r = e.value();
			ForgeIngredients.Plan plan = r.plan(inv);
			List<String> unmet = ForgeRequirements.unmet(r.spec(), who);
			List<ForgeMenu.Ing> ings = new ArrayList<>();
			for (int i = 0; i < r.ingredients().size(); i++) {
				DivineForgeRecipe.Ingredient in = r.ingredients().get(i);
				ings.add(new ForgeMenu.Ing(in.icon(), in.label(), in.count(), plan.owned()[i]));
			}
			entries.add(new ForgeMenu.Entry(e.id().getValue().toString(), r.spec().category().ordinal(), r.result(), name(r),
					r.spec().description() == null ? "" : r.spec().description(), r.spec().duration(), ings, unmet, r.spec().trial(),
					unmet.isEmpty() && plan.complete()));
			if (entries.size() >= ForgeMenu.MAX_ENTRIES) {
				MedievalShips.LOGGER.warn("Divine forge: more than {} recipes, only the first ones are shown", ForgeMenu.MAX_ENTRIES);
				break;
			}
		}
		return new ForgeMenu(forge.getPos(), busy, mine, busy && c.label() != null ? c.label() : "", (int) c.remaining(now), (int) c.total(),
				forge.pendingFor(player.getUuid()), entries, notice == null ? "" : notice);
	}

	/** Opens the forge's interface to a player (the screen handler's opening data carries the list). */
	public static void open(ServerPlayerEntity player, DivineForgeBlockEntity forge) {
		ForgeMenu menu = menu(player, forge, "");
		BlockPos pos = forge.getPos();
		player.openHandledScreen(new ExtendedScreenHandlerFactory<ForgeMenu>() {
			@Override
			public ForgeMenu getScreenOpeningData(ServerPlayerEntity p) {
				return menu;
			}

			@Override
			public Text getDisplayName() {
				return Text.translatableWithFallback("container.medievalships.forge_divine", "Forge divine");
			}

			@Override
			public ScreenHandler createMenu(int syncId, PlayerInventory inventory, PlayerEntity p) {
				return new DivineForgeScreenHandler(syncId, inventory, menu, pos);
			}
		});
	}

	/** The outcome of a click on "Forger": did the crafting start, and the line to show (French). */
	public record Outcome(boolean started, String message) {
	}

	/**
	 * A click on "Forger" for a recipe: checks again that the forge is free, the recipe still loaded, its requirements met
	 * and its ingredients in the inventory, removes exactly the ingredients, and starts the crafting (the result is handed
	 * over at the end). Nothing is removed when anything fails.
	 */
	public static Outcome tryCraft(ServerPlayerEntity player, DivineForgeBlockEntity forge, String recipeId) {
		if (!(forge.getWorld() instanceof ServerWorld world) || forge.isRemoved()) {
			return new Outcome(false, "La forge n'est plus là.");
		}
		if (forge.craft().busy()) {
			long s = (forge.remainingTicks() + 19) / 20;
			return new Outcome(false, "La forge est occupée (encore " + s + " s).");
		}
		RecipeEntry<DivineForgeRecipe> e = byId(world.getServer(), recipeId);
		if (e == null) {
			return new Outcome(false, "Cette recette n'est plus disponible.");
		}
		DivineForgeRecipe r = e.value();
		List<String> unmet = ForgeRequirements.unmet(r.spec(), subject(player));
		if (!unmet.isEmpty()) {
			return new Outcome(false, unmet.get(0) + ".");
		}
		ForgeIngredients.Plan plan = r.plan(stacks(player));
		if (!plan.complete()) {
			StringBuilder sb = new StringBuilder("Ingrédients manquants : ");
			boolean first = true;
			for (int i = 0; i < plan.missing().length; i++) {
				if (plan.missing()[i] > 0) {
					DivineForgeRecipe.Ingredient in = r.ingredients().get(i);
					sb.append(first ? "" : ", ").append(plan.missing()[i]).append(" x ")
							.append(in.label().isEmpty() ? in.icon().getName().getString() : in.label());
					first = false;
				}
			}
			return new Outcome(false, sb.append('.').toString());
		}
		List<ItemStack> taken = pay(player, plan);
		String label = name(r);
		if (!forge.startRecipe(world, player, e.id().getValue().toString(), r.result(), r.spec().commands(), label, r.spec().duration())) {
			for (ItemStack s : taken) {
				player.getInventory().offerOrDrop(s);
			}
			return new Outcome(false, "La forge est occupée.");
		}
		return new Outcome(true, "La forge divine se met à l'ouvrage : " + label + " (" + seconds(r.spec().duration()) + ").");
	}

	/** A crafting started through the API with a result for a player (no recipe file). */
	public static boolean startForApi(ServerWorld world, DivineForgeBlockEntity forge, ServerPlayerEntity player, ItemStack result, int ticks) {
		return forge.startRecipe(world, player, DivineForgeBlockEntity.API_RECIPE, result, List.of(), result.getName().getString(), ticks);
	}

	/** Removes what the plan says from the player's inventory; the stacks taken (to give them back if needed). */
	static List<ItemStack> pay(ServerPlayerEntity player, ForgeIngredients.Plan plan) {
		PlayerInventory inv = player.getInventory();
		List<ItemStack> taken = new ArrayList<>();
		for (int k = 0; k < SLOTS.length && k < plan.take().length; k++) {
			int n = plan.take()[k];
			if (n > 0) {
				ItemStack removed = inv.removeStack(SLOTS[k], n);
				if (!removed.isEmpty()) {
					taken.add(removed);
				}
			}
		}
		inv.markDirty();
		return taken;
	}

	/** "10 s", "1 min 30 s". */
	public static String seconds(int ticks) {
		int s = Math.max(1, (ticks + 19) / 20);
		return s < 60 ? s + " s" : s / 60 + " min" + (s % 60 == 0 ? "" : " " + s % 60 + " s");
	}

	/**
	 * Runs a recipe's reward commands as the player, at their position, silently, with the permission level of a command
	 * block (2), like the workshops' {@code workshopCommands}: only the recipe files (the server's data packs) choose them.
	 */
	public static void runCommands(ServerPlayerEntity player, List<String> commands, @Nullable String what) {
		if (commands.isEmpty()) {
			return;
		}
		ServerWorld world = player.getEntityWorld();
		ServerCommandSource source = player.getCommandSource(world).withAdditionalPermissions(LeveledPermissionPredicate.GAMEMASTERS).withSilent();
		for (String command : commands) {
			try {
				world.getServer().getCommandManager().parseAndExecute(source, command);
			} catch (RuntimeException e) {
				MedievalShips.LOGGER.warn("Divine forge ({}): the command \"{}\" failed", what, command, e);
			}
		}
	}

	/** The forge at this block: its anchor, or any block inside the extent of a loaded forge; null when none. */
	@Nullable
	public static DivineForgeBlockEntity find(World world, BlockPos pos) {
		if (world.getBlockEntity(pos) instanceof DivineForgeBlockEntity f) {
			return f;
		}
		Vec3d p = Vec3d.ofCenter(pos);
		for (TentCollisions.Placed t : TentCollisions.nearby(world, new Box(pos).expand(16))) {
			if (t.type().isDivineForge() && t.extent().expand(0.01).contains(p) && world.getBlockEntity(t.pos()) instanceof DivineForgeBlockEntity f) {
				return f;
			}
		}
		return null;
	}

	/** The loaded forge nearest to a point within {@code radius} blocks, or null. */
	@Nullable
	public static DivineForgeBlockEntity nearest(World world, Vec3d from, double radius) {
		DivineForgeBlockEntity best = null;
		double bestD = radius * radius;
		for (TentCollisions.Placed t : TentCollisions.all(world)) {
			if (!t.type().isDivineForge()) {
				continue;
			}
			double d = t.pos().getSquaredDistance(from);
			if (d <= bestD && world.getBlockEntity(t.pos()) instanceof DivineForgeBlockEntity f) {
				bestD = d;
				best = f;
			}
		}
		return best;
	}

	/** Is the player close enough to the forge to use its interface ({@link #REACH} blocks of its extent)? */
	public static boolean inReach(PlayerEntity player, DivineForgeBlockEntity forge) {
		Box e = forge.worldExtent().expand(REACH);
		return !forge.isRemoved() && e.contains(player.getEyePos());
	}
}
