package fr.medievalships.api;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.forge.DivineForge;
import fr.medievalships.forge.DivineForgeBlockEntity;

/**
 * The divine forge for other mods (1.34.0): the forge crafts nothing and is linked to nothing; a mod (a profession or
 * crafting system of the server's own) can make it look busy — the fire and the heat columns brighter, the gears
 * faster, the hammer blows and sparks, the magic sound at the end — for as long as it wants, and hear when that ends.
 * Server side only (the state is synced: {@link #isActive} also answers on the client); every method takes the forge's
 * anchor block or any block inside its extent. Commands for the same: {@code /forge animer|arreter|etat}. See
 * docs/FORGE.md.
 *
 * <pre>{@code
 * // 10 s of activity while my own system crafts something
 * DivineForgeApi.startActivity(world, pos, 200);
 * DivineForgeApi.ACTIVITY_FINISHED.register((world, pos, stopped) -> {
 *     if (!stopped) MySystem.forgeDone(world, pos);
 * });
 * }</pre>
 */
public final class DivineForgeApi {
	private DivineForgeApi() {
	}

	/** An activity has just started ({@code /forge animer} or {@link #startActivity}). */
	@FunctionalInterface
	public interface ActivityStarted {
		void onStarted(ServerWorld world, BlockPos pos, int ticks);
	}

	/** An activity has ended. */
	@FunctionalInterface
	public interface ActivityFinished {
		/**
		 * @param pos     the forge's anchor block
		 * @param stopped ended before its time ({@code /forge arreter}, {@link #stopActivity}, the forge removed); false when
		 *                its time elapsed
		 */
		void onFinished(ServerWorld world, BlockPos pos, boolean stopped);
	}

	public static final Event<ActivityStarted> ACTIVITY_STARTED = EventFactory.createArrayBacked(ActivityStarted.class,
			listeners -> (world, pos, ticks) -> {
				for (ActivityStarted l : listeners) {
					l.onStarted(world, pos, ticks);
				}
			});

	public static final Event<ActivityFinished> ACTIVITY_FINISHED = EventFactory.createArrayBacked(ActivityFinished.class,
			listeners -> (world, pos, stopped) -> {
				for (ActivityFinished l : listeners) {
					l.onFinished(world, pos, stopped);
				}
			});

	/** The forge at this block (its anchor, or any block inside a loaded forge's extent), or null. */
	@Nullable
	public static DivineForgeBlockEntity find(World world, BlockPos pos) {
		return DivineForge.find(world, pos);
	}

	/** Is there a forge at this block? */
	public static boolean isForge(World world, BlockPos pos) {
		return find(world, pos) != null;
	}

	/**
	 * Makes the forge active for {@code ticks} (1 to 72000): its activity animation, then the magic sound and the
	 * {@link #ACTIVITY_FINISHED} event. False when there is no forge there or it is already active (one at a time).
	 */
	public static boolean startActivity(ServerWorld world, BlockPos pos, int ticks) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.startActivity(world, ticks);
	}

	/** The same as {@link #startActivity} (the name of the first plans). */
	public static boolean startCrafting(ServerWorld world, BlockPos pos, int ticks) {
		return startActivity(world, pos, ticks);
	}

	/** Ends the activity under way now. False when there was none. */
	public static boolean stopActivity(ServerWorld world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.stop(world);
	}

	/** Is the forge at this block active? Works on the client too (its copy of the state). */
	public static boolean isActive(World world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f != null && f.active();
	}

	/** Ticks left of the activity under way (0 at rest or no forge). */
	public static long remainingTicks(World world, BlockPos pos) {
		DivineForgeBlockEntity f = find(world, pos);
		return f == null ? 0 : f.remainingTicks();
	}
}
