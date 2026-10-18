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
 * The water of the world is not drawn inside the dry rooms of a vessel (the Nautilus at the
 * surface: without this the surface of the sea would be seen across its engine room and its
 * staircase). The world is not changed: only the drawing of the water blocks whose centre lies in
 * a dry cell is skipped, and the chunk sections around the hull are drawn again when it moves.
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
		double x = pos.getX() + 0.5, y = pos.getY() + 0.5, z = pos.getZ() + 0.5;
		for (Hull h : hs) {
			double dx = x - h.pose.x(), dz = z - h.pose.z();
			if (dx * dx + dz * dz > h.radius * h.radius) {
				continue;
			}
			double[] l = h.pose.toLocal(x, y, z);
			byte k = h.grid.kindAt(l[0], l[1], l[2]);
			if (k != InteriorGrid.OUT) {
				return h.grid.dry(k, l[1], h.state);
			}
		}
		return false;
	}

	/** Client tick: new snapshot; the sections around a hull that moved are drawn again (at most twice a second). */
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
			boolean near = client.player != null && client.player.squaredDistanceTo(ship) < (REDRAW_DISTANCE + r) * (REDRAW_DISTANCE + r);
			boolean changed = last == null || moved((ShipPose) last[0], pose) || !state.equals(last[1]);
			if (near && changed && (last == null || now - (Long) last[2] >= 10)) {
				redraw(client, pose, r, grid);
				if (last != null) {
					redraw(client, (ShipPose) last[0], r, grid);
				}
				last = new Object[] {pose, state, now};
			}
			seen.put(ship.getId(), last == null ? new Object[] {pose, state, now} : last);
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
		int y0 = (int) Math.floor(pose.y() + grid.y0), y1 = (int) Math.ceil(pose.y() + grid.y0 + grid.ny * grid.cell);
		client.worldRenderer.scheduleBlockRenders((int) Math.floor(pose.x() - r), y0, (int) Math.floor(pose.z() - r),
				(int) Math.ceil(pose.x() + r), y1, (int) Math.ceil(pose.z() + r));
	}
}
