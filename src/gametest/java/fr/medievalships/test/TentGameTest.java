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

import fr.medievalships.core.CannonState;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.tent.CannonBlockEntity;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.tent.Tents;

/**
 * In-game checks of the tents (about 40 s of game time). The adventurer tent in detail: {@code /tent place} on a
 * stone platform, the anchor block and its facing, a survival player walking into a front leg is stopped by its
 * collision box (the static boxes of TentCollisions through the entity collision mixin), screenshots,
 * {@code /tent remove}, the block and the boxes are gone. Then each of the eighteen other tents once (the five other
 * camp tents, the six merchant tents of 1.14.0, the five of 1.15.0 and the two of 1.16.0, at most about 9 x 9 blocks
 * with their rug, 8.2 high: the 29 x 29 platform and the 12 blocks of air above it hold them): placed, block and facing
 * and block entity, its first collision box answers a collision query, one screenshot, removed. Last the medieval
 * cannon (1.16.0): the same, plus its own block entity type ({@code medievalships:cannon}), its persisted state written
 * and read back through NBT, its muzzle on the far side from the breech, a screenshot from the reference's angle.
 * The three training areas of 1.18.0 (about 7.5 x 7.5 blocks, 3 high) are placed once each like the tents, before the
 * cannon. Called once from {@link ShipClientGameTest}.
 */
public final class TentGameTest {
	private static final TentType TYPE = TentTypes.ADVENTURER;
	/** Dry ground of the flat world, east of every basin (the sloop's is at x 880-920, the frigate's at 1072-1128). */
	private static final int X = 1300;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;

	private TentGameTest() {
	}

	private static BlockPos anchor() {
		return new BlockPos(X, GROUND + 1, 0);
	}

