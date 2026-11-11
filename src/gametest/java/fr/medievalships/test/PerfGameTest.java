package fr.medievalships.test;

import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.Difficulty;

import fr.medievalships.client.render.RenderStats;
import fr.medievalships.client.render.ShipModels;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipCollisions;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipInteriors;
import fr.medievalships.entity.ShipTracker;

/**
 * The performance benchmark (1.29.0): numbers only, no threshold (the CI renders with llvmpipe, where every frame is
 * slow: what is compared is this run's "with" against its own "without"). On ground of its own (x 6000): a city of
 * {@link #PROPS 40 props} (camp, merchant and market tents, carts, workshops, the tavern, decorations, three stakes) on a
 * stone square, a harbour to the east with the six big ships (royal lion, fortress, gear steamship, galleon, warship,
 * blue frigate) moored side by side and the Nautilus, and twenty mobs (villagers and zombies with AI, walking about
 * the square and a deck: their every movement goes through the collision hook). Then, from three cameras (the
 * market, the quay, a deck), the frame time with the mod's renderers and with them switched off
 * ({@link RenderStats#skip}), the time the mod spends emitting vertices, the quads and furniture blocks it submits,
 * the memory the render thread allocates per frame; and on the server, over 100 ticks, the tick time at rest and
 * with the royal lion ship under way on a route, the collision hook's calls, hull queries, boxes and time per tick,
 * the dry-room queries, the memory the server thread allocates per tick, and the garbage collections of the whole run.
 * Everything is PASS lines with the numbers (docs/PERFORMANCE.md keeps them per version). Called once from
 * {@link ShipClientGameTest}, in solo and on the dedicated server; about 70 s of game time.
 */
public final class PerfGameTest {
	private static final int X = 6000, Z = 0;
	/** Top of the stone square; the anchors of the props sit on it. */
	private static final int GROUND = -60;
	/**
	 * The water of the harbour: a stone-walled basin raised above the flat world's ground (bedrock is at -64: the only
	 * way to the 14 blocks of depth the Nautilus needs), its surface, where the ships are put, the top of y -50.
	 */
	private static final int HARBOUR_X0 = X + 70, HARBOUR_X1 = X + 270, HARBOUR_Z0 = Z - 90, HARBOUR_Z1 = Z + 90;
	private static final int WATER_TOP = -50;
	private static final String[] PROPS = {
			"tent_command", "tent_adventurer", "tent_market", "tent_camp", "tent_dwelling", "tent_chief",
			"tente_armurier", "tente_alchimiste", "tente_herboriste", "tente_forgeron", "tente_nourriture", "tente_tissus",
			"tente_lion_pavillon", "tente_lion_longue", "tente_imperiale", "tente_lion_drapee", "tente_lion_chapiteau",
			"tente_balance_bleue", "tente_draperie", "tente_fleur_de_lys",
			"cart_covered_white", "cart_hay", "cart_merchant_wagon", "cart_market", "cart_logs", "cart_barrels",
			"workshop_blacksmith", "workshop_tailor", "workshop_cook", "workshop_alchemist",
			"taverne_nomade",
			"deco_guirlande", "deco_etendoir", "deco_lanterne", "deco_banniere", "deco_filet", "deco_sechoir",
			"pieu_defensif", "pieu_defensif", "pieu_defensif"};
	/** The vessels of the harbour, moored side by side (bow to the south), and the x of each. */
	private static final ShipType[] SHIPS = {Ships.ROYAL_LION_SHIP, Ships.FORTRESS_SHIP, Ships.GEAR_STEAMSHIP, Ships.GALLEON,
			Ships.WARSHIP, Ships.BLUE_FRIGATE, Ships.NAUTILUS};
	private static final int[] SHIP_X = {X + 90, X + 115, X + 140, X + 165, X + 190, X + 215, X + 248};
	/** Frames measured per camera (or the wall-clock limit, whichever comes first) and ticks per server measure. */
	private static final int FRAMES = 200;
	private static final long FRAME_MILLIS = 6000;
	private static final int TICKS = 100;
	private static final String ROUTE = "perf_lion";

	private PerfGameTest() {
	}

