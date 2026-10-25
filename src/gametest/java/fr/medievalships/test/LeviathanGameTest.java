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
 * In-game checks of the Sky Leviathan (about 60 s of game time): placed in the air over open ground,
 * hovers, the views of the reference sheet (side, front, back, top, perspective, the balloon, the fins, the suspended
 * hull), the furnished rooms, walking on the main deck, flown from the helm (climb, forward, turn) with its animations
 * (engine still when parked and turning under way, rudder and elevator fins following the helm and the climb, shot
 * from outside during the turn, the engine room under way), the pilot steps off onto the quarterdeck, the captain's
 * door, the ladder of the tower up through the balloon to the observation deck, the item. The HUD is hidden for the
 * screenshots (comparison sheet docs/comparaison_sky_leviathan.png). Called once from {@link ShipClientGameTest}.
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

	/**
	 * Diagnostic line: the airship as the server and as this client see it (position, yaw, speeds), and the player as the
	 * client simulates him, in the frame of both hulls (feet, on ground, climbing, spectator, camera).
	 */
	private static void diag(ClientGameTestContext context, TestServerContext server, Consumer<String> log, String tag) {
		double[] sv = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			ServerPlayerEntity p = srv.getPlayerManager().getPlayerList().get(0);
			return s == null ? null : new double[] {s.getX(), s.getY(), s.getZ(), s.getYaw(), s.physics().speed, s.syncedVerticalSpeed(),
					p.getX(), p.getY(), p.getZ()};
		});
		Object[] cl = context.computeOnClient((MinecraftClient c) -> {
			ShipEntity s = null;
			for (ShipEntity e : ShipTracker.ships(c.world)) {
				if (!e.isRemoved() && e.shipType() == TYPE) {
					s = e;
				}
			}
			var p = c.player;
			return new Object[] {s == null ? null : s.pose(), p.getX(), p.getY(), p.getZ(), p.isOnGround(), p.isClimbing(), p.isSpectator(),
					c.getCameraEntity() == p, p.hasVehicle(), p.horizontalCollision, p.getVelocity().y};
		});
		if (sv == null || cl[0] == null) {
			log.accept(TYPE.id() + " diag " + tag + ": no ship");
			return;
		}
		ShipPose sp = new ShipPose(sv[0], sv[1], sv[2], sv[3]), cp = (ShipPose) cl[0];
		double px = (Double) cl[1], py = (Double) cl[2], pz = (Double) cl[3];
		double[] ls = sp.toLocal(px, py, pz), lc = cp.toLocal(px, py, pz), lsv = sp.toLocal(sv[6], sv[7], sv[8]);
		double[] lag = sp.toLocal(cp.x(), cp.y(), cp.z());
		log.accept(String.format(Locale.ROOT,
				"%s diag %s: speed %.2f vy %.2f, client hull lags (local %.2f %.2f %.2f, yaw %.2f); player local %.2f %.2f %.2f (server hull) "
						+ "%.2f %.2f %.2f (client hull), server copy %.2f %.2f %.2f; ground %s climbing %s spectator %s camera %s riding %s "
						+ "hcoll %s vy %.3f",
				TYPE.id(), tag, sv[4], sv[5], lag[0], lag[1], lag[2], ShipPose.wrapDegrees(cp.yaw() - sp.yaw()), ls[0], ls[1], ls[2], lc[0],
				lc[1], lc[2], lsv[0], lsv[1], lsv[2], cl[4], cl[5], cl[6], cl[7], cl[8], cl[9], (Double) cl[10]));
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
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);   // clean screenshots
		double keel = p0.y() + g.lowestY();
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f, ground %d, keel %.2f", id, p0.x(), p0.y(), p0.z(), ground, keel));
		check.accept(keel >= ground + 0.9 && keel < ground + 4, String.format(Locale.ROOT, "%s placed in the air above the ground (keel %.2f, ground %d)",
				id, keel, ground));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");
		context.waitTicks(40);
		ShipPose hover = pose(server);
		check.accept(Math.abs(hover.y() - p0.y()) < 0.01, String.format(Locale.ROOT, "%s hovers (%.3f -> %.3f)", id, p0.y(), hover.y()));

		// parked: the engine is still (gears, pistons)
		float[] a0 = anim(context);
		context.waitTicks(20);
		float[] a1 = anim(context);
		check.accept(a0 != null && a1 != null && a0[0] == a1[0], String.format(Locale.ROOT, "%s parked: the engine is still (phase %s -> %s)", id,
				a0 == null ? "?" : a0[0], a1 == null ? "?" : a1[0]));

		// the views of the reference sheet, then close-ups of the balloon, the fins and the suspended hull
		String[] names = {"1_cote", "2_avant", "3_arriere", "4_dessus", "5_perspective", "18_ballon", "19_ailerons", "20_coque_suspendue"};
		double[][] eyes = { // eye x, y, z, target x, y, z
				{48, 12.5, -1, 0, 12.5, -1}, {0, 13, 60, 0, 13, -1}, {0, 13, -62, 0, 13, -1}, {8, 68, -1, 0, 10, -1}, {44, 24, 40, 0, 11, -1},
				{30, 21, 7, 0, 17.0, -2}, {17, 25, -46, 0, 17.5, -27}, {29, 1.5, 5, 0, 0.5, -1.5}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, hover, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 30 : 15);
			shot.accept(id + "_" + names[k]);
		}

		// the rooms, furnished with the decoration mods (their stand-ins when a mod is missing), from the
		// viewpoints of the reference sheet's interior views
		String[] rooms = {"9_salle_commune", "10_cabine_capitaine", "11_bureau_capitaine", "12_salle_cartes", "13_cale", "14_coursive",
				"15_salle_machines", "16_pont_principal", "17_salle_machines_arriere"};
		double[][] cams = { // eye x, y, z, target x, y, z
				{2.7, -1.38, 4.3, -1.6, -2.5, 8.8}, {-1.2, 1.62, -14.6, 2.2, 0.5, -17.8}, {0.6, 1.62, -8.6, -1.6, 0.6, -12.0},
				{0.0, 4.62, -15.8, 0.0, 3.6, -19.5}, {0.3, -3.88, 5.9, -0.3, -4.8, -2.0}, {0.0, -1.38, 0.3, 0.0, -1.9, -9.0},
				{0.1, -1.38, -10.9, 0.0, -3.4, -14.2}, {3.6, 1.62, 4.5, 0.0, 3.0, -11.0},
				{-1.95, -3.4, -13.6, 0.2, -4.3, -16.2}}; // beside the boiler, aft to the piston engine and its flywheel
		for (int k = 0; k < rooms.length; k++) {
			double[] c = cams[k];
			lookLocal(server, hover, c[0], c[1], c[2], c[3], c[4], c[5]);
			context.waitTicks(k == 0 ? 20 : rooms[k].startsWith("15") ? 40 : 10);
			shot.accept(id + "_" + rooms[k]);
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
		lookLocal(server, pose(server), l[0], l[1] + 1.62, l[2], 0.0, 2.0, 9.0);   // turned towards the bow, over the deck
		context.waitTicks(10);
		shot.accept(id + "_6_pont");

		// the captain's door, then into the captain's quarters
		setDoor(server, LeviathanLayout.CAPTAIN_DOOR, true);
		tpLocal(server, pose(server), 0, 0.05, -6.6, 180, 0);
		context.waitTicks(15);
		context.getInput().holdKeyFor(o -> o.forwardKey, 25);
		context.waitTicks(10);
		l = local(context, server);
		check.accept(l[2] < -8.3 && Math.abs(l[1]) < 0.08, String.format(Locale.ROOT, "%s walks into the captain's quarters (local z %.2f y %.2f)", id, l[2], l[1]));
		lookLocal(server, pose(server), l[0], l[1] + 1.62, l[2], -2.6, 0.6, -11.2);   // the captain's desk, not the bedroom door
		context.waitTicks(10);
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
		float[] climbing0 = anim(context);
		context.getInput().releaseKey(o -> o.jumpKey);
		ShipPose s1 = pose(server);
		check.accept(s1.y() - s0.y() > 1.5, String.format(Locale.ROOT, "%s climbs slowly under command (%.2f blocks in 4 s)", id, s1.y() - s0.y()));
		check.accept(climbing0 != null && climbing0[2] > 0.3, String.format(Locale.ROOT, "%s climbing: the elevator fins follow (climb %.2f)", id,
				climbing0 == null ? 0f : climbing0[2]));
		float[] a2 = anim(context);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(80);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose s2 = pose(server);
		double dist = Math.hypot(s2.x() - s1.x(), s2.z() - s1.z());
		check.accept(dist > 1.0, String.format(Locale.ROOT, "%s flies forward under command (%.2f blocks in 4 s)", id, dist));
		float[] a3 = anim(context);
		check.accept(a2 != null && a3 != null && a3[0] - a2[0] > 0.3, String.format(Locale.ROOT,
				"%s under way: the engine turns (phase %.2f -> %.2f)", id, a2 == null ? 0f : a2[0], a3 == null ? 0f : a3[0]));
		// a turn to port, still climbing: the rudder fins follow the helm, the side fins the climb; seen from a
		// camera behind the fins (an invisible marker armour stand) while the helm is hard over
		context.getInput().holdKey(o -> o.forwardKey);
		context.getInput().holdKey(o -> o.leftKey);
		context.getInput().holdKey(o -> o.jumpKey);
		context.waitTicks(36);
		ShipPose sp = pose(server);
		double[] ce = sp.toWorld(17, 25, -46), ct = sp.toWorld(0, 17.5, -27);
		double cdx = ct[0] - ce[0], cdy = ct[1] - ce[1], cdz = ct[2] - ce[2];
		server.runCommand(String.format(Locale.ROOT,
				"summon armor_stand %.3f %.3f %.3f {Tags:[\"leviathan_cam\"],Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,Rotation:[%.1ff,%.1ff]}",
				ce[0], ce[1], ce[2], (float) Math.toDegrees(Math.atan2(-cdx, cdz)), (float) -Math.toDegrees(Math.atan2(cdy, Math.hypot(cdx, cdz)))));
		context.waitTicks(4);
		float[] a4 = anim(context);
		boolean camera = context.computeOnClient((MinecraftClient c) -> {
			for (net.minecraft.entity.Entity e : c.world.getEntities()) {
				if (e instanceof net.minecraft.entity.decoration.ArmorStandEntity && e.squaredDistanceTo(ce[0], ce[1], ce[2]) < 1.0) {
					c.setCameraEntity(e);
					return true;
				}
			}
			return false;
		});
		context.waitTicks(2);
		shot.accept(id + "_21_ailerons_en_virage");
		context.runOnClient((MinecraftClient c) -> c.setCameraEntity(c.player));
		server.runCommand("kill @e[type=armor_stand,tag=leviathan_cam]");
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.getInput().releaseKey(o -> o.jumpKey);
		log.accept(id + " fins shot from " + (camera ? "the camera behind the fins" : "the helm (no camera)"));
		check.accept(a4 != null && Math.abs(a4[1]) > 0.3 && a4[2] > 0.3, String.format(Locale.ROOT,
				"%s turning and climbing: rudder and elevator fins over (helm %.2f, climb %.2f)", id, a4 == null ? 0f : a4[1], a4 == null ? 0f : a4[2]));
		check.accept(collisions(server) == 0, id + " flight: inside nothing");
		diag(context, server, log, "before dismount");
		server.runCommand("ride @p dismount");
		for (int i = 0; i < 10; i++) {
			context.waitTicks(1);
			diag(context, server, log, "dismount +" + (i + 1));
		}
		l = local(context, server);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]) && Math.abs(l[1] - LeviathanLayout.QUARTERDECK_Y) < 0.15,
				String.format(Locale.ROOT, "%s the pilot steps off onto the quarterdeck (local %.2f %.2f %.2f)", id, l[0], l[1], l[2]));
		// still under way (strong inertia): the engine room running
		server.runCommand("gamemode spectator @a");
		float[] a5 = anim(context);
		double[] ec = cams[8];
		lookLocal(server, pose(server), ec[0], ec[1], ec[2], ec[3], ec[4], ec[5]);
		context.waitTicks(4);
		shot.accept(id + "_22_salle_machines_en_marche");
		float[] a6 = anim(context);
		check.accept(a5 != null && a6 != null && a6[0] != a5[0], String.format(Locale.ROOT,
				"%s coasting: the engine still turns (phase %.2f -> %.2f)", id, a5 == null ? 0f : a5[0], a6 == null ? 0f : a6[0]));
		server.runCommand("gamemode survival @a");

		// the ladder of the tower, up through the balloon to the observation deck
		setDoor(server, LeviathanLayout.TOWER_DOOR, true);
		setDoor(server, LeviathanLayout.TOP_HATCH, true);
		diag(context, server, log, "before the tower");
		tpLocal(server, pose(server), 0, 0.05, -1.5, 180, -30);
		for (int i = 0; i < 10; i++) {
			context.waitTicks(1);
			diag(context, server, log, "tower +" + (i + 1));
		}
		context.getInput().holdKey(o -> o.jumpKey);
		context.getInput().holdKey(o -> o.forwardKey);
		double top = -99;
		for (int i = 0; i < 30 && top < LeviathanLayout.TOP_DECK_Y - 0.1; i++) {
			context.waitTicks(10);
			diag(context, server, log, "ladder " + i);
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
		lookLocal(server, pose(server), l[0], l[1] + 1.62, l[2], 0.0, LeviathanLayout.TOP_DECK_Y, -10.0);   // along the deck, aft
		context.waitTicks(10);
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
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		context.waitTicks(10);
	}
}
