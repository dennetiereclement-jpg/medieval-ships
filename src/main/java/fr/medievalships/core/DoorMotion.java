package fr.medievalships.core;

/**
 * The movement of a door (pure Java, tested in JUnit). The server keeps only the target (open or closed), the game
 * tick the current movement started at and the progress it started from; the progress at any time follows
 * ({@link #progress}: linear in time, 0 = closed, 1 = open), on the server for the collisions and the sounds and on
 * every client, between two ticks, for the drawing (nothing is sent per tick).
 *
 * <p>The pose at a progress (1.32.0, the same functions on the server and on the clients), for a {@link Curve} of the
 * door's size:
 * <ul>
 * <li>the unlocking ({@link #unlock}, the first {@link Curve#unlock} of the progress, about 15 %): the bolts slide out,
 * the handles and rings turn ({@link #handle}); the leaves wait;</li>
 * <li>then the leaves ({@link #leaf}): a short pause, then a slow start, an acceleration and a slowing down (a cycloid:
 * no jerk, the inertia of a heavy leaf); at the end of an opening they go a little past the stop and settle back
 * ({@link Curve#overshoot}); at the end of a closing they hit the frame still moving ({@link Curve#impactSpeed}) and
 * bounce back a little ({@link Curve#rebound}) before they rest;</li>
 * <li>the second leaf of a double door starts a little later ({@link Curve#delay}) and, closing, closes first;</li>
 * <li>a movement that turns back half way starts from the pose the other one had ({@link #leafAt}: no jump).</li>
 * </ul>
 * The gears turn with their leaf ({@link #gearAngle} of the leaf's opening: their speed follows the leaves'), the
 * piston rods slide with it.
 *
 * <p>The collisions ({@link #solidAfter}): a closed door is solid; opening, it stays solid until every leaf is half open;
 * once it is no longer solid it becomes solid again only when its leaves are closed and still (closing, the passage
 * stays free until then; a closing that turns back to opening does not make it solid again).
 */
public final class DoorMotion {
	/** Opening of the leaves (0..1) at which an opening door stops being solid. */
	public static final double HALF = 0.5;
	/** Distance (blocks) a bolt slides (during the unlocking). */
	public static final double BOLT_TRAVEL = 0.25;
	/** Distance (blocks) a piston rod slides with its leaf. */
	public static final double PISTON_TRAVEL = 0.25;
	/**
	 * Angle (degrees) a handle or a ring ({@code handle_*}) turns while the door unlocks, clockwise seen from the front:
	 * a ring goes no further (it would hit the strike side); the wheel of a steam door turns freely
	 * ({@link #WHEEL_ANGLE}).
	 */
	public static final double HANDLE_ANGLE = 30.0, WHEEL_ANGLE = 180.0;
	/** Ticks over which a movement that turned back fades from the pose of the other one. */
	public static final double BLEND_TICKS = 6.0;
	/** Part of the leaves' stroke after which an opening leaf runs past its stop (the settling at the end). */
	public static final double OVERSHOOT_FROM = 0.72;
	/** Events of a tick of movement ({@link #events}). */
	public static final int EV_LEAVES_START = 1, EV_IMPACT = 2, EV_SECOND_IMPACT = 4, EV_LOCKED = 8, EV_OPENED = 16, EV_CREAK = 32;

	/**
	 * The shape of a movement: {@code unlock} the share of the progress the unlocking takes; {@code pause} the share of
	 * a leaf's stroke before it moves (opening) and where it bounces (closing); {@code overshoot} how far (share of 90°)
	 * an opening leaf runs past its stop; {@code impactSpeed} the share of its mean speed a closing leaf still has when
	 * it hits the frame; {@code rebound} how far (share of 90°) it bounces back; {@code delay} the head start of the
	 * first leaf of a double door (share of the leaves' stroke); {@code creakPeriod} the ticks between two creaks (0:
	 * none).
	 */
	public record Curve(double unlock, double pause, double overshoot, double impactSpeed, double rebound, double delay, int creakPeriod) {
	}

	public static final Curve SMALL = new Curve(0.15, 0.05, 0.05, 0.55, 0.025, 0.0, 0);
	public static final Curve MEDIUM = new Curve(0.15, 0.05, 0.04, 0.55, 0.02, 0.08, 0);
	public static final Curve LARGE = new Curve(0.15, 0.04, 0.03, 0.5, 0.015, 0.10, 16);

	private DoorMotion() {
	}

	public static Curve curve(DoorType.Size size) {
		return switch (size) {
			case SMALL -> SMALL;
			case MEDIUM -> MEDIUM;
			case LARGE -> LARGE;
		};
	}

