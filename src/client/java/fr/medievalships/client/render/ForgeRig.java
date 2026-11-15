package fr.medievalships.client.render;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import fr.medievalships.client.model.BbModel;

/**
 * What moves in a divine forge model (1.34.0), found once per loaded model from its bone names (the contract of
 * {@code tools/forge/}): the gears ({@code gear_a_*} clockwise seen from the front, {@code gear_b_*} the other way, each
 * about its own z axis through its pivot, with the gears it hangs from), the flipbooks (every {@code <name>_f<n>}:
 * {@code fire_f0..3}, {@code flow_l_f0..3}, {@code flow_r_f0..3}, one image shown at a time), the bones seen only while
 * crafting ({@code craft_*}) or only at rest ({@code idle_*}), and the empty bones whose pivot is a point of the client's
 * effects ({@code fx_spark_*}, {@code fx_steam_*}, {@code fx_ember_*}, {@code fx_holy_*}). A model without any of them
 * is simply drawn still.
 */
public final class ForgeRig {
	private static final Pattern FRAME = Pattern.compile("^(.+)_f(\\d{1,2})$");
	private static final Map<BbModel, ForgeRig> CACHE = Collections.synchronizedMap(new WeakHashMap<>());

	/** A gear: its bone, its pivot and axis (model-local blocks), its way of turning, the gears above and under it. */
	public static final class Gear {
		public final BbModel.Bone bone;
		public final float px, py, pz, ax, ay, az;
		/** {@code gear_a_*}: clockwise seen from the front. */
		public final boolean clockwise;
		int[] ancestors = new int[0];
		int[] descendants = new int[0];

		Gear(BbModel.Bone bone, boolean clockwise) {
			this.bone = bone;
			this.clockwise = clockwise;
			double[] o = bone.originBlocks();
			px = (float) o[0];
			py = (float) o[1];
			pz = (float) o[2];
			double[] a = bone.axisBlocks(0, 0, 1);
			ax = (float) a[0];
			ay = (float) a[1];
			az = (float) a[2];
		}
	}

	/** A flipbook: its name ({@code fire}, {@code flow_l}...) and, per image, the bones of that image. */
	public static final class Flipbook {
		public final String name;
		public final List<List<BbModel.Bone>> frames = new ArrayList<>();

		Flipbook(String name) {
			this.name = name;
		}

		public int size() {
			return frames.size();
		}
	}

	public final List<Gear> gears = new ArrayList<>();
	public final List<Flipbook> flipbooks = new ArrayList<>();
	public final List<BbModel.Bone> craft = new ArrayList<>();
	public final List<BbModel.Bone> idle = new ArrayList<>();
	public final List<double[]> sparks = new ArrayList<>(), steams = new ArrayList<>(), embers = new ArrayList<>(), holies = new ArrayList<>();

	private ForgeRig() {
	}

	/** The rig of a model (computed at its first use, forgotten with the model when the resources reload). */
	public static ForgeRig of(BbModel model) {
		return CACHE.computeIfAbsent(model, ForgeRig::build);
	}

	private static ForgeRig build(BbModel m) {
		ForgeRig r = new ForgeRig();
		Map<String, Flipbook> books = new HashMap<>();
		Map<BbModel.Bone, Integer> gearIndex = new HashMap<>();
		for (BbModel.Bone b : m.bones) {
			String n = b.name;
			if (n.startsWith("gear_a") || n.startsWith("gear_b")) {
				gearIndex.put(b, r.gears.size());
				r.gears.add(new Gear(b, n.startsWith("gear_a")));
				continue;
			}
			if (n.startsWith("craft_")) {
				r.craft.add(b);
				continue;
			}
			if (n.startsWith("idle_")) {
				r.idle.add(b);
				continue;
			}
			if (n.startsWith("fx_spark")) {
				r.sparks.add(b.originBlocks());
				continue;
			}
			if (n.startsWith("fx_steam")) {
				r.steams.add(b.originBlocks());
				continue;
			}
			if (n.startsWith("fx_ember")) {
				r.embers.add(b.originBlocks());
				continue;
			}
			if (n.startsWith("fx_holy")) {
				r.holies.add(b.originBlocks());
				continue;
			}
			Matcher f = FRAME.matcher(n);
			if (f.matches()) {
				Flipbook book = books.computeIfAbsent(f.group(1), Flipbook::new);
				int i = Integer.parseInt(f.group(2));
				while (book.frames.size() <= i) {
					book.frames.add(new ArrayList<>());
				}
				book.frames.get(i).add(b);
			}
		}
		for (Flipbook b : books.values()) {
			if (b.size() > 1) {
				r.flipbooks.add(b);
			}
		}
		// gears hanging from gears (a pinion on a wheel): the outer one's turn carries the inner one
		List<List<Integer>> below = new ArrayList<>();
		for (int i = 0; i < r.gears.size(); i++) {
			below.add(new ArrayList<>());
		}
		for (int i = 0; i < r.gears.size(); i++) {
			List<Integer> up = new ArrayList<>();
			for (BbModel.Bone a = r.gears.get(i).bone.parent(); a != null; a = a.parent()) {
				Integer j = gearIndex.get(a);
				if (j != null) {
					up.add(0, j);
					below.get(j).add(i);
				}
			}
			r.gears.get(i).ancestors = up.stream().mapToInt(Integer::intValue).toArray();
		}
		for (int i = 0; i < r.gears.size(); i++) {
			r.gears.get(i).descendants = below.get(i).stream().mapToInt(Integer::intValue).toArray();
		}
		return r;
	}

	/** Does the model have anything that moves or changes? */
	public boolean animated() {
		return !gears.isEmpty() || !flipbooks.isEmpty() || !craft.isEmpty() || !idle.isEmpty();
	}

	/**
	 * Hides in a pose what this state does not show: the other images of each flipbook ({@code frame[i]} the image of
	 * {@code flipbooks.get(i)}), the {@code craft_*} bones at rest or the {@code idle_*} bones while crafting, the
	 * {@code detail} bones far away.
	 */
	public void hideState(BbModel model, BbModel.Pose pose, boolean crafting, int[] frame, boolean detailed) {
		for (int i = 0; i < flipbooks.size(); i++) {
			Flipbook b = flipbooks.get(i);
			int shown = i < frame.length ? frame[i] : 0;
			for (int k = 0; k < b.size(); k++) {
				if (k != shown) {
					for (BbModel.Bone bone : b.frames.get(k)) {
						model.hide(pose, bone);
					}
				}
			}
		}
		for (BbModel.Bone bone : crafting ? idle : craft) {
			model.hide(pose, bone);
		}
		if (!detailed) {
			model.hideAll(pose, "detail");
		}
	}
}
