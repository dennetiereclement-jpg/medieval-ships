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

import fr.medievalships.core.Gangplank;
import fr.medievalships.core.RoyalLionLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The Royal Lion Ship in a real game (called once from {@link ShipClientGameTest}, about 70 s of game time): placed on
 * a basin beside a stone quay and floating at its waterline, the model loaded with its two textures and its
 * animations, the views of the references photographed (no HUD), the player stands on the main deck, the forecastle,
 * the quarterdeck, in the captain's cabin, the royal state room, the crew quarters and the cargo hold, walks on the main
 * deck, the doors open; the furnished rooms are photographed, the player sits on three seats (the captain's chair, a
 * velvet chair of the state room, a bench of the crew's mess) and stands up beside each, walks among the cargo of the
 * hold and across the cabin; the gangplank is deployed onto the quay and retracted with its lever, then the ship sails
 * under the player's control from the helm (the wheel and the rudder turn, the sails stay set) and is removed.
 */
public final class RoyalLionShipGameTest {
	private static final ShipType TYPE = Ships.ROYAL_LION_SHIP;
	private static final int X = 3900;

	private RoyalLionShipGameTest() {
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

	/** Fills the ship-local box (x0..x1, z0..z1) at world heights y0..y1 with a block. */
	private static void fillLocal(TestServerContext server, ShipPose p, double x0, double x1, double z0, double z1, int y0, int y1, String block) {
		double[] a = p.toWorld(x0, 0, z0), b = p.toWorld(x1, 0, z1);
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d %s", (int) Math.floor(Math.min(a[0], b[0])), y0,
				(int) Math.floor(Math.min(a[2], b[2])), (int) Math.floor(Math.max(a[0], b[0])), y1, (int) Math.floor(Math.max(a[2], b[2])), block));
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
	 * The decoration (about 10 s): the furnished rooms photographed from inside (the decoration mods' blocks, their
	 * stand-ins when a mod is missing), the player sits on the captain's chair, a velvet chair of the state room and a
	 * bench of the crew's mess and stands up on the floor beside each, then walks among the furniture along the hold's
	 * centre line and across the captain's cabin to the window seat.
	 */
	private static void furnishedRooms(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		double c = RoyalLionLayout.CABIN_FLOOR_Y, s = RoyalLionLayout.STATEROOM_FLOOR_Y, lo = RoyalLionLayout.LOWER_FLOOR_Y;
		double m = RoyalLionLayout.MAIN_DECK_Y, q = RoyalLionLayout.QUARTERDECK_Y;
		server.runCommand("gamemode spectator @a");
		double[][] eyes = {{0.3, c + 1.62, -9.2}, {0.6, c + 1.62, -18.4}, {0.0, s + 1.62, -13.0}, {1.0, lo + 1.62, -4.0}, {1.5, lo + 1.62, -2.1},
				{0.0, q + 3.0, -8.2}};
		double[][] targets = {{0, c + 1.0, -19.5}, {0, c + 0.8, -8.5}, {0, s + 0.8, -19.5}, {0.5, lo + 0.6, -15.0}, {0, lo + 0.5, 14.0},
				{0, m + 0.5, 8.0}};
		String[] names = {"m1_cabine_vers_poupe", "m2_cabine_vers_porte", "m3_salle_apparat", "m4_quartiers_equipage", "m5_cale", "m6_cargaison_pont"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose(server), eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(k == 0 ? 15 : 8);
			shot.accept(id + "_" + names[k]);
		}
		server.runCommand("gamemode survival @a");
		// sitting down and standing up
		double[][] spots = {{-2.75, c + 0.56, -15.0}, {1.05, s + 0.5, -16.0}, {2.55, lo + 0.56, -10.4}};
		String[] what = {"the captain's chair", "a velvet chair of the state room", "a bench of the crew's mess"};
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
		// walking among the furniture: forward along the hold's centre line, aft across the captain's cabin
		tp(server, pose(server), 0.6, lo + 0.02, 0.3, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(20);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] h = localPlayer(context, server);
		log.accept(String.format(Locale.ROOT, "%s walked in the hold to local %.2f %.3f %.2f", id, h[0], h[1], h[2]));
		check.accept(h[2] > 2.5 && Math.abs(h[1] - lo) < 0.1, String.format(Locale.ROOT,
				"%s: the player walks between the cargo along the hold (z %.2f, y %.3f)", id, h[2], h[1]));
		tp(server, pose(server), 0.0, c + 0.02, -11.8, 180, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(22);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] w = localPlayer(context, server);
		log.accept(String.format(Locale.ROOT, "%s walked in the captain's cabin to local %.2f %.3f %.2f", id, w[0], w[1], w[2]));
		check.accept(w[2] < -15.0 && Math.abs(w[1] - c) < 0.6, String.format(Locale.ROOT,
				"%s: the player walks across the furnished cabin towards the stern windows (z %.2f, y %.3f)", id, w[2], w[1]));
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 -40 0 30", X));
		context.waitTicks(20);
		// a basin 64 wide, 100 long and 14 deep, walled with glass up to the water
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
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 -12 rotated 0 0 run ship spawn %s", X, id));
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
		boolean furl = server.computeOnServer(srv -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(TYPE);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		context.waitTicks(30);
		boolean anims = context.computeOnClient(mc -> {
			fr.medievalships.client.model.BbModel m = fr.medievalships.client.render.ShipModels.get(fr.medievalships.client.render.ShipModels.ROYAL_LION_SHIP);
			if (m == null || m.textureCount() != 2) {
				return false;
			}
			for (String a : new String[] {"sail_wind", "sail_furl", "steer", "flag_wave", "lantern_sway", "rope_sway", "door_0", "door_1", "door_2",
					"door_3"}) {
				if (!m.animations.containsKey(a)) {
					return false;
				}
			}
			return true;
		});
		check.accept(anims, id + ": the model loaded in game has its two textures and its animations (sails, helm, pennants, lanterns, ropes, doors)");
		// the viewpoints of the references (071: starboard bow; 044, 126: port bow; the stern), then the side and the top
		double[][] eyes = {{-36, 6, 25}, {58, 22, 14}, {46, 10, 36}, {-22, 17, -36}, {60, 12, 4}, {0.05, 80, 2}};
		double[][] targets = {{0, 12, -1}, {0, 12.5, 0}, {0, 12, -1}, {0, 9, -13}, {0, 13, 4}, {0, 0, 2}};
		String[] names = {"1_reference_071", "2_reference_044", "3_reference_126", "4_poupe", "5_cote", "6_dessus"};
		for (int k = 0; k < eyes.length; k++) {
			look(server, pose, eyes[k][0], eyes[k][1], eyes[k][2], targets[k][0], targets[k][1], targets[k][2]);
			context.waitTicks(15);
			shot.accept(id + "_" + names[k]);
		}
		server.runOnServer(srv -> fr.medievalships.data.ConfigManager.ship(TYPE).furlSailWhenStopped = furl);

		// walking aboard: every deck and every room
		server.runCommand("gamemode survival @a");
		double[][] spots = {
				{0.0, RoyalLionLayout.MAIN_DECK_Y, 1.5, 180},
				{0.0, RoyalLionLayout.FORECASTLE_Y, 15.5, 0},
				{1.6, RoyalLionLayout.QUARTERDECK_Y, -10.6, 180},
				{0.0, RoyalLionLayout.CABIN_FLOOR_Y, -12.5, 180},
				{2.0, RoyalLionLayout.STATEROOM_FLOOR_Y, -16.0, 180},
				{1.0, RoyalLionLayout.LOWER_FLOOR_Y, -10.0, 180},
				{0.0, RoyalLionLayout.LOWER_FLOOR_Y, 2.0, 0}};
		String[] where = {"main deck", "forecastle", "quarterdeck", "captain's cabin", "royal state room", "crew quarters", "cargo hold"};
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
			shot.accept(id + "_" + (7 + k) + "_" + where[k].replace(' ', '_').replace("'", ""));
		}
		// walking on the main deck while the ship is still: a few steps forward, still on the deck
		tp(server, pose(server), 0.6, RoyalLionLayout.MAIN_DECK_Y + 0.02, 0.5, 0, 5);
		context.waitTicks(5);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(20);
		context.getInput().releaseKey(o -> o.forwardKey);
		double[] c2 = context.computeOnClient((MinecraftClient mc) -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		double[] l2 = pose(server).toLocal(c2[0], c2[1], c2[2]);
		log.accept(String.format(Locale.ROOT, "%s walked on the main deck to local %.2f %.3f %.2f", id, l2[0], l2[1], l2[2]));
		check.accept(l2[2] > 2.0 && Math.abs(l2[1] - RoyalLionLayout.MAIN_DECK_Y) < 0.1, String.format(Locale.ROOT,
				"%s: the player walks on the main deck (moved to z %.2f, y %.3f)", id, l2[2], l2[1]));
		boolean opened = server.computeOnServer(srv -> {
			ShipEntity e = ship(srv.getOverworld());
			e.toggleDoor(RoyalLionLayout.CABIN_DOOR);
			e.toggleDoor(RoyalLionLayout.STATEROOM_DOOR);
			e.toggleDoor(RoyalLionLayout.BULKHEAD_DOOR);
			e.toggleDoor(RoyalLionLayout.STATEROOM_DOOR_S);
			return e.doorOpen(RoyalLionLayout.CABIN_DOOR) && e.doorOpen(RoyalLionLayout.STATEROOM_DOOR) && e.doorOpen(RoyalLionLayout.BULKHEAD_DOOR)
					&& e.doorOpen(RoyalLionLayout.STATEROOM_DOOR_S);
		});
		check.accept(opened, id + ": the cabin, bulkhead and both state room doors open");
		furnishedRooms(context, server, check, log, shot);

		// the gangplank onto a stone quay on the starboard side (top one block above the water), with its lever
		ShipPose pq = pose(server);
		fillLocal(server, pq, -16.0, -9.0, -2.0, 8.0, -63, -49, "stone");
		context.waitTicks(10);
		check.accept(plank(server) == Gangplank.State.RETRACTED, id + ": gangplank stowed at first");
		tp(server, pq, -1.0, RoyalLionLayout.MAIN_DECK_Y + 0.02, 0.5, 0, 10);
		context.waitTicks(5);
		String msg = lever(server);
		Gangplank.State st = plank(server);
		log.accept(String.format(Locale.ROOT, "%s gangplank lever: %s (%s)", id, st, msg));
		check.accept(st == Gangplank.State.DEPLOYING, String.format(Locale.ROOT, "%s: the lever deploys the gangplank (%s %s)", id, st, msg));
		waitPlank(context, server, Gangplank.State.DEPLOYED, 90);
		check.accept(plank(server) == Gangplank.State.DEPLOYED, id + ": the gangplank lies on the quay");
		server.runCommand("gamemode spectator @a");
		look(server, pq, -22, 10, 12, -6, 5, 3);
		context.waitTicks(10);
		shot.accept(id + "_14_passerelle");
		server.runCommand("gamemode survival @a");
		tp(server, pq, -1.0, RoyalLionLayout.MAIN_DECK_Y + 0.02, 0.5, 0, 10);
		context.waitTicks(5);
		msg = lever(server);
		check.accept(plank(server) == Gangplank.State.RETRACTING, String.format(Locale.ROOT, "%s: the lever retracts the gangplank (%s)", id, msg));
		waitPlank(context, server, Gangplank.State.RETRACTED, 90);
		check.accept(plank(server) == Gangplank.State.RETRACTED, id + ": the gangplank is stowed again");
		fillLocal(server, pq, -16.0, -9.0, -2.0, 8.0, -49, -49, "air");
		fillLocal(server, pq, -16.0, -9.0, -2.0, 8.0, -63, -50, "water");
		context.waitTicks(10);

		// at the helm: the big ship gathers way slowly, then a turn to port
		ShipPose p0 = pose(server);
		tp(server, p0, 0.0, RoyalLionLayout.QUARTERDECK_Y + 0.02, RoyalLionLayout.PILOT_Z, 0, 10);
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
		check.accept(helm[1] > 0.9f, String.format(Locale.ROOT, "%s: the sails are set under way (open %.2f)", id, helm[1]));
		context.runOnClient(mc -> mc.options.hudHidden = false);
		context.waitTicks(2);
		shot.accept(id + "_15_a_la_barre");
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose moved = pose(server);
		double dist = Math.hypot(moved.x() - start.x(), moved.z() - start.z());
		log.accept(String.format(Locale.ROOT, "%s moved %.2f blocks in 7 s at the helm", id, dist));
		check.accept(dist > 1.0 && dist < 30, String.format(Locale.ROOT, "%s sails under the player's control (moved %.2f)", id, dist));
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		context.runOnClient(mc -> mc.options.hudHidden = true);
		look(server, pose(server), -24, 8, 34, 0, 8, 10);
		context.waitTicks(12);
		shot.accept(id + "_16_sous_voiles");
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
