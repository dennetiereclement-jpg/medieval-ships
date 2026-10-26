package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Random;
import java.util.function.DoubleBinaryOperator;

import org.junit.jupiter.api.Test;

import com.google.gson.Gson;

/**
 * The features shared by every vessel (1.9): placement permissions, the visual bank of the aircraft in turns, the
 * pilot's panel, destinations for the autopilot ({@code goto}), and the early-exit space check of the placement.
 */
class SharedFeaturesTest {
	private static final double DT = 0.05;

	// ------------------------------------------------------------------ permissions

	@Test
	void everyoneMayPlaceByDefault() {
		ServerSettings s = new ServerSettings();
		s.sanitize();
		assertTrue(s.mayPlace("galley", false, "Alice", "0000-1"));
		assertTrue(s.mayPlace("sky_leviathan", false, "Alice", "0000-1"));
		assertTrue(s.mayPlace("sky_leviathan", true, "Admin", "0000-2"));
	}

	@Test
	void placeRequiresAdminLetsOnlyAdminsAndAllowedPlayersPlace() {
		ServerSettings s = new ServerSettings();
		s.placeRequiresAdmin = true;
		s.placeAllowedPlayers = new java.util.ArrayList<>(List.of(" Capitaine_Nemo ", "1234-ABCD", ""));
		s.sanitize();
		assertFalse(s.mayPlace("galley", false, "Alice", "0000-1"), "a player who is not allowed");
		assertTrue(s.mayPlace("galley", true, "Admin", "0000-2"), "an admin");
		assertTrue(s.mayPlace("galley", false, "capitaine_nemo", "0000-3"), "an allowed player, by name (any case)");
		assertTrue(s.mayPlace("nautilus", false, "Bob", "1234-abcd"), "an allowed player, by UUID");
		assertEquals(2, s.placeAllowedPlayers.size(), "blank entries are dropped");
	}

	@Test
	void someVesselsCanBeReservedToAdmins() {
		ServerSettings s = new ServerSettings();
		s.placeAdminOnly = new java.util.ArrayList<>(List.of("sky_leviathan", "crystal_airship"));
		s.sanitize();
		assertFalse(s.mayPlace("sky_leviathan", false, "Alice", "0000-1"));
		assertFalse(s.mayPlace("crystal_airship", false, "Alice", "0000-1"));
		assertTrue(s.mayPlace("galley", false, "Alice", "0000-1"), "the other vessels stay free");
		assertTrue(s.mayPlace("sky_leviathan", true, "Admin", "0000-2"));
	}

	@Test
	void placeAdminOnlyAcceptsTheAliasesAndReportsUnknownIds() {
		ServerSettings s = new ServerSettings();
		s.placeAdminOnly = new java.util.ArrayList<>(List.of("grand_warship", " Sky_Leviathan ", "sky_leviathan", "galion_volant"));
		s.sanitize();
		assertEquals(List.of("warship", "sky_leviathan", "galion_volant"), s.placeAdminOnly, "aliases and any case become the ids, once each");
		assertFalse(s.mayPlace("warship", false, "Alice", "0000-1"), "\"grand_warship\" reserves the great warship");
		assertFalse(s.mayPlace("sky_leviathan", false, "Alice", "0000-1"));
		assertTrue(s.mayPlace("galleon", false, "Alice", "0000-1"));
		assertEquals(List.of("galion_volant"), s.unknownVessels(), "a typo is reported (logged as a warning)");
	}

