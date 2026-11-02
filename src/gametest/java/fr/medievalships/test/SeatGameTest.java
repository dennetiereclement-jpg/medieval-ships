package fr.medievalships.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.NbtWriteView;
import net.minecraft.util.ErrorReporter;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.shape.VoxelShape;

import fr.medievalships.client.SeatPicker;
import fr.medievalships.core.Seating;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.network.SitPayload;
import fr.medievalships.tent.SeatEntity;
import fr.medievalships.tent.Seats;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;

/**
 * In-game checks of the seats (1.19.0), on the nomad tavern placed on a stone platform of its own, the player in
 * survival: seat 0 through the server's handler of the sit request (the {@link SitPayload} a right click sends): riding a
 * {@link SeatEntity}, feet 0.6 below the seat's surface (thighs on it), body and look facing the seat's yaw, the seat
 * entity never saved; an armor stand refused on the same seat, accepted on another one (two riders at once); standing
 * up with the sneak key (vanilla): the seat entity is gone, the player stands clear of every collision box; the real
 * client path for seat 1 (look at it, {@link SeatPicker} picks it, the use key sends the request); the tavern removed
 * while seated: the player is stood up, no seat entity is left. Screenshot of the player sitting. Called once from
 * {@link ShipClientGameTest} (solo and dedicated server).
 */
public final class SeatGameTest {
	/** Dry ground of the flat world, east of the other props' platforms (tents 1300, workshops 1600). */
	private static final int X = 2300;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;
	private static final TentType TYPE = TentTypes.TAVERN;

	private SeatGameTest() {
	}

	private static BlockPos anchor() {
		return new BlockPos(X, GROUND + 1, 0);
	}

	private static ServerPlayerEntity player(MinecraftServer srv) {
		return srv.getPlayerManager().getPlayerList().get(0);
	}

	/** World point of a seat's surface (the tavern faces south). */
	private static double[] seat(int i) {
		BlockPos a = anchor();
		return Seating.world(a.getX(), a.getY(), a.getZ(), TYPE.seats(TentType.SOUTH).get(i));
	}

	private static float seatYaw(int i) {
		return TYPE.seats(TentType.SOUTH).get(i).yaw();
	}

	/** Puts the player's eyes at (ex, ey, ez) looking at (tx, ty, tz). */
	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	/** Where a player would stand up from seat i (the same search as getting up), or null. */
	private static double[] standingSpot(TestServerContext server, int i) {
		double[] s = seat(i);
		return server.computeOnServer(srv -> {
			Vec3d v = Seats.standingSpot(srv.getOverworld(), player(srv), s[0], s[1], s[2], seatYaw(i), anchor().getY());
			return v == null ? null : new double[] {v.x, v.y, v.z};
		});
	}

	/** Puts the player at seat i's standing spot (else 1.5 in front of it), looking at the seat. */
	private static void goTo(TestServerContext server, int i) {
		double[] s = seat(i);
		double[] spot = standingSpot(server, i);
		if (spot == null) {
			double[] f = Seating.facing(seatYaw(i));
			spot = new double[] {s[0] + f[0] * 1.5, anchor().getY(), s[2] + f[1] * 1.5};
		}
		look(server, spot[0], spot[1] + 1.62, spot[2], s[0], s[1] - 0.1, s[2]);
	}

	private static int seatEntities(TestServerContext server) {
		return server.computeOnServer(srv -> srv.getOverworld().getEntitiesByClass(SeatEntity.class, new Box(anchor()).expand(24), e -> true)
				.size());
	}

