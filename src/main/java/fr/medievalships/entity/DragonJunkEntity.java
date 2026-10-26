package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.fluid.FluidState;
import net.minecraft.item.Item;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.JunkLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/**
 * The Dragon Junk ({@code medievalships:dragon_junk}). It flies like the other airships and, unlike them, skims the
 * water: coming down over a lake or the sea, its keel stops {@link JunkLayout#WATER_HOVER} above the surface (its
 * anchor may dip in), and it rises back out if it was pushed lower. Only its own vertical speed is touched, before
 * the normal flight tick, so the move still goes through the collisions and carries everyone aboard.
 */
public class DragonJunkEntity extends ShipEntity {
	/** Keel points sampled for the water (ship-local z). */
	private static final double[] KEEL_Z = {-12.0, -6.0, 0.0, 6.0, 12.0, 17.0};

	public DragonJunkEntity(EntityType<? extends DragonJunkEntity> type, World world) {
		super(type, world);
	}

	/** Players walk in its rooms while it flies: the hull follows the server without the vanilla glide. */
	@Override
	protected boolean followsServerExactly() {
		return true;
	}

	@Override
	public void tick() {
		if (getEntityWorld() instanceof ServerWorld world && !isRemoved()) {
			skimWater(world);
		}
		super.tick();
	}

	/** Keeps the keel over the water: no further descent within the hover height, a gentle rise if below it. */
	private void skimWater(ServerWorld world) {
		double gap = waterGap(world, pose());
		if (Double.isNaN(gap) || gap >= JunkLayout.WATER_HOVER + 0.05) {
			return;
		}
		var flight = flight();
		double a = config().flight != null ? config().flight.verticalAcceleration * 0.05 : 0.05;
		if (gap < JunkLayout.WATER_HOVER - 0.3) {
			flight.vy = Math.max(flight.vy, 0.6);
		} else if (flight.vy <= a) {
			// cancels what a descent order would add this tick: the altitude holds
			flight.vy = a;
		}
	}

	/** Lowest height of the keel over the water surface under it (negative: under the surface), NaN without water. */
	static double waterGap(ServerWorld world, ShipPose pose) {
		double best = Double.NaN;
		BlockPos.Mutable pos = new BlockPos.Mutable();
		for (double z : KEEL_Z) {
			double ky = JunkLayout.keelY(z);
			double[] w = pose.toWorld(0.0, ky, z);
			int bx = (int) Math.floor(w[0]), bz = (int) Math.floor(w[2]);
			if (!world.isChunkLoaded(bx >> 4, bz >> 4)) {
				continue;
			}
			int y0 = (int) Math.floor(w[1] - JunkLayout.WATER_HOVER - 1.0);
			int y1 = (int) Math.floor(w[1]) + 6;
			double surface = Double.NaN;
			for (int y = y0; y <= y1; y++) {
				pos.set(bx, y, bz);
				FluidState fluid = world.getFluidState(pos);
				if (fluid.isIn(FluidTags.WATER)) {
					surface = y + fluid.getHeight(world, pos);
				} else if (!Double.isNaN(surface)) {
					break;
				}
			}
			if (!Double.isNaN(surface)) {
				double gap = w[1] - surface;
				best = Double.isNaN(best) ? gap : Math.min(best, gap);
			}
		}
		return best;
	}

	@Override
	public ShipType shipType() {
		return Ships.DRAGON_JUNK;
	}

	@Override
	public Item item() {
		return MedievalShips.DRAGON_JUNK_ITEM;
	}
}
