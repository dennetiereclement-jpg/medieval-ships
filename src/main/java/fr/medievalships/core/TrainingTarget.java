package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

/**
 * An interactive training target of a training area (1.19.0): a dummy, a sword-and-shield dummy or a punching bag that
 * players hit. Read from the optional {@code "targets"} list of {@code assets/medievalships/training/<id>.json}
 * (written by the training generators):
 *
 * <pre>
 * "targets": [ {"kind": "dummy" | "shield_dummy" | "bag", "bone": "target_0",
 *               "pivot": [x, y, z],                    // rotation point: base of the dummy's post / top of the bag's chain
 *               "hitbox": [x0, y0, z0, x1, y1, z1],    // the part that can be hit (prop-local, axis-aligned)
 *               "shield_box": [x0, y0, z0, x1, y1, z1] // shield_dummy only: the shield
 *             }, ... ]
 * </pre>
 *
 * Coordinates are prop-local blocks like the colliders' (y up from the ground top, +z the prop's front, the anchor
 * block's centre at 0, 0, 0), turned with the prop's FACING by {@link #rotate(int)} (the same quarter turns as
 * {@link TentType#rotate(double, double, int)}). The model moves each target's parts under its own top-level bone
 * {@link #bone()} (origin = the pivot) with the children {@link #head()}, {@link #armLeft()}, {@link #armRight()},
 * {@link #shield()} (child of the left arm) and {@link #sword()} (child of the right arm): the static renderer leaves
 * them to the target's entity, which draws them swinging after each hit.
 *
 * @param kind      what it is (its reaction, its sounds)
 * @param bone      the top-level bone of its moving parts
 * @param px        pivot x (prop-local blocks)
 * @param py        pivot y
 * @param pz        pivot z
 * @param hitbox    the part that can be hit
 * @param shieldBox the shield of a sword-and-shield dummy, or null
 */
public record TrainingTarget(Kind kind, String bone, double px, double py, double pz, TentType.Box hitbox, TentType.Box shieldBox) {
	/** The three kinds of targets (JSON {@code "kind"}). */
	public enum Kind {
		/** A straw dummy on a post: tilts back, nods, swings its arms. */
		DUMMY("dummy"),
		/** A dummy holding a sword and a shield: the shield recoils when it is hit, the sword rings when the body is. */
		SHIELD_DUMMY("shield_dummy"),
		/** A punching bag on a chain: swings like a pendulum. */
		BAG("bag");

		public final String id;

		Kind(String id) {
			this.id = id;
		}

		/** The kind of a JSON name (case and dashes ignored); unknown names are dummies. */
		public static Kind of(String name) {
			String s = name == null ? "" : name.trim().toLowerCase(Locale.ROOT).replace('-', '_');
			for (Kind k : values()) {
				if (k.id.equals(s)) {
					return k;
				}
			}
			return s.contains("bag") ? BAG : s.contains("shield") ? SHIELD_DUMMY : DUMMY;
		}
	}

	/** The part of a target a hit landed on (sent to the clients with the hit). */
	public static final int PART_BODY = 0, PART_SHIELD = 1;

	public String head() {
		return bone + "_head";
	}

	public String armLeft() {
		return bone + "_arm_l";
	}

	public String armRight() {
		return bone + "_arm_r";
	}

	public String shield() {
		return bone + "_shield";
	}

	public String sword() {
		return bone + "_sword";
	}

	/** Does it have a shield that can be hit apart from its body? */
	public boolean hasShield() {
		return kind == Kind.SHIELD_DUMMY && shieldBox != null;
	}

	/** The room the target's entity takes: its hitbox, with its shield when it has one (so the shield can be hit). */
	public TentType.Box reach() {
		if (!hasShield()) {
			return hitbox;
		}
		TentType.Box s = shieldBox;
		return new TentType.Box(Math.min(hitbox.x0(), s.x0()), Math.min(hitbox.y0(), s.y0()), Math.min(hitbox.z0(), s.z0()),
				Math.max(hitbox.x1(), s.x1()), Math.max(hitbox.y1(), s.y1()), Math.max(hitbox.z1(), s.z1()));
	}

	/** The target turned by quarter turns (pivot and boxes alike), like the colliders. */
	public TrainingTarget rotate(int quarter) {
		double[] p = TentType.rotate(px, pz, quarter);
		return new TrainingTarget(kind, bone, p[0], py, p[1], TentType.rotate(hitbox, quarter),
				shieldBox == null ? null : TentType.rotate(shieldBox, quarter));
	}

	/** The inverse of {@link TentType#rotate(double, double, int)}: a facing-turned point (or direction) back to prop-local. */
	public static double[] unrotate(double x, double z, int quarter) {
		return TentType.rotate(x, z, (4 - (quarter & 3)) & 3);
	}

