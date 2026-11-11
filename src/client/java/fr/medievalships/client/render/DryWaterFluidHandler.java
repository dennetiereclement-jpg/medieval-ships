package fr.medievalships.client.render;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.client.render.fluid.v1.FluidRenderHandler;
import net.fabricmc.fabric.api.client.render.fluid.v1.FluidRenderHandlerRegistry;

import net.minecraft.block.BlockState;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.texture.Sprite;
import net.minecraft.client.texture.SpriteAtlasTexture;
import net.minecraft.fluid.Fluid;
import net.minecraft.fluid.FluidState;
import net.minecraft.fluid.Fluids;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.BlockRenderView;

/**
 * Fabric API's render handler for the water (still and flowing), wrapped: the handler registered before this mod (Fabric
 * API's own, or another mod's) still draws everything, this one only skips the blocks inside the dry rooms of a vessel
 * ({@link DryWater#skip}).
 *
 * <p>This is the path every chunk meshing pipeline honours. The vanilla {@code FluidRenderer.render} is cancelled at
 * its head by Fabric API's mixin, which calls {@code FluidRenderHandler.renderFluid} of the registered handler and only
 * draws the vanilla geometry when the handler asks for it. Sodium never calls the vanilla renderer: its
 * {@code net.caffeinemc.mods.sodium.fabric.render.FluidRendererImpl.render} looks the handler up in
 * {@code FluidRenderHandlerRegistry} and calls {@code FluidRendering.render(handler, ...)}, that is
 * {@code handler.renderFluid}, with its own fast renderer as the default geometry; so returning early here draws nothing
 * under Sodium as well (and under Iris or Nvidium, which build on Sodium's meshing). The mixin on the vanilla renderer
 * ({@code FluidRendererMixin}) stays as a fallback for a client where another mod registers its own water handler after
 * this one, without Sodium.
 */
final class DryWaterFluidHandler implements FluidRenderHandler {
	private final FluidRenderHandler delegate;

	private DryWaterFluidHandler(FluidRenderHandler delegate) {
		this.delegate = delegate;
	}

	/** Wraps the handlers of the still and the flowing water (once). */
	static void register() {
		for (Fluid fluid : new Fluid[] {Fluids.WATER, Fluids.FLOWING_WATER}) {
			FluidRenderHandler previous = FluidRenderHandlerRegistry.INSTANCE.get(fluid);
			if (previous != null && !(previous instanceof DryWaterFluidHandler)) {
				FluidRenderHandlerRegistry.INSTANCE.register(fluid, new DryWaterFluidHandler(previous));
			}
		}
	}

	@Override
	public Sprite[] getFluidSprites(@Nullable BlockRenderView view, @Nullable BlockPos pos, FluidState state) {
		return delegate.getFluidSprites(view, pos, state);
	}

	@Override
	public int getFluidColor(@Nullable BlockRenderView view, @Nullable BlockPos pos, FluidState state) {
		return delegate.getFluidColor(view, pos, state);
	}

	@Override
	public void renderFluid(BlockPos pos, BlockRenderView world, VertexConsumer vertexConsumer, BlockState blockState, FluidState fluidState) {
		if (DryWater.skip(pos)) {
			return;
		}
		delegate.renderFluid(pos, world, vertexConsumer, blockState, fluidState);
	}

	@Override
	public void reloadTextures(SpriteAtlasTexture textureAtlas) {
		delegate.reloadTextures(textureAtlas);
	}
}
