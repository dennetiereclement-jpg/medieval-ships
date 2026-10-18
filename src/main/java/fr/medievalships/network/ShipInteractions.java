package fr.medievalships.network;

import net.minecraft.entity.Entity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.ShipGeometry;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;

/** Server side handling of {@link ShipInteractPayload}. */
public final class ShipInteractions {
	private static final double MAX_REACH = 8.0;

	private ShipInteractions() {
	}

	public static void handle(ShipInteractPayload payload, ServerPlayerEntity player) {
		Entity entity = player.getEntityWorld().getEntityById(payload.entityId());
		if (!(entity instanceof ShipEntity ship) || ship.isRemoved() || player.isSpectator()) {
			return;
		}
		double[] w = ship.pose().toWorld(payload.lx(), payload.ly(), payload.lz());
		// the client picked the point; make sure it is plausible for this player
		if (player.getEyePos().squaredDistanceTo(w[0], w[1], w[2]) > MAX_REACH * MAX_REACH) {
			return;
		}
		if (payload.action() == ShipInteractPayload.ATTACK) {
			attack(ship, player);
			return;
		}
		ShipGeometry.PickKind[] kinds = ShipGeometry.PickKind.values();
		if (payload.kind() < 0 || payload.kind() >= kinds.length) {
			return;
		}
		switch (kinds[payload.kind()]) {
			case HELM -> takeHelm(ship, player);
			case SEAT -> sit(ship, player, payload.seat());
			case HULL -> board(ship, player, w);
			case DECK -> {
				// clicking the deck does nothing, but it must not reach the water under the hull
			}
			case DOOR -> {
				if (payload.seat() >= 0 && payload.seat() < fr.medievalships.core.InteriorGrid.MAX_DOORS) {
					Text msg = ship.toggleDoor(payload.seat());
					if (msg != null) {
						player.sendMessage(msg, true);
					}
				}
			}
		}
	}

	private static void takeHelm(ShipEntity ship, ServerPlayerEntity player) {
		if (ship.isAutopilotEnabled()) {
			player.sendMessage(Text.literal("Le pilote automatique tient la barre (/ship ai disable).").formatted(Formatting.YELLOW), true);
			return;
		}
		if (player.getVehicle() == ship && ship.seatOf(player) == ShipGeometry.PILOT_SEAT) {
			return;
		}
		if (!ship.seat(player, ShipGeometry.PILOT_SEAT)) {
			player.sendMessage(Text.literal("Quelqu'un tient déjà la barre.").formatted(Formatting.YELLOW), true);
			return;
		}
		player.sendMessage(Text.literal("Z/S : ramer avant/arrière, Q/D : barre, Espace/Ctrl : allure, Maj : quitter")
				.formatted(Formatting.GOLD), true);
	}

	private static void sit(ShipEntity ship, ServerPlayerEntity player, int seat) {
		if (seat <= ShipGeometry.PILOT_SEAT || seat >= ship.geometry().seats().size()) {
			return;
		}
		if (!ship.seat(player, seat)) {
			player.sendMessage(Text.literal("Cette place est prise.").formatted(Formatting.YELLOW), true);
		}
	}

	private static void board(ShipEntity ship, ServerPlayerEntity player, double[] hit) {
		if (player.hasVehicle()) {
			player.stopRiding();
		}
		Vec3d spot = ship.boardingPosition(player.getX(), player.getZ());
		player.requestTeleport(spot.x, spot.y, spot.z);
		player.setVelocity(0, 0, 0);
		player.sendMessage(Text.literal("Bienvenue à bord ! Clic droit sur un banc pour s'asseoir, sur la barre pour piloter.")
				.formatted(Formatting.GOLD), true);
	}

	private static void attack(ShipEntity ship, ServerPlayerEntity player) {
		if (!ShipPermissions.isAdmin(player)) {
			return;
		}
		if (!player.isSneaking()) {
			player.sendMessage(Text.literal("Accroupi + clic gauche pour récupérer le navire.").formatted(Formatting.GRAY), true);
			return;
		}
		ship.removeAllPassengers();
		if (!player.isCreative()) {
			player.getInventory().offerOrDrop(new ItemStack(ship.item()));
		} else if (!player.getInventory().contains(new ItemStack(ship.item()))) {
			player.getInventory().offerOrDrop(new ItemStack(ship.item()));
		}
		ship.discard();
		player.sendMessage(Text.literal("Navire récupéré.").formatted(Formatting.GREEN), true);
	}
}
