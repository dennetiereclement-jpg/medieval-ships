package fr.medievalships.network;

import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Server -> client: a drawbridge as the client must draw and collide it. Sent when a player joins or changes world
 * (every bridge of that world), when a bridge's definition changes, and at every transition of its cycle; the
 * client computes the leaves' angle itself from the motion data and the world time (only changes travel). With
 * {@code removed}, the client forgets the bridge.
 *
 * @param id        the bridge id
 * @param removed   forget this bridge
 * @param converted the deck has been converted (closed: real blocks; otherwise the leaves are drawn and solid)
 * @param leaves    the two leaves: frame and captured blocks
 * @param zones     channel geometry (for the preview and the client's diagnostics)
 * @param motion    cycle state and animation parameters
 * @param preview   this player sees the selections, zones and swept volumes drawn
 * @param chains    draw the lifting chains (from the free end of each leaf to anchors over its hinge)
 * @param chainHeight height of the chains' anchors over the hinge (0: the leaf's length plus 1.5)
 */
public record DrawbridgeSyncPayload(String id, boolean removed, boolean converted, List<Leaf> leaves, Zones zones, Motion motion, boolean preview,
		boolean chains, double chainHeight) implements CustomPayload {

	/** One captured block of a leaf: its original position and its block state ({@code minecraft:oak_planks[...]}). */
	public record Block(int x, int y, int z, String state) {
		public static final PacketCodec<ByteBuf, Block> CODEC = PacketCodec.tuple(
				PacketCodecs.VAR_INT, Block::x,
				PacketCodecs.VAR_INT, Block::y,
				PacketCodecs.VAR_INT, Block::z,
				PacketCodecs.STRING, Block::state,
				Block::new);
	}

	/** A leaf: hinge point, hinge axis (u), inward direction (v), selection corners, blocks. */
	public record Leaf(String name, double hx, double hy, double hz, double ux, double uz, double vx, double vz, List<Integer> selection,
			List<Block> blocks) {
		public static final PacketCodec<ByteBuf, Leaf> CODEC = PacketCodec.tuple(
				PacketCodecs.STRING, Leaf::name,
				PacketCodecs.DOUBLE, Leaf::hx,
				PacketCodecs.DOUBLE, Leaf::hy,
				PacketCodecs.DOUBLE, Leaf::hz,
				PacketCodecs.DOUBLE, Leaf::ux,
				PacketCodecs.DOUBLE, Leaf::uz,
				PacketCodecs.DOUBLE, Leaf::vx,
				PacketCodecs.DOUBLE, Leaf::vz,
				PacketCodecs.VAR_INT.collect(PacketCodecs.toList()), Leaf::selection,
				Block.CODEC.collect(PacketCodecs.toList()), Leaf::blocks,
				Leaf::new);
	}

	/** Channel geometry: centre, direction, navigable half width, deck half span, approach, hysteresis, water, underside. */
	public record Zones(double cx, double cz, double dx, double dz, double halfWidth, double halfSpan, double approach, double hysteresis,
			double waterY, double undersideY) {
		public static final PacketCodec<ByteBuf, Zones> CODEC = PacketCodec.tuple(
				PacketCodecs.DOUBLE, Zones::cx,
				PacketCodecs.DOUBLE, Zones::cz,
				PacketCodecs.DOUBLE, Zones::dx,
				PacketCodecs.DOUBLE, Zones::dz,
				PacketCodecs.DOUBLE, Zones::halfWidth,
				PacketCodecs.DOUBLE, Zones::halfSpan,
				PacketCodecs.DOUBLE, Zones::approach,
				PacketCodecs.DOUBLE, Zones::hysteresis,
				PacketCodecs.DOUBLE, Zones::waterY,
				PacketCodecs.DOUBLE, Zones::undersideY,
				Zones::new);
	}

	/**
	 * The cycle: state ordinal, the current move (from this angle to that one, started at this world tick, over this
	 * many ticks, eased as {@code BridgeCycle.ease}), the open angle, whether the deck's blocks are in the world.
	 */
	public record Motion(int state, double moveFrom, double moveTo, long startTick, int moveTicks, double openAngle, boolean blocksInWorld) {
		public static final PacketCodec<ByteBuf, Motion> CODEC = PacketCodec.tuple(
				PacketCodecs.VAR_INT, Motion::state,
				PacketCodecs.DOUBLE, Motion::moveFrom,
				PacketCodecs.DOUBLE, Motion::moveTo,
				PacketCodecs.VAR_LONG, Motion::startTick,
				PacketCodecs.VAR_INT, Motion::moveTicks,
				PacketCodecs.DOUBLE, Motion::openAngle,
				PacketCodecs.BOOLEAN, Motion::blocksInWorld,
				Motion::new);
	}

	public static final CustomPayload.Id<DrawbridgeSyncPayload> ID = new CustomPayload.Id<>(Identifier.of(MedievalShips.MOD_ID, "drawbridge"));

	public static final PacketCodec<RegistryByteBuf, DrawbridgeSyncPayload> CODEC = PacketCodec.tuple(
			PacketCodecs.STRING, DrawbridgeSyncPayload::id,
			PacketCodecs.BOOLEAN, DrawbridgeSyncPayload::removed,
			PacketCodecs.BOOLEAN, DrawbridgeSyncPayload::converted,
			Leaf.CODEC.collect(PacketCodecs.toList()), DrawbridgeSyncPayload::leaves,
			Zones.CODEC, DrawbridgeSyncPayload::zones,
			Motion.CODEC, DrawbridgeSyncPayload::motion,
			PacketCodecs.BOOLEAN, DrawbridgeSyncPayload::preview,
			PacketCodecs.BOOLEAN, DrawbridgeSyncPayload::chains,
			PacketCodecs.DOUBLE, DrawbridgeSyncPayload::chainHeight,
			DrawbridgeSyncPayload::new);

	/** The payload that makes a client forget a bridge. */
	public static DrawbridgeSyncPayload removal(String id) {
		return new DrawbridgeSyncPayload(id, true, false, List.of(), new Zones(0, 0, 0, 1, 1, 1, 1, 0, 0, 0), new Motion(0, 0, 0, 0, 0, 0, true), false,
				false, 0);
	}

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
