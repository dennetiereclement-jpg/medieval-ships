package fr.medievalships.test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestDedicatedServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerConnection;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.entity.Entity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;

import fr.medievalships.core.HullProfile;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.Ships.GalleonLayout;
import fr.medievalships.core.Ships.WarshipLayout;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * Real client test: a player falls, jumps and walks on the deck, jumps aboard from a quay,
 * a mob stands on the deck, and the ship is steered with everything aboard (galley); then the
 * great galleon: decks, cabin, balcony, stairs, 16 seats, heavy handling and carrying.
 * Results are written to run/medievalships-test.txt, screenshots to the screenshot folder.
 */
public class ShipClientGameTest implements FabricClientGameTest {
	private final List<String> report = new ArrayList<>();
	private final List<String> failures = new ArrayList<>();

	/** Where the scenario runs: the integrated server of a solo world, or a real dedicated server. */
	private record Env(TestServerContext getServer, TestClientWorldContext getClientWorld) {
	}

	private String tag = "";

	@Override
	public void runTest(ClientGameTestContext context) {
		log("lithium installed: %s", net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("lithium"));
		try (TestSingleplayerContext sp = context.worldBuilder().create()) {
			tag = "solo";
			scenario(context, new Env(sp.getServer(), sp.getClientWorld()));
		} catch (Throwable t) {
			fail("solo: exception: " + t);
		}
		// same scenario on a dedicated server, the client connected over the network (like a real server)
		try {
			Files.writeString(Path.of("eula.txt"), "eula=true\n");
		} catch (IOException e) {
			fail("dedie: cannot write eula.txt: " + e);
		}
		try (TestDedicatedServerContext ds = context.worldBuilder().createServer();
				TestServerConnection connection = ds.connect()) {
			tag = "dedie";
			scenario(context, new Env(ds, connection.getClientWorld()));
		} catch (Throwable t) {
			fail("dedie: exception: " + t);
		}
		finish(context);
	}

