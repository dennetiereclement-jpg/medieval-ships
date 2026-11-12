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
 * restart), the saved destinations, and the last known position of the ships some players logged out aboard (1.30.0:
 * found again, their chunk loaded, when those players come back; the spot each player stood on is in his own data,
 * see {@code DeckAnchors}). {@code playerShips} is the per-account record of the versions before 1.30.0, only read once.
 */
public final class ShipData extends PersistentState {
	private static final Gson GSON = new GsonBuilder().create();

	/** Serialised form (plain JSON inside the NBT file: easy to inspect and to migrate). */
	static final class Contents {
		Map<String, Route> routes = new TreeMap<>();
		Map<String, FerryRecord> ferries = new HashMap<>();
		Map<String, String> playerShips = new HashMap<>();
		/** Ships with players who logged out aboard (1.30.0), by ship UUID. */
		Map<String, CrewShipRecord> crewAway = new HashMap<>();
		/** Saved destinations ({@code /ship destination add}), by name. */
		Map<String, Destination> destinations = new TreeMap<>();
		/**
		 * Ships' boats written off by their ship while out of reach of the server (lost, unloaded): the ship has its deco
		 * boat back aboard, so such a boat vanishes when it is loaded again (never two boats). 1.30.0.
		 */
		java.util.LinkedHashSet<String> retiredBoats = new java.util.LinkedHashSet<>();
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

	/** Last known position of a ship some players logged out aboard (1.30.0). */
	public static final class CrewShipRecord {
		public String dimension;
		public double x;
		public double y;
		public double z;

		public CrewShipRecord() {
		}

		public CrewShipRecord(String dimension, double x, double y, double z) {
			this.dimension = dimension;
			this.x = x;
			this.y = y;
			this.z = z;
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
						if (c.crewAway == null) {
							c.crewAway = new HashMap<>();
						}
						if (c.destinations == null) {
							c.destinations = new TreeMap<>();
						}
						if (c.retiredBoats == null) {
							c.retiredBoats = new java.util.LinkedHashSet<>();
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

	/**
	 * The ship a player was aboard when he logged out, recorded per account before 1.30.0 (now kept in each player's own
	 * data): read once and forgotten.
	 */
	public UUID takeLegacyPlayerShip(UUID player) {
		String s = contents.playerShips.remove(player.toString());
		if (s == null) {
			return null;
		}
		markDirty();
		try {
			return UUID.fromString(s);
		} catch (IllegalArgumentException e) {
			return null;
		}
	}

	/** Players logged out aboard this ship: it records where it goes from now on. */
	public void markCrewAway(UUID ship, String dimension, double x, double y, double z) {
		contents.crewAway.put(ship.toString(), new CrewShipRecord(dimension, x, y, z));
		markDirty();
	}

	public CrewShipRecord crewAway(UUID ship) {
		return contents.crewAway.get(ship.toString());
	}

	/** Called by a ship every few seconds: its new position, if players logged out aboard it. */
	public void updateCrewAway(UUID ship, String dimension, double x, double y, double z) {
		CrewShipRecord r = contents.crewAway.get(ship.toString());
		if (r != null && (!dimension.equals(r.dimension) || Math.abs(r.x - x) > 1 || Math.abs(r.y - y) > 1 || Math.abs(r.z - z) > 1)) {
			r.dimension = dimension;
			r.x = x;
			r.y = y;
			r.z = z;
			markDirty();
		}
	}

	public boolean hasCrewAway(UUID ship) {
		return contents.crewAway.containsKey(ship.toString());
	}

	public void removeCrewAway(UUID ship) {
		if (contents.crewAway.remove(ship.toString()) != null) {
			markDirty();
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

	/** At most this many written-off boats are remembered (the oldest are forgotten: a boat lost for good never comes back). */
	static final int MAX_RETIRED_BOATS = 512;

	/** A ship wrote its boat off (see {@link Contents#retiredBoats}). */
	public void retireBoat(UUID boat) {
		if (contents.retiredBoats.add(boat.toString())) {
			while (contents.retiredBoats.size() > MAX_RETIRED_BOATS) {
				java.util.Iterator<String> it = contents.retiredBoats.iterator();
				it.next();
				it.remove();
			}
			markDirty();
		}
	}

	public boolean isRetiredBoat(UUID boat) {
		return !contents.retiredBoats.isEmpty() && contents.retiredBoats.contains(boat.toString());
	}

	/** The written-off boat was loaded again and removed: nothing more to remember. */
	public void forgetRetiredBoat(UUID boat) {
		if (contents.retiredBoats.remove(boat.toString())) {
			markDirty();
		}
	}
}
