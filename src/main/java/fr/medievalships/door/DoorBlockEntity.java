package fr.medievalships.door;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.vehicle.VehicleEntity;
import net.minecraft.network.listener.ClientPlayPacketListener;
import net.minecraft.network.packet.Packet;
import net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.state.property.Properties;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.world.World;
import net.minecraft.world.event.GameEvent;

import fr.medievalships.core.DoorAccess;
import fr.medievalships.core.DoorDemands;
import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorMotion;
import fr.medievalships.core.DoorType;

/**
 * The block entity of a door ({@code medievalships:porte}, on its controller block): its movement (target, start
 * tick, start progress: the clients compute the rest, see {@link DoorMotion}), its settings (access and quest tag,
 * manual, redstone, automatic closing, direction of opening), its linked levers, its name, and what asks it to be
 * open ({@link DoorDemands}). Saved with the chunk and sent to the clients with the block entity update packet at
 * every change (never per tick).
 *
 * <p>The server ticker returns at once while nothing happens ({@link #busy}): it only works while the door moves (the
 * collisions at half way and at the end, the check for entities in the way while it closes), while a command's
 * timer or the automatic closing runs, and every {@link #LEVER_PERIOD} ticks when levers are linked (their blocks
 * read only where their chunk is loaded).
 */
public class DoorBlockEntity extends BlockEntity {
	/** Ticks between two looks at the linked levers. */
	public static final int LEVER_PERIOD = 4;
	/** Most linked levers per door, and their farthest distance (blocks) from the door. */
	public static final int MAX_LEVERS = 8;
	public static final double LEVER_RANGE = 32.0;
	/** Ticks before a door that something kept from closing tries again. */
	public static final int RETRY_TICKS = 40;

	// ---- movement (sent to the clients)
	private boolean target;
	private long startTick;
	private float startProgress;
	private boolean backward = true;
	// ---- settings
	private DoorAccess access = DoorAccess.LIBRE;
	private String questTag = "";
	private boolean manualEnabled = true;
	private boolean redstoneEnabled = true;
	private int autoCloseSeconds;
	private String name = "";
	private final List<BlockPos> levers = new ArrayList<>();
	// ---- what asks it to be open
	private final DoorDemands demands = new DoorDemands();
	private long autoCloseAt;
	/** Game tick until which the door stays open because something was in its way. */
	private long holdUntil;
	/** Last known state of each linked lever (bit i), kept while its chunk is not loaded. */
	private int leverBits;
	/** A movement whose end (collisions, sounds) is still to be handled; true after loading until the first tick looks. */
	private boolean pending = true;

	public DoorBlockEntity(BlockPos pos, BlockState state) {
		super(Doors.BLOCK_ENTITY, pos, state);
	}

	// ------------------------------------------------------------------ reading

	@Nullable
	public DoorType doorType() {
		return getCachedState().getBlock() instanceof DoorBlock d ? d.doorType() : null;
	}

	public int quarter() {
		return DoorStructure.quarter(getCachedState());
	}

	/** Is the door asked to be open (opening or open)? */
	public boolean target() {
		return target;
	}

	public long startTick() {
		return startTick;
	}

	public float startProgress() {
		return startProgress;
	}

	/** Does it open backwards (away from the player who placed it)? */
	public boolean backward() {
		return backward;
	}

	public DoorAccess access() {
		return access;
	}

	public String questTag() {
		return questTag;
	}

	public boolean manualEnabled() {
		return manualEnabled;
	}

	public boolean redstoneEnabled() {
		return redstoneEnabled;
	}

	public int autoCloseSeconds() {
		return autoCloseSeconds;
	}

	public String name() {
		return name;
	}

	public List<BlockPos> levers() {
		return List.copyOf(levers);
	}

	public DoorDemands demands() {
		return demands;
	}

