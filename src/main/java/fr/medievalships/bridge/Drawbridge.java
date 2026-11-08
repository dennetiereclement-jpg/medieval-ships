package fr.medievalships.bridge;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.command.argument.BlockArgumentParser;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.vehicle.VehicleEntity;
import net.minecraft.fluid.FluidState;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.nbt.StringNbtReader;
import net.minecraft.registry.Registries;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.storage.NbtReadView;
import net.minecraft.text.Text;
import net.minecraft.util.ErrorReporter;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPhysics;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.bridge.BridgeCycle;
import fr.medievalships.core.bridge.BridgeTuning;
import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.DrawbridgeConfig;
import fr.medievalships.core.bridge.Gauge;
import fr.medievalships.core.bridge.LeafFrame;
import fr.medievalships.core.bridge.LeafShape;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipTracker;

/**
 * One drawbridge of the server: its definition (the two leaves' selections, hinges, the channel, the tuning), the
 * captured blocks of its deck, and its running cycle. Closed, the deck is made of its real blocks; the rest of the
 * time the leaves are collision boxes ({@link DrawbridgeCollisions.Source}) that the clients draw from the same
 * synced data. Everything happens on the server; see {@link Drawbridges} for the ticking and the API.
 */
public final class Drawbridge implements DrawbridgeCollisions.Source {
	/** A captured block of the deck: its position, its state ({@code minecraft:oak_planks[...]}) and its block entity's data (SNBT) or null. */
	public static final class BlockRecord {
		public int x, y, z;
		public String state;
		@Nullable
		public String nbt;

		public BlockRecord() {
		}

		public BlockRecord(int x, int y, int z, String state, @Nullable String nbt) {
			this.x = x;
			this.y = y;
			this.z = z;
			this.state = state;
			this.nbt = nbt;
		}

		public BlockPos pos() {
			return new BlockPos(x, y, z);
		}
	}

	/** One leaf as defined by the administrator and captured from the world. */
	public static final class LeafDef {
		public String name;
		/** The two corners of the selection (inclusive), null until set. */
		@Nullable
		public int[] pos1;
		@Nullable
		public int[] pos2;
		/** A point of the hinge line, or null: the outer bottom (or top) edge of the selection. */
		@Nullable
		public double[] hinge;
		/** With an automatic hinge: on the top edge of the deck instead of the bottom one. */
		public boolean hingeTop;
		/** The deck's blocks, captured at the conversion and at every opening. */
		public List<BlockRecord> blocks = new ArrayList<>();

		public LeafDef() {
		}

		public LeafDef(String name) {
			this.name = name;
		}

		public boolean complete() {
			return pos1 != null && pos2 != null;
		}

		public int[] min() {
			return new int[] {Math.min(pos1[0], pos2[0]), Math.min(pos1[1], pos2[1]), Math.min(pos1[2], pos2[2])};
		}

		public int[] max() {
			return new int[] {Math.max(pos1[0], pos2[0]), Math.max(pos1[1], pos2[1]), Math.max(pos1[2], pos2[2])};
		}

		/** Centre of the selection box (world, doubles). */
		public double[] centre() {
			int[] a = min(), b = max();
			return new double[] {(a[0] + b[0] + 1) / 2.0, (a[1] + b[1] + 1) / 2.0, (a[2] + b[2] + 1) / 2.0};
		}

		public boolean contains(int x, int y, int z) {
			if (!complete()) {
				return false;
			}
			int[] a = min(), b = max();
			return x >= a[0] && x <= b[0] && y >= a[1] && y <= b[1] && z >= a[2] && z <= b[2];
		}

		boolean overlaps(LeafDef o) {
			if (!complete() || !o.complete()) {
				return false;
			}
			int[] a = min(), b = max(), c = o.min(), d = o.max();
			return a[0] <= d[0] && b[0] >= c[0] && a[1] <= d[1] && b[1] >= c[1] && a[2] <= d[2] && b[2] >= c[2];
		}
	}

	/** The saved form of a bridge (JSON in {@link DrawbridgeData}). */
	public static final class Saved {
		public String id;
		public String dimension = "minecraft:overworld";
		public LeafDef[] leaves = {new LeafDef("A"), new LeafDef("B")};
		/** Channel direction (x, z), or null: perpendicular to the span between the leaves. */
		@Nullable
		public double[] axis;
		/** Channel centre (x, y, z), or null: the middle between the leaves. */
		@Nullable
		public double[] centre;
		/** Navigable half width, or null: half the distance between the hinge lines. */
		@Nullable
		public Double halfWidth;
		/** Water surface, or null: found under the centre. */
		@Nullable
		public Double waterY;
		public double approach = 50;
		public double hysteresis = 8;
		public double openAngle = 80;
		public int durationTicks = 160;
		public int closeDelayTicks = 100;
		public int warningTicks = 80;
		public double margin = 0.5;
		public double stopDistance = 6;
		public boolean converted;
		public boolean suspended;
		/** Draw the lifting chains (free end of each leaf to anchors over its hinge). */
		public boolean chains = true;
		/** Height of the chains' anchors over the hinge, 0 = automatic (the leaf's length plus 1.5). */
		public double chainHeight;
		public String state = "FERME";
		public double angle;
		public boolean blocksInWorld = true;
	}

	/** A vessel the bridge is taking into account. */
	public static final class Tracked {
		public String label = "";
		public long lastSeen;
		public double distance;
		public int side;
		public boolean requiresOpening;
		public boolean tooWide;
		public boolean inPassage;
		public boolean inApproach;
		public boolean approaching;
		/** Seen within the approach once: counted until it leaves the keep zone (hysteresis). */
		public boolean triggered;
		public int idleTicks;
		public boolean idle;
		/** Its chunk is unloaded: kept for a while, it may still be there. */
		public boolean unknown;
		public double x, z;
		public String reason = "";
		public Gauge.Decision decision;

		/** Does this vessel ask the bridge to be (or stay) open? */
		public boolean demands(DrawbridgeConfig cfg) {
			if (!requiresOpening || tooWide) {
				return false;
			}
			if (inPassage) {
				return true;
			}
			boolean idleIgnored = idleTicks > cfg.idleIgnoreSeconds * 20;
			return triggered && !idleIgnored;
		}
	}

	private static final String[] LEAF_NAMES = {"A", "B"};

	public final String id;
	public final RegistryKey<World> dimension;
	final Saved def;
	private BridgeTuning tuning;
	final BridgeCycle cycle = new BridgeCycle();
	private LeafShape[] shapes;
	private LeafFrame[] frames;
	private ChannelZones zones;
	private double waterY = Double.NaN;
	private double undersideY = Double.NaN;
	private List<double[]> barriers = List.of();
	private double[] bounds;
	private List<Long> chunks = List.of();
	final Map<UUID, Tracked> tracked = new LinkedHashMap<>();
	/** Scripted or API requests ("keep it open for me"): key -> expiry tick. */
	final Map<String, Long> requests = new HashMap<>();
	final Set<UUID> debugPlayers = new HashSet<>();
	final Set<UUID> previewPlayers = new HashSet<>();
	/** Needs saving. */
	boolean dirty;
	private long lastScan = -1000;
	/** After a restart: the passage counts as occupied until this tick (its entities may not be loaded yet). */
	private long holdUntil;
	private double cachedAngle = Double.NaN;
	private List<double[]> cachedBoxes = List.of();
	private final Map<UUID, Long> lastWarning = new HashMap<>();
	private int soundTicks;

