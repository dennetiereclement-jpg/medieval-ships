package fr.medievalships.core;

/**
 * The hit reaction of one training target, played on the client only (1.19.0): a few light damped oscillators, one per
 * moving bone of the target, stepped once per client tick while something moves and not at all at rest.
 *
 * <p>Each bone has a small rotation (a rotation vector in prop-local axes, radians: x tilts towards +z, z tilts towards
 * -x, y twists) relative to its parent bone, about the bone's origin (the pivot of the target, the neck, the shoulders,
 * the shield's grip, the sword's grip), pulled back to rest by a spring and slowed by damping
 * ({@code a = -w² sin(angle) - 2 zeta w speed}). A hit gives an angular kick that makes the hit point move along the
 * hit direction ({@code (r x d) v / |r|²}, r from the bone's origin to the hit point): the dummy's body tilts back away
 * from the attacker (and twists a little if the hit is off its axis), the punching bag swings away from it like a
 * pendulum about the top of its chain ({@code w = sqrt(g / L)}), a new hit adds to the current motion. The children
 * that are not hit follow the body with a lag (driven by its angular acceleration): the head nods, the arms swing.
 * On a sword-and-shield dummy a hit on the shield throws the shield arm back and makes the shield wobble, a hit on the
 * body tilts the dummy and makes the sword ring (a fast, little damped vibration).
 *
 * <p>Pure math with no Minecraft class: the entity feeds it the hits it receives from the server and steps it; the
 * renderer reads {@link #rotation} for each bone (see TrainingTargetRenderer).
 */
public final class TargetMotion {
	/** The bones of a target, in the order of {@link #rotation}. */
	public static final int ROOT = 0, HEAD = 1, ARM_L = 2, ARM_R = 3, SHIELD = 4, SWORD = 5, BONES = 6;
	/** One game tick in seconds, and the integration sub-steps per tick (the sword's vibration is the stiffest spring). */
	static final double TICK = 0.05;
	static final int SUBSTEPS = 6;
	/** Below these (radians, radians per second) for every bone, the target is at rest: everything is zeroed and stops. */
	static final double REST_ANGLE = 1.5e-3, REST_SPEED = 1.5e-2;
	/** A motion that never settles (it always does) is stopped after this many ticks without a hit. */
	static final int MAX_TICKS = 1200;
	private static final double G = 9.81;

	private final TrainingTarget target;
	/** Prop-local origins of the bones (blocks); the root's is the pivot, a missing one is guessed or unused. */
	private final double[][] joints = new double[BONES][];
	/** Per bone: tilt and twist angular frequencies (rad/s), damping ratios, largest angle, drive by the root's acceleration. */
	private final double[] tilt = new double[BONES], twist = new double[BONES], zetaTilt = new double[BONES], zetaTwist = new double[BONES],
			max = new double[BONES], drive = new double[BONES];
	private final double[][] angle = new double[BONES][3], speed = new double[BONES][3], last = new double[BONES][3];
	private final double[] rootAccel = new double[3];
	/** Linear speed (blocks/s) given to the hit point of the body (root) and of the shield arm by a full-strength hit. */
	private final double kick, armKick;
	private boolean moving;
	private int ticks;

