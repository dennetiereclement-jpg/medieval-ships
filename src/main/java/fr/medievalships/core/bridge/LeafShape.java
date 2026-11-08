package fr.medievalships.core.bridge;

import java.util.ArrayList;
import java.util.List;

/**
 * The blocks of one leaf as solid boxes in its {@link LeafFrame}: built once from the captured block states (their
 * collision shapes) and asked, every tick, for the world boxes of the leaf raised by an angle, for the volume it
 * sweeps between two angles, and for what it leaves free under it. Pure Java: the game code feeds it the blocks'
 * positions and collision boxes, the tests feed it cubes.
 */
public final class LeafShape {
	/** One solid box of the leaf in leaf-local coordinates ({@link LeafFrame}: a along the hinge, b inward, c up). */
	public record LocalBox(double a0, double b0, double c0, double a1, double b1, double c1) {
	}

	/** Angle step (degrees) used when sampling a swept volume. */
	public static final double SWEEP_STEP = 5.0;

	private final LeafFrame frame;
	private final List<LocalBox> boxes;
	private final double minA, maxA, minB, maxB, minC, maxC;

	/**
	 * @param frame the leaf's hinge and swing direction
	 * @param worldBoxes solid boxes of the leaf's blocks in world coordinates ({minX, minY, minZ, maxX, maxY, maxZ}
	 *        each), with the leaf closed
	 */
	public LeafShape(LeafFrame frame, List<double[]> worldBoxes) {
		this.frame = frame;
		List<LocalBox> local = new ArrayList<>();
		double a0 = Double.MAX_VALUE, b0 = Double.MAX_VALUE, c0 = Double.MAX_VALUE;
		double a1 = -Double.MAX_VALUE, b1 = -Double.MAX_VALUE, c1 = -Double.MAX_VALUE;
		for (double[] w : worldBoxes) {
			double[] l = frame.localBox(w[0], w[1], w[2], w[3], w[4], w[5]);
			local.add(new LocalBox(l[0], l[1], l[2], l[3], l[4], l[5]));
			a0 = Math.min(a0, l[0]);
			b0 = Math.min(b0, l[1]);
			c0 = Math.min(c0, l[2]);
			a1 = Math.max(a1, l[3]);
			b1 = Math.max(b1, l[4]);
			c1 = Math.max(c1, l[5]);
		}
		if (local.isEmpty()) {
			a0 = b0 = c0 = a1 = b1 = c1 = 0;
		}
		this.boxes = List.copyOf(local);
		this.minA = a0;
		this.maxA = a1;
		this.minB = b0;
		this.maxB = b1;
		this.minC = c0;
		this.maxC = c1;
	}

	public LeafFrame frame() {
		return frame;
	}

	public List<LocalBox> boxes() {
		return boxes;
	}

	public boolean isEmpty() {
		return boxes.isEmpty();
	}

	/** Extent along the hinge (local a). */
	public double minA() {
		return minA;
	}

	public double maxA() {
		return maxA;
	}

	/** Extent inward from the hinge (local b): {@link #maxB()} is the reach of the free end. */
	public double minB() {
		return minB;
	}

	public double maxB() {
		return maxB;
	}

	/** Vertical extent relative to the hinge (local c), the leaf closed. */
	public double minC() {
		return minC;
	}

	public double maxC() {
		return maxC;
	}

	/** World boxes ({minX, minY, minZ, maxX, maxY, maxZ}) of every solid box, the leaf raised by {@code angleDeg}. */
	public List<double[]> worldBoxes(double angleDeg) {
		List<double[]> out = new ArrayList<>(boxes.size());
		for (LocalBox b : boxes) {
			out.add(frame.rotatedBox(b.a0(), b.b0(), b.c0(), b.a1(), b.b1(), b.c1(), angleDeg));
		}
		return out;
	}

	/** World boxes of the solid boxes intersecting a world query box, the leaf raised by {@code angleDeg}. */
	public void collect(double angleDeg, double qMinX, double qMinY, double qMinZ, double qMaxX, double qMaxY, double qMaxZ,
			List<double[]> out) {
		double[] bound = bounds(angleDeg);
		if (bound[0] > qMaxX || bound[3] < qMinX || bound[1] > qMaxY || bound[4] < qMinY || bound[2] > qMaxZ || bound[5] < qMinZ) {
			return;
		}
		for (LocalBox b : boxes) {
			double[] w = frame.rotatedBox(b.a0(), b.b0(), b.c0(), b.a1(), b.b1(), b.c1(), angleDeg);
			if (w[0] < qMaxX && w[3] > qMinX && w[1] < qMaxY && w[4] > qMinY && w[2] < qMaxZ && w[5] > qMinZ) {
				out.add(w);
			}
		}
	}

