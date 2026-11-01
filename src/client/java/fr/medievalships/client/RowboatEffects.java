package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.RowboatLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Rowboat, only near the player (a few vanilla particles, vanilla sounds): a splash and the
 * paddle sound where the blades bite the water at each catch of the rowing cycle, a smaller one where they leave it,
 * the creak of a tholepin now and then, small splashes at the bow under way.
 */
public final class RowboatEffects {
	private static final double RANGE = 64;
	/** The rowing cycle ("row", 2 time units): the blades enter the water at 0 (sweep +22) and leave it at 1 (sweep -22). */
	private static final double CYCLE = 2.0;

	private RowboatEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.ROWBOAT || player == null || player.squaredDistanceTo(ship) > RANGE * RANGE) {
			return;
		}
		ShipPose pose = ship.pose();
		Random r = world.random;
		double speed = Math.abs(ship.syncedSpeed());
		if (ship.oarWeight > 0.4) {
			boolean catchNow = crossed(ship.lastOarPhase, ship.oarPhase, 0.0);
			boolean release = crossed(ship.lastOarPhase, ship.oarPhase, 1.0);
			if (catchNow || release) {
				for (int side = -1; side <= 1; side += 2) {
					double[] b = RowboatLayout.oarBlade(side, catchNow ? 22 : -22, -8);
					double[] w = pose.toWorld(b[0], 0.0, b[2]);
					if (!inWater(world, w)) {
						continue;
					}
					int n = catchNow ? 4 : 2;
					for (int i = 0; i < n; i++) {
						double[] v = pose.dirToWorld(side * 0.04, 0.0, catchNow ? -0.06 : 0.08);
						world.addParticleClient(ParticleTypes.SPLASH, w[0] + (r.nextDouble() - 0.5) * 0.4, w[1] + 0.05, w[2] + (r.nextDouble() - 0.5) * 0.4,
								v[0], 0.12 + 0.1 * r.nextDouble(), v[2]);
					}
					if (catchNow && side > 0) {
						world.playSoundClient(w[0], w[1], w[2], SoundEvents.ENTITY_BOAT_PADDLE_WATER, SoundCategory.NEUTRAL, 0.45f,
								0.85f + 0.2f * r.nextFloat(), false);
					}
				}
			}
			// the tholepins creak under the load, once or twice a cycle
			if (crossed(ship.lastOarPhase, ship.oarPhase, 0.35) && r.nextInt(3) == 0) {
				double[] w = pose.toWorld(0, RowboatLayout.THWART_TOP, RowboatLayout.OARLOCK_Z);
				world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_WOOD_STEP, SoundCategory.NEUTRAL, 0.18f, 0.45f + 0.1f * r.nextFloat(), false);
			}
		}
		// small splashes at the bow under way
		if (speed > 1.0 && r.nextFloat() < 0.35 * Math.min(1.0, speed / ship.config().normalSpeed)) {
			double side = r.nextBoolean() ? 1 : -1;
			double z = RowboatLayout.HALF_LENGTH - 0.3 - r.nextDouble() * 1.2;
			double[] w = pose.toWorld(side * (RowboatLayout.halfWidth(z) + 0.1), 0.0, z);
			if (inWater(world, w)) {
				double[] v = pose.dirToWorld(side * 0.05, 0.0, 0.0);
				world.addParticleClient(ParticleTypes.SPLASH, w[0], w[1] + 0.05, w[2], v[0], 0.06, v[2]);
			}
		}
	}

	/** Did the cycle phase pass the point {@code at} (in [0, CYCLE)) between the two phases? */
	private static boolean crossed(float before, float after, double at) {
		if (after <= before) {
			return false;
		}
		return Math.floor((after - at) / CYCLE) != Math.floor((before - at) / CYCLE);
	}

	private static boolean inWater(ClientWorld world, double[] w) {
		return world.getFluidState(BlockPos.ofFloored(w[0], w[1] - 0.1, w[2])).isIn(FluidTags.WATER);
	}
}
