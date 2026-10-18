package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.block.enums.CameraSubmersionType;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.Camera;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.entity.ShipInteriors;

/** Inside a dry compartment of a submarine the camera is not under water: no blue fog. */
@Mixin(Camera.class)
abstract class CameraMixin {
	@Shadow
	public abstract Vec3d getCameraPos();

	@Inject(method = "getSubmersionType", at = @At("HEAD"), cancellable = true)
	private void medievalships$dryCompartment(CallbackInfoReturnable<CameraSubmersionType> cir) {
		MinecraftClient client = MinecraftClient.getInstance();
		if (client.world == null) {
			return;
		}
		Vec3d p = getCameraPos();
		if (ShipInteriors.dryAt(client.world, p.x, p.y, p.z)) {
			cir.setReturnValue(CameraSubmersionType.NONE);
		}
	}
}
