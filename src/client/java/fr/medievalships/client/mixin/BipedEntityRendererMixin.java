package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.item.ItemModelManager;
import net.minecraft.client.render.entity.BipedEntityRenderer;
import net.minecraft.client.render.entity.state.BipedEntityRenderState;
import net.minecraft.entity.LivingEntity;

import fr.medievalships.entity.ShipEntity;

/** A player holding the helm of a vessel stands at the wheel instead of sitting. */
@Mixin(BipedEntityRenderer.class)
abstract class BipedEntityRendererMixin {
	@Inject(method = "updateBipedRenderState", at = @At("TAIL"))
	private static void medievalships$standAtTheHelm(LivingEntity entity, BipedEntityRenderState state, float tickProgress,
			ItemModelManager itemModelResolver, CallbackInfo ci) {
		if (entity.getVehicle() instanceof ShipEntity ship && ship.standsAtHelm(entity)) {
			state.hasVehicle = false;
		}
	}
}
