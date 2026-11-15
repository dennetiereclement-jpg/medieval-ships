package fr.medievalships.forge;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.packet.CustomPayload;

import fr.medievalships.MedievalShips;

/**
 * Server to client (1.34.0): the divine forge's interface refreshed ({@link ForgeMenu}) for the open screen of sync id
 * {@code syncId}, after a click on "Forger" or when what it shows changed (the inventory, the forge's business).
 */
public record ForgeMenuPayload(int syncId, ForgeMenu menu) implements CustomPayload {
	public static final CustomPayload.Id<ForgeMenuPayload> ID = new CustomPayload.Id<>(MedievalShips.id("forge_menu"));
	public static final PacketCodec<RegistryByteBuf, ForgeMenuPayload> CODEC = PacketCodec.of(ForgeMenuPayload::write, ForgeMenuPayload::read);

	private void write(RegistryByteBuf buf) {
		buf.writeVarInt(syncId);
		menu.write(buf);
	}

	private static ForgeMenuPayload read(RegistryByteBuf buf) {
		return new ForgeMenuPayload(buf.readVarInt(), ForgeMenu.read(buf));
	}

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
