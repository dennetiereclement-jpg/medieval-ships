package fr.medievalships.door;

import java.util.ArrayList;
import java.util.List;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.state.property.BooleanProperty;
import net.minecraft.state.property.EnumProperty;
import net.minecraft.state.property.IntProperty;
import net.minecraft.state.property.Properties;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkSectionPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.World;
import net.minecraft.world.WorldView;

import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorType;

/**
 * The shape of a door in the world, shared by its controller block ({@link DoorBlock}, column 0 / row 0) and its
 * parts ({@link DoorPartBlock}, every other cell): the block state properties, the collision and outline shapes, the
 * cells of a door, finding the controller from any cell, and removing a whole door (never an orphan part).
 */
public final class DoorStructure {
	/** Where the front of the door faces (towards the player who placed it). */
	public static final EnumProperty<Direction> FACING = Properties.HORIZONTAL_FACING;
	/** The door blocks the passage (closed, or opening and not yet half open). */
	public static final BooleanProperty SOLID = BooleanProperty.of("solid");
	/** Column (0 = left seen from the front) and row (0 = bottom) of a part. */
	public static final IntProperty COL = IntProperty.of("col", 0, 3);
	public static final IntProperty ROW = IntProperty.of("row", 0, 5);

	/** A thin slab (4/16) in the middle of the thickness: the collision of a closed cell and the outline of every cell. */
	private static final VoxelShape SLAB_Z = Block.createCuboidShape(0, 0, 6, 16, 16, 10);
	private static final VoxelShape SLAB_X = Block.createCuboidShape(6, 0, 0, 10, 16, 16);

	/** Set while a whole door is being removed: the removal of its own cells does not start it again. */
	private static boolean removing;

	private DoorStructure() {
	}

	public static int quarter(BlockState state) {
		return state.contains(FACING) ? state.get(FACING).getHorizontalQuarterTurns() : 0;
	}

	public static Direction facing(int quarter) {
		return Direction.fromHorizontalQuarterTurns(quarter);
	}

	/** The outline of a cell: the slab, open or not (to aim at the door and close it again). */
	public static VoxelShape outline(BlockState state) {
		return state.get(FACING).getAxis() == Direction.Axis.Z ? SLAB_Z : SLAB_X;
	}

	/** The collision of a cell: the slab while solid, nothing once the door is open. */
	public static VoxelShape collision(BlockState state) {
		return state.get(SOLID) ? outline(state) : VoxelShapes.empty();
	}

	static BlockPos pos(int[] c) {
		return new BlockPos(c[0], c[1], c[2]);
	}

	/** Every cell of a door whose controller is at {@code controller}, column by column, bottom up. */
	public static List<BlockPos> cells(BlockPos controller, int quarter, DoorType type) {
		List<BlockPos> out = new ArrayList<>(type.cells());
		for (int[] c : DoorLayout.cells(controller.getX(), controller.getY(), controller.getZ(), quarter, type.width(), type.height())) {
			out.add(new BlockPos(c[0], c[1], c[2]));
		}
		return out;
	}

	/** The state of the cell (col, row) of a door: the controller block's for (0, 0), the shared part's otherwise. */
	public static BlockState stateOf(DoorType type, int quarter, int col, int row, boolean solid) {
		Direction f = facing(quarter);
		if (col == 0 && row == 0) {
			return Doors.block(type).getDefaultState().with(FACING, f).with(SOLID, solid);
		}
		return Doors.PART.getDefaultState().with(FACING, f).with(COL, col).with(ROW, row).with(SOLID, solid);
	}

	static boolean loaded(WorldView world, BlockPos pos) {
		return world.isChunkLoaded(ChunkSectionPos.getSectionCoord(pos.getX()), ChunkSectionPos.getSectionCoord(pos.getZ()));
	}

	/**
	 * The controller of the door a block belongs to (the block itself for a controller), or null when it is no door
	 * cell or a part whose controller is missing (an orphan) or not loaded.
	 */
	@Nullable
	public static BlockPos controllerOf(WorldView world, BlockPos pos) {
		BlockState s = world.getBlockState(pos);
		if (s.getBlock() instanceof DoorBlock) {
			return pos;
		}
		if (s.getBlock() instanceof DoorPartBlock) {
			BlockPos c = expectedController(pos, s);
			if (!loaded(world, c)) {
				return null;
			}
			return owns(world.getBlockState(c), s) ? c : null;
		}
		return null;
	}

