package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.fluid.FluidState;
import net.minecraft.fluid.WaterFluid;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;

import fr.medievalships.entity.ShipInteriors;

/**
 * The specks the still sea water sheds around the player (underwater particles) are not shed in the dry
 * rooms of a vessel below the waterline (the hold of the Old Corsair, the Nautilus): the water blocks of
 * the world are still there, under the hull, but the room is dry.
 */
@Mixin(WaterFluid.class)
abstract class WaterFluidMixin {
	@Inject(method = "randomDisplayTick", cancellable = true, at = @At(value = "INVOKE",
			target = "Lnet/minecraft/world/World;addParticleClient(Lnet/minecraft/particle/ParticleEffect;DDDDDD)V"))
	private void medievalships$noSpecksInDryRooms(World world, BlockPos pos, FluidState state, Random random, CallbackInfo ci) {
		if (ShipInteriors.dryAt(world, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5)) {
			ci.cancel();
		}
	}
}
