package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.CrystalLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Crystal Airship, only near the player (vanilla particles, a handful per tick): a few blue
 * magic sparks round its glowing crystals (the platform under the keel, the floating pods, the eyes of the engines, the
 * porthole of the stern medallion), more of them while its engines run (under way, climbing, or someone at the helm), and a
 * light breath of vapour behind the engines under way.
 */
public final class CrystalEffects {
	private static final double RANGE = 80;

	private CrystalEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.CRYSTAL_AIRSHIP || player == null || player.squaredDistanceTo(ship) > RANGE * RANGE) {
			return;
		}
		ShipPose pose = ship.pose();
		double speed = Math.abs(ship.syncedSpeed());
		double climb = Math.abs(ship.syncedVerticalSpeed());
		boolean running = speed > 0.15 || climb > 0.15 || ship.passengerInSeat(ShipGeometry.PILOT_SEAT) != null || ship.autopilotActive();
		double load = running ? Math.min(1.0, (speed + climb) / ship.config().normalSpeed) : 0.0;
		Random r = world.random;
		// sparks round the crystals: the platform under the keel and the two floating pods
		double[][] crystals = {
				{0.0, CrystalLayout.BOTTOM_CRYSTAL[1] - 1.2, CrystalLayout.BOTTOM_CRYSTAL[0], 1.4},
				{CrystalLayout.FRONT_POD[0], CrystalLayout.FRONT_POD[1], CrystalLayout.FRONT_POD[2], 1.2},
				{CrystalLayout.REAR_POD[0], CrystalLayout.REAR_POD[1], CrystalLayout.REAR_POD[2], 1.4}};
		for (double[] c : crystals) {
			if (r.nextFloat() < (running ? 0.18 + 0.2 * load : 0.06)) {
				double[] w = pose.toWorld(c[0] + (r.nextDouble() - 0.5) * c[3] * 2, c[1] + (r.nextDouble() - 0.5) * c[3] * 2,
						c[2] + (r.nextDouble() - 0.5) * c[3] * 2);
				world.addParticleClient(r.nextFloat() < 0.5 ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.GLOW, w[0], w[1], w[2],
						(r.nextDouble() - 0.5) * 0.02, 0.02, (r.nextDouble() - 0.5) * 0.02);
			}
		}
		if (!running) {
			return;
		}
		// the crystal eyes of the nacelles, vapour behind them and behind the stern engine
		for (int side = -1; side <= 1; side += 2) {
			double x = side * (CrystalLayout.NACELLE[0] + CrystalLayout.NACELLE[4] + 0.3);
			if (r.nextFloat() < 0.12 + 0.2 * load) {
				double[] w = pose.toWorld(x, CrystalLayout.NACELLE[1] + (r.nextDouble() - 0.5) * 2, CrystalLayout.NACELLE_EYE_Z + (r.nextDouble() - 0.5) * 2);
				world.addParticleClient(ParticleTypes.ELECTRIC_SPARK, w[0], w[1], w[2], side * 0.03, 0.01, 0);
			}
			if (speed > 0.3 && r.nextFloat() < 0.15 * load) {
				double[] w = pose.toWorld(side * CrystalLayout.NACELLE[0], CrystalLayout.NACELLE[1], CrystalLayout.NACELLE[2] - 0.6);
				double[] back = pose.toWorld(side * CrystalLayout.NACELLE[0], CrystalLayout.NACELLE[1], CrystalLayout.NACELLE[2] - 1.6);
				world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], (back[0] - w[0]) * 0.1, 0.0, (back[2] - w[2]) * 0.1);
			}
		}
		// a few sparks at the porthole of the stern medallion
		if (r.nextFloat() < 0.1 * load) {
			double[] w = pose.toWorld((r.nextDouble() - 0.5) * 1.6, CrystalLayout.MEDALLION[0] + (r.nextDouble() - 0.5) * 1.6, CrystalLayout.MEDALLION[1] - 0.8);
			world.addParticleClient(ParticleTypes.ELECTRIC_SPARK, w[0], w[1], w[2], 0, 0.01, -0.02);
		}
	}
}