	/**
	 * @param target the target, prop-local (facing south: the model's own axes)
	 * @param joints the prop-local origins of {@link #ROOT}... {@link #SWORD} from the model (any may be null, the array too)
	 */
	public TargetMotion(TrainingTarget target, double[][] joints) {
		this.target = target;
		for (int b = 0; b < BONES; b++) {
			this.joints[b] = joints != null && b < joints.length ? joints[b] : null;
		}
		this.joints[ROOT] = new double[] {target.px(), target.py(), target.pz()};
		TentType.Box h = target.hitbox();
		switch (target.kind()) {
			case BAG -> {
				// a pendulum about the top of the chain: w = sqrt(g / L), L down to the middle of the bag
				double length = Math.max(0.4, target.py() - (h.y0() + h.y1()) / 2);
				set(ROOT, Math.sqrt(G / length), 3.2, 0.15, 0.25, 0.75, 0);
				kick = 1.8;
				armKick = 0;
			}
			case SHIELD_DUMMY -> {
				// a heavier dummy on a stiffer post: it tilts less; its sword rings, its shield arm recoils
				set(ROOT, 8.5, 10, 0.25, 0.35, 0.25, 0);
				set(HEAD, 11, 11, 0.25, 0.3, 0.4, 0.7);
				set(ARM_L, 9, 9, 0.3, 0.3, 0.55, 0.6);
				set(ARM_R, 8, 8, 0.22, 0.3, 0.5, 0.8);
				set(SHIELD, 16, 16, 0.12, 0.15, 0.22, 0.2);
				set(SWORD, 42, 42, 0.05, 0.08, 0.12, 0.15);
				kick = 1.8;
				armKick = 1.5;
			}
			default -> {
				// the straw dummy on its post: about 1.1 Hz, settles in about 3 s
				set(ROOT, 7, 9, 0.22, 0.35, 0.35, 0);
				set(HEAD, 11, 11, 0.25, 0.3, 0.45, 0.9);
				set(ARM_L, 8, 8, 0.2, 0.3, 0.6, 1.2);
				set(ARM_R, 8, 8, 0.2, 0.3, 0.6, 1.2);
				kick = 2.6;
				armKick = 0;
			}
		}
	}

	private void set(int bone, double wTilt, double wTwist, double zTilt, double zTwist, double maxAngle, double driven) {
		tilt[bone] = wTilt;
		twist[bone] = wTwist;
		zetaTilt[bone] = zTilt;
		zetaTwist[bone] = zTwist;
		max[bone] = maxAngle;
		drive[bone] = driven;
	}

	public TrainingTarget target() {
		return target;
	}

	/** Is anything moving? (false at rest: {@link #tick} then does nothing) */
	public boolean moving() {
		return moving;
	}

	/**
	 * A hit (prop-local): the horizontal direction it pushes ({@code dirX, dirZ}, from the attacker towards the target;
	 * normalised here), its strength (0..1, {@link TrainingTarget#strength}), the part hit ({@link TrainingTarget#PART_BODY}
	 * or {@link TrainingTarget#PART_SHIELD}), the hit point, and a seed for the small side wobble (the server's hit
	 * counter, the same on every client).
	 */
	public void hit(double dirX, double dirZ, double strength, int part, double hx, double hy, double hz, int seed) {
		double len = Math.hypot(dirX, dirZ);
		if (len < 1e-6 || !(strength > 0)) {
			return;
		}
		double dx = dirX / len, dz = dirZ / len;
		double s = Math.min(1.0, strength);
		// a small deterministic side wobble (-1..1), so that two hits do not look the same
		double side = ((((seed * 0x9E3779B1L) >>> 8) & 0xFFFF) / 32767.5) - 1.0;
		TentType.Box hb = target.hitbox();
		if (!Double.isFinite(hx) || !Double.isFinite(hy) || !Double.isFinite(hz)) {
			hx = (hb.x0() + hb.x1()) / 2;
			hy = (hb.y0() + hb.y1()) / 2;
			hz = (hb.z0() + hb.z1()) / 2;
		}
		boolean shield = part == TrainingTarget.PART_SHIELD && target.hasShield();
		// the body (or the bag) about its pivot: a hit on the shield moves it a little
		kickAt(ROOT, hx - target.px(), hy - target.py(), hz - target.pz(), dx, dz, kick * s * (shield ? 0.35 : 1.0), side * 0.18);
		if (target.kind() == TrainingTarget.Kind.SHIELD_DUMMY) {
			if (shield) {
				// the shield arm thrown back from its shoulder, the shield wobbling on its grip, the sword a little
				double[] shoulder = joints[ARM_L];
				if (shoulder == null) {
					TentType.Box sb = target.shieldBox();
					shoulder = new double[] {(sb.x0() + sb.x1()) / 2, sb.y1() + 0.1, (sb.z0() + sb.z1()) / 2};
				}
				kickAt(ARM_L, hx - shoulder[0], hy - shoulder[1], hz - shoulder[2], dx, dz, armKick * s, side * 0.25);
				// about the horizontal axis across the hit and a little about the vertical
				speed[SHIELD][0] += dz * 1.8 * s;
				speed[SHIELD][2] += -dx * 1.8 * s;
				speed[SHIELD][1] += side * 0.9 * s;
				ring(0.8 * s, side);
			} else {
				ring(2.2 * s, side);
			}
		}
		moving = true;
		ticks = 0;
	}

