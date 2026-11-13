package fr.medievalships.door;

import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.ai.pathing.NavigationType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;

import fr.medievalships.entity.ShipPermissions;

/**
 * What every cell of a door does the same way, controller or part: the click (the same access checks on every cell),
 * the redstone next to any cell, who may break it, the pathfinding.
 */
final class DoorCells {
	private DoorCells() {
	}

	/** The mobs walk through an open door only (a closed one is a wall for them). */
	static boolean pathfind(BlockState state, NavigationType type) {
		return type != NavigationType.WATER && !state.get(DoorStructure.SOLID);
	}

	/** A click on any cell: the door's access decides (server); an orphan part removes itself. */
	static ActionResult use(BlockState state, World world, BlockPos pos, PlayerEntity player) {
		if (!(world instanceof ServerWorld sw)) {
			return ActionResult.SUCCESS;
		}
		DoorBlockEntity door = DoorStructure.door(world, pos);
		if (door == null) {
			if (state.getBlock() instanceof DoorPartBlock && DoorStructure.loaded(world, DoorStructure.expectedController(pos, state))) {
				world.setBlockState(pos, Blocks.AIR.getDefaultState());
			}
			return ActionResult.PASS;
		}
		door.click(sw, player);
		return ActionResult.SUCCESS;
	}

	/** Something changed next to a cell: the door looks at the redstone around all its cells again. */
	static void neighborUpdate(World world, BlockPos pos) {
		if (world instanceof ServerWorld sw) {
			DoorBlockEntity door = DoorStructure.door(world, pos);
			if (door != null) {
				door.updateRedstone(sw);
			}
		}
	}

	/**
	 * May this player break the door (any cell)? Always in creative mode or for an administrator; otherwise only a
	 * free door ({@code acces libre}): the others cannot be broken in survival.
	 */
	static boolean mayBreak(BlockView world, BlockPos pos, PlayerEntity player) {
		if (player.isCreative() || ShipPermissions.isAdmin(player)) {
			return true;
		}
		if (!(world instanceof World w)) {
			return true;
		}
		DoorBlockEntity door = DoorStructure.door(w, pos);
		return door == null || door.access().free();
	}
}
