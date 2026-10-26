package fr.medievalships.entity;

import java.util.List;

import net.minecraft.block.BlockState;
import net.minecraft.block.LilyPadBlock;
import net.minecraft.fluid.FluidState;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.Heightmap;
import net.minecraft.world.World;

import fr.medievalships.core.Autopilot;
import fr.medievalships.core.Dive;
import fr.medievalships.core.Flight;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;

/** Adapts the Minecraft world to the pure navigation code (terrain, water, other hulls). */
final class ShipWorld implements ShipMover.Obstacles, Autopilot.Navigator, Flight.Terrain, Dive.Sea {
	private final World world;
	private final ShipEntity self;
	private final BlockPos.Mutable pos = new BlockPos.Mutable();
	private final ShipEntity[] others;
	private final ShipPose[] otherPoses;
	private final ShipGeometry[] otherGeometries;

	ShipWorld(World world, ShipEntity self) {
		this(world, self, self.getX(), self.getY(), self.getZ());
	}

	/**
	 * The world around a point, for a vessel that is not there yet (placement, and its preview on the client): the
	 * other hulls within 80 blocks of it are obstacles. Only {@link #blocked} and {@link #waterSurface} may be used
	 * without a vessel.
	 */
	ShipWorld(World world, @org.jetbrains.annotations.Nullable ShipEntity self, double x, double y, double z) {
		this.world = world;
		this.self = self;
		ShipEntity[] all = ShipTracker.ships(world); // shared array: never write into it
		ShipEntity[] near = new ShipEntity[all.length];
		int n = 0;
		for (ShipEntity s : all) {
			if (s != self && !s.isRemoved() && s.squaredDistanceTo(x, y, z) < 80 * 80) {
				near[n++] = s;
			}
		}
		this.others = java.util.Arrays.copyOf(near, n);
		this.otherPoses = new ShipPose[n];
		this.otherGeometries = new ShipGeometry[n];
		for (int i = 0; i < n; i++) {
			otherPoses[i] = others[i].pose();
			otherGeometries[i] = others[i].geometry();
		}
	}

	private boolean loaded(double x, double z) {
		return world.isChunkLoaded(((int) Math.floor(x)) >> 4, ((int) Math.floor(z)) >> 4);
	}

	/** Is the chunk of this column loaded (nothing is known about an unloaded one)? */
	boolean isLoaded(double x, double z) {
		return loaded(x, z);
	}

	@Override
	public boolean blocked(double wx, double wy, double wz) {
		if (!loaded(wx, wz)) {
			return true;
		}
		pos.set(Math.floor(wx), Math.floor(wy), Math.floor(wz));
		BlockState state = world.getBlockState(pos);
		if (!state.isAir() && !(state.getBlock() instanceof LilyPadBlock)) {
			VoxelShape shape = state.getCollisionShape(world, pos);
			if (!shape.isEmpty()) {
				double lx = wx - pos.getX(), ly = wy - pos.getY(), lz = wz - pos.getZ();
				List<Box> boxes = shape.getBoundingBoxes();
				for (Box b : boxes) {
					if (lx >= b.minX && lx <= b.maxX && ly >= b.minY && ly <= b.maxY && lz >= b.minZ && lz <= b.maxZ) {
						return true;
					}
				}
			}
		}
		return insideOtherHull(wx, wy, wz);
	}

	private boolean insideOtherHull(double wx, double wy, double wz) {
		for (int i = 0; i < otherPoses.length; i++) {
			ShipPose p = otherPoses[i];
			double r = otherGeometries[i].boundingRadius();
			double dx = wx - p.x(), dz = wz - p.z();
			if (dx * dx + dz * dz > r * r) {
				continue;
			}
			double[] l = p.toLocal(wx, wy, wz);
			if (otherGeometries[i].insideHull(l[0], l[1], l[2])) {
				return true;
			}
		}
		return false;
	}

	/** Open water, at least two blocks deep, with nothing solid just above the surface. */
	@Override
	public boolean navigable(double x, double z) {
		if (!loaded(x, z)) {
			return false;
		}
		int bx = (int) Math.floor(x), bz = (int) Math.floor(z);
		double water = self.getY() + self.geometry().hull().waterlineY;
		int surface = (int) Math.floor(water - 0.2);
		for (int dy = 0; dy >= -1; dy--) {
			pos.set(bx, surface + dy, bz);
			if (!world.getFluidState(pos).isIn(FluidTags.WATER)) {
				return false;
			}
		}
		for (int dy = 1; dy <= 2; dy++) {
			pos.set(bx, surface + dy, bz);
			BlockState state = world.getBlockState(pos);
			if (!state.isAir() && !(state.getBlock() instanceof LilyPadBlock)
					&& !state.getCollisionShape(world, pos).isEmpty()) {
				return false;
			}
		}
		double wy = water + 0.2;
		return !insideOtherHull(x, wy, z);
	}

