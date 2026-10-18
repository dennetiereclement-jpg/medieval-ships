package fr.medievalships.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

import fr.medievalships.client.render.ShipModels;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/** Client tick logic: carrying the local player on deck, and interaction hints. */
public final class ClientShipEvents {
	private static String lastHint = "";
	private static int hintCooldown;

	private ClientShipEvents() {
	}

	/**
	 * Runs after every entity of the client world has ticked. The local player is simulated by
	 * this client, so this is where he is moved along with the deck he stands on: by the exact
	 * displacement of the hull since the previous tick (translation + rotation about the hull).
	 * Only the current position is shifted, so the player and the ship interpolate together.
	 */
	public static void endWorldTick(ClientWorld world) {
		MinecraftClient client = MinecraftClient.getInstance();
		ClientPlayerEntity player = client.player;
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved()) {
				continue;
			}
			ShipPose now = ship.pose();
			ShipPose last = ship.lastCarryPose();
			ship.setLastCarryPose(now);
			if (last == null || player == null || player.hasVehicle() || player.isSpectator() || last.equals(now)) {
				continue;
			}
			double[] local = last.toLocal(player.getX(), player.getY(), player.getZ());
			if (!ship.geometry().inCarryVolume(local[0], local[1], local[2])) {
				continue;
			}
			double[] w = now.toWorld(local[0], local[1], local[2]);
			player.setPosition(w[0], w[1], w[2]);
			float dyaw = (float) ShipPose.wrapDegrees(now.yaw() - last.yaw());
			if (dyaw != 0) {
				player.setYaw(player.getYaw() + dyaw);
				player.setHeadYaw(player.getHeadYaw() + dyaw);
				player.setBodyYaw(player.bodyYaw + dyaw);
			}
		}
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (!ship.isRemoved()) {
				wake(world, ship, player);
				engine(world, ship, player);
			}
		}
		rescue(world, player);
		showHint(client);
	}

	/**
	 * Mod-independent safety net: if the local player ended up inside the deck or fell through it
	 * during the tick (another mod replacing the collision code, lag...), put him back on top of
	 * it, with no visible jump.
	 */
	private static void rescue(ClientWorld world, ClientPlayerEntity player) {
		if (player == null || player.hasVehicle() || player.isSpectator() || player.noClip) {
			return;
		}
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved()) {
				continue;
			}
			ShipPose pose = ship.pose();
			double[] l = pose.toLocal(player.getX(), player.getY(), player.getZ());
			double top = ship.geometry().deckRescueY(l[0], l[1], l[2]);
			if (Double.isNaN(top) && falling(player)) {
				// fast fall straight through a deck in a single tick
				top = ship.geometry().deckCrossingY(l[0], l[2], player.lastY - pose.y(), l[1], 1e-3, true);
			}
			if (!Double.isNaN(top)) {
				player.setPosition(player.getX(), pose.y() + top, player.getZ());
				if (player.getVelocity().y < 0) {
					player.setVelocity(player.getVelocity().x, 0, player.getVelocity().z);
				}
				player.setOnGround(true);
				player.fallDistance = 0;
				return;
			}
		}
	}

	/**
	 * Foam at the bow and a light wake behind ships that ask for it, proportional to the speed and
	 * only near the player (a handful of vanilla particles per tick).
	 */
	private static void wake(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		ShipModels.Visual visual = ShipModels.of(ship.shipType());
		double speed = Math.abs(ship.syncedSpeed());
		if (visual == null || !visual.bowWake() || speed < 0.8 || player == null || player.squaredDistanceTo(ship) > 96 * 96) {
			return;
		}
		ShipPose pose = ship.pose();
		var hull = ship.geometry().hull();
		double bowZ = hull.halfLength - 1.2;
		int n = (int) Math.min(4, Math.ceil(speed));
		for (int i = 0; i < n; i++) {
			double side = world.random.nextBoolean() ? 1 : -1;
			double z = bowZ - world.random.nextDouble() * 4.0;
			double x = side * (hull.halfWidth(z) + 0.1);
			double[] w = pose.toWorld(x, hull.waterlineY + 0.15, z);
			double[] out = pose.dirToWorld(side * 0.12, 0.08, 0.0);
			world.addParticleClient(ParticleTypes.SPLASH, w[0], w[1], w[2], out[0], out[1] + 0.05, out[2]);
		}
		if (world.random.nextInt(3) == 0) {
			double[] w = pose.toWorld((world.random.nextDouble() - 0.5) * 3.0, hull.waterlineY + 0.1, -hull.halfLength - 0.8);
			world.addParticleClient(ParticleTypes.BUBBLE, w[0], w[1] - 0.2, w[2], 0, 0.02, 0);
			world.addParticleClient(ParticleTypes.SPLASH, w[0], w[1], w[2], 0, 0.04, 0);
		}
	}

	/**
	 * Steam engine: black smoke from the funnels (thicker when under way), foam and spray thrown up by
	 * the paddle wheel, and the beat of the engine, all following the speed. Only near the player.
	 */
	private static void engine(ClientWorld world, ShipEntity ship, ClientPlayerEntity player) {
		ShipModels.Visual visual = ShipModels.of(ship.shipType());
		if (visual == null || visual.engine() == null || player == null || player.squaredDistanceTo(ship) > 80 * 80) {
			return;
		}
		ShipModels.Engine engine = visual.engine();
		ShipPose pose = ship.pose();
		double speed = Math.abs(ship.syncedSpeed());
		double load = Math.min(1.0, speed / Math.max(0.5, ship.config().normalSpeed));
		long t = world.getTime() + ship.getId() * 7L;
		// smoke: a puff every few ticks at rest, every tick and thicker under way
		int every = load > 0.05 ? 1 : 5;
		if (t % every == 0) {
			double[] drift = pose.dirToWorld(0, 0, -0.04 - 0.05 * load);
			for (double[] f : engine.funnels()) {
				double[] w = pose.toWorld(f[0] + (world.random.nextDouble() - 0.5) * 0.5, f[1], f[2] + (world.random.nextDouble() - 0.5) * 0.5);
				world.addParticleClient(ParticleTypes.LARGE_SMOKE, w[0], w[1], w[2], drift[0], 0.07 + 0.05 * load, drift[2]);
				if (load > 0.05) {
					// thick dark plume under way
					world.addParticleClient(ParticleTypes.LARGE_SMOKE, w[0], w[1] + 0.2, w[2], drift[0] * 1.3, 0.1 + 0.05 * load, drift[2] * 1.3);
				}
				if (load > 0.4 && world.random.nextInt(3) == 0) {
					world.addParticleClient(ParticleTypes.CAMPFIRE_COSY_SMOKE, w[0], w[1] + 0.3, w[2], drift[0], 0.05, drift[2]);
				}
			}
		}
		double water = ship.geometry().hull().waterlineY;
		double[] wh = engine.wheels()[0];
		if (speed > 0.3) {
			for (double[] w0 : engine.wheels()) {
				// foam where the paddles enter and leave the water, spray at the back of the wheel
				int n = (int) Math.ceil(2 * load);
				for (int i = 0; i < n; i++) {
					double z = w0[2] + (world.random.nextDouble() - 0.5) * 2 * w0[3];
					double x = w0[0] + (world.random.nextDouble() - 0.5) * 1.2;
					double[] w = pose.toWorld(x, water + 0.1, z);
					double[] out = pose.dirToWorld(Math.signum(w0[0]) * 0.05, 0.12 + 0.1 * load, -0.15 * Math.signum(ship.syncedSpeed()));
					world.addParticleClient(ParticleTypes.SPLASH, w[0], w[1], w[2], out[0], out[1], out[2]);
				}
				if (world.random.nextInt(3) == 0) {
					double[] w = pose.toWorld(w0[0], water - 0.3, w0[2] - Math.signum(ship.syncedSpeed()) * w0[3]);
					world.addParticleClient(ParticleTypes.BUBBLE, w[0], w[1], w[2], 0, 0.05, 0);
				}
			}
		}
		// engine beat: faster with the speed; a slow idle beat at rest
		int beat = (int) Math.round(16 - 10 * load);
		if (t % beat == 0 && player.squaredDistanceTo(ship) < 48 * 48) {
			double[] w = pose.toWorld(0, ship.geometry().hull().mainDeckY, 0);
			world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_PISTON_CONTRACT, SoundCategory.NEUTRAL,
					0.12f + 0.18f * (float) load, 0.55f + 0.25f * (float) load, false);
			if (speed > 0.3 && t % (beat * 2) == 0) {
				double[] p = pose.toWorld(wh[0], water + 0.2, wh[2]);
				world.playSoundClient(p[0], p[1], p[2], SoundEvents.ENTITY_GENERIC_SPLASH, SoundCategory.NEUTRAL,
						0.08f + 0.12f * (float) load, 0.9f, false);
			}
		}
		if (t % 40 == 0 && player.squaredDistanceTo(ship) < 32 * 32) {
			double[] w = pose.toWorld(0, engine.funnels()[0][1] - 4, engine.funnels()[0][2]);
			world.playSoundClient(w[0], w[1], w[2], SoundEvents.BLOCK_FURNACE_FIRE_CRACKLE, SoundCategory.NEUTRAL, 0.5f, 0.8f, false);
		}
	}

	/** A real fall (not a teleport): moving down, at most terminal speed, barely sideways. */
	private static boolean falling(ClientPlayerEntity player) {
		double drop = player.lastY - player.getY();
		double side = Math.hypot(player.getX() - player.lastX, player.getZ() - player.lastZ);
		return player.getVelocity().y < -0.05 && drop > 0 && drop < 4.2 && side < 1.5;
	}

	private static void showHint(MinecraftClient client) {
		ShipPicker.Target t = ShipPicker.current();
		String hint = "";
		if (t != null) {
			hint = switch (t.pick().kind()) {
				case HELM -> t.ship().autopilotActive() ? "Pilote automatique à la barre" : "Clic droit : prendre la barre";
				case SEAT -> "Clic droit : s'asseoir";
				case HULL -> "Clic droit : monter à bord";
				case DECK -> "";
			};
		}
		if (hintCooldown > 0) {
			hintCooldown--;
		}
		if (!hint.isEmpty() && (!hint.equals(lastHint) || hintCooldown == 0)) {
			client.inGameHud.setOverlayMessage(Text.literal(hint).formatted(Formatting.GRAY), false);
			hintCooldown = 30;
		}
		lastHint = hint;
	}
}
