package fr.medievalships.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.GalleyEntity;
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
		for (GalleyEntity ship : ShipTracker.ships(world)) {
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
			if (!ShipGeometry.inCarryVolume(local[0], local[1], local[2])) {
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
		showHint(client);
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