	Drawbridge(Saved def) {
		this.def = def;
		this.id = def.id;
		this.dimension = RegistryKey.of(RegistryKeys.WORLD, Identifier.of(def.dimension));
		if (def.leaves == null || def.leaves.length != 2) {
			def.leaves = new LeafDef[] {new LeafDef("A"), new LeafDef("B")};
		}
		for (int i = 0; i < 2; i++) {
			if (def.leaves[i] == null) {
				def.leaves[i] = new LeafDef(LEAF_NAMES[i]);
			}
			def.leaves[i].name = LEAF_NAMES[i];
			if (def.leaves[i].blocks == null) {
				def.leaves[i].blocks = new ArrayList<>();
			}
		}
		this.tuning = new BridgeTuning(def.approach, def.hysteresis, def.openAngle, def.durationTicks, def.closeDelayTicks, def.warningTicks,
				def.margin, def.stopDistance).sanitized();
		BridgeCycle.State state = BridgeCycle.State.FERME;
		try {
			state = BridgeCycle.State.valueOf(def.state == null ? "FERME" : def.state);
		} catch (IllegalArgumentException ignored) {
			// an unknown saved state: closed
		}
		if (!def.converted) {
			state = BridgeCycle.State.FERME;
			def.blocksInWorld = true;
		} else if (!def.blocksInWorld && !state.leavesOut()) {
			state = BridgeCycle.State.ERREUR; // saved closed without its blocks: the leaves stay as boxes, the placement is retried
		} else if (def.blocksInWorld && state.leavesOut()) {
			state = BridgeCycle.State.FERME; // saved with the blocks in place: closed, whatever the saved state says
			def.angle = 0;
		}
		if (state == BridgeCycle.State.ATTENTE_SECURITE) {
			state = BridgeCycle.State.FERME;
		}
		cycle.restore(state, state == BridgeCycle.State.OUVERT ? tuning.openAngle() : Math.max(0, Math.min(tuning.openAngle(), def.angle)),
				def.blocksInWorld, def.suspended);
	}

	/** A new, empty bridge in a dimension. */
	static Drawbridge create(String id, RegistryKey<World> dimension, DrawbridgeConfig cfg) {
		Saved s = new Saved();
		s.id = id;
		s.dimension = dimension.getValue().toString();
		BridgeTuning t = cfg.defaults();
		s.approach = t.approach();
		s.hysteresis = t.hysteresis();
		s.openAngle = t.openAngle();
		s.durationTicks = t.durationTicks();
		s.closeDelayTicks = t.closeDelayTicks();
		s.warningTicks = t.warningTicks();
		s.margin = t.margin();
		s.stopDistance = t.stopDistance();
		return new Drawbridge(s);
	}

	// ------------------------------------------------------------------ accessors

	public BridgeTuning tuning() {
		return tuning;
	}

	public void setTuning(BridgeTuning t) {
		tuning = t.sanitized();
		def.approach = tuning.approach();
		def.hysteresis = tuning.hysteresis();
		def.openAngle = tuning.openAngle();
		def.durationTicks = tuning.durationTicks();
		def.closeDelayTicks = tuning.closeDelayTicks();
		def.warningTicks = tuning.warningTicks();
		def.margin = tuning.margin();
		def.stopDistance = tuning.stopDistance();
		if (zones != null) {
			zones = ChannelZones.of(zones.cx(), zones.cz(), zones.dx(), zones.dz(), zones.halfWidth(), zones.halfSpan(), tuning.approach(),
					tuning.hysteresis());
		}
		dirty = true;
	}

	public BridgeCycle cycle() {
		return cycle;
	}

	public void markDirty() {
		dirty = true;
	}

	public boolean chains() {
		return def.chains;
	}

	public double chainHeight() {
		return def.chainHeight;
	}

	/** Lifting chains on or off, and the height of their anchors over the hinge (0: automatic). */
	public void setChains(boolean on, double height) {
		def.chains = on;
		def.chainHeight = Double.isNaN(height) ? 0 : Math.max(0, Math.min(128, height));
		dirty = true;
	}

	public Set<UUID> previewPlayers() {
		return previewPlayers;
	}

	public Set<UUID> debugPlayers() {
		return debugPlayers;
	}

	public Map<String, Long> requests() {
		return requests;
	}

	public Map<UUID, Tracked> tracked() {
		return tracked;
	}

	/** The administrator sets a corner of a leaf's selection (only while the bridge is not converted). */
	public void setSelection(int leaf, boolean first, int x, int y, int z) {
		LeafDef l = def.leaves[leaf];
		if (first) {
			l.pos1 = new int[] {x, y, z};
		} else {
			l.pos2 = new int[] {x, y, z};
		}
		invalidate();
	}

	/** A point of a leaf's hinge line (null: automatic, on the outer bottom edge, or the top one with {@code top}). */
	public void setHinge(int leaf, @Nullable double[] point, boolean top) {
		def.leaves[leaf].hinge = point;
		def.leaves[leaf].hingeTop = top;
		invalidate();
	}

	public void setAxis(@Nullable double[] axis) {
		def.axis = axis;
		invalidate();
	}

	public void setCentre(@Nullable double[] centre) {
		def.centre = centre;
		invalidate();
	}

	public void setHalfWidth(@Nullable Double halfWidth) {
		def.halfWidth = halfWidth;
		invalidate();
	}

	public void setWaterY(@Nullable Double y) {
		def.waterY = y;
		invalidate();
	}

	/** The definition changed: the analysis must be run again. Never while converted (the commands refuse that). */
	private void invalidate() {
		shapes = null;
		frames = null;
		zones = null;
		dirty = true;
	}

	/** Measures one vessel against this bridge ({@code /pontlevis <id> tester}): envelope, verdict, position in the zones. */
	public List<String> measure(ServerWorld world, ShipEntity ship) {
		List<String> out = new ArrayList<>();
		if (!analysed()) {
			out.add("Le pont n'est pas analysé : lancez /pontlevis " + id + " verifier.");
			return out;
		}
		DrawbridgeConfig cfg = ConfigManager.drawbridges();
		Gauge.Envelope env = VesselScanner.envelopeOfShip(world, ship, zones, cfg);
		String label = ship.hasCustomName() ? ship.getCustomName().getString() : ship.shipType().frenchName();
		if (env == null) {
			out.add(label + " : ignoré par les ponts-levis (aéronef, ou profil « ignore »).");
			return out;
		}
		Gauge.Decision d = Gauge.decide(env, undersideY, waterY, tuning.margin(), zones.halfWidth());
		double dist = zones.distanceToDeck(env.x(), env.z(), env.reachAlong());
		out.add(String.format(Locale.ROOT, "%s : haut à %.2f au-dessus de l'eau (%s), %.1f de large vu des tours, portée %.1f vers le pont", label,
				d.vesselHeight(), env.detail(), d.widthNeeded(), env.reachAlong()));
		out.add(String.format(Locale.ROOT, "pont : hauteur libre %.2f, marge %.2f, chenal %.1f de large", d.freeHeight(), tuning.margin(), d.widthAvailable()));
		out.add("verdict : " + switch (d.verdict()) {
			case PASSE_DESSOUS -> "passe sous le pont fermé, aucune levée";
			case OUVERTURE_REQUISE -> "ouverture requise";
			case TROP_LARGE -> "trop large pour passer entre les tours, même pont ouvert (le navire attendra)";
		});
		out.add("  " + d.reason());
		out.add(String.format(Locale.ROOT, "position : à %.1f du bord du tablier, côté %s, %s%s", dist, zones.side(env.x(), env.z()) > 0 ? "+" : "-",
				!zones.inBand(env.x(), env.z(), env.halfAcross()) ? "hors du chenal navigable"
						: zones.inPassage(dist) ? "dans le passage" : zones.inApproach(dist) ? "dans la zone d'approche" : zones.inKeepZone(dist) ? "dans la zone d'hystérésis" : "hors des zones",
				tracked.containsKey(ship.getUuid()) ? " (pris en compte)" : ""));
		return out;
	}

	public boolean converted() {
		return def.converted;
	}

	public LeafDef leaf(int i) {
		return def.leaves[i];
	}

	/** The channel zones (null until the bridge has been analysed). */
	@Nullable
	public ChannelZones zones() {
		return zones;
	}

	public double waterY() {
		return waterY;
	}

	public double undersideY() {
		return undersideY;
	}

	@Nullable
	public LeafFrame frame(int i) {
		return frames == null ? null : frames[i];
	}

	@Nullable
	public LeafShape shape(int i) {
		return shapes == null ? null : shapes[i];
	}

