package fr.medievalships.entity;

import java.util.List;

import net.minecraft.entity.Entity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.world.World;

import fr.medievalships.core.SideLadder;

/**
 * World queries about the side ladders of the vessels ({@link SideLadder}, 1.30.0), used on both sides: by the
 * {@code LivingEntity#isClimbing} mixin (the same zone on the client that predicts the climb and on the server), by the
 * carrying of the climbers along with a moving hull and by the server's anti-flight reset. Broad phase first (the hull's
 * bounding circle), no allocation.
 */
public final class ShipLadders {
	/** Ticks of a moving ship's travel the server allows for between its own hull and the one the player's client saw. */
	private static final double LAG_TICKS = 10;

	private ShipLadders() {
	}

	/** Is this entity on a side ladder of a ship? (A server player gets the allowance for the lag of a moving hull.) */
	public static boolean climbing(Entity e) {
		World world = e.getEntityWorld();
		ShipEntity[] ships = ShipTracker.ships(world);
		if (ships.length == 0 || e instanceof ShipEntity || e.hasVehicle()) {
			return false;
		}
		boolean lag = e instanceof ServerPlayerEntity;
		for (ShipEntity ship : ships) {
			if (!ship.isRemoved() && on(ship, e.getX(), e.getY(), e.getZ(), lag)) {
				return true;
			}
		}
		return false;
	}

	/** Is the world point (feet) on a side ladder of this ship (its current pose)? */
	public static boolean on(ShipEntity ship, double x, double y, double z, boolean lag) {
		return on(ship, ship.getX(), ship.getY(), ship.getZ(), ship.getYaw(), x, y, z, lag);
	}

	/** Same, for the ship at the given pose (the carry uses the previous tick's pose). */
	public static boolean on(ShipEntity ship, double px, double py, double pz, double yaw, double x, double y, double z, boolean lag) {
		List<SideLadder.Ladder> ladders = SideLadder.of(ship.shipType().id());
		if (ladders.isEmpty()) {
			return false;
		}
		double tolW = 0, tolU = 0;
		if (lag) {
			tolW = 0.5 + Math.abs(ship.syncedSpeed()) / 20.0 * LAG_TICKS;
			tolU = 0.5 + Math.abs(ship.yawDelta()) * Math.PI / 180.0 * ship.geometry().boundingRadius() * LAG_TICKS;
		}
		double r = ship.geometry().boundingRadius() + 2 + tolW;
		double dx = x - px, dz = z - pz;
		if (dx * dx + dz * dz > r * r) {
			return false;
		}
		double a = Math.toRadians(yaw), c = Math.cos(a), s = Math.sin(a);
		double lx = dx * c + dz * s, lz = -dx * s + dz * c;
		return SideLadder.climbing(ladders, ship.geometry().hull().waterlineY, lx, y - py, lz, tolW, tolU);
	}
}
