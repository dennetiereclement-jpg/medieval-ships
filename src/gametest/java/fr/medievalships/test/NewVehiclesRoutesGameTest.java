package fr.medievalships.test;

import java.util.Locale;
import java.util.Optional;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnReason;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.nbt.NbtElement;
import net.minecraft.nbt.NbtOps;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.NbtReadView;
import net.minecraft.storage.NbtWriteView;
import net.minecraft.util.ErrorReporter;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.Heightmap;

import fr.medievalships.core.Autopilot;
import fr.medievalships.core.CorsairLayout;
import fr.medievalships.core.LeviathanLayout;
import fr.medievalships.core.Route;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * Routes and persistence of the Old Corsair and the Sky Leviathan in a real game (called from
 * {@link ShipClientGameTest}): each one gets a route made with the /ship route commands, leaves its
 * first stop after the wait, sails / flies to the next stop and moors there (the airship at its
 * landing clearance over the ground, not on the quay height under its hanging fin); then its saved
 * data (the entity NBT written by the game's own save code, read back into a fresh entity, and the
 * route in the world data) keeps its position, heading, altitude, route, autopilot state and doors.
 * About 75 seconds of game time.
 */
public final class NewVehiclesRoutesGameTest {
	private NewVehiclesRoutesGameTest() {
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log) {
		try {
			corsair(context, server, world, check, log);
		} catch (RuntimeException e) {
			check.accept(false, "old_corsair route test: exception " + e);
		}
		try {
			leviathan(context, server, world, check, log);
		} catch (RuntimeException e) {
			check.accept(false, "sky_leviathan route test: exception " + e);
		}
	}

	// ------------------------------------------------------------------ the Old Corsair: a sea route

