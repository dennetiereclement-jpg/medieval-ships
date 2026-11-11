package fr.medievalships.client.render;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;

/**
 * Counters of what the mod's renderers do each frame (ships, props, their furniture), read by the in-game benchmark
 * ({@code PerfGameTest}): frames seen (one per world render), time between frames, time spent in the mod's own vertex
 * emission, quads and furniture blocks submitted, mesh cells looked at and culled. Render thread only (the counters are
 * plain longs, written where the command queue runs the mod's callbacks and read between frames by the test).
 * {@link #skip} is the benchmark's debug toggle: the mod's renderers draw nothing while it is set, which gives the frame
 * time of the same scene without them.
 */
public final class RenderStats {
	/** Debug toggle of the benchmark: the ships and props are not drawn at all. */
	public static volatile boolean skip;
	/** Frames seen (world renders) since the last reset, and the nanoseconds they spanned. */
	public static long frames;
	public static long frameNanos;
	/** Time spent in the mod's vertex emission (its custom render commands), quads and furniture blocks it submitted. */
	public static long emitNanos;
	public static long quads;
	public static long decorBlocks;
	/** Static mesh cells looked at, and how many of them were skipped as out of view. */
	public static long cells;
	public static long cellsCulled;
	/** Quads of static bones that were transformed on the CPU this session (0 once every mesh is baked). */
	public static long staticQuadsBaked;
	private static long lastFrame;
	private static boolean installed;

	private RenderStats() {
	}

	/** Registers the frame clock (once). */
	public static void install() {
		if (installed) {
			return;
		}
		installed = true;
		WorldRenderEvents.START_MAIN.register(context -> {
			long now = System.nanoTime();
			if (lastFrame != 0) {
				frames++;
				frameNanos += now - lastFrame;
			}
			lastFrame = now;
		});
	}

	public static void reset() {
		frames = 0;
		frameNanos = 0;
		emitNanos = 0;
		quads = 0;
		decorBlocks = 0;
		cells = 0;
		cellsCulled = 0;
		lastFrame = 0;
	}

	/** {frames, frameNanos, emitNanos, quads, decorBlocks, cells, cellsCulled, staticQuadsBaked}. */
	public static long[] snapshot() {
		return new long[] {frames, frameNanos, emitNanos, quads, decorBlocks, cells, cellsCulled, staticQuadsBaked};
	}
}
