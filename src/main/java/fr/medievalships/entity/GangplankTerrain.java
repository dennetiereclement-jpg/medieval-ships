package fr.medievalships.entity;

import java.util.List;

import net.minecraft.block.BlockState;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.core.Gangplank;
import fr.medievalships.core.ShipPose;

/**
 * The world as the gangplank's safety checks see it ({@link Gangplank#findLanding}, {@link Gangplank#clearance}), in
 * ship-local coordinates: block collision shapes only (water is not a landing), never loading a chunk (an unloaded
 * column has no surface and counts as solid). Used on lever clicks and once after loading, never every tick.
 */
final class GangplankTerrain implements Gangplank.Terrain {
	private final World world;
	private final ShipPose pose;
	private final BlockPos.Mutable pos = new BlockPos.Mutable();

	GangplankTerrain(World world, ShipPose pose) {
		this.world = world;
		this.pose = pose;
	}

	private boolean loaded(int bx, int bz) {
		return world.isChunkLoaded(bx >> 4, bz >> 4);
	}

	@Override
	public double surface(double lx, double lz, double yMin, double yMax) {
		double wx = pose.worldX(lx, lz), wz = pose.worldZ(lx, lz);
		int bx = (int) Math.floor(wx), bz = (int) Math.floor(wz);
		if (!loaded(bx, bz)) {
			return Double.NaN;
		}
		double fx = wx - bx, fz = wz - bz;
		int top = (int) Math.floor(pose.y() + yMax), bottom = (int) Math.floor(pose.y() + yMin);
		for (int by = top; by >= bottom; by--) {
			double t = topAt(bx, by, bz, fx, fz);
			if (Double.isNaN(t)) {
				continue;
			}
			double y = by + t;
			if (y > pose.y() + yMax + 1e-6 || y < pose.y() + yMin - 1e-6) {
				return Double.NaN; // the first solid met is out of range (inside a wall above, or under the range)
			}
			// an exposed top: nothing solid just above it where one would walk
			if (!solidWorld(wx, y + 0.3, wz)) {
				return y - pose.y();
			}
			return Double.NaN;
		}
		return Double.NaN;
	}

	/** Top of the collision shape of block (bx, by, bz) at the point (fx, fz) of the block, or NaN. */
	private double topAt(int bx, int by, int bz, double fx, double fz) {
		pos.set(bx, by, bz);
		BlockState state = world.getBlockState(pos);
		if (state.isAir()) {
			return Double.NaN;
		}
		VoxelShape shape = state.getCollisionShape(world, pos);
		if (shape.isEmpty()) {
			return Double.NaN;
		}
		double best = Double.NaN;
		List<Box> boxes = shape.getBoundingBoxes();
		for (Box b : boxes) {
			if (fx >= b.minX - 0.05 && fx <= b.maxX + 0.05 && fz >= b.minZ - 0.05 && fz <= b.maxZ + 0.05 && !(b.maxY <= best)) {
				best = b.maxY;
			}
		}
		return best;
	}

	@Override
	public boolean solid(double lx, double ly, double lz) {
		double[] w = pose.toWorld(lx, ly, lz);
		return solidWorld(w[0], w[1], w[2]);
	}

	private boolean solidWorld(double wx, double wy, double wz) {
		int bx = (int) Math.floor(wx), by = (int) Math.floor(wy), bz = (int) Math.floor(wz);
		if (!loaded(bx, bz)) {
			return true;
		}
		pos.set(bx, by, bz);
		BlockState state = world.getBlockState(pos);
		if (state.isAir()) {
			return false;
		}
		VoxelShape shape = state.getCollisionShape(world, pos);
		if (shape.isEmpty()) {
			return false;
		}
		double fx = wx - bx, fy = wy - by, fz = wz - bz;
		for (Box b : shape.getBoundingBoxes()) {
			if (fx > b.minX && fx < b.maxX && fy > b.minY && fy < b.maxY && fz > b.minZ && fz < b.maxZ) {
				return true;
			}
		}
		return false;
	}
}
