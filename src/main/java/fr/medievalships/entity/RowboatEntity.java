package fr.medievalships.entity;

import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.Item;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.RowboatLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/**
 * The Rowboat ({@code medievalships:rowboat}): two seats on the thwarts, the rower (pilot) seated and not standing; a
 * click anywhere on it takes the oars, or the passenger's seat when the oars are taken; leaving it lands on the nearest
 * ground within reach, else in the water beside it (like a vanilla boat).
 */
public class RowboatEntity extends ShipEntity {
	/**
	 * The ship whose boat this is, while it is on the water (1.30.0, {@link ShipBoatHandling}); null for a rowboat
	 * placed from its item, or once its ship is gone.
	 */
	@Nullable
	private UUID motherShip;

	public RowboatEntity(EntityType<? extends RowboatEntity> type, World world) {
		super(type, world);
	}

	@Nullable
	public UUID motherShip() {
		return motherShip;
	}

	public void setMotherShip(@Nullable UUID ship) {
		motherShip = ship;
	}

	@Override
	protected void readCustomData(ReadView view) {
		super.readCustomData(view);
		String mother = view.getString("MotherShip", "");
		try {
			motherShip = mother.isEmpty() ? null : UUID.fromString(mother);
		} catch (IllegalArgumentException e) {
			motherShip = null;
		}
	}

	@Override
	protected void writeCustomData(WriteView view) {
		super.writeCustomData(view);
		view.putString("MotherShip", motherShip == null ? "" : motherShip.toString());
	}

	@Override
	public void tick() {
		super.tick();
		// a ship's boat its ship has written off (lost while unloaded, its deco back aboard): it vanishes (never two)
		if (motherShip != null && !isRemoved() && (age + getId()) % 40 == 0 && getEntityWorld() instanceof ServerWorld world) {
			ShipBoatHandling.checkRetired(this, world);
		}
	}

	@Override
	public ShipType shipType() {
		return Ships.ROWBOAT;
	}

	@Override
	public Item item() {
		return MedievalShips.ROWBOAT_ITEM;
	}

	/** The rower sits on his thwart. */
	@Override
	public boolean standsAtHelm(Entity passenger) {
		return false;
	}

	/** The whole boat is its "helm": when the oars are taken, the click gives the passenger's seat instead. */
	@Override
	public boolean seat(Entity passenger, int seat) {
		if (seat == ShipGeometry.PILOT_SEAT) {
			Entity rower = passengerInSeat(ShipGeometry.PILOT_SEAT);
			if (rower != null && rower != passenger) {
				seat = freeSeat(false);
				if (seat < 0) {
					return false;
				}
			}
		}
		return super.seat(passenger, seat);
	}

	/**
	 * Off the boat: onto solid ground beside it when there is some within a couple of blocks (a quay, a bank), else
	 * into the water beside the seat.
	 */
	@Override
	public Vec3d updatePassengerForDismount(LivingEntity passenger) {
		Vec3d fallback = super.updatePassengerForDismount(passenger);
		World world = getEntityWorld();
		ShipPose pose = pose();
		double z = Math.max(-RowboatLayout.HALF_LENGTH + 0.5, Math.min(RowboatLayout.HALF_LENGTH - 0.5, pose.toLocal(passenger.getX(), passenger.getY(), passenger.getZ())[2]));
		double[][] candidates = {{RowboatLayout.DISMOUNT_X, z}, {-RowboatLayout.DISMOUNT_X, z}, {RowboatLayout.DISMOUNT_X + 1.0, z},
				{-RowboatLayout.DISMOUNT_X - 1.0, z}, {0.0, RowboatLayout.TIP + 1.0}, {0.0, -RowboatLayout.TIP - 1.0}};
		BlockPos.Mutable pos = new BlockPos.Mutable();
		for (double[] c : candidates) {
			double[] w = pose.toWorld(c[0], 0.0, c[1]);
			int bx = (int) Math.floor(w[0]), bz = (int) Math.floor(w[2]), by = (int) Math.floor(getY());
			for (int dy = 1; dy >= -1; dy--) {
				int y = by + dy;
				if (!free(world, pos.set(bx, y, bz)) || !free(world, pos.set(bx, y + 1, bz))) {
					continue;
				}
				BlockState ground = world.getBlockState(pos.set(bx, y - 1, bz));
				if (!ground.getCollisionShape(world, pos).isEmpty() && !world.getFluidState(pos.set(bx, y, bz)).isIn(FluidTags.WATER)) {
					return new Vec3d(bx + 0.5, y, bz + 0.5);
				}
			}
		}
		return fallback;
	}

	private static boolean free(World world, BlockPos pos) {
		return world.getBlockState(pos).getCollisionShape(world, pos).isEmpty();
	}
}
