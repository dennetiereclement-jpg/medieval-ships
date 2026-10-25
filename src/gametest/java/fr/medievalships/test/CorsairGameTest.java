package fr.medievalships.test;

import java.util.Locale;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.CorsairLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The Old Corsair in a real game (called from {@link ShipClientGameTest}): it floats on a basin, the
 * player stands on its main deck, in the captain's cabin, the common room and the hold (dry below the
 * waterline), a door opens, and the ship sails under the player's control. About 40 seconds.
 */
public final class CorsairGameTest {
	/** Reports a check (PASS / FAIL line of the test report). */
	public interface Check {
		void check(boolean ok, String fmt, Object... args);
	}

	public interface Log {
		void log(String fmt, Object... args);
	}

	public interface Shot {
		void shot(String name);
	}

	private CorsairGameTest() {
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, Check check, Log log,
			Shot shot) {
		ShipType type = Ships.OLD_CORSAIR;
		String id = type.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand("tp @p 315 -30 -40 0 30");
		context.waitTicks(30);
		// a basin 30 wide, 90 long and 14 deep, walled with glass
		int x0 = 300, x1 = 330, z0 = -45, z1 = 45, top = -46;
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", x0, z0, x1, z1));
		context.waitTicks(30);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x1, top, z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z1, x1, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x0, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x1, z0, x1, top, z1));
		for (int z = z0 + 1; z < z1; z += 30) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", x0 + 1, z, x1 - 1, Math.min(z1 - 1, z + 29)));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -30 %d air", x0 + 1, z, x1 - 1, Math.min(z1 - 1, z + 29)));
		}
		server.runCommand("execute positioned 315 -50 -12 rotated 0 0 run ship spawn " + id);
		world.waitForChunksRender();
		context.waitTicks(60);
		ShipPose pose = pose(server, type);
		if (pose == null) {
			check.check(false, "%s: spawned in the basin", id);
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
			return;
		}
		double surface = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			BlockPos pos = new BlockPos(315, -50, (int) Math.floor(pose.z()));
			return pos.getY() + (double) w.getFluidState(pos).getHeight(w, pos);
		});
		log.log("%s at %.2f %.2f %.2f, water surface %.3f", id, pose.x(), pose.y(), pose.z(), surface);
		check.check(Math.abs(pose.y() - (surface - type.hull().waterlineY)) < 0.25, "%s floats on the surface (y %.2f, water %.2f)", id,
				pose.y(), surface);
		double[][] eyes = {{40, 7, 30}, {0, 9, 55}, {-4, 10, -45}, {32, 12, 45}};
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_perspective"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], 0, 12, 0);
			context.waitTicks(k == 0 ? 30 : 15);
			shot.shot(id + "_" + names[k]);
		}

		// walking aboard: main deck, quarterdeck, captain's cabin, common room, hold (below the waterline)
		server.runCommand("gamemode survival @a");
		double[][] spots = {
				{0.0, CorsairLayout.MAIN_DECK_Y, -5.5, 180},
				{1.6, CorsairLayout.QUARTERDECK_Y, -15.0, 180},
				{0.0, CorsairLayout.CABIN_FLOOR_Y, -16.0, 180},
				{0.6, CorsairLayout.LOWER_FLOOR_Y, 6.5, 200},
				{0.0, CorsairLayout.LOWER_FLOOR_Y, -8.0, 180},
				{0.0, CorsairLayout.HOLD_FLOOR_Y, -6.0, 0}};
		String[] where = {"main deck", "quarterdeck", "captain's cabin", "common room", "coursive", "hold"};
		for (int k = 0; k < spots.length; k++) {
			ShipPose p = pose(server, type);
			tp(server, p, spots[k][0], spots[k][1] + 0.02, spots[k][2], (float) spots[k][3], 10);
			context.waitTicks(k == spots.length - 1 ? 80 : 30);
			double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
					mc.player.isOnGround() ? 1 : 0, mc.player.isTouchingWater() ? 1 : 0, mc.player.isSubmergedInWater() ? 1 : 0,
					mc.player.getAir()});
			double[] l = pose(server, type).toLocal(c[0], c[1], c[2]);
			log.log("%s %s: local %.2f %.3f %.2f, on ground %s, water %s/%s, air %.0f", id, where[k], l[0], l[1], l[2], c[3], c[4], c[5], c[6]);
			check.check(Math.abs(l[1] - spots[k][1]) < 0.08 && c[3] > 0, "%s: standing in the %s (local y %.3f)", id, where[k], l[1]);
			if (spots[k][1] < 0) {
				check.check(c[4] == 0 && c[5] == 0, "%s: the %s is dry below the waterline (water %s/%s)", id, where[k], c[4], c[5]);
			}
			shot.shot(id + "_" + (5 + k) + "_" + where[k].replace(' ', '_').replace("'", ""));
		}
		// a door of the lower deck
		boolean opened = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			s.toggleDoor(CorsairLayout.KITCHEN_DOOR);
			return s.doorOpen(CorsairLayout.KITCHEN_DOOR);
		});
		check.check(opened, "%s: the kitchen door opens", id);

		// at the helm: the ship gathers way slowly
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f", pose(server, type).toWorld(0, CorsairLayout.QUARTERDECK_Y + 0.02,
				CorsairLayout.PILOT_Z)[0], pose(server, type).toWorld(0, CorsairLayout.QUARTERDECK_Y + 0.02, CorsairLayout.PILOT_Z)[1],
				pose(server, type).toWorld(0, CorsairLayout.QUARTERDECK_Y + 0.02, CorsairLayout.PILOT_Z)[2]));
		context.waitTicks(10);
		server.runOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity s = ship(srv.getOverworld(), type);
			if (s != null) {
				s.seat(player, ShipGeometry.PILOT_SEAT);
			}
		});
		context.waitTicks(10);
		ShipPose start = pose(server, type);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(140);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose moved = pose(server, type);
		double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
		log.log("%s moved %.2f blocks in 7 s at the helm", id, dist);
		check.check(dist > 1.5 && dist < 30, "%s sails under the player's control (moved %.2f)", id, dist);
		shot.shot(id + "_11_a_la_barre");
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			if (s != null) {
				s.discard();
			}
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose pose(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : s.pose();
		});
	}

	private static void tp(TestServerContext server, ShipPose pose, double lx, double ly, double lz, float localYaw, float pitch) {
		double[] w = pose.toWorld(lx, ly, lz);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", w[0], w[1], w[2], (float) (pose.yaw() + localYaw), pitch));
	}

	private static void look(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}
}
