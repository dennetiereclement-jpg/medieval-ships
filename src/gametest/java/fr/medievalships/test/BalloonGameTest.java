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
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the steampunk hot-air balloon (about 25 s of game time): placed in the air over open ground with
 * its space checked, hovers, the views of the reference picture (its viewpoint, the side, the front), a player stands
 * on the basket's deck, takes the burner's valves, climbs (the flame flares), flies forward (the gear wheel turns),
 * turns, steps off onto the deck, a screenshot in flight, the item. The HUD is hidden for the screenshots. Called once
 * from {@link ShipClientGameTest}.
 */
public final class BalloonGameTest {
	private static final ShipType TYPE = Ships.HOT_AIR_BALLOON;
	private static final int X = 760, Z = 40;

	private BalloonGameTest() {
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

	/** The client copy of the balloon's animation state: wheel phase, helm, climb (null if not there). */
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

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		ShipGeometry g = TYPE.geometry();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -20 %d 0 20", X, Z - 40));
		context.waitTicks(30);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, X, Z));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d %d rotated 0 0 run ship spawn %s", X, ground, Z, id));
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
				"%s placed in the air above the ground with its space checked (lowest point %.2f, ground %d)", id, low, ground));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(20);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));
		float[] a0 = anim(context);
		check.accept(a0 != null && Math.abs(a0[2]) < 0.05, id + " parked: the burner is at its pilot light");

		// the viewpoint of the reference picture, then the side and the front
		String[] names = {"1_reference", "2_cote", "3_avant"};
		double[][] eyes = {{15.5, 9.4, 7.3, 0, 9.3, 0}, {18, 9, 0.01, 0, 9, 0}, {0.01, 9, 19, 0, 9, 0}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, hover, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 25 : 10);
			shot.accept(id + "_" + names[k]);
		}

		// standing on the basket's deck
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, hover, 0, 0.6, 2.8, 180, 10);
		context.waitTicks(30);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1]) < 0.1 && g.inCarryVolume(l[0], l[1] + 0.2, l[2]),
				String.format(Locale.ROOT, "%s stands on the basket's deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));

		// the player takes the burner's valves: a soft climb (the flame flares), forward (the gear wheel turns), a turn
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			return ship(srv.getOverworld()).seat(player, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, id + " the player takes the controls");
		ShipPose s0 = pose(server);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(20);
		ShipPose sEarly = pose(server);
		context.waitTicks(60);
		float[] a1 = anim(context);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = pose(server);
		log.accept(String.format(Locale.ROOT, "%s climb: %.2f -> %.2f (after 1 s: %.2f)", id, s0.y(), s1.y(), sEarly.y()));
		check.accept(sEarly.y() - s0.y() < 0.5 && s1.y() - s0.y() > 1.5, String.format(Locale.ROOT,
				"%s takes off progressively under command (%.2f blocks after 1 s, %.2f after 4 s)", id, sEarly.y() - s0.y(), s1.y() - s0.y()));
		check.accept(a1 != null && a1[2] > 0.3, String.format(Locale.ROOT, "%s climbing: the burner flares (%.2f)", id, a1 == null ? 0f : a1[2]));
		context.waitTicks(30);
		float[] a2 = anim(context);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		ShipPose s2 = pose(server);
		float[] a3 = anim(context);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 1.5, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 4 s)", id, dist));
		check.accept(a2 != null && a3 != null && a3[0] - a2[0] > 0.1, String.format(Locale.ROOT,
				"%s under way: the gear wheel turns (phase %.2f -> %.2f)", id, a2 == null ? 0f : a2[0], a3 == null ? 0f : a3[0]));
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(60);
		ShipPose s3 = pose(server);
		double turned = Math.abs(ShipPose.wrapDegrees(s3.yaw() - s2.yaw()));
		check.accept(turned > 5, String.format(Locale.ROOT, "%s turns gently (%.1f degrees in 3 s)", id, turned));
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		server.runCommand("ride @p dismount");
		context.waitTicks(5);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1] + 0.2, l[2]) && Math.abs(l[1]) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off onto the deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		check.accept(collisions(server) == 0, id + " flight: inside nothing");
		server.runCommand("gamemode spectator @a");
		lookLocal(server, pose(server), 15.5, 9.4, 7.3, 0, 9.3, 0);
		context.waitTicks(4);
		shot.accept(id + "_4_en_vol");

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
	}
}
