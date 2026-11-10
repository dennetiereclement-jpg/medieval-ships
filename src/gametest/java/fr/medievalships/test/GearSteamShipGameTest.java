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

import fr.medievalships.core.Gangplank;
import fr.medievalships.core.GearSteamLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The Gear Steamship in a real game (called once from {@link ShipClientGameTest}, about 45 s of game time): placed
 * on a basin and floating at its waterline, the model loaded with its two textures and its animations, the
 * reference's viewpoint (starboard bow) and the side, stern and top views photographed (no HUD), then the furnished
 * engine room, engine, crew quarters, captain's cabin and hold; the player stands on the waist, the forecastle, the
 * engine house roof, the poop deck, the bridge, in the engine room, the crew quarters, the captain's cabin and the
 * hold, sits in the captain's chair and stands up on the cabin floor, walks on the waist, the engine room door opens, the gangplank is
 * put out and stowed again, and the ship steams under the player's control from the helm (the wheel turns, the
 * gears turn, the funnel smokes, the engine beats); then it is removed.
 */
public final class GearSteamShipGameTest {
	private static final ShipType TYPE = Ships.GEAR_STEAMSHIP;
	private static final int X = 4900;   // open water of its own, away from the props (x 1000..2300), the drawbridge (2560..2800) and the other city ships (fortress 3368..3432, royal lion 3868..3932)

