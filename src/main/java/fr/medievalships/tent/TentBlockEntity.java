package fr.medievalships.tent;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.TentType;

/**
 * The block entity of a tent's anchor block: no ticker, no data of its own (the type comes from the block, the
 * facing from the block state); it only exists so the client can draw the tent (TentBlockEntityRenderer) and so
 * the collision registry is told when the tent's chunk loads and unloads (block entity load / unload events).
 * {@link CannonBlockEntity} (the cannon's, its own type) extends it with a persisted state.
 */
public class TentBlockEntity extends BlockEntity {
	public TentBlockEntity(BlockPos pos, BlockState state) {
		this(Tents.BLOCK_ENTITY, pos, state);
	}

	/** For the subclasses with their own block entity type (the cannon's). */
	protected TentBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state) {
		super(type, pos, state);
	}

	public TentType tentType() {
		return getCachedState().getBlock() instanceof TentBlock tent ? tent.tentType() : null;
	}

	public int quarter() {
		return TentBlock.quarter(getCachedState());
	}
}