	public boolean analysed() {
		return shapes != null && zones != null;
	}

	Saved toSaved() {
		def.suspended = cycle.suspended();
		def.state = cycle.state().name();
		def.angle = cycle.angle();
		def.blocksInWorld = cycle.blocksInWorld();
		return def;
	}

	// ------------------------------------------------------------------ analysis of the world

	/** What an analysis found: problems (fatal, the conversion is refused), warnings, and figures. */
	public record Report(List<String> problems, List<String> warnings, List<String> info) {
		public boolean ok() {
			return problems.isEmpty();
		}
	}

	/**
	 * Reads the leaves from the world without changing it: frames, shapes, channel, water, underside, swept volume
	 * against the fixed blocks. With {@code capture}, the block records are refreshed too (the conversion, and each
	 * opening); otherwise the shapes come from the world's blocks but the saved records stay.
	 */
	public Report analyse(ServerWorld world, boolean capture) {
		return analyse(world, capture, true);
	}

	/**
	 * {@link #analyse(ServerWorld, boolean)}; with {@code strict} false (an opening, the reload after a restart) a
	 * conflict of the swept volume with fixed blocks is only a warning: the leaves must exist whatever was built around.
	 */
	public Report analyse(ServerWorld world, boolean capture, boolean strict) {
		List<String> problems = new ArrayList<>(), warnings = new ArrayList<>(), info = new ArrayList<>();
		LeafDef a = def.leaves[0], b = def.leaves[1];
		for (LeafDef l : def.leaves) {
			if (!l.complete()) {
				problems.add("vantail " + l.name + " : sélection incomplète (pos1 et pos2)");
			}
		}
		if (!problems.isEmpty()) {
			return new Report(problems, warnings, info);
		}
		if (a.overlaps(b)) {
			problems.add("les sélections des vantaux A et B se chevauchent");
		}
		double[] ca = a.centre(), cb = b.centre();
		double sx = cb[0] - ca[0], sz = cb[2] - ca[2];
		double span = Math.hypot(sx, sz);
		if (span < 1) {
			problems.add("les deux vantaux sont au même endroit");
			return new Report(problems, warnings, info);
		}
		// the channel runs across the span; axis-aligned when the span nearly is
		double dx, dz;
		if (def.axis != null && Math.hypot(def.axis[0], def.axis[1]) > 1e-6) {
			dx = def.axis[0];
			dz = def.axis[1];
		} else if (Math.abs(sx) / span > 0.95) {
			dx = 0;
			dz = 1;
		} else if (Math.abs(sz) / span > 0.95) {
			dx = 1;
			dz = 0;
		} else {
			dx = -sz / span;
			dz = sx / span;
		}
		double len = Math.hypot(dx, dz);
		dx /= len;
		dz /= len;
		if (Math.abs(dx * sx + dz * sz) / span > 0.7) {
			warnings.add("l'axe du chenal est presque parallèle à la travée : vérifiez /pontlevis " + id + " axe");
		}
		LeafFrame[] fr = new LeafFrame[2];
		LeafShape[] sh = new LeafShape[2];
		List<List<BlockRecord>> captured = new ArrayList<>();
		for (int i = 0; i < 2; i++) {
			LeafDef leaf = def.leaves[i];
			double[] c = leaf.centre(), o = def.leaves[1 - i].centre();
			double inX = o[0] - c[0], inZ = o[2] - c[2];
			// the blocks first (their boxes do not depend on the hinge), the hinge then, from the deck's own layer
			List<BlockRecord> records = new ArrayList<>();
			List<double[]> boxes = new ArrayList<>();
			int[] mn = leaf.min(), mx = leaf.max();
			BlockPos.Mutable pos = new BlockPos.Mutable();
			int volume = (mx[0] - mn[0] + 1) * (mx[1] - mn[1] + 1) * (mx[2] - mn[2] + 1);
			if (volume > 20000) {
				problems.add("vantail " + leaf.name + " : sélection trop grande (" + volume + " blocs, 20000 au plus)");
				continue;
			}
			boolean fromWorld = capture || !def.converted || cycle.blocksInWorld();
			if (fromWorld) {
				for (int x = mn[0]; x <= mx[0]; x++) {
					for (int y = mn[1]; y <= mx[1]; y++) {
						for (int z = mn[2]; z <= mx[2]; z++) {
							pos.set(x, y, z);
							if (!world.isChunkLoaded(x >> 4, z >> 4)) {
								problems.add("vantail " + leaf.name + " : tronçon non chargé en " + x + " " + z);
								return new Report(problems, warnings, info);
							}
							BlockState state = world.getBlockState(pos);
							if (state.isAir() || !state.getFluidState().isEmpty() && state.getBlock() == Blocks.WATER || state.getBlock() == Blocks.LAVA) {
								continue;
							}
							String nbt = null;
							if (state.hasBlockEntity()) {
								BlockEntity be = world.getBlockEntity(pos);
								if (be != null) {
									nbt = be.createNbtWithIdentifyingData(world.getRegistryManager()).toString();
								}
							}
							records.add(new BlockRecord(x, y, z, BlockArgumentParser.stringifyBlockState(state), nbt));
							addBoxes(boxes, state, pos, world);
						}
					}
				}
			} else {
				for (BlockRecord r : leaf.blocks) {
					BlockState state = parseState(r.state);
					if (state != null) {
						addBoxes(boxes, state, r.pos(), world);
					}
				}
				records.addAll(leaf.blocks);
			}
			if (records.isEmpty()) {
				problems.add("vantail " + leaf.name + " : aucun bloc dans la sélection");
				continue;
			}
			captured.add(records);
			double[] hinge = leaf.hinge;
			LeafFrame probe = LeafFrame.of(c[0], c[1], c[2], dx, dz, inX, inZ);
			if (hinge == null) {
				// the outer face of the selection (the side of the fixed structure), at the bottom (or top) of the deck's own
				// layer: the most populated horizontal layer of blocks, under the railings and over whatever hangs beneath
				double bMin = Double.MAX_VALUE;
				for (double x : new double[] {mn[0], mx[0] + 1}) {
					for (double z : new double[] {mn[2], mx[2] + 1}) {
						bMin = Math.min(bMin, probe.toLocal(x, 0, z)[1]);
					}
				}
				int deckY = deckLayer(records);
				double hy = leaf.hingeTop ? deckY + 1 : deckY;
				hinge = new double[] {c[0] + probe.vx() * bMin, hy, c[2] + probe.vz() * bMin};
			}
			fr[i] = LeafFrame.of(hinge[0], hinge[1], hinge[2], dx, dz, inX, inZ);
			sh[i] = new LeafShape(fr[i], boxes);
			info.add(String.format(Locale.ROOT, "vantail %s : %d blocs, %d boîtes solides, longueur %.1f, largeur %.1f, épaisseur %.1f, charnière %.1f %.1f %.1f (%s)",
					leaf.name, records.size(), boxes.size(), sh[i].maxB() - Math.min(0, sh[i].minB()), sh[i].maxA() - sh[i].minA(), sh[i].maxC() - sh[i].minC(),
					hinge[0], hinge[1], hinge[2], leaf.hinge == null ? (leaf.hingeTop ? "automatique, bord haut du plancher" : "automatique, bord bas du plancher") : "fixée"));
			if (sh[i].minB() < -0.5) {
				warnings.add(String.format(Locale.ROOT, "vantail %s : des blocs dépassent de %.1f derrière la charnière (ils balaieront le côté rive)", leaf.name,
						-sh[i].minB()));
			}
		}
		if (!problems.isEmpty()) {
			return new Report(problems, warnings, info);
		}
		// the channel
		double cx = def.centre != null ? def.centre[0] : (ca[0] + cb[0]) / 2;
		double cz = def.centre != null ? def.centre[2] : (ca[2] + cb[2]) / 2;
		double halfSpan = 0.5;
		for (LeafShape s : sh) {
			halfSpan = Math.max(halfSpan, (s.maxA() - s.minA()) / 2);
		}
		double hingeGap = Math.abs((fr[1].hx() - fr[0].hx()) * fr[0].vx() + (fr[1].hz() - fr[0].hz()) * fr[0].vz());
		double halfWidth = def.halfWidth != null ? def.halfWidth : hingeGap / 2;
		if (halfWidth < 0.5) {
			problems.add("largeur navigable nulle : indiquez /pontlevis " + id + " chenal largeur <blocs>");
			return new Report(problems, warnings, info);
		}
		double water = def.waterY != null ? def.waterY : findWater(world, cx, cz, Math.min(fr[0].hy(), fr[1].hy()) + 1);
		if (Double.isNaN(water)) {
			problems.add("pas d'eau trouvée sous le centre du pont : indiquez /pontlevis " + id + " eau <y>");
			return new Report(problems, warnings, info);
		}
		ChannelZones zn = ChannelZones.of(cx, cz, dx, dz, halfWidth, halfSpan, tuning.approach(), tuning.hysteresis());
		double under = Double.NaN;
		for (LeafShape s : sh) {
			double u = s.undersideOver(zn::across, halfWidth);
			if (!Double.isNaN(u) && !(u >= under)) {
				under = u;
			}
		}
		if (Double.isNaN(under)) {
			problems.add("aucun bloc des vantaux au-dessus du chenal : vérifiez les sélections et la largeur du chenal");
			return new Report(problems, warnings, info);
		}
		if (under <= water) {
			problems.add(String.format(Locale.ROOT, "le dessous du tablier (%.2f) est sous l'eau (%.2f) : vérifiez /pontlevis %s eau", under, water, id));
			return new Report(problems, warnings, info);
		}
		info.add(String.format(Locale.ROOT, "chenal : axe (%.2f, %.2f), centre %.1f %.1f, largeur navigable %.1f (écart des charnières %.1f), travée %.1f de large",
				dx, dz, cx, cz, 2 * halfWidth, hingeGap, 2 * halfSpan));
		info.add(String.format(Locale.ROOT, "eau à %.2f, dessous du tablier à %.2f : hauteur libre %.2f (marge %.2f : un navire de plus de %.2f ouvre le pont)",
				water, under, under - water, tuning.margin(), under - water - tuning.margin()));
		if (under - water < 3) {
			warnings.add("hauteur libre inférieure à 3 blocs : le pilote automatique des navires ne considère pas le passage comme navigable sous le pont fermé");
		}
		// the swept volume against the fixed blocks (towers, high walkways)
		List<String> hits = new ArrayList<>();
		double safeAngle = sweptAgainstBlocks(world, sh, hits);
		if (!hits.isEmpty()) {
			String msg = String.format(Locale.ROOT, "les vantaux heurteraient des blocs fixes en montant (angle sûr : %.0f°) : %s", safeAngle, String.join(", ", hits));
			if (strict) {
				problems.add(msg);
			} else {
				warnings.add(msg);
			}
		} else {
			info.add(String.format(Locale.ROOT, "volume balayé jusqu'à %.0f° : libre de tout bloc fixe", tuning.openAngle()));
		}
		if (!problems.isEmpty()) {
			return new Report(problems, warnings, info);
		}
		// adopt the analysis
		frames = fr;
		shapes = sh;
		zones = zn;
		waterY = water;
		undersideY = under;
		boolean fromWorld = capture || !def.converted || cycle.blocksInWorld();
		if (fromWorld) {
			for (int i = 0; i < 2; i++) {
				def.leaves[i].blocks = captured.get(i);
			}
			dirty = true;
		}
		barriers = computeBarriers();
		bounds = computeBounds();
		chunks = computeChunks();
		cachedAngle = Double.NaN;
		return new Report(problems, warnings, info);
	}

