package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.OptionalInt;

/**
 * The requirements of a divine forge recipe (1.34.0) besides its ingredients, checked against a player: the server's
 * profession (a scoreboard objective and a minimum score), a command tag (a recipe unlocked by a quest or an NPC) and
 * an operator level. The game side ({@code fr.medievalships.forge.ForgeRecipes}) answers the {@link Subject} questions
 * from the scoreboard and the player; this class only decides, and says why in French (the reasons the interface shows
 * greyed out under a recipe).
 */
public final class ForgeRequirements {
	private ForgeRequirements() {
	}

	/** What the check needs to know about the player. */
	public interface Subject {
		/** Does the server have this scoreboard objective? */
		boolean objectiveExists(String objective);

		/** The player's score in this objective, or empty when they have none. */
		OptionalInt score(String objective);

		/** Does the player carry this command tag ({@code /tag})? */
		boolean hasTag(String tag);

		/** The player's operator level (0 to 4). */
		int permissionLevel();
	}

	/** The requirements the player does not meet, as French reasons (empty: all met). */
	public static List<String> unmet(ForgeRecipeSpec recipe, Subject who) {
		List<String> out = new ArrayList<>();
		if (recipe.profession() != null) {
			String p = recipe.profession();
			if (!who.objectiveExists(p)) {
				out.add("Métier « " + p + " » niveau " + recipe.level() + " requis (métier inconnu du serveur)");
			} else {
				int have = who.score(p).orElse(0);
				if (have < recipe.level()) {
					out.add("Métier « " + p + " » niveau " + recipe.level() + " requis (vous : " + have + ")");
				}
			}
		}
		if (recipe.tag() != null && !who.hasTag(recipe.tag())) {
			out.add("Recette à débloquer (tag « " + recipe.tag() + " » requis)");
		}
		if (recipe.permission() > 0 && who.permissionLevel() < recipe.permission()) {
			out.add("Réservée au niveau d'opérateur " + recipe.permission());
		}
		return out;
	}
}
