package fr.medievalships.network;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Server -> client (1.30.0), sent just before a teleport of that client's player onto a deck (stepping off a seat,
 * coming back aboard after a reconnection, a command...): the target in the ship's local frame. The client puts its
 * player on that spot of the hull as it draws it, a few ticks behind the server's: the world position of the teleport
 * would land him off the spot (inside a wall, over the rail) on a ship under way.
 */
public record DeckTeleportPayload(int shipId, float lx, float ly, float lz, float yaw) implements CustomPayload {
	public static final CustomPayload.Id<DeckTeleportPayload> ID = new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "deck_teleport"));

	public static final PacketCodec<RegistryByteBuf, DeckTeleportPayload> CODEC = PacketCodec.tuple(
			PacketCodecs.VAR_INT, DeckTeleportPayload::shipId,
			PacketCodecs.FLOAT, DeckTeleportPayload::lx,
			PacketCodecs.FLOAT, DeckTeleportPayload::ly,
			PacketCodecs.FLOAT, DeckTeleportPayload::lz,
			PacketCodecs.FLOAT, DeckTeleportPayload::yaw,
			DeckTeleportPayload::new);

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
