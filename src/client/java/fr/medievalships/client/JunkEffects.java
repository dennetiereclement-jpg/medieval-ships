package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.JunkLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Dragon Junk, only near the player (a handful of vanilla particles a tick): skimming low over
 * the water, spray along its sides and a wake behind its stern, stronger with the speed; under way, wisps of wind
 * streaming from the ends of the long booms that hold the sail's clews out.
 */
public final class JunkEffects {
	private static final double RANGE = 80;

	private JunkEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.DRAGON_JUNK || player == null || player.squaredDistanceTo(ship) > RANGE * RANGE) {
			return;
		}
		ShipPose pose = ship.pose();
		double speed = Math.abs(ship.syncedSpeed());
		Random r = world.random;
		// low over the water: spray along the sides at the keel, a wake at the stern
		double[] keel = pose.toWorld(0.0, JunkLayout.keelY(0.0), 0.0);
		BlockPos below = BlockPos.ofFloored(keel[0], keel[1] - JunkLayout.WATER_HOVER - 0.6, keel[2]);
		if (world.getFluidState(below).isIn(FluidTags.WATER) || world.getFluidState(below.down()).isIn(FluidTags.WATER)) {
			double surface = below.getY() + (world.getFluidState(below).isIn(FluidTags.WATER) ? 1.0 : 0.0);
			int n = speed > 0.3 ? 2 + (int) (speed * 0.8) : r.nextFloat() < 0.15 ? 1 : 0;
			for (int i = 0; i < n; i++) {
				double z = -14.0 + r.nextDouble() * 30.0;
				double side = r.nextBoolean() ? 1 : -1;
				double[] w = pose.toWorld(side * (JunkLayout.hullX(z, -2.0) + 0.2), 0, z);
				world.addParticleClient(ParticleTypes.SPLASH, w[0], surface + 0.05, w[2], 0, 0.1, 0);
			}
			if (speed > 0.6 && r.nextFloat() < 0.6) {
				double[] w = pose.toWorld((r.nextDouble() - 0.5) * 3.0, 0, JunkLayout.STERN_Z - 0.8 - r.nextDouble() * 2.0);
				world.addParticleClient(ParticleTypes.BUBBLE_POP, w[0], surface + 0.05, w[2], 0, 0.02, 0);
				world.addParticleClient(ParticleTypes.SPLASH, w[0], surface + 0.05, w[2], 0, 0.05, 0);
			}
		}
		// under way: the wind streaming off the ends of the clew booms
		if (speed > 1.5 && r.nextFloat() < 0.12 * speed / ship.config().normalSpeed) {
			double side = r.nextBoolean() ? 1 : -1;
			double[] w = pose.toWorld(side * JunkLayout.CLEW_BOOM_END[0], JunkLayout.CLEW_BOOM_END[1], JunkLayout.CLEW_BOOM_END[2]);
			double[] back = pose.toWorld(0, 0, -1);
			double[] o = pose.toWorld(0, 0, 0);
			world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], (back[0] - o[0]) * 0.08, 0.0, (back[2] - o[2]) * 0.08);
		}
	}
}