	@Test
	void oldConfigFilesKeepTheNewDefaults() {
		// a "server" section written by 1.8 (no new keys), and one with explicit nulls
		ServerSettings old = new Gson().fromJson("{\"adminPermissionLevel\":3,\"placeRequiresAdmin\":false}", ServerSettings.class);
		old.sanitize();
		assertEquals(3, old.adminPermissionLevel);
		assertTrue(old.placeAdminOnly.isEmpty() && old.placeAllowedPlayers.isEmpty());
		assertTrue(old.playerDestinations);
		assertEquals(1000, old.playerDestinationMaxDistance, 1e-9, "a player's destination is at most 1000 blocks away by default");
		ServerSettings nulls = new Gson().fromJson("{\"placeAdminOnly\":null,\"placeAllowedPlayers\":null}", ServerSettings.class);
		nulls.sanitize();
		assertNotNull(nulls.placeAdminOnly);
		assertTrue(nulls.mayPlace("galley", false, "Alice", "x"));
		FlightConfig f = new Gson().fromJson("{\"climbSpeed\":1.0}", FlightConfig.class);
		f.sanitize();
		assertEquals(6.0, f.bankAngle, 1e-9, "a flight block without the new key banks by default");
	}

	// ------------------------------------------------------------------ banking

	@Test
	void banksIntoTheTurnLikeACoordinatedTurn() {
		double limit = 6;
		assertEquals(0, Flight.bankTarget(0, 12, limit), 1e-12, "turning on the spot: no bank");
		assertEquals(0, Flight.bankTarget(5, 0, limit), 1e-12, "straight: no bank");
		double right = Flight.bankTarget(4, 8, limit);
		assertTrue(right > 2 && right < 4, "4 blocks/s, 8 deg/s: about 3.3 degrees (" + right + ")");
		assertEquals(-right, Flight.bankTarget(4, -8, limit), 1e-12, "left turn: the other way");
		assertEquals(-right, Flight.bankTarget(-4, 8, limit), 1e-12, "going astern: the other way");
		assertEquals(limit, Flight.bankTarget(10, 30, limit), 1e-12, "never more than the limit");
		assertEquals(0, Flight.bankTarget(10, 30, 0), 1e-12, "bank disabled");
	}

	@Test
	void bankEasesInAndOut() {
		double b = 0;
		for (int i = 0; i < 20; i++) {
			b = Flight.bankStep(b, 6, DT);
		}
		assertTrue(b > 3 && b < 5.5, "after 1 s it is on its way (" + b + ")");
		for (int i = 0; i < 60; i++) {
			b = Flight.bankStep(b, 6, DT);
		}
		assertEquals(6, b, 0.1, "after 4 s it is there");
		for (int i = 0; i < 200; i++) {
			b = Flight.bankStep(b, 0, DT);
		}
		assertEquals(0, b, 1e-9, "back level once the turn is over");
	}

	@Test
	void everyAircraftBanksByDefaultWithoutTheDecksDriftingFromTheirCollisions() {
		int aircraft = 0;
		for (ShipType t : Ships.ALL) {
			ShipConfig c = t.defaults().get();
			c.sanitize();
			if (!t.geometry().flying()) {
				assertEquals(null, c.flight, t.id() + ": only aircraft have flight settings");
				continue;
			}
			aircraft++;
			double limit = Flight.bankLimit(t.geometry(), c.flight);
			assertTrue(c.flight.bankAngle > 0 && limit > 0, t.id() + ": banking is on by default");
			assertTrue(limit <= c.flight.bankAngle + 1e-9, t.id());
			// the renderer's own transform (Flight.bankPoint) applied, at full bank either way, to every place where one
			// walks: the deck from rail to rail up to head height, and every walkable cell of the rooms
			double drift = 0;
			for (double[] p : walkablePoints(t.geometry())) {
				for (double bank : new double[] {limit, -limit}) {
					double[] q = Flight.bankPoint(p[0], p[1], t.geometry().hull().mainDeckY, bank);
					drift = Math.max(drift, Math.hypot(q[0] - p[0], q[1] - p[1]));
				}
			}
			assertTrue(drift <= Flight.BANK_TOLERANCE + 1e-9,
					t.id() + ": at full bank no walkable deck or room is drawn more than half a block away (" + drift + ")");
			FlightConfig off = c.flight;
			off.bankAngle = 0;
			assertEquals(0, Flight.bankLimit(t.geometry(), off), 1e-12, t.id() + ": bankAngle 0 disables it");
		}
		assertTrue(aircraft >= 2);
		ShipConfig airship = Ships.STEAMPUNK_AIRSHIP.defaults().get();
		assertEquals(6.0, Flight.bankLimit(Ships.STEAMPUNK_AIRSHIP.geometry(), airship.flight), 1e-9, "the small airship banks fully");
		ShipConfig leviathan = Ships.SKY_LEVIATHAN.defaults().get();
		double l = Flight.bankLimit(Ships.SKY_LEVIATHAN.geometry(), leviathan.flight);
		assertTrue(l > 0.3 && l < 1.5, "the Sky Leviathan, rooms from its hold to the top of its balloon, hardly leans (" + l + ")");
	}

