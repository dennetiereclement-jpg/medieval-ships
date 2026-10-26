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
import fr.medievalships.core.JunkLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the Dragon Junk (about 45 s of game time), over a pool of water dug for it: placed in the air over
 * the water, hovers; the views of the reference sheet (side, front, back, top, perspective) and its rooms (main deck,
 * the deck before the stern house, main room, storage, bedroom, stern cabin); standing and walking on the main deck,
 * through the stern house's door into the stern cabin; flown from the helm (climb, forward, a turn) with the wheel
 * following the helm; brought down onto the water, where it stops low over the surface instead of sinking; the pilot
 * steps off onto the quarterdeck; the item. The HUD is hidden for the screenshots. Called once from
 * {@link ShipClientGameTest}.
 */
public final class JunkGameTest {
	private static final ShipType TYPE = Ships.DRAGON_JUNK;
	private static final int X = -520, Z = -60;

	private JunkGameTest() {
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

	/** The client copy of the junk's helm (null if not there). */
	private static Float helm(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> {
			for (ShipEntity s : ShipTracker.ships(c.world)) {
				if (!s.isRemoved() && s.shipType() == TYPE) {
					return s.helmVisual;
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
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 %d 0 20", X, Z - 40));
		context.waitTicks(30);
		// a pool of water three blocks deep under it: it is placed over the water and comes down onto it later (its chunks
		// force-loaded first: the fill does nothing where a chunk is not loaded)
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 20, Z - 30, X + 20, Z + 45));
		context.waitTicks(30);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, X, Z));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d water", X - 20, ground - 3, Z - 30, X + 20, ground - 1, Z + 7));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d water", X - 20, ground - 3, Z + 8, X + 20, ground - 1, Z + 45));
		context.waitTicks(5);
		boolean pool = server.computeOnServer(srv -> srv.getOverworld().getFluidState(new net.minecraft.util.math.BlockPos(X, ground - 1, Z + 40))
				.isIn(net.minecraft.registry.tag.FluidTags.WATER) && srv.getOverworld().getFluidState(new net.minecraft.util.math.BlockPos(X, ground - 1, Z - 25))
				.isIn(net.minecraft.registry.tag.FluidTags.WATER));
		check.accept(pool, id + ": the pool of water is filled under it");
		int water = server.computeOnServer(srv -> srv.getOverworld().getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, X, Z));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d %d rotated 0 0 run ship spawn %s", X, water, Z, id));
		world.waitForChunksRender();
		context.waitTicks(30);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": not spawned");
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		double low = p0.y() + g.lowestY();
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, water surface %d, lowest point (anchor) %.2f", id, p0.x(), p0.y(), p0.z(), water,
				low));
		check.accept(low >= water + 0.9 && low < water + 4, String.format(Locale.ROOT,
				"%s placed in the air above the water (anchor %.2f, surface %d)", id, low, water));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(20);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));

		// the views of the reference sheet, then the rooms (reference interior views) with the decoration mods
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_dessus", "5_perspective", "6_pont", "7_pont_cabine", "8_salle_principale",
				"9_reserve", "10_chambre", "11_cabine_poupe"};
		double[][] eyes = { // eye x, y, z, target x, y, z
				{42, 8.5, 2.5, 0, 8.5, 2.5}, {0, 9, 48, 0, 8.5, 0}, {0, 6, -48, 0, 5.5, -2}, {4, 56, 1, 0, 0, 1}, {28, 13, 26, 0, 6, 0},
				{-2.2, 1.62, 5.2, 0.8, 0.0, 11.6}, {-1.2, 1.62, 5.0, 0.3, 3.4, -8.0}, {2.0, -1.38, 6.8, -0.6, -2.7, 2.2},
				{-0.9, -1.38, 8.2, 0.6, -2.5, 15.0}, {-0.8, 1.12, -2.6, 1.6, -0.4, -8.6}, {0.0, 4.12, -8.9, 0.0, 3.1, -17.5}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, hover, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 25 : k == 5 ? 20 : 10);
			shot.accept(id + "_" + names[k]);
		}

		// standing and walking on the main deck
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, hover, 0, JunkLayout.MAIN_DECK_Y + 0.6, 9.0, 0, 10);
		context.waitTicks(30);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1] - JunkLayout.MAIN_DECK_Y) < 0.08, String.format(Locale.ROOT, "%s stands on the main deck (local y %.3f)", id, l[1]));
		context.getInput().holdKeyFor(o -> o.forwardKey, 15);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - JunkLayout.MAIN_DECK_Y) < 0.08,
				String.format(Locale.ROOT, "%s walks on the main deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));

		// through the stern house's door into the stern cabin
		setDoor(server, JunkLayout.STERN_DOOR, true);
		tpLocal(server, pose(server), 0.0, JunkLayout.QUARTERDECK_Y + 0.05, -6.9, 180, 0);
		context.waitTicks(10);
		context.getInput().holdKeyFor(o -> o.forwardKey, 25);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(l[2] < -9.0 && Math.abs(l[1] - JunkLayout.QUARTERDECK_Y) < 0.08, String.format(Locale.ROOT,
				"%s walks into the stern cabin (local z %.2f y %.2f)", id, l[2], l[1]));
		lookLocal(server, pose(server), l[0], l[1] + 1.62, l[2], 0.0, 3.2, -17.0);
		context.waitTicks(8);
		shot.accept(id + "_12_dans_la_cabine");

		// flown from the helm: climb, forward, a turn
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
		check.accept(s1.y() - s0.y() > 1.2, String.format(Locale.ROOT, "%s climbs under command (%.2f blocks in 2 s)", id, s1.y() - s0.y()));
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(60);
		ShipPose s2 = pose(server);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 1.5, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 3 s)", id, dist));
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(40);
		Float h = helm(context);
		ShipPose s3 = pose(server);
		double turned = Math.abs(ShipPose.wrapDegrees(s3.yaw() - s2.yaw()));
		check.accept(turned > 4, String.format(Locale.ROOT, "%s turns (%.1f degrees in 2 s)", id, turned));
		check.accept(h != null && Math.abs(h) > 0.3, String.format(Locale.ROOT, "%s turning: the wheel and the rudder follow the helm (%.2f)", id,
				h == null ? 0f : h));
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		check.accept(collisions(server) == 0, id + " flight: inside nothing");

		// down onto the water: it stops low over the surface (its keel WATER_HOVER above it), it does not sink
		context.getInput().holdKey(o -> o.sprintKey);
		context.waitTicks(130);
		context.getInput().releaseKey(o -> o.sprintKey);
		context.waitTicks(10);
		ShipPose s4 = pose(server);
		double keel = s4.y() + JunkLayout.keelY(0.0);
		check.accept(keel > water + 0.4 && keel < water + 1.4, String.format(Locale.ROOT,
				"%s comes down onto the water and hovers low over it (keel %.2f, surface %d)", id, keel, water));
		server.runCommand("ride @p dismount");
		context.waitTicks(5);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - JunkLayout.QUARTERDECK_Y) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		server.runCommand("gamemode spectator @a");
		lookLocal(server, pose(server), 30, 6, 24, 0, 1, 0);
		context.waitTicks(6);
		shot.accept(id + "_13_au_ras_de_l_eau");

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
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 20, Z - 30, X + 20, Z + 45));
		server.runCommand("gamemode survival @a");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		context.waitTicks(10);
	}
}