	public static Curve curve(DoorType type) {
		return curve(type.size());
	}

	// ------------------------------------------------------------------ time

	/**
	 * Progress 0..1 at time {@code now} (ticks, fractional on a client) of a movement towards {@code target} that
	 * started at {@code startTick} from {@code startProgress} and takes {@code duration} ticks for a full stroke.
	 */
	public static double progress(boolean target, long startTick, double startProgress, double now, int duration) {
		double elapsed = Math.max(0, now - startTick);
		double step = elapsed / Math.max(1, duration);
		double p = target ? startProgress + step : startProgress - step;
		return clamp01(p);
	}

	/** Is the door still moving at this progress? */
	public static boolean moving(boolean target, double progress) {
		return target ? progress < 1 : progress > 0;
	}

	/** Ticks left before the movement ends. */
	public static int ticksLeft(boolean target, double progress, int duration) {
		return (int) Math.ceil((target ? 1 - progress : progress) * duration - 1e-9);
	}

	/** A smooth curve (smoothstep): slow start, slow end (the 1.31.0 curve of the drawing; still used for small ramps). */
	public static double ease(double p) {
		p = clamp01(p);
		return p * p * (3 - 2 * p);
	}

	// ------------------------------------------------------------------ the pose

	/** Where the leaves are in their stroke (0..1) at a progress: 0 during the unlocking. */
	public static double leafPhase(Curve c, double t) {
		return clamp01((clamp01(t) - c.unlock) / (1 - c.unlock));
	}

	/**
	 * The stroke (0..1) of one leaf ({@code leaf} 0 = left, the first; 1 = right, the second) of a door with
	 * {@code leaves} leaves at a leaves' phase: the first leaf has a head start of {@link Curve#delay}.
	 */
	public static double leafShare(Curve c, int leaves, int leaf, double s) {
		if (leaves < 2 || c.delay <= 0) {
			return clamp01(s);
		}
		double d = c.delay;
		return leaf == 0 ? clamp01(s / (1 - d)) : clamp01((s - d) / (1 - d));
	}

	/** The cycloid 0..1: zero speed and zero acceleration at both ends, the fastest in the middle. */
	public static double cycloid(double x) {
		x = clamp01(x);
		return x - Math.sin(2 * Math.PI * x) / (2 * Math.PI);
	}

	/**
	 * How open a leaf is (0 closed, 1 open: 90°; a little more while it settles at the end of an opening, a little
	 * open while it bounces at the end of a closing) at its stroke {@code u}, opening or closing.
	 */
	public static double leafCurve(Curve c, boolean opening, double u) {
		u = clamp01(u);
		if (u <= c.pause) {
			// opening: still waiting; closing: it hit the frame and bounces back a little before resting
			return opening || c.pause <= 0 ? 0 : c.rebound * Math.sin(Math.PI * u / c.pause);
		}
		double x = (u - c.pause) / (1 - c.pause);
		if (opening) {
			double f = cycloid(x);
			if (x > OVERSHOOT_FROM) {
				double b = Math.sin(Math.PI * (x - OVERSHOOT_FROM) / (1 - OVERSHOOT_FROM));
				f += c.overshoot * b * b; // past the stop and back, zero speed at the end
			}
			return f;
		}
		// closing: the cycloid on its open half; towards the frame the leaf keeps part of its speed (it slams)
		double k0 = 1 - c.impactSpeed;
		double k = k0 + (1 - k0) * ease(x / 0.5);
		return x - k * Math.sin(2 * Math.PI * x) / (2 * Math.PI);
	}

	/** How open a leaf is at a progress, opening ({@code target}) or closing (no turning back taken into account). */
	public static double leaf(Curve c, int leaves, int leaf, boolean target, double t) {
		return leafCurve(c, target, leafShare(c, leaves, leaf, leafPhase(c, t)));
	}

	/**
	 * How open a leaf is at time {@code now} of a movement (fractional between two ticks on a client): {@link #leaf},
	 * and for a movement that started half way (it turned back), the pose of the other movement at that point faded out
	 * over {@link #BLEND_TICKS}.
	 */
	public static double leafAt(Curve c, int leaves, int leaf, boolean target, long startTick, double startProgress, double now, int duration) {
		double t = progress(target, startTick, startProgress, now, duration);
		double v = leaf(c, leaves, leaf, target, t);
		if (startProgress > 0 && startProgress < 1) {
			double e = (now - startTick) / BLEND_TICKS;
			if (e < 1) {
				double from = leaf(c, leaves, leaf, !target, startProgress), to = leaf(c, leaves, leaf, target, startProgress);
				v += (from - to) * (1 - ease(Math.max(0, e)));
			}
		}
		return v;
	}

