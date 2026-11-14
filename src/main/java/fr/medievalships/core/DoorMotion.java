package fr.medievalships.core;

/**
 * The movement of a door (pure Java, tested in JUnit). The server keeps only the target (open or closed), the game
 * tick the current movement started at and the progress it started from; the progress at any time follows
 * ({@link #progress}: linear in time, 0 = closed, 1 = open), on the server for the collisions and the sounds and on
 * every client, every frame, for the drawing (nothing is sent per tick; the clients smooth their clock and the
 * changes of movement with {@link DoorClock} and {@link DoorTrack}).
 *
 * <p>The pose at a progress (1.33.0, the same functions on the server and on the clients), for a {@link Curve} of the
 * door's size:
 * <ul>
 * <li>opening, the unlocking first ({@link Curve#unlock} of the progress): the handles and rings turn
 * ({@link #handle}), then the bolts slide out ({@link #unlock}) and the latch clicks ({@link #EV_UNLATCH}); the leaves
 * wait;</li>
 * <li>then the leaves ({@link #leafCurve}): a push (the speed rises quickly) and the inertia of the leaf (the speed
 * falls slowly), up to a cushioned stop: the speed comes down to zero at the stop, never past it, no bounce
 * ({@link Curve#pushRise}, {@link Curve#pushFall}: the heavier, the slower the push and the longer the glide);</li>
 * <li>closing, the leaves start softly and gain speed up to the frame ({@link Curve#impactSpeed}), hit it (the slam),
 * bounce back a very little and settle ({@link Curve#bounce}, {@link Curve#rebound}: one small bounce and a tinier
 * one, damped), while the rings rattle ({@link Curve#jiggle}); then the handles turn and the bolts slide back in
 * (the locking: the last {@link Curve#unlock} of the movement);</li>
 * <li>the second leaf of a double door starts a little later ({@link Curve#delay}) and, closing, closes first (the
 * first one comes and laps over it);</li>
 * <li>a movement that turns back half way goes on from where the leaves are, on its own curve ({@link #turnBack}: no
 * jump, no rush).</li>
 * </ul>
 * The gears turn with their leaf ({@link #gearAngle} of the leaf's opening: their speed follows the leaves'), the
 * piston rods slide with it. The sounds are events of the same curve ({@link #events}).
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
	/**
	 * The unlocking, in shares of its own time: the handle is turned by {@link #HANDLE_UP}, the bolts slide out from
	 * {@link #BOLTS_FROM} to {@link #BOLTS_OUT} (the latch clicks then), the leaves start at 1; the handle comes back
	 * over the first {@link #HANDLE_BACK} of the leaves' stroke.
	 */
	public static final double HANDLE_UP = 0.5, BOLTS_FROM = 0.15, BOLTS_OUT = 0.85, HANDLE_BACK = 0.3;
	/**
	 * The locking (the end of a closing), in shares of its own time: the handle turns by {@link #LOCK_TURNED}, the
	 * bolts slide back in from {@link #LOCK_BOLTS_FROM} to {@link #LOCK_BOLTS_IN} (they clack then), the handle comes back
	 * from {@link #LOCK_RELEASE} to the end.
	 */
	public static final double LOCK_TURNED = 0.35, LOCK_BOLTS_FROM = 0.2, LOCK_BOLTS_IN = 0.75, LOCK_RELEASE = 0.6;
	/** Speed kept from one bounce of a closing leaf to the next (the second bounce is {@code RESTITUTION²} as high). */
	public static final double RESTITUTION = 0.35;
	/** Events of a tick of movement ({@link #events}). */
	public static final int EV_LEAVES_START = 1, EV_IMPACT = 2, EV_SECOND_IMPACT = 4, EV_LOCKED = 8, EV_OPENED = 16, EV_CREAK = 32,
			EV_UNLATCH = 64, EV_LATCHED = 128;

	/**
	 * The shape of a movement: {@code unlock} the share of the progress the unlocking (and, closing, the locking)
	 * takes; {@code delay} the head start of the first leaf of a double door (share of the leaves' stroke);
	 * {@code pushRise}, {@code pushFall} the opening's speed, {@code x^rise (1-x)^fall} over the stroke (the speed peaks
	 * at {@code rise / (rise + fall)}: a quick push then a long glide; the fall > 1: zero speed and no shock at the
	 * stop); {@code impactSpeed} the speed of a closing leaf when it hits the frame, in shares of its mean speed
	 * (1.5..3: it gains speed all the way); {@code bounce} the share of a closing leaf's stroke after it hit the frame
	 * (its bounces, then rest); {@code rebound} how high it bounces back (share of 90°); {@code creaks} how many creaks
	 * along a stroke (0: none); {@code jiggle} the degrees the rings rattle at the slam (0: none).
	 */
	public record Curve(double unlock, double delay, int pushRise, int pushFall, double impactSpeed, double bounce, double rebound, int creaks,
			double jiggle) {
		public Curve {
			if (unlock < 0 || unlock >= 0.5 || delay < 0 || delay >= 0.5 || pushRise < 0 || pushFall < 1 || impactSpeed < 1.5 || impactSpeed > 3
					|| bounce < 0 || bounce >= 0.5 || rebound < 0 || rebound > 0.1 || creaks < 0) {
				throw new IllegalArgumentException("bad door curve");
			}
		}
	}

	/** A small door (16 ticks), light: a brisk push that friction soon stops, a crisp slam. */
	public static final Curve SMALL = new Curve(0.19, 0.0, 1, 3, 2.0, 0.16, 0.025, 0, 9.0);
	/** A medium double door (28 ticks), heavier: a push and a longer glide, the second leaf a little later. */
	public static final Curve MEDIUM = new Curve(0.16, 0.10, 1, 2, 1.8, 0.14, 0.018, 1, 7.0);
	/**
	 * A great gate (80 ticks), massive: it gets going slowly, then glides a long way (its inertia), creaks, and slams
	 * deep with almost no bounce.
	 */
	public static final Curve LARGE = new Curve(0.11, 0.12, 2, 3, 1.6, 0.10, 0.012, 4, 5.0);

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

	/** A smooth curve (smoothstep): slow start, slow end (the small ramps of the handles, the bolts, the blends). */
	public static double ease(double p) {
		p = clamp01(p);
		return p * p * (3 - 2 * p);
	}

	// ------------------------------------------------------------------ the pose

	/** Where the leaves are in their stroke (0..1) at a progress: 0 during the unlocking (the locking, closing). */
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

	/**
	 * The opening of a pushed leaf (0..1) at its stroke {@code x}: the integral of a speed {@code x^a (1-x)^b}, scaled to
	 * end at 1 (the regularised incomplete beta function: a polynomial for whole exponents). It only rises, from rest to
	 * rest.
	 */
	public static double push(int a, int b, double x) {
		x = clamp01(x);
		int n = a + b + 1;
		double sum = 0, binom = 1; // C(n, j) built up from C(n, 0)
		for (int j = 0; j <= n; j++) {
			if (j > a) {
				sum += binom * Math.pow(x, j) * Math.pow(1 - x, n - j);
			}
			binom = binom * (n - j) / (j + 1);
		}
		return clamp01(sum);
	}

	/** The speed of {@link #push} (its derivative over the stroke), for the tests and the tools. */
	public static double pushSpeed(int a, int b, double x) {
		x = clamp01(x);
		// 1 / B(a + 1, b + 1) = (a + b + 1)! / (a! b!)
		double norm = 1;
		for (int i = 1; i <= a + b + 1; i++) {
			norm *= i;
		}
		for (int i = 2; i <= a; i++) {
			norm /= i;
		}
		for (int i = 2; i <= b; i++) {
			norm /= i;
		}
		return norm * Math.pow(x, a) * Math.pow(1 - x, b);
	}

	/**
	 * The bounces of a closing leaf after the slam ({@code z} 0..1 over the bounce time): one small arc of height
	 * {@code rebound}, a second one {@link #RESTITUTION}² as high, then rest; never into the frame.
	 */
	public static double bounceCurve(double rebound, double z) {
		z = clamp01(z);
		double z1 = 1 / (1 + RESTITUTION); // arcs last as long as their speed: the second one is shorter
		if (z < z1) {
			double q = z / z1;
			return rebound * 4 * q * (1 - q);
		}
		double q = (z - z1) / (1 - z1);
		return rebound * RESTITUTION * RESTITUTION * 4 * q * (1 - q);
	}

	/**
	 * How open a leaf is (0 closed, 1 open: 90°; a very little open while it bounces at the end of a closing) at its
	 * stroke {@code u}, opening or closing. Opening: the push and the glide to a cushioned stop ({@link #push}).
	 * Closing (the time runs from {@code u} = 1 to 0): a soft start, a speed that grows up to the frame
	 * ({@link Curve#impactSpeed}), the slam, the bounces ({@link #bounceCurve}), rest.
	 */
	public static double leafCurve(Curve c, boolean opening, double u) {
		u = clamp01(u);
		if (opening) {
			return push(c.pushRise, c.pushFall, u);
		}
		double x = 1 - u, b = c.bounce;
		if (x < 1 - b) {
			double y = x / (1 - b), v = c.impactSpeed;
			// P(0) = 0, P'(0) = 0 (soft start), P(1) = 1, P'(1) = v (the slam), P'' >= 0 (it keeps gaining speed)
			return 1 - ((3 - v) * y * y + (v - 2) * y * y * y);
		}
		return b <= 0 ? 0 : bounceCurve(c.rebound, (x - (1 - b)) / b);
	}

	/** How open a leaf is at a progress, opening ({@code target}) or closing (no turning back taken into account). */
	public static double leaf(Curve c, int leaves, int leaf, boolean target, double t) {
		return leafCurve(c, target, leafShare(c, leaves, leaf, leafPhase(c, t)));
	}

	/**
	 * How open a leaf is at time {@code now} of a movement (fractional between two ticks on a client): {@link #leaf} at
	 * its {@link #progress}. A movement that turned back half way started where the other one left its leaves
	 * ({@link #turnBack}); what little differs (the other leaf, the handles) is faded by the clients ({@link DoorTrack}).
	 */
	public static double leafAt(Curve c, int leaves, int leaf, boolean target, long startTick, double startProgress, double now, int duration) {
		return leaf(c, leaves, leaf, target, progress(target, startTick, startProgress, now, duration));
	}

	/** How open the leaves are on average (both leaves of a double door) at a progress, opening or closing. */
	public static double meanLeaf(Curve c, int leaves, boolean target, double t) {
		double v = leaf(c, leaves, 0, target, t);
		return leaves < 2 ? v : (v + leaf(c, leaves, 1, target, t)) / 2;
	}

	/**
	 * The progress a movement towards {@code target} starts from when the door turns back at the progress {@code p} of
	 * the other movement: the point of its own curve where the leaves are as open as they are (on average), so that the
	 * leaves go on from where they are, at the pace of the new curve (a closing door opened again does not jump open,
	 * an opening door closed again does not crash shut). While the door unlocks or locks (its leaves at rest), and at
	 * rest, the progress is kept.
	 */
	public static double turnBack(Curve c, int leaves, boolean target, double p) {
		p = clamp01(p);
		if (p <= c.unlock || p >= 1) {
			return p;
		}
		double l = meanLeaf(c, leaves, !target, p);
		// the new curve only rises with the progress over [lo, 1]: opening from the start of the leaves' stroke, closing
		// from the slam of the last leaf (below it, the bounces)
		double lo = target ? c.unlock : impactProgress(c, leaves), hi = 1;
		if (l <= meanLeaf(c, leaves, target, lo)) {
			return lo;
		}
		for (int i = 0; i < 48; i++) {
			double mid = (lo + hi) / 2;
			if (meanLeaf(c, leaves, target, mid) < l) {
				lo = mid;
			} else {
				hi = mid;
			}
		}
		return (lo + hi) / 2;
	}

	/** The progress of a closing at which its last leaf (the first one) slams into the frame. */
	public static double impactProgress(Curve c, int leaves) {
		double s = leaves < 2 || c.delay <= 0 ? c.bounce : c.bounce * (1 - c.delay);
		return c.unlock + s * (1 - c.unlock);
	}

	/** The least open leaf at a progress of an opening (the second one of a double door). */
	public static double leastOpen(Curve c, int leaves, double t) {
		double v = leaf(c, leaves, 0, true, t);
		return leaves < 2 ? v : Math.min(v, leaf(c, leaves, 1, true, t));
	}

	/** Where the unlocking (opening) or the locking (closing) is, 0..1 of its own time, at a progress (1: over). */
	static double lockPhase(Curve c, boolean target, double t) {
		if (c.unlock <= 0) {
			return 1;
		}
		double w = clamp01(t) / c.unlock;
		return target ? Math.min(1, w) : clamp01(1 - w);
	}

	/**
	 * How far the door is unlocked (0..1: the bolts out, the latch free) at a progress: opening, the bolts slide out
	 * during the unlocking once the handle has started to turn; closing, they slide back in during the locking, once
	 * the leaves rest.
	 */
	public static double unlock(Curve c, boolean target, double t) {
		if (c.unlock <= 0) {
			return t > 0 ? 1 : 0;
		}
		double w = clamp01(t) / c.unlock; // 0 closed .. 1 the leaves' stroke begins
		return target ? ease((w - BOLTS_FROM) / (BOLTS_OUT - BOLTS_FROM)) : ease((w - (1 - LOCK_BOLTS_IN)) / (LOCK_BOLTS_IN - LOCK_BOLTS_FROM));
	}

	/**
	 * How far the handles and rings are turned (0..1) at a progress: opening, they turn while the door unlocks and come
	 * back while the leaves start; closing, they stay while the leaves move and turn (then come back) while the door
	 * locks.
	 */
	public static double handle(Curve c, boolean target, double t) {
		t = clamp01(t);
		if (target) {
			if (t <= c.unlock) {
				return c.unlock <= 0 ? 1 : ease(t / (HANDLE_UP * c.unlock));
			}
			return 1 - ease(leafPhase(c, t) / HANDLE_BACK);
		}
		if (t >= c.unlock || c.unlock <= 0) {
			return 0;
		}
		double w = lockPhase(c, false, t);
		return w < LOCK_RELEASE ? ease(w / LOCK_TURNED) : 1 - ease((w - LOCK_RELEASE) / (1 - LOCK_RELEASE));
	}

	/**
	 * The rattle of the rings (degrees about +z, both ways, damped to rest) at a progress of a closing: it starts when
	 * the last leaf slams into the frame and dies out while that leaf bounces and settles.
	 */
	public static double jiggle(Curve c, int leaves, boolean target, double t) {
		if (target || c.jiggle <= 0 || c.bounce <= 0) {
			return 0;
		}
		double u = leafShare(c, leaves, 0, leafPhase(c, t));
		if (u >= c.bounce) {
			return 0;
		}
		double z = 1 - u / c.bounce; // 0 at the slam, 1 at rest
		return c.jiggle * Math.sin(3 * Math.PI * z) * (1 - z) * (1 - z);
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
	 * Where along the stroke of the first leaf (0..1, in the time of the movement: from closed opening, from open
	 * closing) the {@code k}-th creak of a door is: spread over the stroke, and closing, over its approach only (never on
	 * the slam).
	 */
	public static double creakAt(Curve c, boolean opening, int k) {
		double end = opening ? 0.8 : 0.7 - c.bounce;
		return c.creaks <= 1 ? (0.1 + end) / 2 : 0.1 + (end - 0.1) * k / (c.creaks - 1);
	}

	/**
	 * What happens between the progress {@code prevT} of the previous tick and {@code t} (a bit set of {@code EV_*}).
	 * Opening: the latch is free ({@link #EV_UNLATCH}: the bolts are out), the first leaf starts
	 * ({@link #EV_LEAVES_START}), it is fully open ({@link #EV_OPENED}). Closing: a leaf hits the frame (the last one
	 * {@link #EV_IMPACT}, the first {@link #EV_SECOND_IMPACT}), the last one is at rest after its bounces
	 * ({@link #EV_LATCHED}: the latch), the bolts are back in ({@link #EV_LOCKED}). Both ways: a creak
	 * ({@link #EV_CREAK}, {@link Curve#creaks} along the stroke of the first leaf).
	 */
	public static int events(Curve c, int leaves, boolean target, double prevT, double t) {
		int e = 0;
		double sp = leafPhase(c, prevT), s = leafPhase(c, t);
		double u0p = leafShare(c, leaves, 0, sp), u0 = leafShare(c, leaves, 0, s);
		if (target) {
			if (c.unlock > 0 && prevT < BOLTS_OUT * c.unlock && t >= BOLTS_OUT * c.unlock) {
				e |= EV_UNLATCH;
			}
			if (sp <= 0 && s > 0) {
				e |= EV_LEAVES_START;
			}
			if (prevT < 1 && t >= 1) {
				e |= EV_OPENED;
			}
		} else {
			if (u0p > c.bounce && u0 <= c.bounce) {
				e |= EV_IMPACT;
			}
			if (leaves >= 2 && leafShare(c, leaves, 1, sp) > c.bounce && leafShare(c, leaves, 1, s) <= c.bounce) {
				e |= EV_SECOND_IMPACT;
			}
			if (sp > 0 && s <= 0) {
				e |= EV_LATCHED;
			}
			double lock = (1 - LOCK_BOLTS_IN) * c.unlock;
			if (prevT > lock && t <= lock) {
				e |= EV_LOCKED;
			}
		}
		for (int k = 0; k < c.creaks; k++) {
			double at = creakAt(c, target, k);
			if (target ? u0p < at && u0 >= at : u0p > 1 - at && u0 <= 1 - at) {
				e |= EV_CREAK;
			}
		}
		return e;
	}

	// ------------------------------------------------------------------ the moving parts

	/** Angle (degrees) of the gears at an opening of their leaf: {@code turns} full turns over the leaf's stroke. */
	public static double gearAngle(double opening, int turns) {
		return 360.0 * turns * opening;
	}

	/** How far (blocks) the bolts have slid at a progress: all their travel during the unlocking. */
	public static double boltOffset(Curve c, boolean target, double t) {
		return BOLT_TRAVEL * unlock(c, target, t);
	}

	/** How far (blocks) the piston rods have slid at an opening of their leaf. */
	public static double pistonOffset(double opening) {
		return PISTON_TRAVEL * clamp01(opening);
	}

	/**
	 * Angle (degrees, about +z: negative = clockwise seen from the front) of the handles and rings of a door at a
	 * progress: clockwise while the door unlocks, back while the leaves start, the rattle at the slam, the turn of the
	 * locking; a steam door's wheel turns further (and does not rattle).
	 */
	public static double handleAngle(DoorType type, boolean target, double t) {
		DoorMotion.Curve c = curve(type);
		double turn = -(type.steam() ? WHEEL_ANGLE : HANDLE_ANGLE) * handle(c, target, t);
		return type.steam() ? turn : turn - jiggle(c, type.leaves(), target, t);
	}

	static double clamp01(double v) {
		return v < 0 ? 0 : v > 1 ? 1 : v;
	}
}
