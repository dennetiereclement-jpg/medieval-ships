package fr.medievalships.api;

import java.util.List;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.forge.DivineForgeBlockEntity;
import fr.medievalships.forge.ForgeRecipes;

/**
 * The divine forge for other mods (1.34.0): a profession or crafting system that has its own recipes can still use the
 * forge's animation (the fire and the heat columns brighter, the gears faster, the hammer blows and sparks, the magic
 * sound at the end) and, if it wants, let the forge hand its result over at the end. Server side only; every method
 * takes the forge's anchor block or any block inside its extent. See docs/FORGE.md.
 *
 * <pre>{@code
 * // 30 s of crafting animation, nothing handed over (the mod gives its item itself, e.g. on CRAFT_FINISHED)
 * DivineForgeApi.startCrafting(world, pos, 600);
 * // 10 s, then the forge hands the stack to the player (kept for them if they are away)
 * DivineForgeApi.startCrafting(world, pos, 200, player, myStack);
 * DivineForgeApi.CRAFT_FINISHED.register((world, pos, player, playerId, recipe, result, animationOnly) -> {
 *     if (player != null && recipe != null) MyJobs.addXp(player, "forge", 25);
 * });
 * }</pre>
 */
public final class DivineForgeApi {
	private DivineForgeApi() {
	}

	/**
	 * A crafting has just started (a player's recipe from the interface, an animation from {@code /forge animer} or
	 * {@link #startCrafting}).
	 */
	@FunctionalInterface
	public interface CraftStarted {
		/**
		 * @param player the player it is crafted for, or null (an animation)
		 * @param recipe the recipe id, or null (an animation); {@code medievalships:api} for {@link #startCrafting(ServerWorld, BlockPos, int, ServerPlayerEntity, ItemStack)}
		 * @param ticks  how long it lasts
		 */
		void onStarted(ServerWorld world, BlockPos pos, @Nullable ServerPlayerEntity player, @Nullable Identifier recipe, int ticks);
	}

	/** A crafting has ended (its time elapsed, stopped by an administrator, or the forge removed). */
	@FunctionalInterface
	public interface CraftFinished {
		/**
		 * @param player        the player it was crafted for, when connected (else null)
		 * @param playerId      that player's UUID (null for an animation): when {@code player} is null, the result was kept
		 *                      in the forge for their next click
		 * @param recipe        the recipe id, or null for an animation
		 * @param result        a copy of the stack handed over (empty for an animation)
		 * @param animationOnly an animation (no recipe, no player, no result)
		 */
		void onFinished(ServerWorld world, BlockPos pos, @Nullable ServerPlayerEntity player, @Nullable UUID playerId, @Nullable Identifier recipe,
				ItemStack result, boolean animationOnly);
	}

	public static final Event<CraftStarted> CRAFT_STARTED = EventFactory.createArrayBacked(CraftStarted.class,
			listeners -> (world, pos, player, recipe, ticks) -> {
				for (CraftStarted l : listeners) {
					l.onStarted(world, pos, player, recipe, ticks);
				}
			});

	public static final Event<CraftFinished> CRAFT_FINISHED = EventFactory.createArrayBacked(CraftFinished.class,
			listeners -> (world, pos, player, playerId, recipe, result, animationOnly) -> {
				for (CraftFinished l : listeners) {
					l.onFinished(world, pos, player, playerId, recipe, result, animationOnly);
				}
			});

	/** The forge at this block (its anchor, or any block inside a loaded forge's extent), or null. */
	@Nullable
	public static DivineForgeBlockEntity find(World world, BlockPos pos) {
		return ForgeRecipes.find(world, pos);
	}

	/** Is there a forge at this block? */
	public static boolean isForge(World world, BlockPos pos) {
		return find(world, pos) != null;
	}

	/**
	 * Plays the crafting animation for {@code ticks} (1 to 72000), nothing handed over at the end. False when there is no
	 * forge there or it is busy (one crafting at a time).
	 */
	public static boolean startCrafting(ServerWorld world, BlockPos pos, int ticks) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.startAnimation(world, ticks);
	}

	/**
	 * Plays the crafting animation for {@code ticks}, then hands {@code result} to {@code player} (into the inventory, at
	 * their feet when it is full, kept in the forge until their next click when they are away). False when there is no
	 * forge there or it is busy. With a null player or an empty stack it is a bare animation.
	 */
	public static boolean startCrafting(ServerWorld world, BlockPos pos, int ticks, @Nullable ServerPlayerEntity player, ItemStack result) {
		DivineForgeBlockEntity f = find(world, pos);
		if (f == null) {
			return false;
		}
		if (player == null || result.isEmpty()) {
			return f.startAnimation(world, ticks);
		}
		return ForgeRecipes.startForApi(world, f, player, result.copy(), ticks);
	}

	/** Ends the crafting under way now (a player's result is handed over early). False when nothing was under way. */
	public static boolean stopCrafting(ServerWorld world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.stop(world);
	}

	/** Is the forge at this block crafting (or animating)? Works on the client too (its copy of the state). */
	public static boolean isCrafting(World world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.crafting();
	}

	/** Ticks left of the crafting under way (0 at rest or no forge). */
	public static long remainingTicks(World world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f == null ? 0 : f.remainingTicks();
	}

	/** Opens the forge's own interface to a player (whatever {@code workshopCommands} says). False when there is no forge. */
	public static boolean openInterface(ServerPlayerEntity player, BlockPos pos) {
		DivineForgeBlockEntity f = find(player.getEntityWorld(), pos);
		if (f == null) {
			return false;
		}
		ForgeRecipes.open(player, f);
		return true;
	}

	/** The ids of the forge recipes the server has loaded now (trial recipes left out when {@code forgeTestRecipe} is false). */
	public static List<Identifier> recipes(ServerWorld world) {
		return ForgeRecipes.all(world.getServer()).stream().map(e -> e.id().getValue()).toList();
	}
}
