package fr.medievalships.door;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.vehicle.VehicleEntity;
import net.minecraft.item.ItemStack;
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
import fr.medievalships.core.DoorData;
import fr.medievalships.core.DoorDemands;
import fr.medievalships.core.DoorKeys;
import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorMotion;
import fr.medievalships.core.DoorType;
import fr.medievalships.entity.ShipPermissions;

/**
 * The block entity of a door ({@code medievalships:porte}, on its controller block): its movement (target, start
 * tick, start progress: the clients compute the rest, see {@link DoorMotion}), its settings (access and quest tag,
 * lock, manual, redstone, automatic closing, direction of opening), its linked levers, its name, and what asks it to be
 * open ({@link DoorDemands}). Saved with the chunk (with the version of its data, {@link DoorData}) and sent to the
 * clients with the block entity update packet at every change (never per tick; the lock is never sent).
 *
 * <p>The server ticker returns at once while nothing happens ({@link #busy}): it only works while the door moves (the
 * collisions, the sounds of the movement, the check for entities in the way while it closes), while a command's
 * timer or the automatic closing runs, and every {@link #LEVER_PERIOD} ticks when levers are linked (their blocks
 * read only where their chunk is loaded).
 *
 * <p>1.32.0: the keys ({@link #useKey}, {@link DoorKeys}), the automatic closing of one minute by default (the doors of
 * 1.31.0 migrated, {@link DoorData#autoClose}), the movement curve of {@link DoorMotion} for the collisions and the
 * sounds (unlocking click, leaves, creaks of the great gates, the slam of the closing, the lock).
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
	/** The lock of the door ("" for none): the keys bound to it open it in the key access. Never sent to the clients. */
	private String lock = "";
	private boolean manualEnabled = true;
	private boolean redstoneEnabled = true;
	private int autoCloseSeconds = DoorData.AUTO_CLOSE_DEFAULT;
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
	/** Loaded from older data: an open door held by hand gets its automatic closing on the first tick. */
	private boolean scheduleAutoClose;

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

	/** The door's lock ("" for none; on a client always "": it is never sent). */
	public String lock() {
		return lock;
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

	/** What a key bound to this door shows ("Ouvre : ..."): its name, or the coordinates of its controller. */
	public String keyLabel() {
		return DoorKeys.label(name, pos.getX(), pos.getY(), pos.getZ());
	}

	/** The door as the messages name it: « name », or its coordinates. */
	public String displayLabel() {
		return name.isEmpty() ? String.format(Locale.ROOT, "en %d %d %d", pos.getX(), pos.getY(), pos.getZ()) : "« " + name + " »";
	}

	public List<BlockPos> levers() {
		return List.copyOf(levers);
	}

	public DoorDemands demands() {
		return demands;
	}

	/** Game tick at which the automatic closing will drop the hand's demand (0: none running). */
	public long autoCloseAt() {
		return autoCloseAt;
	}

	/** The movement curve of this door's size. */
	public DoorMotion.Curve curve() {
		DoorType t = doorType();
		return t == null ? DoorMotion.SMALL : DoorMotion.curve(t);
	}

	/** Progress 0..1 at a game time (fractional between two ticks on a client). */
	public double progressAt(double now) {
		DoorType t = doorType();
		return DoorMotion.progress(target, startTick, startProgress, now, t == null ? 1 : t.durationTicks());
	}

	/** How open a leaf is (0 left, 1 right) at a game time, as drawn (the curve of {@link DoorMotion#leafAt}). */
	public double leafAt(double now, int leaf) {
		DoorType t = doorType();
		if (t == null) {
			return 0;
		}
		return DoorMotion.leafAt(DoorMotion.curve(t), t.leaves(), leaf, target, startTick, startProgress, now, t.durationTicks());
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
		if (scheduleAutoClose) {
			// a 1.31.0 door left open by hand: its new automatic closing starts now
			scheduleAutoClose = false;
			if (target && demands.manual && autoCloseAt == 0 && autoCloseSeconds > 0) {
				autoCloseAt = now + autoCloseSeconds * 20L;
				markDirty();
			}
		}
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

	/**
	 * The movement this tick: the collisions (with the curve the clients draw), the sounds of its events, the entities
	 * in the way while it closes.
	 */
	private void step(ServerWorld world, long now) {
		DoorType t = doorType();
		if (t == null) {
			pending = false;
			return;
		}
		DoorMotion.Curve c = DoorMotion.curve(t);
		int n = t.leaves();
		double p = progressAt(now);
		boolean solid = solid();
		// a movement that ended long ago (a door loaded with its chunk): its end is handled quietly
		boolean quiet = now > startTick + DoorMotion.ticksLeft(target, startProgress, t.durationTicks()) + 2;
		if (!quiet && now > startTick) {
			movementEffects(world, t, c, DoorMotion.events(c, n, target, progressAt(now - 1), p, now - startTick), now - startTick);
		}
		if (target) {
			if (DoorMotion.solidAfter(c, n, solid, true, p) != solid) {
				setSolid(world, false);
			}
			if (p >= 1) {
				pending = false;
			}
			return;
		}
		if (!solid) {
			// closing, its leaves not yet shut: never on somebody
			if (somethingInTheWay(world, t)) {
				holdUntil = now + RETRY_TICKS;
				markDirty();
				move(world, true);
				return;
			}
			if (DoorMotion.solidAfter(c, n, false, false, p)) {
				setSolid(world, true);
			}
		}
		if (p <= 0) {
			pending = false;
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
		startEffects(world, t, open);
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

	private void play(ServerWorld world, DoorType t, SoundEvent sound, float volume, float pitch) {
		double[] o = origin();
		world.playSound(null, o[0], o[1] + t.height() * 0.5, o[2], sound, SoundCategory.BLOCKS, volume, pitch);
	}

	private float pitch(ServerWorld world, DoorType t) {
		return t.soundPitch() * (0.95f + world.getRandom().nextFloat() * 0.1f);
	}

	/** The start of a movement: the latch (opening), the steam doors' piston, hiss and puff of steam. */
	private void startEffects(ServerWorld world, DoorType t, boolean open) {
		float pitch = pitch(world, t);
		if (open) {
			// the bolts and the latch: the leaves only move once the door is unlocked (see movementEffects)
			play(world, t, SoundEvents.BLOCK_TRIPWIRE_CLICK_ON, 0.6f, pitch * 0.9f);
			if (t.material() != DoorType.Material.WOOD) {
				play(world, t, SoundEvents.BLOCK_IRON_TRAPDOOR_OPEN, 0.35f, pitch * 1.2f);
			}
			world.emitGameEvent(null, GameEvent.BLOCK_OPEN, pos);
		}
		if (t.material() == DoorType.Material.STEAM) {
			play(world, t, open ? SoundEvents.BLOCK_PISTON_EXTEND : SoundEvents.BLOCK_PISTON_CONTRACT, 0.5f, pitch);
			play(world, t, SoundEvents.BLOCK_FIRE_EXTINGUISH, 0.35f, 0.8f + world.getRandom().nextFloat() * 0.2f);
		}
		if (t.steam()) {
			puff(world, t, 1.0);
		}
	}

	/**
	 * The sounds of the events of a tick of movement ({@link DoorMotion#events}): the leaves start (the door's open
	 * sound), a leaf hits the frame (the close sound; the second one softer), the bolts lock again, the creaks and
	 * mechanical noises of the great gates every {@link DoorMotion.Curve#creakPeriod} ticks while their leaves move.
	 */
	private void movementEffects(ServerWorld world, DoorType t, DoorMotion.Curve c, int ev, long ticks) {
		if (ev == 0) {
			return;
		}
		float pitch = pitch(world, t);
		float volume = t.size() == DoorType.Size.LARGE ? 1.4f : 1.0f;
		boolean wood = t.material() == DoorType.Material.WOOD;
		if ((ev & DoorMotion.EV_LEAVES_START) != 0) {
			play(world, t, wood ? SoundEvents.BLOCK_WOODEN_DOOR_OPEN : SoundEvents.BLOCK_IRON_DOOR_OPEN, volume, pitch);
		}
		if ((ev & DoorMotion.EV_SECOND_IMPACT) != 0) {
			play(world, t, wood ? SoundEvents.BLOCK_WOODEN_DOOR_CLOSE : SoundEvents.BLOCK_IRON_DOOR_CLOSE, volume * 0.6f, pitch * 1.05f);
		}
		if ((ev & DoorMotion.EV_IMPACT) != 0) {
			play(world, t, wood ? SoundEvents.BLOCK_WOODEN_DOOR_CLOSE : SoundEvents.BLOCK_IRON_DOOR_CLOSE, volume, pitch);
			world.emitGameEvent(null, GameEvent.BLOCK_CLOSE, pos);
		}
		if ((ev & DoorMotion.EV_LOCKED) != 0) {
			play(world, t, SoundEvents.BLOCK_TRIPWIRE_CLICK_OFF, 0.6f, pitch * 0.9f);
			if (t.steam()) {
				puff(world, t, 0.4);
			}
		}
		if ((ev & DoorMotion.EV_OPENED) != 0 && t.steam()) {
			puff(world, t, 0.4);
		}
		if ((ev & DoorMotion.EV_CREAK) != 0) {
			boolean odd = (ticks / Math.max(1, c.creakPeriod())) % 2 == 1;
			float p = 0.5f + world.getRandom().nextFloat() * 0.12f;
			if (wood) {
				play(world, t, odd ? SoundEvents.BLOCK_LADDER_STEP : SoundEvents.BLOCK_CHEST_OPEN, odd ? 0.8f : 0.45f, p);
			} else {
				play(world, t, odd ? SoundEvents.BLOCK_CHAIN_STEP : SoundEvents.BLOCK_GRINDSTONE_USE, odd ? 0.8f : 0.3f, p);
			}
		}
	}

	/** A few puffs of steam at the top of the frame ({@code share} of the full puff), nothing lasting. */
	private void puff(ServerWorld world, DoorType t, double share) {
		int full = switch (t.size()) {
			case SMALL -> 5;
			case MEDIUM -> 8;
			case LARGE -> 14;
		};
		int n = Math.max(1, (int) Math.round(full * share));
		double[] top = DoorLayout.toWorld(pos.getX(), pos.getY(), pos.getZ(), quarter(), t.width(), 0, t.height() - 0.3, 0.3);
		world.spawnParticles(ParticleTypes.CLOUD, top[0], top[1], top[2], n, t.width() * 0.3, 0.15, 0.15, 0.02);
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

	/**
	 * A player's click on any cell: the access decides (with, only when it refuses, the keys and the master key the
	 * player carries anywhere in his inventory), then the manual demand toggles.
	 */
	public void click(ServerWorld world, PlayerEntity player) {
		DoorAccess.Click verdict = access.click(manualEnabled, player.getCommandTags(), questTag, false);
		boolean byMaster = false;
		if (verdict != DoorAccess.Click.OK) {
			Set<String> carried = KeyItem.carriedLocks(player);
			DoorAccess.Click withKey = access.click(manualEnabled, player.getCommandTags(), questTag, DoorKeys.carries(carried, lock));
			verdict = DoorKeys.click(access, manualEnabled, player.getCommandTags(), questTag, lock, carried, KeyItem.carriesMaster(player),
					ShipPermissions.isAdmin(player));
			byMaster = verdict == DoorAccess.Click.OK && withKey != DoorAccess.Click.OK;
		}
		if (verdict != DoorAccess.Click.OK) {
			refuse(world, player, verdict.message(questTag));
			return;
		}
		String result = toggle(world);
		if (result != null) {
			player.sendMessage(Text.literal(result).formatted(Formatting.GOLD), true);
		} else if (byMaster) {
			player.sendMessage(Text.literal(target ? "Passe-partout : porte ouverte." : "Passe-partout : porte fermée.").formatted(Formatting.GOLD), true);
		}
	}

	/** A refused click: the message in the action bar, the locked chest's sound. */
	private void refuse(ServerWorld world, PlayerEntity player, String message) {
		player.sendMessage(Text.literal(message).formatted(Formatting.RED), true);
		double[] o = origin();
		world.playSound(null, o[0], o[1] + 1, o[2], SoundEvents.BLOCK_CHEST_LOCKED, SoundCategory.BLOCKS, 1.0f, 1.0f);
	}

	/**
	 * A click with a key or the master key in hand ({@code sneaking}: the player sneaks), see {@link DoorKeys#gesture}:
	 * the ordinary click, or one of the administrators' gestures (bind a blank key, give the door the lock of a key,
	 * switch the door between free and key access with the master key).
	 */
	public void useKey(ServerWorld world, PlayerEntity player, ItemStack stack, boolean sneaking) {
		boolean admin = ShipPermissions.isAdmin(player);
		String keyLock = KeyItem.lockOf(stack);
		switch (DoorKeys.gesture(KeyItem.held(stack), sneaking, admin, keyLock, lock)) {
			case CLICK -> click(world, player);
			case BIND -> {
				boolean copy = !lock.isEmpty();
				ensureLock();
				KeyItem.bind(stack, lock, keyLabel());
				if (access != DoorAccess.CLE) {
					setAccess(world, DoorAccess.CLE, null);
				} else {
					changed(world);
				}
				player.sendMessage(Text.literal((copy ? "Double de la clé de la porte " : "Clé liée à la porte ") + displayLabel()
						+ " : seuls les détenteurs de sa clé (et le passe-partout) l'ouvrent.").formatted(Formatting.GOLD), true);
				keySound(world);
			}
			case SHARE -> {
				boolean had = !lock.isEmpty();
				lock = keyLock;
				if (access != DoorAccess.CLE) {
					setAccess(world, DoorAccess.CLE, null);
				} else {
					changed(world);
				}
				String from = KeyItem.labelOf(stack);
				player.sendMessage(Text.literal("Porte " + displayLabel() + " : même serrure que la clé" + (from.isEmpty() ? "" : " de « " + from + " »")
						+ (had ? " (ses anciennes clés ne l'ouvrent plus)." : ".")).formatted(Formatting.GOLD), true);
				keySound(world);
			}
			case ALREADY -> player.sendMessage(Text.literal("Cette clé ouvre déjà cette porte.").formatted(Formatting.YELLOW), true);
			case TOGGLE -> {
				DoorAccess next = DoorKeys.toggled(access);
				setAccess(world, next, null);
				player.sendMessage(Text.literal("Porte " + displayLabel() + (next == DoorAccess.CLE
						? " : accès à clé (seuls les détenteurs de sa clé et le passe-partout l'ouvrent)."
						: " : accès libre (tout le monde l'ouvre).")).formatted(Formatting.GOLD), true);
				keySound(world);
			}
			case NOT_ADMIN -> refuse(world, player, "Seul un administrateur peut lier une clé à une porte.");
			case MASTER_REFUSED -> refuse(world, player, DoorAccess.Click.MASTER_REFUSED.message(""));
		}
	}

	private void keySound(ServerWorld world) {
		double[] o = origin();
		world.playSound(null, o[0], o[1] + 1, o[2], SoundEvents.ITEM_LODESTONE_COMPASS_LOCK, SoundCategory.BLOCKS, 0.8f, 1.2f);
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

	/**
	 * Opens — commands: for {@code seconds} when positive, otherwise like a hand (the automatic closing, one minute by
	 * default, applies).
	 */
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

	/** Sets the access; the key access gives the door a lock when it has none (without keys: only the master key opens it). */
	public void setAccess(ServerWorld world, DoorAccess access, String tag) {
		this.access = access;
		this.questTag = access == DoorAccess.QUETE && tag != null ? tag : "";
		if (access == DoorAccess.CLE) {
			ensureLock();
		}
		if (access == DoorAccess.VERROUILLEE || access == DoorAccess.ADMIN) {
			// locking closes a door a hand or a command opened
			demands.manual = false;
			demands.timedUntil = 0;
			autoCloseAt = 0;
		}
		changed(world);
		evaluate(world);
	}

	/** Gives the door a lock if it has none; returns it. */
	public String ensureLock() {
		if (lock.isEmpty()) {
			lock = DoorKeys.newLock(ThreadLocalRandom.current());
			markDirty();
		}
		return lock;
	}

	/** A new lock ({@code /porte serrure changer}): the keys of the old one no longer open the door. Returns it. */
	public String renewLock(ServerWorld world) {
		String old = lock;
		do {
			lock = DoorKeys.newLock(ThreadLocalRandom.current());
		} while (lock.equals(old));
		changed(world);
		return lock;
	}

	/** Gives the door this lock (the keys of that lock open it; its old keys no longer do). */
	public void setLock(ServerWorld world, String lock) {
		this.lock = lock == null ? "" : lock;
		changed(world);
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
		autoCloseSeconds = DoorData.clamp(seconds);
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
		int version = view.getInt("version", 0);
		target = view.getBoolean("open", false);
		startTick = view.getLong("start_tick", 0L);
		startProgress = view.getFloat("start_progress", 0f);
		backward = view.getBoolean("backward", true);
		DoorAccess a = DoorAccess.parse(view.getString("access", "libre"));
		access = a == null ? DoorAccess.LIBRE : a;
		questTag = view.getString("quest_tag", "");
		lock = view.getString("lock", "");
		manualEnabled = view.getBoolean("manual", true);
		redstoneEnabled = view.getBoolean("redstone", true);
		// 1.31.0 saved no version and closed nothing by default: those doors take the minute of 1.32.0
		autoCloseSeconds = DoorData.autoClose(version, view.getInt("auto_close", -1));
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
		scheduleAutoClose = version < DoorData.VERSION;
		pending = true; // the first tick finishes a movement the save interrupted (collisions)
	}

	@Override
	protected void writeData(WriteView view) {
		super.writeData(view);
		view.putInt("version", DoorData.VERSION);
		view.putBoolean("open", target);
		view.putLong("start_tick", startTick);
		view.putFloat("start_progress", startProgress);
		view.putBoolean("backward", backward);
		view.putString("access", access.word());
		if (!questTag.isEmpty()) {
			view.putString("quest_tag", questTag);
		}
		if (!lock.isEmpty()) {
			view.putString("lock", lock);
		}
		view.putBoolean("manual", manualEnabled);
		view.putBoolean("redstone", redstoneEnabled);
		view.putInt("auto_close", autoCloseSeconds);
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

	/** What the clients get (the chunk data and the update packet): everything but the lock (a client never needs it). */
	@Override
	public NbtCompound toInitialChunkDataNbt(RegistryWrapper.WrapperLookup registries) {
		NbtCompound nbt = createNbt(registries);
		nbt.remove("lock");
		return nbt;
	}
}
