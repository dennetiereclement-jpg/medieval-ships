package fr.medievalships.network;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.MedievalShips;

/**
 * Client -> server (1.19.0): the player right-clicked a seat of a prop (a stool of the nomad tavern, the tatami area's
 * bench...): the prop's anchor block and the seat's index in its JSON's {@code "seats"}. The client picked it against
 * small boxes around the seats ({@code SeatPicker}); the server checks everything again before seating the player
 * ({@link fr.medievalships.tent.Seats#handle}).
 */
public record SitPayload(BlockPos anchor, int seat) implements CustomPayload {
	public static final CustomPayload.Id<SitPayload> ID = new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "sit"));

	public static final PacketCodec<RegistryByteBuf, SitPayload> CODEC = PacketCodec.tuple(
			BlockPos.PACKET_CODEC, SitPayload::anchor,
			PacketCodecs.VAR_INT, SitPayload::seat,
			SitPayload::new);

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
