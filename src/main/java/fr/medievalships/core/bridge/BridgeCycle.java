package fr.medievalships.core.bridge;

/**
 * The automatic cycle of a drawbridge: FERMÉ, ATTENTE_SÉCURITÉ, OUVERTURE, OUVERT, FERMETURE, ERREUR. Pure state
 * machine, ticked by the game with what it observed ({@link Input}); it answers with the leaves' angle and events
 * ({@link Listener}) the game turns into block changes, sounds and messages. The same code runs in the unit tests.
 *
 * <ul>
 * <li>FERMÉ: the deck is made of its real blocks. A vessel needing the opening (or a manual order) starts the
 * safety wait.</li>
 * <li>ATTENTE_SÉCURITÉ: the opening is announced; after the warning time, the leaves rise only once nobody stands
 * on the deck and nothing is in the volume they sweep. The wait goes on, with a diagnostic, while something is in the
 * way; it is cancelled if nothing needs the opening any more.</li>
 * <li>OUVERTURE / FERMETURE: the angle eases from where it is to the target over a time proportional to the way to
 * go (slow start, slow arrival: a heavy deck on its winch, {@link #ease}). A closing is reversed (the leaves rise
 * again from their current angle) when a vessel needs the opening again or something enters the volume under the
 * leaves.</li>
 * <li>OUVERT: stays open while a vessel needs it or occupies the passage; once free, waits the closing delay (reset
 * by any new need), then closes if the swept volume is clear.</li>
 * <li>ERREUR: the leaves are down but the deck's blocks cannot be put back (a block occupies their place): the leaves
 * stay as walkable collision boxes, the placement is retried periodically, and a new need reopens normally.</li>
 * </ul>
 * With the automatism suspended, nothing happens by itself; the manual orders still go through the same safety
 * checks.
 */
public final class BridgeCycle {
	public enum State {
		FERME, ATTENTE_SECURITE, OUVERTURE, OUVERT, FERMETURE, ERREUR;

		/** Are the leaves represented by moving collision boxes (the deck's blocks removed from the world)? */
		public boolean leavesOut() {
			return this != FERME && this != ATTENTE_SECURITE;
		}

		public boolean moving() {
			return this == OUVERTURE || this == FERMETURE;
		}

		public static State of(int ordinal) {
			State[] v = values();
			return ordinal >= 0 && ordinal < v.length ? v[ordinal] : FERME;
		}

		public String french() {
			return switch (this) {
				case FERME -> "fermé";
				case ATTENTE_SECURITE -> "attente de sécurité";
				case OUVERTURE -> "ouverture";
				case OUVERT -> "ouvert";
				case FERMETURE -> "fermeture";
				case ERREUR -> "erreur";
			};
		}
	}

	/**
	 * What the game observed this tick.
	 *
	 * @param demand          a vessel needing the opening is in the approach, the keep zone or the passage, or a
	 *                        scripted request is active
	 * @param passageOccupied a vessel needing the opening is in the passage itself (never close on it)
	 * @param deckClear       nobody (player, creature, vehicle) stands on the deck or straddles its ends
	 * @param sweptClear      nothing is in the volume the leaves would sweep for the intended movement
	 * @param footprintFree   the places of the deck's blocks are free (air or replaceable), so they can be put back
	 * @param loaded          the chunks of the deck are loaded (nothing is decided while they are not)
	 */
	public record Input(boolean demand, boolean passageOccupied, boolean deckClear, boolean sweptClear, boolean footprintFree, boolean loaded) {
		public static final Input QUIET = new Input(false, false, true, true, true, true);

		public Input withDemand(boolean d) {
			return new Input(d, passageOccupied, deckClear, sweptClear, footprintFree, loaded);
		}
	}

	/** Events of the cycle, in the order they happen. */
	public interface Listener {
		/** Entering the safety wait: announce the coming movement. */
		default void safetyWait() {
		}

		/** The leaves start rising; {@code removeBlocks} when the deck's blocks must now leave the world. */
		default void opening(boolean removeBlocks) {
		}

		default void opened() {
		}

		default void closing() {
		}

		/** The leaves are down and the deck's blocks must be put back. */
		default void closed() {
		}

		/** A closing was interrupted: the leaves rise again. */
		default void reversed() {
		}