	/** The y of the most populated horizontal layer of a leaf's blocks: its floor (railings above and lanterns below are thinner). */
	static int deckLayer(List<BlockRecord> records) {
		Map<Integer, Integer> count = new HashMap<>();
		for (BlockRecord r : records) {
			count.merge(r.y, 1, Integer::sum);
		}
		int best = records.isEmpty() ? 0 : records.get(0).y, n = -1;
		for (Map.Entry<Integer, Integer> e : count.entrySet()) {
			if (e.getValue() > n || (e.getValue() == n && e.getKey() < best)) {
				best = e.getKey();
				n = e.getValue();
			}
		}
		return best;
	}

	private static void addBoxes(List<double[]> boxes, BlockState state, BlockPos pos, World world) {
		VoxelShape shape = state.getCollisionShape(world, pos);
		if (shape.isEmpty()) {
			return;
		}
		for (Box b : shape.getBoundingBoxes()) {
			boxes.add(new double[] {pos.getX() + b.minX, pos.getY() + b.minY, pos.getZ() + b.minZ, pos.getX() + b.maxX, pos.getY() + b.maxY, pos.getZ() + b.maxZ});
		}
	}

	/** The water surface under a point (scanning down from {@code fromY}), or NaN. */
	static double findWater(ServerWorld world, double x, double z, double fromY) {
		int bx = (int) Math.floor(x), bz = (int) Math.floor(z);
		if (!world.isChunkLoaded(bx >> 4, bz >> 4)) {
			return Double.NaN;
		}
		BlockPos.Mutable pos = new BlockPos.Mutable();
		for (int y = (int) Math.floor(fromY); y >= Math.max(world.getBottomY(), fromY - 24); y--) {
			pos.set(bx, y, bz);
			FluidState f = world.getFluidState(pos);
			if (f.isIn(FluidTags.WATER)) {
				return y + f.getHeight(world, pos);
			}
		}
		return Double.NaN;
	}

	/**
	 * Where the rising leaves would meet fixed blocks: every block position covered by the swept boxes, outside the
	 * selections, with a collision shape, in front of the hinge. The blocks behind the hinge (the abutment or the
	 * tower the deck rests against) are not counted: the deck's thickness and its railings turn into them as they
	 * would in a real bascule bridge, and a collision box buried in a solid block changes nothing. Returns the
	 * largest clear angle; fills {@code hits} with the first few.
	 */
	private double sweptAgainstBlocks(ServerWorld world, LeafShape[] sh, List<String> hits) {
		double safe = tuning.openAngle();
		Set<Long> seen = new HashSet<>();
		BlockPos.Mutable pos = new BlockPos.Mutable();
		for (double angle = LeafShape.SWEEP_STEP; angle <= tuning.openAngle() + 1e-9; angle += LeafShape.SWEEP_STEP) {
			boolean hit = false;
			for (LeafShape s : sh) {
				for (double[] w : s.worldBoxes(Math.min(angle, tuning.openAngle()))) {
					int x0 = (int) Math.floor(w[0] + 1e-6), x1 = (int) Math.ceil(w[3] - 1e-6) - 1;
					int y0 = (int) Math.floor(w[1] + 1e-6), y1 = (int) Math.ceil(w[4] - 1e-6) - 1;
					int z0 = (int) Math.floor(w[2] + 1e-6), z1 = (int) Math.ceil(w[5] - 1e-6) - 1;
					for (int x = x0; x <= x1; x++) {
						for (int y = y0; y <= y1; y++) {
							for (int z = z0; z <= z1; z++) {
								if (def.leaves[0].contains(x, y, z) || def.leaves[1].contains(x, y, z)) {
									continue;
								}
								if (s.frame().toLocal(x + 0.5, y + 0.5, z + 0.5)[1] < 0) {
									continue; // behind the hinge: the abutment the leaf turns into
								}
								long key = BlockPos.asLong(x, y, z);
								if (!seen.add(key)) {
									continue;
								}
								pos.set(x, y, z);
								if (!world.isChunkLoaded(x >> 4, z >> 4)) {
									continue;
								}
								BlockState state = world.getBlockState(pos);
								if (state.isAir() || state.getCollisionShape(world, pos).isEmpty()) {
									continue;
								}
								hit = true;
								if (hits.size() < 8) {
									hits.add(String.format(Locale.ROOT, "%d %d %d (%s) à %.0f°", x, y, z,
											Registries.BLOCK.getId(state.getBlock()).getPath(), angle));
								}
							}
						}
					}
				}
			}
			if (hit && safe >= angle) {
				safe = angle - LeafShape.SWEEP_STEP;
			}
		}
		return Math.max(0, safe);
	}

