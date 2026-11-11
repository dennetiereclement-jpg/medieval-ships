package fr.medievalships.client.model;

import java.io.Reader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Minimal Blockbench (.bbmodel, "free"/generic format) loader and animator.
 *
 * <p>Supports cubes with per-face UVs and arbitrary rotations, nested groups (bones) with
 * pivots and rotations, and bone animations (rotation / position / scale keyframes, linear,
 * Catmull-Rom and step interpolation). This lets the model and its animations be edited in
 * Blockbench and reloaded with a resource pack, without GeckoLib.
 *
 * <p>Output coordinates are ship-local blocks: x = -bbX/16, y = bbY/16, z = -bbZ/16
 * (Blockbench north = ship bow = +z). Elements whose name starts with {@code glow} are flagged
 * to be rendered full bright.
 *
 * <p>Performance (1.29.0): the bones no animation moves (nine tenths of a ship) are baked once into a flat
 * <b>static mesh</b> of ship-local quads ({@link #QUAD_FLOATS} floats each), grouped per bone into cells of
 * {@link #CELL_SIZE} blocks, each cell split per texture and per light class (plain, {@code lit}, {@code glow}). A
 * renderer that implements {@link MeshSink} gets those runs whole ({@link MeshSink#mesh}) after a visibility test of
 * each cell ({@link MeshSink#cellVisible}, the renderer's frustum), so nothing of a static bone is transformed or
 * copied quad by quad every frame; a plain {@link QuadSink} still gets every quad one by one, exactly as before. Only
 * the animated bones (sails, flags, doors, oars...) are transformed each frame, through scratch arrays of the pose
 * (no allocation per bone or per quad).
 */
public final class BbModel {
	/** Face order and conventions (Minecraft block-model UV rules). */
	private static final String[] FACE_NAMES = {"north", "south", "west", "east", "up", "down"};
	private static final int[][] FACE_AXES = {
			// normal, u dir, v dir (as axis index * sign: 1=x, 2=y, 3=z)
			{-3, -1, -2}, {3, 1, -2}, {-1, 3, -2}, {1, -3, -2}, {2, 1, 3}, {-2, 1, -3}};
	/** Floats per baked quad of the static mesh: four corners (x, y, z, u, v) then the face normal (nx, ny, nz). */
	public static final int QUAD_FLOATS = 23;
	/** Side of the cells the static quads of a bone are grouped in (blocks). */
	public static final float CELL_SIZE = 8f;
	/** Light classes of a run of baked quads: lit by the world, by the vessel's own lamps ({@code lit}), full bright ({@code glow}). */
	public static final int LIGHT_WORLD = 0, LIGHT_LAMPS = 1, LIGHT_GLOW = 2;
	private static final float[] IDENTITY = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
	/** Static quads baked so far in this JVM (benchmark counter: it stops growing once every drawn model is baked). */
	public static long bakedQuads;

	public final int textureWidth;
	public final int textureHeight;
	public final List<Bone> bones = new ArrayList<>();
	public final Map<String, Bone> bonesByName = new HashMap<>();
	public final Map<String, Animation> animations = new HashMap<>();
	private final List<Bone> roots = new ArrayList<>();
	/** Per texture UV size (Blockbench 4.9+ {@code uv_width}/{@code uv_height}), else the resolution. */
	private final List<int[]> textureSizes = new ArrayList<>();
	/** A plate thinner than this (Blockbench pixels)... */
	private static final float THIN_PLATE_PX = 2.1f;
	/** ...and wider than this on both other sides has no edge faces. */
	private static final float THIN_PLATE_MIN_SIZE_PX = 6.4f;
	private int quadCount;
	/** Highest face texture index + 1 (at least {@link #textureCount}): the texture slots of the static mesh. */
	private int textureSlots = 1;
	/** Opt-in (model field "medievalships_cull_thin_plates"): thin plates are drawn without their edge faces. */
	private boolean cullThinPlates;
	/** The baked static bones (lazily, at the first render). */
	private StaticMesh mesh;
	/** A pose reused by a renderer between frames ({@link #scratchPose}). */
	private Pose scratch;

	public static final class Bone {
		public final String name;
		public final int index;
		final float[] origin;
		final float[] rotation;
		final List<Bone> children = new ArrayList<>();
		final List<Quad> quads = new ArrayList<>();
		Bone parent;
		/** Translucent effect (a light beam, water): bones named "fx_*" and their children, drawn in their own pass. */
		boolean fx;
		/** Moved by an animation (itself or one of its parents): its quads are transformed every frame. */
		boolean animated;
		/** A bone that never moves: its transform in ship-local Blockbench pixels (3x4 affine), computed by the bake. */
		float[] staticMatrix;
		/** Its cells in the static mesh: [cellFrom, cellTo). */
		int cellFrom, cellTo;
		/** Its parents' transforms at rest, composed ({@link BbModel#renderPart}), computed once. */
		float[] restParent;

		Bone(String name, int index, float[] origin, float[] rotation) {
			this.name = name;
			this.index = index;
			this.origin = origin;
			this.rotation = rotation;
		}
	}

	/** A face in bone space (Blockbench pixels), after the element's own rotation. */
	static final class Quad {
		final float[] pos = new float[12];
		final float[] uv = new float[8];
		final float[] normal = new float[3];
		final boolean glow;
		boolean lit;
		/**
		 * Seen from both sides: its cube has no face opposite to it (a deck slab with its top only, an inner window pane),
		 * so its back may be what the model shows there. A face whose cube has the opposite face is hidden by it when
		 * seen from behind, and a renderer may skip it then (back-face culling).
		 */
		boolean twoSided;
		/** Index in the model's texture list. */
		final int texture;

		Quad(boolean glow, int texture) {
			this.glow = glow;
			this.texture = texture;
		}

		int lightClass() {
			return glow ? LIGHT_GLOW : lit ? LIGHT_LAMPS : LIGHT_WORLD;
		}

		/** The run of a cell this quad belongs to: its light class, the two-sided ones after the others. */
		int runClass() {
			return lightClass() + (twoSided ? 3 : 0);
		}
	}

	/** Runs per texture slot in a cell: three light classes, one-sided then two-sided. */
	private static final int RUNS = 6;

	/**
	 * The baked static bones: every quad of a bone no animation moves, in ship-local blocks with its normal, grouped
	 * per bone into cells of {@link #CELL_SIZE} blocks; in a cell the quads are ordered by texture slot, and by light
	 * class within a slot. {@code ranges} holds, per cell, {@code perCell} = slots x 3 + 1 quad indices into
	 * {@code data}: the start of each (slot, class) run and the end of the cell. {@code bounds}: per cell, the tight
	 * box of its quads (min x, y, z, max x, y, z).
	 */
	static final class StaticMesh {
		final float[] data;
		final float[] bounds;
		final int[] ranges;
		final int perCell;
		final int cells;

		StaticMesh(float[] data, float[] bounds, int[] ranges, int perCell, int cells) {
			this.data = data;
			this.bounds = bounds;
			this.ranges = ranges;
			this.perCell = perCell;
			this.cells = cells;
		}
	}

	public enum Loop { LOOP, ONCE, HOLD }

	public static final class Animation {
		public final String name;
		public final float length;
		public final Loop loop;
		final Map<String, Channel[]> tracks = new HashMap<>(); // bone -> {rotation, position, scale}

		Animation(String name, float length, Loop loop) {
			this.name = name;
			this.length = length;
			this.loop = loop;
		}

		public float wrapTime(float t) {
			if (length <= 0) {
				return 0;
			}
			if (loop == Loop.LOOP) {
				float r = t % length;
				return r < 0 ? r + length : r;
			}
			return Math.max(0, Math.min(length, t));
		}
	}

	static final class Channel {
		final float[] times;
		final float[][] values;
		final int[] interpolation; // 0 linear, 1 catmullrom, 2 step

		Channel(float[] times, float[][] values, int[] interpolation) {
			this.times = times;
			this.values = values;
			this.interpolation = interpolation;
		}

		void sample(float t, float[] out) {
			int n = times.length;
			if (t <= times[0] || n == 1) {
				System.arraycopy(values[0], 0, out, 0, 3);
				return;
			}
			if (t >= times[n - 1]) {
				System.arraycopy(values[n - 1], 0, out, 0, 3);
				return;
			}
			int i = 0;
			while (i < n - 2 && t > times[i + 1]) {
				i++;
			}
			float t0 = times[i], t1 = times[i + 1];
			float f = t1 > t0 ? (t - t0) / (t1 - t0) : 0;
			int mode = interpolation[i + 1] == 1 || interpolation[i] == 1 ? 1 : interpolation[i];
			for (int a = 0; a < 3; a++) {
				float v0 = values[i][a], v1 = values[i + 1][a];
				if (mode == 2) {
					out[a] = v0;
				} else if (mode == 1) {
					float vp = values[Math.max(0, i - 1)][a];
					float vn = values[Math.min(n - 1, i + 2)][a];
					float f2 = f * f, f3 = f2 * f;
					out[a] = 0.5f * ((2 * v0) + (-vp + v1) * f + (2 * vp - 5 * v0 + 4 * v1 - vn) * f2
							+ (-vp + 3 * v0 - 3 * v1 + vn) * f3);
				} else {
					out[a] = v0 + (v1 - v0) * f;
				}
			}
		}
	}

	/** Per-bone animation offsets, reused between frames. */
	public static final class Pose {
		final float[][] rot;
		final float[][] pos;
		final float[][] scale;
		/** Bones not drawn (with their children) in this pose. */
		final boolean[] hidden;
		/** Draw only the translucent effects ("fx_*" bones), or only the rest. */
		public boolean fxPass;
		private final float[] tmp = new float[3];
		/** Scratch corners, uvs and normal of {@link BbModel#renderPart} and {@link BbModel#render} (no allocation per call). */
		final float[] partPos = new float[12];
		final float[] partUv = new float[8];
		final float[] partNormal = new float[3];
		/** Scratch of the animated bones' transforms: Euler angles, rotation matrix, local and composed matrices per depth. */
		final float[] euler = new float[3];
		final float[] rotation = new float[9];
		final float[] local = new float[12];
		private float[][] stack = new float[16][];

		Pose(int bones) {
			rot = new float[bones][3];
			pos = new float[bones][3];
			scale = new float[bones][3];
			hidden = new boolean[bones];
			reset();
		}

		public void reset() {
			for (int i = 0; i < rot.length; i++) {
				rot[i][0] = rot[i][1] = rot[i][2] = 0;
				pos[i][0] = pos[i][1] = pos[i][2] = 0;
				scale[i][0] = scale[i][1] = scale[i][2] = 1;
				hidden[i] = false;
			}
			fxPass = false;
		}

		/** Number of bones this pose was made for. */
		public int bones() {
			return rot.length;
		}

		/** The composed matrix scratch of a nesting depth. */
		float[] matrix(int depth) {
			if (depth >= stack.length) {
				stack = Arrays.copyOf(stack, Math.max(depth + 1, stack.length * 2));
			}
			float[] m = stack[depth];
			if (m == null) {
				m = stack[depth] = new float[12];
			}
			return m;
		}
	}

	/** Does the model have translucent effects ("fx_*" bones)? */
	public boolean hasEffects() {
		for (Bone b : bones) {
			if (b.fx) {
				return true;
			}
		}
		return false;
	}

	/** Hides a bone (and its children) in a pose; unknown names are ignored. */
	public void hide(Pose pose, String bone) {
		Bone b = bonesByName.get(bone);
		if (b != null) {
			pose.hidden[b.index] = true;
		}
	}

	/** Is there a bone of that name? */
	public boolean hasBone(String bone) {
		return bonesByName.containsKey(bone);
	}

	/** The origin (pivot) of a bone in model-local blocks (x = -bbX/16, y = bbY/16, z = -bbZ/16), or null for an unknown name. */
	public double[] origin(String bone) {
		Bone b = bonesByName.get(bone);
		return b == null ? null : new double[] {-b.origin[0] / 16.0, b.origin[1] / 16.0, -b.origin[2] / 16.0};
	}

	/**
	 * Sets a bone's extra rotation in a pose (Blockbench degrees about its own axes, added to the bone's rotation like
	 * an animation's); unknown names are ignored. Only {@link #renderSubtree} applies it to bones no animation moves.
	 */
	public void rotate(Pose pose, String bone, float x, float y, float z) {
		Bone b = bonesByName.get(bone);
		if (b != null) {
			pose.rot[b.index][0] = x;
			pose.rot[b.index][1] = y;
			pose.rot[b.index][2] = z;
		}
	}

	/**
	 * Emits the quads of one bone and its children only (a training target's moving parts), in model-local blocks like
	 * {@link #render}: every bone of the subtree is transformed with the pose's rotations ({@link #rotate}), whether an
	 * animation moves it or not; its parents, if any, at rest. With no extra rotation the quads are exactly the ones the
	 * full render draws for that subtree. Hidden bones of the pose are skipped as in {@link #render}.
	 */
	public void renderSubtree(Pose pose, String bone, QuadSink sink) {
		Bone b = bonesByName.get(bone);
		if (b == null) {
			return;
		}
		java.util.ArrayDeque<Bone> chain = new java.util.ArrayDeque<>();
		for (Bone a = b.parent; a != null; a = a.parent) {
			if (pose.hidden[a.index]) {
				return;
			}
			chain.push(a);
		}
		float[] m = IDENTITY.clone();
		for (Bone a : chain) {
			m = compose(m, restMatrix(a));
		}
		float[] p = new float[12], uv = new float[8], n = new float[3];
		renderBone(b, m, pose, -1, sink, null, p, uv, n, true, 0);
	}

	/**
	 * Emits the quads of one bone and its children at rest, in model-local blocks, from the static mesh ({@link #render}:
	 * baked once, copied out): exactly the quads the full render draws for that subtree, with no per-call allocation (the
	 * pose's scratch arrays). The caller places the part (a folding gangplank's segments). Hidden bones of the pose are
	 * skipped, as is the whole part under a hidden parent.
	 */
	public void renderPart(Pose pose, String bone, QuadSink sink) {
		Bone b = bonesByName.get(bone);
		if (b == null) {
			return;
		}
		for (Bone a = b.parent; a != null; a = a.parent) {
			if (pose.hidden[a.index]) {
				return;
			}
		}
		if (b.restParent == null) {
			java.util.ArrayDeque<Bone> chain = new java.util.ArrayDeque<>();
			for (Bone a = b.parent; a != null; a = a.parent) {
				chain.push(a);
			}
			float[] m = IDENTITY.clone();
			for (Bone a : chain) {
				m = compose(m, restMatrix(a));
			}
			b.restParent = m;
		}
		mesh();
		renderBone(b, b.restParent, pose, -1, sink, sink instanceof MeshSink ms ? ms : null, pose.partPos, pose.partUv, pose.partNormal, false, 0);
	}

	/** A bone's own transform at rest (3x4 affine, Blockbench pixels): R * (v - o) + o. */
	private static float[] restMatrix(Bone bone) {
		float[][] R = rotationMatrix(bone.rotation);
		float[] o = bone.origin;
		float[] local = new float[12];
		for (int i = 0; i < 3; i++) {
			float off = o[i];
			for (int j = 0; j < 3; j++) {
				local[i * 4 + j] = R[i][j];
				off -= R[i][j] * o[j];
			}
			local[i * 4 + 3] = off;
		}
		return local;
	}

	@FunctionalInterface
	public interface QuadSink {
		/**
		 * @param p      4 corners (x, y, z) in ship-local blocks
		 * @param uv     4 corners (u, v) normalised to [0, 1]
		 * @param normal face normal in ship-local space
		 */
		void quad(float[] p, float[] uv, float[] normal, boolean glow);

		/**
		 * {@code lit}: elements whose name starts with {@code lit} (rooms of a vessel), lit by the
		 * vessel's own lamps rather than by the world light where the entity stands.
		 */
		default void quad(float[] p, float[] uv, float[] normal, boolean glow, boolean lit) {
			quad(p, uv, normal, glow);
		}

		/** {@code twoSided}: a face whose cube has no opposite face (see {@link Quad#twoSided}): never to be back-face culled. */
		default void quad(float[] p, float[] uv, float[] normal, boolean glow, boolean lit, boolean twoSided) {
			quad(p, uv, normal, glow, lit);
		}
	}

	/**
	 * A sink that takes the static mesh in runs: the quads of the bones no animation moves come baked
	 * ({@link #QUAD_FLOATS} floats each, ship-local blocks, the face normal once), a cell at a time, after
	 * {@link #cellVisible} let the cell through. The animated bones still come quad by quad ({@link QuadSink}).
	 */
	public interface MeshSink extends QuadSink {
		/** Is a cell of static quads (its tight box, ship-local blocks) worth drawing? */
		default boolean cellVisible(float minX, float minY, float minZ, float maxX, float maxY, float maxZ) {
			return true;
		}

		/**
		 * A run of baked quads of one light class ({@link #LIGHT_WORLD}, {@link #LIGHT_LAMPS}, {@link #LIGHT_GLOW}):
		 * quads {@code from} (inclusive) to {@code to} (exclusive) of {@code data}, {@link #QUAD_FLOATS} floats each.
		 * {@code twoSided}: faces that may be seen from behind (never to be back-face culled, see {@link Quad#twoSided}).
		 */
		void mesh(float[] data, int from, int to, int lightClass, boolean twoSided);
	}

	public BbModel(Reader reader) {
		JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
		JsonObject res = root.has("resolution") ? root.getAsJsonObject("resolution") : null;
		textureWidth = res != null ? res.get("width").getAsInt() : 16;
		textureHeight = res != null ? res.get("height").getAsInt() : 16;
		if (root.has("textures")) {
			for (JsonElement e : root.getAsJsonArray("textures")) {
				JsonObject t = e.getAsJsonObject();
				textureSizes.add(new int[] {
						t.has("uv_width") ? t.get("uv_width").getAsInt() : textureWidth,
						t.has("uv_height") ? t.get("uv_height").getAsInt() : textureHeight});
			}
		}

		cullThinPlates = root.has("medievalships_cull_thin_plates") && root.get("medievalships_cull_thin_plates").getAsBoolean();
		Map<String, JsonObject> elements = new HashMap<>();
		for (JsonElement e : root.getAsJsonArray("elements")) {
			JsonObject o = e.getAsJsonObject();
			elements.put(o.get("uuid").getAsString(), o);
		}
		Map<String, String> boneNameByUuid = new HashMap<>();
		for (JsonElement e : root.getAsJsonArray("outliner")) {
			if (e.isJsonObject()) {
				roots.add(readGroup(e.getAsJsonObject(), null, elements, boneNameByUuid));
			}
		}
		if (root.has("animations")) {
			for (JsonElement e : root.getAsJsonArray("animations")) {
				readAnimation(e.getAsJsonObject(), boneNameByUuid);
			}
		}
		for (Animation anim : animations.values()) {
			for (String name : anim.tracks.keySet()) {
				Bone b = bonesByName.get(name);
				if (b != null) {
					markAnimated(b);
				}
			}
		}
		textureSlots = Math.max(textureSlots, textureCount());
	}

	private static void markAnimated(Bone b) {
		b.animated = true;
		for (Bone c : b.children) {
			markAnimated(c);
		}
	}

	public int quadCount() {
		return quadCount;
	}

	public Pose newPose() {
		return new Pose(bones.size());
	}

	/** A pose of this model reused between frames by its renderer (one thread), reset before each use. */
	public Pose scratchPose() {
		if (scratch == null) {
			scratch = newPose();
		} else {
			scratch.reset();
		}
		return scratch;
	}

	/** Quads of the bones no animation moves (the static mesh), and the cells they are grouped in. */
	public int staticQuadCount() {
		StaticMesh m = mesh();
		return m.cells == 0 ? 0 : m.ranges[(m.cells - 1) * m.perCell + m.perCell - 1];
	}

	public int staticCellCount() {
		return mesh().cells;
	}

	/** Is the static mesh baked already (it is at the first render)? */
	public boolean isBaked() {
		return mesh != null;
	}

	private Bone readGroup(JsonObject g, Bone parent, Map<String, JsonObject> elements, Map<String, String> names) {
		Bone bone = new Bone(g.get("name").getAsString(), bones.size(), vec(g, "origin", 0), vec(g, "rotation", 0));
		bone.parent = parent;
		bone.fx = bone.name.startsWith("fx_") || (parent != null && parent.fx);
		bones.add(bone);
		bonesByName.putIfAbsent(bone.name, bone);
		if (g.has("uuid")) {
			names.put(g.get("uuid").getAsString(), bone.name);
		}
		if (g.has("visibility") && !g.get("visibility").getAsBoolean()) {
			return bone;
		}
		for (JsonElement c : g.getAsJsonArray("children")) {
			if (c.isJsonObject()) {
				bone.children.add(readGroup(c.getAsJsonObject(), bone, elements, names));
			} else {
				JsonObject el = elements.get(c.getAsString());
				if (el != null && (!el.has("visibility") || el.get("visibility").getAsBoolean())) {
					readCube(el, bone);
				}
			}
		}
		return bone;
	}

	private void readCube(JsonObject el, Bone bone) {
		if (el.has("type") && !"cube".equals(el.get("type").getAsString())) {
			return; // meshes, locators...: not supported
		}
		float[] from = vec(el, "from", 0), to = vec(el, "to", 0);
		float inflate = el.has("inflate") ? el.get("inflate").getAsFloat() : 0;
		for (int a = 0; a < 3; a++) {
			from[a] -= inflate;
			to[a] += inflate;
		}
		float[] origin = vec(el, "origin", 0);
		float[][] rot = rotationMatrix(vec(el, "rotation", 0));
		boolean glow = el.get("name").getAsString().startsWith("glow");
		boolean lit = el.get("name").getAsString().startsWith("lit");
		JsonObject faces = el.getAsJsonObject("faces");
		// a thin plate (a hull panel, a wall lining): its edge faces are never seen, they are not drawn
		float[] dims = {Math.abs(to[0] - from[0]), Math.abs(to[1] - from[1]), Math.abs(to[2] - from[2])};
		int thinAxis = -1;
		{
			int min = 0;
			for (int a = 1; a < 3; a++) {
				if (dims[a] < dims[min]) {
					min = a;
				}
			}
			float middle = Math.min(dims[(min + 1) % 3], dims[(min + 2) % 3]);
			if (cullThinPlates && dims[min] < THIN_PLATE_PX && middle > THIN_PLATE_MIN_SIZE_PX) {
				thinAxis = min;
			}
		}
		for (int f = 0; f < 6; f++) {
			JsonObject face = faces.has(FACE_NAMES[f]) ? faces.getAsJsonObject(FACE_NAMES[f]) : null;
			if (face == null || !face.has("texture") || face.get("texture").isJsonNull()) {
				continue;
			}
			if (thinAxis >= 0 && Math.abs(FACE_AXES[f][0]) - 1 != thinAxis) {
				continue;
			}
			JsonElement texEl = face.get("texture");
			int tex = texEl.isJsonPrimitive() && texEl.getAsJsonPrimitive().isNumber() ? texEl.getAsInt() : 0;
			float tw = tex < textureSizes.size() ? textureSizes.get(tex)[0] : textureWidth;
			float th = tex < textureSizes.size() ? textureSizes.get(tex)[1] : textureHeight;
			JsonArray uvArr = face.getAsJsonArray("uv");
			float u1 = uvArr.get(0).getAsFloat() / tw, v1 = uvArr.get(1).getAsFloat() / th;
			float u2 = uvArr.get(2).getAsFloat() / tw, v2 = uvArr.get(3).getAsFloat() / th;
			int faceRot = face.has("rotation") ? face.get("rotation").getAsInt() : 0;
			Quad q = new Quad(glow, Math.max(0, tex));
			q.lit = lit;
			// the opposite face of the cube (north/south, west/east, up/down are consecutive in FACE_NAMES)
			JsonObject back = faces.has(FACE_NAMES[f ^ 1]) ? faces.getAsJsonObject(FACE_NAMES[f ^ 1]) : null;
			q.twoSided = back == null || !back.has("texture") || back.get("texture").isJsonNull();
			textureSlots = Math.max(textureSlots, q.texture + 1);
			int[] ax = FACE_AXES[f];
			float[] cu = {0, 1, 1, 0}, cv = {0, 0, 1, 1};
			for (int k = 0; k < 4; k++) {
				float[] p = new float[3];
				for (int a = 0; a < 3; a++) {
					int axis = a + 1;
					if (Math.abs(ax[0]) == axis) {
						p[a] = ax[0] > 0 ? to[a] : from[a];
					} else if (Math.abs(ax[1]) == axis) {
						p[a] = ax[1] > 0 ? from[a] + (to[a] - from[a]) * cu[k] : to[a] + (from[a] - to[a]) * cu[k];
					} else {
						p[a] = ax[2] > 0 ? from[a] + (to[a] - from[a]) * cv[k] : to[a] + (from[a] - to[a]) * cv[k];
					}
				}
				float[] r = transform(rot, p, origin);
				System.arraycopy(r, 0, q.pos, k * 3, 3);
				// face UV rotation (0/90/180/270) rotates which UV corner lands on which vertex
				int kk = Math.floorMod(k + faceRot / 90, 4);
				q.uv[k * 2] = u1 + (u2 - u1) * cu[kk];
				q.uv[k * 2 + 1] = v1 + (v2 - v1) * cv[kk];
			}
			float[] n = {0, 0, 0};
			n[Math.abs(ax[0]) - 1] = Math.signum(ax[0]);
			float[] rn = mul(rot, n);
			System.arraycopy(rn, 0, q.normal, 0, 3);
			bone.quads.add(q);
			quadCount++;
		}
	}

	private void readAnimation(JsonObject a, Map<String, String> names) {
		String loopStr = a.has("loop") ? a.get("loop").getAsString() : "once";
		Loop loop = "loop".equals(loopStr) ? Loop.LOOP : "hold".equals(loopStr) ? Loop.HOLD : Loop.ONCE;
		Animation anim = new Animation(a.get("name").getAsString(), a.has("length") ? a.get("length").getAsFloat() : 0, loop);
		if (a.has("animators")) {
			for (Map.Entry<String, JsonElement> entry : a.getAsJsonObject("animators").entrySet()) {
				JsonObject an = entry.getValue().getAsJsonObject();
				String bone = names.getOrDefault(entry.getKey(), an.has("name") ? an.get("name").getAsString() : entry.getKey());
				Map<String, List<JsonObject>> byChannel = new HashMap<>();
				for (JsonElement k : an.getAsJsonArray("keyframes")) {
					JsonObject kf = k.getAsJsonObject();
					byChannel.computeIfAbsent(kf.get("channel").getAsString(), c -> new ArrayList<>()).add(kf);
				}
				Channel[] channels = new Channel[3];
				String[] order = {"rotation", "position", "scale"};
				for (int c = 0; c < 3; c++) {
					List<JsonObject> kfs = byChannel.get(order[c]);
					if (kfs != null && !kfs.isEmpty()) {
						channels[c] = channel(kfs, c == 2 ? 1 : 0);
					}
				}
				anim.tracks.put(bone, channels);
			}
		}
		animations.put(anim.name, anim);
	}

	private static Channel channel(List<JsonObject> kfs, float fallback) {
		kfs.sort((x, y) -> Float.compare(x.get("time").getAsFloat(), y.get("time").getAsFloat()));
		int n = kfs.size();
		float[] times = new float[n];
		float[][] values = new float[n][3];
		int[] interp = new int[n];
		for (int i = 0; i < n; i++) {
			JsonObject kf = kfs.get(i);
			times[i] = kf.get("time").getAsFloat();
			JsonObject dp = kf.getAsJsonArray("data_points").get(0).getAsJsonObject();
			values[i][0] = number(dp, "x", fallback);
			values[i][1] = number(dp, "y", fallback);
			values[i][2] = number(dp, "z", fallback);
			String ip = kf.has("interpolation") ? kf.get("interpolation").getAsString() : "linear";
			interp[i] = "catmullrom".equals(ip) ? 1 : "step".equals(ip) ? 2 : 0;
		}
		return new Channel(times, values, interp);
	}

	private static float number(JsonObject o, String key, float fallback) {
		if (!o.has(key)) {
			return fallback;
		}
		try {
			String s = o.get(key).getAsString().trim();
			return s.isEmpty() ? fallback : Float.parseFloat(s);
		} catch (NumberFormatException e) {
			return fallback; // Molang expressions are not supported
		}
	}

	/**
	 * Adds an animation to the pose.
	 *
	 * @param time   animation time in seconds (wrapped / clamped according to its loop mode)
	 * @param weight 0..1, blends the animation towards the rest pose
	 */
	public void apply(Pose pose, String animation, float time, float weight) {
		Animation anim = animations.get(animation);
		if (anim == null || weight <= 0) {
			return;
		}
		float t = anim.wrapTime(time);
		float[] v = pose.tmp;
		for (Map.Entry<String, Channel[]> e : anim.tracks.entrySet()) {
			Bone bone = bonesByName.get(e.getKey());
			if (bone == null) {
				continue;
			}
			Channel[] ch = e.getValue();
			int b = bone.index;
			if (ch[0] != null) {
				ch[0].sample(t, v);
				// added to the bone Euler angles, exactly like the Blockbench viewer
				pose.rot[b][0] += v[0] * weight;
				pose.rot[b][1] += v[1] * weight;
				pose.rot[b][2] += v[2] * weight;
			}
			if (ch[1] != null) {
				ch[1].sample(t, v);
				pose.pos[b][0] += v[0] * weight;
				pose.pos[b][1] += v[1] * weight;
				pose.pos[b][2] += v[2] * weight;
			}
			if (ch[2] != null) {
				ch[2].sample(t, v);
				for (int a = 0; a < 3; a++) {
					pose.scale[b][a] *= 1 + (v[a] - 1) * weight;
				}
			}
		}
	}

	/** Emits every quad of the model in ship-local block coordinates for the given pose. */
	public void render(Pose pose, QuadSink sink) {
		render(pose, -1, sink);
	}

	/**
	 * Same, limited to the faces using texture {@code texture} (-1 = all). A {@link MeshSink} gets the static bones as
	 * baked runs, a plain sink quad by quad.
	 */
	public void render(Pose pose, int texture, QuadSink sink) {
		mesh();
		MeshSink ms = sink instanceof MeshSink m ? m : null;
		float[] p = pose.partPos, uv = pose.partUv, n = pose.partNormal;
		for (Bone root : roots) {
			renderBone(root, IDENTITY, pose, texture, sink, ms, p, uv, n, false, 0);
		}
	}

	/** Number of textures declared by the model (at least 1). */
	public int textureCount() {
		return Math.max(1, textureSizes.size());
	}

	/**
	 * Emits a bone and its children. {@code dynamic}: transform this bone and its children with the pose even if no
	 * animation moves them ({@link #renderSubtree}); otherwise a static bone comes from the baked mesh.
	 */
	private void renderBone(Bone bone, float[] parent, Pose pose, int texture, QuadSink sink, MeshSink ms, float[] p, float[] uv, float[] n,
			boolean dynamic, int depth) {
		int b = bone.index;
		if (pose.hidden[b]) {
			return;
		}
		if (!bone.animated && !dynamic) {
			renderStatic(bone, pose, texture, sink, ms, p, uv, n, depth);
			return;
		}
		float[] r = pose.euler;
		r[0] = bone.rotation[0] + pose.rot[b][0];
		r[1] = bone.rotation[1] + pose.rot[b][1];
		r[2] = bone.rotation[2] + pose.rot[b][2];
		float[] R = rotationMatrix(r, pose.rotation);
		float[] s = pose.scale[b], o = bone.origin, t = pose.pos[b];
		// local = R * S * (v - o) + o + t   (3x4 affine, row major)
		float[] local = pose.local;
		for (int i = 0; i < 3; i++) {
			float off = o[i] + t[i];
			for (int j = 0; j < 3; j++) {
				float v = R[i * 3 + j] * s[j];
				local[i * 4 + j] = v;
				off -= v * o[j];
			}
			local[i * 4 + 3] = off;
		}
		float[] m = compose(parent, local, pose.matrix(depth));
		if (bone.fx == pose.fxPass) {
			for (Quad q : bone.quads) {
				if (texture >= 0 && q.texture != texture) {
					continue;
				}
				for (int k = 0; k < 4; k++) {
					float x = q.pos[k * 3], y = q.pos[k * 3 + 1], z = q.pos[k * 3 + 2];
					float wx = m[0] * x + m[1] * y + m[2] * z + m[3];
					float wy = m[4] * x + m[5] * y + m[6] * z + m[7];
					float wz = m[8] * x + m[9] * y + m[10] * z + m[11];
					p[k * 3] = -wx / 16f;
					p[k * 3 + 1] = wy / 16f;
					p[k * 3 + 2] = -wz / 16f;
				}
				System.arraycopy(q.uv, 0, uv, 0, 8);
				float nx = m[0] * q.normal[0] + m[1] * q.normal[1] + m[2] * q.normal[2];
				float ny = m[4] * q.normal[0] + m[5] * q.normal[1] + m[6] * q.normal[2];
				float nz = m[8] * q.normal[0] + m[9] * q.normal[1] + m[10] * q.normal[2];
				float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
				if (len < 1e-6f) {
					continue; // fully collapsed (e.g. furled to zero)
				}
				n[0] = -nx / len;
				n[1] = ny / len;
				n[2] = -nz / len;
				sink.quad(p, uv, n, q.glow, q.lit, q.twoSided);
			}
		}
		for (Bone c : bone.children) {
			renderBone(c, m, pose, texture, sink, ms, p, uv, n, dynamic, depth + 1);
		}
	}

	/** A bone that never moves: its cells of baked quads, whole to a mesh sink, one quad at a time to a plain sink. */
	private void renderStatic(Bone bone, Pose pose, int texture, QuadSink sink, MeshSink ms, float[] p, float[] uv, float[] n, int depth) {
		StaticMesh sm = mesh;
		if (bone.fx == pose.fxPass && bone.cellFrom < bone.cellTo && texture < textureSlots) {
			int perCell = sm.perCell;
			int[] ranges = sm.ranges;
			float[] data = sm.data;
			for (int cell = bone.cellFrom; cell < bone.cellTo; cell++) {
				int base = cell * perCell;
				int q0 = texture < 0 ? ranges[base] : ranges[base + texture * RUNS];
				int q1 = texture < 0 ? ranges[base + perCell - 1] : ranges[base + texture * RUNS + RUNS];
				if (q0 == q1) {
					continue;
				}
				if (ms != null) {
					int bb = cell * 6;
					if (!ms.cellVisible(sm.bounds[bb], sm.bounds[bb + 1], sm.bounds[bb + 2], sm.bounds[bb + 3], sm.bounds[bb + 4], sm.bounds[bb + 5])) {
						continue;
					}
				}
				int t0 = texture < 0 ? 0 : texture, t1 = texture < 0 ? textureSlots - 1 : texture;
				for (int t = t0; t <= t1; t++) {
					for (int c = 0; c < RUNS; c++) {
						int from = ranges[base + t * RUNS + c], to = ranges[base + t * RUNS + c + 1];
						if (from >= to) {
							continue;
						}
						if (ms != null) {
							ms.mesh(data, from, to, c % 3, c >= 3);
						} else {
							for (int q = from; q < to; q++) {
								int o = q * QUAD_FLOATS;
								for (int k = 0; k < 4; k++) {
									p[k * 3] = data[o + k * 5];
									p[k * 3 + 1] = data[o + k * 5 + 1];
									p[k * 3 + 2] = data[o + k * 5 + 2];
									uv[k * 2] = data[o + k * 5 + 3];
									uv[k * 2 + 1] = data[o + k * 5 + 4];
								}
								n[0] = data[o + 20];
								n[1] = data[o + 21];
								n[2] = data[o + 22];
								sink.quad(p, uv, n, c % 3 == LIGHT_GLOW, c % 3 == LIGHT_LAMPS, c >= 3);
							}
						}
					}
				}
			}
		}
		for (Bone c : bone.children) {
			renderBone(c, bone.staticMatrix, pose, texture, sink, ms, p, uv, n, false, depth + 1);
		}
	}

	// ------------------------------------------------------------------ static mesh

	/** The baked static bones, baked at the first call. */
	StaticMesh mesh() {
		if (mesh == null) {
			mesh = bake();
		}
		return mesh;
	}

	/** Grows a float buffer: {buffer, length}. */
	private static final class FloatBuf {
		float[] a = new float[QUAD_FLOATS * 256];
		int n;

		void add(float v) {
			if (n == a.length) {
				a = Arrays.copyOf(a, a.length * 2);
			}
			a[n++] = v;
		}
	}

	private StaticMesh bake() {
		int perCell = textureSlots * RUNS + 1;
		FloatBuf data = new FloatBuf();
		List<Float> boundsList = new ArrayList<>();
		List<Integer> rangesList = new ArrayList<>();
		int[] cells = {0};
		for (Bone root : roots) {
			bakeBone(root, IDENTITY, perCell, data, boundsList, rangesList, cells);
		}
		float[] bounds = new float[boundsList.size()];
		for (int i = 0; i < bounds.length; i++) {
			bounds[i] = boundsList.get(i);
		}
		int[] ranges = new int[rangesList.size()];
		for (int i = 0; i < ranges.length; i++) {
			ranges[i] = rangesList.get(i);
		}
		return new StaticMesh(Arrays.copyOf(data.a, data.n), bounds, ranges, perCell, cells[0]);
	}

	/** Bakes a static bone (its quads into cells), then its static children; an animated child's subtree is left to the frame. */
	private void bakeBone(Bone bone, float[] parent, int perCell, FloatBuf data, List<Float> bounds, List<Integer> ranges, int[] cells) {
		if (bone.animated) {
			return;
		}
		float[] m = compose(parent, restMatrix(bone));
		bone.staticMatrix = m;
		bone.cellFrom = cells[0];
		int nq = bone.quads.size();
		if (nq > 0) {
			// every quad in ship-local blocks, with its normal (exactly what the old per-frame copy produced)
			float[] pos = new float[nq * 12];
			float[] nor = new float[nq * 3];
			long[] keys = new long[nq];
			for (int qi = 0; qi < nq; qi++) {
				Quad q = bone.quads.get(qi);
				float cx = 0, cy = 0, cz = 0;
				for (int k = 0; k < 4; k++) {
					float x = q.pos[k * 3], y = q.pos[k * 3 + 1], z = q.pos[k * 3 + 2];
					float px = -(m[0] * x + m[1] * y + m[2] * z + m[3]) / 16f;
					float py = (m[4] * x + m[5] * y + m[6] * z + m[7]) / 16f;
					float pz = -(m[8] * x + m[9] * y + m[10] * z + m[11]) / 16f;
					pos[qi * 12 + k * 3] = px;
					pos[qi * 12 + k * 3 + 1] = py;
					pos[qi * 12 + k * 3 + 2] = pz;
					cx += px;
					cy += py;
					cz += pz;
				}
				float nx = m[0] * q.normal[0] + m[1] * q.normal[1] + m[2] * q.normal[2];
				float ny = m[4] * q.normal[0] + m[5] * q.normal[1] + m[6] * q.normal[2];
				float nz = m[8] * q.normal[0] + m[9] * q.normal[1] + m[10] * q.normal[2];
				float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
				len = len < 1e-6f ? 1f : len;
				nor[qi * 3] = -nx / len;
				nor[qi * 3 + 1] = ny / len;
				nor[qi * 3 + 2] = -nz / len;
				int ix = (int) Math.floor(cx / 4 / CELL_SIZE), iy = (int) Math.floor(cy / 4 / CELL_SIZE), iz = (int) Math.floor(cz / 4 / CELL_SIZE);
				keys[qi] = ((long) (ix + 0x8000) << 40) | ((long) (iy + 0x8000) << 20) | (iz + 0x8000);
			}
			// the quads of each cell, by texture slot then light class
			TreeMap<Long, List<Integer>> byCell = new TreeMap<>();
			for (int qi = 0; qi < nq; qi++) {
				byCell.computeIfAbsent(keys[qi], k -> new ArrayList<>()).add(qi);
			}
			for (List<Integer> cell : byCell.values()) {
				float minX = Float.MAX_VALUE, minY = Float.MAX_VALUE, minZ = Float.MAX_VALUE;
				float maxX = -Float.MAX_VALUE, maxY = -Float.MAX_VALUE, maxZ = -Float.MAX_VALUE;
				for (int t = 0; t < textureSlots; t++) {
					for (int c = 0; c < RUNS; c++) {
						ranges.add(data.n / QUAD_FLOATS);
						for (int qi : cell) {
							Quad q = bone.quads.get(qi);
							if (q.texture != t || q.runClass() != c) {
								continue;
							}
							for (int k = 0; k < 4; k++) {
								float px = pos[qi * 12 + k * 3], py = pos[qi * 12 + k * 3 + 1], pz = pos[qi * 12 + k * 3 + 2];
								data.add(px);
								data.add(py);
								data.add(pz);
								data.add(q.uv[k * 2]);
								data.add(q.uv[k * 2 + 1]);
								minX = Math.min(minX, px);
								minY = Math.min(minY, py);
								minZ = Math.min(minZ, pz);
								maxX = Math.max(maxX, px);
								maxY = Math.max(maxY, py);
								maxZ = Math.max(maxZ, pz);
							}
							data.add(nor[qi * 3]);
							data.add(nor[qi * 3 + 1]);
							data.add(nor[qi * 3 + 2]);
							bakedQuads++;
						}
					}
				}
				ranges.add(data.n / QUAD_FLOATS);
				bounds.add(minX);
				bounds.add(minY);
				bounds.add(minZ);
				bounds.add(maxX);
				bounds.add(maxY);
				bounds.add(maxZ);
				cells[0]++;
			}
		}
		bone.cellTo = cells[0];
		for (Bone c : bone.children) {
			bakeBone(c, m, perCell, data, bounds, ranges, cells);
		}
	}

	// ------------------------------------------------------------------ math

	/** Blockbench / three.js Euler order ZYX: R = Rz * Ry * Rx (degrees). */
	static float[][] rotationMatrix(float[] deg) {
		float[] r = rotationMatrix(deg, new float[9]);
		return new float[][] {{r[0], r[1], r[2]}, {r[3], r[4], r[5]}, {r[6], r[7], r[8]}};
	}

	/** Same, row major into {@code out} (9 floats). */
	static float[] rotationMatrix(float[] deg, float[] out) {
		double a = Math.toRadians(deg[0]), b = Math.toRadians(deg[1]), c = Math.toRadians(deg[2]);
		double ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b), cc = Math.cos(c), sc = Math.sin(c);
		out[0] = (float) (cc * cb);
		out[1] = (float) (cc * sb * sa - sc * ca);
		out[2] = (float) (cc * sb * ca + sc * sa);
		out[3] = (float) (sc * cb);
		out[4] = (float) (sc * sb * sa + cc * ca);
		out[5] = (float) (sc * sb * ca - cc * sa);
		out[6] = (float) (-sb);
		out[7] = (float) (cb * sa);
		out[8] = (float) (cb * ca);
		return out;
	}

	private static float[] mul(float[][] m, float[] v) {
		return new float[] {
				m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
				m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
				m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]};
	}

	private static float[] transform(float[][] m, float[] p, float[] o) {
		float[] d = {p[0] - o[0], p[1] - o[1], p[2] - o[2]};
		float[] r = mul(m, d);
		return new float[] {r[0] + o[0], r[1] + o[1], r[2] + o[2]};
	}

	/** a * b for 3x4 affine matrices. */
	private static float[] compose(float[] a, float[] b) {
		return compose(a, b, new float[12]);
	}

	/** a * b for 3x4 affine matrices, into {@code r} (neither operand). */
	private static float[] compose(float[] a, float[] b, float[] r) {
		for (int i = 0; i < 3; i++) {
			for (int j = 0; j < 4; j++) {
				float v = a[i * 4] * b[j] + a[i * 4 + 1] * b[4 + j] + a[i * 4 + 2] * b[8 + j];
				if (j == 3) {
					v += a[i * 4 + 3];
				}
				r[i * 4 + j] = v;
			}
		}
		return r;
	}

	private static float[] vec(JsonObject o, String key, float def) {
		if (!o.has(key)) {
			return new float[] {def, def, def};
		}
		JsonArray a = o.getAsJsonArray(key);
		return new float[] {a.get(0).getAsFloat(), a.get(1).getAsFloat(), a.get(2).getAsFloat()};
	}
}
