package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.BalloonLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the hot-air balloon, only near the player (a handful of vanilla particles a tick, vanilla sounds):
 * the burner's pilot light and, while it climbs, its roaring flame rising into the mouth of the envelope (flames and
 * a little smoke); smoke from the boiler's stack under way; the wind in the rigging at speed; the chains and the
 * basket creaking in the sway.
 */
public final class BalloonEffects {
	private static final double RANGE = 80;
	private static final double SOUND_RANGE = 48;

	private BalloonEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.HOT_AIR_BALLOON || player == null || player.squaredDistanceTo(ship) > RANGE * RANGE) {
			return;
		}
		ShipPose pose = ship.pose();
		Random r = world.random;
		long t = world.getTime() + ship.getId() * 7L;
		double climbSpeed = ship.config().flight == null ? 1.0 : ship.config().flight.climbSpeed;
		double climb = Math.max(0.0, Math.min(1.0, ship.syncedVerticalSpeed() / Math.max(0.2, climbSpeed)));
		double speed = Math.abs(ship.syncedSpeed());
		double load = Math.min(1.0, speed / Math.max(0.5, ship.config().normalSpeed));
		boolean burning = climb > 0.15;
		// the burner: a small pilot light always, a roaring flame while climbing
		double[] b = BalloonLayout.BURNER;
		int n = burning ? 2 + (int) Math.round(climb * 3) : r.nextFloat() < 0.35f ? 1 : 0;
		for (int i = 0; i < n; i++) {
			double[] w = pose.toWorld(b[0] + (r.nextDouble() - 0.5) * 0.5, b[1] + r.nextDouble() * 0.4, b[2] + (r.nextDouble() - 0.5) * 0.5);
			world.addParticleClient(burning && r.nextBoolean() ? ParticleTypes.FLAME : ParticleTypes.SMALL_FLAME, w[0], w[1], w[2],
					(r.nextDouble() - 0.5) * 0.02, 0.06 + 0.1 * climb, (r.nextDouble() - 0.5) * 0.02);
		}
		if (burning && t % 3 == 0) {
			double[] w = pose.toWorld((r.nextDouble() - 0.5) * 0.6, BalloonLayout.FLAME_TOP + 0.4, (r.nextDouble() - 0.5) * 0.6);
			world.addParticleClient(ParticleTypes.SMOKE, w[0], w[1], w[2], 0, 0.05, 0);
		}
		// the boiler's stack: a puff now and then, a steady plume under way
		double[] s = BalloonLayout.STACK;
		if (t % (load > 0.05 ? 4 : 16) == 0) {
			double[] w = pose.toWorld(s[0], s[1], s[2]);
			double[] drift = pose.dirToWorld(0, 0, -0.03 - 0.06 * load);
			world.addParticleClient(ParticleTypes.SMOKE, w[0], w[1], w[2], drift[0], 0.04, drift[2]);
			if (load > 0.3 && r.nextBoolean()) {
				world.addParticleClient(ParticleTypes.CAMPFIRE_COSY_SMOKE, w[0], w[1], w[2], drift[0], 0.03, drift[2]);
			}
		}
		if (player.squaredDistanceTo(ship) > SOUND_RANGE * SOUND_RANGE) {
			return;
		}
		double[] bw = pose.toWorld(b[0], b[1], b[2]);
		if (burning) {
			// the roar of the burner: bursts of fire over a crackle
			if (t % 10 == 0) {
				world.playSoundClient(bw[0], bw[1], bw[2], SoundEvents.ITEM_FIRECHARGE_USE, SoundCategory.NEUTRAL, 0.3f + 0.3f * (float) climb,
						0.55f + 0.1f * r.nextFloat(), false);
			}
			if (t % 7 == 3) {
				world.playSoundClient(bw[0], bw[1], bw[2], SoundEvents.BLOCK_FIRE_AMBIENT, SoundCategory.NEUTRAL, 0.45f, 0.8f, false);
			}
		} else if (t % 40 == 0) {
			world.playSoundClient(bw[0], bw[1], bw[2], SoundEvents.BLOCK_CAMPFIRE_CRACKLE, SoundCategory.NEUTRAL, 0.22f, 1.0f, false);
		}
		// the wind in the rigging at speed, the chains and the basket creaking in the sway
		if (speed > 0.8 && t % 50 == 0) {
			world.playSoundClient(player.getX(), player.getY() + 1, player.getZ(), SoundEvents.ITEM_ELYTRA_FLYING, SoundCategory.NEUTRAL,
					0.05f + 0.06f * (float) load, 1.3f, false);
		}
		if (t % 90 == 0) {
			double[] w = pose.toWorld(0, BalloonLayout.MOUTH_Y - 0.5, 0);
			world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_CHAIN_STEP, SoundCategory.NEUTRAL, 0.16f, 0.7f, false);
		}
		if (t % 150 == 70) {
			double[] w = pose.toWorld(0, 0.3, 0);
			world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_WOOD_STEP, SoundCategory.NEUTRAL, 0.3f, 0.55f, false);
		}
	}
}
