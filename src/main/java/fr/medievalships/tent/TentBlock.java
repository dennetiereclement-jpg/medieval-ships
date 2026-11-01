package fr.medievalships.tent;

import java.util.List;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.ShapeContext;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.item.ItemStack;
import net.minecraft.loot.context.LootWorldContext;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.EnumProperty;
import net.minecraft.state.property.Properties;
import net.minecraft.util.BlockMirror;
import net.minecraft.util.BlockRotation;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;

/**
 * The anchor block of a tent: invisible (the block entity renderer draws the whole tent), a thin floor for its own
 * collision (players walk through the tent freely; the posts and furniture collide through
 * {@link TentCollisions}), a full outline so it can be aimed at and broken; FACING = where the tent's front
 * points (towards the player who placed it). Breaking it drops the tent's item.
 */
public class TentBlock extends BlockWithEntity {
	public static final EnumProperty<Direction> FACING = Properties.HORIZONTAL_FACING;
	private static final VoxelShape FLOOR = Block.createCuboidShape(0, 0, 0, 16, 2, 16);
	private final TentType type;

	public TentBlock(TentType type, AbstractBlock.Settings settings) {
		super(settings);
		this.type = type;
		setDefaultState(getStateManager().getDefaultState().with(FACING, Direction.SOUTH));
	}

	public TentType tentType() {
		return type;
	}

	/** Quarter turns of the facing of a state: south 0, west 1, north 2, east 3 (see {@link TentType#rotate}). */
	public static int quarter(BlockState state) {
		return state.contains(FACING) ? state.get(FACING).getHorizontalQuarterTurns() : 0;
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		return AbstractBlock.createCodec(settings -> new TentBlock(type, settings));
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	@Nullable
	public BlockState getPlacementState(ItemPlacementContext ctx) {
		// the entrance faces the player who places the tent
		return getDefaultState().with(FACING, ctx.getHorizontalPlayerFacing().getOpposite());
	}

	@Override
	protected BlockState rotate(BlockState state, BlockRotation rotation) {
		return state.with(FACING, rotation.rotate(state.get(FACING)));
	}

	@Override
	protected BlockState mirror(BlockState state, BlockMirror mirror) {
		return state.rotate(mirror.getRotation(state.get(FACING)));
	}

	@Override
	protected BlockRenderType getRenderType(BlockState state) {
		return BlockRenderType.INVISIBLE;
	}

	@Override
	protected VoxelShape getOutlineShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return VoxelShapes.fullCube();
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return FLOOR;
	}

	@Override
	@Nullable
	public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
		return new TentBlockEntity(pos, state);
	}

	@Override
	public void onPlaced(World world, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack itemStack) {
		super.onPlaced(world, pos, state, placer, itemStack);
		TentCollisions.add(world, pos, type, quarter(state));
	}

	@Override
	protected void onStateReplaced(BlockState state, ServerWorld world, BlockPos pos, boolean moved) {
		TentCollisions.remove(world, pos);
		super.onStateReplaced(state, world, pos, moved);
	}

	@Override
	protected List<ItemStack> getDroppedStacks(BlockState state, LootWorldContext.Builder builder) {
		return List.of(new ItemStack(this));
	}
}
