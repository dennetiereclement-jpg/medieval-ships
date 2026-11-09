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
import net.minecraft.text.Text;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.FortressLayout;
import fr.medievalships.core.Gangplank;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The Fortress Ship in a real game (called once from {@link ShipClientGameTest}, about 75 s of game time): placed in a
 * basin beside a stone quay and floating at its waterline, the model loaded with its two textures and animations, the
 * three references' viewpoints and a top view photographed (no HUD), the player stands on every level (waist,
 * forecastle, quarterdeck, the keep's roof, the turret, the captain's cabin, the officers' room, the mess, the hold,
 * the crew quarters), walks on the waist, the doors open; the furnished rooms are photographed, the player sits on
 * three seats (the captain's chair, the commander's chair of the war table, a bench of the mess) and stands up beside
 * each, walks among the cargo of the hold and across the cabin to the desk; the gangplank is deployed onto the quay and
 * retracted with its lever, and the ship sails a few seconds under the player's control from the helm.
 */
public final class FortressShipGameTest {
	private static final ShipType TYPE = Ships.FORTRESS_SHIP;
	private static final int X = 3400;

	private FortressShipGameTest() {
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

	private static Gangplank.State plank(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			return s == null ? null : s.gangplankState();
		});
	}

	private static String lever(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			Text t = s == null ? null : s.useGangplankLever(srv.getOverworld());
			return t == null ? "" : t.getString();
		});
	}

	private static void waitPlank(ClientGameTestContext context, TestServerContext server, Gangplank.State want, int maxTicks) {
		for (int t = 0; t < maxTicks && plank(server) != want; t += 5) {
			context.waitTicks(5);
		}
	}

	/** Index of the passenger seat nearest to a ship-local point. */
	private static int seatNear(double x, double y, double z) {
		int best = -1;
		double bd = Double.MAX_VALUE;
		for (ShipGeometry.Seat s : TYPE.geometry().seats()) {
			double d = Math.pow(s.x() - x, 2) + Math.pow(s.y() - y, 2) + Math.pow(s.z() - z, 2);
			if (!s.pilot() && d < bd) {
				bd = d;
				best = s.index();
			}
		}
		return best;
	}

	/** The player's ship-local position, whether he stands on the ground, whether he rides a seat (client side). */
	private static double[] localPlayer(ClientGameTestContext context, TestServerContext server) {
		double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
				mc.player.isOnGround() ? 1 : 0, mc.player.hasVehicle() ? 1 : 0});
		double[] l = pose(server).toLocal(c[0], c[1], c[2]);
		return new double[] {l[0], l[1], l[2], c[3], c[4]};
	}

	/**
	 * The decoration (about 12 s): the furnished rooms photographed from inside (the decoration mods' blocks, their
	 * stand-ins when a mod is missing), the player sits on the captain's chair behind the desk, the commander's chair of
	 * the war table and a bench of the mess and stands up on the floor beside each, then walks among the cargo along the
	 * hold's centre line and across the captain's cabin from the door to the desk.
	 */
	private static void furnishedRooms(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		double c = FortressLayout.CABIN_FLOOR_Y, q = FortressLayout.QUARTERDECK_Y, lo = FortressLayout.LOWER_FLOOR_Y;
		double m = FortressLayout.MAIN_DECK_Y, f = FortressLayout.FORECASTLE_Y;
		server.runCommand("gamemode spectator @a");
		double[][] eyes = {{0.3, c + 1.62, -10.2}, {1.2, q + 1.62, -13.9}, {1.6, m + 1.62, 9.0}, {0.6, lo + 1.62, 4.8}, {0.0, lo + 1.62, 13.6},
				{1.2, f + 2.6, 4.2}};
		double[][] targets = {{0, c + 1.0, -19.0}, {-1.9, q + 0.8, -17.5}, {-0.5, m + 0.5, 16.0}, {0, lo + 0.5, -15.0}, {0, lo + 0.5, 6.0},
				{-1.0, m + 0.5, -8.0}};
		String[] names = {"m1_cabine_capitaine", "m2_salle_du_conseil", "m3_refectoire", "m4_cale", "m5_quartiers_equipage", "m6_cargaison_pont"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose(server), eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(k == 0 ? 15 : 8);
			shot.accept(id + "_" + names[k]);
		}
		server.runCommand("gamemode survival @a");
		// sitting down and standing up
		double[][] spots = {{0.0, c + 0.56, -18.45}, {-1.9, q + 0.56, -17.5}, {1.05, m + 0.56, 13.0}};
		String[] what = {"the captain's chair", "the commander's chair of the war table", "a bench of the mess"};
		for (int k = 0; k < spots.length; k++) {
			int seat = seatNear(spots[k][0], spots[k][1], spots[k][2]);
			ShipGeometry.Seat st = TYPE.geometry().seats().get(seat);
			tp(server, pose(server), st.dismountLocal()[0], st.dismountLocal()[1], st.dismountLocal()[2], 0, 10);
			context.waitTicks(5);
			boolean sat = server.computeOnServer(srv -> {
				ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
				ShipEntity e = ship(srv.getOverworld());
				return e != null && e.seat(player, seat) && e.seatOf(player) == seat;
			});
			context.waitTicks(10);
			double[] l = localPlayer(context, server);
			log.accept(String.format(Locale.ROOT, "%s on %s (seat %d): local %.2f %.3f %.2f, riding %s", id, what[k], seat, l[0], l[1], l[2], l[4]));
			check.accept(sat && l[4] > 0 && Math.abs(l[0] - st.x()) < 0.3 && Math.abs(l[2] - st.z()) < 0.3,
					String.format(Locale.ROOT, "%s: the player sits on %s (seat %d)", id, what[k], seat));
			if (k == 0) {
				shot.accept(id + "_m7_assis_au_bureau");
			}
			server.runCommand("ride @p dismount");
			context.waitTicks(15);
			l = localPlayer(context, server);
			double[] d = st.dismountLocal();
			log.accept(String.format(Locale.ROOT, "%s stood up from seat %d at local %.2f %.3f %.2f (spot %.2f %.2f %.2f), on ground %s", id, seat,
					l[0], l[1], l[2], d[0], d[1], d[2], l[3]));
			check.accept(l[4] == 0 && l[3] > 0 && Math.abs(l[1] - (d[1] - 0.02)) < 0.1 && Math.hypot(l[0] - d[0], l[2] - d[2]) < 0.6,
					String.format(Locale.ROOT, "%s: standing up from %s onto the floor beside it (local y %.3f)", id, what[k], l[1]));
		}
		// walking among the furniture: forward along the hold's centre line, aft across the captain's cabin to the desk
		tp(server, pose(server), 0.0, lo + 0.02, -10.5, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(20);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] h = localPlayer(context, server);
		log.accept(String.format(Locale.ROOT, "%s walked in the hold to local %.2f %.3f %.2f", id, h[0], h[1], h[2]));
		check.accept(h[2] > -8.0 && Math.abs(h[1] - lo) < 0.1, String.format(Locale.ROOT,
				"%s: the player walks between the cargo along the hold (z %.2f, y %.3f)", id, h[2], h[1]));
		tp(server, pose(server), 0.0, c + 0.02, -10.2, 180, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(22);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] w = localPlayer(context, server);
		log.accept(String.format(Locale.ROOT, "%s walked in the captain's cabin to local %.2f %.3f %.2f", id, w[0], w[1], w[2]));
		check.accept(w[2] < -14.0 && w[2] > -16.6 && Math.abs(w[1] - c) < 0.1, String.format(Locale.ROOT,
				"%s: the player walks across the furnished cabin from the door to the desk (z %.2f, y %.3f)", id, w[2], w[1]));
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 -40 0 30", X));
		context.waitTicks(20);
		// a basin 64 wide and 100 long, 14 deep; a stone quay along its west side (the ship's starboard side) one block
		// above the water, for the gangplank
		int x0 = X - 32, x1 = X + 32, z0 = -50, z1 = 50, top = -50;
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
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 -6 rotated 0 0 run ship spawn %s", X, id));
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
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f yaw %.1f, water surface %.3f", id, pose.x(), pose.y(), pose.z(), pose.yaw(), surface));
		check.accept(Math.abs(pose.y() - (surface - TYPE.hull().waterlineY)) < 0.25,
				String.format(Locale.ROOT, "%s floats on the surface (y %.2f, water %.2f)", id, pose.y(), surface));
		// the stone quay on the starboard side, its top one block above the water, from 9 to 13 blocks out
		Gangplank.Spec spec = Gangplank.of(id);
		check.accept(spec != null, id + ": has a gangplank spec");
		if (spec == null) {
			server.runOnServer(srv -> ship(srv.getOverworld()).discard());
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
			return;
		}
		double[] qa = pose.toWorld(spec.hx() + spec.o() * 6.5, 0, spec.hz() - 3.0), qb = pose.toWorld(spec.hx() + spec.o() * 10.5, 0, spec.hz() + 3.0);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -49 %d stone", (int) Math.floor(Math.min(qa[0], qb[0])),
				(int) Math.floor(Math.min(qa[2], qb[2])), (int) Math.floor(Math.max(qa[0], qb[0])), (int) Math.floor(Math.max(qa[2], qb[2]))));
		context.runOnClient(mc -> mc.options.hudHidden = true);
		boolean anims = context.computeOnClient(mc -> {
			fr.medievalships.client.model.BbModel m = fr.medievalships.client.render.ShipModels.get(fr.medievalships.client.render.ShipModels.FORTRESS_SHIP);
			if (m == null || m.textureCount() != 2) {
				return false;
			}
			for (String a : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "rope_sway", "door_0", "door_4"}) {
				if (!m.animations.containsKey(a)) {
					return false;
				}
			}
			return true;
		});
		check.accept(anims, id + ": the model loaded in game has its two textures and its animations");
		boolean furl = server.computeOnServer(srv -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(TYPE);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		context.waitTicks(40);
		// the references' viewpoints (main: port side; second: port bow, low; third: starboard quarter), the stern and the top
		double[][] eyes = {{60, 10.5, 12}, {30, 3.5, 40}, {-52, 6.0, -14}, {22, 15, -36}, {0.05, 80, 3}};
		double[][] targets = {{0, 11.5, 1.5}, {0, 10.5, -3}, {0, 11, 1}, {0, 10, -12}, {0, 0, 3}};
		String[] names = {"1_reference_principale_babord", "2_reference_avant_babord", "3_reference_tribord_arriere", "4_chateau_arriere", "5_dessus"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(15);
			shot.accept(id + "_" + names[k]);
		}
		server.runOnServer(srv -> fr.medievalships.data.ConfigManager.ship(TYPE).furlSailWhenStopped = furl);

		// standing on every level, all doors open
		server.runOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			for (int d = 0; d < 5; d++) {
				if (!e.doorOpen(d)) {
					e.toggleDoor(d);
				}
			}
		});
		boolean doors = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			for (int d = 0; d < 5; d++) {
				if (!e.doorOpen(d)) {
					return false;
				}
			}
			return true;
		});
		check.accept(doors, id + ": the five doors open (cabin, keep, mess, crew quarters, turret)");
		server.runCommand("gamemode survival @a");
		double[][] spots = {
				{0.0, FortressLayout.MAIN_DECK_Y, -7.0, 180},
				{0.0, FortressLayout.FORECASTLE_Y, 11.0, 0},
				{2.0, FortressLayout.QUARTERDECK_Y, -11.0, 180},
				{0.0, FortressLayout.KEEP_Y, -13.95, 180},
				{0.0, FortressLayout.KEEP_Y, -16.5, 180},
				{0.0, FortressLayout.CABIN_FLOOR_Y, -14.0, 180},
				{0.0, FortressLayout.QUARTERDECK_Y, -16.0, 180},
				{0.0, FortressLayout.MAIN_DECK_Y, 10.0, 0},
				{0.0, FortressLayout.LOWER_FLOOR_Y, -8.0, 180},
				{0.0, FortressLayout.LOWER_FLOOR_Y, 11.0, 0}};
		String[] where = {"waist", "forecastle", "quarterdeck", "keep's roof", "turret", "captain's cabin", "officers' room", "crew's mess", "hold",
				"crew quarters"};
		for (int k = 0; k < spots.length; k++) {
			ShipPose p = pose(server);
			tp(server, p, spots[k][0], spots[k][1] + 0.02, spots[k][2], (float) spots[k][3], 10);
			context.waitTicks(20);
			double[] c = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(),
					mc.player.isOnGround() ? 1 : 0, mc.player.isTouchingWater() ? 1 : 0});
			double[] l = pose(server).toLocal(c[0], c[1], c[2]);
			log.accept(String.format(Locale.ROOT, "%s %s: local %.2f %.3f %.2f, on ground %s, water %s", id, where[k], l[0], l[1], l[2], c[3], c[4]));
			check.accept(Math.abs(l[1] - spots[k][1]) < 0.08 && c[3] > 0 && c[4] == 0,
					String.format(Locale.ROOT, "%s: standing in the %s (local y %.3f)", id, where[k], l[1]));
			if (k == 0 || k == 3 || k == 5 || k == 8) {
				shot.accept(id + "_" + (6 + k) + "_" + where[k].replace(' ', '_').replace("'", ""));
			}
		}
		// a few steps forward on the waist
		tp(server, pose(server), 0.0, FortressLayout.MAIN_DECK_Y + 0.02, -7.5, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(20);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] c2 = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		double[] l2 = pose(server).toLocal(c2[0], c2[1], c2[2]);
		log.accept(String.format(Locale.ROOT, "%s walked on the waist to local %.2f %.3f %.2f", id, l2[0], l2[1], l2[2]));
		check.accept(l2[2] > -6.5 && Math.abs(l2[1] - FortressLayout.MAIN_DECK_Y) < 0.1,
				String.format(Locale.ROOT, "%s: the player walks on the waist (moved to z %.2f, y %.3f)", id, l2[2], l2[1]));
		furnishedRooms(context, server, check, log, shot);
		server.runCommand("gamemode survival @a");

		// the gangplank: deployed onto the quay with its lever, then retracted
		check.accept(plank(server) == Gangplank.State.RETRACTED, id + ": the gangplank is stowed at spawn");
		String msg = lever(server);
		context.waitTicks(4);
		Gangplank.State st = plank(server);
		log.accept(String.format(Locale.ROOT, "%s: lever -> %s (%s)", id, st, msg));
		check.accept(st == Gangplank.State.DEPLOYING || st == Gangplank.State.DEPLOYED, id + ": the lever deploys the gangplank onto the quay (" + msg + ")");
		waitPlank(context, server, Gangplank.State.DEPLOYED, 80);
		check.accept(plank(server) == Gangplank.State.DEPLOYED, id + ": the gangplank lies on the quay");
		server.runCommand("gamemode spectator @a");
		look(server, pose(server), spec.hx() + spec.o() * 9.0, spec.hy() + 3.0, spec.hz() + 9.0, spec.hx() + spec.o() * 3.0, spec.hy() - 1.5, spec.hz());
		context.waitTicks(10);
		shot.accept(id + "_16_passerelle_deployee");
		lever(server);
		waitPlank(context, server, Gangplank.State.RETRACTED, 80);
		check.accept(plank(server) == Gangplank.State.RETRACTED, id + ": the gangplank is stowed again");
		server.runCommand("gamemode survival @a");

		// at the helm: the heaviest ship gathers way slowly, then a turn to port
		ShipPose p0 = pose(server);
		tp(server, p0, 0.0, FortressLayout.QUARTERDECK_Y + 0.02, FortressLayout.PILOT_Z, 0, 10);
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
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(100);
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(40);
		float[] helm = context.computeOnClient(mc -> {
			ShipEntity e = clientShip(mc);
			return e == null ? new float[] {0, 0, 0} : new float[] {e.helmVisual, e.sailOpen, e.syncedSpeed()};
		});
		log.accept(String.format(Locale.ROOT, "%s at the helm: helm %.2f, sails open %.2f, speed %.2f", id, helm[0], helm[1], helm[2]));
		check.accept(Math.abs(helm[0]) > 0.3f, String.format(Locale.ROOT, "%s: the wheel and the rudder turn with the helm (%.2f)", id, helm[0]));
		context.runOnClient(mc -> mc.options.hudHidden = false);
		context.waitTicks(2);
		shot.accept(id + "_17_a_la_barre");
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose moved = pose(server);
		double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
		log.accept(String.format(Locale.ROOT, "%s moved %.2f blocks in 7 s at the helm", id, dist));
		check.accept(dist > 0.8 && dist < 30, String.format(Locale.ROOT, "%s sails under the player's control (moved %.2f)", id, dist));
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			if (e != null) {
				e.discard();
			}
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}
}
