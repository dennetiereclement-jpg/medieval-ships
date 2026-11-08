package fr.medievalships.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.Difficulty;

import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.tent.StakeHazard;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentBlockEntity;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.tent.Tents;

/**
 * In-game checks of the defensive stake (1.25.0). On a stone platform of its own (x 1300, z 80, beside the
 * decorations'; chunks force-loaded): one stake placed facing south by {@code /deco place} (its point to the north,
 * away from the player who would have planted it looking north), block / facing / block entity, a server ticker (and
 * none for another prop), its boxes registered and its trunk colliding. Then the point: a zombie (NoAI, a helmet against
 * the sun) put at the point is hurt within 10 ticks and pushed outward (north), not hurt again before the cooldown, hurt
 * again after it; a zombie at the foot (against the front face of the trunk's first box) and one against the trunk's
 * side at mid-length, and a villager at the point, are never hurt. The test player in survival at the point (its
 * Resistance V, which would cancel any damage, taken away meanwhile and given back after) is neither hurt nor hit by the
 * stake by default, is hurt once "damagePlayers" is set through the config API (restored after). Three stakes placed side by side one block apart all stand; a screenshot from the reference's angle;
 * a stake broken drops its item. Called once from {@link ShipClientGameTest}.
 */
public final class StakeGameTest {
	private static final int X = 1300, Z = 80;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;
	private static final TentType TYPE = TentTypes.STAKE;

