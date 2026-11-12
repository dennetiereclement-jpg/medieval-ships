package fr.medievalships.network;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Server -> clients (1.30.0): where a player stands on a deck, in that ship's local frame ({@code lx ly lz}, feet),
 * his yaw and head yaw relative to the hull, his pitch. The clients draw him there on the hull as they draw it, so he
 * never slides on a moving deck (the vanilla world position of a player is sent every other tick and interpolated on
 * its own, out of step with the hull). Sent to the players tracking him when it changes, and again every second;
 * {@code shipId} {@code -1}: he left the deck (the vanilla position applies again).
 */
public record DeckPosPayload(int entityId, int shipId, float lx, float ly, float lz, float yaw, float headYaw, float pitch)
		implements CustomPayload {
	public static final CustomPayload.Id<DeckPosPayload> ID = new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "deck_pos"));

	public static final PacketCodec<RegistryByteBuf, DeckPosPayload> CODEC = PacketCodec.tuple(
			PacketCodecs.VAR_INT, DeckPosPayload::entityId,
			PacketCodecs.VAR_INT, DeckPosPayload::shipId,
			PacketCodecs.FLOAT, DeckPosPayload::lx,
			PacketCodecs.FLOAT, DeckPosPayload::ly,
			PacketCodecs.FLOAT, DeckPosPayload::lz,
			PacketCodecs.FLOAT, DeckPosPayload::yaw,
			PacketCodecs.FLOAT, DeckPosPayload::headYaw,
			PacketCodecs.FLOAT, DeckPosPayload::pitch,
			DeckPosPayload::new);

	public static DeckPosPayload left(int entityId) {
		return new DeckPosPayload(entityId, -1, 0, 0, 0, 0, 0, 0);
	}

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
