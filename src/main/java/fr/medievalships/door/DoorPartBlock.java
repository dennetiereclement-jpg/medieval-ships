package fr.medievalships.door;

import java.util.List;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.block.ShapeContext;
import net.minecraft.entity.ai.pathing.NavigationType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.loot.context.LootWorldContext;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.state.StateManager;
import net.minecraft.util.ActionResult;
import net.minecraft.util.BlockMirror;
import net.minecraft.util.BlockRotation;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.random.Random;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;
import net.minecraft.world.WorldView;
import net.minecraft.world.block.WireOrientation;
import net.minecraft.world.tick.ScheduledTickView;

/**
 * The block of every cell of a door but its controller ({@code medievalships:porte_partie}, shared by the ten doors, no
 * block entity): FACING, its column and row in the opening, SOLID. Invisible; it answers the click and the redstone
 * like the controller, and a part whose controller is gone removes itself (never an orphan: on a neighbour's update,
 * on a click, when broken).
 */
public class DoorPartBlock extends Block {
	public static final MapCodec<DoorPartBlock> CODEC = createCodec(DoorPartBlock::new);

	public DoorPartBlock(AbstractBlock.Settings settings) {
		super(settings);
		setDefaultState(getStateManager().getDefaultState().with(DoorStructure.FACING, Direction.SOUTH).with(DoorStructure.COL, 0)
				.with(DoorStructure.ROW, 1).with(DoorStructure.SOLID, true));
	}

	@Override
	protected MapCodec<? extends Block> getCodec() {
		return CODEC;
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(DoorStructure.FACING, DoorStructure.COL, DoorStructure.ROW, DoorStructure.SOLID);
	}

	@Override
	protected BlockState rotate(BlockState state, BlockRotation rotation) {
		return state.with(DoorStructure.FACING, rotation.rotate(state.get(DoorStructure.FACING)));
	}

	@Override
	protected BlockState mirror(BlockState state, BlockMirror mirror) {
		return state.rotate(mirror.getRotation(state.get(DoorStructure.FACING)));
	}

	@Override
	protected BlockRenderType getRenderType(BlockState state) {
		return BlockRenderType.INVISIBLE;
	}

	@Override
	protected VoxelShape getOutlineShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return DoorStructure.outline(state);
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return DoorStructure.collision(state);
	}

	@Override
	protected boolean canPathfindThrough(BlockState state, NavigationType type) {
		return DoorCells.pathfind(state, type);
	}

	/** A part whose controller is gone (or no longer owns it) disappears with its neighbour's update. */
	@Override
	protected BlockState getStateForNeighborUpdate(BlockState state, WorldView world, ScheduledTickView tickView, BlockPos pos, Direction direction,
			BlockPos neighborPos, BlockState neighborState, Random random) {
		BlockPos c = DoorStructure.expectedController(pos, state);
		if (DoorStructure.loaded(world, c) && !DoorStructure.owns(world.getBlockState(c), state)) {
			return Blocks.AIR.getDefaultState();
		}
		return state;
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		return DoorCells.use(state, world, pos, player);
	}

	@Override
	protected void neighborUpdate(BlockState state, World world, BlockPos pos, Block sourceBlock, @Nullable WireOrientation wireOrientation, boolean notify) {
		DoorCells.neighborUpdate(world, pos);
	}

	@Override
	protected float calcBlockBreakingDelta(BlockState state, PlayerEntity player, BlockView world, BlockPos pos) {
		return DoorCells.mayBreak(world, pos, player) ? super.calcBlockBreakingDelta(state, player, world, pos) : 0f;
	}

	@Override
	public BlockState onBreak(World world, BlockPos pos, BlockState state, PlayerEntity player) {
		// the whole door goes; out of creative mode, its item drops at the controller (a part drops nothing itself)
		if (world instanceof ServerWorld sw) {
			DoorStructure.removeDoor(sw, pos, state, pos, !player.isCreative());
		}
		return super.onBreak(world, pos, state, player);
	}

	@Override
	protected void onStateReplaced(BlockState state, ServerWorld world, BlockPos pos, boolean moved) {
		DoorStructure.removeDoor(world, pos, state, null, false);
		super.onStateReplaced(state, world, pos, moved);
	}

	@Override
	protected List<ItemStack> getDroppedStacks(BlockState state, LootWorldContext.Builder builder) {
		return List.of();
	}

	@Override
	protected ItemStack getPickStack(WorldView world, BlockPos pos, BlockState state, boolean includeData) {
		BlockPos c = DoorStructure.controllerOf(world, pos);
		if (c != null && world.getBlockState(c).getBlock() instanceof DoorBlock d) {
			return new ItemStack(d);
		}
		return ItemStack.EMPTY;
	}
}
