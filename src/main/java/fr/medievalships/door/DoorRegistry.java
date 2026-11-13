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
 * position, type and name of each door. Filled when a door is placed (and when a door's chunk loads, for the doors
 * placed otherwise), emptied when it is removed; a command finds a named door here, wherever it is.
 */
public final class DoorRegistry extends PersistentState {
	private static final Gson GSON = new GsonBuilder().create();

	/** One door: where its controller is, what it is, its name ("" for none). */
	public static final class Entry {
		public String dimension;
		public int x, y, z;
		public String type;
		public String name = "";

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

	/** Adds or updates a door. */
	public void put(World world, BlockPos controller, DoorType type, String name) {
		Entry e = new Entry();
		e.dimension = dim(world);
		e.x = controller.getX();
		e.y = controller.getY();
		e.z = controller.getZ();
		e.type = type.id();
		e.name = name == null ? "" : name;
		Entry old = contents.doors.put(key(e.dimension, controller), e);
		if (old == null || !old.name.equals(e.name) || !old.type.equals(e.type)) {
			markDirty();
		}
	}

	/** Adds a door found in the world if it is not known yet (a chunk loading), keeping its name. */
	public void ensure(World world, BlockPos controller, DoorType type, String name) {
		Entry old = contents.doors.get(key(dim(world), controller));
		if (old == null || !old.type.equals(type.id()) || !old.name.equals(name == null ? "" : name)) {
			put(world, controller, type, name);
		}
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
