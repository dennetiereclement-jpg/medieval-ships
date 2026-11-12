package fr.medievalships.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Side ladders (échelles de coupée, 1.30.0): on both sides of every vessel that floats with its deck above the water, a
 * ladder hangs from the bulwark down to {@link #BELOW_WATER} blocks under the sea, so that someone who fell overboard can
 * climb back aboard. Shared by the server and the client: the spots ({@link #of}), the climbing zone ({@link #climbing},
 * fed by the {@code LivingEntity#isClimbing} mixin on both sides, so the client's prediction and the server agree), the
 * collision boxes the climber is pressed against ({@link #collectBoxes}) and the baked mesh ({@link #mesh}).
 *
 * <h2>Frame and profile</h2>
 * Ship-local blocks (see {@link Gangplank}): +x port, +y up, +z bow. A ladder lies on side {@link Ladder#side} (+1 port,
 * -1 starboard) centred at {@link Ladder#z}; {@code X = side * x} is the outboard distance. Its inner face follows the hull
 * side, {@link Ladder#hullX}(y): a piecewise-linear profile from the bulwark top down, never moving inboard as it goes down
 * (a hanging ladder rests on the bulwark and on the wales and hangs straight down where the hull curves away under it), so
 * a climber pressed against it never meets an overhang. The profiles were measured on the models and the collision
 * hulls (the hull side, the wales, the rail caps) and are checked against both by {@code SideLadderTest}. In plan the
 * ladder follows the hull's line with {@link Ladder#slope} (dX/dz). The bottom is computed at run time from the type's
 * waterline ({@link #bottom}), so a changed {@code WATERLINE_Y} moves it with the water.
 */
public final class SideLadder {
	public static final int PORT = 1;
	public static final int STARBOARD = -1;
	/** Thickness of the ladder off the hull (rails), blocks: a climber's body rests against its outer face. */
	public static final double DEPTH = 0.16;
	/** The ladder goes down this far under the water surface. */
	public static final double BELOW_WATER = 1.6;
	/** Width of a rail along the hull. */
	public static final double RAIL = 0.09;
	/** Spacing of the rungs. */
	public static final double RUNG_STEP = 0.3;
	/** Under the water the collision slab also fills this much of the gap between the ladder and a hull curving away. */
	public static final double FILL_BELOW_WATER = 0.45;
	/** Floats per quad of {@link #mesh}: the layout of {@code BbModel.QUAD_FLOATS} (4 x (x, y, z, u, v), then the normal). */
	public static final int QUAD_FLOATS = 23;
	/** Climbing zone (see {@link #climbing}): along the hull beyond the ladder's edges, under its bottom, above its top. */
	public static final double GRIP_W = 0.15, REACH_BELOW = 1.2, ABOVE_TOP = 0.3;
	/** Climbing zone across: from this far inboard of the ladder's outer face to this far outboard of it (body centre). */
	public static final double INBOARD = 0.6, REACH_OUT = 0.8;

	/**
	 * One ladder.
	 *
	 * @param side      +1 port, -1 starboard
	 * @param z         centre along the keel
	 * @param halfWidth half its width along the hull
	 * @param slope     dX/dz of the hull line in plan at the ladder (the ladder turns with it)
	 * @param top       the top of the bulwark (collision) it hangs from: the climber steps over it onto the deck
	 * @param style     material, a {@link Gangplank#STYLES} cell of the gangplank atlas (wood, dark_wood, worn, elven,
	 *                  copper, steel...)
	 * @param profile   y0, X0, y1, X1... (y going down from {@code top}, X never decreasing): the outboard distance of the
	 *                  hull side under the ladder's inner face; linear between the points, constant beyond the last
	 */
	public record Ladder(int side, double z, double halfWidth, double slope, double top, String style, double[] profile) {
		/** Outboard distance of the ladder's inner face at height y. */
		public double hullX(double y) {
			double[] p = profile;
			if (y >= p[0]) {
				return p[1];
			}
			for (int i = 2; i < p.length; i += 2) {
				if (y >= p[i]) {
					double t = (p[i - 2] - y) / (p[i - 2] - p[i]);
					return p[i - 1] + (p[i + 1] - p[i - 1]) * t;
				}
			}
			return p[p.length - 1];
		}

		/** Outboard distance of the ladder's outer face (what a climber rests against) at height y. */
		public double faceX(double y) {
			return hullX(y) + DEPTH;
		}

		/** Ship-local x of a point at outboard distance X, {@code dz} along the keel from the centre (plan slope). */
		public double localX(double X, double dz) {
			return side * (X + slope * dz);
		}
	}

	private SideLadder() {
	}

	/** Bottom of the ladders of a hull: {@link #BELOW_WATER} under its waterline. */
	public static double bottom(double waterlineY) {
		return waterlineY - BELOW_WATER;
	}

	/** The side ladders of a ship type (empty: none, e.g. the rowboat and the aircraft). */
	public static List<Ladder> of(String shipId) {
		return TABLE.getOrDefault(shipId, List.of());
	}

	/** The ship types that have side ladders. */
	public static java.util.Set<String> ships() {
		return TABLE.keySet();
	}

	/**
	 * Is a body whose feet are at the ship-local point (lx, ly, lz) on one of these ladders: within its width (plus
	 * {@link #GRIP_W}), between {@link #REACH_BELOW} under its bottom and {@link #ABOVE_TOP} over its top, and across from
	 * {@link #INBOARD} inboard of its outer face (stepping over the bulwark at the top) to {@link #REACH_OUT} outboard of it
	 * (a swimmer reaching out). {@code tolW} and {@code tolU} widen it along the hull and across (the server's allowance
	 * for a moving ship, see {@code ShipLadders}). Allocates nothing.
	 */
	public static boolean climbing(List<Ladder> ladders, double waterlineY, double lx, double ly, double lz, double tolW, double tolU) {
		double bottom = bottom(waterlineY);
		for (int i = 0, n = ladders.size(); i < n; i++) {
			Ladder l = ladders.get(i);
			double dz = lz - l.z;
			if (Math.abs(dz) > l.halfWidth + GRIP_W + tolW || ly < bottom - REACH_BELOW || ly > l.top + ABOVE_TOP) {
				continue;
			}
			double y = Math.max(bottom, Math.min(l.top, ly));
			double u = l.side * lx - (l.faceX(y) + l.slope * dz);
			if (u >= -INBOARD - tolU && u <= REACH_OUT + tolU) {
				return true;
			}
		}
		return false;
	}

	/** Farthest a ladder (with its climbing zone) reaches from the ship's origin in plan. */
	public static double reach(List<Ladder> ladders, double waterlineY) {
		double r = 0;
		double bottom = bottom(waterlineY);
		for (Ladder l : ladders) {
			double x = l.faceX(bottom) + Math.abs(l.slope) * l.halfWidth + REACH_OUT;
			double z = Math.abs(l.z) + l.halfWidth + GRIP_W;
			r = Math.max(r, Math.hypot(x, z));
		}
		return r;
	}

	/** Height of the slices of a sloped part of the profile in {@link #collectBoxes}. */
	private static final double SLICE = 0.25;

	/**
	 * Emits the world boxes of the ladders that intersect the world query box: for each ladder, a slab from its inner face
	 * to its outer face (under the water, filling up to {@link #FILL_BELOW_WATER} of the gap to the hull too), cut in
	 * slices where the profile slopes, each slice as deep as the profile's widest point in it (so the stack never
	 * overhangs the climber); covered with world-aligned boxes like the hull ({@link ShipGeometry#emitLocal}).
	 */
	public static void collectBoxes(List<Ladder> ladders, double waterlineY, ShipPose pose, double qMinX, double qMinY, double qMinZ,
			double qMaxX, double qMaxY, double qMaxZ, ShipGeometry.BoxSink sink) {
		if (ladders.isEmpty()) {
			return;
		}
		double bottom = bottom(waterlineY);
		double c = pose.cos(), s = pose.sin();
		double cx = (qMinX + qMaxX) / 2 - pose.x(), cz = (qMinZ + qMaxZ) / 2 - pose.z();
		double rx = (qMaxX - qMinX) / 2, rz = (qMaxZ - qMinZ) / 2;
		double lcx = cx * c + cz * s, lcz = -cx * s + cz * c;
		double lr = rx * Math.abs(c) + rz * Math.abs(s) + 0.6;
		double lrz = rx * Math.abs(s) + rz * Math.abs(c) + 0.6;
		double lyMin = qMinY - pose.y(), lyMax = qMaxY - pose.y();
		for (int i = 0, n = ladders.size(); i < n; i++) {
			Ladder l = ladders.get(i);
			double zMin = l.z - l.halfWidth, zMax = l.z + l.halfWidth;
			if (lcz + lrz < zMin || lcz - lrz > zMax || lyMax < bottom || lyMin > l.top) {
				continue;
			}
			double xOut = l.faceX(bottom) + Math.abs(l.slope) * l.halfWidth;
			double xIn = l.hullX(l.top) - FILL_BELOW_WATER - Math.abs(l.slope) * l.halfWidth;
			double X = l.side * lcx;
			if (X + lr < xIn || X - lr > xOut) {
				continue;
			}
			int parts = Math.abs(l.slope) * l.halfWidth > 0.04 ? 2 : 1;
			double y0 = Math.max(bottom, lyMin - SLICE), y1 = Math.min(l.top, lyMax + SLICE);
			// walk down the profile from the top; constant runs are one slice
			double y = y1;
			while (y > y0 + 1e-6) {
				double next = nextBreak(l, y, y0);
				double hx = l.hullX(next); // widest in [next, y] (the profile never narrows going down)
				double inner = hx - (next < waterlineY ? FILL_BELOW_WATER : 0);
				for (int k = 0; k < parts; k++) {
					double w0 = -l.halfWidth + 2 * l.halfWidth * k / parts, w1 = -l.halfWidth + 2 * l.halfWidth * (k + 1) / parts;
					double lo = Math.min(l.slope * w0, l.slope * w1), hi = Math.max(l.slope * w0, l.slope * w1);
					double a = l.side * (inner + lo), b = l.side * (hx + DEPTH + hi);
					ShipGeometry.emitLocal(pose, Math.min(a, b), next, l.z + w0, Math.max(a, b), y, l.z + w1, sink);
				}
				y = next;
			}
		}
	}

	/** The next height under y where the slab is cut: the next profile point, or one slice down on a sloped part. */
	private static double nextBreak(Ladder l, double y, double floor) {
		double[] p = l.profile;
		for (int i = 0; i < p.length; i += 2) {
			if (p[i] < y - 1e-6) {
				// y lies above point i: the part from point i-1 (or the top) to point i
				boolean flat = i == 0 || p[i + 1] == p[i - 1];
				double stop = flat ? p[i] : Math.max(p[i], y - SLICE);
				return Math.max(floor, stop);
			}
		}
		return floor;
	}

	// ------------------------------------------------------------------ mesh

	/**
	 * The ladders' quads in ship-local blocks ({@link #QUAD_FLOATS} floats each, UVs in the gangplank atlas
	 * {@code textures/entity/gangplank.png}, see {@link Gangplank#region}): two rails following the profile from the bottom
	 * to the bulwark top, the rungs every {@link #RUNG_STEP}, two metal hooks over the bulwark. Built once per ship type and
	 * drawn as a static mesh. Faces against the hull are left out.
	 */
	public static float[] mesh(List<Ladder> ladders, double waterlineY) {
		MeshBuilder m = new MeshBuilder();
		double bottom = bottom(waterlineY);
		for (Ladder l : ladders) {
			int[] rail = Gangplank.region(l.style, "rail");
			int[] rung = Gangplank.region(l.style, "board");
			int[] metal = Gangplank.region(l.style, "metal");
			// the rails: the profile's points from the top down to the bottom, cut in pieces of at most a block
			List<double[]> path = new ArrayList<>();
			double topRail = l.top + 0.06;
			path.add(new double[] {topRail, l.hullX(l.top)});
			for (int i = 0; i < l.profile.length; i += 2) {
				if (l.profile[i] < topRail - 1e-6 && l.profile[i] > bottom + 1e-6) {
					path.add(new double[] {l.profile[i], l.profile[i + 1]});
				}
			}
			path.add(new double[] {bottom, l.hullX(bottom)});
			for (int side = -1; side <= 1; side += 2) {
				double w0 = side < 0 ? -l.halfWidth : l.halfWidth - RAIL, w1 = w0 + RAIL;
				for (int i = 0; i + 1 < path.size(); i++) {
					double[] a = path.get(i), b = path.get(i + 1);
					int pieces = Math.max(1, (int) Math.ceil((a[0] - b[0]) / 1.0 - 1e-6));
					for (int k = 0; k < pieces; k++) {
						double ya = a[0] + (b[0] - a[0]) * k / pieces, yb = a[0] + (b[0] - a[0]) * (k + 1) / pieces;
						double xa = a[1] + (b[1] - a[1]) * k / pieces, xb = a[1] + (b[1] - a[1]) * (k + 1) / pieces;
						m.prism(l, yb, xb, ya, xa, 0, DEPTH, w0, w1, rail, k == 0 && i == 0, k == pieces - 1 && i + 2 == path.size());
					}
				}
			}
			// the rungs, set into the rails
			double rw = l.halfWidth - RAIL;
			for (double y = bottom + RUNG_STEP / 2; y < l.top - 0.12; y += RUNG_STEP) {
				double x = l.hullX(y);
				m.prism(l, y - 0.035, x, y + 0.035, x, DEPTH * 0.3, DEPTH * 0.85, -rw, rw, rung, true, true);
			}
			// the hooks over the bulwark top
			double xt = l.hullX(l.top);
			for (int side = -1; side <= 1; side += 2) {
				double wc = side * (l.halfWidth - RAIL / 2);
				m.box(l, l.top, l.top + 0.07, xt - 0.32, xt + DEPTH, wc - 0.035, wc + 0.035, metal);
				m.box(l, l.top - 0.22, l.top, xt - 0.32, xt - 0.26, wc - 0.035, wc + 0.035, metal);
			}
		}
		return m.toArray();
	}

	/** Collects quads in the {@link #QUAD_FLOATS} layout. */
	private static final class MeshBuilder {
		private float[] data = new float[QUAD_FLOATS * 256];
		private int n;

		float[] toArray() {
			return java.util.Arrays.copyOf(data, n * QUAD_FLOATS);
		}

		/** A local point of a ladder: outboard X (plus u across), height y, w along the hull from its centre. */
		private static double[] point(Ladder l, double X, double y, double w) {
			return new double[] {l.localX(X, w), y, l.z + w};
		}

		/**
		 * A prism along the profile: its section is u in [u0, u1] (outboard of the profile line) by w in [w0, w1]; its ends
		 * at heights yb (profile X xb) and ya (profile X xa), ya above yb. Caps only where asked; never the inner face.
		 */
		void prism(Ladder l, double yb, double xb, double ya, double xa, double u0, double u1, double w0, double w1, int[] region,
				boolean capTop, boolean capBottom) {
			// corners: b = bottom end, a = top end; i = inner (u0), o = outer (u1); 0 = w0, 1 = w1
			double[] bi0 = point(l, xb + u0, yb, w0), bi1 = point(l, xb + u0, yb, w1), bo0 = point(l, xb + u1, yb, w0), bo1 = point(l, xb + u1, yb, w1);
			double[] ai0 = point(l, xa + u0, ya, w0), ai1 = point(l, xa + u0, ya, w1), ao0 = point(l, xa + u1, ya, w0), ao1 = point(l, xa + u1, ya, w1);
			double[] mid = point(l, (xa + xb) / 2 + (u0 + u1) / 2, (ya + yb) / 2, (w0 + w1) / 2);
			quad(bo0, bo1, ao1, ao0, region, mid); // outer face
			quad(bi0, bo0, ao0, ai0, region, mid); // w0 side
			quad(bo1, bi1, ai1, ao1, region, mid); // w1 side
			if (capTop) {
				quad(ai0, ao0, ao1, ai1, region, mid);
			}
			if (capBottom) {
				quad(bi1, bo1, bo0, bi0, region, mid);
			}
		}

		/** A plain box in the ladder's frame (heights y0..y1, X x0..x1, w w0..w1), all six faces. */
		void box(Ladder l, double y0, double y1, double x0, double x1, double w0, double w1, int[] region) {
			prism(l, y0, x0, y1, x0, 0, x1 - x0, w0, w1, region, true, true);
			double[] a = point(l, x0, y0, w0), b = point(l, x0, y0, w1), c = point(l, x0, y1, w1), d = point(l, x0, y1, w0);
			quad(a, b, c, d, region, point(l, (x0 + x1) / 2, (y0 + y1) / 2, (w0 + w1) / 2)); // the inner face too (the hook's end shows)
		}

		/** A quad; the normal is computed from its corners and turned to face away from {@code inside} (the prism's centre). */
		void quad(double[] a, double[] b, double[] c, double[] d, int[] region, double[] inside) {
			if (n * QUAD_FLOATS + QUAD_FLOATS > data.length) {
				data = java.util.Arrays.copyOf(data, data.length * 2);
			}
			double ux = c[0] - a[0], uy = c[1] - a[1], uz = c[2] - a[2];
			double vx = d[0] - b[0], vy = d[1] - b[1], vz = d[2] - b[2];
			double nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
			double len = Math.sqrt(nx * nx + ny * ny + nz * nz);
			if (len < 1e-12) {
				return;
			}
			double fx = (a[0] + c[0]) / 2 - inside[0], fy = (a[1] + c[1]) / 2 - inside[1], fz = (a[2] + c[2]) / 2 - inside[2];
			double f = nx * fx + ny * fy + nz * fz < 0 ? -1 : 1;
			nx = nx / len * f;
			ny = ny / len * f;
			nz = nz / len * f;
			float u0 = region[0] / (float) Gangplank.ATLAS, v0 = region[1] / (float) Gangplank.ATLAS;
			float u1 = (region[0] + region[2]) / (float) Gangplank.ATLAS, v1 = (region[1] + region[3]) / (float) Gangplank.ATLAS;
			float[][] uv = {{u0, v1}, {u1, v1}, {u1, v0}, {u0, v0}};
			double[][] p = {a, b, c, d};
			int o = n * QUAD_FLOATS;
			for (int k = 0; k < 4; k++) {
				data[o + k * 5] = (float) p[k][0];
				data[o + k * 5 + 1] = (float) p[k][1];
				data[o + k * 5 + 2] = (float) p[k][2];
				data[o + k * 5 + 3] = uv[k][0];
				data[o + k * 5 + 4] = uv[k][1];
			}
			data[o + 20] = (float) nx;
			data[o + 21] = (float) ny;
			data[o + 22] = (float) nz;
			n++;
		}
	}

	// ------------------------------------------------------------------ the spots

	private static Ladder port(double z, double halfWidth, double slope, double top, String style, double... profile) {
		return new Ladder(PORT, z, halfWidth, slope, top, style, profile);
	}

	private static Ladder starboard(double z, double halfWidth, double slope, double top, String style, double... profile) {
		return new Ladder(STARBOARD, z, halfWidth, slope, top, style, profile);
	}

	/**
	 * The spots, chosen on each model clear of the gunports, oars, paddle boxes, chains and deadeyes, decorations, the
	 * gangplank and its stowed pack, and the boats carried on deck (see docs/ECHELLES.md); the profiles are generated by
	 * {@code SideLadderTest#main} from the models and the collision hulls.
	 */
	private static final Map<String, List<Ladder>> TABLE = Map.ofEntries(
			// @generated-start
			Map.entry("galley", List.of(
					port(0.0, 0.4, 0.0, 1.688, "wood", 1.688, 2.844, -2.687, 2.844),
					starboard(0.0, 0.4, 0.0, 1.688, "wood", 1.688, 2.844, -2.687, 2.844))),
			Map.entry("galleon", List.of(
					port(-4.5, 0.4, 0.019, 2.35, "dark_wood", 2.35, 4.555, 1.35, 4.581, 1.1, 4.645, -3.087, 4.645),
					starboard(-2.0, 0.35, 0.004, 2.288, "dark_wood", 2.288, 4.579, 1.038, 4.658, -3.087, 4.658),
					port(9.5, 0.4, -0.18, 2.475, "dark_wood", 2.475, 3.805, 1.225, 3.824, 0.975, 4.073, -3.087, 4.073),
					starboard(9.5, 0.4, -0.18, 2.475, "dark_wood", 2.475, 3.865, 1.225, 3.865, 0.975, 4.073, -3.087, 4.073))),
			Map.entry("warship", List.of(
					port(1.8, 0.38, -0.01, 5.9, "dark_wood", 5.9, 6.574, 5.65, 6.631, 5.4, 6.654, 3.15, 6.654, 2.65, 6.77, 1.4, 6.77, 1.15, 6.848, -2.787, 6.848),
					starboard(1.8, 0.38, -0.01, 5.9, "dark_wood", 5.9, 6.574, 5.65, 6.631, 5.4, 6.654, 3.15, 6.654, 2.65, 6.77, 1.4, 6.77, 1.15, 6.848, -2.787, 6.848),
					port(21.0, 0.4, -0.267, 7.9, "dark_wood", 7.9, 4.485, 7.15, 4.485, 6.9, 4.711, -2.787, 4.711),
					starboard(21.0, 0.4, -0.267, 7.9, "dark_wood", 7.9, 4.485, 7.15, 4.485, 6.9, 4.711, -2.787, 4.711))),
			Map.entry("medieval_galley", List.of(
					port(-3.0, 0.4, 0.059, 1.863, "wood", 1.863, 2.645, -2.887, 2.645),
					starboard(-3.0, 0.4, 0.059, 1.863, "wood", 1.863, 2.624, -2.887, 2.624))),
			Map.entry("steam_paddleboat", List.of(
					port(6.5, 0.4, -0.329, 3.525, "steel", 3.525, 3.127, 0.525, 3.154, -3.037, 3.154),
					starboard(6.5, 0.4, -0.329, 3.525, "steel", 3.525, 3.127, 0.525, 3.154, -3.037, 3.154))),
			Map.entry("elven_sailboat", List.of(
					port(1.0, 0.4, -0.048, 1.963, "elven", 1.963, 3.06, -3.037, 3.06),
					starboard(1.0, 0.4, -0.048, 1.963, "elven", 1.963, 3.06, -3.037, 3.06))),
			Map.entry("nautilus", List.of(
					port(-12.9, 0.4, 0.03, 9.0, "copper", 9.0, 2.684, 7.75, 3.333, 7.0, 3.497, 6.75, 3.518, 6.5, 3.718, 6.25, 4.034, 6.0, 4.513, 5.75, 4.603, 5.5, 5.013, 5.25, 5.072, 5.0, 5.513, 4.75, 5.513, 4.5, 5.628, 4.25, 5.79, 4.0, 6.021, 3.75, 6.064, 3.25, 6.302, 3.0, 6.513, 2.5, 6.579, 2.25, 6.644, 2.0, 6.71, 1.5, 7.013, -0.75, 7.013, -1.0, 7.104, -2.875, 7.104),
					starboard(-12.9, 0.4, 0.03, 9.0, "copper", 9.0, 2.684, 7.75, 3.333, 7.0, 3.497, 6.75, 3.518, 6.25, 4.034, 6.0, 4.513, 5.75, 4.603, 5.5, 5.013, 5.25, 5.072, 5.0, 5.513, 4.5, 5.628, 4.25, 5.79, 4.0, 6.013, 3.75, 6.064, 3.25, 6.302, 3.0, 6.513, 2.75, 6.513, 2.5, 6.68, 2.25, 6.687, 2.0, 6.71, 1.75, 6.775, 1.5, 7.013, -1.0, 7.104, -2.875, 7.104),
					port(11.9, 0.4, 0.09, 9.0, "copper", 9.0, 2.661, 7.75, 3.336, 7.0, 3.506, 6.75, 3.526, 6.5, 3.622, 6.25, 3.962, 6.0, 4.537, 5.75, 4.582, 5.5, 5.037, 5.25, 5.037, 4.25, 5.756, 4.0, 6.037, 3.75, 6.038, 3.25, 6.31, 3.0, 6.537, 2.5, 6.552, 2.25, 6.625, 2.0, 6.704, 1.75, 6.84, 1.5, 7.037, -1.0, 7.089, -2.875, 7.089),
					starboard(11.9, 0.4, 0.1, 9.0, "copper", 9.0, 2.662, 7.75, 3.34, 7.0, 3.51, 6.75, 3.53, 6.25, 3.966, 6.0, 4.541, 5.75, 4.583, 5.5, 5.041, 5.25, 5.041, 4.5, 5.615, 4.25, 5.755, 4.0, 6.041, 3.75, 6.041, 3.25, 6.31, 3.0, 6.541, 2.75, 6.541, 2.5, 6.653, 2.25, 6.663, 2.0, 6.704, 1.75, 6.783, 1.5, 7.041, -1.0, 7.093, -2.875, 7.093))),
			Map.entry("old_corsair", List.of(
					port(-5.0, 0.4, 0.0, 6.0, "worn", 6.0, 4.615, 5.5, 4.615, 5.0, 4.72, 4.5, 4.863, 4.25, 4.863, 4.0, 5.001, -2.187, 5.001),
					starboard(-5.0, 0.4, 0.0, 6.0, "worn", 6.0, 4.615, 5.5, 4.615, 5.0, 4.72, 4.5, 4.863, 4.25, 4.863, 4.0, 5.001, -2.187, 5.001),
					port(9.0, 0.4, -0.06, 6.0, "worn", 6.0, 4.525, 5.25, 4.531, 4.75, 4.706, 3.75, 4.736, 3.25, 4.785, 2.75, 4.785, 2.5, 5.001, 2.0, 5.025, -2.187, 5.025),
					starboard(9.0, 0.4, -0.06, 6.0, "worn", 6.0, 4.525, 5.25, 4.531, 4.75, 4.706, 3.75, 4.736, 3.25, 4.785, 2.75, 4.785, 2.5, 5.001, 2.0, 5.025, -2.187, 5.025))),
			Map.entry("blue_frigate", List.of(
					port(-2.5, 0.4, 0.02, 6.975, "dark_wood", 6.975, 4.952, 4.975, 5.009, 1.475, 5.009, 1.225, 5.123, -2.088, 5.123),
					starboard(-2.5, 0.4, 0.02, 6.975, "dark_wood", 6.975, 4.952, 4.975, 5.009, 1.475, 5.009, 1.225, 5.123, -2.088, 5.123),
					port(9.5, 0.4, -0.1, 6.975, "dark_wood", 6.975, 4.541, 4.975, 4.595, 1.725, 4.613, 1.475, 4.726, 1.225, 4.727, -2.088, 4.727),
					starboard(9.5, 0.4, -0.1, 6.975, "dark_wood", 6.975, 4.541, 4.975, 4.595, 1.725, 4.613, 1.475, 4.726, 1.225, 4.727, -2.088, 4.727))),
			Map.entry("trade_sloop", List.of(
					port(0.0, 0.4, -0.005, 2.188, "wood", 2.188, 2.482, 0.688, 2.503, -3.187, 2.503),
					starboard(0.0, 0.4, -0.005, 2.188, "wood", 2.188, 2.482, 0.688, 2.503, -3.187, 2.503))),
			Map.entry("royal_lion_ship", List.of(
					port(-1.3, 0.35, 0.0, 6.475, "dark_wood", 6.475, 6.113, 3.475, 6.113, 3.225, 6.556, 2.975, 6.616, -2.088, 6.616),
					starboard(-1.3, 0.35, 0.0, 6.475, "dark_wood", 6.475, 6.113, 3.475, 6.113, 3.225, 6.556, 2.975, 6.616, -2.088, 6.616),
					port(10.75, 0.35, -0.16, 6.475, "dark_wood", 6.475, 5.424, 6.225, 5.433, 4.475, 5.461, 3.975, 5.461, 3.475, 6.048, -2.088, 6.048),
					starboard(10.75, 0.35, -0.16, 6.475, "dark_wood", 6.475, 5.424, 6.225, 5.433, 4.475, 5.461, 3.975, 5.461, 3.475, 6.048, -2.088, 6.048))),
			Map.entry("fortress_ship", List.of(
					port(-7.2, 0.4, 0.02, 5.975, "steel", 5.975, 6.463, 5.725, 6.575, 1.975, 6.575, 1.725, 6.648, -2.088, 6.648),
					starboard(-7.2, 0.4, 0.02, 5.975, "steel", 5.975, 6.463, 5.725, 6.575, 1.975, 6.575, 1.725, 6.677, -2.088, 6.677),
					port(7.6, 0.4, -0.14, 8.475, "steel", 8.475, 6.139, 7.975, 6.368, 7.475, 6.421, -2.088, 6.421),
					starboard(7.6, 0.4, -0.12, 8.475, "steel", 8.475, 6.143, 7.975, 6.372, 7.475, 6.413, -2.088, 6.413))),
			Map.entry("gear_steamship", List.of(
					port(6.0, 0.4, 0.02, 5.975, "steel", 5.975, 5.009, 4.975, 5.009, 4.725, 5.166, 4.225, 5.193, 2.475, 5.253, -2.088, 5.253),
					starboard(6.0, 0.4, 0.02, 5.975, "steel", 5.975, 5.009, 4.975, 5.009, 4.725, 5.166, 4.225, 5.193, 2.475, 5.253, -2.088, 5.253),
					port(13.0, 0.4, -0.24, 7.475, "steel", 7.475, 4.097, -2.088, 4.097),
					starboard(13.0, 0.4, -0.24, 7.475, "steel", 7.475, 4.097, -2.088, 4.097)))
			// @generated-end
	);
}
