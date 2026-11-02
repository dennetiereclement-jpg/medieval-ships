package fr.medievalships.tent;

import java.util.ArrayList;
import java.util.List;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityPose;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Seating;
import fr.medievalships.core.TentType;
import fr.medievalships.network.SitPayload;

/**
 * Sitting on the seats of the props (1.19.0): the {@link SeatEntity} type ({@code medievalships:seat}), the sit request
 * from the client ({@link SitPayload}) and its server-side checks, standing up.
 *
 * <p>Any prop whose JSON lists {@code "seats"} ({@link TentType#seats}) can be sat on: the nomad tavern's stools and
 * benches, the tatami area's bench. One player per seat, any number of players on different seats. Everything is
 * decided on the server: the prop is still there, the seat exists, the player is within reach, alive, not a spectator,
 * not already riding, the seat is free ({@link #sit}).
 */
public final class Seats {
	/** {@code medievalships:seat}: never saved, never summoned (see {@link SeatEntity}). */
	public static EntityType<SeatEntity> SEAT;

	/** What a sit request came to. */
	public enum Result {
		SEATED, OCCUPIED, ALREADY_RIDING, TOO_FAR, NO_SEAT, NOT_ALLOWED
	}

	private Seats() {
	}

	/** The entity type, the payload and its handler, the disconnect hook. Called once from {@link Tents#register}. */
	public static void register() {
		RegistryKey<EntityType<?>> key = RegistryKey.of(RegistryKeys.ENTITY_TYPE, MedievalShips.id("seat"));
		SEAT = Registry.register(Registries.ENTITY_TYPE, key, EntityType.Builder.<SeatEntity>create(SeatEntity::new, SpawnGroup.MISC)
				.dimensions(0.25f, 0.25f)
				.disableSummon()
				.makeFireImmune()
				.maxTrackingRange(10)
				.trackingTickInterval(10)
				.build(key));
		PayloadTypeRegistry.playC2S().register(SitPayload.ID, SitPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(SitPayload.ID, (payload, context) -> handle(payload, context.player()));
		// before vanilla saves the player file: a seated player is stood up beside his seat, the seat goes (never saved)
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> standUp(handler.player));
	}

	/** A player right-clicked a seat (server thread). */
	public static void handle(SitPayload payload, ServerPlayerEntity player) {
		if (sit(player, payload.anchor(), payload.seat()) == Result.OCCUPIED) {
			player.sendMessage(Text.literal("Cette place est prise.").formatted(Formatting.YELLOW), true);
		}
	}

	/**
	 * Seats {@code rider} on the seat {@code index} of the prop anchored at {@code anchor}, after checking everything:
	 * a server world, the rider alive, not a spectator, not riding nor carrying anything; the anchor loaded and still a
	 * prop with that seat; the rider's eyes within {@link Seating#SERVER_REACH} of the seat; nobody on it.
	 */
	public static Result sit(Entity rider, BlockPos anchor, int index) {
		if (!(rider.getEntityWorld() instanceof ServerWorld world) || !rider.isAlive() || rider.isRemoved() || rider.isSpectator()) {
			return Result.NOT_ALLOWED;
		}
		if (rider.hasVehicle() || rider.hasPassengers()) {
			return Result.ALREADY_RIDING;
		}
		if (anchor == null || !world.isPosLoaded(anchor)) {
			return Result.NO_SEAT;
		}
		BlockState state = world.getBlockState(anchor);
		if (!(state.getBlock() instanceof TentBlock block)) {
			return Result.NO_SEAT;
		}
		TentType type = block.tentType();
		int quarter = TentBlock.quarter(state);
		List<TentType.Seat> seats = type.seats(quarter);
		if (index < 0 || index >= seats.size()) {
			return Result.NO_SEAT;
		}
		double[] w = Seating.world(anchor.getX(), anchor.getY(), anchor.getZ(), seats.get(index));
		if (rider.getEyePos().squaredDistanceTo(w[0], w[1], w[2]) > Seating.SERVER_REACH * Seating.SERVER_REACH) {
			return Result.TOO_FAR;
		}
		SeatEntity existing = find(world, anchor, index);
		if (existing != null) {
			if (existing.hasPassengers()) {
				return Result.OCCUPIED;
			}
			existing.discard(); // left empty this tick: replaced
		}
		SeatEntity seat = SeatEntity.create(world, anchor, type, quarter, index);
		if (!world.spawnEntity(seat)) {
			return Result.NO_SEAT;
		}
		// forced: the checks above replace vanilla's (a player who just got up may sit down again at once)
		if (!rider.startRiding(seat, true, true)) {
			seat.discard();
			return Result.NOT_ALLOWED;
		}
		if (rider instanceof ServerPlayerEntity player) {
			// the rotation is the client's: tell it to face the seat (the body is kept square to it every tick)
			player.rotate(seat.seatYaw(), false, player.getPitch(), false);
		}
		return Result.SEATED;
	}

