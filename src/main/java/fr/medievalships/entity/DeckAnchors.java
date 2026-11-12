package fr.medievalships.entity;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityWorldChangeEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.loader.api.FabricLoader;

import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;
import net.minecraft.util.Uuids;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.Heightmap;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.DeckAnchor;
import fr.medievalships.core.DeckFrame;
import fr.medievalships.core.ShipPose;
import fr.medievalships.data.ShipData;

/**
 * Back on the deck after a reconnection (1.30.0): the spot a player stands or sits on aboard a ship is kept in his own
 * data ({@link #ANCHOR}, a persistent data attachment of the player entity, saved in his player file). A player who
 * logged out aboard a ship that then sailed on comes back on that ship's deck, at the same spot, as soon as the ship is
 * loaded; if the ship is gone, on dry ground nearby (never in the sea). Because the anchor is in the player file, it
 * follows each character of a multi-character mod (Nexus Characters swaps the whole player file under the same account
 * UUID): nothing is kept per account, so one character never inherits another one's ship.
 */
public final class DeckAnchors {
	private DeckAnchors() {
	}

	static final Codec<DeckAnchor> CODEC = RecordCodecBuilder.create(i -> i.group(
			Uuids.CODEC.fieldOf("ship").forGetter(DeckAnchor::ship),
			Codec.STRING.fieldOf("dimension").forGetter(DeckAnchor::dimension),
			Codec.DOUBLE.fieldOf("x").forGetter(DeckAnchor::x),
			Codec.DOUBLE.fieldOf("y").forGetter(DeckAnchor::y),
			Codec.DOUBLE.fieldOf("z").forGetter(DeckAnchor::z),
			Codec.FLOAT.fieldOf("yaw").forGetter(DeckAnchor::yaw)
	).apply(i, DeckAnchor::new));

	/** Persistent, not copied on death (a dead character does not respawn aboard). */
	public static final AttachmentType<DeckAnchor> ANCHOR = AttachmentRegistry.create(MedievalShips.id("deck_anchor"),
			builder -> builder.persistent(CODEC));

	/** Ticks after joining before the anchor is applied (a multi-character mod restores its character first). */
	static final int JOIN_DELAY = 10;
	/** Ticks to wait for a ship that is not loaded yet (its chunk loaded from its last known position). */
	static final int WAIT_TICKS = 200;
	/** Ticks to wait when the ship's last position is unknown (it may still load near the player). */
	static final int WAIT_UNKNOWN_TICKS = 40;
	/** Ticks between two updates of a player's anchor while he stays aboard. */
	static final int MAINTAIN_PERIOD = 10;

	private static final List<Pending> PENDING = new ArrayList<>();

	private static final class Pending {
		final ServerPlayerEntity player;
		final int due;
		@Nullable
		final UUID legacyShip;
		int giveUpAt = Integer.MAX_VALUE;
		boolean searched;
		boolean secured;

