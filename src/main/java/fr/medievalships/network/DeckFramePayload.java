package fr.medievalships.network;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Client -> server (1.30.0), sent just before a movement packet: the hull the client carries its own player with, as it
 * draws it (see {@link fr.medievalships.core.DeckFrame}). {@code shipId} is the ship entity and {@code x y z yaw} its
 * pose on that client; the positions of the movement packets that follow are relative to that hull. {@code shipId}
 * {@code -1}: the player stands on no deck any more, {@code x y z} is then his own world position.
 */
public record DeckFramePayload(int shipId, double x, double y, double z, float yaw) implements CustomPayload {
	public static final CustomPayload.Id<DeckFramePayload> ID = new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "deck_frame"));

	public static final PacketCodec<RegistryByteBuf, DeckFramePayload> CODEC = PacketCodec.tuple(
			PacketCodecs.VAR_INT, DeckFramePayload::shipId,
			PacketCodecs.DOUBLE, DeckFramePayload::x,
			PacketCodecs.DOUBLE, DeckFramePayload::y,
			PacketCodecs.DOUBLE, DeckFramePayload::z,
			PacketCodecs.FLOAT, DeckFramePayload::yaw,
			DeckFramePayload::new);

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
