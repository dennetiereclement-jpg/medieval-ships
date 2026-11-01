package fr.medievalships.core;

/**
 * The small persisted state of a placed cannon (the medieval cannon {@code canon_medieval}, {@link TentTypes#CANNON}):
 * is a ball loaded, how many powder charges are rammed in, how many ticks are left on a lit fuse, and the game time of
 * the last shot. Immutable, pure Java (no Minecraft class) so the rules are unit-tested; the block entity
 * ({@code fr.medievalships.tent.CannonBlockEntity}) holds one and saves it with the block entity data API under the
 * keys {@link #KEY_LOADED}... .
 *
 * <p>Nothing changes it yet: the firing system is future work (see docs/TENTES.md, section "Canon médiéval :
 * architecture du tir"). {@link #EMPTY} is the state of every cannon placed today and is written as nothing at all
 * (no key: the chunk data of an unused cannon stays empty).
 *
 * @param loaded       a cannonball is in the barrel
 * @param powder       powder charges rammed in, 0..{@link #MAX_POWDER}
 * @param fuseTicks    ticks left before the shot when the fuse is lit, 0 = not lit (0..{@link #MAX_FUSE_TICKS})
 * @param lastShotTime world game time of the last shot, {@link #NEVER} if it never fired
 */
public record CannonState(boolean loaded, int powder, int fuseTicks, long lastShotTime) {
	/** NBT keys of the block entity data. */
	public static final String KEY_LOADED = "Loaded", KEY_POWDER = "Powder", KEY_FUSE = "FuseTicks", KEY_LAST_SHOT = "LastShot";
	/** The most powder charges a barrel takes. */
	public static final int MAX_POWDER = 3;
	/** The longest fuse (10 s). */
	public static final int MAX_FUSE_TICKS = 200;
	/** {@link #lastShotTime} of a cannon that never fired. */
	public static final long NEVER = -1L;
	/** Unloaded, no powder, fuse not lit, never fired: every new cannon. */
	public static final CannonState EMPTY = new CannonState(false, 0, 0, NEVER);

	public CannonState {
		powder = Math.max(0, Math.min(MAX_POWDER, powder));
		fuseTicks = Math.max(0, Math.min(MAX_FUSE_TICKS, fuseTicks));
		lastShotTime = lastShotTime < 0 ? NEVER : lastShotTime;
	}

	/** Nothing loaded, nothing lit, never fired (written as no key at all). */
	public boolean isEmpty() {
		return equals(EMPTY);
	}

	/** Is the fuse burning? */
	public boolean lit() {
		return fuseTicks > 0;
	}

	/** Could it fire: a ball and at least one charge of powder. */
	public boolean ready() {
		return loaded && powder > 0;
	}

	public CannonState withLoaded(boolean loaded) {
		return new CannonState(loaded, powder, fuseTicks, lastShotTime);
	}

	public CannonState withPowder(int powder) {
		return new CannonState(loaded, powder, fuseTicks, lastShotTime);
	}

	public CannonState withFuseTicks(int fuseTicks) {
		return new CannonState(loaded, powder, fuseTicks, lastShotTime);
	}

	public CannonState withLastShotTime(long lastShotTime) {
		return new CannonState(loaded, powder, fuseTicks, lastShotTime);
	}

	/** The state right after a shot at {@code gameTime}: barrel emptied, fuse out, the time remembered. */
	public CannonState fired(long gameTime) {
		return new CannonState(false, 0, 0, gameTime);
	}
}