	/** Local (x, y) of the places where one walks: deck edges at foot and head height, every walkable cell. */
	private static List<double[]> walkablePoints(ShipGeometry g) {
		List<double[]> out = new java.util.ArrayList<>();
		double deck = g.hull().mainDeckY, w = g.hull().maxHalfWidth;
		for (double x : new double[] {-w, 0, w}) {
			out.add(new double[] {x, deck});
			out.add(new double[] {x, deck + 2.0});
		}
		InteriorGrid grid = g.interior();
		if (grid != null) {
			for (int i = 0; i < grid.nx; i++) {
				for (int k = 0; k < grid.nz; k++) {
					for (int j = 0; j < grid.ny; j++) {
						byte kind = grid.kind(i, j, k);
						if (kind == InteriorGrid.DRY || kind == InteriorGrid.LADDER || kind == InteriorGrid.AIRLOCK || kind >= InteriorGrid.DOOR) {
							out.add(new double[] {grid.x0 + (i + 0.5) * grid.cell, grid.y0 + (j + 0.5) * grid.cell});
						}
					}
				}
			}
		}
		return out;
	}

	@Test
	void theStarboardSideGoesDownInARightTurn() {
		// the yaw grows in a right turn (clockwise seen from above); local +x is the port side
		double bank = Flight.bankTarget(5, 10, 6);
		assertTrue(bank > 0, "a right turn banks positive (" + bank + ")");
		double deck = 1.2;
		double[] starboard = Flight.bankPoint(-3, deck, deck, bank), port = Flight.bankPoint(3, deck, deck, bank);
		assertTrue(starboard[1] < deck - 0.1 && port[1] > deck + 0.1, "starboard (inside of the turn) down, port up: "
				+ starboard[1] + " / " + port[1]);
		double[] axis = Flight.bankPoint(0, deck, deck, bank);
		assertEquals(0, axis[0], 1e-12, "the roll axis is the keel line at deck height");
		assertEquals(deck, axis[1], 1e-12);
		double[] left = Flight.bankPoint(-3, deck, deck, Flight.bankTarget(5, -10, 6));
		assertTrue(left[1] > deck + 0.1, "a left turn lifts the starboard side");
	}

	// ------------------------------------------------------------------ the pilot's panel

	private static PilotHud.Status airship() {
		PilotHud.Status s = new PilotHud.Status();
		s.vessel = "Dirigeable steampunk";
		s.kind = PilotHud.Kind.AIRCRAFT;
		s.speed = 4.2;
		s.slowSpeed = 2.5;
		s.normalSpeed = 5.0;
		s.fastSpeed = 8.0;
		s.verticalSpeed = 1.2;
		s.deckY = 112.4;
		s.groundClearance = 24.2;
		return s;
	}

