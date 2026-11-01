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
 * A tent: ONE block, drawn as a big static model (like the ships) from its anchor block, its furniture from the
 * decoration mods embedded visually, its posts and platforms solid through the entity collision mixin.
 *
 * <p>Everything geometric is read from {@code assets/medievalships/tents/<id>.json}, written by the tent's Python
 * generator ({@code tools/tents/generate_<id>.py}): the model path, the decor file, the extent box (the room the
 * tent takes: the free-area check before placing, the render distance) and the collision boxes. Coordinates are
 * tent-local blocks: y up, +z the tent's front (towards the player who placed it), the anchor block's centre at
 * (0, 0, 0) on the ground. Facing the block towards a direction turns the model by a quarter turn
 * ({@link #rotate}); nothing else moves, nothing ticks.
 *
 * <p>To add a tent: write its generator (the model, the decor JSON and the tents JSON come out of
 * {@code tentlib.export}), then add one {@link #load} line to {@link TentTypes#ALL}, the two names in the lang
 * files, and run the generator (it also paints the item icon).
 */
public final class TentType {
	/** A box in tent-local blocks: x0, y0, z0, x1, y1, z1. */
	public record Box(double x0, double y0, double z0, double x1, double y1, double z1) {
		public double width() {
			return x1 - x0;
		}

		public double height() {
			return y1 - y0;
		}

		public double depth() {
			return z1 - z0;
		}
	}

	/** Quarter turns of the horizontal facings, as Minecraft counts them: south 0, west 1, north 2, east 3. */
	public static final int SOUTH = 0, WEST = 1, NORTH = 2, EAST = 3;

	private final String id;
	private final String frenchName;
	private final String englishName;
	private final String model;
	private final String decor;
	private final Box extent;
	private final List<Box> colliders;
	/** The collision boxes already turned to each facing (index = quarter turns), computed once. */
	private final List<List<Box>> rotatedColliders = new ArrayList<>();
	private final Box[] rotatedExtent = new Box[4];

	TentType(String id, String frenchName, String englishName, String model, String decor, Box extent, List<Box> colliders) {
		this.id = id;
		this.frenchName = frenchName;
		this.englishName = englishName;
		this.model = model;
		this.decor = decor;
		this.extent = extent;
		this.colliders = List.copyOf(colliders);
		for (int q = 0; q < 4; q++) {
			List<Box> list = new ArrayList<>();
			for (Box b : colliders) {
				list.add(rotate(b, q));
			}
			rotatedColliders.add(List.copyOf(list));
			rotatedExtent[q] = rotate(extent, q);
		}
	}

	public String id() {
		return id;
	}

	public String frenchName() {
		return frenchName;
	}

	public String englishName() {
		return englishName;
	}

	/** The model, relative to {@code assets/medievalships/} ({@code models/entity/<id>.bbmodel}). */
	public String model() {
		return model;
	}

	/** The furniture file as a class-path resource ({@code /assets/medievalships/interiors/<id>_decor.json}), or null. */
	public String decor() {
		return decor;
	}

	/** The room the tent takes, tent-local (facing south). */
	public Box extent() {
		return extent;
	}

	/** Tent-local collision boxes (facing south). */
	public List<Box> colliders() {
		return colliders;
	}

	/** The extent turned to a facing (quarter turns, see {@link #SOUTH}...). */
	public Box extent(int quarter) {
		return rotatedExtent[quarter & 3];
	}

	/** The collision boxes turned to a facing. */
	public List<Box> colliders(int quarter) {
		return rotatedColliders.get(quarter & 3);
	}

	/**
	 * Turns a tent-local point by quarter turns about the vertical: the same rotation as the renderer's
	 * (yaw of the facing: south 0, west 90, north 180, east 270; local +z goes to the facing).
	 */
	public static double[] rotate(double x, double z, int quarter) {
		for (int k = 0; k < (quarter & 3); k++) {
			double nx = -z;
			z = x;
			x = nx;
		}
		return new double[] {x, z};
	}

	/** A box turned by quarter turns (its corners turned, then sorted). */
	public static Box rotate(Box b, int quarter) {
		double[] a = rotate(b.x0, b.z0, quarter);
		double[] c = rotate(b.x1, b.z1, quarter);
		return new Box(Math.min(a[0], c[0]), b.y0, Math.min(a[1], c[1]), Math.max(a[0], c[0]), b.y1, Math.max(a[1], c[1]));
	}

	/** Reads {@code /assets/medievalships/tents/<id>.json} from the class path (the mod jar). */
	public static TentType load(String id, String frenchName, String englishName) {
		String resource = "/assets/medievalships/tents/" + id + ".json";
		try (InputStream in = TentType.class.getResourceAsStream(resource)) {
			if (in == null) {
				throw new IllegalStateException("missing tent geometry " + resource);
			}
			try (Reader reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return parse(id, frenchName, englishName, JsonParser.parseReader(reader).getAsJsonObject());
			}
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
	}

	static TentType parse(String id, String frenchName, String englishName, JsonObject root) {
		String model = root.has("model") && !root.get("model").isJsonNull() ? root.get("model").getAsString() : "models/entity/" + id + ".bbmodel";
		String decor = root.has("decor") && !root.get("decor").isJsonNull() ? root.get("decor").getAsString() : null;
		Box extent = box(root.getAsJsonArray("extent"));
		List<Box> colliders = new ArrayList<>();
		if (root.has("colliders")) {
			for (JsonElement e : root.getAsJsonArray("colliders")) {
				colliders.add(box(e.getAsJsonArray()));
			}
		}
		return new TentType(id, frenchName, englishName, model, decor, extent, colliders);
	}

	private static Box box(JsonArray a) {
		return new Box(a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble(), a.get(3).getAsDouble(), a.get(4).getAsDouble(),
				a.get(5).getAsDouble());
	}

	@Override
	public String toString() {
		return id;
	}
}
