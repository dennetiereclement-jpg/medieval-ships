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
import fr.medievalships.core.LeviathanLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the Sky Leviathan (about 45 s of game time): placed in the air over open ground,
 * hovers, the reference views, walking on the main deck, flown from the helm (climb, forward), the
 * pilot steps off onto the quarterdeck, the captain's door, the ladder of the tower up through the
 * balloon to the observation deck, the item. Called once from {@link ShipClientGameTest}.
 */
public final class LeviathanGameTest {
	private static final ShipType TYPE = Ships.SKY_LEVIATHAN;

	private LeviathanGameTest() {
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
		server.runCommand("tp @p 300 -20 -40 0 20");
		context.waitTicks(40);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, 300, 0));
		server.runCommand(String.format(Locale.ROOT, "execute positioned 300 %d 0 rotated 0 0 run ship spawn %s", ground, id));
		world.waitForChunksRender();
		context.waitTicks(40);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": not spawned");
			return;
		}
		double keel = p0.y() + g.lowestY();
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, ground %d, keel %.2f", id, p0.x(), p0.y(), p0.z(), ground, keel));
		check.accept(keel >= ground + 0.9 && keel < ground + 4, String.format(Locale.ROOT, "%s placed in the air above the ground (keel %.2f, ground %d)",
				id, keel, ground));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(40);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));

		// the views of the reference sheet
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_dessus", "5_perspective"};
		double[][] eyes = {{75, 13, -1}, {0, 15, 80}, {0, 15, -82}, {0.01, 95, -1}, {55, 26, 50}};
		for (int k = 0; k < names.length; k++) {
			lookLocal(server, hover, eyes[k][0], eyes[k][1], eyes[k][2], 0, k == 3 ? 0 : 13, -1);
			context.waitTicks(k == 0 ? 30 : 15);
			shot.accept(id + "_" + names[k]);
		}

		// walking on the main deck
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, hover, 0, LeviathanLayout.MAIN_DECK_Y + 0.6, 4.0, 180, 10);
		context.waitTicks(40);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1] - LeviathanLayout.MAIN_DECK_Y) < 0.08, String.format(Locale.ROOT, "%s stands on the main deck (local y %.3f)", id, l[1]));
		context.getInput().holdKeyFor(o -> o.forwardKey, 20);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1]) < 0.08,
				String.format(Locale.ROOT, "%s walks on the main deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		shot.accept(id + "_6_pont");

		// the captain's door, then into the captain's quarters
		setDoor(server, LeviathanLayout.CAPTAIN_DOOR, true);
		tpLocal(server, pose(server), 0, 0.05, -6.6, 180, 0);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, 25);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(l[2] < -8.3 && Math.abs(l[1]) < 0.08, String.format(Locale.ROOT, "%s walks into the captain's quarters (local z %.2f y %.2f)", id, l[2], l[1]));
		shot.accept(id + "_7_cabine");

		// flown from the helm: climb, forward, then the pilot steps off onto the quarterdeck
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			return ship(srv.getOverworld()).seat(player, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, id + " the player takes the helm");
		ShipPose s0 = pose(server);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = pose(server);
		check.accept(s1.y() - s0.y() > 1.5, String.format(Locale.ROOT, "%s climbs slowly under command (%.2f blocks in 4 s)", id, s1.y() - s0.y()));
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose s2 = pose(server);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 1.0, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 4 s)", id, dist));
		check.accept(collisions(server) == 0, id + " flight: inside nothing");
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - LeviathanLayout.QUARTERDECK_Y) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));

		// the ladder of the tower, up through the balloon to the observation deck
		setDoor(server, LeviathanLayout.TOWER_DOOR, true);
		setDoor(server, LeviathanLayout.TOP_HATCH, true);
		tpLocal(server, pose(server), 0, 0.05, -1.5, 180, -30);
		context.waitTicks(10);
		context.getInput().holdKey(o -> o.jumpKey);
		context.getInput().holdKey(o -> o.forwardKey);
		double top = -99;
		for (int i = 0; i < 30 && top < LeviathanLayout.TOP_DECK_Y - 0.1; i++) {
			context.waitTicks(10);
			top = local(context, server)[1];
		}
		context.waitTicks(20);
		context.getInput().releaseKey(o -> o.jumpKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(20);
		l = local(context, server);
		log.accept(String.format(Locale.ROOT, "%s after the ladder: local %.2f %.2f %.2f", id, l[0], l[1], l[2]));
		check.accept(Math.abs(l[1] - LeviathanLayout.TOP_DECK_Y) < 0.1 && g.inCarryVolume(l[0], l[1], l[2]),
				String.format(Locale.ROOT, "%s climbs the tower's ladder onto the observation deck (local y %.2f)", id, l[1]));
		shot.accept(id + "_8_pont_superieur");

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
		context.waitTicks(10);
	}
}
