package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;

/**
 * The Gear Steamship ({@code gear_steamship}): a steampunk steamer of 42 blocks from its stern gallery to its stem
 * head (45 with the bow boom), 10 wide, with an iron-plated black hull trimmed with stepped copper and brass bands,
 * copper pipes and two brass gear wheels on each side, a riveted copper dome and a tall black funnel on its engine
 * house, two masts with black square sails bordered with gold (a big gold gear on the main sail), a crane at the
 * stern with a hanging crate and a raised prow carrying a lantern on a boom. It sails like a heavy steamer (its
 * gears turn and its funnel smokes under way) and has rooms: the engine room with its boiler, the crew quarters,
 * the captain's cabin (the deckhouse, the bridge with the helm on its roof) and the hold, described by its interior
 * grid ({@code tools/gear_steam_interior.py}).
 *
 * <p>Ship-local blocks, the same numbers as {@code tools/gear_steam_shape.py}: y = 0 is the waterline.
 */
public final class GearSteamLayout {
	public static final double HALF_LENGTH = 18.0;
	public static final double TIP = 19.0;
	public static final double MAX_HALF_WIDTH = 5.0;
	public static final double WATERLINE_Y = 0.6;
	public static final double KEEL_DEPTH = 3.0;
	public static final double HOLD_FLOOR_Y = 1.0;
	public static final double MAIN_DECK_Y = 4.5;
	public static final double FORECASTLE_Y = 6.0;
	public static final double POOP_Y = 7.5;
	public static final double ENGINE_ROOF_Y = 9.0;
	public static final double BRIDGE_Y = 11.0;
	public static final double CABIN_FLOOR_Y = POOP_Y;
	public static final double TRANSOM_Z = -16.0;
	public static final double GALLERY_Z = -20.0;
	/** The aft face of the poop deck carried over the stern gallery (the gallery's last block stands out beyond it). */
	public static final double OVERHANG_Z = -18.5;
	public static final double POOP_FRONT_Z = -6.5;
	public static final double ENGINE_FRONT_Z = 5.0;
	public static final double FORECASTLE_Z = 11.5;
	public static final double DECK_MAX_Z = 19.5;
	/** The captain's deckhouse: its fore part stands on the engine house roof and wraps the funnel, which rises through it. */
	public static final double[] DECKHOUSE_Z = {-12.0, -5.0};
	public static final double DECKHOUSE_HALF = 3.0;
	/** The front wall of the captain's cabin (the aft face of the funnel casing inside the deckhouse). */
	public static final double CABIN_FRONT_Z = -7.0;
	/** Collision top of the waist bulwark (its copper cap is drawn at 5.5, the railing higher). */
	public static final double WAIST_BULWARK_TOP = 6.0;
	/** The main mast, stepped on the keel (through the hold and the waist). */
	public static final double MAIN_MAST_Z = 7.5;
	public static final double MAIN_MAST_TOP = 19.6;
	/** Top of the lookout box at the main masthead. */
	public static final double MAIN_BOX_TOP = 20.0;
	/** The mizzen, stepped on the poop deck; its lookout box tops at 18.1. */
	public static final double MIZZEN_Z = -15.9;
	public static final double MIZZEN_TOP = 18.0;
	public static final double MIZZEN_BOX_TOP = 18.1;
	public static final double MAIN_YARD_Y = 17.2;
	public static final double MIZZEN_YARD_Y = 15.5;
	public static final double MAIN_YARD_HALF = 6.0;
	public static final double MIZZEN_YARD_HALF = 3.45;
	/** The yards are braced round (the starboard arms aft) and peaked (the aft arms higher), as in the model. */
	public static final double BRACE_DEG = 62.0;
	public static final double YARD_TILT_DEG = 22.0;
	/** The funnel on the engine house roof (its mouth, where it smokes) and the copper dome. */
	public static final double FUNNEL_Z = -5.6;
	public static final double FUNNEL_R = 1.4;
	public static final double FUNNEL_TOP = 18.0;
	public static final double DOME_Z = -0.9;
	public static final double DOME_R = 2.85;
	public static final double DOME_TOP = 14.2;
	/** The stern crane: its post on the poop deck's aft edge, the tip of its jib and the crate hanging under it. */
	public static final double CRANE_Z = -18.0;
	public static final double[] CRANE_TIP = {0.0, 13.0, -23.0};
	public static final double[] CRATE_Y = {7.4, 8.7};
	/** The raised prow and the boom carrying the great bow lantern. */
	public static final double[] STEM_HEAD = {0.0, 10.9, 22.0};
	public static final double[] BOOM_TIP = {0.0, 10.7, 25.2};
	/** How far aft the hanging crate reaches. */
	public static final double STERN_REACH_Z = -23.95;
	/** The big brass gear wheel on each side (y, z, radius), the small one at the bow. */
	public static final double[] BIG_GEAR = {4.5, -0.4, 2.0};
	public static final double[] BOW_GEAR = {5.8, 17.4, 1.1};
	public static final double HELM_Z = -7.75;
	public static final double PILOT_Z = -8.55;
	/** Stairs and ladders of the interior grid (x0, x1) and (z start, z end). */
	public static final double[] FC_STAIR_X = {1.5, 3.0};
	public static final double[] FC_STAIR_Z = {10.0, 11.5};
	public static final double[] COMPANION_X = {1.5, 3.0};
	public static final double[] COMPANION_Z = {6.0, 9.5};
	public static final double[] ENGINE_STAIR_X = {-3.5, -2.0};
	public static final double[] ENGINE_STAIR_Z = {-1.0, -4.5};
	public static final double[] POOP_STEP_X = {3.0, 4.5};
	public static final double[] ROOF_LADDER_X = {2.5, 3.5};
	public static final double[] ROOF_LADDER_Z = {5.0, 5.5};
	public static final double[] BRIDGE_LADDER_X = {1.5, 2.5};
	public static final double[] BRIDGE_LADDER_Z = {-12.5, -12.0};
	/** Doors of the interior grid. */
	public static final int ENGINE_DOOR = 0;
	public static final int CREW_DOOR = 1;
	public static final int GALLERY_DOOR = 2;
	public static final int CABIN_DOOR = 3;
	public static final String GRID = "/assets/medievalships/interiors/gear_steamship.grid";
	public static final String DECOR = "/assets/medievalships/interiors/gear_steamship_decor.json";

