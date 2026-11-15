package fr.medievalships.forge;

import java.util.Collection;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import net.minecraft.block.Block;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.tent.TentCollisions;

/**
 * The divine forge (1.34.0): its block entity type {@code medievalships:forge_divine} (registered by
 * {@code Tents.register} once the forge's block exists; the block and its item are the props', in the tab "Ateliers"),
 * and finding a forge from any of its blocks ({@link #find}) or near a point ({@link #nearest}).
 */
public final class DivineForge {
	public static final Identifier ID = MedievalShips.id("forge_divine");
	public static BlockEntityType<DivineForgeBlockEntity> BLOCK_ENTITY;

	private DivineForge() {
	}

	/** The block entity type of the forge's anchor blocks (called by {@code Tents.register} with the forge's blocks). */
	public static void registerBlockEntity(Collection<? extends Block> blocks) {
		BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, ID,
				FabricBlockEntityTypeBuilder.create(DivineForgeBlockEntity::new, blocks.toArray(Block[]::new)).build());
	}

	/** The forge at this block: its anchor, or any block inside the extent of a loaded forge; null when none. */
	@Nullable
	public static DivineForgeBlockEntity find(World world, BlockPos pos) {
		if (world.getBlockEntity(pos) instanceof DivineForgeBlockEntity f) {
			return f;
		}
		Vec3d p = Vec3d.ofCenter(pos);
		for (TentCollisions.Placed t : TentCollisions.nearby(world, new Box(pos).expand(16))) {
			if (t.type().isDivineForge() && t.extent().expand(0.01).contains(p) && world.getBlockEntity(t.pos()) instanceof DivineForgeBlockEntity f) {
				return f;
			}
		}
		return null;
	}

	/** The loaded forge nearest to a point within {@code radius} blocks, or null. */
	@Nullable
	public static DivineForgeBlockEntity nearest(World world, Vec3d from, double radius) {
		DivineForgeBlockEntity best = null;
		double bestD = radius * radius;
		for (TentCollisions.Placed t : TentCollisions.all(world)) {
			if (!t.type().isDivineForge()) {
				continue;
			}
			double d = t.pos().getSquaredDistance(from);
			if (d <= bestD && world.getBlockEntity(t.pos()) instanceof DivineForgeBlockEntity f) {
				bestD = d;
				best = f;
			}
		}
		return best;
	}
}
