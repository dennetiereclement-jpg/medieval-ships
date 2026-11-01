package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.FrigateLayout;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Blue-Sailed Frigate, only near the player (the foam wake is the generic one of
 * {@link ClientShipEvents}): the big hull creaks now and then, more under way and in a turn; the rigging
 * creaks and the canvas flaps while the sails are set; the water washes along the bow, louder with the
 * speed. Vanilla sounds, client side and random, so two ships never creak in step.
 */
public final class FrigateEffects {
	/** Sounds played so far (read by the in-game test). */
	public static int sounds;

	private FrigateEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.BLUE_FRIGATE || player == null) {
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
		long t = world.getTime() + ship.getId() * 13L;
		// the timbers of the big hull groan (deep)
		if (r.nextFloat() < 0.005 + 0.018 * run + 0.03 * turn) {
			double side = r.nextBoolean() ? 1 : -1;
			double z = -15.0 + r.nextDouble() * 30.0;
			sound(world, pose, side * 3.5, FrigateLayout.LOWER_FLOOR_Y + r.nextDouble() * 3.5, z, SoundEvents.BLOCK_WOODEN_TRAPDOOR_OPEN,
					0.12f + 0.15f * (float) run, 0.4f + 0.12f * r.nextFloat());
		}
		float sail = ship.sailOpen;
		if (sail > 0.5f) {
			// the rigging creaks aloft, the canvas flaps now and then
			if (r.nextFloat() < 0.008 + 0.02 * run) {
				double z = r.nextBoolean() ? FrigateLayout.FORE_MAST_Z : FrigateLayout.MAIN_MAST_Z;
				sound(world, pose, 0, 14.0 + r.nextDouble() * 12.0, z, SoundEvents.ITEM_LEAD_TIED, 0.25f + 0.2f * (float) run,
						0.5f + 0.2f * r.nextFloat());
			}
			if (r.nextFloat() < 0.004 + 0.012 * run) {
				double z = r.nextBoolean() ? FrigateLayout.FORE_MAST_Z : FrigateLayout.MAIN_MAST_Z;
				sound(world, pose, 0, 18.0 + r.nextDouble() * 8.0, z, SoundEvents.ENTITY_PHANTOM_FLAP, 0.15f + 0.15f * (float) run,
						0.4f + 0.15f * r.nextFloat());
			}
		}
		// sails set or furled: the rustle of the canvas
		if (Math.abs(sail - ship.lastSailOpen) > 0.004f && t % 12 == 0) {
			sound(world, pose, 0, 16.0, FrigateLayout.FORE_MAST_Z, SoundEvents.ITEM_ARMOR_EQUIP_LEATHER.value(), 0.5f, 0.55f);
		}
		// the bow wave washing along the hull
		if (speed > 0.5) {
			int every = (int) Math.round(30 - 18 * run);
			if (t % every == 0) {
				double side = (t / every) % 2 == 0 ? 1 : -1;
				sound(world, pose, side * 2.5, 0.2, 15.0, SoundEvents.BLOCK_WATER_AMBIENT, 0.15f + 0.35f * (float) run,
						0.75f + 0.3f * (float) run);
			}
		}
	}

	private static void sound(ClientWorld world, ShipPose pose, double x, double y, double z, SoundEvent sound, float volume, float pitch) {
		double[] w = pose.toWorld(x, y, z);
		world.playSoundClient(w[0], w[1], w[2], sound, SoundCategory.NEUTRAL, volume, pitch, false);
		sounds++;
	}
}
