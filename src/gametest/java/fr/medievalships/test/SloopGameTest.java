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

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.SloopLayout;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the trade sloop (about 40 s of game time): spawned on a basin it floats at its waterline inside
 * nothing, its sails furl at rest and set again, the views of the reference (port bow, side, stern, top), a survival
 * player stands and walks on the main deck and up on the stern platform between the crates, takes the tiller and
 * sails under control (the tiller turns, the sails stay set, the boat gathers way and turns), steps off onto the
 * stern platform, a view under sail from outside, the item. Called once from {@link ShipClientGameTest}.
 */
public final class SloopGameTest {
	private static final ShipType TYPE = Ships.TRADE_SLOOP;
	/** The basin: 40 wide, 60 long, walled with glass up to the water. */
	private static final int X0 = 880, X1 = 920, Z0 = -30, Z1 = 30, TOP = -50;

	private SloopGameTest() {
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

	private static int collisions(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			if (s == null) {
				return -1;
			}
			ServerWorld w = srv.getOverworld();
			return ShipMover.countCollisions(s.geometry(), s.pose(), (x, y, z) -> {
				BlockPos pos = BlockPos.ofFloored(x, y, z);
				return !w.getBlockState(pos).getCollisionShape(w, pos).isEmpty();
			});
		});
	}

	/** Sails and helm of the sloop as the client sees them: {set (0/1), open fraction, helm, speed}. */
	private static float[] state(ClientGameTestContext context) {
		return context.computeOnClient(mc -> {
			ShipEntity s = clientShip(mc);
			return s == null ? new float[] {-1, -1, 0, 0} : new float[] {s.sailSet() ? 1 : 0, s.sailOpen, s.helmVisual, s.syncedSpeed()};
		});
	}

	private static double[] local(ClientGameTestContext context, TestServerContext server) {
		double[] p = context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ(),
				c.player.isOnGround() ? 1 : 0});
		double[] l = pose(server).toLocal(p[0], p[1], p[2]);
		return new double[] {l[0], l[1], l[2], p[3]};
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

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		ShipGeometry g = TYPE.geometry();
		double main = SloopLayout.MAIN_DECK_Y, aft = SloopLayout.AFT_DECK_Y;
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 %d 0 30", (X0 + X1) / 2, Z0 - 10));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X1, TOP, Z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z1, X1, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X0, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X1, Z0, X1, TOP, Z1));
		for (int z = Z0 + 1; z < Z1; z += 30) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", X0 + 1, z, X1 - 1, Math.min(Z1 - 1, z + 29)));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -30 %d air", X0 + 1, z, X1 - 1, Math.min(Z1 - 1, z + 29)));
		}
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 -12 rotated 0 0 run ship spawn %s", (X0 + X1) / 2, id));
		world.waitForChunksRender();
		context.waitTicks(40);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": spawned in the basin");
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		double surface = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			BlockPos pos = new BlockPos((X0 + X1) / 2, -50, (int) Math.floor(p0.z()));
			return pos.getY() + (double) w.getFluidState(pos).getHeight(w, pos);
		});
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, water surface %.3f", id, p0.x(), p0.y(), p0.z(), surface));
		check.accept(Math.abs(p0.y() - (surface - TYPE.hull().waterlineY)) < 0.25,
				String.format(Locale.ROOT, "%s floats at its waterline (y %.2f, water %.2f)", id, p0.y(), surface));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");

		// at rest the sails furl (furlSailWhenStopped) after 5 s; set again for the views of the reference
		context.waitTicks(100);
		float[] s0 = state(context);
		log.accept(String.format(Locale.ROOT, "%s at rest: sail set %.0f, open %.2f", id, s0[0], s0[1]));
		check.accept(s0[0] == 0 && s0[1] < 0.15f, String.format(Locale.ROOT, "%s: the sails furl onto the boom when stopped (open %.2f)", id, s0[1]));
		lookLocal(server, pose(server), 14, 4.5, 21, 0, 5.2, -1);
		context.waitTicks(10);
		shot.accept(id + "_0_voiles_ferlees");
		boolean furl = server.computeOnServer(srv -> {
			var cfg = fr.medievalships.data.ConfigManager.ship(TYPE);
			boolean was = cfg.furlSailWhenStopped;
			cfg.furlSailWhenStopped = false;
			return was;
		});
		context.waitTicks(60);
		float[] s1 = state(context);
		check.accept(s1[0] == 1 && s1[1] > 0.9f, String.format(Locale.ROOT, "%s: the sails are set again (open %.2f)", id, s1[1]));
		boolean anims = context.computeOnClient(mc -> {
			fr.medievalships.client.model.BbModel m = fr.medievalships.client.render.ShipModels.get(fr.medievalships.client.render.ShipModels.TRADE_SLOOP);
			if (m == null) {
				return false;
			}
			for (String n : new String[] {"sail_wind", "sail_furl", "steer", "lantern_sway", "rope_sway"}) {
				if (!m.animations.containsKey(n)) {
					return false;
				}
			}
			return m.bonesByName.containsKey("sail_main") && m.bonesByName.containsKey("sail_jib") && m.bonesByName.containsKey("rudder");
		});
		check.accept(anims, id + ": the model loaded in game has its sails, rudder and animations");
		ShipPose p = pose(server);
		double[][] eyes = {{14, 4.5, 21, 0, 5.2, -1}, {30, 5, 0.5, 0, 5.5, 0.5}, {-13, 5, -24, 0, 5, 0}, {0.05, 36, 0.5, 0, 0, 0.5}};
		String[] names = {"1_reference_babord_avant", "2_cote", "3_arriere", "4_dessus"};
		for (int k = 0; k < eyes.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, p, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 20 : 12);
			shot.accept(id + "_" + names[k]);
		}

		// a survival player stands and walks on the main deck, then up on the stern platform between the crates
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tpLocal(server, pose(server), 0, main + 0.02, 2.0, 180, 10);
		context.waitTicks(30);
		double[] l = local(context, server);
		check.accept(Math.abs(l[1] - main) < 0.08 && l[3] > 0, String.format(Locale.ROOT, "%s: standing on the main deck (local y %.3f)", id, l[1]));
		context.getInput().holdKeyFor(o -> o.forwardKey, 14);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - main) < 0.08 && l[2] < 1.3,
				String.format(Locale.ROOT, "%s: walks aft along the deck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		tpLocal(server, pose(server), 0, aft + 0.02, -4.4, 180, 10);
		context.waitTicks(20);
		l = local(context, server);
		check.accept(Math.abs(l[1] - aft) < 0.08 && l[3] > 0, String.format(Locale.ROOT, "%s: standing on the stern platform (local y %.3f)", id, l[1]));
		lookLocal(server, pose(server), 0.3, aft + 1.62, -4.4, 0, main + 1.0, 6.0);
		context.waitTicks(8);
		shot.accept(id + "_5_sur_le_pont");

		// at the tiller: the boat gathers way progressively, then turns to port
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity player = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity s = ship(srv.getOverworld());
			return s != null && s.seat(player, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, id + ": the player takes the tiller");
		context.waitTicks(10);
		ShipPose start = pose(server);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		ShipPose mid = pose(server);
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(50);
		float[] s2 = state(context);
		ShipPose end = pose(server);
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		double d1 = Math.hypot(mid.x() - start.x(), mid.z() - start.z()), d2 = Math.hypot(end.x() - start.x(), end.z() - start.z());
		double turned = Math.abs(ShipPose.wrapDegrees(end.yaw() - mid.yaw()));
		log.accept(String.format(Locale.ROOT, "%s at the tiller: %.2f blocks after 4 s, %.2f after 6.5 s, turned %.1f deg, helm %.2f, sails %.2f, speed %.2f",
				id, d1, d2, turned, s2[2], s2[1], s2[3]));
		check.accept(d1 > 1.0 && d2 > d1 + 1.0 && d2 < 30, String.format(Locale.ROOT, "%s sails under the player's control, gathering way (%.2f then %.2f blocks)", id, d1, d2));
		check.accept(Math.abs(s2[2]) > 0.3f, String.format(Locale.ROOT, "%s: the tiller and the rudder follow the helm (%.2f)", id, s2[2]));
		check.accept(s2[1] > 0.9f, String.format(Locale.ROOT, "%s: the sails stay set under way (open %.2f)", id, s2[1]));
		check.accept(turned > 5, String.format(Locale.ROOT, "%s turns to port (%.1f degrees in 2.5 s)", id, turned));
		check.accept(collisions(server) == 0, id + " under way: inside nothing");
		// the pilot steps off onto the stern platform
		server.runCommand("ride @p dismount");
		context.waitTicks(5);
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - aft) < 0.15,
				String.format(Locale.ROOT, "%s: the pilot steps off onto the stern platform (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		server.runCommand("gamemode spectator @a");
		lookLocal(server, pose(server), 16, 5, 18, 0, 5, 0);
		context.waitTicks(8);
		shot.accept(id + "_6_sous_voiles");
		server.runOnServer(srv -> fr.medievalships.data.ConfigManager.ship(TYPE).furlSailWhenStopped = furl);

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
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
		server.runCommand("gamemode survival @a");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		context.waitTicks(10);
	}
}
