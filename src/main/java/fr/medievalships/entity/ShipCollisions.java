package fr.medievalships.entity;

import java.util.ArrayList;
import java.util.List;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.World;

import fr.medievalships.core.ShipGeometry;

/** Adds the hull boxes of nearby ships to the collisions of a moving entity. */
public final class ShipCollisions {
	private ShipCollisions() {
	}

	public static List<VoxelShape> withHulls(List<VoxelShape> collisions, @Nullable Entity entity, Vec3d movement, Box box, World world) {
		if (!wantsHulls(entity, world)) {
			return collisions;
		}
		List<VoxelShape> out = new ArrayList<>(collisions);
		return appendHulls(out, entity, box.stretch(movement), world) ? out : collisions;
	}

	/**
	 * Adds the hull boxes intersecting {@code query} to a mutable list. Used by our own mixin and by
	 * the compatibility hook for mods that replace the vanilla collision code (Lithium).
	 *
	 * @return true if something was added
	 */
	public static boolean appendHulls(List<VoxelShape> out, @Nullable Entity entity, Box query, World world) {
		if (!wantsHulls(entity, world)) {
			return false;
		}
		int before = out.size();
		for (GalleyEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved() || (entity != null && entity.getRootVehicle() == ship)) {
				continue;
			}
			ShipGeometry.collectBoxes(ship.pose(), query.minX, query.minY, query.minZ, query.maxX, query.maxY, query.maxZ,
					(a, b, c, d, e, f) -> out.add(VoxelShapes.cuboid(a, b, c, d, e, f)));
		}
		return out.size() > before;
	}

	private static boolean wantsHulls(@Nullable Entity entity, World world) {
		if (ShipTracker.ships(world).length == 0 || entity instanceof GalleyEntity) {
			return false;
		}
		// Players are simulated by their own client, which collides them with the hull it
		// displays. The server copy of the hull runs a few ticks ahead of what that client sees;
		// colliding the player against it here would only produce false "moved wrongly" corrections.
		return !(entity instanceof ServerPlayerEntity);
	}
}
