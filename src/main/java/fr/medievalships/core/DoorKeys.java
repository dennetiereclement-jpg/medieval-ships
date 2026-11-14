package fr.medievalships.core;

import java.util.Collection;
import java.util.Locale;
import java.util.random.RandomGenerator;

/**
 * The keys of the doors (1.32.0, pure Java, tested in JUnit). A door may have a lock: a random identifier saved in its
 * block entity. A key ({@code medievalships:cle}) is blank until an administrator binds it to a lock; a bound key
 * carries the lock and the label of its door (its name, or its coordinates) and keeps them when it is renamed at an
 * anvil. A door in the {@link DoorAccess#CLE} access opens on a click only for a player carrying a key of its lock
 * anywhere in his inventory; the administrators' master key ({@code medievalships:cle_universelle}) opens every door,
 * whatever its access, but only for an administrator.
 *
 * <p>The gestures with a key in hand ({@link #gesture}), administrators only: a right click on a door with a blank key
 * binds the key to the door's lock (created when the door has none) and puts the door in the key access (another blank
 * key: a copy); sneaking with a bound key, the door takes the key's lock (one key for the front and back doors of a
 * house); sneaking with the master key, the door switches between free and key access. Nobody else binds a key.
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
		/** A blank key in an administrator's hand: bound to the door's lock, the door in key access. */
		BIND,
		/** An administrator sneaking with a bound key: the door takes the key's lock. */
		SHARE,
		/** ... a key the door's lock already opens. */
		ALREADY,
		/** An administrator sneaking with the master key: free / key access. */
		TOGGLE,
		/** A blank key in the hand of a player who is not an administrator. */
		NOT_ADMIN,
		/** A player who is not an administrator sneaking with the master key. */
		MASTER_REFUSED
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

	/** Does a key of this lock open a door of that lock? (A blank key, or a door without lock: never.) */
	public static boolean opens(String keyLock, String doorLock) {
		return keyLock != null && !keyLock.isEmpty() && keyLock.equals(doorLock);
	}

	/** Does one of the carried keys open the door? */
	public static boolean carries(Collection<String> carriedLocks, String doorLock) {
		if (carriedLocks == null || doorLock == null || doorLock.isEmpty()) {
			return false;
		}
		for (String k : carriedLocks) {
			if (opens(k, doorLock)) {
				return true;
			}
		}
		return false;
	}

	/**
	 * What a click does on a door: its access with the keys carried ({@code carriedLocks}); refused, the master key
	 * carried by an administrator opens it anyway, carried by somebody else it says it does not obey him.
	 */
	public static DoorAccess.Click click(DoorAccess access, boolean manualEnabled, Collection<String> tags, String questTag, String doorLock,
			Collection<String> carriedLocks, boolean carriesMaster, boolean admin) {
		DoorAccess.Click base = access.click(manualEnabled, tags, questTag, carries(carriedLocks, doorLock));
		if (base == DoorAccess.Click.OK) {
			return base;
		}
		if (carriesMaster) {
			return admin ? DoorAccess.Click.OK : DoorAccess.Click.MASTER_REFUSED;
		}
		return base;
	}

	/** What a click with {@code held} in hand does ({@code keyLock}: the lock of a bound key; {@code doorLock}: the door's, or ""). */
	public static Gesture gesture(Held held, boolean sneaking, boolean admin, String keyLock, String doorLock) {
		return switch (held) {
			case OTHER -> Gesture.CLICK;
			case BLANK -> admin ? Gesture.BIND : Gesture.NOT_ADMIN;
			case BOUND -> !sneaking || !admin ? Gesture.CLICK : opens(keyLock, doorLock) ? Gesture.ALREADY : Gesture.SHARE;
			case MASTER -> !sneaking ? Gesture.CLICK : admin ? Gesture.TOGGLE : Gesture.MASTER_REFUSED;
		};
	}

	/** The access a door takes when an administrator sneaks on it with the master key: key access, or free from key access. */
	public static DoorAccess toggled(DoorAccess access) {
		return access == DoorAccess.CLE ? DoorAccess.LIBRE : DoorAccess.CLE;
	}

	/** The label a key shows ("Ouvre : ..."): the door's name, or the coordinates of its controller. */
	public static String label(String name, int x, int y, int z) {
		return name != null && !name.isEmpty() ? name : String.format(Locale.ROOT, "%d %d %d", x, y, z);
	}
}
