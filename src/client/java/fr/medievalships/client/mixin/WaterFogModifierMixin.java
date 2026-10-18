package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.render.Camera;
import net.minecraft.client.render.RenderTickCounter;
import net.minecraft.client.render.fog.FogData;
import net.minecraft.client.render.fog.WaterFogModifier;
import net.minecraft.client.world.ClientWorld;

import fr.medievalships.client.render.ShipFog;

/**
 * The sea fog seen from a dry room: clear over the length of a room, then as thick as for a
 * swimmer whose eyes have got used to the water (the player in the room is not in the water, so his
 * own underwater visibility would make it far too thick).
 */
@Mixin(WaterFogModifier.class)
abstract class WaterFogModifierMixin {
	@Inject(method = "applyStartEndModifier", at = @At("TAIL"))
	private void medievalships$fromADryRoom(FogData data, Camera camera, ClientWorld world, float viewDistance, RenderTickCounter counter,
			CallbackInfo ci) {
		if (ShipFog.inDryRoomUnderWater(camera)) {
			data.environmentalStart = ShipFog.CLEAR_DISTANCE;
			data.environmentalEnd = ShipFog.END_DISTANCE;
			data.skyEnd = data.environmentalEnd;
			data.cloudEnd = data.environmentalEnd;
		}
	}
}
