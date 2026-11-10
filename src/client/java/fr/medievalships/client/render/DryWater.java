package fr.medievalships.client.render;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The water of the world is not drawn inside the dry rooms of a vessel (a hold under the waterline, the Nautilus at
 * the surface: without this the surface of the sea would be seen across the hold, its companionway and the floor
 * slabs). The world is not changed: only the drawing of the water blocks that lie in the rooms is skipped (the rule is
 * {@link InteriorGrid#hidesWater}: 27 points of the block, hidden when one is dry and none outside the hull, a block
 * straddling the outer hull only when the dry points outnumber the outside ones), and the chunk sections around the
 * hull are drawn again when the vessel appears, moves, or opens a door.
 *
 * <p>Read by the chunk builder threads: the hulls are an immutable snapshot published each tick.
 */
public final class DryWater {
	private record Hull(ShipPose pose, InteriorGrid grid, InteriorGrid.State state, double radius) {
	}

	private static volatile Hull[] hulls = new Hull[0];
	/** Per ship: pose and state when its sections were last drawn again, and when. */
	private static final Map<Integer, Object[]> drawn = new HashMap<>();
	private static final double REDRAW_DISTANCE = 96;

	private DryWater() {
	}

	/** Is the water block at this position inside the dry rooms of a vessel (not to be drawn)? */
	public static boolean hidden(BlockPos pos) {
		Hull[] hs = hulls;
		if (hs.length == 0) {
			return false;
		}
		double x = pos.getX() + 0.5, z = pos.getZ() + 0.5;
		for (Hull h : hs) {
			double dx = x - h.pose.x(), dz = z - h.pose.z();
			if (dx * dx + dz * dz > h.radius * h.radius) {
				continue;
			}
			if (h.grid.hidesWater(h.pose, pos.getX(), pos.getY(), pos.getZ(), h.state)) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Client tick: new snapshot; the sections around a hull are drawn again when it is first seen (placed, loaded,
	 * teleported, or tracked from afar: whatever the distance, so that sections built before it arrived are redone),
	 * and when it moved or opened a door while near the player (at most twice a second).
	 */
	public static void tick(MinecraftClient client, ClientWorld world) {
		List<Hull> list = new ArrayList<>();
		long now = world.getTime();
		Map<Integer, Object[]> seen = new HashMap<>();
		for (ShipEntity ship : ShipTracker.ships(world)) {
			InteriorGrid grid = ship.geometry().interior();
			if (grid == null || ship.isRemoved()) {
				continue;
			}
			ShipPose pose = ship.pose();
			InteriorGrid.State state = ship.interiorState();
			double r = ship.geometry().boundingRadius();
			list.add(new Hull(pose, grid, state, r));
			Object[] last = drawn.get(ship.getId());
			boolean first = last == null;
			boolean near = client.player != null && client.player.squaredDistanceTo(ship) < (REDRAW_DISTANCE + r) * (REDRAW_DISTANCE + r);
			boolean changed = first || moved((ShipPose) last[0], pose) || !state.equals(last[1]);
			if (changed && (first || (near && now - (Long) last[2] >= 10))) {
				redraw(client, pose, r, grid);
				if (!first) {
					redraw(client, (ShipPose) last[0], r, grid);
				}
				last = new Object[] {pose, state, now};
			}
			seen.put(ship.getId(), last);
		}
		drawn.clear();
		drawn.putAll(seen);
		hulls = list.toArray(new Hull[0]);
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
}