	/** Progress 0..1 at a game time (fractional between two ticks on a client). */
	public double progressAt(double now) {
		DoorType t = doorType();
		return DoorMotion.progress(target, startTick, startProgress, now, t == null ? 1 : t.durationTicks());
	}

	public double progress() {
		return world == null ? startProgress : progressAt(world.getTime());
	}

	public boolean moving() {
		return DoorMotion.moving(target, progress());
	}

	/** Is the door solid (its block states)? */
	public boolean solid() {
		BlockState s = getCachedState();
		return s.contains(DoorStructure.SOLID) && s.get(DoorStructure.SOLID);
	}

	/** Every cell of the door. */
	public List<BlockPos> cells() {
		DoorType t = doorType();
		return t == null ? List.of(pos) : DoorStructure.cells(pos, quarter(), t);
	}

	/** World centre of the bottom of the opening. */
	public double[] origin() {
		DoorType t = doorType();
		int w = t == null ? 1 : t.width();
		return new double[] {DoorLayout.originX(pos.getX(), quarter(), w), pos.getY(), DoorLayout.originZ(pos.getZ(), quarter(), w)};
	}

	// ------------------------------------------------------------------ the server's side

	/** The ticker: returns at once while nothing happens. */
	public static void serverTick(World world, BlockPos pos, BlockState state, DoorBlockEntity door) {
		if (door.busy() && world instanceof ServerWorld sw) {
			door.tick(sw);
		}
	}

	/** Is there anything to do this tick (a movement, a timer, linked levers)? */
	public boolean busy() {
		return pending || !levers.isEmpty() || demands.timedUntil > 0 || autoCloseAt > 0 || holdUntil > 0;
	}

	private void tick(ServerWorld world) {
		long now = world.getTime();
		boolean changed = false;
		if (demands.timedUntil > 0 && now >= demands.timedUntil) {
			demands.timedUntil = 0;
			changed = true;
		}
		if (autoCloseAt > 0 && now >= autoCloseAt) {
			autoCloseAt = 0;
			demands.manual = false;
			changed = true;
		}
		if (holdUntil > 0 && now >= holdUntil) {
			holdUntil = 0;
			changed = true;
		}
		if (!levers.isEmpty() && Math.floorMod(now + pos.hashCode(), LEVER_PERIOD) == 0) {
			changed |= pollLevers(world);
		}
		if (changed) {
			markDirty();
			evaluate(world);
		}
		if (pending) {
			step(world, now);
		}
	}

	/** The movement this tick: the collisions at half way and at the end, the entities in the way while closing. */
	private void step(ServerWorld world, long now) {
		DoorType t = doorType();
		if (t == null) {
			pending = false;
			return;
		}
		double p = progressAt(now);
		boolean solid = solid();
		// a movement that ended long ago (a door loaded with its chunk): its end is handled quietly
		boolean quiet = now > startTick + DoorMotion.ticksLeft(target, startProgress, t.durationTicks()) + 2;
		if (target) {
			if (DoorMotion.solidAfter(solid, true, p) != solid) {
				setSolid(world, false);
			}
			if (p >= 1) {
				pending = false;
				if (!quiet) {
					effects(world, t, false, true);
				}
			}
			return;
		}
		if (p > 0 || !solid) {
			// closing (or closed but not yet solid): never on somebody
			if (somethingInTheWay(world, t)) {
				holdUntil = now + RETRY_TICKS;
				markDirty();
				move(world, true);
				return;
			}
		}
		if (p <= 0) {
			if (!solid) {
				setSolid(world, true);
			}
			pending = false;
			if (!quiet) {
				effects(world, t, false, false);
			}
		}
	}

	/** Re-reads every demand and starts the movement it calls for (never closing on an entity in the way). */
	public void evaluate(ServerWorld world) {
		long now = world.getTime();
		boolean want = demands.wanted(now, access.redstoneAccepted(redstoneEnabled), access.leversAccepted(redstoneEnabled)) || now < holdUntil;
		if (want == target) {
			return;
		}
		DoorType t = doorType();
		if (!want && t != null && somethingInTheWay(world, t)) {
			holdUntil = now + RETRY_TICKS / 2;
			markDirty();
			return;
		}
		move(world, want);
	}

