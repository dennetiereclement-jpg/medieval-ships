package fr.medievalships.entity;

import org.jetbrains.annotations.Nullable;

import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;

/** Finds valid water for a new ship and spawns it. */
public final class ShipPlacement {
	private ShipPlacement() {
	}

	/**
	 * Where a vessel would be placed: {@code pose} and whether it fits ({@code valid}). When it does not fit, the
	 * pose is the first one that was tried (for the red preview).
	 */
	public record Spot(ShipPose pose, boolean valid) {
	}

	/**
	 * Spawns a ship of the given type near (x, z) facing {@code yaw}. When {@code ahead} is true the ship is pushed
	 * forward so its stern starts at the clicked point (the player is not inside the hull).
	 *
	 * @return the ship, or null if there is not enough open water
	 */
	@Nullable
	public static ShipEntity place(ServerWorld world, ShipType type, double x, double y, double z, float yaw, boolean ahead) {
		Spot spot = find(world, type, x, y, z, yaw, ahead);
		if (spot == null || !spot.valid()) {
			return null;
		}
		ShipEntity ship = MedievalShips.entityType(type).create(world, net.minecraft.entity.SpawnReason.COMMAND);
		if (ship == null) {
			return null;
		}
		ShipPose p = spot.pose();
		ship.refreshPositionAndAngles(p.x(), p.y(), p.z(), yaw, 0f);
		ship.setShipYaw(yaw);
		world.spawnEntity(ship);
		return ship;
	}

	/**
	 * The space check of the placement, the same on the server (item, {@code /ship spawn}) and on the client (the
	 * preview of the item): the first pose near (x, z) facing {@code yaw} where the whole vessel is inside nothing
	 * (terrain, buildings, other hulls) — a ship floating on open water, an aircraft above whatever was clicked.
	 *
	 * @return the pose and whether it fits, or null for a ship when there is no water at all to show it on
	 */
	@Nullable
	public static Spot find(World world, ShipType type, double x, double y, double z, float yaw, boolean ahead) {
		ShipWorld shipWorld = new ShipWorld(world, null, x, y, z);
		if (type.geometry().flying()) {
			return findInTheAir(shipWorld, type, x, y, z, yaw, ahead);
		}
		double fx = -Math.sin(Math.toRadians(yaw)), fz = Math.cos(Math.toRadians(yaw));
		double h = type.hull().halfLength;
		double[] offsets = ahead ? new double[] {h + 2, h - 2, h + 6, h - 6, 0} : new double[] {0, 0.4 * h, -0.4 * h, 0.8 * h, -0.8 * h};
		ShipPose first = null;
		for (double off : offsets) {
			double cx = x + fx * off, cz = z + fz * off;
			double surface = shipWorld.waterSurface(cx, cz, y);
			if (Double.isNaN(surface)) {
				continue;
			}
			double sy = surface - type.hull().waterlineY;
			ShipPose pose = new ShipPose(cx, sy, cz, yaw);
			if (!ShipMover.collides(type.geometry(), pose, shipWorld)) {
				return new Spot(pose, true);
			}
			if (first == null) {
				first = pose;
			}
		}
		return first == null ? null : new Spot(first, false);
	}

	/**
	 * Aircraft: anywhere above the ground or the water where the whole aircraft fits (balloon,
	 * fins, propeller), its keel a block above the clicked surface or higher, never inside a hill
	 * or a building.
	 */
	private static Spot findInTheAir(ShipWorld shipWorld, ShipType type, double x, double y, double z, float yaw, boolean ahead) {
		double fx = -Math.sin(Math.toRadians(yaw)), fz = Math.cos(Math.toRadians(yaw));
		double h = type.hull().halfLength;
		double[] offsets = ahead ? new double[] {h + 2, h + 6, h - 2, 0} : new double[] {0, 0.5 * h, -0.5 * h};
		double base = y + 1.0 - type.geometry().lowestY();
		double ceiling = fr.medievalships.data.ConfigManager.ship(type).flight.maxAltitude;
		ShipPose first = new ShipPose(x + fx * offsets[0], base, z + fz * offsets[0], yaw);
		for (double off : offsets) {
			double cx = x + fx * off, cz = z + fz * off;
			for (double dy = 0; dy <= 16; dy += 1.0) {
				ShipPose pose = new ShipPose(cx, base + dy, cz, yaw);
				if (pose.y() + type.geometry().topY() > ceiling) {
					break;
				}
				if (!ShipMover.collides(type.geometry(), pose, shipWorld)) {
					return new Spot(pose, true);
				}
			}
		}
		return new Spot(first, false);
	}

	/** Moves a ship to the nearest open water position (within 24 blocks); an aircraft to the nearest free space. */
	public static boolean unstuck(ShipEntity ship) {
		if (!(ship.getEntityWorld() instanceof ServerWorld world)) {
			return false;
		}
		ShipWorld shipWorld = new ShipWorld(world, ship);
		if (ship.geometry().flying()) {
			for (int r = 0; r <= 24; r += 2) {
				for (int a = 0; a < 360; a += r == 0 ? 360 : 30) {
					for (int dy = 0; dy <= 24; dy += 2) {
						double cx = ship.getX() - Math.sin(Math.toRadians(a)) * r;
						double cz = ship.getZ() + Math.cos(Math.toRadians(a)) * r;
						ShipPose pose = new ShipPose(cx, ship.getY() + dy, cz, ship.getYaw());
						if (ShipMover.countCollisions(ship.geometry(), pose, shipWorld) == 0) {
							ship.refreshPositionAndAngles(cx, pose.y(), cz, ship.getYaw(), 0f);
							ship.physics().speed = 0;
							ship.physics().yawRate = 0;
							ship.flight().vy = 0;
							return true;
						}
					}
				}
			}
			return false;
		}
		for (int r = 0; r <= 24; r += 2) {
			for (int a = 0; a < 360; a += r == 0 ? 360 : 15) {
				double cx = ship.getX() - Math.sin(Math.toRadians(a)) * r;
				double cz = ship.getZ() + Math.cos(Math.toRadians(a)) * r;
				double waterline = ship.geometry().hull().waterlineY;
				double surface = shipWorld.waterSurface(cx, cz, ship.getY() + waterline);
				if (Double.isNaN(surface)) {
					continue;
				}
				surface -= waterline;
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
