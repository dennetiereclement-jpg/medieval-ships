package fr.medievalships.entity;

import org.jetbrains.annotations.Nullable;

import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.FlightConfig;
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

	/** Heading steps (degrees) of a placement: the preview and the click use the same rounded heading. */
	public static final float YAW_STEP = 2f;

	/**
	 * What a placement starts from, the same for the preview (client) and the click (server): the point of the aimed
	 * block face, its two in-face coordinates moved to the middle of the face (the coordinate across the face is the
	 * face's own, the same anywhere on it, rounded to 1/4096 block so the rounding error of the ray does not move it),
	 * and the heading rounded to {@link #YAW_STEP} degrees. While the player aims at the same face with the same
	 * rounded heading, both sides compute exactly the same spot.
	 */
	public record Aim(double x, double y, double z, float yaw) {
		public static Aim of(net.minecraft.util.hit.BlockHitResult hit, float yaw) {
			net.minecraft.util.math.BlockPos b = hit.getBlockPos();
			net.minecraft.util.math.Vec3d p = hit.getPos();
			net.minecraft.util.math.Direction.Axis across = hit.getSide().getAxis();
			double x = across == net.minecraft.util.math.Direction.Axis.X ? onFace(p.x) : b.getX() + 0.5;
			double y = across == net.minecraft.util.math.Direction.Axis.Y ? onFace(p.y) : b.getY() + 0.5;
			double z = across == net.minecraft.util.math.Direction.Axis.Z ? onFace(p.z) : b.getZ() + 0.5;
			return new Aim(x, y, z, snapYaw(yaw));
		}

		/** The face's coordinate, without the ray's rounding error (block faces are on 1/16 steps). */
		static double onFace(double v) {
			return Math.round(v * 4096.0) / 4096.0;
		}
	}

	/** The heading rounded to {@link #YAW_STEP} degrees. */
	public static float snapYaw(float yaw) {
		return Math.round(yaw / YAW_STEP) * YAW_STEP;
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
		FlightConfig flight = fr.medievalships.data.ConfigManager.ship(type).flight;
		return find(world, type, x, y, z, yaw, ahead, flight == null ? Double.POSITIVE_INFINITY : flight.maxAltitude);
	}

	/**
	 * {@link #find(World, ShipType, double, double, double, float, boolean)} with the aircraft's altitude ceiling given
	 * (the client's preview passes the server's, see {@link fr.medievalships.data.SyncedConfig}).
	 */
	@Nullable
	public static Spot find(World world, ShipType type, double x, double y, double z, float yaw, boolean ahead, double maxAltitude) {
		ShipWorld shipWorld = new ShipWorld(world, null, x, y, z);
		if (type.geometry().flying()) {
			return findInTheAir(shipWorld, type, x, y, z, yaw, ahead, maxAltitude);
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
	private static Spot findInTheAir(ShipWorld shipWorld, ShipType type, double x, double y, double z, float yaw, boolean ahead,
			double ceiling) {
		double fx = -Math.sin(Math.toRadians(yaw)), fz = Math.cos(Math.toRadians(yaw));
		double h = type.hull().halfLength;
		double[] offsets = ahead ? new double[] {h + 2, h + 6, h - 2, 0} : new double[] {0, 0.5 * h, -0.5 * h};
		double base = y + 1.0 - type.geometry().lowestY();
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

	/**
	 * Where a ship given a destination at (x, z) would stop: {@code known} false when the chunk there is not loaded
	 * (nothing can be checked; the point is kept), else the nearest point to (x, z) whose water is open around the
	 * hull's half width, at the ship's own water level.
	 */
	public record WaterSpot(boolean known, double x, double z) {
	}

	/**
	 * The open water nearest to (x, z) within {@code radius} blocks for this ship (the point itself if it is open
	 * water), or null if there is none: the column and four columns the hull's half width around it are navigable
	 * (open water two blocks deep at the ship's waterline, nothing solid above, no other hull). Only loaded chunks are
	 * read; a few thousand block reads at most, once per command.
	 */
	@Nullable
	public static WaterSpot openWaterNear(ShipEntity ship, double x, double z, int radius) {
		ShipWorld w = new ShipWorld(ship.getEntityWorld(), ship, x, ship.getY(), z);
		if (!w.isLoaded(x, z)) {
			return new WaterSpot(false, x, z);
		}
		double hw = ship.geometry().hull().maxHalfWidth;
		for (int r = 0; r <= radius; r += 2) {
			int n = r == 0 ? 1 : Math.max(8, (int) Math.ceil(Math.PI * r));
			for (int k = 0; k < n; k++) {
				double a = 2 * Math.PI * k / n;
				double cx = x + r * Math.cos(a), cz = z + r * Math.sin(a);
				if (w.navigable(cx, cz) && w.navigable(cx + hw, cz) && w.navigable(cx - hw, cz) && w.navigable(cx, cz + hw)
						&& w.navigable(cx, cz - hw)) {
					return new WaterSpot(true, cx, cz);
				}
			}
		}
		return null;
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
