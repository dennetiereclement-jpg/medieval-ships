package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.block.BlockState;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.block.FluidRenderer;
import net.minecraft.fluid.FluidState;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.BlockRenderView;

import fr.medievalships.client.render.DryWater;

/** The water of the world is not drawn inside the dry rooms of a vessel (see {@link DryWater}). */
@Mixin(FluidRenderer.class)
abstract class FluidRendererMixin {
	@Inject(method = "render", at = @At("HEAD"), cancellable = true)
	private void medievalships$dryRooms(BlockRenderView world, BlockPos pos, VertexConsumer vertexConsumer, BlockState blockState,
			FluidState fluidState, CallbackInfo ci) {
		if (fluidState.isIn(FluidTags.WATER) && DryWater.hidden(pos)) {
			ci.cancel();
		}
	}
}
