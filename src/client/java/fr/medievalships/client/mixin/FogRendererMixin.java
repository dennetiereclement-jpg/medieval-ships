package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.block.enums.CameraSubmersionType;
import net.minecraft.client.render.Camera;
import net.minecraft.client.render.fog.FogRenderer;

import fr.medievalships.client.render.ShipFog;

/**
 * In a dry compartment of a submerged vessel the fog is the fog of the sea (blue, closing in with
 * distance, as for a swimmer), so that the sea seen through the windows and portholes looks like the
 * sea seen in it; {@link WaterFogModifierMixin} keeps the room itself clear.
 */
@Mixin(FogRenderer.class)
abstract class FogRendererMixin {
	@Inject(method = "getCameraSubmersionType", at = @At("RETURN"), cancellable = true)
	private void medievalships$seaBehindTheGlass(Camera camera, CallbackInfoReturnable<CameraSubmersionType> cir) {
		if (cir.getReturnValue() == CameraSubmersionType.ATMOSPHERIC && ShipFog.inDryRoomUnderWater(camera)) {
			cir.setReturnValue(CameraSubmersionType.WATER);
		}
	}
}
