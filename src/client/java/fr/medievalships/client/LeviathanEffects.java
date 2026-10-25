package fr.medievalships.client;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.random.Random;

import fr.medievalships.core.LeviathanLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.entity.ShipEntity;

/**
 * Client effects of the Sky Leviathan, only near the player (vanilla particles and sounds, a handful per tick).
 * <p>
 * The engine runs while the airship moves or climbs, or while someone (or the autopilot) holds the helm; parked,
 * it is cold: no beat, no steam but a rare wisp from the boiler kept warm, the gears and pistons still (their
 * animation follows the speed, see {@code tools/generate_leviathan.py}). Running: steam puffing from the safety
 * valve of the boiler and the valves of its pipes, from the two pipes of the tower where they enter the balloon
 * and from the exhaust vents on both sides of the hull above the engine room; the beat of the pistons, the clatter
 * of the gears, the roar of the firebox and the hiss of the valves, all faster and stronger with the speed. Now and
 * then, parked or not, the timbers and the ropes creak in the wind.
 */
public final class LeviathanEffects {
	/** Effects within this distance of the player (the engine room's sounds within ENGINE_ROOM). */
	private static final double RANGE = 96, ENGINE_ROOM = 28, HULL = 48;
	/** The safety valve on the dome of the boiler, the valves of its two pipes (ship-local). */
	private static final double DOME_Y = -1.5, VALVE_Y = -1.1, VALVE_X = 1.4, VALVE_DZ = 0.6;

	private LeviathanEffects() {
	}

