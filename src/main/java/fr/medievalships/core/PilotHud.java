package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * The pilot's panel (client HUD, French): speed, altitude and vertical speed of an aircraft, depth of a submarine,
 * engine state and gait, autopilot state, the keys. Shown only to the player at the helm, and to the player standing
 * by the helm while the autopilot steers; nobody else sees it. Pure text, built from the synced state of the vessel.
 */
public final class PilotHud {
	private static final Locale FR = Locale.FRANCE;

	public enum Kind { SHIP, AIRCRAFT, SUBMARINE }

	/** What the panel shows. Unknown values are NaN / null. */
	public static final class Status {
		public String vessel = "";
		public Kind kind = Kind.SHIP;
		/** Signed speed (blocks/s), negative going astern. */
		public double speed;
		public double slowSpeed = 2.5;
		public double normalSpeed = 5.0;
		public double fastSpeed = 8.0;
		/** French name of the gait ("lente", "normale", "rapide"). */
		public String gait = "normale";
		/** Vertical speed (blocks/s), positive climbing. */
		public double verticalSpeed;
		/** World height of the main deck (the altitude of an aircraft). */
		public double deckY = Double.NaN;
		/** Height of the keel above the ground under the vessel. */
		public double groundClearance = Double.NaN;
		/** Submarine: depth below the surfaced position (blocks). */
		public double depth = Double.NaN;
		public boolean autopilot;
		/** {@link Autopilot.Phase} name. */
		public String autopilotPhase;
		/** Label of the point the autopilot heads for. */
		public String autopilotTarget;
		/** Horizontal distance to that point (blocks). */
		public double autopilotDistance = Double.NaN;
		/** The autopilot follows a destination given with {@code /pilote goto}: the helm can be taken back. */
		public boolean autopilotGoto;
		/** The player holds the helm (false: he stands by it while the autopilot steers). */
		public boolean atHelm = true;
	}

	private PilotHud() {
	}

	/** The lines of the panel, the first one being the title (the vessel's name), the last one the keys. */
	public static List<String> lines(Status s) {
		List<String> out = new ArrayList<>();
		out.add(s.vessel == null || s.vessel.isBlank() ? "Navire" : s.vessel);
		double v = Math.abs(s.speed);
		out.add(s.speed < -0.05
				? String.format(FR, "Vitesse : %.1f blocs/s en arrière", v)
				: String.format(FR, "Vitesse : %.1f blocs/s (%.0f km/h)", v, v * 3.6));
		if (s.kind == Kind.AIRCRAFT) {
			String alt = Double.isNaN(s.deckY) ? "?" : String.valueOf((int) Math.floor(s.deckY));
			out.add(Double.isNaN(s.groundClearance) || Double.isInfinite(s.groundClearance)
					? "Altitude : " + alt
					: String.format(FR, "Altitude : %s (%.0f blocs sous la quille)", alt, Math.max(0, s.groundClearance)));
			out.add("Vertical : " + vertical(s.verticalSpeed, "montée", "descente", "palier"));
		} else if (s.kind == Kind.SUBMARINE) {
			double d = Double.isNaN(s.depth) ? 0 : s.depth;
			String state = s.verticalSpeed > 0.05 ? "remonte" : s.verticalSpeed < -0.05 ? "plonge" : d < Dive.SURFACED ? "en surface" : "stable";
			out.add(String.format(FR, "Profondeur : %.0f m (%s)", d, state));
		}
		out.add(s.kind == Kind.SHIP
				? "Allure : " + s.gait + " · " + engineState(s)
				: "Moteur : " + engineState(s) + " · allure " + s.gait);
		out.add("Pilote auto : " + autopilot(s));
		if (s.atHelm) {
			out.add(switch (s.kind) {
				case AIRCRAFT -> "[Z/S vitesse · Q/D cap · Espace monter · Ctrl descendre · Maj quitter]";
				case SUBMARINE -> "[Z/S vitesse · Q/D cap · Espace remonter · Ctrl plonger · Maj quitter]";
				case SHIP -> "[Z/S avant/arrière · Q/D barre · Espace/Ctrl allure · Maj quitter]";
			});
		} else if (s.autopilotGoto) {
			out.add("[Clic droit sur la barre : reprendre la main]");
		}
		return out;
	}

	/** Engine (or oars and sails) from the speed: stopped, astern, slow, cruising, full speed. */
	public static String engineState(Status s) {
		double v = s.speed;
		if (Math.abs(v) < 0.15) {
			return s.kind == Kind.AIRCRAFT ? "vol stationnaire" : "à l'arrêt";
		}
		if (v < 0) {
			return "marche arrière";
		}
		if (v <= (s.slowSpeed + s.normalSpeed) / 2) {
			return "ralenti";
		}
		return v <= (s.normalSpeed + s.fastSpeed) / 2 ? "croisière" : "plein régime";
	}

	private static String vertical(double vy, String up, String down, String level) {
		if (vy > 0.05) {
			return String.format(FR, "%s %.1f bloc/s", up, vy);
		}
		if (vy < -0.05) {
			return String.format(FR, "%s %.1f bloc/s", down, -vy);
		}
		return level;
	}

	private static String autopilot(Status s) {
		if (!s.autopilot) {
			return "inactif";
		}
		String target = s.autopilotTarget == null || s.autopilotTarget.isBlank() ? "" : s.autopilotTarget;
		String dist = Double.isNaN(s.autopilotDistance) ? "" : String.format(FR, " (%.0f blocs)", s.autopilotDistance);
		String phase = s.autopilotPhase == null ? "" : s.autopilotPhase;
		return switch (phase) {
			case "SAILING" -> target.isEmpty() ? "en route" + dist : "en route vers " + target + dist;
			case "DOCKED" -> target.isEmpty() ? "à l'escale" : "à l'escale " + target;
			case "FINISHED" -> "arrivé à destination";
			case "RECOVERING" -> "se dégage d'un obstacle";
			default -> "en attente";
		};
	}
}
