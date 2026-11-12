package fr.medievalships.test;

import java.util.Locale;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.HullShape;
import fr.medievalships.core.ShipBoats;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.RowboatEntity;
import fr.medievalships.entity.ShipBoatHandling;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The ships' boats in a real game (1.30.0, solo and on the dedicated server, about 50 s of game time): the great galleon,
 * the great warship and the Old Corsair each in turn on a basin of their own. A player on the deck clicks the deco boat:
 * a real Rowboat goes on the water on his side, clear of the hull, floating, the deco hidden (also on the client); a
 * second order at once (two players) launches no second boat; too far, it is refused; clicked again it is hoisted aboard
 * and the deco is back; from the boat itself a click on the hull hoists it with its rower put on the deck. The warship's
 * deck box of its boat goes with it. With the galleon: refused while the ship is out of the water, a boat destroyed is
 * noticed (the deco comes back), a boat written off vanishes when it is seen again, and a ship picked up leaves its boat
 * as an ordinary Rowboat. The Nautilus' lifeboat (the same Rowboat now) is checked by its own scenario.
 */
public final class ShipBoatGameTest {
	private static final int X = 7400;
	private static final int X0 = X - 20, X1 = X + 20, Z0 = -40, Z1 = 40, TOP = -50;
	private static final ShipType[] TYPES = {Ships.GALLEON, Ships.WARSHIP, Ships.OLD_CORSAIR};

