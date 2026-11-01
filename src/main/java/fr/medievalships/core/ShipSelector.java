package fr.medievalships.core;

import java.util.List;
import java.util.Locale;

/**
 * Which vessel a scripted command means ({@code /ship as <vessel> ...}, {@code /ship test <vessel> ...}, from a
 * command block or an NPC): by its name ({@code /ship name}), its UUID (whole, or its first characters), its type
 * ({@code galley}, {@code grand_warship}...: the nearest one of that type), or {@link #NEAREST} (the usual
 * targeting of the {@code /ship} commands). Names win over UUIDs, UUIDs over types; among several matches the one
 * in the command's dimension, then the nearest. Pure matching, the game code lists the candidates.
 */
public final class ShipSelector {
	/** The usual target of the {@code /ship} commands (ridden, stood on, looked at, nearest). */
	public static final String NEAREST = "nearest";
	/** Shortest UUID prefix accepted (hexadecimal characters). */
	public static final int MIN_UUID_PREFIX = 6;

	/** A loaded vessel: its name (null when it has none), UUID, type id, distance to the command and dimension. */
	public record Candidate(String name, String uuid, String typeId, double distance, boolean sameWorld) {
	}

	private ShipSelector() {
	}

	public static boolean isNearest(String selector) {
		return selector != null && (selector.equalsIgnoreCase(NEAREST) || selector.equalsIgnoreCase("proche")
				|| selector.equalsIgnoreCase("plus_proche"));
	}

	/** Index of the vessel the selector means among the candidates, -1 if none matches. */
	public static int match(String selector, List<Candidate> candidates) {
		if (selector == null || selector.isBlank() || candidates == null || candidates.isEmpty()) {
			return -1;
		}
		String s = selector.trim();
		String lower = s.toLowerCase(Locale.ROOT);
		int best = pick(candidates, c -> c.name() != null && c.name().equalsIgnoreCase(s));
		if (best < 0) {
			best = pick(candidates, c -> c.uuid() != null && c.uuid().equalsIgnoreCase(s));
		}
		if (best < 0 && isUuidPrefix(lower)) {
			String bare = lower.replace("-", "");
			best = pick(candidates, c -> c.uuid() != null && c.uuid().toLowerCase(Locale.ROOT).replace("-", "").startsWith(bare));
		}
		if (best < 0) {
			ShipType type = Ships.byId(lower);
			String typeId = type == null ? lower : type.id();
			best = pick(candidates, c -> c.typeId() != null && c.typeId().equalsIgnoreCase(typeId));
		}
		return best;
	}

	/** Does this look like the first characters of a UUID (at least {@link #MIN_UUID_PREFIX} hexadecimal ones)? */
	static boolean isUuidPrefix(String s) {
		String bare = s.replace("-", "");
		if (bare.length() < MIN_UUID_PREFIX || bare.length() > 32) {
			return false;
		}
		for (int i = 0; i < bare.length(); i++) {
			if (Character.digit(bare.charAt(i), 16) < 0) {
				return false;
			}
		}
		return true;
	}

	private interface Filter {
		boolean test(Candidate c);
	}

	/** The matching candidate of the command's dimension nearest to it (else the nearest anywhere), -1 if none. */
	private static int pick(List<Candidate> candidates, Filter filter) {
		int best = -1;
		for (int i = 0; i < candidates.size(); i++) {
			Candidate c = candidates.get(i);
			if (!filter.test(c)) {
				continue;
			}
			if (best < 0 || better(c, candidates.get(best))) {
				best = i;
			}
		}
		return best;
	}

	private static boolean better(Candidate a, Candidate b) {
		if (a.sameWorld() != b.sameWorld()) {
			return a.sameWorld();
		}
		return a.distance() < b.distance();
	}

	/** The selector that names a vessel in a script: its name quoted when it has spaces, else its UUID. */
	public static String quote(String name) {
		if (name == null || name.isBlank()) {
			return "";
		}
		boolean plain = true;
		for (int i = 0; i < name.length(); i++) {
			char ch = name.charAt(i);
			if (!(Character.isLetterOrDigit(ch) || ch == '_' || ch == '-' || ch == '.' || ch == '+')) {
				plain = false;
				break;
			}
		}
		return plain ? name : "\"" + name.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
	}
}
