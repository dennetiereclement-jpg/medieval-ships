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
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.RowboatLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the Rowboat (about 25 s of game time): placed on a small basin like a vanilla boat, floats, the
 * reference's view and two more screenshots, a swimming player clicks it and finds himself seated at the oars (dry, not
 * standing), rows forward with the oars animated, turns short, a passenger takes the second thwart and a third one is
 * refused, leaving the boat lands beside it, the item. Called once from {@link ShipClientGameTest}.
 */
public final class RowboatGameTest {
	private static final ShipType TYPE = Ships.ROWBOAT;
	private static final int X = 760;
	/** The basin's surface (filled from -63 to -59; the top source block is 8/9 high, so the ship floats at -58.11). */
	private static final double WATER = -58.0;

	private RowboatGameTest() {
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

	private static void lookLocal(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}

	/** The player's state: seated in the rowboat, at which seat, standing at the helm, touching water, y. */
	private static Object[] rider(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			ShipEntity s = ship(srv.getOverworld());
			boolean aboard = s != null && pl.getVehicle() == s;
			return new Object[] {aboard, aboard ? s.seatOf(pl) : -1, aboard && s.standsAtHelm(pl), pl.isTouchingWater(), pl.getY()};
		});
	}

	/** The client copy of the rowboat's oars: phase and weight of the rowing animation. */
	private static float[] oars(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> {
			for (ShipEntity s : ShipTracker.ships(c.world)) {
				if (!s.isRemoved() && s.shipType() == TYPE) {
					return new float[] {s.oarPhase, s.oarWeight};
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
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=rbcrew]");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -40 0 0 40", X));
		context.waitTicks(30);
		// a small basin of its own, 5 deep
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -16 %d -59 16 water", X - 15, X + 15));
		context.waitTicks(10);
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %.0f 0 rotated 0 0 run ship spawn %s", X, WATER, id));
		world.waitForChunksRender();
		context.waitTicks(30);
		ShipPose p0 = pose(server);
		if (p0 == null) {
			check.accept(false, id + ": not spawned");
			return;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		log.accept(String.format(Locale.ROOT, "%s at %.2f %.2f %.2f yaw %.1f", id, p0.x(), p0.y(), p0.z(), p0.yaw()));
		check.accept(Math.abs(p0.y() + g.hull().waterlineY - WATER) < 0.3, String.format(Locale.ROOT, "%s floats: water line at y=%.2f (basin surface %.0f)", id,
				p0.y() + g.hull().waterlineY, WATER));
		check.accept(collisions(server) == 0, id + " placed: inside nothing");

		// the reference's viewpoint (forward-port, above, looking aft), then the side and the top
		String[] names = {"1_reference", "2_cote", "3_dessus"};
		double[][] eyes = {{3.9, 2.7, 4.15, -0.15, 0.3, -0.45}, {9.0, 1.6, 0.0, 0.0, 0.4, 0.0}, {0.01, 11.0, 0.0, 0.0, 0.0, 0.0}};
		for (int k = 0; k < names.length; k++) {
			double[] e = eyes[k];
			lookLocal(server, p0, e[0], e[1], e[2], e[3], e[4], e[5]);
			context.waitTicks(k == 0 ? 25 : 12);
			shot.accept(id + "_" + names[k]);
		}

		// a survival player swimming beside the boat clicks it: he sits down at the oars, dry, seated (not standing)
		server.runCommand("gamemode survival @a");
		server.runCommand("clear @a");
		lookLocal(server, p0, 2.1, 1.1, 0.3, 0.0, 0.55, 0.2);
		context.waitTicks(15);
		Object[] r0 = rider(server);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(20);
		Object[] r1 = rider(server);
		check.accept(Boolean.TRUE.equals(r0[3]) && !Boolean.TRUE.equals(r0[0]), String.format(Locale.ROOT, "%s the player starts in the water beside it (touching water %s)", id, r0[3]));
		check.accept(Boolean.TRUE.equals(r1[0]) && (Integer) r1[1] == ShipGeometry.PILOT_SEAT, String.format(Locale.ROOT,
				"%s a click on the hull seats him at the oars (aboard %s, seat %s)", id, r1[0], r1[1]));
		check.accept(!Boolean.TRUE.equals(r1[2]), id + " the rower sits on his thwart (not standing at a helm)");
		double waterY = p0.y() + g.hull().waterlineY;
		check.accept(!Boolean.TRUE.equals(r1[3]) && (Double) r1[4] > waterY - 0.05, String.format(Locale.ROOT,
				"%s seated he is out of the water (touching %s, y %.2f, surface %.2f)", id, r1[3], r1[4], waterY));

		// rowing: forward, the oars animated at the pace of the boat; then a short turn
		float[] a0 = oars(context);
		ShipPose s0 = pose(server);
		context.getInput().holdKey(o -> o.forwardKey);
		context.waitTicks(60);
		ShipPose s1 = pose(server);
		float[] a1 = oars(context);
		double dist = Math.hypot(s1.x() - s0.x(), s1.z() - s0.z());
		check.accept(dist > 2.5, String.format(Locale.ROOT, "%s rows forward under command (%.2f blocks in 3 s)", id, dist));
		check.accept(a0 != null && a1 != null && a1[1] > 0.5 && a1[0] - a0[0] > 0.8, String.format(Locale.ROOT,
				"%s under way the oars row (weight %.2f, phase %.2f -> %.2f)", id, a1 == null ? 0f : a1[1], a0 == null ? 0f : a0[0], a1 == null ? 0f : a1[0]));
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(8);
		shot.accept(id + "_4_a_la_rame");
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.FIRST_PERSON));
		context.getInput().holdKey(o -> o.leftKey);
		context.waitTicks(40);
		ShipPose s2 = pose(server);
		context.getInput().releaseKey(o -> o.leftKey);
		context.getInput().releaseKey(o -> o.forwardKey);
		double turned = Math.abs(ShipPose.wrapDegrees(s2.yaw() - s1.yaw()));
		check.accept(turned > 25, String.format(Locale.ROOT, "%s turns short (%.1f degrees in 2 s)", id, turned));
		Object[] r2 = rider(server);
		check.accept(Boolean.TRUE.equals(r2[0]) && !Boolean.TRUE.equals(r2[3]), id + " still seated and dry after rowing");
		check.accept(collisions(server) == 0, id + " rowing: inside nothing");
		context.waitTicks(40);
		ShipPose s3 = pose(server);
		context.waitTicks(20);
		ShipPose s4 = pose(server);
		double drift = Math.hypot(s4.x() - s3.x(), s4.z() - s3.z());
		check.accept(drift < 1.5, String.format(Locale.ROOT, "%s little inertia: %.2f blocks in 1 s, 2 s after the oars stopped", id, drift));

		// a passenger on the aft thwart, a third one refused (two seats)
		ShipPose now = pose(server);
		double[] w1 = now.toWorld(0, 1.5, RowboatLayout.PASSENGER_Z), w2 = now.toWorld(0, 1.5, RowboatLayout.THWART_Z[0]);
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"rbcrew\",\"rb1\"]}", w1[0], w1[1], w1[2]));
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"rbcrew\",\"rb2\"]}", w2[0], w2[1], w2[2]));
		context.waitTicks(10);
		int[] seated = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld());
			int first = 0, second = 0;
			for (Entity e : srv.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("rb1") && s.seat(e, 1)) {
					first++;
				}
			}
			for (Entity e : srv.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("rb2") && s.seat(e, ShipGeometry.PILOT_SEAT)) {
					second++;
				}
			}
			return new int[] {first, second, s.getPassengerList().size()};
		});
		check.accept(seated[0] == 1 && seated[1] == 0 && seated[2] == 2, String.format(Locale.ROOT,
				"%s a passenger takes the aft thwart, a third one is refused (%d, %d, %d aboard)", id, seated[0], seated[1], seated[2]));
		// the player is still seated (a teleport would dismount him): the shot from the third person, facing him
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.THIRD_PERSON_FRONT));
		context.waitTicks(8);
		shot.accept(id + "_5_deux_a_bord");
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// leaving the boat: beside it, in the water (no ground within reach here)
		server.runCommand("ride @p dismount");
		context.waitTicks(10);
		Object[] r3 = rider(server);
		double[] pl = context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ()});
		double[] loc = pose(server).toLocal(pl[0], pl[1], pl[2]);
		check.accept(!Boolean.TRUE.equals(r3[0]) && (Math.abs(loc[0]) > g.hull().halfWidth(Math.min(2.4, Math.abs(loc[2]))) + 0.3 || Math.abs(loc[2]) > g.hull().tip),
				String.format(Locale.ROOT, "%s leaving it lands outside the hull (local %.2f %.2f %.2f)", id, loc[0], loc[1], loc[2]));

		// the item
		server.runCommand("clear @a");
		server.runCommand("ship give " + id + " @p");
		Integer items = server.computeOnServer(srv -> srv.getPlayerManager().getPlayerList().get(0).getInventory().count(MedievalShips.item(TYPE)));
		check.accept(items != null && items == 1, String.format(Locale.ROOT, "%s item: /ship give gives it (%s)", id, items));
		server.runCommand("clear @a");
		server.runCommand("kill @e[type=minecraft:armor_stand,tag=rbcrew]");
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
