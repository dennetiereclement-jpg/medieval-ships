package fr.medievalships.core;

/**
 * The crafting state of one divine forge (1.34.0): at rest, or crafting from a start tick to an end tick (game time,
 * {@code World#getTime}: it goes on across a restart and stands still while the server is stopped). A crafting is a
 * player's recipe (its id, the player's UUID and name) or a bare animation started by an administrator or another mod
 * ({@code /forge animer}, {@code DivineForgeApi}: no recipe, no player). One at a time per forge: {@link #start}
 * refuses while busy. Once the end tick is reached the crafting is {@link #due}; the server then hands the result over
 * and calls {@link #complete}, which brings the forge back to rest. The block entity keeps the item stacks (the result,
 * the pending results of absent players) and persists these fields; this class is the pure machine (JUnit).
 */
public final class ForgeCraft {
	/** Longest crafting accepted (ticks): one hour, like the recipes' maximum; longer requests are cut to it. */
	public static final int MAX_TICKS = ForgeRecipeSpec.MAX_DURATION;

	public enum Phase {
		IDLE, CRAFTING
	}

	/** What a finished crafting was: the start and end ticks, the recipe (null: an animation) and the player (null: nobody). */
	public record Finished(long start, long end, String recipe, String player, String playerName, String label) {
		public boolean animationOnly() {
			return recipe == null;
		}
	}

	private Phase phase = Phase.IDLE;
	private long start, end;
	private String recipe, player, playerName, label;

	public Phase phase() {
		return phase;
	}

	public boolean crafting() {
		return phase == Phase.CRAFTING;
	}

	/** Busy (a new crafting refused): crafting, even past its end until the server completes it. */
	public boolean busy() {
		return phase == Phase.CRAFTING;
	}

	/** Has the crafting reached its end (the server must complete it)? */
	public boolean due(long now) {
		return phase == Phase.CRAFTING && now >= end;
	}

	public long start() {
		return start;
	}

	public long end() {
		return end;
	}

	/** The recipe id being crafted, or null (at rest, or an animation). */
	public String recipe() {
		return recipe;
	}

	/** The UUID (text) of the player it is crafted for, or null. */
	public String player() {
		return player;
	}

	public String playerName() {
		return playerName;
	}

	/** What the forge shows it is making (the recipe's name, or "Animation"), or null at rest. */
	public String label() {
		return label;
	}

	public boolean animationOnly() {
		return phase == Phase.CRAFTING && recipe == null;
	}

	/** Ticks left (0 at rest or once due). */
	public long remaining(long now) {
		return phase == Phase.CRAFTING ? Math.max(0, end - now) : 0;
	}

	/** Ticks the whole crafting lasts (0 at rest). */
	public long total() {
		return phase == Phase.CRAFTING ? Math.max(1, end - start) : 0;
	}

	/** How far it is, 0 to 1 (0 at rest; clamped when the clock is before the start or after the end). */
	public double progress(long now) {
		if (phase != Phase.CRAFTING) {
			return 0;
		}
		return Math.max(0, Math.min(1, (now - start) / (double) Math.max(1, end - start)));
	}

	/**
	 * Starts a crafting of {@code ticks} (1 to {@link #MAX_TICKS}, clamped) at {@code now}: a recipe for a player, or an
	 * animation when {@code recipe} is null. False (nothing changes) while the forge is busy.
	 */
	public boolean start(long now, int ticks, String recipe, String player, String playerName, String label) {
		if (busy()) {
			return false;
		}
		int t = Math.max(1, Math.min(MAX_TICKS, ticks));
		phase = Phase.CRAFTING;
		start = now;
		end = now + t;
		this.recipe = recipe;
		this.player = recipe == null ? null : player;
		this.playerName = recipe == null ? null : playerName;
		this.label = label;
		return true;
	}

	/** Moves the end of the crafting (an administrator stopping it now: {@code end = now}); nothing at rest. */
	public void endAt(long tick) {
		if (phase == Phase.CRAFTING) {
			end = Math.max(start, tick);
		}
	}

	/** Ends the crafting (due or not) and goes back to rest: what it was, or null when the forge was at rest. */
	public Finished complete() {
		if (phase != Phase.CRAFTING) {
			return null;
		}
		Finished f = new Finished(start, end, recipe, player, playerName, label);
		reset();
		return f;
	}

	/** Back to rest without a result (an animation stopped). */
	public void reset() {
		phase = Phase.IDLE;
		start = end = 0;
		recipe = player = playerName = label = null;
	}

	/**
	 * Restores a saved state (the block entity's data): a crafting whose end is not after its start, or a phase other
	 * than crafting, gives the rest.
	 */
	public void restore(boolean crafting, long start, long end, String recipe, String player, String playerName, String label) {
		reset();
		if (crafting && end > start) {
			this.phase = Phase.CRAFTING;
			this.start = start;
			this.end = end;
			this.recipe = blank(recipe);
			this.player = this.recipe == null ? null : blank(player);
			this.playerName = this.recipe == null ? null : blank(playerName);
			this.label = blank(label);
		}
	}

	private static String blank(String s) {
		return s == null || s.isEmpty() ? null : s;
	}
}
