package fr.medievalships.tent;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.BlockState;
import net.minecraft.block.piston.PistonBehavior;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;
import net.minecraft.world.explosion.Explosion;

import fr.medievalships.core.Seating;
import fr.medievalships.core.TentType;

/**
 * The invisible thing a player sitting on a prop's seat rides ({@code medievalships:seat}, 1.19.0): spawned on demand
 * by {@link Seats#sit} exactly at the seat's surface, facing the seat's yaw, gone as soon as nobody sits on it.
 *
 * <ul>
 * <li>Never saved: neither with its chunk nor in the rider's player file ({@link #shouldSave}, {@link #saveSelfData}),
 * so nothing is left behind after a restart or a crash; a player who logs out while seated is stood up first
 * ({@link Seats#standUp}, disconnect event).</li>
 * <li>No AI, no gravity, no movement, no collision, cannot be hit, pushed, burnt, blown up, pushed by pistons or
 * summoned; its tick (server only) just checks it still has a living rider and that its prop is still there with the
 * same facing, else it removes itself (death, teleport, spectator mode, the prop broken or replaced).</li>
 * <li>The rider's attachment point is the seat's surface: a player's feet go 0.6 below it and the vanilla sitting
 * pose puts the thighs on the surface ({@link Seating}). His body faces the seat's yaw, his head turns at most
 * {@link Seating#HEAD_TURN} degrees from it (like a boat's passengers), on both sides.</li>
 * <li>One rider ({@link #canAddPassenger}). Getting up is vanilla's (sneak): the rider stands at the first free spot
 * in front of the seat, else at its sides, else behind ({@link Seats#standingSpot}), never inside a collision box of
 * the props or a block.</li>
 * </ul>
 */
public class SeatEntity extends Entity {
	/** The seat's yaw, exact (the spawn packet only carries a byte); the client turns its player with it. */
	private static final TrackedData<Float> SEAT_YAW = DataTracker.registerData(SeatEntity.class, TrackedDataHandlerRegistry.FLOAT);

	/** Server side only: the prop's anchor block, its type and facing, and the seat's index in its JSON. */
	@Nullable
	private BlockPos anchor;
	@Nullable
	private TentType type;
	private int quarter;
	private int index = -1;

	public SeatEntity(EntityType<?> entityType, World world) {
		super(entityType, world);
		setNoGravity(true);
		setInvulnerable(true);
	}

	/** A seat of a placed prop at its surface, facing its yaw (server side; not spawned yet). */
	static SeatEntity create(World world, BlockPos anchor, TentType type, int quarter, int index) {
		SeatEntity e = new SeatEntity(Seats.SEAT, world);
		TentType.Seat s = type.seats(quarter).get(index);
		double[] w = Seating.world(anchor.getX(), anchor.getY(), anchor.getZ(), s);
		e.anchor = anchor.toImmutable();
		e.type = type;
		e.quarter = quarter & 3;
		e.index = index;
		e.refreshPositionAndAngles(w[0], w[1], w[2], s.yaw(), 0f);
		e.dataTracker.set(SEAT_YAW, s.yaw());
		return e;
	}

	/** The yaw the sitter faces (Minecraft degrees, 0 = south). */
	public float seatYaw() {
		return dataTracker.get(SEAT_YAW);
	}

	/** The prop's anchor block (server side; null on the client). */
	@Nullable
	public BlockPos anchor() {
		return anchor;
	}

	/** The seat's index in its prop's JSON (server side; -1 on the client). */
	public int seatIndex() {
		return index;
	}

	/** Is this the seat {@code index} of the prop anchored at {@code pos}? */
	boolean isSeat(BlockPos pos, int seat) {
		return !isRemoved() && seat == index && pos.equals(anchor);
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		builder.add(SEAT_YAW, 0f);
	}

	@Override
	public void tick() {
		// nothing moves: the rider's position follows the seat in vanilla (tickRiding); the server only checks the seat
		// is still in use, cheaply (one block state read per occupied seat)
		if (getEntityWorld() instanceof ServerWorld world && !inUse(world)) {
			discard(); // remove() stands the rider up first
		}
	}

