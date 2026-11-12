package fr.medievalships.entity;

import java.util.List;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.entity.SpawnReason;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.Dive;
import fr.medievalships.core.HullShape;
import fr.medievalships.core.ShipBoats;
import fr.medievalships.core.ShipMover;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ShipData;

/**
 * The ships' boats, server side (1.30.0, see {@link ShipBoats}): a click on the deco boat (or the Nautilus' lever, or
 * {@code /ship barque}) puts a real Rowboat on the water beside the hull and hides the deco; the same click, or a click
 * on the hull from the boat itself, hoists it back aboard with its crew. One boat per ship; its id is saved with the
 * ship, the ship's id with the boat.
 *
 * <p>Robustness: a boat destroyed where the server can see it is noticed within two seconds (the deco comes back); a
 * boat out of reach of the server (unloaded, carried away by a player who logged out in it) is written off by the next
 * recovery: the ship gets its deco back and that boat vanishes when it is loaded again ({@link ShipData#retireBoat}),
 * so there are never two. A ship picked up leaves its boat on the water as an ordinary Rowboat.
 */
public final class ShipBoatHandling {
	/** The ship's side of things that is not saved: manoeuvre in progress, last place the boat was seen. */
	static final class State {
		long busyUntil;
		int missing;
		double lastX = Double.NaN;
		double lastZ = Double.NaN;

		void seen(Entity boat) {
			lastX = boat.getX();
			lastZ = boat.getZ();
			missing = 0;
		}

		void reset() {
			missing = 0;
			lastX = Double.NaN;
			lastZ = Double.NaN;
		}
	}

	/** The cleanup runs every second; the boat is written off after this many checks missing from a loaded chunk. */
	static final int MISSING_CHECKS = 2;

	private ShipBoatHandling() {
	}

	/** A click on the deco boat (or the Nautilus' lever): launches it, or takes it back aboard. Returns the message, or null. */
	@Nullable
	public static Text use(ShipEntity ship, ServerWorld world, @Nullable ServerPlayerEntity player) {
		if (ship.boatSpec() == null) {
			return null;
		}
		return ship.toggle(ShipBoats.AWAY_BIT) ? recover(ship, world, player, false) : launch(ship, world, player);
	}

	/** The ship's boat entity on the water, or null (none, destroyed, out of reach of the server). */
	@Nullable
	public static Entity boat(ShipEntity ship, ServerWorld world) {
		UUID id = ship.lifeboatId();
		Entity e = id == null ? null : world.getEntity(id);
		return e == null || e.isRemoved() ? null : e;
	}

	private static boolean busy(ShipEntity ship, ServerWorld world) {
		return world.getTime() < ship.boatState.busyUntil;
	}

	// ------------------------------------------------------------------ launch

