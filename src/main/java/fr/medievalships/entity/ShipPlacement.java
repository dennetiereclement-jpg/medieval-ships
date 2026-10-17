package fr.medievalships.entity;

import org.jetbrains.annotations.Nullable;

import net.minecraft.server.world.ServerWorld;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;

/** Finds valid water for a new ship and spawns it. */
public final class ShipPlacement {
	private ShipPlacement() {
	}

	/**
	 * Spawns a ship of the given type near (x, z) facing {@code yaw}. When {@code ahead} is true the ship is pushed
	 * forward so its stern starts at the clicked point (the player is not inside the hull).
	 *
	 * @return the ship, or null if there is not enough open water
	 */
	@Nullable
	public static ShipEntity place(ServerWorld world, ShipType type, double x, double y, double z, float yaw, boolean ahead) {
		ShipEntity ship = MedievalShips.entityType(type).create(world, net.minecraft.entity.SpawnReason.COMMAND);
		if (ship == null) {
			return null;
		}
		ship.refreshPositionAndAngles(x, y, z, yaw, 0f); // the obstacle scan looks around the ship's position
		ShipWorld shipWorld = new ShipWorld(world, ship);
		double fx = -Math.sin(Math.toRadians(yaw)), fz = Math.cos(Math.toRadians(yaw));
		double h = type.hull().halfLength;
		double[] offsets = ahead ? new double[] {h + 2, h - 2, h + 6, h - 6, 0} : new double[] {0, 0.4 * h, -0.4 * h, 0.8 * h, -0.8 * h};
		for (double off : offsets) {
			double cx = x + fx * off, cz = z + fz * off;
			double surface = shipWorld.waterSurface(cx, cz, y);
			if (Double.isNaN(surface)) {
				continue;
			}
			ShipPose pose = new ShipPose(cx, surface, cz, yaw);
			if (ShipMover.countCollisions(type.geometry(), pose, shipWorld) == 0) {
				ship.refreshPositionAndAngles(cx, surface, cz, yaw, 0f);
				ship.setShipYaw(yaw);
				world.spawnEntity(ship);
				return ship;
			}
		}
		return null;
	}

	/** Moves a ship to the nearest open water position (within 24 blocks). */
	public static boolean unstuck(ShipEntity ship) {
		if (!(ship.getEntityWorld() instanceof ServerWorld world)) {
			return false;
		}
		ShipWorld shipWorld = new ShipWorld(world, ship);
		for (int r = 0; r <= 24; r += 2) {
			for (int a = 0; a < 360; a += r == 0 ? 360 : 15) {
				double cx = ship.getX() - Math.sin(Math.toRadians(a)) * r;
				double cz = ship.getZ() + Math.cos(Math.toRadians(a)) * r;
				double surface = shipWorld.waterSurface(cx, cz, ship.getY());
				if (Double.isNaN(surface)) {
					continue;
				}
				for (int dyaw = 0; dyaw < 360; dyaw += 45) {
					float yaw = ship.getYaw() + dyaw;
					if (ShipMover.countCollisions(ship.geometry(), new ShipPose(cx, surface, cz, yaw), shipWorld) == 0) {
						ship.refreshPositionAndAngles(cx, surface, cz, yaw, 0f);
						ship.setShipYaw(yaw);
						ship.physics().speed = 0;
						ship.physics().yawRate = 0;
						return true;
					}
				}
			}
		}
		return false;
	}
}
