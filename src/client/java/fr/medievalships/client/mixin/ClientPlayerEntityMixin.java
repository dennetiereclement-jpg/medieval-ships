package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;

import fr.medievalships.client.render.ShipFog;

/**
 * From a dry room under the sea the player sees the water as a swimmer whose eyes have got used to it:
 * the vanilla fog colour is brightened to the clear blue of the sea (instead of staying near black, the
 * player himself not being in the water).
 */
@Mixin(ClientPlayerEntity.class)
abstract class ClientPlayerEntityMixin {
	@Inject(method = "getUnderwaterVisibility", at = @At("HEAD"), cancellable = true)
	private void medievalships$eyesUsedToTheSea(CallbackInfoReturnable<Float> cir) {
		MinecraftClient client = MinecraftClient.getInstance();
		if (client.gameRenderer != null && ShipFog.inDryRoomUnderWater(client.gameRenderer.getCamera())) {
			cir.setReturnValue(1f);
		}
	}
}
