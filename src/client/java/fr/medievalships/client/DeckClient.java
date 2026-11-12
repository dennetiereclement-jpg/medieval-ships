package fr.medievalships.client;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.network.OtherClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.entity.Entity;
import net.minecraft.entity.PositionInterpolator;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.core.DeckFrame;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;
import fr.medievalships.network.DeckFramePayload;
import fr.medievalships.network.DeckPosPayload;
import fr.medievalships.network.DeckTeleportPayload;

/**
 * Players on moving decks in multiplayer (1.30.0), client side (see {@link DeckFrame}):
 * <ul>
 * <li>the hull this client carries its own player with is sent before each of its movement packets
 * ({@link DeckFramePayload}), so that the server keeps him on the same spot of its own hull;</li>
 * <li>the other players standing on a deck are drawn on the hull as this client draws it, at the deck position the
 * server sends ({@link DeckPosPayload}), interpolated in deck coordinates: they never slide nor jitter on a deck under
 * way, whatever the delays;</li>
 * <li>a teleport onto a deck ({@link DeckTeleportPayload}) lands on that spot of the hull drawn here;</li>
 * <li>if the hull moved before the player ticks (a player entity added after the ships, e.g. after a respawn), the
 * player is carried first, so that he always walks against the hull where it is.</li>
 * </ul>
 * Everything is forgotten when leaving a server; the entries of the other players go with their entity.
 */
public final class DeckClient {
	private DeckClient() {
	}

	/** Scratch vector (client thread only). */
	private static final double[] TMP = new double[3];

	// ---- the frame sent for the local player
	@Nullable
	private static ClientPlayerEntity framePlayer;
	/** Ship of the last frame sent, -1 none, -2 nothing sent yet for this player entity. */
	private static int sentShip = -2;
	private static double sentX, sentY, sentZ;
	private static float sentYaw;
	private static int sentAge;

	// ---- a teleport onto a deck
	@Nullable
	private static DeckTeleportPayload pending;
	/** The payload arrived just before its teleport (not a leftover waiting for its ship). */
	private static boolean pendingFresh;
	private static int pendingTicks;
	private static double pendingX, pendingY, pendingZ;

	// ---- the other players standing on decks, by entity id
	private static final Map<Integer, Remote> REMOTE = new HashMap<>();

	private static final class Remote {
		int shipId;
		final DeckFrame.Lerp lerp = new DeckFrame.Lerp();
		/** Ship yaw of the last placement (the body turns with the hull). */
		double appliedYaw = Double.NaN;
		int missing;
	}

