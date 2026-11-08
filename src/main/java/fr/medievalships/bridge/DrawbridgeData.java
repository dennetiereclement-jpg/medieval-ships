package fr.medievalships.bridge;

import java.util.LinkedHashMap;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mojang.serialization.Codec;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.PersistentState;
import net.minecraft.world.PersistentStateType;

import fr.medievalships.MedievalShips;

/**
 * The drawbridges of the server, stored in the overworld's {@code data/medievalships_drawbridges.dat} as plain JSON
 * inside the NBT (easy to inspect, easy to migrate): for each bridge its definition, the captured blocks of its deck
 * (states and block entity data) and the state of its cycle. Written at every change that matters (definition,
 * conversion, restoration, transition, and every second while the leaves move), saved by the game with the world.
 */
public final class DrawbridgeData extends PersistentState {
	private static final Gson GSON = new GsonBuilder().create();

	static final class Contents {
		int version = 1;
		Map<String, Drawbridge.Saved> bridges = new LinkedHashMap<>();
	}

	private static final Codec<DrawbridgeData> CODEC = Codec.STRING.fieldOf("json").codec().xmap(
			json -> {
				DrawbridgeData d = new DrawbridgeData();
				try {
					Contents c = GSON.fromJson(json, Contents.class);
					if (c != null) {
						d.contents = c;
						if (c.bridges == null) {
							c.bridges = new LinkedHashMap<>();
						}
					}
				} catch (Exception e) {
					MedievalShips.LOGGER.error("Could not read the drawbridge data", e);
				}
				return d;
			},
			d -> GSON.toJson(d.contents));

	public static final PersistentStateType<DrawbridgeData> TYPE =
			new PersistentStateType<>(MedievalShips.MOD_ID + "_drawbridges", DrawbridgeData::new, CODEC, null);

	private Contents contents = new Contents();

	public DrawbridgeData() {
	}

	public static DrawbridgeData get(MinecraftServer server) {
		return server.getOverworld().getPersistentStateManager().getOrCreate(TYPE);
	}

	public Map<String, Drawbridge.Saved> bridges() {
		return contents.bridges;
	}

	public void put(Drawbridge.Saved saved) {
		contents.bridges.put(saved.id, saved);
		markDirty();
	}

	public boolean remove(String id) {
		boolean removed = contents.bridges.remove(id) != null;
		if (removed) {
			markDirty();
		}
		return removed;
	}
}
