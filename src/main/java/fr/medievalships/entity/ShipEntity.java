package fr.medievalships.entity;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

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

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Autopilot;
import fr.medievalships.core.Gait;
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

	private static final double DT = 0.05;

	// ---- server state
	private final ShipPhysics physics = new ShipPhysics();
	private final Autopilot autopilot = new Autopilot();
	private boolean aiEnabled;
	@Nullable
	private String routeName;
	private Gait gait = Gait.NORMAL;
	/** Per-ship maximum speed in blocks/s, NaN = use the gaits from the config. */
	private double speedLimit = Double.NaN;
	private final Map<Integer, Integer> seatByEntity = new HashMap<>();
	private int pendingSeat = -1;
	private int stoppedTicks;
	private boolean lastJump;
	private boolean lastSprint;
	private boolean seatsDirty;

	// ---- shared / client state
	private final PositionInterpolator interpolator = new PositionInterpolator(this, 3);
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
	public float sailOpen = 1f;
	public float lastSailOpen = 1f;
	public float helmVisual;
	public float lastHelmVisual;
	public float rockTime;

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
	}

	@Override
	protected void readCustomData(ReadView view) {
		physics.speed = view.getDouble("Speed", 0);
		physics.yawRate = view.getDouble("YawRate", 0);
		physics.helm = view.getDouble("Helm", 0);
		gait = Gait.byOrdinal(view.getInt("Gait", Gait.NORMAL.ordinal()));
		double limit = view.getDouble("SpeedLimit", -1);
		speedLimit = limit > 0 ? limit : Double.NaN;
		aiEnabled = view.getBoolean("Autopilot", false);
		String route = view.getString("Route", "");
		routeName = route.isEmpty() ? null : route;
		autopilot.target = view.getInt("ApTarget", 0);
		autopilot.direction = view.getInt("ApDirection", 1);
		autopilot.phase = Autopilot.Phase.values()[Math.max(0, Math.min(Autopilot.Phase.values().length - 1,
				view.getInt("ApPhase", 0)))];
		autopilot.waitTicks = view.getInt("ApWait", 0);
		autopilot.legStartX = view.getDouble("ApLegX", getX());
		autopilot.legStartZ = view.getDouble("ApLegZ", getZ());
		setShipYaw(getYaw());
		dataTracker.set(AUTOPILOT, aiEnabled);
		dataTracker.set(GAIT, gait.ordinal());
	}

	@Override
	protected void writeCustomData(WriteView view) {
		view.putDouble("Speed", physics.speed);
		view.putDouble("YawRate", physics.yawRate);
		view.putDouble("Helm", physics.helm);
		view.putInt("Gait", gait.ordinal());
		view.putDouble("SpeedLimit", Double.isNaN(speedLimit) ? -1 : speedLimit);
		view.putBoolean("Autopilot", aiEnabled);
		view.putString("Route", routeName == null ? "" : routeName);
		view.putInt("ApTarget", autopilot.target);
		view.putInt("ApDirection", autopilot.direction);
		view.putInt("ApPhase", autopilot.phase.ordinal());
		view.putInt("ApWait", autopilot.waitTicks);
		view.putDouble("ApLegX", autopilot.legStartX);
		view.putDouble("ApLegZ", autopilot.legStartZ);
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

	@Override
	public void onRemove(RemovalReason reason) {
		// called for every removal, including chunk unloading and client-side despawn
		ShipTracker.remove(this);
		super.onRemove(reason);
	}

	@Override
	public void remove(RemovalReason reason) {
		if (reason.shouldDestroy() && getEntityWorld() instanceof ServerWorld sw) {
			ShipData.get(sw.getServer()).removeFerry(getUuid());
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
		if (Math.abs(diff) > 45) {
			setYaw(target);
		}
		parseSeats();
		ShipConfig cfg = config();

		lastOarPhase = oarPhase;
		lastOarWeight = oarWeight;
		lastSailOpen = sailOpen;
		lastHelmVisual = helmVisual;
		float speed = Math.abs(syncedSpeed());
		float rowing = speed > 0.15f ? 1f : 0f;
		oarWeight += (rowing - oarWeight) * 0.06f;
		oarPhase += (float) (DT * Math.max(0.35, Math.min(1.6, speed / cfg.normalSpeed)) * oarWeight);
		sailOpen += ((sailSet() ? 1f : 0f) - sailOpen) * 0.05f;
		helmVisual += (syncedHelm() - helmVisual) * 0.3f;
		rockTime += DT;
	}

	private void serverTick(ServerWorld world) {
		ShipConfig cfg = config();
		ShipWorld shipWorld = new ShipWorld(world, this);
		ShipPose before = pose();
		if (seatsDirty) {
			syncSeats();
		}

		// ---- controls
		ShipPhysics.Controls controls;
		Entity pilot = passengerInSeat(ShipGeometry.PILOT_SEAT);
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
		ShipPhysics.Step step = physics.step(controls, cfg, DT);

		// ---- buoyancy: follow the water surface under the hull
		double dy = 0;
		double sBow = shipWorld.waterSurface(before.worldX(0, 7), before.worldZ(0, 7), getY());
		double sMid = shipWorld.waterSurface(getX(), getZ(), getY());
		double sStern = shipWorld.waterSurface(before.worldX(0, -7), before.worldZ(0, -7), getY());
		double sum = 0;
		int n = 0;
		for (double s : new double[] {sBow, sMid, sStern}) {
			if (!Double.isNaN(s)) {
				sum += s;
				n++;
			}
		}
		if (n > 0) {
			dy = Math.max(-0.15, Math.min(0.15, (sum / n - getY()) * 0.3));
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
		if (aiEnabled && age % 20 == 0) {
			if (ConfigManager.server().chunkLoadAutopilotShips) {
				ChunkPos here = new ChunkPos(BlockPos.ofFloored(getX(), getY(), getZ()));
				world.getChunkManager().addTicket(ChunkTicketType.PORTAL, here, ConfigManager.server().chunkLoadRadius);
				double ahead = 24 * Math.signum(physics.speed == 0 ? 1 : physics.speed);
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

		if (pilot instanceof ServerPlayerEntity player && age % 10 == 0) {
			player.sendMessage(helmStatus(cfg), true);
		}
	}

	private ShipPhysics.Controls manualControls(ServerPlayerEntity player, ShipConfig cfg) {
		PlayerInput in = player.getPlayerInput();
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

	private Text helmStatus(ShipConfig cfg) {
		double kmh = Math.abs(physics.speed) * 3.6;
		String dir = physics.speed < -0.05 ? " (arrière)" : "";
		String limit = Double.isNaN(speedLimit) ? "" : String.format(" max %.1f", speedLimit);
		return Text.literal(String.format("Allure %s%s - %.1f blocs/s (%.0f km/h)%s  [Espace/Ctrl: allure, Maj: quitter]",
				gait.frenchName(), limit, Math.abs(physics.speed), kmh, dir)).formatted(Formatting.GOLD);
	}

	/** Moves mobs, items and other entities standing on the deck along with the hull (server side). */
	private void carryEntities(ServerWorld world, ShipPose before, ShipPose after) {
		double dYaw = after.yaw() - before.yaw();
		double r = geometry().boundingRadius();
		Box area = new Box(before.x() - r, before.y() - 2, before.z() - r, before.x() + r, before.y() + 8, before.z() + r);
		List<Entity> list = world.getOtherEntities(this, area, e -> !(e instanceof PlayerEntity) && !e.hasVehicle()
				&& !(e instanceof ShipEntity) && !e.isRemoved());
		for (Entity e : list) {
			double[] l = before.toLocal(e.getX(), e.getY(), e.getZ());
			if (!geometry().inCarryVolume(l[0], l[1], l[2])) {
				continue;
			}
			double rescue = geometry().deckRescueY(l[0], l[1], l[2]);
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
	}

	public void setGait(Gait g) {
		gait = g;
		dataTracker.set(GAIT, g.ordinal());
	}

	public void startRoute(Route route) {
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
			say(Text.literal(String.format("%s est arrivé à %s. Départ dans %d s.", shipName(), stop.label(index), wait))
					.formatted(Formatting.AQUA), false);
		}

		@Override
		public void stuck() {
			MedievalShips.LOGGER.warn("Ship {} on route {} is stuck at {}, {}, {}", getUuid(), routeName,
					(int) getX(), (int) getY(), (int) getZ());
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
		seatByEntity.put(passenger.getId(), seat);
		seatsDirty = true;
		syncSeats();
	}

	@Override
	protected void removePassenger(Entity passenger) {
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
		return s >= 0 && s < geometry().seats().size() ? geometry().seats().get(s) : geometry().seats().get(ShipGeometry.PILOT_SEAT);
	}

	@Override
	protected Vec3d getPassengerAttachmentPos(Entity passenger, EntityDimensions dimensions, float scaleFactor) {
		ShipGeometry.Seat seat = seatFor(passenger);
		double[] d = pose().dirToWorld(seat.x(), seat.y(), seat.z());
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