		/** Periodic diagnostic while a safety condition holds the cycle. */
		default void blocked(String why) {
		}

		/** Entering ERREUR. */
		default void error(String why) {
		}

		/** Leaving ERREUR. */
		default void recovered() {
		}
	}

	/** How often (ticks) the same diagnostic is repeated while the cycle waits. */
	public static final int DIAGNOSTIC_INTERVAL = 100;
	/** How often (ticks) the placement of the blocks is retried in ERREUR. */
	public static final int ERROR_RETRY = 60;

	private State state = State.FERME;
	private double angle;
	/** The current move: from this angle to that one, over this many ticks, this many done (see {@link #ease}). */
	private double moveFrom;
	private double moveTo = Double.NaN;
	private int moveTicks;
	private int moveDone;
	private int ticksInState;
	private int closeCountdown;
	private boolean suspended;
	private boolean manualOpen;
	private boolean manualClose;
	private boolean blocksInWorld = true;
	private String diagnostic = "";
	private int diagnosticCooldown;

	public State state() {
		return state;
	}

	/** The leaves' angle now (degrees, 0 closed). */
	public double angle() {
		return angle;
	}

	/** The angle the current move started from (clients animate from it). */
	public double moveFrom() {
		return moveFrom;
	}

	/** The angle the current move goes to (NaN before a move is set up). */
	public double moveTo() {
		return moveTo;
	}

	/** Ticks the current move takes in all. */
	public int moveTicks() {
		return moveTicks;
	}

	/** Ticks of the current move already done (the clients animate from {@code now - moveDone}). */
	public int moveDone() {
		return moveDone;
	}

	/**
	 * The easing of a move: progress 0..1 in time to progress 0..1 in angle, slow at both ends (smoothstep). The
	 * server's collision boxes and every client's drawing use it, so they agree at every tick.
	 */
	public static double ease(double p) {
		p = Math.max(0, Math.min(1, p));
		return p * p * (3 - 2 * p);
	}

	/** The angle of a move after {@code done} of its {@code ticks} ticks. */
	public static double angleOf(double from, double to, int ticks, double done) {
		if (ticks <= 0 || Double.isNaN(to)) {
			return from;
		}
		return from + (to - from) * ease(done / ticks);
	}

	/** Sets up a move from the current angle to {@code to}: its time is proportional to the way to go. */
	private void startMove(double to, BridgeTuning t) {
		moveFrom = angle;
		moveTo = to;
		moveTicks = Math.max(1, (int) Math.round(t.durationTicks() * Math.abs(to - angle) / Math.max(1e-9, t.openAngle())));
		moveDone = 0;
	}

	public int ticksInState() {
		return ticksInState;
	}

	public boolean suspended() {
		return suspended;
	}

	/** Are the deck's blocks in the world (as opposed to carried by the leaves' boxes)? */
	public boolean blocksInWorld() {
		return blocksInWorld;
	}

	public String diagnostic() {
		return diagnostic;
	}

	public void setSuspended(boolean suspended) {
		this.suspended = suspended;
	}

	/** Restores a saved state (after a restart). The game checks the obstacles itself before ticking on. */
	public void restore(State state, double angle, boolean blocksInWorld, boolean suspended) {
		this.state = state;
		this.angle = angle;
		this.moveFrom = angle;
		this.moveTo = Double.NaN; // set up at the first tick, with the tuning
		this.moveTicks = 0;
		this.moveDone = 0;
		this.ticksInState = 0;
		this.blocksInWorld = blocksInWorld;
		this.suspended = suspended;
		this.closeCountdown = 0;
		this.diagnostic = "";
	}

	/** Manual order: open (through the safety wait and its checks). */
	public void requestOpen() {
		manualOpen = true;
		manualClose = false;
	}

	/** Manual order: close (ignores the vessels' needs, never the entities in the way). */
	public void requestClose() {
		manualClose = true;
		manualOpen = false;
	}

	public boolean manualOpenPending() {
		return manualOpen;
	}

	public boolean manualClosePending() {
		return manualClose;
	}

	private void enter(State next) {
		state = next;
		moveFrom = angle;
		moveTo = Double.NaN;
		moveTicks = 0;
		moveDone = 0;
		ticksInState = 0;
		diagnostic = "";
		diagnosticCooldown = 0;
	}

