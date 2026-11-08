package fr.medievalships.bridge;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.jetbrains.annotations.Nullable;

import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.vehicle.AbstractBoatEntity;
import net.minecraft.registry.Registries;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Box;

import fr.medievalships.core.Autopilot;
import fr.medievalships.core.HullShape;
import fr.medievalships.core.Route;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.Waypoint;
import fr.medievalships.core.bridge.ChannelZones;
import fr.medievalships.core.bridge.DrawbridgeConfig;
import fr.medievalships.core.bridge.Gauge;
import fr.medievalships.core.bridge.VesselProfile;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * Finds the vessels around a drawbridge and measures them. The mod's vessels come from the cached registry
 * ({@link ShipTracker}: never a scan of every entity), the vanilla boats and the vehicles of other mods that have a
 * profile from one indexed box query over the detection zone. Each one gets an {@link Gauge.Envelope}: the model's
 * highest point (masts, superstructure, balloon: {@link ShipGeometry#topY}), the heads of the seated passengers and
 * of the people standing on deck when they are higher, the hull's extents along and across the channel for its
 * current heading, corrected by the {@link VesselProfile} of its kind when one is configured.
 */
final class VesselScanner {
	/** One vessel seen near the bridge. */
	record Observation(Entity entity, @Nullable ShipEntity ship, Gauge.Envelope envelope, Gauge.Decision decision, double distance, int side,
			boolean inPassage, boolean inApproach, boolean inKeep, boolean idle, boolean approaching, boolean crossing) {
	}

	private VesselScanner() {
	}

	/** Height above the water surface scanned for vessels' tops. */
	static final double SCAN_HEIGHT = 80.0;

	static List<Observation> scan(ServerWorld world, Drawbridge bridge, DrawbridgeConfig cfg) {
		ChannelZones zones = bridge.zones();
		double waterY = bridge.waterY();
		double[] d = zones.detectionBox(waterY - cfg.detectionDepth, waterY + SCAN_HEIGHT);
		Box area = new Box(d[0], d[1], d[2], d[3], d[4], d[5]);
		List<Observation> out = new ArrayList<>();
		for (ShipEntity ship : ShipTracker.ships(world)) {
			if (ship.isRemoved()) {
				continue;
			}
			double r = ship.geometry().boundingRadius();
			if (!area.intersects(ship.getBoundingBox().expand(r, 64, r))) {
				continue;
			}
			Observation o = observe(world, bridge, cfg, ship, ship);
			if (o != null) {
				out.add(o);
			}
		}
		for (Entity e : world.getOtherEntities(null, area, e -> !(e instanceof ShipEntity) && !e.isRemoved() && !e.hasVehicle()
				&& (e instanceof AbstractBoatEntity || cfg.profile(Registries.ENTITY_TYPE.getId(e.getType()).toString()) != null))) {
			Observation o = observe(world, bridge, cfg, e, null);
			if (o != null) {
				out.add(o);
			}
		}
		return out;
	}

	@Nullable
	private static Observation observe(ServerWorld world, Drawbridge bridge, DrawbridgeConfig cfg, Entity e, @Nullable ShipEntity ship) {
		ChannelZones zones = bridge.zones();
		Gauge.Envelope env = ship != null ? envelopeOfShip(world, ship, zones, cfg) : envelopeOfEntity(e, zones, cfg, bridge.waterY());
		if (env == null) {
			return null;
		}
		if (!zones.inBand(env.x(), env.z(), env.halfAcross())) {
			return null; // beside the channel (moored on a bank, sailing past the towers): no business with the bridge
		}
		double dist = zones.distanceToDeck(env.x(), env.z(), env.reachAlong());
		boolean inKeep = zones.inKeepZone(dist);
		if (!inKeep) {
			return null;
		}
		Gauge.Decision decision = Gauge.decide(env, bridge.undersideY(), bridge.waterY(), bridge.tuning().margin(), zones.halfWidth());
		boolean inPassage = zones.inPassage(dist);
		int side = zones.side(env.x(), env.z());
		// towards the bridge: the direction that reduces the distance along the channel
		double tx = -side * zones.dx(), tz = -side * zones.dz();
		boolean idle, approaching, crossing = false;
		if (ship != null) {
			if (ship.isAutopilotEnabled()) {
				Autopilot.Phase ph = ship.autopilot().phase;
				idle = !(ph == Autopilot.Phase.SAILING || ph == Autopilot.Phase.RECOVERING);
				crossing = !idle && routeCrosses(world, ship, zones, env.halfAcross());
			} else {
				idle = ship.passengerInSeat(ShipGeometry.PILOT_SEAT) == null && Math.abs(ship.syncedSpeed()) < 0.1
						&& ship.getVelocity().horizontalLength() < 0.02;
			}
			double fx = -Math.sin(Math.toRadians(ship.getYaw())), fz = Math.cos(Math.toRadians(ship.getYaw()));
			approaching = inPassage || crossing || fx * tx + fz * tz > -0.2;
		} else {
			idle = !e.hasPassengers() && e.getVelocity().horizontalLength() < 0.02;
			approaching = inPassage || e.hasPassengers() || e.getVelocity().x * tx + e.getVelocity().z * tz > 0.005;
		}
		return new Observation(e, ship, env, decision, dist, side, inPassage, zones.inApproach(dist), true, idle, approaching, crossing);
	}

	/** The envelope of one of the mod's vessels; null for one the bridge ignores (aircraft, profile {@code ignore}). */
	@Nullable
	static Gauge.Envelope envelopeOfShip(ServerWorld world, ShipEntity ship, ChannelZones zones, DrawbridgeConfig cfg) {
		ShipGeometry g = ship.geometry();
		HullShape h = g.hull();
		VesselProfile p = cfg.profile(ship.shipType().id());
		if (g.flying() || (p != null && p.ignore)) {
			return null;
		}
		double water = ship.getY() + h.waterlineY;
		double modelTop = g.topY() - h.waterlineY; // the model's top above the water (masts, castles, lanterns)
		double top = water + (p == null ? modelTop : p.height(modelTop));
		StringBuilder detail = new StringBuilder(String.format(Locale.ROOT, "modèle %.1f", modelTop));
		if (p != null && p.height != null) {
			detail.append(String.format(Locale.ROOT, " (profil %.1f)", p.height));
		}
		if (p != null && p.heightOffset != 0) {
			detail.append(String.format(Locale.ROOT, " %+.1f profil", p.heightOffset));
		}
		if (p == null || p.occupants) {
			double occ = occupantsTop(world, ship);
			if (occ > top) {
				detail.append(String.format(Locale.ROOT, ", occupants +%.1f", occ - top));
				top = occ;
			}
		}
		double halfW = Math.max(h.maxHalfWidth, g.aiHalfWidth());
		for (ShipGeometry.LocalBox s : g.solids()) {
			halfW = Math.max(halfW, Math.max(Math.abs(s.minX()), Math.abs(s.maxX())));
		}
		if (p != null && p.width != null) {
			halfW = p.width / 2;
		}
		double reachAlong = zones.reachAlong(ship.getYaw(), g.aiReach(), g.aiBack(), halfW);
		double halfAcross = zones.reachAcross(ship.getYaw(), g.aiReach(), g.aiBack(), halfW);
		String label = ship.hasCustomName() ? ship.getCustomName().getString() : ship.shipType().frenchName();
		return new Gauge.Envelope(ship.getX(), ship.getY(), ship.getZ(), top, reachAlong, halfAcross, g.boundingRadius(), label, detail.toString());
	}

	/** Highest head aboard (seated passengers, people standing on the decks), world Y; -infinity when nobody. */
	private static double occupantsTop(ServerWorld world, ShipEntity ship) {
		double top = Double.NEGATIVE_INFINITY;
		for (Entity pass : ship.getPassengerList()) {
			top = Math.max(top, pass.getBoundingBox().maxY);
		}
		ShipGeometry g = ship.geometry();
		double r = g.boundingRadius();
		Box area = new Box(ship.getX() - r, ship.getY() + g.lowestY() - 1, ship.getZ() - r, ship.getX() + r, ship.getY() + g.topY() + 3, ship.getZ() + r);
		for (Entity e : world.getOtherEntities(ship, area, e -> e instanceof LivingEntity && !e.isSpectator() && !e.hasVehicle() && !e.isRemoved())) {
			if (ship.isAboard(e)) {
				top = Math.max(top, e.getBoundingBox().maxY);
			}
		}
		return top;
	}

	/** The envelope of a vanilla boat or of another mod's vehicle, by its profile; null when its profile ignores it. */
	@Nullable
	static Gauge.Envelope envelopeOfEntity(Entity e, ChannelZones zones, DrawbridgeConfig cfg, double bridgeWaterY) {
		String typeId = Registries.ENTITY_TYPE.getId(e.getType()).toString();
		VesselProfile p = cfg.profile(typeId);
		if (p == null && e instanceof AbstractBoatEntity) {
			p = cfg.profile(DrawbridgeConfig.VANILLA_BOAT);
		}
		if (p == null || p.ignore) {
			return null;
		}
		Box box = e.getBoundingBox();
		// the water under a floating boat: its box's bottom is just under the surface; the bridge's water level is as good
		double water = e instanceof AbstractBoatEntity ? Math.min(bridgeWaterY, box.minY + 0.4) : bridgeWaterY;
		double top = (p.height != null ? water + p.height : box.maxY) + p.heightOffset;
		String detail = String.format(Locale.ROOT, "boîte %.1f%s", box.maxY - water, p.height != null ? String.format(Locale.ROOT, " (profil %.1f)", p.height) : "");
		if (p.occupants) {
			double occ = Double.NEGATIVE_INFINITY;
			for (Entity pass : e.getPassengerList()) {
				occ = Math.max(occ, pass.getBoundingBox().maxY);
			}
			if (occ > top) {
				detail += String.format(Locale.ROOT, ", occupants +%.1f", occ - top);
				top = occ;
			}
		}
		double half = p.width != null ? p.width / 2 : Math.max(box.getLengthX(), box.getLengthZ()) / 2;
		double reachAlong = zones.reachAlong(e.getYaw(), half, half, half);
		double halfAcross = zones.reachAcross(e.getYaw(), half, half, half);
		String label = e.hasCustomName() ? e.getCustomName().getString() : e.getType().getName().getString();
		return new Gauge.Envelope(e.getX(), e.getY(), e.getZ(), top, reachAlong, halfAcross, half * 1.5, label, detail);
	}

	/**
	 * Does the autopilot's route cross the bridge line within the channel, in the next few legs? The leg from the
	 * vessel to its target point, then the following ones (up to 8 points or 300 blocks).
	 */
	static boolean routeCrosses(ServerWorld world, ShipEntity ship, ChannelZones zones, double halfAcross) {
		Route route = ShipData.get(world.getServer()).route(ship.routeName());
		if (route == null || route.size() == 0) {
			return false;
		}
		Autopilot ap = ship.autopilot();
		int idx = Math.max(0, Math.min(route.size() - 1, ap.target)), dir = ap.direction == 0 ? 1 : ap.direction;
		double px = ship.getX(), pz = ship.getZ(), acc = 0;
		for (int guard = 0; guard < 8; guard++) {
			Waypoint w = route.get(idx);
			if (segmentCrosses(zones, px, pz, w.x, w.z, halfAcross)) {
				return true;
			}
			acc += Math.hypot(w.x - px, w.z - pz);
			if (acc > 300) {
				return false;
			}
			px = w.x;
			pz = w.z;
			int[] nx = Autopilot.next(route, idx, dir);
			if (nx == null) {
				return false;
			}
			idx = nx[0];
			dir = nx[1];
		}
		return false;
	}

	/** Does the segment cross the bridge's line (along = 0) within the navigable band (plus the hull's half width)? */
	static boolean segmentCrosses(ChannelZones zones, double x0, double z0, double x1, double z1, double halfAcross) {
		double a0 = zones.along(x0, z0), a1 = zones.along(x1, z1);
		if (a0 * a1 > 0 || a0 == a1) {
			return false;
		}
		double t = a0 / (a0 - a1);
		double x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t;
		return Math.abs(zones.across(x, z)) <= zones.halfWidth() + ChannelZones.LATERAL_MARGIN + halfAcross;
	}
}
