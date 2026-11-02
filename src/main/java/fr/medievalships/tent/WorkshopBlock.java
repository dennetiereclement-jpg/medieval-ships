package fr.medievalships.tent;

import java.util.List;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.ParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;

/**
 * The anchor block of a crafting workshop: a {@link TentBlock} (same drawing, collisions, placement and drops) that
 * also gives off the particles of its JSON ({@link TentType#particles}: the forge's smoke, the altar's enchanting
 * glyphs...), client-side only, at the vanilla random display ticks of the block (no ticker, nothing on the server).
 * Right-clicking it (1.22.0) fires the generic hook of {@link WorkshopInteraction} (an event for other mods, a command
 * from the server config, else a short message): the mod itself has no recipes, no crafting interface, no progression.
 */
public class WorkshopBlock extends TentBlock {
	public WorkshopBlock(TentType type, AbstractBlock.Settings settings) {
		super(type, settings);
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		TentType type = tentType();
		return AbstractBlock.createCodec(settings -> new WorkshopBlock(type, settings));
	}

	/**
	 * A right click (1.22.0): on the server, {@link WorkshopInteraction#use} (the {@code WorkshopUseCallback} event, then
	 * the command configured for the profession, else a short message); on the client, just the arm swing. Spectators:
	 * nothing.
	 */
	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		if (player.isSpectator()) {
			return ActionResult.PASS;
		}
		if (world instanceof ServerWorld serverWorld && player instanceof ServerPlayerEntity serverPlayer) {
			return WorkshopInteraction.use(serverPlayer, serverWorld, pos, tentType());
		}
		return ActionResult.SUCCESS;
	}

	/**
	 * The same with an item in hand (like a crafting table: the item is not used on the workshop; sneaking places it as
	 * usual). Only for the main hand, so that one click fires the hook once.
	 */
	@Override
	protected ActionResult onUseWithItem(ItemStack stack, BlockState state, World world, BlockPos pos, PlayerEntity player, Hand hand,
			BlockHitResult hit) {
		return hand == Hand.MAIN_HAND ? onUse(state, world, pos, player, hit) : ActionResult.PASS;
	}

	@Override
	public void randomDisplayTick(BlockState state, World world, BlockPos pos, Random random) {
		List<TentType.Particle> sources = tentType().particles(quarter(state));
		if (sources.isEmpty()) {
			return;
		}
		double cx = pos.getX() + 0.5, cy = pos.getY(), cz = pos.getZ() + 0.5;
		for (TentType.Particle p : sources) {
			if (random.nextDouble() >= p.chance()) {
				continue;
			}
			ParticleEffect effect = effect(p.type());
			if (effect == null) {
				continue;
			}
			for (int i = 0; i < p.count(); i++) {
				double x = cx + p.x() + (random.nextDouble() - 0.5) * 0.15;
				double y = cy + p.y() + (random.nextDouble() - 0.5) * 0.1;
				double z = cz + p.z() + (random.nextDouble() - 0.5) * 0.15;
				double[] v = velocity(p.type(), random);
				world.addParticleClient(effect, x, y, z, v[0], v[1], v[2]);
			}
		}
	}

	/** The vanilla particle of a JSON type name ({@link TentType#PARTICLE_TYPES}), or null for an unknown one. */
	@Nullable
	static ParticleEffect effect(String type) {
		return switch (type) {
			case "flame" -> ParticleTypes.FLAME;
			case "small_flame" -> ParticleTypes.SMALL_FLAME;
			case "smoke" -> ParticleTypes.SMOKE;
			case "campfire_smoke" -> ParticleTypes.CAMPFIRE_COSY_SMOKE;
			case "enchant" -> ParticleTypes.ENCHANT;
			case "witch" -> ParticleTypes.WITCH;
			case "portal" -> ParticleTypes.PORTAL;
			case "end_rod" -> ParticleTypes.END_ROD;
			case "electric_spark" -> ParticleTypes.ELECTRIC_SPARK;
			case "glow" -> ParticleTypes.GLOW;
			default -> null;
		};
	}

	/** A small velocity suited to the particle: smoke rises, glyphs and portal motes drift, flames stay put. */
	private static double[] velocity(String type, Random random) {
		return switch (type) {
			case "smoke" -> new double[] {0, 0.015, 0};
			case "campfire_smoke" -> new double[] {0, 0.05, 0};
			// these two move by their velocity as an offset towards their start point (like the enchanting table's glyphs)
			case "enchant", "portal" -> new double[] {(random.nextDouble() - 0.5) * 0.8, random.nextDouble() * 0.5, (random.nextDouble() - 0.5) * 0.8};
			case "end_rod", "glow", "witch", "electric_spark" ->
					new double[] {(random.nextDouble() - 0.5) * 0.02, 0.01 + random.nextDouble() * 0.01, (random.nextDouble() - 0.5) * 0.02};
			default -> new double[] {0, 0, 0};
		};
	}
}
