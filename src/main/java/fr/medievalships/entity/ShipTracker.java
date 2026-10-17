package fr.medievalships.entity;

import java.util.Arrays;
import java.util.Map;
import java.util.WeakHashMap;

import net.minecraft.entity.Entity;
import net.minecraft.world.World;

import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;

/**
 * Loaded ships per world (client and server worlds separately). Collision and carry code runs
 * for every moving entity, so it must not search the world for ships: it reads a small cached
 * array instead. Entries may be removed ships: callers check {@link Entity#isRemoved()}.
 */
public final class ShipTracker {
	private static final GalleyEntity[] NONE = new GalleyEntity[0];
	private static final Map<World, GalleyEntity[]> SHIPS = new WeakHashMap<>();

	private ShipTracker() {
	}

	public static synchronized void add(GalleyEntity ship) {
		World world = ship.getEntityWorld();
		if (world.isClient()) {
			// the client only has one world at a time: drop the previous ones (dimension change)
			SHIPS.keySet().removeIf(w -> w.isClient() && w != world);
		}
		GalleyEntity[] current = SHIPS.getOrDefault(world, NONE);
		for (GalleyEntity s : current) {
			if (s == ship) {
				return;
			}
		}
		GalleyEntity[] next = Arrays.stream(current).filter(s -> !s.isRemoved()).toArray(GalleyEntity[]::new);
		next = Arrays.copyOf(next, next.length + 1);
		next[next.length - 1] = ship;
		SHIPS.put(world, next);
	}

	public static synchronized void remove(GalleyEntity ship) {
		World world = ship.getEntityWorld();
		GalleyEntity[] current = SHIPS.get(world);
		if (current != null) {
			SHIPS.put(world, Arrays.stream(current).filter(s -> s != ship && !s.isRemoved()).toArray(GalleyEntity[]::new));
		}
	}

	/** Ships hold their world, so the weak keys never expire by themselves: clear explicitly. */
	public static synchronized void clear(World world) {
		SHIPS.remove(world);
	}

	public static synchronized void clearClientWorlds() {
		SHIPS.keySet().removeIf(World::isClient);
	}

	public static synchronized GalleyEntity[] ships(World world) {
		return SHIPS.getOrDefault(world, NONE);
	}

	/** The ship whose deck volume contains this entity's feet, if any. */
	public static GalleyEntity shipUnder(Entity entity) {
		for (GalleyEntity ship : ships(entity.getEntityWorld())) {
			if (ship.isRemoved()) {
				continue;
			}
			ShipPose pose = ship.pose();
			double[] l = pose.toLocal(entity.getX(), entity.getY(), entity.getZ());
			if (ShipGeometry.inCarryVolume(l[0], l[1], l[2])) {
				return ship;
			}
		}
		return null;
	}
}
