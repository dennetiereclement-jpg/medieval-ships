package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.GameRenderer;

import fr.medievalships.client.ShipPicker;

@Mixin(GameRenderer.class)
abstract class GameRendererMixin {
	@Inject(method = "updateCrosshairTarget", at = @At("RETURN"))
	private void medievalships$pickShips(float tickDelta, CallbackInfo ci) {
		ShipPicker.update(MinecraftClient.getInstance(), tickDelta);
	}
}
