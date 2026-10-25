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

import fr.medievalships.core.HullContact;


/** Adds the hull boxes of nearby ships to the collisions of a moving entity. */
public final class ShipCollisions {
	/** Test switch: simulates another mod replacing the collision code (the hulls are then ignored). */
	private static volatile boolean disabledForTest;

	private ShipCollisions() {
	}

	public static void disableForTest(boolean disabled) {
		disabledForTest = disabled;
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
		// a collider the entity already overlaps by a hair still stops it (see HullContact)
		Box own = entity == null ? null : entity.getBoundingBox();
		double[] body = own == null ? null : new double[] {own.minX, own.minY, own.minZ, own.maxX, own.maxY, own.maxZ};
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved() || (entity != null && entity.getRootVehicle() == ship)) {
				continue;
			}
			ship.geometry().collectBoxes(ship.pose(), ship.interiorState(), query.minX, query.minY, query.minZ, query.maxX, query.maxY, query.maxZ,
					(a, b, c, d, e, f) -> {
						double[] k = HullContact.clip(body, new double[] {a, b, c, d, e, f});
						if (k != null) {
							out.add(VoxelShapes.cuboid(k[0], k[1], k[2], k[3], k[4], k[5]));
						}
					});
		}
		return out.size() > before;
	}

	private static boolean wantsHulls(@Nullable Entity entity, World world) {
		if (disabledForTest || ShipTracker.ships(world).length == 0 || entity instanceof ShipEntity) {
			return false;
		}
		// Players are simulated by their own client, which collides them with the hull it
		// displays. The server copy of the hull runs a few ticks ahead of what that client sees;
		// colliding the player against it here would only produce false "moved wrongly" corrections.
		return !(entity instanceof ServerPlayerEntity);
	}
}
