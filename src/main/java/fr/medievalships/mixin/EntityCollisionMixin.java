package fr.medievalships.mixin;

import java.util.List;

import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

import net.minecraft.entity.Entity;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.entity.ShipCollisions;

/**
 * Every entity movement (walking, falling, step-up) goes through this static method with the
 * list of entity collision shapes: the ship decks and hull walls are added to that list, so
 * players and mobs can stand and walk on board.
 */
@Mixin(Entity.class)
abstract class EntityCollisionMixin {
	@ModifyVariable(
			method = "adjustMovementForCollisions(Lnet/minecraft/entity/Entity;Lnet/minecraft/util/math/Vec3d;Lnet/minecraft/util/math/Box;Lnet/minecraft/world/World;Ljava/util/List;)Lnet/minecraft/util/math/Vec3d;",
			at = @At("HEAD"),
			argsOnly = true)
	private static List<VoxelShape> medievalships$addHulls(List<VoxelShape> collisions, @Nullable Entity entity, Vec3d movement,
			Box box, World world, List<VoxelShape> originalCollisions) {
		return ShipCollisions.withHulls(collisions, entity, movement, box, world);
	}

	/** The step-up path (walking into a wall or a deck step) gathers its colliders here. */
	@ModifyVariable(
			method = "findCollisionsForMovement(Lnet/minecraft/entity/Entity;Lnet/minecraft/world/World;Ljava/util/List;Lnet/minecraft/util/math/Box;)Ljava/util/List;",
			at = @At("HEAD"),
			argsOnly = true)
	private static List<VoxelShape> medievalships$addHullsForStep(List<VoxelShape> collisions, @Nullable Entity entity, World world,
			List<VoxelShape> originalCollisions, Box box) {
		return ShipCollisions.withHulls(collisions, entity, Vec3d.ZERO, box, world);
	}
}