	/** Where the controller of a part should be. */
	static BlockPos expectedController(BlockPos part, BlockState s) {
		return pos(DoorLayout.controllerFromCell(part.getX(), part.getY(), part.getZ(), quarter(s), s.get(COL), s.get(ROW)));
	}

	/** Is {@code controller} the controller of a door that has a part in this state (same facing, the cell inside its opening)? */
	static boolean owns(BlockState controller, BlockState part) {
		if (!(controller.getBlock() instanceof DoorBlock d) || controller.get(FACING) != part.get(FACING)) {
			return false;
		}
		DoorType t = d.doorType();
		return part.get(COL) < t.width() && part.get(ROW) < t.height();
	}

	/** The door's block entity at a cell (controller or part), or null. */
	@Nullable
	public static DoorBlockEntity door(World world, BlockPos pos) {
		BlockPos c = controllerOf(world, pos);
		return c != null && world.getBlockEntity(c) instanceof DoorBlockEntity be ? be : null;
	}

	/** A cell of this door in the world: the controller block, or a part in its place with the same facing. */
	static boolean isCell(BlockState s, DoorType type, int quarter, int col, int row) {
		if (col == 0 && row == 0) {
			return s.getBlock() instanceof DoorBlock d && d.doorType() == type && quarter(s) == quarter;
		}
		return s.getBlock() instanceof DoorPartBlock && quarter(s) == quarter && s.get(COL) == col && s.get(ROW) == row;
	}

	/**
	 * Removes a whole door after one of its cells was removed or is being broken: every other cell still in place goes
	 * (no drops), except {@code keep} (the cell a player is breaking, left to the game); {@code dropItem}: one door item
	 * is dropped at the controller. {@code removed} is the state the removed (or broken) cell had. The door leaves the
	 * registry of names. Never runs again for the cells it removes itself.
	 */
	public static void removeDoor(ServerWorld world, BlockPos at, BlockState removed, @Nullable BlockPos keep, boolean dropItem) {
		if (removing) {
			return;
		}
		BlockPos controller;
		DoorType type;
		int quarter = quarter(removed);
		if (removed.getBlock() instanceof DoorBlock d) {
			controller = at;
			type = d.doorType();
		} else if (removed.getBlock() instanceof DoorPartBlock) {
			controller = expectedController(at, removed);
			if (!loaded(world, controller)) {
				return;
			}
			BlockState cs = world.getBlockState(controller);
			if (!(cs.getBlock() instanceof DoorBlock d) || quarter(cs) != quarter) {
				return; // already gone: nothing else to remove (the parts left go with their neighbours' updates)
			}
			type = d.doorType();
		} else {
			return;
		}
		removing = true;
		try {
			for (int[] c : DoorLayout.cells(controller.getX(), controller.getY(), controller.getZ(), quarter, type.width(), type.height())) {
				BlockPos p = new BlockPos(c[0], c[1], c[2]);
				if (p.equals(keep) || !loaded(world, p)) {
					continue;
				}
				if (isCell(world.getBlockState(p), type, quarter, c[3], c[4])) {
					world.setBlockState(p, Blocks.AIR.getDefaultState(), Block.NOTIFY_ALL | Block.SKIP_DROPS);
				}
			}
			if (dropItem) {
				Block.dropStack(world, controller, new ItemStack(Doors.item(type)));
			}
			DoorRegistry.get(world.getServer()).remove(world, controller);
		} finally {
			removing = false;
		}
	}

	/** The box of the cells of a door (to find the entities in its opening). */
	public static Box openingBox(BlockPos controller, int quarter, DoorType type) {
		double[] b = DoorLayout.worldBox(controller.getX(), controller.getY(), controller.getZ(), quarter, type.width(), -type.width() / 2.0, 0, -0.5,
				type.width() / 2.0, type.height(), 0.5);
		return new Box(b[0], b[1], b[2], b[3], b[4], b[5]);
	}

	/** The box a closing door may hit: its opening and the quarter circles its leaves sweep. */
	public static Box sweptBox(BlockPos controller, int quarter, DoorType type, boolean backward) {
		double[] b = DoorLayout.sweptWorld(type, controller.getX(), controller.getY(), controller.getZ(), quarter, backward);
		return new Box(b[0], b[1], b[2], b[3], b[4], b[5]);
	}
}
