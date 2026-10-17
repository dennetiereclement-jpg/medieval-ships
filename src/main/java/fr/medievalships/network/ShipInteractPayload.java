package fr.medievalships.network;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Client -> server: the player used (right click) or attacked (left click) a part of a ship.
 * The hit point is in ship-local coordinates. The vanilla interaction packets cannot be used:
 * the server checks them against the small entity box, not against a 20 block hull.
 */
public record ShipInteractPayload(int entityId, int action, int kind, int seat, float lx, float ly, float lz)
		implements CustomPayload {
	public static final int USE = 0;
	public static final int ATTACK = 1;

	public static final CustomPayload.Id<ShipInteractPayload> ID =
			new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "interact"));

	public static final PacketCodec<RegistryByteBuf, ShipInteractPayload> CODEC = PacketCodec.tuple(
			PacketCodecs.VAR_INT, ShipInteractPayload::entityId,
			PacketCodecs.VAR_INT, ShipInteractPayload::action,
			PacketCodecs.VAR_INT, ShipInteractPayload::kind,
			PacketCodecs.VAR_INT, ShipInteractPayload::seat,
			PacketCodecs.FLOAT, ShipInteractPayload::lx,
			PacketCodecs.FLOAT, ShipInteractPayload::ly,
			PacketCodecs.FLOAT, ShipInteractPayload::lz,
			ShipInteractPayload::new);

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
