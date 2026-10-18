package fr.medievalships.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.entity.LivingEntity;

import fr.medievalships.entity.ShipInteriors;

/** The ladders of a vessel's interior grid are climbable like vanilla ladders. */
@Mixin(LivingEntity.class)
abstract class LivingEntityLadderMixin {
	@Inject(method = "isClimbing", at = @At("HEAD"), cancellable = true)
	private void medievalships$vesselLadder(CallbackInfoReturnable<Boolean> cir) {
		LivingEntity self = (LivingEntity) (Object) this;
		// on the rungs, or just stepping out at the top of the ladder (the rungs under the feet)
		if (!self.isSpectator() && (ShipInteriors.ladderAt(self.getEntityWorld(), self.getX(), self.getY() + 0.3, self.getZ())
				|| ShipInteriors.ladderAt(self.getEntityWorld(), self.getX(), self.getY() - 0.45, self.getZ()))) {
			cir.setReturnValue(true);
		}
	}
}
