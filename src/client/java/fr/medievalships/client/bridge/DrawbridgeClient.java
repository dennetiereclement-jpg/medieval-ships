package fr.medievalships.client.bridge;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.BlockState;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.command.argument.BlockArgumentParser;
import net.minecraft.registry.Registries;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.bridge.DrawbridgeCollisions;
import fr.medievalships.core.bridge.BridgeCycle;
import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.LeafFrame;
import fr.medievalships.core.bridge.LeafShape;
import fr.medievalships.network.DrawbridgeSyncPayload;

/**
 * The drawbridges as this client knows them (what the server sent, see {@link DrawbridgeSyncPayload}): the leaves'
 * frames and blocks, the channel, and the cycle's motion from which the angle is computed at any instant from the
 * world time. Each bridge is a collision source for the local player ({@link DrawbridgeCollisions}) and is drawn by
 * {@code DrawbridgeRenderer}. Kept per client world; forgotten on disconnect.
 */
public final class DrawbridgeClient {
	/** A captured block to draw: its original position and its state. */
	public record RenderBlock(int x, int y, int z, BlockState state) {
	}

	public static final class ClientBridge implements DrawbridgeCollisions.Source {
		public final String id;
		private final World world;
		public boolean converted;
		public final LeafFrame[] frames = new LeafFrame[2];
		public final LeafShape[] shapes = new LeafShape[2];
		public final List<List<RenderBlock>> blocks = List.of(new ArrayList<>(), new ArrayList<>());
		/** Selection corners {minX, minY, minZ, maxX, maxY, maxZ} of each leaf, null when not set. */
		public final int[][] selections = new int[2][];
		@Nullable
		public ChannelZones zones;
		public double waterY, undersideY;
		public BridgeCycle.State state = BridgeCycle.State.FERME;
		public double moveFrom;
		public double moveTo;
		public long startTick;
		public int moveTicks;
		public double openAngle;
		public boolean blocksInWorld = true;
		public boolean preview;
		public boolean chains = true;
		public double chainHeight;
		private List<double[]> barriers = List.of();
		@Nullable
		private double[] bounds;
		private double cachedAngle = Double.NaN;
		private List<double[]> cachedBoxes = List.of();

		ClientBridge(String id, World world) {
			this.id = id;
			this.world = world;
		}

		/** The leaves' angle at a world time (ticks, fractional while rendering): the server's eased move, replayed. */
		public double angle(double now) {
			return switch (state) {
				case OUVERTURE, FERMETURE -> BridgeCycle.angleOf(moveFrom, moveTo, moveTicks, Math.max(0, Math.min(moveTicks, now - startTick)));
				case OUVERT -> openAngle;
				default -> 0;
			};
		}

		@Override
		public boolean leavesOut() {
			return converted && state.leavesOut() && shapes[0] != null && shapes[1] != null;
		}

		@Override
		public List<double[]> leafBoxes() {
			double angle = angle(world.getTime());
			if (angle != cachedAngle) {
				List<double[]> out = new ArrayList<>();
				for (LeafShape s : shapes) {
					if (s != null) {
						out.addAll(s.worldBoxes(angle));
					}
				}
				cachedBoxes = out;
				cachedAngle = angle;
			}
			return cachedBoxes;
		}

		@Override
		public List<double[]> barrierBoxes() {
			return barriers;
		}

		@Override
		public double[] bounds() {
			return bounds;
		}

		void finish() {
			List<double[]> bars = new ArrayList<>();
			double[] r = {Double.MAX_VALUE, Double.MAX_VALUE, Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE};
			for (LeafShape s : shapes) {
				if (s == null || s.isEmpty()) {
					continue;
				}
				double[] bar = s.barrierBox();
				bars.add(bar);
				double[] b = s.sweptBounds(0, 90);
				for (int k = 0; k < 3; k++) {
					r[k] = Math.min(r[k], Math.min(b[k], bar[k]));
					r[k + 3] = Math.max(r[k + 3], Math.max(b[k + 3], bar[k + 3]));
				}
			}
			barriers = bars;
			bounds = bars.isEmpty() ? null : r;
			cachedAngle = Double.NaN;
		}
	}

