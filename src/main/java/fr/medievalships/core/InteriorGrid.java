package fr.medievalships.core;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * Interior of a vessel with rooms (the Nautilus) in 0.5 block cells, ship-local: what is solid,
 * dry, a ladder, a door. Written by {@code tools/nautilus_interior.py}, which also draws the walls,
 * floors and ceilings of the model on the boundaries of these cells, so what is drawn is what
 * collides.
 *
 * <p>Doors are solid when closed and dry when open; the airlock is dry or flooded.
 */
public final class InteriorGrid {
	public static final byte OUT = 0;
	public static final byte SOLID = 1;
	public static final byte DRY = 2;
	public static final byte LADDER = 3;
	public static final byte AIRLOCK = 4;
	/** Glass in the hull: solid and dry; the model leaves it open, so the sea is seen through it. */
	public static final byte WINDOW = 5;
	/** Under a piece of furniture: solid and dry; the furniture itself is drawn instead of walls. */
	public static final byte FURNITURE = 6;
	public static final byte DOOR = 16;
	public static final int MAX_DOORS = 32;

	/** Doors and airlock of one vessel: the airlock water level goes from 0 (pumped out) to 1 (full). */
	public record State(long openDoors, float airlockLevel) {
		public static final State CLOSED = new State(0L, 0f);

		public boolean doorOpen(int door) {
			return (openDoors & (1L << door)) != 0;
		}

		public boolean airlockFlooded() {
			return airlockLevel >= 0.999f;
		}

		public boolean airlockDry() {
			return airlockLevel <= 0.001f;
		}

		public State withDoor(int door, boolean open) {
			return new State(open ? openDoors | (1L << door) : openDoors & ~(1L << door), airlockLevel);
		}

		public State withAirlock(float level) {
			return new State(openDoors, Math.max(0f, Math.min(1f, level)));
		}
	}

	public final int nx;
	public final int ny;
	public final int nz;
	public final double x0;
	public final double y0;
	public final double z0;
	public final double cell;
	private final byte[] cells;
	/** Centre of each door (ship-local), null for the indices without door. */
	private final double[][] doorCenters;
	/** Floor and ceiling of the airlock (ship-local heights; NaN without airlock). */
	public final double airlockFloor;
	public final double airlockTop;
	/** Cells where entities are carried along: inside, or in the 2.5 blocks above a walkable outside surface. */
	private final boolean[] carry;

	InteriorGrid(int nx, int ny, int nz, double x0, double y0, double z0, double cell, byte[] cells) {
		this.nx = nx;
		this.ny = ny;
		this.nz = nz;
		this.x0 = x0;
		this.y0 = y0;
		this.z0 = z0;
		this.cell = cell;
		this.cells = cells;
		this.carry = new boolean[cells.length];
		int lowest = Integer.MAX_VALUE, highest = -1;
		for (int i = 0; i < cells.length; i++) {
			if (cells[i] == AIRLOCK) {
				lowest = Math.min(lowest, i % ny);
				highest = Math.max(highest, i % ny);
			}
		}
		double[][] sums = new double[MAX_DOORS][4];
		for (int ix = 0; ix < nx; ix++) {
			for (int iz = 0; iz < nz; iz++) {
				for (int iy = 0; iy < ny; iy++) {
					int k = cells[(ix * nz + iz) * ny + iy] - DOOR;
					if (k >= 0 && k < MAX_DOORS) {
						sums[k][0] += x0 + (ix + 0.5) * cell;
						sums[k][1] += y0 + (iy + 0.5) * cell;
						sums[k][2] += z0 + (iz + 0.5) * cell;
						sums[k][3]++;
					}
				}
			}
		}
		this.doorCenters = new double[MAX_DOORS][];
		for (int k = 0; k < MAX_DOORS; k++) {
			if (sums[k][3] > 0) {
				doorCenters[k] = new double[] {sums[k][0] / sums[k][3], sums[k][1] / sums[k][3], sums[k][2] / sums[k][3]};
			}
		}
		this.airlockFloor = highest < 0 ? Double.NaN : y0 + lowest * cell;
		this.airlockTop = highest < 0 ? Double.NaN : y0 + (highest + 1) * cell;
		int above = (int) Math.round(2.5 / cell);
		for (int ix = 0; ix < nx; ix++) {
			for (int iz = 0; iz < nz; iz++) {
				int base = (ix * nz + iz) * ny;
				int sinceSolid = Integer.MAX_VALUE;
				for (int iy = 0; iy < ny; iy++) {
					byte k = cells[base + iy];
					if (k != OUT) {
						carry[base + iy] = true;
						sinceSolid = k == SOLID || k == WINDOW || k == FURNITURE || k >= DOOR ? 0 : Integer.MAX_VALUE;
					} else {
						if (sinceSolid != Integer.MAX_VALUE) {
							sinceSolid++;
						}
						carry[base + iy] = sinceSolid <= above;
					}
				}
			}
		}
	}

