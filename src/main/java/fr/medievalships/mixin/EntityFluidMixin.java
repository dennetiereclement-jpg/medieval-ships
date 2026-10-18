package fr.medievalships.mixin;

import java.util.Set;

import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import it.unimi.dsi.fastutil.objects.Object2DoubleMap;

import net.minecraft.entity.Entity;
import net.minecraft.fluid.Fluid;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.registry.tag.TagKey;

import fr.medievalships.entity.ShipInteriors;

/**
 * The compartments of a submarine are dry, even deep under the sea: an entity inside them is not
 * in the water (no swimming, no drowning, no current, no underwater view), although the world's
 * water blocks are still there (they are never replaced, so the sea is left untouched).
 */
@Mixin(Entity.class)
abstract class EntityFluidMixin {
	@Shadow
	protected Object2DoubleMap<TagKey<Fluid>> fluidHeight;
	@Shadow
	protected boolean submergedInWater;
	@Shadow
	@Final
	private Set<TagKey<Fluid>> submergedFluidTag;

	@Inject(method = "updateMovementInFluid", at = @At("HEAD"), cancellable = true)
	private void medievalships$dryCompartment(TagKey<Fluid> tag, double speed, CallbackInfoReturnable<Boolean> cir) {
		if (tag == FluidTags.WATER && ShipInteriors.dryBody((Entity) (Object) this)) {
			fluidHeight.put(tag, 0.0);
			cir.setReturnValue(false);
		}
	}

	@Inject(method = "updateSubmergedInWaterState", at = @At("TAIL"))
	private void medievalships$dryEyes(CallbackInfo ci) {
		Entity self = (Entity) (Object) this;
		if (submergedInWater || !submergedFluidTag.isEmpty()) {
			if (ShipInteriors.dryAt(self.getEntityWorld(), self.getX(), self.getEyeY(), self.getZ())) {
				submergedInWater = false;
				submergedFluidTag.clear();
			}
		}
	}
}
