package fr.medievalships.core;

import java.util.Collection;
import java.util.Locale;
import java.util.random.RandomGenerator;

/**
 * The keys of the doors (1.32.0; one key, one door since 1.33.0; pure Java, tested in JUnit). A door may have a lock:
 * a random identifier saved in its block entity. A key ({@code medievalships:cle}) is blank until an administrator
 * binds it to a door; a bound key carries the door's lock, the door itself (its dimension and the position of its
 * controller, {@link #doorId}) and its label (its name, or its coordinates), and keeps them when it is renamed at an
 * anvil. A door in the {@link DoorAccess#CLE} access opens on a click only for a player carrying a key of that very
 * door anywhere in his inventory: the lock and the door must both match ({@link #opens}), so that two doors that
 * happen to have the same lock (shared in 1.32.0, a copied block entity, a duplicated structure) never open with the
 * same key. The administrators' master key ({@code medievalships:cle_universelle}) opens every door, whatever its
 * access, but only for an administrator.
 *
 * <p>The keys bound in 1.32.0 carry no door: such a key opens the first door of its lock it is used on, and is bound to
 * that door from then on ({@link #opening}, the caller writes the door into the key). Nothing else changes for them.
 *
 * <p>The gestures with a key in hand ({@link #gesture}), administrators only: a right click on a door with a blank key
 * binds the key to that door (its lock created when it has none, or renewed when another door uses it,
 * {@link #needsNewLock}) and puts the door in the key access (another blank key: a copy of the key of that same door);
 * sneaking with the master key, the door switches between free and key access. A key already bound to a door is never
 * bound to another ({@link Gesture#OTHER_DOOR}, {@link #boundElsewhere}). Nobody else binds a key.
 */
public final class DoorKeys {
	/** Item ids of the key and of the master key. */
	public static final String KEY = "cle", MASTER = "cle_universelle";
	/** Length of a lock identifier (lower case hexadecimal: 48 random bits). */
	public static final int LOCK_CHARS = 12;

	/** What the player holds in the hand he clicks with. */
	public enum Held {
		OTHER, BLANK, BOUND, MASTER
	}

	/** What a click with that in hand does. */
	public enum Gesture {
		/** The ordinary click (the access decides, with the keys and the master key carried). */
		CLICK,
		/** A blank key in an administrator's hand: bound to this door, the door in key access. */
		BIND,
		/** An administrator sneaking with a key of this door. */
		ALREADY,
		/** An administrator sneaking with a key bound to another door: refused, a key opens one door only. */
		OTHER_DOOR,
		/** An administrator sneaking with the master key: free / key access. */
		TOGGLE,
		/** A blank key in the hand of a player who is not an administrator. */
		NOT_ADMIN,
		/** A player who is not an administrator sneaking with the master key. */
		MASTER_REFUSED
	}

	/**
	 * A key carried by a player: its lock and the door it was bound to ({@link #doorId}; "" for a key bound in 1.32.0,
	 * which opens the first door of its lock it is used on).
	 */
	public record Key(String lock, String door) {
		public Key {
			lock = lock == null ? "" : lock;
			door = door == null ? "" : door;
		}

		/** A key of 1.32.0, bound to a lock but not yet to a door. */
		public boolean legacy() {
			return !lock.isEmpty() && door.isEmpty();
		}
	}

	private DoorKeys() {
	}

	/** A new random lock. */
	public static String newLock(RandomGenerator random) {
		StringBuilder b = new StringBuilder(LOCK_CHARS);
		for (int i = 0; i < LOCK_CHARS; i++) {
			b.append(Character.forDigit(random.nextInt(16), 16));
		}
		return b.toString();
	}

