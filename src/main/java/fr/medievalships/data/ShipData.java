package fr.medievalships.data;

import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mojang.serialization.Codec;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.PersistentState;
import net.minecraft.world.PersistentStateType;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Destination;
import fr.medievalships.core.Route;

/**
 * World-level data, stored in the overworld's {@code data/medievalships.dat}:
 * routes, the last known position of autopilot ships (so their chunks are loaded again after a
 * restart), the ship each player was aboard when disconnecting and the saved destinations.
 */
public final class ShipData extends PersistentState {
	private static final Gson GSON = new GsonBuilder().create();

	/** Serialised form (plain JSON inside the NBT file: easy to inspect and to migrate). */
	static final class Contents {
		Map<String, Route> routes = new TreeMap<>();
		Map<String, FerryRecord> ferries = new HashMap<>();
		Map<String, String> playerShips = new HashMap<>();
		/** Saved destinations ({@code /ship destination add}), by name. */
		Map<String, Destination> destinations = new TreeMap<>();
	}

	public static final class FerryRecord {
		public String dimension;
		public double x;
		public double z;
		public String route;

		public FerryRecord() {
		}

		public FerryRecord(String dimension, double x, double z, String route) {
			this.dimension = dimension;
			this.x = x;
			this.z = z;
			this.route = route;
		}
	}

	private static final Codec<ShipData> CODEC = Codec.STRING.fieldOf("json").codec().xmap(
			json -> {
				ShipData d = new ShipData();
				try {
					Contents c = GSON.fromJson(json, Contents.class);
					if (c != null) {
						d.contents = c;
						if (c.routes == null) {
							c.routes = new TreeMap<>();
						}
						if (c.ferries == null) {
							c.ferries = new HashMap<>();
						}
						if (c.playerShips == null) {
							c.playerShips = new HashMap<>();
						}
						if (c.destinations == null) {
							c.destinations = new TreeMap<>();
						}
					}
				} catch (Exception e) {
					MedievalShips.LOGGER.error("Could not read ship data", e);
				}
				return d;
			},
			d -> GSON.toJson(d.contents));

	public static final PersistentStateType<ShipData> TYPE =
			new PersistentStateType<>(MedievalShips.MOD_ID, ShipData::new, CODEC, null);

	private Contents contents = new Contents();

	public ShipData() {
	}

	public static ShipData get(MinecraftServer server) {
		return server.getOverworld().getPersistentStateManager().getOrCreate(TYPE);
	}

	public Map<String, Route> routes() {
		return contents.routes;
	}

	public Route route(String name) {
		return name == null ? null : contents.routes.get(name);
	}

	public void putRoute(Route route) {
		contents.routes.put(route.name, route);
		markDirty();
	}

	public boolean removeRoute(String name) {
		boolean removed = contents.routes.remove(name) != null;
		markDirty();
		return removed;
	}

	public Map<String, FerryRecord> ferries() {
		return contents.ferries;
	}

	public void updateFerry(UUID ship, FerryRecord record) {
		contents.ferries.put(ship.toString(), record);
		markDirty();
	}

	public void removeFerry(UUID ship) {
		if (contents.ferries.remove(ship.toString()) != null) {
			markDirty();
		}
	}

	public void setPlayerShip(UUID player, UUID ship) {
		if (ship == null) {
			if (contents.playerShips.remove(player.toString()) != null) {
				markDirty();
			}
		} else {
			contents.playerShips.put(player.toString(), ship.toString());
			markDirty();
		}
	}

	public UUID playerShip(UUID player) {
		String s = contents.playerShips.get(player.toString());
		try {
			return s == null ? null : UUID.fromString(s);
		} catch (IllegalArgumentException e) {
			return null;
		}
	}

	public Map<String, Destination> destinations() {
		return contents.destinations;
	}

	public Destination destination(String name) {
		return name == null ? null : contents.destinations.get(name);
	}

	public void putDestination(Destination destination) {
		contents.destinations.put(destination.name, destination);
		markDirty();
	}

	public boolean removeDestination(String name) {
		boolean removed = contents.destinations.remove(name) != null;
		markDirty();
		return removed;
	}
}