	/** The barriers: a thin wall across each leaf's outer end (the shore side), see {@link LeafShape#barrierBox}. */
	private List<double[]> computeBarriers() {
		List<double[]> out = new ArrayList<>();
		for (LeafShape s : shapes) {
			out.add(s.barrierBox());
		}
		return out;
	}

	private double[] computeBounds() {
		double[] r = {Double.MAX_VALUE, Double.MAX_VALUE, Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE};
		for (LeafShape s : shapes) {
			double[] b = s.sweptBounds(0, 90);
			for (int k = 0; k < 3; k++) {
				r[k] = Math.min(r[k], b[k]);
				r[k + 3] = Math.max(r[k + 3], b[k + 3]);
			}
		}
		for (double[] b : barriers) {
			for (int k = 0; k < 3; k++) {
				r[k] = Math.min(r[k], b[k]);
				r[k + 3] = Math.max(r[k + 3], b[k + 3]);
			}
		}
		return r;
	}

	private List<Long> computeChunks() {
		List<Long> out = new ArrayList<>();
		int cx0 = ((int) Math.floor(bounds[0])) >> 4, cx1 = ((int) Math.floor(bounds[3])) >> 4;
		int cz0 = ((int) Math.floor(bounds[2])) >> 4, cz1 = ((int) Math.floor(bounds[5])) >> 4;
		for (int cx = cx0; cx <= cx1; cx++) {
			for (int cz = cz0; cz <= cz1; cz++) {
				out.add(ChunkPos.toLong(cx, cz));
			}
		}
		return out;
	}

	// ------------------------------------------------------------------ conversion, restoration

	/** Converts the deck: captures its blocks and starts the cycle, closed (the blocks stay). */
	public Report convert(ServerWorld world) {
		Report r = analyse(world, true);
		if (!r.ok()) {
			return r;
		}
		def.converted = true;
		cycle.restore(BridgeCycle.State.FERME, 0, true, cycle.suspended());
		tracked.clear();
		DrawbridgeCollisions.add(world, this);
		dirty = true;
		Drawbridges.sync(this, world);
		return r;
	}

	/**
	 * Puts the deck's blocks back where they were (if the leaves are out) and stops the cycle: the bridge is defined
	 * but no longer converted. Only the captured positions are touched.
	 */
	public int restore(ServerWorld world) {
		int placed = 0;
		if (!cycle.blocksInWorld()) {
			placed = placeBlocks(world, true);
		}
		def.converted = false;
		cycle.restore(BridgeCycle.State.FERME, 0, true, cycle.suspended());
		tracked.clear();
		requests.clear();
		DrawbridgeCollisions.remove(world, this);
		dirty = true;
		Drawbridges.sync(this, world);
		return placed;
	}

	/** Removes the captured blocks from the world (the leaves take over). */
	int removeBlocks(ServerWorld world) {
		int n = 0;
		for (LeafDef leaf : def.leaves) {
			for (BlockRecord r : leaf.blocks) {
				BlockPos pos = r.pos();
				if (world.getBlockState(pos).hasBlockEntity()) {
					world.removeBlockEntity(pos); // so that a container does not spill its items
				}
				if (world.setBlockState(pos, Blocks.AIR.getDefaultState(), Block.NOTIFY_LISTENERS | Block.FORCE_STATE | Block.SKIP_DROPS | Block.MOVED)) {
					n++;
				}
			}
		}
		return n;
	}

	/**
	 * Puts the captured blocks back, with their block entities' data; with {@code force}, over whatever stands there,
	 * else only where the place is free (air or replaceable).
	 */
	int placeBlocks(ServerWorld world, boolean force) {
		int n = 0;
		for (LeafDef leaf : def.leaves) {
			for (BlockRecord r : leaf.blocks) {
				BlockState state = parseState(r.state);
				if (state == null) {
					MedievalShips.LOGGER.warn("Drawbridge {}: unknown block state {} at {} {} {}", id, r.state, r.x, r.y, r.z);
					continue;
				}
				BlockPos pos = r.pos();
				BlockState current = world.getBlockState(pos);
				if (!force && !(current.isAir() || current.isReplaceable())) {
					continue;
				}
				if (!world.setBlockState(pos, state, Block.NOTIFY_LISTENERS | Block.FORCE_STATE)) {
					continue;
				}
				n++;
				if (r.nbt != null) {
					BlockEntity be = world.getBlockEntity(pos);
					if (be != null) {
						try {
							NbtCompound nbt = StringNbtReader.readCompound(r.nbt);
							be.read(NbtReadView.create(ErrorReporter.EMPTY, world.getRegistryManager(), nbt));
							be.markDirty();
							world.updateListeners(pos, state, state, Block.NOTIFY_LISTENERS);
						} catch (Exception e) {
							MedievalShips.LOGGER.warn("Drawbridge {}: block entity data of {} {} {} not restored: {}", id, r.x, r.y, r.z, e.toString());
						}
					}
				}
			}
		}
		return n;
	}

	@Nullable
	static BlockState parseState(String s) {
		try {
			return BlockArgumentParser.block(Registries.BLOCK, s, false).blockState();
		} catch (Exception e) {
			return null;
		}
	}

	/** Are the places of the captured blocks free (air or replaceable)? */
	boolean footprintFree(ServerWorld world) {
		for (LeafDef leaf : def.leaves) {
			for (BlockRecord r : leaf.blocks) {
				BlockState s = world.getBlockState(r.pos());
				if (!(s.isAir() || s.isReplaceable())) {
					return false;
				}
			}
		}
		return true;
	}

	/** The first block occupying the footprint, for the diagnostics; null if free. */
	@Nullable
	String footprintBlocker(ServerWorld world) {
		for (LeafDef leaf : def.leaves) {
			for (BlockRecord r : leaf.blocks) {
				BlockState s = world.getBlockState(r.pos());
				if (!(s.isAir() || s.isReplaceable())) {
					return Registries.BLOCK.getId(s.getBlock()).getPath() + " en " + r.x + " " + r.y + " " + r.z;
				}
			}
		}
		return null;
	}

	boolean chunksLoaded(ServerWorld world) {
		for (long key : chunks) {
			if (!world.isChunkLoaded(ChunkPos.getPackedX(key), ChunkPos.getPackedZ(key))) {
				return false;
			}
		}
		return true;
	}

	// ------------------------------------------------------------------ safety checks

	/** Entities that must never be moved by the leaves: living beings (not spectators) and vehicles (boats, minecarts). */
	private static boolean matters(Entity e) {
		return !e.isRemoved() && !(e instanceof ShipEntity) && !e.isSpectator() && (e instanceof LivingEntity || e instanceof VehicleEntity);
	}

	/** Who stands on the deck or straddles its ends (the leaves closed): their names, empty if nobody. */
	List<String> onDeck(ServerWorld world) {
		List<String> out = new ArrayList<>();
		for (LeafShape s : shapes) {
			double[] b = s.bounds(0);
			Box area = new Box(b[0] - 0.5, b[1] - 0.2, b[2] - 0.5, b[3] + 0.5, b[4] + 2.5, b[5] + 0.5);
			for (Entity e : world.getOtherEntities(null, area, Drawbridge::matters)) {
				String name = e.getName().getString();
				if (!out.contains(name)) {
					out.add(name);
				}
			}
		}
		return out;
	}

