package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;

import fr.medievalships.core.LeviathanLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Sky Leviathan, only near the player: steam puffing from the valves of the boiler
 * and from the pipes of the tower into the balloon, and the beat of the engine, both faster with the speed.
 */
public final class LeviathanEffects {
	private LeviathanEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.SKY_LEVIATHAN || player == null || player.squaredDistanceTo(ship) > 96 * 96) {
			return;
		}
		ShipPose pose = ship.pose();
		double speed = Math.abs(ship.syncedSpeed());
		double run = Math.min(1.0, speed / ship.config().normalSpeed);
		var r = world.random;
		// the safety valve of the boiler, in the engine room: a hiss now and then, more often under way
		if (r.nextFloat() < 0.05 + 0.25 * run) {
			double[] w = pose.toWorld(LeviathanLayout.BOILER_X + (r.nextDouble() - 0.5) * 0.4, -1.2, LeviathanLayout.BOILER_Z + 0.9);
			world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], 0, 0.03, 0);
		}
		// steam from the two pipes of the tower where they enter the balloon
		if (r.nextFloat() < 0.04 + 0.2 * run) {
			double side = r.nextBoolean() ? 1 : -1;
			double[] w = pose.toWorld(side * 0.8, 8.4, LeviathanLayout.TOWER_Z0 - 0.3);
			double[] v = pose.dirToWorld(side * 0.03, -0.01, -0.02);
			world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], v[0], v[1], v[2]);
		}
		// exhaust vents on both sides of the hull, aft, above the engine room
		if (speed > 0.2 && r.nextFloat() < 0.35 * run) {
			double side = r.nextBoolean() ? 1 : -1;
			double z = -13.0 + r.nextDouble();
			double[] w = pose.toWorld(side * (LeviathanLayout.hullX(z, -1.0) + 0.2), -1.0, z);
			double[] v = pose.dirToWorld(side * 0.06, 0.04, -0.04);
			world.addParticleClient(ParticleTypes.CAMPFIRE_COSY_SMOKE, w[0], w[1], w[2], v[0], v[1] * 0.5, v[2]);
		}
		// the beat of the engine
		if (speed > 0.2) {
			int period = Math.max(6, (int) Math.round(20 - speed * 2));
			if (ship.age % period == 0) {
				double[] w = pose.toWorld(0, -3.0, LeviathanLayout.BOILER_Z);
				world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_PISTON_EXTEND, SoundCategory.NEUTRAL, 0.3f, 0.5f, false);
			}
		}
	}
}
