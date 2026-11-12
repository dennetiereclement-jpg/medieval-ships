package fr.medievalships.client.mixin.sync;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayNetworkHandler;
import net.minecraft.network.packet.s2c.play.PlayerPositionLookS2CPacket;

import fr.medievalships.client.DeckClient;

/**
 * A teleport onto a deck (1.30.0) lands on that spot of the hull as this client draws it, and the client's frame goes to
 * the server before the teleport's confirmation (see {@link DeckClient#onTeleportApplied}).
 */
@Mixin(ClientPlayNetworkHandler.class)
abstract class ClientPlayNetworkHandlerDeckMixin {
	@Inject(method = "onPlayerPositionLook", at = @At(value = "INVOKE",
			target = "Lnet/minecraft/network/ClientConnection;send(Lnet/minecraft/network/packet/Packet;)V", ordinal = 0))
	private void medievalships$deckTeleport(PlayerPositionLookS2CPacket packet, CallbackInfo ci) {
		MinecraftClient client = MinecraftClient.getInstance();
		if (client.player != null) {
			DeckClient.onTeleportApplied(client.player);
		}
	}
}
