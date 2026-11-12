package fr.medievalships.entity;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import net.minecraft.command.permission.LeveledPermissionPredicate;
import net.minecraft.command.permission.PermissionLevel;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.PositionInterpolator;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.network.packet.s2c.play.PositionFlag;
import net.minecraft.server.command.CommandOutput;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.PlayerInput;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;
import net.minecraft.world.rule.GameRules;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Autopilot;
import fr.medievalships.core.Gangplank;
import fr.medievalships.core.Dive;
import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.Landing;
import fr.medievalships.core.Ships;
import fr.medievalships.core.Flight;
import fr.medievalships.core.Gait;
import fr.medievalships.core.GotoRoutes;
import fr.medievalships.core.Route;
import fr.medievalships.core.ShipConfig;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPhysics;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Waypoint;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;

/**
 * The navigable medieval galley: a single server-authoritative entity.
 *
 * <ul>
 * <li>Navigation (physics, collisions, autopilot) runs on the server only; clients interpolate.</li>
 * <li>Seated passengers (helmsman + the seats of the ship type) ride the entity normally.</li>
 * <li>Any number of people can also walk freely on the deck: the deck and hull are provided as
 * collision boxes (see {@code EntityCollisionMixin}) and everything standing on board is carried
 * along with the hull (server side for mobs/items, client side for the local player).</li>
 * </ul>
 */
