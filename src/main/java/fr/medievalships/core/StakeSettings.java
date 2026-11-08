package fr.medievalships.core;

/**
 * The defensive stakes' server settings (1.24.0, {@code "server": {"stake": {...}}} of {@code config/medievalships.json}):
 * how hard a stake's point hits the hostile mobs that touch it. These values apply to every stake of the server: they
 * override the hazard values of the model's JSON ({@link TentType.Hazard}, the same defaults), so an administrator tunes
 * the stakes without touching the mod. Players are spared unless {@link #damagePlayers} (never in creative or
 * spectator mode); passive mobs, villagers and NPCs are never hurt.
 */
public final class StakeSettings {
	public static final double DEFAULT_DAMAGE = 4.0, DEFAULT_KNOCKBACK = 0.4;
	public static final int DEFAULT_COOLDOWN_TICKS = 20;
	/** The clamps of {@link #sanitize}. */
	public static final double MAX_DAMAGE = 100.0, MAX_KNOCKBACK = 4.0;
	public static final int MIN_COOLDOWN_TICKS = 1, MAX_COOLDOWN_TICKS = 1200;

	/** Damage of one hit (half hearts: 4.0 = two hearts), 0-100. */
	public double damage = DEFAULT_DAMAGE;
	/** Strength of the push outward along the point (vanilla knockback strength: a sword hit is 0.4), 0-4. */
	public double knockback = DEFAULT_KNOCKBACK;
	/** Ticks before the same entity can be hit again by the same stake (20 = one second), 1-1200. */
	public int cooldownTicks = DEFAULT_COOLDOWN_TICKS;
	/** Do the stakes hurt survival / adventure players too? (never creative or spectator players) */
	public boolean damagePlayers = false;

	/** Clamps the values to sane ranges (NaN gives the default). */
	public StakeSettings sanitize() {
		damage = Double.isNaN(damage) ? DEFAULT_DAMAGE : Math.max(0.0, Math.min(MAX_DAMAGE, damage));
		knockback = Double.isNaN(knockback) ? DEFAULT_KNOCKBACK : Math.max(0.0, Math.min(MAX_KNOCKBACK, knockback));
		cooldownTicks = Math.max(MIN_COOLDOWN_TICKS, Math.min(MAX_COOLDOWN_TICKS, cooldownTicks));
		return this;
	}
}
