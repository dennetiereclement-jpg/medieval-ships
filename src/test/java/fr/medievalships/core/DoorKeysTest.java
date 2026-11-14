package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.SplittableRandom;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.DoorAccess.Click;
import fr.medievalships.core.DoorKeys.Gesture;
import fr.medievalships.core.DoorKeys.Held;
import fr.medievalships.core.DoorKeys.Key;

/**
 * The keys of the doors (1.32.0; one key, one door since 1.33.0) in pure Java: the locks, a bound key opening its own
 * door only (its lock and the door itself), the keys of 1.32.0 bound to the first door they open, each door with its
 * own lock, the master key (the administrators' only), the gestures of the administrators with a key in hand, the
 * automatic closing of one minute and the migration of the doors saved by 1.31.0.
 */
class DoorKeysTest {
	private static final String LOCK = "0123456789ab", OTHER = "ba9876543210";
	private static final String DOOR = DoorKeys.doorId("minecraft:overworld", 120, 64, -40);
	private static final String BACK = DoorKeys.doorId("minecraft:overworld", 120, 64, -50);
	private static final String NETHER = DoorKeys.doorId("minecraft:the_nether", 120, 64, -40);
	private static final List<String> NONE = List.of();
	private static final List<Key> NO_KEY = List.of();

	@Test
	void locksAreRandomHexadecimalIdentifiers() {
		SplittableRandom random = new SplittableRandom(42);
		Set<String> seen = new HashSet<>();
		for (int i = 0; i < 2000; i++) {
			String l = DoorKeys.newLock(random);
			assertTrue(DoorKeys.validLock(l), l);
			assertEquals(DoorKeys.LOCK_CHARS, l.length());
			assertTrue(seen.add(l), "no two doors get the same lock: " + l);
		}
		assertFalse(DoorKeys.validLock(""));
		assertFalse(DoorKeys.validLock(null));
		assertFalse(DoorKeys.validLock("0123456789AB"), "lower case only");
		assertFalse(DoorKeys.validLock("0123456789a"));
		assertFalse(DoorKeys.validLock("0123456789xz"));
		assertEquals("minecraft:overworld 120 64 -40", DOOR);
	}

	@Test
	void aKeyOpensTheOneDoorItWasBoundTo() {
		assertTrue(DoorKeys.opens(LOCK, DOOR, LOCK, DOOR));
		assertFalse(DoorKeys.opens(OTHER, DOOR, LOCK, DOOR), "another lock");
		// the same lock on another door (shared in 1.32.0, a copied block entity, a duplicated structure): refused
		assertFalse(DoorKeys.opens(LOCK, DOOR, LOCK, BACK), "another door with the same lock");
		assertFalse(DoorKeys.opens(LOCK, DOOR, LOCK, NETHER), "the same position in another dimension");
		assertFalse(DoorKeys.opens("", "", LOCK, DOOR), "a blank key");
		assertFalse(DoorKeys.opens(null, null, LOCK, DOOR));
		assertFalse(DoorKeys.opens("", "", "", DOOR), "a blank key on a door without lock");
		assertFalse(DoorKeys.opens(LOCK, DOOR, "", DOOR), "a door without lock");
		assertTrue(DoorKeys.carries(List.of(new Key(OTHER, BACK), new Key(LOCK, DOOR)), LOCK, DOOR), "anywhere in the inventory");
		assertFalse(DoorKeys.carries(List.of(new Key(OTHER, DOOR)), LOCK, DOOR));
		assertFalse(DoorKeys.carries(List.of(new Key(LOCK, BACK)), LOCK, DOOR), "the key of the other door of the same lock");
		assertFalse(DoorKeys.carries(List.of(new Key("", "")), "", DOOR));
		assertFalse(DoorKeys.carries(null, LOCK, DOOR));
	}

	@Test
	void aKeyOf132IsBoundToTheFirstDoorItOpens() {
		Key legacy = new Key(LOCK, "");
		assertTrue(legacy.legacy());
		assertFalse(new Key(LOCK, DOOR).legacy());
		assertFalse(new Key("", "").legacy(), "a blank key is not a key of 1.32.0");
		// not bound to a door yet: it opens the doors of its lock (the caller binds it to the first one)
		assertTrue(DoorKeys.opens(legacy, LOCK, DOOR));
		assertTrue(DoorKeys.opens(legacy, LOCK, BACK));
		assertFalse(DoorKeys.opens(legacy, OTHER, DOOR));
		// a key bound to this very door is preferred to a key of 1.32.0 (which is then kept for its own door)
		Key own = new Key(LOCK, DOOR);
		assertSame(own, DoorKeys.opening(List.of(legacy, own), LOCK, DOOR));
		assertSame(legacy, DoorKeys.opening(List.of(new Key(LOCK, BACK), legacy), LOCK, DOOR));
		assertNull(DoorKeys.opening(List.of(new Key(LOCK, BACK)), LOCK, DOOR));
		assertNull(DoorKeys.opening(null, LOCK, DOOR));
		// once bound (the caller writes the door into it), it opens that door only
		Key bound = new Key(LOCK, BACK);
		assertTrue(DoorKeys.opens(bound, LOCK, BACK));
		assertFalse(DoorKeys.opens(bound, LOCK, DOOR));
	}

