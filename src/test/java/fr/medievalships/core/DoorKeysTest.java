package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.SplittableRandom;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.DoorAccess.Click;
import fr.medievalships.core.DoorKeys.Gesture;
import fr.medievalships.core.DoorKeys.Held;

/**
 * The keys of the doors (1.32.0) in pure Java: the locks, a bound key opening its door only, the master key (the
 * administrators' only), the gestures of the administrators with a key in hand, the automatic closing of one minute
 * and the migration of the doors saved by 1.31.0.
 */
class DoorKeysTest {
	private static final String LOCK = "0123456789ab", OTHER = "ba9876543210";
	private static final List<String> NONE = List.of();

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
	}

	@Test
	void aBoundKeyOpensItsDoorOnly() {
		assertTrue(DoorKeys.opens(LOCK, LOCK));
		assertFalse(DoorKeys.opens(OTHER, LOCK), "the key of another door");
		assertFalse(DoorKeys.opens("", LOCK), "a blank key");
		assertFalse(DoorKeys.opens(null, LOCK));
		assertFalse(DoorKeys.opens("", ""), "a blank key on a door without lock");
		assertTrue(DoorKeys.carries(List.of(OTHER, LOCK), LOCK), "anywhere in the inventory");
		assertFalse(DoorKeys.carries(List.of(OTHER), LOCK));
		assertFalse(DoorKeys.carries(List.of(""), ""));
		assertFalse(DoorKeys.carries(null, LOCK));
	}

	@Test
	void theKeyAccess() {
		DoorAccess cle = DoorAccess.CLE;
		// the key of this lock, anywhere: opens; none, or the key of another door: refused with the message
		assertEquals(Click.OK, DoorKeys.click(cle, true, NONE, "", LOCK, List.of(LOCK), false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, NONE, false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, List.of(OTHER), false, false));
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", LOCK, NONE, false, true), "an admin without key nor master key");
		assertEquals("Vous n'avez pas la clé de cette porte.", Click.KEY_MISSING.message(""));
		// the manual setting still applies to the key holders
		assertEquals(Click.MANUAL_OFF, DoorKeys.click(cle, false, NONE, "", LOCK, List.of(LOCK), false, false));
		// a door without lock in key access: nobody's key
		assertEquals(Click.KEY_MISSING, DoorKeys.click(cle, true, NONE, "", "", List.of(""), false, false));
		// the key does nothing for the other accesses
		assertEquals(Click.LOCKED, DoorKeys.click(DoorAccess.VERROUILLEE, true, NONE, "", LOCK, List.of(LOCK), false, false));
		assertEquals(Click.OK, DoorKeys.click(DoorAccess.LIBRE, true, NONE, "", LOCK, NONE, false, false));
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
			assertEquals(Click.OK, DoorKeys.click(a, true, NONE, "tag", LOCK, NONE, true, true), "master key, admin: " + a);
			assertEquals(Click.OK, DoorKeys.click(a, false, NONE, "tag", LOCK, NONE, true, true), "even the manual off: " + a);
			Click other = DoorKeys.click(a, true, NONE, "tag", LOCK, NONE, true, false);
			if (a == DoorAccess.LIBRE) {
				assertEquals(Click.OK, other, "a free door opens for anyone, master key or not");
			} else {
				assertEquals(Click.MASTER_REFUSED, other, "master key, not an admin: " + a);
			}
		}
		assertEquals("Ce passe-partout ne vous obéit pas.", Click.MASTER_REFUSED.message(""));
		// a non-admin carrying both the master key and the door's key: the key opens
		assertEquals(Click.OK, DoorKeys.click(DoorAccess.CLE, true, NONE, "", LOCK, List.of(LOCK), true, false));
	}

	@Test
	void theGesturesWithAKeyInHand() {
		// a blank key: bound by an administrator (sneaking or not), refused to the others
		assertEquals(Gesture.BIND, DoorKeys.gesture(Held.BLANK, false, true, "", ""));
		assertEquals(Gesture.BIND, DoorKeys.gesture(Held.BLANK, true, true, "", LOCK), "a second blank key: a copy");
		assertEquals(Gesture.NOT_ADMIN, DoorKeys.gesture(Held.BLANK, false, false, "", LOCK));
		assertEquals(Gesture.NOT_ADMIN, DoorKeys.gesture(Held.BLANK, true, false, "", LOCK));
		// a bound key: an ordinary click, but an administrator sneaking gives its lock to the door
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.BOUND, false, true, LOCK, OTHER));
		assertEquals(Gesture.SHARE, DoorKeys.gesture(Held.BOUND, true, true, LOCK, OTHER));
		assertEquals(Gesture.SHARE, DoorKeys.gesture(Held.BOUND, true, true, LOCK, ""), "a door without lock takes the key's");
		assertEquals(Gesture.ALREADY, DoorKeys.gesture(Held.BOUND, true, true, LOCK, LOCK));
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.BOUND, true, false, LOCK, OTHER), "a player sneaking with his key opens his door");
		// the master key: an ordinary click (it opens), sneaking an administrator switches free / key access
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.MASTER, false, true, "", LOCK));
		assertEquals(Gesture.TOGGLE, DoorKeys.gesture(Held.MASTER, true, true, "", LOCK));
		assertEquals(Gesture.MASTER_REFUSED, DoorKeys.gesture(Held.MASTER, true, false, "", LOCK));
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.MASTER, false, false, "", LOCK));
		assertEquals(Gesture.CLICK, DoorKeys.gesture(Held.OTHER, true, true, "", LOCK));
		assertEquals(DoorAccess.CLE, DoorKeys.toggled(DoorAccess.LIBRE));
		assertEquals(DoorAccess.LIBRE, DoorKeys.toggled(DoorAccess.CLE));
		assertEquals(DoorAccess.CLE, DoorKeys.toggled(DoorAccess.QUETE));
		assertEquals("maison_12", DoorKeys.label("maison_12", 1, 2, 3));
		assertEquals("120 64 -40", DoorKeys.label("", 120, 64, -40));
		assertEquals("120 64 -40", DoorKeys.label(null, 120, 64, -40));
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
