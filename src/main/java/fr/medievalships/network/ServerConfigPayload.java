package fr.medievalships.network;

import java.util.ArrayList;
import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ServerSettings;
import fr.medievalships.core.ShipConfig;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ConfigManager;

/**
 * Server -> client: the settings of {@code config/medievalships.json} the client needs to show the same thing as the
 * server does (sent when a player joins and after {@code /ship reload}): who may place what (the client compares
 * with its own permission level, which the game keeps up to date), and per vessel the altitude ceiling (placement
 * preview), the bank angle (drawn on the client) and the gait speeds (the pilot's panel). See
 * {@link fr.medievalships.data.SyncedConfig}.
 */
public record ServerConfigPayload(int adminPermissionLevel, boolean placeRequiresAdmin, List<String> placeAdminOnly,
		List<String> placeAllowedPlayers, List<Vessel> vessels) implements CustomPayload {

	/** One vessel's values; {@code maxAltitude} and {@code bankAngle} are 0 for a vessel that does not fly. */
	public record Vessel(String id, double maxAltitude, double bankAngle, double slowSpeed, double normalSpeed, double fastSpeed) {
		public static final PacketCodec<ByteBuf, Vessel> CODEC = PacketCodec.tuple(
				PacketCodecs.STRING, Vessel::id,
				PacketCodecs.DOUBLE, Vessel::maxAltitude,
				PacketCodecs.DOUBLE, Vessel::bankAngle,
				PacketCodecs.DOUBLE, Vessel::slowSpeed,
				PacketCodecs.DOUBLE, Vessel::normalSpeed,
				PacketCodecs.DOUBLE, Vessel::fastSpeed,
				Vessel::new);

		/** The values of this vessel in a config. */
		public static Vessel of(ShipType type, ShipConfig c) {
			return new Vessel(type.id(), c.flight == null ? 0 : c.flight.maxAltitude, c.flight == null ? 0 : c.flight.bankAngle,
					c.slowSpeed, c.normalSpeed, c.fastSpeed);
		}
	}

	public static final CustomPayload.Id<ServerConfigPayload> ID =
			new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "server_config"));

	public static final PacketCodec<RegistryByteBuf, ServerConfigPayload> CODEC = PacketCodec.tuple(
			PacketCodecs.VAR_INT, ServerConfigPayload::adminPermissionLevel,
			PacketCodecs.BOOLEAN, ServerConfigPayload::placeRequiresAdmin,
			PacketCodecs.STRING.collect(PacketCodecs.toList()), ServerConfigPayload::placeAdminOnly,
			PacketCodecs.STRING.collect(PacketCodecs.toList()), ServerConfigPayload::placeAllowedPlayers,
			Vessel.CODEC.collect(PacketCodecs.toList()), ServerConfigPayload::vessels,
			ServerConfigPayload::new);

	/** The server's current settings. */
	public static ServerConfigPayload current() {
		ServerSettings s = ConfigManager.server();
		List<Vessel> vessels = new ArrayList<>();
		for (ShipType t : Ships.ALL) {
			vessels.add(Vessel.of(t, ConfigManager.ship(t)));
		}
		return new ServerConfigPayload(s.adminPermissionLevel, s.placeRequiresAdmin, List.copyOf(s.placeAdminOnly),
				List.copyOf(s.placeAllowedPlayers), vessels);
	}

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