	private GearSteamLayout() {
	}

	/** The ship type (registered as {@link Ships#GEAR_STEAMSHIP}). */
	public static ShipType type() {
		HullShape.Params p = new HullShape.Params();
		p.halfLength = HALF_LENGTH;
		p.tip = TIP;
		p.maxHalfWidth = MAX_HALF_WIDTH;
		p.foreScale = 18.8;
		p.forePowA = 2.4;
		p.forePowB = 0.62;
		p.aftScale = 24.0;
		p.aftPowA = 3.2;
		p.aftPowB = 0.5;
		p.keelDepth = KEEL_DEPTH;
		p.keelRise = 2.6;
		p.keelPow = 3.0;
		p.railBase = 5.5;
		p.railRiseFore = 1.5;
		p.railRiseAft = 0.0;
		p.railPow = 4.0;
		p.railFloors = List.of(new HullShape.RaisedDeck(Double.NEGATIVE_INFINITY, POOP_FRONT_Z, POOP_Y + 1.0),
				new HullShape.RaisedDeck(POOP_FRONT_Z, ENGINE_FRONT_Z, ENGINE_ROOF_Y + 1.0),
				new HullShape.RaisedDeck(FORECASTLE_Z, Double.POSITIVE_INFINITY, FORECASTLE_Y + 1.5));
		p.waterlineY = WATERLINE_Y;
		p.mainDeckY = MAIN_DECK_Y;
		p.deckMinZ = ENGINE_FRONT_Z;
		p.deckMaxZ = DECK_MAX_Z;
		p.bottomSection = new double[][] {{0.0, 1.0}, {0.5, 0.92}, {0.82, 0.6}, {0.97, 0.15}};
		HullShape hull = new HullShape(p);

		ShipGeometry.Spec spec = new ShipGeometry.Spec();
		spec.interior = GRID;
		spec.decor = DECOR;
		double b = BRIDGE_Y;
		List<ShipGeometry.Seat> seats = new ArrayList<>();
		// the pilot stands at the wheel on the bridge (the roof of the captain's deckhouse)
		seats.add(new ShipGeometry.Seat(ShipGeometry.PILOT_SEAT, 0.0, b + 0.28, PILOT_Z, true, new double[] {1.2, b + 0.02, PILOT_Z}));
		for (InteriorDecor.SeatSpot spot : InteriorDecor.load(DECOR).seats()) {
			seats.add(new ShipGeometry.Seat(seats.size(), spot.x(), spot.y(), spot.z(), false,
					new double[] {spot.dismountX(), spot.dismountY(), spot.dismountZ()}));
		}
		spec.seats = List.copyOf(seats);
		spec.helm = new ShipGeometry.LocalBox(-0.8, b + 0.2, HELM_Z - 0.45, 0.8, b + 1.8, HELM_Z + 0.35);
		// the masts and the funnel above the decks (the grid holds them below its top)
		spec.masts = List.of(
				new ShipGeometry.Mast(0, MAIN_MAST_Z, MAIN_DECK_Y, MAIN_BOX_TOP, 0.48),
				new ShipGeometry.Mast(0, MIZZEN_Z, POOP_Y, MIZZEN_BOX_TOP, 0.38));
		List<ShipGeometry.LocalBox> solids = new ArrayList<>();
		for (ShipGeometry.Mast mast : spec.masts) {
			solids.add(new ShipGeometry.LocalBox(mast.x() - mast.half(), mast.bottom(), mast.z() - mast.half(), mast.x() + mast.half(), mast.top(),
					mast.z() + mast.half()));
		}
		solids.add(new ShipGeometry.LocalBox(-FUNNEL_R, ENGINE_ROOF_Y, FUNNEL_Z - FUNNEL_R, FUNNEL_R, FUNNEL_TOP, FUNNEL_Z + FUNNEL_R));
		spec.solids = List.copyOf(solids);
		spec.probeHeights = new double[] {0.2, 2.0, 4.0, 6.0};
		// the boom, its lantern, the crane's jib and crate, the stern gallery, the rudder and the yard arms touch
		// the shore before the hull
		List<double[]> probes = new ArrayList<>();
		for (double t = 0.0; t <= 1.0001; t += 0.25) {
			probes.add(new double[] {0, STEM_HEAD[1] + (BOOM_TIP[1] - STEM_HEAD[1]) * t, STEM_HEAD[2] + (BOOM_TIP[2] - STEM_HEAD[2]) * t});
		}
		probes.add(new double[] {0, BOOM_TIP[1] - 2.6, BOOM_TIP[2] - 0.4});
		probes.add(new double[] {0, STEM_HEAD[1] - 4.0, 21.0});
		probes.add(CRANE_TIP.clone());
		probes.add(new double[] {0, CRATE_Y[0], CRANE_TIP[2] - 0.75});
		probes.add(new double[] {0, CRATE_Y[0], CRANE_TIP[2] + 0.75});
		for (double side : new double[] {1, -1}) {
			probes.add(new double[] {side * 3.5, 3.5, GALLERY_Z - 0.5});
			probes.add(new double[] {side * 3.5, POOP_Y + 1.0, GALLERY_Z - 0.5});
		}
		probes.add(new double[] {0, -1.0, -17.4});
		yardArms(probes, MAIN_YARD_Y, MAIN_MAST_Z, 0.675, MAIN_YARD_HALF);
		yardArms(probes, MIZZEN_YARD_Y, MIZZEN_Z, 0.575, MIZZEN_YARD_HALF);
		spec.extraProbes = List.copyOf(probes);
		spec.boundingRadius = -STERN_REACH_Z + 1.0;
		spec.aiReach = BOOM_TIP[2];
		spec.aiBack = -STERN_REACH_Z;
		spec.aiHalfWidth = MAX_HALF_WIDTH + 1.0;
		spec.lowestY = -KEEL_DEPTH;
		spec.boardMinZ = ENGINE_FRONT_Z + 0.6;
		spec.boardMaxZ = FORECASTLE_Z - 1.7;
		spec.boardHalfWidth = 0.9;
		spec.avoidZ = new double[] {};
		spec.sternPost = false;
		return new ShipType("gear_steamship", "Navire à vapeur à engrenages", new ShipGeometry(hull, spec), GearSteamLayout::config);
	}

