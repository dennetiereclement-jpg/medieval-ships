package fr.medievalships.client;

import java.util.List;

import net.minecraft.client.MinecraftClient;
import net.minecraft.particle.ParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.client.render.ForgeRig;
import fr.medievalships.client.render.TentModels;
import fr.medievalships.core.ForgeAnimation;
import fr.medievalships.core.TentType;
import fr.medievalships.forge.DivineForgeBlockEntity;

/**
 * The divine forge's effects on the client (1.34.0), from its block entity's client ticker, only for a forge within
 * {@link ForgeAnimation#EFFECTS_DISTANCE} blocks of the player: sparks and embers now and then at the {@code fx_spark_*}
 * and {@code fx_ember_*} points of its models, a puff of steam at an {@code fx_steam_*} point from time to time, motes of
 * holy light at the {@code fx_holy_*} points (the statue), all more frequent while crafting; spaced sounds (the fire's
 * crackle, a faint noise of machinery, the hiss of the steam) and, while crafting, the hammer on the anvil with a burst of
 * sparks. Vanilla particles and sounds only, a few per second at most, nothing lasting: no real fire, nothing burns.
 * Without the models' points the effects come from fixed points of the agreed layout (anvil, furnace, pipes, statue).
 */
public final class DivineForgeEffects {
	/** Points of the agreed layout (forge-local blocks) used when the models give none. */
	private static final List<double[]> SPARKS = List.of(new double[] {0, 1.5, 1.45}),
			EMBERS = List.of(new double[] {0, 1.4, 0.35}, new double[] {-0.6, 1.0, 0.4}, new double[] {0.6, 1.0, 0.4}),
			STEAMS = List.of(new double[] {-3.0, 6.2, -1.0}, new double[] {3.0, 6.2, -1.0}),
			HOLIES = List.of(new double[] {0, 9.0, -0.5});

	private DivineForgeEffects() {
	}

	/** Hands the forges' client ticker to these effects. */
	public static void install() {
		DivineForgeBlockEntity.clientEffects = DivineForgeEffects::tick;
	}

