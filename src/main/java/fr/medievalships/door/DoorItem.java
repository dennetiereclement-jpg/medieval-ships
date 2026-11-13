package fr.medievalships.door;

import java.util.Locale;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.ShapeContext;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.BlockItem;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.sound.SoundCategory;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.world.World;
import net.minecraft.world.event.GameEvent;

import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorType;

/**
 * The item of a door (one per model, {@code /give @p medievalships:<id>}): placed with its front towards the player,
 * its opening centred on the aimed cell (a door 2 wide: that cell and the one to its right; 4 wide: from -1 to +2),
 * only when every cell of the opening is free (air, grass, snow...) and nobody stands in it; otherwise a French message
 * and nothing is placed.
 */
public class DoorItem extends BlockItem {
	private final DoorType type;

	public DoorItem(DoorBlock block, Settings settings) {
		super(block, settings);
		this.type = block.doorType();
	}

	public DoorType doorType() {
		return type;
	}

	@Override
	public ActionResult place(ItemPlacementContext context) {
		World world = context.getWorld();
		PlayerEntity player = context.getPlayer();
		Direction facing = context.getHorizontalPlayerFacing().getOpposite();
		int quarter = facing.getHorizontalQuarterTurns();
		BlockPos target = context.getBlockPos();
		int[] c = DoorLayout.controllerFromTarget(target.getX(), target.getY(), target.getZ(), quarter, type.width());
		BlockPos controller = new BlockPos(c[0], c[1], c[2]);
		String problem = problem(world, controller, quarter, type, player);
		if (problem != null) {
			if (player != null && !world.isClient()) {
				player.sendMessage(Text.literal(problem).formatted(Formatting.RED), true);
			}
			return ActionResult.FAIL;
		}
		if (world instanceof ServerWorld sw) {
			place(sw, controller, quarter, type);
			BlockState state = world.getBlockState(controller);
			BlockSoundGroup group = state.getSoundGroup();
			world.playSound(null, controller, group.getPlaceSound(), SoundCategory.BLOCKS, (group.getVolume() + 1f) / 2f, group.getPitch() * 0.8f);
			world.emitGameEvent(player, GameEvent.BLOCK_PLACE, controller);
			context.getStack().decrementUnlessCreative(1, player);
		}
		return ActionResult.SUCCESS;
	}

	/**
	 * Why a door of this type cannot stand with its controller at {@code controller} facing {@code quarter} (French),
	 * or null when it can: every cell is inside the world, replaceable, modifiable by the player and free of entities.
	 */
	@Nullable
	public static String problem(World world, BlockPos controller, int quarter, DoorType type, @Nullable PlayerEntity player) {
		for (BlockPos p : DoorStructure.cells(controller, quarter, type)) {
			if (!world.isInBuildLimit(p)) {
				return "La porte sortirait des limites du monde.";
			}
			if (!DoorStructure.loaded(world, p)) {
				return "Une partie de la porte tomberait dans une zone non chargée.";
			}
			BlockState s = world.getBlockState(p);
			if (!s.isReplaceable()) {
				return String.format(Locale.ROOT, "Pas assez de place pour la %s (%d de large, %d de haut) : %s en %d %d %d.", type.nameFr(), type.width(),
						type.height(), s.getBlock().getName().getString(), p.getX(), p.getY(), p.getZ());
			}
			if (player != null && !world.canEntityModifyAt(player, p)) {
				return "Vous ne pouvez pas construire ici.";
			}
			BlockState closed = DoorStructure.stateOf(type, quarter, 0, 0, true);
			if (!world.canPlace(closed, p, ShapeContext.absent())) {
				return "Quelqu'un ou quelque chose se trouve dans l'ouverture de la porte.";
			}
		}
		return null;
	}

	/** Places a door (closed, solid) whose cells were checked: the controller first, then the parts. */
	public static void place(ServerWorld world, BlockPos controller, int quarter, DoorType type) {
		world.setBlockState(controller, DoorStructure.stateOf(type, quarter, 0, 0, true), Block.NOTIFY_ALL);
		for (int col = 0; col < type.width(); col++) {
			for (int row = 0; row < type.height(); row++) {
				if (col == 0 && row == 0) {
					continue;
				}
				int[] c = DoorLayout.cell(controller.getX(), controller.getY(), controller.getZ(), quarter, col, row);
				world.setBlockState(new BlockPos(c[0], c[1], c[2]), DoorStructure.stateOf(type, quarter, col, row, true), Block.NOTIFY_ALL);
			}
		}
		if (world.getBlockEntity(controller) instanceof DoorBlockEntity be) {
			be.placed(world);
		}
		DoorRegistry.get(world.getServer()).put(world, controller, type, "");
	}
}
