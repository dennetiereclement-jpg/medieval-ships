package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnReason;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.NbtReadView;
import net.minecraft.storage.NbtWriteView;
import net.minecraft.text.Text;
import net.minecraft.util.ErrorReporter;

import fr.medievalships.core.Gangplank;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the boarding gangplanks (dry dock of their own, built by commands): the trade sloop beside a stone
 * quay, its lever clicked for real (client pick, payload, server toggle) -> DEPLOYING -> 3 s -> DEPLOYED with the
 * collision boxes registered on the client; a survival player walks from the quay up the plank onto the deck and back
 * down to the quay (forward key only); retracting is refused while he stands on the plank, accepted once clear; the
 * pilot's thrust is ignored while the plank is out; a block in the swing refuses the deploy; the entity's NBT keeps a
 * coherent state (a move in progress resolves to an end state, a plank whose quay is gone retracts after the
 * reload); the steampunk airship refuses in the air with no platform and deploys beside one. Called from
 * {@link ShipClientGameTest} (solo and on the dedicated server).
 */
public final class GangplankGameTest {
	private static final ShipType SLOOP = Ships.TRADE_SLOOP;
	private static final ShipType AIRSHIP = Ships.STEAMPUNK_AIRSHIP;
	/** The dock: a stone quay (top y -48) west of a water basin (surface about -49.1). */
	private static final int X0 = 1190, X1 = 1242, Z0 = -18, Z1 = 18;
	private static final int QUAY_EAST = 1216, QUAY_TOP = -49;
	private static final int SHIP_X = 1222;
	/** The airship's sky: far from the dock. */
	private static final int AX = 1320, AY = -35;

