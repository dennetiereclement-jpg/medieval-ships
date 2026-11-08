package fr.medievalships.bridge;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerWorldEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipPhysics;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.LeafFrame;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.network.DrawbridgeSyncPayload;

/**
 * The drawbridges of the server: loaded from {@link DrawbridgeData} when it starts, ticked every server tick, saved
 * when they change, sent to the clients when they join, change world or when a bridge changes. Also the API the
 * ships use ({@link #gate}) and scripts use ({@link #request}).
 */
public final class Drawbridges {
	private static final Map<String, Drawbridge> BRIDGES = new LinkedHashMap<>();
	private static boolean loaded;

	private Drawbridges() {
	}

	public static void init() {
		PayloadTypeRegistry.playS2C().register(DrawbridgeSyncPayload.ID, DrawbridgeSyncPayload.CODEC);
		ServerLifecycleEvents.SERVER_STARTED.register(Drawbridges::load);
		ServerLifecycleEvents.SERVER_STOPPING.register(Drawbridges::save);
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			BRIDGES.clear();
			loaded = false;
		});
		ServerTickEvents.END_SERVER_TICK.register(Drawbridges::serverTick);
		ServerWorldEvents.UNLOAD.register((server, world) -> DrawbridgeCollisions.clear(world));
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sendAll(handler.player));
		ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD.register((player, origin, destination) -> sendAll(player));
	}

	private static void load(MinecraftServer server) {
		BRIDGES.clear();
		int n = 0;
		for (Drawbridge.Saved saved : DrawbridgeData.get(server).bridges().values()) {
			try {
				Drawbridge b = new Drawbridge(saved);
				BRIDGES.put(b.id, b);
				n++;
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Drawbridge {} could not be loaded", saved == null ? "?" : saved.id, e);
			}
		}
		loaded = true;
		if (n > 0) {
			MedievalShips.LOGGER.info("{} drawbridge(s) loaded", n);
		}
	}

	/** Writes the bridges that changed into the world's data. */
	public static void save(MinecraftServer server) {
		DrawbridgeData data = null;
		for (Drawbridge b : BRIDGES.values()) {
			if (!b.dirty) {
				continue;
			}
			if (data == null) {
				data = DrawbridgeData.get(server);
			}
			data.put(b.toSaved());
			b.dirty = false;
		}
	}

	public static Collection<Drawbridge> all() {
		return BRIDGES.values();
	}

	@Nullable
	public static Drawbridge get(String id) {
		return id == null ? null : BRIDGES.get(id);
	}

	public static List<Drawbridge> inWorld(ServerWorld world) {
		List<Drawbridge> out = new ArrayList<>();
		for (Drawbridge b : BRIDGES.values()) {
			if (b.dimension.equals(world.getRegistryKey())) {
				out.add(b);
			}
		}
		return out;
	}

	/** Creates an empty bridge in a world (its leaves still to select). */
	public static Drawbridge create(MinecraftServer server, String id, ServerWorld world) {
		Drawbridge b = Drawbridge.create(id, world.getRegistryKey(), ConfigManager.drawbridges());
		BRIDGES.put(id, b);
		b.dirty = true;
		save(server);
		return b;
	}

	/** Deletes a bridge: its deck is restored first if the leaves are out; only its own blocks are touched. */
	public static void delete(MinecraftServer server, Drawbridge b) {
		ServerWorld world = server.getWorld(b.dimension);
		if (world != null) {
			if (b.converted()) {
				b.restore(world);
			}
			DrawbridgeCollisions.remove(world, b);
			for (ServerPlayerEntity p : world.getPlayers()) {
				send(p, DrawbridgeSyncPayload.removal(b.id));
			}
		}
		BRIDGES.remove(b.id);
		DrawbridgeData.get(server).remove(b.id);
	}

	private static void serverTick(MinecraftServer server) {
		if (!loaded || BRIDGES.isEmpty()) {
			return;
		}
		for (Drawbridge b : new ArrayList<>(BRIDGES.values())) {
			ServerWorld world = server.getWorld(b.dimension);
			if (world == null) {
				continue;
			}
			try {
				b.tick(world, world.getTime());
			} catch (Exception e) {
				MedievalShips.LOGGER.error("Drawbridge {}: error in its tick", b.id, e);
			}
		}
		save(server);
	}

	/**
	 * The ships' hook: limits the speed of an autopilot vessel that needs a bridge not yet open (or that cannot pass
	 * at all) so that it waits before the deck, and warns a player at the helm. Cheap when there is no bridge.
	 */
	public static ShipPhysics.Controls gate(ShipEntity ship, ShipPose pose, ShipPhysics.Controls controls) {
		if (BRIDGES.isEmpty() || !(ship.getEntityWorld() instanceof ServerWorld world)) {
			return controls;
		}
		long now = world.getTime();
		for (Drawbridge b : BRIDGES.values()) {
			if (b.converted() && b.dimension.equals(world.getRegistryKey()) && b.analysed()) {
				controls = b.gate(ship, pose, controls, now);
			}
		}
		return controls;
	}

	/**
	 * A scripted request (a quest's private vessel, another mod): the bridge opens and stays open for the given time,
	 * under the usual safety checks. {@code key} names the requester (a vessel name, a script id); asking again with
	 * the same key extends it.
	 */
	public static void request(Drawbridge b, String key, int seconds, ServerWorld world) {
		b.requests.put(key, world.getTime() + Math.max(1, seconds) * 20L);
	}

	/** Withdraws a scripted request. */
	public static boolean cancelRequest(Drawbridge b, String key) {
		return b.requests.remove(key) != null;
	}

	// ------------------------------------------------------------------ sync

	static DrawbridgeSyncPayload payload(Drawbridge b, boolean preview, long now) {
		List<DrawbridgeSyncPayload.Leaf> leaves = new ArrayList<>();
		for (int i = 0; i < 2; i++) {
			Drawbridge.LeafDef l = b.leaf(i);
			LeafFrame f = b.frame(i);
			List<Integer> sel = new ArrayList<>();
			if (l.complete()) {
				int[] mn = l.min(), mx = l.max();
				sel = List.of(mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]);
			}
			List<DrawbridgeSyncPayload.Block> blocks = new ArrayList<>();
			if (b.converted() || (preview && b.analysed())) {
				for (Drawbridge.BlockRecord r : l.blocks) {
					blocks.add(new DrawbridgeSyncPayload.Block(r.x, r.y, r.z, r.state));
				}
			}
			leaves.add(f == null ? new DrawbridgeSyncPayload.Leaf(l.name, 0, 0, 0, 0, 0, 0, 0, sel, blocks)
					: new DrawbridgeSyncPayload.Leaf(l.name, f.hx(), f.hy(), f.hz(), f.ux(), f.uz(), f.vx(), f.vz(), sel, blocks));
		}
		ChannelZones z = b.zones();
		DrawbridgeSyncPayload.Zones zones = z == null ? new DrawbridgeSyncPayload.Zones(0, 0, 0, 1, 0, 0, 0, 0, 0, 0)
				: new DrawbridgeSyncPayload.Zones(z.cx(), z.cz(), z.dx(), z.dz(), z.halfWidth(), z.halfSpan(), z.approach(), z.hysteresis(), b.waterY(),
						b.undersideY());
		DrawbridgeSyncPayload.Motion motion = new DrawbridgeSyncPayload.Motion(b.cycle().state().ordinal(), b.cycle().angleAtStart(),
				now - b.cycle().ticksInState(), b.tuning().step(), b.tuning().openAngle(), b.cycle().blocksInWorld());
		return new DrawbridgeSyncPayload(b.id, false, b.converted() && b.analysed(), leaves, zones, motion, preview);
	}

	private static void send(ServerPlayerEntity player, DrawbridgeSyncPayload payload) {
		if (ServerPlayNetworking.canSend(player, DrawbridgeSyncPayload.ID)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	/** Sends a bridge to every player of its world (its preview to those who asked for it). */
	public static void sync(Drawbridge b, ServerWorld world) {
		long now = world.getTime();
		for (ServerPlayerEntity p : world.getPlayers()) {
			boolean preview = b.previewPlayers.contains(p.getUuid());
			if (b.converted() || preview) {
				send(p, payload(b, preview, now));
			} else {
				send(p, DrawbridgeSyncPayload.removal(b.id));
			}
		}
	}

	/** Sends a bridge to one player (after a preview toggle). */
	public static void syncTo(ServerPlayerEntity p, Drawbridge b) {
		boolean preview = b.previewPlayers.contains(p.getUuid());
		if (b.converted() || preview) {
			send(p, payload(b, preview, p.getEntityWorld().getTime()));
		} else {
			send(p, DrawbridgeSyncPayload.removal(b.id));
		}
	}

	/** Everything a player needs on joining or changing world: the bridges of his world. */
	static void sendAll(ServerPlayerEntity player) {
		ServerWorld world = player.getEntityWorld();
		for (Drawbridge b : inWorld(world)) {
			if (b.converted() || b.previewPlayers.contains(player.getUuid())) {
				send(player, payload(b, b.previewPlayers.contains(player.getUuid()), world.getTime()));
			}
		}
	}
}