	private static void corsair(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log) {
		ShipType type = Ships.OLD_CORSAIR;
		String id = type.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand("tp @p 415 -25 -20 0 40");
		// a basin 29 wide, 114 long, 14 deep, walled with glass
		int x0 = 400, x1 = 430, z0 = -40, z1 = 75, top = -46;
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", x0, z0, x1, z1));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x1, top, z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z1, x1, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x0, z0, x0, top, z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", x1, z0, x1, top, z1));
		for (int z = z0 + 1; z < z1; z += 30) {
			int zz = Math.min(z1 - 1, z + 29);
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", x0 + 1, z, x1 - 1, zz));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -20 %d air", x0 + 1, z, x1 - 1, zz));
		}
		server.runCommand("execute positioned 415 -50 -5 rotated 0 0 run ship spawn " + id);
		world.waitForChunksRender();
		context.waitTicks(40);
		ShipPose a = pose(server, type);
		if (a == null) {
			check.accept(false, id + " route: spawned in the basin");
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
			return;
		}
		// the route, with the commands: a stop where it is (3 s), a quay 36 blocks ahead (8 s), back and forth
		String route = "nv_corsaire";
		double bz = a.z() + 36;
		server.runCommand("ship route delete " + route);
		server.runCommand("ship route create " + route + " pingpong");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addstop %s 3 Depart", a.x(), a.y(), a.z(), route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addstop %s 8 Quai", a.x(), a.y(), bz, route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route start %s", a.x(), a.y(), a.z(), route));
		context.waitTicks(1);
		Object[] st = state(server, type);
		log.accept(String.format(Locale.ROOT, "%s route: started at %.2f %.2f %.2f, %s", id, a.x(), a.y(), a.z(), describe(st)));
		check.accept(st != null && (Boolean) st[0] && route.equals(st[1]) && st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 0,
				id + " route: /ship route start puts it on the route, moored at its first stop (" + describe(st) + ")");
		// it leaves after 3 s and heads for the quay
		double startDist = bz - a.z();
		double minDist = startDist, maxSpeed = 0;
		boolean departed = false, docked = false;
		int collisions = 0;
		ShipPose p = a;
		for (int s = 0; s < 45 && !docked; s++) {
			context.waitTicks(20);
			st = state(server, type);
			p = pose(server, type);
			if (st == null || p == null) {
				break;
			}
			minDist = Math.min(minDist, Math.hypot(p.x() - a.x(), p.z() - bz));
			maxSpeed = Math.max(maxSpeed, (Double) st[5]);
			collisions = Math.max(collisions, collisions(server, type));
			departed |= st[2] == Autopilot.Phase.SAILING && (Integer) st[3] == 1;
			docked = st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 1;
			if (s % 5 == 0 || docked) {
				log.accept(String.format(Locale.ROOT, "%s route t=%ds: z %.2f (quay %.2f) %s", id, s + 1, p.z(), bz, describe(st)));
			}
		}
		check.accept(departed, id + " route: leaves its first stop after the wait, towards the quay");
		check.accept(startDist - minDist > 20, String.format(Locale.ROOT, "%s route: sails towards the quay (%.1f -> %.1f blocks, top speed %.2f)", id,
				startDist, minDist, maxSpeed));
		double off = p == null ? 99 : Math.hypot(p.x() - a.x(), p.z() - bz);
		check.accept(docked && off < type.defaults().get().aiStopRadius + 1.0 && Math.abs((Double) st[5]) < 0.8,
				String.format(Locale.ROOT, "%s route: stops and moors at the quay (%.2f blocks off, %s)", id, off, describe(st)));
		collisions = Math.max(collisions, collisions(server, type));
		check.accept(collisions == 0, id + " route: never inside the basin walls, all along the voyage (" + collisions + ")");

		// persistence: a door opened, the ship saved and read back
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			s.setDoor(CorsairLayout.CABIN_DOOR, true);
			s.setDoor(CorsairLayout.KITCHEN_DOOR, false);
			return true;
		});
		persistence(server, type, new int[] {CorsairLayout.CABIN_DOOR, CorsairLayout.KITCHEN_DOOR}, route, check, log);
		server.runCommand("save-all");
		context.waitTicks(5);

		cleanup(server, type, route);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}

	// ------------------------------------------------------------------ the Sky Leviathan: an air route

	private static void leviathan(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log) {
		ShipType type = Ships.SKY_LEVIATHAN;
		String id = type.id();
		ShipGeometry g = type.geometry();
		double deck = g.hull().mainDeckY;
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		int x0 = 470, x1 = 530, z0 = -50, z1 = 170;
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", x0, z0, x1, z1));
		server.runCommand("tp @p 560 -10 10 60 20");
		context.waitTicks(30);
		int ground = server.computeOnServer(srv -> srv.getOverworld().getTopY(Heightmap.Type.MOTION_BLOCKING, 500, 0));
		server.runCommand(String.format(Locale.ROOT, "execute positioned 500 %d 0 rotated 0 0 run ship spawn %s", ground, id));
		world.waitForChunksRender();
		context.waitTicks(30);
		ShipPose a = pose(server, type);
		if (a == null) {
			check.accept(false, id + " route: spawned above the ground");
			server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
			return;
		}
		// the air route: take-off stop where it is (2 s), a waypoint 60 blocks ahead set 6 blocks above the altitude
		// the ground clearance alone would give (so reaching it shows the waypoint's own height is flown), then a
		// mooring stop 115 blocks ahead set at the height of a quay on the ground (20 s), back and forth
		String route = "nv_ciel";
		double clearanceDeck = ground + type.defaults().get().flight.aiClearance - g.lowestY() + deck;
		double wy = clearanceDeck + 6, wz = a.z() + 60, by = ground + 1, bz = a.z() + 115;
		server.runCommand("ship route delete " + route);
		server.runCommand("ship route create " + route + " pingpong air");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f rotated 0 0 run ship route addstop %s 2 Envol", a.x(),
				a.y() + deck, a.z(), route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addpoint %s", a.x(), wy, wz, route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f rotated 0 0 run ship route addstop %s 20 Mouillage", a.x(), by,
				bz, route));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route start %s", a.x(), a.y(), a.z(), route));
		context.waitTicks(1);
		Object[] st = state(server, type);
		log.accept(String.format(Locale.ROOT, "%s route: started at %.2f %.2f %.2f (ground %d), %s", id, a.x(), a.y(), a.z(), ground, describe(st)));
		check.accept(st != null && (Boolean) st[0] && route.equals(st[1]) && st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 0,
				id + " route: /ship route start puts it on the air route, at its take-off stop (" + describe(st) + ")");
		double startDist = bz - a.z();
		double minDist = startDist, maxY = a.y();
		boolean departed = false, docked = false;
		int collisions = 0;
		ShipPose p = a;
		for (int s = 0; s < 75 && !docked; s++) {
			context.waitTicks(20);
			st = state(server, type);
			p = pose(server, type);
			if (st == null || p == null) {
				break;
			}
			minDist = Math.min(minDist, Math.hypot(p.x() - a.x(), p.z() - bz));
			maxY = Math.max(maxY, p.y());
			collisions = Math.max(collisions, collisions(server, type));
			departed |= st[2] == Autopilot.Phase.SAILING;
			// moored once docked at the stop and settled at its altitude
			docked = st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 2 && Math.abs((Double) st[6]) < 0.05;
			if (s % 5 == 0 || docked) {
				log.accept(String.format(Locale.ROOT, "%s route t=%ds: z %.2f (stop %.2f) y %.2f keel %.2f %s", id, s + 1, p.z(), bz, p.y(),
						p.y() + g.lowestY(), describe(st)));
			}
		}
		check.accept(departed, id + " route: takes off from its first stop after the wait");
		check.accept(maxY + deck >= wy - 1.5, String.format(Locale.ROOT,
				"%s route: climbs to the waypoint's own altitude, above the clearance one (deck %.2f -> %.2f, waypoint deck %.2f, clearance deck %.2f)",
				id, a.y() + deck, maxY + deck, wy, clearanceDeck));
		check.accept(startDist - minDist > 90, String.format(Locale.ROOT, "%s route: flies towards the stop (%.1f -> %.1f blocks)", id, startDist,
				minDist));
		double off = p == null ? 99 : Math.hypot(p.x() - a.x(), p.z() - bz);
		double keel = p == null ? Double.NaN : p.y() + g.lowestY();
		double landing = type.defaults().get().flight.aiLandingClearance;
		check.accept(docked && off < type.defaults().get().aiStopRadius + 1.0,
				String.format(Locale.ROOT, "%s route: comes down and moors at the stop (%.2f blocks off, %s)", id, off, describe(st)));
		check.accept(keel >= ground + landing - 0.3 && keel < ground + landing + 1.0,
				String.format(Locale.ROOT, "%s route: moored at its landing clearance over the ground, not on the quay height (keel %.2f, ground %d)", id,
						keel, ground));
		check.accept(collisions == 0, id + " route: never inside the ground (" + collisions + ")");

		// persistence while moored: doors, position, heading, altitude, route and autopilot state
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			s.setDoor(LeviathanLayout.CAPTAIN_DOOR, true);
			s.setDoor(LeviathanLayout.TOWER_DOOR, false);
			return true;
		});
		persistence(server, type, new int[] {LeviathanLayout.CAPTAIN_DOOR, LeviathanLayout.TOWER_DOOR}, route, check, log);

		// and it leaves again (the wait is skipped with /ship route depart)
		ShipPose before = pose(server, type);
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route depart", before.x(), before.y(), before.z()));
		context.waitTicks(80);
		st = state(server, type);
		ShipPose after = pose(server, type);
		check.accept(st != null && st[2] == Autopilot.Phase.SAILING && (Integer) st[3] == 1 && after.y() > before.y() + 0.3,
				String.format(Locale.ROOT, "%s route: leaves the mooring again, climbing (y %.2f -> %.2f, %s)", id, before.y(), after.y(), describe(st)));

		cleanup(server, type, route);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", x0, z0, x1, z1));
	}

	// ------------------------------------------------------------------ persistence

	/**
	 * Saves the ship with the game's own entity save code (the NBT written into the region files), reads it back
	 * into a new entity (not added to the world) and compares; the route is written and read back with the codec
	 * of the world data.
	 */
	private static void persistence(TestServerContext server, ShipType type, int[] doors, String route, BiConsumer<Boolean, String> check,
			Consumer<String> log) {
		String id = type.id();
		String result = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			if (s == null) {
				return "no ship";
			}
			NbtWriteView view = NbtWriteView.create(ErrorReporter.EMPTY, srv.getRegistryManager());
			if (!s.saveSelfData(view)) {
				return "not saved";
			}
			NbtCompound nbt = view.getNbt();
			Optional<Entity> loaded = EntityType.getEntityFromData(NbtReadView.create(ErrorReporter.EMPTY, srv.getRegistryManager(), nbt), w,
					SpawnReason.LOAD);
			if (loaded.isEmpty() || !(loaded.get() instanceof ShipEntity c)) {
				return "not read back: " + nbt.getKeys();
			}
			StringBuilder bad = new StringBuilder();
			ShipPose p = s.pose(), q = c.pose();
			if (c.shipType() != type) {
				bad.append(" type");
			}
			if (Math.abs(p.x() - q.x()) > 1e-3 || Math.abs(p.z() - q.z()) > 1e-3) {
				bad.append(" position");
			}
			if (Math.abs(p.y() - q.y()) > 1e-3) {
				bad.append(" altitude");
			}
			if (Math.abs(ShipPose.wrapDegrees(p.yaw() - q.yaw())) > 0.01) {
				bad.append(" yaw ").append(q.yaw()).append("/").append(p.yaw());
			}
			if (c.isAutopilotEnabled() != s.isAutopilotEnabled() || !route.equals(c.routeName())) {
				bad.append(" route ").append(c.routeName());
			}
			Autopilot x = s.autopilot(), y = c.autopilot();
			if (x.phase != y.phase || x.target != y.target || x.direction != y.direction || Math.abs(x.waitTicks - y.waitTicks) > 1) {
				bad.append(" autopilot ").append(y.phase).append(" ").append(y.target).append(" ").append(y.waitTicks);
			}
			if (Math.abs(s.physics().speed - c.physics().speed) > 1e-6 || Math.abs(s.flight().vy - c.flight().vy) > 1e-6) {
				bad.append(" speed");
			}
			for (int d : doors) {
				if (s.doorOpen(d) != c.doorOpen(d)) {
					bad.append(" door").append(d);
				}
			}
			if (!s.doorOpen(doors[0]) || s.doorOpen(doors[1])) {
				bad.append(" (doors not set)");
			}
			// the route itself, in the world data
			ShipData data = ShipData.get(srv);
			NbtElement saved = ShipData.TYPE.codec().encodeStart(NbtOps.INSTANCE, data).getOrThrow();
			ShipData back = ShipData.TYPE.codec().parse(NbtOps.INSTANCE, saved).getOrThrow();
			Route r0 = data.route(route), r1 = back.route(route);
			if (r0 == null || r1 == null || r1.size() != r0.size() || r1.air != r0.air || r1.mode != r0.mode) {
				bad.append(" saved route");
			} else {
				for (int i = 0; i < r0.size(); i++) {
					if (Math.abs(r0.get(i).y - r1.get(i).y) > 1e-6 || r0.get(i).waitSeconds != r1.get(i).waitSeconds) {
						bad.append(" saved point ").append(i + 1);
					}
				}
			}
			return String.format(Locale.ROOT, "%s|at %.2f %.2f %.2f yaw %.1f, %s %s target %d wait %d, %d NBT keys", bad.toString().trim(), q.x(), q.y(),
					q.z(), q.yaw(), c.routeName(), y.phase, y.target, y.waitTicks, nbt.getKeys().size());
		});
		String[] parts = result.split("\\|", 2);
		log.accept(id + " saved and read back: " + result);
		check.accept(parts.length == 2 && parts[0].isEmpty(),
				id + " persistence: position, heading, altitude, speed, route, autopilot state and doors survive the save (" + result + ")");
	}

	// ------------------------------------------------------------------ helpers

	private static void cleanup(TestServerContext server, ShipType type, String route) {
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			if (s != null) {
				s.setAutopilot(false);
				s.removeAllPassengers();
				s.discard();
			}
			ShipData.get(srv).removeRoute(route);
			return true;
		});
	}

	/** {AI on, route, phase, target, wait ticks, speed, vertical speed}. */
	private static Object[] state(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			if (s == null) {
				return null;
			}
			Autopilot ap = s.autopilot();
			return new Object[] {s.isAutopilotEnabled(), s.routeName(), ap.phase, ap.target, ap.waitTicks, s.physics().speed, s.flight().vy};
		});
	}

	private static String describe(Object[] st) {
		return st == null ? "no ship" : String.format(Locale.ROOT, "ai %s route %s phase %s target %s wait %s speed %.2f vy %.2f", st[0], st[1], st[2],
				st[3], st[4], (Double) st[5], (Double) st[6]);
	}

	/** Probe points of the ship inside a block with a collision shape. */
	private static int collisions(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			if (s == null) {
				return 0;
			}
			ShipPose p = s.pose();
			int n = 0;
			BlockPos.Mutable pos = new BlockPos.Mutable();
			for (double[] l : type.geometry().probes()) {
				double[] wp = p.toWorld(l[0], l[1], l[2]);
				pos.set(Math.floor(wp[0]), Math.floor(wp[1]), Math.floor(wp[2]));
				if (!w.getBlockState(pos).getCollisionShape(w, pos).isEmpty()) {
					n++;
				}
			}
			return n;
		});
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose pose(TestServerContext server, ShipType type) {
		return server.computeOnServer((MinecraftServer srv) -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : s.pose();
		});
	}
}