	/**
	 * Kicks a bone so that the point at (rx, ry, rz) from its origin moves at {@code v} along (dx, 0, dz); plus a small
	 * kick across ({@code across} of it) for the side wobble.
	 */
	private void kickAt(int bone, double rx, double ry, double rz, double dx, double dz, double v, double across) {
		double r2 = Math.max(0.09, rx * rx + ry * ry + rz * rz);
		// w = (r x d) v / |r|², d = (dx, 0, dz)
		double wx = ry * dz, wy = rz * dx - rx * dz, wz = -ry * dx;
		// across: the same with the direction turned a quarter (d' = (-dz, 0, dx))
		double ax = ry * dx, ay = -rz * dz - rx * dx, az = ry * dz;
		speed[bone][0] += (wx + across * ax) * v / r2;
		speed[bone][1] += (wy + across * ay) * v / r2;
		speed[bone][2] += (wz + across * az) * v / r2;
	}

	/** Sets the sword ringing: a fast small vibration about a horizontal axis. */
	private void ring(double amount, double side) {
		speed[SWORD][0] += amount * (0.6 + 0.4 * side);
		speed[SWORD][2] += amount * (0.6 - 0.4 * side);
	}

	/** One client tick: steps the oscillators (when moving), then stops everything once it is all below the rest thresholds. */
	public void tick() {
		for (int b = 0; b < BONES; b++) {
			System.arraycopy(angle[b], 0, last[b], 0, 3);
		}
		if (!moving) {
			return;
		}
		double h = TICK / SUBSTEPS;
		for (int k = 0; k < SUBSTEPS; k++) {
			for (int b = 0; b < BONES; b++) {
				if (tilt[b] <= 0) {
					continue;
				}
				for (int a = 0; a < 3; a++) {
					double w = a == 1 ? twist[b] : tilt[b];
					double z = a == 1 ? zetaTwist[b] : zetaTilt[b];
					double acc = -w * w * Math.sin(angle[b][a]) - 2 * z * w * speed[b][a];
					if (b != ROOT) {
						acc -= drive[b] * rootAccel[a];
					} else {
						rootAccel[a] = acc;
					}
					speed[b][a] += acc * h;
					angle[b][a] += speed[b][a] * h;
					if (angle[b][a] > max[b]) {
						angle[b][a] = max[b];
						speed[b][a] = -0.3 * Math.abs(speed[b][a]);
					} else if (angle[b][a] < -max[b]) {
						angle[b][a] = -max[b];
						speed[b][a] = 0.3 * Math.abs(speed[b][a]);
					}
				}
			}
		}
		boolean still = true;
		for (int b = 0; b < BONES && still; b++) {
			for (int a = 0; a < 3; a++) {
				if (Math.abs(angle[b][a]) > REST_ANGLE || Math.abs(speed[b][a]) > REST_SPEED) {
					still = false;
					break;
				}
			}
		}
		if (still || ++ticks > MAX_TICKS) {
			for (int b = 0; b < BONES; b++) {
				for (int a = 0; a < 3; a++) {
					angle[b][a] = 0;
					speed[b][a] = 0;
				}
			}
			rootAccel[0] = rootAccel[1] = rootAccel[2] = 0;
			moving = false;
		}
	}

	/**
	 * The rotation of a bone between the last tick and this one ({@code partial} 0..1): a rotation vector in prop-local
	 * axes, radians, written to {@code out[0..2]}.
	 */
	public void rotation(int bone, float partial, float[] out) {
		for (int a = 0; a < 3; a++) {
			out[a] = (float) (last[bone][a] + (angle[bone][a] - last[bone][a]) * partial);
		}
	}

	/** The current angle of a bone about an axis (0 x, 1 y, 2 z), radians (tests). */
	public double angle(int bone, int axis) {
		return angle[bone][axis];
	}
}