	/** Is this a lock identifier ({@link #LOCK_CHARS} lower case hexadecimal digits)? */
	public static boolean validLock(String lock) {
		return lock != null && lock.length() == LOCK_CHARS && lock.chars().allMatch(c -> (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'));
	}

	/** The identity of a door, as its keys carry it: its dimension and the position of its controller. */
	public static String doorId(String dimension, int x, int y, int z) {
		return String.format(Locale.ROOT, "%s %d %d %d", dimension == null ? "" : dimension, x, y, z);
	}

	/**
	 * Does a key (its lock, and its door: "" for a key of 1.32.0) open a door (its lock and its identity)? The lock must
	 * be the door's, and the key bound to that very door (a key of 1.32.0: to any door of its lock, until it is used).
	 * A blank key, or a door without lock: never.
	 */
	public static boolean opens(String keyLock, String keyDoor, String doorLock, String doorId) {
		if (keyLock == null || keyLock.isEmpty() || doorLock == null || doorLock.isEmpty() || !keyLock.equals(doorLock)) {
			return false;
		}
		return keyDoor == null || keyDoor.isEmpty() || keyDoor.equals(doorId);
	}

	public static boolean opens(Key key, String doorLock, String doorId) {
		return key != null && opens(key.lock(), key.door(), doorLock, doorId);
	}

	/**
	 * The key among those carried that opens the door: a key bound to it first, otherwise a key of 1.32.0 of its lock
	 * (the caller then binds that key to this door); null when none does.
	 */
	public static Key opening(Collection<Key> carried, String doorLock, String doorId) {
		if (carried == null) {
			return null;
		}
		Key legacy = null;
		for (Key k : carried) {
			if (opens(k, doorLock, doorId)) {
				if (!k.legacy()) {
					return k;
				}
				if (legacy == null) {
					legacy = k;
				}
			}
		}
		return legacy;
	}

	/** Does one of the carried keys open the door? */
	public static boolean carries(Collection<Key> carried, String doorLock, String doorId) {
		return opening(carried, doorLock, doorId) != null;
	}

	/**
	 * What a click does on a door: its access with the keys carried ({@code carried}); refused, the master key carried
	 * by an administrator opens it anyway, carried by somebody else it says it does not obey him.
	 */
	public static DoorAccess.Click click(DoorAccess access, boolean manualEnabled, Collection<String> tags, String questTag, String doorLock,
			String doorId, Collection<Key> carried, boolean carriesMaster, boolean admin) {
		DoorAccess.Click base = access.click(manualEnabled, tags, questTag, carries(carried, doorLock, doorId));
		if (base == DoorAccess.Click.OK) {
			return base;
		}
		if (carriesMaster) {
			return admin ? DoorAccess.Click.OK : DoorAccess.Click.MASTER_REFUSED;
		}
		return base;
	}

	/**
	 * What a click with {@code held} in hand does ({@code keyLock}, {@code keyDoor}: the lock and the door of a bound key;
	 * {@code doorLock}, {@code doorId}: the door's lock, or "", and its identity).
	 */
	public static Gesture gesture(Held held, boolean sneaking, boolean admin, String keyLock, String keyDoor, String doorLock, String doorId) {
		return switch (held) {
			case OTHER -> Gesture.CLICK;
			case BLANK -> admin ? Gesture.BIND : Gesture.NOT_ADMIN;
			case BOUND -> !sneaking || !admin ? Gesture.CLICK : opens(keyLock, keyDoor, doorLock, doorId) ? Gesture.ALREADY : Gesture.OTHER_DOOR;
			case MASTER -> !sneaking ? Gesture.CLICK : admin ? Gesture.TOGGLE : Gesture.MASTER_REFUSED;
		};
	}

	/**
	 * Does a door need a new lock before a key is bound to it? When it has none; when its lock was made for another
	 * door ({@code lockHome}: the door the lock was made for, "" for a lock of 1.32.0) — the door is a copy (a copied
	 * block entity, a duplicated structure); when its lock of 1.32.0 is also another door's ({@code usedElsewhere}: the
	 * locks shared in 1.32.0). Each door has its own lock.
	 */
	public static boolean needsNewLock(String lock, String lockHome, String doorId, boolean usedElsewhere) {
		if (lock == null || lock.isEmpty()) {
			return true;
		}
		if (lockHome != null && !lockHome.isEmpty()) {
			return !lockHome.equals(doorId);
		}
		return usedElsewhere;
	}

	/** The access a door takes when an administrator sneaks on it with the master key: key access, or free from key access. */
	public static DoorAccess toggled(DoorAccess access) {
		return access == DoorAccess.CLE ? DoorAccess.LIBRE : DoorAccess.CLE;
	}

	/** The label a key shows ("Ouvre uniquement : ..."): the door's name, or the coordinates of its controller. */
	public static String label(String name, int x, int y, int z) {
		return name != null && !name.isEmpty() ? name : String.format(Locale.ROOT, "%d %d %d", x, y, z);
	}

	/** A key's label as a message names its door: « name », or "la porte en x y z". */
	public static String describe(String label) {
		if (label == null || label.isEmpty()) {
			return "une autre porte";
		}
		return label.matches("-?\\d+ -?\\d+ -?\\d+") ? "la porte en " + label : "« " + label + " »";
	}

	/** What an administrator reads when he tries to bind a key of another door: one key, one door. */
	public static String boundElsewhere(String keyLabel) {
		return "Cette clé est déjà liée à " + describe(keyLabel) + ". Une clé n'ouvre qu'une seule porte.";
	}
}
