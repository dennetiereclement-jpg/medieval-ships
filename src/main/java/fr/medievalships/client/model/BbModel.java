package fr.medievalships.client.model;

import java.io.Reader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
 */
public final class BbModel {
	/** Face order and conventions (Minecraft block-model UV rules). */
	private static final String[] FACE_NAMES = {"north", "south", "west", "east", "up", "down"};
	private static final int[][] FACE_AXES = {
			// normal, u dir, v dir (as axis index * sign: 1=x, 2=y, 3=z)
			{-3, -1, -2}, {3, 1, -2}, {-1, 3, -2}, {1, -3, -2}, {2, 1, 3}, {-2, 1, -3}};

	public final int textureWidth;
	public final int textureHeight;
	public final List<Bone> bones = new ArrayList<>();
	public final Map<String, Bone> bonesByName = new HashMap<>();
	public final Map<String, Animation> animations = new HashMap<>();
	private final List<Bone> roots = new ArrayList<>();
	/** Per texture UV size (Blockbench 4.9+ {@code uv_width}/{@code uv_height}), else the resolution. */
	private final List<int[]> textureSizes = new ArrayList<>();
	private int quadCount;

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
		/** Index in the model's texture list. */
		final int texture;

		Quad(boolean glow, int texture) {
			this.glow = glow;
			this.texture = texture;
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
	}

	public int quadCount() {
		return quadCount;
	}

	public Pose newPose() {
		return new Pose(bones.size());
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
		for (int f = 0; f < 6; f++) {
			JsonObject face = faces.has(FACE_NAMES[f]) ? faces.getAsJsonObject(FACE_NAMES[f]) : null;
			if (face == null || !face.has("texture") || face.get("texture").isJsonNull()) {
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
			Quad q = new Quad(glow, tex);
			q.lit = lit;
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

	/** Same, limited to the faces using texture {@code texture} (-1 = all). */
	public void render(Pose pose, int texture, QuadSink sink) {
		float[] identity = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
		float[] p = new float[12], uv = new float[8], n = new float[3];
		for (Bone root : roots) {
			renderBone(root, identity, pose, texture, sink, p, uv, n);
		}
	}

	/** Number of textures declared by the model (at least 1). */
	public int textureCount() {
		return Math.max(1, textureSizes.size());
	}

	private void renderBone(Bone bone, float[] parent, Pose pose, int texture, QuadSink sink, float[] p, float[] uv, float[] n) {
		int b = bone.index;
		if (pose.hidden[b]) {
			return;
		}
		float[] r = {bone.rotation[0] + pose.rot[b][0], bone.rotation[1] + pose.rot[b][1], bone.rotation[2] + pose.rot[b][2]};
		float[][] R = rotationMatrix(r);
		float[] s = pose.scale[b], o = bone.origin, t = pose.pos[b];
		// local = R * S * (v - o) + o + t   (3x4 affine, row major)
		float[] local = new float[12];
		for (int i = 0; i < 3; i++) {
			float off = o[i] + t[i];
			for (int j = 0; j < 3; j++) {
				local[i * 4 + j] = R[i][j] * s[j];
				off -= R[i][j] * s[j] * o[j];
			}
			local[i * 4 + 3] = off;
		}
		float[] m = compose(parent, local);
		for (Quad q : bone.quads) {
			if (bone.fx != pose.fxPass) {
				break;
			}
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
			sink.quad(p, uv, n, q.glow, q.lit);
		}
		for (Bone c : bone.children) {
			renderBone(c, m, pose, texture, sink, p, uv, n);
		}
	}

	// ------------------------------------------------------------------ math

	/** Blockbench / three.js Euler order ZYX: R = Rz * Ry * Rx (degrees). */
	static float[][] rotationMatrix(float[] deg) {
		double a = Math.toRadians(deg[0]), b = Math.toRadians(deg[1]), c = Math.toRadians(deg[2]);
		double ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b), cc = Math.cos(c), sc = Math.sin(c);
		return new float[][] {
				{(float) (cc * cb), (float) (cc * sb * sa - sc * ca), (float) (cc * sb * ca + sc * sa)},
				{(float) (sc * cb), (float) (sc * sb * sa + cc * ca), (float) (sc * sb * ca - cc * sa)},
				{(float) (-sb), (float) (cb * sa), (float) (cb * ca)}};
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
		float[] r = new float[12];
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
