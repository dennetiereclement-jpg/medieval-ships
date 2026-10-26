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
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.SkiffLayout;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the Rustic Skyskiff (about 40 s of game time): placed in the air over open ground, hovers, the
 * views of the reference sheet (side, front, back, top, perspective) and its rooms (fore deck, cabin front and pilot
 * post, common room, bedroom, hold, pilot deck), standing and walking on the fore deck, through the cabin door into
 * the cabin, flown from the helm (a quick climb, forward, a tight turn) with its animations (engine still when parked,
 * running under way: the tubes' fans and the beating wings), the pilot steps off onto the pilot deck, the item. The HUD
 * is hidden for the screenshots. Called once from {@link ShipClientGameTest}.
 */
public final class SkiffGameTest {
	private static final ShipType TYPE = Ships.RUSTIC_SKIFF;
	private static final int X = 660;

	private SkiffGameTest() {
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

	/** The client copy of the skiff's animation state: engine phase, helm, climb (null if not there). */
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
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -20 -40 0 20", X));
		context.waitTicks(30);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, X, 0));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d 0 rotated 0 0 run ship spawn %s", X, ground, id));
		world.waitForChunksRender();
		context.waitTicks(30);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": not spawned");
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		double low = p0.y() + g.lowestY();
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, ground %d, lowest point %.2f", id, p0.x(), p0.y(), p0.z(), ground, low));
		check.accept(low >= ground + 0.9 && low < ground + 4, String.format(Locale.ROOT,
				"%s placed in the air above the ground (lowest point %.2f, ground %d)", id, low, ground));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(20);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));
		float[] a0 = anim(context);
		context.waitTicks(10);
		float[] a1 = anim(context);
		check.accept(a0 != null && a1 != null && a0[0] == a1[0], String.format(Locale.ROOT, "%s parked: the tubes' fans and the wings are still (%s -> %s)",
				id, a0 == null ? "?" : a0[0], a1 == null ? "?" : a1[0]));

		// the views of the reference sheet, then the rooms (reference interior views) with the decoration mods
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_dessus", "5_perspective", "6_pont_avant", "7_cabine_poste", "8_salle_commune",
				"9_chambre", "10_cale", "11_poste_pilotage"};
		double[][] eyes = { // eye x, y, z, target x, y, z
				{44, 1.0, -2.5, 0, 1.0, -2.5}, {0, 1.5, 44, 0, 1.5, -1}, {0, 1.5, -46, 0, 1.5, -1}, {6, 52, -1.5, 0, 0, -1.5},
				{30, 13, 24, 0, 1.0, -3.5},
				{1.4, 1.62, 8.5, 0.0, 1.2, -2.0}, {0.4, 1.62, 5.5, 0.0, 2.8, -3.5}, {-0.4, 1.62, -3.7, -1.0, 0.5, -7.4},
				{-0.6, 1.62, -8.3, 1.4, 0.6, -11.6}, {0.0, -0.95, 3.9, 0.0, -1.4, -8.0}, {2.5, 4.62, -12.3, 0.0, 4.0, -3.0}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, hover, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 25 : k == 5 ? 20 : 10);
			shot.accept(id + "_" + names[k]);
		}

		// standing and walking on the fore deck
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, hover, 0, 0.6, 5.0, 180, 10);
		context.waitTicks(30);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1]) < 0.08, String.format(Locale.ROOT, "%s stands on the fore deck (local y %.3f)", id, l[1]));
		context.getInput().holdKeyFor(o -> o.forwardKey, 15);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1]) < 0.08,
				String.format(Locale.ROOT, "%s walks on the fore deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));

		// through the cabin door into the cabin
		setDoor(server, SkiffLayout.CABIN_DOOR, true);
		tpLocal(server, pose(server), -0.5, 0.05, -1.8, 180, 0);
		context.waitTicks(10);
		context.getInput().holdKeyFor(o -> o.forwardKey, 25);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(l[2] < -3.8 && Math.abs(l[1]) < 0.08, String.format(Locale.ROOT, "%s walks into the cabin (local z %.2f y %.2f)", id, l[2], l[1]));
		lookLocal(server, pose(server), l[0], l[1] + 1.62, l[2], -2.2, 0.8, -5.2);
		context.waitTicks(8);
		shot.accept(id + "_12_dans_la_cabine");

		// flown from the helm: a quick climb, forward, a tight turn; the pilot steps off onto the pilot deck
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			return ship(srv.getOverworld()).seat(player, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, id + " the player takes the helm");
		ShipPose s0 = pose(server);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(40);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = pose(server);
		check.accept(s1.y() - s0.y() > 2.0, String.format(Locale.ROOT, "%s climbs quickly under command (%.2f blocks in 2 s)", id, s1.y() - s0.y()));
		float[] a2 = anim(context);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(50);
		ShipPose s2 = pose(server);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 2.0, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 2.5 s)", id, dist));
		float[] a3 = anim(context);
		check.accept(a2 != null && a3 != null && a3[0] - a2[0] > 0.3, String.format(Locale.ROOT,
				"%s under way: the fans spin and the wings beat (phase %.2f -> %.2f)", id, a2 == null ? 0f : a2[0], a3 == null ? 0f : a3[0]));
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(40);
		float[] a4 = anim(context);
		ShipPose s3 = pose(server);
		double turned = Math.abs(ShipPose.wrapDegrees(s3.yaw() - s2.yaw()));
		check.accept(turned > 15, String.format(Locale.ROOT, "%s turns tightly (%.1f degrees in 2 s)", id, turned));
		check.accept(a4 != null && Math.abs(a4[1]) > 0.3, String.format(Locale.ROOT, "%s turning: the wheel and the rear wings follow the helm (%.2f)",
				id, a4 == null ? 0f : a4[1]));
		// seen from outside while turning
		server.runCommand("ride @p dismount");
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(5);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - SkiffLayout.PILOT_Y) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off onto the pilot deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		check.accept(collisions(server) == 0, id + " flight: inside nothing");
		server.runCommand("gamemode spectator @a");
		lookLocal(server, pose(server), 26, 6, -26, 0, -1, -6);
		context.waitTicks(4);
		shot.accept(id + "_13_en_vol");

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
		server.runCommand("gamemode survival @a");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		context.waitTicks(10);
	}
}