	/** Top of the ground, trees and buildings in a column (aircraft autopilot); +infinity if not loaded. */
	@Override
	public double groundTop(double x, double z) {
		if (!loaded(x, z)) {
			return Double.POSITIVE_INFINITY;
		}
		return world.getTopY(Heightmap.Type.MOTION_BLOCKING, (int) Math.floor(x), (int) Math.floor(z));
	}

	/**
	 * Submarine: origin height at which it floats on the surface here, from the top of the water
	 * column that contains its hull (however deep it is), or NaN if it is not in the water.
	 */
	double surfacedY(ShipEntity ship) {
		double x = ship.getX(), z = ship.getZ();
		if (!loaded(x, z)) {
			return Double.NaN;
		}
		int bx = (int) Math.floor(x), bz = (int) Math.floor(z);
		int start = (int) Math.floor(ship.getY() + ship.geometry().hull().mainDeckY - 1.0);
		int y = Integer.MIN_VALUE;
		for (int k = 0; k <= 3; k++) {
			pos.set(bx, start - k, bz);
			if (world.getFluidState(pos).isIn(FluidTags.WATER)) {
				y = start - k;
				break;
			}
		}
		if (y == Integer.MIN_VALUE) {
			return Double.NaN;
		}
		int top = world.getTopYInclusive();
		while (y < top) {
			pos.set(bx, y + 1, bz);
			if (!world.getFluidState(pos).isIn(FluidTags.WATER)) {
				break;
			}
			y++;
		}
		pos.set(bx, y, bz);
		return y + world.getFluidState(pos).getHeight(world, pos) - ship.geometry().hull().waterlineY;
	}

	// ---- submarine: the sea around it, for its autopilot (columns cached for the tick)

	private double seaLevel = Double.NaN;
	private final java.util.Map<Long, double[]> columns = new java.util.HashMap<>();

	/** Water surface and sea bed of a column: {surface, bed}. */
	private double[] column(double x, double z) {
		int bx = (int) Math.floor(x), bz = (int) Math.floor(z);
		long key = ((long) bx << 32) ^ (bz & 0xffffffffL);
		double[] c = columns.get(key);
		if (c != null) {
			return c;
		}
		if (Double.isNaN(seaLevel)) {
			double s = surfacedY(self);
			seaLevel = Double.isNaN(s) ? self.getY() + self.geometry().hull().waterlineY : s + self.geometry().hull().waterlineY;
		}
		double surface = waterSurface(x, z, seaLevel - 0.5);
		double bed = Double.NEGATIVE_INFINITY;
		if (!Double.isNaN(surface)) {
			int bottom = Math.max(world.getBottomY(), (int) Math.floor(surface) - 200);
			bed = bottom;
			for (int y = (int) Math.floor(surface) - 1; y >= bottom; y--) {
				pos.set(bx, y, bz);
				BlockState state = world.getBlockState(pos);
				if (!state.isAir() && !state.getCollisionShape(world, pos).isEmpty()) {
					bed = y + 1;
					break;
				}
			}
		}
		c = new double[] {surface, bed};
		columns.put(key, c);
		return c;
	}

	@Override
	public double surface(double x, double z) {
		return column(x, z)[0];
	}

	@Override
	public double bed(double x, double z) {
		return column(x, z)[1];
	}

	/** Water surface height at a column near {@code nearY}, or NaN if there is no water. */
	double waterSurface(double x, double z, double nearY) {
		if (!loaded(x, z)) {
			return Double.NaN;
		}
		int bx = (int) Math.floor(x), bz = (int) Math.floor(z);
		int start = (int) Math.floor(nearY + 0.5);
		for (int y = start + 2; y >= start - 3; y--) {
			pos.set(bx, y, bz);
			FluidState fluid = world.getFluidState(pos);
			if (fluid.isIn(FluidTags.WATER)) {
				// go up while there is water above
				int top = y;
				for (int k = 0; k < 4; k++) {
					pos.set(bx, top + 1, bz);
					if (!world.getFluidState(pos).isIn(FluidTags.WATER)) {
						break;
					}
					top++;
				}
				pos.set(bx, top, bz);
				return top + world.getFluidState(pos).getHeight(world, pos);
			}
		}
		return Double.NaN;
	}
}