	/** World box enclosing the whole leaf raised by {@code angleDeg}. */
	public double[] bounds(double angleDeg) {
		return frame.rotatedBox(minA, minB, minC, maxA, maxB, maxC, angleDeg);
	}

	/** Is a world point inside one of the solid boxes, the leaf raised by {@code angleDeg}? */
	public boolean contains(double angleDeg, double x, double y, double z) {
		double[] bound = bounds(angleDeg);
		if (x < bound[0] || x > bound[3] || y < bound[1] || y > bound[4] || z < bound[2] || z > bound[5]) {
			return false;
		}
		// exact test in leaf space: rotate the point back
		double[] l = frame.toLocal(x, y, z);
		double r = Math.toRadians(-angleDeg), cos = Math.cos(r), sin = Math.sin(r);
		double b = l[1] * cos - l[2] * sin, c = l[1] * sin + l[2] * cos;
		for (LocalBox bx : boxes) {
			if (l[0] >= bx.a0() && l[0] <= bx.a1() && b >= bx.b0() && b <= bx.b1() && c >= bx.c0() && c <= bx.c1()) {
				return true;
			}
		}
		return false;
	}

	/**
	 * World boxes of the volume the leaf sweeps between two angles (both included), sampled every
	 * {@link #SWEEP_STEP} degrees: anything intersecting one of them is in the way of the movement.
	 */
	public List<double[]> sweptBoxes(double fromDeg, double toDeg) {
		List<double[]> out = new ArrayList<>();
		double lo = Math.min(fromDeg, toDeg), hi = Math.max(fromDeg, toDeg);
		int n = Math.max(1, (int) Math.ceil((hi - lo) / SWEEP_STEP));
		for (int i = 0; i <= n; i++) {
			out.addAll(worldBoxes(lo + (hi - lo) * i / n));
		}
		return out;
	}

	/** World box enclosing the whole swept volume between two angles. */
	public double[] sweptBounds(double fromDeg, double toDeg) {
		double[] r = {Double.MAX_VALUE, Double.MAX_VALUE, Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE};
		double lo = Math.min(fromDeg, toDeg), hi = Math.max(fromDeg, toDeg);
		int n = Math.max(1, (int) Math.ceil((hi - lo) / SWEEP_STEP));
		for (int i = 0; i <= n; i++) {
			double[] b = bounds(lo + (hi - lo) * i / n);
			for (int k = 0; k < 3; k++) {
				r[k] = Math.min(r[k], b[k]);
				r[k + 3] = Math.max(r[k + 3], b[k + 3]);
			}
		}
		return r;
	}

	/**
	 * The lowest underside of the closed leaf over the navigable band: the smallest world Y of the bottoms of the
	 * boxes whose horizontal centre is within {@code halfWidth} of the channel's axis (as {@code across} measures
	 * it), or NaN when no box is over the band. Beams and lanterns hanging under the deck lower it.
	 */
	public double undersideOver(Across across, double halfWidth) {
		double best = Double.NaN;
		for (LocalBox b : boxes) {
			double[] w = frame.rotatedBox(b.a0(), b.b0(), b.c0(), b.a1(), b.b1(), b.c1(), 0);
			double cx = (w[0] + w[3]) / 2, cz = (w[2] + w[5]) / 2;
			if (Math.abs(across.across(cx, cz)) <= halfWidth && !(w[1] >= best)) {
				best = w[1];
			}
		}
		return best;
	}

	/**
	 * The barrier across this leaf's outer end (the shore side): a thin world box just outside the leaf's outer face,
	 * the width of the leaf plus a little, from half a block under the deck's top to 2.5 above it. Solid while the
	 * leaves are out, so nobody steps onto a moving or missing deck; the same on the server and the clients.
	 */
	public double[] barrierBox() {
		return frame.rotatedBox(minA - 0.6, minB - 0.6, maxC - 0.5, maxA + 0.6, minB - 0.05, maxC + 2.5, 0);
	}

	/** Distance across the channel of a world point (see {@link ChannelZones#across}). */
	@FunctionalInterface
	public interface Across {
		double across(double x, double z);
	}

	/** Does a world box intersect one of the given boxes? */
	public static boolean intersectsAny(List<double[]> boxes, double x0, double y0, double z0, double x1, double y1, double z1) {
		for (double[] w : boxes) {
			if (x0 < w[3] && x1 > w[0] && y0 < w[4] && y1 > w[1] && z0 < w[5] && z1 > w[2]) {
				return true;
			}
		}
		return false;
	}
}
