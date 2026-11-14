package fr.medievalships.door;

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
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.entity.ai.pathing.NavigationType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.loot.context.LootWorldContext;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.state.StateManager;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.BlockMirror;
import net.minecraft.util.BlockRotation;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;
import net.minecraft.world.block.WireOrientation;

import fr.medievalships.core.DoorType;

/**
 * The controller block of a door ({@code medievalships:<id>}, one per model), at column 0 / row 0 of the opening
 * (bottom left seen from the front), with the door's block entity ({@link DoorBlockEntity}: state, settings, levers,
 * name). Invisible (the block entity renderer draws the whole door); the collision and outline of every cell are
 * the ones of {@link DoorStructure}; the click, the redstone, the breaking and the protections are shared with the
 * parts ({@link DoorPartBlock}) through {@link DoorCells}.
 */
public class DoorBlock extends BlockWithEntity {
	private final DoorType type;

	public DoorBlock(DoorType type, AbstractBlock.Settings settings) {
		super(settings);
		this.type = type;
		setDefaultState(getStateManager().getDefaultState().with(DoorStructure.FACING, Direction.SOUTH).with(DoorStructure.SOLID, true));
	}

	public DoorType doorType() {
		return type;
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		return AbstractBlock.createCodec(settings -> new DoorBlock(type, settings));
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(DoorStructure.FACING, DoorStructure.SOLID);
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

	@Override
	@Nullable
	public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
		return new DoorBlockEntity(pos, state);
	}

	/** A server ticker that returns at once while nothing happens (no movement, no linked lever, no timer). */
	@Override
	@Nullable
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(World world, BlockState state, BlockEntityType<T> blockEntityType) {
		if (world.isClient()) {
			return null;
		}
		return validateTicker(blockEntityType, Doors.BLOCK_ENTITY, DoorBlockEntity::serverTick);
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		return DoorCells.use(state, world, pos, player);
	}

	@Override
	protected ActionResult onUseWithItem(ItemStack stack, BlockState state, World world, BlockPos pos, PlayerEntity player, Hand hand, BlockHitResult hit) {
		return DoorCells.useWithItem(stack, state, world, pos, player, hand);
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
		// the controller's own item comes from its drops (afterBreak): only the other cells are removed here
		if (world instanceof ServerWorld sw) {
			DoorStructure.removeDoor(sw, pos, state, pos, false);
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
		return List.of(new ItemStack(this));
	}
}
