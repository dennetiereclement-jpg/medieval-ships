package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.GearSteamLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Gear Steamship, only near the player (the foam at the bow is the generic one of
 * {@link ClientShipEvents}): smoke from the funnel (a thin wisp at rest, a thick dark plume under way), a puff of
 * steam now and then from the copper dome, the beat of the engine (faster with the speed), the boiler's fire, the
 * churn of the screw under the counter, the creak of the hull and of the rigging. Vanilla particles and sounds,
 * client side and random. The gear wheels turn with the speed through the model's {@code engine} animation.
 */
public final class GearSteamEffects {
	/** Smoke puffs and sounds so far (read by the in-game test). */
	public static int puffs;
	public static int sounds;

	private GearSteamEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.GEAR_STEAMSHIP || player == null) {
			return;
		}
		double d2 = player.squaredDistanceTo(ship);
		if (d2 > 80 * 80) {
			return;
		}
		ShipPose pose = ship.pose();
		Random r = world.random;
		double speed = Math.abs(ship.syncedSpeed());
		double load = Math.min(1.0, speed / Math.max(0.5, ship.config().normalSpeed));
		long t = world.getTime() + ship.getId() * 7L;
		// the funnel: a puff every few ticks at rest, every tick and thicker under way
		int every = load > 0.05 ? 1 : 6;
		if (t % every == 0) {
			double[] drift = pose.dirToWorld(0, 0, -0.04 - 0.05 * load);
			double rr = GearSteamLayout.FUNNEL_R * 0.6;
			double[] w = pose.toWorld((r.nextDouble() - 0.5) * rr, GearSteamLayout.FUNNEL_TOP + 0.2, GearSteamLayout.FUNNEL_Z + (r.nextDouble() - 0.5) * rr);
			world.addParticleClient(ParticleTypes.LARGE_SMOKE, w[0], w[1], w[2], drift[0], 0.07 + 0.05 * load, drift[2]);
			puffs++;
			if (load > 0.05) {
				world.addParticleClient(ParticleTypes.LARGE_SMOKE, w[0], w[1] + 0.2, w[2], drift[0] * 1.3, 0.1 + 0.05 * load, drift[2] * 1.3);
			}
			if (load > 0.4 && r.nextInt(3) == 0) {
				world.addParticleClient(ParticleTypes.CAMPFIRE_COSY_SMOKE, w[0], w[1] + 0.3, w[2], drift[0], 0.05, drift[2]);
			}
		}
		// a puff of steam from the relief valve on the dome, now and then (more often under way)
		if (r.nextFloat() < 0.01 + 0.03 * load) {
			double[] w = pose.toWorld(0, GearSteamLayout.DOME_TOP + 0.6, GearSteamLayout.DOME_Z);
			for (int i = 0; i < 4; i++) {
				world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], (r.nextDouble() - 0.5) * 0.05, 0.12, (r.nextDouble() - 0.5) * 0.05);
			}
			if (d2 < 40 * 40) {
				sound(world, pose, 0, GearSteamLayout.DOME_TOP, GearSteamLayout.DOME_Z, SoundEvents.BLOCK_FIRE_EXTINGUISH, 0.25f, 1.4f + 0.2f * r.nextFloat());
			}
		}
		// the churn of the screw under the counter
		if (speed > 0.3 && r.nextInt(2) == 0) {
			double[] w = pose.toWorld((r.nextDouble() - 0.5) * 2.0, 0.1, -16.6 - r.nextDouble());
			double[] v = pose.dirToWorld(0, 0.06, -0.15 * Math.signum(ship.syncedSpeed()));
			world.addParticleClient(ParticleTypes.SPLASH, w[0], w[1], w[2], v[0], v[1], v[2]);
			if (r.nextInt(3) == 0) {
				world.addParticleClient(ParticleTypes.BUBBLE, w[0], w[1] - 0.3, w[2], 0, 0.05, 0);
			}
		}
		if (d2 > 48 * 48) {
			return;
		}
		// the engine beat: faster with the speed; a slow idle beat at rest
		int beat = (int) Math.round(16 - 10 * load);
		if (t % beat == 0) {
			sound(world, pose, 0, GearSteamLayout.MAIN_DECK_Y + 1.0, -2.0, SoundEvents.BLOCK_PISTON_CONTRACT, 0.12f + 0.18f * (float) load,
					0.5f + 0.25f * (float) load);
		}
		if (t % 40 == 0 && d2 < 32 * 32) {
			sound(world, pose, 0, GearSteamLayout.MAIN_DECK_Y + 1.0, GearSteamLayout.FUNNEL_Z, SoundEvents.BLOCK_FURNACE_FIRE_CRACKLE, 0.5f, 0.8f);
		}
		// the iron hull and the rigging creak now and then, more under way and in a turn
		double turn = Math.min(1.0, Math.abs(ship.helmVisual) * load * 2);
		if (r.nextFloat() < 0.004 + 0.012 * load + 0.02 * turn) {
			double side = r.nextBoolean() ? 1 : -1;
			sound(world, pose, side * 3.5, 2.0 + r.nextDouble() * 3.0, -14.0 + r.nextDouble() * 28.0, SoundEvents.BLOCK_CHAIN_STEP, 0.3f + 0.2f * (float) load,
					0.5f + 0.15f * r.nextFloat());
		}
		if (ship.sailOpen > 0.5f && r.nextFloat() < 0.004 + 0.01 * load) {
			sound(world, pose, 0, 14.0 + r.nextDouble() * 4.0, GearSteamLayout.MAIN_MAST_Z, SoundEvents.ITEM_LEAD_TIED, 0.2f + 0.15f * (float) load,
					0.5f + 0.2f * r.nextFloat());
		}
	}

	private static void sound(ClientWorld world, ShipPose pose, double x, double y, double z, SoundEvent sound, float volume, float pitch) {
		double[] w = pose.toWorld(x, y, z);
		world.playSoundClient(w[0], w[1], w[2], sound, SoundCategory.NEUTRAL, volume, pitch, false);
		sounds++;
	}
}