	private static void tick(DivineForgeBlockEntity be) {
		MinecraftClient mc = MinecraftClient.getInstance();
		World world = be.getWorld();
		if (world == null || mc.player == null || mc.world != world) {
			return;
		}
		BlockPos pos = be.getPos();
		boolean crafting = be.crafting();
		boolean started = crafting && !be.wasCrafting;
		be.wasCrafting = crafting;
		double cx = pos.getX() + 0.5, cy = pos.getY(), cz = pos.getZ() + 0.5;
		if (!ForgeAnimation.near(mc.player.squaredDistanceTo(cx, cy + 2.0, cz))) {
			return;
		}
		TentType type = be.tentType();
		if (type == null) {
			return;
		}
		int q = be.quarter();
		Random r = world.random;
		long now = world.getTime();
		List<double[]> sparks = points(type, 0), embers = points(type, 1), steams = points(type, 2), holies = points(type, 3);

		// sparks and embers now and then, motes of holy light at the statue
		emit(world, sparks, q, cx, cy, cz, r, ForgeAnimation.chance(ForgeAnimation.SPARK_IDLE, ForgeAnimation.SPARK_CRAFT, crafting), 0);
		emit(world, embers, q, cx, cy, cz, r, ForgeAnimation.chance(ForgeAnimation.EMBER_IDLE, ForgeAnimation.EMBER_CRAFT, crafting), 1);
		emit(world, holies, q, cx, cy, cz, r, ForgeAnimation.chance(ForgeAnimation.HOLY_IDLE, ForgeAnimation.HOLY_CRAFT, crafting), crafting ? 4 : 3);
		if (started) {
			for (int i = 0; i < 6; i++) {
				emit(world, embers, q, cx, cy, cz, r, 1.0, 1);
			}
		}

		// a puff of steam from a pipe from time to time
		if (be.nextSteam == 0 || now < be.nextSteam - 2000) {
			be.nextSteam = now + ForgeAnimation.interval(ForgeAnimation.STEAM_IDLE_MIN / 2, ForgeAnimation.STEAM_IDLE_MAX, r.nextDouble());
		} else if (now >= be.nextSteam && !steams.isEmpty()) {
			double[] p = world(steams.get(r.nextInt(steams.size())), q, cx, cy, cz);
			for (int i = 0; i < 5 + r.nextInt(4); i++) {
				world.addParticleClient(ParticleTypes.WHITE_SMOKE, p[0] + (r.nextDouble() - 0.5) * 0.2, p[1], p[2] + (r.nextDouble() - 0.5) * 0.2,
						(r.nextDouble() - 0.5) * 0.02, 0.06 + r.nextDouble() * 0.05, (r.nextDouble() - 0.5) * 0.02);
			}
			sound(world, p, SoundEvents.BLOCK_FIRE_EXTINGUISH, 0.18f, 1.6f + r.nextFloat() * 0.3f);
			be.nextSteam = now + (crafting ? ForgeAnimation.interval(ForgeAnimation.STEAM_CRAFT_MIN, ForgeAnimation.STEAM_CRAFT_MAX, r.nextDouble())
					: ForgeAnimation.interval(ForgeAnimation.STEAM_IDLE_MIN, ForgeAnimation.STEAM_IDLE_MAX, r.nextDouble()));
		}

		// the fire's crackle, the machinery
		double[] fire = world(embers.get(0), q, cx, cy, cz);
		if (be.nextCrackle == 0 || now < be.nextCrackle - 2000) {
			be.nextCrackle = now + ForgeAnimation.interval(0, ForgeAnimation.CRACKLE_MAX, r.nextDouble());
		} else if (now >= be.nextCrackle) {
			sound(world, fire, SoundEvents.BLOCK_BLASTFURNACE_FIRE_CRACKLE, crafting ? 0.9f : 0.6f, 0.8f + r.nextFloat() * 0.2f);
			be.nextCrackle = now + ForgeAnimation.interval(ForgeAnimation.CRACKLE_MIN, ForgeAnimation.CRACKLE_MAX, r.nextDouble()) / (crafting ? 2 : 1);
		}
		if (be.nextMachine == 0 || now < be.nextMachine - 4000) {
			be.nextMachine = now + ForgeAnimation.interval(ForgeAnimation.MACHINE_MIN / 2, ForgeAnimation.MACHINE_MAX, r.nextDouble());
		} else if (now >= be.nextMachine) {
			sound(world, new double[] {cx, cy + 3.0, cz}, SoundEvents.BLOCK_PISTON_CONTRACT, crafting ? 0.2f : 0.1f, 0.55f + r.nextFloat() * 0.15f);
			be.nextMachine = now + ForgeAnimation.interval(ForgeAnimation.MACHINE_MIN, ForgeAnimation.MACHINE_MAX, r.nextDouble()) / (crafting ? 2 : 1);
		}

		// while crafting: the hammer on the anvil, a burst of sparks with each blow
		if (crafting) {
			if (be.nextHammer == 0 || now < be.nextHammer - 2000 || started) {
				be.nextHammer = now + 6;
			} else if (now >= be.nextHammer) {
				double[] anvil = world(sparks.get(0), q, cx, cy, cz);
				sound(world, anvil, SoundEvents.BLOCK_ANVIL_USE, 0.35f, 0.9f + r.nextFloat() * 0.3f);
				for (double[] s : sparks) {
					double[] p = world(s, q, cx, cy, cz);
					for (int i = 0; i < 3; i++) {
						world.addParticleClient(ParticleTypes.LAVA, p[0], p[1], p[2], 0, 0, 0);
					}
					for (int i = 0; i < 4; i++) {
						world.addParticleClient(ParticleTypes.WAX_ON, p[0] + (r.nextDouble() - 0.5) * 0.3, p[1] + 0.1, p[2] + (r.nextDouble() - 0.5) * 0.3,
								(r.nextDouble() - 0.5) * 0.4, 0.2 + r.nextDouble() * 0.3, (r.nextDouble() - 0.5) * 0.4);
					}
				}
				be.nextHammer = now + ForgeAnimation.interval(ForgeAnimation.HAMMER_MIN, ForgeAnimation.HAMMER_MAX, r.nextDouble());
			}
		} else {
			be.nextHammer = 0;
		}
	}

