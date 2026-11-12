package fr.medievalships.entity;

import org.jetbrains.annotations.Nullable;

import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.Dive;
import fr.medievalships.core.InteriorDecor;
import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.Ships.NautilusLayout;

/**
 * The fittings of the Nautilus, server side: the controls the players click (salon shutters,
 * projector, lamps, airlock valves, lifeboat), the rules of the doors that open onto the sea, the
 * airlock that fills and empties, the sounds of the engine.
 */
public final class NautilusFittings {
	/** The airlock fills or empties in 6 seconds. */
	static final float AIRLOCK_RATE = 1f / 120f;

	private NautilusFittings() {
	}

	/** The control {@code index} of the decor was used (a test, a command). Returns the message, or null. */
	@Nullable
	public static Text use(ShipEntity ship, ServerWorld world, int index) {
		return use(ship, world, index, null);
	}

	/** A player used the control {@code index} of the decor. Returns a message for him, or null. */
	@Nullable
	public static Text use(ShipEntity ship, ServerWorld world, int index, @Nullable net.minecraft.server.network.ServerPlayerEntity player) {
		InteriorDecor decor = ship.geometry().decor();
		if (decor == null || index < 0 || index >= decor.switches().size()) {
			return null;
		}
		InteriorDecor.Switch w = decor.switches().get(index);
		double[] at = ship.pose().toWorld(w.x(), w.y(), w.z());
		return switch (w.action()) {
			case "shutters" -> {
				boolean close = !ship.toggle(NautilusLayout.SHUTTERS_CLOSED);
				ship.setToggle(NautilusLayout.SHUTTERS_CLOSED, close);
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.8f, 0.7f);
				double[] bay = ship.pose().toWorld(0, 2.6, 0);
				sound(world, bay, close ? SoundEvents.BLOCK_PISTON_EXTEND : SoundEvents.BLOCK_PISTON_CONTRACT, 1.0f, 0.5f);
				yield info(close ? "Les panneaux de fer se referment sur les baies du salon." : "Les panneaux s'ouvrent : la mer apparaît derrière les baies.");
			}
			case "floodlight" -> {
				boolean on = !ship.toggle(NautilusLayout.FLOODLIGHT_ON);
				ship.setToggle(NautilusLayout.FLOODLIGHT_ON, on);
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.8f, on ? 0.9f : 0.7f);
				yield info(on ? "Projecteur allumé." : "Projecteur éteint.");
			}
			case "lights" -> {
				boolean off = !ship.toggle(NautilusLayout.LIGHTS_OFF);
				ship.setToggle(NautilusLayout.LIGHTS_OFF, off);
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.8f, off ? 0.7f : 0.9f);
				yield info(off ? "Lumières du bord éteintes." : "Lumières du bord allumées.");
			}
			case "airlock_fill" -> {
				Text refused = fill(ship);
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.6f, 0.6f);
				yield refused;
			}
			case "airlock_pump" -> {
				Text refused = pump(ship);
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.6f, 0.6f);
				yield refused;
			}
			case "lifeboat" -> {
				sound(world, at, SoundEvents.BLOCK_LEVER_CLICK, 0.8f, 0.7f);
				yield ShipBoatHandling.use(ship, world, player); // the mod's Rowboat, like every ship's boat (1.30.0)
			}
			default -> null;
		};
	}

	// ------------------------------------------------------------------ airlock

	/** Opens the filling valve: the sea comes into the airlock (inner door closed). */
	@Nullable
	public static Text fill(ShipEntity ship) {
		if (ship.doorOpen(NautilusLayout.AIRLOCK_INNER_DOOR)) {
			return refused("Fermez la porte intérieure du sas avant de le remplir.");
		}
		if (ship.airlockTarget() >= 1f) {
			return info(ship.airlockLevel() >= 0.999f ? "Le sas est déjà plein." : "Le sas se remplit...");
		}
		ship.setAirlockTarget(1f);
		return info("Vanne ouverte : le sas se remplit d'eau de mer.");
	}

	/** Starts the pumps: the airlock is emptied (outer door closed). */
	@Nullable
	public static Text pump(ShipEntity ship) {
		if (ship.doorOpen(NautilusLayout.AIRLOCK_OUTER_DOOR)) {
			return refused("Fermez la porte extérieure du sas avant de le vider.");
		}
		if (ship.airlockTarget() <= 0f) {
			return info(ship.airlockLevel() <= 0.001f ? "Le sas est déjà vide." : "Les pompes vident le sas...");
		}
		ship.setAirlockTarget(0f);
		return info("Pompes en marche : le sas se vide.");
	}

	/** Is there sea water behind the outer door of the airlock? */
	static boolean waterOutside(ShipEntity ship, ServerWorld world) {
		double[] p = ship.pose().toWorld(NautilusLayout.AIRLOCK_OUTER_X, NautilusLayout.AIRLOCK_OUTER_Y, NautilusLayout.AIRLOCK_OUTER_Z);
		return world.getFluidState(BlockPos.ofFloored(p[0], p[1], p[2])).isIn(FluidTags.WATER);
	}

	/**
	 * Why a door must stay shut, or null: the hatches of the outer hull open only on the surface;
	 * the airlock opens onto the sea only when full, and onto the ship only when empty.
	 */
	@Nullable
	public static Text doorRefusal(ShipEntity ship, int door, boolean open) {
		if (!open) {
			return null;
		}
		if ((door == NautilusLayout.HATCH_DOOR || door == NautilusLayout.BOAT_HATCH_DOOR) && ship.syncedDepth() > Dive.SURFACED) {
			return refused("Le panneau ne s'ouvre qu'en surface : remontez d'abord.");
		}
		InteriorGrid.State s = ship.interiorState();
		if (door == NautilusLayout.AIRLOCK_INNER_DOOR && (!s.airlockDry() || ship.airlockTarget() > 0f)) {
			return refused("Le sas est plein d'eau : videz-le d'abord (vanne de laiton).");
		}
		if (door == NautilusLayout.AIRLOCK_OUTER_DOOR && ship.getEntityWorld() instanceof ServerWorld world && waterOutside(ship, world)
				&& (!s.airlockFlooded() || ship.airlockTarget() < 1f)) {
			return refused("La mer est derrière cette porte : remplissez d'abord le sas (vanne rouge).");
		}
		return null;
	}

	/**
	 * Before a dive: shuts the open hatches of the outer hull (main hatch, lifeboat hatch). Returns
	 * null when they are shut, or the name of the hatch someone is standing in (it stays open).
	 */
	@Nullable
	public static String shutHatchesForDive(ShipEntity ship, ServerWorld world) {
		InteriorGrid grid = ship.geometry().interior();
		int[] doors = {NautilusLayout.HATCH_DOOR, NautilusLayout.BOAT_HATCH_DOOR};
		String[] names = {"le panneau d'accès", "la trappe du canot"};
		for (int i = 0; i < doors.length; i++) {
			if (!ship.doorOpen(doors[i])) {
				continue;
			}
			double[] c = grid.doorCenter(doors[i]);
			double[] w = ship.pose().toWorld(c[0], c[1], c[2]);
			net.minecraft.util.math.Box box = new net.minecraft.util.math.Box(w[0] - 0.6, w[1] - 1.6, w[2] - 0.6, w[0] + 0.6, w[1] + 0.4, w[2] + 0.6);
			if (!world.getOtherEntities(ship, box, e -> !e.isSpectator() && e.getVehicle() != ship).isEmpty()) {
				return names[i];
			}
		}
		for (int door : doors) {
			if (ship.doorOpen(door)) {
				ship.setDoor(door, false);
				double[] c = grid.doorCenter(door);
				sound(world, ship.pose().toWorld(c[0], c[1], c[2]), SoundEvents.BLOCK_IRON_TRAPDOOR_CLOSE, 1.0f, 0.8f);
			}
		}
		return null;
	}

	// ------------------------------------------------------------------ lifeboat

	/**
	 * Puts the lifeboat on the water beside the hull (on the surface only): since 1.30.0 the mod's Rowboat, as for
	 * every ship's boat ({@link ShipBoatHandling}).
	 */
	@Nullable
	public static Text launchLifeboat(ShipEntity ship, ServerWorld world) {
		return ShipBoatHandling.launch(ship, world, null);
	}

	/**
	 * Takes the lifeboat back into its recess: it must be near the hull ({@code force}: an admin replaces it wherever it
	 * is, or if it was lost). See {@link ShipBoatHandling#recover}.
	 */
	@Nullable
	public static Text recoverLifeboat(ShipEntity ship, ServerWorld world, boolean force) {
		return ShipBoatHandling.recover(ship, world, null, force);
	}

	// ------------------------------------------------------------------ tick

	/** Each server tick: the airlock fills or empties, the engine is heard. */
	public static void tick(ShipEntity ship, ServerWorld world) {
		InteriorGrid grid = ship.geometry().interior();
		if (grid == null) {
			return;
		}
		float level = ship.airlockLevel();
		float target = ship.airlockTarget();
		if (ship.doorOpen(NautilusLayout.AIRLOCK_OUTER_DOOR) && waterOutside(ship, world)) {
			target = 1f; // open onto the sea: full whatever the pumps do
			ship.setAirlockTarget(1f);
		}
		if (level != target) {
			float next = target > level ? Math.min(target, level + AIRLOCK_RATE) : Math.max(target, level - AIRLOCK_RATE);
			ship.setAirlockLevel(next);
			double[] c = ship.pose().toWorld(0, (grid.airlockFloor + grid.airlockTop) / 2, 27.0);
			if (ship.age % 12 == 0) {
				sound(world, c, target > level ? SoundEvents.BLOCK_WATER_AMBIENT : SoundEvents.BLOCK_BUBBLE_COLUMN_UPWARDS_AMBIENT, 1.0f, 1.0f);
			}
			if (next == target) {
				sound(world, c, SoundEvents.BLOCK_IRON_DOOR_CLOSE, 0.7f, 0.6f);
			}
		}
		// the engine: a beat that follows the speed, and the hum of the batteries
		double speed = Math.abs(ship.syncedSpeed());
		if (speed > 0.2) {
			int period = Math.max(5, (int) Math.round(18 - speed * 2));
			if (ship.age % period == 0) {
				double[] e = ship.pose().toWorld(-1.6, NautilusLayout.ENGINE_Y, NautilusLayout.ENGINE_Z);
				sound(world, e, SoundEvents.BLOCK_PISTON_EXTEND, 0.25f, 0.55f);
			}
		}
		if (ship.age % 80 == 0) {
			double[] e = ship.pose().toWorld(-4.0, NautilusLayout.ENGINE_Y, -16.0);
			sound(world, e, SoundEvents.BLOCK_BEACON_AMBIENT, 0.35f, 0.6f);
		}
	}

	private static void sound(ServerWorld world, double[] at, SoundEvent sound, float volume, float pitch) {
		world.playSound(null, at[0], at[1], at[2], sound, net.minecraft.sound.SoundCategory.NEUTRAL, volume, pitch);
	}

	private static Text info(String s) {
		return Text.literal(s).formatted(Formatting.GOLD);
	}

	private static Text refused(String s) {
		return Text.literal(s).formatted(Formatting.RED);
	}
}