	@Test
	void panelOfAnAircraftPilot() {
		List<String> l = PilotHud.lines(airship());
		assertEquals("Dirigeable steampunk", l.get(0));
		assertTrue(l.contains("Vitesse : 4,2 blocs/s (15 km/h)"), l.toString());
		assertTrue(l.contains("Altitude : 112 (24 blocs sous la quille)"), l.toString());
		assertTrue(l.contains("Vertical : montée 1,2 bloc/s"), l.toString());
		PilotHud.Status low = airship();
		low.speed = 1.96;
		low.groundClearance = 1.2;
		low.verticalSpeed = -2.5;
		List<String> lo = PilotHud.lines(low);
		assertTrue(lo.contains("Vitesse : 2,0 blocs/s (7 km/h)") && lo.contains("Altitude : 112 (1 bloc sous la quille)")
				&& lo.contains("Vertical : descente 2,5 blocs/s"), "French plurals: " + lo);
		assertTrue(l.contains("Moteur : croisière · allure normale"), l.toString());
		assertTrue(l.contains("Pilote auto : inactif"), l.toString());
		assertTrue(l.get(l.size() - 1).startsWith("[") && l.get(l.size() - 1).contains("Espace monter"), l.toString());
		PilotHud.Status hover = airship();
		hover.speed = 0;
		hover.verticalSpeed = 0;
		List<String> h = PilotHud.lines(hover);
		assertTrue(h.contains("Moteur : vol stationnaire · allure normale") && h.contains("Vertical : palier"), h.toString());
	}

	@Test
	void panelShowsTheKeysAsBoundAndTheAdminsSpeedLimit() {
		PilotHud.Status s = airship();
		s.keys = new PilotHud.Keys("W", "S", "A", "D", "Space", "Left Control", "Left Shift");
		List<String> l = PilotHud.lines(s);
		assertEquals("[W/S vitesse · A/D cap · Space monter · Left Control descendre · Left Shift quitter]", l.get(l.size() - 1),
				"a QWERTY (or rebound) keyboard sees its own keys");
		assertFalse(l.stream().anyMatch(x -> x.startsWith("Limite")), "no limit line without a limit");
		s.speedLimit = 3.0;
		List<String> lim = PilotHud.lines(s);
		assertTrue(lim.contains("Limite : 3,0 blocs/s (administrateur)"), lim.toString());
		PilotHud.Status ship = new PilotHud.Status();
		ship.speedLimit = 1.5;
		List<String> sl = PilotHud.lines(ship);
		assertTrue(sl.contains("Limite : 1,5 bloc/s (administrateur)"), sl.toString());
		assertEquals("[Z/S avant/arrière · Q/D barre · Espace/Ctrl allure · Maj quitter]", sl.get(sl.size() - 1), "default: AZERTY names");
	}

	@Test
	void panelOfAShipAndOfTheSubmarine() {
		PilotHud.Status s = new PilotHud.Status();
		s.vessel = "Galère médiévale";
		s.speed = -1.5;
		s.gait = "rapide";
		List<String> l = PilotHud.lines(s);
		assertTrue(l.contains("Vitesse : 1,5 bloc/s en arrière"), l.toString());
		assertTrue(l.contains("Allure : rapide · marche arrière"), l.toString());
		assertFalse(l.stream().anyMatch(x -> x.startsWith("Altitude")), "no altitude on the water");
		PilotHud.Status n = new PilotHud.Status();
		n.kind = PilotHud.Kind.SUBMARINE;
		n.depth = 12.3;
		n.verticalSpeed = -0.6;
		assertTrue(PilotHud.lines(n).contains("Profondeur : 12 m (plonge)"), PilotHud.lines(n).toString());
	}

	@Test
	void panelWhileTheAutopilotFliesToADestination() {
		PilotHud.Status s = airship();
		s.autopilot = true;
		s.autopilotPhase = "SAILING";
		s.autopilotTarget = "Port aérien";
		s.autopilotDistance = 120.4;
		s.autopilotGoto = true;
		s.atHelm = false;
		List<String> l = PilotHud.lines(s);
		assertTrue(l.contains("Pilote auto : en route vers Port aérien (120 blocs)"), l.toString());
		assertEquals("[Clic droit sur la barre : reprendre la main]", l.get(l.size() - 1));
		s.autopilotPhase = "FINISHED";
		assertTrue(PilotHud.lines(s).contains("Pilote auto : arrivé à destination"));
		s.autopilotGoto = false;
		List<String> ferry = PilotHud.lines(s);
		assertFalse(ferry.get(ferry.size() - 1).startsWith("["), "a ferry's autopilot cannot be taken back from the helm");
	}