	private StakeGameTest() {
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	/** Spawns a NoAI mob (zombies get a helmet: no burning in the sun) at a world position; returns its uuid. */
	private static UUID spawn(TestServerContext server, EntityType<? extends MobEntity> type, double x, double y, double z) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			MobEntity m = type.create(w, SpawnReason.COMMAND);
			if (m == null) {
				return null;
			}
			m.setAiDisabled(true);
			m.setPersistent();
			m.setSilent(true);
			if ((Object) type == EntityType.ZOMBIE) {
				m.equipStack(EquipmentSlot.HEAD, new ItemStack(Items.IRON_HELMET));
			}
			m.refreshPositionAndAngles(x, y, z, 180f, 0f);
			w.spawnEntity(m);
			return m.getUuid();
		});
	}

	/** {health, x, y, z, vx, vy, vz} of an entity, or null when it is gone. */
	private static double[] state(TestServerContext server, UUID id) {
		return server.computeOnServer(srv -> {
			Entity e = id == null ? null : srv.getOverworld().getEntity(id);
			if (!(e instanceof LivingEntity l)) {
				return null;
			}
			return new double[] {l.getHealth(), l.getX(), l.getY(), l.getZ(), l.getVelocity().x, l.getVelocity().y, l.getVelocity().z};
		});
	}

	private static double health(TestServerContext server, UUID id) {
		double[] s = state(server, id);
		return s == null ? -1 : s[0];
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d %d 0 40", X, GROUND + 8, Z + 6));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, Z - 16, X + 16, Z + 16));
		context.waitTicks(30);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", X - 10, Z - 8, X + 10, GROUND, Z + 8));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", X - 10, GROUND + 1, Z - 8, X + 10, GROUND + 6, Z + 8));
		server.runCommand(String.format(Locale.ROOT, "kill @e[type=!player,x=%d,y=%d,z=%d,dx=20,dy=8,dz=16]", X - 10, GROUND, Z - 8));
		boolean peaceful = server.computeOnServer(srv -> srv.getOverworld().getDifficulty() == Difficulty.PEACEFUL);
		if (peaceful) {
			server.runCommand("difficulty easy"); // hostile mobs vanish in peaceful
		}
		context.waitTicks(10);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		BlockPos a = new BlockPos(X, GROUND + 1, Z);
		int before = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
		server.runCommand(String.format(Locale.ROOT, "deco place %s %d %d %d south", TYPE.id(), a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(20);
		Object[] b0 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var st = w.getBlockState(a);
			boolean ok = st.getBlock() instanceof TentBlock b && b.tentType() == TYPE;
			boolean ticker = ok && st.getBlockEntityTicker(w, Tents.BLOCK_ENTITY) != null;
			boolean otherTicker = Tents.block(TentTypes.DECO_LANTERN).getDefaultState().getBlockEntityTicker(w, Tents.BLOCK_ENTITY) != null
					|| Tents.block(TentTypes.ADVENTURER).getDefaultState().getBlockEntityTicker(w, Tents.BLOCK_ENTITY) != null;
			return new Object[] {ok, ok ? st.get(TentBlock.FACING).asString() : st.getBlock().toString(), w.getBlockEntity(a) != null,
					TentCollisions.count(w), ticker, otherTicker};
		});
		check.accept(Boolean.TRUE.equals(b0[0]), "pieu_defensif placed by /deco place (" + b0[1] + ")");
		check.accept("south".equals(b0[1]), "pieu_defensif faces south (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[2]), "pieu_defensif has its block entity");
		check.accept((Integer) b0[3] == before + 1, "pieu_defensif registered its collision boxes (" + b0[3] + ")");
		check.accept(Boolean.TRUE.equals(b0[4]), "pieu_defensif has a server ticker (its hazard)");
		check.accept(!Boolean.TRUE.equals(b0[5]), "the other props (lantern, adventurer tent) have no ticker");
		if (!Boolean.TRUE.equals(b0[0])) {
			finish(context, server, peaceful);
			return;
		}
		// the trunk collides (its first box), the point's place does not
		int[] hits = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			List<Box> boxes = TentCollisions.worldBoxes(TYPE, a, TentType.SOUTH);
			List<VoxelShape> out = new ArrayList<>();
			TentCollisions.append(out, null, boxes.get(0).expand(0.05), w);
			List<VoxelShape> tip = new ArrayList<>();
			TentCollisions.append(tip, null, new Box(a.getX() + 0.2, a.getY() + 0.05, a.getZ() + 0.5 - 2.2, a.getX() + 0.8, a.getY() + 1.9,
					a.getZ() + 0.5 - 1.6), w);
			return new int[] {out.size(), tip.size()};
		});
		check.accept(hits[0] >= 1, "pieu_defensif its trunk collides (" + hits[0] + " shape(s))");
		check.accept(hits[1] == 0, "pieu_defensif nothing collides at the point's place (" + hits[1] + ")");

		// the point (facing south: to the north, -z): a zombie at it, a villager at it; a zombie at the foot, against the front
		// face of the trunk's first box (z1 0.236 + half a zombie 0.3 + 0.02), one against the trunk's side at mid-length,
		// beside its second box (x 0.29 + 0.3 + 0.02, z -0.6): both nearly touch the trunk, a hazard box any longer or wider
		// than the point would catch them (NoAI mobs do not move: they stay where they are put)
		double px = a.getX() + 0.5, py = a.getY(), pz = a.getZ() + 0.5 - 1.9;
		UUID zPoint = spawn(server, EntityType.ZOMBIE, px + 0.12, py, pz);
		UUID zFoot = spawn(server, EntityType.ZOMBIE, px, py, a.getZ() + 0.5 + 0.556);
		UUID zSide = spawn(server, EntityType.ZOMBIE, px + 0.61, py, a.getZ() + 0.5 - 0.6);
		UUID villager = spawn(server, EntityType.VILLAGER, px - 0.12, py, pz);
		check.accept(zPoint != null && zFoot != null && zSide != null && villager != null, "the zombies and the villager are spawned");
		double h0 = health(server, zPoint);
		int firstHit = -1;
		double[] atHit = null;
		for (int t = 1; t <= 12 && firstHit < 0; t++) {
			context.waitTick();
			double[] s = state(server, zPoint);
			if (s != null && s[0] < h0 - 0.5) {
				firstHit = t;
				atHit = s;
			}
		}
		log.accept(String.format(Locale.ROOT, "stake: zombie at the point %.1f hp -> %s at tick %d, velocity %s", h0, atHit == null ? "-" : atHit[0],
				firstHit, atHit == null ? "-" : String.format(Locale.ROOT, "%.2f %.2f %.2f", atHit[4], atHit[5], atHit[6])));
		check.accept(firstHit > 0 && firstHit <= 10, "a zombie at the point is hurt within 10 ticks (tick " + firstHit + ")");
		check.accept(atHit != null && (atHit[6] < -0.05 || atHit[3] < pz - 0.05), String.format(Locale.ROOT,
				"the zombie is pushed outward along the point (north): velocity z %.2f, moved %.2f", atHit == null ? 0 : atHit[6],
				atHit == null ? 0 : atHit[3] - pz));
		if (atHit != null) {
			double h1 = atHit[0];
			context.waitTicks(14); // within the cooldown (20 ticks): no second hit
			double h2 = health(server, zPoint);
			check.accept(Math.abs(h2 - h1) < 0.01, String.format(Locale.ROOT, "not hurt again before the cooldown (%.1f -> %.1f)", h1, h2));
			// back to the point (in case the push moved it), then hurt again once the cooldown is over
			server.runOnServer(srv -> {
				Entity e = srv.getOverworld().getEntity(zPoint);
				if (e != null) {
					e.refreshPositionAndAngles(px + 0.12, py, pz, 180f, 0f);
					e.setVelocity(0, 0, 0);
				}
			});
			int second = -1;
			for (int t = 1; t <= 16 && second < 0; t++) {
				context.waitTick();
				if (health(server, zPoint) < h2 - 0.5) {
					second = t;
				}
			}
			check.accept(second > 0, "hurt again after the cooldown (" + (14 + second) + " ticks after the first hit)");
		}
		double hf = health(server, zFoot), hs = health(server, zSide), hv = health(server, villager);
		double vMax = server.computeOnServer(srv -> srv.getOverworld().getEntity(villager) instanceof LivingEntity l ? (double) l.getMaxHealth() : -1.0);
		check.accept(hf == 20.0, "a zombie at the stake's foot is not hurt (" + hf + ")");
		check.accept(hs == 20.0, "a zombie beside the trunk is not hurt (" + hs + ")");
		check.accept(hv > 0 && hv == vMax, "a villager at the point is never hurt (" + hv + " / " + vMax + ")");
		for (UUID id : new UUID[] {zPoint, zFoot, zSide, villager}) {
			server.runOnServer(srv -> {
				Entity e = id == null ? null : srv.getOverworld().getEntity(id);
				if (e != null) {
					e.discard();
				}
			});
		}

		// the test player in survival at the point: spared by default, hurt with damagePlayers = true (restored after). The
		// scenario gave it an infinite Resistance V (amplifier 4: every damage times 0), taken away meanwhile, given back
		boolean savedPlayers = server.computeOnServer(srv -> ConfigManager.server().stake.damagePlayers);
		StatusEffectInstance savedResistance = server.computeOnServer(srv -> {
			StatusEffectInstance r = srv.getPlayerManager().getPlayerList().get(0).getStatusEffect(StatusEffects.RESISTANCE);
			return r == null ? null : new StatusEffectInstance(r);
		});
		try {
			server.runOnServer(srv -> ConfigManager.server().stake.damagePlayers = false);
			server.runCommand("effect clear @a minecraft:resistance");
			server.runCommand("gamemode survival @a");
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 0", px, a.getY(), pz));
			server.runOnServer(srv -> {
				ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
				pl.setHealth(pl.getMaxHealth());
			});
			boolean resisting = server.computeOnServer(srv -> srv.getPlayerManager().getPlayerList().get(0).hasStatusEffect(StatusEffects.RESISTANCE));
			check.accept(!resisting, "the test player's Resistance is taken away for the stake's checks");
			// by default: over 25 ticks (5 looks of the stake) never hurt, never hit by a stake, never remembered by it
			double hp = 20.0, lowest = Double.MAX_VALUE;
			boolean struck = false;
			for (int t = 0; t < 25; t++) {
				context.waitTick();
				Object[] r = server.computeOnServer(srv -> {
					ServerWorld w = srv.getOverworld();
					ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
					DamageSource last = pl.getRecentDamageSource();
					boolean remembered = w.getBlockEntity(a) instanceof TentBlockEntity be && !be.hazardReady(pl.getUuid(), w.getTime(), Integer.MAX_VALUE);
					return new Object[] {(double) pl.getHealth(), last != null && last.isOf(StakeHazard.STAKE_DAMAGE) || remembered};
				});
				hp = (Double) r[0];
				lowest = Math.min(lowest, hp);
				struck |= Boolean.TRUE.equals(r[1]);
			}
			check.accept(lowest >= 19.99 && !struck, String.format(Locale.ROOT,
					"a survival player at the point is not hurt nor hit by the stake by default (lowest %.1f hp, hit %s)", lowest, struck));
			server.runOnServer(srv -> ConfigManager.server().stake.damagePlayers = true);
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 0", px, a.getY(), pz));
			double hurt = hp;
			boolean byStake = false;
			for (int t = 0; t < 14 && hurt >= hp - 0.5; t++) {
				context.waitTick();
				Object[] r = server.computeOnServer(srv -> {
					ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
					DamageSource last = pl.getRecentDamageSource();
					return new Object[] {(double) pl.getHealth(), last != null && last.isOf(StakeHazard.STAKE_DAMAGE)};
				});
				hurt = (Double) r[0];
				byStake = Boolean.TRUE.equals(r[1]);
			}
			check.accept(hurt < hp - 0.5 && byStake, String.format(Locale.ROOT,
					"with damagePlayers = true the player at the point is hurt by the stake (%.1f -> %.1f, stake damage %s)", hp, hurt, byStake));
		} finally {
			server.runOnServer(srv -> ConfigManager.server().stake.damagePlayers = savedPlayers);
			server.runOnServer(srv -> {
				ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
				pl.setHealth(pl.getMaxHealth());
				if (savedResistance != null) {
					pl.addStatusEffect(new StatusEffectInstance(savedResistance));
				}
			});
			server.runCommand("gamemode spectator @a");
		}

		// three stakes side by side, one block apart (the area check allows a row)
		for (int k = 0; k < 3; k++) {
			server.runCommand(String.format(Locale.ROOT, "deco place %s %d %d %d south", TYPE.id(), a.getX() + 3 + k, a.getY(), a.getZ()));
		}
		context.waitTicks(10);
		int row = server.computeOnServer(srv -> {
			int n = 0;
			for (int k = 0; k < 3; k++) {
				if (srv.getOverworld().getBlockState(a.add(3 + k, 0, 0)).getBlock() instanceof TentBlock b && b.tentType() == TYPE) {
					n++;
				}
			}
			return n;
		});
		check.accept(row == 3, "three stakes side by side one block apart all stand (" + row + " / 3)");
		// the reference's angle: from the side (east), a little in front, at about head height
		look(server, a.getX() + 0.5 + 4.6, a.getY() + 1.9, a.getZ() + 0.5 + 1.2, a.getX() + 2.0, a.getY() + 0.9, a.getZ() + 0.5 - 0.8);
		context.waitTicks(25);
		shot.accept("pieu_defensif_2_reference");
		look(server, a.getX() + 3.5, a.getY() + 2.4, a.getZ() + 0.5 + 5.0, a.getX() + 3.5, a.getY() + 0.8, a.getZ() + 0.5 - 0.8);
		context.waitTicks(12);
		shot.accept("pieu_defensif_3_rangee");

		// broken, a stake drops its item
		boolean dropped = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			w.breakBlock(a, true);
			Box near = new Box(a).expand(1.5);
			boolean found = false;
			for (ItemEntity item : w.getEntitiesByClass(ItemEntity.class, near, e -> true)) {
				found |= item.getStack().isOf(Tents.item(TYPE));
				item.discard();
			}
			return found;
		});
		context.waitTicks(5);
		check.accept(dropped, "a broken stake drops its item");
		for (int k = 0; k < 3; k++) {
			server.runCommand(String.format(Locale.ROOT, "deco remove %d %d %d", a.getX() + 3 + k, a.getY(), a.getZ()));
		}
		context.waitTicks(10);
		int left = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
		check.accept(left == before, "the stakes removed, their collision boxes forgotten (" + left + " prop(s) left)");
		finish(context, server, peaceful);
	}

	private static void finish(ClientGameTestContext context, TestServerContext server, boolean peaceful) {
		if (peaceful) {
			server.runCommand("difficulty peaceful");
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, Z - 16, X + 16, Z + 16));
	}
}