	/** Starts a movement towards open or closed from wherever the door is. */
	private void move(ServerWorld world, boolean open) {
		DoorType t = doorType();
		if (t == null || open == target) {
			return;
		}
		long now = world.getTime();
		double p = progressAt(now);
		target = open;
		startTick = now;
		startProgress = (float) p;
		pending = true;
		markDirty();
		sync(world);
		effects(world, t, true, open);
	}

	private void setSolid(ServerWorld world, boolean solid) {
		DoorType t = doorType();
		if (t == null) {
			return;
		}
		int q = quarter();
		for (int[] c : DoorLayout.cells(pos.getX(), pos.getY(), pos.getZ(), q, t.width(), t.height())) {
			BlockPos p = new BlockPos(c[0], c[1], c[2]);
			if (!DoorStructure.loaded(world, p)) {
				continue;
			}
			BlockState s = world.getBlockState(p);
			if (DoorStructure.isCell(s, t, q, c[3], c[4]) && s.get(DoorStructure.SOLID) != solid) {
				// listeners only: the clients get the new shape, no neighbour update (no redstone loop, nothing pops off)
				world.setBlockState(p, s.with(DoorStructure.SOLID, solid), Block.NOTIFY_LISTENERS);
			}
		}
	}

	/** Is a player, a mob or a vehicle in the opening or in the quarter circles the leaves sweep? */
	public boolean somethingInTheWay(ServerWorld world, DoorType t) {
		Box box = DoorStructure.sweptBox(pos, quarter(), t, backward).contract(0.01);
		return !world.getOtherEntities(null, box, DoorBlockEntity::blocksClosing).isEmpty();
	}

	static boolean blocksClosing(Entity e) {
		return e.isAlive() && !e.isSpectator() && (e instanceof LivingEntity || e instanceof VehicleEntity);
	}

	/** Sounds (and the steam doors' puffs) at the start ({@code start}) or the end of a movement. */
	private void effects(ServerWorld world, DoorType t, boolean start, boolean open) {
		double[] o = origin();
		double cx = o[0], cy = o[1] + t.height() * 0.5, cz = o[2];
		float pitch = t.soundPitch() * (0.95f + world.getRandom().nextFloat() * 0.1f);
		float volume = t.size() == DoorType.Size.LARGE ? 1.4f : 1.0f;
		SoundEvent sound = null;
		if (start && open) {
			sound = t.material() == DoorType.Material.WOOD ? SoundEvents.BLOCK_WOODEN_DOOR_OPEN : SoundEvents.BLOCK_IRON_DOOR_OPEN;
			if (t.material() == DoorType.Material.STEAM) {
				world.playSound(null, cx, cy, cz, SoundEvents.BLOCK_PISTON_EXTEND, SoundCategory.BLOCKS, 0.5f, pitch);
			}
			world.emitGameEvent(null, GameEvent.BLOCK_OPEN, pos);
		} else if (start) {
			if (t.material() == DoorType.Material.STEAM) {
				world.playSound(null, cx, cy, cz, SoundEvents.BLOCK_PISTON_CONTRACT, SoundCategory.BLOCKS, 0.5f, pitch);
			}
		} else if (!open) {
			sound = t.material() == DoorType.Material.WOOD ? SoundEvents.BLOCK_WOODEN_DOOR_CLOSE : SoundEvents.BLOCK_IRON_DOOR_CLOSE;
			world.emitGameEvent(null, GameEvent.BLOCK_CLOSE, pos);
		}
		if (sound != null) {
			world.playSound(null, cx, cy, cz, sound, SoundCategory.BLOCKS, volume, pitch);
		}
		if (t.steam()) {
			// a few puffs of steam at the top of the frame, nothing lasting
			int n = switch (t.size()) {
				case SMALL -> 4;
				case MEDIUM -> 7;
				case LARGE -> 12;
			};
			double[] top = DoorLayout.toWorld(pos.getX(), pos.getY(), pos.getZ(), quarter(), t.width(), 0, t.height() - 0.3, 0.3);
			world.spawnParticles(ParticleTypes.CLOUD, top[0], top[1], top[2], n, t.width() * 0.3, 0.15, 0.15, 0.02);
		}
	}