	@Test
	void engineStateFollowsTheSpeed() {
		PilotHud.Status s = airship();
		double[][] cases = {{2.0, 0}, {3.6, 0}, {3.9, 1}, {6.4, 1}, {6.6, 2}};
		String[] names = {"ralenti", "croisière", "plein régime"};
		for (double[] c : cases) {
			s.speed = c[0];
			assertEquals(names[(int) c[1]], PilotHud.engineState(s), "at " + c[0] + " blocks/s");
		}
	}

	// ------------------------------------------------------------------ goto

	@Test
	void gotoRouteIsAOnePointRouteOfItsOwn() {
		String name = GotoRoutes.routeName("1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809");
		assertEquals("goto-1a2b3c4d", name);
		assertTrue(GotoRoutes.isGoto(name));
		assertFalse(GotoRoutes.isGoto("ferry_capitale"));
		assertFalse(GotoRoutes.isGoto(null));
		Route r = GotoRoutes.build(name, "minecraft:overworld", true, "Port", 100.04, 80.0, -300.06);
		assertEquals(Route.Mode.ONCE, r.mode);
		assertTrue(r.air);
		assertEquals(1, r.size());
		assertFalse(r.get(0).isStop(), "it stops there for good (the end of a once route), it does not wait to leave");
		assertEquals(100.0, r.get(0).x, 1e-9);
		assertEquals(-300.1, r.get(0).z, 1e-9);
		assertEquals("Port", r.get(0).label(0));
		assertEquals("100 80 -300", GotoRoutes.label(100.2, 80.4, -299.6, true));
		assertEquals("100 -300", GotoRoutes.label(100.2, 80.4, -299.6, false));
		assertTrue(GotoRoutes.isGoto("GOTO-port"), "the prefix is reserved in any case");
	}

	@Test
	void whoMayGiveADestination() {
		// admins always may
		assertEquals(null, GotoRoutes.vesselRefusal(true, true, "ferry_capitale", true));
		// a free vessel, or one already on a destination (the player redirects it)
		assertEquals(null, GotoRoutes.vesselRefusal(false, false, null, false));
		assertEquals(null, GotoRoutes.vesselRefusal(false, true, "goto-1a2b3c4d", false));
		assertEquals(null, GotoRoutes.vesselRefusal(false, false, "goto-1a2b3c4d", false), "a paused destination");
		// a ferry: running, paused (its assignment would be lost), or an admin's autopilot without a route
		assertEquals(GotoRoutes.Refusal.FERRY, GotoRoutes.vesselRefusal(false, true, "ferry_capitale", false));
		assertEquals(GotoRoutes.Refusal.PAUSED_FERRY, GotoRoutes.vesselRefusal(false, false, "ferry_capitale", false));
		assertEquals(GotoRoutes.Refusal.FERRY, GotoRoutes.vesselRefusal(false, true, null, false));
		// someone else at the helm
		assertEquals(GotoRoutes.Refusal.HELM_TAKEN, GotoRoutes.vesselRefusal(false, false, null, true));
		assertEquals(GotoRoutes.Refusal.FERRY, GotoRoutes.vesselRefusal(false, true, "ferry_capitale", true), "the ferry first");
		// the destination itself
		assertEquals(null, GotoRoutes.destinationRefusal(false, 999, 1000, false));
		assertEquals(GotoRoutes.Refusal.TOO_FAR, GotoRoutes.destinationRefusal(false, 1001, 1000, false));
		assertEquals(null, GotoRoutes.destinationRefusal(true, 50_000, 1000, false), "no limit for an admin");
		assertEquals(GotoRoutes.Refusal.SUBMARINE, GotoRoutes.destinationRefusal(true, 10, 1000, true), "never the Nautilus");
		assertEquals(GotoRoutes.Refusal.SUBMARINE, GotoRoutes.destinationRefusal(false, 5000, 1000, true));
	}