	/** Puts the boat on the water beside the hull, on the player's side when there is room (on the surface only). */
	@Nullable
	public static Text launch(ShipEntity ship, ServerWorld world, @Nullable ServerPlayerEntity player) {
		ShipBoats.Spec spec = ship.boatSpec();
		if (spec == null) {
			return refused("Ce navire n'a pas de barque.");
		}
		if (ship.toggle(ShipBoats.AWAY_BIT)) {
			return refused(spec.The() + " est déjà à l'eau.");
		}
		if (busy(ship, world)) {
			return refused(spec.The() + " est en cours de manœuvre.");
		}
		if (ship.geometry().flying()) {
			return refused("Posez d'abord le navire sur l'eau pour mettre " + spec.the() + " à l'eau.");
		}
		if (ship.geometry().submarine() && ship.syncedDepth() > Dive.SURFACED) {
			return refused(spec.The() + " ne se détache qu'en surface : remontez d'abord.");
		}
		HullShape hull = ship.geometry().hull();
		double waterline = ship.getY() + hull.waterlineY;
		ShipWorld around = new ShipWorld(world, null, ship.getX(), ship.getY(), ship.getZ()); // the ship itself is an obstacle
		double here = around.waterSurface(ship.getX(), ship.getZ(), waterline);
		if (Double.isNaN(here) || Math.abs(here - waterline) > 1.0) {
			return refused("Le navire n'est pas à flot : impossible de mettre " + spec.the() + " à l'eau.");
		}
		ShipPose pose = ship.pose();
		int side = player == null ? 1 : ShipBoats.sideOf(pose.toLocal(player.getX(), player.getY(), player.getZ())[0]);
		float yaw = ship.getYaw();
		double rowboatWaterline = Ships.ROWBOAT.hull().waterlineY;
		for (double[] c : ShipBoats.launchCandidates(spec, hull, side)) {
			double[] w = pose.toWorld(c[0], hull.waterlineY, c[1]);
			double surface = around.waterSurface(w[0], w[2], waterline);
			if (Double.isNaN(surface) || Math.abs(surface - waterline) > 1.0) {
				continue; // no water there, or not at the ship's level (a quay, a pond)
			}
			ShipPose at = new ShipPose(w[0], surface - rowboatWaterline, w[2], yaw);
			if (ShipMover.collides(Ships.ROWBOAT.geometry(), at, around)) {
				continue; // against the hull, another hull, the bank
			}
			RowboatEntity boat = MedievalShips.ROWBOAT.create(world, SpawnReason.TRIGGERED);
			if (boat == null) {
				break;
			}
			boat.refreshPositionAndAngles(at.x(), at.y(), at.z(), yaw, 0f);
			boat.setShipYaw(yaw);
			boat.setMotherShip(ship.getUuid());
			boat.addCommandTag(ShipBoats.TAG);
			world.spawnEntity(boat);
			ship.setLifeboatId(boat.getUuid());
			ship.setToggle(ShipBoats.AWAY_BIT, true);
			ship.boatState.busyUntil = world.getTime() + ShipBoats.BUSY_TICKS;
			ship.boatState.seen(boat);
			double[] deco = decoCenter(ship, spec);
			sound(world, deco, SoundEvents.BLOCK_CHAIN_PLACE, 1.0f, 0.8f);
			sound(world, new double[] {at.x(), at.y(), at.z()}, SoundEvents.ENTITY_GENERIC_SPLASH, 1.0f, 0.8f);
			return info(String.format("%s est à l'eau, à %s. Pour %s hisser à bord : ramenez-%s le long de la coque, puis clic droit sur son chantier "
					+ "(ou sur la coque depuis la barque).", spec.The(), c[2] > 0 ? "bâbord" : "tribord", spec.it(), spec.it()));
		}
		return refused("Pas d'eau libre le long de la coque pour mettre " + spec.the() + " à l'eau.");
	}

	// ------------------------------------------------------------------ recovery

	/**
	 * Hoists the boat back aboard: it must be alongside ({@code force}: an administrator brings it back wherever it
	 * is). Its crew is put on the deck, at the spot a player boarding from there would land on. A boat the server
	 * cannot find any more is written off: the ship gets its deco back.
	 */
	@Nullable
	public static Text recover(ShipEntity ship, ServerWorld world, @Nullable ServerPlayerEntity player, boolean force) {
		ShipBoats.Spec spec = ship.boatSpec();
		if (spec == null) {
			return refused("Ce navire n'a pas de barque.");
		}
		if (!ship.toggle(ShipBoats.AWAY_BIT) && ship.lifeboatId() == null) {
			return info(spec.The() + " est déjà à bord.");
		}
		if (!force && busy(ship, world)) {
			return refused(spec.The() + " est en cours de manœuvre.");
		}
		boolean submerged = ship.geometry().submarine() && ship.syncedDepth() > Dive.SURFACED;
		if (!force && submerged) {
			return refused("Remontez en surface pour rembarquer " + spec.the() + ".");
		}
		Entity boat = boat(ship, world);
		if (boat == null) {
			writeOff(ship, world);
			return info(String.format("%s était perdu%s : %s de rechange a été embarqué%s.", spec.The(), spec.e(),
					spec.feminine() ? "une " + spec.noun() : "un " + spec.noun(), spec.e()));
		}
		HullShape hull = ship.geometry().hull();
		ShipPose pose = ship.pose();
		if (!force) {
			double[] l = pose.toLocal(boat.getX(), boat.getY(), boat.getZ());
			if (!ShipBoats.inReach(spec, hull, l[0], l[1], l[2])) {
				return refused(String.format("%s est trop loin : ramenez-%s à moins de %d blocs de son chantier.", spec.The(), spec.it(),
						(int) Math.floor(ShipBoats.reach(spec, hull))));
			}
		}
		// the crew climbs aboard (or, forced while under the sea, is left swimming where it is)
		List<Entity> crew = List.copyOf(boat.getPassengerList());
		Vec3d deck = ship.boardingPosition(boat.getX(), boat.getZ());
		for (Entity e : crew) {
			e.stopRiding();
			if (!submerged) {
				e.requestTeleport(deck.x, deck.y, deck.z);
				e.setVelocity(0, 0, 0);
			}
		}
		if (boat instanceof RowboatEntity rb) {
			rb.setMotherShip(null);
		}
		boat.discard();
		ship.setLifeboatId(null);
		ship.setToggle(ShipBoats.AWAY_BIT, false);
		ship.boatState.busyUntil = world.getTime() + ShipBoats.BUSY_TICKS;
		ship.boatState.reset();
		sound(world, decoCenter(ship, spec), SoundEvents.BLOCK_CHAIN_PLACE, 1.0f, 0.8f);
		return info(String.format("%s a été hissé%s à bord.", spec.The(), spec.e()));
	}

