package fr.medievalships.mixin.compat;

import java.util.List;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.entity.Entity;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.entity.ShipCollisions;

/**
 * Lithium replaces the vanilla entity movement collision code (Entity#collide /
 * collideBoundingBox) and gathers entity collisions itself, so the vanilla hook never runs when it
 * is installed. Its entity collision gathering goes through this method: add the hulls there too.
 * Only applied when Lithium is present.
 */
@Pseudo
@Mixin(targets = "net.caffeinemc.mods.lithium.common.entity.LithiumEntityCollisions", remap = false)
abstract class LithiumEntityCollisionsMixin {
	@Inject(method = "appendEntityCollisions", at = @At("TAIL"), remap = false, require = 0)
	private static void medievalships$appendHulls(List<VoxelShape> entityCollisions, World world, Entity entity, Box box,
			CallbackInfo ci) {
		ShipCollisions.appendHulls(entityCollisions, entity, box, world);
	}
}
