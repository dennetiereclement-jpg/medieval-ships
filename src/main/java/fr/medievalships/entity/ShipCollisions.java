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
			// the vanilla list is copied only once something is really added (a mob far from every hull, tent and
			// bridge, the common case on a big server, costs no allocation here)
			Lazy out = new Lazy(collisions);
			Box query = box.stretch(movement);
			if (hulls) {
				appendHulls(out, entity, query, world);
			}
			// the posts, platforms and furniture of the tents (static boxes, see TentCollisions)
			fr.medievalships.tent.TentCollisions.append(out, entity, query, world);
			// the raised or moving leaves of the drawbridges and the barriers across their ends (1.24.0)
			fr.medievalships.bridge.DrawbridgeCollisions.append(out, entity, query, world);
			return out.list == null ? collisions : out.list;
		} finally {
			NANOS[side] += System.nanoTime() - t0;
		}
	}

	/** A copy of the vanilla collision list made at the first shape added to it; before that, a read-only view of it. */
	private static final class Lazy extends java.util.AbstractList<VoxelShape> {
		private final List<VoxelShape> base;
		List<VoxelShape> list;

		Lazy(List<VoxelShape> base) {
			this.base = base;
		}

		@Override
		public VoxelShape get(int index) {
			return list == null ? base.get(index) : list.get(index);
		}

		@Override
		public int size() {
			return list == null ? base.size() : list.size();
		}

		@Override
		public boolean add(VoxelShape shape) {
			if (list == null) {
				list = new ArrayList<>(base.size() + 8);
				list.addAll(base);
			}
			return list.add(shape);
		}

		@Override
		public void add(int index, VoxelShape shape) {
			if (index != size()) {
				throw new UnsupportedOperationException();
			}
			add(shape);
		}
	}

	/**
	 * Broad phase of a hull: may the query box touch it at all? The hull's bounding circle, widened by the reach of a
	 * deployed gangplank (its steps run down to the quay, outside the hull), against the box; nothing of the ship (its
	 * pose, the doors, the wall gap, the cells) is computed for a far one.
	 */
	private static boolean mayTouch(ShipEntity ship, Box q) {
		double rx = (q.maxX - q.minX) / 2, rz = (q.maxZ - q.minZ) / 2;
		double reach = ship.geometry().boundingRadius() + rx + rz + (ship.gangplank() != null && ship.gangplankState().out() ? GANGPLANK_REACH : 0);
		double dx = (q.minX + q.maxX) / 2 - ship.getX(), dz = (q.minZ + q.maxZ) / 2 - ship.getZ();
		return dx * dx + dz * dz <= reach * reach;
	}

	/** How far outside the hull's bounding circle a deployed gangplank's steps and stairs may reach (blocks). */
	private static final double GANGPLANK_REACH = 20;

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
		fr.medievalships.core.ShipGeometry.BoxSink sink = null;
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved() || (entity != null && entity.getRootVehicle() == ship) || !mayTouch(ship, query)) {
				continue;
			}
			SHIPS[side]++;
			if (sink == null) {
				// a collider the entity already overlaps by a hair still stops it (see HullContact)
				Box own = entity == null ? null : entity.getBoundingBox();
				double[] body = own == null ? null : new double[] {own.minX, own.minY, own.minZ, own.maxX, own.maxY, own.maxZ};
				sink = (a, b, c, d, e, f) -> {
					BOXES[side]++;
					double[] k = HullContact.clip(body, new double[] {a, b, c, d, e, f});
					if (k != null) {
						out.add(VoxelShapes.cuboid(k[0], k[1], k[2], k[3], k[4], k[5]));
					}
				};
			}
			ship.geometry().collectBoxes(ship.pose(), ship.interiorState(), ship.gangplankWallGap(), query.minX, query.minY, query.minZ,
					query.maxX, query.maxY, query.maxZ, sink);
			// a deployed gangplank: its steps along the slope and its inboard stairs
			ship.collectGangplankBoxes(query.minX, query.minY, query.minZ, query.maxX, query.maxY, query.maxZ, sink);
			// the side ladders (1.30.0): the slab a climber rests against, outboard of the hull
			fr.medievalships.core.SideLadder.collectBoxes(fr.medievalships.core.SideLadder.of(ship.shipType().id()),
					ship.geometry().hull().waterlineY, ship.pose(), query.minX, query.minY, query.minZ, query.maxX, query.maxY, query.maxZ, sink);
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
