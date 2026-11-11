package fr.medievalships.client.render;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.entity.Entity;
import net.minecraft.fluid.FluidState;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.ChunkSectionPos;

import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The water of the world is not drawn inside the dry rooms of a vessel (a hold under the waterline, the Nautilus at
 * the surface: without this the surface of the sea would be seen across the hold, its companionway and the floor
 * slabs). The world is not changed: only the drawing of the water blocks that lie in the rooms is skipped (the rule is
 * {@link InteriorGrid#hidesWater}: 27 points of the block, hidden when one is dry and none outside the hull, a block
 * straddling the outer hull only when the dry points outnumber the outside ones, and always when its top face lies
 * wholly within the hull), and the chunk sections around the hull are drawn again when the vessel appears, moves, or
 * opens a door.
 *
 * <p>The skipping is done by {@link DryWaterFluidHandler}, Fabric API's fluid render handler (honoured by the vanilla
 * chunk builder and by Sodium's), with {@code FluidRendererMixin} on the vanilla renderer as a fallback.
 *
 * <p>Read by the chunk builder threads: the hulls are an immutable snapshot published each tick.
 *
 * <p>Safety nets against sections meshed before their hull was known (joining a server, the chunks and the vessels
 * arrive in any order; a vessel is seen here one tick after its entity): the sections around a hull are drawn again on
 * its first sight, once more two seconds later, and, while the local player stands in a dry room near the sea level,
 * every five seconds the sections of the water band around the hull that were not meshed since its last redraw (each
 * section meshed near a hull stamps the time of the snapshot it used) are scheduled again.
 */
public final class DryWater {
	private record Hull(ShipPose pose, InteriorGrid grid, InteriorGrid.State state, double radius) {
	}

	/** The hulls as the chunk builder threads see them, and the world time they were published at. */
	private record Snapshot(Hull[] hulls, long time) {
	}

	/** Per ship: the pose and state its sections were last drawn again for, and when; its first sight; the checks done. */
	private static final class Seen {
		ShipPose pose;
		InteriorGrid.State state;
		long drawnAt;
		final long firstSeen;
		boolean secondLook;
		long staleCheckAt = Long.MIN_VALUE / 2;

		Seen(long now) {
			firstSeen = now;
		}
	}

	private static volatile Snapshot snapshot = new Snapshot(new Hull[0], 0);
	private static final Map<Integer, Seen> seen = new HashMap<>();
	/** Sections meshed with a hull within reach of their water, by section position: the time of the snapshot they used. */
	private static final ConcurrentHashMap<Long, Long> meshed = new ConcurrentHashMap<>();

	private static final double REDRAW_DISTANCE = 96;
	/** Ticks after the first sight of a vessel before its sections are drawn again once more. */
	private static final int SECOND_LOOK = 40;
	/** Ticks between two checks of the stale sections around the hull the player stands in. */
	private static final int STALE_PERIOD = 100;
	/** Ticks after a redraw before its sections may be found stale (the meshing has to catch up first). */
	private static final int STALE_SETTLE = 40;
	/** How far from the sea level the player's eyes may be for the stale check, and the depth of the water band checked. */
	private static final double SEA_BAND = 3;

	private DryWater() {
	}

	/** Called once at client init: hooks the water's render handler. */
	public static void init() {
		DryWaterFluidHandler.register();
	}

	/** Forgets everything (leaving a world). */
	public static void clear() {
		snapshot = new Snapshot(new Hull[0], 0);
		seen.clear();
		meshed.clear();
	}

	/** Is the water block at this position inside the dry rooms of a vessel (not to be drawn)? */
	public static boolean hidden(BlockPos pos) {
		return hidden(snapshot, pos, false);
	}

	/**
	 * The chunk builder's question for a water block it meshes: {@link #hidden}, and the section is stamped with the
	 * snapshot it used when a hull is within reach of the block (so that the stale check knows it was meshed in the know).
	 */
	static boolean skip(BlockPos pos) {
		return hidden(snapshot, pos, true);
	}

	private static boolean hidden(Snapshot s, BlockPos pos, boolean stamp) {
		Hull[] hs = s.hulls;
		if (hs.length == 0) {
			return false;
		}
		double x = pos.getX() + 0.5, z = pos.getZ() + 0.5;
		boolean near = false;
		for (Hull h : hs) {
			double dx = x - h.pose.x(), dz = z - h.pose.z();
			if (dx * dx + dz * dz > h.radius * h.radius) {
				continue;
			}
			if (stamp && !near) {
				near = true;
				stamp(pos, s.time);
			}
			if (h.grid.hidesWater(h.pose, pos.getX(), pos.getY(), pos.getZ(), h.state)) {
				return true;
			}
		}
		return false;
	}

	private static void stamp(BlockPos pos, long time) {
		long key = ChunkSectionPos.asLong(pos.getX() >> 4, pos.getY() >> 4, pos.getZ() >> 4);
		Long t = meshed.get(key);
		if (t == null || t < time) {
			meshed.put(key, time);
		}
	}

	/**
	 * Client tick: new snapshot; the sections around a hull are drawn again when it is first seen (placed, loaded,
	 * teleported, or tracked from afar: whatever the distance, so that sections built before it arrived are redone),
	 * once more two seconds later, and when it moved or opened a door while near the player (at most twice a second);
	 * the stale check runs while the player stands in a dry room near the sea level.
	 */
	public static void tick(MinecraftClient client, ClientWorld world) {
		List<Hull> list = new ArrayList<>();
		long now = world.getTime();
		Map<Integer, Seen> kept = new HashMap<>();
		Entity player = client.player;
		for (ShipEntity ship : ShipTracker.ships(world)) {
			InteriorGrid grid = ship.geometry().interior();
			if (grid == null || ship.isRemoved()) {
				continue;
			}
			ShipPose pose = ship.pose();
			InteriorGrid.State state = ship.interiorState();
			double r = ship.geometry().boundingRadius();
			list.add(new Hull(pose, grid, state, r));
			Seen s = seen.get(ship.getId());
			boolean first = s == null;
			if (first) {
				s = new Seen(now);
			}
			boolean near = player != null && player.squaredDistanceTo(ship) < (REDRAW_DISTANCE + r) * (REDRAW_DISTANCE + r);
			boolean changed = first || moved(s.pose, pose) || !state.equals(s.state);
			if (changed && (first || (near && now - s.drawnAt >= 10))) {
				redraw(client, pose, r, grid);
				if (!first) {
					redraw(client, s.pose, r, grid);
				}
				s.pose = pose;
				s.state = state;
				s.drawnAt = now;
			} else if (!s.secondLook && now - s.firstSeen >= SECOND_LOOK) {
				// the chunks that arrived after the first sight were meshed with the hull known; those that arrived just
				// before it, in the same batch, may have been meshed without it: one more pass
				s.secondLook = true;
				redraw(client, pose, r, grid);
				s.drawnAt = now;
			}
			if (player != null && now - s.drawnAt >= STALE_SETTLE && now - s.staleCheckAt >= STALE_PERIOD && inside(player, pose, grid, state, r)) {
				double sea = seaLevel(world, pose, grid);
				if (!Double.isNaN(sea) && Math.abs(player.getEyeY() - sea) <= SEA_BAND) {
					s.staleCheckAt = now;
					redrawStale(client, pose, r, sea, s.drawnAt);
				}
			}
			kept.put(ship.getId(), s);
		}
		seen.clear();
		seen.putAll(kept);
		if (list.isEmpty()) {
			if (!meshed.isEmpty()) {
				meshed.clear();
			}
		} else if (now % STALE_PERIOD == 0) {
			prune(list);
		}
		snapshot = new Snapshot(list.toArray(new Hull[0]), now);
	}

	private static boolean moved(ShipPose a, ShipPose b) {
		double dx = a.x() - b.x(), dy = a.y() - b.y(), dz = a.z() - b.z();
		return dx * dx + dy * dy + dz * dz > 0.04 || Math.abs(ShipPose.wrapDegrees(a.yaw() - b.yaw())) > 0.5;
	}

	private static void redraw(MinecraftClient client, ShipPose pose, double r, InteriorGrid grid) {
		if (client.worldRenderer == null) {
			return;
		}
		int y0 = (int) Math.floor(pose.y() + grid.y0) - 1, y1 = (int) Math.ceil(pose.y() + grid.y0 + grid.ny * grid.cell) + 1;
		client.worldRenderer.scheduleBlockRenders((int) Math.floor(pose.x() - r) - 1, y0, (int) Math.floor(pose.z() - r) - 1,
				(int) Math.ceil(pose.x() + r) + 1, y1, (int) Math.ceil(pose.z() + r) + 1);
	}

	/** Are the player's eyes in a dry room of this hull? */
	private static boolean inside(Entity player, ShipPose pose, InteriorGrid grid, InteriorGrid.State state, double r) {
		double ex = player.getX(), ey = player.getEyeY(), ez = player.getZ();
		double dx = ex - pose.x(), dz = ez - pose.z();
		if (dx * dx + dz * dz > r * r) {
			return false;
		}
		double[] l = pose.toLocal(ex, ey, ez);
		return grid.dryAt(l[0], l[1], l[2], state);
	}

	/**
	 * The surface of the water in the hull's centre column, within the height of its grid (the water of the world is
	 * still there under the vessel); NaN when there is none (a dry dock, an airship).
	 */
	private static double seaLevel(ClientWorld world, ShipPose pose, InteriorGrid grid) {
		int x = (int) Math.floor(pose.x()), z = (int) Math.floor(pose.z());
		int top = (int) Math.ceil(pose.y() + grid.y0 + grid.ny * grid.cell), bottom = (int) Math.floor(pose.y() + grid.y0) - 1;
		BlockPos.Mutable p = new BlockPos.Mutable();
		for (int y = top; y >= bottom; y--) {
			p.set(x, y, z);
			FluidState f = world.getFluidState(p);
			if (f.isIn(FluidTags.WATER)) {
				return y + f.getHeight(world, p);
			}
		}
		return Double.NaN;
	}

	/**
	 * Schedules again the sections of the water band around the hull (from {@link #SEA_BAND} under the sea level to just
	 * above it, within the hull's radius) that were not meshed since the hull's last redraw.
	 */
	private static void redrawStale(MinecraftClient client, ShipPose pose, double r, double sea, long drawnAt) {
		if (client.worldRenderer == null) {
			return;
		}
		int sx0 = ((int) Math.floor(pose.x() - r) - 1) >> 4, sx1 = ((int) Math.ceil(pose.x() + r) + 1) >> 4;
		int sz0 = ((int) Math.floor(pose.z() - r) - 1) >> 4, sz1 = ((int) Math.ceil(pose.z() + r) + 1) >> 4;
		int sy0 = ((int) Math.floor(sea - SEA_BAND)) >> 4, sy1 = ((int) Math.floor(sea + 1)) >> 4;
		for (int sx = sx0; sx <= sx1; sx++) {
			for (int sz = sz0; sz <= sz1; sz++) {
				// the nearest point of the section's column to the hull's axis must be within its radius
				double nx = Math.max(sx * 16, Math.min(pose.x(), sx * 16 + 16)) - pose.x();
				double nz = Math.max(sz * 16, Math.min(pose.z(), sz * 16 + 16)) - pose.z();
				if (nx * nx + nz * nz > r * r) {
					continue;
				}
				for (int sy = sy0; sy <= sy1; sy++) {
					Long t = meshed.get(ChunkSectionPos.asLong(sx, sy, sz));
					if (t == null || t < drawnAt) {
						client.worldRenderer.scheduleChunkRender(sx, sy, sz);
					}
				}
			}
		}
	}

	/** Drops the stamps of the sections far from every hull. */
	private static void prune(List<Hull> hulls) {
		meshed.keySet().removeIf(key -> {
			double cx = ChunkSectionPos.unpackX(key) * 16 + 8, cz = ChunkSectionPos.unpackZ(key) * 16 + 8;
			for (Hull h : hulls) {
				double dx = cx - h.pose.x(), dz = cz - h.pose.z(), reach = h.radius + 12;
				if (dx * dx + dz * dz <= reach * reach) {
					return false;
				}
			}
			return true;
		});
	}
}
