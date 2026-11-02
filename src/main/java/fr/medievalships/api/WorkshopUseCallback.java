package fr.medievalships.api;

import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.TentType;

/**
 * Fired on the server when a player (not a spectator) right-clicks one of the mod's crafting workshops (1.22.0), at
 * most once every 10 ticks per player: the hook through which another mod links a crafting / profession system to the
 * workshops. The mod itself has no recipes, no crafting interface and no progression.
 *
 * <p>Return {@link ActionResult#PASS} to let the mod carry on: it runs the command configured for the profession
 * ({@code "workshopCommands"} in {@code config/medievalships.json}), else it shows a short action-bar message. Any
 * other result cancels that and becomes the result of the click (e.g. {@link ActionResult#SUCCESS} after opening your
 * own screen). Listeners are called in registration order until one returns something else than PASS.
 *
 * <pre>{@code
 * WorkshopUseCallback.EVENT.register((player, world, pos, type, profession) -> {
 *     if (!"jeweler".equals(profession)) return ActionResult.PASS;
 *     MyCrafting.openJewellerMenu(player);
 *     return ActionResult.SUCCESS;
 * });
 * }</pre>
 */
@FunctionalInterface
public interface WorkshopUseCallback {
	Event<WorkshopUseCallback> EVENT = EventFactory.createArrayBacked(WorkshopUseCallback.class,
			listeners -> (player, world, pos, type, profession) -> {
				for (WorkshopUseCallback listener : listeners) {
					ActionResult result = listener.interact(player, world, pos, type, profession);
					if (result != ActionResult.PASS) {
						return result;
					}
				}
				return ActionResult.PASS;
			});

	/**
	 * @param player     the player who clicked (survival, adventure or creative)
	 * @param world      the workshop's world
	 * @param pos        the workshop's anchor block
	 * @param type       the workshop ({@link TentType#id()}: {@code workshop_jeweler}...)
	 * @param profession its profession id ({@link TentType#profession()}: {@code jeweler}, {@code blacksmith}...)
	 * @return PASS to let the mod run the configured command (or show its message), anything else to cancel it
	 */
	ActionResult interact(ServerPlayerEntity player, ServerWorld world, BlockPos pos, TentType type, String profession);
}
