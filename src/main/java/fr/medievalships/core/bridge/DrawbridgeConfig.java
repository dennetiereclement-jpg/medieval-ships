package fr.medievalships.core.bridge;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Settings shared by every drawbridge ({@code "drawbridges"} section of {@code config/medievalships.json}): the
 * defaults a new bridge starts with (each bridge keeps its own copy, adjustable with {@code /pontlevis}), the
 * detection rate and policies, the sound volume, and the vessel profiles ({@link VesselProfile}).
 */
public final class DrawbridgeConfig {
	/** Key of the profile used for every vanilla boat and raft (chest boats included). */
	public static final String VANILLA_BOAT = "vanilla_boat";

	// ---- defaults of a new bridge (see BridgeTuning)
	public double approach = 50.0;
	public double hysteresis = 8.0;
	public double openAngle = 80.0;
	public double openSeconds = 8.0;
	public double closeDelaySeconds = 5.0;
	public double warningSeconds = 4.0;
	public double margin = 0.5;
	public double stopDistance = 6.0;

	// ---- detection
	/** Ticks between two scans of the approach zones (the cycle itself runs every tick). */
	public int detectionIntervalTicks = 5;
	/** A vessel without pilot, autopilot or motion for this long in the approach is a moored one: ignored. */
	public double idleIgnoreSeconds = 60.0;
	/** A vessel whose chunk is unloaded stays taken into account for this long (it may still be there). */
	public double unloadedGraceSeconds = 120.0;
	/** Lowest point counted for vessels: the detection boxes reach this far under the water surface. */
	public double detectionDepth = 8.0;

	// ---- ambience
	/** Volume of the chain, winch and creak sounds (0 = silent). */
	public double soundVolume = 0.6;
	/** Announce the movements to the players around (action bar) and with a discreet bell. */
	public boolean announce = true;
	public double announceRadius = 48.0;

	/** Vessel profiles by ship type id, entity type id, or {@link #VANILLA_BOAT}. */
	public Map<String, VesselProfile> profiles = new LinkedHashMap<>();

	public DrawbridgeConfig() {
		// vanilla boats: hull 0.56 high, the occupants' heads counted by the measurement
		profiles.put(VANILLA_BOAT, new VesselProfile(0.6, 0.0, 1.4, true, false));
	}

	public BridgeTuning defaults() {
		return new BridgeTuning(approach, hysteresis, openAngle, (int) Math.round(openSeconds * 20), (int) Math.round(closeDelaySeconds * 20),
				(int) Math.round(warningSeconds * 20), margin, stopDistance).sanitized();
	}

	/** The profile of a key ({@code galley}, {@code minecraft:oak_boat}, {@code vanilla_boat}), or null. Keys are case insensitive. */
	public VesselProfile profile(String key) {
		if (key == null || profiles == null) {
			return null;
		}
		VesselProfile p = profiles.get(key);
		if (p != null) {
			return p;
		}
		String lower = key.toLowerCase(Locale.ROOT);
		for (Map.Entry<String, VesselProfile> e : profiles.entrySet()) {
			if (e.getKey() != null && e.getKey().toLowerCase(Locale.ROOT).equals(lower)) {
				return e.getValue();
			}
		}
		return null;
	}

	public void sanitize() {
		approach = clamp(approach, 4, 512, 50);
		hysteresis = clamp(hysteresis, 0, 128, 8);
		openAngle = clamp(openAngle, 10, 90, 80);
		openSeconds = clamp(openSeconds, 0.5, 120, 8);
		closeDelaySeconds = clamp(closeDelaySeconds, 0, 600, 5);
		warningSeconds = clamp(warningSeconds, 0, 120, 4);
		margin = clamp(margin, 0, 8, 0.5);
		stopDistance = clamp(stopDistance, 0, 64, 6);
		detectionIntervalTicks = (int) clamp(detectionIntervalTicks, 1, 40, 5);
		idleIgnoreSeconds = clamp(idleIgnoreSeconds, 5, 3600, 60);
		unloadedGraceSeconds = clamp(unloadedGraceSeconds, 0, 3600, 120);
		detectionDepth = clamp(detectionDepth, 0, 64, 8);
		soundVolume = clamp(soundVolume, 0, 2, 0.6);
		announceRadius = clamp(announceRadius, 0, 256, 48);
		if (profiles == null) {
			profiles = new LinkedHashMap<>();
		}
		Map<String, VesselProfile> clean = new LinkedHashMap<>();
		for (Map.Entry<String, VesselProfile> e : profiles.entrySet()) {
			if (e.getKey() == null || e.getKey().isBlank() || e.getValue() == null) {
				continue;
			}
			e.getValue().sanitize();
			clean.put(e.getKey().trim(), e.getValue());
		}
		if (!clean.containsKey(VANILLA_BOAT)) {
			clean.put(VANILLA_BOAT, new VesselProfile(0.6, 0.0, 1.4, true, false));
		}
		profiles = clean;
	}

	private static double clamp(double v, double lo, double hi, double def) {
		return Double.isNaN(v) ? def : Math.max(lo, Math.min(hi, v));
	}
}
