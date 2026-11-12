package fr.medievalships.entity;

import java.util.Collection;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.EntityTrackingEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityPosition;
import net.minecraft.network.packet.c2s.play.PlayerMoveC2SPacket;
import net.minecraft.network.packet.s2c.play.PositionFlag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.DeckFrame;
import fr.medievalships.core.ShipPose;
import fr.medievalships.network.DeckFramePayload;
import fr.medievalships.network.DeckPosPayload;
import fr.medievalships.network.DeckTeleportPayload;

/**
 * Players on moving decks in multiplayer (1.30.0), server side; see {@link DeckFrame} for the principle.
 *
 * <ul>
 * <li>A client reports the hull it carries its player with ({@link DeckFramePayload}); the positions of its movement
 * packets are then put on the same spot of the server's hull ({@link #onMove}), and the server carries that player
 * with its hull between two packets like a mob ({@link #carriedByServer}). The server copy of the player is exactly where
 * he stands on the deck, whatever the delay of his connection: the other players, the interactions, the safety nets and
 * the data saved with him all see the right spot.</li>
 * <li>The deck position of every player standing on a ship goes to the players tracking him ({@link DeckPosPayload}),
 * who draw him on the hull as they draw it: no sliding, no jitter, whatever their own delay.</li>
 * <li>A teleport onto a deck (seat left, back aboard, command) is also sent in deck coordinates
 * ({@link DeckTeleportPayload}) so that the client lands on the spot of the hull it draws.</li>
 * </ul>
 *
 * The state lives in the {@link ServerPlayerEntity} itself ({@link Holder}): a player entity replaced (respawn, death,
 * another character of a multi-character mod) starts with none, nothing leaks from one to the next. Cost: a few
 * arithmetic operations per player and per tick, packets only while someone walks on a deck (a player standing still
 * on a moving deck does not change his deck position).
 */
public final class DeckSync {
	private DeckSync() {
	}

	/** Per-player state, kept by the player entity (a mixin adds the field). */
	public static final class State {
		/** The ship whose frame the client reports, or null (its positions are world positions). */
		@Nullable
		ShipEntity frameShip;
		double fx, fy, fz;
		float fyaw;
		/** The last position the client reported, as it sent it (its own world space). */
		double rawX, rawY, rawZ;
		boolean hasRaw;
		/** The ship and deck position last sent to the trackers ({x, y, z, yaw, head, pitch}). */
		@Nullable
		ShipEntity relayShip;
		final double[] relayed = new double[6];
		int relayAge;
		/** Server tick of the last check of the player's anchor ({@link DeckAnchors}). */
		int anchorTick;

		ShipPose frame() {
			return new ShipPose(fx, fy, fz, fyaw);
		}
	}

	/** Implemented by {@link ServerPlayerEntity} (mixin): the deck state of that very entity. */
	public interface Holder {
		@Nullable
		State medievalships$deck();

		void medievalships$setDeck(@Nullable State state);
	}

	static State state(ServerPlayerEntity player) {
		Holder h = (Holder) player;
		State s = h.medievalships$deck();
		if (s == null) {
			s = new State();
			h.medievalships$setDeck(s);
		}
		return s;
	}

	@Nullable
	static State peek(ServerPlayerEntity player) {
		return ((Holder) player).medievalships$deck();
	}

	/** The ship whose frame this player's client reports (tests, debugging), or null. */
	@Nullable
	public static ShipEntity frameShip(ServerPlayerEntity player) {
		State s = peek(player);
		return s == null ? null : s.frameShip;
	}

