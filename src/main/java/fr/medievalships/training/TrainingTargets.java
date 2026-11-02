package fr.medievalships.training;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerWorldEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TrainingTarget;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentBlockEntity;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.tent.Tents;

/**
 * The training targets' life on the server (1.19.0): the entity type {@code medievalships:training_target}
 * ({@link TrainingTargetEntity}, never saved), and one target entity per {@link TrainingTarget} of each training
 * area that stands in a loaded chunk.
 *
 * <ul>
 * <li>Spawning: when an area's block entity loads (its chunk loading, or the area being placed: the Fabric block
 * entity load event) or the area is placed ({@code TrainingAreaBlock.onPlaced}), its anchor is put in a per-world
 * queue; the queue is served at the end of the world's tick (never while a chunk is loading), and only once the
 * entities of the anchor's chunk and of the target's chunk are loaded ({@link ServerWorld#isChunkLoaded(long)}): then
 * every target that has no entity bound to the same anchor and index gets one ({@link #ensure}: never two, extra
 * ones are discarded).</li>
 * <li>Removal: breaking or replacing the anchor block ({@code TrainingAreaBlock.onStateReplaced}: {@code /tent remove},
 * a creative player, {@code /setblock}) discards its targets; a chunk that unloads takes its targets with it (not
 * saved); a target whose area is gone discards itself ({@link TrainingTargetEntity#tick}, every 2 s); a target whose
 * chunk unloads while its area stays loaded is asked for again (it comes back when its chunk does).</li>
 * </ul>
 * Cost: nothing while no area loads; the queue is empty almost always.
 */
public final class TrainingTargets {
	public static EntityType<TrainingTargetEntity> TYPE;
	/** Per world: anchors whose targets must be checked, with the world time of their next check. Server thread only. */
	private static final Map<ServerWorld, Map<BlockPos, Long>> PENDING = new HashMap<>();
	/** An anchor whose chunks are not loaded yet is checked again this many ticks later. */
	private static final int RETRY = 20;
	/** The targets are looked for in the area's extent grown by this much (blocks). */
	private static final double SEARCH_MARGIN = 2.0;

	/** What {@link #ensure} did. */
	public enum Result {
		/** Every target has its entity. */
		DONE,
		/** Some target's chunk (or the anchor's) has no loaded entities yet: try again later. */
		WAIT,
		/** No training area with targets at that anchor (any more). */
		GONE
	}

	private TrainingTargets() {
	}

