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
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * Real client test: a player falls, jumps and walks on the deck, jumps aboard from a quay,
 * a mob stands on the deck, and the ship is steered with everything aboard.
 * Results are written to run/medievalships-test.txt, screenshots to the screenshot folder.
 */
public class ShipClientGameTest implements FabricClientGameTest {
	private final List<String> report = new ArrayList<>();
	private final List<String> failures = new ArrayList<>();

	@Override
	public void runTest(ClientGameTestContext context) {
		try (TestSingleplayerContext sp = context.worldBuilder().create()) {
			var server = sp.getServer();
			log("world loaded");
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
			check(ShipGeometry.inCarryVolume(l[0], l[1], l[2]) && l[1] > HullProfile.MAIN_DECK_Y - 0.1,
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
			check(ShipGeometry.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - HullProfile.deckY(l[2])) < 0.1,
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
				GalleyEntity ship = ship(server2.getOverworld());
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
				check(ShipGeometry.inCarryVolume(zl[0], zl[1], zl[2]), "carry: zombie should still be aboard");
			}
		} catch (Throwable t) {
			fail("exception: " + t);
		}
		finish(context);
	}

	// ------------------------------------------------------------------ helpers

	private static GalleyEntity ship(ServerWorld world) {
		for (GalleyEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved()) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose shipPose(TestSingleplayerContext sp) {
		return sp.getServer().computeOnServer(server -> {
			GalleyEntity s = ship(server.getOverworld());
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