	public static void init() {
		PayloadTypeRegistry.playC2S().register(DeckFramePayload.ID, DeckFramePayload.CODEC);
		PayloadTypeRegistry.playS2C().register(DeckPosPayload.ID, DeckPosPayload.CODEC);
		PayloadTypeRegistry.playS2C().register(DeckTeleportPayload.ID, DeckTeleportPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(DeckFramePayload.ID, (payload, context) -> onFrame(context.player(), payload));
		// a player coming into view of another one standing on a deck: where he stands, at once
		EntityTrackingEvents.START_TRACKING.register((entity, observer) -> {
			if (entity instanceof ServerPlayerEntity player) {
				State s = peek(player);
				if (s != null && s.relayShip != null && !s.relayShip.isRemoved()) {
					send(observer, payload(player, s.relayShip, s.relayed));
				}
			}
		});
		// another world: the frame and the deck of the old one mean nothing there
		ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD.register((player, origin, destination) -> reset(player));
		ServerTickEvents.END_SERVER_TICK.register(DeckSync::endTick);
	}

	/** Forgets the frame and the deck of a player (teleport to another world...). */
	public static void reset(ServerPlayerEntity player) {
		State s = peek(player);
		if (s != null) {
			s.frameShip = null;
			s.hasRaw = false;
			s.relayShip = null;
		}
	}

	// ------------------------------------------------------------------ client frames

	static void onFrame(ServerPlayerEntity player, DeckFramePayload payload) {
		State s = state(player);
		ServerWorld world = player.getEntityWorld();
		if (payload.shipId() < 0) {
			if (s.frameShip != null) {
				s.frameShip = null;
				// stepping off a deck under way: the client's own world position is where the player really is (it
				// differs from the server copy kept on the server's hull by the delay of that client)
				Vec3d at = new Vec3d(payload.x(), payload.y(), payload.z());
				if (!player.hasVehicle() && at.isFinite() && player.getEntityPos().squaredDistanceTo(at) < 16 * 16) {
					Box box = player.getBoundingBox().offset(at.subtract(player.getEntityPos()));
					if (world.isSpaceEmpty(player, box)) {
						player.setPosition(at);
						player.networkHandler.syncWithPlayerPosition();
					}
				}
			}
			return;
		}
		Entity e = world.getEntityById(payload.shipId());
		if (!(e instanceof ShipEntity ship) || ship.isRemoved() || player.hasVehicle() || player.isSpectator()) {
			s.frameShip = null;
			return;
		}
		ShipPose client = new ShipPose(payload.x(), payload.y(), payload.z(), payload.yaw());
		ShipPose server = ship.pose();
		if (!DeckFrame.plausible(client, server)) {
			s.frameShip = null;
			return;
		}
		boolean start = s.frameShip != ship;
		s.frameShip = ship;
		s.fx = payload.x();
		s.fy = payload.y();
		s.fz = payload.z();
		s.fyaw = payload.yaw();
		if (start && s.hasRaw) {
			// stepping aboard: the server copy goes at once to the spot of its own hull where the client stands
			double[] l = new double[3];
			DeckFrame.toLocal(client, s.rawX, s.rawY, s.rawZ, l);
			if (ship.geometry().inCarryVolume(l[0], l[1], l[2])) {
				DeckFrame.toWorld(server, l[0], l[1], l[2], l);
				if (player.squaredDistanceTo(l[0], l[1], l[2]) < 16 * 16) {
					player.setPosition(l[0], l[1], l[2]);
					player.networkHandler.syncWithPlayerPosition();
				}
			}
		}
	}

	/**
	 * A movement packet of this player, on the server thread: with a frame, its position (and yaw) go to the same spot
	 * of the server's hull. Returns the packet to process (the same one when nothing changes).
	 */
	public static PlayerMoveC2SPacket onMove(ServerPlayerEntity player, PlayerMoveC2SPacket packet) {
		State s = peek(player);
		if (s == null) {
			return packet;
		}
		boolean pos = packet.changesPosition(), look = packet.changesLook();
		double x = packet.getX(player.getX()), y = packet.getY(player.getY()), z = packet.getZ(player.getZ());
		if (pos) {
			s.rawX = x;
			s.rawY = y;
			s.rawZ = z;
			s.hasRaw = true;
		}
		ShipEntity ship = s.frameShip;
		if (ship == null || (!pos && !look)) {
			return packet;
		}
		if (ship.isRemoved() || ship.getEntityWorld() != player.getEntityWorld() || player.hasVehicle()) {
			s.frameShip = null;
			return packet;
		}
		ShipPose client = s.frame();
		ShipPose server = ship.pose();
		if (pos) {
			double[] l = new double[3];
			DeckFrame.toLocal(client, x, y, z, l);
			if (!ship.geometry().inCarryVolume(l[0], l[1], l[2])) {
				// off the deck without a word (a stale frame): a world position
				s.frameShip = null;
				return packet;
			}
			DeckFrame.toWorld(server, l[0], l[1], l[2], l);
			x = l[0];
			y = l[1];
			z = l[2];
		}
		float yaw = look ? DeckFrame.reframeYaw(client, server, packet.getYaw(player.getYaw())) : player.getYaw();
		float pitch = packet.getPitch(player.getPitch());
		if (pos && look) {
			return new PlayerMoveC2SPacket.Full(x, y, z, yaw, pitch, packet.isOnGround(), packet.horizontalCollision());
		} else if (pos) {
			return new PlayerMoveC2SPacket.PositionAndOnGround(x, y, z, packet.isOnGround(), packet.horizontalCollision());
		}
		return new PlayerMoveC2SPacket.LookAndOnGround(yaw, pitch, packet.isOnGround(), packet.horizontalCollision());
	}

	/**
	 * Does the server move this entity with the ship's hull ({@link ShipEntity} carries mobs, items and these players)?
	 * A player whose client reports this ship's frame, and a fake player (no client: a bot of another mod, a test).
	 */
	public static boolean carriedByServer(Entity entity, ShipEntity ship) {
		if (!(entity instanceof ServerPlayerEntity player) || player.isSpectator()) {
			return false;
		}
		if (player instanceof FakePlayer) {
			return true;
		}
		State s = peek(player);
		return s != null && s.frameShip == ship;
	}

	// ------------------------------------------------------------------ teleports onto a deck

	/**
	 * A teleport of this player is about to be sent: the frame is forgotten (the client sends it again with its
	 * confirmation), and a target on a deck also goes in deck coordinates.
	 */
	public static void beforeTeleport(ServerPlayerEntity player, EntityPosition target, Set<PositionFlag> flags) {
		State s = peek(player);
		if (s != null) {
			s.frameShip = null;
			s.hasRaw = false;
		}
		if (player instanceof FakePlayer || flags.contains(PositionFlag.X) || flags.contains(PositionFlag.Y) || flags.contains(PositionFlag.Z)
				|| !ServerPlayNetworking.canSend(player, DeckTeleportPayload.ID)) {
			return;
		}
		Vec3d p = target.position();
		double[] l = new double[3];
		for (ShipEntity ship : ShipTracker.ships(player.getEntityWorld())) {
			if (ship.isRemoved()) {
				continue;
			}
			ShipPose pose = ship.pose();
			DeckFrame.toLocal(pose, p.x, p.y, p.z, l);
			if (ship.geometry().inCarryVolume(l[0], l[1], l[2])) {
				float yaw = flags.contains(PositionFlag.Y_ROT) ? Float.NaN : DeckFrame.wrap(target.yaw() - pose.yaw());
				ServerPlayNetworking.send(player, new DeckTeleportPayload(ship.getId(), (float) l[0], (float) l[1], (float) l[2], yaw));
				return;
			}
		}
	}

	// ------------------------------------------------------------------ deck positions to the other clients

	private static void endTick(MinecraftServer server) {
		int now = server.getTicks();
		for (ServerWorld world : server.getWorlds()) {
			if (ShipTracker.ships(world).length == 0) {
				continue;
			}
			// the world's players, fake ones included (they are not in the player manager's list)
			for (ServerPlayerEntity player : world.getPlayers()) {
				relay(player, now);
			}
		}
	}

	/** The ship whose deck this player stands on (not seated), or null. */
	@Nullable
	public static ShipEntity standingOn(ServerPlayerEntity player) {
		if (player.hasVehicle() || player.isSpectator() || player.isRemoved()) {
			return null;
		}
		State s = peek(player);
		if (s != null && s.frameShip != null && !s.frameShip.isRemoved() && s.frameShip.getEntityWorld() == player.getEntityWorld()) {
			return s.frameShip;
		}
		return ShipTracker.shipUnder(player);
	}

	private static void relay(ServerPlayerEntity player, int now) {
		ShipEntity ship = standingOn(player);
		State s = ship == null ? peek(player) : state(player);
		if (s == null) {
			return;
		}
		if (ship == null) {
			if (s.relayShip != null) {
				s.relayShip = null;
				sendToTrackers(player, DeckPosPayload.left(player.getId()));
			}
			return;
		}
		ShipPose pose = ship.pose();
		double[] l = new double[3];
		DeckFrame.toLocal(pose, player.getX(), player.getY(), player.getZ(), l);
		float yaw = DeckFrame.wrap(player.getYaw() - pose.yaw());
		float head = DeckFrame.wrap(player.getHeadYaw() - pose.yaw());
		float pitch = player.getPitch();
		if (s.relayShip == ship && now - s.relayAge < DeckFrame.RESEND_TICKS && !DeckFrame.changed(s.relayed, l[0], l[1], l[2], yaw, head, pitch)) {
			return;
		}
		s.relayShip = ship;
		s.relayAge = now;
		double[] r = s.relayed;
		r[0] = l[0];
		r[1] = l[1];
		r[2] = l[2];
		r[3] = yaw;
		r[4] = head;
		r[5] = pitch;
		sendToTrackers(player, payload(player, ship, r));
	}

	private static DeckPosPayload payload(ServerPlayerEntity player, ShipEntity ship, double[] r) {
		return new DeckPosPayload(player.getId(), ship.getId(), (float) r[0], (float) r[1], (float) r[2], (float) r[3], (float) r[4], (float) r[5]);
	}

	private static void sendToTrackers(ServerPlayerEntity player, DeckPosPayload payload) {
		Collection<ServerPlayerEntity> trackers = PlayerLookup.tracking(player);
		for (ServerPlayerEntity observer : trackers) {
			send(observer, payload);
		}
	}

	private static void send(ServerPlayerEntity observer, DeckPosPayload payload) {
		if (!(observer instanceof FakePlayer) && ServerPlayNetworking.canSend(observer, DeckPosPayload.ID)) {
			ServerPlayNetworking.send(observer, payload);
		}
	}
}
