package fr.medievalships.client.mixin;

import org.joml.Matrix4f;
import org.joml.Vector4f;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.mojang.blaze3d.buffers.GpuBufferSlice;

import net.minecraft.client.render.Camera;
import net.minecraft.client.render.RenderTickCounter;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.client.util.memory.ObjectAllocator;

import fr.medievalships.client.render.RenderCulling;

/**
 * Hands the projection matrix of each world render to {@link RenderCulling}: the frustum the ships' mesh cells and the
 * props are tested against (vanilla culls a whole entity, never its parts, and never a block entity drawn outside its
 * block). Optional: without it (another mod reshaping this method) nothing is culled by the mod and all is drawn.
 */
@Mixin(WorldRenderer.class)
abstract class WorldRendererMixin {
	@Inject(method = "render(Lnet/minecraft/client/util/memory/ObjectAllocator;Lnet/minecraft/client/render/RenderTickCounter;ZLnet/minecraft/client/render/Camera;"
			+ "Lorg/joml/Matrix4f;Lorg/joml/Matrix4f;Lorg/joml/Matrix4f;Lcom/mojang/blaze3d/buffers/GpuBufferSlice;Lorg/joml/Vector4f;Z)V",
			at = @At("HEAD"), require = 0)
	private void medievalships$frustum(ObjectAllocator allocator, RenderTickCounter tickCounter, boolean renderBlockOutline, Camera camera,
			Matrix4f positionMatrix, Matrix4f basicProjectionMatrix, Matrix4f projectionMatrix, GpuBufferSlice fogBuffer, Vector4f fogColor,
			boolean renderSky, CallbackInfo ci) {
		RenderCulling.frame(projectionMatrix);
	}
}