	private GearSteamShipGameTest() {
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
		// a basin 56 wide, 100 long and 14 deep, walled with glass up to the water
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
		boolean furl = server.computeOnServer(srv -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(TYPE);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		context.runOnClient(mc -> mc.options.hudHidden = true);
		boolean anims = context.computeOnClient(mc -> {
			fr.medievalships.client.model.BbModel m = fr.medievalships.client.render.ShipModels.get(fr.medievalships.client.render.ShipModels.GEAR_STEAMSHIP);
			if (m == null || m.textureCount() != 2) {
				return false;
			}
			for (String a : new String[] {"sail_wind", "sail_furl", "steer", "lantern_sway", "engine", "door_0", "door_3"}) {
				if (!m.animations.containsKey(a)) {
					return false;
				}
			}
			return m.bonesByName.containsKey("gear_big_s") && m.bonesByName.containsKey("crate_hang");
		});
		check.accept(anims, id + ": the model loaded in game has its two textures, its animations and its gears");
		context.waitTicks(40);
		// the reference's viewpoint (starboard bow), then the side, the stern and the top
		double[][] eyes = {{-38, 12.6, 14.7}, {-55, 9, 1}, {-14, 12, -46}, {0.05, 70, 1}};
		double[][] targets = {{0, 8.5, 1.5}, {0, 9, 1}, {0, 8, -12}, {0, 0, 1}};
		String[] names = {"1_reference_avant_tribord", "2_cote", "3_arriere", "4_dessus"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(15);
			shot.accept(id + "_" + names[k]);
		}
		// the furnished rooms (the decoration mods' blocks drawn by the ship, the engine, the galley, the cargo)
		double mm = GearSteamLayout.MAIN_DECK_Y, pp = GearSteamLayout.POOP_Y, hh = GearSteamLayout.HOLD_FLOOR_Y;
		double[][] roomEyes = {{0.2, mm + 1.62, 4.1}, {-0.6, mm + 1.62, -0.3}, {2.6, mm + 1.62, -7.6}, {-0.4, pp + 1.62, -11.2}, {0.4, hh + 1.62, 3.0}};
		double[][] roomTargets = {{-0.3, mm + 1.2, -4.5}, {3.0, mm + 1.5, 1.8}, {-0.5, mm + 0.8, -15.0}, {0.3, pp + 0.9, -7.2}, {0.0, hh + 0.9, -14.0}};
		String[] roomNames = {"16_salle_des_machines", "17_machine_a_vapeur", "18_quartiers_equipage", "19_cabine_capitaine", "20_cale"};
		for (int k = 0; k < roomEyes.length; k++) {
			look(server, pose, roomEyes[k][0], roomEyes[k][1], roomEyes[k][2], roomTargets[k][0], roomTargets[k][1], roomTargets[k][2]);
			context.waitTicks(12);
			shot.accept(id + "_" + roomNames[k]);
		}
		context.runOnClient(mc -> mc.options.hudHidden = false);

		// walking aboard: every level and room
		server.runCommand("gamemode survival @a");
		double m = GearSteamLayout.MAIN_DECK_Y;
		double[][] spots = {
				{-1.5, m, 9.0, 0},
				{0.0, GearSteamLayout.FORECASTLE_Y, 14.0, 0},
				{3.6, GearSteamLayout.ENGINE_ROOF_Y, 1.0, 180},
				{1.5, GearSteamLayout.POOP_Y, -14.0, 180},
				{0.0, GearSteamLayout.BRIDGE_Y, -10.0, 0},
				{3.0, m, -2.0, 180},
				{0.0, m, -14.8, 0},
				{0.0, GearSteamLayout.CABIN_FLOOR_Y, -9.8, 180},
				{0.0, GearSteamLayout.HOLD_FLOOR_Y, -6.0, 0},
				{0.0, m, -19.0, 180}};
		String[] where = {"waist", "forecastle", "engine house roof", "poop deck", "bridge", "engine room", "crew quarters", "captain's cabin", "hold",
				"stern gallery"};
		for (int k = 0; k < spots.length; k++) {
			ShipPose p = pose(server);
			tp(server, p, spots[k][0], spots[k][1] + 0.02, spots[k][2], (float) spots[k][3], 10);
			context.waitTicks(25);
			double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
					mc.player.isOnGround() ? 1 : 0, mc.player.isTouchingWater() ? 1 : 0});
			double[] l = pose(server).toLocal(c[0], c[1], c[2]);
			log.accept(String.format(Locale.ROOT, "%s %s: local %.2f %.3f %.2f, on ground %s, water %s", id, where[k], l[0], l[1], l[2], c[3], c[4]));
			check.accept(Math.abs(l[1] - spots[k][1]) < 0.08 && c[3] > 0 && c[4] == 0,
					String.format(Locale.ROOT, "%s: standing in the %s (local y %.3f)", id, where[k], l[1]));
			if (k == 5 || k == 7 || k == 4) {
				shot.accept(id + "_" + (5 + k) + "_" + where[k].replace(' ', '_').replace("'", ""));
			}
		}
		// 1.28.0: the waterline now runs 0.4 block under the hold's floor; seen from the foot of the companionway, no sheet
		// of water is drawn across the hold, and the chunk renderer hides every water block of the basin inside the hull
		server.runCommand("gamemode spectator @a");
		look(server, pose(server), 2.25, GearSteamLayout.HOLD_FLOOR_Y + 1.62, 9.7, 0.0, GearSteamLayout.HOLD_FLOOR_Y + 0.3, -1.0);
		context.waitTicks(12);
		shot.accept(id + "_cale_niveau_mer");
		DryWaterGameTest.check(context, TYPE, check, log);
		server.runCommand("gamemode survival @a");
		// the captain's chair (the first seat of the furniture), then standing up on the cabin floor
		boolean sat = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity e = ship(srv.getOverworld());
			return e != null && e.seat(player, 1) && e.seatOf(player) == 1;
		});
		context.waitTicks(10);
		check.accept(sat, id + ": the player sits in the captain's chair");
		server.runCommand("ride @p dismount");
		context.waitTicks(15);
		double[] cs = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
				mc.player.hasVehicle() ? 1 : 0});
		double[] lc = pose(server).toLocal(cs[0], cs[1], cs[2]);
		log.accept(String.format(Locale.ROOT, "%s stood up from the captain's chair at local %.2f %.3f %.2f", id, lc[0], lc[1], lc[2]));
		check.accept(cs[3] == 0 && Math.abs(lc[1] - GearSteamLayout.CABIN_FLOOR_Y) < 0.1 && Math.abs(lc[2] + 9.5) < 1.0,
				String.format(Locale.ROOT, "%s: stands up from the captain's chair on the cabin floor (local y %.3f, z %.2f)", id, lc[1], lc[2]));
		// a few steps on the waist while the ship is still
		tp(server, pose(server), -1.5, m + 0.02, 5.8, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(15);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] c2 = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		double[] l2 = pose(server).toLocal(c2[0], c2[1], c2[2]);
		log.accept(String.format(Locale.ROOT, "%s walked on the waist to local %.2f %.3f %.2f", id, l2[0], l2[1], l2[2]));
		check.accept(l2[2] > 7.0 && Math.abs(l2[1] - m) < 0.1, String.format(Locale.ROOT, "%s: the player walks on the waist (z %.2f, y %.3f)", id,
				l2[2], l2[1]));
		boolean opened = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			e.toggleDoor(GearSteamLayout.ENGINE_DOOR);
			return e.doorOpen(GearSteamLayout.ENGINE_DOOR);
		});
		check.accept(opened, id + ": the engine room door opens");
		// the gangplank: put out (as deployed onto a quay), then stowed again
		Gangplank.State[] states = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			if (e == null || e.gangplank() == null) {
				return new Gangplank.State[] {null, null};
			}
			e.forceGangplank(Gangplank.State.DEPLOYED, 30f);
			Gangplank.State out = e.gangplankState();
			return new Gangplank.State[] {out, null};
		});
		context.waitTicks(10);
		look(server, pose(server), -14, 7, 16, -4, 4, 8);
		context.runOnClient(mc -> mc.options.hudHidden = true);
		context.waitTicks(10);
		shot.accept(id + "_13_passerelle");
		context.runOnClient(mc -> mc.options.hudHidden = false);
		Gangplank.State back = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			if (e == null) {
				return null;
			}
			e.forceGangplank(Gangplank.State.RETRACTED, 0f);
			return e.gangplankState();
		});
		check.accept(states[0] == Gangplank.State.DEPLOYED && back == Gangplank.State.RETRACTED,
				id + ": the gangplank is put out and stowed again (" + states[0] + ", " + back + ")");

		// at the helm on the bridge: the steamer gathers way, then a turn to starboard
		ShipPose p0 = pose(server);
		tp(server, p0, 0.0, GearSteamLayout.BRIDGE_Y + 0.02, GearSteamLayout.PILOT_Z, 0, 10);
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
		int puffs0 = context.computeOnClient(mc -> fr.medievalships.client.GearSteamEffects.puffs);
		int sounds0 = context.computeOnClient(mc -> fr.medievalships.client.GearSteamEffects.sounds);
		float wheel0 = context.computeOnClient(mc -> {
			ShipEntity e = clientShip(mc);
			return e == null ? 0f : e.wheelPhase;
		});
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(100);
		context.getInput().holdKey(o -> o.rightKey);
		context.waitTicks(40);
		float[] helm = context.computeOnClient(mc -> {
			ShipEntity e = clientShip(mc);
			return e == null ? new float[] {0, 0, 0} : new float[] {e.helmVisual, e.wheelPhase, e.syncedSpeed()};
		});
		log.accept(String.format(Locale.ROOT, "%s at the helm: helm %.2f, engine phase %.2f -> %.2f, speed %.2f", id, helm[0], wheel0, helm[1], helm[2]));
		check.accept(Math.abs(helm[0]) > 0.3f, String.format(Locale.ROOT, "%s: the wheel and the rudder turn with the helm (%.2f)", id, helm[0]));
		check.accept(Math.abs(helm[1] - wheel0) > 0.5f, String.format(Locale.ROOT, "%s: the gears turn under way (phase %.2f)", id, helm[1] - wheel0));
		shot.accept(id + "_14_a_la_barre");
		context.getInput().releaseKey(o -> o.rightKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose moved = pose(server);
		double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
		log.accept(String.format(Locale.ROOT, "%s moved %.2f blocks in 7 s at the helm", id, dist));
		check.accept(dist > 1.0 && dist < 30, String.format(Locale.ROOT, "%s steams under the player's control (moved %.2f)", id, dist));
		int puffs = context.computeOnClient(mc -> fr.medievalships.client.GearSteamEffects.puffs) - puffs0;
		int sounds = context.computeOnClient(mc -> fr.medievalships.client.GearSteamEffects.sounds) - sounds0;
		check.accept(puffs > 20 && sounds > 0, String.format(Locale.ROOT, "%s: the funnel smokes and the engine beats (%d puffs, %d sounds)", id, puffs,
				sounds));
		// under way, seen from outside
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		context.runOnClient(mc -> mc.options.hudHidden = true);
		look(server, pose(server), -24, 9, 30, 0, 9, 6);
		context.waitTicks(12);
		shot.accept(id + "_15_en_route");
		context.runOnClient(mc -> mc.options.hudHidden = false);
		server.runOnServer(srv -> {
			fr.medievalships.data.ConfigManager.ship(TYPE).furlSailWhenStopped = furl;
			ShipEntity e = ship(srv.getOverworld());
			if (e != null) {
				e.discard();
			}
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}
}