	/** A living rider still sits here and the prop is still there, with the same facing and this seat. */
	private boolean inUse(ServerWorld world) {
		if (anchor == null || type == null || !hasPassengers()) {
			return false;
		}
		for (Entity p : getPassengerList()) {
			if (!p.isAlive() || p.isRemoved() || p.isSpectator()) {
				return false;
			}
		}
		if (!world.isPosLoaded(anchor)) {
			return false;
		}
		BlockState state = world.getBlockState(anchor);
		return state.getBlock() instanceof TentBlock block && block.tentType() == type && TentBlock.quarter(state) == quarter
				&& index < type.seats().size();
	}

	@Override
	public void remove(RemovalReason reason) {
		if (!getEntityWorld().isClient() && hasPassengers()) {
			// while this seat is not removed yet: the riders then stand up beside it (updatePassengerForDismount), not
			// inside the stool where they sat
			removeAllPassengers();
		}
		super.remove(reason);
	}

	@Override
	protected boolean canAddPassenger(Entity passenger) {
		return getPassengerList().isEmpty();
	}

	@Override
	protected void addPassenger(Entity passenger) {
		super.addPassenger(passenger);
		// the sitter faces the seat's yaw (on the client this turns the local player: rotation is the client's)
		float yaw = seatYaw();
		passenger.setYaw(yaw);
		passenger.lastYaw = yaw;
		passenger.setHeadYaw(yaw);
		passenger.setBodyYaw(yaw);
	}

	@Override
	protected Vec3d getPassengerAttachmentPos(Entity passenger, EntityDimensions dimensions, float scaleFactor) {
		return Vec3d.ZERO; // the seat entity stands at the seat's surface: see Seating
	}

	@Override
	protected void updatePassengerPosition(Entity passenger, PositionUpdater positionUpdater) {
		super.updatePassengerPosition(passenger, positionUpdater);
		clampPassengerYaw(passenger);
	}

	@Override
	public void onPassengerLookAround(Entity passenger) {
		clampPassengerYaw(passenger);
	}

	/** The body square to the seat, the head within {@link Seating#HEAD_TURN} degrees of it (as vanilla boats do). */
	private void clampPassengerYaw(Entity passenger) {
		float yaw = seatYaw();
		passenger.setBodyYaw(yaw);
		float f = MathHelper.wrapDegrees(passenger.getYaw() - yaw);
		float g = MathHelper.clamp(f, -Seating.HEAD_TURN, Seating.HEAD_TURN);
		passenger.lastYaw += g - f;
		passenger.setYaw(passenger.getYaw() + g - f);
		passenger.setHeadYaw(passenger.getYaw());
	}

	@Override
	public Vec3d updatePassengerForDismount(LivingEntity passenger) {
		double ground = anchor != null ? anchor.getY() : Math.floor(getY() - 0.5);
		Vec3d spot = Seats.standingSpot(getEntityWorld(), passenger, getX(), getY(), getZ(), seatYaw(), ground);
		return spot != null ? spot : super.updatePassengerForDismount(passenger);
	}

	@Override
	public boolean damage(ServerWorld world, DamageSource source, float amount) {
		return false;
	}

	@Override
	public boolean isAttackable() {
		return false;
	}

	@Override
	public boolean isImmuneToExplosion(Explosion explosion) {
		return true;
	}

	@Override
	public PistonBehavior getPistonBehavior() {
		return PistonBehavior.IGNORE;
	}

	@Override
	public boolean canUsePortals(boolean allowVehicles) {
		return false;
	}

	/** Not saved with its chunk: a seat only exists while someone sits on it. */
	@Override
	public boolean shouldSave() {
		return false;
	}

	/** Not written anywhere either (a chunk, a player's "RootVehicle", a passenger list): nothing comes back after a restart. */
	@Override
	public boolean saveSelfData(WriteView view) {
		return false;
	}

	@Override
	protected void readCustomData(ReadView view) {
	}

	@Override
	protected void writeCustomData(WriteView view) {
	}
}