	/** A prop-local yaw (Minecraft convention: 0 = +z, 90 = -x) turned with the facing: yaw + 90 per quarter turn. */
	public static float rotateYaw(float yaw, int quarter) {
		return ((yaw + 90f * (quarter & 3)) % 360f + 360f) % 360f;
	}

	/**
	 * The distance along a ray (origin o, direction d, any length: t is in units of d) at which it enters a box, 0 if the
	 * origin is inside, {@link Double#POSITIVE_INFINITY} if it misses (or the box is behind).
	 */
	public static double rayBox(TentType.Box b, double ox, double oy, double oz, double dx, double dy, double dz) {
		double t0 = 0, t1 = Double.POSITIVE_INFINITY;
		double[] o = {ox, oy, oz}, d = {dx, dy, dz};
		double[] lo = {b.x0(), b.y0(), b.z0()}, hi = {b.x1(), b.y1(), b.z1()};
		for (int a = 0; a < 3; a++) {
			if (Math.abs(d[a]) < 1e-12) {
				if (o[a] < lo[a] || o[a] > hi[a]) {
					return Double.POSITIVE_INFINITY;
				}
				continue;
			}
			double ta = (lo[a] - o[a]) / d[a], tb = (hi[a] - o[a]) / d[a];
			if (ta > tb) {
				double s = ta;
				ta = tb;
				tb = s;
			}
			t0 = Math.max(t0, ta);
			t1 = Math.min(t1, tb);
			if (t0 > t1) {
				return Double.POSITIVE_INFINITY;
			}
		}
		return t0;
	}

	/** The reaction strength (0.25 .. 1) of a hit of {@code amount} damage: a fist about 0.35, a sword or a full bow about 1. */
	public static float strength(float amount) {
		if (Float.isNaN(amount)) {
			return 0.25f;
		}
		return Math.max(0.25f, Math.min(1f, 0.25f + amount / 10f));
	}

	/**
	 * The targets of a prop's JSON, turned to each facing (index = quarter turns): four empty lists when it has none.
	 * Entries without a usable pivot or hitbox are skipped; a missing bone is {@code target_<i>}.
	 */
	public static List<List<TrainingTarget>> parseAll(JsonObject root) {
		List<TrainingTarget> list = new ArrayList<>();
		if (root.has("targets") && root.get("targets").isJsonArray()) {
			JsonArray a = root.getAsJsonArray("targets");
			for (int i = 0; i < a.size(); i++) {
				JsonElement e = a.get(i);
				if (!e.isJsonObject()) {
					continue;
				}
				TrainingTarget t = parse(e.getAsJsonObject(), list.size());
				if (t != null) {
					list.add(t);
				}
			}
		}
		List<List<TrainingTarget>> turned = new ArrayList<>();
		for (int q = 0; q < 4; q++) {
			List<TrainingTarget> l = new ArrayList<>();
			for (TrainingTarget t : list) {
				l.add(t.rotate(q));
			}
			turned.add(List.copyOf(l));
		}
		return List.copyOf(turned);
	}

	/** One entry of {@code "targets"}, or null when it has no pivot or no hitbox. */
	static TrainingTarget parse(JsonObject o, int index) {
		JsonArray pivot = o.has("pivot") && o.get("pivot").isJsonArray() ? o.getAsJsonArray("pivot") : null;
		TentType.Box hitbox = box(o, "hitbox");
		if (pivot == null || pivot.size() < 3 || hitbox == null) {
			return null;
		}
		Kind kind = Kind.of(o.has("kind") ? o.get("kind").getAsString() : null);
		String bone = o.has("bone") && !o.get("bone").isJsonNull() ? o.get("bone").getAsString() : "target_" + index;
		TentType.Box shield = kind == Kind.SHIELD_DUMMY ? box(o, "shield_box") : null;
		return new TrainingTarget(kind, bone, pivot.get(0).getAsDouble(), pivot.get(1).getAsDouble(), pivot.get(2).getAsDouble(), hitbox, shield);
	}

	/** A box field (corners in any order), or null when absent, malformed or empty. */
	private static TentType.Box box(JsonObject o, String key) {
		if (!o.has(key) || !o.get(key).isJsonArray()) {
			return null;
		}
		JsonArray a = o.getAsJsonArray(key);
		if (a.size() < 6) {
			return null;
		}
		double x0 = a.get(0).getAsDouble(), y0 = a.get(1).getAsDouble(), z0 = a.get(2).getAsDouble();
		double x1 = a.get(3).getAsDouble(), y1 = a.get(4).getAsDouble(), z1 = a.get(5).getAsDouble();
		TentType.Box b = new TentType.Box(Math.min(x0, x1), Math.min(y0, y1), Math.min(z0, z1), Math.max(x0, x1), Math.max(y0, y1), Math.max(z0, z1));
		return b.width() > 1e-6 && b.height() > 1e-6 && b.depth() > 1e-6 ? b : null;
	}
}
