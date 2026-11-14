package fr.medievalships.client.render;

import java.io.Reader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import net.minecraft.resource.Resource;
import net.minecraft.resource.ResourceManager;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.client.model.BbModel;
import fr.medievalships.core.DoorType;
import fr.medievalships.core.DoorTypes;

/**
 * The door models (1.31.0), read from {@code assets/medievalships/models/entity/<id>.bbmodel} with their own texture
 * {@code textures/entity/<id>.png} ({@link DoorType#model()}, {@link DoorType#texture()}), reloaded with the resource
 * packs (F3+T). A door whose model is missing is simply not drawn (logged once per reload). For each model, the
 * moving parts are found once: the leaves ({@code leaf_l}, {@code leaf_r}), the gears ({@code gear_a_*} clockwise
 * seen from the front, {@code gear_b_*} the other way), the bolts ({@code bolt_*}) and the piston rods
 * ({@code piston_*}), each with its pivot in model-local blocks and its moving ancestors; 1.32.0: the handles and
 * rings ({@code handle_*}, {@code ring_*}, {@code poignee_*}, {@code anneau_*}: they turn about the z axis through their
 * pivot, clockwise seen from the front, while the door unlocks) and the leaf each part hangs from (its gears and rods
 * follow that leaf).
 */
public final class DoorModels {
	/** What moves in a door model. */
	public enum Kind {
		LEAF_L, LEAF_R, GEAR_A, GEAR_B, BOLT, PISTON, HANDLE
	}

	/** A moving part: its bone, its pivot (model-local blocks), the moving parts it hangs from (outermost first). */
	public static final class Part {
		public final BbModel.Bone bone;
		public final Kind kind;
		public final double px, py, pz;
		/** Indices (in {@link Loaded#parts}) of the moving parts above it, outermost first. */
		public int[] ancestors = new int[0];
		/** Indices of the moving parts under it (hidden when it is drawn: they are drawn on their own). */
		public int[] descendants = new int[0];
		/** Bolts: +1 / -1, the way "out of the leaf" along x (away from the middle of its leaf, or of the door). */
		public int boltSign = 1;
		/** The leaf it is (or hangs from): 0 = {@code leaf_l}, 1 = {@code leaf_r}, -1 = the frame. */
		public int leaf = -1;

		Part(BbModel.Bone bone, Kind kind) {
			this.bone = bone;
			this.kind = kind;
			double[] o = bone.originBlocks();
			px = o[0];
			py = o[1];
			pz = o[2];
		}
	}

	/** A loaded door model, its texture and its moving parts. */
	public static final class Loaded {
		public final BbModel model;
		public final Identifier texture;
		public final List<Part> parts;

		Loaded(BbModel model, Identifier texture, List<Part> parts) {
			this.model = model;
			this.texture = texture;
			this.parts = parts;
		}
	}

	private static final Map<DoorType, Loaded> LOADED = new HashMap<>();
	private static final Set<DoorType> MISSING = new HashSet<>();

	private DoorModels() {
	}

	@Nullable
	public static Loaded get(DoorType type) {
		return LOADED.get(type);
	}

	/** How many door models are loaded (tests). */
	public static int loadedCount() {
		return LOADED.size();
	}

	public static void reload(ResourceManager manager) {
		LOADED.clear();
		MISSING.clear();
		for (DoorType t : DoorTypes.ALL) {
			Identifier id = MedievalShips.id(t.model());
			Optional<Resource> resource = manager.getResource(id);
			if (resource.isEmpty()) {
				MISSING.add(t);
				MedievalShips.LOGGER.warn("No model for the door {} ({}): it will not be drawn", t.id(), id);
				continue;
			}
			try (Reader reader = resource.get().getReader()) {
				BbModel m = new BbModel(reader);
				Loaded l = new Loaded(m, MedievalShips.id(t.texture()), parts(m, t));
				LOADED.put(t, l);
				MedievalShips.LOGGER.info("Loaded door model {}: {} bones, {} faces, {} moving parts", t.id(), m.bones.size(), m.quadCount(), l.parts.size());
			} catch (Exception e) {
				MISSING.add(t);
				MedievalShips.LOGGER.error("Could not load door model {}", id, e);
			}
		}
	}

	@Nullable
	static Kind kindOf(String name) {
		if (name.equals("leaf_l")) {
			return Kind.LEAF_L;
		}
		if (name.equals("leaf_r")) {
			return Kind.LEAF_R;
		}
		if (name.startsWith("gear_a")) {
			return Kind.GEAR_A;
		}
		if (name.startsWith("gear_b")) {
			return Kind.GEAR_B;
		}
		if (name.startsWith("bolt")) {
			return Kind.BOLT;
		}
		if (name.startsWith("piston")) {
			return Kind.PISTON;
		}
		if (name.startsWith("handle") || name.startsWith("ring") || name.startsWith("poignee") || name.startsWith("anneau")) {
			return Kind.HANDLE;
		}
		return null;
	}

	/** The moving parts of a model, with their ancestors, descendants and bolt directions. */
	static List<Part> parts(BbModel m, DoorType type) {
		List<Part> parts = new ArrayList<>();
		Map<BbModel.Bone, Integer> index = new HashMap<>();
		for (BbModel.Bone b : m.bones) {
			Kind k = kindOf(b.name);
			if (k == Kind.LEAF_R && type.leaves() < 2) {
				k = null; // a single-leaf door has no right leaf: the bone stays a fixed part
			}
			if (k != null) {
				index.put(b, parts.size());
				parts.add(new Part(b, k));
			}
		}
		List<List<Integer>> below = new ArrayList<>();
		for (int i = 0; i < parts.size(); i++) {
			below.add(new ArrayList<>());
		}
		for (int i = 0; i < parts.size(); i++) {
			Part p = parts.get(i);
			List<Integer> up = new ArrayList<>();
			Part leaf = null;
			for (BbModel.Bone a = p.bone.parent(); a != null; a = a.parent()) {
				Integer j = index.get(a);
				if (j != null) {
					up.add(0, j);
					below.get(j).add(i);
					if (leaf == null && (parts.get(j).kind == Kind.LEAF_L || parts.get(j).kind == Kind.LEAF_R)) {
						leaf = parts.get(j);
					}
				}
			}
			p.ancestors = up.stream().mapToInt(Integer::intValue).toArray();
			p.leaf = p.kind == Kind.LEAF_L ? 0 : p.kind == Kind.LEAF_R ? 1 : leaf == null ? -1 : leaf.kind == Kind.LEAF_L ? 0 : 1;
			if (p.kind == Kind.BOLT) {
				// the middle of its leaf, from the leaf's pivot read in the model (its span: to the middle, or across for one leaf)
				double span = leaf == null ? 0 : type.leaves() == 1 ? 2 * Math.abs(leaf.px) : Math.abs(leaf.px);
				double middle = leaf == null ? 0 : leaf.kind == Kind.LEAF_L ? leaf.px + span / 2.0 : leaf.px - span / 2.0;
				p.boltSign = p.px < middle - 1e-6 ? -1 : 1;
			}
		}
		for (int i = 0; i < parts.size(); i++) {
			parts.get(i).descendants = below.get(i).stream().mapToInt(Integer::intValue).toArray();
		}
		return parts;
	}
}