	private void scenario(ClientGameTestContext context, Env sp) {
		{
			var server = sp.getServer();
			log("world loaded");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doWeatherCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			server.runCommand("weather clear");
			// a basin of water 5 blocks deep, open sky above
			server.runCommand("fill -14 -63 -26 14 -50 26 air");
			server.runCommand("fill -14 -63 -26 14 -59 26 water");
			// a stone quay along the starboard side... of the basin (east)
			server.runCommand("fill 4 -63 -6 7 -58 6 stone");
			server.runCommand("execute positioned 0 -58 0 rotated 0 0 run ship spawn");
			sp.getClientWorld().waitForChunksRender();
			context.waitTicks(40);

			ShipPose pose = shipPose(sp);
			if (pose == null) {
				fail("ship was not spawned");
				return;
			}
			log("ship at %.2f %.2f %.2f yaw %.1f", pose.x(), pose.y(), pose.z(), pose.yaw());
			double deckY = pose.y() + HullProfile.MAIN_DECK_Y;
			log("expected main deck top %.3f", deckY);

			// overview screenshots
			server.runCommand("gamemode spectator @a");
			server.runCommand("tp @p 16 -50 -16 45 25");
			context.waitTicks(30);
			shot(context, "01_overview");
			server.runCommand("tp @p -13 -55 3 -100 8");
			context.waitTicks(20);
			shot(context, "02_side");
			server.runCommand("tp @p 2 -50 22 160 30");
			context.waitTicks(20);
			shot(context, "02b_bow");
			server.runCommand("gamemode survival @a");
			server.runCommand("effect give @a minecraft:resistance infinite 4 true");
			server.runCommand("effect give @a minecraft:saturation infinite 4 true");
			server.runCommand("effect give @a minecraft:water_breathing infinite 0 true");

			// 1. falling onto the deck
			server.runCommand("tp @p 1.5 -53 -3 0 30");
			context.waitTicks(60);
			double[] p = playerPos(context);
			log("after drop: player y=%.3f onGround=%s", p[1], p[3] > 0);
			check(Math.abs(p[1] - deckY) < 0.08, "falling: player should stand on the deck (y=%.3f, deck=%.3f)", p[1], deckY);
			shot(context, "03_on_deck_first_person");
			context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
			context.waitTicks(5);
			shot(context, "04_on_deck_third_person");
			context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

			// 2. jumping on the deck
			double minY = Double.MAX_VALUE;
			for (int i = 0; i < 3; i++) {
				context.getInput().holdKeyFor(o -> o.jumpKey, 2);
				for (int t = 0; t < 14; t++) {
					context.waitTick();
					minY = Math.min(minY, playerPos(context)[1]);
				}
			}
			context.waitTicks(20);
			p = playerPos(context);
			log("after jumps: y=%.3f, lowest=%.3f", p[1], minY);
			check(Math.abs(p[1] - deckY) < 0.08 && minY > deckY - 0.1, "jumping: player must land back on the deck (y=%.3f min=%.3f)", p[1], minY);

			// 3. walking to the bow (step onto the raised fore deck, stopped by the bow walls)
			context.getInput().holdKeyFor(o -> o.forwardKey, 80);
			context.waitTicks(10);
			p = playerPos(context);
			double[] l = shipPose(sp).toLocal(p[0], p[1], p[2]);
			log("after walking forward: local x=%.2f y=%.2f z=%.2f", l[0], l[1], l[2]);
			check(fr.medievalships.core.Ships.GALLEY.geometry().inCarryVolume(l[0], l[1], l[2]) && l[1] > HullProfile.MAIN_DECK_Y - 0.1,
					"walking: player must still be aboard (local %.2f %.2f %.2f)", l[0], l[1], l[2]);
			check(l[2] > HullProfile.FORE_DECK_START, "walking: player should have climbed onto the fore deck (z=%.2f)", l[2]);
			shot(context, "05_at_the_bow");

			// 4. jumping aboard from the quay
			server.runCommand("tp @p 6.5 -57 0 90 10");
			context.waitTicks(30);
			// run-up and a single jump over the rail, then stop
			context.getInput().holdKey(o -> o.sprintKey);
			context.getInput().holdKey(o -> o.forwardKey);
			context.waitTicks(6);
			context.getInput().holdKey(o -> o.jumpKey);
			for (int t = 0; t < 20; t++) {
				context.waitTick();
				if (t == 1) {
					context.getInput().releaseKey(o -> o.jumpKey);
				}
				double[] q = playerPos(context);
				double[] ql = pose.toLocal(q[0], q[1], q[2]);
				log("  jump tick %d: local x=%.3f y=%.3f ground=%s", t, ql[0], ql[1], q[3] > 0);
				if (t == 14) {
					context.getInput().releaseKey(o -> o.forwardKey);
				}
			}
			context.getInput().releaseKey(o -> o.sprintKey);
			context.getInput().releaseKey(o -> o.forwardKey);
			context.waitTicks(30);
			p = playerPos(context);
			l = shipPose(sp).toLocal(p[0], p[1], p[2]);
			log("after jumping from the quay: local x=%.2f y=%.2f z=%.2f", l[0], l[1], l[2]);
			check(fr.medievalships.core.Ships.GALLEY.geometry().inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - HullProfile.deckY(l[2])) < 0.1,
					"quay: player should have landed on the deck (local %.2f %.2f %.2f)", l[0], l[1], l[2]);
			shot(context, "06_jumped_from_quay");

			// 5. a mob on the deck (server-side collisions)
			server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"deckmob\"]}",
					pose.worldX(0.8, 3), deckY + 3, pose.worldZ(0.8, 3)));
			context.waitTicks(60);
			double[] z = mobPos(sp);
			log("zombie at y=%.3f", z == null ? Double.NaN : z[1]);
			check(z != null && Math.abs(z[1] - deckY) < 0.08, "mob: armor stand should stand on the deck");

			// 5b. swimming up under the hull must not get inside it
			server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f 0 -60", pose.worldX(0.6, -2), pose.y() - 3.5, pose.worldZ(0.6, -2)));
			context.waitTicks(10);
			context.getInput().holdKey(o -> o.jumpKey);
			double maxY = -1e9;
			for (int t = 0; t < 60; t++) {
				context.waitTick();
				maxY = Math.max(maxY, playerPos(context)[1]);
			}
			context.getInput().releaseKey(o -> o.jumpKey);
			shot(context, "06b_under_the_hull");
			double hullBottom = pose.y() + HullProfile.bottomY(-2, 0.6);
			log("swimming up under the hull: highest head y=%.3f, hull bottom=%.3f", maxY + 1.8, hullBottom);
			check(maxY + 1.8 <= hullBottom + 0.05, "under the hull: the swimmer must be stopped by the hull bottom");
			server.runCommand("tp @p 1.5 -55 -3 0 30");
			context.waitTicks(40);

			// 6. steering with the player at the helm: the zombie must be carried
			sp.getServer().runOnServer(server2 -> {
				ServerPlayerEntity player = server2.getPlayerManager().getPlayerList().get(0);
				ShipEntity ship = ship(server2.getOverworld());
				if (ship != null) {
					ship.seat(player, ShipGeometry.PILOT_SEAT);
				}
			});
			context.waitTicks(10);
			ShipPose start = shipPose(sp);
			context.getInput().holdKey(o -> o.forwardKey);
			context.waitTicks(80);
			context.getInput().releaseKey(o -> o.forwardKey);
			context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
			context.waitTicks(10);
			shot(context, "07_sailing");
			context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
			ShipPose moved = shipPose(sp);
			double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
			log("ship moved %.2f blocks under player control", dist);
			check(dist > 2, "steering: the ship should move forward (moved %.2f)", dist);
			z = mobPos(sp);
			if (z != null) {
				double[] zl = moved.toLocal(z[0], z[1], z[2]);
				log("zombie local after sailing: %.2f %.2f %.2f", zl[0], zl[1], zl[2]);
				check(fr.medievalships.core.Ships.GALLEY.geometry().inCarryVolume(zl[0], zl[1], zl[2]), "carry: zombie should still be aboard");
			}
			galleon(context, sp);
			warship(context, sp);
			for (ShipType type : NEW_SHIPS) {
				newShip(context, sp, type);
			}
			airship(context, sp);
			nautilus(context, sp);
		}
	}

	// ------------------------------------------------------------------ great galleon

	private void galleon(ClientGameTestContext context, Env sp) {
		var server = sp.getServer();
		ShipGeometry g = Ships.GALLEON.geometry();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		// a large basin east of the first one (the galleon is 43 blocks long with its bowsprit)
		server.runCommand("fill 30 -63 -40 62 -59 70 water");
		server.runCommand("tp @p 46 -40 20 180 40");
		context.waitTicks(20);
		server.runCommand("execute positioned 46 -58 -8 rotated 0 0 run ship spawn galleon");
		sp.getClientWorld().waitForChunksRender();
		context.waitTicks(40);
		ShipPose pose = shipPose(sp, Ships.GALLEON);
		if (pose == null) {
			fail("galleon: not spawned");
			return;
		}
		log("galleon at %.2f %.2f %.2f yaw %.1f", pose.x(), pose.y(), pose.z(), pose.yaw());
		Boolean galleyStillThere = server.computeOnServer(s -> ship(s.getOverworld(), Ships.GALLEY) != null);
		check(Boolean.TRUE.equals(galleyStillThere), "galleon: the galley is still there (both ships coexist)");
		double main = pose.y() + GalleonLayout.MAIN_DECK_Y;

		// screenshots (sails furl once the ship has been stopped for 5 s: take both states)
		lookLocal(server, pose, 26, 16, 24, 0, 6, 0);
		context.waitTicks(30);
		shot(context, "g01_galleon_overview");
		lookLocal(server, pose, -34, 7, 2, 0, 7, 2);
		context.waitTicks(20);
		shot(context, "g02_galleon_side");
		lookLocal(server, pose, -9, 6, -31, 0, 3, -16);
		context.waitTicks(20);
		shot(context, "g03_galleon_stern");
		lookLocal(server, pose, 10, 9, 34, 0, 5, 15);
		context.waitTicks(20);
		shot(context, "g04_galleon_bow");

		server.runCommand("gamemode survival @a");
		// 1. falling onto the main deck, then jumping
		tpLocal(server, pose, 1.5, 4, 3, 0, 30);
		context.waitTicks(60);
		double[] p = playerPos(context);
		double[] l = pose.toLocal(p[0], p[1], p[2]);
		check(Math.abs(p[1] - main) < 0.08, "galleon falling: player on the main deck (y=%.3f, deck=%.3f)", p[1], main);
		double minY = Double.MAX_VALUE;
		for (int i = 0; i < 3; i++) {
			context.getInput().holdKeyFor(o -> o.jumpKey, 2);
			for (int t = 0; t < 14; t++) {
				context.waitTick();
				minY = Math.min(minY, playerPos(context)[1]);
			}
		}
		context.waitTicks(20);
		p = playerPos(context);
		check(Math.abs(p[1] - main) < 0.08 && minY > main - 0.1, "galleon jumping: back on the deck (y=%.3f min=%.3f)", p[1], minY);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, "g05_galleon_deck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 2. into the great cabin through the bulkhead door
		l = walkLocal(context, sp, Ships.GALLEON, pose, 0, GalleonLayout.MAIN_DECK_Y, -6.0, 180, 0, 30);
		log("galleon cabin: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(l[2] < GalleonLayout.BULKHEAD_Z - 1.5 && Math.abs(l[1] - GalleonLayout.MAIN_DECK_Y) < 0.1,
				"galleon cabin: player walked into the cabin (local z=%.2f y=%.2f)", l[2], l[1]);
		shot(context, "g06_galleon_cabin");

		// 3. through the transom door onto the stern balcony
		l = walkLocal(context, sp, Ships.GALLEON, pose, 0, GalleonLayout.MAIN_DECK_Y, -15.0, 180, 0, 40);
		log("galleon balcony: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(l[2] < -g.hull().halfLength && l[2] > GalleonLayout.BALCONY_BACK && Math.abs(l[1] - GalleonLayout.MAIN_DECK_Y) < 0.1,
				"galleon balcony: player on the balcony, held by the balustrade (local z=%.2f y=%.2f)", l[2], l[1]);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(5);
		shot(context, "g07_galleon_balcony");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 4. up the stairs to the quarterdeck, and to the forecastle
		double qx = (GalleonLayout.STAIR_X0 + GalleonLayout.STAIR_X1) / 2;
		l = walkLocal(context, sp, Ships.GALLEON, pose, qx, GalleonLayout.MAIN_DECK_Y, -5.0, 180, 0, 50);
		log("galleon quarterdeck: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(Math.abs(l[1] - GalleonLayout.QUARTERDECK_Y) < 0.1 && l[2] < GalleonLayout.BULKHEAD_Z,
				"galleon stairs: player climbed onto the quarterdeck (local y=%.2f z=%.2f)", l[1], l[2]);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, "g08_galleon_quarterdeck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		double fx = (GalleonLayout.FC_STAIR_X0 + GalleonLayout.FC_STAIR_X1) / 2;
		l = walkLocal(context, sp, Ships.GALLEON, pose, fx, GalleonLayout.MAIN_DECK_Y, 7.6, 0, 0, 40);
		log("galleon forecastle: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(Math.abs(l[1] - GalleonLayout.FORECASTLE_Y) < 0.1 && l[2] > GalleonLayout.FORECASTLE_START,
				"galleon stairs: player climbed onto the forecastle (local y=%.2f z=%.2f)", l[1], l[2]);

		// 5. sixteen seats: 15 armor stands + the player at the helm; a 17th passenger is refused
		for (int i = 1; i < 16; i++) {
			ShipGeometry.Seat seat = g.seats().get(i);
			double[] w = pose.toWorld(seat.x(), seat.y() + 0.5, seat.z());
			server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"crew\",\"crew%d\"]}",
					w[0], w[1], w[2], i));
		}
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"extra\"]}",
				pose.worldX(-2, 2), main + 1, pose.worldZ(-2, 2)));
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"deckmob\",\"galleonmob\"]}",
				pose.worldX(2.2, 1.5), main + 2, pose.worldZ(2.2, 1.5)));
		context.waitTicks(20);
		int[] seated = server.computeOnServer(s -> {
			ShipEntity ship = ship(s.getOverworld(), Ships.GALLEON);
			ServerPlayerEntity player = s.getPlayerManager().getPlayerList().get(0);
			List<Entity> all = new ArrayList<>();
			s.getOverworld().iterateEntities().forEach(all::add);
			int ok = 0;
			for (Entity e : all) {
				for (int i = 1; i < 16; i++) {
					if (e.getCommandTags().contains("crew" + i) && ship.seat(e, i)) {
						ok++;
					}
				}
			}
			boolean pilot = ship.seat(player, ShipGeometry.PILOT_SEAT);
			int refused = 0;
			for (Entity e : all) {
				if (e.getCommandTags().contains("extra")) {
					for (int i = 0; i < 16; i++) {
						if (!ship.seat(e, i)) {
							refused++;
						}
					}
					refused += e.startRiding(ship) ? 0 : 1;
				}
			}
			return new int[] {ok, pilot ? 1 : 0, ship.getPassengerList().size(), refused};
		});
		log("galleon seats: %d crew seated, pilot %d, passengers %d, refusals %d/17", seated[0], seated[1], seated[2], seated[3]);
		check(seated[0] == 15 && seated[1] == 1 && seated[2] == 16, "galleon seats: 16 passengers seated (%d + %d)", seated[0], seated[1]);
		check(seated[3] == 17, "galleon seats: a 17th passenger is refused");
		context.waitTicks(10);

		// 6. heavy handling: slow to gather way, keeps going once the helm is released, wide turns
		ShipPose start = shipPose(sp, Ships.GALLEON);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(40);
		ShipPose after2s = shipPose(sp, Ships.GALLEON);
		context.waitTicks(120);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose released = shipPose(sp, Ships.GALLEON);
		float speedAtRelease = server.computeOnServer(s -> ship(s.getOverworld(), Ships.GALLEON).syncedSpeed());
		context.getInput().holdKey(o -> o.rightKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.rightKey);
		ShipPose coasted = shipPose(sp, Ships.GALLEON);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(10);
		shot(context, "g09_galleon_sailing");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		double d2 = Math.hypot(after2s.x() - start.x(), after2s.z() - start.z());
		double d8 = Math.hypot(released.x() - start.x(), released.z() - start.z());
		double glide = Math.hypot(coasted.x() - released.x(), coasted.z() - released.z());
		double turned = Math.abs(ShipPose.wrapDegrees(coasted.yaw() - released.yaw()));
		log("galleon handling: %.2f blocks in 2 s, %.2f in 8 s, speed %.2f, %.2f blocks coasting in 4 s while turning %.1f deg",
				d2, d8, speedAtRelease, glide, turned);
		check(d2 < 1.5 && d8 > 4, "galleon handling: slow acceleration (%.2f in 2 s, %.2f in 8 s)", d2, d8);
		check(glide > 3, "galleon handling: inertia, keeps going without power (%.2f)", glide);
		check(turned > 2 && turned < 40, "galleon handling: turns, but slowly (%.1f deg in 4 s)", turned);
		int still = server.computeOnServer(s -> ship(s.getOverworld(), Ships.GALLEON).getPassengerList().size());
		check(still == 16, "galleon carry: the 16 passengers are still seated (%d)", still);
		double[] m = server.computeOnServer(s -> {
			for (Entity e : s.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("galleonmob")) {
					return new double[] {e.getX(), e.getY(), e.getZ()};
				}
			}
			return null;
		});
		if (m != null) {
			double[] ml = coasted.toLocal(m[0], m[1], m[2]);
			log("galleon deck mob local after sailing: %.2f %.2f %.2f", ml[0], ml[1], ml[2]);
			check(g.inCarryVolume(ml[0], ml[1], ml[2]) && Math.abs(ml[1] - GalleonLayout.MAIN_DECK_Y) < 0.1,
					"galleon carry: the mob standing on deck is carried");
		} else {
			fail("galleon carry: deck mob missing");
		}
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		p = playerPos(context);
		ShipPose now = shipPose(sp, Ships.GALLEON);
		l = now.toLocal(p[0], p[1], p[2]);
		check(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - GalleonLayout.QUARTERDECK_Y) < 0.15,
				"galleon dismount: the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", l[0], l[1], l[2]);
		// sails are still set for a few seconds after stopping: look at them from outside
		server.runCommand("gamemode spectator @a");
		lookLocal(server, now, 24, 13, 20, 0, 10, 1);
		context.waitTicks(15);
		shot(context, "g10_galleon_sails_set");
		lookLocal(server, now, -6, 9, 30, 0, 9, 4);
		context.waitTicks(10);
		shot(context, "g11_galleon_sails_front");
		server.runCommand("gamemode survival @a");
		// safety nets: collisions switched off (as if another mod had replaced them), the player
		// must still be caught by the deck when falling onto it from high above
		fr.medievalships.entity.ShipCollisions.disableForTest(true);
		try {
			for (int k = 0; k < 2; k++) {
				ShipPose sp2 = shipPose(sp, Ships.GALLEON);
				double dropZ = k == 0 ? 3 : -12;
				double surface = k == 0 ? GalleonLayout.MAIN_DECK_Y : GalleonLayout.QUARTERDECK_Y;
				tpLocal(server, sp2, -1.5, surface + 9, dropZ, 0, 20);
				context.waitTicks(60);
				double[] q = playerPos(context);
				double[] ql = shipPose(sp, Ships.GALLEON).toLocal(q[0], q[1], q[2]);
				log("no collisions, drop %d: local %.2f %.2f %.2f", k, ql[0], ql[1], ql[2]);
				check(Math.abs(ql[1] - surface) < 0.15, "safety net: without collisions the player is still caught by the %s (local y=%.2f)",
						k == 0 ? "main deck" : "quarterdeck", ql[1]);
			}
		} finally {
			fr.medievalships.entity.ShipCollisions.disableForTest(false);
		}

		server.runCommand("clear @a");
		server.runCommand("ship give galleon @p");
		Integer items = server.computeOnServer(s ->
				s.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.GALLEON_ITEM));
		check(items != null && items == 1, "galleon item: /ship give galleon gives the item (%s)", items);
	}

	// ------------------------------------------------------------------ great warship

	private void warship(ClientGameTestContext context, Env sp) {
		var server = sp.getServer();
		ShipGeometry g = Ships.WARSHIP.geometry();
		server.runCommand("ride @p dismount");
		// checked here, while the first two ships are still in loaded chunks (150 blocks away
		// from the third basin, a solo world unloads them normally)
		Boolean others = server.computeOnServer(s -> ship(s.getOverworld(), Ships.GALLEY) != null && ship(s.getOverworld(), Ships.GALLEON) != null);
		check(Boolean.TRUE.equals(others), "warship: the galley and the galleon are still there before the third ship is launched");
		server.runCommand("gamemode spectator @a");
		// a third, larger basin west of the others (the warship is about 67 blocks long overall)
		server.runCommand("tp @p -90 -30 10 180 40");
		context.waitTicks(40);
		server.runCommand("fill -110 -63 -60 -70 -59 80 water");
		server.runCommand("execute positioned -90 -58 -20 rotated 0 0 run ship spawn warship");
		sp.getClientWorld().waitForChunksRender();
		context.waitTicks(40);
		ShipPose pose = shipPose(sp, Ships.WARSHIP);
		if (pose == null) {
			fail("warship: not spawned");
			return;
		}
		log("warship at %.2f %.2f %.2f yaw %.1f", pose.x(), pose.y(), pose.z(), pose.yaw());
		double main = pose.y() + WarshipLayout.MAIN_DECK_Y;

		lookLocal(server, pose, 40, 22, 34, 0, 12, 0);
		context.waitTicks(30);
		shot(context, "w01_warship_overview");
		lookLocal(server, pose, -50, 10, 4, 0, 10, 4);
		context.waitTicks(20);
		shot(context, "w02_warship_side");
		lookLocal(server, pose, -14, 11, -50, 0, 7, -26);
		context.waitTicks(20);
		shot(context, "w03_warship_stern");
		lookLocal(server, pose, 16, 12, 52, 0, 8, 26);
		context.waitTicks(20);
		shot(context, "w04_warship_bow");

		server.runCommand("gamemode survival @a");
		// 1. main deck: fall and jumps
		tpLocal(server, pose, 2.0, WarshipLayout.MAIN_DECK_Y + 5, 5.5, 0, 30);
		context.waitTicks(60);
		double[] p = playerPos(context);
		check(Math.abs(p[1] - main) < 0.08, "warship falling: player on the main deck (y=%.3f, deck=%.3f)", p[1], main);
		double minY = Double.MAX_VALUE;
		for (int i = 0; i < 3; i++) {
			context.getInput().holdKeyFor(o -> o.jumpKey, 2);
			for (int t = 0; t < 14; t++) {
				context.waitTick();
				minY = Math.min(minY, playerPos(context)[1]);
			}
		}
		context.waitTicks(20);
		p = playerPos(context);
		check(Math.abs(p[1] - main) < 0.08 && minY > main - 0.1, "warship jumping: back on the deck (y=%.3f min=%.3f)", p[1], minY);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, "w05_warship_deck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 2. great cabin through the bulkhead door
		double[] l = walkLocal(context, sp, Ships.WARSHIP, pose, 0, WarshipLayout.MAIN_DECK_Y, -8.0, 180, 0, 30);
		log("warship cabin: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(l[2] < WarshipLayout.QUARTERDECK_START - 2 && Math.abs(l[1] - WarshipLayout.MAIN_DECK_Y) < 0.1,
				"warship cabin: player walked into the great cabin (local z=%.2f y=%.2f)", l[2], l[1]);
		shot(context, "w06_warship_cabin");

		// 3. main deck -> quarterdeck -> poop deck by the two staircases, then the forecastle
		double qx = (WarshipLayout.QD_STAIR_X0 + WarshipLayout.POOP_STAIR_X1) / 2;
		l = walkLocal(context, sp, Ships.WARSHIP, pose, qx, WarshipLayout.MAIN_DECK_Y, -6.8, 180, 0, 70);
		log("warship poop deck: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(Math.abs(l[1] - WarshipLayout.POOP_Y) < 0.1 && l[2] < WarshipLayout.POOP_START,
				"warship stairs: player climbed to the quarterdeck then the poop deck (local y=%.2f z=%.2f)", l[1], l[2]);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(5);
		shot(context, "w07_warship_poop_deck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		double fx = (WarshipLayout.FC_STAIR_X0 + WarshipLayout.FC_STAIR_X1) / 2;
		l = walkLocal(context, sp, Ships.WARSHIP, pose, fx, WarshipLayout.MAIN_DECK_Y, 13.8, 0, 0, 40);
		log("warship forecastle: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(Math.abs(l[1] - WarshipLayout.FORECASTLE_Y) < 0.1 && l[2] > WarshipLayout.FORECASTLE_START,
				"warship stairs: player climbed onto the forecastle (local y=%.2f z=%.2f)", l[1], l[2]);

		// 4. twenty-four seats: 23 armor stands + the player at the helm; a 25th is refused
		int n = g.seats().size();
		for (int i = 1; i < n; i++) {
			ShipGeometry.Seat seat = g.seats().get(i);
			double[] w = pose.toWorld(seat.x(), seat.y() + 0.5, seat.z());
			server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"wcrew\",\"wcrew%d\"]}",
					w[0], w[1], w[2], i));
		}
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"wextra\"]}",
				pose.worldX(-1.5, 3), main + 1, pose.worldZ(-1.5, 3)));
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"warshipmob\"]}",
				pose.worldX(1.5, -2.0), main + 2, pose.worldZ(1.5, -2.0)));
		context.waitTicks(20);
		int[] seated = server.computeOnServer(s -> {
			ShipEntity ship = ship(s.getOverworld(), Ships.WARSHIP);
			ServerPlayerEntity player = s.getPlayerManager().getPlayerList().get(0);
			List<Entity> all = new ArrayList<>();
			s.getOverworld().iterateEntities().forEach(all::add);
			int ok = 0;
			for (Entity e : all) {
				for (int i = 1; i < n; i++) {
					if (e.getCommandTags().contains("wcrew" + i) && ship.seat(e, i)) {
						ok++;
					}
				}
			}
			boolean pilot = ship.seat(player, ShipGeometry.PILOT_SEAT);
			int refused = 0;
			for (Entity e : all) {
				if (e.getCommandTags().contains("wextra")) {
					refused += e.startRiding(ship) ? 0 : 1;
				}
			}
			return new int[] {ok, pilot ? 1 : 0, ship.getPassengerList().size(), refused};
		});
		log("warship seats: %d crew seated, pilot %d, passengers %d, refusals %d", seated[0], seated[1], seated[2], seated[3]);
		check(seated[0] == n - 1 && seated[1] == 1 && seated[2] == 24, "warship seats: 24 passengers seated (%d + %d)", seated[0], seated[1]);
		check(seated[3] == 1, "warship seats: a 25th passenger is refused");
		context.waitTicks(10);

		// 5. very heavy handling
		ShipPose start = shipPose(sp, Ships.WARSHIP);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(40);
		ShipPose after2s = shipPose(sp, Ships.WARSHIP);
		context.waitTicks(160);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose released = shipPose(sp, Ships.WARSHIP);
		context.getInput().holdKey(o -> o.rightKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.rightKey);
		ShipPose coasted = shipPose(sp, Ships.WARSHIP);
		double d2 = Math.hypot(after2s.x() - start.x(), after2s.z() - start.z());
		double d10 = Math.hypot(released.x() - start.x(), released.z() - start.z());
		double glide = Math.hypot(coasted.x() - released.x(), coasted.z() - released.z());
		double turned = Math.abs(ShipPose.wrapDegrees(coasted.yaw() - released.yaw()));
		log("warship handling: %.2f blocks in 2 s, %.2f in 10 s, %.2f coasting in 4 s while turning %.1f deg", d2, d10, glide, turned);
		check(d2 < 1.0 && d10 > 4, "warship handling: very slow acceleration (%.2f in 2 s, %.2f in 10 s)", d2, d10);
		check(glide > 3, "warship handling: strong inertia (%.2f)", glide);
		check(turned > 1 && turned < 30, "warship handling: wide, slow turns (%.1f deg in 4 s)", turned);
		int still = server.computeOnServer(s -> ship(s.getOverworld(), Ships.WARSHIP).getPassengerList().size());
		check(still == 24, "warship carry: the 24 passengers are still seated (%d)", still);
		double[] m = server.computeOnServer(s -> {
			for (Entity e : s.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("warshipmob")) {
					return new double[] {e.getX(), e.getY(), e.getZ()};
				}
			}
			return null;
		});
		if (m != null) {
			double[] ml = coasted.toLocal(m[0], m[1], m[2]);
			log("warship deck mob local after sailing: %.2f %.2f %.2f", ml[0], ml[1], ml[2]);
			check(g.inCarryVolume(ml[0], ml[1], ml[2]) && Math.abs(ml[1] - WarshipLayout.MAIN_DECK_Y) < 0.1,
					"warship carry: the mob standing on deck is carried");
		} else {
			fail("warship carry: deck mob missing");
		}
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		p = playerPos(context);
		ShipPose now = shipPose(sp, Ships.WARSHIP);
		l = now.toLocal(p[0], p[1], p[2]);
		check(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - WarshipLayout.QUARTERDECK_Y) < 0.15,
				"warship dismount: the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", l[0], l[1], l[2]);
		server.runCommand("gamemode spectator @a");
		lookLocal(server, now, 42, 20, 36, 0, 16, 2);
		context.waitTicks(15);
		shot(context, "w08_warship_sails_set");
		server.runCommand("gamemode survival @a");

		// 6. safety net with the collisions switched off
		fr.medievalships.entity.ShipCollisions.disableForTest(true);
		try {
			for (int k = 0; k < 2; k++) {
				ShipPose sp2 = shipPose(sp, Ships.WARSHIP);
				double surface = k == 0 ? WarshipLayout.MAIN_DECK_Y : WarshipLayout.POOP_Y;
				tpLocal(server, sp2, -1.5, surface + 9, k == 0 ? 5.5 : -23.5, 0, 20);
				context.waitTicks(60);
				double[] q = playerPos(context);
				double[] ql = shipPose(sp, Ships.WARSHIP).toLocal(q[0], q[1], q[2]);
				check(Math.abs(ql[1] - surface) < 0.15, "warship safety net: without collisions the player is still caught by the %s (local y=%.2f)",
						k == 0 ? "main deck" : "poop deck", ql[1]);
			}
		} finally {
			fr.medievalships.entity.ShipCollisions.disableForTest(false);
		}
		server.runCommand("clear @a");
		server.runCommand("ship give warship @p");
		Integer items = server.computeOnServer(s ->
				s.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.WARSHIP_ITEM));
		check(items != null && items == 1, "warship item: /ship give warship gives the item (%s)", items);
	}

	/** Ships added after the warship: the same scenario for each, one after the other in a fourth basin. */
	private static final List<ShipType> NEW_SHIPS = List.of(Ships.MEDIEVAL_GALLEY, Ships.STEAM_PADDLEBOAT, Ships.ELVEN_SAILBOAT);

	private void newShip(ClientGameTestContext context, Env sp, ShipType type) {
		var server = sp.getServer();
		String id = type.id();
		ShipGeometry g = type.geometry();
		fr.medievalships.core.HullShape h = g.hull();
		server.runCommand("ride @p dismount");
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=ncrew]");
		server.runCommand("gamemode spectator @a");
		// fourth basin, north of the others: 44 x 100 blocks, 5 deep
		server.runCommand("tp @p -42 -40 112 0 40");
		context.waitTicks(40);
		server.runCommand("fill -64 -63 100 -20 -59 200 water");
		server.runCommand("execute positioned -42 -58 125 rotated 0 0 run ship spawn " + id);
		sp.getClientWorld().waitForChunksRender();
		context.waitTicks(40);
		ShipPose pose = shipPose(sp, type);
		if (pose == null) {
			fail(id + ": not spawned");
			return;
		}
		log("%s at %.2f %.2f %.2f yaw %.1f", id, pose.x(), pose.y(), pose.z(), pose.yaw());
		double water = pose.y() + h.waterlineY;
		check(water > -58.3 && water < -57.7, "%s floats: water line at y=%.2f (basin surface -58)", id, water);
		double deck = pose.y() + h.mainDeckY;

		// the six views of the reference picture, sails set (they furl after 5 s stopped otherwise)
		boolean furl = server.computeOnServer(s -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(type);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		double L = h.tip, top = Math.max(8, L * 0.5);
		String[][] views = {{"1_droite"}, {"2_gauche"}, {"3_proue"}, {"4_poupe"}, {"5_dessus"}, {"6_perspective"}};
		double[][] eyes = {{-1.75 * L, 0.4 * top, 0.2}, {1.75 * L, 0.4 * top, 0.2}, {0.4, 0.45 * top, 1.9 * L},
				{0.4, 0.45 * top, -1.9 * L}, {0.01, 2.5 * L, 0.0}, {1.25 * L, 0.75 * top, 1.3 * L}};
		for (int k = 0; k < views.length; k++) {
			lookLocal(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], 0, k == 4 ? 0 : 0.4 * top, 0);
			context.waitTicks(k == 0 ? 30 : 15);
			shot(context, id + "_" + views[k][0]);
		}
		server.runOnServer(s -> fr.medievalships.data.ConfigManager.ship(type).furlSailWhenStopped = furl);

		server.runCommand("gamemode survival @a");
		// 1. falling onto the deck (a free spot by the side: amidships may be a deckhouse), jumping
		double[] spot = g.boardingSpot(h.maxHalfWidth + 0.5, -1.0);
		tpLocal(server, pose, spot[0], h.mainDeckY + 4, spot[2], 0, 30);
		context.waitTicks(60);
		double[] p = playerPos(context);
		check(Math.abs(p[1] - deck) < 0.08, "%s falling: player on the deck (y=%.3f, deck=%.3f)", id, p[1], deck);
		double minY = Double.MAX_VALUE;
		for (int i = 0; i < 3; i++) {
			context.getInput().holdKeyFor(o -> o.jumpKey, 2);
			for (int t = 0; t < 14; t++) {
				context.waitTick();
				minY = Math.min(minY, playerPos(context)[1]);
			}
		}
		context.waitTicks(20);
		p = playerPos(context);
		check(Math.abs(p[1] - deck) < 0.08 && minY > deck - 0.1, "%s jumping: back on the deck (y=%.3f min=%.3f)", id, p[1], minY);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, id + "_7_pont");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 2. every seat taken (armor stands + the player at the helm), one more is refused
		int n = g.seats().size();
		ShipPose now = shipPose(sp, type);
		for (int i = 1; i < n; i++) {
			ShipGeometry.Seat seat = g.seats().get(i);
			double[] w = now.toWorld(seat.x(), seat.y() + 0.5, seat.z());
			server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"ncrew\",\"ncrew%d\"]}",
					w[0], w[1], w[2], i));
		}
		double[] xw = now.toWorld(0, h.mainDeckY + 1, 2);
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"ncrew\",\"nextra\"]}",
				xw[0], xw[1], xw[2]));
		context.waitTicks(20);
		int[] seated = server.computeOnServer(srv -> {
			ShipEntity ship = ship(srv.getOverworld(), type);
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			List<Entity> all = new ArrayList<>();
			srv.getOverworld().iterateEntities().forEach(all::add);
			int ok = 0;
			for (Entity e : all) {
				for (int i = 1; i < n; i++) {
					if (e.getCommandTags().contains("ncrew" + i) && ship.seat(e, i)) {
						ok++;
					}
				}
			}
			boolean pilot = ship.seat(player, ShipGeometry.PILOT_SEAT);
			int refused = 0;
			for (Entity e : all) {
				if (e.getCommandTags().contains("nextra")) {
					refused += e.startRiding(ship) ? 0 : 1;
				}
			}
			return new int[] {ok, pilot ? 1 : 0, ship.getPassengerList().size(), refused};
		});
		check(seated[0] == n - 1 && seated[1] == 1 && seated[2] == n, "%s seats: %d passengers seated (%d + pilot %d)", id, n, seated[0], seated[1]);
		check(seated[3] == 1, "%s seats: one passenger too many is refused", id);

		// 3. sailing: forward, then a turn; the passengers stay aboard
		ShipPose start = shipPose(sp, type);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose run = shipPose(sp, type);
		context.getInput().holdKey(o -> o.rightKey);
		context.waitTicks(60);
		context.getInput().releaseKey(o -> o.rightKey);
		ShipPose turned = shipPose(sp, type);
		double dist = Math.hypot(run.x() - start.x(), run.z() - start.z());
		double turn = Math.abs(ShipPose.wrapDegrees(turned.yaw() - run.yaw()));
		log("%s handling: %.2f blocks in 4 s, %.1f deg in 3 s", id, dist, turn);
		check(dist > 2.0, "%s sailing: moves forward under command (%.2f blocks in 4 s)", id, dist);
		check(turn > 3.0, "%s sailing: turns under command (%.1f deg)", id, turn);
		int still = server.computeOnServer(srv -> ship(srv.getOverworld(), type).getPassengerList().size());
		check(still == n, "%s carry: the %d passengers are still seated (%d)", id, n, still);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(5);
		shot(context, id + "_8_navigation");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		p = playerPos(context);
		double[] l = shipPose(sp, type).toLocal(p[0], p[1], p[2]);
		check(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - h.mainDeckY) < 0.15,
				"%s dismount: the pilot steps off onto the deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]);
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=ncrew]");

		// 4. autopilot on a route: two points, the second one 40 blocks ahead
		ShipPose a = shipPose(sp, type);
		server.runCommand("gamemode spectator @a");
		double[] far = {-42, -58, 175};
		String route = "essai_" + id;
		server.runCommand("ship route create " + route + " once");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f -58 %.1f run ship route addpoint %s", a.x(), a.z(), route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f run ship route addpoint %s", far[0], far[1], far[2], route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f -58 %.1f run ship route assign %s", a.x(), a.z(), route));
		double before = Math.hypot(a.x() - far[0], a.z() - far[2]);
		context.waitTicks(400);
		ShipPose b = shipPose(sp, type);
		double after = Math.hypot(b.x() - far[0], b.z() - far[2]);
		log("%s autopilot: %.1f -> %.1f blocks from the second point", id, before, after);
		check(after < before - 8, "%s autopilot: follows its route (%.1f -> %.1f blocks)", id, before, after);
		lookLocal(server, b, 1.4 * L, 0.8 * top, 1.4 * L, 0, 0.3 * top, 0);
		context.waitTicks(15);
		shot(context, id + "_9_pilote_auto");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f run ship ai disable", b.x(), b.y(), b.z()));
		server.runCommand("ship route delete " + route);

		// 5. the item, then the ship is removed to make room for the next one
		server.runCommand("clear @a");
		server.runCommand("ship give " + id + " @p");
		Integer items = server.computeOnServer(srv ->
				srv.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.item(type)));
		check(items != null && items == 1, "%s item: /ship give %s gives the item (%s)", id, id, items);
		server.runCommand("clear @a");
		server.computeOnServer(srv -> {
			ShipEntity ship = ship(srv.getOverworld(), type);
			if (ship != null) {
				ship.removeAllPassengers();
				ship.discard();
			}
			return null;
		});
		context.waitTicks(10);
	}

	// ------------------------------------------------------------------ steampunk airship

	private static int airshipCount(Env sp) {
		return sp.getServer().computeOnServer(srv -> {
			int n = 0;
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				n += !s.isRemoved() && s.shipType() == Ships.STEAMPUNK_AIRSHIP ? 1 : 0;
			}
			return n;
		});
	}

	private static int airshipCollisions(Env sp) {
		return sp.getServer().computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), Ships.STEAMPUNK_AIRSHIP);
			if (s == null) {
				return -1;
			}
			ServerWorld w = srv.getOverworld();
			return fr.medievalships.core.ShipMover.countCollisions(s.geometry(), s.pose(), (x, y, z) -> {
				var pos = net.minecraft.util.math.BlockPos.ofFloored(x, y, z);
				return !w.getBlockState(pos).getCollisionShape(w, pos).isEmpty();
			});
		});
	}

	/** The airship over open ground east of the basins: placed in the air, hovers, flown by hand, autopilot in 3D. */
	private void airship(ClientGameTestContext context, Env sp) {
		var server = sp.getServer();
		ShipType type = Ships.STEAMPUNK_AIRSHIP;
		String id = type.id();
		ShipGeometry g = type.geometry();
		fr.medievalships.core.HullShape h = g.hull();
		server.runCommand("ride @p dismount");
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=ncrew]");
		server.runCommand("gamemode spectator @a");
		server.runCommand("tp @p 100 -40 -20 0 30");
		context.waitTicks(40);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, 100, 0));
		server.runCommand(String.format(Locale.ROOT, "execute positioned 100 %d 0 rotated 0 0 run ship spawn %s", ground, id));
		sp.getClientWorld().waitForChunksRender();
		context.waitTicks(40);
		ShipPose pose = shipPose(sp, type);
		if (pose == null) {
			fail(id + ": not spawned");
			return;
		}
		log("%s at %.2f %.2f %.2f, ground top %d", id, pose.x(), pose.y(), pose.z(), ground);
		double keel = pose.y() + g.lowestY();
		check(keel >= ground + 0.9 && keel < ground + 3, "%s placed in the air: keel %.2f above the ground (%d)", id, keel, ground);
		check(airshipCollisions(sp) == 0, "%s placed in the air: inside nothing", id);
		context.waitTicks(60);
		ShipPose hover = shipPose(sp, type);
		check(Math.abs(hover.y() - pose.y()) < 0.01, "%s hovers: no fall (y %.3f -> %.3f in 3 s)", id, pose.y(), hover.y());

		// the six views of the reference picture
		double L = 13, top = 9;
		String[] views = {"1_droite", "2_gauche", "3_proue", "4_poupe", "5_dessus", "6_perspective"};
		double[][] eyes = {{-2.2 * L, 0.5 * top, -1}, {2.2 * L, 0.5 * top, -1}, {0.4, 0.7 * top, 2.4 * L}, {0.4, 0.7 * top, -2.6 * L},
				{0.01, 3.2 * L, -1}, {1.6 * L, 1.2 * top, 1.7 * L}};
		for (int k = 0; k < views.length; k++) {
			lookLocal(server, hover, eyes[k][0], eyes[k][1], eyes[k][2], 0, k == 4 ? 0 : 0.7 * top, -1);
			context.waitTicks(k == 0 ? 30 : 15);
			shot(context, id + "_" + views[k]);
		}

		// seats: 5 passengers and the pilot, one more refused
		server.runCommand("gamemode survival @a");
		int n = g.seats().size();
		for (int i = 1; i < n; i++) {
			ShipGeometry.Seat seat = g.seats().get(i);
			double[] w = hover.toWorld(seat.x(), seat.y() + 0.5, seat.z());
			server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"ncrew\",\"ncrew%d\"],NoGravity:1b}",
					w[0], w[1], w[2], i));
		}
		double[] xw = hover.toWorld(0, h.mainDeckY + 1, 2);
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"ncrew\",\"nextra\"],NoGravity:1b}",
				xw[0], xw[1], xw[2]));
		double[] pw = hover.toWorld(0, h.mainDeckY + 0.1, -2);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f", pw[0], pw[1], pw[2]));
		context.waitTicks(10);
		int[] seated = server.computeOnServer(srv -> {
			ShipEntity ship = ship(srv.getOverworld(), type);
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			List<Entity> all = new ArrayList<>();
			srv.getOverworld().iterateEntities().forEach(all::add);
			int ok = 0;
			for (Entity e : all) {
				for (int i = 1; i < n; i++) {
					if (e.getCommandTags().contains("ncrew" + i) && ship.seat(e, i)) {
						ok++;
					}
				}
			}
			boolean pilot = ship.seat(player, ShipGeometry.PILOT_SEAT);
			int refused = 0;
			for (Entity e : all) {
				if (e.getCommandTags().contains("nextra")) {
					refused += e.startRiding(ship) ? 0 : 1;
				}
			}
			return new int[] {ok, pilot ? 1 : 0, ship.getPassengerList().size(), refused};
		});
		check(seated[0] == n - 1 && seated[1] == 1 && seated[2] == n, "%s seats: %d aboard (%d passengers + pilot %d)", id, n, seated[0], seated[1]);
		check(seated[3] == 1, "%s seats: one passenger too many is refused", id);

		// manual flight: climb (jump key), hold the altitude, forward, turn, descend (sprint key)
		ShipPose s0 = shipPose(sp, type);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = shipPose(sp, type);
		context.waitTicks(40);
		ShipPose s2 = shipPose(sp, type);
		context.waitTicks(40);
		ShipPose s3 = shipPose(sp, type);
		log("%s climb: %.2f -> %.2f, then %.3f, %.3f", id, s0.y(), s1.y(), s2.y(), s3.y());
		check(s1.y() - s0.y() > 3, "%s climbs under command (%.2f blocks in 4 s)", id, s1.y() - s0.y());
		check(Math.abs(s3.y() - s2.y()) < 0.02, "%s holds its altitude (%.3f -> %.3f)", id, s2.y(), s3.y());
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(100);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose s4 = shipPose(sp, type);
		context.getInput().holdKey(o -> o.rightKey);
		context.waitTicks(60);
		context.getInput().releaseKey(o -> o.rightKey);
		ShipPose s5 = shipPose(sp, type);
		double dist = Math.hypot(s4.x() - s3.x(), s4.z() - s3.z());
		double turn = Math.abs(ShipPose.wrapDegrees(s5.yaw() - s4.yaw()));
		log("%s flight: %.2f blocks in 5 s, %.1f deg in 3 s, altitude %.3f -> %.3f", id, dist, turn, s3.y(), s5.y());
		check(dist > 2, "%s flies forward under command (%.2f blocks in 5 s)", id, dist);
		check(turn > 3, "%s turns under command (%.1f deg)", id, turn);
		check(Math.abs(s5.y() - s3.y()) < 0.05, "%s level flight while moving (%.3f -> %.3f)", id, s3.y(), s5.y());
		context.getInput().holdKey(o -> o.sprintKey);
		context.waitTicks(50);
		context.getInput().releaseKey(o -> o.sprintKey);
		context.waitTicks(30);
		ShipPose s6 = shipPose(sp, type);
		check(s5.y() - s6.y() > 1.5, "%s comes down under command (%.2f -> %.2f)", id, s5.y(), s6.y());
		int still = server.computeOnServer(srv -> ship(srv.getOverworld(), type).getPassengerList().size());
		check(still == n, "%s carry: the %d aboard are still seated (%d)", id, n, still);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(5);
		shot(context, id + "_7_vol");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		double[] p = playerPos(context);
		double[] l = shipPose(sp, type).toLocal(p[0], p[1], p[2]);
		check(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - h.mainDeckY) < 0.15,
				"%s dismount: the pilot steps off onto the deck of the gondola (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]);
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=ncrew]");
		check(airshipCollisions(sp) == 0, "%s manual flight: never inside anything", id);

		// autopilot on an air route: over a 16 block wall to a stop 12 blocks higher, 60 blocks away
		ShipPose a = shipPose(sp, type);
		server.runCommand("gamemode spectator @a");
		double wallZ = a.z() + 30;
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d stone", (int) a.x() - 14, ground, (int) wallZ,
				(int) a.x() + 14, ground + 15, (int) wallZ + 2));
		double[] far = {a.x(), a.y() + h.mainDeckY + 12, a.z() + 60};
		String route = "essai_air";
		server.runCommand("ship route create " + route + " once air");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f run ship route addpoint %s", a.x(), a.y() + h.mainDeckY,
				a.z(), route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f rotated 90 0 run ship route addstop %s 20 Arrivee",
				far[0], far[1], far[2], route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f run ship route assign %s", a.x(), a.y(), a.z(), route));
		double maxKeel = -999;
		int collisions = 0;
		ShipPose b = a;
		for (int i = 0; i < 60; i++) {
			context.waitTicks(20);
			b = shipPose(sp, type);
			if (Math.abs(b.z() - wallZ) < 6) {
				maxKeel = Math.max(maxKeel, b.y() + g.lowestY());
			}
			collisions = Math.max(collisions, airshipCollisions(sp));
			if (Math.hypot(b.x() - far[0], b.z() - far[2]) < 3 && Math.abs(b.y() + h.mainDeckY - far[1]) < 1.2) {
				break;
			}
		}
		double reach = Math.hypot(b.x() - far[0], b.z() - far[2]);
		log("%s autopilot: %.1f blocks from the stop, deck at %.2f (stop %.2f), keel over the wall %.2f (wall top %d)", id, reach,
				b.y() + h.mainDeckY, far[1], maxKeel, ground + 16);
		check(maxKeel > ground + 16, "%s autopilot: climbs over the wall (keel %.2f, wall top %d)", id, maxKeel, ground + 16);
		check(collisions == 0, "%s autopilot: never inside the wall or the ground", id);
		check(reach < 3.5 && Math.abs(b.y() + h.mainDeckY - far[1]) < 1.5,
				"%s autopilot: reaches the stop in 3D (%.1f blocks away, deck %.2f for %.2f)", id, reach, b.y() + h.mainDeckY, far[1]);
		lookLocal(server, b, 26, 14, 20, 0, 6, -1);
		context.waitTicks(15);
		shot(context, id + "_8_pilote_auto");
		// it turns on the spot (about 6.6 deg/s): give it up to 30 s once docked
		ShipPose c = shipPose(sp, type);
		for (int i = 0; i < 30 && Math.abs(ShipPose.wrapDegrees(c.yaw() - 90)) >= 3; i++) {
			context.waitTicks(20);
			c = shipPose(sp, type);
		}
		check(Math.abs(ShipPose.wrapDegrees(c.yaw() - 90)) < 6, "%s autopilot: turns to the stop's heading while waiting (%.1f)", id, c.yaw());
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.1f %.1f %.1f run ship ai disable", c.x(), c.y(), c.z()));
		server.runCommand("ship route delete " + route);

		// the item: right click on the ground places a second airship above it
		server.runCommand("gamemode creative @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p 150 %d -40 0 50", ground));
		context.waitTicks(20);
		server.runCommand("item replace entity @p weapon.mainhand with medievalships:steampunk_airship");
		context.waitTicks(5);
		int before = airshipCount(sp);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(20);
		int after = airshipCount(sp);
		check(after == before + 1, "%s item: right click on the ground places an airship (%d -> %d)", id, before, after);
		server.runCommand("clear @a");
		server.runCommand("ship give " + id + " @p");
		Integer items = server.computeOnServer(srv ->
				srv.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.item(type)));
		check(items != null && items == 1, "%s item: /ship give %s gives the item (%s)", id, id, items);
		server.runCommand("clear @a");
		server.computeOnServer(srv -> {
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (s.shipType() == type) {
					s.removeAllPassengers();
					s.discard();
				}
			}
			return null;
		});
		context.waitTicks(10);
	}

	// ------------------------------------------------------------------ Nautilus

	private static int nautilusCollisions(Env sp) {
		return sp.getServer().computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), Ships.NAUTILUS);
			if (s == null) {
				return -1;
			}
			ServerWorld w = srv.getOverworld();
			return fr.medievalships.core.ShipMover.countCollisions(s.geometry(), s.pose(), (x, y, z) -> {
				var pos = net.minecraft.util.math.BlockPos.ofFloored(x, y, z);
				return !w.getBlockState(pos).getCollisionShape(w, pos).isEmpty();
			});
		});
	}

	/** Client and server view of the player: in the water, under it, air, camera under water, local position. */
	private double[] playerWater(ClientGameTestContext context, Env sp, ShipPose pose) {
		double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {
				mc.player.isTouchingWater() ? 1 : 0, mc.player.isSubmergedInWater() ? 1 : 0,
				mc.gameRenderer.getCamera().getSubmersionType() == net.minecraft.block.enums.CameraSubmersionType.WATER ? 1 : 0,
				mc.player.getX(), mc.player.getY(), mc.player.getZ(), mc.player.isOnGround() ? 1 : 0});
		double[] s = sp.getServer().computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			return new double[] {pl.isTouchingWater() ? 1 : 0, pl.isSubmergedInWater() ? 1 : 0, pl.getAir(), pl.getMaxAir()};
		});
		double[] l = pose.toLocal(c[3], c[4], c[5]);
		return new double[] {c[0], c[1], c[2], s[0], s[1], s[2], s[3], l[0], l[1], l[2], c[6]};
	}

	/** The Nautilus in a deep basin: placed, walked through, stairs, ladder, hatch, dive and surface, dry inside. */
	private void nautilus(ClientGameTestContext context, Env sp) {
		var server = sp.getServer();
		ShipType type = Ships.NAUTILUS;
		String id = type.id();
		ShipGeometry g = type.geometry();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand("tp @p 215 -20 -90 0 30");
		context.waitTicks(40);
		// a basin 28 blocks wide, 142 long and 27 deep, walled with glass
		int x0 = 200, x1 = 230, z0 = -72, z1 = 72, top = -34;
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x1, top, z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z1, x1, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x0, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x1, z0, x1, top, z1));
		for (int z = z0 + 1; z < z1; z += 40) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -37 %d water", x0 + 1, z, x1 - 1, Math.min(z1 - 1, z + 39)));
		}
		server.runCommand("tp @p 215 -20 -50 0 30");
		context.waitTicks(20);
		server.runCommand("execute positioned 215 -37 -20 rotated 0 0 run ship spawn " + id);
		sp.getClientWorld().waitForChunksRender();
		context.waitTicks(60);
		ShipPose pose = shipPose(sp, type);
		if (pose == null) {
			fail(id + ": not spawned");
			return;
		}
		double surface = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var pos = new net.minecraft.util.math.BlockPos(215, -37, (int) Math.floor(pose.z()));
			return pos.getY() + (double) w.getFluidState(pos).getHeight(w, pos);
		});
		log("%s at %.2f %.2f %.2f, water surface %.3f", id, pose.x(), pose.y(), pose.z(), surface);
		check(Math.abs(pose.y() - (surface - g.hull().waterlineY)) < 0.2, "%s floats on the surface (y %.2f, surfaced %.2f)", id, pose.y(),
				surface - g.hull().waterlineY);
		check(nautilusCollisions(sp) == 0, "%s placed: inside nothing", id);

		// outside views (step 1: prototype hull)
		String[] views = {"1_droite", "2_gauche", "3_perspective"};
		double[][] eyes = {{-60, 6, 0}, {60, 6, 0}, {40, 25, 55}};
		for (int k = 0; k < views.length; k++) {
			lookLocal(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], 0, 2, 0);
			context.waitTicks(k == 0 ? 30 : 15);
			shot(context, id + "_" + views[k]);
		}

		// inside, on the surface: main level, then the lower level (under the waterline)
		server.runCommand("gamemode survival @a");
		server.runCommand("effect clear @a minecraft:water_breathing");
		tpLocal(server, pose, 0, 0.02, -10, 0, 0);
		context.waitTicks(40);
		double[] w = playerWater(context, sp, shipPose(sp, type));
		log("%s main level: water %s/%s camera %s, local y %.3f", id, w[0], w[3], w[2], w[8]);
		check(w[0] == 0 && w[3] == 0 && Math.abs(w[8]) < 0.06 && w[10] > 0, "%s walks on the main level floor (local y %.3f)", id, w[8]);
		tpLocal(server, pose, 0, Ships.NautilusLayout.LOWER_FLOOR_Y + 0.02, 0, 0, 0);
		context.waitTicks(200);
		w = playerWater(context, sp, shipPose(sp, type));
		log("%s lower level (below the waterline): touching water client %s server %s, submerged %s/%s, camera %s, air %.0f/%.0f, y %.3f",
				id, w[0], w[3], w[1], w[4], w[2], w[5], w[6], w[8]);
		check(w[0] == 0 && w[3] == 0 && w[1] == 0 && w[4] == 0, "%s lower level is dry although below the waterline", id);
		check(w[2] == 0, "%s lower level: no underwater view", id);
		check(w[5] == w[6], "%s lower level: the player keeps all his air (%.0f/%.0f)", id, w[5], w[6]);
		check(Math.abs(w[8] - Ships.NautilusLayout.LOWER_FLOOR_Y) < 0.06, "%s lower level: standing on its floor (local y %.3f)", id, w[8]);
		shot(context, id + "_4_pont_inferieur");

		// stairs from the lower level up to the main level
		double[] l = walkLocal(context, sp, type, shipPose(sp, type), -1.75, Ships.NautilusLayout.LOWER_FLOOR_Y, 8.0, 0, 0, 70);
		log("%s stairs: local %.2f %.2f %.2f", id, l[0], l[1], l[2]);
		check(Math.abs(l[1] - Ships.NautilusLayout.MAIN_FLOOR_Y) < 0.06 && l[2] > 14.4, "%s climbs the stairs to the main level (local y %.2f z %.2f)",
				id, l[1], l[2]);

		// ladder up to the hatch: stopped under the closed hatch, out on the top of the hull once it is open
		ShipPose here = shipPose(sp, type);
		tpLocal(server, here, 0, 0.02, Ships.NautilusLayout.HATCH_Z - 0.2, 0, 0);
		context.waitTicks(15);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(120);
		w = playerWater(context, sp, shipPose(sp, type));
		double hatchTop = Ships.NautilusLayout.AXIS_Y + Ships.NautilusLayout.halfHeight(Ships.NautilusLayout.HATCH_Z);
		log("%s ladder, hatch closed: local y %.2f (hull top %.2f)", id, w[8], hatchTop);
		check(w[8] > 3.5 && w[8] + 1.8 < hatchTop, "%s climbs the ladder and stops under the closed hatch (local y %.2f)", id, w[8]);
		server.computeOnServer(srv -> ship(srv.getOverworld(), type).toggleDoor(Ships.NautilusLayout.HATCH_DOOR));
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(20);
		w = playerWater(context, sp, shipPose(sp, type));
		log("%s ladder, hatch open: local %.2f %.2f %.2f", id, w[7], w[8], w[9]);
		check(w[8] > hatchTop - 1.0, "%s goes out through the open hatch onto the hull (local y %.2f, top %.2f)", id, w[8], hatchTop);
		shot(context, id + "_5_sur_la_coque");

		// dive with the hatch open is refused; close it, take the helm in the wheelhouse and dive
		boolean opened = server.computeOnServer(srv -> ship(srv.getOverworld(), type).doorOpen(Ships.NautilusLayout.HATCH_DOOR));
		check(opened, "%s the hatch is open", id);
		tpLocal(server, shipPose(sp, type), 0, Ships.NautilusLayout.TOWER_FLOOR_Y + 0.02, 27.5, 0, 0);
		context.waitTicks(10);
		server.computeOnServer(srv -> {
			ShipEntity ship = ship(srv.getOverworld(), type);
			return ship.seat(srv.getPlayerManager().getPlayerList().get(0), ShipGeometry.PILOT_SEAT);
		});
		context.waitTicks(10);
		ShipPose d0 = shipPose(sp, type);
		context.getInput().holdKey(o -> o.sprintKey);
		context.waitTicks(60);
		context.getInput().releaseKey(o -> o.sprintKey);
		ShipPose d1 = shipPose(sp, type);
		check(Math.abs(d1.y() - d0.y()) < 0.3, "%s does not dive with the hatch open (%.2f -> %.2f)", id, d0.y(), d1.y());
		server.computeOnServer(srv -> ship(srv.getOverworld(), type).toggleDoor(Ships.NautilusLayout.HATCH_DOOR));
		context.waitTicks(10);
		context.getInput().holdKey(o -> o.sprintKey);
		context.waitTicks(260);
		context.getInput().releaseKey(o -> o.sprintKey);
		context.waitTicks(100);
		ShipPose d2 = shipPose(sp, type);
		context.waitTicks(60);
		ShipPose d3 = shipPose(sp, type);
		float depth = server.computeOnServer(srv -> ship(srv.getOverworld(), type).syncedDepth());
		log("%s dive: %.2f -> %.2f, then %.3f (depth %.1f)", id, d1.y(), d2.y(), d3.y(), depth);
		check(d1.y() - d2.y() > 6, "%s dives under command (%.2f blocks)", id, d1.y() - d2.y());
		check(Math.abs(d3.y() - d2.y()) < 0.05, "%s holds its depth (%.3f -> %.3f)", id, d2.y(), d3.y());
		check(nautilusCollisions(sp) == 0, "%s dived: inside nothing", id);
		Text msg = server.computeOnServer(srv -> ship(srv.getOverworld(), type).toggleDoor(Ships.NautilusLayout.HATCH_DOOR));
		boolean still = server.computeOnServer(srv -> ship(srv.getOverworld(), type).doorOpen(Ships.NautilusLayout.HATCH_DOOR));
		check(msg != null && !still, "%s the hatch does not open under water", id);

		// sail submerged with an armor stand standing in the hall, then walk inside under the sea
		ShipPose d4 = shipPose(sp, type);
		double[] mw = d4.toWorld(1.0, 0.5, -4);
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"ncrew\",\"nautilusmob\"]}", mw[0], mw[1], mw[2]));
		context.waitTicks(40);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(120);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(40);
		ShipPose d5 = shipPose(sp, type);
		double moved = Math.hypot(d5.x() - d4.x(), d5.z() - d4.z());
		double[] mob = server.computeOnServer(srv -> {
			for (Entity e : srv.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("nautilusmob")) {
					return new double[] {e.getX(), e.getY(), e.getZ()};
				}
			}
			return null;
		});
		double[] ml = mob == null ? new double[] {99, 99, 99} : d5.toLocal(mob[0], mob[1], mob[2]);
		log("%s sailing submerged: %.2f blocks, armor stand local %.2f %.2f %.2f", id, moved, ml[0], ml[1], ml[2]);
		check(moved > 2, "%s sails submerged (%.2f blocks)", id, moved);
		check(Math.abs(ml[1]) < 0.1 && Math.abs(ml[2] + 4) < 1.5, "%s carries what stands in its rooms (armor stand local y %.2f z %.2f)", id, ml[1], ml[2]);
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		tpLocal(server, d5, 0, 0.02, -14, 0, 0);
		context.waitTicks(200);
		w = playerWater(context, sp, shipPose(sp, type));
		log("%s inside, submerged: touching water %s/%s, submerged %s/%s, camera %s, air %.0f/%.0f, local y %.3f", id, w[0], w[3], w[1], w[4],
				w[2], w[5], w[6], w[8]);
		check(w[0] == 0 && w[3] == 0 && w[1] == 0 && w[4] == 0 && w[2] == 0, "%s submerged: the rooms are dry (no water, no underwater view)", id);
		check(w[5] == w[6], "%s submerged: the player keeps all his air (%.0f/%.0f)", id, w[5], w[6]);
		check(Math.abs(w[8]) < 0.06, "%s submerged: standing on the main level floor (local y %.3f)", id, w[8]);
		shot(context, id + "_6_interieur_en_plongee");
		// diagnosis of the far end of the hall: the end wall seen from 10 and from 30 blocks, and the hall looking aft
		for (double[] v : new double[][] {{18, 0}, {-2, 0}, {0, 180}}) {
			tpLocal(server, d5, 0, 0.02, v[0], (float) v[1], 0);
			context.waitTicks(15);
			shot(context, String.format(Locale.ROOT, "%s_6_diag_z%.0f_cap%.0f", id, v[0], v[1]));
		}
		String gfx = context.computeOnClient(mc -> mc.options.getPreset().getValue().toString());
		log("%s graphics preset: %s", id, gfx);
		tpLocal(server, d5, 0, 0.02, -14, 0, 0);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, 60);
		context.waitTicks(20);
		w = playerWater(context, sp, shipPose(sp, type));
		check(Math.abs(w[8]) < 0.06 && Math.abs(w[7]) < 3.1 && w[1] == 0, "%s submerged: walking in the hall (local %.2f %.2f %.2f)", id, w[7], w[8], w[9]);
		server.runCommand("gamemode spectator @a");
		lookLocal(server, shipPose(sp, type), -22, -3, -10, 0, 0, 0);
		context.waitTicks(20);
		shot(context, id + "_7_sous_l_eau");

		// back to the helm and up to the surface
		server.runCommand("gamemode survival @a");
		tpLocal(server, shipPose(sp, type), 0, Ships.NautilusLayout.TOWER_FLOOR_Y + 0.02, 27.5, 0, 0);
		context.waitTicks(10);
		server.computeOnServer(srv -> ship(srv.getOverworld(), type).seat(srv.getPlayerManager().getPlayerList().get(0), ShipGeometry.PILOT_SEAT));
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(500);
		context.getInput().releaseKey(o -> o.jumpKey);
		context.waitTicks(60);
		float depthEnd = server.computeOnServer(srv -> ship(srv.getOverworld(), type).syncedDepth());
		log("%s surfacing: depth %.2f", id, depthEnd);
		check(depthEnd < 0.5, "%s rises back to the surface (depth %.2f)", id, depthEnd);
		server.runCommand("ride @p dismount");
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=ncrew]");

		// the item: /ship give, and right click on the water places one
		server.computeOnServer(srv -> {
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (s.shipType() == type) {
					s.removeAllPassengers();
					s.discard();
				}
			}
			return null;
		});
		server.runCommand("clear @a");
		server.runCommand("ship give " + id + " @p");
		Integer items = server.computeOnServer(srv ->
				srv.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.item(type)));
		check(items != null && items == 1, "%s item: /ship give %s gives the item (%s)", id, id, items);
		server.runCommand("gamemode creative @a");
		server.runCommand("tp @p 215 -33 -71 0 35");
		context.waitTicks(20);
		server.runCommand("item replace entity @p weapon.mainhand with medievalships:" + id);
		context.waitTicks(5);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(20);
		ShipPose placed = shipPose(sp, type);
		check(placed != null, "%s item: right click on the water places the Nautilus", id);
		server.runCommand("clear @a");
		server.computeOnServer(srv -> {
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (s.shipType() == type) {
					s.discard();
				}
			}
			return null;
		});
		context.waitTicks(10);
	}

	/** Teleports the player to a ship-local position, then walks forward for {@code ticks}; returns the local position. */
	private double[] walkLocal(ClientGameTestContext context, Env sp, ShipType type, ShipPose pose, double lx, double ly, double lz,
			float localYaw, float pitch, int ticks) {
		tpLocal(sp.getServer(), pose, lx, ly + 0.02, lz, localYaw, pitch);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, ticks);
		context.waitTicks(15);
		double[] p = playerPos(context);
		return shipPose(sp, type).toLocal(p[0], p[1], p[2]);
	}

	/** Spectator camera at a ship-local point, looking at another ship-local point. */
	private static void lookLocal(net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext server, ShipPose pose,
			double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}

	private static void tpLocal(net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext server, ShipPose pose,
			double lx, double ly, double lz, float localYaw, float pitch) {
		double[] w = pose.toWorld(lx, ly, lz);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", w[0], w[1], w[2],
				(float) (pose.yaw() + localYaw), pitch));
	}

	// ------------------------------------------------------------------ helpers

	private static ShipEntity ship(ServerWorld world) {
		return ship(world, Ships.GALLEY);
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose shipPose(Env sp, ShipType type) {
		return sp.getServer().computeOnServer(server -> {
			ShipEntity s = ship(server.getOverworld(), type);
			return s == null ? null : s.pose();
		});
	}

	private static ShipPose shipPose(Env sp) {
		return sp.getServer().computeOnServer(server -> {
			ShipEntity s = ship(server.getOverworld());
			return s == null ? null : s.pose();
		});
	}

	private static double[] mobPos(Env sp) {
		return sp.getServer().computeOnServer((MinecraftServer server) -> {
			for (Entity e : server.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("deckmob")) {
					return new double[] {e.getX(), e.getY(), e.getZ()};
				}
			}
			return null;
		});
	}

	private static double[] playerPos(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) ->
				new double[] {c.player.getX(), c.player.getY(), c.player.getZ(), c.player.isOnGround() ? 1 : 0});
	}

	private void shot(ClientGameTestContext context, String name) {
		context.takeScreenshot(tag + "_" + name);
	}

	private void log(String fmt, Object... args) {
		String s = (tag.isEmpty() ? "" : "[" + tag + "] ") + String.format(Locale.ROOT, fmt, args);
		report.add(s);
		System.out.println("[medievalships-test] " + s);
	}

	private void check(boolean ok, String fmt, Object... args) {
		String s = (tag.isEmpty() ? "" : "[" + tag + "] ") + String.format(Locale.ROOT, fmt, args);
		report.add((ok ? "PASS " : "FAIL ") + s);
		System.out.println("[medievalships-test] " + (ok ? "PASS " : "FAIL ") + s);
		if (!ok) {
			failures.add(s);
		}
	}

	private void fail(String s) {
		check(false, "%s", s);
	}

	private void finish(ClientGameTestContext context) {
		try {
			Files.write(Path.of("medievalships-test.txt"), report);
		} catch (IOException e) {
			System.out.println("[medievalships-test] could not write report: " + e);
		}
		if (!failures.isEmpty()) {
			throw new AssertionError(failures.size() + " check(s) failed: " + String.join(" | ", failures));
		}
	}
}
