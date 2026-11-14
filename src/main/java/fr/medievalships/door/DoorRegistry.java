package fr.medievalships.door;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mojang.serialization.Codec;

import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.PersistentState;
import net.minecraft.world.PersistentStateType;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.DoorType;

/**
 * The doors of the server and their names ({@code /porte nommer}), stored in the overworld's
 * {@code data/medievalships_doors.dat} as plain JSON inside the NBT, like the drawbridges: dimension, controller
 * position, type and name of each door, and since 1.33.0 its lock (server side only: never sent to a client). Filled
 * when a door is placed (and when a door's chunk loads, for the doors placed otherwise), emptied when it is removed; a
 * command finds a named door here, wherever it is; binding a key finds here whether another door uses the same lock
 * ({@link #lockUsedElsewhere}: the locks shared in 1.32.0).
 */
public final class DoorRegistry extends PersistentState {
	private static final Gson GSON = new GsonBuilder().create();

	/** One door: where its controller is, what it is, its name ("" for none), its lock ("" or null: none, or not known yet). */
	public static final class Entry {
		public String dimension;
		public int x, y, z;
		public String type;
		public String name = "";
		public String lock = "";

		public BlockPos pos() {
			return new BlockPos(x, y, z);
		}
	}

	static final class Contents {
		int version = 1;
		Map<String, Entry> doors = new LinkedHashMap<>();
	}

	private static final Codec<DoorRegistry> CODEC = Codec.STRING.fieldOf("json").codec().xmap(
			json -> {
				DoorRegistry d = new DoorRegistry();
				try {
					Contents c = GSON.fromJson(json, Contents.class);
					if (c != null) {
						d.contents = c;
						if (c.doors == null) {
							c.doors = new LinkedHashMap<>();
						}
					}
				} catch (Exception e) {
					MedievalShips.LOGGER.error("Could not read the door registry", e);
				}
				return d;
			},
			d -> GSON.toJson(d.contents));

	public static final PersistentStateType<DoorRegistry> TYPE =
			new PersistentStateType<>(MedievalShips.MOD_ID + "_doors", DoorRegistry::new, CODEC, null);

	private Contents contents = new Contents();

	public DoorRegistry() {
	}

	public static DoorRegistry get(MinecraftServer server) {
		return server.getOverworld().getPersistentStateManager().getOrCreate(TYPE);
	}

	private static String key(String dimension, BlockPos pos) {
		return dimension + " " + pos.getX() + " " + pos.getY() + " " + pos.getZ();
	}

	private static String dim(World world) {
		return world.getRegistryKey().getValue().toString();
	}

	/** Adds or updates a door (its lock kept when it was known). */
	public void put(World world, BlockPos controller, DoorType type, String name) {
		Entry old = contents.doors.get(key(dim(world), controller));
		put(world, controller, type, name, old == null || old.lock == null ? "" : old.lock);
	}

	/** Adds or updates a door with its lock. */
	public void put(World world, BlockPos controller, DoorType type, String name, String lock) {
		Entry e = new Entry();
		e.dimension = dim(world);
		e.x = controller.getX();
		e.y = controller.getY();
		e.z = controller.getZ();
		e.type = type.id();
		e.name = name == null ? "" : name;
		e.lock = lock == null ? "" : lock;
		Entry old = contents.doors.put(key(e.dimension, controller), e);
		if (old == null || !old.name.equals(e.name) || !old.type.equals(e.type) || !e.lock.equals(old.lock)) {
			markDirty();
		}
	}

	/** Adds a door found in the world if it is not known yet (a chunk loading), keeping its name and its lock up to date. */
	public void ensure(World world, BlockPos controller, DoorType type, String name, String lock) {
		Entry old = contents.doors.get(key(dim(world), controller));
		String n = name == null ? "" : name, l = lock == null ? "" : lock;
		if (old == null || !old.type.equals(type.id()) || !old.name.equals(n) || !l.equals(old.lock)) {
			put(world, controller, type, n, l);
		}
	}

	/** A door's lock changed (a key bound, a new lock). */
	public void setLock(World world, BlockPos controller, String lock) {
		Entry e = contents.doors.get(key(dim(world), controller));
		String l = lock == null ? "" : lock;
		if (e != null && !l.equals(e.lock)) {
			e.lock = l;
			markDirty();
		}
	}

	/**
	 * Does another door than the one at {@code controller} use this lock (the locks shared in 1.32.0, a copied door)?
	 * A door whose chunk is loaded is looked at (an entry that no longer matches it is corrected); the others are
	 * trusted as they were last seen.
	 */
	public boolean lockUsedElsewhere(World world, BlockPos controller, String lock) {
		if (lock == null || lock.isEmpty()) {
			return false;
		}
		String self = key(dim(world), controller);
		boolean used = false;
		for (Map.Entry<String, Entry> me : new ArrayList<>(contents.doors.entrySet())) {
			Entry e = me.getValue();
			if (me.getKey().equals(self) || !lock.equals(e.lock)) {
				continue;
			}
			World w = world.getServer() == null ? null : world.getServer().getWorld(net.minecraft.registry.RegistryKey.of(
					net.minecraft.registry.RegistryKeys.WORLD, net.minecraft.util.Identifier.of(e.dimension)));
			if (w != null && DoorStructure.loaded(w, e.pos())) {
				if (!(w.getBlockEntity(e.pos()) instanceof DoorBlockEntity d)) {
					contents.doors.remove(me.getKey()); // a door removed without the game knowing
					markDirty();
					continue;
				}
				if (!lock.equals(d.lock())) {
					e.lock = d.lock();
					markDirty();
					continue;
				}
			}
			used = true;
		}
		return used;
	}

	/** How many other doors use this lock (the information of {@code /porte serrure info}). */
	public int doorsWithLock(World world, BlockPos controller, String lock) {
		if (lock == null || lock.isEmpty()) {
			return 0;
		}
		String self = key(dim(world), controller);
		int n = 0;
		for (Map.Entry<String, Entry> me : contents.doors.entrySet()) {
			n += !me.getKey().equals(self) && lock.equals(me.getValue().lock) ? 1 : 0;
		}
		return n;
	}

	public void remove(World world, BlockPos controller) {
		if (contents.doors.remove(key(dim(world), controller)) != null) {
			markDirty();
		}
	}

	/** The door of a name (any case), or null. */
	@Nullable
	public Entry byName(String name) {
		if (name == null || name.isEmpty()) {
			return null;
		}
		String k = name.toLowerCase(Locale.ROOT);
		for (Entry e : contents.doors.values()) {
			if (e.name != null && e.name.toLowerCase(Locale.ROOT).equals(k)) {
				return e;
			}
		}
		return null;
	}

	/** Every known door, the named ones first. */
	public List<Entry> all() {
		List<Entry> out = new ArrayList<>(contents.doors.values());
		out.sort((a, b) -> {
			boolean na = a.name != null && !a.name.isEmpty(), nb = b.name != null && !b.name.isEmpty();
			if (na != nb) {
				return na ? -1 : 1;
			}
			return na ? a.name.compareToIgnoreCase(b.name) : 0;
		});
		return out;
	}

	/** Every name in use (command suggestions). */
	public List<String> names() {
		List<String> out = new ArrayList<>();
		for (Entry e : contents.doors.values()) {
			if (e.name != null && !e.name.isEmpty()) {
				out.add(e.name);
			}
		}
		return out;
	}
}