	/**
	 * What is in the volume the leaves would sweep between two angles: living beings and vehicles by their boxes, the
	 * mod's vessels by their real hulls, masts and superstructures (and their occupants); empty if clear.
	 */
	List<String> inSweep(ServerWorld world, double from, double to) {
		List<String> out = new ArrayList<>();
		for (LeafShape s : shapes) {
			List<double[]> swept = s.sweptBoxes(from, to);
			double[] b = s.sweptBounds(from, to);
			Box area = new Box(b[0], b[1], b[2], b[3], b[4], b[5]);
			for (Entity e : world.getOtherEntities(null, area, Drawbridge::matters)) {
				Box eb = e.getBoundingBox();
				if (LeafShape.intersectsAny(swept, eb.minX, eb.minY, eb.minZ, eb.maxX, eb.maxY, eb.maxZ)) {
					String name = e.getName().getString();
					if (!out.contains(name)) {
						out.add(name);
					}
				}
			}
			for (ShipEntity ship : ShipTracker.ships(world)) {
				if (ship.isRemoved() || ship.geometry().flying()) {
					continue;
				}
				double r = ship.geometry().boundingRadius();
				if (!area.intersects(ship.getBoundingBox().expand(r, 64, r))) {
					continue;
				}
				boolean[] hit = {false};
				ship.geometry().collectBoxes(ship.pose(), ship.interiorState(), ship.gangplankWallGap(), b[0], b[1], b[2], b[3], b[4], b[5],
						(x0, y0, z0, x1, y1, z1) -> {
							if (!hit[0] && LeafShape.intersectsAny(swept, x0, y0, z0, x1, y1, z1)) {
								hit[0] = true;
							}
						});
				if (hit[0]) {
					String name = ship.hasCustomName() ? ship.getCustomName().getString() : ship.shipType().frenchName();
					if (!out.contains(name)) {
						out.add(name);
					}
				}
			}
		}
		return out;
	}

	// ------------------------------------------------------------------ the tick

	/** One server tick of this bridge (only once converted and analysed). */
	void tick(ServerWorld world, long now) {
		if (!def.converted) {
			return;
		}
		if (!analysed()) {
			// after a restart: rebuild the shapes from the saved records (the world's blocks may be gone)
			if (!chunksLoadedForAnalysis(world)) {
				return;
			}
			Report r = analyse(world, false, false);
			if (!r.ok()) {
				MedievalShips.LOGGER.warn("Drawbridge {}: cannot be analysed after loading: {}", id, r.problems());
				int placed = cycle.blocksInWorld() ? 0 : placeBlocks(world, false);
				MedievalShips.LOGGER.warn("Drawbridge {}: taken out of service, {} block(s) of its deck put back", id, placed);
				def.converted = false;
				cycle.restore(BridgeCycle.State.FERME, 0, true, cycle.suspended());
				dirty = true;
				tellAdmins(world, Text.literal("[Pont-levis " + id + "] hors service après le chargement (" + String.join(" ; ", r.problems())
						+ ") : ses blocs ont été remis, vérifiez-le (/pontlevis " + id + " verifier).").formatted(Formatting.RED));
				return;
			}
			for (String w : r.warnings()) {
				MedievalShips.LOGGER.warn("Drawbridge {}: {}", id, w);
			}
			DrawbridgeCollisions.add(world, this);
			holdUntil = now + 100;
			Drawbridges.sync(this, world);
		}
		DrawbridgeConfig cfg = ConfigManager.drawbridges();
		boolean loaded = chunksLoaded(world);
		if (loaded && now - lastScan >= cfg.detectionIntervalTicks) {
			lastScan = now;
			scan(world, now, cfg);
		}
		// the inputs the cycle needs in its current state (the entity queries only when they matter)
		boolean demand = false, passage = false;
		for (Tracked t : tracked.values()) {
			if (t.demands(cfg)) {
				demand = true;
				if (t.inPassage) {
					passage = true;
				}
			}
		}
		requests.values().removeIf(expiry -> expiry < now);
		if (!requests.isEmpty()) {
			demand = true;
		}
		if (now < holdUntil && cycle.state().leavesOut()) {
			passage = true; // just loaded: the vessels of the passage may not be there yet
		}
		BridgeCycle.State st = cycle.state();
		boolean deckClear = true, sweptClear = true, footprint = true;
		List<String> blockers = List.of();
		if (loaded) {
			if (st == BridgeCycle.State.ATTENTE_SECURITE && cycle.ticksInState() >= tuning.warningTicks() - 1) {
				blockers = onDeck(world);
				deckClear = blockers.isEmpty();
				if (deckClear) {
					blockers = inSweep(world, 0, tuning.openAngle());
					sweptClear = blockers.isEmpty();
				}
			} else if (st == BridgeCycle.State.FERMETURE || (st == BridgeCycle.State.OUVERT && !demand && !passage)) {
				blockers = inSweep(world, 0, cycle.angle());
				sweptClear = blockers.isEmpty();
			}
			if (st == BridgeCycle.State.FERMETURE || st == BridgeCycle.State.ERREUR) {
				footprint = footprintFree(world);
			}
		}
		final List<String> inTheWay = blockers;
		BridgeCycle.Input in = new BridgeCycle.Input(demand, passage, deckClear, sweptClear, footprint, loaded);
		BridgeCycle.State before = cycle.state();
		double angleBefore = cycle.angle();
		cycle.tick(in, tuning, new BridgeCycle.Listener() {
			@Override
			public void safetyWait() {
				sound(world, SoundEvents.BLOCK_BELL_USE, 0.7f, 0.8f);
				tellAround(world, Text.literal("Pont-levis « " + id + " » : il va se lever, quittez le tablier.").formatted(Formatting.GOLD), true);
			}

			@Override
			public void opening(boolean removeBlocks) {
				if (removeBlocks) {
					Report r = analyse(world, true, false); // the deck as it is now (an added lantern, a repaired plank)
					if (!r.ok()) {
						MedievalShips.LOGGER.warn("Drawbridge {}: the deck could not be re-read before opening: {} (the saved blocks are used)", id, r.problems());
					}
					for (String w : r.warnings()) {
						tellAdmins(world, Text.literal("[Pont-levis " + id + "] " + w).formatted(Formatting.YELLOW));
					}
					removeBlocks(world);
				}
				sound(world, SoundEvents.BLOCK_IRON_TRAPDOOR_OPEN, 0.8f, 0.5f);
				sound(world, SoundEvents.BLOCK_CHAIN_PLACE, 0.9f, 0.6f);
			}

			@Override
			public void opened() {
				sound(world, SoundEvents.BLOCK_CHAIN_PLACE, 0.8f, 0.5f);
				sound(world, SoundEvents.BLOCK_WOOD_PLACE, 0.8f, 0.6f);
				dust(world, 3, 0.05);
				tellPilots(world, Text.literal("Pont-levis « " + id + " » ouvert : passage libre.").formatted(Formatting.AQUA));
			}

			@Override
			public void closing() {
				sound(world, SoundEvents.BLOCK_LEVER_CLICK, 0.6f, 0.7f);
				sound(world, SoundEvents.BLOCK_CHAIN_PLACE, 0.9f, 0.55f);
				tellAround(world, Text.literal("Pont-levis « " + id + " » : les vantaux redescendent.").formatted(Formatting.GOLD), true);
			}

			@Override
			public void closed() {
				placeBlocks(world, false);
				sound(world, SoundEvents.BLOCK_WOOD_PLACE, 1.0f, 0.6f);
				sound(world, SoundEvents.BLOCK_IRON_DOOR_CLOSE, 0.7f, 0.5f);
				dust(world, 6, 0.08);
			}

			@Override
			public void reversed() {
				sound(world, SoundEvents.BLOCK_CHAIN_HIT, 0.9f, 0.6f);
				tellAround(world, Text.literal("Pont-levis « " + id + " » : fermeture interrompue, les vantaux remontent.").formatted(Formatting.YELLOW), true);
			}

			@Override
			public void blocked(String why) {
				String who = inTheWay.isEmpty() ? "" : " (" + String.join(", ", inTheWay) + ")";
				if (why.contains("occupé par un bloc")) {
					String b = footprintBlocker(world);
					who = b == null ? "" : " (" + b + ")";
				}
				tellAround(world, Text.literal("Pont-levis « " + id + " » : en attente, " + why + who + ".").formatted(Formatting.YELLOW), true);
				tellAdmins(world, Text.literal("[Pont-levis " + id + "] en attente : " + why + who).formatted(Formatting.YELLOW));
			}

			@Override
			public void error(String why) {
				String b = footprintBlocker(world);
				tellAdmins(world, Text.literal("[Pont-levis " + id + "] erreur : " + why + (b == null ? "" : " (" + b + ")")).formatted(Formatting.RED));
			}

			@Override
			public void recovered() {
				tellAdmins(world, Text.literal("[Pont-levis " + id + "] l'erreur est levée.").formatted(Formatting.GREEN));
			}
		});
		if (cycle.state() != before) {
			dirty = true;
			Drawbridges.sync(this, world);
		} else if (cycle.state().moving() && now % 20 == 0) {
			dirty = true;
		}
		if (cycle.angle() != angleBefore) {
			cachedAngle = Double.NaN;
		}
		if (cycle.state().moving()) {
			motionSounds(world);
		}
		if (cycle.state() != BridgeCycle.State.FERME && now % 20 == 0) {
			for (long key : chunks) {
				world.getChunkManager().addTicket(ChunkTicketType.PORTAL, new ChunkPos(ChunkPos.getPackedX(key), ChunkPos.getPackedZ(key)), 2);
			}
		}
		if (!debugPlayers.isEmpty() && now % 20 == 0) {
			debugOutput(world, cfg);
		}
	}

