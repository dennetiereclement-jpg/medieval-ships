package fr.medievalships.core;

/**
 * What asks a door to be open (pure Java, tested in JUnit): a click or a command ({@link #manual}), the redstone next
 * to any of its cells ({@link #redstone}), one of its linked levers ({@link #lever}), a command with a duration
 * ({@link #timedUntil}, game tick). The door stays open as long as one of them asks (a logical OR, filtered by its
 * access and settings: {@link #wanted}), then closes.
 */
public final class DoorDemands {
	public boolean manual;
	public boolean redstone;
	public boolean lever;
	/** Game tick until which a command keeps the door open (0: none). */
	public long timedUntil;

	/** Does anything ask the door to be open at {@code now}, the redstone and levers counted only when allowed? */
	public boolean wanted(long now, boolean redstoneAccepted, boolean leversAccepted) {
		return manual || (redstoneAccepted && redstone) || (leversAccepted && lever) || (timedUntil > 0 && now < timedUntil);
	}

	/** What holds the door open apart from the manual demand, in French (for the messages), or null. */
	public String holder(long now, boolean redstoneAccepted, boolean leversAccepted) {
		if (redstoneAccepted && redstone) {
			return "la redstone";
		}
		if (leversAccepted && lever) {
			return "un levier lié";
		}
		if (timedUntil > 0 && now < timedUntil) {
			return "une commande";
		}
		return null;
	}

	/** Forgets every demand. */
	public void clear() {
		manual = false;
		redstone = false;
		lever = false;
		timedUntil = 0;
	}
}
