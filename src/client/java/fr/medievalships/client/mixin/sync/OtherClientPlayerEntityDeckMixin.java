package fr.medievalships.client.mixin.sync;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.network.OtherClientPlayerEntity;

import fr.medievalships.client.DeckClient;

/** Another player standing on a moving deck (1.30.0) is drawn at his deck position on the hull, see {@link DeckClient}. */
@Mixin(OtherClientPlayerEntity.class)
abstract class OtherClientPlayerEntityDeckMixin {
	@Inject(method = "tickMovement", at = @At("HEAD"))
	private void medievalships$onDeck(CallbackInfo ci) {
		DeckClient.beforeRemoteMovement((OtherClientPlayerEntity) (Object) this);
	}
}
