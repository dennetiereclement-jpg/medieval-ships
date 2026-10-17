package fr.medievalships.entity;

import java.util.List;

import net.minecraft.block.BlockState;
import net.minecraft.block.LilyPadBlock;
import net.minecraft.fluid.FluidState;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.core.Autopilot;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;

/** Adapts the Minecraft world to the pure navigation code (terrain, water, other hulls). */
final class ShipWorld implements ShipMover.Obstacles, Autopilot.Navigator {
	private final World world;
	private final ShipEntity self;
	private final BlockPos.Mutable pos = new BlockPos.Mutable();
	private final ShipEntity[] others;
	private final ShipPose[] otherPoses;
	private final ShipGeometry[] otherGeometries;

	ShipWorld(World world, ShipEntity self) {
		this.world = world;
		this.self = self;
		ShipEntity[] all = ShipTracker.ships(world); // shared array: never write into it
		ShipEntity[] near = new ShipEntity[all.length];
		int n = 0;
		for (ShipEntity s : all) {
			if (s != self && !s.isRemoved() && s.squaredDistanceTo(self) < 80 * 80) {
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