	/**
	 * A player in the ship's own boat clicks the ship's hull: the boat is hoisted aboard with him (true), when it is
	 * this ship's boat; otherwise he simply boards (false).
	 */
	public static boolean hoistFrom(ShipEntity ship, ServerWorld world, ServerPlayerEntity player) {
		Entity vehicle = player.getVehicle();
		if (ship.boatSpec() == null || vehicle == null || ship.lifeboatId() == null || !ship.lifeboatId().equals(vehicle.getUuid())) {
			return false;
		}
		Text msg = recover(ship, world, player, false);
		if (msg != null) {
			player.sendMessage(msg, true);
		}
		return true;
	}

	/** The boat is lost (out of reach of the server, or destroyed): the ship has its deco back; that boat vanishes if it comes back. */
	static void writeOff(ShipEntity ship, ServerWorld world) {
		UUID id = ship.lifeboatId();
		if (id != null) {
			ShipData.get(world.getServer()).retireBoat(id);
		}
		ship.setLifeboatId(null);
		ship.setToggle(ShipBoats.AWAY_BIT, false);
		ship.boatState.reset();
	}

	// ------------------------------------------------------------------ upkeep

	/**
	 * Every second while the boat is away: is it still there? Seen: its place is noted. Missing from a chunk whose
	 * entities are loaded (it was destroyed, picked up): written off after two checks, the deco is back aboard.
	 * Missing from an unloaded chunk: nothing is known, it stays the ship's boat.
	 */
	static void tick(ShipEntity ship, ServerWorld world) {
		State st = ship.boatState;
		if (ship.lifeboatId() == null) {
			ship.setToggle(ShipBoats.AWAY_BIT, false); // away with no boat known (an old save): back aboard
			st.reset();
			return;
		}
		Entity boat = boat(ship, world);
		if (boat != null) {
			st.seen(boat);
			return;
		}
		if (Double.isNaN(st.lastX)) {
			return; // not seen since the server started: it may come with its chunk, or a recovery will write it off
		}
		if (!world.isChunkLoaded(ChunkPos.toLong(((int) Math.floor(st.lastX)) >> 4, ((int) Math.floor(st.lastZ)) >> 4))) {
			st.missing = 0;
			return;
		}
		if (++st.missing >= MISSING_CHECKS) {
			writeOff(ship, world);
		}
	}

	/** The ship is picked up or removed: its boat on the water becomes an ordinary Rowboat. */
	static void onShipRemoved(ShipEntity ship, ServerWorld world) {
		if (ship.lifeboatId() == null) {
			return;
		}
		Entity boat = world.getEntity(ship.lifeboatId());
		if (boat instanceof RowboatEntity rb && ship.getUuid().equals(rb.motherShip())) {
			rb.setMotherShip(null);
			rb.removeCommandTag(ShipBoats.TAG);
		}
	}

	/** A ship's boat checks now and then whether its ship wrote it off; if so it vanishes, its crew left in the water. */
	static void checkRetired(RowboatEntity boat, ServerWorld world) {
		ShipData data = ShipData.get(world.getServer());
		if (!data.isRetiredBoat(boat.getUuid())) {
			return;
		}
		data.forgetRetiredBoat(boat.getUuid());
		for (Entity e : List.copyOf(boat.getPassengerList())) {
			e.stopRiding();
			if (e instanceof ServerPlayerEntity p) {
				p.sendMessage(Text.literal("Cette barque a été remplacée à bord de son navire.").formatted(Formatting.YELLOW), true);
			}
		}
		boat.setMotherShip(null);
		boat.discard();
	}

	// ------------------------------------------------------------------ helpers

	private static double[] decoCenter(ShipEntity ship, ShipBoats.Spec spec) {
		var b = spec.deco();
		return ship.pose().toWorld((b.minX() + b.maxX()) / 2, (b.minY() + b.maxY()) / 2, (b.minZ() + b.maxZ()) / 2);
	}

	private static void sound(ServerWorld world, double[] at, SoundEvent sound, float volume, float pitch) {
		world.playSound(null, at[0], at[1], at[2], sound, SoundCategory.NEUTRAL, volume, pitch);
	}

	private static Text info(String s) {
		return Text.literal(s).formatted(Formatting.GOLD);
	}

	private static Text refused(String s) {
		return Text.literal(s).formatted(Formatting.RED);
	}
}