	public static void init() {
		ClientPlayNetworking.registerGlobalReceiver(DeckPosPayload.ID, (payload, context) -> receive(payload));
		ClientPlayNetworking.registerGlobalReceiver(DeckTeleportPayload.ID, (payload, context) -> {
			pending = payload;
			pendingFresh = true;
		});
		// after ClientShipEvents (registered before): the hulls have moved, the local player has been carried
		ClientTickEvents.END_WORLD_TICK.register(DeckClient::endWorldTick);
		ClientEntityEvents.ENTITY_UNLOAD.register((entity, world) -> REMOTE.remove(entity.getId()));
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> clear());
		ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> clear());
	}

	public static void clear() {
		REMOTE.clear();
		framePlayer = null;
		sentShip = -2;
		pending = null;
		pendingFresh = false;
	}

	@Nullable
	private static ShipEntity ship(World world, int id) {
		Entity e = world.getEntityById(id);
		return e instanceof ShipEntity ship && !ship.isRemoved() ? ship : null;
	}

	// ------------------------------------------------------------------ the local player

	/**
	 * Start of the local player's tick: if a hull he stands on has already moved this tick (it ticked before him), he
	 * is carried now, before walking (the end-of-tick carry of {@link ClientShipEvents} does the rest).
	 */
	public static void beforePlayerTick(ClientPlayerEntity player) {
		World world = player.getEntityWorld();
		if (world == null || player.hasVehicle() || player.isSpectator()) {
			return;
		}
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved()) {
				continue;
			}
			ShipPose last = ship.lastCarryPose();
			if (last == null) {
				continue;
			}
			ShipPose now = ship.pose();
			if (last.equals(now)) {
				continue;
			}
			DeckFrame.toLocal(last, player.getX(), player.getY(), player.getZ(), TMP);
			if (!ship.geometry().inCarryVolume(TMP[0], TMP[1], TMP[2])) {
				continue;
			}
			ship.setLastCarryPose(now);
			DeckFrame.toWorld(now, TMP[0], TMP[1], TMP[2], TMP);
			player.setPosition(TMP[0], TMP[1], TMP[2]);
			float dyaw = DeckFrame.wrap(now.yaw() - last.yaw());
			if (dyaw != 0) {
				player.setYaw(player.getYaw() + dyaw);
				player.setHeadYaw(player.getHeadYaw() + dyaw);
				player.setBodyYaw(player.bodyYaw + dyaw);
			}
			return;
		}
	}

	/** Just before the local player's movement packet: the hull it is relative to, when it changed. */
	public static void beforeMovementPackets(ClientPlayerEntity player) {
		sendFrame(player, false);
	}

	private static void sendFrame(ClientPlayerEntity player, boolean force) {
		if (!ClientPlayNetworking.canSend(DeckFramePayload.ID)) {
			return;
		}
		if (player != framePlayer) {
			framePlayer = player;
			sentShip = -2;
		}
		ShipEntity ship = null;
		ShipPose pose = null;
		World world = player.getEntityWorld();
		if (world != null && !player.hasVehicle() && !player.isSpectator()) {
			for (ShipEntity s : ShipTracker.ships(world)) {
				if (s.isRemoved()) {
					continue;
				}
				ShipPose p = s.pose();
				DeckFrame.toLocal(p, player.getX(), player.getY(), player.getZ(), TMP);
				if (s.geometry().inCarryVolume(TMP[0], TMP[1], TMP[2])) {
					ship = s;
					pose = p;
					break;
				}
			}
		}
		sentAge++;
		if (ship == null) {
			if (force || sentShip != -1) {
				ClientPlayNetworking.send(new DeckFramePayload(-1, player.getX(), player.getY(), player.getZ(), 0f));
				sentShip = -1;
				sentAge = 0;
			}
			return;
		}
		float yaw = (float) pose.yaw();
		if (force || sentShip != ship.getId() || sentX != pose.x() || sentY != pose.y() || sentZ != pose.z() || sentYaw != yaw
				|| sentAge >= DeckFrame.RESEND_TICKS) {
			ClientPlayNetworking.send(new DeckFramePayload(ship.getId(), pose.x(), pose.y(), pose.z(), yaw));
			sentShip = ship.getId();
			sentX = pose.x();
			sentY = pose.y();
			sentZ = pose.z();
			sentYaw = yaw;
			sentAge = 0;
		}
	}

	/**
	 * A teleport of the local player was just applied (before its confirmation goes): onto a deck, it lands on that
	 * spot of the hull as drawn here; the frame goes again in any case (the server dropped it with the teleport).
	 */
	public static void onTeleportApplied(ClientPlayerEntity player) {
		DeckTeleportPayload p = pending;
		if (p != null && (!pendingFresh || player.hasVehicle())) {
			pending = p = null; // a leftover of an earlier teleport, or seated: nothing to adjust
		}
		pendingFresh = false;
		if (p != null) {
			ShipEntity ship = ship(player.getEntityWorld(), p.shipId());
			if (ship != null) {
				placeOnDeck(player, ship, p);
				pending = null;
			} else {
				// the ship is not known here yet (coming back aboard after a reconnection): placed when it arrives
				pendingTicks = 0;
				pendingX = player.getX();
				pendingY = player.getY();
				pendingZ = player.getZ();
			}
		}
		sendFrame(player, true);
	}

	private static void placeOnDeck(ClientPlayerEntity player, ShipEntity ship, DeckTeleportPayload p) {
		ShipPose pose = ship.pose();
		DeckFrame.toWorld(pose, p.lx(), p.ly(), p.lz(), TMP);
		float yaw = Float.isNaN(p.yaw()) ? player.getYaw() : (float) (pose.yaw() + p.yaw());
		player.setPosition(TMP[0], TMP[1], TMP[2]);
		player.setYaw(yaw);
		player.setHeadYaw(yaw);
		player.setVelocity(Vec3d.ZERO);
		player.setLastPositionAndAngles(new Vec3d(TMP[0], TMP[1], TMP[2]), yaw, player.getPitch());
		ship.setLastCarryPose(pose);
	}

	// ------------------------------------------------------------------ the other players

	private static void receive(DeckPosPayload p) {
		if (p.shipId() < 0) {
			REMOTE.remove(p.entityId());
			return;
		}
		Remote r = REMOTE.get(p.entityId());
		if (r == null || r.shipId != p.shipId()) {
			r = new Remote();
			r.shipId = p.shipId();
			REMOTE.put(p.entityId(), r);
		}
		r.lerp.target(p.lx(), p.ly(), p.lz(), p.yaw(), p.headYaw(), p.pitch());
	}

	/** Is this entity drawn on a deck by this class (tests)? */
	public static boolean onDeck(Entity entity) {
		return REMOTE.containsKey(entity.getId());
	}

	private static void start(PlayerEntity e, Remote r, ShipPose pose) {
		DeckFrame.toLocal(pose, e.getX(), e.getY(), e.getZ(), TMP);
		r.lerp.start(TMP[0], TMP[1], TMP[2], DeckFrame.wrap(e.getYaw() - pose.yaw()), DeckFrame.wrap(e.getHeadYaw() - pose.yaw()), e.getPitch());
		r.appliedYaw = pose.yaw();
	}

	/**
	 * Start of another player's movement tick: one step of his deck interpolation, placed on the hull as it is now.
	 * The previous position is put on the same hull, so that his walking animation and body follow his walk on the
	 * deck only (not the ship's own motion); vanilla's interpolation of his world position is not used meanwhile.
	 */
	public static void beforeRemoteMovement(OtherClientPlayerEntity e) {
		Remote r = REMOTE.get(e.getId());
		if (r == null || e.hasVehicle()) {
			return;
		}
		ShipEntity ship = ship(e.getEntityWorld(), r.shipId);
		if (ship == null) {
			return;
		}
		ShipPose pose = ship.pose();
		if (!r.lerp.started()) {
			start(e, r, pose);
		}
		r.lerp.step();
		DeckFrame.toWorld(pose, r.lerp.lastX, r.lerp.lastY, r.lerp.lastZ, TMP);
		e.lastX = TMP[0];
		e.lastY = TMP[1];
		e.lastZ = TMP[2];
		place(e, r, pose);
		PositionInterpolator interpolator = e.getInterpolator();
		if (interpolator != null) {
			interpolator.clear();
		}
	}

	private static void place(PlayerEntity e, Remote r, ShipPose pose) {
		DeckFrame.toWorld(pose, r.lerp.x, r.lerp.y, r.lerp.z, TMP);
		e.setPosition(TMP[0], TMP[1], TMP[2]);
		if (!Double.isNaN(r.appliedYaw)) {
			e.setBodyYaw(e.bodyYaw + DeckFrame.wrap(pose.yaw() - r.appliedYaw));
		}
		r.appliedYaw = pose.yaw();
		e.setYaw((float) (pose.yaw() + r.lerp.yaw));
		e.setHeadYaw((float) (pose.yaw() + r.lerp.head));
		e.setPitch(r.lerp.pitch);
	}

	/** End of the client tick, after the hulls moved: the other players on decks go onto the hulls where they are now. */
	private static void endWorldTick(ClientWorld world) {
		if (!REMOTE.isEmpty()) {
			Iterator<Map.Entry<Integer, Remote>> it = REMOTE.entrySet().iterator();
			while (it.hasNext()) {
				Map.Entry<Integer, Remote> en = it.next();
				Remote r = en.getValue();
				Entity e = world.getEntityById(en.getKey());
				if (e == null) {
					if (++r.missing > 100) {
						it.remove(); // never came (or went without an unload event)
					}
					continue;
				}
				r.missing = 0;
				if (!(e instanceof OtherClientPlayerEntity other)) {
					it.remove();
					continue;
				}
				ShipEntity ship = ship(world, r.shipId);
				if (ship == null || other.hasVehicle()) {
					continue;
				}
				ShipPose pose = ship.pose();
				if (!r.lerp.started()) {
					start(other, r, pose);
				}
				place(other, r, pose);
			}
		}
		ClientPlayerEntity player = net.minecraft.client.MinecraftClient.getInstance().player;
		if (pending != null && !pendingFresh && player != null) {
			// a teleport onto a deck whose ship was not known yet: placed as soon as it arrives, if the player is still
			// where the teleport put him
			ShipEntity ship = ship(world, pending.shipId());
			double dx = player.getX() - pendingX, dy = player.getY() - pendingY, dz = player.getZ() - pendingZ;
			if (++pendingTicks > 60 || player.hasVehicle() || dx * dx + dy * dy + dz * dz > 6 * 6) {
				pending = null;
			} else if (ship != null) {
				placeOnDeck(player, ship, pending);
				pending = null;
				sendFrame(player, true);
			}
		}
	}
}
