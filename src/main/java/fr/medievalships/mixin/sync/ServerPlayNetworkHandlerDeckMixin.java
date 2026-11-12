package fr.medievalships.mixin.sync;

import java.util.Set;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.entity.EntityPosition;
import net.minecraft.network.packet.c2s.play.PlayerMoveC2SPacket;
import net.minecraft.network.packet.s2c.play.PositionFlag;
import net.minecraft.server.network.ServerPlayNetworkHandler;
import net.minecraft.server.network.ServerPlayerEntity;

import fr.medievalships.entity.DeckSync;

/**
 * Players on moving decks (1.30.0, see {@link DeckSync}): the movement packets of a client that reports the hull it
 * carries its player with are put on the same spot of the server's hull, and a teleport onto a deck also goes to the
 * client in deck coordinates.
 */
@Mixin(ServerPlayNetworkHandler.class)
abstract class ServerPlayNetworkHandlerDeckMixin {
	@Shadow
	public ServerPlayerEntity player;

	/** On the server thread only (the packet first arrives on the network thread, which hands it over unchanged). */
	@ModifyVariable(method = "onPlayerMove", at = @At("HEAD"), argsOnly = true)
	private PlayerMoveC2SPacket medievalships$deckFrame(PlayerMoveC2SPacket packet) {
		if (player == null || !player.getEntityWorld().getServer().isOnThread()) {
			return packet;
		}
		return DeckSync.onMove(player, packet);
	}

	@Inject(method = "requestTeleport(Lnet/minecraft/entity/EntityPosition;Ljava/util/Set;)V", at = @At("HEAD"))
	private void medievalships$deckTeleport(EntityPosition pos, Set<PositionFlag> flags, CallbackInfo ci) {
		if (player != null) {
			DeckSync.beforeTeleport(player, pos, flags);
		}
	}
}
