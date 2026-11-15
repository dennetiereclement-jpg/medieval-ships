package fr.medievalships.tent;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.command.permission.LeveledPermissionPredicate;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.MedievalShips;
import fr.medievalships.api.WorkshopUseCallback;
import fr.medievalships.core.TentType;
import fr.medievalships.data.ConfigManager;

/**
 * What a right click on a crafting workshop does on the server (1.22.0) — a light, generic hook, no recipes, no
 * interface and no progression of the mod's own:
 * <ol>
 * <li>spectators: nothing; at most one use every {@link #COOLDOWN_TICKS} ticks per player (the others are swallowed);</li>
 * <li>the {@link WorkshopUseCallback} event (another mod may handle the click and cancel what follows);</li>
 * <li>the command configured for the workshop's profession ({@code "workshopCommands"} of the server settings), run as
 * the player ({@code @s}), at their position, silently, with the permission level of a command block (2): only the
 * server's config chooses the command, the player merely triggers it;</li>
 * <li>else a short action-bar message ("Établi du joaillier — aucune interface de fabrication n'est reliée").</li>
 * </ol>
 */
public final class WorkshopInteraction {
	/** One use every 10 ticks (half a second) per player at most. */
	public static final int COOLDOWN_TICKS = 10;
	/** Translation key of the message shown when nothing is linked ({@code %s} = the workshop's name). */
	public static final String UNLINKED_KEY = "message.medievalships.workshop_unlinked";
	private static final Map<UUID, Integer> LAST_USE = new HashMap<>();

	private WorkshopInteraction() {
	}

	/** The server side of a click on the workshop {@code type} at {@code pos} (see the class comment). */
	public static ActionResult use(ServerPlayerEntity player, ServerWorld world, BlockPos pos, TentType type) {
		if (player.isSpectator()) {
			return ActionResult.PASS;
		}
		MinecraftServer server = world.getServer();
		int now = server.getTicks();
		Integer last = LAST_USE.get(player.getUuid());
		if (last != null && now >= last && now - last < COOLDOWN_TICKS) {
			return ActionResult.SUCCESS;
		}
		if (LAST_USE.size() > 256) {
			LAST_USE.values().removeIf(t -> now < t || now - t >= COOLDOWN_TICKS);
		}
		LAST_USE.put(player.getUuid(), now);
		String profession = type.profession();
		ActionResult result = WorkshopUseCallback.EVENT.invoker().interact(player, world, pos, type, profession);
		if (result != ActionResult.PASS) {
			return result;
		}
		String command = ConfigManager.server().workshopCommand(profession);
		if (command != null) {
			ServerCommandSource source = player.getCommandSource(world).withAdditionalPermissions(LeveledPermissionPredicate.GAMEMASTERS)
					.withSilent();
			try {
				server.getCommandManager().parseAndExecute(source, command);
			} catch (RuntimeException e) {
				MedievalShips.LOGGER.warn("workshopCommands.{}: \"{}\" failed", profession, command, e);
			}
		} else {
			Text name = Text.translatable("block.medievalships." + type.id());
			player.sendMessage(Text.translatableWithFallback(UNLINKED_KEY, "%s — aucune interface de fabrication n'est reliée", name), true);
		}
		return ActionResult.SUCCESS;
	}
}