	private GangplankGameTest() {
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipEntity clientShip(MinecraftClient mc, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(mc.world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipPose pose(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : s.pose();
		});
	}

	private static Gangplank.State serverState(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : s.gangplankState();
		});
	}

	/** The plank as the client sees it: {state ordinal, number of collision boxes it adds, angle}. */
	private static double[] clientPlank(ClientGameTestContext context, ShipType type) {
		return context.computeOnClient(mc -> {
			ShipEntity s = clientShip(mc, type);
			if (s == null) {
				return new double[] {-1, 0, 0};
			}
			int[] n = {0};
			s.collectGangplankBoxes(-3e7, -1e3, -3e7, 3e7, 1e3, 3e7, (a, b, c, d, e, f) -> n[0]++);
			return new double[] {s.gangplankState().ordinal(), n[0], s.gangplankTarget()};
		});
	}

	private static String lever(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			Text t = s == null ? null : s.useGangplankLever(srv.getOverworld());
			return t == null ? "" : t.getString();
		});
	}

	private static double[] player(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ(),
				c.player.isOnGround() ? 1 : 0});
	}

	private static void tpWorld(TestServerContext server, double x, double y, double z, float yaw, float pitch) {
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", x, y, z, yaw, pitch));
	}

	private static void lookLocal(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		tpWorld(server, e[0], e[1] - 1.62, e[2], yaw, pitch);
	}

	/** World yaw of a ship-local horizontal direction. */
	private static float yawLocal(ShipPose pose, double lx, double lz) {
		double[] d = pose.dirToWorld(lx, 0, lz);
		return (float) ShipPose.yawOf(d[0], d[2]);
	}

	private static String roundTrip(TestServerContext server, String expectState) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, SLOOP);
			if (s == null) {
				return "no ship";
			}
			NbtWriteView view = NbtWriteView.create(ErrorReporter.EMPTY, srv.getRegistryManager());
			if (!s.saveSelfData(view)) {
				return "not saved";
			}
			java.util.Optional<Entity> loaded = EntityType.getEntityFromData(
					NbtReadView.create(ErrorReporter.EMPTY, srv.getRegistryManager(), view.getNbt()), w, SpawnReason.LOAD);
			if (loaded.isEmpty() || !(loaded.get() instanceof ShipEntity c)) {
				return "not read back";
			}
			String bad = "";
			if (!c.gangplankState().name().equals(expectState)) {
				bad += " state " + c.gangplankState() + " (saved " + s.gangplankState() + ")";
			}
			if (Math.abs(c.gangplankTarget() - s.gangplankTarget()) > 1e-4) {
				bad += " angle " + c.gangplankTarget();
			}
			return bad.isEmpty() ? "ok" : bad;
		});
	}

	private static void waitState(ClientGameTestContext context, TestServerContext server, ShipType type, Gangplank.State want, int maxTicks) {
		for (int t = 0; t < maxTicks; t += 5) {
			if (serverState(server, type) == want) {
				return;
			}
			context.waitTicks(5);
		}
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		Gangplank.Spec spec = Gangplank.of(SLOOP.id());
		check.accept(spec != null, "trade_sloop has a gangplank spec");
		if (spec == null) {
			return;
		}
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		tpWorld(server, SHIP_X - 14, -40, 0, -90, 20);
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		context.waitTicks(20);
		// the dock: stone quay, deep water, glass walls
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -30 %d air", X0, Z0, X1, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", X0, Z0, QUAY_EAST, QUAY_TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", QUAY_EAST + 1, Z0 + 1, X1 - 1, Z1 - 1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -49 %d glass", QUAY_EAST + 1, Z0, X1, Z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -49 %d glass", QUAY_EAST + 1, Z1, X1, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -49 %d glass", X1, Z0, X1, Z1));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 0 rotated 0 0 run ship spawn %s", SHIP_X, SLOOP.id()));
		world.waitForChunksRender();
		context.waitTicks(60);
		ShipPose p = pose(server, SLOOP);
		check.accept(p != null, "gangplank: the sloop is in the dock");
		if (p == null) {
			cleanup(context, server);
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		log.accept(String.format(Locale.ROOT, "gangplank dock: sloop at %.2f %.2f %.2f yaw %.1f", p.x(), p.y(), p.z(), p.yaw()));
		check.accept(serverState(server, SLOOP) == Gangplank.State.RETRACTED, "gangplank: stowed at spawn");
		lookLocal(server, p, -11, 6, 9, spec.hx(), spec.hy() + 1, spec.hz());
		context.waitTicks(15);
		shot.accept("passerelle_0_rangee");

		// ---- the lever, clicked for real: the client picks it, the server deploys
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		lookLocal(server, p, spec.leverX() + 0.9, spec.leverY() + 1.62, spec.leverZ() + 1.0, spec.leverX(), spec.leverY() + 0.6, spec.leverZ());
		context.waitTicks(15);
		boolean picked = context.computeOnClient(mc -> {
			var t = fr.medievalships.client.ShipPicker.current();
			return t != null && t.pick().kind() == ShipGeometry.PickKind.LEVER;
		});
		check.accept(picked, "gangplank: the crosshair picks the lever on the deck");
		if (picked) {
			context.getInput().pressKey(o -> o.useKey);
		} else {
			lever(server, SLOOP);
		}
		context.waitTicks(4);
		Gangplank.State st = serverState(server, SLOOP);
		check.accept(st == Gangplank.State.DEPLOYING, "gangplank: the lever starts the deploy (" + st + ")");
		context.waitTicks(6);
		double[] cp = clientPlank(context, SLOOP);
		check.accept(cp[0] == Gangplank.State.DEPLOYING.ordinal() && cp[1] == 0,
				String.format(Locale.ROOT, "gangplank: the client sees it moving, no collision yet (state %.0f, boxes %.0f)", cp[0], cp[1]));
		lookLocal(server, p, -9, 4.5, 8, spec.hx() - 1.5, spec.hy() - 0.5, spec.hz());
		context.waitTicks(16);
		shot.accept("passerelle_1_deploiement");
		waitState(context, server, SLOOP, Gangplank.State.DEPLOYED, 60);
		context.waitTicks(5);
		st = serverState(server, SLOOP);
		cp = clientPlank(context, SLOOP);
		double angle = cp[2];
		log.accept(String.format(Locale.ROOT, "gangplank: deployed at %.1f degrees, %.0f boxes on the client", angle, cp[1]));
		check.accept(st == Gangplank.State.DEPLOYED, "gangplank: DEPLOYED about 3 s later (" + st + ")");
		check.accept(cp[0] == Gangplank.State.DEPLOYED.ordinal() && cp[1] > 4,
				String.format(Locale.ROOT, "gangplank: the client registered its walkable boxes (%.0f)", cp[1]));
		check.accept(angle >= spec.minAngle() && angle <= spec.maxAngle() && angle > 5,
				String.format(Locale.ROOT, "gangplank: slopes down to the quay (%.1f degrees)", angle));
		double[] tip = p.toWorld(spec.point(angle, spec.length(), 0, 0)[0], spec.point(angle, spec.length(), 0, 0)[1],
				spec.point(angle, spec.length(), 0, 0)[2]);
		check.accept(Math.abs(tip[1] - (QUAY_TOP + 1 + Gangplank.TIP_LIFT)) < 0.05 && tip[0] < QUAY_EAST + 1,
				String.format(Locale.ROOT, "gangplank: its tip rests on the quay (%.2f %.2f)", tip[0], tip[1]));
		lookLocal(server, p, -10, 5, 7.5, spec.hx() - 1.5, spec.hy() - 0.8, spec.hz());
		server.runCommand("gamemode spectator @a");
		context.waitTicks(15);
		shot.accept("passerelle_2_deployee");

		// ---- a survival player walks from the quay up the plank onto the deck (forward key only)
		server.runCommand("gamemode survival @a");
		double[] start = p.toWorld(spec.point(angle, spec.length() + 1.2, 0, 0)[0], 0, spec.hz());
		tpWorld(server, start[0], QUAY_TOP + 1.02, start[2], yawLocal(p, 1, 0), 10);
		context.waitTicks(20);
		double[] q = player(context);
		check.accept(q[3] > 0 && Math.abs(q[1] - (QUAY_TOP + 1)) < 0.05, String.format(Locale.ROOT, "gangplank: standing on the quay (y %.2f)", q[1]));
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(14);
		double[] mid = p.toLocal(player(context)[0], player(context)[1], player(context)[2]);
		log.accept(String.format(Locale.ROOT, "gangplank: walking up, local %.2f %.2f %.2f", mid[0], mid[1], mid[2]));
		// on until the middle of the deck (or 4 s)
		walkUntil(context, pp -> spec.o() * (p.toLocal(pp[0], pp[1], pp[2])[0]) < 0.3, 80);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(10);
		q = player(context);
		double[] l = p.toLocal(q[0], q[1], q[2]);
		double deck = SLOOP.hull().deckY(l[2]);
		log.accept(String.format(Locale.ROOT, "gangplank: after the walk, local %.2f %.2f %.2f (deck %.2f)", l[0], l[1], l[2], deck));
		check.accept(Math.abs(l[1] - deck) < 0.1 && Math.abs(l[0]) < SLOOP.hull().innerHalfWidth(l[2]) && q[3] > 0,
				String.format(Locale.ROOT, "gangplank: walked from the quay up the plank onto the deck, no jump (local %.2f %.2f %.2f)", l[0], l[1], l[2]));

		// ---- and back down to the quay
		tpWorld(server, q[0], q[1], q[2], yawLocal(p, -1, 0), 10);
		context.waitTicks(10);
		context.getInput().holdKey(o -> o.forwardKey);
		final double tipX = tip[0];
		walkUntil(context, pp -> pp[0] < tipX - 1.2, 90);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(10);
		q = player(context);
		log.accept(String.format(Locale.ROOT, "gangplank: after the walk back, %.2f %.2f %.2f", q[0], q[1], q[2]));
		check.accept(Math.abs(q[1] - (QUAY_TOP + 1)) < 0.05 && q[0] < tip[0] && q[3] > 0,
				String.format(Locale.ROOT, "gangplank: walked back down the plank to the quay (%.2f %.2f)", q[0], q[1]));

		// ---- retract refused while a player stands on it
		double[] onPlank = p.toWorld(spec.point(angle, spec.length() * 0.5, 0, 0)[0], spec.point(angle, spec.length() * 0.5, 0, 0)[1] + 0.3, spec.hz());
		tpWorld(server, onPlank[0], onPlank[1], onPlank[2], yawLocal(p, 1, 0), 15);
		context.waitTicks(20);
		q = player(context);
		double[] lq = p.toLocal(q[0], q[1], q[2]);
		check.accept(q[3] > 0 && lq[1] > spec.hy() - spec.length() * Math.sin(Math.toRadians(angle)),
				String.format(Locale.ROOT, "gangplank: a player stands on the sloping plank (local %.2f %.2f)", lq[0], lq[1]));
		String msg = lever(server, SLOOP);
		check.accept(msg.contains("quelqu'un") && serverState(server, SLOOP) == Gangplank.State.DEPLOYED,
				"gangplank: retract refused while someone is on it (" + msg + ")");
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(10);
		shot.accept("passerelle_3_joueur_dessus");
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// ---- the pilot's thrust is ignored while the plank is out
		boolean seated = server.computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity s = ship(srv.getOverworld(), SLOOP);
			return s != null && s.seat(pl, ShipGeometry.PILOT_SEAT);
		});
		check.accept(seated, "gangplank: the player takes the tiller");
		ShipPose before = pose(server, SLOOP);
		context.getInput().holdKey(o -> o.forwardKey);
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(50);
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		ShipPose after = pose(server, SLOOP);
		double moved = Math.hypot(after.x() - before.x(), after.z() - before.z());
		double turned = Math.abs(ShipPose.wrapDegrees(after.yaw() - before.yaw()));
		check.accept(moved < 0.01 && turned < 0.01 && Math.abs(after.y() - before.y()) < 0.01,
				String.format(Locale.ROOT, "gangplank: pilot input ignored while deployed, the sloop stays moored (moved %.3f, turned %.2f)", moved, turned));
		server.runCommand("ride @p dismount");
		context.waitTicks(5);

		// ---- retract accepted once clear
		double[] deckSpot = p.toWorld(0.0, SLOOP.hull().deckY(-1.0) + 0.02, -1.0);
		tpWorld(server, deckSpot[0], deckSpot[1], deckSpot[2], 0, 10);
		context.waitTicks(10);
		msg = lever(server, SLOOP);
		check.accept(serverState(server, SLOOP) == Gangplank.State.RETRACTING, "gangplank: retract accepted when clear (" + msg + ")");
		waitState(context, server, SLOOP, Gangplank.State.RETRACTED, 80);
		context.waitTicks(5);
		cp = clientPlank(context, SLOOP);
		check.accept(serverState(server, SLOOP) == Gangplank.State.RETRACTED && cp[0] == Gangplank.State.RETRACTED.ordinal() && cp[1] == 0,
				String.format(Locale.ROOT, "gangplank: back to RETRACTED, no collision left on the client (%.0f, %.0f)", cp[0], cp[1]));

		// ---- a block in the swing refuses the deploy
		double[] arc = p.toWorld(spec.point(-40, 2.6, 0, 0)[0], spec.point(-40, 2.6, 0, 0)[1], spec.point(-40, 2.6, 0, 0)[2]);
		String block = String.format(Locale.ROOT, "%d %d %d", (int) Math.floor(arc[0]), (int) Math.floor(arc[1]), (int) Math.floor(arc[2]));
		server.runCommand("setblock " + block + " stone");
		msg = lever(server, SLOOP);
		check.accept(msg.equals(Gangplank.SWING_BLOCKED) && serverState(server, SLOOP) == Gangplank.State.RETRACTED,
				"gangplank: deploy refused with a block in the swing (" + msg + ")");
		server.runCommand("setblock " + block + " air");

		// ---- the entity's NBT keeps a coherent state
		msg = lever(server, SLOOP);
		check.accept(serverState(server, SLOOP) == Gangplank.State.DEPLOYING, "gangplank: deploys again (" + msg + ")");
		check.accept("ok".equals(roundTrip(server, "DEPLOYED")), "gangplank NBT: a deploy in progress reloads deployed (" + roundTrip(server, "DEPLOYED") + ")");
		waitState(context, server, SLOOP, Gangplank.State.DEPLOYED, 80);
		check.accept("ok".equals(roundTrip(server, "DEPLOYED")), "gangplank NBT: deployed reloads deployed, same angle");
		lever(server, SLOOP);
		check.accept("ok".equals(roundTrip(server, "RETRACTED")), "gangplank NBT: a retraction in progress reloads stowed");
		waitState(context, server, SLOOP, Gangplank.State.RETRACTED, 80);
		check.accept("ok".equals(roundTrip(server, "RETRACTED")), "gangplank NBT: stowed reloads stowed");

		// ---- after a reload, a plank whose quay is gone retracts
		lever(server, SLOOP);
		waitState(context, server, SLOOP, Gangplank.State.DEPLOYED, 80);
		// the quay under the tip crumbles while nobody uses the lever (no check every tick: only after a load)
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d water", QUAY_EAST - 6, QUAY_TOP - 4, Z0 + 1, QUAY_EAST, QUAY_TOP, Z1 - 1));
		context.waitTicks(5);
		check.accept(serverState(server, SLOOP) == Gangplank.State.DEPLOYED, "gangplank: no environment scan every tick (still deployed)");
		String reload = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, SLOOP);
			if (s == null || s.gangplankState() != Gangplank.State.DEPLOYED) {
				return "not deployed";
			}
			NbtWriteView view = NbtWriteView.create(ErrorReporter.EMPTY, srv.getRegistryManager());
			s.saveSelfData(view);
			s.discard();
			java.util.Optional<Entity> loaded = EntityType.getEntityFromData(
					NbtReadView.create(ErrorReporter.EMPTY, srv.getRegistryManager(), view.getNbt()), w, SpawnReason.LOAD);
			if (loaded.isEmpty()) {
				return "not read back";
			}
			return w.spawnEntity(loaded.get()) ? "ok" : "not spawned";
		});
		check.accept("ok".equals(reload), "gangplank: the deployed sloop saved and loaded again (" + reload + ")");
		context.waitTicks(10);
		Gangplank.State gone = serverState(server, SLOOP);
		check.accept(gone == Gangplank.State.RETRACTING || gone == Gangplank.State.RETRACTED,
				"gangplank: after the reload its quay is gone, it retracts (" + gone + ")");
		waitState(context, server, SLOOP, Gangplank.State.RETRACTED, 80);
		check.accept(serverState(server, SLOOP) == Gangplank.State.RETRACTED, "gangplank: stowed again");
		// with no quay any more: a deploy is refused, never into the water
		msg = lever(server, SLOOP);
		check.accept(serverState(server, SLOOP) == Gangplank.State.RETRACTED && !msg.isEmpty() && !msg.contains("déploie"),
				"gangplank: no quay, deploy refused (" + msg + ")");

		airship(context, server, world, check, log, shot);
		cleanup(context, server);
	}

	private static void airship(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		Gangplank.Spec spec = Gangplank.of(AIRSHIP.id());
		check.accept(spec != null, "steampunk_airship has a gangplank spec");
		if (spec == null) {
			return;
		}
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		tpWorld(server, AX - 16, AY + 4, 0, -90, 10);
		context.waitTicks(10);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", AX - 24, -16, AX + 8, 16));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", AX - 24, AY - 12, -16, AX + 8, AY + 20, 16));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d 0 rotated 0 0 run ship spawn %s", AX, AY, AIRSHIP.id()));
		world.waitForChunksRender();
		context.waitTicks(40);
		ShipPose p = pose(server, AIRSHIP);
		check.accept(p != null, "gangplank: the airship hovers in the sky");
		if (p == null) {
			return;
		}
		// in the air, nothing under the tip: refused, never into the void
		String msg = lever(server, AIRSHIP);
		check.accept(msg.equals(Gangplank.NO_LANDING) && serverState(server, AIRSHIP) == Gangplank.State.RETRACTED,
				"gangplank: airship refused in the air with no platform (" + msg + ")");
		// a boarding platform beside it, a little below the hinge
		p = pose(server, AIRSHIP);
		double[] hinge = p.toWorld(spec.hx(), spec.hy(), spec.hz());
		int top = (int) Math.floor(hinge[1] - 0.8) - 1;
		double[] near = p.toWorld(spec.hx() - 2.4, 0, spec.hz());
		int east = (int) Math.floor(near[0]);
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d spruce_planks", east - 6, top, (int) Math.floor(hinge[2]) - 4, east, top,
				(int) Math.floor(hinge[2]) + 4));
		context.waitTicks(5);
		msg = lever(server, AIRSHIP);
		check.accept(serverState(server, AIRSHIP) == Gangplank.State.DEPLOYING, "gangplank: airship deploys beside a platform (" + msg + ")");
		waitState(context, server, AIRSHIP, Gangplank.State.DEPLOYED, 80);
		context.waitTicks(5);
		double[] cp = clientPlank(context, AIRSHIP);
		check.accept(cp[0] == Gangplank.State.DEPLOYED.ordinal() && cp[1] > 4,
				String.format(Locale.ROOT, "gangplank: airship plank deployed and walkable on the client (%.0f boxes, %.1f degrees)", cp[1], cp[2]));
		ShipPose before = pose(server, AIRSHIP);
		context.waitTicks(40);
		ShipPose after = pose(server, AIRSHIP);
		check.accept(Math.abs(after.y() - before.y()) < 0.01 && Math.hypot(after.x() - before.x(), after.z() - before.z()) < 0.01,
				"gangplank: the airship is held in place while its plank is out");
		lookLocal(server, p, -12, 6, 9, spec.hx() - 2, spec.hy() - 0.5, spec.hz());
		context.waitTicks(15);
		shot.accept("passerelle_4_dirigeable_ponton");
		// a player walks from the platform onto the airship
		server.runCommand("gamemode survival @a");
		double angle = cp[2];
		double[] start = p.toWorld(spec.point(angle, spec.length() + 1.0, 0, 0)[0], 0, spec.hz());
		tpWorld(server, start[0], top + 1.02, start[2], yawLocal(p, 1, 0), 10);
		context.waitTicks(15);
		context.getInput().holdKey(o -> o.forwardKey);
		final ShipPose ap = p;
		walkUntil(context, pp -> spec.o() * (ap.toLocal(pp[0], pp[1], pp[2])[0]) < 0.4, 90);
		context.getInput().releaseKey(o -> o.forwardKey);
		context.waitTicks(10);
		double[] q = player(context);
		double[] l = p.toLocal(q[0], q[1], q[2]);
		log.accept(String.format(Locale.ROOT, "gangplank: airship walk ends at local %.2f %.2f %.2f", l[0], l[1], l[2]));
		check.accept(Math.abs(l[1] - AIRSHIP.hull().deckY(l[2])) < 0.1 && Math.abs(l[0]) < AIRSHIP.hull().innerHalfWidth(l[2]) && q[3] > 0,
				String.format(Locale.ROOT, "gangplank: walked from the platform onto the airship's deck (local %.2f %.2f %.2f)", l[0], l[1], l[2]));
		server.runCommand("gamemode spectator @a");
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), AIRSHIP);
			if (s != null) {
				s.removeAllPassengers();
				s.discard();
			}
			return null;
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", AX - 24, -16, AX + 8, 16));
	}

	/** Keeps walking (the forward key is held) until the client player's position satisfies {@code done}, at most maxTicks. */
	private static void walkUntil(ClientGameTestContext context, java.util.function.Predicate<double[]> done, int maxTicks) {
		for (int t = 0; t < maxTicks; t += 2) {
			if (done.test(player(context))) {
				return;
			}
			context.waitTicks(2);
		}
	}

	private static void cleanup(ClientGameTestContext context, TestServerContext server) {
		context.getInput().releaseKey(o -> o.forwardKey);
		server.runCommand("ride @p dismount");
		server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), SLOOP);
			if (s != null) {
				s.removeAllPassengers();
				s.discard();
			}
			return null;
		});
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
		server.runCommand("gamemode survival @a");
		context.runOnClient((MinecraftClient c) -> {
			c.options.hudHidden = false;
			c.options.setPerspective(Perspective.FIRST_PERSON);
		});
		context.waitTicks(10);
	}
}