	/** Sends the door's state to the clients that see it (the block entity update packet). */
	public void sync(ServerWorld world) {
		BlockState s = getCachedState();
		world.updateListeners(pos, s, s, Block.NOTIFY_LISTENERS);
	}

	private void changed(ServerWorld world) {
		markDirty();
		sync(world);
	}

	// ------------------------------------------------------------------ the inputs

	/** A player's click on any cell: the access decides, then the manual demand toggles. */
	public void click(ServerWorld world, PlayerEntity player) {
		DoorAccess.Click verdict = access.click(manualEnabled, player.getCommandTags(), questTag);
		if (verdict != DoorAccess.Click.OK) {
			player.sendMessage(Text.literal(verdict.message(questTag)).formatted(Formatting.RED), true);
			double[] o = origin();
			world.playSound(null, o[0], o[1] + 1, o[2], SoundEvents.BLOCK_CHEST_LOCKED, SoundCategory.BLOCKS, 1.0f, 1.0f);
			return;
		}
		String result = toggle(world);
		if (result != null) {
			player.sendMessage(Text.literal(result).formatted(Formatting.GOLD), true);
		}
	}

	/**
	 * Opens the door if it is closed or closing, closes it otherwise (the manual demand, with the automatic closing
	 * when set). Returns why nothing visible changed (French), or null.
	 */
	public String toggle(ServerWorld world) {
		long now = world.getTime();
		if (target) {
			demands.manual = false;
			demands.timedUntil = 0;
			autoCloseAt = 0;
		} else {
			demands.manual = true;
			autoCloseAt = autoCloseSeconds > 0 ? now + autoCloseSeconds * 20L : 0;
		}
		markDirty();
		boolean before = target;
		evaluate(world);
		if (before && target) {
			String holder = demands.holder(now, access.redstoneAccepted(redstoneEnabled), access.leversAccepted(redstoneEnabled));
			return holder != null ? "La porte reste ouverte : " + holder + " la maintient." : "Quelque chose bloque la fermeture de la porte.";
		}
		return null;
	}

	/** Opens (a manual demand, or for {@code seconds} when positive) — commands. Returns what still holds it, or null. */
	public void open(ServerWorld world, int seconds) {
		long now = world.getTime();
		if (seconds > 0) {
			demands.timedUntil = Math.max(demands.timedUntil, now + seconds * 20L);
		} else {
			demands.manual = true;
			autoCloseAt = autoCloseSeconds > 0 ? now + autoCloseSeconds * 20L : 0;
		}
		markDirty();
		evaluate(world);
	}

	/** Closes (forgets the manual and timed demands) — commands. Returns what still holds it open (French), or null. */
	@Nullable
	public String close(ServerWorld world) {
		demands.manual = false;
		demands.timedUntil = 0;
		autoCloseAt = 0;
		markDirty();
		evaluate(world);
		if (target) {
			String holder = demands.holder(world.getTime(), access.redstoneAccepted(redstoneEnabled), access.leversAccepted(redstoneEnabled));
			return holder != null ? holder : "une entité dans le passage";
		}
		return null;
	}

	/** Reads the redstone around every cell (any cell powered: the redstone asks the door to be open). */
	public void updateRedstone(ServerWorld world) {
		boolean powered = false;
		for (BlockPos p : cells()) {
			if (DoorStructure.loaded(world, p) && world.isReceivingRedstonePower(p)) {
				powered = true;
				break;
			}
		}
		if (powered != demands.redstone) {
			demands.redstone = powered;
			markDirty();
			evaluate(world);
		}
	}

