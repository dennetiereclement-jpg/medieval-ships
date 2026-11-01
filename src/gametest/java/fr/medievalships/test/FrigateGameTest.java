package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.FrigateLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The Blue-Sailed Frigate in a real game (called once from {@link ShipClientGameTest}, about 35 s of game
 * time): placed on a basin and floating at its waterline, its sails furl at rest and are set again, the model's
 * animations are loaded, the reference's viewpoint (port bow) and the side, front, back and top views are
 * photographed (no HUD), the player stands on the main deck, the quarterdeck, in the captain's cabin and in
 * the hold, the cabin door opens, and the ship sails under the player's control from the helm (the wheel and
 * the rudder turn, the sails stay set, the hull creaks and the bow wave washes).
 */
public final class FrigateGameTest {
	private static final ShipType TYPE = Ships.BLUE_FRIGATE;
	private static final int X = 1100;

	private FrigateGameTest() {
	}

	private static ShipEntity ship(ServerWorld world) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == TYPE) {
				return s;
			}
		}
		return null;
	}

	private static ShipEntity clientShip(MinecraftClient mc) {
		for (ShipEntity s : ShipTracker.ships(mc.world)) {
			if (!s.isRemoved() && s.shipType() == TYPE) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose pose(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			return s == null ? null : s.pose();
		});
	}

	private static float[] sails(ClientGameTestContext context) {
		return context.computeOnClient(mc -> {
			ShipEntity s = clientShip(mc);
			return s == null ? new float[] {-1, -1} : new float[] {s.sailSet() ? 1 : 0, s.sailOpen};
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

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 -40 0 30", X));
		context.waitTicks(20);
		// a basin 56 wide, 100 long and 14 deep, walled with glass up to the water (the hull is seen over the walls)
		int x0 = X - 28, x1 = X + 28, z0 = -50, z1 = 50, top = -50;
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", x0, z0, x1, z1));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x1, top, z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z1, x1, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x0, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x1, z0, x1, top, z1));
		for (int z = z0 + 1; z < z1; z += 30) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", x0 + 1, z, x1 - 1, Math.min(z1 - 1, z + 29)));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -30 %d air", x0 + 1, z, x1 - 1, Math.min(z1 - 1, z + 29)));
		}
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 -14 rotated 0 0 run ship spawn %s", X, id));
		world.waitForChunksRender();
		context.waitTicks(50);
		ShipPose pose = pose(server);
		if (pose == null) {
			check.accept(false, id + ": spawned in the basin");
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
			return;
		}
		double surface = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			BlockPos pos = new BlockPos(X, -50, (int) Math.floor(pose.z()));
			return pos.getY() + (double) w.getFluidState(pos).getHeight(w, pos);
		});
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, water surface %.3f", id, pose.x(), pose.y(), pose.z(), surface));
		check.accept(Math.abs(pose.y() - (surface - TYPE.hull().waterlineY)) < 0.25,
				String.format(Locale.ROOT, "%s floats on the surface (y %.2f, water %.2f)", id, pose.y(), surface));
		context.runOnClient(mc -> mc.options.hudHidden = true);

		// at rest the sails furl after 5 s (furlSailWhenStopped): the ship was spawned stopped
		context.waitTicks(100);
		float[] s = sails(context);
		check.accept(s[0] == 0 && s[1] < 0.15f, String.format(Locale.ROOT, "%s: the sails are furled when the ship is stopped (open %.2f)", id, s[1]));
		look(server, pose, 36, 12.5, 44, 0, 9.5, -2);
		context.waitTicks(15);
		shot.accept(id + "_0_voiles_ferlees");
		boolean furl = server.computeOnServer(srv -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(TYPE);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		context.waitTicks(70);
		s = sails(context);
		check.accept(s[0] == 1 && s[1] > 0.9f, String.format(Locale.ROOT, "%s: the sails are set again (open %.2f)", id, s[1]));
		boolean anims = context.computeOnClient(mc -> {
			fr.medievalships.client.model.BbModel m = fr.medievalships.client.render.ShipModels.get(fr.medievalships.client.render.ShipModels.BLUE_FRIGATE);
			if (m == null || m.textureCount() != 2) {
				return false;
			}
			for (String a : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "rope_sway", "door_0"}) {
				if (!m.animations.containsKey(a)) {
					return false;
				}
			}
			return true;
		});
		check.accept(anims, id + ": the model loaded in game has its two textures and its animations (sails, helm, flags, lanterns, ropes, door)");
		// the reference's viewpoint (port bow), then the side, front, back and top views
		double[][] eyes = {{36, 12.5, 44}, {52, 8, 0}, {0, 10, 56}, {-2, 11, -52}, {0.05, 75, 2}};
		double[][] targets = {{0, 9.5, -2}, {0, 12, 0}, {0, 13, 0}, {0, 12, -8}, {0, 0, 2}};
		String[] names = {"1_reference_avant_babord", "2_cote", "3_avant", "4_arriere", "5_dessus"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(15);
			shot.accept(id + "_" + names[k]);
		}
		server.runOnServer(srv -> fr.medievalships.data.ConfigManager.ship(TYPE).furlSailWhenStopped = furl);

		// walking aboard: main deck, quarterdeck, captain's cabin, hold
		server.runCommand("gamemode survival @a");
		double[][] spots = {
				{0.0, FrigateLayout.MAIN_DECK_Y, -2.5, 180},
				{1.6, FrigateLayout.QUARTERDECK_Y, -12.5, 180},
				{0.0, FrigateLayout.CABIN_FLOOR_Y, -12.0, 180},
				{0.0, FrigateLayout.LOWER_FLOOR_Y, -6.0, 0}};
		String[] where = {"main deck", "quarterdeck", "captain's cabin", "hold"};
		for (int k = 0; k < spots.length; k++) {
			ShipPose p = pose(server);
			tp(server, p, spots[k][0], spots[k][1] + 0.02, spots[k][2], (float) spots[k][3], 10);
			context.waitTicks(30);
			double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
					mc.player.isOnGround() ? 1 : 0, mc.player.isTouchingWater() ? 1 : 0});
			double[] l = pose(server).toLocal(c[0], c[1], c[2]);
			log.accept(String.format(Locale.ROOT, "%s %s: local %.2f %.3f %.2f, on ground %s, water %s", id, where[k], l[0], l[1], l[2], c[3], c[4]));
			check.accept(Math.abs(l[1] - spots[k][1]) < 0.08 && c[3] > 0 && c[4] == 0,
					String.format(Locale.ROOT, "%s: standing in the %s (local y %.3f)", id, where[k], l[1]));
			shot.accept(id + "_" + (6 + k) + "_" + where[k].replace(' ', '_').replace("'", ""));
		}
		// walking on the main deck while the ship is still: a few steps forward, still on the deck
		tp(server, pose(server), 0.0, FrigateLayout.MAIN_DECK_Y + 0.02, 0.0, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(25);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] c2 = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
				mc.player.isOnGround() ? 1 : 0});
		double[] l2 = pose(server).toLocal(c2[0], c2[1], c2[2]);
		log.accept(String.format(Locale.ROOT, "%s walked on the main deck to local %.2f %.3f %.2f", id, l2[0], l2[1], l2[2]));
		check.accept(l2[2] > 1.0 && Math.abs(l2[1] - FrigateLayout.MAIN_DECK_Y) < 0.1, String.format(Locale.ROOT,
				"%s: the player walks on the main deck (moved to z %.2f, y %.3f)", id, l2[2], l2[1]));
		// the cabin door
		boolean opened = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			e.toggleDoor(FrigateLayout.CABIN_DOOR);
			return e.doorOpen(FrigateLayout.CABIN_DOOR);
		});
		check.accept(opened, id + ": the cabin door opens");

		// at the helm: the big ship gathers way slowly, then a turn to port
		ShipPose p0 = pose(server);
		tp(server, p0, 0.0, FrigateLayout.QUARTERDECK_Y + 0.02, FrigateLayout.PILOT_Z, 0, 10);
		context.waitTicks(10);
		server.runOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity e = ship(srv.getOverworld());
			if (e != null) {
				e.seat(player, ShipGeometry.PILOT_SEAT);
			}
		});
		context.waitTicks(10);
		ShipPose start = pose(server);
		int sounds0 = context.computeOnClient(mc -> fr.medievalships.client.FrigateEffects.sounds);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(100);
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(50);
		float[] helm = context.computeOnClient(mc -> {
			ShipEntity e = clientShip(mc);
			return e == null ? new float[] {0, 0, 0} : new float[] {e.helmVisual, e.sailOpen, e.syncedSpeed()};
		});
		log.accept(String.format(Locale.ROOT, "%s at the helm: helm %.2f, sails open %.2f, speed %.2f", id, helm[0], helm[1], helm[2]));
		check.accept(Math.abs(helm[0]) > 0.3f, String.format(Locale.ROOT, "%s: the wheel and the rudder turn with the helm (%.2f)", id, helm[0]));
		check.accept(helm[1] > 0.9f, String.format(Locale.ROOT, "%s: the sails are set under way (open %.2f)", id, helm[1]));
		context.runOnClient(mc -> mc.options.hudHidden = false);
		context.waitTicks(2);
		shot.accept(id + "_10_a_la_barre");
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose moved = pose(server);
		double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
		log.accept(String.format(Locale.ROOT, "%s moved %.2f blocks in 7.5 s at the helm", id, dist));
		check.accept(dist > 1.0 && dist < 30, String.format(Locale.ROOT, "%s sails under the player's control (moved %.2f)", id, dist));
		int sounds = context.computeOnClient(mc -> fr.medievalships.client.FrigateEffects.sounds) - sounds0;
		check.accept(sounds > 0, String.format(Locale.ROOT, "%s: the hull creaks and the bow wave washes under way (%d sounds)", id, sounds));
		// under way, seen from outside: the foam at the bow, the sails set
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		context.runOnClient(mc -> mc.options.hudHidden = true);
		look(server, pose(server), 22, 7, 32, 0, 7, 10);
		context.waitTicks(12);
		float speed = context.computeOnClient(mc -> {
			ShipEntity e = clientShip(mc);
			return e == null ? 0f : e.syncedSpeed();
		});
		check.accept(speed > 0.6f, String.format(Locale.ROOT, "%s: still under way, foam at the bow (speed %.2f)", id, speed));
		shot.accept(id + "_11_sous_voiles");
		context.runOnClient(mc -> mc.options.hudHidden = false);
		server.runOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			if (e != null) {
				e.discard();
			}
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}
}