	/** One kind of point of the forge's models (0 sparks, 1 embers, 2 steam, 3 holy), or the layout's when they have none. */
	private static List<double[]> points(TentType type, int kind) {
		BbModel main = TentModels.get(type);
		List<double[]> found = null;
		if (main != null) {
			found = pick(ForgeRig.of(main), kind);
		}
		if (found == null || found.isEmpty()) {
			for (TentModels.Extra e : TentModels.extras(type)) {
				List<double[]> l = pick(ForgeRig.of(e.model()), kind);
				if (!l.isEmpty()) {
					found = found == null || found.isEmpty() ? l : found;
				}
			}
		}
		if (found != null && !found.isEmpty()) {
			return found;
		}
		return switch (kind) {
			case 0 -> SPARKS;
			case 1 -> EMBERS;
			case 2 -> STEAMS;
			default -> HOLIES;
		};
	}

	private static List<double[]> pick(ForgeRig rig, int kind) {
		return switch (kind) {
			case 0 -> rig.sparks;
			case 1 -> rig.embers;
			case 2 -> rig.steams;
			default -> rig.holies;
		};
	}

	/** A forge-local point in the world, turned to the forge's facing. */
	private static double[] world(double[] p, int quarter, double cx, double cy, double cz) {
		double[] r = TentType.rotate(p[0], p[2], quarter);
		return new double[] {cx + r[0], cy + p[1], cz + r[1]};
	}

	/**
	 * Each point emits with this chance per tick (shared out when there are many: about four points' worth in all);
	 * {@code kind} 0 a spark, 1 an ember, 3 a mote of holy light, 4 the same while crafting (with glyphs).
	 */
	private static void emit(World world, List<double[]> points, int q, double cx, double cy, double cz, Random r, double chance, int kind) {
		double each = chance * Math.min(1.0, 4.0 / Math.max(1, points.size()));
		for (double[] pt : points) {
			if (r.nextDouble() >= each) {
				continue;
			}
			double[] p = world(pt, q, cx, cy, cz);
			double x = p[0] + (r.nextDouble() - 0.5) * 0.25, y = p[1] + (r.nextDouble() - 0.5) * 0.15, z = p[2] + (r.nextDouble() - 0.5) * 0.25;
			ParticleEffect effect = switch (kind) {
				case 0 -> r.nextInt(3) == 0 ? ParticleTypes.LAVA : ParticleTypes.SMALL_FLAME;
				case 1 -> ParticleTypes.SMALL_FLAME;
				default -> ParticleTypes.END_ROD;
			};
			switch (kind) {
				case 0 -> world.addParticleClient(effect, x, y, z, (r.nextDouble() - 0.5) * 0.06, 0.04 + r.nextDouble() * 0.06, (r.nextDouble() - 0.5) * 0.06);
				case 1 -> world.addParticleClient(effect, x, y, z, (r.nextDouble() - 0.5) * 0.01, 0.02 + r.nextDouble() * 0.03, (r.nextDouble() - 0.5) * 0.01);
				default -> {
					world.addParticleClient(effect, x, y, z, (r.nextDouble() - 0.5) * 0.02, 0.005 + r.nextDouble() * 0.015, (r.nextDouble() - 0.5) * 0.02);
					if (kind == 4 && r.nextInt(2) == 0) {
						world.addParticleClient(ParticleTypes.ENCHANT, x, y + 0.5, z, (r.nextDouble() - 0.5) * 1.6, r.nextDouble() * 0.8 - 0.4,
								(r.nextDouble() - 0.5) * 1.6);
					}
				}
			}
		}
	}

	private static void sound(World world, double[] p, SoundEvent sound, float volume, float pitch) {
		world.playSoundClient(p[0], p[1], p[2], sound, SoundCategory.BLOCKS, volume, pitch, false);
	}
}
