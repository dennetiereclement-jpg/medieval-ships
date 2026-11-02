package fr.medievalships.training;

import java.util.function.BiFunction;

import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;
import org.joml.Vector3fc;

import net.minecraft.block.Blocks;
import net.minecraft.block.piston.PistonBehavior;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityPose;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LightningEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.MovementType;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.projectile.ProjectileEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.BlockStateParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.tag.DamageTypeTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Arm;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;
import net.minecraft.world.explosion.Explosion;

import fr.medievalships.core.TargetMotion;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.core.TrainingTarget;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.tent.Tents;

/**
 * A training target of a training area (entity type {@code medievalships:training_target}, 1.19.0): the dummy, the
 * sword-and-shield dummy or the punching bag that players hit, one entity per {@link TrainingTarget} of the area's
 * JSON, spawned and removed by {@link TrainingTargets} (never saved: the area spawns it again when its chunk loads).
 *
 * <p>A living entity so that every vanilla attack reaches it the normal way (fists, swords, axes, maces, spears,
 * tridents, arrows, crossbow bolts, any mod damage that goes through {@link #damage}), but with no AI, no gravity, no
 * movement at all (held at its home, knockback resistance 1, nothing pushes it, velocity always zero), immune to fire,
 * explosions, lightning, status effects, drowning and falls, and it never loses health nor dies ({@link #kill} and
 * {@link #onDeath} do nothing: {@code /tent remove} is the way to take an area and its targets away). Its box is the
 * target's hitbox (with its shield), turned with the area's facing, known to the clients through tracked data.
 *
 * <p>A hit ({@link #damage}) deals no damage and returns false (no knockback, no successful-hit effects, no durability
 * lost, no experience, no loot, the arrows bounce off): it works out the direction of the hit (the attacker's look,
 * the projectile's flight) and the part hit (the shield or the body of a sword-and-shield dummy: the first box the ray
 * meets), plays a sound (straw and wood for the dummies, a thud and the chain for the bag, a clang for the shield; at
 * most one every {@link #SOUND_GAP} ticks), spawns a few particles, and sends the reaction to the clients in its tracked
 * data (a hit counter, the direction times the strength, the hit point, the part). Each client then plays the reaction
 * with a {@link TargetMotion} (stepped in {@link #tick} only while it moves) that TrainingTargetRenderer draws.
 *
 * <p>Server cost: {@link #tick} does nothing but keep it at its home and, every {@link #CHECK_PERIOD} ticks, check that
 * its area still stands (an orphan discards itself). Nothing at all on the client at rest.
 */
