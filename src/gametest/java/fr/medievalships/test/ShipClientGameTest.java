package fr.medievalships.test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.entity.Entity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;

import fr.medievalships.core.HullProfile;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.Ships.GalleonLayout;
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

	@Override
	public void runTest(ClientGameTestContext context) {
		try (TestSingleplayerContext sp = context.worldBuilder().create()) {
			var server = sp.getServer();
			log("world loaded (lithium installed: %s)", net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("lithium"));
			if ("1".equals(System.getenv("MS_TEST_MINIMAL"))) {
				context.takeScreenshot("00_minimal");
				finish(context);
				return;
			}
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
				finish(context);
				return;
			}
			log("ship at %.2f %.2f %.2f yaw %.1f", pose.x(), pose.y(), pose.z(), pose.yaw());
			double deckY = pose.y() + HullProfile.MAIN_DECK_Y;
			log("expected main deck top %.3f", deckY);

			// overview screenshots
			server.runCommand("gamemode spectator @a");
			server.runCommand("tp @p 16 -50 -16 45 25");
			context.waitTicks(30);
			context.takeScreenshot("01_overview");
			server.runCommand("tp @p -13 -55 3 -100 8");
			context.waitTicks(20);
			context.takeScreenshot("02_side");
			server.runCommand("tp @p 2 -50 22 160 30");
			context.waitTicks(20);
			context.takeScreenshot("02b_bow");
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
			context.takeScreenshot("03_on_deck_first_person");
			context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
			context.waitTicks(5);
			context.takeScreenshot("04_on_deck_third_person");
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
			context.takeScreenshot("05_at_the_bow");

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
			context.takeScreenshot("06_jumped_from_quay");

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
			context.takeScreenshot("06b_under_the_hull");
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
			context.takeScreenshot("07_sailing");
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
		} catch (Throwable t) {
			fail("exception: " + t);
		}
		finish(context);
	}

	// ------------------------------------------------------------------ great galleon

	private void galleon(ClientGameTestContext context, TestSingleplayerContext sp) {
		var server = sp.getServer();
		ShipGeometry g = Ships.GALLEON.geometry();
		server.runCommand("ride @a dismount");
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
		context.takeScreenshot("g01_galleon_overview");
		lookLocal(server, pose, -34, 7, 2, 0, 7, 2);
		context.waitTicks(20);
		context.takeScreenshot("g02_galleon_side");
		lookLocal(server, pose, -9, 6, -31, 0, 3, -16);
		context.waitTicks(20);
		context.takeScreenshot("g03_galleon_stern");
		lookLocal(server, pose, 10, 9, 34, 0, 5, 15);
		context.waitTicks(20);
		context.takeScreenshot("g04_galleon_bow");

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
		context.takeScreenshot("g05_galleon_deck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 2. into the great cabin through the bulkhead door
		l = walkLocal(context, sp, pose, 0, GalleonLayout.MAIN_DECK_Y, -6.0, 180, 0, 30);
		log("galleon cabin: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(l[2] < GalleonLayout.BULKHEAD_Z - 1.5 && Math.abs(l[1] - GalleonLayout.MAIN_DECK_Y) < 0.1,
				"galleon cabin: player walked into the cabin (local z=%.2f y=%.2f)", l[2], l[1]);
		context.takeScreenshot("g06_galleon_cabin");

		// 3. through the transom door onto the stern balcony
		l = walkLocal(context, sp, pose, 0, GalleonLayout.MAIN_DECK_Y, -15.0, 180, 0, 40);
		log("galleon balcony: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(l[2] < -g.hull().halfLength && l[2] > GalleonLayout.BALCONY_BACK && Math.abs(l[1] - GalleonLayout.MAIN_DECK_Y) < 0.1,
				"galleon balcony: player on the balcony, held by the balustrade (local z=%.2f y=%.2f)", l[2], l[1]);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(5);
		context.takeScreenshot("g07_galleon_balcony");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// 4. up the stairs to the quarterdeck, and to the forecastle
		double qx = (GalleonLayout.STAIR_X0 + GalleonLayout.STAIR_X1) / 2;
		l = walkLocal(context, sp, pose, qx, GalleonLayout.MAIN_DECK_Y, -5.0, 180, 0, 50);
		log("galleon quarterdeck: local %.2f %.2f %.2f", l[0], l[1], l[2]);
		check(Math.abs(l[1] - GalleonLayout.QUARTERDECK_Y) < 0.1 && l[2] < GalleonLayout.BULKHEAD_Z,
				"galleon stairs: player climbed onto the quarterdeck (local y=%.2f z=%.2f)", l[1], l[2]);
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		context.takeScreenshot("g08_galleon_quarterdeck");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		double fx = (GalleonLayout.FC_STAIR_X0 + GalleonLayout.FC_STAIR_X1) / 2;
		l = walkLocal(context, sp, pose, fx, GalleonLayout.MAIN_DECK_Y, 7.6, 0, 0, 40);
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
		context.takeScreenshot("g09_galleon_sailing");
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
		server.runCommand("ride @a dismount");
		context.waitTicks(10);
		p = playerPos(context);
		ShipPose now = shipPose(sp, Ships.GALLEON);
		l = now.toLocal(p[0], p[1], p[2]);
		check(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - GalleonLayout.QUARTERDECK_Y) < 0.15,
				"galleon dismount: the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", l[0], l[1], l[2]);
		server.runCommand("clear @a");
		server.runCommand("ship give galleon @p");
		Integer items = server.computeOnServer(s ->
				s.getPlayerManager().getPlayerList().get(0).getInventory().count(fr.medievalships.MedievalShips.GALLEON_ITEM));
		check(items != null && items == 1, "galleon item: /ship give galleon gives the item (%s)", items);
	}

	/** Teleports the player to a ship-local position, then walks forward for {@code ticks}; returns the local position. */
	private double[] walkLocal(ClientGameTestContext context, TestSingleplayerContext sp, ShipPose pose, double lx, double ly, double lz,
			float localYaw, float pitch, int ticks) {
		tpLocal(sp.getServer(), pose, lx, ly + 0.02, lz, localYaw, pitch);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, ticks);
		context.waitTicks(15);
		double[] p = playerPos(context);
		return shipPose(sp, Ships.GALLEON).toLocal(p[0], p[1], p[2]);
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

	private static ShipPose shipPose(TestSingleplayerContext sp, ShipType type) {
		return sp.getServer().computeOnServer(server -> {
			ShipEntity s = ship(server.getOverworld(), type);
			return s == null ? null : s.pose();
		});
	}

	private static ShipPose shipPose(TestSingleplayerContext sp) {
		return sp.getServer().computeOnServer(server -> {
			ShipEntity s = ship(server.getOverworld());
			return s == null ? null : s.pose();
		});
	}

	private static double[] mobPos(TestSingleplayerContext sp) {
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

	private void log(String fmt, Object... args) {
		String s = String.format(Locale.ROOT, fmt, args);
		report.add(s);
		System.out.println("[medievalships-test] " + s);
	}

	private void check(boolean ok, String fmt, Object... args) {
		String s = String.format(Locale.ROOT, fmt, args);
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
