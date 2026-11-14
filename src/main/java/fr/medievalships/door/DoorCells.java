package fr.medievalships.door;

import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.ai.pathing.NavigationType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;

import fr.medievalships.entity.ShipPermissions;

/**
 * What every cell of a door does the same way, controller or part: the click (the same access checks on every cell),
 * a key in hand (1.32.0), the redstone next to any cell, who may break it, the pathfinding.
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

	/**
	 * A click with an item in hand (not sneaking: sneaking with a key, the game uses the item instead, see
	 * {@link KeyItem#useOnBlock}): a key or the master key makes its gesture on the door ({@link DoorBlockEntity#useKey});
	 * any other item, the ordinary click ({@link #use}).
	 */
	static ActionResult useWithItem(ItemStack stack, BlockState state, World world, BlockPos pos, PlayerEntity player, Hand hand) {
		if (!(stack.getItem() instanceof KeyItem)) {
			return ActionResult.PASS_TO_DEFAULT_BLOCK_ACTION;
		}
		if (!(world instanceof ServerWorld sw)) {
			return ActionResult.SUCCESS;
		}
		DoorBlockEntity door = DoorStructure.door(world, pos);
		if (door == null) {
			return ActionResult.PASS_TO_DEFAULT_BLOCK_ACTION; // an orphan part: the ordinary click removes it
		}
		door.useKey(sw, player, stack, player.shouldCancelInteraction());
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
