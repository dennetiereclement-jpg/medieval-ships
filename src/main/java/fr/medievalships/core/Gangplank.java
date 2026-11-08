package fr.medievalships.core;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
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
 * Deployed, it rests at the angle found by the landing search, within {@link Spec#minAngle}..{@link Spec#maxAngle}.
 *
 * <h2>Folding (accordion)</h2>
 * The plank is a folding gangway of {@link #segments} segments of equal length {@code s} (segment {@code k} spans
 * {@code u} in [k s, (k+1) s]), hinged to each other. Stowed, it is folded zig-zag into a compact pack hanging
 * against the OUTSIDE of the hull side just under the hinge: segment 0 hangs down from the hinge (walking surface
 * facing outboard), segment 1 folds back up on it, and so on; the pack is one segment high and {@code n} layers of
 * {@link #FOLD_UNDER} + {@link #FOLD_OVER} thick, its inner face {@link Fold#standoff} outboard of the hinge line
 * (clear of the hull, see {@link #fold}) and its top {@link #STOW_DROP} under the hinge height. Joint {@code j}
 * (between segments j-1 and j, at {@code u = j s}) folds the walking surfaces against each other (odd j: "top"
 * fold, pivot {@link #FOLD_OVER} over the walking surface) or the undersides (even j: "bottom" fold, pivot
 * {@link #FOLD_UNDER} under it), so the layers stack without crossing. The handrails' stanchions of each segment
 * fold flat, inwards, onto its walking surface (pivot line {@link #RAIL_PIVOT_V} over it, {@link #RAIL_PIVOT_INSET}
 * inside its side edges). Deploying, the pack lifts out and up, unfolds segment by segment (joint 1 first) while the
 * whole swings to the target slope, the handrails stand up, and the plank lands straight, exactly as a one-piece
 * plank at the target angle ({@link #foldPose}); retracting is the reverse. A segment's pose is
 * {@code (a_k, cx_k, cy_k)}: its points are, relative to the hinge (X outboard, Y up),
 * <pre>
 *   X = cx_k + u cos a_k + v sin a_k,   Y = cy_k - u sin a_k + v cos a_k
 * </pre>
 * (straight: every {@code a_k = a}, {@code cx_k = cy_k = 0}: the formula above). {@link Spec#stowedAngle} (default -90,
 * raised upright, the stowed position of 1.23.0) is now only the start of the swing that {@link #clearance} sweeps,
 * so the deploy rules are unchanged.
 *
 * <h2>Models</h2>
 * {@code models/entity/gangplank_<ship id>.bbmodel} (tools/gangplank/gangplanklib.py): model-local
 * (u, v, w) = (x, y, z): hinge line along the model's z axis through the origin, the plank along +x, its
 * top surface at y = 0, centred on z, straight. One bone per segment, {@code seg_<k>} (origin at its inner end,
 * {@code (k s, 0, 0)}), each with its two handrails {@code rail_<k>_0} (-z side) and {@code rail_<k>_1} (+z side)
 * as children. The renderer maps each segment with its pose: translate to the hinge, rotate 180 degrees about y for
 * a starboard plank, translate by (cx_k, cy_k, 0), then rotate by -a_k about z (the model's +x end goes down for a
 * positive angle); a handrail is first turned inwards about its pivot line (along x) by the rail fold
 * ({@link #railPoint}). {@code models/entity/gangplank_lever_<style>.bbmodel}: the base at the
 * origin on the deck, a bone {@code handle} pivoting at the base and tilting in the model's x-y plane, the
 * lever facing the model's +x. The renderer turns it about +y by {@link Spec#leverYaw} degrees
 * ({@code RotationAxis.POSITIVE_Y}: 0 = facing the ship's +x, 90 = facing -z, 180 = facing -x); by default
 * the lever faces inboard (see {@link #leverYawOrDefault}).
 */
public final class Gangplank {
	/** Path of the spec files on the classpath. */
	public static final String DIR = "/assets/medievalships/gangplanks/";
	/** Styles, in the order of their cells in the atlas textures/entity/gangplank.png (gangplanklib.STYLES). */
	public static final List<String> STYLES = List.of("wood", "dark_wood", "worn", "elven", "copper", "crystal", "jade", "steel");
	/** Size of the atlas, pixels. */
	public static final int ATLAS = 256;

	/**
	 * Atlas region (u, v, w, h in pixels) of a part of a style: plank, board, rail, metal, cord (rope or chain), end,
	 * accent, handle, knob (as gangplanklib._CELL).
	 */
	public static int[] region(String style, String part) {
		int i = Math.max(0, STYLES.indexOf(style));
		int ox = (i % 2) * 128, oy = (i / 2) * 32;
		int[] r = switch (part) {
			case "plank" -> new int[] {0, 0, 64, 16};
			case "board" -> new int[] {0, 16, 64, 16};
			case "rail" -> new int[] {64, 0, 32, 16};
			case "metal" -> new int[] {96, 0, 16, 16};
			case "cord" -> new int[] {112, 0, 16, 16};
			case "end" -> new int[] {64, 16, 16, 16};
			case "accent" -> new int[] {80, 16, 16, 16};
			case "handle" -> new int[] {96, 16, 16, 16};
			default -> new int[] {112, 16, 16, 16};
		};
		return new int[] {ox + r[0], oy + r[1], r[2], r[3]};
	}
	/** Start of the swing the clearance check sweeps: the one-piece plank of 1.23.0 was stowed upright (see the class doc). */
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
	 * @param stowedAngle start of the swing the clearance check sweeps (default -90, raised; see the class doc)
	 * @param segments    folding segments (0: {@code ceil(length / SEGMENT)}, at least 2), see {@link Gangplank#segments}
	 * @param stowOffset  least gap between the hinge line and the stowed pack's inner face, outboard (0: from the hull
	 *                    shape only), see {@link Gangplank#fold}
	 */
	public record Spec(String shipId, Side side, double hx, double hy, double hz, double width, double length, String style,
			double leverX, double leverY, double leverZ, double leverYaw, Box step, double railGapZ0, double railGapZ1,
			double minAngle, double maxAngle, double maxDrop, double chainX, double chainY, double chainZ, double stowedAngle,
			int segments, double stowOffset) {

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
			0, 0, 0, Double.NaN, Double.NaN, Double.NaN, STOWED_ANGLE, 0, 0);

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
		int segments = (int) num(o, "segments", 0);
		if (segments != 0 && (segments < 2 || segments > MAX_SEGMENTS)) {
			throw new IllegalArgumentException(shipId + ": gangplank segments out of [2, " + MAX_SEGMENTS + "]: " + segments);
		}
		double stowOffset = num(o, "stow_offset", 0);
		if (!(stowOffset >= 0 && stowOffset <= 2)) {
			throw new IllegalArgumentException(shipId + ": gangplank stow_offset out of [0, 2]: " + stowOffset);
		}
		return new Spec(shipId, side, hinge[0], hinge[1], hinge[2], width, length, style, lever[0], lever[1], lever[2], leverYaw, step,
				gap == null ? Double.NaN : Math.min(gap[0], gap[1]), gap == null ? Double.NaN : Math.max(gap[0], gap[1]),
				minA, maxA, maxDrop, chain == null ? Double.NaN : chain[0], chain == null ? Double.NaN : chain[1],
				chain == null ? Double.NaN : chain[2], stowed, segments, stowOffset);
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

	// ------------------------------------------------------------------ animation

	/** Ticks a deploy or a retraction takes (3 s). */
	public static final int DURATION = 60;
	/** Part of the animation spent unlocking (a short pause, the latch lifting) before the swing. */
	private static final double UNLOCK = 0.1;
	/** Part of the animation where the plank has arrived and settles (a small bounce). */
	private static final double SETTLE = 0.12;
	/** The walking surface of the tip rests this far above the landing surface (the bevelled tip and its shoe). */
	public static final double TIP_LIFT = 0.1;
	/** Largest rise between two consecutive walking boxes of the plank (players step up to 0.6). */
	public static final double STEP_RISE = 0.25;
	/** Largest rise of one stair of the inboard step box. */
	public static final double STAIR_RISE = 0.45;
	/** Thickness of the walking boxes. */
	public static final double BOX_THICKNESS = 0.3;
	/** The first walking box starts this far inboard of the hinge (over the top of the bulwark). */
	public static final double INBOARD = 0.3;

	/** Progress 0..1 of an animation started {@code ticks} ago. */
	public static double progress(double ticks) {
		return Math.max(0.0, Math.min(1.0, ticks / DURATION));
	}

	private static double ease(double t) {
		t = Math.max(0, Math.min(1, t));
		return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
	}

	/**
	 * Angle of a plank deploying, at progress p (0 stowed .. 1 resting at {@code target}): a short unlock (the plank
	 * lifts a little inboard), an eased swing out and down, a small bounce once it touches the landing.
	 */
	public static double deployCurve(double p, double stowed, double target) {
		if (p <= 0) {
			return stowed;
		}
		if (p >= 1) {
			return target;
		}
		if (p < UNLOCK) {
			return stowed - 3.0 * Math.sin(Math.PI * p / UNLOCK);
		}
		double swingEnd = 1.0 - SETTLE;
		if (p < swingEnd) {
			return stowed + (target - stowed) * ease((p - UNLOCK) / (swingEnd - UNLOCK));
		}
		double r = (p - swingEnd) / SETTLE;
		return target - 1.5 * Math.sin(Math.PI * r) * (1 - r * 0.5);
	}

	/** Angle of the plank in a state, {@code ticks} after the state started (fractional for rendering). */
	public static double angle(Spec spec, State state, double ticks, double target) {
		return switch (state) {
			case RETRACTED -> spec.stowedAngle();
			case DEPLOYED -> target;
			case DEPLOYING -> deployCurve(progress(ticks), spec.stowedAngle(), target);
			case RETRACTING -> deployCurve(1.0 - progress(ticks), spec.stowedAngle(), target);
		};
	}

	/** Lever position 0 (stowed) .. 1 (deployed) in a state: it flips during the first 6 ticks of a move. */
	public static double leverPosition(State state, double ticks) {
		double f = Math.max(0, Math.min(1, ticks / 6.0));
		return switch (state) {
			case RETRACTED -> 0;
			case DEPLOYED -> 1;
			case DEPLOYING -> f;
			case RETRACTING -> 1 - f;
		};
	}

	// ------------------------------------------------------------------ folding (accordion)

	/** Longest segment of the folding plank (blocks): {@code ceil(length / SEGMENT)} segments, at least 2. */
	public static final double SEGMENT = 1.6;
	/** Most segments a plank may have (the {@code segments} override included). */
	public static final int MAX_SEGMENTS = 12;
	/** Depth of a segment under its walking surface (boards, stringers, straps), blocks: the "bottom" fold pivot. */
	public static final double FOLD_UNDER = 0.27;
	/** Height of a segment over its walking surface, handrails folded flat (cleats, flat stanchions, caps): the "top" fold pivot. */
	public static final double FOLD_OVER = 0.135;
	/** The handrails' stanchions fold about a line along the plank this high over the walking surface... */
	public static final double RAIL_PIVOT_V = 0.075;
	/** ...this far inside the plank's side edges. */
	public static final double RAIL_PIVOT_INSET = 0.04;
	/** Gap kept between the stowed pack and the hull side (blocks). */
	public static final double STOW_CLEARANCE = 0.06;
	/** The stowed pack's top (the hinge end of segment 0) hangs this far under the hinge height. */
	public static final double STOW_DROP = 0.12;
	/** Stowed, segment 0 hangs straight down (degrees, down positive). */
	public static final double HANG = 90.0;
	/** While unfolding, the plank is held this far over the horizontal (or over the target if it slopes up). */
	public static final double RAISE = 20.0;
	// deploy timeline (progress 0..1): unlock, lift out, unfold, lower, settle; the handrails stand up near the end
	private static final double LIFT_END = 0.40;
	private static final double UNFOLD_START = 0.30;
	private static final double UNFOLD_END = 0.76;
	private static final double LOWER_START = 0.62;
	private static final double RAIL_START = 0.76;

	/** Number of folding segments of a plank: the spec's override, else {@code ceil(length / SEGMENT)}, at least 2. */
	public static int segments(Spec spec) {
		int n = spec.segments() > 0 ? spec.segments() : (int) Math.ceil(spec.length() / SEGMENT - 1e-9);
		return Math.max(2, Math.min(MAX_SEGMENTS, n));
	}

	/**
	 * A plank's folding geometry: {@code n} segments of {@code seg} blocks; the stowed pack's inner face {@code standoff}
	 * outboard of the hinge line; segment 0's pose offset ({@code offX}, {@code offY}) when stowed; {@code stowed}: the
	 * stowed pose ({@link #foldPose} at progress 0), computed once (never write it).
	 */
	public record Fold(int n, double seg, double standoff, double offX, double offY, double[] stowed) {
		/** Thickness of the stowed pack, outboard (blocks). */
		public double thickness() {
			return n * (FOLD_UNDER + FOLD_OVER);
		}
	}

	private static final Map<Spec, Fold> FOLDS = new ConcurrentHashMap<>();

	/**
	 * The folding geometry of a plank (cached). The stowed pack keeps clear of the hull: its inner face is
	 * {@link #STOW_CLEARANCE} outboard of the hull's outer face (the largest {@link HullShape#halfWidth} over the plank's
	 * width, hinge plates included) or of the spec's {@code stow_offset} (fittings of the model standing out of the hull
	 * under the hinge: wales, port lids, channels; measured on the models by tools/gangplank/ships_g2.py), whichever is
	 * further out.
	 */
	public static Fold fold(Spec spec) {
		return FOLDS.computeIfAbsent(spec, sp -> {
			ShipType t = Ships.byId(sp.shipId());
			return fold(sp, t == null ? null : t.hull());
		});
	}

	/** {@link #fold} against a given hull (null: the spec's {@code stow_offset} only). Not cached. */
	public static Fold fold(Spec spec, HullShape hull) {
		int n = segments(spec);
		double seg = spec.length() / n;
		double standoff = Math.max(spec.stowOffset(), hullStandoff(spec, hull)) + STOW_CLEARANCE;
		double[] stowed = new double[3 * n + 1];
		Fold f = new Fold(n, seg, standoff, standoff + FOLD_UNDER, -STOW_DROP, stowed);
		foldPose(f, 0.0, 0.0, stowed);
		return f;
	}

	/** How far the hull's outer face stands outboard of the hinge line over the plank's width (0 if inboard). */
	public static double hullStandoff(Spec spec, HullShape hull) {
		if (hull == null) {
			return 0.0;
		}
		double hw = spec.width() / 2 + 0.1;
		double max = 0.0;
		for (int i = 0; i <= 16; i++) {
			double z = spec.hz() - hw + 2 * hw * i / 16.0;
			max = Math.max(max, hull.halfWidth(z) - Math.abs(spec.hx()));
		}
		return max;
	}

	/** Fold progress 0 (stowed pack) .. 1 (straight on the landing) of a state, {@code ticks} after it started. */
	public static double foldProgress(State state, double ticks) {
		return switch (state) {
			case RETRACTED -> 0.0;
			case DEPLOYED -> 1.0;
			case DEPLOYING -> progress(ticks);
			case RETRACTING -> 1.0 - progress(ticks);
		};
	}

	/** How open joint {@code j} (1..n-1) is at progress p: 0 folded .. 1 straight; joint 1 opens first. */
	public static double jointOpening(double p, int j, int n) {
		int m = n - 1;
		double span = UNFOLD_END - UNFOLD_START;
		double w = m <= 1 ? span : span * 0.5;
		double start = m <= 1 ? UNFOLD_START : UNFOLD_START + (j - 1) * (span - w) / (m - 1);
		return ease((p - start) / w);
	}

	/** Handrail fold at progress p, degrees: 90 = flat on the walking surface (stowed, moving), 0 = upright. */
	public static double railFold(double p) {
		return 90.0 * (1.0 - ease((p - RAIL_START) / (1.0 - SETTLE - RAIL_START)));
	}

	/**
	 * The pose of every segment at progress p (0 stowed .. 1 resting straight at {@code target}), see the class doc:
	 * {@code out[3k] = a_k} (degrees, down positive), {@code out[3k+1] = cx_k}, {@code out[3k+2] = cy_k} (blocks, relative
	 * to the hinge, X outboard, Y up), {@code out[3n]} = the handrail fold ({@link #railFold}). Allocation free.
	 * Timeline: a short unlock (the pack lifts off the hull a little), the folded pack swings out and up about the hinge
	 * to {@link #RAISE} degrees over the horizontal (or over the target), unfolds there segment by segment, the straight
	 * plank lowers to the target and bounces a little as it lands (as {@link #deployCurve}).
	 */
	public static void foldPose(Fold f, double p, double target, double[] out) {
		int n = f.n();
		double s = f.seg();
		double raised = Math.min(target, 0.0) - RAISE;
		double swingEnd = 1.0 - SETTLE;
		double a0;
		double g; // part of the stowed offset left
		if (p <= 0) {
			a0 = HANG;
			g = 1;
		} else if (p < UNLOCK) {
			a0 = HANG - 3.0 * Math.sin(Math.PI * p / UNLOCK);
			g = 1;
		} else if (p < LIFT_END) {
			double e = ease((p - UNLOCK) / (LIFT_END - UNLOCK));
			a0 = HANG + (raised - HANG) * e;
			g = 1 - e;
		} else if (p < LOWER_START) {
			a0 = raised;
			g = 0;
		} else if (p < swingEnd) {
			a0 = raised + (target - raised) * ease((p - LOWER_START) / (swingEnd - LOWER_START));
			g = 0;
		} else if (p < 1) {
			double r = (p - swingEnd) / SETTLE;
			a0 = target - 1.5 * Math.sin(Math.PI * r) * (1 - r * 0.5);
			g = 0;
		} else {
			a0 = target;
			g = 0;
		}
		out[0] = a0;
		out[1] = g * f.offX();
		out[2] = g * f.offY();
		for (int j = 1; j < n; j++) {
			boolean top = (j & 1) == 1;
			double theta = (top ? -180.0 : 180.0) * (1.0 - (p >= 1 ? 1.0 : jointOpening(p, j, n)));
			double pu = j * s, pv = top ? FOLD_OVER : -FOLD_UNDER;
			double ap = Math.toRadians(out[3 * (j - 1)]), c = Math.cos(ap), sn = Math.sin(ap);
			// the pivot, carried by segment j-1, stays put; segment j turns about it
			double wx = out[3 * (j - 1) + 1] + pu * c + pv * sn;
			double wy = out[3 * (j - 1) + 2] - pu * sn + pv * c;
			double ak = out[3 * (j - 1)] + theta, rk = Math.toRadians(ak), ck = Math.cos(rk), sk = Math.sin(rk);
			out[3 * j] = ak;
			out[3 * j + 1] = wx - (pu * ck + pv * sk);
			out[3 * j + 2] = wy - (-pu * sk + pv * ck);
		}
		out[3 * n] = p >= 1 ? 0.0 : railFold(p);
	}

	/**
	 * The pose of a plank in a state ({@link #foldPose} at {@link #foldProgress}): the shared stowed pose when retracted
	 * (never write it), else computed into {@code scratch} (at least {@code 3 n + 1} long).
	 */
	public static double[] foldPose(Spec spec, State state, double ticks, double target, double[] scratch) {
		Fold f = fold(spec);
		if (state == State.RETRACTED) {
			return f.stowed();
		}
		foldPose(f, foldProgress(state, ticks), target, scratch);
		return scratch;
	}

	/** Ship-local point (u, v, w) (model-local coordinates) of segment k in a pose ({@link #foldPose}), into out[0..2]. */
	public static void foldPoint(Spec spec, double[] pose, int k, double u, double v, double w, double[] out) {
		double r = Math.toRadians(pose[3 * k]), c = Math.cos(r), sn = Math.sin(r);
		double x = pose[3 * k + 1] + u * c + v * sn;
		double y = pose[3 * k + 2] - u * sn + v * c;
		out[0] = spec.hx() + spec.o() * x;
		out[1] = spec.hy() + y;
		out[2] = spec.hz() + spec.o() * w;
	}

	/**
	 * Model-local point (u, v, w) of a handrail ({@code side} -1: the -z one, +1: the +z one) with its stanchions folded
	 * inwards by {@code fold} degrees about their pivot line, in its segment's straight frame; into out[0..2].
	 */
	public static void railPoint(Spec spec, int side, double fold, double u, double v, double w, double[] out) {
		double pz = side * (spec.width() / 2 - RAIL_PIVOT_INSET);
		double psi = Math.toRadians(-side * fold), c = Math.cos(psi), sn = Math.sin(psi);
		double dv = v - RAIL_PIVOT_V, dw = w - pz;
		out[0] = u;
		out[1] = RAIL_PIVOT_V + dv * c - dw * sn;
		out[2] = pz + dv * sn + dw * c;
	}

	// ------------------------------------------------------------------ collisions

	/**
	 * Walking boxes of the plank resting at angle {@code a} (ship-local, axis aligned in the ship's frame: the plank
	 * runs across the hull, along x): thin steps following the slope, each at most {@link #STEP_RISE} above or below
	 * the next, so walkers go up and down without jumping. Box 0 starts {@link #INBOARD} inboard of the hinge, over the
	 * bulwark. Each box's top is the higher end of its part of the slope.
	 */
	public static List<Box> plankBoxes(Spec spec, double a) {
		double r = Math.toRadians(a), c = Math.cos(r), s = Math.sin(r);
		double L = spec.length();
		int n = Math.max(2, (int) Math.ceil(L * Math.abs(s) / STEP_RISE - 1e-9));
		n = Math.max(n, (int) Math.ceil(L * c / 1.0));
		List<Box> out = new ArrayList<>();
		double z0 = spec.hz() - spec.width() / 2, z1 = spec.hz() + spec.width() / 2;
		for (int k = 0; k < n; k++) {
			double u0 = L * k / n, u1 = L * (k + 1) / n;
			double top = spec.hy() - Math.min(u0 * s, u1 * s);
			double x0 = spec.hx() + spec.o() * (k == 0 ? -INBOARD : u0 * c);
			double x1 = spec.hx() + spec.o() * u1 * c;
			out.add(Box.of(x0, top - BOX_THICKNESS, z0, x1, top, z1));
		}
		return out;
	}

	/**
	 * The inboard step box as a staircase rising towards the hull side: n stairs of at most {@link #STAIR_RISE},
	 * stacked solid boxes from its bottom (the deck) up to its top (the hinge height). Empty without a step box.
	 */
	public static List<Box> stairBoxes(Spec spec) {
		Box st = spec.step();
		if (st == null) {
			return List.of();
		}
		double rise = st.maxY() - st.minY();
		int n = Math.max(1, (int) Math.ceil(rise / STAIR_RISE - 1e-9));
		List<Box> out = new ArrayList<>();
		boolean outboardIsMax = spec.o() > 0; // the hull side is at +x for a port plank
		double depth = (st.maxX() - st.minX()) / n;
		for (int k = 0; k < n; k++) {
			double top = st.minY() + rise * (k + 1) / n;
			// stair k (k = 0 the lowest, innermost) reaches from its inner edge to the hull side
			if (outboardIsMax) {
				out.add(new Box(st.minX() + depth * k, st.minY(), st.minZ(), st.maxX(), top, st.maxZ()));
			} else {
				out.add(new Box(st.minX(), st.minY(), st.minZ(), st.maxX() - depth * k, top, st.maxZ()));
			}
		}
		return out;
	}

	/** Every box that collides while the plank is deployed at angle {@code a}: the plank's steps and the stairs. */
	public static List<Box> deployedBoxes(Spec spec, double a) {
		List<Box> out = new ArrayList<>(plankBoxes(spec, a));
		out.addAll(stairBoxes(spec));
		return out;
	}

	// ------------------------------------------------------------------ landing and clearance

	/** What the safety checks need to know of the world, in ship-local coordinates. */
	public interface Terrain {
		/**
		 * Highest top surface of a solid block in the column at (lx, lz) between yMin and yMax (ship-local), NaN if
		 * none or if that part of the world is not loaded (never load chunks).
		 */
		double surface(double lx, double lz, double yMin, double yMax);

		/** Is this ship-local point inside a solid block's collision shape (true where the world is not loaded)? */
		boolean solid(double lx, double ly, double lz);
	}

	/** Result of the landing search: the deployed angle, or NaN and the reason (French, for the action bar). */
	public record Landing(double angle, double surfaceY, String refusal) {
		public boolean ok() {
			return refusal == null;
		}
	}

	public static final String NO_LANDING = "Aucun quai ni ponton à portée : la passerelle ne peut pas être déployée dans le vide.";
	public static final String TOO_LOW = "Le quai est trop bas pour la passerelle (pente trop forte).";
	public static final String TOO_HIGH = "Le quai est trop haut pour la passerelle.";
	public static final String NO_STABLE = "Pas d'appui stable au bout de la passerelle.";
	public static final String SWING_BLOCKED = "Un bloc gêne le déploiement de la passerelle.";
	public static final String PATH_BLOCKED = "Un bloc encombre la passerelle : le passage serait bouché.";

	/**
	 * Looks for a solid top surface (quay, platform) under or over the tip, within the spec's slope range and
	 * {@link Spec#maxDrop}: scans the columns at the tip (centre and both corners), computes the angle at which the
	 * tip rests {@link #TIP_LIFT} above that surface, and repeats at the new reach of the tip until it settles.
	 */
	public static Landing findLanding(Spec spec, Terrain t) {
		double L = spec.length();
		double drop = Math.min(spec.maxDrop(), L * Math.sin(Math.toRadians(spec.maxAngle())));
		// one block beyond the allowed range both ways: a quay just out of reach is reported as too high / too low
		double yMin = spec.hy() - drop - TIP_LIFT - 1.0;
		double yMax = spec.hy() - L * Math.sin(Math.toRadians(spec.minAngle())) - TIP_LIFT + 1.0;
		double a = Math.max(spec.minAngle(), Math.min(spec.maxAngle(), 0.0));
		double surface = Double.NaN;
		for (int iter = 0; iter < 4; iter++) {
			double reach = L * Math.cos(Math.toRadians(a)) - 0.2;
			double s = Double.NaN;
			for (double w : new double[] {0.0, -(spec.width() / 2 - 0.2), spec.width() / 2 - 0.2}) {
				double lx = spec.hx() + spec.o() * reach;
				double v = t.surface(lx, spec.hz() + w, yMin, yMax);
				if (!Double.isNaN(v) && !(v <= s)) {
					s = v;
				}
			}
			if (Double.isNaN(s)) {
				return iter == 0 || Double.isNaN(surface) ? new Landing(Double.NaN, Double.NaN, NO_LANDING)
						: new Landing(Double.NaN, Double.NaN, NO_STABLE);
			}
			double next = Math.toDegrees(Math.asin(Math.max(-1, Math.min(1, (spec.hy() - (s + TIP_LIFT)) / L))));
			// out of the slope range: no need to look further
			if (spec.hy() - s > spec.maxDrop() + TIP_LIFT + 1e-6 || next > spec.maxAngle() + 1e-6) {
				return new Landing(Double.NaN, s, TOO_LOW);
			}
			if (next < spec.minAngle() - 1e-6) {
				return new Landing(Double.NaN, s, TOO_HIGH);
			}
			boolean settled = !Double.isNaN(surface) && Math.abs(s - surface) < 0.05 && Math.abs(next - a) < 0.5;
			surface = s;
			a = next;
			if (settled) {
				break;
			}
		}
		if (spec.hy() - surface > spec.maxDrop() + TIP_LIFT + 1e-6 || a > spec.maxAngle() + 1e-6) {
			return new Landing(Double.NaN, surface, TOO_LOW);
		}
		if (a < spec.minAngle() - 1e-6) {
			return new Landing(Double.NaN, surface, TOO_HIGH);
		}
		return new Landing(a, surface, null);
	}

	/**
	 * Clearance of a deploy to angle {@code a}: the plank's swing from its stowed angle must not cross solid blocks
	 * (its tip only touches the landing at the end), and the walkway on the deployed plank must be free (headroom for
	 * a player). Returns null if clear, else the reason (French).
	 */
	public static String clearance(Spec spec, double a, Terrain t) {
		double L = spec.length();
		double hw = spec.width() / 2 - 0.15;
		double from = spec.stowedAngle();
		int steps = Math.max(2, (int) Math.ceil(Math.abs(a - from) / 7.5));
		for (int i = 0; i <= steps; i++) {
			double ang = from + (a - from) * i / steps;
			boolean last = i == steps;
			for (double u = 0.4; u <= L + 1e-6; u += 0.4) {
				double uu = Math.min(u, L - 0.05);
				for (double w : new double[] {-hw, 0.0, hw}) {
					// just above the walking surface; also its underside while swinging (not at rest on the landing)
					double[] p = spec.point(ang, uu, 0.05, w);
					if (t.solid(p[0], p[1], p[2])) {
						return SWING_BLOCKED;
					}
					if (!last && Math.abs(ang - a) > 4.0) {
						double[] q = spec.point(ang, uu, -0.2, w);
						if (t.solid(q[0], q[1], q[2])) {
							return SWING_BLOCKED;
						}
					}
				}
			}
		}
		for (double u = 0.5; u <= L - 0.25; u += 0.5) {
			for (double w : new double[] {-hw + 0.15, hw - 0.15}) {
				// headroom measured straight up from the walking surface
				double[] p = spec.point(a, u, 0, w);
				for (double v : new double[] {0.6, 1.5}) {
					if (t.solid(p[0], p[1] + v, p[2])) {
						return PATH_BLOCKED;
					}
				}
			}
		}
		return null;
	}

	// ------------------------------------------------------------------ picking

	/** Ship-local box of the lever (clicked to deploy / retract). */
	public static Box leverBox(Spec spec) {
		return new Box(spec.leverX() - 0.32, spec.leverY(), spec.leverZ() - 0.32, spec.leverX() + 0.32, spec.leverY() + 1.0,
				spec.leverZ() + 0.32);
	}

	/** Ray (ship-local origin and direction) against the lever: entry distance, or -1. */
	public static double pickLever(Spec spec, double[] o, double[] d, double maxDist) {
		Box b = leverBox(spec);
		double t = ShipGeometry.rayBox(o, d, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ());
		return t >= 0 && t <= maxDist ? t : -1;
	}

	/** Does a world-independent local box intersect any of the boxes (all ship-local)? */
	public static boolean intersects(List<Box> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		for (Box b : boxes) {
			if (x0 < b.maxX() && x1 > b.minX() && y0 < b.maxY() && y1 > b.minY() && z0 < b.maxZ() && z1 > b.minZ()) {
				return true;
			}
		}
		return false;
	}
}
