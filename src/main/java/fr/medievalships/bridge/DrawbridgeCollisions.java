package fr.medievalships.bridge;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.World;

import fr.medievalships.core.HullContact;
import fr.medievalships.entity.ShipEntity;

/**
 * The solid parts of the drawbridges whose leaves are out of the world (raised, moving, or down without their
 * blocks): the leaves' boxes at their current angle and the barriers across the deck's ends. Kept per world, on the
 * server (the bridges themselves) and on each client (what the server sent), and added to the collisions of a
 * moving entity from the same hook as the ship hulls ({@code ShipCollisions}); also an obstacle for the hulls
 * ({@code ShipWorld}). Nothing is registered while a bridge is closed: its deck is then made of real blocks.
 */
public final class DrawbridgeCollisions {
	/** A drawbridge as the collisions see it (the server's bridge object, or a client's copy). */
	public interface Source {
		/** Are the leaves out of the world (their boxes stand in for the deck)? */
		boolean leavesOut();

		/** World boxes ({minX, minY, minZ, maxX, maxY, maxZ}) of the leaves at their current angle. */
		List<double[]> leafBoxes();

		/** World boxes of the barriers across the deck's ends (while the leaves are out). */
		List<double[]> barrierBoxes();

		/** World box enclosing every box the source may produce (for a quick rejection). */
		double[] bounds();
	}

	private static final Map<World, List<Source>> BY_WORLD = new WeakHashMap<>();

	private DrawbridgeCollisions() {
	}

	public static synchronized void add(World world, Source source) {
		List<Source> list = BY_WORLD.computeIfAbsent(world, w -> new ArrayList<>());
		if (!list.contains(source)) {
			list.add(source);
		}
	}

	public static synchronized void remove(World world, Source source) {
		List<Source> list = BY_WORLD.get(world);
		if (list != null) {
			list.remove(source);
			if (list.isEmpty()) {
				BY_WORLD.remove(world);
			}
		}
	}

	public static synchronized void clear(World world) {
		BY_WORLD.remove(world);
	}

	public static synchronized void clearClientWorlds() {
		BY_WORLD.keySet().removeIf(World::isClient);
	}

	private static synchronized Source[] sources(World world) {
		List<Source> list = BY_WORLD.get(world);
		return list == null || list.isEmpty() ? new Source[0] : list.toArray(new Source[0]);
	}

	/** Any drawbridge with its leaves out in this world? */
	public static boolean any(World world) {
		for (Source s : sources(world)) {
			if (s.leavesOut()) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Adds the boxes intersecting {@code query} to a mutable list of collision shapes. The moving leaves are not given
	 * to the players on the server (they are simulated by their own client, which has the same leaves; see
	 * {@code ShipCollisions}); the barriers, static, are given to everyone.
	 *
	 * @return true if something was added
	 */
	public static boolean append(List<VoxelShape> out, @Nullable Entity entity, Box query, World world) {
		if (entity instanceof ShipEntity) {
			return false;
		}
		Source[] sources = sources(world);
		if (sources.length == 0) {
			return false;
		}
		boolean leaves = !(entity instanceof ServerPlayerEntity);
		Box own = entity == null ? null : entity.getBoundingBox();
		double[] body = own == null ? null : new double[] {own.minX, own.minY, own.minZ, own.maxX, own.maxY, own.maxZ};
		int before = out.size();
		for (Source s : sources) {
			if (!s.leavesOut()) {
				continue;
			}
			double[] b = s.bounds();
			if (b != null && (b[0] > query.maxX || b[3] < query.minX || b[1] > query.maxY || b[4] < query.minY || b[2] > query.maxZ || b[5] < query.minZ)) {
				continue;
			}
			if (leaves) {
				for (double[] w : s.leafBoxes()) {
					add(out, body, w, query);
				}
			}
			for (double[] w : s.barrierBoxes()) {
				add(out, body, w, query);
			}
		}
		return out.size() > before;
	}

	private static void add(List<VoxelShape> out, @Nullable double[] body, double[] w, Box query) {
		if (w[0] < query.maxX && w[3] > query.minX && w[1] < query.maxY && w[4] > query.minY && w[2] < query.maxZ && w[5] > query.minZ) {
			// a box the entity already overlaps by a hair still stops it (see HullContact)
			double[] k = HullContact.clip(body, w.clone());
			if (k != null) {
				out.add(VoxelShapes.cuboid(k[0], k[1], k[2], k[3], k[4], k[5]));
			}
		}
	}

	/** Is a world point inside a leaf or a barrier (an obstacle for a hull's probes)? */
	public static boolean blocked(World world, double x, double y, double z) {
		for (Source s : sources(world)) {
			if (!s.leavesOut()) {
				continue;
			}
			double[] b = s.bounds();
			if (b != null && (x < b[0] || x > b[3] || y < b[1] || y > b[4] || z < b[2] || z > b[5])) {
				continue;
			}
			for (double[] w : s.leafBoxes()) {
				if (x >= w[0] && x <= w[3] && y >= w[1] && y <= w[4] && z >= w[2] && z <= w[5]) {
					return true;
				}
			}
			for (double[] w : s.barrierBoxes()) {
				if (x >= w[0] && x <= w[3] && y >= w[1] && y <= w[4] && z >= w[2] && z <= w[5]) {
					return true;
				}
			}
		}
		return false;
	}

	/** Does this entity stand on (or just above) a leaf or a barrier (the server's anti-flight check)? */
	public static boolean standsOn(Entity e) {
		Source[] sources = sources(e.getEntityWorld());
		if (sources.length == 0) {
			return false;
		}
		Box b = e.getBoundingBox();
		double y0 = b.minY - 0.6, y1 = b.minY + 0.1;
		for (Source s : sources) {
			if (!s.leavesOut()) {
				continue;
			}
			for (double[] w : s.leafBoxes()) {
				if (b.minX < w[3] && b.maxX > w[0] && y0 < w[4] && y1 > w[1] && b.minZ < w[5] && b.maxZ > w[2]) {
					return true;
				}
			}
		}
		return false;
	}
}