	private ShipBoatGameTest() {
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	private static ShipEntity clientShip(MinecraftClient mc, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(mc.world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	/** The Rowboats on the water whose ship is this one. */
	private static int boatsOf(ServerWorld world, UUID ship) {
		int n = 0;
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s instanceof RowboatEntity rb && ship.equals(rb.motherShip())) {
				n++;
			}
		}
		return n;
	}

	private static ServerPlayerEntity player(net.minecraft.server.MinecraftServer srv) {
		return srv.getPlayerManager().getPlayerList().get(0);
	}

	private static void lookLocal(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}

	/** Where a player stands on the deck beside the deco boat, on the starboard side (ship-local feet). */
	private static double[] deckSpot(ShipType type) {
		ShipBoats.Spec spec = ShipBoats.of(type.id());
		double cz = (spec.deco().minZ() + spec.deco().maxZ()) / 2;
		return switch (type.id()) {
			case "warship" -> new double[] {-2.4, Ships.WarshipLayout.MAIN_DECK_Y, cz};
			case "old_corsair" -> new double[] {-2.0, fr.medievalships.core.CorsairLayout.QUARTERDECK_Y, cz};
			default -> new double[] {-2.0, Ships.GalleonLayout.MAIN_DECK_Y, cz};
		};
	}

	/** The player stands beside the deco boat and right-clicks it (the real client: picking, packet, server). */
	private static void clickDecoBoat(ClientGameTestContext context, TestServerContext server, ShipType type) {
		ShipPose pose = server.computeOnServer(srv -> ship(srv.getOverworld(), type).pose());
		ShipBoats.Spec spec = ShipBoats.of(type.id());
		double[] f = deckSpot(type);
		ShipGeometry.LocalBox d = spec.deco();
		server.runCommand("gamemode survival @a");
		lookLocal(server, pose, f[0], f[1] + 1.62, f[2], (d.minX() + d.maxX()) / 2, (d.minY() + d.maxY()) / 2, (d.minZ() + d.maxZ()) / 2);
		context.waitTicks(12);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(10);
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 -30 0 30", X));
		context.waitTicks(20);
		// a basin 40 wide, 80 long and 14 deep, walled with glass up to the water
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X1, TOP, Z0));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z1, X1, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X0, Z0, X0, TOP, Z1));
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d glass", X1, Z0, X1, TOP, Z1));
		for (int z = Z0 + 1; z < Z1; z += 30) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d -50 %d water", X0 + 1, z, X1 - 1, Math.min(Z1 - 1, z + 29)));
			server.runCommand(String.format(Locale.ROOT, "fill %d -49 %d %d -30 %d air", X0 + 1, z, X1 - 1, Math.min(Z1 - 1, z + 29)));
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		for (ShipType type : TYPES) {
			try {
				testShip(context, server, world, type, check, log, shot);
			} catch (RuntimeException e) {
				check.accept(false, type.id() + " boat: exception " + e);
			}
			server.runCommand("ride @p dismount");
			server.computeOnServer(srv -> {
				for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
					if (s.getX() > X0 - 8 && s.getX() < X1 + 8) {
						s.removeAllPassengers();
						s.discard();
					}
				}
				return null;
			});
			context.waitTicks(5);
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand("gamemode survival @a");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
	}

	private static void testShip(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, ShipType type,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = type.id();
		ShipBoats.Spec spec = ShipBoats.of(id);
		HullShape hull = type.hull();
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -30 -30 0 30", X));
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d -50 0 rotated 0 0 run ship spawn %s", X, id));
		world.waitForChunksRender();
		context.waitTicks(50);
		ShipPose pose = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : s.pose();
		});
		if (pose == null) {
			check.accept(false, id + " boat: the ship is spawned in the basin");
			return;
		}
		boolean away0 = server.computeOnServer(srv -> ship(srv.getOverworld(), type).toggle(ShipBoats.AWAY_BIT));
		check.accept(!away0, id + " boat: on its chocks at first");

		// 1. the player on the deck, starboard of the deco boat, right-clicks it: the boat goes on the water on his side
		clickDecoBoat(context, server, type);
		Object[] l = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			Entity b = ShipBoatHandling.boat(s, srv.getOverworld());
			return new Object[] {s.toggle(ShipBoats.AWAY_BIT), b instanceof RowboatEntity, boatsOf(srv.getOverworld(), s.getUuid()),
					b == null ? null : s.pose().toLocal(b.getX(), b.getY(), b.getZ())};
		});
		double[] bl = (double[]) l[3];
		log.accept(String.format(Locale.ROOT, "%s boat launched: away %s, rowboat %s, boats %s, local %s", id, l[0], l[1], l[2],
				bl == null ? "-" : String.format(Locale.ROOT, "%.2f %.2f %.2f", bl[0], bl[1], bl[2])));
		check.accept(Boolean.TRUE.equals(l[0]) && Boolean.TRUE.equals(l[1]) && (Integer) l[2] == 1,
				String.format(Locale.ROOT, "%s boat: the click on the deco boat puts one Rowboat of the mod on the water (away %s, rowboat %s, %s boat)", id, l[0], l[1], l[2]));
		if (bl == null) {
			return;
		}
		// 2. other orders right after (a second player clicking at the same moment): no second boat, not taken back at once
		Object[] twice = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			Text a = ShipBoatHandling.launch(s, w, player(srv));
			Text b = ShipBoatHandling.use(s, w, null);
			Text c = ShipBoatHandling.use(s, w, null);
			return new Object[] {a == null ? "" : a.getString(), boatsOf(w, s.getUuid()), s.toggle(ShipBoats.AWAY_BIT), b == null ? "" : b.getString(),
					c == null ? "" : c.getString()};
		});
		log.accept(String.format(Locale.ROOT, "%s boat: launch again -> '%s' / use -> '%s' / '%s'", id, twice[0], twice[3], twice[4]));
		check.accept((Integer) twice[1] == 1 && Boolean.TRUE.equals(twice[2]) && ((String) twice[3]).contains("manœuvre"), String.format(Locale.ROOT,
				"%s boat: one boat per ship, a second click at once neither launches another nor takes it back (%s boat, '%s')", id, twice[1], twice[3]));
		check.accept(bl[0] < -(hull.halfWidth(bl[2]) + 1.0 + 0.5), String.format(Locale.ROOT,
				"%s boat: on the clicking player's side (starboard), clear of the hull (local x %.2f, hull half width %.2f)", id, bl[0], hull.halfWidth(bl[2])));
		// it floats on the surface, inside nothing
		context.waitTicks(40);
		double[] fl = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			Entity b = ShipBoatHandling.boat(s, w);
			if (b == null) {
				return null;
			}
			BlockPos top = BlockPos.ofFloored(b.getX(), TOP, b.getZ());
			double surface = top.getY() + (double) w.getFluidState(top).getHeight(w, top);
			int hits = fr.medievalships.core.ShipMover.countCollisions(Ships.ROWBOAT.geometry(), ((ShipEntity) b).pose(), (x, y, z) -> {
				BlockPos p = BlockPos.ofFloored(x, y, z);
				return !w.getBlockState(p).getCollisionShape(w, p).isEmpty();
			});
			return new double[] {b.getY() + Ships.ROWBOAT.hull().waterlineY, surface, hits, s.getY() + s.geometry().hull().waterlineY};
		});
		check.accept(fl != null && Math.abs(fl[0] - fl[1]) < 0.3 && fl[2] == 0, fl == null ? id + " boat: gone after its launch"
				: String.format(Locale.ROOT, "%s boat: floats on the surface (water line %.2f, surface %.2f, ship's water line %.2f, %d collisions)", id, fl[0], fl[1], fl[3],
						(int) fl[2]));
		Boolean clientAway = context.computeOnClient((MinecraftClient mc) -> {
			ShipEntity s = clientShip(mc, type);
			return s != null && s.toggle(ShipBoats.AWAY_BIT);
		});
		check.accept(Boolean.TRUE.equals(clientAway), id + " boat: the deco boat is hidden on the client too");
		server.runCommand("gamemode spectator @a");
		double off = ShipBoats.sideOffset(hull, spec.launchZ());
		lookLocal(server, pose, -off - 13, hull.waterlineY + 7, spec.launchZ() - 8, -off * 0.4, hull.waterlineY + 1.5, spec.launchZ());
		context.waitTicks(20);
		shot.accept(id + "_barque_1_a_l_eau");
		double deckTop = deckSpot(type)[1];
		lookLocal(server, pose, -3.5, deckTop + 4.5, spec.launchZ() - 6, 0, deckTop, (spec.deco().minZ() + spec.deco().maxZ()) / 2);
		context.waitTicks(12);
		shot.accept(id + "_barque_2_chantier_vide");

		// 3. too far from its chocks: refused, it stays on the water
		double reach = ShipBoats.reach(spec, hull);
		double farZ = spec.launchZ() + (spec.launchZ() >= 0 ? -1 : 1) * (reach + 2);
		Object[] far = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			Entity b = ShipBoatHandling.boat(s, w);
			double[] home = {b.getX(), b.getY(), b.getZ()};
			double[] there = s.pose().toWorld(-off - 2, hull.waterlineY, farZ);
			b.setPosition(there[0], b.getY(), there[2]);
			Text t = ShipBoatHandling.recover(s, w, null, false);
			boolean stays = ShipBoatHandling.boat(s, w) != null && s.toggle(ShipBoats.AWAY_BIT);
			b.setPosition(home[0], home[1], home[2]);
			return new Object[] {t == null ? "" : t.getString(), stays};
		});
		log.accept(String.format(Locale.ROOT, "%s boat: recovered from %.0f blocks along the hull -> '%s'", id, Math.abs(farZ - spec.launchZ()), far[0]));
		check.accept(((String) far[0]).contains("trop loin") && Boolean.TRUE.equals(far[1]),
				String.format(Locale.ROOT, "%s boat: too far, refused with a message (%s), it stays on the water", id, far[0]));

		// 4. clicked again from the deck: hoisted aboard, the deco is back (server and client)
		context.waitTicks(30);
		clickDecoBoat(context, server, type);
		Object[] back = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			return new Object[] {s.toggle(ShipBoats.AWAY_BIT), boatsOf(w, s.getUuid()), s.lifeboatId()};
		});
		context.waitTicks(5);
		Boolean clientBack = context.computeOnClient((MinecraftClient mc) -> {
			ShipEntity s = clientShip(mc, type);
			return s != null && !s.toggle(ShipBoats.AWAY_BIT);
		});
		check.accept(!Boolean.TRUE.equals(back[0]) && (Integer) back[1] == 0 && back[2] == null && Boolean.TRUE.equals(clientBack),
				String.format(Locale.ROOT, "%s boat: the click again hoists it aboard, the deco is back (away %s, %s boat, client %s)", id, back[0], back[1], clientBack));
		server.runCommand("gamemode spectator @a");
		lookLocal(server, pose, -3.5, deckTop + 4.5, spec.launchZ() - 6, 0, deckTop, (spec.deco().minZ() + spec.deco().maxZ()) / 2);
		context.waitTicks(12);
		shot.accept(id + "_barque_3_rembarquee");

		// 5. from the boat itself: its rower clicks the hull, the boat is hoisted aboard and he is put on the deck
		server.runCommand("gamemode survival @a");
		double[] spot = deckSpot(type);
		double[] sw = pose.toWorld(spot[0], spot[1] + 0.02, spot[2]);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f", sw[0], sw[1], sw[2]));
		context.waitTicks(45);
		Object[] hoist = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			ServerPlayerEntity p = player(srv);
			Text t = ShipBoatHandling.launch(s, w, p);
			Entity b = ShipBoatHandling.boat(s, w);
			boolean seated = b instanceof RowboatEntity rb && rb.seat(p, ShipGeometry.PILOT_SEAT);
			return new Object[] {t == null ? "" : t.getString(), seated};
		});
		context.waitTicks(45);
		Object[] h = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			ServerPlayerEntity p = player(srv);
			boolean riding = p.getVehicle() instanceof RowboatEntity;
			boolean handled = ShipBoatHandling.hoistFrom(s, w, p);
			return new Object[] {riding, handled, s.toggle(ShipBoats.AWAY_BIT), boatsOf(w, s.getUuid()), p.hasVehicle()};
		});
		context.waitTicks(20);
		double[] me = server.computeOnServer(srv -> {
			ServerPlayerEntity p = player(srv);
			ShipEntity s = ship(srv.getOverworld(), type);
			double[] lp = s.pose().toLocal(p.getX(), p.getY(), p.getZ());
			return new double[] {lp[0], lp[1], lp[2], s.geometry().inCarryVolume(lp[0], lp[1], lp[2]) ? 1 : 0};
		});
		log.accept(String.format(Locale.ROOT, "%s boat: launched for the rower '%s', seated %s; hoisted from it: riding %s, handled %s, away %s, %s boat; rower at local %.2f %.2f %.2f",
				id, hoist[0], hoist[1], h[0], h[1], h[2], h[3], me[0], me[1], me[2]));
		check.accept(Boolean.TRUE.equals(hoist[1]) && Boolean.TRUE.equals(h[0]) && Boolean.TRUE.equals(h[1]) && !Boolean.TRUE.equals(h[2]) && (Integer) h[3] == 0
				&& !Boolean.TRUE.equals(h[4]) && me[3] == 1 && me[1] > hull.waterlineY + 0.5,
				String.format(Locale.ROOT, "%s boat: its rower clicks the hull: hoisted aboard, he stands on the deck (local %.2f %.2f %.2f)", id, me[0], me[1], me[2]));

		// the warship's boat is a deck box one stands on: it goes with the boat
		if (spec.solid() != null) {
			int[] boxes = new int[2];
			for (int k = 0; k < 2; k++) {
				boolean away = k == 1;
				boxes[k] = server.computeOnServer(srv -> {
					ServerWorld w = srv.getOverworld();
					ShipEntity s = ship(w, type);
					s.setToggle(ShipBoats.AWAY_BIT, away);
					double[] c = s.pose().toWorld(0, (spec.solid().minY() + spec.solid().maxY()) / 2, (spec.solid().minZ() + spec.solid().maxZ()) / 2);
					net.minecraft.util.math.Box q = new net.minecraft.util.math.Box(c[0] - 0.4, c[1] - 0.2, c[2] - 0.4, c[0] + 0.4, c[1] + 0.2, c[2] + 0.4);
					java.util.List<net.minecraft.util.shape.VoxelShape> out = new java.util.ArrayList<>();
					fr.medievalships.entity.ShipCollisions.appendHulls(out, null, q, w);
					s.setToggle(ShipBoats.AWAY_BIT, false);
					return out.size();
				});
			}
			check.accept(boxes[0] > 0 && boxes[1] == 0, String.format(Locale.ROOT,
					"%s boat: one stands on the deco boat, not on its empty chocks while it is away (%d / %d boxes)", id, boxes[0], boxes[1]));
		}

		if (type == Ships.GALLEON) {
			robustness(context, server, type, check, log);
		}
	}

	/** The galleon: out of the water, a boat destroyed, a boat written off, the ship picked up. */
	private static void robustness(ClientGameTestContext context, TestServerContext server, ShipType type, BiConsumer<Boolean, String> check,
			Consumer<String> log) {
		String id = type.id();
		context.waitTicks(45);
		// lifted out of the water (one tick, put back at once): refused, no boat
		Object[] dry = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			double y = s.getY();
			s.setPosition(s.getX(), y + 8, s.getZ());
			Text t = ShipBoatHandling.launch(s, w, null);
			s.setPosition(s.getX(), y, s.getZ());
			return new Object[] {t == null ? "" : t.getString(), s.toggle(ShipBoats.AWAY_BIT), boatsOf(w, s.getUuid())};
		});
		log.accept(String.format(Locale.ROOT, "%s boat out of the water: '%s'", id, dry[0]));
		check.accept(((String) dry[0]).contains("pas à flot") && !Boolean.TRUE.equals(dry[1]) && (Integer) dry[2] == 0,
				String.format(Locale.ROOT, "%s boat: refused with a message while the ship is not afloat (%s)", id, dry[0]));

		// two players clicking on the same tick while it is aboard: one launch, the other click refused (no boat taken back)
		Object[] race = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			Text a = ShipBoatHandling.use(s, w, player(srv));
			Text b = ShipBoatHandling.use(s, w, null);
			return new Object[] {a == null ? "" : a.getString(), b == null ? "" : b.getString(), s.toggle(ShipBoats.AWAY_BIT), boatsOf(w, s.getUuid())};
		});
		log.accept(String.format(Locale.ROOT, "%s boat: two clicks on the same tick -> '%s' / '%s'", id, race[0], race[1]));
		check.accept(Boolean.TRUE.equals(race[2]) && (Integer) race[3] == 1, String.format(Locale.ROOT,
				"%s boat: two players clicking on the same tick: one boat on the water (away %s, %s boat)", id, race[2], race[3]));
		context.waitTicks(45);
		server.computeOnServer(srv -> ShipBoatHandling.recover(ship(srv.getOverworld(), type), srv.getOverworld(), null, false));
		context.waitTicks(45);

		// destroyed on the water: the ship notices it and has its deco back, no boat left
		server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			ShipBoatHandling.launch(s, w, null);
			return null;
		});
		context.waitTicks(30);
		server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			Entity b = ShipBoatHandling.boat(ship(w, type), w);
			if (b != null) {
				b.discard();
			}
			return null;
		});
		context.waitTicks(70);
		Object[] lost = server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return new Object[] {s.toggle(ShipBoats.AWAY_BIT), s.lifeboatId()};
		});
		check.accept(!Boolean.TRUE.equals(lost[0]) && lost[1] == null, String.format(Locale.ROOT,
				"%s boat: destroyed on the water, the ship has its deco back within seconds (away %s)", id, lost[0]));

		// written off while out of reach (as a recovery does): the old boat vanishes when it is seen again, never two
		context.waitTicks(45);
		UUID old = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			ShipBoatHandling.launch(s, w, null);
			UUID b = s.lifeboatId();
			if (b != null) {
				ShipData.get(srv).retireBoat(b);
				s.setLifeboatId(null);
				s.setToggle(ShipBoats.AWAY_BIT, false);
			}
			return b;
		});
		context.waitTicks(60);
		Object[] retired = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			Entity b = old == null ? null : w.getEntity(old);
			return new Object[] {old != null, b == null || b.isRemoved(), old != null && ShipData.get(srv).isRetiredBoat(old), boatsOf(w, ship(w, type).getUuid())};
		});
		check.accept(Boolean.TRUE.equals(retired[0]) && Boolean.TRUE.equals(retired[1]) && !Boolean.TRUE.equals(retired[2]) && (Integer) retired[3] == 0,
				String.format(Locale.ROOT, "%s boat: written off by its ship, the old boat vanishes when it is seen again (gone %s, remembered %s)", id, retired[1], retired[2]));

		// the ship picked up: its boat on the water stays, an ordinary Rowboat
		context.waitTicks(45);
		UUID left = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ShipEntity s = ship(w, type);
			ShipBoatHandling.launch(s, w, null);
			UUID b = s.lifeboatId();
			s.discard();
			return b;
		});
		context.waitTicks(50);
		Object[] orphan = server.computeOnServer(srv -> {
			Entity b = left == null ? null : srv.getOverworld().getEntity(left);
			return new Object[] {b instanceof RowboatEntity && !b.isRemoved(), b instanceof RowboatEntity rb && rb.motherShip() == null,
					b != null && b.getCommandTags().contains(ShipBoats.TAG)};
		});
		check.accept(Boolean.TRUE.equals(orphan[0]) && Boolean.TRUE.equals(orphan[1]) && !Boolean.TRUE.equals(orphan[2]),
				String.format(Locale.ROOT, "%s boat: the ship picked up, its boat stays on the water as an ordinary Rowboat (there %s, free %s)", id, orphan[0], orphan[1]));
	}
}