	@Test
	void eachDoorHasItsOwnLock() {
		// no lock yet: one is made
		assertTrue(DoorKeys.needsNewLock("", "", DOOR, false));
		assertTrue(DoorKeys.needsNewLock(null, null, DOOR, false));
		// a lock made for this door: kept, even when copies elsewhere carry it (they get their own at their first key)
		assertFalse(DoorKeys.needsNewLock(LOCK, DOOR, DOOR, false));
		assertFalse(DoorKeys.needsNewLock(LOCK, DOOR, DOOR, true));
		// a lock made for another door: this door is a copy (block entity, structure) and gets its own
		assertTrue(DoorKeys.needsNewLock(LOCK, BACK, DOOR, false));
		assertTrue(DoorKeys.needsNewLock(LOCK, NETHER, DOOR, false));
		// a lock of 1.32.0 (made for no door in particular): kept if this door alone has it, renewed when another door
		// shares it (the shared locks of 1.32.0)
		assertFalse(DoorKeys.needsNewLock(LOCK, "", DOOR, false));
		assertTrue(DoorKeys.needsNewLock(LOCK, "", DOOR, true));
	}

	@Test
	void theKeyAccess() {
		DoorAccess cle = DoorAccess.CLE;
		// the key of this door, anywhere: opens; none, the key of another door, or of another door of the same lock: refused
		assertEquals(Click.OK, DoorKeys.click(cle, true, NONE, "", LOCK, DOOR, List.of(new Key(LOCK, DOOR)), false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, DOOR, NO_KEY, false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, DOOR, List.of(new Key(OTHER, DOOR)), false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, BACK, List.of(new Key(LOCK, DOOR)), false, false),
				"one key, one door: the back door with the same lock stays shut");
		assertEquals(Click.OK, DoorKeys.click(cle, true, NONE, "", LOCK, BACK, List.of(new Key(LOCK, "")), false, false), "a key of 1.32.0");
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, DOOR, NO_KEY, false, true), "an admin without key nor master key");
		assertEquals("Vous n'avez pas la clé de cette porte.", Click.KEY_MISSING.message(""));
		// the manual setting still applies to the key holders
		assertEquals(Click.MANUAL_OFF, DoorKeys.click(cle, false, NONE, "", LOCK, DOOR, List.of(new Key(LOCK, DOOR)), false, false));
		// a door without lock in key access: nobody's key
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", "", DOOR, List.of(new Key("", "")), false, false));
		// the key does nothing for the other accesses
		assertEquals(Click.LOCKED, DoorKeys.click(DoorAccess.VERROUILLEE, true, NONE, "", LOCK, DOOR, List.of(new Key(LOCK, DOOR)), false, false));
		assertEquals(Click.OK, DoorKeys.click(DoorAccess.LIBRE, true, NONE, "", LOCK, DOOR, NO_KEY, false, false));
		// the redstone next to a key door is ignored (a player's button), the linked levers and the commands are not
		assertFalse(cle.redstoneAccepted(true));
		assertTrue(cle.leversAccepted(true));
		assertFalse(cle.free(), "a key door cannot be broken in survival");
		assertEquals(DoorAccess.CLE, DoorAccess.parse("clé"));
		assertEquals(DoorAccess.CLE, DoorAccess.parse("cle"));
	}

	@Test
	void theMasterKeyOpensEverythingForAnAdministratorOnly() {
		for (DoorAccess a : DoorAccess.values()) {
			assertEquals(Click.OK, DoorKeys.click(a, true, NONE, "tag", LOCK, DOOR, NO_KEY, true, true), "master key, admin: " + a);
			assertEquals(Click.OK, DoorKeys.click(a, false, NONE, "tag", LOCK, DOOR, NO_KEY, true, true), "even the manual off: " + a);
			Click other = DoorKeys.click(a, true, NONE, "tag", LOCK, DOOR, NO_KEY, true, false);
			if (a == DoorAccess.LIBRE) {
				assertEquals(Click.OK, other, "a free door opens for anyone, master key or not");
			} else {
				assertEquals(Click.MASTER_REFUSED, other, "master key, not an admin: " + a);
			}
		}
		assertEquals("Ce passe-partout ne vous obéit pas.", Click.MASTER_REFUSED.message(""));
		// a non-admin carrying both the master key and the door's key: the key opens
		assertEquals(Click.OK, DoorKeys.click(DoorAccess.CLE, true, NONE, "", LOCK, DOOR, List.of(new Key(LOCK, DOOR)), true, false));
	}

	@Test
	void theGesturesWithAKeyInHand() {
		// a blank key: bound by an administrator (sneaking or not), refused to the others
		assertEquals(Gesture.BIND, DoorKeys.gesture(Held.BLANK, false, true, "", "", "", DOOR));
		assertEquals(Gesture.BIND, DoorKeys.gesture(Held.BLANK, true, true, "", "", LOCK, DOOR), "a second blank key: a copy of the key of this door");
		assertEquals(Gesture.NOT_ADMIN, DoorKeys.gesture(Held.BLANK, false, false, "", "", LOCK, DOOR));
		assertEquals(Gesture.NOT_ADMIN, DoorKeys.gesture(Held.BLANK, true, false, "", "", LOCK, DOOR));
		// a bound key: an ordinary click; an administrator sneaking with it on another door is refused (no shared lock)
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.BOUND, false, true, LOCK, DOOR, OTHER, BACK));
		assertEquals(Gesture.OTHER_DOOR, DoorKeys.gesture(Held.BOUND, true, true, LOCK, DOOR, OTHER, BACK));
		assertEquals(Gesture.OTHER_DOOR, DoorKeys.gesture(Held.BOUND, true, true, LOCK, DOOR, "", BACK), "a door without lock does not take the key's");
		assertEquals(Gesture.OTHER_DOOR, DoorKeys.gesture(Held.BOUND, true, true, LOCK, DOOR, LOCK, BACK), "the same lock on another door");
		assertEquals(Gesture.OTHER_DOOR, DoorKeys.gesture(Held.BOUND, true, true, LOCK, "", OTHER, BACK), "a key of 1.32.0 of another lock");
		assertEquals(Gesture.ALREADY, DoorKeys.gesture(Held.BOUND, true, true, LOCK, DOOR, LOCK, DOOR));
		assertEquals(Gesture.ALREADY, DoorKeys.gesture(Held.BOUND, true, true, LOCK, "", LOCK, DOOR), "a key of 1.32.0 of this lock");
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.BOUND, true, false, LOCK, DOOR, OTHER, BACK), "a player sneaking with his key opens his door");
		// the master key: an ordinary click (it opens), sneaking an administrator switches free / key access
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.MASTER, false, true, "", "", LOCK, DOOR));
		assertEquals(Gesture.TOGGLE, DoorKeys.gesture(Held.MASTER, true, true, "", "", LOCK, DOOR));
		assertEquals(Gesture.MASTER_REFUSED, DoorKeys.gesture(Held.MASTER, true, false, "", "", LOCK, DOOR));
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.MASTER, false, false, "", "", LOCK, DOOR));
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.OTHER, true, true, "", "", LOCK, DOOR));
		assertEquals(DoorAccess.CLE, DoorKeys.toggled(DoorAccess.LIBRE));
		assertEquals(DoorAccess.LIBRE, DoorKeys.toggled(DoorAccess.CLE));
		assertEquals(DoorAccess.CLE, DoorKeys.toggled(DoorAccess.QUETE));
		assertEquals("maison_12", DoorKeys.label("maison_12", 1, 2, 3));
		assertEquals("120 64 -40", DoorKeys.label("", 120, 64, -40));
		assertEquals("120 64 -40", DoorKeys.label(null, 120, 64, -40));
	}

	@Test
	void theMessageOfAKeyBoundElsewhere() {
		assertEquals("Cette clé est déjà liée à « maison_12 ». Une clé n'ouvre qu'une seule porte.", DoorKeys.boundElsewhere("maison_12"));
		assertEquals("Cette clé est déjà liée à la porte en 120 64 -40. Une clé n'ouvre qu'une seule porte.", DoorKeys.boundElsewhere("120 64 -40"));
		assertEquals("Cette clé est déjà liée à une autre porte. Une clé n'ouvre qu'une seule porte.", DoorKeys.boundElsewhere(""));
	}

	@Test
	void theAutomaticClosingOfOneMinuteAndThe131Doors() {
		assertEquals(60, DoorData.AUTO_CLOSE_DEFAULT);
		// a 1.31.0 door (no version): its closing was the old default (never, not saved): one minute now
		assertEquals(60, DoorData.autoClose(0, -1));
		assertEquals(60, DoorData.autoClose(0, 0));
		// ... an administrator had set another closing: kept
		assertEquals(5, DoorData.autoClose(0, 5));
		assertEquals(3600, DoorData.autoClose(0, 99999));
		// a 1.32.0 door keeps what it saved, "never" included
		assertEquals(0, DoorData.autoClose(DoorData.VERSION, 0));
		assertEquals(25, DoorData.autoClose(DoorData.VERSION, 25));
		assertEquals(60, DoorData.autoClose(DoorData.VERSION, -1));
		assertEquals(0, DoorData.clamp(-3));
		assertEquals(DoorData.AUTO_CLOSE_MAX, DoorData.clamp(5000));
	}

	@Test
	void unknownWordsAreNotAccesses() {
		assertNull(DoorAccess.parse("passe"));
		assertNotEquals(DoorAccess.CLE, DoorAccess.parse("libre"));
	}
}