	@Test
	void aShipSentInlandIsReportedStuckSoItsDestinationIsCancelled() {
		// open sea up to z = 40, land beyond: the destination (z = 90) cannot be reached; the autopilot must report it
		// (ShipEntity then cancels the destination and releases its chunks) instead of trying forever
		ShipType type = Ships.GALLEY;
		ShipGeometry g = type.geometry();
		ShipConfig cfg = type.defaults().get();
		ShipMover.Obstacles coast = (x, y, z) -> z >= 40;
		Autopilot.Navigator sea = (x, z) -> z < 40;
		ShipPose pose = new ShipPose(0, 62, 0, 0);
		Route route = GotoRoutes.build("goto-land", "minecraft:overworld", false, "Prairie", 5, 62, 90);
		Autopilot ap = new Autopilot();
		ap.start(route, pose, cfg, g);
		ShipPhysics physics = new ShipPhysics();
		int[] stuck = {-1};
		int[] tick = {0};
		Autopilot.Listener listener = new Autopilot.Listener() {
			@Override
			public void stuck() {
				if (stuck[0] < 0) {
					stuck[0] = tick[0];
				}
			}
		};
		int collisions = 0;
		for (; tick[0] < 20 * 300 && stuck[0] < 0; tick[0]++) {
			ShipPhysics.Controls c = ap.tick(route, pose, physics.speed, physics.yawRate, Gait.NORMAL, cfg, g, sea, listener);
			ShipPhysics.Step step = physics.step(c, cfg, DT);
			ShipMover.Result r = ShipMover.move(g, pose, step.forward(), step.yaw(), 0, coast);
			physics.collide(r.forwardBlocked(), r.rotationBlocked());
			pose = r.pose();
			collisions += ShipMover.countCollisions(g, pose, coast);
		}
		assertTrue(stuck[0] > 0, "the autopilot reports the unreachable destination (" + ap.phase + " at " + pose + ")");
		assertTrue(stuck[0] < 20 * 180, "within three minutes (" + stuck[0] / 20 + " s)");
		assertEquals(0, collisions, "never on the land");
		assertTrue(ap.phase != Autopilot.Phase.FINISHED, "it did not pretend to arrive");
	}

	/** A world with a height map: everything under ground(x, z) is solid. */
	private record Land(DoubleBinaryOperator ground) implements ShipMover.Obstacles, Flight.Terrain {
		@Override
		public boolean blocked(double x, double y, double z) {
			return y < ground.applyAsDouble(Math.floor(x), Math.floor(z));
		}

		@Override
		public double groundTop(double x, double z) {
			return ground.applyAsDouble(Math.floor(x), Math.floor(z));
		}
	}

