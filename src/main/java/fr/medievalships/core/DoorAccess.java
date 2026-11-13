package fr.medievalships.core;

import java.util.Collection;
import java.util.Locale;

/**
 * Who may open a door (pure Java, tested in JUnit), checked the same way on every cell of the door:
 * <ul>
 * <li>{@link #LIBRE}: a click, the redstone, the linked levers, the commands;</li>
 * <li>{@link #VERROUILLEE}: the click is refused (locked chest sound) and the redstone next to the door ignored; the
 * levers an administrator linked and the commands still open it;</li>
 * <li>{@link #LEVIER}: the click does nothing; the redstone, the linked levers and the commands open it;</li>
 * <li>{@link #ADMIN}: the commands only;</li>
 * <li>{@link #QUETE}: the click only for the players carrying the command tag of the door (given by a quest or a
 * NPC with {@code /tag @p add <tag>}); the redstone, the levers and the commands too.</li>
 * </ul>
 * There is no key system. Per door, a manual setting (click allowed or not) and a redstone setting (redstone and
 * linked levers taken into account or not) come on top.
 */
public enum DoorAccess {
	LIBRE("libre"), VERROUILLEE("verrouillee"), LEVIER("levier"), ADMIN("admin"), QUETE("quete");

	/** Verdict of a click. */
	public enum Click {
		OK, LOCKED, LEVER_ONLY, ADMIN_ONLY, MANUAL_OFF, QUEST_MISSING;

		/** The French message shown to the player (action bar), or null for {@link #OK}. */
		public String message(String questTag) {
			return switch (this) {
				case OK -> null;
				case LOCKED -> "Cette porte est verrouillée.";
				case LEVER_ONLY -> "Cette porte s'ouvre avec un levier ou un mécanisme.";
				case ADMIN_ONLY -> "Cette porte ne s'ouvre pas à la main.";
				case MANUAL_OFF -> "Cette porte ne s'ouvre pas à la main.";
				case QUEST_MISSING -> "Cette porte reste close : vous n'avez pas encore le droit de passer.";
			};
		}
	}

	private final String word;

	DoorAccess(String word) {
		this.word = word;
	}

	/** The word of the commands and of the saved data ({@code libre}, {@code verrouillee}...). */
	public String word() {
		return word;
	}

	/** French description for /porte info. */
	public String describe(String questTag) {
		return switch (this) {
			case LIBRE -> "libre";
			case VERROUILLEE -> "verrouillée";
			case LEVIER -> "levier / mécanisme seulement";
			case ADMIN -> "commandes seulement";
			case QUETE -> "quête (tag « " + (questTag == null ? "" : questTag) + " »)";
		};
	}

	/** The access of a word (accents and case ignored), or null. */
	public static DoorAccess parse(String s) {
		if (s == null) {
			return null;
		}
		String k = s.trim().toLowerCase(Locale.ROOT).replace('é', 'e').replace('è', 'e').replace('ê', 'e');
		for (DoorAccess a : values()) {
			if (a.word.equals(k)) {
				return a;
			}
		}
		return switch (k) {
			case "verrouille", "locked" -> VERROUILLEE;
			case "free", "open" -> LIBRE;
			case "lever" -> LEVIER;
			case "quest" -> QUETE;
			default -> null;
		};
	}

	/** What a click of a player carrying {@code tags} does on a door of this access. */
	public Click click(boolean manualEnabled, Collection<String> tags, String questTag) {
		switch (this) {
			case ADMIN:
				return Click.ADMIN_ONLY;
			case VERROUILLEE:
				return Click.LOCKED;
			case LEVIER:
				return Click.LEVER_ONLY;
			default:
				break;
		}
		if (!manualEnabled) {
			return Click.MANUAL_OFF;
		}
		if (this == QUETE) {
			return questTag != null && !questTag.isEmpty() && tags != null && tags.contains(questTag) ? Click.OK : Click.QUEST_MISSING;
		}
		return Click.OK;
	}

	/** Does the redstone next to the door count? */
	public boolean redstoneAccepted(boolean redstoneEnabled) {
		return redstoneEnabled && this != ADMIN && this != VERROUILLEE;
	}

	/** Do the linked levers count? */
	public boolean leversAccepted(boolean redstoneEnabled) {
		return redstoneEnabled && this != ADMIN;
	}

	/** Is the door free (breakable in survival by anyone)? */
	public boolean free() {
		return this == LIBRE;
	}

	/** A valid quest tag: what {@code /tag} accepts (letters, digits, {@code _ - . +}), 1 to 64 characters. */
	public static boolean validTag(String tag) {
		return tag != null && tag.matches("[A-Za-z0-9_.+-]{1,64}");
	}
}