	private static final Map<World, Map<String, ClientBridge>> BY_WORLD = new WeakHashMap<>();

	private DrawbridgeClient() {
	}

	/** A payload from the server (client thread). */
	public static synchronized void receive(DrawbridgeSyncPayload p, ClientWorld world) {
		Map<String, ClientBridge> map = BY_WORLD.computeIfAbsent(world, w -> new LinkedHashMap<>());
		ClientBridge old = map.get(p.id());
		if (p.removed()) {
			if (old != null) {
				map.remove(p.id());
				DrawbridgeCollisions.remove(world, old);
			}
			return;
		}
		ClientBridge b = new ClientBridge(p.id(), world);
		b.converted = p.converted();
		b.preview = p.preview();
		for (int i = 0; i < 2 && i < p.leaves().size(); i++) {
			DrawbridgeSyncPayload.Leaf l = p.leaves().get(i);
			if (l.selection().size() == 6) {
				int[] sel = new int[6];
				for (int k = 0; k < 6; k++) {
					sel[k] = l.selection().get(k);
				}
				b.selections[i] = sel;
			}
			boolean hasFrame = Math.hypot(l.ux(), l.uz()) > 1e-6 && Math.hypot(l.vx(), l.vz()) > 1e-6;
			if (!hasFrame) {
				continue;
			}
			b.frames[i] = new LeafFrame(l.hx(), l.hy(), l.hz(), l.ux(), l.uz(), l.vx(), l.vz());
			List<double[]> boxes = new ArrayList<>();
			for (DrawbridgeSyncPayload.Block blk : l.blocks()) {
				BlockState state;
				try {
					state = BlockArgumentParser.block(Registries.BLOCK, blk.state(), false).blockState();
				} catch (Exception e) {
					MedievalShips.LOGGER.warn("Drawbridge {}: unknown block state {}", p.id(), blk.state());
					continue;
				}
				BlockPos pos = new BlockPos(blk.x(), blk.y(), blk.z());
				b.blocks.get(i).add(new RenderBlock(blk.x(), blk.y(), blk.z(), state));
				VoxelShape shape = state.getCollisionShape(world, pos);
				if (!shape.isEmpty()) {
					for (Box bx : shape.getBoundingBoxes()) {
						boxes.add(new double[] {pos.getX() + bx.minX, pos.getY() + bx.minY, pos.getZ() + bx.minZ, pos.getX() + bx.maxX, pos.getY() + bx.maxY,
								pos.getZ() + bx.maxZ});
					}
				}
			}
			b.shapes[i] = new LeafShape(b.frames[i], boxes);
		}
		DrawbridgeSyncPayload.Zones z = p.zones();
		if (Math.hypot(z.dx(), z.dz()) > 1e-6 && z.halfWidth() > 0) {
			b.zones = ChannelZones.of(z.cx(), z.cz(), z.dx(), z.dz(), z.halfWidth(), z.halfSpan(), z.approach(), z.hysteresis());
			b.waterY = z.waterY();
			b.undersideY = z.undersideY();
		}
		DrawbridgeSyncPayload.Motion m = p.motion();
		b.state = BridgeCycle.State.of(m.state());
		b.moveFrom = m.moveFrom();
		b.moveTo = m.moveTo();
		b.startTick = m.startTick();
		b.moveTicks = m.moveTicks();
		b.openAngle = m.openAngle();
		b.blocksInWorld = m.blocksInWorld();
		b.chains = p.chains();
		b.chainHeight = p.chainHeight();
		b.finish();
		map.put(p.id(), b);
		if (old != null) {
			DrawbridgeCollisions.remove(world, old);
		}
		DrawbridgeCollisions.add(world, b);
	}

	public static synchronized Collection<ClientBridge> bridges(World world) {
		Map<String, ClientBridge> map = BY_WORLD.get(world);
		return map == null ? List.of() : new ArrayList<>(map.values());
	}

	/** Disconnected: forget everything. */
	public static synchronized void clear() {
		BY_WORLD.clear();
	}
}
