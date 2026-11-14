package fr.medievalships.client.render;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.world.World;

import fr.medievalships.core.DoorClock;

/**
 * The clock this client draws the doors with (1.33.0): a {@link DoorClock} on the world's time, ticked at the end of
 * every client tick in which the world's time advanced (not paused, not frozen), reset with the world. The doors are
 * drawn at {@link #now}: the server's time followed smoothly, so that its time packet (every second) never makes a door
 * jump.
 */
public final class DoorClientClock {
	private static final DoorClock CLOCK = new DoorClock();
	private static ClientWorld world;

	private DoorClientClock() {
	}

	/** End of a client tick (its world's time already advanced). */
	public static void tick(MinecraftClient client) {
		ClientWorld w = client.world;
		if (w != world) {
			CLOCK.reset();
			world = w;
		}
		if (w != null && !client.isPaused() && w.getTickManager().shouldTick()) {
			CLOCK.tick(w.getTime());
		}
	}

	/** The time to draw a door of {@code w} with ({@code tickProgress}: the share of the tick gone by). */
	public static double now(World w, float tickProgress) {
		if (w == null) {
			return 0;
		}
		if (w != world || !CLOCK.started()) {
			return w.getTime() + tickProgress;
		}
		return CLOCK.now(tickProgress);
	}

	/** Forgets the world (disconnected). */
	public static void clear() {
		CLOCK.reset();
		world = null;
	}
}