	/** A /fill, split into pieces of at most 32768 blocks (the command's limit). */
	private static void fill(TestServerContext server, int x0, int y0, int z0, int x1, int y1, int z1, String block) {
		int dx = x1 - x0 + 1, dy = y1 - y0 + 1;
		int step = Math.max(1, 32000 / (dx * dy));
		for (int z = z0; z <= z1; z += step) {
			int zEnd = Math.min(z1, z + step - 1);
			server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d %s", x0, y0, z, x1, y1, zEnd, block));
		}
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	/** Spawns a mob with its AI (zombies get a helmet: no burning in the sun) at a world position. */
	private static void spawn(TestServerContext server, EntityType<? extends MobEntity> type, double x, double y, double z, float yaw) {
		server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			MobEntity m = type.create(w, SpawnReason.COMMAND);
			if (m == null) {
				return null;
			}
			m.setPersistent();
			m.setSilent(true);
			if ((Object) type == EntityType.ZOMBIE) {
				m.equipStack(EquipmentSlot.HEAD, new ItemStack(Items.IRON_HELMET));
			}
			m.addCommandTag("perfmob");
			m.refreshPositionAndAngles(x, y, z, yaw, 0f);
			w.spawnEntity(m);
			return null;
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

	private static long gcCount() {
		long n = 0;
		for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
			n += Math.max(0, gc.getCollectionCount());
		}
		return n;
	}

	/** Bytes allocated so far by a thread (HotSpot), or -1 when the JVM cannot tell. */
	private static long allocated(long threadId) {
		try {
			var bean = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
			if (!bean.isThreadAllocatedMemorySupported()) {
				return -1;
			}
			if (!bean.isThreadAllocatedMemoryEnabled()) {
				bean.setThreadAllocatedMemoryEnabled(true);
			}
			return bean.getThreadAllocatedBytes(threadId);
		} catch (Throwable t) {
			return -1;
		}
	}

	/** Measures frames from the current camera: {frames, frameNanos, emitNanos, quads, decorBlocks, cells, cellsCulled, baked, allocBytes}. */
	private static long[] frames(ClientGameTestContext context, boolean withMod) {
		long thread = context.computeOnClient(c -> Thread.currentThread().threadId());
		context.runOnClient(c -> {
			RenderStats.skip = !withMod;
			RenderStats.reset();
		});
		context.waitTicks(5); // the toggle settles (the first frames after it are not counted)
		context.runOnClient(c -> RenderStats.reset());
		long a0 = allocated(thread);
		long start = System.currentTimeMillis();
		long[] s;
		do {
			context.waitTick();
			s = context.computeOnClient(c -> RenderStats.snapshot());
		} while (s[0] < FRAMES && System.currentTimeMillis() - start < FRAME_MILLIS);
		long a1 = allocated(thread);
		context.runOnClient(c -> RenderStats.skip = false);
		long[] out = new long[s.length + 1];
		System.arraycopy(s, 0, out, 0, s.length);
		out[s.length] = a0 < 0 || a1 < 0 ? -1 : a1 - a0;
		return out;
	}

	private static double ms(long nanos, long count) {
		return count == 0 ? 0 : nanos / 1e6 / count;
	}

	/** One camera: frames with and without the mod's renderers, one PASS line with the numbers. */
	private static void camera(ClientGameTestContext context, String name, BiConsumer<Boolean, String> check, Consumer<String> log) {
		long[] with = frames(context, true);
		long[] without = frames(context, false);
		double fWith = ms(with[1], with[0]), fWithout = ms(without[1], without[0]);
		double alloc = with[8] < 0 || with[0] == 0 ? -1 : with[8] / 1048576.0 / with[0];
		check.accept(true, String.format(Locale.ROOT,
				"perf client [%s]: %d + %d frames, frame %.1f ms with the mod's renderers vs %.1f ms without (%.1f ms attributable), "
						+ "mod vertex emission %.2f ms/frame, %d quads + %d furniture blocks per frame, %d mesh cells (%d culled), %.2f MB/frame allocated on the render thread",
				name, with[0], without[0], fWith, fWithout, fWith - fWithout, ms(with[2], with[0]), with[0] == 0 ? 0 : with[3] / with[0],
				with[0] == 0 ? 0 : with[4] / with[0], with[0] == 0 ? 0 : with[5] / with[0], with[0] == 0 ? 0 : with[6] / with[0], alloc));
		log.accept(String.format(Locale.ROOT, "perf client [%s]: without the mod %d quads/frame, %.2f MB/frame allocated", name,
				without[0] == 0 ? 0 : without[3] / without[0], without[8] < 0 || without[0] == 0 ? -1 : without[8] / 1048576.0 / without[0]));
	}

	/** Mean of the server's last {@link #TICKS} tick times (ms), the collision and dry-room counters of a measure. */
	private static double[] serverMeasure(ClientGameTestContext context, TestServerContext server) {
		long thread = server.computeOnServer(srv -> Thread.currentThread().threadId());
		long[] c0 = server.computeOnServer(srv -> ShipCollisions.stats(false));
		long d0 = server.computeOnServer(srv -> ShipInteriors.DRY_CALLS[0]);
		long a0 = allocated(thread);
		context.waitTicks(TICKS);
		long a1 = allocated(thread);
		long[] c1 = server.computeOnServer(srv -> ShipCollisions.stats(false));
		long d1 = server.computeOnServer(srv -> ShipInteriors.DRY_CALLS[0]);
		double mspt = server.computeOnServer(srv -> {
			long[] times = srv.getTickTimes();
			double sum = 0;
			int n = Math.min(TICKS, times.length);
			for (int i = 0; i < n; i++) {
				sum += times[i];
			}
			return sum / n / 1e6;
		});
		return new double[] {mspt, (c1[0] - c0[0]) / (double) TICKS, (c1[1] - c0[1]) / (double) TICKS, (c1[2] - c0[2]) / (double) TICKS,
				(c1[3] - c0[3]) / 1e6 / TICKS, (d1 - d0) / (double) TICKS, a0 < 0 || a1 < 0 ? -1 : (a1 - a0) / 1024.0 / TICKS};
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		long gc0 = gcCount();
		long wall0 = System.currentTimeMillis();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d %d 0 40", X, GROUND + 12, Z - 60));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 70, Z - 50, X + 70, Z + 50));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", HARBOUR_X0 - 6, HARBOUR_Z0 - 6, HARBOUR_X1 + 6, HARBOUR_Z1 + 6));
		context.waitTicks(40);
		boolean peaceful = server.computeOnServer(srv -> srv.getOverworld().getDifficulty() == Difficulty.PEACEFUL);
		if (peaceful) {
			server.runCommand("difficulty easy"); // the zombies vanish in peaceful
		}
		// the square and the harbour
		server.runCommand(String.format(Locale.ROOT, "kill @e[type=!player,x=%d,y=%d,z=%d,dx=%d,dy=40,dz=%d]", X - 70, GROUND - 5, Z - 95,
				HARBOUR_X1 + 10 - (X - 70), HARBOUR_Z1 + 10 - (Z - 95)));
		fill(server, X - 64, GROUND - 2, Z - 40, X + 64, GROUND, Z + 40, "stone");
		fill(server, X - 64, GROUND + 1, Z - 40, X + 64, GROUND + 14, Z + 40, "air");
		fill(server, HARBOUR_X0 - 1, -63, HARBOUR_Z0 - 1, HARBOUR_X1 + 1, -30, HARBOUR_Z1 + 1, "air");
		fill(server, HARBOUR_X0 - 1, -63, HARBOUR_Z0 - 1, HARBOUR_X1 + 1, WATER_TOP, HARBOUR_Z1 + 1, "stone");
		fill(server, HARBOUR_X0, -63, HARBOUR_Z0, HARBOUR_X1, WATER_TOP, HARBOUR_Z1, "water");
		world.waitForChunksRender();
		context.waitTicks(20);
		// the props: 8 columns 16 apart, 5 rows 14 apart, every one facing south
		int before = server.computeOnServer(srv -> fr.medievalships.tent.TentCollisions.count(srv.getOverworld()));
		int placed = 0;
		for (int i = 0; i < PROPS.length; i++) {
			int col = i % 8, row = i / 8;
			int x = X - 56 + col * 16, z = Z - 28 + row * 14;
			server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", PROPS[i], x, GROUND + 1, z));
			placed++;
		}
		context.waitTicks(10);
		int props = server.computeOnServer(srv -> fr.medievalships.tent.TentCollisions.count(srv.getOverworld())) - before;
		// the vessels, bow to the south, side by side
		for (int i = 0; i < SHIPS.length; i++) {
			server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d %d rotated 0 0 run ship spawn %s", SHIP_X[i], WATER_TOP + 1, Z,
					SHIPS[i].id()));
		}
		context.waitTicks(40);
		int vessels = server.computeOnServer(srv -> {
			int n = 0;
			for (ShipType t : SHIPS) {
				if (ship(srv.getOverworld(), t) != null) {
					n++;
				}
			}
			return n;
		});
		// the mobs: ten villagers and ten zombies in the streets of the square, four more villagers on the lion's deck
		int mobs = 0;
		for (int i = 0; i < 20; i++) {
			int col = i % 8, row = i / 8;
			double x = X - 56 + col * 16 + 8, z = Z - 28 + row * 14 + 7;
			EntityType<? extends MobEntity> kind = i % 2 == 0 ? EntityType.VILLAGER : EntityType.ZOMBIE;
			spawn(server, kind, x, GROUND + 1, z, i * 37f);
			mobs++;
		}
		ShipPose lion = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), Ships.ROYAL_LION_SHIP);
			return s == null ? null : s.pose();
		});
		double lionDeck = lion == null ? 0 : lion.y() + Ships.ROYAL_LION_SHIP.geometry().hull().mainDeckY;
		if (lion != null) {
			for (int i = 0; i < 4; i++) {
				double[] w = lion.toWorld(i % 2 == 0 ? -1.5 : 1.5, 0, -8 + i * 5);
				spawn(server, EntityType.VILLAGER, w[0], lionDeck + 0.1, w[2], 90f);
				mobs++;
			}
		}
		int alive = server.computeOnServer(srv -> {
			int n = 0;
			for (var e : srv.getOverworld().iterateEntities()) {
				if (e.getCommandTags().contains("perfmob")) {
					n++;
				}
			}
			return n;
		});
		log.accept(String.format(Locale.ROOT, "perf scene: %d of %d props placed (%d registered), %d of %d vessels afloat, %d of %d mobs alive",
				placed, PROPS.length, props, vessels, SHIPS.length, alive, mobs));
		check.accept(props >= PROPS.length - 2 && vessels == SHIPS.length, String.format(Locale.ROOT,
				"perf scene: the city of %d props and the %d vessels are in place (%d props registered, %d vessels)", PROPS.length, SHIPS.length, props,
				vessels));
		StringBuilder census = new StringBuilder();
		for (ShipType t : SHIPS) {
			var model = context.computeOnClient(c -> ShipModels.get(ShipModels.of(t)));
			census.append(t.id()).append('=').append(model == null ? "?" : Integer.toString(model.quadCount())).append(' ');
		}
		log.accept("perf models (faces): " + census.toString().trim());
		world.waitForChunksRender();
		context.waitTicks(40);

		// ---- client: three cameras
		look(server, X, GROUND + 3.5, Z - 46, X, GROUND + 1, Z + 10);
		context.waitTicks(20);
		shot.accept("perf_market");
		camera(context, "market", check, log);
		look(server, X + 64, WATER_TOP + 5, Z - 60, X + 160, WATER_TOP + 1, Z);
		context.waitTicks(20);
		shot.accept("perf_harbour");
		camera(context, "harbour", check, log);
		if (lion != null) {
			double[] e = lion.toWorld(2.5, 0, -24);
			double[] t = lion.toWorld(40, 0, 60);
			look(server, e[0], lionDeck + 1.7, e[2], t[0], lionDeck + 2, t[2]);
			context.waitTicks(20);
			shot.accept("perf_deck");
			camera(context, "deck", check, log);
		}

		// ---- server: at rest, then with the royal lion ship under way
		look(server, X + 64, WATER_TOP + 5, Z - 60, X + 160, WATER_TOP + 1, Z);
		context.waitTicks(10);
		double[] rest = serverMeasure(context, server);
		double[] moving = rest;
		if (lion != null) {
			server.runCommand("ship route delete " + ROUTE);
			server.runCommand("ship route create " + ROUTE + " pingpong");
			server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addstop %s 1 A", lion.x(), lion.y(), lion.z(), ROUTE));
			server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addstop %s 1 B", lion.x(), lion.y(), lion.z() + 40,
					ROUTE));
			server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route start %s", lion.x(), lion.y(), lion.z(), ROUTE));
			context.waitTicks(30); // it leaves its first stop after a second
			moving = serverMeasure(context, server);
			double speed = server.computeOnServer(srv -> {
				ShipEntity s = ship(srv.getOverworld(), Ships.ROYAL_LION_SHIP);
				return s == null ? 0 : Math.abs(s.physics().speed);
			});
			log.accept(String.format(Locale.ROOT, "perf server: the royal lion ship sails at %.2f blocks/s during the second measure", speed));
			server.runCommand("ship route delete " + ROUTE);
		}
		check.accept(true, String.format(Locale.ROOT,
				"perf server: %d ticks, MSPT %.2f ms (%d mobs, %d vessels at rest) vs %.2f ms with the royal lion ship under way; "
						+ "collision hook %.0f calls/tick, %.3f ms/tick, %.0f hull queries/tick, %.0f boxes/tick; dry-room queries %.0f/tick; "
						+ "%.0f KB/tick allocated on the server thread (%.0f KB/tick under way)",
				TICKS, rest[0], alive, vessels, moving[0], rest[1], rest[4], rest[2], rest[3], rest[5], rest[6], moving[6]));
		log.accept(String.format(Locale.ROOT, "perf server under way: collision hook %.0f calls/tick, %.3f ms/tick, %.0f hull queries/tick, %.0f boxes/tick",
				moving[1], moving[4], moving[2], moving[3]));
		check.accept(true, String.format(Locale.ROOT, "perf run: %d garbage collections in %.0f s of wall time", gcCount() - gc0,
				(System.currentTimeMillis() - wall0) / 1000.0));

		// ---- the broad phase of the collision hook: a lone villager 150 blocks from every vessel moves for two seconds,
		// the hook is called for its every step and asks no hull for a single box (1.29.0)
		server.runCommand("kill @e[type=!player,tag=perfmob]");
		context.waitTicks(40); // the killed mobs fall and twitch for a second, some on a deck: let them go first
		spawn(server, EntityType.VILLAGER, X - 60, GROUND + 1, Z - 40, 0f);
		context.waitTicks(5);
		long[] far0 = server.computeOnServer(srv -> ShipCollisions.stats(false));
		context.waitTicks(40);
		long[] far1 = server.computeOnServer(srv -> ShipCollisions.stats(false));
		check.accept(far1[1] - far0[1] == 0, String.format(Locale.ROOT,
				"perf broad phase: a villager 150 blocks from every vessel went through the collision hook %d times in 40 ticks and no hull was queried (%d)",
				far1[0] - far0[0], far1[1] - far0[1]));

		// ---- cleanup
		server.computeOnServer(srv -> {
			for (ShipType t : SHIPS) {
				ShipEntity s = ship(srv.getOverworld(), t);
				if (s != null) {
					s.discard();
				}
			}
			return null;
		});
		server.runCommand("kill @e[type=!player,tag=perfmob]");
		for (int i = 0; i < PROPS.length; i++) {
			int col = i % 8, row = i / 8;
			server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", X - 56 + col * 16, GROUND + 1, Z - 28 + row * 14));
		}
		context.waitTicks(5);
		if (peaceful) {
			server.runCommand("difficulty peaceful");
		}
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 70, Z - 50, X + 70, Z + 50));
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", HARBOUR_X0 - 6, HARBOUR_Z0 - 6, HARBOUR_X1 + 6, HARBOUR_Z1 + 6));
		List<String> left = new ArrayList<>();
		server.computeOnServer(srv -> {
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (!s.isRemoved()) {
					left.add(s.shipType().id());
				}
			}
			return null;
		});
		log.accept("perf cleanup: vessels left " + left);
	}
}