	private static Object[] blockAt(TestServerContext server, BlockPos pos) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var state = w.getBlockState(pos);
			boolean tent = state.getBlock() instanceof TentBlock b && b.tentType() == TYPE;
			return new Object[] {tent, tent ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
					w.getBlockEntity(pos) != null};
		});
	}

	private static double[] player(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			return new double[] {pl.getX(), pl.getY(), pl.getZ()};
		});
	}

	/** Puts the player's eyes at (ex, ey, ez) looking at (tx, ty, tz). */
	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	/** Places one tent facing south on the platform, checks block, facing, block entity, one collision box, one shot, removes it. */
	private static void quick(TentType type, ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> shot) {
		quick(type, context, server, world, check, shot, null);
	}

	/**
	 * A free NPC spot inside a tent (prop-local, facing south): the centre of a 1 x 1 x 2.2 column standing on the ground
	 * inside the extent (0.8 from its sides), off the anchor block, clear of every collision box; the nearest to the
	 * extent's centre on a quarter-block grid, or null.
	 */
	static double[] npcSpot(TentType type) {
		TentType.Box e = type.extent(TentType.SOUTH);
		double cx = (e.x0() + e.x1()) / 2, cz = (e.z0() + e.z1()) / 2;
		double[] best = null;
		double bestD = Double.MAX_VALUE;
		for (double x = e.x0() + 0.8; x <= e.x1() - 0.8; x += 0.25) {
			for (double z = e.z0() + 0.8; z <= e.z1() - 0.8; z += 0.25) {
				if (Math.abs(x) < 0.85 && Math.abs(z) < 0.85) {
					continue; // the anchor block (its thin floor collides)
				}
				boolean free = true;
				for (TentType.Box b : type.colliders(TentType.SOUTH)) {
					if (x + 0.5 > b.x0() && x - 0.5 < b.x1() && z + 0.5 > b.z0() && z - 0.5 < b.z1() && 2.2 > b.y0() && 0.0 < b.y1()) {
						free = false;
						break;
					}
				}
				double d = Math.hypot(x - cx, z - cz);
				if (free && d < bestD) {
					bestD = d;
					best = new double[] {x, z};
				}
			}
		}
		return best;
	}

	/**
	 * The military camp tents (1.24.0): once each like {@link #quick}, plus a villager (NoAI) put on a free NPC spot inside
	 * ({@link #npcSpot}) is not inside any collision box in game (the mixin's path) and stays where it was put.
	 */
	private static void camp(TentType type, ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = type.id();
		BlockPos a = anchor();
		double[] spot = npcSpot(type);
		check.accept(spot != null, id + " has a free NPC spot inside (1 x 1 x 2.2, clear of every collision box)");
		Runnable villager = spot == null ? null : () -> {
			double vx = a.getX() + 0.5 + spot[0], vz = a.getZ() + 0.5 + spot[1];
			java.util.UUID uuid = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				var v = net.minecraft.entity.EntityType.VILLAGER.create(w, net.minecraft.entity.SpawnReason.COMMAND);
				if (v == null) {
					return null;
				}
				v.setAiDisabled(true);
				v.setSilent(true);
				v.refreshPositionAndAngles(vx, a.getY(), vz, 0f, 0f);
				w.spawnEntity(v);
				return v.getUuid();
			});
			context.waitTicks(10);
			double[] r = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				var v = uuid == null ? null : w.getEntity(uuid);
				if (v == null) {
					return null;
				}
				java.util.List<net.minecraft.util.shape.VoxelShape> out = new java.util.ArrayList<>();
				TentCollisions.append(out, v, v.getBoundingBox().contract(0.02), w);
				double[] res = {out.size(), v.getX() - vx, v.getY() - a.getY(), v.getZ() - vz};
				v.discard();
				return res;
			});
			log.accept(String.format(Locale.ROOT, "%s NPC spot (%.2f, %.2f): %s", id, spot[0], spot[1], r == null ? "no villager"
					: String.format(Locale.ROOT, "%d shape(s), moved %.2f %.2f %.2f", (int) r[0], r[1], r[2], r[3])));
			check.accept(r != null && r[0] == 0, id + " a villager on its NPC spot is not inside any collision box");
			check.accept(r != null && Math.abs(r[1]) < 0.1 && Math.abs(r[2]) < 0.1 && Math.abs(r[3]) < 0.1, id + " the villager stays on its NPC spot");
		};
		quick(type, context, server, world, check, shot, villager);
	}

	private static void quick(TentType type, ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> shot, Runnable extra) {
		String id = type.id();
		BlockPos a = anchor();
		int before = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", id, a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(20);
		Object[] b0 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var state = w.getBlockState(a);
			boolean tent = state.getBlock() instanceof TentBlock b && b.tentType() == type;
			return new Object[] {tent, tent ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
					w.getBlockEntity(a) != null};
		});
		check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed: anchor block at %s (%s)", id, a.toShortString(), b0[1]));
		check.accept("south".equals(b0[1]), id + " faces south (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[3]), id + " has its block entity");
		check.accept((Integer) b0[2] == before + 1, id + " registered its collision boxes (" + b0[2] + " tent(s) in the registry)");
		// one collision: the tent's first world box answers a collision query through TentCollisions.append (the mixin's path)
		int hits = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var boxes = TentCollisions.worldBoxes(type, a, TentType.SOUTH);
			if (boxes.isEmpty()) {
				return -1;
			}
			java.util.List<net.minecraft.util.shape.VoxelShape> out = new java.util.ArrayList<>();
			TentCollisions.append(out, null, boxes.get(0).expand(0.05), w);
			return out.size();
		});
		check.accept(hits >= 1, id + " a collision query on its first solid box finds it (" + hits + " shape(s))");
		if (extra != null) {
			extra.run();
		}
		// one screenshot from the front-left, above
		TentType.Box e = type.extent(TentType.SOUTH);
		double cx = a.getX() + 0.5, cz = a.getZ() + 0.5;
		double r = Math.max(e.width(), e.depth()) * 1.15 + 2.0;
		look(server, cx - r * 0.6, GROUND + 1 + e.height() * 0.8 + 1.5, cz + r * 0.8, cx, GROUND + 1 + e.height() * 0.4, cz);
		context.waitTicks(25);
		shot.accept(id + "_1_reference");
		// removed by position
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(10);
		Object[] b2 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			return new Object[] {w.getBlockState(a).getBlock() instanceof TentBlock, TentCollisions.count(w), w.getBlockEntity(a) != null};
		});
		check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[2]), id + " removed by /tent remove x y z");
		check.accept((Integer) b2[1] == before, id + " its collision boxes are forgotten (" + b2[1] + " tent(s) left)");
	}

	/**
	 * The medieval cannon: placed once like the tents ({@link #quick}), then placed again for its own checks: its block
	 * entity is a {@link CannonBlockEntity} of the type {@code medievalships:cannon}, empty when placed (no key in its
	 * NBT), a state set on it is written to NBT and read back identical by a fresh block entity, the muzzle is on the far
	 * side from the breech (facing south: to the north), a screenshot from the reference's angle; removed.
	 */
	private static void cannon(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		TentType type = TentTypes.CANNON;
		quick(type, context, server, world, check, shot);
		BlockPos a = anchor();
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", type.id(), a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(20);
		Object[] r = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var be = w.getBlockEntity(a);
			if (!(be instanceof CannonBlockEntity cbe)) {
				return new Object[] {false, String.valueOf(be), false, false, false, "", 0.0, 0.0};
			}
			var registries = srv.getRegistryManager();
			boolean ownType = cbe.getType() == Tents.CANNON_BLOCK_ENTITY;
			boolean emptyAtFirst = cbe.cannonState().isEmpty() && !cbe.createNbt(registries).contains(CannonState.KEY_LOADED);
			CannonState set = new CannonState(true, 2, 0, 1234L);
			cbe.setCannonState(set);
			var nbt = cbe.createNbtWithIdentifyingData(registries);
			var copy = net.minecraft.block.entity.BlockEntity.createFromNbt(a, w.getBlockState(a), nbt, registries);
			boolean roundTrip = copy instanceof CannonBlockEntity c2 && set.equals(c2.cannonState());
			cbe.setCannonState(CannonState.EMPTY);
			var m = cbe.muzzle();
			var d = cbe.muzzleDirection();
			return new Object[] {true, nbt.toString(), ownType, emptyAtFirst, roundTrip, String.valueOf(copy), m.z - (a.getZ() + 0.5), d.z};
		});
		log.accept("canon_medieval NBT with a state: " + r[1]);
		check.accept(Boolean.TRUE.equals(r[0]), "canon_medieval has a CannonBlockEntity (" + (Boolean.TRUE.equals(r[0]) ? "yes" : r[1]) + ")");
		check.accept(Boolean.TRUE.equals(r[2]), "canon_medieval its block entity type is medievalships:cannon");
		check.accept(Boolean.TRUE.equals(r[3]), "canon_medieval a new cannon is empty and writes no state key");
		check.accept(Boolean.TRUE.equals(r[4]), "canon_medieval its state (loaded, 2 powder, last shot 1234) is saved and read back (" + r[5] + ")");
		check.accept((Double) r[6] < -1.5 && (Double) r[7] < -0.9, String.format(Locale.ROOT,
				"canon_medieval facing south (breech to the south), the muzzle is to the north (z %+.2f, direction z %.2f)", r[6], r[7]));
		// the reference's angle: from the left front of the muzzle, a little above
		double cx = a.getX() + 0.5, cz = a.getZ() + 0.5;
		look(server, cx - 4.2, GROUND + 1 + 2.4, cz - 3.4, cx, GROUND + 1 + 1.0, cz - 0.4);
		context.waitTicks(25);
		shot.accept("canon_medieval_2_reference");
		look(server, cx - 4.5, GROUND + 1 + 1.6, cz + 0.4, cx, GROUND + 1 + 1.0, cz);
		context.waitTicks(12);
		shot.accept("canon_medieval_3_cote");
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(10);
		boolean gone = server.computeOnServer(srv -> !(srv.getOverworld().getBlockEntity(a) instanceof CannonBlockEntity));
		check.accept(gone, "canon_medieval removed");
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, -16, X + 16, 16));
		context.waitTicks(30);
		// a flat stone platform of its own on dry land, the air cleared above it
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -14 %d %d 14 stone", X - 14, X + 14, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -14 %d %d 14 air", X - 14, GROUND + 1, X + 14, GROUND + 12));
		context.waitTicks(10);
		// the six merchant tents (1.14.0) and the five of 1.15.0 are in the list placed below, and each fits the cleared
		// area of the platform
		check.accept(TentTypes.ALL.containsAll(TentTypes.MERCHANTS) && TentTypes.MERCHANTS.size() == 6,
				"the six merchant tents are placed once each below (" + TentTypes.MERCHANTS.size() + ")");
		check.accept(TentTypes.ALL.containsAll(TentTypes.MERCHANTS2) && TentTypes.MERCHANTS2.size() == 5,
				"the five merchant tents of 1.15.0 are placed once each below (" + TentTypes.MERCHANTS2.size() + ")");
		check.accept(TentTypes.ALL.containsAll(TentTypes.MERCHANTS3) && TentTypes.MERCHANTS3.size() == 2,
				"the two merchant tents of 1.16.0 are placed once each below (" + TentTypes.MERCHANTS3.size() + ")");
		check.accept(TentTypes.ALL.containsAll(TentTypes.MERCHANTS4) && TentTypes.MERCHANTS4.size() == 2,
				"the two merchant stalls of 1.17.0 (the baker's, the longer fishmonger's) are placed once each below ("
						+ TentTypes.MERCHANTS4.size() + ")");
		check.accept(TentTypes.ALL.containsAll(TentTypes.MERCHANTS5) && TentTypes.MERCHANTS5.size() == 1,
				"the jeweller's tent of 1.21.0 is placed once below (" + TentTypes.MERCHANTS5.size() + ")");
		check.accept(TentTypes.TRAINING.size() == 3, "the three training areas of 1.18.0 are placed once each below (" + TentTypes.TRAINING.size()
				+ ")");
		check.accept(TentTypes.ALL.containsAll(TentTypes.CAMP_TENTS) && TentTypes.CAMP_TENTS.size() == 3,
				"the three military camp tents of 1.24.0 are placed once each below, with a villager on an NPC spot (" + TentTypes.CAMP_TENTS.size() + ")");
		for (TentType t : java.util.stream.Stream.of(TentTypes.MERCHANTS, TentTypes.MERCHANTS2, TentTypes.MERCHANTS3, TentTypes.MERCHANTS4,
				TentTypes.MERCHANTS5, TentTypes.CAMP_TENTS, TentTypes.TRAINING, TentTypes.ARTILLERY)
				.flatMap(java.util.List::stream).toList()) {
			TentType.Box e = t.extent(TentType.SOUTH);
			check.accept(e.x0() > -14 && e.x1() < 14 && e.z0() > -14 && e.z1() < 14 && e.y1() < 12,
					String.format(Locale.ROOT, "%s fits the cleared platform (extent x %.1f..%.1f z %.1f..%.1f h %.1f)", t.id(), e.x0(), e.x1(),
							e.z0(), e.z1(), e.y1()));
		}
		BlockPos a = anchor();
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", id, a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(30);
		Object[] b0 = blockAt(server, a);
		check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed by /tent place: anchor block at %s (%s)", id, a.toShortString(), b0[1]));
		check.accept("south".equals(b0[1]), id + " faces south as asked (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[3]), id + " has its block entity");
		check.accept((Integer) b0[2] >= 1, id + " registered its collision boxes (" + b0[2] + " tent(s) in the registry)");
		if (!Boolean.TRUE.equals(b0[0])) {
			for (TentType t : TentTypes.ALL) {
				if (TentTypes.CAMP_TENTS.contains(t)) {
					camp(t, context, server, world, check, log, shot);
				} else if (t != TYPE) {
					quick(t, context, server, world, check, shot);
				}
			}
			for (TentType t : TentTypes.TRAINING) {
				quick(t, context, server, world, check, shot);
			}
			cannon(context, server, world, check, log, shot);
			return;
		}
		// the same tent placed again on top of it is refused (the area is not free)
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", id, a.getX() + 1, a.getY(), a.getZ() + 1));
		context.waitTicks(5);
		Object[] b1 = blockAt(server, a.add(1, 0, 1));
		check.accept(!Boolean.TRUE.equals(b1[0]) && (Integer) b1[2] == (Integer) b0[2], id + " a second tent over the first is refused");

		// screenshots: the reference's view (front-left, above), the front, the inside
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		look(server, X - 7.5, GROUND + 5.5, 9.5, X + 0.5, GROUND + 2.0, 0.5);
		context.waitTicks(25);
		shot.accept(id + "_1_reference");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f %.1f %.1f", X + 0.5, GROUND + 3.0, 11.0, 180.0, 8.0));
		context.waitTicks(12);
		shot.accept(id + "_2_face");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f %.1f %.1f", X + 0.3, GROUND + 2.6, 3.2, 180.0, 18.0));
		context.waitTicks(12);
		shot.accept(id + "_3_interieur");

		// a survival player walks north into the right front leg (tent-local (1.3, 0, 2.45) -> world x+1.3, z+2.45): stopped by it
		TentType.Box leg = null;
		for (TentType.Box c : TYPE.colliders(TentType.SOUTH)) {
			if (c.z0() > 1.5 && c.y0() < 0.2 && c.x0() > 0.5) {
				leg = c;
				break;
			}
		}
		check.accept(leg != null, id + " has a front leg collision box");
		if (leg != null) {
			double lx = a.getX() + 0.5 + (leg.x0() + leg.x1()) / 2, lz = a.getZ() + 0.5 + leg.z1();
			server.runCommand("gamemode survival @a");
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 10", lx, a.getY(), lz + 1.2));
			context.waitTicks(10);
			double[] p0 = player(server);
			context.getInput().holdKeyFor(o -> o.forwardKey, 25);
			context.waitTicks(5);
			double[] p1 = player(server);
			log.accept(String.format(Locale.ROOT, "%s walk into the leg: z %.2f -> %.2f (leg face at %.2f)", id, p0[2], p1[2], lz));
			check.accept(p1[2] > lz + 0.25 && p0[2] - p1[2] > 0.3, String.format(Locale.ROOT,
					"%s the front leg stops the player (moved %.2f, stopped %.2f in front of it)", id, p0[2] - p1[2], p1[2] - lz));
			// and the player can walk freely through the entrance (no collision on the canvas)
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 10", a.getX() + 0.5, a.getY(), a.getZ() + 0.5 + 3.0));
			context.waitTicks(8);
			double[] q0 = player(server);
			context.getInput().holdKeyFor(o -> o.forwardKey, 20);
			context.waitTicks(5);
			double[] q1 = player(server);
			check.accept(q0[2] - q1[2] > 1.5, String.format(Locale.ROOT, "%s the entrance is open (walked %.2f blocks in)", id, q0[2] - q1[2]));
			server.runCommand("gamemode spectator @a");
		}

		// /tent remove: the block and its boxes are gone
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d 0 run tent remove nearest", X, GROUND + 1));
		context.waitTicks(10);
		Object[] b2 = blockAt(server, a);
		check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[3]), id + " removed by /tent remove (block " + b2[1] + ")");
		check.accept((Integer) b2[2] == (Integer) b0[2] - 1, id + " its collision boxes are forgotten (" + b2[2] + " tent(s) left)");
		// the other tents (camp tents, the merchant tents of 1.14.0 - 1.17.0, the jeweller's of 1.21.0), once each
		for (TentType t : TentTypes.ALL) {
			if (TentTypes.CAMP_TENTS.contains(t)) {
				camp(t, context, server, world, check, log, shot);
			} else if (t != TYPE) {
				quick(t, context, server, world, check, shot);
			}
		}
		// the three training areas (1.18.0): fenced yards of about 7 x 7 blocks, once each
		for (TentType t : TentTypes.TRAINING) {
			quick(t, context, server, world, check, shot);
		}
		// the medieval cannon (1.16.0)
		cannon(context, server, world, check, log, shot);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, -16, X + 16, 16));
	}
}