	/**
	 * Both ends of a yard at height y, hung {@code off} before its mast at z, peaked by {@link #YARD_TILT_DEG} (the
	 * starboard arm higher) and braced round by {@link #BRACE_DEG} (the starboard arm aft), as in the model.
	 */
	static double[] yardArm(double side, double y, double mastZ, double off, double half) {
		double t = Math.toRadians(YARD_TILT_DEG), b = Math.toRadians(BRACE_DEG);
		double x = side * half;
		double xr = x * Math.cos(t), yr = -x * Math.sin(t);
		return new double[] {xr * Math.cos(b) - off * Math.sin(b), y + yr, mastZ + xr * Math.sin(b) + off * Math.cos(b)};
	}

	private static void yardArms(List<double[]> probes, double y, double mastZ, double off, double half) {
		for (double side : new double[] {1, -1}) {
			probes.add(yardArm(side, y, mastZ, off, half));
		}
	}

	/** A heavy steamer: slow to gather way and to stop, a long glide, steady turns. */
	public static ShipConfig config() {
		ShipConfig c = new ShipConfig();
		c.slowSpeed = 1.6;
		c.normalSpeed = 3.8;
		c.fastSpeed = 6.2;
		c.reverseSpeed = 1.2;
		c.acceleration = 0.26;
		c.braking = 0.5;
		c.waterDrag = 0.06;
		c.maxTurnRate = 6.5;
		c.minTurnFactor = 0.08;
		c.helmRate = 0.75;
		c.helmReturnRate = 0.55;
		c.turnResponse = 0.5;
		c.turnSpeedLoss = 0.1;
		c.waveRocking = 0.6;
		c.aiWaypointRadius = 14.0;
		c.aiStopRadius = 3.5;
		c.aiLookahead = 28.0;
		c.aiProbeDistance = 75.0;
		c.aiStuckSeconds = 12;
		c.aiTurnAroundSpeed = 1.6;
		return c;
	}
}
