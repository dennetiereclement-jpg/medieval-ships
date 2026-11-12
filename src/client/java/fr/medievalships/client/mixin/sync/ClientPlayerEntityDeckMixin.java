package fr.medievalships.client.mixin.sync;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.network.ClientPlayerEntity;

import fr.medievalships.client.DeckClient;

/**
 * The local player on a moving deck (1.30.0, see {@link DeckClient}): carried before he walks if the hull already moved
 * this tick, and the hull he is carried with sent just before his movement packet.
 */
@Mixin(ClientPlayerEntity.class)
abstract class ClientPlayerEntityDeckMixin {
	@Inject(method = "tick", at = @At("HEAD"))
	private void medievalships$carryFirst(CallbackInfo ci) {
		DeckClient.beforePlayerTick((ClientPlayerEntity) (Object) this);
	}

	@Inject(method = "sendMovementPackets", at = @At("HEAD"))
	private void medievalships$deckFrame(CallbackInfo ci) {
		DeckClient.beforeMovementPackets((ClientPlayerEntity) (Object) this);
	}
}
