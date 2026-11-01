package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.block.Blocks;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.Autopilot;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * A quest scripted with commands only, as an NPC or a command block would run it (called once from
 * {@link ShipClientGameTest}, about 50 s of game time): a {@code once} route with a held stop at the quay and a timed
 * stop at the port that vanishes the ship at its end, an arrival command, a galley spawned on the route by name and
 * held at the quay ({@code /ship spawn galley route ... wait named ...}), the player boarding ({@code /ship test ...
 * aboard}, {@code /execute if ship ... aboard}), the departure on the order ({@code /ship as "La Sirène" route
 * depart}), the crossing with the player carried, the mooring at the port where the arrival command runs, the
 * passengers landed on the quay ({@code /ship as ... disembark}) and the ship vanishing after the port's wait.
 */
public final class QuestCommandsGameTest {
	/** The test area: a basin x0..x1, z0..z1 (glass walls), water up to y=-49, a stone quay along the east wall at the port. */
	private static final int X0 = -420, X1 = -390, Z0 = -40, Z1 = 70, TOP = -46;
	private static final int SHIP_X = -408, QUAY_Z = -22, PORT_Z = 38;
	private static final String ROUTE = "pnj_traversee";
	private static final String NAME = "La Sirène";
	private static final String SELECTOR = "\"La Sirène\"";
	/** Set by the arrival command of the port, and by /execute if ship ... aboard. */
	private static final BlockPos ARRIVED = new BlockPos(-395, -47, PORT_Z);
	private static final BlockPos ABOARD = new BlockPos(-395, -47, QUAY_Z);

	private QuestCommandsGameTest() {
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		try {
			scenario(context, server, world, check, log, shot);
		} catch (RuntimeException e) {
			check.accept(false, "quest commands: exception " + e);
		} finally {
			cleanup(server);
		}
	}

