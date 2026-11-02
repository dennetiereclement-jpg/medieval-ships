package fr.medievalships.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.block.BlockState;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.ExperienceOrbEntity;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.projectile.ArrowEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.network.packet.c2s.play.PlayerActionC2SPacket;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Hand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.client.render.TrainingTargetRenderer;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.core.TrainingTarget;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.training.TrainingTargetEntity;
import fr.medievalships.training.TrainingTargets;

/**
 * In-game checks of the interactive training targets (1.19.0), on a stone platform of their own (x 1450, chunks
 * force-loaded). Each of the three training areas is placed ({@code /tent place}); its targets have spawned on the
 * server, one per JSON target (the tatami area has none), at their homes, with the target's box; the client has them
 * too (same boxes) and the area's static renderer leaves their bones to them. Each target is hit by a player attack
 * (a fist, then an iron sword) and by an arrow: its health does not change, it is still there, nothing drops, the hit
 * counter grows on the server and on the client and the client's reaction plays. On a sword-and-shield dummy a hit
 * aimed at the shield is told apart from a hit aimed at the body. {@code /kill} leaves the targets alone; asking for
 * them again (as when the area's block entity loads again) adds no duplicate; the anchor cannot be broken by a
 * survival player (the real mining path) nor by an explosion; {@code /tent remove} takes the targets away, a new
 * placement brings exactly one per target back; the chunks unloaded and loaded again bring them back once; the shield
 * area is placed facing west (turned homes) and removed by {@code /training remove}, the dummy area by a creative
 * player breaking its anchor. Screenshots of a dummy and of the bag mid-swing and of a shield hit. Called once from
 * {@link ShipClientGameTest}.
 */
public final class TrainingTargetGameTest {
	/** Dry ground of the flat world, between the tents' (1300) and the workshops' (1600) platforms. */
	private static final int X = 1450;
	private static final int GROUND = -60;

	private TrainingTargetGameTest() {
	}

	private static BlockPos anchor() {
		return new BlockPos(X, GROUND + 1, 0);
	}

