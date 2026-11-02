package fr.medievalships.client;

import java.util.List;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.entity.Entity;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.Seating;
import fr.medievalships.core.TentType;
import fr.medievalships.network.SitPayload;
import fr.medievalships.tent.SeatEntity;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;

/**
 * Client-side picking of the props' seats (1.19.0): every frame, after vanilla (and {@link ShipPicker}) computed the
 * crosshair target, the look ray is tested against a small box around each seat of the props near the player (their
 * {@link TentType#seats} turned with the prop's facing, from {@link TentCollisions}' list of the loaded props). A seat
 * nearer than whatever vanilla aims at (the props' invisible anchor block and a seated rider excepted), within
 * {@link Seating#PICK_RANGE}, becomes {@link #use}'s target: a right click sends a {@link SitPayload}, the server checks
 * it and seats the player. Vanilla's crosshair target is left untouched (left click, block outline). Nothing is picked
 * while riding, sneaking or in spectator mode, nor when the server does not know the payload.
 */
public final class SeatPicker {
	/** The seat under the crosshair: its prop's anchor block and its index. */
	public record Target(BlockPos anchor, int seat, double distance) {
	}

	@Nullable
	private static Target current;

	private SeatPicker() {
	}

	@Nullable
	public static Target current() {
		return current;
	}

	/** Called after vanilla computed the crosshair target, every frame. */
	public static void update(MinecraftClient client, float tickDelta) {
		current = null;
		ClientPlayerEntity player = client.player;
		Entity camera = client.getCameraEntity();
		if (player == null || client.world == null || camera != player || player.hasVehicle() || player.isSpectator() || player.isSneaking()
				|| !TentCollisions.any(client.world)) {
			return;
		}
		Vec3d eye = camera.getCameraPosVec(tickDelta);
		Vec3d look = camera.getRotationVec(tickDelta);
		double max = Seating.PICK_RANGE;
		HitResult hit = client.crosshairTarget;
		if (hit != null && hit.getType() != HitResult.Type.MISS && !(hit instanceof BlockHitResult block
				&& client.world.getBlockState(block.getBlockPos()).getBlock() instanceof TentBlock)
				&& !(hit instanceof EntityHitResult e && e.getEntity().getVehicle() instanceof SeatEntity)) {
			// something nearer (a wall, a table's block, a mob...) hides the seats behind it; the props' anchor blocks do
			// not, nor somebody already sitting (his seat is picked through him: the server answers "Cette place est prise.")
			max = Math.min(max, hit.getPos().distanceTo(eye));
		}
		double reach2 = (Seating.PICK_RANGE + 1.0) * (Seating.PICK_RANGE + 1.0);
		Target best = null;
		for (TentCollisions.Placed p : TentCollisions.all(client.world)) {
			List<TentType.Seat> seats = p.type().seats(p.quarter());
			if (seats.isEmpty() || p.extent().squaredMagnitude(eye) > reach2) {
				continue;
			}
			for (int i = 0; i < seats.size(); i++) {
				double[] w = Seating.world(p.pos().getX(), p.pos().getY(), p.pos().getZ(), seats.get(i));
				double t = Seating.rayBox(eye.x, eye.y, eye.z, look.x, look.y, look.z, Seating.pickBox(w[0], w[1], w[2]), max);
				if (!Double.isNaN(t) && (best == null || t < best.distance())) {
					best = new Target(p.pos(), i, t);
				}
			}
		}
		current = best;
	}

	/** A right click: sends the sit request for the seat under the crosshair, if any. */
	public static boolean use(ClientPlayerEntity player) {
		Target t = current;
		if (t == null || player.hasVehicle() || !ClientPlayNetworking.canSend(SitPayload.ID)) {
			return false;
		}
		ClientPlayNetworking.send(new SitPayload(t.anchor(), t.seat()));
		current = null;
		return true;
	}
}