	/** Looks at the linked levers whose chunk is loaded (never loads one); true when the lever demand changed. */
	private boolean pollLevers(ServerWorld world) {
		int bits = leverBits;
		for (int i = 0; i < levers.size() && i < MAX_LEVERS; i++) {
			BlockPos p = levers.get(i);
			if (!DoorStructure.loaded(world, p)) {
				continue; // kept as it was last seen
			}
			bits = powered(world.getBlockState(p)) ? bits | (1 << i) : bits & ~(1 << i);
		}
		leverBits = bits;
		boolean any = bits != 0;
		if (any != demands.lever) {
			demands.lever = any;
			return true;
		}
		return false;
	}

	/** Is a linkable block (lever, button, pressure plate...) switched on? */
	public static boolean powered(BlockState s) {
		if (s.contains(Properties.POWERED)) {
			return s.get(Properties.POWERED);
		}
		if (s.contains(Properties.POWER)) {
			return s.get(Properties.POWER) > 0;
		}
		return false;
	}

	/** Can this block be linked (it has an on / off or a power state)? */
	public static boolean linkable(BlockState s) {
		return s.contains(Properties.POWERED) || s.contains(Properties.POWER);
	}

	// ------------------------------------------------------------------ settings (commands)

	public void setAccess(ServerWorld world, DoorAccess access, String tag) {
		this.access = access;
		this.questTag = access == DoorAccess.QUETE && tag != null ? tag : "";
		if (access == DoorAccess.VERROUILLEE || access == DoorAccess.ADMIN) {
			// locking closes a door a hand or a command opened
			demands.manual = false;
			demands.timedUntil = 0;
			autoCloseAt = 0;
		}
		changed(world);
		evaluate(world);
	}

	public void setManual(ServerWorld world, boolean on) {
		manualEnabled = on;
		changed(world);
	}

	public void setRedstone(ServerWorld world, boolean on) {
		redstoneEnabled = on;
		changed(world);
		evaluate(world);
	}

	public void setAutoClose(ServerWorld world, int seconds) {
		autoCloseSeconds = Math.max(0, Math.min(3600, seconds));
		if (autoCloseSeconds == 0) {
			autoCloseAt = 0;
		} else if (demands.manual) {
			autoCloseAt = world.getTime() + autoCloseSeconds * 20L;
		}
		changed(world);
	}

	public void setBackward(ServerWorld world, boolean backward) {
		this.backward = backward;
		changed(world);
	}

	public void setName(ServerWorld world, String name) {
		this.name = name == null ? "" : name;
		changed(world);
	}

	/** Links a lever; returns why not (French), or null. */
	@Nullable
	public String link(ServerWorld world, BlockPos lever) {
		if (levers.contains(lever)) {
			return "Ce levier est déjà lié à cette porte.";
		}
		if (levers.size() >= MAX_LEVERS) {
			return "Cette porte a déjà " + MAX_LEVERS + " leviers liés (le maximum).";
		}
		double[] o = origin();
		double d = Math.sqrt(lever.getSquaredDistance(o[0], o[1] + 1, o[2]));
		if (d > LEVER_RANGE + 1e-6) {
			return String.format(Locale.ROOT, "Le levier est trop loin de la porte (%.0f blocs, %d au plus).", d, (int) LEVER_RANGE);
		}
		levers.add(lever.toImmutable());
		leverBits = 0;
		changed(world);
		pollLevers(world);
		evaluate(world);
		return null;
	}

	/** Unlinks a lever (null: all of them); returns how many were removed. */
	public int unlink(ServerWorld world, @Nullable BlockPos lever) {
		int before = levers.size();
		if (lever == null) {
			levers.clear();
		} else {
			levers.remove(lever);
		}
		leverBits = 0;
		demands.lever = false;
		pollLevers(world);
		changed(world);
		evaluate(world);
		return before - levers.size();
	}

