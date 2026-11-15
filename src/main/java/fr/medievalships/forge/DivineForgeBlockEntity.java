package fr.medievalships.forge;

import java.util.function.Consumer;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.network.listener.ClientPlayPacketListener;
import net.minecraft.network.packet.Packet;
import net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.world.World;

import fr.medievalships.api.DivineForgeApi;
import fr.medievalships.core.ForgeActivity;
import fr.medievalships.core.ForgeAnimation;
import fr.medievalships.core.TentType;
import fr.medievalships.tent.TentBlockEntity;
import fr.medievalships.tent.TentCollisions;

/**
 * The block entity of the divine forge (1.34.0, type {@code medievalships:forge_divine}): a {@link TentBlockEntity} (the
 * collisions and the drawing follow it like any prop) that keeps the forge's state: at rest, or active until an end tick
 * ({@link ForgeActivity}). Persisted (an activity under way goes on after a restart, its end being game time) and sent to
 * the clients, which animate the forge from it. The forge crafts nothing and is linked to nothing: only
 * {@code /forge animer} and {@link DivineForgeApi} start an activity, for whatever system the server uses.
 *
 * <p>The server ticker only compares the end tick with the clock and ends the activity when it is due ({@link #finish}:
 * a magic sound and light, the {@link DivineForgeApi#ACTIVITY_FINISHED} event); the client ticker hands the forge to the
 * client's effects ({@link #clientEffects}: particles and sounds near the player). No entity, no real fire.
 */
public class DivineForgeBlockEntity extends TentBlockEntity {
	/** Version of the saved data. */
	public static final int VERSION = 1;

	/** The client's effects (particles, sounds), set by the client initializer; null on a dedicated server. */
	@Nullable
	public static volatile Consumer<DivineForgeBlockEntity> clientEffects;

	private final ForgeActivity activity = new ForgeActivity();

	// ---- client side only, never saved: the eased pace of the animation and the effects' timers (game ticks)
	/** The renderer's eased pace (gears, flipbooks), integrated from frame to frame. */
	public final ForgeAnimation.Track track = new ForgeAnimation.Track();
	public long nextCrackle, nextMachine, nextSteam, nextHammer;
	/** Was the forge active at the last client tick (the change starts a burst of effects)? */
	public boolean wasActive;

	public DivineForgeBlockEntity(BlockPos pos, BlockState state) {
		super(DivineForge.BLOCK_ENTITY, pos, state);
	}

	/** The state (read only for the callers: change it through {@link #startActivity} and {@link #stop}). */
	public ForgeActivity activity() {
		return activity;
	}

	/** Is the forge active (the animation of an activity under way)? */
	public boolean active() {
		return activity.active();
	}

	/** Ticks left of the activity under way (0 at rest). */
	public long remainingTicks() {
		return world == null ? 0 : activity.remaining(world.getTime());
	}

	/** The forge's world box (its extent turned to its facing), for distances and for finding it from any point. */
	public Box worldExtent() {
		TentType t = tentType();
		return t == null ? new Box(pos) : TentCollisions.worldExtent(t, pos, quarter());
	}

	// ------------------------------------------------------------------ starting and ending (server)

	/** Starts an activity of {@code ticks} (1 to {@link ForgeActivity#MAX_TICKS}): {@code /forge animer}, the API. False when active. */
	public boolean startActivity(ServerWorld world, int ticks) {
		if (!activity.start(world.getTime(), ticks)) {
			return false;
		}
		world.playSound(null, pos, SoundEvents.BLOCK_BLASTFURNACE_FIRE_CRACKLE, SoundCategory.BLOCKS, 1.0f, 0.7f);
		world.playSound(null, pos, SoundEvents.BLOCK_SMITHING_TABLE_USE, SoundCategory.BLOCKS, 0.8f, 0.8f);
		changed(world);
		DivineForgeApi.ACTIVITY_STARTED.invoker().onStarted(world, pos, (int) activity.total());
		return true;
	}