	/** Reads a grid file from the class path (the mod jar), e.g. {@code /assets/medievalships/interiors/nautilus.grid}. */
	public static InteriorGrid load(String resource) {
		try (InputStream in = InteriorGrid.class.getResourceAsStream(resource)) {
			if (in == null) {
				throw new IllegalStateException("missing interior grid " + resource);
			}
			ByteArrayOutputStream bytes = new ByteArrayOutputStream();
			in.transferTo(bytes);
			return parse(bytes.toByteArray());
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
	}

	static InteriorGrid parse(byte[] data) {
		ByteBuffer b = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
		byte[] magic = new byte[8];
		b.get(magic);
		if (!new String(magic, StandardCharsets.US_ASCII).equals("MSGRID1\0")) {
			throw new IllegalArgumentException("not an interior grid");
		}
		int nx = b.getInt(), ny = b.getInt(), nz = b.getInt();
		double x0 = b.getDouble(), y0 = b.getDouble(), z0 = b.getDouble(), cell = b.getDouble();
		byte[] cells = new byte[nx * ny * nz];
		int i = 0;
		while (b.hasRemaining()) {
			byte kind = b.get();
			int run = 0;
			for (int shift = 0; ; shift += 7) {
				int v = b.get() & 0xFF;
				run |= (v & 0x7F) << shift;
				if ((v & 0x80) == 0) {
					break;
				}
			}
			java.util.Arrays.fill(cells, i, i + run, kind);
			i += run;
		}
		if (i != cells.length) {
			throw new IllegalArgumentException("truncated interior grid");
		}
		return new InteriorGrid(nx, ny, nz, x0, y0, z0, cell, cells);
	}

	public int ix(double lx) {
		return (int) Math.floor((lx - x0) / cell);
	}

	public int iy(double ly) {
		return (int) Math.floor((ly - y0) / cell);
	}

	public int iz(double lz) {
		return (int) Math.floor((lz - z0) / cell);
	}

	/** Cell kind, {@link #OUT} beyond the grid. */
	public byte kind(int ix, int iy, int iz) {
		if (ix < 0 || iy < 0 || iz < 0 || ix >= nx || iy >= ny || iz >= nz) {
			return OUT;
		}
		return cells[(ix * nz + iz) * ny + iy];
	}

	public byte kindAt(double lx, double ly, double lz) {
		return kind(ix(lx), iy(ly), iz(lz));
	}

	/** Does this cell stop entities (wall, floor, closed door)? */
	public static boolean solid(byte kind, State state) {
		if (kind == SOLID || kind == WINDOW || kind == FURNITURE) {
			return true;
		}
		if (kind >= DOOR) {
			return !state.doorOpen(kind - DOOR);
		}
		return false;
	}

	/** Centre of a door (ship-local), or null. */
	public double[] doorCenter(int door) {
		return door >= 0 && door < MAX_DOORS ? doorCenters[door] : null;
	}

	/** Height of the water in the airlock (ship-local). */
	public double airlockWaterY(State state) {
		return airlockFloor + state.airlockLevel() * (airlockTop - airlockFloor);
	}

	/**
	 * Is this point dry air (inside a watertight compartment, open door, airlock above its water)?
	 * Walls count as dry.
	 */
	public boolean dry(byte kind, double ly, State state) {
		return switch (kind) {
			case OUT -> false;
			case AIRLOCK -> state.airlockDry() || ly > airlockWaterY(state);
			default -> true;
		};
	}

	public boolean solidAt(double lx, double ly, double lz, State state) {
		return solid(kindAt(lx, ly, lz), state);
	}

	public boolean dryAt(double lx, double ly, double lz, State state) {
		return dry(kindAt(lx, ly, lz), ly, state);
	}

	public boolean ladderAt(double lx, double ly, double lz) {
		return kindAt(lx, ly, lz) == LADDER;
	}

	/** Not outside the hull (inside a space, a wall or a door). */
	public boolean insideAt(double lx, double ly, double lz) {
		return kindAt(lx, ly, lz) != OUT;
	}

	public boolean carryAt(double lx, double ly, double lz) {
		int ix = ix(lx), iy = iy(ly), iz = iz(lz);
		if (ix < 0 || iy < 0 || iz < 0 || ix >= nx || iy >= ny || iz >= nz) {
			return false;
		}
		return carry[(ix * nz + iz) * ny + iy];
	}

	// ---- the world's water drawn across the rooms (the client skips it: fr.medievalships.client.render.DryWater)

	/** Where the samples of a water block are taken: at 0.1, 0.5 and 0.9 of the block along each axis (27 points). */
	private static final double[] WATER_SAMPLE_OFFSETS = {-0.4, 0.0, 0.4};

	/**
	 * Sorts the 27 sample points of the world's water block whose lower corner is (bx, by, bz) into {outside the hull,
	 * dry, wet inside}: outside is {@link #OUT}; dry is a room, a wall, a floor, a piece of furniture, a door or the
	 * airlock above its water (see {@link #dry}); wet inside is the airlock under its water. The vessel is at {@code pose}.
	 */
	public int[] waterSamples(ShipPose pose, int bx, int by, int bz, State state) {
		double c = pose.cos(), s = pose.sin();
		double dx = bx + 0.5 - pose.x(), dz = bz + 0.5 - pose.z();
		double lxc = dx * c + dz * s, lzc = -dx * s + dz * c, lyc = by + 0.5 - pose.y();
		// a block whose centre is more than a block from the grid is wholly outside it (the usual case: the open sea)
		if (lxc < x0 - 1.0 || lxc > x0 + nx * cell + 1.0 || lyc < y0 - 1.0 || lyc > y0 + ny * cell + 1.0 || lzc < z0 - 1.0
				|| lzc > z0 + nz * cell + 1.0) {
			return new int[] {27, 0, 0};
		}
		int out = 0, dry = 0, wet = 0;
		for (double ox : WATER_SAMPLE_OFFSETS) {
			for (double oz : WATER_SAMPLE_OFFSETS) {
				// the world offsets (ox, oz) of the sample, turned into the ship's frame
				double lx = lxc + ox * c + oz * s, lz = lzc - ox * s + oz * c;
				for (double oy : WATER_SAMPLE_OFFSETS) {
					double ly = lyc + oy;
					byte k = kindAt(lx, ly, lz);
					if (k == OUT) {
						out++;
					} else if (dry(k, ly, state)) {
						dry++;
					} else {
						wet++;
					}
				}
			}
		}
		return new int[] {out, dry, wet};
	}

	/**
	 * The rule on the counts of {@link #waterSamples}: the block is not drawn when at least one of its samples is dry and
	 * none is outside the hull (it lies in a room, a floor slab, a staircase, a wall); a block straddling the outer hull
	 * is hidden only when its dry samples outnumber the outside ones. (What would be drawn is the surface of the sea,
	 * which otherwise cuts across a hold under the waterline, a companionway or a floor slab.)
	 */
	public static boolean hidesWater(int[] samples) {
		int out = samples[0], dry = samples[1];
		return dry > 0 && (out == 0 || dry > out);
	}

	/** Is the world's water block whose lower corner is (bx, by, bz) inside this vessel at {@code pose}, not to be drawn? */
	public boolean hidesWater(ShipPose pose, int bx, int by, int bz, State state) {
		return hidesWater(waterSamples(pose, bx, by, bz, state));
	}

	/** Sink for local boxes. */
	public interface LocalBoxSink {
		void accept(double minX, double minY, double minZ, double maxX, double maxY, double maxZ);
	}

	/**
	 * Emits the solid cells within local bounds, merged into vertical runs (one box per run of
	 * solid cells in a column).
	 */
	public void solidRuns(double lxMin, double lyMin, double lzMin, double lxMax, double lyMax, double lzMax, State state,
			LocalBoxSink sink) {
		int ix0 = Math.max(0, ix(lxMin)), ix1 = Math.min(nx - 1, ix(lxMax));
		int iy0 = Math.max(0, iy(lyMin)), iy1 = Math.min(ny - 1, iy(lyMax));
		int iz0 = Math.max(0, iz(lzMin)), iz1 = Math.min(nz - 1, iz(lzMax));
		for (int ix = ix0; ix <= ix1; ix++) {
			for (int iz = iz0; iz <= iz1; iz++) {
				int base = (ix * nz + iz) * ny;
				int start = -1;
				for (int iy = iy0; iy <= iy1 + 1; iy++) {
					boolean s = iy <= iy1 && solid(cells[base + iy], state);
					if (s && start < 0) {
						start = iy;
					} else if (!s && start >= 0) {
						sink.accept(x0 + ix * cell, y0 + start * cell, z0 + iz * cell,
								x0 + (ix + 1) * cell, y0 + iy * cell, z0 + (iz + 1) * cell);
						start = -1;
					}
				}
			}
		}
	}

	/**
	 * Top of the solid run containing a local point (a foot sunk into a floor or a step), if that
	 * top is less than {@code maxDepth} above it and there is head room above; NaN otherwise.
	 */
	public double floorAbove(double lx, double ly, double lz, double maxDepth, State state) {
		int ix = ix(lx), iy = iy(ly), iz = iz(lz);
		if (!solid(kind(ix, iy, iz), state)) {
			return Double.NaN;
		}
		int top = iy;
		while (solid(kind(ix, top + 1, iz), state)) {
			top++;
		}
		double y = y0 + (top + 1) * cell;
		if (y - ly > maxDepth) {
			return Double.NaN;
		}
		for (int k = 1; k <= 3; k++) {
			if (solid(kind(ix, top + k, iz), state)) {
				return Double.NaN;
			}
		}
		return y;
	}

	/**
	 * Highest floor top crossed going down from {@code yBefore} to {@code yAfter} (local) at a
	 * column, when it was crossed by more than {@code minDepth}; NaN otherwise.
	 */
	public double floorCrossed(double lx, double lz, double yBefore, double yAfter, double minDepth, State state) {
		int ix = ix(lx), iz = iz(lz);
		if (ix < 0 || iz < 0 || ix >= nx || iz >= nz || yAfter >= yBefore) {
			return Double.NaN;
		}
		for (int iy = iy(yBefore - 0.05); iy >= Math.max(0, iy(yAfter)); iy--) {
			if (solid(kind(ix, iy, iz), state) && !solid(kind(ix, iy + 1, iz), state)) {
				double top = y0 + (iy + 1) * cell;
				if (yBefore >= top - 0.05 && yAfter < top - minDepth) {
					return top;
				}
			}
		}
		return Double.NaN;
	}
}