	private void note(String why, Listener l) {
		diagnostic = why;
		if (diagnosticCooldown <= 0) {
			l.blocked(why);
			diagnosticCooldown = DIAGNOSTIC_INTERVAL;
		}
	}

	/** One server tick. */
	public void tick(Input in, BridgeTuning t, Listener l) {
		ticksInState++;
		if (diagnosticCooldown > 0) {
			diagnosticCooldown--;
		}
		if (!in.loaded()) {
			diagnostic = "tronçons du pont non chargés : pont figé";
			return;
		}
		double target = t.openAngle();
		switch (state) {
			case FERME -> {
				if (manualOpen || (!suspended && in.demand())) {
					enter(State.ATTENTE_SECURITE);
					l.safetyWait();
				}
			}
			case ATTENTE_SECURITE -> {
				boolean wanted = manualOpen || (!suspended && in.demand());
				if (!wanted) {
					enter(blocksInWorld ? State.FERME : State.ERREUR);
					return;
				}
				if (ticksInState < t.warningTicks()) {
					return;
				}
				if (!in.deckClear()) {
					note("quelqu'un se trouve sur le tablier", l);
					return;
				}
				if (!in.sweptClear()) {
					note("un obstacle se trouve dans le volume balayé par les vantaux", l);
					return;
				}
				manualOpen = false;
				boolean remove = blocksInWorld;
				blocksInWorld = false;
				enter(State.OUVERTURE);
				startMove(target, t);
				l.opening(remove);
			}
			case OUVERTURE -> {
				if (moveTicks <= 0 || Double.isNaN(moveTo)) {
					startMove(target, t); // restored in the middle of a move
				}
				moveDone++;
				angle = angleOf(moveFrom, moveTo, moveTicks, moveDone);
				if (moveDone >= moveTicks) {
					angle = moveTo;
					enter(State.OUVERT);
					closeCountdown = t.closeDelayTicks();
					l.opened();
				}
			}
			case OUVERT -> {
				if (Math.abs(angle - target) > 1e-9 && !manualClose) {
					// the open angle was changed while open: go there
					enter(State.OUVERTURE);
					startMove(target, t);
					return;
				}
				boolean hold = !manualClose && (in.passageOccupied() || (!suspended && in.demand()) || manualOpen);
				if (manualOpen) {
					manualOpen = false; // an "open" order on an open bridge: nothing more to do
				}
				if (hold) {
					closeCountdown = t.closeDelayTicks();
					diagnostic = "";
					return;
				}
				if (suspended && !manualClose) {
					return; // automatism suspended: stays open until told otherwise
				}
				if (in.passageOccupied()) {
					note("un navire occupe le passage : fermeture refusée", l);
					return;
				}
				if (closeCountdown > 0) {
					closeCountdown--;
					return;
				}
				if (!in.sweptClear()) {
					note("un obstacle se trouve dans le volume de fermeture", l);
					return;
				}
				manualClose = false;
				enter(State.FERMETURE);
				startMove(0, t);
				l.closing();
			}
			case FERMETURE -> {
				if ((!suspended && in.demand()) || in.passageOccupied() || !in.sweptClear() || manualOpen) {
					enter(State.OUVERTURE);
					startMove(target, t);
					l.reversed();
					return;
				}
				if (moveTicks <= 0 || Double.isNaN(moveTo)) {
					startMove(0, t); // restored in the middle of a move
				}
				moveDone++;
				angle = angleOf(moveFrom, moveTo, moveTicks, moveDone);
				if (moveDone >= moveTicks) {
					angle = 0;
					if (in.footprintFree()) {
						blocksInWorld = true;
						enter(State.FERME);
						l.closed();
					} else {
						enter(State.ERREUR);
						l.error("l'emplacement du tablier est occupé par un bloc : les vantaux restent baissés sans leurs blocs");
					}
				}
			}
			case ERREUR -> {
				if (manualOpen || (!suspended && in.demand())) {
					enter(State.ATTENTE_SECURITE);
					l.recovered();
					l.safetyWait();
					return;
				}
				if (ticksInState % ERROR_RETRY == 0) {
					if (in.footprintFree()) {
						blocksInWorld = true;
						enter(State.FERME);
						l.recovered();
						l.closed();
					} else {
						note("l'emplacement du tablier est toujours occupé par un bloc", l);
					}
				}
			}
		}
	}
}