	/** Ends the activity under way now ({@code /forge arreter}, the API). False at rest. */
	public boolean stop(ServerWorld world) {
		if (!activity.active()) {
			return false;
		}
		boolean early = !activity.due(world.getTime());
		activity.endAt(world.getTime());
		finish(world, early, false);
		return true;
	}

	static void serverTick(World world, BlockPos pos, BlockState state, DivineForgeBlockEntity forge) {
		if (forge.activity.due(world.getTime()) && world instanceof ServerWorld sw) {
			forge.finish(sw, false, false);
		}
	}

	static void clientTick(World world, BlockPos pos, BlockState state, DivineForgeBlockEntity forge) {
		Consumer<DivineForgeBlockEntity> fx = clientEffects;
		if (fx != null) {
			fx.accept(forge);
		}
	}

	/**
	 * Ends the activity: the magic sound and light (unless the forge is being removed), the clients told, the
	 * {@link DivineForgeApi#ACTIVITY_FINISHED} event ({@code stopped}: ended before its time).
	 */
	void finish(ServerWorld world, boolean stopped, boolean removed) {
		if (!activity.complete()) {
			return;
		}
		if (!removed) {
			double[] c = center();
			world.playSound(null, pos, SoundEvents.BLOCK_BEACON_POWER_SELECT, SoundCategory.BLOCKS, 1.2f, 1.3f);
			world.playSound(null, pos, SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME, SoundCategory.BLOCKS, 1.5f, 0.8f);
			world.spawnParticles(ParticleTypes.END_ROD, c[0], c[1] + 1.2, c[2], 28, 0.8, 0.6, 0.8, 0.04);
			world.spawnParticles(ParticleTypes.WAX_ON, c[0], c[1] + 0.8, c[2], 14, 0.6, 0.3, 0.6, 0.5);
			changed(world);
		}
		DivineForgeApi.ACTIVITY_FINISHED.invoker().onFinished(world, pos, stopped || removed);
	}

	/** Where the forge's end-of-activity light comes from: above the anvil, in front of the furnace (world coordinates). */
	double[] center() {
		double[] r = TentType.rotate(0, 1.4, quarter());
		return new double[] {pos.getX() + 0.5 + r[0], pos.getY() + 1.0, pos.getZ() + 0.5 + r[1]};
	}

	/** The forge is taken away (broken, {@code /tent remove}): an activity under way ends with it; nothing is left. */
	@Override
	public void onBlockReplaced(BlockPos pos, BlockState oldState) {
		super.onBlockReplaced(pos, oldState);
		if (world instanceof ServerWorld sw && activity.active()) {
			activity.endAt(sw.getTime());
			finish(sw, true, true);
		}
	}

	/** Saved, and sent to the clients that see the forge (the block entity update packet). */
	void changed(ServerWorld world) {
		markDirty();
		BlockState s = getCachedState();
		world.updateListeners(pos, s, s, Block.NOTIFY_LISTENERS);
	}

	// ------------------------------------------------------------------ saving and syncing

	@Override
	protected void readData(ReadView view) {
		super.readData(view);
		activity.restore(view.getBoolean("active", false), view.getLong("start", 0L), view.getLong("end", 0L));
	}

	@Override
	protected void writeData(WriteView view) {
		super.writeData(view);
		view.putInt("forge_version", VERSION);
		view.putBoolean("active", activity.active());
		if (activity.active()) {
			view.putLong("start", activity.start());
			view.putLong("end", activity.end());
		}
	}

	@Override
	public Packet<ClientPlayPacketListener> toUpdatePacket() {
		return BlockEntityUpdateS2CPacket.create(this);
	}

	/** What the clients get: the whole state (at rest or active, start and end ticks). */
	@Override
	public NbtCompound toInitialChunkDataNbt(RegistryWrapper.WrapperLookup registries) {
		return createNbt(registries);
	}
}
