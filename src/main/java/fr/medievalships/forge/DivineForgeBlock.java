package fr.medievalships.forge;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;
import fr.medievalships.tent.WorkshopBlock;

/**
 * The anchor block of the divine forge (1.34.0): a {@link WorkshopBlock} — drawing, collisions, placement, drops, and a
 * right click exactly like every workshop (the {@code WorkshopUseCallback} event with the profession
 * {@code forge_divine}, then the command of {@code workshopCommands.forge_divine}, else the short "no interface is
 * linked" message) — with its own block entity ({@link DivineForgeBlockEntity}: at rest or active) and its tickers (the
 * server ends an activity when it is due; the client plays the effects near the player).
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
}
