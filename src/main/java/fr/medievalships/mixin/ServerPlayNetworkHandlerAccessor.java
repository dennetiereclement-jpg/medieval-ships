package fr.medievalships.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

import net.minecraft.server.network.ServerPlayNetworkHandler;

/**
 * The vanilla anti-flight check only looks at blocks under the player: on the raised decks the
 * water is too far below the feet, so players standing there must have their counter reset.
 */
@Mixin(ServerPlayNetworkHandler.class)
public interface ServerPlayNetworkHandlerAccessor {
	@Accessor("floatingTicks")
	void medievalships$setFloatingTicks(int ticks);
}