public class TrainingTargetEntity extends LivingEntity {
	private static final TrackedData<BlockPos> ANCHOR = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.BLOCK_POS);
	/** The target's index in its area's list, plus the facing's quarter turns times 256. */
	private static final TrackedData<Integer> SLOT = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.INTEGER);
	/** The area's prop id. */
	private static final TrackedData<String> PROP = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.STRING);
	/** Width (world x), height, depth (world z) of the box. */
	private static final TrackedData<Vector3fc> SIZE = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.VECTOR_3F);
	/** The last hit: its horizontal direction (world) times its strength, its point (from the entity's position), its part. */
	private static final TrackedData<Vector3fc> HIT_DIR = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.VECTOR_3F);
	private static final TrackedData<Vector3fc> HIT_POINT = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.VECTOR_3F);
	private static final TrackedData<Byte> HIT_PART = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.BYTE);
	/** The number of hits so far (registered last: when a client sees it change, the hit's other fields are already set). */
	private static final TrackedData<Integer> HITS = DataTracker.registerData(TrainingTargetEntity.class, TrackedDataHandlerRegistry.INTEGER);

	/** At most one hit sound every this many ticks per target. */
	public static final int SOUND_GAP = 3;
	/** The orphan check period (ticks). */
	public static final int CHECK_PERIOD = 40;

	/**
	 * Client side: the prop-local origins of a target's bones ({@link TargetMotion#ROOT}... {@link TargetMotion#SWORD}),
	 * read from the model by the client initializer; null entries for bones the model lacks.
	 */
	public static BiFunction<TentType, TrainingTarget, double[][]> joints = (type, target) -> null;

	/** Server side: where it is held. */
	@Nullable
	private Vec3d home;
	private long lastSound = Long.MIN_VALUE;
	/** The prop resolved from {@link #PROP} (both sides). */
	@Nullable
	private TentType prop;
	/** Client side: the hit counter already played (MIN_VALUE until the first tick: older hits are not replayed). */
	private int seenHits = Integer.MIN_VALUE;
	/** Client side: the reaction being played, created on the first hit seen. */
	@Nullable
	private TargetMotion motion;

	public TrainingTargetEntity(EntityType<? extends TrainingTargetEntity> type, World world) {
		super(type, world);
		this.noClip = true;
		this.setNoGravity(true);
	}

	public static DefaultAttributeContainer.Builder createAttributes() {
		return LivingEntity.createLivingAttributes().add(EntityAttributes.MAX_HEALTH, 20.0).add(EntityAttributes.KNOCKBACK_RESISTANCE, 1.0)
				.add(EntityAttributes.EXPLOSION_KNOCKBACK_RESISTANCE, 1.0).add(EntityAttributes.GRAVITY, 0.0);
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		super.initDataTracker(builder);
		builder.add(ANCHOR, BlockPos.ORIGIN);
		builder.add(SLOT, 0);
		builder.add(PROP, "");
		builder.add(SIZE, new Vector3f());
		builder.add(HIT_DIR, new Vector3f());
		builder.add(HIT_POINT, new Vector3f());
		builder.add(HIT_PART, (byte) 0);
		builder.add(HITS, 0);
	}

	/**
	 * Server side, before spawning: binds the entity to target {@code index} of the area of {@code type} at
	 * {@code anchor} facing {@code quarter}, sizes its box and puts it at its home.
	 */
	public void bind(BlockPos anchor, TentType type, int index, int quarter) {
		TrainingTarget t = type.targets(quarter).get(index);
		TentType.Box r = t.reach();
		dataTracker.set(ANCHOR, anchor.toImmutable());
		dataTracker.set(SLOT, index | (quarter & 3) << 8);
		dataTracker.set(PROP, type.id());
		dataTracker.set(SIZE, new Vector3f((float) r.width(), (float) r.height(), (float) r.depth()));
		prop = type;
		home = home(anchor, t);
		setPosition(home);
		calculateDimensions();
		setYaw(0);
		setBodyYaw(0);
		setHeadYaw(0);
	}

	/** The home of a (facing-turned) target of the area at {@code anchor}: the bottom centre of its box. */
	public static Vec3d home(BlockPos anchor, TrainingTarget turned) {
		TentType.Box r = turned.reach();
		return new Vec3d(anchor.getX() + 0.5 + (r.x0() + r.x1()) / 2, anchor.getY() + r.y0(), anchor.getZ() + 0.5 + (r.z0() + r.z1()) / 2);
	}

	public BlockPos anchor() {
		return dataTracker.get(ANCHOR);
	}

	public int index() {
		return dataTracker.get(SLOT) & 0xFF;
	}

	public int quarter() {
		return dataTracker.get(SLOT) >> 8 & 3;
	}

	/** The area's prop, or null while unknown (a client that has not received the data yet). */
	@Nullable
	public TentType prop() {
		if (prop == null || !prop.id().equals(dataTracker.get(PROP))) {
			prop = TentTypes.byId(dataTracker.get(PROP));
		}
		return prop;
	}

	/** The target, turned to the area's facing, or null when the data does not name one. */
	@Nullable
	public TrainingTarget target() {
		TentType type = prop();
		int i = index();
		return type != null && i < type.targets().size() ? type.targets(quarter()).get(i) : null;
	}

	/** The target prop-local (facing south), or null. */
	@Nullable
	public TrainingTarget localTarget() {
		TentType type = prop();
		int i = index();
		return type != null && i < type.targets().size() ? type.targets().get(i) : null;
	}

	/** The number of hits it received (both sides; the client's copy follows the server's). */
	public int hits() {
		return dataTracker.get(HITS);
	}

	/** The part the last hit landed on ({@link TrainingTarget#PART_BODY}, {@link TrainingTarget#PART_SHIELD}). */
	public int lastPart() {
		return dataTracker.get(HIT_PART);
	}

	/** The last hit's strength (0..1). */
	public float lastStrength() {
		return dataTracker.get(HIT_DIR).length();
	}

	/** Client side: the reaction being played, or null before the first hit. */
	@Nullable
	public TargetMotion motion() {
		return motion;
	}

	/** A box of the target in world coordinates (a facing-turned prop-local box). */
	public Box worldBox(TentType.Box b) {
		BlockPos a = anchor();
		double cx = a.getX() + 0.5, cy = a.getY(), cz = a.getZ() + 0.5;
		return new Box(cx + b.x0(), cy + b.y0(), cz + b.z0(), cx + b.x1(), cy + b.y1(), cz + b.z1());
	}

	// ------------------------------------------------------------------ box

	@Override
	protected EntityDimensions getBaseDimensions(EntityPose pose) {
		Vector3fc s = dataTracker == null ? null : dataTracker.get(SIZE);
		if (s == null || s.x() <= 0 || s.y() <= 0) {
			return super.getBaseDimensions(pose);
		}
		return EntityDimensions.changing(Math.max(s.x(), s.z()), s.y());
	}

	/** The exact box of the target (not square like the vanilla ones): its hitbox with its shield. */
	@Override
	protected Box calculateDefaultBoundingBox(Vec3d pos) {
		Vector3fc s = dataTracker == null ? null : dataTracker.get(SIZE);
		if (s == null || s.x() <= 0 || s.y() <= 0) {
			return super.calculateDefaultBoundingBox(pos);
		}
		return new Box(pos.x - s.x() / 2, pos.y, pos.z - s.z() / 2, pos.x + s.x() / 2, pos.y + s.y(), pos.z + s.z() / 2);
	}

	@Override
	public void onTrackedDataSet(TrackedData<?> data) {
		super.onTrackedDataSet(data);
		if (SIZE.equals(data)) {
			calculateDimensions();
		} else if (PROP.equals(data)) {
			prop = null;
		}
	}

	// ------------------------------------------------------------------ hits

	/**
	 * A hit: never any damage (returns false), but the reaction (direction, part, strength), a sound and a few particles.
	 * Damage with no attacker and no source entity (fire, cactus, the void, {@code /kill}) is ignored.
	 */
	@Override
	public boolean damage(ServerWorld world, DamageSource source, float amount) {
		TrainingTarget t = target();
		if (isRemoved() || t == null || source.isIn(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			return false;
		}
		Entity direct = source.getSource();
		Entity attacker = source.getAttacker();
		Entity from = direct != null ? direct : attacker;
		Vec3d sourcePos = source.getPosition();
		if (from == null && sourcePos == null) {
			return false;
		}
		Box body = worldBox(t.hitbox());
		Box shield = t.hasShield() ? worldBox(t.shieldBox()) : null;
		Vec3d centre = body.getCenter();
		// the ray that brought the hit: a projectile's flight, an attacker's look
		Vec3d origin, ray;
		if (from instanceof ProjectileEntity p) {
			origin = p.getEntityPos();
			ray = p.getVelocity();
			if (ray.lengthSquared() < 1e-6) {
				ray = centre.subtract(origin);
			}
		} else if (from != null) {
			origin = from.getEyePos();
			ray = from.getRotationVector();
		} else {
			origin = sourcePos;
			ray = centre.subtract(origin);
		}
		double tBody = rayBox(body, origin, ray), tShield = shield == null ? Double.POSITIVE_INFINITY : rayBox(shield, origin, ray);
		if (Double.isInfinite(tBody) && Double.isInfinite(tShield)) {
			// a hit that does not come along its ray (a sweep, an area spell): along the line to the body's centre
			ray = centre.subtract(origin);
			tBody = rayBox(body, origin, ray);
			tShield = shield == null ? Double.POSITIVE_INFINITY : rayBox(shield, origin, ray);
		}
		int part = shield != null && tShield <= tBody + 0.05 ? TrainingTarget.PART_SHIELD : TrainingTarget.PART_BODY;
		double tHit = part == TrainingTarget.PART_SHIELD ? tShield : tBody;
		Vec3d point = Double.isFinite(tHit) ? origin.add(ray.multiply(tHit)) : centre;
		// the push: horizontal, from the attacker towards the target
		Vec3d push = new Vec3d(ray.x, 0, ray.z);
		if (push.lengthSquared() < 1e-6) {
			push = new Vec3d(centre.x - origin.x, 0, centre.z - origin.z);
		}
		if (push.lengthSquared() < 1e-6) {
			push = new Vec3d(0, 0, 1);
		}
		float strength = TrainingTarget.strength(amount);
		push = push.normalize().multiply(strength);
		dataTracker.set(HIT_DIR, new Vector3f((float) push.x, 0f, (float) push.z));
		dataTracker.set(HIT_POINT, new Vector3f((float) (point.x - getX()), (float) (point.y - getY()), (float) (point.z - getZ())));
		dataTracker.set(HIT_PART, (byte) part);
		dataTracker.set(HITS, dataTracker.get(HITS) + 1);
		long now = world.getTime();
		if (now - lastSound >= SOUND_GAP || now < lastSound) {
			lastSound = now;
			effects(world, t, part, point, strength);
		}
		return false;
	}

	/** The sound and the few particles of a hit. */
	private void effects(ServerWorld world, TrainingTarget t, int part, Vec3d p, float strength) {
		float pitch = 0.9f + random.nextFloat() * 0.2f;
		float volume = 0.55f + 0.45f * strength;
		if (part == TrainingTarget.PART_SHIELD) {
			// the clang of the shield (wood and iron)
			world.playSound(null, p.x, p.y, p.z, SoundEvents.ITEM_SHIELD_BLOCK.value(), SoundCategory.PLAYERS, volume, pitch);
			world.playSound(null, p.x, p.y, p.z, SoundEvents.BLOCK_CHAIN_HIT, SoundCategory.PLAYERS, 0.5f * volume, 1.4f * pitch);
			world.spawnParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 4, 0.08, 0.08, 0.08, 0.15);
		} else if (t.kind() == TrainingTarget.Kind.BAG) {
			// a dull thud of the stuffed leather, the chain rattling
			world.playSound(null, p.x, p.y, p.z, SoundEvents.BLOCK_WOOL_BREAK, SoundCategory.PLAYERS, volume, 0.75f * pitch);
			world.playSound(null, p.x, p.y, p.z, SoundEvents.BLOCK_CHAIN_STEP, SoundCategory.PLAYERS, 0.4f * volume, pitch);
			world.spawnParticles(new BlockStateParticleEffect(ParticleTypes.BLOCK, Blocks.BROWN_WOOL.getDefaultState()), p.x, p.y, p.z, 3, 0.1, 0.1,
					0.1, 0.05);
		} else {
			// straw and the wooden frame of the dummy
			world.playSound(null, p.x, p.y, p.z, SoundEvents.ENTITY_ARMOR_STAND_HIT, SoundCategory.PLAYERS, volume, pitch);
			world.playSound(null, p.x, p.y, p.z, SoundEvents.BLOCK_GRASS_BREAK, SoundCategory.PLAYERS, 0.5f * volume, pitch);
			world.spawnParticles(new BlockStateParticleEffect(ParticleTypes.BLOCK, Blocks.HAY_BLOCK.getDefaultState()), p.x, p.y, p.z, 4, 0.1, 0.12,
					0.1, 0.05);
		}
	}

	/** {@link TrainingTarget#rayBox} with Minecraft vectors and boxes. */
	private static double rayBox(Box b, Vec3d o, Vec3d d) {
		return TrainingTarget.rayBox(new TentType.Box(b.minX, b.minY, b.minZ, b.maxX, b.maxY, b.maxZ), o.x, o.y, o.z, d.x, d.y, d.z);
	}

	// ------------------------------------------------------------------ tick

	/**
	 * Server: held at its home, and every {@link #CHECK_PERIOD} ticks an orphan check (its area gone: discarded).
	 * Client: plays the new hits and steps the reaction while it moves. No AI, no movement, no base tick.
	 */
	@Override
	public void tick() {
		World world = getEntityWorld();
		if (world.isClient()) {
			clientTick();
			return;
		}
		if (home == null) {
			discard(); // not bound to an area (never spawned by TrainingTargets)
			return;
		}
		if (getX() != home.x || getY() != home.y || getZ() != home.z) {
			setPosition(home);
		}
		if ((age + getId()) % CHECK_PERIOD == 0 && world instanceof ServerWorld sw && !TrainingTargets.stillStands(sw, this)) {
			// its area is gone, or turned (a new facing: its targets are spawned again)
			discard();
			TrainingTargets.request(sw, anchor());
		}
	}

	private void clientTick() {
		int hits = dataTracker.get(HITS);
		if (seenHits == Integer.MIN_VALUE) {
			seenHits = hits;
		} else if (hits != seenHits) {
			seenHits = hits;
			playHit(hits);
		}
		if (motion != null && motion.moving()) {
			motion.tick();
		}
	}

	/** Client side: gives the last hit (world data) to the reaction, in the area's own axes. */
	private void playHit(int seed) {
		TentType type = prop();
		TrainingTarget local = localTarget();
		if (type == null || local == null) {
			return;
		}
		if (motion == null || motion.target() != local) {
			motion = new TargetMotion(local, joints.apply(type, local));
		}
		int q = quarter();
		Vector3fc d = dataTracker.get(HIT_DIR);
		Vector3fc o = dataTracker.get(HIT_POINT);
		BlockPos a = anchor();
		double[] dir = TrainingTarget.unrotate(d.x(), d.z(), q);
		double wx = getX() + o.x() - (a.getX() + 0.5), wz = getZ() + o.z() - (a.getZ() + 0.5);
		double[] p = TrainingTarget.unrotate(wx, wz, q);
		motion.hit(dir[0], dir[1], d.length(), dataTracker.get(HIT_PART), p[0], getY() + o.y() - a.getY(), p[1], seed);
	}

	// ------------------------------------------------------------------ nothing moves it, nothing hurts it

	@Override
	public void move(MovementType type, Vec3d movement) {
	}

	@Override
	public void setVelocity(Vec3d velocity) {
	}

	@Override
	public void addVelocity(double deltaX, double deltaY, double deltaZ) {
	}

	@Override
	public void addVelocityInternal(Vec3d velocity) {
	}

	@Override
	public void takeKnockback(double strength, double x, double z) {
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	protected void pushAway(Entity entity) {
	}

	@Override
	public void pushAwayFrom(Entity entity) {
	}

	@Override
	public PistonBehavior getPistonBehavior() {
		return PistonBehavior.IGNORE;
	}

	@Override
	protected boolean canStartRiding(Entity entity) {
		return false;
	}

	@Override
	public boolean canUsePortals(boolean allowVehicles) {
		return false;
	}

	@Override
	public boolean hasNoGravity() {
		return true;
	}

	@Override
	public boolean isFireImmune() {
		return true;
	}

	@Override
	public boolean canBreatheInWater() {
		return true;
	}

	@Override
	public boolean canFreeze() {
		return false;
	}

	@Override
	public boolean handleFallDamage(double fallDistance, float damagePerDistance, DamageSource damageSource) {
		return false;
	}

	@Override
	public boolean isImmuneToExplosion(Explosion explosion) {
		return true;
	}

	@Override
	public void onStruckByLightning(ServerWorld world, LightningEntity lightning) {
	}

	@Override
	public boolean canHaveStatusEffect(StatusEffectInstance effect) {
		return false;
	}

	@Override
	public boolean addStatusEffect(StatusEffectInstance effect, @Nullable Entity source) {
		return false;
	}

	@Override
	public boolean isAffectedBySplashPotions() {
		return false;
	}

	/** Never below its full health. */
	@Override
	public void setHealth(float health) {
		super.setHealth(getMaxHealth());
	}

	/** {@code /kill} does nothing (the damage path ignores it too): the area's removal ({@code /tent remove}) takes it away. */
	@Override
	public void kill(ServerWorld world) {
	}

	@Override
	public void onDeath(DamageSource damageSource) {
	}

	/** Not a mob nor a player, not "part of the game": no mob targets it. */
	@Override
	public boolean isMobOrPlayer() {
		return false;
	}

	@Override
	public boolean isPartOfGame() {
		return false;
	}

	/** Never saved: its area spawns it again when its chunk loads (no duplicates, nothing left behind). */
	@Override
	public boolean shouldSave() {
		return false;
	}

	@Override
	public Arm getMainArm() {
		return Arm.RIGHT;
	}

	/** Drawn as far as its area's model (the server's tent render distance), not by the size of its box. */
	@Override
	public boolean shouldRender(double distance) {
		double far = ConfigManager.server().tentRenderDistance;
		return distance < far * far;
	}

	/** Middle click in creative: the area's item. */
	@Override
	@Nullable
	public ItemStack getPickBlockStack() {
		TentType type = prop();
		return type == null || Tents.item(type) == null ? null : new ItemStack(Tents.item(type));
	}
}
