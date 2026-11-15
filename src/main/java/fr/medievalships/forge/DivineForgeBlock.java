package fr.medievalships.forge;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;
import fr.medievalships.tent.WorkshopBlock;
import fr.medievalships.tent.WorkshopInteraction;

/**
 * The anchor block of the divine forge (1.34.0): a {@link WorkshopBlock} (drawing, collisions, placement, drops, the
 * workshops' right-click hook) with its own block entity ({@link DivineForgeBlockEntity}: the crafting state) and its
 * tickers (the server completes a crafting when it is due; the client plays the effects near the player). A right click
 * first hands the player the results the forge kept for them, then goes through {@link WorkshopInteraction} like every
 * workshop (the {@code WorkshopUseCallback} event, the command of {@code workshopCommands.forge_divine}), and opens the
 * forge's own interface when neither handled it.
 */
public class DivineForgeBlock extends WorkshopBlock {
	public DivineForgeBlock(TentType type, AbstractBlock.Settings settings) {
		super(type, settings);
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		TentType type = tentType();
		return AbstractBlock.createCodec(settings -> new DivineForgeBlock(type, settings));
	}

	@Override
	@Nullable
	public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
		return new DivineForgeBlockEntity(pos, state);
	}

	@Override
	@Nullable
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(World world, BlockState state, BlockEntityType<T> blockEntityType) {
		BlockEntityTicker<DivineForgeBlockEntity> ticker = world.isClient() ? DivineForgeBlockEntity::clientTick : DivineForgeBlockEntity::serverTick;
		return validateTicker(blockEntityType, DivineForge.BLOCK_ENTITY, ticker);
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		if (player.isSpectator()) {
			return ActionResult.PASS;
		}
		if (world instanceof ServerWorld serverWorld && player instanceof ServerPlayerEntity serverPlayer) {
			DivineForgeBlockEntity forge = world.getBlockEntity(pos) instanceof DivineForgeBlockEntity f ? f : null;
			if (forge != null) {
				forge.deliverPending(serverPlayer);
			}
			return WorkshopInteraction.use(serverPlayer, serverWorld, pos, tentType(), () -> {
				if (forge != null && !forge.isRemoved()) {
					ForgeRecipes.open(serverPlayer, forge);
				}
			});
		}
		return ActionResult.SUCCESS;
	}
}