		Pending(ServerPlayerEntity player, int due, @Nullable UUID legacyShip) {
			this.player = player;
			this.due = due;
			this.legacyShip = legacyShip;
		}
	}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(DeckAnchors::tick);
		// another world (portal, command): the ship of the old one is left behind
		ServerEntityWorldChangeEvents.AFTER_PLAYER_CHANGE_WORLD.register((player, origin, destination) -> {
			if (!restoring(player)) {
				player.removeAttached(ANCHOR);
			}
		});
	}

	/** The anchor of a player, or null. */
	@Nullable
	public static DeckAnchor anchor(ServerPlayerEntity player) {
		return player.getAttached(ANCHOR);
	}

	/** Is this player waiting to be put back aboard (just joined)? */
	public static boolean restoring(ServerPlayerEntity player) {
		for (Pending p : PENDING) {
			if (p.player == player) {
				return true;
			}
		}
		return false;
	}

	/** The anchor for a player on (or seated in) this ship, from where he is now. */
	static DeckAnchor anchorOn(ServerPlayerEntity player, ShipEntity ship) {
		ShipPose pose = ship.pose();
		Vec3d feet = player.getVehicle() == ship ? ship.updatePassengerForDismount(player) : player.getEntityPos();
		double[] l = new double[3];
		DeckFrame.toLocal(pose, feet.x, feet.y, feet.z, l);
		return new DeckAnchor(ship.getUuid(), ship.getEntityWorld().getRegistryKey().getValue().toString(), l[0], l[1], l[2],
				DeckFrame.wrap(player.getYaw() - pose.yaw()));
	}

	/** Every {@link #MAINTAIN_PERIOD} ticks: the anchor follows the player while he is aboard, and goes when he leaves. */
	static void maintain(ServerPlayerEntity player, int now) {
		if (player instanceof FakePlayer || (now + player.getId()) % MAINTAIN_PERIOD != 0 || player.isRemoved() || restoring(player)) {
			return;
		}
		ShipEntity ship = player.getVehicle() instanceof ShipEntity seated ? seated : DeckSync.standingOn(player);
		DeckAnchor old = player.getAttached(ANCHOR);
		if (ship == null) {
			if (old != null) {
				player.removeAttached(ANCHOR);
			}
			return;
		}
		DeckAnchor a = anchorOn(player, ship);
		if (a.differs(old)) {
			player.setAttached(ANCHOR, a);
		}
	}

	/** A player leaves the server (seated players were stood up on their seat's spot first). */
	public static void onDisconnect(ServerPlayerEntity player, @Nullable ShipEntity ship, MinecraftServer server) {
		if (restoring(player)) {
			PENDING.removeIf(p -> p.player == player);
			return; // not put back aboard yet: his anchor stays as it was
		}
		if (ship == null || ship.isRemoved()) {
			player.removeAttached(ANCHOR);
			return;
		}
		player.setAttached(ANCHOR, anchorOn(player, ship));
		// the ship records where it goes from now on, so that it can be found (and its chunk loaded) at his return
		ShipData.get(server).markCrewAway(ship.getUuid(), ship.getEntityWorld().getRegistryKey().getValue().toString(), ship.getX(),
				ship.getY(), ship.getZ());
	}

	/** A player joined: put back aboard shortly, if his data says he was aboard. */
	public static void onJoin(ServerPlayerEntity player, MinecraftServer server) {
		UUID legacy = ShipData.get(server).takeLegacyPlayerShip(player.getUuid());
		if (legacy != null && FabricLoader.getInstance().isModLoaded("nexuscharacters")) {
			legacy = null; // kept per account before 1.30.0: may belong to another character of that account
		}
		PENDING.removeIf(p -> p.player.getUuid().equals(player.getUuid()));
		PENDING.add(new Pending(player, server.getTicks() + JOIN_DELAY, legacy));
	}

	/** Applies an anchor at once (tests, and the end of {@link #tick}'s wait). */
	public static void scheduleRestore(ServerPlayerEntity player, int delay) {
		PENDING.removeIf(p -> p.player == player);
		PENDING.add(new Pending(player, player.getEntityWorld().getServer().getTicks() + delay, null));
	}

	private static void tick(MinecraftServer server) {
		int now = server.getTicks();
		for (ServerWorld world : server.getWorlds()) {
			for (ServerPlayerEntity player : world.getPlayers()) {
				maintain(player, now);
			}
		}
		if (PENDING.isEmpty()) {
			return;
		}
		Iterator<Pending> it = PENDING.iterator();
		while (it.hasNext()) {
			Pending p = it.next();
			ServerPlayerEntity player = p.player;
			if (player.isRemoved() || player.isDisconnected()) {
				it.remove();
				continue;
			}
			if (now < p.due) {
				continue;
			}
			DeckAnchor anchor = player.getAttached(ANCHOR);
			UUID shipId = anchor != null ? anchor.ship() : p.legacyShip;
			if (shipId == null) {
				it.remove();
				continue;
			}
			ShipEntity ship = find(server, shipId);
			if (ship != null) {
				it.remove();
				putAboard(player, ship, anchor);
				continue;
			}
			if (!p.searched) {
				p.searched = true;
				ShipData.CrewShipRecord rec = ShipData.get(server).crewAway(shipId);
				ServerWorld w = rec == null ? null : server.getWorld(RegistryKey.of(RegistryKeys.WORLD, Identifier.tryParse(rec.dimension)));
				if (w != null) {
					// the ship sailed out of the loaded area: load its chunk (the ticket expires by itself)
					w.getChunkManager().addTicket(ChunkTicketType.PORTAL, new ChunkPos(BlockPos.ofFloored(rec.x, rec.y, rec.z)), 2);
					p.giveUpAt = now + WAIT_TICKS;
				} else {
					p.giveUpAt = now + WAIT_UNKNOWN_TICKS;
				}
			}
			if (!p.secured && unsafe(player)) {
				// waiting high above the sea (the deck of an airship that flew away): on safe ground meanwhile
				p.secured = true;
				Vec3d safe = safeSpot(player);
				player.teleport(player.getEntityWorld(), safe.x, safe.y, safe.z, Set.of(), player.getYaw(), player.getPitch(), false);
				player.fallDistance = 0;
			}
			if (now >= p.giveUpAt) {
				it.remove();
				// the ship is gone (sunk, picked up): nothing to come back to
				player.removeAttached(ANCHOR);
				if (unsafe(player) || player.isTouchingWater()) {
					Vec3d safe = safeSpot(player);
					player.teleport(player.getEntityWorld(), safe.x, safe.y, safe.z, Set.of(), player.getYaw(), player.getPitch(), false);
					player.fallDistance = 0;
				}
				if (anchor != null) {
					player.sendMessage(Text.literal("Le navire sur lequel vous étiez n'est plus là : vous voici en lieu sûr.").formatted(Formatting.GOLD),
							false);
				}
			}
		}
	}

	/** The ship entity with this UUID in any world, or null. */
	@Nullable
	static ShipEntity find(MinecraftServer server, UUID id) {
		for (ServerWorld world : server.getWorlds()) {
			Entity e = world.getEntity(id);
			if (e instanceof ShipEntity ship && !ship.isRemoved()) {
				return ship;
			}
		}
		return null;
	}

	/** Puts a player on the anchor's spot of the ship (or the nearest standing spot), with his yaw on the deck. */
	static void putAboard(ServerPlayerEntity player, ShipEntity ship, @Nullable DeckAnchor anchor) {
		ShipPose pose = ship.pose();
		double[] spot;
		float yaw;
		if (anchor != null) {
			spot = DeckAnchor.restoreSpot(ship.geometry(), ship.interiorState(), anchor.x(), anchor.y(), anchor.z());
			yaw = (float) (pose.yaw() + anchor.yaw());
		} else {
			// legacy record (before 1.30.0): the deck's standing spot nearest to the player
			double[] l = pose.toLocal(player.getX(), player.getY(), player.getZ());
			spot = DeckAnchor.restoreSpot(ship.geometry(), ship.interiorState(), Double.NaN, Double.NaN, l[2]);
			yaw = player.getYaw();
		}
		double[] w = pose.toWorld(spot[0], spot[1], spot[2]);
		ServerWorld world = (ServerWorld) ship.getEntityWorld();
		if (player.getEntityWorld() == world && player.squaredDistanceTo(w[0], w[1], w[2]) < 0.05 * 0.05) {
			return; // still standing there (the ship did not move while he was away)
		}
		player.teleport(world, w[0], w[1], w[2], Set.of(), yaw, player.getPitch(), false);
		player.fallDistance = 0;
		player.setVelocity(Vec3d.ZERO);
		player.setAttached(ANCHOR, anchorOn(player, ship));
		String name = ship.hasCustomName() ? ship.getCustomName().getString() : "navire";
		player.sendMessage(Text.literal("De retour à bord (" + name + ").").formatted(Formatting.AQUA), true);
		MedievalShips.LOGGER.info("{} put back aboard {} ({}) at local {}, {}, {}", player.getStringifiedName(), name, ship.getUuid(),
				String.format(java.util.Locale.ROOT, "%.2f", spot[0]), String.format(java.util.Locale.ROOT, "%.2f", spot[1]),
				String.format(java.util.Locale.ROOT, "%.2f", spot[2]));
	}

	/** Would this player fall (no ground within 3 blocks under his feet, not in water, not on a deck)? */
	static boolean unsafe(ServerPlayerEntity player) {
		ServerWorld world = player.getEntityWorld();
		if (player.isTouchingWater() || DeckSync.standingOn(player) != null || player.getAbilities().flying) {
			return false;
		}
		BlockPos feet = BlockPos.ofFloored(player.getX(), player.getY() + 0.01, player.getZ());
		for (int dy = 0; dy <= 3; dy++) {
			BlockPos p = feet.down(dy);
			BlockState s = world.getBlockState(p);
			if (!s.getCollisionShape(world, p).isEmpty() || !s.getFluidState().isEmpty()) {
				return false;
			}
		}
		return true;
	}

	/** A safe place near the player: the deck of a ship nearby, else dry ground, else the world spawn. */
	static Vec3d safeSpot(ServerPlayerEntity player) {
		ServerWorld world = player.getEntityWorld();
		Vec3d best = null;
		double bestDist = 48 * 48;
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved()) {
				continue;
			}
			Vec3d spot = ship.boardingPosition(player.getX(), player.getZ());
			double d = spot.squaredDistanceTo(player.getEntityPos());
			if (d < bestDist) {
				bestDist = d;
				best = spot;
			}
		}
		if (best != null) {
			return best;
		}
		double[] dry = DeckAnchor.nearestDry(net.minecraft.util.math.MathHelper.floor(player.getX()), net.minecraft.util.math.MathHelper.floor(player.getZ()), 64, (x, z) -> dryGround(world, x, z));
		if (dry != null) {
			return new Vec3d(dry[0], dry[1], dry[2]);
		}
		BlockPos spawn = world.getSpawnPoint().getPos();
		return new Vec3d(spawn.getX() + 0.5, world.getTopY(Heightmap.Type.MOTION_BLOCKING, spawn.getX(), spawn.getZ()), spawn.getZ() + 0.5);
	}

	/** Standing height on dry ground at a loaded column, or NaN. */
	private static double dryGround(ServerWorld world, int x, int z) {
		if (!world.isChunkLoaded(x >> 4, z >> 4)) {
			return Double.NaN;
		}
		int top = world.getTopY(Heightmap.Type.MOTION_BLOCKING, x, z);
		if (top <= world.getBottomY()) {
			return Double.NaN;
		}
		BlockPos below = new BlockPos(x, top - 1, z);
		BlockState s = world.getBlockState(below);
		if (!s.getFluidState().isEmpty() || s.getCollisionShape(world, below).isEmpty()) {
			return Double.NaN;
		}
		BlockPos head = new BlockPos(x, top + 1, z);
		if (!world.getBlockState(head).getCollisionShape(world, head).isEmpty()) {
			return Double.NaN;
		}
		return top + s.getCollisionShape(world, below).getMax(net.minecraft.util.math.Direction.Axis.Y) - 1.0;
	}
}