	private static void scenario(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		ShipType type = Ships.GALLEY;
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 %d 0 45", SHIP_X, QUAY_Z + 10));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X1, TOP, Z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z1, X1, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X0, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X1, Z0, X1, TOP, Z1));
		for (int z = Z0 + 1; z < Z1; z += 30) {
			int zz = Math.min(Z1 - 1, z + 29);
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", X0 + 1, z, X1 - 1, zz));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -20 %d air", X0 + 1, z, X1 - 1, zz));
		}
		// the quay of the port: stone along the east wall, its top level with the water surface
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d stone", X1 - 8, PORT_Z - 8, X1 - 1, PORT_Z + 8));
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d %d air", ARRIVED.getX(), ARRIVED.getY(), ARRIVED.getZ()));
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d %d air", ABOARD.getX(), ABOARD.getY(), ABOARD.getZ()));
		world.waitForChunksRender();
		context.waitTicks(10);

		// --- the route, as an administrator scripts it once
		server.runCommand("ship route delete " + ROUTE);
		server.runCommand("ship route create " + ROUTE + " once");
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -49 %d run ship route addstop %s hold Quai du village", SHIP_X, QUAY_Z, ROUTE));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -49 %d run ship route addstop %s 8 Port", SHIP_X, PORT_Z, ROUTE));
		server.runCommand("ship route end " + ROUTE + " despawn");
		server.runCommand(String.format(Locale.ROOT, "ship route onarrive %s 2 setblock %d %d %d minecraft:gold_block", ROUTE,
				ARRIVED.getX(), ARRIVED.getY(), ARRIVED.getZ()));
		context.waitTicks(2);
		String saved = server.computeOnServer(srv -> {
			var r = ShipData.get(srv).route(ROUTE);
			return r == null ? "no route" : String.format(Locale.ROOT, "%s %s %d points, stop1 wait %d, stop2 wait %d, onarrive %s", r.mode, r.end(),
					r.size(), r.get(0).waitSeconds, r.get(1).waitSeconds, r.get(1).onArrive);
		});
		log.accept("quest route: " + saved);
		check.accept(saved.startsWith("ONCE DESPAWN 2 points, stop1 wait -1, stop2 wait 8, onarrive setblock"),
				"quest: the route is scripted with hold stop, despawn end and arrival command (" + saved + ")");

		// --- the NPC spawns the ship at the quay, on the route, held, by name
		server.runCommand(String.format(Locale.ROOT, "ship spawn %s route %s wait named %s", type.id(), ROUTE, NAME));
		world.waitForChunksRender();
		context.waitTicks(20);
		Object[] st = state(server);
		ShipPose a = pose(server);
		log.accept("quest spawn: " + describe(st) + (a == null ? "" : String.format(Locale.ROOT, " at %.2f %.2f %.2f yaw %.1f", a.x(), a.y(), a.z(), a.yaw())));
		check.accept(st != null, "quest: /ship spawn <type> route <name> wait named <name> spawns the named ship");
		if (st == null || a == null) {
			return;
		}
		check.accept((Boolean) st[0] && ROUTE.equals(st[1]) && st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 0 && (Boolean) st[5],
				"quest: spawned at the first stop of the route, moored and held (" + describe(st) + ")");
		check.accept(Math.hypot(a.x() - SHIP_X, a.z() - QUAY_Z) < 3 && Math.abs(ShipPose.wrapDegrees(a.yaw())) < 2,
				String.format(Locale.ROOT, "quest: spawned at the quay facing the port (%.1f %.1f yaw %.1f)", a.x(), a.z(), a.yaw()));
		check.accept(testCommand(server, "ship test " + SELECTOR + " holding") == 1, "quest: /ship test <name> holding says yes");
		check.accept(testCommand(server, "ship test " + SELECTOR + " aboard @p") == 0, "quest: /ship test <name> aboard @p says no before boarding");
		check.accept(testCommand(server, "ship test " + SELECTOR + " at 1") == 1, "quest: /ship test <name> at 1 says yes at the quay");

		// --- the player boards (on the deck, carried) ; the NPC checks everyone is aboard
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		double deck = a.y() + type.hull().mainDeckY;
		double[] onDeck = a.toWorld(0, type.hull().mainDeckY + 0.6, -2);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f 0 20", onDeck[0], onDeck[1], onDeck[2]));
		context.waitTicks(30);
		double[] p = playerPos(context);
		log.accept(String.format(Locale.ROOT, "quest: player on deck at %.2f %.2f %.2f (deck %.2f)", p[0], p[1], p[2], deck));
		int aboard = testCommand(server, "ship test " + SELECTOR + " aboard @p");
		check.accept(aboard == 1, "quest: /ship test <name> aboard @p says yes once the player stands on the deck (" + aboard + ")");
		server.runCommand(String.format(Locale.ROOT, "execute if ship %s aboard @p run setblock %d %d %d minecraft:emerald_block", SELECTOR, ABOARD.getX(),
				ABOARD.getY(), ABOARD.getZ()));
		server.runCommand(String.format(Locale.ROOT, "execute unless ship %s aboard @p run setblock %d %d %d minecraft:redstone_block", SELECTOR,
				ABOARD.getX(), ABOARD.getY(), ABOARD.getZ()));
		context.waitTicks(2);
		check.accept(block(server, ABOARD) == Blocks.EMERALD_BLOCK, "quest: /execute if|unless ship <name> aboard @p works as a condition ("
				+ block(server, ABOARD) + ")");
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot.accept("quest_01_held_at_quay");
		// held: four more seconds and it has not moved
		context.waitTicks(80);
		st = state(server);
		ShipPose held = pose(server);
		check.accept(st != null && st[2] == Autopilot.Phase.DOCKED && (Boolean) st[5] && held != null && Math.hypot(held.x() - a.x(), held.z() - a.z()) < 0.5,
				"quest: held at the quay until told to leave (" + describe(st) + ")");

		// --- the NPC gives the order
		server.runCommand("ship as " + SELECTOR + " route depart");
		context.waitTicks(40);
		st = state(server);
		check.accept(st != null && st[2] == Autopilot.Phase.SAILING && (Integer) st[3] == 1,
				"quest: /ship as <name> route depart makes it leave towards the port (" + describe(st) + ")");
		check.accept(testCommand(server, "ship test " + SELECTOR + " sailing") == 1, "quest: /ship test <name> sailing says yes under way");
		boolean docked = false, carried = true;
		double minDist = Math.abs(PORT_Z - a.z());
		ShipPose q = a;
		for (int s = 0; s < 45 && !docked; s++) {
			context.waitTicks(20);
			st = state(server);
			q = pose(server);
			if (st == null || q == null) {
				break;
			}
			minDist = Math.min(minDist, Math.hypot(q.x() - SHIP_X, q.z() - PORT_Z));
			docked = st[2] == Autopilot.Phase.DOCKED && (Integer) st[3] == 1;
			if (s == 3) {
				p = playerPos(context);
				double[] l = q.toLocal(p[0], p[1], p[2]);
				carried = Math.abs(l[0]) < 3 && Math.abs(l[2] + 2) < 3 && Math.abs(p[1] - (q.y() + type.hull().mainDeckY)) < 0.3;
				log.accept(String.format(Locale.ROOT, "quest t=%ds: player local %.2f %.2f %.2f while sailing", s + 1, l[0], l[1], l[2]));
			}
			if (s % 5 == 0 || docked) {
				log.accept(String.format(Locale.ROOT, "quest t=%ds: z %.2f (port %d) %s", s + 1, q.z(), PORT_Z, describe(st)));
			}
		}
		check.accept(carried, "quest: the player is carried on the deck during the crossing");
		double off = q == null ? 99 : Math.hypot(q.x() - SHIP_X, q.z() - PORT_Z);
		check.accept(docked && off < type.defaults().get().aiStopRadius + 1.0 && Math.abs((Double) st[4]) < 0.8,
				String.format(Locale.ROOT, "quest: sails to the port and moors there (%.2f blocks off, %s)", off, describe(st)));
		context.waitTicks(5);
		check.accept(block(server, ARRIVED) == Blocks.GOLD_BLOCK, "quest: the arrival command of the port ran (" + block(server, ARRIVED) + ")");
		check.accept(testCommand(server, "ship test " + SELECTOR + " at 2") == 1, "quest: /ship test <name> at 2 says yes at the port");
		shot.accept("quest_02_arrived_at_port");

		// --- everybody ashore
		int landed = testCommand(server, "ship as " + SELECTOR + " disembark");
		context.waitTicks(10);
		p = playerPos(context);
		boolean onQuay = p[0] >= X1 - 8.5 && p[0] <= X1 - 0.5 && Math.abs(p[1] - (-49)) < 0.3 && Math.abs(p[2] - PORT_Z) < 9;
		log.accept(String.format(Locale.ROOT, "quest: disembark -> %d, player at %.2f %.2f %.2f", landed, p[0], p[1], p[2]));
		check.accept(landed == 1 && onQuay, String.format(Locale.ROOT, "quest: /ship as <name> disembark lands the player on the quay (%.1f %.1f %.1f)",
				p[0], p[1], p[2]));
		check.accept(testCommand(server, "ship test " + SELECTOR + " aboard @p") == 0 && testCommand(server, "ship test " + SELECTOR + " empty") == 1,
				"quest: nobody aboard after disembarking");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f -90 10", p[0], p[1], p[2]));
		context.waitTicks(5);
		shot.accept("quest_03_landed_on_quay");

		// --- the ship vanishes after the port's wait (8 s from the arrival)
		boolean gone = false;
		for (int s = 0; s < 14 && !gone; s++) {
			context.waitTicks(20);
			gone = state(server) == null;
		}
		check.accept(gone, "quest: the ship vanishes at the end of its once route (end despawn) after the port's wait");
		boolean routeKept = server.computeOnServer(srv -> ShipData.get(srv).route(ROUTE) != null);
		check.accept(routeKept, "quest: the route stays for the next trip");
		int ferries = server.computeOnServer(srv -> ShipData.get(srv).ferries().size());
		log.accept("quest: ferry records left " + ferries);
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
	}

	// ------------------------------------------------------------------ helpers

	private static void cleanup(TestServerContext server) {
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			if (s != null) {
				s.setAutopilot(false);
				s.removeAllPassengers();
				s.discard();
			}
			ShipData.get(srv).removeRoute(ROUTE);
			return true;
		});
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
	}

	/** The result of a command run by the server (as the console), -1 when it fails. */
	private static int testCommand(TestServerContext server, String command) {
		return server.computeOnServer(srv -> {
			try {
				return srv.getCommandManager().getDispatcher().execute(command, srv.getCommandSource());
			} catch (Exception e) {
				System.out.println("[medievalships-test] /" + command + " failed: " + e.getMessage());
				return -1;
			}
		});
	}

	private static net.minecraft.block.Block block(TestServerContext server, BlockPos pos) {
		return server.computeOnServer(srv -> srv.getOverworld().getBlockState(pos).getBlock());
	}

	/** The named ship of the scenario (not another test's galley). */
	private static ShipEntity ship(ServerWorld world) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.hasCustomName() && NAME.equals(s.getCustomName().getString())) {
				return s;
			}
		}
		return null;
	}

	/** {AI on, route, phase, target, speed, holding}. */
	private static Object[] state(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			if (s == null) {
				return null;
			}
			Autopilot ap = s.autopilot();
			return new Object[] {s.isAutopilotEnabled(), s.routeName(), ap.phase, ap.target, s.physics().speed, ap.holding()};
		});
	}

	private static String describe(Object[] st) {
		return st == null ? "no ship" : String.format(Locale.ROOT, "ai %s route %s phase %s target %s speed %.2f holding %s", st[0], st[1], st[2], st[3],
				(Double) st[4], st[5]);
	}

	private static ShipPose pose(TestServerContext server) {
		return server.computeOnServer((MinecraftServer srv) -> {
			ShipEntity s = ship(srv.getOverworld());
			return s == null ? null : s.pose();
		});
	}

	private static double[] playerPos(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ()});
	}
}