	public static void register() {
		RegistryKey<EntityType<?>> key = RegistryKey.of(RegistryKeys.ENTITY_TYPE, MedievalShips.id("training_target"));
		TYPE = Registry.register(Registries.ENTITY_TYPE, key, EntityType.Builder.<TrainingTargetEntity>create(TrainingTargetEntity::new, SpawnGroup.MISC)
				.dimensions(0.6f, 1.8f)
				.maxTrackingRange(10)
				.trackingTickInterval(20)
				.makeFireImmune()
				.disableSaving()
				.disableSummon()
				.dropsNothing()
				.build(key));
		FabricDefaultAttributeRegistry.register(TYPE, TrainingTargetEntity.createAttributes());
		ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, world) -> {
			if (be instanceof TentBlockEntity tent && tent.tentType() != null && tent.tentType().hasTargets()) {
				request(world, be.getPos());
			}
		});
		ServerEntityEvents.ENTITY_UNLOAD.register((entity, world) -> {
			// a target whose own chunk unloads while its area stays: asked for again (it comes back with its chunk)
			if (entity instanceof TrainingTargetEntity t && entity.getRemovalReason() == Entity.RemovalReason.UNLOADED_TO_CHUNK
					&& TentCollisions.at(world, t.anchor()) != null) {
				request(world, t.anchor());
			}
		});
		ServerTickEvents.END_WORLD_TICK.register(TrainingTargets::tick);
		ServerWorldEvents.UNLOAD.register((server, world) -> PENDING.remove(world));
	}

	/** Asks for the targets of the area at {@code anchor} to be checked (and spawned) at the end of this world tick. */
	public static void request(ServerWorld world, BlockPos anchor) {
		PENDING.computeIfAbsent(world, w -> new HashMap<>()).put(anchor.toImmutable(), Long.MIN_VALUE);
	}

	/** The anchors waiting in a world's queue (tests). */
	public static int pending(ServerWorld world) {
		Map<BlockPos, Long> m = PENDING.get(world);
		return m == null ? 0 : m.size();
	}

	private static void tick(ServerWorld world) {
		Map<BlockPos, Long> queue = PENDING.get(world);
		if (queue == null || queue.isEmpty()) {
			return;
		}
		long now = world.getTime();
		List<BlockPos> due = new ArrayList<>();
		for (Map.Entry<BlockPos, Long> e : queue.entrySet()) {
			if (e.getValue() <= now) {
				due.add(e.getKey());
			}
		}
		for (BlockPos anchor : due) {
			Result r = ensure(world, anchor);
			if (r == Result.WAIT) {
				queue.put(anchor, now + RETRY);
			} else {
				queue.remove(anchor);
			}
		}
	}

	private static boolean entitiesLoaded(ServerWorld world, double x, double z) {
		return world.isChunkLoaded(ChunkPos.toLong((int) Math.floor(x) >> 4, (int) Math.floor(z) >> 4));
	}

	/** The training area at {@code anchor} (a prop with targets), or null. */
	private static TentType areaAt(ServerWorld world, BlockPos anchor) {
		BlockState state = world.getBlockState(anchor);
		TentType type = Tents.typeOf(state.getBlock());
		return type != null && type.hasTargets() ? type : null;
	}

	/**
	 * Gives every target of the area at {@code anchor} its entity, if the chunks are loaded: one per target (an
	 * existing one bound to the same anchor and index is kept, any extra one discarded, ones of an index the area no
	 * longer has discarded too).
	 */
	public static Result ensure(ServerWorld world, BlockPos anchor) {
		if (!entitiesLoaded(world, anchor.getX(), anchor.getZ())) {
			return world.isChunkLoaded(anchor) ? Result.WAIT : Result.GONE;
		}
		TentType type = areaAt(world, anchor);
		if (type == null) {
			return Result.GONE;
		}
		int quarter = TentBlock.quarter(world.getBlockState(anchor));
		List<TrainingTarget> targets = type.targets(quarter);
		TrainingTargetEntity[] found = new TrainingTargetEntity[targets.size()];
		for (TrainingTargetEntity e : of(world, anchor, type, quarter)) {
			int i = e.index();
			if (i >= targets.size() || e.prop() != type || e.quarter() != quarter || found[i] != null) {
				e.discard();
			} else {
				found[i] = e;
			}
		}
		boolean waiting = false;
		for (int i = 0; i < targets.size(); i++) {
			if (found[i] != null) {
				continue;
			}
			Vec3d home = TrainingTargetEntity.home(anchor, targets.get(i));
			if (!entitiesLoaded(world, home.x, home.z)) {
				waiting = true;
				continue;
			}
			TrainingTargetEntity e = new TrainingTargetEntity(TYPE, world);
			e.bind(anchor, type, i, quarter);
			world.spawnEntity(e);
		}
		return waiting ? Result.WAIT : Result.DONE;
	}

	/** The target entities bound to the area at {@code anchor} (loaded ones, in and around its extent). */
	public static List<TrainingTargetEntity> of(ServerWorld world, BlockPos anchor, TentType type, int quarter) {
		Box area = TentCollisions.worldExtent(type, anchor, quarter).expand(SEARCH_MARGIN);
		BlockPos a = anchor.toImmutable();
		return world.getEntitiesByClass(TrainingTargetEntity.class, area, e -> !e.isRemoved() && a.equals(e.anchor()));
	}

	/** The target entities bound to the area at {@code anchor} (its type and facing read from the block), or none. */
	public static List<TrainingTargetEntity> of(ServerWorld world, BlockPos anchor) {
		TentType type = areaAt(world, anchor);
		return type == null ? List.of() : of(world, anchor, type, TentBlock.quarter(world.getBlockState(anchor)));
	}

	/** Discards the targets of an area that is being removed (its block replaced) and forgets its queue entry. */
	public static void removeAll(ServerWorld world, BlockPos anchor, TentType type, int quarter) {
		Map<BlockPos, Long> queue = PENDING.get(world);
		if (queue != null) {
			queue.remove(anchor);
		}
		for (Iterator<TrainingTargetEntity> it = of(world, anchor, type, quarter).iterator(); it.hasNext();) {
			it.next().discard();
		}
	}

	/**
	 * Does the area of a target still stand? False when the anchor's chunk is loaded and holds no training area of the
	 * target's type and facing with that target; true while the anchor's chunk is not loaded (it is found again when the
	 * chunk loads: no duplicate).
	 */
	public static boolean stillStands(ServerWorld world, TrainingTargetEntity target) {
		BlockPos anchor = target.anchor();
		if (!world.isChunkLoaded(anchor)) {
			return true;
		}
		BlockState state = world.getBlockState(anchor);
		TentType type = Tents.typeOf(state.getBlock());
		return type != null && type == target.prop() && TentBlock.quarter(state) == target.quarter() && target.index() < type.targets().size();
	}
}
