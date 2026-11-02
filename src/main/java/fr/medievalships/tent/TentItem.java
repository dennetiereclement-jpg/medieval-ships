package fr.medievalships.tent;

import java.util.Locale;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.BlockState;
import net.minecraft.block.PlantBlock;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.BlockItem;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;

/**
 * The item of a tent: a block item whose placement first checks that the tent's whole extent (turned to the
 * facing the block will get) is free — air, replaceable plants, snow, flowers — and stands on ground solid enough;
 * otherwise a French message and nothing is placed. Never overwrites anything: the plants in the extent stay.
 */
public class TentItem extends BlockItem {
	private final TentType type;
	/** Share of the footprint's columns that must have ground under them. */
	private static final double GROUND_SHARE = 0.6;

	public TentItem(TentBlock block, Settings settings) {
		super(block, settings);
		this.type = block.tentType();
	}

	public TentType tentType() {
		return type;
	}

	@Override
	public ActionResult place(ItemPlacementContext context) {
		BlockPos pos = context.getBlockPos();
		Direction facing = context.getHorizontalPlayerFacing().getOpposite();
		String problem = freeAreaProblem(context.getWorld(), pos, type, facing.getHorizontalQuarterTurns());
		if (problem != null) {
			PlayerEntity player = context.getPlayer();
			if (player != null && !context.getWorld().isClient()) {
				player.sendMessage(Text.literal(problem).formatted(Formatting.RED), true);
			}
			return ActionResult.FAIL;
		}
		return super.place(context);
	}

	/**
	 * Why the tent cannot stand with its anchor at {@code pos} facing {@code quarter} (French), or null when it can:
	 * every block of its extent is air or something a tent may cover, and most of its footprint has ground under it.
	 */
	@Nullable
	public static String freeAreaProblem(World world, BlockPos pos, TentType type, int quarter) {
		TentType.Box e = type.extent(quarter);
		int x0 = pos.getX() + (int) Math.floor(e.x0() + 0.5), x1 = pos.getX() + (int) Math.ceil(e.x1() + 0.5) - 1;
		int z0 = pos.getZ() + (int) Math.floor(e.z0() + 0.5), z1 = pos.getZ() + (int) Math.ceil(e.z1() + 0.5) - 1;
		int y0 = pos.getY(), y1 = pos.getY() + (int) Math.ceil(e.y1()) - 1;
		int columns = 0, grounded = 0;
		BlockPos.Mutable m = new BlockPos.Mutable();
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				for (int y = y0; y <= y1; y++) {
					BlockState s = world.getBlockState(m.set(x, y, z));
					if (!coverable(s) && !m.equals(pos)) {
						return String.format(Locale.ROOT, "Pas assez de place pour %s (%d x %d blocs, %d de haut) : %s en %d %d %d.",
								type.isWorkshop() ? "l'atelier" : type.isCannon() ? "le canon" : type.isTraining() ? "l'aire d'entraînement"
										: type.isDecoration() ? "la décoration" : "la tente", x1 - x0 + 1, z1 - z0 + 1, y1 - y0 + 1, s.getBlock().getName().getString(),
								x, y, z);
					}
				}
				columns++;
				BlockState under = world.getBlockState(m.set(x, y0 - 1, z));
				if (!under.isAir() && !under.isReplaceable() && !under.getCollisionShape(world, m).isEmpty()) {
					grounded++;
				}
			}
		}
		BlockState anchorGround = world.getBlockState(m.set(pos.getX(), y0 - 1, pos.getZ()));
		if (anchorGround.getCollisionShape(world, m).isEmpty() || grounded < columns * GROUND_SHARE) {
			return type.isWorkshop() ? "Le sol n'est pas assez plein sous l'atelier : posez-le sur un terrain plat."
					: type.isCannon() ? "Le sol n'est pas assez plein sous le canon : posez-le sur un terrain plat (rempart, quai, cour)."
					: type.isTraining() ? "Le sol n'est pas assez plein sous l'aire d'entraînement : posez-la sur un terrain plat (cour, place)."
					: type.isDecoration() ? "Le sol n'est pas assez plein sous la décoration : posez-la sur un terrain plat (rue, place, quai)."
					: "Le sol n'est pas assez plein sous la tente : posez-la sur un terrain plat.";
		}
		return null;
	}

	/** May a tent be drawn over this block? Air, plants and snow that a tent would simply cover. */
	public static boolean coverable(BlockState s) {
		return s.isAir() || s.isReplaceable() || s.isIn(BlockTags.FLOWERS) || s.isIn(BlockTags.SAPLINGS) || s.isIn(BlockTags.SNOW)
				|| s.isIn(BlockTags.REPLACEABLE_BY_TREES) || s.getBlock() instanceof PlantBlock;
	}
}
