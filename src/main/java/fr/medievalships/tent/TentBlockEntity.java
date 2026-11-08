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

	// ---- 1.25.0: the hazard's per-entity cooldown (StakeHazard), transient: never saved, created on the first hit

	/** Last hit (game time) of each entity the prop's hazard hurt; null until the first hit (most props: never). */
	private java.util.Map<java.util.UUID, Long> hazardHits;

	/** May the hazard hit this entity now (no hit within the last {@code cooldown} ticks)? */
	public boolean hazardReady(java.util.UUID id, long now, int cooldown) {
		Long last = hazardHits == null ? null : hazardHits.get(id);
		return last == null || now - last >= cooldown || now < last;
	}

	/** Remembers that the hazard hit this entity now. */
	public void hazardHit(java.util.UUID id, long now) {
		if (hazardHits == null) {
			hazardHits = new java.util.HashMap<>();
		}
		hazardHits.put(id, now);
	}

	/** Forgets the hits older than the cooldown (the map stays as small as the crowd at the point). */
	public void pruneHazardHits(long now, int cooldown) {
		if (hazardHits != null) {
			hazardHits.values().removeIf(t -> now - t >= cooldown || now < t);
		}
	}

	/** How many entities are remembered (tests). */
	public int hazardMemory() {
		return hazardHits == null ? 0 : hazardHits.size();
	}
}
