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

import fr.medievalships.MedievalShips;
import fr.medievalships.core.CrystalLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the Crystal Airship (about 50 s of game time): placed in the air over open ground, hovers, the views
 * of the reference sheet (side, front, back, top, perspective) and close-ups (balloon, ring, engines, stern castle), the
 * furnished rooms (cockpit, lounge, engine room, storeroom, officers' mess, hold), standing and walking on the main deck,
 * walking through the castle's door into the officers' mess, flown from the helm in the cockpit (climb, forward, turn: the
 * propellers turn under way), the pilot steps off in the cockpit, the item. The HUD is hidden for the screenshots.
 * Called once from {@link ShipClientGameTest}.
 */
public final class CrystalGameTest {
	private static final ShipType TYPE = Ships.CRYSTAL_AIRSHIP;
	private static final int X = -260, Z = 60;

	private CrystalGameTest() {
	}

	private static ShipEntity ship(ServerWorld world) {
		for (ShipEntity s : ShipTracker.ships(world)) {
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

	private static int collisions(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			if (s == null) {
				return -1;
			}
			ServerWorld w = srv.getOverworld();
			return ShipMover.countCollisions(s.geometry(), s.pose(), (x, y, z) -> {
				var pos = net.minecraft.util.math.BlockPos.ofFloored(x, y, z);
				return !w.getBlockState(pos).getCollisionShape(w, pos).isEmpty();
			});
		});
	}

	private static double[] local(ClientGameTestContext context, TestServerContext server) {
		double[] p = context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ()});
		return pose(server).toLocal(p[0], p[1], p[2]);
	}

	private static void tpLocal(TestServerContext server, ShipPose pose, double lx, double ly, double lz, float localYaw, float pitch) {
		double[] w = pose.toWorld(lx, ly, lz);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", w[0], w[1], w[2], (float) (pose.yaw() + localYaw), pitch));
	}

	private static void lookLocal(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}

	/** The client copy of the airship's animation state: engine phase, helm, climb (null if not there). */
	private static float[] anim(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> {
			for (ShipEntity s : ShipTracker.ships(c.world)) {
				if (!s.isRemoved() && s.shipType() == TYPE) {
					return new float[] {s.wheelPhase, s.helmVisual, s.climbVisual};
				}
			}
			return null;
		});
	}

	private static void setDoor(TestServerContext server, int door, boolean open) {
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			if (s != null && s.doorOpen(door) != open) {
				s.toggleDoor(door);
			}
			return null;
		});
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		ShipGeometry g = TYPE.geometry();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -20 %d 0 20", X, Z - 40));
		context.waitTicks(40);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, X, Z));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d %d rotated 0 0 run ship spawn %s", X, ground, Z, id));
		world.waitForChunksRender();
		context.waitTicks(40);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": not spawned");
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);   // clean screenshots
		double keel = p0.y() + g.lowestY();
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, ground %d, lowest point %.2f", id, p0.x(), p0.y(), p0.z(), ground, keel));
		check.accept(keel >= ground + 0.9 && keel < ground + 4, String.format(Locale.ROOT,
				"%s placed in the air above the ground (lowest point %.2f, ground %d)", id, keel, ground));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(30);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));
		float[] a0 = anim(context);
		context.waitTicks(10);
		float[] a1 = anim(context);
		check.accept(a0 != null && a1 != null && a0[0] == a1[0], id + " parked: the propellers are still");

		// the views of the reference sheet, then close-ups
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_dessus", "5_perspective", "6_ballon", "7_anneau", "8_moteurs", "9_chateau"};
		double[][] eyes = { // eye x, y, z, target x, y, z
				{60, 6, 0, 0, 6, 0}, {0, 6, 66, 0, 6, 0}, {0, 6, -66, 0, 6, 0}, {6, 76, 0, 0, 0, 0}, {44, 3, 16, 0, 6.5, -2.5},
				{30, 22, 14, 0, 17, 0}, {14, 4, 8, 0, 5.5, -0.3}, {22, 0, -26, 8, -2.5, -17}, {-18, 8, -32, 0, 4, -18}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, hover, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 30 : 15);
			shot.accept(id + "_" + names[k]);
		}
		// the furnished rooms, from the viewpoints of the reference sheet's interior views
		String[] rooms = {"10_poste_pilotage", "11_salon", "12_salle_machines", "13_reserve", "14_carre", "15_cale", "16_salon_arriere"};
		double[][] cams = {
				{0.0, 4.62, -19.6, 0.0, 4.0, -14.0}, {2.4, -2.38, -1.5, -2.6, -3.0, 6.5}, {0.2, -2.38, -8.2, 0.0, -6.0, -16.6},
				{0.0, -2.38, 11.0, 0.0, -3.4, 18.0}, {0.0, 1.62, -11.2, 0.0, 0.6, -21.0}, {0.0, -5.88, -5.0, 0.0, -6.6, 3.0},
				{-1.0, -2.38, 8.8, 1.6, -3.2, -3.5}};
		for (int k = 0; k < rooms.length; k++) {
			double[] c = cams[k];
			lookLocal(server, hover, c[0], c[1], c[2], c[3], c[4], c[5]);
			context.waitTicks(k == 0 ? 20 : 10);
			shot.accept(id + "_" + rooms[k]);
		}

		// standing and walking on the main deck
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, hover, 0, CrystalLayout.MAIN_DECK_Y + 0.6, 5.0, 180, 10);
		context.waitTicks(40);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1] - CrystalLayout.MAIN_DECK_Y) < 0.08, String.format(Locale.ROOT, "%s stands on the main deck (local y %.3f)", id, l[1]));
		context.getInput().holdKeyFor(o -> o.forwardKey, 20);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1]) < 0.08,
				String.format(Locale.ROOT, "%s walks on the main deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		lookLocal(server, pose(server), 2.4, CrystalLayout.MAIN_DECK_Y + 1.62, 8.8, -0.6, 2.6, -10.0);   // beside the ring's foot, towards the castle
		context.waitTicks(10);
		shot.accept(id + "_17_pont");

		// through the castle's door into the officers' mess
		setDoor(server, CrystalLayout.CASTLE_DOOR, true);
		tpLocal(server, pose(server), 0, 0.05, -8.6, 180, 0);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, 25);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(l[2] < -11.0 && Math.abs(l[1]) < 0.08, String.format(Locale.ROOT, "%s walks into the officers' mess (local z %.2f y %.2f)", id, l[2], l[1]));

		// flown from the helm in the cockpit: climb, forward, turn; then the pilot steps off in the cockpit
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			return ship(srv.getOverworld()).seat(player, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, id + " the player takes the helm");
		ShipPose s0 = pose(server);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(80);
		float[] climbing = anim(context);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = pose(server);
		check.accept(s1.y() - s0.y() > 1.0, String.format(Locale.ROOT, "%s climbs slowly under command (%.2f blocks in 4 s)", id, s1.y() - s0.y()));
		check.accept(climbing != null && climbing[2] > 0.3, String.format(Locale.ROOT, "%s climbing: the flaps follow (climb %.2f)", id,
				climbing == null ? 0f : climbing[2]));
		float[] a2 = anim(context);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose s2 = pose(server);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 0.8, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 4 s)", id, dist));
		float[] a3 = anim(context);
		check.accept(a2 != null && a3 != null && a3[0] - a2[0] > 0.2, String.format(Locale.ROOT,
				"%s under way: the propellers turn (phase %.2f -> %.2f)", id, a2 == null ? 0f : a2[0], a3 == null ? 0f : a3[0]));
		context.getInput().holdKey(o -> o.forwardKey);
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(80);          // a heavy airship: the helm comes over, then the bow swings round slowly
		float[] a4 = anim(context);
		ShipPose s3 = pose(server);
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		check.accept(a4 != null && Math.abs(a4[1]) > 0.3, String.format(Locale.ROOT, "%s turning: the wheel follows the helm (%.2f)", id,
				a4 == null ? 0f : a4[1]));
		check.accept(Math.abs(ShipPose.wrapDegrees(s3.yaw() - s2.yaw())) > 1.0, String.format(Locale.ROOT, "%s turns slowly (%.2f degrees in 4 s)", id,
				ShipPose.wrapDegrees(s3.yaw() - s2.yaw())));
		check.accept(collisions(server) == 0, id + " flight: inside nothing");
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - CrystalLayout.L2_Y) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off in the cockpit (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));

		// the item
		server.runCommand("clear @a");
		server.runCommand("ship give " + id + " @p");
		Integer items = server.computeOnServer(srv -> srv.getPlayerManager().getPlayerList().get(0).getInventory().count(MedievalShips.item(TYPE)));
		check.accept(items != null && items == 1, String.format(Locale.ROOT, "%s item: /ship give gives it (%s)", id, items));
		server.runCommand("clear @a");
		server.computeOnServer(srv -> {
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (s.shipType() == TYPE) {
					s.removeAllPassengers();
					s.discard();
				}
			}
			return null;
		});
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		context.waitTicks(10);
	}
}
