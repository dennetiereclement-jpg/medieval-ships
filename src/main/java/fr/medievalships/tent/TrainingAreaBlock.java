package fr.medievalships.tent;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;
import fr.medievalships.training.TrainingTargets;

/**
 * The anchor block of a training area (1.19.0): a {@link TentBlock} (same drawing, collisions, placement and drops)
 * registered unbreakable in survival and adventure (hardness -1, the blast resistance of bedrock, pistons blocked:
 * see {@link Tents#register}; an admin removes it in creative mode or with {@code /tent remove}), which also keeps its
 * training targets ({@link TrainingTargets}): asked for when it is placed, discarded when it is broken or replaced.
 */
public class TrainingAreaBlock extends TentBlock {
	public TrainingAreaBlock(TentType type, AbstractBlock.Settings settings) {
		super(type, settings);
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		TentType type = tentType();
		return AbstractBlock.createCodec(settings -> new TrainingAreaBlock(type, settings));
	}

	@Override
	public void onPlaced(World world, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack itemStack) {
		super.onPlaced(world, pos, state, placer, itemStack);
		if (world instanceof ServerWorld sw && tentType().hasTargets()) {
			TrainingTargets.request(sw, pos);
		}
	}

	@Override
	protected void onStateReplaced(BlockState state, ServerWorld world, BlockPos pos, boolean moved) {
		if (tentType().hasTargets()) {
			TrainingTargets.removeAll(world, pos, tentType(), quarter(state));
		}
		super.onStateReplaced(state, world, pos, moved);
	}
}
