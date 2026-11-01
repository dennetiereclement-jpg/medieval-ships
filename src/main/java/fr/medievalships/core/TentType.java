package fr.medievalships.core;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

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
 *
 * <p>The carts are the same kind of prop in a second family ({@link #group()} {@code "carts"}): their files are
 * {@code assets/medievalships/carts/<id>.json} (written by {@code tools/carts/generate_<id>.py}), their atlas
 * {@code textures/entity/carts.png} (the JSON's {@code "texture"}), their items in the tab "Charrettes"
 * ({@link TentTypes#CARTS}). Same block, block entity, renderer, collisions and commands as the tents.
 *
 * <p>The crafting workshops are the third family ({@link #group()} {@code "workshops"}, {@link TentTypes#WORKSHOPS}, tab
 * "Ateliers"): files {@code assets/medievalships/workshops/<id>.json}, plus an optional {@code "particles"} list
 * ({@link Particle}: a forge's smoke, an altar's glow) drawn client-side by the anchor block's random display ticks.
 *
 * <p>The artillery is the fourth family ({@link #group()} {@code "artillery"}, {@link TentTypes#ARTILLERY}, tab
 * "Artillerie"): files {@code assets/medievalships/artillery/<id>.json} (written by
 * {@code tools/merchant/generate_<id>.py}), its own atlas, a {@code CannonBlock} and a {@code CannonBlockEntity} (block
 * entity type {@code medievalships:cannon}) that keeps a {@link CannonState}, plus the optional {@code "muzzle"}
 * point and {@code "muzzle_dir"} direction ({@link Muzzle}) where a future shot's smoke and projectile will start.
 *
 * <p>The training areas are the fifth family ({@link #group()} {@code "training"}, {@link TentTypes#TRAINING}, tab
 * "Entraînement"): fenced yards of about 7 x 7 blocks (dummies, punching bag, tatamis, racks) drawn as one static model
 * like the others, files {@code assets/medievalships/training/<id>.json} (written by
 * {@code tools/training/generate_<id>.py}), each with its own atlas.
 */
public final class TentType {
	/**
	 * A particle source of a prop (JSON {@code "particles": [{"type": "flame", "pos": [x, y, z], "chance": 0.5, "count": 1}]}):
	 * a vanilla particle type among {@link #PARTICLE_TYPES}, a prop-local point (turned with the facing like the
	 * collision boxes), the probability that it emits at each random display tick of the anchor block (vanilla calls
	 * it about once every 2 s for a block near the player) and how many particles it then emits.
	 */
	public record Particle(String type, double x, double y, double z, double chance, int count) {
		/** Is the type one the block knows how to spawn? (unknown types are ignored in game) */
		public boolean known() {
			return PARTICLE_TYPES.contains(type);
		}

		/** The source turned by quarter turns (see {@link TentType#rotate(double, double, int)}). */
		public Particle rotate(int quarter) {
			double[] r = TentType.rotate(x, z, quarter);
			return new Particle(type, r[0], y, r[1], chance, count);
		}
	}

	/**
	 * The mouth of a cannon's barrel (JSON {@code "muzzle": [x, y, z], "muzzle_dir": [dx, dy, dz]}): the prop-local point
	 * at the centre of the bore's opening and the unit direction a shot leaves along (normalised on reading; facing
	 * south like everything in the JSON, turned with the facing by {@link #rotate(int)}). Read for the future firing
	 * system (smoke, flash, projectile spawn); nothing uses it in game yet.
	 */
	public record Muzzle(double x, double y, double z, double dx, double dy, double dz) {
		/** The muzzle turned by quarter turns (point and direction alike). */
		public Muzzle rotate(int quarter) {
			double[] p = TentType.rotate(x, z, quarter);
			double[] d = TentType.rotate(dx, dz, quarter);
			return new Muzzle(p[0], y, p[1], d[0], dy, d[1]);
		}
	}

	/** The particle types a prop's JSON may name (vanilla ids, {@code minecraft:} optional). */
	public static final List<String> PARTICLE_TYPES = List.of("flame", "smoke", "campfire_smoke", "enchant", "witch", "portal", "end_rod",
			"electric_spark", "small_flame", "glow");

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

	/** The three families of one-block props: their JSON folder under {@code assets/medievalships/} and their creative tab. */
	public static final String TENTS = "tents", CARTS = "carts", WORKSHOPS = "workshops";
	/** The fourth family: the artillery (the medieval cannon), tab "Artillerie". */
	public static final String ARTILLERY = "artillery";
	/** The fifth family: the training areas (1.18.0), tab "Entraînement". */
	public static final String TRAINING = "training";
	/** The atlas a prop's model is drawn with when its JSON names none (the tents'). */
	public static final String DEFAULT_TEXTURE = "textures/entity/tents.png";

	private final String group;
	private final String texture;
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
	private final List<Particle> particles;
	/** The particle sources already turned to each facing (index = quarter turns). */
	private final List<List<Particle>> rotatedParticles = new ArrayList<>();
	/** The muzzle turned to each facing (index = quarter turns), or null for a prop that is not a gun. */
	private final Muzzle[] rotatedMuzzle = new Muzzle[4];
	private final Muzzle muzzle;

	TentType(String group, String texture, String id, String frenchName, String englishName, String model, String decor, Box extent,
			List<Box> colliders, List<Particle> particles, Muzzle muzzle) {
		this.group = group;
		this.texture = texture;
		this.id = id;
		this.frenchName = frenchName;
		this.englishName = englishName;
		this.model = model;
		this.decor = decor;
		this.extent = extent;
		this.colliders = List.copyOf(colliders);
		this.particles = List.copyOf(particles);
		this.muzzle = muzzle;
		for (int q = 0; q < 4; q++) {
			rotatedMuzzle[q] = muzzle == null ? null : muzzle.rotate(q);
			List<Box> list = new ArrayList<>();
			for (Box b : colliders) {
				list.add(rotate(b, q));
			}
			rotatedColliders.add(List.copyOf(list));
			rotatedExtent[q] = rotate(extent, q);
			List<Particle> ps = new ArrayList<>();
			for (Particle p : particles) {
				ps.add(p.rotate(q));
			}
			rotatedParticles.add(List.copyOf(ps));
		}
	}

	public String id() {
		return id;
	}

	/** {@link #TENTS}, {@link #CARTS}, {@link #WORKSHOPS}, {@link #ARTILLERY} or {@link #TRAINING}: the JSON folder and the creative tab. */
	public String group() {
		return group;
	}

	public boolean isCart() {
		return CARTS.equals(group);
	}

	public boolean isWorkshop() {
		return WORKSHOPS.equals(group);
	}

	/** A piece of artillery (the medieval cannon): a CannonBlock with its own block entity type. */
	public boolean isCannon() {
		return ARTILLERY.equals(group);
	}

	/** A training area (1.18.0): "l'aire d'entraînement", feminine like a tent. */
	public boolean isTraining() {
		return TRAINING.equals(group);
	}

	/** Is the French name masculine ("posé", "le canon", "l'atelier") rather than feminine ("posée", "la tente")? */
	public boolean masculine() {
		return isWorkshop() || isCannon();
	}

	/** The muzzle of a gun (facing south), or null when the JSON has none. */
	public Muzzle muzzle() {
		return muzzle;
	}

	/** The muzzle turned to a facing, or null. */
	public Muzzle muzzle(int quarter) {
		return rotatedMuzzle[quarter & 3];
	}

	/** The atlas of the model, relative to {@code assets/medievalships/} ({@code textures/entity/tents.png} or {@code carts.png}). */
	public String texture() {
		return texture;
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

	/** Prop-local particle sources (facing south); empty for most props. */
	public List<Particle> particles() {
		return particles;
	}

	/** The particle sources turned to a facing. */
	public List<Particle> particles(int quarter) {
		return rotatedParticles.get(quarter & 3);
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
		return load(TENTS, id, frenchName, englishName);
	}

	/** Reads {@code /assets/medievalships/<group>/<id>.json} from the class path (the mod jar). */
	public static TentType load(String group, String id, String frenchName, String englishName) {
		String resource = "/assets/medievalships/" + group + "/" + id + ".json";
		try (InputStream in = TentType.class.getResourceAsStream(resource)) {
			if (in == null) {
				throw new IllegalStateException("missing tent geometry " + resource);
			}
			try (Reader reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
				return parse(group, id, frenchName, englishName, JsonParser.parseReader(reader).getAsJsonObject());
			}
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
	}

	static TentType parse(String id, String frenchName, String englishName, JsonObject root) {
		return parse(TENTS, id, frenchName, englishName, root);
	}

	static TentType parse(String group, String id, String frenchName, String englishName, JsonObject root) {
		String texture = root.has("texture") && !root.get("texture").isJsonNull() ? root.get("texture").getAsString() : DEFAULT_TEXTURE;
		String model = root.has("model") && !root.get("model").isJsonNull() ? root.get("model").getAsString() : "models/entity/" + id + ".bbmodel";
		String decor = root.has("decor") && !root.get("decor").isJsonNull() ? root.get("decor").getAsString() : null;
		Box extent = box(root.getAsJsonArray("extent"));
		List<Box> colliders = new ArrayList<>();
		if (root.has("colliders")) {
			for (JsonElement e : root.getAsJsonArray("colliders")) {
				colliders.add(box(e.getAsJsonArray()));
			}
		}
		List<Particle> particles = new ArrayList<>();
		if (root.has("particles") && root.get("particles").isJsonArray()) {
			for (JsonElement e : root.getAsJsonArray("particles")) {
				JsonObject o = e.getAsJsonObject();
				String type = o.get("type").getAsString().trim().toLowerCase(Locale.ROOT);
				if (type.startsWith("minecraft:")) {
					type = type.substring("minecraft:".length());
				}
				JsonArray pos = o.getAsJsonArray("pos");
				double chance = o.has("chance") ? Math.max(0.0, Math.min(1.0, o.get("chance").getAsDouble())) : 1.0;
				int count = o.has("count") ? Math.max(1, Math.min(16, o.get("count").getAsInt())) : 1;
				particles.add(new Particle(type, pos.get(0).getAsDouble(), pos.get(1).getAsDouble(), pos.get(2).getAsDouble(), chance, count));
			}
		}
		Muzzle muzzle = null;
		if (root.has("muzzle") && root.get("muzzle").isJsonArray()) {
			JsonArray m = root.getAsJsonArray("muzzle");
			double dx = 0, dy = 0, dz = 1;
			if (root.has("muzzle_dir") && root.get("muzzle_dir").isJsonArray()) {
				JsonArray d = root.getAsJsonArray("muzzle_dir");
				dx = d.get(0).getAsDouble();
				dy = d.get(1).getAsDouble();
				dz = d.get(2).getAsDouble();
			}
			double len = Math.sqrt(dx * dx + dy * dy + dz * dz);
			if (len < 1e-9) {
				dx = 0;
				dy = 0;
				dz = 1;
				len = 1;
			}
			muzzle = new Muzzle(m.get(0).getAsDouble(), m.get(1).getAsDouble(), m.get(2).getAsDouble(), dx / len, dy / len, dz / len);
		}
		return new TentType(group, texture, id, frenchName, englishName, model, decor, extent, colliders, particles, muzzle);
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