	/** The seat entity of a prop's seat, if somebody sits there (or has just got up). */
	@Nullable
	public static SeatEntity find(World world, BlockPos anchor, int index) {
		BlockState state = world.getBlockState(anchor);
		if (!(state.getBlock() instanceof TentBlock block)) {
			return null;
		}
		List<TentType.Seat> seats = block.tentType().seats(TentBlock.quarter(state));
		if (index < 0 || index >= seats.size()) {
			return null;
		}
		double[] w = Seating.world(anchor.getX(), anchor.getY(), anchor.getZ(), seats.get(index));
		List<SeatEntity> found = world.getEntitiesByClass(SeatEntity.class,
				new Box(w[0] - 0.5, w[1] - 0.5, w[2] - 0.5, w[0] + 0.5, w[1] + 0.5, w[2] + 0.5), e -> e.isSeat(anchor, index));
		SeatEntity best = null;
		for (SeatEntity e : found) {
			if (best == null || e.hasPassengers()) {
				best = e;
			}
		}
		return best;
	}

	/** Every seat entity of the prop anchored at {@code anchor} (the prop's extent), riders or not. */
	public static List<SeatEntity> all(World world, BlockPos anchor, TentType type, int quarter) {
		Box area = TentCollisions.worldExtent(type, anchor, quarter).expand(1.0);
		return world.getEntitiesByClass(SeatEntity.class, area, e -> anchor.equals(e.anchor()) && !e.isRemoved());
	}

	/** The prop anchored at {@code pos} is gone or turned: everyone sitting on it stands up, its seats go. */
	public static void release(ServerWorld world, BlockPos pos, TentType type, int quarter) {
		if (type.seats().isEmpty()) {
			return;
		}
		for (SeatEntity seat : all(world, pos, type, quarter)) {
			seat.discard(); // remove() stands the rider up first
		}
	}

	/** A player who logs out (or must get up): off his seat, the seat removed. */
	public static void standUp(ServerPlayerEntity player) {
		if (player.getVehicle() instanceof SeatEntity seat) {
			player.stopRiding(); // vanilla: stands him at updatePassengerForDismount's spot
			seat.discard();
		}
	}

	/**
	 * Where {@code who} stands when getting up from a seat whose surface centre is (sx, sy, sz), facing {@code yaw}: the
	 * first of {@link Seating#standOffsets} (in front, then the front corners, the sides, behind; near then farther)
	 * with ground or a low collision box to stand on (between {@code groundY - 1} and the seat's surface) and room for
	 * the standing body: no block, no box of the props ({@link TentCollisions}), no solid entity. Else on the seat
	 * itself; null if even that is blocked.
	 */
	@Nullable
	public static Vec3d standingSpot(World world, Entity who, double sx, double sy, double sz, float yaw, double groundY) {
		EntityDimensions dims = who.getDimensions(EntityPose.STANDING);
		for (double[] o : Seating.standOffsets(yaw)) {
			double x = sx + o[0], z = sz + o[1];
			double feet = support(world, who, x, z, dims.width(), groundY - 1.0, sy + 0.05);
			if (!Double.isNaN(feet) && free(world, who, dims.getBoxAt(x, feet, z))) {
				return new Vec3d(x, feet, z);
			}
		}
		double feet = support(world, who, sx, sz, dims.width(), groundY - 1.0, sy + 0.05);
		double y = Double.isNaN(feet) ? sy : feet;
		return free(world, who, dims.getBoxAt(sx, y, sz)) ? new Vec3d(sx, y, sz) : null;
	}

	/** The highest top of a collision shape (block or prop box) under a body at (x, z), between minY and maxY; NaN if none. */
	private static double support(World world, Entity who, double x, double z, double width, double minY, double maxY) {
		double h = width / 2.0;
		Box column = new Box(x - h + 1e-3, minY, z - h + 1e-3, x + h - 1e-3, maxY, z + h - 1e-3);
		double best = Double.NaN;
		List<VoxelShape> shapes = new ArrayList<>();
		for (VoxelShape s : world.getBlockCollisions(who, column)) {
			shapes.add(s);
		}
		TentCollisions.append(shapes, who, column, world);
		for (VoxelShape s : shapes) {
			if (s.isEmpty()) {
				continue;
			}
			double top = s.getMax(Direction.Axis.Y);
			if (top <= maxY && (Double.isNaN(best) || top > best)) {
				best = top;
			}
		}
		return best;
	}

	/** Room for a body: no block, no prop collision box, no solid entity in the box (slightly shrunk). */
	private static boolean free(World world, Entity who, Box box) {
		Box b = box.contract(1e-3);
		return world.isSpaceEmpty(who, b) && !TentCollisions.append(new ArrayList<>(), who, b, world);
	}
}