	@Test
	void airshipFliesToItsDestinationOverAWallAndLandsThere() {
		ShipType type = Ships.STEAMPUNK_AIRSHIP;
		ShipGeometry g = type.geometry();
		ShipConfig cfg = type.defaults().get();
		// flat ground at 64, a 20 block high wall across the way at z 40..42
		Land land = new Land((x, z) -> z >= 40 && z <= 42 && Math.abs(x) < 30 ? 84 : 64);
		ShipPose pose = new ShipPose(0, 64 + 1.5 - g.lowestY(), 0, 0);
		// destination: on the ground 90 blocks ahead (deck height = ground level: it lands at its clearance)
		Route route = GotoRoutes.build("goto-test", "minecraft:overworld", true, "Pré", 0, 64, 90);
		Autopilot ap = new Autopilot();
		ap.start(route, pose, cfg, g);
		ShipPhysics physics = new ShipPhysics();
		Flight flight = new Flight();
		Autopilot.Listener quiet = new Autopilot.Listener() {
		};
		int collisions = 0;
		double overWall = Double.NEGATIVE_INFINITY;
		int ticks = 0;
		for (; ticks < 20 * 120 && !(ap.phase == Autopilot.Phase.FINISHED && Math.abs(flight.vy) < 0.01 && ticks > 0); ticks++) {
			Flight.Orders o = Flight.autopilot(ap, route, pose, physics, Gait.NORMAL, cfg, g, land, quiet);
			pose = Flight.tick(g, pose, physics, flight, o.controls(), o.desiredVy(), cfg, land, DT).pose();
			collisions += ShipMover.countCollisions(g, pose, land);
			if (Math.abs(pose.z() - 41) < 6) {
				overWall = Math.max(overWall, pose.y() + g.lowestY());
			}
		}
		assertEquals(Autopilot.Phase.FINISHED, ap.phase, "it arrives (after " + ticks / 20 + " s)");
		assertEquals(0, collisions, "never inside the ground or the wall");
		assertTrue(overWall > 84, "it climbed over the wall (keel " + overWall + ")");
		assertTrue(Math.hypot(pose.x(), pose.z() - 90) < cfg.aiStopRadius + 0.5, "it stops at the destination: " + pose);
		double keel = pose.y() + g.lowestY();
		assertEquals(64 + cfg.flight.aiLandingClearance, keel, 0.15, "it comes down to its landing clearance over the ground");
		assertEquals(0, physics.speed, 0.05, "and stays there");
	}

	@Test
	void shipSailsToItsDestinationAndStops() {
		ShipType type = Ships.GALLEY;
		ShipGeometry g = type.geometry();
		ShipConfig cfg = type.defaults().get();
		ShipMover.Obstacles sea = (x, y, z) -> false;
		Autopilot.Navigator open = (x, z) -> true;
		ShipPose pose = new ShipPose(0, 62, 0, 0);
		Route route = GotoRoutes.build("goto-sea", "minecraft:overworld", false, "Crique", 40, 62, 70);
		Autopilot ap = new Autopilot();
		ap.start(route, pose, cfg, g);
		ShipPhysics physics = new ShipPhysics();
		Autopilot.Listener quiet = new Autopilot.Listener() {
		};
		for (int i = 0; i < 20 * 120 && ap.phase != Autopilot.Phase.FINISHED; i++) {
			ShipPhysics.Controls c = ap.tick(route, pose, physics.speed, physics.yawRate, Gait.NORMAL, cfg, g, open, quiet);
			ShipPhysics.Step step = physics.step(c, cfg, DT);
			ShipMover.Result r = ShipMover.move(g, pose, step.forward(), step.yaw(), 0, sea);
			physics.collide(r.forwardBlocked(), r.rotationBlocked());
			pose = r.pose();
		}
		assertEquals(Autopilot.Phase.FINISHED, ap.phase);
		assertTrue(Math.hypot(pose.x() - 40, pose.z() - 70) < cfg.aiStopRadius + 0.5, "at the destination: " + pose);
	}

	// ------------------------------------------------------------------ placement

	@Test
	void earlyExitSpaceCheckAgreesWithTheCount() {
		Random rnd = new Random(7);
		for (ShipType t : Ships.ALL) {
			for (int i = 0; i < 40; i++) {
				double gx = rnd.nextDouble() * 6, gz = rnd.nextDouble() * 6;
				ShipMover.Obstacles world = (x, y, z) -> y < 60 + 3 * Math.sin(x / gx - z / gz);
				ShipPose pose = new ShipPose(rnd.nextDouble() * 50, 58 + rnd.nextDouble() * 12, rnd.nextDouble() * 50, rnd.nextDouble() * 360);
				assertEquals(ShipMover.countCollisions(t.geometry(), pose, world) > 0, ShipMover.collides(t.geometry(), pose, world), t.id());
			}
		}
	}
}
