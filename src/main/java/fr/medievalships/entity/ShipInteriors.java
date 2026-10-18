package fr.medievalships.entity;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.world.World;

import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.ShipPose;

/**
 * World queries about the interiors of the vessels with rooms (the Nautilus), used by the mixins
 * on both sides: the compartments are dry even under the sea (the world's water blocks are still
 * there, they are simply ignored inside), the ladders are climbable.
 */
public final class ShipInteriors {
	private ShipInteriors() {
	}

	/** The vessel with rooms whose interior grid contains this world point (not outside), or null. */
	@Nullable
	public static ShipEntity vesselAt(World world, double x, double y, double z) {
		ShipEntity[] ships = ShipTracker.ships(world);
		for (ShipEntity ship : ships) {
			InteriorGrid grid = ship.geometry().interior();
			if (grid == null || ship.isRemoved()) {
				continue;
			}
			double r = ship.geometry().boundingRadius();
			double dx = x - ship.getX(), dz = z - ship.getZ();
			if (dx * dx + dz * dz > r * r) {
				continue;
			}
			ShipPose pose = ship.pose();
			double[] l = pose.toLocal(x, y, z);
			if (grid.insideAt(l[0], l[1], l[2])) {
				return ship;
			}
		}
		return null;
	}

	/** Is this world point dry air inside a vessel (a compartment, an open door, the airlock pumped out)? */
	public static boolean dryAt(World world, double x, double y, double z) {
		ShipEntity[] ships = ShipTracker.ships(world);
		if (ships.length == 0) {
			return false;
		}
		for (ShipEntity ship : ships) {
			InteriorGrid grid = ship.geometry().interior();
			if (grid == null || ship.isRemoved()) {
				continue;
			}
			double r = ship.geometry().boundingRadius();
			double dx = x - ship.getX(), dz = z - ship.getZ();
			if (dx * dx + dz * dz > r * r) {
				continue;
			}
			double[] l = ship.pose().toLocal(x, y, z);
			byte kind = grid.kindAt(l[0], l[1], l[2]);
			if (kind != InteriorGrid.OUT) {
				return InteriorGrid.dry(kind, ship.interiorState());
			}
		}
		return false;
	}

	/** Is the body of this entity (feet and middle) in dry air inside a vessel? */
	public static boolean dryBody(Entity entity) {
		World world = entity.getEntityWorld();
		double x = entity.getX(), z = entity.getZ();
		return dryAt(world, x, entity.getY() + 0.2, z) && dryAt(world, x, entity.getY() + entity.getHeight() * 0.6, z);
	}

	/** Is this world point on a ladder of a vessel? */
	public static boolean ladderAt(World world, double x, double y, double z) {
		ShipEntity ship = vesselAt(world, x, y, z);
		if (ship == null) {
			return false;
		}
		double[] l = ship.pose().toLocal(x, y, z);
		return ship.geometry().interior().ladderAt(l[0], l[1], l[2]);
	}
}