	/** The least open leaf at a progress of an opening (the second one of a double door). */
	public static double leastOpen(Curve c, int leaves, double t) {
		double v = leaf(c, leaves, 0, true, t);
		return leaves < 2 ? v : Math.min(v, leaf(c, leaves, 1, true, t));
	}

	/** How far the door is unlocked (0..1: the bolts out, the latch free) at a progress: over the first {@link Curve#unlock}. */
	public static double unlock(Curve c, double t) {
		return c.unlock <= 0 ? (t > 0 ? 1 : 0) : ease(clamp01(t) / c.unlock);
	}

	/**
	 * How far the handles and rings are turned (0..1) at a progress: they turn while the door unlocks, and come back
	 * while the leaves start (closing, the other way round).
	 */
	public static double handle(Curve c, double t) {
		t = clamp01(t);
		if (t <= c.unlock) {
			return c.unlock <= 0 ? 1 : ease(t / (0.6 * c.unlock));
		}
		return 1 - ease(leafPhase(c, t) / 0.25);
	}

	// ------------------------------------------------------------------ collisions and events

	/**
	 * Is the door solid after this step, given whether it was before, its target and its progress? Opening, it stops
	 * being solid once every leaf is half open; closing, it becomes solid once the leaves are closed and still (the
	 * locking that follows is done solid).
	 */
	public static boolean solidAfter(Curve c, int leaves, boolean solidBefore, boolean target, double t) {
		if (!target) {
			return t <= c.unlock + 1e-9 || solidBefore;
		}
		if (leastOpen(c, leaves, t) >= HALF) {
			return false;
		}
		return solidBefore;
	}

	/** Are the leaves moving at this progress (not waiting for the unlocking, not at rest)? */
	public static boolean leavesMoving(Curve c, double t) {
		double s = leafPhase(c, t);
		return s > 0 && s < 1;
	}

	/**
	 * What happens between the progress {@code prevT} of the previous tick and {@code t} (a bit set of {@code EV_*}):
	 * the first leaf starts moving (opening), a leaf hits the frame (closing: the last one {@link #EV_IMPACT}, the first
	 * {@link #EV_SECOND_IMPACT}), the door is locked again (closing ended) or fully open, a creak of a great gate
	 * (every {@link Curve#creakPeriod} ticks while its leaves move).
	 */
	public static int events(Curve c, int leaves, boolean target, double prevT, double t, long ticksSinceStart) {
		int e = 0;
		double sp = leafPhase(c, prevT), s = leafPhase(c, t);
		if (target) {
			if (leafShare(c, leaves, 0, sp) <= c.pause && leafShare(c, leaves, 0, s) > c.pause) {
				e |= EV_LEAVES_START;
			}
			if (prevT < 1 && t >= 1) {
				e |= EV_OPENED;
			}
		} else {
			if (leafShare(c, leaves, 0, sp) > c.pause && leafShare(c, leaves, 0, s) <= c.pause) {
				e |= EV_IMPACT;
			}
			if (leaves >= 2 && leafShare(c, leaves, 1, sp) > c.pause && leafShare(c, leaves, 1, s) <= c.pause) {
				e |= EV_SECOND_IMPACT;
			}
			if (prevT > 0 && t <= 0) {
				e |= EV_LOCKED;
			}
		}
		if (c.creakPeriod > 0 && ticksSinceStart > 0 && ticksSinceStart % c.creakPeriod == c.creakPeriod / 2 && leavesMoving(c, t)) {
			e |= EV_CREAK;
		}
		return e;
	}

	// ------------------------------------------------------------------ the moving parts

	/** Angle (degrees) of the gears at an opening of their leaf: {@code turns} full turns over the leaf's stroke. */
	public static double gearAngle(double opening, int turns) {
		return 360.0 * turns * opening;
	}

	/** How far (blocks) the bolts have slid at a progress: all their travel during the unlocking. */
	public static double boltOffset(Curve c, double t) {
		return BOLT_TRAVEL * unlock(c, t);
	}

	/** How far (blocks) the piston rods have slid at an opening of their leaf. */
	public static double pistonOffset(double opening) {
		return PISTON_TRAVEL * clamp01(opening);
	}

	/**
	 * Angle (degrees, about +z: negative = clockwise seen from the front) of the handles and rings of a door at a
	 * progress: clockwise while the door unlocks, back while the leaves start; a steam door's wheel turns further.
	 */
	public static double handleAngle(DoorType type, double t) {
		return -(type.steam() ? WHEEL_ANGLE : HANDLE_ANGLE) * handle(curve(type), t);
	}

	static double clamp01(double v) {
		return v < 0 ? 0 : v > 1 ? 1 : v;
	}
}
