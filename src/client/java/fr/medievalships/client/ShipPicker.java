package fr.medievalships.client;

import org.jetbrains.annotations.Nullable;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.ShipGeometry;
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * Client-side precise targeting of ships: the hull is 20 blocks long but the entity box is
 * small, so the crosshair target is computed against the real hull, seats and helm.
 */
public final class ShipPicker {
	public record Target(GalleyEntity ship, ShipGeometry.Pick pick) {
	}

	@Nullable
	private static Target current;

	private ShipPicker() {
	}

	@Nullable
	public static Target current() {
		MinecraftClient client = MinecraftClient.getInstance();
		if (current == null || current.ship().isRemoved()
				|| !(client.crosshairTarget instanceof EntityHitResult hit) || hit.getEntity() != current.ship()) {
			return null;
		}
		return current;
	}

	/** Called after vanilla computed the crosshair target: replace it if a ship part is closer. */
	public static void update(MinecraftClient client, float tickDelta) {
		current = null;
		Entity camera = client.getCameraEntity();
		if (camera == null || client.world == null || !(client.player instanceof PlayerEntity player)) {
			return;
		}
		GalleyEntity[] ships = ShipTracker.ships(client.world);
		if (ships.length == 0) {
			return;
		}
		Vec3d eye = camera.getCameraPosVec(tickDelta);
		Vec3d look = camera.getRotationVec(tickDelta);
		double reach = Math.max(player.getBlockInteractionRange(), player.getEntityInteractionRange());
		double vanilla = Double.MAX_VALUE;
		HitResult hit = client.crosshairTarget;
		if (hit != null && hit.getType() != HitResult.Type.MISS) {
			vanilla = hit.getPos().distanceTo(eye);
		}
		Target best = null;
		double bestDist = Math.min(reach, vanilla);
		for (GalleyEntity ship : ships) {
			if (ship.isRemoved() || camera.getRootVehicle() == ship && ship.seatOf(camera) == ShipGeometry.PILOT_SEAT) {
				continue;
			}
			ShipGeometry.Pick pick = ShipGeometry.pick(ship.pose(), eye.x, eye.y, eye.z, look.x, look.y, look.z, bestDist);
			if (pick != null && pick.distance() < bestDist) {
				best = new Target(ship, pick);
				bestDist = pick.distance();
			}
		}
		if (best != null) {
			current = best;
			client.crosshairTarget = new EntityHitResult(best.ship(), eye.add(look.multiply(bestDist)));
		}
	}
}