	/** Are the chunks of the selections loaded (needed to rebuild the shapes after a restart)? */
	private boolean chunksLoadedForAnalysis(ServerWorld world) {
		for (LeafDef leaf : def.leaves) {
			if (!leaf.complete()) {
				return false;
			}
			int[] mn = leaf.min(), mx = leaf.max();
			for (int cx = mn[0] >> 4; cx <= mx[0] >> 4; cx++) {
				for (int cz = mn[2] >> 4; cz <= mx[2] >> 4; cz++) {
					if (!world.isChunkLoaded(cx, cz)) {
						return false;
					}
				}
			}
		}
		return true;
	}

	private void scan(ServerWorld world, long now, DrawbridgeConfig cfg) {
		Set<UUID> seen = new HashSet<>();
		for (VesselScanner.Observation o : VesselScanner.scan(world, this, cfg)) {
			UUID uuid = o.entity().getUuid();
			seen.add(uuid);
			Tracked t = tracked.computeIfAbsent(uuid, u -> new Tracked());
			t.label = o.envelope().label();
			t.lastSeen = now;
			t.distance = o.distance();
			t.side = o.side();
			t.requiresOpening = o.decision().verdict() == Gauge.Verdict.OUVERTURE_REQUISE;
			t.tooWide = o.decision().verdict() == Gauge.Verdict.TROP_LARGE;
			t.inPassage = o.inPassage();
			t.inApproach = o.inApproach();
			t.approaching = o.approaching();
			t.triggered = t.triggered || o.inApproach();
			t.idle = o.idle();
			t.idleTicks = o.idle() ? t.idleTicks + cfg.detectionIntervalTicks : 0;
			t.unknown = false;
			t.x = o.envelope().x();
			t.z = o.envelope().z();
			t.decision = o.decision();
			t.reason = o.decision().reason();
			if (t.tooWide && o.ship() != null && o.approaching() && o.distance() < tuning.approach() && now % 100 == 0) {
				warnPilot(world, o.ship(), now, Text.literal(String.format(Locale.ROOT,
						"Pont-levis « %s » : %s est trop large pour passer entre les tours (%.1f > %.1f blocs).", id, t.label,
						o.decision().widthNeeded(), o.decision().widthAvailable())).formatted(Formatting.RED));
			}
		}
		long grace = (long) (cfg.unloadedGraceSeconds * 20);
		Iterator<Map.Entry<UUID, Tracked>> it = tracked.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<UUID, Tracked> e = it.next();
			if (seen.contains(e.getKey())) {
				continue;
			}
			Tracked t = e.getValue();
			Entity entity = world.getEntity(e.getKey());
			if (entity != null) {
				it.remove(); // loaded, but out of the zones now
				continue;
			}
			if (world.isChunkLoaded(((int) Math.floor(t.x)) >> 4, ((int) Math.floor(t.z)) >> 4)) {
				it.remove(); // its chunk is loaded and it is not there: gone
				continue;
			}
			t.unknown = true; // unloaded: it may still be there
			if (!t.inPassage && now - t.lastSeen > grace) {
				it.remove();
			}
		}
	}

	// ------------------------------------------------------------------ the autopilot gate

	/**
	 * Holds an autopilot vessel that needs the opening (or cannot pass) before the deck while the bridge is not open:
	 * its speed is limited so that it stops {@code stopDistance} blocks before the deck edge, and its autopilot is
	 * told it waits on purpose. A player at the helm stays free and is warned.
	 */
	ShipPhysics.Controls gate(ShipEntity ship, ShipPose pose, ShipPhysics.Controls controls, long now) {
		Tracked t = tracked.get(ship.getUuid());
		if (t == null || !(t.requiresOpening || t.tooWide) || t.inPassage || !t.approaching) {
			return controls;
		}
		if (cycle.state() == BridgeCycle.State.OUVERT && !t.tooWide) {
			return controls;
		}
		double room = t.distance - tuning.stopDistance();
		double vmax = room <= 0.25 ? 0 : Math.sqrt(2 * ship.config().braking * 0.8 * room);
		if (ship.isAutopilotEnabled()) {
			if (vmax < 0.3) {
				ship.autopilot().externalHold();
			}
			if (!Double.isNaN(controls.targetSpeed()) && controls.targetSpeed() > vmax) {
				return new ShipPhysics.Controls(Math.max(0, vmax), controls.helmTarget());
			}
			return controls;
		}
		if (room < 12) {
			warnPilot(ship.getEntityWorld() instanceof ServerWorld sw ? sw : null, ship, now, Text.literal(t.tooWide
					? "Pont-levis « " + id + " » : trop large pour passer entre les tours."
					: "Pont-levis « " + id + " » fermé devant vous : " + (cycle.state() == BridgeCycle.State.FERME ? "il va s'ouvrir" : cycle.state().french())
							+ ", ralentissez.").formatted(Formatting.RED));
		}
		return controls;
	}

	private void warnPilot(@Nullable ServerWorld world, ShipEntity ship, long now, Text text) {
		Entity pilot = ship.passengerInSeat(ShipGeometry.PILOT_SEAT);
		if (!(pilot instanceof ServerPlayerEntity p)) {
			return;
		}
		Long last = lastWarning.get(ship.getUuid());
		if (last != null && now - last < 60) {
			return;
		}
		lastWarning.put(ship.getUuid(), now);
		p.sendMessage(text, true);
	}

	// ------------------------------------------------------------------ messages and sounds

	private double[] soundSpot() {
		if (frames == null) {
			return new double[] {def.leaves[0].complete() ? def.leaves[0].centre()[0] : 0, 64, def.leaves[0].complete() ? def.leaves[0].centre()[2] : 0};
		}
		return new double[] {(frames[0].hx() + frames[1].hx()) / 2, (frames[0].hy() + frames[1].hy()) / 2 + 1, (frames[0].hz() + frames[1].hz()) / 2};
	}

	private void sound(ServerWorld world, SoundEvent sound, float volume, float pitch) {
		float v = (float) (volume * ConfigManager.drawbridges().soundVolume);
		if (v <= 0) {
			return;
		}
		if (frames != null) {
			for (LeafFrame f : frames) {
				world.playSound(null, f.hx(), f.hy() + 1, f.hz(), sound, SoundCategory.BLOCKS, v, pitch);
			}
		} else {
			double[] s = soundSpot();
			world.playSound(null, s[0], s[1], s[2], sound, SoundCategory.BLOCKS, v, pitch);
		}
	}

	/** Chains and winch every half second, a creak and a little dust now and then, while the leaves move. */
	private void motionSounds(ServerWorld world) {
		soundTicks++;
		if (soundTicks % 10 == 0) {
			sound(world, SoundEvents.BLOCK_CHAIN_STEP, 0.6f, 0.6f + 0.2f * world.random.nextFloat());
			dust(world, 1, 0.02);
		}
		if (soundTicks % 35 == 0) {
			sound(world, SoundEvents.BLOCK_WOODEN_DOOR_OPEN, 0.45f, 0.4f + 0.1f * world.random.nextFloat());
		}
	}

	/** Dust of the deck's own material along each hinge line (the mechanism working, the deck landing). */
	private void dust(ServerWorld world, int perBlock, double speed) {
		if (shapes == null || ConfigManager.drawbridges().soundVolume <= 0) {
			return;
		}
		for (int i = 0; i < 2; i++) {
			LeafShape sh = shapes[i];
			BlockState state = dustState(i);
			net.minecraft.particle.BlockStateParticleEffect effect = new net.minecraft.particle.BlockStateParticleEffect(
					net.minecraft.particle.ParticleTypes.BLOCK, state);
			double len = sh.maxA() - sh.minA();
			int n = Math.max(1, (int) Math.round(len));
			for (int k = 0; k < n; k++) {
				double a = sh.minA() + (k + 0.5) * len / n;
				double[] w = sh.frame().toWorld(a, 0.2, sh.maxC() - 0.3, 0);
				world.spawnParticles(effect, w[0], w[1], w[2], perBlock, 0.3, 0.1, 0.3, speed);
			}
		}
	}

	/** The block state the dust of a leaf is made of: its first captured block (planks, usually). */
	private BlockState dustState(int leaf) {
		for (BlockRecord r : def.leaves[leaf].blocks) {
			BlockState st = parseState(r.state);
			if (st != null && st.isOpaque()) {
				return st;
			}
		}
		return Blocks.OAK_PLANKS.getDefaultState();
	}

	/** A message to the players around the bridge. */
	void tellAround(ServerWorld world, Text text, boolean actionBar) {
		DrawbridgeConfig cfg = ConfigManager.drawbridges();
		if (!cfg.announce) {
			return;
		}
		double[] s = soundSpot();
		double r = Math.max(cfg.announceRadius, tuning.approach() + 16);
		for (ServerPlayerEntity p : world.getPlayers(p -> p.squaredDistanceTo(s[0], s[1], s[2]) < r * r)) {
			p.sendMessage(text, actionBar);
		}
	}

	/** A message to the players at the helm of the vessels the bridge takes into account. */
	void tellPilots(ServerWorld world, Text text) {
		for (UUID uuid : tracked.keySet()) {
			if (world.getEntity(uuid) instanceof ShipEntity ship && ship.passengerInSeat(ShipGeometry.PILOT_SEAT) instanceof ServerPlayerEntity p) {
				p.sendMessage(text, true);
			}
		}
	}

	void tellAdmins(ServerWorld world, Text text) {
		for (ServerPlayerEntity p : world.getServer().getPlayerManager().getPlayerList()) {
			if (ShipPermissions.isAdmin(p)) {
				p.sendMessage(text, false);
			}
		}
	}

	/** The debug line (action bar) for the players who asked for it. */
	private void debugOutput(ServerWorld world, DrawbridgeConfig cfg) {
		StringBuilder sb = new StringBuilder(String.format(Locale.ROOT, "« %s » %s %.0f°", id, cycle.state().french(), cycle.angle()));
		if (!cycle.diagnostic().isEmpty()) {
			sb.append(" [").append(cycle.diagnostic()).append(']');
		}
		if (!requests.isEmpty()) {
			sb.append(" demandes:").append(requests.size());
		}
		int shown = 0;
		for (Tracked t : tracked.values()) {
			if (shown++ >= 2) {
				sb.append(" …");
				break;
			}
			sb.append(String.format(Locale.ROOT, " | %s d=%.0f côté %s %s%s%s", t.label, t.distance, t.side > 0 ? "+" : "-",
					t.tooWide ? "TROP LARGE" : t.requiresOpening ? "OUVRIR" : "passe", t.inPassage ? " (passage)" : "",
					t.unknown ? " ?" : t.idleTicks > cfg.idleIgnoreSeconds * 20 ? " (amarré)" : ""));
		}
		Text text = Text.literal(sb.toString()).formatted(Formatting.GRAY);
		for (UUID uuid : debugPlayers) {
			ServerPlayerEntity p = world.getServer().getPlayerManager().getPlayer(uuid);
			if (p != null) {
				p.sendMessage(text, true);
			}
		}
	}

	/** The full status, for {@code /pontlevis <id> etat}. */
	public List<String> status(DrawbridgeConfig cfg) {
		List<String> out = new ArrayList<>();
		out.add(String.format(Locale.ROOT, "Pont-levis « %s » (%s) : %s, %s, angle %.1f° / %.0f°%s%s", id, def.dimension,
				def.converted ? "converti" : "non converti", cycle.state().french(), cycle.angle(), tuning.openAngle(),
				cycle.suspended() ? ", automatisme suspendu" : "", cycle.blocksInWorld() ? "" : ", blocs du tablier portés par les vantaux"));
		if (!cycle.diagnostic().isEmpty()) {
			out.add("  attente : " + cycle.diagnostic());
		}
		for (int i = 0; i < 2; i++) {
			LeafDef l = def.leaves[i];
			out.add(String.format(Locale.ROOT, "  vantail %s : %s, %d blocs capturés%s", l.name,
					l.complete() ? String.format(Locale.ROOT, "%d %d %d -> %d %d %d", l.min()[0], l.min()[1], l.min()[2], l.max()[0], l.max()[1], l.max()[2])
							: "sélection incomplète", l.blocks.size(),
					frames == null ? "" : String.format(Locale.ROOT, ", charnière %.1f %.1f %.1f", frames[i].hx(), frames[i].hy(), frames[i].hz())));
		}
		if (zones != null) {
			out.add(String.format(Locale.ROOT, "  chenal : axe (%.2f, %.2f), centre %.1f %.1f, largeur %.1f, approche %.0f (+%.0f d'hystérésis), eau %.2f, dessous %.2f, hauteur libre %.2f, marge %.2f",
					zones.dx(), zones.dz(), zones.cx(), zones.cz(), 2 * zones.halfWidth(), zones.approach(), zones.hysteresis(), waterY, undersideY,
					undersideY - waterY, tuning.margin()));
		}
		out.add(String.format(Locale.ROOT, "  réglages : durée %.1f s, délai de fermeture %.1f s, sécurité %.1f s, arrêt à %.0f blocs", tuning.durationTicks() / 20.0,
				tuning.closeDelayTicks() / 20.0, tuning.warningTicks() / 20.0, tuning.stopDistance()));
		if (tracked.isEmpty()) {
			out.add("  aucun navire dans les zones");
		}
		for (Tracked t : tracked.values()) {
			out.add(String.format(Locale.ROOT, "  navire %s : à %.1f du tablier, côté %s%s%s%s%s", t.label, t.distance, t.side > 0 ? "+" : "-",
					t.inPassage ? ", dans le passage" : t.inApproach ? ", en approche" : ", zone d'hystérésis", t.unknown ? ", tronçon déchargé (présumé présent)" : "",
					t.idleTicks > cfg.idleIgnoreSeconds * 20 ? ", à l'arrêt depuis longtemps (ignoré)" : "", t.approaching ? "" : ", s'éloigne"));
			out.add("    " + t.reason);
		}
		if (!requests.isEmpty()) {
			out.add("  demandes scriptées : " + String.join(", ", requests.keySet()));
		}
		return out;
	}

	// ------------------------------------------------------------------ collisions (DrawbridgeCollisions.Source)

	@Override
	public boolean leavesOut() {
		return def.converted && shapes != null && cycle.state().leavesOut();
	}

	@Override
	public List<double[]> leafBoxes() {
		double angle = cycle.angle();
		if (angle != cachedAngle || cachedBoxes == null) {
			List<double[]> out = new ArrayList<>();
			for (LeafShape s : shapes) {
				out.addAll(s.worldBoxes(angle));
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
}
