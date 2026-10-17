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
		GalleyEntity[] ships = ShipTracker.ships(world);
		if (ships.length == 0) {
			return collisions;
		}
		if (entity instanceof GalleyEntity) {
			return collisions;
		}
		// Players are simulated by their own client, which collides them with the hull it
		// displays. The server copy of the hull runs a few ticks ahead of what that client sees;
		// colliding the player against it here would only produce false "moved wrongly" corrections.
		if (entity instanceof ServerPlayerEntity) {
			return collisions;
		}
		Box q = box.stretch(movement);
		List<VoxelShape> out = null;
		for (GalleyEntity ship : ships) {
			if (ship.isRemoved() || (entity != null && entity.getRootVehicle() == ship)) {
				continue;
			}
			List<VoxelShape> target = out != null ? out : new ArrayList<>(collisions);
			int before = target.size();
			ShipGeometry.collectBoxes(ship.pose(), q.minX, q.minY, q.minZ, q.maxX, q.maxY, q.maxZ,
					(a, b, c, d, e, f) -> target.add(VoxelShapes.cuboid(a, b, c, d, e, f)));
			if (target.size() > before || out != null) {
				out = target;
			}
		}
		return out != null ? out : collisions;
	}
}