	private static ServerPlayerEntity player(net.minecraft.server.MinecraftServer srv) {
		return srv.getPlayerManager().getPlayerList().get(0);
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	/** The server's target bound to {@code a} with that index, or null. */
	private static TrainingTargetEntity target(ServerWorld w, BlockPos a, int index) {
		for (TrainingTargetEntity t : TrainingTargets.of(w, a)) {
			if (t.index() == index) {
				return t;
			}
		}
		return null;
	}

	/** Every target entity of the world near the platform bound to {@code a}, alive or not counted twice. */
	private static int countNear(ServerWorld w, BlockPos a) {
		return w.getEntitiesByClass(TrainingTargetEntity.class, new Box(a).expand(12), e -> !e.isRemoved() && a.equals(e.anchor())).size();
	}

	/** Items and experience orbs on the platform (nothing may drop from a target). */
	private static int drops(ServerWorld w, BlockPos a) {
		Box b = new Box(a).expand(10, 4, 10);
		return w.getEntitiesByClass(ItemEntity.class, b, e -> !e.getStack().isOf(Items.ARROW)).size()
				+ w.getEntitiesByClass(ExperienceOrbEntity.class, b, e -> true).size();
	}

	/** A box of a target in world coordinates. */
	private static Box world(BlockPos a, TentType.Box b) {
		double cx = a.getX() + 0.5, cy = a.getY(), cz = a.getZ() + 0.5;
		return new Box(cx + b.x0(), cy + b.y0(), cz + b.z0(), cx + b.x1(), cy + b.y1(), cz + b.z1());
	}

	/** The world direction of a target's front: its shield side for a shield dummy, else the area's front. */
	private static Vec3d front(BlockPos a, TrainingTarget t, int quarter) {
		Vec3d c = world(a, t.hitbox()).getCenter();
		if (t.hasShield()) {
			Vec3d s = world(a, t.shieldBox()).getCenter();
			Vec3d d = new Vec3d(s.x - c.x, 0, s.z - c.z);
			if (d.lengthSquared() > 1e-4) {
				return d.normalize();
			}
		}
		double[] f = TentType.rotate(0, 1, quarter);
		return new Vec3d(f[0], 0, f[1]);
	}

	/**
	 * The player attacks target {@code index}, aimed from its eye at the point (the server rotation set just before):
	 * returns {hits before, hits after, health, max health, part, removed, strength, drops}.
	 */
	private static Object[] attack(TestServerContext server, BlockPos a, int index, Vec3d aim) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ServerPlayerEntity pl = player(srv);
			TrainingTargetEntity t = target(w, a, index);
			if (t == null) {
				return new Object[] {-1, -1, 0f, 0f, -1, true, 0f, 0};
			}
			Vec3d eye = pl.getEyePos();
			double dx = aim.x - eye.x, dy = aim.y - eye.y, dz = aim.z - eye.z;
			float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
			float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
			pl.setYaw(yaw);
			pl.setHeadYaw(yaw);
			pl.setPitch(pitch);
			int before = t.hits();
			pl.attack(t);
			return new Object[] {before, t.hits(), t.getHealth(), t.getMaxHealth(), t.lastPart(), t.isRemoved(), t.lastStrength(), drops(w, a)};
		});
	}

	/** On the client: {entities bound to a, hits of target index, its reaction moving, BER mask, box matches}. */
	private static Object[] client(ClientGameTestContext context, BlockPos a, int index, TentType type, double[] serverBox) {
		return context.computeOnClient((MinecraftClient c) -> {
			if (c.world == null) {
				return new Object[] {0, -1, false, 0L, false};
			}
			List<TrainingTargetEntity> list = c.world.getEntitiesByClass(TrainingTargetEntity.class, new Box(a).expand(12),
					e -> a.equals(e.anchor()));
			int hits = -1;
			boolean moving = false, sameBox = false;
			for (TrainingTargetEntity e : list) {
				if (e.index() == index) {
					hits = e.hits();
					moving = e.motion() != null && e.motion().moving();
					Box b = e.getBoundingBox();
					sameBox = serverBox != null && Math.abs(b.minX - serverBox[0]) < 1e-3 && Math.abs(b.minY - serverBox[1]) < 1e-3
							&& Math.abs(b.minZ - serverBox[2]) < 1e-3 && Math.abs(b.maxX - serverBox[3]) < 1e-3 && Math.abs(b.maxY - serverBox[4]) < 1e-3
							&& Math.abs(b.maxZ - serverBox[5]) < 1e-3;
				}
			}
			return new Object[] {list.size(), hits, moving, TrainingTargetRenderer.drawnMask(c.world, a, type), sameBox};
		});
	}

	private static double[] serverBox(TestServerContext server, BlockPos a, int index) {
		return server.computeOnServer(srv -> {
			TrainingTargetEntity t = target(srv.getOverworld(), a, index);
			if (t == null) {
				return null;
			}
			Box b = t.getBoundingBox();
			return new double[] {b.minX, b.minY, b.minZ, b.maxX, b.maxY, b.maxZ};
		});
	}

	/** Places an area and checks its targets (server and client); returns the entity ids. */
	private static List<Integer> place(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, TentType type,
			String facing, int quarter, BiConsumer<Boolean, String> check, Consumer<String> log) {
		String id = type.id();
		BlockPos a = anchor();
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d %s", id, a.getX(), a.getY(), a.getZ(), facing));
		world.waitForChunksRender();
		context.waitTicks(25);
		int n = type.targets().size();
		Object[] r = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			BlockState s = w.getBlockState(a);
			boolean placed = s.getBlock() instanceof TentBlock b && b.tentType() == type && TentBlock.quarter(s) == quarter;
			List<TrainingTargetEntity> list = TrainingTargets.of(w, a);
			boolean[] seen = new boolean[Math.max(1, n)];
			boolean homes = true, healthy = true, boxes = true;
			List<Integer> ids = new ArrayList<>();
			StringBuilder sb = new StringBuilder();
			for (TrainingTargetEntity t : list) {
				int i = t.index();
				ids.add(t.getId());
				if (i >= n || seen[i]) {
					homes = false;
					continue;
				}
				seen[i] = true;
				TrainingTarget g = type.targets(quarter).get(i);
				Vec3d home = TrainingTargetEntity.home(a, g);
				homes &= t.getEntityPos().distanceTo(home) < 1e-6;
				healthy &= t.getHealth() == t.getMaxHealth() && t.isAlive();
				Box want = world(a, g.reach()), got = t.getBoundingBox();
				boxes &= Math.abs(want.minX - got.minX) < 1e-4 && Math.abs(want.maxX - got.maxX) < 1e-4 && Math.abs(want.minY - got.minY) < 1e-4
						&& Math.abs(want.maxY - got.maxY) < 1e-4 && Math.abs(want.minZ - got.minZ) < 1e-4 && Math.abs(want.maxZ - got.maxZ) < 1e-4;
				sb.append(String.format(Locale.ROOT, " %s#%d %.2f %.2f %.2f", g.kind().id, i, t.getX(), t.getY(), t.getZ()));
			}
			return new Object[] {placed, list.size(), homes, healthy, boxes, sb.toString(), ids, countNear(w, a)};
		});
		log.accept(id + " targets:" + r[5]);
		check.accept(Boolean.TRUE.equals(r[0]), id + " placed facing " + facing);
		check.accept((Integer) r[1] == n && (Integer) r[7] == n, String.format(Locale.ROOT, "%s its %d target(s) spawned once each (%s, %s near)", id, n, r[1], r[7]));
		if (n > 0) {
			check.accept(Boolean.TRUE.equals(r[2]), id + " each target at its home (the JSON's box turned to the facing)");
			check.accept(Boolean.TRUE.equals(r[3]), id + " the targets are at full health");
			check.accept(Boolean.TRUE.equals(r[4]), id + " each target's box is its hitbox (with its shield)");
			double[] sb0 = serverBox(server, a, 0);
			Object[] c = client(context, a, 0, type, sb0);
			check.accept((Integer) c[0] == n, id + " the client has the " + n + " target(s) (" + c[0] + ")");
			check.accept(Boolean.TRUE.equals(c[4]), id + " the client's box of target 0 is the server's");
			check.accept((Long) c[3] == (1L << n) - 1, String.format(Locale.ROOT, "%s the static renderer leaves the %d target bones to their entities (mask %x)", id,
					n, (Long) c[3]));
		}
		@SuppressWarnings("unchecked")
		List<Integer> ids = (List<Integer>) r[6];
		return ids;
	}

	/** Every target of the area hit by the player (fist, then sword) and by an arrow. */
	private static void hitAll(ClientGameTestContext context, TestServerContext server, TentType type, int quarter, BiConsumer<Boolean, String> check,
			Consumer<String> log) {
		BlockPos a = anchor();
		String id = type.id();
		List<TrainingTarget> targets = type.targets(quarter);
		for (int i = 0; i < targets.size(); i++) {
			TrainingTarget g = targets.get(i);
			String name = id + " target " + i + " (" + g.kind().id + ")";
			Box body = world(a, g.hitbox());
			Vec3d f = front(a, g, quarter);
			Vec3d centre = body.getCenter();
			// the player in front of it (survival), a fist then an iron sword
			Vec3d stand = centre.add(f.multiply(Math.max(body.getLengthX(), body.getLengthZ()) / 2 + 1.4));
			server.runCommand("gamemode survival @a");
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f", stand.x, a.getY() + 0.0, stand.z));
			server.computeOnServer(srv -> {
				player(srv).setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
				return 0;
			});
			context.waitTicks(15);
			Object[] fist = attack(server, a, i, centre);
			check.accept((Integer) fist[1] == (Integer) fist[0] + 1, String.format(Locale.ROOT, "%s hit by a fist: its hit counter %d -> %d", name, fist[0], fist[1]));
			check.accept(((Float) fist[2]).floatValue() == ((Float) fist[3]).floatValue() && (Float) fist[3] > 0, String.format(Locale.ROOT, "%s no damage (%.1f / %.1f)", name, fist[2], fist[3]));
			check.accept(!Boolean.TRUE.equals(fist[5]), name + " still there after the hit");
			context.waitTicks(2);
			Object[] cl = client(context, a, i, type, null);
			check.accept((Integer) cl[1] == (Integer) fist[1], String.format(Locale.ROOT, "%s the client got the hit (%s)", name, cl[1]));
			check.accept(Boolean.TRUE.equals(cl[2]), name + " its reaction plays on the client");
			server.computeOnServer(srv -> {
				player(srv).setStackInHand(Hand.MAIN_HAND, new ItemStack(Items.IRON_SWORD));
				return 0;
			});
			context.waitTicks(20);
			Object[] sword = attack(server, a, i, centre);
			check.accept((Integer) sword[1] == (Integer) sword[0] + 1 && ((Float) sword[2]).floatValue() == ((Float) sword[3]).floatValue()
					&& !Boolean.TRUE.equals(sword[5]),
					String.format(Locale.ROOT, "%s hit by an iron sword: counted, no damage (%.1f / %.1f), still there", name, sword[2], sword[3]));
			check.accept((Float) sword[6] > (Float) fist[6], String.format(Locale.ROOT, "%s the sword hits harder than the fist (%.2f > %.2f)", name, sword[6], fist[6]));
			server.computeOnServer(srv -> {
				player(srv).setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
				return 0;
			});
			// an arrow shot at it from the front
			server.runCommand("gamemode spectator @a");
			Vec3d from = centre.add(f.multiply(Math.max(body.getLengthX(), body.getLengthZ()) / 2 + 1.5));
			final int idx = i;
			int before = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				TrainingTargetEntity t = target(w, a, idx);
				ArrowEntity arrow = new ArrowEntity(w, from.x, from.y, from.z, new ItemStack(Items.ARROW), null);
				Vec3d d = centre.subtract(from);
				arrow.setVelocity(d.x, d.y, d.z, 1.6f, 0f);
				w.spawnEntity(arrow);
				return t == null ? -1 : t.hits();
			});
			context.waitTicks(8);
			Object[] after = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				TrainingTargetEntity t = target(w, a, idx);
				return t == null ? new Object[] {-1, 0f, 0f, 0, 0} : new Object[] {t.hits(), t.getHealth(), t.getMaxHealth(), t.getStuckArrowCount(), drops(w, a)};
			});
			check.accept((Integer) after[0] > before && before >= 0, String.format(Locale.ROOT, "%s hit by an arrow: counter %d -> %d", name, before, after[0]));
			check.accept(((Float) after[1]).floatValue() == ((Float) after[2]).floatValue() && (Integer) after[3] == 0,
					String.format(Locale.ROOT, "%s the arrow does no damage and does not stick (%.1f / %.1f, %d stuck)", name, after[1], after[2], after[3]));
			check.accept((Integer) after[4] == 0, name + " nothing dropped (no item, no experience): " + after[4]);
		}
	}

	/** On a shield dummy: a hit aimed at the shield from its side is a shield hit, one aimed at the body from behind a body hit. */
	private static void shieldOrBody(ClientGameTestContext context, TestServerContext server, TentType type, int quarter,
			BiConsumer<Boolean, String> check) {
		BlockPos a = anchor();
		List<TrainingTarget> targets = type.targets(quarter);
		for (int i = 0; i < targets.size(); i++) {
			TrainingTarget g = targets.get(i);
			if (!g.hasShield()) {
				continue;
			}
			Vec3d n = front(a, g, quarter);
			Box body = world(a, g.hitbox()), shield = world(a, g.shieldBox());
			Vec3d sc = shield.getCenter(), bc = body.getCenter();
			server.runCommand("gamemode spectator @a");
			Vec3d eye = sc.add(n.multiply(1.6));
			look(server, eye.x, eye.y, eye.z, sc.x, sc.y, sc.z);
			context.waitTicks(15);
			Object[] s = attack(server, a, i, sc);
			check.accept((Integer) s[4] == TrainingTarget.PART_SHIELD && (Integer) s[1] == (Integer) s[0] + 1,
					type.id() + " target " + i + ": a hit aimed at the shield is a shield hit (part " + s[4] + ")");
			Vec3d back = bc.subtract(n.multiply(Math.max(body.getLengthX(), body.getLengthZ()) / 2 + 1.4));
			look(server, back.x, bc.y + 0.2, back.z, bc.x, bc.y, bc.z);
			context.waitTicks(15);
			Object[] b = attack(server, a, i, bc);
			check.accept((Integer) b[4] == TrainingTarget.PART_BODY && (Integer) b[1] == (Integer) b[0] + 1,
					type.id() + " target " + i + ": a hit on the body from behind is a body hit (part " + b[4] + ")");
		}
	}

	/** Survival mining of the anchor (the real path), {@code /kill}, a second request, an explosion: nothing changes. */
	private static void indestructible(ClientGameTestContext context, TestServerContext server, TentType type, BiConsumer<Boolean, String> check,
			boolean explode) {
		BlockPos a = anchor();
		String id = type.id();
		int n = type.targets().size();
		server.runCommand("gamemode survival @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %d %.2f", a.getX() + 0.5, a.getY(), a.getZ() + 2.5));
		context.waitTicks(10);
		Object[] r = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ServerPlayerEntity pl = player(srv);
			BlockState s = w.getBlockState(a);
			float hardness = s.getHardness(w, a);
			float blast = s.getBlock().getBlastResistance();
			pl.interactionManager.processBlockBreakingAction(a, PlayerActionC2SPacket.Action.START_DESTROY_BLOCK, Direction.UP, w.getTopYInclusive(), 0);
			return new Object[] {hardness, blast};
		});
		context.waitTicks(40);
		boolean still = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			player(srv).interactionManager.processBlockBreakingAction(a, PlayerActionC2SPacket.Action.STOP_DESTROY_BLOCK, Direction.UP,
					w.getTopYInclusive(), 0);
			return w.getBlockState(a).getBlock() instanceof TentBlock;
		});
		context.waitTicks(5);
		int left = server.computeOnServer(srv -> TrainingTargets.of(srv.getOverworld(), a).size());
		check.accept((Float) r[0] < 0 && (Float) r[1] >= 3600000f, String.format(Locale.ROOT, "%s unbreakable anchor (hardness %.0f, blast resistance %.0f)", id,
				r[0], r[1]));
		check.accept(still && left == n, id + " a survival player mining its anchor for 2 s does not break it (targets " + left + ")");
		server.runCommand("gamemode spectator @a");
		// /kill: the targets are not killed (the area's removal is the way)
		server.runCommand("kill @e[type=medievalships:training_target]");
		context.waitTicks(5);
		int afterKill = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		check.accept(afterKill == n, id + " /kill leaves the targets alone (" + afterKill + ")");
		// asked for again (as when its block entity loads again): no duplicate
		server.computeOnServer(srv -> {
			TrainingTargets.request(srv.getOverworld(), a);
			TrainingTargets.request(srv.getOverworld(), a);
			return TrainingTargets.ensure(srv.getOverworld(), a).name();
		});
		context.waitTicks(5);
		int again = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		check.accept(again == n, id + " asking for its targets again spawns no duplicate (" + again + ")");
		if (explode) {
			server.computeOnServer(srv -> {
				srv.getOverworld().createExplosion(null, a.getX() + 0.5, a.getY() + 0.5, a.getZ() + 1.5, 3.0f, World.ExplosionSourceType.TNT);
				return 0;
			});
			context.waitTicks(10);
			Object[] e = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				boolean full = true;
				for (TrainingTargetEntity t : TrainingTargets.of(w, a)) {
					full &= t.getHealth() == t.getMaxHealth();
				}
				return new Object[] {w.getBlockState(a).getBlock() instanceof TentBlock, countNear(w, a), full};
			});
			check.accept(Boolean.TRUE.equals(e[0]) && (Integer) e[1] == n && Boolean.TRUE.equals(e[2]),
					id + " an explosion next to it leaves the anchor and the targets (" + e[1] + ", full health " + e[2] + ")");
		}
	}

	private static void platform(TestServerContext server) {
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -14 %d %d 14 stone", X - 14, X + 14, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -14 %d %d 14 air", X - 14, GROUND + 1, X + 14, GROUND + 12));
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		BlockPos a = anchor();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, -16, X + 16, 16));
		context.waitTicks(30);
		platform(server);
		context.waitTicks(10);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		ItemStack[] held = new ItemStack[1];
		server.computeOnServer(srv -> {
			held[0] = player(srv).getMainHandStack().copy();
			return 0;
		});

		// ---- the strike area: a punching bag and three dummies, facing south
		TentType dummy = TentTypes.TRAINING_DUMMY;
		check.accept(dummy.targets().size() >= 2, "training_area_dummy has targets in its JSON (" + dummy.targets().size() + ")");
		List<Integer> first = place(context, server, world, dummy, "south", TentType.SOUTH, check, log);
		double cx = a.getX() + 0.5, cz = a.getZ() + 0.5;
		look(server, cx - 5.5, GROUND + 4.6, cz + 6.5, cx, GROUND + 1.6, cz - 0.8);
		context.waitTicks(20);
		shot.accept("training_dummy_1_repos");
		hitAll(context, server, dummy, TentType.SOUTH, check, log);
		// mid-swing screenshots: a dummy hit hard, the bag hit hard (from the camera's side)
		int dummyIndex = -1, bagIndex = -1;
		for (int i = 0; i < dummy.targets().size(); i++) {
			if (dummy.targets().get(i).kind() == TrainingTarget.Kind.DUMMY && dummyIndex < 0) {
				dummyIndex = i;
			}
			if (dummy.targets().get(i).kind() == TrainingTarget.Kind.BAG && bagIndex < 0) {
				bagIndex = i;
			}
		}
		server.runCommand("gamemode spectator @a");
		if (dummyIndex >= 0) {
			Box b = world(a, dummy.targets(TentType.SOUTH).get(dummyIndex).hitbox());
			Vec3d c = b.getCenter();
			look(server, c.x - 2.6, GROUND + 2.6, c.z + 3.2, c.x, c.y, c.z);
			server.computeOnServer(srv -> {
				player(srv).setStackInHand(Hand.MAIN_HAND, new ItemStack(Items.IRON_SWORD));
				return 0;
			});
			context.waitTicks(25);
			attack(server, a, dummyIndex, c);
			context.waitTicks(3);
			shot.accept("training_dummy_2_mannequin_frappe");
			Object[] cl = client(context, a, dummyIndex, dummy, null);
			check.accept(Boolean.TRUE.equals(cl[2]), "training_area_dummy the dummy swings on the client after a sword hit");
		}
		if (bagIndex >= 0) {
			Box b = world(a, dummy.targets(TentType.SOUTH).get(bagIndex).hitbox());
			Vec3d c = b.getCenter();
			look(server, c.x - 3.2, GROUND + 2.4, c.z + 3.4, c.x, c.y, c.z);
			context.waitTicks(25);
			attack(server, a, bagIndex, c);
			context.waitTicks(7);
			shot.accept("training_dummy_3_sac_balance");
			Object[] cl = client(context, a, bagIndex, dummy, null);
			check.accept(Boolean.TRUE.equals(cl[2]), "training_area_dummy the bag swings on the client after a sword hit");
		}
		server.computeOnServer(srv -> {
			player(srv).setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
			return 0;
		});
		indestructible(context, server, dummy, check, false);
		// /tent remove takes the targets away; placed again: exactly one per target, new entities
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(5);
		int gone = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		check.accept(gone == 0, "training_area_dummy /tent remove takes its targets away (" + gone + " left)");
		List<Integer> second = place(context, server, world, dummy, "south", TentType.SOUTH, check, log);
		check.accept(second.stream().noneMatch(first::contains), "training_area_dummy placed again: new target entities, none left from before");
		// the chunks unloaded (nobody near, not force-loaded) then loaded again: the targets come back, once each
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, -16, X + 16, 16));
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0", X + 3000, GROUND + 20));
		boolean unloaded = false;
		for (int k = 0; k < 30 && !unloaded; k++) {
			context.waitTicks(20);
			unloaded = server.computeOnServer(srv -> !srv.getOverworld().isChunkLoaded(ChunkPos.toLong(a.getX() >> 4, a.getZ() >> 4)));
		}
		log.accept("training_area_dummy chunk unloaded while away: " + unloaded);
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, -16, X + 16, 16));
		int back = -1;
		for (int k = 0; k < 15; k++) {
			context.waitTicks(20);
			back = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
			if (back == dummy.targets().size()) {
				break;
			}
		}
		world.waitForChunksRender();
		context.waitTicks(40);
		int settled = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		check.accept(back == dummy.targets().size() && settled == back, String.format(Locale.ROOT,
				"training_area_dummy after its chunks %s and came back: %d target(s), no duplicate (%d)", unloaded ? "unloaded" : "stayed loaded", back, settled));
		// removed by a creative player breaking its anchor
		server.runCommand("gamemode creative @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %d %.2f", a.getX() + 0.5, a.getY(), a.getZ() + 2.5));
		context.waitTicks(10);
		boolean broken = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ServerPlayerEntity pl = player(srv);
			pl.setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
			pl.interactionManager.processBlockBreakingAction(a, PlayerActionC2SPacket.Action.START_DESTROY_BLOCK, Direction.UP, w.getTopYInclusive(), 0);
			return !(w.getBlockState(a).getBlock() instanceof TentBlock);
		});
		context.waitTicks(5);
		int afterBreak = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		check.accept(broken && afterBreak == 0, "training_area_dummy a creative player breaks its anchor, its targets go with it (" + afterBreak + " left)");
		server.runCommand("gamemode spectator @a");
		int registry = server.computeOnServer(srv -> TentCollisions.at(srv.getOverworld(), a) == null ? 0 : 1);
		check.accept(registry == 0, "training_area_dummy its collision boxes are forgotten");

		// ---- the tatami area: no targets
		TentType tatami = TentTypes.TRAINING_TATAMI;
		place(context, server, world, tatami, "south", TentType.SOUTH, check, log);
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(5);

		// ---- the sword and shield area, facing west (the targets' homes turned), shield or body, removed by /training remove
		TentType shield = TentTypes.TRAINING_SHIELD;
		place(context, server, world, shield, "west", TentType.WEST, check, log);
		hitAll(context, server, shield, TentType.WEST, check, log);
		shieldOrBody(context, server, shield, TentType.WEST, check);
		if (!shield.targets().isEmpty()) {
			TrainingTarget g = shield.targets(TentType.WEST).get(0);
			Vec3d n = front(a, g, TentType.WEST);
			Vec3d sc = world(a, g.shieldBox()).getCenter();
			Vec3d cam = sc.add(n.multiply(2.4)).add(n.z * 1.6, 0, -n.x * 1.6);
			server.runCommand("gamemode spectator @a");
			look(server, cam.x, GROUND + 2.6, cam.z, sc.x, sc.y, sc.z);
			context.waitTicks(25);
			attack(server, a, 0, sc);
			context.waitTicks(3);
			shot.accept("training_shield_4_bouclier");
		}
		indestructible(context, server, shield, check, true);
		server.runCommand(String.format(Locale.ROOT, "training remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(5);
		int shieldLeft = server.computeOnServer(srv -> countNear(srv.getOverworld(), a));
		boolean shieldGone = server.computeOnServer(srv -> !(srv.getOverworld().getBlockState(a).getBlock() instanceof TentBlock));
		check.accept(shieldGone && shieldLeft == 0, "training_area_shield removed by /training remove, its targets with it (" + shieldLeft + " left)");

		platform(server);
		server.computeOnServer(srv -> {
			player(srv).setStackInHand(Hand.MAIN_HAND, held[0] == null ? ItemStack.EMPTY : held[0]);
			return 0;
		});
		server.runCommand("gamemode spectator @a");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, -16, X + 16, 16));
	}
}