public abstract class ShipEntity extends Entity {
	private static final TrackedData<Float> SHIP_YAW = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	private static final TrackedData<Float> SPEED = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	private static final TrackedData<Float> HELM = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	private static final TrackedData<Boolean> SAIL_SET = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.BOOLEAN);
	private static final TrackedData<Boolean> AUTOPILOT = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.BOOLEAN);
	private static final TrackedData<Integer> GAIT = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.INTEGER);
	/** "entityId:seat,entityId:seat" so clients place passengers on the right seats. */
	private static final TrackedData<String> SEATS = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.STRING);
	/** Aircraft: vertical speed (blocks/s), for the fins and the effects. */
	private static final TrackedData<Float> VSPEED = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	/** Vessels with rooms: open doors (bit k = door k of the interior grid). */
	private static final TrackedData<Long> DOORS = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.LONG);
	/** Vessels with rooms: water level in the airlock (0 pumped out .. 1 full). */
	private static final TrackedData<Float> AIRLOCK = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	/** Submarines: depth below the surfaced position (blocks), for the pilot's gauges and the effects. */
	private static final TrackedData<Float> DEPTH = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	/** Vessels with rooms: fittings switched on or off (bits, see {@link Ships.NautilusLayout#SHUTTERS_CLOSED}). */
	private static final TrackedData<Integer> TOGGLES = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.INTEGER);
	/**
	 * Autopilot state for the pilot's panel: {@code "<phase>;<route>;<label>;<x>;<y>;<z>"} of the point it heads for,
	 * empty while it is off (updated twice a second).
	 */
	private static final TrackedData<String> AUTOPILOT_INFO = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.STRING);
	/** Speed limit set by an administrator ({@code /ship speed}), blocks/s; negative = none (the pilot's panel shows it). */
	private static final TrackedData<Float> SPEED_LIMIT = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);
	/**
	 * Gangplank ({@link Gangplank}): state ordinal, world tick its current move started, deployed angle. Only changes
	 * are synced; the clients compute the animation from them.
	 */
	private static final TrackedData<Integer> GANGPLANK = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.INTEGER);
	private static final TrackedData<Long> GANGPLANK_START = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.LONG);
	private static final TrackedData<Float> GANGPLANK_ANGLE = DataTracker.registerData(ShipEntity.class, TrackedDataHandlerRegistry.FLOAT);

	private static final double DT = 0.05;

	// ---- server state
	private final ShipPhysics physics = new ShipPhysics();
	private final Autopilot autopilot = new Autopilot();
	private final Flight flight = new Flight();
	private final Dive dive = new Dive();
	private boolean aiEnabled;
	@Nullable
	private String routeName;
	private Gait gait = Gait.NORMAL;
	/** Per-ship maximum speed in blocks/s, NaN = use the gaits from the config. */
	private double speedLimit = Double.NaN;
	/**
	 * The destination ({@link GotoRoutes}) was given by an administrator: run like a ferry (chunks kept loaded, reloaded
	 * after a restart). A player's destination is only followed while players are aboard.
	 */
	private boolean gotoByAdmin;
	/** Ticks a player's destination has gone on with nobody aboard. */
	private int unattendedTicks;
	/** The autopilot found the destination unreachable: cancelled at the next tick (not from inside its own tick). */
	private boolean gotoUnreachable;
	/** A player at the helm stands: feet on the deck instead of sitting on the seat (player vehicle attachment 0.6 - seat height 0.28). */
	private static final double HELM_STAND_LIFT = 0.32;
	private final Map<Integer, Integer> seatByEntity = new HashMap<>();
	/** The last seat of each entity, kept after it leaves so it steps off beside that seat (not at the helm). */
	private final Map<Integer, Integer> lastSeatByEntity = new HashMap<>();
	private int pendingSeat = -1;
	private int stoppedTicks;
	private boolean lastJump;
	private boolean lastSprint;
	private boolean seatsDirty;
	/** Until this age a message on the pilot's action bar is not replaced by another one. */
	private int diveMessageUntil;
	/** Airlock: level the valves are bringing the water to (0 or 1). */
	private float airlockTarget;
	/** Submarines: depth ordered by a command (blocks below the surface), NaN = none. */
	private double targetDepth = Double.NaN;
	/** The ship's boat once launched (a Rowboat, see {@link ShipBoatHandling}), or null. */
	@Nullable
	private java.util.UUID lifeboat;
	/** The ship's boat, server side: manoeuvre in progress, last place it was seen (not saved). */
	final ShipBoatHandling.State boatState = new ShipBoatHandling.State();
	/** Commands of the stops reached ({@link Waypoint#onArrive}), run at the next tick (not from inside the autopilot's tick). */
	private final List<String> pendingCommands = new ArrayList<>();
	/** The route ended where the vessel vanishes ({@link Route.End#despawns()}): done at the next tick. */
	@Nullable
	private Route.End pendingEnd;

	// ---- shared / client state
	private final PositionInterpolator interpolator = followsServerExactly() ? new ExactInterpolator(this) : new PositionInterpolator(this, 3);
	/** Yaw change during the last tick, applied to passengers so they turn with the ship. */
	private float yawDelta;
	private float lastTickYaw;
	@Nullable
	private ShipPose lastCarryPose;
	private final Map<Integer, Integer> clientSeats = new HashMap<>();
	private String parsedSeats = "";

	// client-side animation state (see client renderer)
	public float oarPhase;
	public float lastOarPhase;
	public float oarWeight;
	public float lastOarWeight;
	/** Paddle wheel turns: follows the signed speed (backwards when going astern). */
	public float wheelPhase;
	public float lastWheelPhase;
	public float sailOpen = 1f;
	public float lastSailOpen = 1f;
	public float helmVisual;
	public float lastHelmVisual;
	/** Aircraft: smoothed vertical speed order for the fins (-1 descending .. 1 climbing). */
	public float climbVisual;
	public float lastClimbVisual;
	/**
	 * Aircraft: drawn bank into the turns (degrees, positive = right side down), see {@link Flight#bankTarget}. Visual
	 * only: the collisions, the decks one walks on and the carrying of the passengers stay level.
	 */
	public float bankVisual;
	public float lastBankVisual;
	public float rockTime;
	/** Vessels with rooms: smoothed opening of each door (0 closed .. 1 open), for the animations. */
	public final float[] doorVisual = new float[InteriorGrid.MAX_DOORS];
	public final float[] lastDoorVisual = new float[InteriorGrid.MAX_DOORS];
	/** Smoothed airlock water level and salon shutters (0 open .. 1 closed). */
	public float airlockVisual;
	public float lastAirlockVisual;
	public float shutterVisual;
	public float lastShutterVisual;
	/** 0 .. 1 while the gangplank is out: the moored vessel stops rocking and bobbing (drawing only). */
	public float gangplankMoor;
	public float lastGangplankMoor;

	protected ShipEntity(EntityType<? extends ShipEntity> type, World world) {
		super(type, world);
	}

	/** The kind of ship (geometry, default settings, model). */
	public abstract ShipType shipType();

	public ShipGeometry geometry() {
		return shipType().geometry();
	}

	public ShipConfig config() {
		return ConfigManager.ship(shipType());
	}

	/** The item that places this ship (dropped / given back when an admin picks it up). */
	public abstract net.minecraft.item.Item item();

	// ------------------------------------------------------------------ data

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		builder.add(SHIP_YAW, 0f);
		builder.add(SPEED, 0f);
		builder.add(HELM, 0f);
		builder.add(SAIL_SET, false);
		builder.add(AUTOPILOT, false);
		builder.add(GAIT, Gait.NORMAL.ordinal());
		builder.add(SEATS, "");
		builder.add(VSPEED, 0f);
		builder.add(DOORS, 0L);
		builder.add(AIRLOCK, 0f);
		builder.add(DEPTH, 0f);
		builder.add(TOGGLES, 0);
		builder.add(AUTOPILOT_INFO, "");
		builder.add(SPEED_LIMIT, -1f);
		builder.add(GANGPLANK, Gangplank.State.RETRACTED.ordinal());
		builder.add(GANGPLANK_START, 0L);
		builder.add(GANGPLANK_ANGLE, 0f);
	}

	@Override
	protected void readCustomData(ReadView view) {
		physics.speed = view.getDouble("Speed", 0);
		physics.yawRate = view.getDouble("YawRate", 0);
		physics.helm = view.getDouble("Helm", 0);
		flight.vy = view.getDouble("VerticalSpeed", 0);
		dive.vy = flight.vy;
		dataTracker.set(DOORS, view.getLong("Doors", 0L));
		float level = view.getFloat("AirlockLevel", view.getBoolean("AirlockFlooded", false) ? 1f : 0f);
		dataTracker.set(AIRLOCK, level);
		airlockTarget = view.getFloat("AirlockTarget", level);
		dataTracker.set(TOGGLES, view.getInt("Toggles", 0));
		targetDepth = view.getDouble("TargetDepth", -1);
		if (targetDepth < 0) {
			targetDepth = Double.NaN;
		}
		String boat = view.getString("Lifeboat", "");
		try {
			lifeboat = boat.isEmpty() ? null : java.util.UUID.fromString(boat);
		} catch (IllegalArgumentException e) {
			lifeboat = null;
		}
		gait = Gait.byOrdinal(view.getInt("Gait", Gait.NORMAL.ordinal()));
		double limit = view.getDouble("SpeedLimit", -1);
		speedLimit = limit > 0 ? limit : Double.NaN;
		dataTracker.set(SPEED_LIMIT, limit > 0 ? (float) limit : -1f);
		aiEnabled = view.getBoolean("Autopilot", false);
		gotoByAdmin = view.getBoolean("GotoByAdmin", false);
		String route = view.getString("Route", "");
		routeName = route.isEmpty() ? null : route;
		autopilot.target = view.getInt("ApTarget", 0);
		autopilot.direction = view.getInt("ApDirection", 1);
		autopilot.phase = Autopilot.Phase.values()[Math.max(0, Math.min(Autopilot.Phase.values().length - 1,
				view.getInt("ApPhase", 0)))];
		autopilot.waitTicks = view.getInt("ApWait", 0);
		autopilot.legStartX = view.getDouble("ApLegX", getX());
		autopilot.legStartZ = view.getDouble("ApLegZ", getZ());
		// gangplank: a move in progress resolves to an end state; a deployed plank is checked again at the first tick
		Gangplank.State plank = Gangplank.State.of(view.getInt("Gangplank", 0));
		float plankAngle = view.getFloat("GangplankAngle", 0f);
		boolean out = plank == Gangplank.State.DEPLOYED || plank == Gangplank.State.DEPLOYING;
		dataTracker.set(GANGPLANK, (out ? Gangplank.State.DEPLOYED : Gangplank.State.RETRACTED).ordinal());
		dataTracker.set(GANGPLANK_ANGLE, plankAngle);
		dataTracker.set(GANGPLANK_START, 0L);
		gangplankCheckPending = out;
		setShipYaw(getYaw());
		dataTracker.set(AUTOPILOT, aiEnabled);
		dataTracker.set(GAIT, gait.ordinal());
	}

	@Override
	protected void writeCustomData(WriteView view) {
		view.putDouble("Speed", physics.speed);
		view.putDouble("YawRate", physics.yawRate);
		view.putDouble("Helm", physics.helm);
		view.putDouble("VerticalSpeed", geometry().submarine() ? dive.vy : flight.vy);
		view.putLong("Doors", dataTracker.get(DOORS));
		view.putFloat("AirlockLevel", dataTracker.get(AIRLOCK));
		view.putFloat("AirlockTarget", airlockTarget);
		view.putInt("Toggles", dataTracker.get(TOGGLES));
		view.putDouble("TargetDepth", Double.isNaN(targetDepth) ? -1 : targetDepth);
		view.putString("Lifeboat", lifeboat == null ? "" : lifeboat.toString());
		view.putInt("Gait", gait.ordinal());
		view.putDouble("SpeedLimit", Double.isNaN(speedLimit) ? -1 : speedLimit);
		view.putBoolean("Autopilot", aiEnabled);
		view.putBoolean("GotoByAdmin", gotoByAdmin);
		view.putString("Route", routeName == null ? "" : routeName);
		view.putInt("ApTarget", autopilot.target);
		view.putInt("ApDirection", autopilot.direction);
		view.putInt("ApPhase", autopilot.phase.ordinal());
		view.putInt("ApWait", autopilot.waitTicks);
		view.putDouble("ApLegX", autopilot.legStartX);
		view.putDouble("ApLegZ", autopilot.legStartZ);
		view.putInt("Gangplank", dataTracker.get(GANGPLANK));
		view.putFloat("GangplankAngle", dataTracker.get(GANGPLANK_ANGLE));
	}

	// ------------------------------------------------------------------ basic entity behaviour

	@Override
	public boolean damage(ServerWorld world, DamageSource source, float amount) {
		return false; // ships are removed by admins (sneak + attack, or /ship remove), never destroyed
	}

	@Override
	public boolean canHit() {
		return false; // interactions use the precise hull picking (ShipInteraction), not the entity box
	}

	@Override
	public boolean isCollidable(@Nullable Entity entity) {
		return false; // collisions come from the hull boxes, not from the entity box
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean shouldRender(double distance) {
		double d = 256.0 * Entity.getRenderDistanceMultiplier();
		return distance < d * d;
	}

	@Override
	public ItemStack getPickBlockStack() {
		return new ItemStack(item());
	}

	@Override
	public PositionInterpolator getInterpolator() {
		return interpolator;
	}

	/**
	 * Client: does the hull follow the server's packets as they come (one tick behind the server), instead of gliding
	 * towards them over three ticks (vanilla, about four ticks behind with the network)? The hull the players walk in
	 * is then where the server has it: a player the server puts on a deck (stepping off the helm, a teleport...) lands
	 * on it, also while the ship climbs or turns. Its yaw is then the precise synced one, as it comes (the packets'
	 * yaw, quantised to 1.4 degrees, is not used: it made the hull swing back and forth by a few tenths of a degree).
	 * Only for a vessel that moves slowly and has rooms (see {@link SkyLeviathanEntity}).
	 */
	protected boolean followsServerExactly() {
		return false;
	}

	/** One-tick interpolation of the position only; the yaw is left to {@link #clientTick}. */
	private static final class ExactInterpolator extends PositionInterpolator {
		private final Entity ship;

		ExactInterpolator(Entity ship) {
			super(ship, 1);
			this.ship = ship;
		}

		@Override
		public void refreshPositionAndAngles(Vec3d pos, float yaw, float pitch) {
			super.refreshPositionAndAngles(pos, ship.getYaw(), pitch);
		}
	}

	@Override
	public void onRemove(RemovalReason reason) {
		// called for every removal, including chunk unloading and client-side despawn
		ShipTracker.remove(this);
		super.onRemove(reason);
	}

	@Override
	public void remove(RemovalReason reason) {
		if (reason.shouldDestroy() && getEntityWorld() instanceof ServerWorld sw) {
			ShipBoatHandling.onShipRemoved(this, sw); // its boat on the water stays, a Rowboat like any other
			ShipData.get(sw.getServer()).removeFerry(getUuid());
			ShipData.get(sw.getServer()).removeCrewAway(getUuid()); // the players logged out aboard will land safely instead
			if (GotoRoutes.isGoto(routeName)) {
				ShipData.get(sw.getServer()).removeRoute(routeName);
			}
		}
		super.remove(reason);
	}

	// ------------------------------------------------------------------ pose

	public ShipPose pose() {
		return new ShipPose(getX(), getY(), getZ(), getYaw());
	}

	public void setShipYaw(float yaw) {
		setYaw(yaw);
		lastYaw = yaw;
		lastTickYaw = yaw;
		dataTracker.set(SHIP_YAW, yaw);
	}

	public float yawDelta() {
		return yawDelta;
	}

	public float syncedSpeed() {
		return dataTracker.get(SPEED);
	}

	public float syncedHelm() {
		return dataTracker.get(HELM);
	}

	public boolean sailSet() {
		return dataTracker.get(SAIL_SET);
	}

	public boolean autopilotActive() {
		return dataTracker.get(AUTOPILOT);
	}

	public float syncedVerticalSpeed() {
		return dataTracker.get(VSPEED);
	}

	public Flight flight() {
		return flight;
	}

	public Dive dive() {
		return dive;
	}

	/** Doors and airlock of a vessel with rooms (synced: the same on the server and the clients). */
	public InteriorGrid.State interiorState() {
		return new InteriorGrid.State(dataTracker.get(DOORS), dataTracker.get(AIRLOCK));
	}

	public boolean doorOpen(int door) {
		return interiorState().doorOpen(door);
	}

	/** Fittings switched on or off (see {@link Ships.NautilusLayout#SHUTTERS_CLOSED}), synced. */
	public boolean toggle(int bit) {
		return (dataTracker.get(TOGGLES) & (1 << bit)) != 0;
	}

	public void setToggle(int bit, boolean on) {
		int t = dataTracker.get(TOGGLES);
		dataTracker.set(TOGGLES, on ? t | (1 << bit) : t & ~(1 << bit));
	}

	/** Water level in the airlock, 0 .. 1 (synced). */
	public float airlockLevel() {
		return dataTracker.get(AIRLOCK);
	}

	public void setAirlockLevel(float level) {
		dataTracker.set(AIRLOCK, Math.max(0f, Math.min(1f, level)));
	}

	/** Level the airlock valves are bringing the water to (server). */
	public float airlockTarget() {
		return airlockTarget;
	}

	public void setAirlockTarget(float target) {
		airlockTarget = target;
	}

	/** Depth ordered by a command, NaN = none (server). */
	public double targetDepth() {
		return targetDepth;
	}

	public void setTargetDepth(double depth) {
		targetDepth = depth;
	}

	@Nullable
	public java.util.UUID lifeboatId() {
		return lifeboat;
	}

	public void setLifeboatId(@Nullable java.util.UUID id) {
		lifeboat = id;
	}

	/** The boat this ship carries on its deck ({@link fr.medievalships.core.ShipBoats}), or null. */
	@Nullable
	public fr.medievalships.core.ShipBoats.Spec boatSpec() {
		return fr.medievalships.core.ShipBoats.of(shipType().id());
	}

	/** Server: opens or closes a door of the interior (no checks, see {@link #toggleDoor}). */
	public void setDoor(int door, boolean open) {
		dataTracker.set(DOORS, interiorState().withDoor(door, open).openDoors());
	}

	/** Submarines: depth below the surfaced position (synced). */
	public float syncedDepth() {
		return dataTracker.get(DEPTH);
	}

	/**
	 * Server: a player opens or closes a door. A hatch of the outer hull only opens on the surface
	 * (it would let the sea in), and while it is open the submarine does not dive.
	 *
	 * @return a message for the player, or null
	 */
	@Nullable
	public Text toggleDoor(int door) {
		boolean open = !doorOpen(door);
		if (geometry().submarine()) {
			Text refused = NautilusFittings.doorRefusal(this, door, open);
			if (refused != null) {
				return refused;
			}
		}
		setDoor(door, open);
		double[] c = geometry().interior().doorCenter(door);
		double[] w = c == null ? new double[] {getX(), getY(), getZ()} : pose().toWorld(c[0], c[1], c[2]);
		getEntityWorld().playSound(null, w[0], w[1], w[2],
				geometry().submarine()
						? (open ? net.minecraft.sound.SoundEvents.BLOCK_IRON_TRAPDOOR_OPEN : net.minecraft.sound.SoundEvents.BLOCK_IRON_TRAPDOOR_CLOSE)
						: (open ? net.minecraft.sound.SoundEvents.BLOCK_WOODEN_DOOR_OPEN : net.minecraft.sound.SoundEvents.BLOCK_WOODEN_DOOR_CLOSE),
				getSoundCategory(), 1.0f, 0.8f);
		return null;
	}

	public Gait gait() {
		return Gait.byOrdinal(dataTracker.get(GAIT));
	}

	@Nullable
	public ShipPose lastCarryPose() {
		return lastCarryPose;
	}

	public void setLastCarryPose(ShipPose pose) {
		lastCarryPose = pose;
	}

	// ------------------------------------------------------------------ tick

	@Override
	public void tick() {
		ShipTracker.add(this);
		lastTickYaw = getYaw();
		super.tick();
		if (getEntityWorld().isClient()) {
			clientTick();
		} else {
			serverTick((ServerWorld) getEntityWorld());
			if (age % 100 == 50 && getEntityWorld() instanceof ServerWorld sw && ShipData.get(sw.getServer()).hasCrewAway(getUuid())) {
				// players logged out aboard: where to find this ship when they come back (DeckAnchors)
				ShipData.get(sw.getServer()).updateCrewAway(getUuid(), sw.getRegistryKey().getValue().toString(), getX(), getY(), getZ());
			}
		}
		yawDelta = (float) ShipPose.wrapDegrees(getYaw() - lastTickYaw);
	}

	/** Yaw at the start of the current tick (render interpolation). */
	public float lastTickYaw() {
		return lastTickYaw;
	}

	private void clientTick() {
		interpolator.tick();
		// precise yaw from the data tracker (entity packets quantise angles to 1.4 degrees,
		// far too coarse for a 20 block hull)
		float target = dataTracker.get(SHIP_YAW);
		float diff = (float) ShipPose.wrapDegrees(target - getYaw());
		setYaw(getYaw() + diff * 0.5f);
		if (Math.abs(diff) > 45 || followsServerExactly()) {
			setYaw(target);
		}
		parseSeats();
		ShipConfig cfg = config();

		lastOarPhase = oarPhase;
		lastOarWeight = oarWeight;
		lastSailOpen = sailOpen;
		lastWheelPhase = wheelPhase;
		lastHelmVisual = helmVisual;
		float speed = Math.abs(syncedSpeed());
		float rowing = speed > 0.15f ? 1f : 0f;
		oarWeight += (rowing - oarWeight) * 0.06f;
		oarPhase += (float) (DT * Math.max(0.35, Math.min(1.6, speed / cfg.normalSpeed)) * oarWeight);
		wheelPhase += (float) (DT * Math.max(-1.6, Math.min(1.6, syncedSpeed() / cfg.normalSpeed)));
		if (Math.abs(wheelPhase) > 1000f) {
			// keep the float precise (the animation loops every 2 time units)
			float wrap = Math.signum(wheelPhase) * 1000f;
			wheelPhase -= wrap;
			lastWheelPhase -= wrap;
		}
		sailOpen += ((sailSet() ? 1f : 0f) - sailOpen) * 0.05f;
		helmVisual += (syncedHelm() - helmVisual) * 0.3f;
		lastClimbVisual = climbVisual;
		lastBankVisual = bankVisual;
		if (cfg.flight != null) {
			float climb = Math.max(-1f, Math.min(1f, syncedVerticalSpeed() / (float) cfg.flight.climbSpeed));
			climbVisual += (climb - climbVisual) * 0.15f;
			// the turn rate as seen here: the yaw change of the last tick (the yaw is already smoothed above)
			// the server's bankAngle (sent to the client with the other settings it needs, see SyncedConfig)
			double bank = Flight.bankTarget(syncedSpeed(), yawDelta / DT,
					Flight.bankLimit(geometry(), fr.medievalships.data.SyncedConfig.vessel(shipType()).bankAngle()));
			bankVisual = (float) Flight.bankStep(bankVisual, bank, DT);
		}
		rockTime += DT;
		lastGangplankMoor = gangplankMoor;
		gangplankMoor += Math.max(-0.05f, Math.min(0.05f, (gangplankState().out() ? 1f : 0f) - gangplankMoor));
		if (geometry().interior() != null) {
			long open = dataTracker.get(DOORS);
			for (int k = 0; k < doorVisual.length; k++) {
				lastDoorVisual[k] = doorVisual[k];
				float shut = (open & (1L << k)) != 0 ? 1f : 0f;
				doorVisual[k] += Math.max(-0.12f, Math.min(0.12f, shut - doorVisual[k]));
			}
			lastAirlockVisual = airlockVisual;
			airlockVisual += (dataTracker.get(AIRLOCK) - airlockVisual) * 0.5f;
			lastShutterVisual = shutterVisual;
			float closed = toggle(Ships.NautilusLayout.SHUTTERS_CLOSED) ? 1f : 0f;
			shutterVisual += Math.max(-0.025f, Math.min(0.025f, closed - shutterVisual));
		}
	}

	private void serverTick(ServerWorld world) {
		ShipConfig cfg = config();
		ShipWorld shipWorld = new ShipWorld(world, this);
		ShipPose before = pose();
		if (seatsDirty) {
			syncSeats();
		}
		gotoChecks(world);
		runPendingCommands(world);
		if (age % 20 == 0 && (lifeboat != null || toggle(fr.medievalships.core.ShipBoats.AWAY_BIT)) && boatSpec() != null) {
			ShipBoatHandling.tick(this, world); // its boat on the water still there? (else the deco is back aboard)
		}
		if (pendingEnd != null) {
			Route.End end = pendingEnd;
			pendingEnd = null;
			endTrip(world, end);
			return;
		}
		if (age % 10 == 0) {
			syncAutopilotInfo(world);
		}

		// ---- controls
		ShipPhysics.Controls controls;
		Entity pilot = passengerInSeat(ShipGeometry.PILOT_SEAT);
		if (gangplankTick(world, pilot, cfg)) {
			return; // the gangplank is out: the vessel is held where it is
		}
		if (geometry().flying()) {
			ShipPhysics.Controls manual = !aiEnabled && pilot instanceof ServerPlayerEntity player
					? manualControls(player, cfg) : ShipPhysics.Controls.COAST;
			flyTick(world, shipWorld, before, manual, pilot, cfg);
			return;
		}
		if (geometry().submarine()) {
			diveTick(world, shipWorld, before, pilot, cfg);
			return;
		}
		if (aiEnabled) {
			Route route = ShipData.get(world.getServer()).route(routeName);
			controls = autopilot.tick(route, before, physics.speed, physics.yawRate, gait, cfg, geometry(), shipWorld, new Announcer(world, route));
		} else if (pilot instanceof ServerPlayerEntity player) {
			controls = manualControls(player, cfg);
		} else {
			controls = ShipPhysics.Controls.COAST;
		}
		if (!Double.isNaN(speedLimit) && !Double.isNaN(controls.targetSpeed())) {
			controls = new ShipPhysics.Controls(Math.max(-speedLimit, Math.min(speedLimit, controls.targetSpeed())), controls.helmTarget());
		}
		// a drawbridge ahead that is not open yet holds an autopilot vessel before it (1.24.0)
		controls = fr.medievalships.bridge.Drawbridges.gate(this, before, controls);
		ShipPhysics.Step step = physics.step(controls, cfg, DT);

		// ---- buoyancy: follow the water surface under the hull
		double dy = 0;
		double probe = 0.7 * geometry().hull().halfLength; // 7 blocks for the galley
		double waterline = geometry().hull().waterlineY;
		double sBow = shipWorld.waterSurface(before.worldX(0, probe), before.worldZ(0, probe), getY() + waterline);
		double sMid = shipWorld.waterSurface(getX(), getZ(), getY() + waterline);
		double sStern = shipWorld.waterSurface(before.worldX(0, -probe), before.worldZ(0, -probe), getY() + waterline);
		double sum = 0;
		int n = 0;
		for (double s : new double[] {sBow, sMid, sStern}) {
			if (!Double.isNaN(s)) {
				sum += s;
				n++;
			}
		}
		if (n > 0) {
			dy = Math.max(-0.15, Math.min(0.15, (sum / n - waterline - getY()) * 0.3));
		} else if (!shipWorld.blocked(getX(), getY() + geometry().hull().keelY(0) - 0.3, getZ())) {
			dy = -0.3; // no water (drained, spawned in the air...): fall until something holds the keel
		}

		// ---- move with collisions
		ShipMover.Result result = ShipMover.move(geometry(), before, step.forward(), step.yaw(), dy, shipWorld);
		physics.collide(result.forwardBlocked(), result.rotationBlocked());
		ShipPose after = result.pose();
		setPosition(after.x(), after.y(), after.z());
		setYaw((float) after.yaw());
		dataTracker.set(SHIP_YAW, (float) after.yaw());
		setVelocity(after.x() - before.x(), after.y() - before.y(), after.z() - before.z());
		carryEntities(world, before, after);

		// ---- synced state for animations
		if (Math.abs(dataTracker.get(SPEED) - physics.speed) > 0.02) {
			dataTracker.set(SPEED, (float) physics.speed);
		}
		if (Math.abs(dataTracker.get(HELM) - physics.helm) > 0.02) {
			dataTracker.set(HELM, (float) physics.helm);
		}
		boolean underWay = Math.abs(physics.speed) > 0.1 || controls.targetSpeed() > 0.1;
		stoppedTicks = underWay ? 0 : stoppedTicks + 1;
		boolean sail = !cfg.furlSailWhenStopped || stoppedTicks < 100;
		if (sail != dataTracker.get(SAIL_SET)) {
			dataTracker.set(SAIL_SET, sail);
		}
		if (dataTracker.get(AUTOPILOT) != aiEnabled) {
			dataTracker.set(AUTOPILOT, aiEnabled);
		}

		// ---- ferries keep their chunks loaded and are remembered across restarts
		if (keepsChunksLoaded() && age % 20 == 0) {
			if (ConfigManager.server().chunkLoadAutopilotShips) {
				ChunkPos here = new ChunkPos(BlockPos.ofFloored(getX(), getY(), getZ()));
				world.getChunkManager().addTicket(ChunkTicketType.PORTAL, here, ConfigManager.server().chunkLoadRadius);
				double ahead = Math.max(24, geometry().aiReach() + 8) * Math.signum(physics.speed == 0 ? 1 : physics.speed);
				ChunkPos front = new ChunkPos(BlockPos.ofFloored(after.worldX(0, ahead), getY(), after.worldZ(0, ahead)));
				if (!front.equals(here)) {
					world.getChunkManager().addTicket(ChunkTicketType.PORTAL, front, ConfigManager.server().chunkLoadRadius);
				}
			}
			if (age % 100 == 0) {
				ShipData.get(world.getServer()).updateFerry(getUuid(), new ShipData.FerryRecord(
						world.getRegistryKey().getValue().toString(), getX(), getZ(), routeName));
			}
		}
	}

	/**
	 * Aircraft: no water and no gravity while it flies. The pilot climbs (jump key) and comes down
	 * (sprint key), the altitude holds by itself; the autopilot plans its own altitude.
	 */
	private void flyTick(ServerWorld world, ShipWorld shipWorld, ShipPose before, ShipPhysics.Controls manual, @Nullable Entity pilot,
			ShipConfig cfg) {
		ShipPhysics.Controls controls = manual;
		double vy = 0;
		if (aiEnabled) {
			Route route = ShipData.get(world.getServer()).route(routeName);
			Flight.Orders orders = Flight.autopilot(autopilot, route, before, physics, gait, cfg, geometry(), shipWorld,
					new Announcer(world, route));
			controls = orders.controls();
			vy = orders.desiredVy();
		} else if (pilot instanceof ServerPlayerEntity player) {
			PlayerInput in = player.getPlayerInput();
			vy = Flight.manual((in.jump() ? 1 : 0) - (in.sprint() ? 1 : 0), cfg.flight);
		}
		if (!Double.isNaN(speedLimit) && !Double.isNaN(controls.targetSpeed())) {
			controls = new ShipPhysics.Controls(Math.max(-speedLimit, Math.min(speedLimit, controls.targetSpeed())), controls.helmTarget());
		}
		Flight.Result result = Flight.tick(geometry(), before, physics, flight, controls, vy, cfg, shipWorld, DT);
		ShipPose after = result.pose();
		setPosition(after.x(), after.y(), after.z());
		setYaw((float) after.yaw());
		dataTracker.set(SHIP_YAW, (float) after.yaw());
		setVelocity(after.x() - before.x(), after.y() - before.y(), after.z() - before.z());
		carryEntities(world, before, after);
		if (Math.abs(dataTracker.get(SPEED) - physics.speed) > 0.02) {
			dataTracker.set(SPEED, (float) physics.speed);
		}
		if (Math.abs(dataTracker.get(HELM) - physics.helm) > 0.02) {
			dataTracker.set(HELM, (float) physics.helm);
		}
		if (Math.abs(dataTracker.get(VSPEED) - flight.vy) > 0.02) {
			dataTracker.set(VSPEED, (float) flight.vy);
		}
		if (!dataTracker.get(SAIL_SET)) {
			dataTracker.set(SAIL_SET, true);
		}
		if (dataTracker.get(AUTOPILOT) != aiEnabled) {
			dataTracker.set(AUTOPILOT, aiEnabled);
		}
		if (keepsChunksLoaded() && age % 20 == 0) {
			if (ConfigManager.server().chunkLoadAutopilotShips) {
				ChunkPos here = new ChunkPos(BlockPos.ofFloored(getX(), getY(), getZ()));
				world.getChunkManager().addTicket(ChunkTicketType.PORTAL, here, ConfigManager.server().chunkLoadRadius);
				double ahead = Math.max(24, geometry().aiReach() + 8) * Math.signum(physics.speed == 0 ? 1 : physics.speed);
				ChunkPos front = new ChunkPos(BlockPos.ofFloored(after.worldX(0, ahead), getY(), after.worldZ(0, ahead)));
				if (!front.equals(here)) {
					world.getChunkManager().addTicket(ChunkTicketType.PORTAL, front, ConfigManager.server().chunkLoadRadius);
				}
			}
			if (age % 100 == 0) {
				ShipData.get(world.getServer()).updateFerry(getUuid(), new ShipData.FerryRecord(
						world.getRegistryKey().getValue().toString(), getX(), getZ(), routeName));
			}
		}
	}

	/**
	 * Submarine: floats like a ship on the surface, dives (sprint key) and rises (jump key) with a
	 * lot of inertia, holds its depth by itself. It never dives with the hatch open.
	 */
	private void diveTick(ServerWorld world, ShipWorld shipWorld, ShipPose before, @Nullable Entity pilot, ShipConfig cfg) {
		ShipPhysics.Controls controls = ShipPhysics.Controls.COAST;
		double surfacedY = shipWorld.surfacedY(this);
		double vy = Dive.hold(before.y(), surfacedY, cfg.dive);
		int input = 0;
		if (aiEnabled) {
			Route route = ShipData.get(world.getServer()).route(routeName);
			Dive.Orders orders = Dive.autopilot(autopilot, route, before, physics, gait, cfg, geometry(), shipWorld, surfacedY,
					new Announcer(world, route));
			controls = orders.controls();
			vy = orders.desiredVy();
			targetDepth = Double.NaN; // the route gives the depth
		} else if (pilot instanceof ServerPlayerEntity player) {
			controls = manualControls(player, cfg);
			PlayerInput in = player.getPlayerInput();
			input = (in.jump() ? 1 : 0) - (in.sprint() ? 1 : 0);
			if (input != 0) {
				targetDepth = Double.NaN; // the pilot takes the ballasts back
			}
			vy = Dive.manual(input, before.y(), surfacedY, cfg.dive);
		}
		if (!aiEnabled && !Double.isNaN(targetDepth) && !Double.isNaN(surfacedY) && input == 0) {
			// depth ordered by a command (/ship nautilus profondeur, ballasts): the hull goes there and holds it
			double depth = Math.min(targetDepth, cfg.dive.maxDepth);
			vy = depth < Dive.SURFACED ? Dive.towards(surfacedY, before.y(), cfg.dive) : Dive.towards(surfacedY - depth, before.y(), cfg.dive);
		}
		boolean hatchOpen = doorOpen(Ships.NautilusLayout.HATCH_DOOR) || doorOpen(Ships.NautilusLayout.BOAT_HATCH_DOOR);
		if (hatchOpen && vy < 0 && Dive.depth(before.y(), surfacedY) < Dive.SURFACED) {
			// ordered to dive with a hatch open: the crew shuts it, unless someone stands in it
			String blocker = NautilusFittings.shutHatchesForDive(this, world);
			if (blocker == null) {
				diveMessage(pilot, Text.literal("Panneaux refermés : plongée !").formatted(Formatting.GOLD));
			} else {
				vy = Dive.hold(before.y(), surfacedY, cfg.dive); // never dive with a hatch open
				diveMessage(pilot, Text.literal("Impossible de plonger : quelqu'un est dans " + blocker + ".").formatted(Formatting.RED));
			}
		}
		if (!Double.isNaN(speedLimit) && !Double.isNaN(controls.targetSpeed())) {
			controls = new ShipPhysics.Controls(Math.max(-speedLimit, Math.min(speedLimit, controls.targetSpeed())), controls.helmTarget());
		}
		controls = fr.medievalships.bridge.Drawbridges.gate(this, before, controls); // a drawbridge ahead (1.24.0)
		Dive.Result result = Dive.tick(geometry(), before, physics, dive, controls, vy, surfacedY, cfg, shipWorld, DT);
		ShipPose after = result.pose();
		setPosition(after.x(), after.y(), after.z());
		setYaw((float) after.yaw());
		dataTracker.set(SHIP_YAW, (float) after.yaw());
		setVelocity(after.x() - before.x(), after.y() - before.y(), after.z() - before.z());
		carryEntities(world, before, after);
		if (Math.abs(dataTracker.get(SPEED) - physics.speed) > 0.02) {
			dataTracker.set(SPEED, (float) physics.speed);
		}
		if (Math.abs(dataTracker.get(HELM) - physics.helm) > 0.02) {
			dataTracker.set(HELM, (float) physics.helm);
		}
		if (Math.abs(dataTracker.get(VSPEED) - dive.vy) > 0.02) {
			dataTracker.set(VSPEED, (float) dive.vy);
		}
		float depth = (float) Dive.depth(after.y(), surfacedY);
		if (Math.abs(dataTracker.get(DEPTH) - depth) > 0.05) {
			dataTracker.set(DEPTH, depth);
		}
		if (!dataTracker.get(SAIL_SET)) {
			dataTracker.set(SAIL_SET, true);
		}
		if (dataTracker.get(AUTOPILOT) != aiEnabled) {
			dataTracker.set(AUTOPILOT, aiEnabled);
		}
		if (aiEnabled && age % 20 == 0 && ConfigManager.server().chunkLoadAutopilotShips) {
			ChunkPos here = new ChunkPos(BlockPos.ofFloored(getX(), getY(), getZ()));
			world.getChunkManager().addTicket(ChunkTicketType.PORTAL, here, ConfigManager.server().chunkLoadRadius);
		}
		if (aiEnabled && age % 100 == 0) {
			ShipData.get(world.getServer()).updateFerry(getUuid(), new ShipData.FerryRecord(
					world.getRegistryKey().getValue().toString(), getX(), getZ(), routeName));
		}
		if (result.verticalBlocked() && vy < 0) {
			diveMessage(pilot, Text.literal("Le fond est trop proche : impossible de descendre plus bas ici.").formatted(Formatting.RED));
		} else if (Double.isNaN(surfacedY) && vy < 0) {
			diveMessage(pilot, Text.literal("Pas d'eau sous la coque : impossible de plonger.").formatted(Formatting.RED));
		}
		NautilusFittings.tick(this, world);
	}

	/** A message for the pilot that the depth gauge does not overwrite for two seconds. */
	private void diveMessage(@Nullable Entity pilot, Text text) {
		if (pilot instanceof ServerPlayerEntity player && age >= diveMessageUntil - 30) {
			player.sendMessage(text, true);
			diveMessageUntil = age + 40;
		}
	}

	private ShipPhysics.Controls manualControls(ServerPlayerEntity player, ShipConfig cfg) {
		PlayerInput in = player.getPlayerInput();
		if (geometry().flying() || geometry().submarine()) {
			// jump / sprint climb and descend (see flyTick, diveTick); the speed is the normal gait
			double target = in.forward() && !in.backward() ? cfg.gaitSpeed(gait) : in.backward() && !in.forward() ? -cfg.reverseSpeed : Double.NaN;
			return new ShipPhysics.Controls(target, (in.right() ? 1 : 0) - (in.left() ? 1 : 0));
		}
		if (in.jump() && !lastJump) {
			setGait(gait.faster());
		}
		if (in.sprint() && !lastSprint) {
			setGait(gait.slower());
		}
		lastJump = in.jump();
		lastSprint = in.sprint();
		double target;
		if (in.forward() && !in.backward()) {
			target = cfg.gaitSpeed(gait);
		} else if (in.backward() && !in.forward()) {
			target = -cfg.reverseSpeed;
		} else {
			target = Double.NaN; // oars at rest: the ship glides on its inertia
		}
		double helm = (in.right() ? 1 : 0) - (in.left() ? 1 : 0);
		return new ShipPhysics.Controls(target, helm);
	}

	/** Moves mobs, items and other entities standing on the deck along with the hull (server side). */
	private void carryEntities(ServerWorld world, ShipPose before, ShipPose after) {
		double dYaw = after.yaw() - before.yaw();
		if (dYaw == 0 && after.x() == before.x() && after.y() == before.y() && after.z() == before.z() && age % 10 != 0) {
			// at rest: nothing to carry; the safety net for an entity sunk into the deck still runs twice a second
			return;
		}
		double r = geometry().boundingRadius();
		Box area = new Box(before.x() - r, before.y() + Math.min(-2, geometry().lowestY() - 1), before.z() - r,
				before.x() + r, before.y() + Math.max(8, geometry().topY() + 3), before.z() + r);
		// players are moved by their own client, except those whose client reports this hull's frame (their server copy
		// stays on the same spot of this hull between two of their packets, see DeckSync) and fake players (no client)
		List<Entity> list = world.getOtherEntities(this, area, e -> (!(e instanceof PlayerEntity) || DeckSync.carriedByServer(e, this))
				&& !e.hasVehicle() && !(e instanceof ShipEntity) && !e.isRemoved());
		for (Entity e : list) {
			double[] l = before.toLocal(e.getX(), e.getY(), e.getZ());
			if (!geometry().inCarryVolume(l[0], l[1], l[2])
					&& !ShipLadders.on(this, before.x(), before.y(), before.z(), before.yaw(), e.getX(), e.getY(), e.getZ(), false)) {
				continue; // neither on the deck nor on a side ladder
			}
			double rescue = e instanceof PlayerEntity ? Double.NaN : geometry().deckRescueY(l[0], l[1], l[2], interiorState());
			if (!Double.isNaN(rescue)) {
				l[1] = rescue; // sank into the deck (another mod replaced the collisions): put it back on top
				if (e.getVelocity().y < 0) {
					e.setVelocity(e.getVelocity().x, 0, e.getVelocity().z);
				}
				e.setOnGround(true);
			}
			double[] w = after.toWorld(l[0], l[1], l[2]);
			e.setPosition(w[0], w[1], w[2]);
			if (dYaw != 0) {
				e.setYaw((float) (e.getYaw() + dYaw));
				if (e instanceof LivingEntity living) {
					living.setHeadYaw((float) (living.getHeadYaw() + dYaw));
					living.setBodyYaw((float) (living.bodyYaw + dYaw));
				}
			}
		}
	}

	// ------------------------------------------------------------------ gangplank

	/** A deployed plank is checked again once after loading (its landing may be gone). */
	private boolean gangplankCheckPending;
	/** Until this age the pilot's "fold the gangplank first" message is not repeated. */
	private int gangplankMessageUntil;
	/** World boxes of the deployed plank (computed once per deploy, the vessel being held), with the pose and angle used. */
	private List<double[]> gangplankBoxes = List.of();
	@Nullable
	private ShipPose gangplankBoxesPose;
	private float gangplankBoxesAngle = Float.NaN;

	/** This vessel's gangplank, or null if its type has none. */
	@Nullable
	public Gangplank.Spec gangplank() {
		return Gangplank.of(shipType().id());
	}

	public Gangplank.State gangplankState() {
		return Gangplank.State.of(dataTracker.get(GANGPLANK));
	}

	/** World tick at which the current move started. */
	public long gangplankStart() {
		return dataTracker.get(GANGPLANK_START);
	}

	/** Deployed angle (degrees, down positive). */
	public float gangplankTarget() {
		return dataTracker.get(GANGPLANK_ANGLE);
	}

	/** Ticks since the current move started (fractional, for the animation). */
	public double gangplankTicks(float tickDelta) {
		return getEntityWorld().getTime() - gangplankStart() + tickDelta;
	}

	/** Angle of the plank now (stowed when there is none). */
	public double gangplankAngle(float tickDelta) {
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			return Gangplank.STOWED_ANGLE;
		}
		return Gangplank.angle(spec, gangplankState(), gangplankTicks(tickDelta), gangplankTarget());
	}

	private void setGangplank(Gangplank.State state, long start, float angle) {
		dataTracker.set(GANGPLANK, state.ordinal());
		dataTracker.set(GANGPLANK_START, start);
		dataTracker.set(GANGPLANK_ANGLE, angle);
	}

	/** Sets the plank's state directly (tests, admin): no checks, no animation. */
	public void forceGangplank(Gangplank.State state, float angle) {
		setGangplank(state, getEntityWorld().getTime() - Gangplank.DURATION, angle);
	}

	/**
	 * The rail opening of a deployed plank for {@link ShipGeometry#collectBoxes}: {side, z0, z1, yTop}, or null.
	 */
	@Nullable
	public double[] gangplankWallGap() {
		if (gangplankState() != Gangplank.State.DEPLOYED) {
			return null;
		}
		Gangplank.Spec spec = gangplank();
		if (spec == null || !spec.hasRailGap()) {
			return null;
		}
		return new double[] {spec.o(), spec.railGapZ0(), spec.railGapZ1(), spec.hy()};
	}

	/**
	 * Adds the collision boxes of the deployed plank (its steps along the slope and the inboard stairs) intersecting a
	 * world query box. Server and clients compute the same boxes from the synced state; nothing while the plank is
	 * stowed or moving.
	 */
	public void collectGangplankBoxes(double qMinX, double qMinY, double qMinZ, double qMaxX, double qMaxY, double qMaxZ,
			ShipGeometry.BoxSink sink) {
		if (gangplankState() != Gangplank.State.DEPLOYED) {
			return;
		}
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			return;
		}
		ShipPose p = pose();
		float a = gangplankTarget();
		ShipPose q = gangplankBoxesPose;
		if (q == null || a != gangplankBoxesAngle || Math.abs(q.x() - p.x()) > 1e-4 || Math.abs(q.y() - p.y()) > 1e-4
				|| Math.abs(q.z() - p.z()) > 1e-4 || Math.abs(q.yaw() - p.yaw()) > 1e-3) {
			List<double[]> boxes = new ArrayList<>();
			for (Gangplank.Box b : Gangplank.deployedBoxes(spec, a)) {
				ShipGeometry.emitLocal(p, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ(),
						(x0, y0, z0, x1, y1, z1) -> boxes.add(new double[] {x0, y0, z0, x1, y1, z1}));
			}
			gangplankBoxes = boxes;
			gangplankBoxesPose = p;
			gangplankBoxesAngle = a;
		}
		for (double[] b : gangplankBoxes) {
			if (b[0] < qMaxX && b[3] > qMinX && b[1] < qMaxY && b[4] > qMinY && b[2] < qMaxZ && b[5] > qMinZ) {
				sink.accept(b[0], b[1], b[2], b[3], b[4], b[5]);
			}
		}
	}

	/** Does this entity stand on (or just above) the deployed plank or its stairs (the server's anti-flight check)? */
	public boolean standsOnGangplank(Entity e) {
		if (gangplankState() != Gangplank.State.DEPLOYED) {
			return false;
		}
		Box b = e.getBoundingBox();
		boolean[] hit = {false};
		collectGangplankBoxes(b.minX, b.minY - 0.6, b.minZ, b.maxX, b.minY + 0.1, b.maxZ, (x0, y0, z0, x1, y1, z1) -> hit[0] = true);
		return hit[0];
	}

	/** The lever was used (a player's click, a test): deploys or retracts the plank. Returns the message for the action bar. */
	@Nullable
	public Text useGangplankLever(ServerWorld world) {
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			return null;
		}
		return switch (gangplankState()) {
			case DEPLOYING, RETRACTING -> Text.literal("La passerelle est en mouvement.").formatted(Formatting.YELLOW);
			case RETRACTED -> deployGangplank(world);
			case DEPLOYED -> retractGangplank(world);
		};
	}

	/** Deploys the plank if every safety check passes; returns the message (refusal in red). */
	public Text deployGangplank(ServerWorld world) {
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			return Text.literal("Ce navire n'a pas de passerelle.").formatted(Formatting.RED);
		}
		if (gangplankState() != Gangplank.State.RETRACTED) {
			return Text.literal("La passerelle est déjà sortie.").formatted(Formatting.YELLOW);
		}
		if (Math.abs(physics.speed) > 1.0 || getVelocity().length() > 0.05 || Math.abs(flight.vy) > 0.5 || Math.abs(dive.vy) > 0.5) {
			return refuse(world, spec, "Le navire doit être à l'arrêt pour déployer la passerelle.");
		}
		if (geometry().submarine() && syncedDepth() > 0.5f) {
			return refuse(world, spec, "Faites d'abord surface pour déployer la passerelle.");
		}
		if (aiEnabled && (autopilot.phase == Autopilot.Phase.SAILING || autopilot.phase == Autopilot.Phase.RECOVERING)) {
			return refuse(world, spec, "Le pilote automatique fait route : impossible de déployer la passerelle.");
		}
		ShipPose p = pose();
		GangplankTerrain terrain = new GangplankTerrain(world, p);
		Gangplank.Landing landing = Gangplank.findLanding(spec, terrain);
		if (!landing.ok()) {
			return refuse(world, spec, landing.refusal());
		}
		String blocked = Gangplank.clearance(spec, landing.angle(), terrain);
		if (blocked != null) {
			return refuse(world, spec, blocked);
		}
		// nobody in the way: the volume a player would occupy over the deployed plank (and the stairs)
		List<Gangplank.Box> path = new ArrayList<>();
		for (Gangplank.Box b : Gangplank.deployedBoxes(spec, landing.angle())) {
			path.add(new Gangplank.Box(b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY() + 1.8, b.maxZ()));
		}
		if (entityIn(world, p, path)) {
			return refuse(world, spec, "Quelqu'un (ou quelque chose) se trouve sur le chemin de la passerelle.");
		}
		setGangplank(Gangplank.State.DEPLOYING, world.getTime(), (float) landing.angle());
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_LEVER_CLICK, 0.6f, 0.8f);
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_WOODEN_TRAPDOOR_OPEN, 1.0f, 0.6f);
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_CHAIN_PLACE, 0.8f, 0.7f);
		return Text.literal("La passerelle se déploie.").formatted(Formatting.GOLD);
	}

	/** Retracts the plank unless someone stands on it or on its stairs; returns the message (refusal in red). */
	public Text retractGangplank(ServerWorld world) {
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			return Text.literal("Ce navire n'a pas de passerelle.").formatted(Formatting.RED);
		}
		if (gangplankState() != Gangplank.State.DEPLOYED) {
			return Text.literal("La passerelle n'est pas déployée.").formatted(Formatting.YELLOW);
		}
		if (gangplankOccupied(world)) {
			return refuse(world, spec, "Impossible de replier la passerelle : quelqu'un est dessus.");
		}
		setGangplank(Gangplank.State.RETRACTING, world.getTime(), gangplankTarget());
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_LEVER_CLICK, 0.6f, 0.7f);
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_CHAIN_PLACE, 0.8f, 0.6f);
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_WOODEN_TRAPDOOR_CLOSE, 0.9f, 0.6f);
		return Text.literal("La passerelle se replie.").formatted(Formatting.GOLD);
	}

	/** Is anyone standing on or inside the deployed plank or its stairs? */
	public boolean gangplankOccupied(ServerWorld world) {
		Gangplank.Spec spec = gangplank();
		if (spec == null || gangplankState() == Gangplank.State.RETRACTED) {
			return false;
		}
		List<Gangplank.Box> boxes = new ArrayList<>();
		for (Gangplank.Box b : Gangplank.deployedBoxes(spec, gangplankTarget())) {
			boxes.add(new Gangplank.Box(b.minX() - 0.05, b.minY(), b.minZ() - 0.05, b.maxX() + 0.05, b.maxY() + 0.6, b.maxZ() + 0.05));
		}
		return entityIn(world, pose(), boxes);
	}

	/** Is a living being or a vehicle (not this vessel, not its seated passengers, no spectator) in one of the local boxes? */
	private boolean entityIn(ServerWorld world, ShipPose p, List<Gangplank.Box> local) {
		double minX = Double.MAX_VALUE, minY = Double.MAX_VALUE, minZ = Double.MAX_VALUE;
		double maxX = -Double.MAX_VALUE, maxY = -Double.MAX_VALUE, maxZ = -Double.MAX_VALUE;
		List<double[]> world0 = new ArrayList<>();
		for (Gangplank.Box b : local) {
			ShipGeometry.emitLocal(p, b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ(),
					(x0, y0, z0, x1, y1, z1) -> world0.add(new double[] {x0, y0, z0, x1, y1, z1}));
		}
		for (double[] w : world0) {
			minX = Math.min(minX, w[0]);
			minY = Math.min(minY, w[1]);
			minZ = Math.min(minZ, w[2]);
			maxX = Math.max(maxX, w[3]);
			maxY = Math.max(maxY, w[4]);
			maxZ = Math.max(maxZ, w[5]);
		}
		if (world0.isEmpty()) {
			return false;
		}
		List<Entity> list = world.getOtherEntities(this, new Box(minX, minY, minZ, maxX, maxY, maxZ),
				e -> !e.isRemoved() && !e.isSpectator() && e.getRootVehicle() != this && !(e instanceof ShipEntity)
						&& (e instanceof LivingEntity || e instanceof net.minecraft.entity.vehicle.VehicleEntity));
		for (Entity e : list) {
			Box eb = e.getBoundingBox();
			for (double[] w : world0) {
				if (eb.minX < w[3] && eb.maxX > w[0] && eb.minY < w[4] && eb.maxY > w[1] && eb.minZ < w[5] && eb.maxZ > w[2]) {
					return true;
				}
			}
		}
		return false;
	}

	private Text refuse(ServerWorld world, Gangplank.Spec spec, String why) {
		gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_LEVER_CLICK, 0.4f, 0.5f);
		return Text.literal(why).formatted(Formatting.RED);
	}

	private void gangplankSound(ServerWorld world, Gangplank.Spec spec, net.minecraft.sound.SoundEvent sound, float volume, float pitch) {
		double[] w = pose().toWorld(spec.hx(), spec.hy(), spec.hz());
		world.playSound(null, w[0], w[1], w[2], sound, net.minecraft.sound.SoundCategory.BLOCKS, volume, pitch);
	}

	/**
	 * Server tick of the gangplank: ends the moves, re-checks a plank deployed before a restart, and while the plank is
	 * out holds the vessel still (no thrust, no drift), tells the pilot to fold it first, lets a moored autopilot count
	 * down and folds the plank for it when it must leave (if nobody is on it). Returns true while the vessel is held.
	 * Nothing runs while the plank is stowed.
	 */
	private boolean gangplankTick(ServerWorld world, @Nullable Entity pilot, ShipConfig cfg) {
		Gangplank.State state = gangplankState();
		if (state == Gangplank.State.RETRACTED) {
			return false;
		}
		Gangplank.Spec spec = gangplank();
		if (spec == null) {
			setGangplank(Gangplank.State.RETRACTED, 0L, 0f);
			return false;
		}
		long t = world.getTime() - gangplankStart();
		if (gangplankCheckPending && state == Gangplank.State.DEPLOYED) {
			// after a restart: the landing must still be there (checked once its chunk is loaded; never loads one)
			double[] tip = pose().toWorld(spec.point(gangplankTarget(), spec.length(), 0, 0)[0], spec.hy(),
					spec.point(gangplankTarget(), spec.length(), 0, 0)[2]);
			if (world.isChunkLoaded(((int) Math.floor(tip[0])) >> 4, ((int) Math.floor(tip[2])) >> 4)) {
				gangplankCheckPending = false;
				Gangplank.Landing landing = Gangplank.findLanding(spec, new GangplankTerrain(world, pose()));
				if (!landing.ok()) {
					setGangplank(Gangplank.State.RETRACTING, world.getTime(), gangplankTarget());
					gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_CHAIN_PLACE, 0.8f, 0.6f);
				} else if (Math.abs(landing.angle() - gangplankTarget()) > 0.5) {
					setGangplank(Gangplank.State.DEPLOYED, gangplankStart(), (float) landing.angle());
				}
				state = gangplankState();
				t = world.getTime() - gangplankStart();
			}
		}
		if (state == Gangplank.State.DEPLOYING && t >= Gangplank.DURATION) {
			setGangplank(Gangplank.State.DEPLOYED, gangplankStart(), gangplankTarget());
			state = Gangplank.State.DEPLOYED;
			gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_WOOD_PLACE, 1.0f, 0.7f);
		} else if (state == Gangplank.State.RETRACTING && t >= Gangplank.DURATION) {
			setGangplank(Gangplank.State.RETRACTED, gangplankStart(), gangplankTarget());
			gangplankSound(world, spec, net.minecraft.sound.SoundEvents.BLOCK_IRON_TRAPDOOR_CLOSE, 0.7f, 0.8f);
			return false;
		}
		// the pilot wants to leave
		if (pilot instanceof ServerPlayerEntity player && age >= gangplankMessageUntil) {
			PlayerInput in = player.getPlayerInput();
			if (in.forward() || in.backward() || in.left() || in.right() || ((geometry().flying() || geometry().submarine()) && (in.jump() || in.sprint()))) {
				player.sendMessage(Text.literal("Repliez d'abord la passerelle").formatted(Formatting.RED), true);
				gangplankMessageUntil = age + 40;
			}
		}
		// the autopilot: counts down at its stop, folds the plank when it leaves (or waits while someone is on it)
		if (aiEnabled) {
			Route route = ShipData.get(world.getServer()).route(routeName);
			if (autopilot.phase == Autopilot.Phase.DOCKED && route != null) {
				autopilot.tick(route, pose(), 0, 0, gait, cfg, geometry(), new ShipWorld(world, this), new Announcer(world, route));
			} else if ((autopilot.phase == Autopilot.Phase.SAILING || autopilot.phase == Autopilot.Phase.RECOVERING)
					&& state == Gangplank.State.DEPLOYED) {
				if (!gangplankOccupied(world)) {
					retractGangplank(world);
				} else if (age >= gangplankMessageUntil) {
					for (ServerPlayerEntity p : playersAboard(world)) {
						p.sendMessage(Text.literal("Départ retardé : quelqu'un est sur la passerelle.").formatted(Formatting.YELLOW), true);
					}
					gangplankMessageUntil = age + 60;
				}
			}
		}
		// held in place: no thrust, no drift
		physics.speed = 0;
		physics.yawRate = 0;
		flight.vy = 0;
		dive.vy = 0;
		setVelocity(0, 0, 0);
		if (dataTracker.get(SPEED) != 0f) {
			dataTracker.set(SPEED, 0f);
		}
		if (dataTracker.get(VSPEED) != 0f) {
			dataTracker.set(VSPEED, 0f);
		}
		stoppedTicks++;
		boolean sail = geometry().flying() || geometry().submarine() || !cfg.furlSailWhenStopped || stoppedTicks < 100;
		if (sail != dataTracker.get(SAIL_SET)) {
			dataTracker.set(SAIL_SET, sail);
		}
		if (dataTracker.get(AUTOPILOT) != aiEnabled) {
			dataTracker.set(AUTOPILOT, aiEnabled);
		}
		if (keepsChunksLoaded() && age % 20 == 0 && ConfigManager.server().chunkLoadAutopilotShips) {
			world.getChunkManager().addTicket(ChunkTicketType.PORTAL, new ChunkPos(getBlockPos()), ConfigManager.server().chunkLoadRadius);
		}
		if (geometry().submarine()) {
			NautilusFittings.tick(this, world);
		}
		return true;
	}

	/** Is this pilot input ignored because the gangplank is out (for the pilot's HUD)? */
	public boolean heldByGangplank() {
		return gangplankState() != Gangplank.State.RETRACTED;
	}

	// ------------------------------------------------------------------ autopilot & admin API

	public boolean isAutopilotEnabled() {
		return aiEnabled;
	}

	@Nullable
	public String routeName() {
		return routeName;
	}

	public Autopilot autopilot() {
		return autopilot;
	}

	public ShipPhysics physics() {
		return physics;
	}

	public double speedLimit() {
		return speedLimit;
	}

	public void setSpeedLimit(double limit) {
		speedLimit = limit > 0 ? limit : Double.NaN;
		dataTracker.set(SPEED_LIMIT, limit > 0 ? (float) limit : -1f);
	}

	/** Speed limit set by an administrator as the client sees it (blocks/s), NaN if none. */
	public double syncedSpeedLimit() {
		float v = dataTracker.get(SPEED_LIMIT);
		return v > 0 ? v : Double.NaN;
	}

	public void setGait(Gait g) {
		gait = g;
		dataTracker.set(GAIT, g.ordinal());
	}

	public void startRoute(Route route) {
		if (GotoRoutes.isGoto(routeName) && !routeName.equals(route.name) && getEntityWorld() instanceof ServerWorld sw) {
			ShipData.get(sw.getServer()).removeRoute(routeName); // an administrator's route replaces the destination
		}
		if (!GotoRoutes.isGoto(route.name)) {
			gotoByAdmin = false; // only a destination has an issuer (startGoto sets it)
		}
		routeName = route.name;
		aiEnabled = true;
		autopilot.start(route, pose(), config(), geometry());
		dataTracker.set(AUTOPILOT, true);
		// the helm belongs to the autopilot now
		Entity pilot = passengerInSeat(ShipGeometry.PILOT_SEAT);
		if (pilot instanceof PlayerEntity) {
			pilot.stopRiding();
		}
	}

	public void setAutopilot(boolean enabled) {
		if (enabled && !aiEnabled && getEntityWorld() instanceof ServerWorld sw) {
			Route route = ShipData.get(sw.getServer()).route(routeName);
			if (route != null) {
				startRoute(route);
				return;
			}
		}
		aiEnabled = enabled;
		if (!enabled) {
			autopilot.stop();
			if (getEntityWorld() instanceof ServerWorld sw) {
				ShipData.get(sw.getServer()).removeFerry(getUuid());
			}
		}
		dataTracker.set(AUTOPILOT, enabled);
		if (!enabled) {
			dataTracker.set(AUTOPILOT_INFO, "");
		}
	}

	/**
	 * Sends the vessel to a destination ({@link GotoRoutes}): its own one-point route, saved with the world, flown or
	 * sailed by the autopilot (which takes the helm). Replaces the previous destination.
	 *
	 * @param byAdmin given by an administrator ({@code /ship goto}): run like a ferry, its chunks kept loaded and the
	 *        trip reloaded after a restart. Otherwise ({@code /pilote goto}) it loads no chunks and is cancelled once
	 *        nobody has been aboard for {@link GotoRoutes#UNATTENDED_TICKS} ticks.
	 */
	public void startGoto(Route route, boolean byAdmin) {
		if (!(getEntityWorld() instanceof ServerWorld sw)) {
			return;
		}
		ShipData.get(sw.getServer()).putRoute(route);
		gotoByAdmin = byAdmin;
		unattendedTicks = 0;
		gotoUnreachable = false;
		if (!byAdmin) {
			ShipData.get(sw.getServer()).removeFerry(getUuid()); // a player's trip is never reloaded without him
		}
		startRoute(route);
		syncAutopilotInfo(sw);
	}

	/** Was the current destination given by an administrator ({@link #startGoto})? */
	public boolean gotoByAdmin() {
		return gotoByAdmin;
	}

	/**
	 * Does the autopilot keep its chunks loaded and its position remembered across restarts (a ferry)? Not for a
	 * player's destination (the players aboard load the chunks they are in), nor once a destination is reached: the
	 * vessel then just holds its position there.
	 */
	private boolean keepsChunksLoaded() {
		return aiEnabled && !(GotoRoutes.isGoto(routeName) && (!gotoByAdmin || autopilot.phase == Autopilot.Phase.FINISHED));
	}

	/**
	 * Destinations: cancels one the autopilot found unreachable, and a player's once nobody has been aboard for
	 * {@link GotoRoutes#UNATTENDED_TICKS} ticks (it cannot be used to send someone else's vessel away).
	 */
	private void gotoChecks(ServerWorld world) {
		if (gotoUnreachable) {
			gotoUnreachable = false;
			Route route = ShipData.get(world.getServer()).route(routeName);
			double left = route == null || route.size() == 0 ? Double.NaN : Math.hypot(route.get(0).x - getX(), route.get(0).z - getZ());
			if (cancelGoto()) {
				// stalled right by the point (a ship against the quay, an aircraft over a crowded spot): as good as there
				tellAround(world, Text.literal(left <= GotoRoutes.CLOSE_ENOUGH
						? String.format(java.util.Locale.ROOT, "%s : arrivé au plus près de la destination (à %.0f blocs), le pilote automatique rend la main.",
								vesselName(), left)
						: vesselName() + " : destination inaccessible, le pilote automatique rend la main.")
						.formatted(left <= GotoRoutes.CLOSE_ENOUGH ? Formatting.AQUA : Formatting.RED));
			}
		}
		if (!onGoto() || gotoByAdmin || age % 20 != 0) {
			return;
		}
		if (age % 200 == 0) {
			ShipData.get(world.getServer()).removeFerry(getUuid()); // never reloaded without its players (older saves)
		}
		unattendedTicks = playerAboard(world) ? 0 : unattendedTicks + 20;
		if (unattendedTicks >= GotoRoutes.UNATTENDED_TICKS && cancelGoto()) {
			MedievalShips.LOGGER.info("Ship {}: nobody aboard for {} s, destination cancelled", getUuid(), GotoRoutes.UNATTENDED_TICKS / 20);
			tellAround(world, Text.literal(vesselName() + " : plus personne à bord, la destination est annulée.").formatted(Formatting.YELLOW));
		}
	}

	/** Is a player (not a spectator) aboard: riding a seat, or standing on the decks or in the rooms? */
	private boolean playerAboard(ServerWorld world) {
		return !playersAboard(world).isEmpty();
	}

	/** The players (not spectators) aboard: riding a seat, or standing on the decks or in the rooms. */
	public List<ServerPlayerEntity> playersAboard(ServerWorld world) {
		List<ServerPlayerEntity> out = new ArrayList<>();
		for (ServerPlayerEntity p : world.getPlayers()) {
			if (!p.isSpectator() && isAboard(p)) {
				out.add(p);
			}
		}
		return out;
	}

	/** Is this entity aboard: riding a seat, or standing on the decks or in the rooms (server side)? */
	public boolean isAboard(Entity e) {
		if (e.getVehicle() == this) {
			return true;
		}
		double r = geometry().boundingRadius() + 2;
		if (e.getEntityWorld() != getEntityWorld() || e.squaredDistanceTo(getX(), getY(), getZ()) > r * r) {
			return false;
		}
		double[] l = pose().toLocal(e.getX(), e.getY(), e.getZ());
		return geometry().inCarryVolume(l[0], l[1], l[2]);
	}

	// ------------------------------------------------------------------ quest scripts: arrival commands, landing, end of trip

	/** Runs a command as the vessel at the next tick (a stop's {@link Waypoint#onArrive}). */
	public void queueCommand(String command) {
		if (command != null && !command.isBlank()) {
			pendingCommands.add(command);
		}
	}

	private void runPendingCommands(ServerWorld world) {
		if (pendingCommands.isEmpty()) {
			return;
		}
		List<String> commands = new ArrayList<>(pendingCommands);
		pendingCommands.clear();
		for (String command : commands) {
			String c = command.startsWith("/") ? command.substring(1) : command;
			MedievalShips.LOGGER.info("Ship {} ({}) runs: /{}", vesselName(), getUuid(), c);
			world.getServer().getCommandManager().parseAndExecute(scriptSource(world), c);
		}
	}

	/**
	 * The command source a scripted command of this vessel runs with: the vessel as the executing entity ({@code @s},
	 * its position and heading), the permission level of the administrators ({@code adminPermissionLevel}: exactly what
	 * whoever set the command may do, nothing more), its output in the server log and, like a command block's, sent to
	 * the operators when the game rule {@code commandBlockOutput} says so.
	 */
	public ServerCommandSource scriptSource(ServerWorld world) {
		CommandOutput output = new CommandOutput() {
			@Override
			public void sendMessage(Text message) {
				MedievalShips.LOGGER.info("[{}] {}", vesselName(), message.getString());
			}

			@Override
			public boolean shouldReceiveFeedback() {
				return false;
			}

			@Override
			public boolean shouldTrackOutput() {
				return true;
			}

			@Override
			public boolean shouldBroadcastConsoleToOps() {
				return world.getGameRules().getValue(GameRules.COMMAND_BLOCK_OUTPUT);
			}
		};
		int level = Math.max(0, Math.min(4, ConfigManager.server().adminPermissionLevel));
		return getCommandSource(world).withOutput(output)
				.withPermissions(LeveledPermissionPredicate.fromLevel(PermissionLevel.fromLevel(level)));
	}

	/**
	 * Where the passengers step off: a quay or the shore beside the hull (see {@link Landing}), null in open water.
	 */
	@Nullable
	public Vec3d landingSpot(ServerWorld world) {
		BlockPos.Mutable pos = new BlockPos.Mutable();
		double[] spot = Landing.find(geometry(), pose(), (x, y, z) -> {
			pos.set(x, y, z);
			if (!world.getFluidState(pos).isEmpty()) {
				return Landing.Block.LIQUID;
			}
			return world.getBlockState(pos).getCollisionShape(world, pos).isEmpty() ? Landing.Block.FREE : Landing.Block.SOLID;
		});
		return spot == null ? null : new Vec3d(spot[0], spot[1], spot[2]);
	}

	/**
	 * Lands every player aboard ({@code /ship disembark}, the end of a trip): at {@code where} when given, else on
	 * the quay or shore beside the hull. In open water, with nowhere to land, the players stay aboard and 0 is
	 * returned; players on seats are nevertheless stood up on the deck.
	 *
	 * @return the number of players landed
	 */
	public int disembark(ServerWorld world, @Nullable Vec3d where) {
		List<ServerPlayerEntity> players = playersAboard(world);
		if (players.isEmpty()) {
			return 0;
		}
		Vec3d spot = where != null ? where : landingSpot(world);
		if (spot == null) {
			for (ServerPlayerEntity p : players) {
				if (p.getVehicle() == this) {
					p.stopRiding();
				}
			}
			return 0;
		}
		int n = 0;
		for (ServerPlayerEntity p : players) {
			if (p.getVehicle() == this) {
				p.stopRiding();
			}
			// side by side rather than in a heap
			double a = n * 2.1, d = n == 0 ? 0 : 0.35 * Math.sqrt(n);
			p.teleport(world, spot.x + Math.cos(a) * d, spot.y, spot.z + Math.sin(a) * d, Set.<PositionFlag>of(), p.getYaw(), p.getPitch(), true);
			n++;
		}
		return n;
	}

	/**
	 * The end of a {@code once} / {@code return} route whose end makes the vessel vanish: the players are landed
	 * beside it, the NPC captain goes with it, its item is left on the spot if asked, and it is removed.
	 */
	private void endTrip(ServerWorld world, Route.End end) {
		int landed = disembark(world, null);
		for (Entity p : new ArrayList<>(getPassengerList())) {
			p.stopRiding();
			if (p.getCommandTags().contains("medievalships_captain")) {
				p.discard();
			}
		}
		if (end == Route.End.DESPAWN_ITEM) {
			dropStack(world, new ItemStack(item()), (float) geometry().hull().mainDeckY);
		}
		MedievalShips.LOGGER.info("Ship {} ({}) reached the end of route {}: {} player(s) landed, removed ({})", vesselName(), getUuid(),
				routeName, landed, end);
		tellAround(world, Text.literal(vesselName() + " a terminé son voyage.").formatted(Formatting.AQUA));
		setAutopilot(false);
		discard();
	}

	private String vesselName() {
		return hasCustomName() ? getCustomName().getString() : "Le navire";
	}

	/** A chat message to the players aboard and near the vessel (whatever {@code announceDepartures} says). */
	private void tellAround(ServerWorld world, Text text) {
		double r = Math.max(ConfigManager.server().announceRadius, geometry().boundingRadius() + 8);
		for (ServerPlayerEntity p : world.getPlayers(p -> p.squaredDistanceTo(this) < r * r)) {
			p.sendMessage(text, false);
		}
	}

	/** Is the autopilot following a destination given with {@code goto} (not an administrator's route)? */
	public boolean onGoto() {
		return aiEnabled && GotoRoutes.isGoto(routeName);
	}

	/**
	 * Cancels the destination given with {@code goto}: the autopilot lets go (an aircraft hovers where it is, a ship
	 * glides to a stop) and its route is forgotten. False if the vessel had no such destination.
	 */
	public boolean cancelGoto() {
		if (!GotoRoutes.isGoto(routeName)) {
			return false;
		}
		String name = routeName;
		setAutopilot(false);
		routeName = null;
		gotoByAdmin = false;
		unattendedTicks = 0;
		if (getEntityWorld() instanceof ServerWorld sw) {
			ShipData.get(sw.getServer()).removeRoute(name);
		}
		return true;
	}

	/** Autopilot state for the pilot's panel (client): see {@link #AUTOPILOT_INFO}. */
	public String syncedAutopilotInfo() {
		return dataTracker.get(AUTOPILOT_INFO);
	}

	private void syncAutopilotInfo(ServerWorld world) {
		String info = "";
		if (aiEnabled) {
			Route route = ShipData.get(world.getServer()).route(routeName);
			Waypoint wp = autopilot.currentTarget(route);
			if (wp != null) {
				String label = wp.label(autopilot.target).replace(';', ',');
				info = String.format(java.util.Locale.ROOT, "%s;%s;%s;%.1f;%.1f;%.1f", autopilot.phase.name(), routeName, label, wp.x, wp.y, wp.z);
			} else {
				info = autopilot.phase.name() + ";" + routeName + ";;;;";
			}
		}
		if (!info.equals(dataTracker.get(AUTOPILOT_INFO))) {
			dataTracker.set(AUTOPILOT_INFO, info);
		}
	}

	/** Sends route events (departure countdown, arrival...) to players aboard and nearby. */
	private final class Announcer implements Autopilot.Listener {
		private final ServerWorld world;
		private final Route route;

		Announcer(ServerWorld world, Route route) {
			this.world = world;
			this.route = route;
		}

		private void say(Text text, boolean actionBar) {
			if (!ConfigManager.server().announceDepartures) {
				return;
			}
			double r = ConfigManager.server().announceRadius;
			for (ServerPlayerEntity p : world.getPlayers(p -> p.squaredDistanceTo(ShipEntity.this) < r * r)) {
				p.sendMessage(text, actionBar);
			}
		}

		private String shipName() {
			return hasCustomName() ? getCustomName().getString() : "Le navire";
		}

		@Override
		public void countdown(int secondsLeft, Waypoint nextStop) {
			say(Text.literal(String.format("%s part vers %s dans %d s", shipName(),
					nextStop.label(route.points.indexOf(nextStop)), secondsLeft)).formatted(Formatting.YELLOW), secondsLeft <= 5);
		}

		@Override
		public void departing(Waypoint from, Waypoint next, int nextIndex) {
			say(Text.literal(shipName() + " lève l'ancre !").formatted(Formatting.GOLD), false);
		}

		@Override
		public void arrived(Waypoint stop, int index) {
			int wait = stop.waitSeconds;
			boolean terminus = route == null || Autopilot.next(route, index, autopilot.direction) == null;
			String then = terminus ? (route != null && route.end().despawns()
					? (stop.holds() ? "Terminus : il repartira sur ordre." : String.format("Terminus : il repartira dans %d s.", wait))
					: "Terminus.")
					: stop.holds() ? "Départ sur ordre." : String.format("Départ dans %d s.", wait);
			say(Text.literal(String.format("%s est arrivé à %s. %s", shipName(), stop.label(index), then)).formatted(Formatting.AQUA), false);
			if (stop.onArrive != null && !stop.onArrive.isBlank() && !GotoRoutes.isGoto(routeName)) {
				queueCommand(stop.onArrive);
			}
		}

		@Override
		public void countdownToEnd(int secondsLeft) {
			say(Text.literal(String.format("%s repart dans %d s : tout le monde à terre !", shipName(), secondsLeft)).formatted(Formatting.YELLOW),
					secondsLeft <= 5);
		}

		@Override
		public void stuck() {
			MedievalShips.LOGGER.warn("Ship {} on route {} is stuck at {}, {}, {}", getUuid(), routeName,
					(int) getX(), (int) getY(), (int) getZ());
			if (GotoRoutes.isGoto(routeName)) {
				// a destination it cannot reach (inland for a ship, walled in...): give it up and release its chunks
				gotoUnreachable = true;
				return;
			}
			Text msg = Text.literal(String.format("[Navires] %s est bloqué en %d %d %d (itinéraire %s). Ajoutez un point de passage ou utilisez /ship unstuck.",
					shipName(), (int) getX(), (int) getY(), (int) getZ(), routeName)).formatted(Formatting.RED);
			for (ServerPlayerEntity p : world.getServer().getPlayerManager().getPlayerList()) {
				if (ShipPermissions.isAdmin(p)) {
					p.sendMessage(msg, false);
				}
			}
		}

		@Override
		public void finished() {
			if (GotoRoutes.isGoto(routeName)) {
				ShipData.get(world.getServer()).removeFerry(getUuid()); // arrived: nothing to reload after a restart
			} else if (route != null && route.end().despawns()) {
				pendingEnd = route.end(); // removed at the next tick, not from inside the autopilot's tick
				return;
			}
			say(Text.literal(shipName() + " est arrivé à destination.").formatted(Formatting.AQUA), false);
		}
	}

	// ------------------------------------------------------------------ seats & passengers

	/** Seats the given entity at a specific seat (server side). */
	public boolean seat(Entity passenger, int seat) {
		if (seat < 0 || seat >= geometry().seats().size() || passengerInSeat(seat) != null) {
			return false;
		}
		if (passenger.hasVehicle()) {
			passenger.stopRiding();
		}
		pendingSeat = seat;
		boolean ok = passenger.startRiding(this);
		pendingSeat = -1;
		return ok;
	}

	@Nullable
	public Entity passengerInSeat(int seat) {
		Map<Integer, Integer> map = getEntityWorld().isClient() ? clientSeats : seatByEntity;
		for (Entity p : getPassengerList()) {
			Integer s = map.get(p.getId());
			if (s != null && s == seat) {
				return p;
			}
		}
		return null;
	}

	public int seatOf(Entity passenger) {
		Map<Integer, Integer> map = getEntityWorld().isClient() ? clientSeats : seatByEntity;
		return map.getOrDefault(passenger.getId(), -1);
	}

	public int freeSeat(boolean pilot) {
		if (pilot) {
			return passengerInSeat(ShipGeometry.PILOT_SEAT) == null ? ShipGeometry.PILOT_SEAT : -1;
		}
		for (ShipGeometry.Seat s : geometry().seats()) {
			if (!s.pilot() && passengerInSeat(s.index()) == null) {
				return s.index();
			}
		}
		return -1;
	}

	@Override
	protected boolean canAddPassenger(Entity passenger) {
		return getPassengerList().size() < geometry().seats().size();
	}

	@Override
	protected void addPassenger(Entity passenger) {
		super.addPassenger(passenger);
		if (getEntityWorld().isClient()) {
			return;
		}
		int seat = pendingSeat;
		if (seat < 0 || passengerInSeat(seat) != null) {
			// passengers added by other means (/ride, saved NPC captain...)
			boolean npcCaptain = !(passenger instanceof PlayerEntity) && passengerInSeat(ShipGeometry.PILOT_SEAT) == null;
			seat = npcCaptain ? ShipGeometry.PILOT_SEAT : freeSeat(false);
			if (seat < 0) {
				seat = freeSeat(true);
			}
		}
		// the last seats of entities gone for good are forgotten (an entity id comes back with a respawned player)
		lastSeatByEntity.keySet().removeIf(id -> !seatByEntity.containsKey(id) && id != passenger.getId());
		seatByEntity.put(passenger.getId(), seat);
		lastSeatByEntity.put(passenger.getId(), seat);
		seatsDirty = true;
		syncSeats();
	}

	@Override
	protected void removePassenger(Entity passenger) {
		if (getEntityWorld().isClient() && passenger instanceof PlayerEntity player && player.isMainPlayer()) {
			// the client keeps its own player where it sat (the server's teleport arrives while it
			// is still seated): put it on its seat's standing spot, never inside a castle floor
			ShipGeometry.Seat seat = seatFor(passenger);
			super.removePassenger(passenger);
			double[] w = pose().toWorld(seat.dismountLocal()[0], seat.dismountLocal()[1], seat.dismountLocal()[2]);
			passenger.setPosition(w[0], w[1], w[2]);
			return;
		}
		super.removePassenger(passenger);
		if (!getEntityWorld().isClient()) {
			seatByEntity.remove(passenger.getId());
			syncSeats();
		}
	}

	private void syncSeats() {
		seatsDirty = false;
		StringBuilder sb = new StringBuilder();
		for (Map.Entry<Integer, Integer> e : seatByEntity.entrySet()) {
			if (sb.length() > 0) {
				sb.append(',');
			}
			sb.append(e.getKey()).append(':').append(e.getValue());
		}
		dataTracker.set(SEATS, sb.toString());
	}

	private void parseSeats() {
		String s = dataTracker.get(SEATS);
		if (s.equals(parsedSeats)) {
			return;
		}
		parsedSeats = s;
		clientSeats.clear();
		if (s.isEmpty()) {
			return;
		}
		for (String part : s.split(",")) {
			String[] kv = part.split(":");
			try {
				clientSeats.put(Integer.parseInt(kv[0]), Integer.parseInt(kv[1]));
				lastSeatByEntity.put(Integer.parseInt(kv[0]), Integer.parseInt(kv[1]));
			} catch (RuntimeException ignored) {
				// malformed entry: ignore
			}
		}
	}

	@Override
	@Nullable
	public LivingEntity getControllingPassenger() {
		return null; // movement is server-authoritative, the helmsman only sends his inputs
	}

	private ShipGeometry.Seat seatFor(Entity passenger) {
		if (getEntityWorld().isClient()) {
			parseSeats();
		}
		int s = seatOf(passenger);
		if (s < 0) {
			// already off its seat (dismounting): the seat it has just left
			s = lastSeatByEntity.getOrDefault(passenger.getId(), ShipGeometry.PILOT_SEAT);
		}
		return s >= 0 && s < geometry().seats().size() ? geometry().seats().get(s) : geometry().seats().get(ShipGeometry.PILOT_SEAT);
	}

	/** Does this passenger stand (a player at the helm) rather than sit? */
	public boolean standsAtHelm(Entity passenger) {
		if (!(passenger instanceof PlayerEntity)) {
			return false;
		}
		if (getEntityWorld().isClient()) {
			parseSeats();
		}
		return seatOf(passenger) == ShipGeometry.PILOT_SEAT;
	}

	@Override
	protected Vec3d getPassengerAttachmentPos(Entity passenger, EntityDimensions dimensions, float scaleFactor) {
		ShipGeometry.Seat seat = seatFor(passenger);
		double lift = standsAtHelm(passenger) ? HELM_STAND_LIFT : 0.0;
		double[] d = pose().dirToWorld(seat.x(), seat.y() + lift, seat.z());
		return new Vec3d(d[0], d[1], d[2]);
	}

	@Override
	protected void updatePassengerPosition(Entity passenger, PositionUpdater positionUpdater) {
		super.updatePassengerPosition(passenger, positionUpdater);
		if (yawDelta != 0) {
			passenger.setYaw(passenger.getYaw() + yawDelta);
			passenger.setHeadYaw(passenger.getHeadYaw() + yawDelta);
			if (passenger instanceof LivingEntity living && !(passenger instanceof PlayerEntity)) {
				living.setBodyYaw(living.bodyYaw + yawDelta);
			}
		}
		if (seatOf(passenger) == ShipGeometry.PILOT_SEAT && !(passenger instanceof PlayerEntity)) {
			// NPC helmsman faces the bow
			passenger.setYaw(getYaw());
			passenger.setHeadYaw(getYaw());
			if (passenger instanceof LivingEntity living) {
				living.setBodyYaw(getYaw());
			}
		}
	}

	@Override
	public Vec3d updatePassengerForDismount(LivingEntity passenger) {
		ShipGeometry.Seat seat = seatFor(passenger);
		double[] local = seat.dismountLocal();
		double[] w = pose().toWorld(local[0], local[1], local[2]);
		return new Vec3d(w[0], w[1], w[2]);
	}

	/** Puts an entity on the deck at the standing spot nearest to the given world position. */
	public Vec3d boardingPosition(double wx, double wz) {
		ShipPose p = pose();
		double[] l = p.toLocal(wx, getY(), wz);
		double[] spot = geometry().boardingSpot(l[0], l[2]);
		double[] w = p.toWorld(spot[0], spot[1], spot[2]);
		return new Vec3d(w[0], w[1], w[2]);
	}
}
