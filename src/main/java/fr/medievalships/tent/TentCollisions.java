package fr.medievalships.tent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;
import fr.medievalships.entity.ShipEntity;

/**
 * The solid parts of the placed tents (posts, platforms, railings, furniture): static world boxes, kept per world
 * and per chunk, filled when a tent block is placed or its chunk loads (block entity load events) and emptied when
 * it is broken or its chunk unloads. {@link #append} adds the boxes near a moving entity to its collisions, from the
 * same mixin as the ship hulls ({@code EntityCollisionMixin} through {@code ShipCollisions}). No scan, no tick.
 */
public final class TentCollisions {
	/** A placed tent: its anchor, its type, its facing and its boxes in world coordinates. */
	public record Placed(BlockPos pos, TentType type, int quarter, List<Box> boxes, Box extent) {
	}

	/** Per world (server worlds and client worlds alike): chunk -> tents whose extent touches that chunk. */
	private static final Map<World, Map<Long, List<Placed>>> BY_WORLD = new HashMap<>();
	private static final Map<World, Map<BlockPos, Placed>> BY_POS = new HashMap<>();

	private TentCollisions() {
	}

	/** World boxes of a tent at an anchor with a facing. */
	public static List<Box> worldBoxes(TentType type, BlockPos pos, int quarter) {
		List<Box> out = new ArrayList<>();
		double cx = pos.getX() + 0.5, cy = pos.getY(), cz = pos.getZ() + 0.5;
		for (TentType.Box b : type.colliders(quarter)) {
			out.add(new Box(cx + b.x0(), cy + b.y0(), cz + b.z0(), cx + b.x1(), cy + b.y1(), cz + b.z1()));
		}
		return out;
	}

	/** The world box of a tent's extent at an anchor with a facing. */
	public static Box worldExtent(TentType type, BlockPos pos, int quarter) {
		TentType.Box e = type.extent(quarter);
		double cx = pos.getX() + 0.5, cy = pos.getY(), cz = pos.getZ() + 0.5;
		return new Box(cx + e.x0(), cy + e.y0(), cz + e.z0(), cx + e.x1(), cy + e.y1(), cz + e.z1());
	}

	public static synchronized void add(World world, BlockPos pos, TentType type, int quarter) {
		pos = pos.toImmutable();
		Map<BlockPos, Placed> byPos = BY_POS.computeIfAbsent(world, w -> new HashMap<>());
		Placed old = byPos.get(pos);
		if (old != null && old.type() == type && old.quarter() == quarter) {
			return; // already known (placed, then its chunk's load event)
		}
		if (old != null) {
			remove(world, pos);
		}
		Placed placed = new Placed(pos, type, quarter, List.copyOf(worldBoxes(type, pos, quarter)), worldExtent(type, pos, quarter));
		byPos.put(pos, placed);
		Map<Long, List<Placed>> chunks = BY_WORLD.computeIfAbsent(world, w -> new HashMap<>());
		for (long key : chunksOf(placed.extent())) {
			chunks.computeIfAbsent(key, k -> new ArrayList<>()).add(placed);
		}
	}

	public static synchronized void remove(World world, BlockPos pos) {
		Map<BlockPos, Placed> byPos = BY_POS.get(world);
		if (byPos == null) {
			return;
		}
		Placed placed = byPos.remove(pos);
		if (placed == null) {
			return;
		}
		Map<Long, List<Placed>> chunks = BY_WORLD.get(world);
		if (chunks != null) {
			for (long key : chunksOf(placed.extent())) {
				List<Placed> list = chunks.get(key);
				if (list != null) {
					list.remove(placed);
					if (list.isEmpty()) {
						chunks.remove(key);
					}
				}
			}
		}
	}

	public static synchronized void clear(World world) {
		BY_WORLD.remove(world);
		BY_POS.remove(world);
	}

	/** Client worlds, on disconnect. */
	public static synchronized void clearClientWorlds() {
		BY_WORLD.keySet().removeIf(World::isClient);
		BY_POS.keySet().removeIf(World::isClient);
	}

	@Nullable
	public static synchronized Placed at(World world, BlockPos pos) {
		Map<BlockPos, Placed> byPos = BY_POS.get(world);
		return byPos == null ? null : byPos.get(pos);
	}

	/** The tents known in a world (loaded chunks). */
	public static synchronized List<Placed> all(World world) {
		Map<BlockPos, Placed> byPos = BY_POS.get(world);
		return byPos == null ? List.of() : new ArrayList<>(byPos.values());
	}

	/** Any tent known in this world? (cheap: the common case of a world without tents skips everything) */
	public static synchronized boolean any(World world) {
		Map<Long, List<Placed>> chunks = BY_WORLD.get(world);
		return chunks != null && !chunks.isEmpty();
	}

	public static synchronized int count(World world) {
		Map<BlockPos, Placed> byPos = BY_POS.get(world);
		return byPos == null ? 0 : byPos.size();
	}

	/**
	 * Adds the tent boxes intersecting {@code query} to a mutable list of collision shapes.
	 *
	 * @return true if something was added
	 */
	public static boolean append(List<VoxelShape> out, @Nullable Entity entity, Box query, World world) {
		if (entity instanceof ShipEntity) {
			return false;
		}
		List<Placed> near;
		synchronized (TentCollisions.class) {
			Map<Long, List<Placed>> chunks = BY_WORLD.get(world);
			if (chunks == null || chunks.isEmpty()) {
				return false;
			}
			near = null;
			int cx0 = ((int) Math.floor(query.minX)) >> 4, cx1 = ((int) Math.floor(query.maxX)) >> 4;
			int cz0 = ((int) Math.floor(query.minZ)) >> 4, cz1 = ((int) Math.floor(query.maxZ)) >> 4;
			for (int cx = cx0; cx <= cx1; cx++) {
				for (int cz = cz0; cz <= cz1; cz++) {
					List<Placed> list = chunks.get(ChunkPos.toLong(cx, cz));
					if (list != null) {
						if (near == null) {
							near = new ArrayList<>();
						}
						for (Placed p : list) {
							if (!near.contains(p)) {
								near.add(p);
							}
						}
					}
				}
			}
		}
		if (near == null) {
			return false;
		}
		int before = out.size();
		for (Placed p : near) {
			if (!p.extent().intersects(query)) {
				continue;
			}
			for (Box b : p.boxes()) {
				if (b.intersects(query)) {
					out.add(VoxelShapes.cuboid(b));
				}
			}
		}
		return out.size() > before;
	}

	private static List<Long> chunksOf(Box extent) {
		List<Long> keys = new ArrayList<>();
		int cx0 = ((int) Math.floor(extent.minX)) >> 4, cx1 = ((int) Math.floor(extent.maxX)) >> 4;
		int cz0 = ((int) Math.floor(extent.minZ)) >> 4, cz1 = ((int) Math.floor(extent.maxZ)) >> 4;
		for (int cx = cx0; cx <= cx1; cx++) {
			for (int cz = cz0; cz <= cz1; cz++) {
				keys.add(ChunkPos.toLong(cx, cz));
			}
		}
		return keys;
	}
}
