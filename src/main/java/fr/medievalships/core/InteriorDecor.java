package fr.medievalships.core;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Furniture of a vessel with rooms (the Nautilus), written by {@code tools/nautilus_decor.py}:
 * blocks of decoration mods drawn in the rooms (the blocks are never placed in the world: the
 * vessel draws their models where they stand, moving with it), and the seats.
 *
 * <p>A block whose mod is not installed is replaced by its stand-in, a bone of the vessel's model
 * named {@link Block#fallback()}.
 */
public final class InteriorDecor {
	/**
	 * A decoration block: its id ({@code mod:block}), the centre of its bottom face (ship-local),
	 * its rotation about the vertical (degrees, 0 = the block's north facing the stern), its scale;
	 * glow: drawn full-bright while the vessel's lamps are lit (a lantern).
	 */
	public record Block(String block, double x, double y, double z, float yaw, float scale, String fallback, boolean glow) {
	}

	/** A seat: where the passenger sits (ship-local) and where he stands up. */
	public record SeatSpot(double x, double y, double z, double dismountX, double dismountY, double dismountZ) {
	}

	/**
	 * A control the players use with a click (a lever, a valve): its action, e.g. {@code shutters},
	 * {@code floodlight}, {@code lights}, {@code airlock_fill}, {@code airlock_pump}, {@code lifeboat},
	 * and the box it is clicked in (centre and half sizes, ship-local).
	 */
	public record Switch(String action, double x, double y, double z, double hx, double hy, double hz) {
	}

	/**
	 * A vanilla painting hung in a frame of the vessel's model: its motive (the texture
	 * {@code minecraft:textures/painting/<motive>.png}), the centre of its canvas (ship-local), the
	 * horizontal normal of the wall it hangs on (towards the room) and its size in blocks.
	 */
	public record Painting(String motive, double x, double y, double z, double nx, double nz, double w, double h) {
	}

	private final List<Block> blocks;
	private final List<SeatSpot> seats;
	private final List<Switch> switches;
	private final List<Painting> paintings;

	InteriorDecor(List<Block> blocks, List<SeatSpot> seats, List<Switch> switches, List<Painting> paintings) {
		this.blocks = List.copyOf(blocks);
		this.seats = List.copyOf(seats);
		this.switches = List.copyOf(switches);
		this.paintings = List.copyOf(paintings);
	}

	public List<Painting> paintings() {
		return paintings;
	}

	public List<Switch> switches() {
		return switches;
	}

	public List<Block> blocks() {
		return blocks;
	}

	public List<SeatSpot> seats() {
		return seats;
	}

	/** Reads a decor file from the class path (the mod jar). */
	public static InteriorDecor load(String resource) {
		try (InputStream in = InteriorDecor.class.getResourceAsStream(resource)) {
			if (in == null) {
				throw new IllegalStateException("missing interior decor " + resource);
			}
			try (Reader reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return parse(JsonParser.parseReader(reader).getAsJsonObject());
			}
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
	}

	static InteriorDecor parse(JsonObject root) {
		List<Block> blocks = new ArrayList<>();
		JsonArray b = root.has("blocks") ? root.getAsJsonArray("blocks") : new JsonArray();
		for (JsonElement e : b) {
			JsonObject o = e.getAsJsonObject();
			blocks.add(new Block(o.get("block").getAsString(), o.get("x").getAsDouble(), o.get("y").getAsDouble(), o.get("z").getAsDouble(),
					o.has("yaw") ? o.get("yaw").getAsFloat() : 0f, o.has("scale") ? o.get("scale").getAsFloat() : 1f,
					o.has("fallback") ? o.get("fallback").getAsString() : "", o.has("glow") && o.get("glow").getAsBoolean()));
		}
		List<SeatSpot> seats = new ArrayList<>();
		JsonArray s = root.has("seats") ? root.getAsJsonArray("seats") : new JsonArray();
		for (JsonElement e : s) {
			JsonObject o = e.getAsJsonObject();
			seats.add(new SeatSpot(o.get("x").getAsDouble(), o.get("y").getAsDouble(), o.get("z").getAsDouble(),
					o.get("dx").getAsDouble(), o.get("dy").getAsDouble(), o.get("dz").getAsDouble()));
		}
		List<Switch> switches = new ArrayList<>();
		JsonArray w = root.has("switches") ? root.getAsJsonArray("switches") : new JsonArray();
		for (JsonElement e : w) {
			JsonObject o = e.getAsJsonObject();
			switches.add(new Switch(o.get("action").getAsString(), o.get("x").getAsDouble(), o.get("y").getAsDouble(), o.get("z").getAsDouble(),
					o.get("hx").getAsDouble(), o.get("hy").getAsDouble(), o.get("hz").getAsDouble()));
		}
		List<Painting> paintings = new ArrayList<>();
		JsonArray p = root.has("paintings") ? root.getAsJsonArray("paintings") : new JsonArray();
		for (JsonElement e : p) {
			JsonObject o = e.getAsJsonObject();
			paintings.add(new Painting(o.get("motive").getAsString(), o.get("x").getAsDouble(), o.get("y").getAsDouble(), o.get("z").getAsDouble(),
					o.get("nx").getAsDouble(), o.get("nz").getAsDouble(), o.get("w").getAsDouble(), o.get("h").getAsDouble()));
		}
		return new InteriorDecor(blocks, seats, switches, paintings);
	}
}
