package fr.medievalships.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.util.Hand;

import fr.medievalships.client.ShipPicker;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.network.ShipInteractPayload;

/**
 * Right / left clicks on a ship part go to the server through {@link ShipInteractPayload}
 * (the vanilla packets are validated against the small entity box).
 */
@Mixin(MinecraftClient.class)
abstract class MinecraftClientMixin {
	@Shadow
	public ClientPlayerEntity player;
	@Shadow
	private int itemUseCooldown;

	@Inject(method = "doItemUse", at = @At("HEAD"), cancellable = true)
	private void medievalships$useShip(CallbackInfo ci) {
		ShipPicker.Target t = ShipPicker.current();
		if (t == null || player == null || t.pick().kind() == ShipGeometry.PickKind.DECK) {
			return; // on the deck vanilla behaviour applies (eating, drinking...), never reaching the water below
		}
		send(t, ShipInteractPayload.USE);
		itemUseCooldown = 4;
		player.swingHand(Hand.MAIN_HAND);
		ci.cancel();
	}

	@Inject(method = "doAttack", at = @At("HEAD"), cancellable = true)
	private void medievalships$attackShip(CallbackInfoReturnable<Boolean> cir) {
		ShipPicker.Target t = ShipPicker.current();
		if (t == null || player == null) {
			return;
		}
		send(t, ShipInteractPayload.ATTACK);
		player.swingHand(Hand.MAIN_HAND);
		cir.setReturnValue(false);
	}

	private static void send(ShipPicker.Target t, int action) {
		ShipGeometry.Pick p = t.pick();
		ClientPlayNetworking.send(new ShipInteractPayload(t.ship().getId(), action, p.kind().ordinal(), p.seat(),
				(float) p.lx(), (float) p.ly(), (float) p.lz()));
	}
}