	/** {riding seat index or -1, feet y, yaw, is the seat entity saved somewhere} on the server. */
	private static double[] serverState(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity p = player(srv);
			if (p.getVehicle() instanceof SeatEntity seat) {
				boolean saved = seat.shouldSave() || seat.saveData(NbtWriteView.create(ErrorReporter.EMPTY));
				return new double[] {seat.seatIndex(), p.getY(), seat.seatYaw(), saved ? 1 : 0};
			}
			return new double[] {-1, p.getY(), 0, 0};
		});
	}

	/** {riding?, feet y, yaw, body yaw} on the client. */
	private static double[] clientState(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> new double[] {c.player.hasVehicle() ? 1 : 0, c.player.getY(), c.player.getYaw(),
				c.player.getBodyYaw()});
	}

	/** Is the standing player clear of every block and every collision box of the props? */
	private static boolean clear(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity p = player(srv);
			Box box = p.getBoundingBox().contract(1e-3);
			List<VoxelShape> shapes = new ArrayList<>();
			return srv.getOverworld().isSpaceEmpty(p, box) && !TentCollisions.append(shapes, p, box, srv.getOverworld());
		});
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -15 %d %d 15 stone", X - 15, X + 15, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -15 %d %d 15 air", X - 15, GROUND + 1, X + 15, GROUND + 12));
		context.waitTicks(10);
		BlockPos a = anchor();
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", TYPE.id(), a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(15);
		boolean placed = server.computeOnServer(srv -> srv.getOverworld().getBlockState(a).getBlock() instanceof TentBlock b
				&& b.tentType() == TYPE);
		check.accept(placed, "seats: the nomad tavern placed by /tent place at " + a.toShortString());
		int n = TYPE.seats().size();
		check.accept(n >= 2, "seats: the tavern has " + n + " seats");
		if (!placed || n < 2) {
			return;
		}
		server.runCommand("gamemode survival @a");
		context.waitTicks(5);

		// 1. seat 0 through the server's handler of the sit request
		goTo(server, 0);
		context.waitTicks(10);
		server.runOnServer(srv -> Seats.handle(new SitPayload(a, 0), player(srv)));
		context.waitTicks(10);
		double[] s0 = seat(0);
		double[] st = serverState(server);
		double[] cl = clientState(context);
		log.accept(String.format(Locale.ROOT, "seats: seat 0 surface at y=%.3f yaw %.1f; server: seat %d feet y=%.3f; client: riding %s feet y=%.3f"
				+ " yaw %.1f body %.1f", s0[1], seatYaw(0), (int) st[0], st[1], cl[0] > 0, cl[1], cl[2], cl[3]));
		check.accept(st[0] == 0, "seats: the player rides seat 0 (server) after the sit request");
		check.accept(cl[0] > 0, "seats: the player rides on his client too");
		check.accept(Math.abs(st[1] - (s0[1] - Seating.PLAYER_RIDING_DROP)) < 0.02,
				String.format(Locale.ROOT, "seats: feet 0.6 below the seat's surface, thighs on it (server feet %.3f, surface %.3f)", st[1], s0[1]));
		check.accept(Math.abs(cl[1] - (s0[1] - Seating.PLAYER_RIDING_DROP)) < 0.05,
				String.format(Locale.ROOT, "seats: same height on the client (feet %.3f)", cl[1]));
		check.accept(Math.abs(Seating.yawDifference(cl[3], seatYaw(0))) < 3,
				String.format(Locale.ROOT, "seats: body facing the seat's yaw %.1f (body %.1f)", seatYaw(0), cl[3]));
		check.accept(Math.abs(Seating.yawDifference(cl[2], seatYaw(0))) < 3,
				String.format(Locale.ROOT, "seats: looking the seat's way (yaw %.1f)", cl[2]));
		check.accept(st[3] == 0, "seats: the seat entity is never saved (chunk, player file)");
		check.accept(seatEntities(server) == 1, "seats: one seat entity");
		context.runOnClient((MinecraftClient c) -> {
			c.options.hudHidden = true;
			c.options.setPerspective(Perspective.THIRD_PERSON_FRONT);
		});
		context.waitTicks(15);
		shot.accept("seat_1_player_sitting");
		context.runOnClient((MinecraftClient c) -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot.accept("seat_2_player_sitting_back");
		context.runOnClient((MinecraftClient c) -> {
			c.options.setPerspective(Perspective.FIRST_PERSON);
			c.options.hudHidden = false;
		});

		// 2. one rider per seat: an armor stand is refused on seat 0, then sits on seat 1 (two riders at once)
		double[] spot0 = standingSpot(server, 0);
		double[] at0 = spot0 != null ? spot0 : new double[] {s0[0], s0[1] + 0.1, s0[2]};
		double[] spot1 = standingSpot(server, 1);
		double[] s1 = seat(1);
		double[] at1 = spot1 != null ? spot1 : new double[] {s1[0], s1[1] + 0.1, s1[2]};
		server.runCommand(String.format(Locale.ROOT, "summon minecraft:armor_stand %.3f %.3f %.3f {Tags:[\"seatstand\"]}", at0[0], at0[1], at0[2]));
		context.waitTicks(5);
		String stand = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			List<ArmorStandEntity> l = w.getEntitiesByClass(ArmorStandEntity.class, new Box(a).expand(24),
					e -> e.getCommandTags().contains("seatstand"));
			if (l.isEmpty()) {
				return "none";
			}
			ArmorStandEntity e = l.get(0);
			SeatEntity seat0 = Seats.find(w, a, 0);
			Seats.Result onTaken = Seats.sit(e, a, 0);
			boolean vanilla = seat0 != null && e.startRiding(seat0);
			boolean ridingAfterRefusal = e.hasVehicle();
			e.refreshPositionAndAngles(at1[0], at1[1], at1[2], 0f, 0f); // within reach of seat 1
			Seats.Result onFree = Seats.sit(e, a, 1);
			boolean both = e.getVehicle() instanceof SeatEntity se && se.seatIndex() == 1 && player(srv).getVehicle() instanceof SeatEntity sp
					&& sp.seatIndex() == 0;
			return onTaken + " " + vanilla + " " + ridingAfterRefusal + " " + onFree + " " + both;
		});
		log.accept("seats: armor stand on seat 0 then seat 1: " + stand);
		String[] r = stand.split(" ");
		check.accept(r.length == 5 && r[0].equals("OCCUPIED"), "seats: an armor stand is refused on the occupied seat 0 (" + stand + ")");
		check.accept(r.length == 5 && r[1].equals("false") && r[2].equals("false"), "seats: vanilla riding refused too: one rider per seat");
		check.accept(r.length == 5 && r[3].equals("SEATED") && r[4].equals("true"), "seats: the armor stand sits on seat 1 while the player sits on 0");
		check.accept(seatEntities(server) == 2, "seats: two seat entities for two riders");
		server.runOnServer(srv -> {
			for (ArmorStandEntity e : srv.getOverworld().getEntitiesByClass(ArmorStandEntity.class, new Box(a).expand(24),
					x -> x.getCommandTags().contains("seatstand"))) {
				e.stopRiding();
				e.discard();
			}
		});
		context.waitTicks(5);
		check.accept(seatEntities(server) == 1, "seats: the armor stand gone, its seat entity removed with it");

		// 3. standing up with the sneak key (vanilla dismount)
		context.getInput().holdKeyFor(o -> o.sneakKey, 4);
		context.waitTicks(10);
		st = serverState(server);
		cl = clientState(context);
		double[] p = server.computeOnServer(srv -> new double[] {player(srv).getX(), player(srv).getY(), player(srv).getZ()});
		log.accept(String.format(Locale.ROOT, "seats: stood up at %.2f %.2f %.2f (seat 0 at %.2f %.2f %.2f)", p[0], p[1], p[2], s0[0], s0[1], s0[2]));
		check.accept(st[0] < 0 && cl[0] == 0, "seats: sneaking stands the player up (server and client)");
		check.accept(seatEntities(server) == 0, "seats: no seat entity left once nobody sits");
		check.accept(clear(server), "seats: standing clear of the blocks and the tavern's collision boxes");
		check.accept(Math.hypot(p[0] - s0[0], p[2] - s0[2]) < 2.0, "seats: standing beside seat 0");

		// 4. the real client path: look at seat 1, the picker picks it, the use key sends the request
		goTo(server, 1);
		context.waitTicks(15);
		SeatPicker.Target target = context.computeOnClient((MinecraftClient c) -> SeatPicker.current());
		check.accept(target != null && target.seat() == 1 && target.anchor().equals(a),
				"seats: the crosshair picks seat 1 (" + (target == null ? "nothing" : target.seat() + " of " + target.anchor().toShortString()) + ")");
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(10);
		st = serverState(server);
		check.accept(st[0] == 1, "seats: a right click on seat 1 seats the player there (riding " + (int) st[0] + ")");
		if (st[0] != 1) {
			server.runOnServer(srv -> Seats.handle(new SitPayload(a, 1), player(srv)));
			context.waitTicks(5);
		}

		// 5. the tavern removed while the player sits: he stands up, no seat entity is left
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(10);
		st = serverState(server);
		cl = clientState(context);
		boolean gone = server.computeOnServer(srv -> !(srv.getOverworld().getBlockState(a).getBlock() instanceof TentBlock));
		check.accept(gone, "seats: the tavern removed by /tent remove");
		check.accept(st[0] < 0 && cl[0] == 0, "seats: the seated player is stood up when the tavern goes");
		check.accept(seatEntities(server) == 0, "seats: no seat entity left after the tavern's removal");
		server.runCommand("gamemode spectator @a");
	}
}