	public static void tick(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		if (ship.shipType() != Ships.SKY_LEVIATHAN || player == null || player.squaredDistanceTo(ship) > RANGE * RANGE) {
			return;
		}
		ShipPose pose = ship.pose();
		double speed = Math.abs(ship.syncedSpeed());
		double climb = Math.abs(ship.syncedVerticalSpeed());
		boolean running = speed > 0.15 || climb > 0.15 || ship.passengerInSeat(ShipGeometry.PILOT_SEAT) != null || ship.autopilotActive();
		double load = running ? Math.min(1.0, (speed + climb) / ship.config().normalSpeed) : 0.0;
		Random r = world.random;
		long t = world.getTime() + ship.getId() * 13L;
		double[] boiler = pose.toWorld(LeviathanLayout.BOILER_X, -3.0, LeviathanLayout.BOILER_Z);
		double toEngine = player.squaredDistanceTo(boiler[0], boiler[1], boiler[2]);

		// the safety valve on the dome: a wisp now and then while the boiler is kept warm, puffs under way
		if (r.nextFloat() < (running ? 0.08 + 0.3 * load : 0.012)) {
			double[] w = pose.toWorld(LeviathanLayout.BOILER_X + (r.nextDouble() - 0.5) * 0.3, DOME_Y, LeviathanLayout.BOILER_Z + 0.3);
			world.addParticleClient(ParticleTypes.WHITE_SMOKE, w[0], w[1], w[2], 0, 0.04, 0);
			if (running && r.nextFloat() < 0.3) {
				world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], 0, 0.02, 0);
			}
		}
		if (!running) {
			creak(world, ship, player, pose, r, t);
			return;
		}
		// the valves of the pipes from the dome to the walls: short jets sideways, with their hiss
		if (r.nextFloat() < 0.03 + 0.12 * load) {
			double side = r.nextBoolean() ? 1 : -1;
			double[] w = pose.toWorld(side * VALVE_X, VALVE_Y, LeviathanLayout.BOILER_Z + VALVE_DZ + 0.15);
			double[] v = pose.dirToWorld(side * 0.05, 0.02, 0.04);
			for (int i = 0; i < 3; i++) {
				world.addParticleClient(ParticleTypes.WHITE_SMOKE, w[0], w[1], w[2], v[0] * (1 + i * 0.4), v[1], v[2] * (1 + i * 0.4));
			}
			if (toEngine < ENGINE_ROOM * ENGINE_ROOM) {
				play(world, w, SoundEvents.BLOCK_FIRE_EXTINGUISH, 0.06f + 0.08f * (float) load, 1.6f + 0.3f * r.nextFloat());
			}
		}
		// steam from the two pipes of the tower where they enter the balloon
		if (r.nextFloat() < 0.05 + 0.2 * load) {
			double side = r.nextBoolean() ? 1 : -1;
			double[] w = pose.toWorld(side * 0.8, 8.4, LeviathanLayout.TOWER_Z0 - 0.3);
			double[] v = pose.dirToWorld(side * 0.03, -0.01, -0.02);
			world.addParticleClient(ParticleTypes.CLOUD, w[0], w[1], w[2], v[0], v[1], v[2]);
		}
		// the exhaust vents on both sides of the hull, aft, above the engine room: steam and a little smoke
		if (r.nextFloat() < 0.1 + 0.35 * load) {
			double side = r.nextBoolean() ? 1 : -1;
			double z = -13.0 + r.nextDouble();
			double[] w = pose.toWorld(side * (LeviathanLayout.hullX(z, -1.0) + 0.2), -1.0, z);
			double[] v = pose.dirToWorld(side * 0.06, 0.04, -0.04 - 0.04 * load);
			world.addParticleClient(r.nextInt(3) == 0 ? ParticleTypes.CAMPFIRE_COSY_SMOKE : ParticleTypes.WHITE_SMOKE, w[0], w[1], w[2], v[0], v[1] * 0.5,
					v[2]);
		}
		// the beat of the pistons (one stroke each per turn of the flywheel), slow when the airship only hovers
		int beat = (int) Math.max(5, Math.round(18 - 12 * load));
		if (t % beat == 0 && toEngine < 64 * 64) {
			double[] w = pose.toWorld(0, -3.0, LeviathanLayout.BOILER_Z - 1.7);
			boolean out = (t / beat) % 2 == 0;
			play(world, w, out ? SoundEvents.BLOCK_PISTON_EXTEND : SoundEvents.BLOCK_PISTON_CONTRACT, 0.12f + 0.2f * (float) load,
					0.5f + 0.15f * (float) load);
		}
		if (toEngine < ENGINE_ROOM * ENGINE_ROOM) {
			// the clatter of the gear trains on the walls, under way
			if (speed > 0.15 && t % Math.max(3, beat / 2) == 1) {
				double side = (t / 7) % 2 == 0 ? 1 : -1;
				double[] w = pose.toWorld(side * 3.6, -1.3, -13.8);
				play(world, w, SoundEvents.BLOCK_CHAIN_STEP, 0.12f + 0.1f * (float) load, 0.7f + 0.2f * r.nextFloat());
			}
			// the roar of the firebox
			if (t % 50 == 7) {
				play(world, boiler, SoundEvents.BLOCK_BLASTFURNACE_FIRE_CRACKLE, 0.5f + 0.3f * (float) load, 0.8f);
			}
		}
		creak(world, ship, player, pose, r, t);
	}

	/** The timbers of the hull and the ropes of the suspension creak in the wind, now and then. */
	private static void creak(ClientWorld world, ShipEntity ship, ClientPlayerEntity player, ShipPose pose, Random r, long t) {
		if (t % 90 != 31 || r.nextFloat() > 0.6 || player.squaredDistanceTo(ship) > HULL * HULL) {
			return;
		}
		double[] w = pose.toWorld((r.nextDouble() - 0.5) * 8, 2.0 + r.nextDouble() * 4, (r.nextDouble() - 0.5) * 30);
		play(world, w, r.nextBoolean() ? SoundEvents.BLOCK_WOOD_STEP : SoundEvents.BLOCK_LADDER_STEP, 0.3f, 0.5f + 0.1f * r.nextFloat());
	}

	private static void play(ClientWorld world, double[] w, SoundEvent sound, float volume, float pitch) {
		world.playSoundClient(w[0], w[1], w[2], sound, SoundCategory.NEUTRAL, volume, pitch, false);
	}
}