	/** Initial state of a door just placed: solid, closed, the redstone around it read. */
	void placed(ServerWorld world) {
		target = false;
		startTick = world.getTime();
		startProgress = 0;
		pending = false;
		demands.redstone = false;
		markDirty();
		updateRedstone(world);
	}

	// ------------------------------------------------------------------ saving and syncing

	@Override
	protected void readData(ReadView view) {
		super.readData(view);
		target = view.getBoolean("open", false);
		startTick = view.getLong("start_tick", 0L);
		startProgress = view.getFloat("start_progress", 0f);
		backward = view.getBoolean("backward", true);
		DoorAccess a = DoorAccess.parse(view.getString("access", "libre"));
		access = a == null ? DoorAccess.LIBRE : a;
		questTag = view.getString("quest_tag", "");
		manualEnabled = view.getBoolean("manual", true);
		redstoneEnabled = view.getBoolean("redstone", true);
		autoCloseSeconds = view.getInt("auto_close", 0);
		name = view.getString("name", "");
		levers.clear();
		view.getOptionalIntArray("levers").ifPresent(a2 -> {
			for (int i = 0; i + 2 < a2.length && levers.size() < MAX_LEVERS; i += 3) {
				levers.add(new BlockPos(a2[i], a2[i + 1], a2[i + 2]));
			}
		});
		demands.manual = view.getBoolean("want_manual", false);
		demands.redstone = view.getBoolean("want_redstone", false);
		demands.lever = view.getBoolean("want_lever", false);
		demands.timedUntil = view.getLong("timed_until", 0L);
		autoCloseAt = view.getLong("auto_close_at", 0L);
		holdUntil = view.getLong("hold_until", 0L);
		leverBits = view.getInt("lever_bits", 0);
		pending = true; // the first tick finishes a movement the save interrupted (collisions)
	}

	@Override
	protected void writeData(WriteView view) {
		super.writeData(view);
		view.putBoolean("open", target);
		view.putLong("start_tick", startTick);
		view.putFloat("start_progress", startProgress);
		view.putBoolean("backward", backward);
		view.putString("access", access.word());
		if (!questTag.isEmpty()) {
			view.putString("quest_tag", questTag);
		}
		view.putBoolean("manual", manualEnabled);
		view.putBoolean("redstone", redstoneEnabled);
		if (autoCloseSeconds > 0) {
			view.putInt("auto_close", autoCloseSeconds);
		}
		if (!name.isEmpty()) {
			view.putString("name", name);
		}
		if (!levers.isEmpty()) {
			int[] a = new int[levers.size() * 3];
			for (int i = 0; i < levers.size(); i++) {
				a[i * 3] = levers.get(i).getX();
				a[i * 3 + 1] = levers.get(i).getY();
				a[i * 3 + 2] = levers.get(i).getZ();
			}
			view.putIntArray("levers", a);
		}
		view.putBoolean("want_manual", demands.manual);
		view.putBoolean("want_redstone", demands.redstone);
		view.putBoolean("want_lever", demands.lever);
		if (demands.timedUntil > 0) {
			view.putLong("timed_until", demands.timedUntil);
		}
		if (autoCloseAt > 0) {
			view.putLong("auto_close_at", autoCloseAt);
		}
		if (holdUntil > 0) {
			view.putLong("hold_until", holdUntil);
		}
		if (leverBits != 0) {
			view.putInt("lever_bits", leverBits);
		}
	}

	@Override
	public Packet<ClientPlayPacketListener> toUpdatePacket() {
		return BlockEntityUpdateS2CPacket.create(this);
	}

	@Override
	public NbtCompound toInitialChunkDataNbt(RegistryWrapper.WrapperLookup registries) {
		return createNbt(registries);
	}
}
