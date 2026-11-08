package fr.medievalships.core;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Boarding gangplank (passerelle) of a ship or large airship: its per-vessel spec
 * ({@code assets/medievalships/gangplanks/<ship id>.json}) and the geometry shared by the server
 * (safety checks, collisions) and the client (rendering, picking).
 *
 * <h2>Frame</h2>
 * Every coordinate of a spec is in the SHIP-LOCAL frame of {@link ShipGeometry} (the frame of
 * {@link ShipGeometry.Seat}, {@link HullShape} and the ship's .bbmodel as BbModel emits it), in blocks:
 * <ul>
 * <li>x = lateral, <b>+x = port</b> (left when facing the bow), -x = starboard;</li>
 * <li>y = up, 0 = the hull origin (the waterline of a ship; an airship's model origin);</li>
 * <li>z = along the keel, <b>+z = bow</b>.</li>
 * </ul>
 * World = {@link ShipPose#toWorld}: wx = x + lx cos(yaw) - lz sin(yaw), wy = y + ly,
 * wz = z + lx sin(yaw) + lz cos(yaw).
 *
 * <h2>The plank</h2>
 * The plank turns about its hinge line, which runs along the keel (the z axis) through {@link Spec#hinge}.
 * {@code o} = {@link Side#sign} is the outboard direction (+1 port, -1 starboard). A point of the plank at
 * distance {@code u} from the hinge along the plank, height {@code v} above its walking surface and offset
 * {@code w} along the keel, with the plank at angle {@code a} (degrees, <b>down positive</b>: 0 =
 * horizontal, +20 = sloping down to a quay lower than the deck, -90 = raised upright), is
 * <pre>
 *   x = hx + o (u cos a + v sin a)
 *   y = hy - u sin a + v cos a
 *   z = hz + o w
 * </pre>
 * Stowed, the plank stands raised along the hull side at {@link Spec#stowedAngle} (default -90: upright,
 * walking surface facing inboard). Deployed, it rests at the angle found by the landing search, within
 * {@link Spec#minAngle}..{@link Spec#maxAngle}.
 *
 * <h2>Models</h2>
 * {@code models/entity/gangplank_<ship id>.bbmodel} (tools/gangplank/gangplanklib.py): model-local
 * (u, v, w) = (x, y, z): hinge line along the model's z axis through the origin, the plank along +x, its
 * top surface at y = 0, centred on z. The renderer maps it with the formula above: translate to the hinge,
 * rotate 180 degrees about y for a starboard plank, then rotate by -a about z (the model's +x end goes
 * down for a positive angle). {@code models/entity/gangplank_lever_<style>.bbmodel}: the base at the
 * origin on the deck, a bone {@code handle} pivoting at the base and tilting in the model's x-y plane, the
 * lever facing the model's +x. The renderer turns it about +y by {@link Spec#leverYaw} degrees
 * ({@code RotationAxis.POSITIVE_Y}: 0 = facing the ship's +x, 90 = facing -z, 180 = facing -x); by default
 * the lever faces inboard (see {@link #leverYawOrDefault}).
 */
public final class Gangplank {
	/** Path of the spec files on the classpath. */
	public static final String DIR = "/assets/medievalships/gangplanks/";
	/** Default stowed angle: raised upright against the hull side. */
	public static final double STOWED_ANGLE = -90.0;

	private Gangplank() {
	}

	/** The side of the hull the plank opens on; {@link #sign} is the outboard x direction. */
	public enum Side {
		PORT(1), STARBOARD(-1);

		public final int sign;

		Side(int sign) {
			this.sign = sign;
		}

		public static Side parse(String s) {
			return switch (s.toLowerCase(java.util.Locale.ROOT)) {
				case "port", "babord", "bâbord", "left" -> PORT;
				case "starboard", "tribord", "right" -> STARBOARD;
				default -> throw new IllegalArgumentException("gangplank side must be port or starboard: " + s);
			};
		}
	}

	/** Plank state (tracked data, NBT). Append only: the ordinal is saved and synced. */
	public enum State {
		RETRACTED, DEPLOYING, DEPLOYED, RETRACTING;

		public static State of(int ordinal) {
			State[] v = values();
			return ordinal >= 0 && ordinal < v.length ? v[ordinal] : RETRACTED;
		}

		/** The plank is out of its stowed position (moving or resting on the quay). */
		public boolean out() {
			return this != RETRACTED;
		}
	}

	/** Inboard step box (ship-local), solid only while the plank is deployed. */
	public record Box(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
		public static Box of(double x0, double y0, double z0, double x1, double y1, double z1) {
			return new Box(Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1), Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1));
		}
	}

	/**
	 * One vessel's gangplank (see the class doc for the frame).
	 *
	 * @param shipId      ship type id (file name)
	 * @param side        hull side it opens on
	 * @param hx          hinge line centre, at the walking height where it meets the ship
	 * @param width       across the plank (along the keel), blocks
	 * @param length      from the hinge to the tip, blocks
	 * @param style       wood, dark_wood, worn, elven, copper, crystal, jade, steel (model and lever)
	 * @param leverX      base of the lever on the deck
	 * @param leverYaw    facing of the lever, degrees (NaN: facing inboard, see {@link #leverYawOrDefault})
	 * @param step        inboard step box (solid while deployed) or null
	 * @param railGapZ0   span along the keel where the hull rail above the hinge stops colliding while deployed
	 *                    (NaN: none)
	 * @param minAngle    allowed deployed slope range, degrees, down positive
	 * @param maxDrop     largest drop hinge -> landing it may bridge (blocks)
	 * @param chainX      fixed point the support chains / ropes run from (NaN: above the hinge)
	 * @param stowedAngle angle when stowed (default -90, raised)
	 */
	public record Spec(String shipId, Side side, double hx, double hy, double hz, double width, double length, String style,
			double leverX, double leverY, double leverZ, double leverYaw, Box step, double railGapZ0, double railGapZ1,
			double minAngle, double maxAngle, double maxDrop, double chainX, double chainY, double chainZ, double stowedAngle) {

		public int o() {
			return side.sign;
		}

		public boolean hasRailGap() {
			return !Double.isNaN(railGapZ0);
		}

		public boolean hasChainAnchor() {
			return !Double.isNaN(chainX);
		}

		/** Ship-local point of the plank at angle {@code a} (degrees, down positive), see the class doc. */
		public double[] point(double a, double u, double v, double w) {
			double r = Math.toRadians(a), c = Math.cos(r), s = Math.sin(r);
			return new double[] {hx + o() * (u * c + v * s), hy - u * s + v * c, hz + o() * w};
		}

		/** Lever yaw in degrees: the rotation about +y (right handed, like {@code RotationAxis.POSITIVE_Y}) of the lever model. */
		public double leverYawOrDefault() {
			return Gangplank.leverYawOrDefault(this);
		}

		/** Where the support chains start (ship-local): the anchor, or 2.4 above the hinge, a little inboard. */
		public double[] chainAnchor(double w) {
			if (hasChainAnchor()) {
				return new double[] {chainX, chainY, chainZ + o() * w};
			}
			return new double[] {hx - o() * 0.15, hy + 2.4, hz + o() * w};
		}
	}

	/** Lever facing: the spec's lever_yaw, else inboard (yaw 0 = +x for a starboard plank, 180 = -x for a port one). */
	public static double leverYawOrDefault(Spec spec) {
		if (!Double.isNaN(spec.leverYaw())) {
			return spec.leverYaw();
		}
		return spec.side() == Side.STARBOARD ? 0.0 : 180.0;
	}

	// ------------------------------------------------------------------ loading

	private static final Map<String, Spec> CACHE = new ConcurrentHashMap<>();
	private static final Spec NONE = new Spec("", Side.PORT, 0, 0, 0, 0, 0, "", 0, 0, 0, 0, null, Double.NaN, Double.NaN,
			0, 0, 0, Double.NaN, Double.NaN, Double.NaN, STOWED_ANGLE);

	/** The gangplank of a ship type, or null if it has none (no spec file). Cached. */
	public static Spec of(String shipId) {
		Spec s = CACHE.computeIfAbsent(shipId, id -> {
			Spec loaded = load(id);
			return loaded == null ? NONE : loaded;
		});
		return s == NONE ? null : s;
	}

	/** Reads {@code /assets/medievalships/gangplanks/<id>.json} from the classpath; null if absent. */
	public static Spec load(String shipId) {
		try (InputStream in = Gangplank.class.getResourceAsStream(DIR + shipId + ".json")) {
			if (in == null) {
				return null;
			}
			try (Reader reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return parse(shipId, JsonParser.parseReader(reader).getAsJsonObject());
			}
		} catch (java.io.IOException e) {
			throw new IllegalStateException("cannot read gangplank spec " + shipId, e);
		}
	}

	/** Parses a spec (see the class doc and docs/PASSERELLES.md); throws on a missing or bad field. */
	public static Spec parse(String shipId, JsonObject o) {
		Side side = Side.parse(o.get("side").getAsString());
		double[] hinge = vec(o, "hinge", 3, true);
		double width = num(o, "width", Double.NaN);
		double length = num(o, "length", Double.NaN);
		if (!(width >= 0.8 && width <= 6) || !(length >= 1 && length <= 12)) {
			throw new IllegalArgumentException(shipId + ": gangplank width / length out of range: " + width + " / " + length);
		}
		String style = o.has("style") ? o.get("style").getAsString() : "wood";
		double[] lever = vec(o, "lever", 3, true);
		double leverYaw = num(o, "lever_yaw", Double.NaN);
		double[] st = vec(o, "step", 6, false);
		Box step = st == null ? null : Box.of(st[0], st[1], st[2], st[3], st[4], st[5]);
		double[] gap = vec(o, "rail_gap", 2, false);
		double[] angles = vec(o, "angles", 2, false);
		double minA = angles == null ? -15 : Math.min(angles[0], angles[1]);
		double maxA = angles == null ? 35 : Math.max(angles[0], angles[1]);
		if (minA < -45 || maxA > 60) {
			throw new IllegalArgumentException(shipId + ": gangplank angles out of [-45, 60]: " + minA + ", " + maxA);
		}
		double maxDrop = num(o, "max_drop", length * Math.sin(Math.toRadians(maxA)));
		double[] chain = vec(o, "chain_anchor", 3, false);
		double stowed = num(o, "stowed_angle", STOWED_ANGLE);
		return new Spec(shipId, side, hinge[0], hinge[1], hinge[2], width, length, style, lever[0], lever[1], lever[2], leverYaw, step,
				gap == null ? Double.NaN : Math.min(gap[0], gap[1]), gap == null ? Double.NaN : Math.max(gap[0], gap[1]),
				minA, maxA, maxDrop, chain == null ? Double.NaN : chain[0], chain == null ? Double.NaN : chain[1],
				chain == null ? Double.NaN : chain[2], stowed);
	}

	private static double num(JsonObject o, String key, double def) {
		JsonElement e = o.get(key);
		return e == null || e.isJsonNull() ? def : e.getAsDouble();
	}

	private static double[] vec(JsonObject o, String key, int n, boolean required) {
		JsonElement e = o.get(key);
		if (e == null || e.isJsonNull()) {
			if (required) {
				throw new IllegalArgumentException("gangplank spec: missing " + key);
			}
			return null;
		}
		JsonArray a = e.getAsJsonArray();
		if (a.size() != n) {
			throw new IllegalArgumentException("gangplank spec: " + key + " needs " + n + " numbers");
		}
		double[] out = new double[n];
		for (int i = 0; i < n; i++) {
			out[i] = a.get(i).getAsDouble();
		}
		return out;
	}
}
