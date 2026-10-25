package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.CorsairLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Old Corsair, only near the player (the bow wake is the generic one of
 * {@link ClientShipEvents}): the old hull groans now and then, more under way and in a turn; the rigging
 * creaks and the canvas flaps while the sails are set; the water washes along the bow, louder with the
 * speed; the fire of the kitchen hearth crackles and smokes a little. Sounds are client side and random,
 * so two ships never creak in step.
 */
public final class CorsairEffects {
	/** Sounds played so far (read by the in-game test). */
	public static int sounds;

	private CorsairEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.OLD_CORSAIR || player == null) {
			return;
		}
		double d2 = player.squaredDistanceTo(ship);
		if (d2 > 48 * 48) {
			return;
		}
		ShipPose pose = ship.pose();
		Random r = world.random;
		double speed = Math.abs(ship.syncedSpeed());
		double run = Math.min(1.0, speed / ship.config().normalSpeed);
		double turn = Math.min(1.0, Math.abs(ship.helmVisual) * run * 2);
		long t = world.getTime() + ship.getId() * 11L;
		// the timbers of the old hull groan
		if (r.nextFloat() < 0.006 + 0.02 * run + 0.03 * turn) {
			double side = r.nextBoolean() ? 1 : -1;
			double z = -18.0 + r.nextDouble() * 34.0;
			sound(world, pose, side * 3.5, CorsairLayout.LOWER_FLOOR_Y + r.nextDouble() * 4.0, z, SoundEvents.BLOCK_WOODEN_TRAPDOOR_OPEN,
					0.1f + 0.15f * (float) run, 0.45f + 0.15f * r.nextFloat());
		}
		float sail = ship.sailOpen;
		if (sail > 0.5f) {
			// the rigging creaks aloft, the canvas flaps now and then
			if (r.nextFloat() < 0.008 + 0.02 * run) {
				double z = r.nextBoolean() ? CorsairLayout.FORE_MAST_Z : CorsairLayout.MAIN_MAST_Z;
				sound(world, pose, 0, 14.0 + r.nextDouble() * 12.0, z, SoundEvents.ITEM_LEAD_TIED, 0.25f + 0.2f * (float) run,
						0.5f + 0.2f * r.nextFloat());
			}
			if (r.nextFloat() < 0.004 + 0.012 * run) {
				double z = r.nextBoolean() ? CorsairLayout.FORE_MAST_Z : CorsairLayout.MAIN_MAST_Z;
				sound(world, pose, 0, 18.0 + r.nextDouble() * 8.0, z, SoundEvents.ENTITY_PHANTOM_FLAP, 0.15f + 0.15f * (float) run,
						0.45f + 0.15f * r.nextFloat());
			}
		}
		// sails set or furled: the rustle of the canvas
		if (Math.abs(sail - ship.lastSailOpen) > 0.004f && t % 12 == 0) {
			sound(world, pose, 0, 16.0, CorsairLayout.FORE_MAST_Z, SoundEvents.ITEM_ARMOR_EQUIP_LEATHER.value(), 0.5f, 0.6f);
		}
		// the bow wave washing along the hull
		if (speed > 0.5) {
			int every = (int) Math.round(30 - 18 * run);
			if (t % every == 0) {
				double side = (t / every) % 2 == 0 ? 1 : -1;
				sound(world, pose, side * 2.5, 0.2, 17.0, SoundEvents.BLOCK_WATER_AMBIENT, 0.15f + 0.35f * (float) run,
						0.8f + 0.3f * (float) run);
			}
		}
		// the kitchen hearth: crackling (heard from close by), a wisp of smoke and a spark when the ship is
		// nearly still (world particles would trail behind a ship under way)
		double[] f = CorsairLayout.HEARTH_FIRE;
		double[] fire = pose.toWorld(f[0], f[1], f[2]);
		if (player.squaredDistanceTo(fire[0], fire[1], fire[2]) < 12 * 12) {
			if (t % 30 == 0) {
				world.playSoundClient(fire[0], fire[1], fire[2], SoundEvents.BLOCK_CAMPFIRE_CRACKLE, SoundCategory.BLOCKS,
						0.5f + 0.3f * r.nextFloat(), 0.8f + 0.2f * r.nextFloat(), false);
				sounds++;
			}
			if (speed < 0.3 && t % 6 == 0) {
				double[] w = pose.toWorld(f[0] + (r.nextDouble() - 0.5) * 0.6, f[1] + 0.3, f[2] + 0.05);
				world.addParticleClient(ParticleTypes.SMOKE, w[0], w[1], w[2], 0, 0.02, 0);
				if (r.nextInt(4) == 0) {
					world.addParticleClient(ParticleTypes.SMALL_FLAME, w[0], w[1] - 0.15, w[2], 0, 0.005, 0);
				}
			}
		}
	}

	private static void sound(ClientWorld world, ShipPose pose, double x, double y, double z, SoundEvent sound, float volume, float pitch) {
		double[] w = pose.toWorld(x, y, z);
		world.playSoundClient(w[0], w[1], w[2], sound, SoundCategory.NEUTRAL, volume, pitch, false);
		sounds++;
	}
}
