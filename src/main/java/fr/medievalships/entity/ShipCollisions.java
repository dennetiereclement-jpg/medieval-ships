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
	/**
	 * Benchmark counters ({@code PerfGameTest}), [0] for server worlds, [1] for client worlds: calls of the movement hook,
	 * ships whose hull was asked for boxes, boxes added, nanoseconds spent in the hook. Plain counters written by the
	 * world's thread and read between ticks by the test.
	 */
	public static final long[] CALLS = new long[2];
	public static final long[] SHIPS = new long[2];
	public static final long[] BOXES = new long[2];
	public static final long[] NANOS = new long[2];

	private ShipCollisions() {
	}

	/** {calls, ships, boxes, nanos} of a side ({@code client}: client worlds). */
	public static long[] stats(boolean client) {
		int i = client ? 1 : 0;
		return new long[] {CALLS[i], SHIPS[i], BOXES[i], NANOS[i]};
	}

	public static void disableForTest(boolean disabled) {
		disabledForTest = disabled;
	}

	public static List<VoxelShape> withHulls(List<VoxelShape> collisions, @Nullable Entity entity, Vec3d movement, Box box, World world) {
		long t0 = System.nanoTime();
		int side = world.isClient() ? 1 : 0;
		CALLS[side]++;
		try {
			boolean hulls = wantsHulls(entity, world);
			if (!hulls && !fr.medievalships.tent.TentCollisions.any(world) && !fr.medievalships.bridge.DrawbridgeCollisions.any(world)) {
				return collisions;
			}
			List<VoxelShape> out = new ArrayList<>(collisions);
			Box query = box.stretch(movement);
			boolean added = hulls && appendHulls(out, entity, query, world);
			// the posts, platforms and furniture of the tents (static boxes, see TentCollisions)
			added |= fr.medievalships.tent.TentCollisions.append(out, entity, query, world);
			// the raised or moving leaves of the drawbridges and the barriers across their ends (1.24.0)
			added |= fr.medievalships.bridge.DrawbridgeCollisions.append(out, entity, query, world);
			return added ? out : collisions;
		} finally {
			NANOS[side] += System.nanoTime() - t0;
		}
	}

	/**
	 * Adds the hull boxes intersecting {@code query} to a mutable list. Used by our own mixin and by
	 * the compatibility hook for mods that replace the vanilla collision code (Lithium).
	 *
	 * @return true if something was added
	 */
	public static boolean appendHulls(List<VoxelShape> out, @Nullable Entity entity, Box query, World world) {
		boolean tents = fr.medievalships.tent.TentCollisions.append(out, entity, query, world);
		tents |= fr.medievalships.bridge.DrawbridgeCollisions.append(out, entity, query, world);
		if (!wantsHulls(entity, world)) {
			return tents;
		}
		int before = out.size();
		int side = world.isClient() ? 1 : 0;
		// a collider the entity already overlaps by a hair still stops it (see HullContact)
		Box own = entity == null ? null : entity.getBoundingBox();
		double[] body = own == null ? null : new double[] {own.minX, own.minY, own.minZ, own.maxX, own.maxY, own.maxZ};
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved() || (entity != null && entity.getRootVehicle() == ship)) {
				continue;
			}
			SHIPS[side]++;
			fr.medievalships.core.ShipGeometry.BoxSink sink = (a, b, c, d, e, f) -> {
				BOXES[side]++;
				double[] k = HullContact.clip(body, new double[] {a, b, c, d, e, f});
				if (k != null) {
					out.add(VoxelShapes.cuboid(k[0], k[1], k[2], k[3], k[4], k[5]));
				}
			};
			ship.geometry().collectBoxes(ship.pose(), ship.interiorState(), ship.gangplankWallGap(), query.minX, query.minY, query.minZ,
					query.maxX, query.maxY, query.maxZ, sink);
			// a deployed gangplank: its steps along the slope and its inboard stairs
			ship.collectGangplankBoxes(query.minX, query.minY, query.minZ, query.maxX, query.maxY, query.maxZ, sink);
		}
		return tents || out.size() > before;
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
