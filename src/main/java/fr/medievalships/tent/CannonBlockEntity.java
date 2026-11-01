package fr.medievalships.tent;

import net.minecraft.block.BlockState;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.core.CannonState;
import fr.medievalships.core.TentType;

/**
 * The block entity of a cannon (block entity type {@code medievalships:cannon}, {@link Tents#CANNON_BLOCK_ENTITY}): a
 * {@link TentBlockEntity} (drawn by the same TentBlockEntityRenderer, the same collision boxes) that also keeps the
 * cannon's {@link CannonState} — loaded, powder, fuse ticks, last shot time — saved and read with the block entity
 * data API ({@link #writeData} / {@link #readData}, keys {@link CannonState#KEY_LOADED}...). A new cannon is
 * {@link CannonState#EMPTY}, written as no key at all.
 *
 * <p>No ticker yet and nothing changes the state in game: this is the storage the future firing system plugs into
 * (docs/TENTES.md, "Canon médiéval : architecture du tir"): {@link CannonBlock#onUse} would load / ram / ignite,
 * a ticker registered through {@code CannonBlock.getTicker} would count {@link CannonState#fuseTicks} down and call a
 * {@code fire()} here (smoke and flash at {@link #muzzle()}, the sound, the projectile along {@link #muzzleDirection()},
 * {@link CannonState#fired}); the client recoil (bones "barrel", "carriage", "wheel_left", "wheel_right") would then
 * need the state on the client (toInitialChunkDataNbt / toUpdatePacket, not written yet).
 */
public class CannonBlockEntity extends TentBlockEntity {
	private CannonState state = CannonState.EMPTY;

	public CannonBlockEntity(BlockPos pos, BlockState blockState) {
		super(Tents.CANNON_BLOCK_ENTITY, pos, blockState);
	}

	/** The cannon's current state (never null). */
	public CannonState cannonState() {
		return state;
	}

	/** Replaces the state (null = {@link CannonState#EMPTY}) and marks the chunk for saving when it changed. */
	public void setCannonState(CannonState next) {
		next = next == null ? CannonState.EMPTY : next;
		if (!next.equals(state)) {
			state = next;
			markDirty();
		}
	}

	/** The world point at the centre of the muzzle (for smoke, flash, projectile), or the block's top centre if the JSON has none. */
	public Vec3d muzzle() {
		TentType type = tentType();
		TentType.Muzzle m = type == null ? null : type.muzzle(quarter());
		BlockPos p = getPos();
		return m == null ? Vec3d.ofCenter(p).add(0, 0.5, 0) : new Vec3d(p.getX() + 0.5 + m.x(), p.getY() + m.y(), p.getZ() + 0.5 + m.z());
	}

	/** The unit direction a shot would leave along (world axes), or straight up if the JSON has no muzzle. */
	public Vec3d muzzleDirection() {
		TentType type = tentType();
		TentType.Muzzle m = type == null ? null : type.muzzle(quarter());
		return m == null ? new Vec3d(0, 1, 0) : new Vec3d(m.dx(), m.dy(), m.dz());
	}

	@Override
	protected void readData(ReadView view) {
		super.readData(view);
		state = new CannonState(view.getBoolean(CannonState.KEY_LOADED, false), view.getInt(CannonState.KEY_POWDER, 0),
				view.getInt(CannonState.KEY_FUSE, 0), view.getLong(CannonState.KEY_LAST_SHOT, CannonState.NEVER));
	}

	@Override
	protected void writeData(WriteView view) {
		super.writeData(view);
		// only what differs from an empty cannon: an unused cannon adds nothing to its chunk's data
		if (state.loaded()) {
			view.putBoolean(CannonState.KEY_LOADED, true);
		}
		if (state.powder() != 0) {
			view.putInt(CannonState.KEY_POWDER, state.powder());
		}
		if (state.fuseTicks() != 0) {
			view.putInt(CannonState.KEY_FUSE, state.fuseTicks());
		}
		if (state.lastShotTime() != CannonState.NEVER) {
			view.putLong(CannonState.KEY_LAST_SHOT, state.lastShotTime());
		}
	}
}
