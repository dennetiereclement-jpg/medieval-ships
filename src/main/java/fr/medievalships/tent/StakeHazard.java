package fr.medievalships.tent;

import java.util.List;

import net.minecraft.block.BlockState;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.damage.DamageType;
import net.minecraft.entity.mob.Monster;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.StakeSettings;
import fr.medievalships.core.TentType;
import fr.medievalships.data.ConfigManager;

/**
 * The server ticker of the props that hurt (1.24.0: the defensive stake's point, {@link TentType.Hazard}). Registered by
 * {@link TentBlock#getTicker} only for a type with a hazard and only on the server: every other prop stays tick-free.
 * Every {@link #PERIOD} ticks (staggered by position so a row of stakes does not work on the same tick) it asks the
 * world for the living entities inside the small hazard box (no area scan), then hurts each hostile mob
 * ({@link Monster}) found there with the damage type {@code medievalships:stake} and pushes it outward along the point;
 * the same entity is not hit again before the cooldown (a transient map in the block entity, never saved). Players only
 * when {@link StakeSettings#damagePlayers} (never in creative or spectator mode); villagers, animals, NPCs never. The
 * values come from the server config ({@link StakeSettings}), which overrides the model's. No client class here.
 */
public final class StakeHazard {
	/** The damage type of a stake (data/medievalships/damage_type/stake.json; death message "death.attack.medievalships.stake"). */
	public static final RegistryKey<DamageType> STAKE_DAMAGE = RegistryKey.of(RegistryKeys.DAMAGE_TYPE, MedievalShips.id("stake"));
	/** Ticks between two looks at the point. */
	public static final int PERIOD = 5;

	private StakeHazard() {
	}

	/** The block entity ticker (server only). */
	public static void tick(World world, BlockPos pos, BlockState state, TentBlockEntity be) {
		if (!(world instanceof ServerWorld sw)) {
			return;
		}
		long now = sw.getTime();
		if (Math.floorMod(now + phase(pos), PERIOD) != 0) {
			return;
		}
		TentType type = be.tentType();
		TentType.Hazard h = type == null ? null : type.hazard(TentBlock.quarter(state));
		if (h == null) {
			return;
		}
		StakeSettings s = ConfigManager.server().stake;
		be.pruneHazardHits(now, s.cooldownTicks);
		Box box = worldBox(h, pos);
		List<LivingEntity> touching = sw.getEntitiesByClass(LivingEntity.class, box, e -> hurts(e, s.damagePlayers));
		for (LivingEntity e : touching) {
			if (!be.hazardReady(e.getUuid(), now, s.cooldownTicks)) {
				continue;
			}
			be.hazardHit(e.getUuid(), now);
			e.damage(sw, source(sw), (float) s.damage);
			if (s.knockback > 0 && e.isAlive()) {
				// takeKnockback pushes away from (x, z): towards the point's direction, outward
				e.takeKnockback(s.knockback, -h.dirX(), -h.dirZ());
			}
		}
	}

	/** A position's phase in the period (a row of stakes spreads over the ticks). */
	public static int phase(BlockPos pos) {
		return Math.floorMod(pos.getX() * 31 + pos.getZ() * 17 + pos.getY() * 7, PERIOD);
	}

	/** The hazard box of a prop anchored at pos, in world coordinates (the hazard already turned to the facing). */
	public static Box worldBox(TentType.Hazard h, BlockPos pos) {
		double cx = pos.getX() + 0.5, cy = pos.getY(), cz = pos.getZ() + 0.5;
		TentType.Box b = h.box();
		return new Box(cx + b.x0(), cy + b.y0(), cz + b.z0(), cx + b.x1(), cy + b.y1(), cz + b.z1());
	}

	/** Does the point hurt this entity? Living hostile mobs; players only when allowed, never creative or spectator ones. */
	public static boolean hurts(LivingEntity e, boolean damagePlayers) {
		if (!e.isAlive() || e.isSpectator()) {
			return false;
		}
		if (e instanceof PlayerEntity p) {
			return damagePlayers && !p.isCreative() && !p.getAbilities().invulnerable;
		}
		return e instanceof Monster;
	}

	/** The stake's damage source (the mod's damage type; the cactus' if a data pack removed it). */
	public static DamageSource source(ServerWorld world) {
		var registry = world.getRegistryManager().getOrThrow(RegistryKeys.DAMAGE_TYPE);
		RegistryEntry<DamageType> entry = registry.getOptional(STAKE_DAMAGE).map(e -> (RegistryEntry<DamageType>) e).orElse(null);
		return entry != null ? new DamageSource(entry) : world.getDamageSources().cactus();
	}
}
