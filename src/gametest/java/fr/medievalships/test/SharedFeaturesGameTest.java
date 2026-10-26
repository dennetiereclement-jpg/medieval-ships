package fr.medievalships.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.world.Heightmap;

import fr.medievalships.client.PilotHudOverlay;
import fr.medievalships.client.PlacementPreview;
import fr.medievalships.core.Autopilot;
import fr.medievalships.core.Flight;
import fr.medievalships.core.GotoRoutes;
import fr.medievalships.core.LeviathanLayout;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.data.ShipData;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipPlacement;
import fr.medievalships.entity.ShipTracker;
import fr.medievalships.network.ShipInteractions;

/**
 * In-game checks of the features shared by every vessel (called once from {@link ShipClientGameTest}, about 90 s of
 * game time): the placement preview (green ghost where the server places the vessel, red where it does not fit and
 * then nothing is placed, the per-vessel placement permission), the pilot's panel (shown at the helm, hidden for the
 * others), a destination given by the pilot with {@code /pilote goto} (the autopilot takes the helm, flies there and
 * stops; taking the helm back cancels it), and the bank in the turns of the steampunk airship and the Sky Leviathan
 * with a player standing on the deck (he stays on it).
 */
public final class SharedFeaturesGameTest {
	/** The test area: open ground well away from the other tests. */
	private static final int X = 200, Z = -420;

	private SharedFeaturesGameTest() {
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		List<UUID> mine = new ArrayList<>();
		server.runCommand("ride @p dismount");
		server.runCommand("clear @a");
		try {
			UUID placed = preview(context, server, world, check, log, shot, mine);
			if (placed != null) {
				hudAndGoto(context, server, placed, check, log, shot);
			}
		} catch (RuntimeException e) {
			check.accept(false, "shared features: preview / panel / goto: exception " + e);
		}
		remove(server, mine);
		try {
			banking(context, server, world, Ships.STEAMPUNK_AIRSHIP, X, Z - 120, 35, 0, 0.8, 0.1, -2, 0, check, log, shot, mine);
		} catch (RuntimeException e) {
			check.accept(false, "shared features: steampunk_airship banking: exception " + e);
		}
		remove(server, mine);
		try {
			banking(context, server, world, Ships.SKY_LEVIATHAN, X, Z - 330, 60, LeviathanLayout.MAIN_DECK_Y, 0, 0.6, 4.0, 180, check, log,
					shot, mine);
		} catch (RuntimeException e) {
			check.accept(false, "shared features: sky_leviathan banking: exception " + e);
		}
		remove(server, mine);
		server.runCommand("ride @p dismount");
		server.runCommand("clear @a");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
	}

	// ------------------------------------------------------------------ helpers

	private static ShipEntity byId(ServerWorld world, UUID id) {
		return world.getEntity(id) instanceof ShipEntity s && !s.isRemoved() ? s : null;
	}

	private static ShipPose pose(TestServerContext server, UUID id) {
		return server.computeOnServer(srv -> {
			ShipEntity s = byId(srv.getOverworld(), id);
			return s == null ? null : s.pose();
		});
	}

	/** The vessels of this type near the test area, as the server sees them. */
	private static List<UUID> near(TestServerContext server, ShipType type, double x, double z, double r) {
		return server.computeOnServer(srv -> {
			List<UUID> out = new ArrayList<>();
			for (ShipEntity s : ShipTracker.ships(srv.getOverworld())) {
				if (!s.isRemoved() && s.shipType() == type && Math.hypot(s.getX() - x, s.getZ() - z) < r) {
					out.add(s.getUuid());
				}
			}
			return out;
		});
	}

	private static void remove(TestServerContext server, List<UUID> ids) {
		server.runCommand("ride @p dismount");
		server.computeOnServer(srv -> {
			for (UUID id : ids) {
				ShipEntity s = byId(srv.getOverworld(), id);
				if (s != null) {
					s.cancelGoto();
					s.setAutopilot(false);
					s.removeAllPassengers();
					s.discard();
				}
			}
			return null;
		});
		ids.clear();
	}

	private static int ground(TestServerContext server, int x, int z) {
		return server.computeOnServer(srv -> srv.getOverworld().getTopY(Heightmap.Type.MOTION_BLOCKING, x, z));
	}

	private static double[] playerLocal(ClientGameTestContext context, ShipPose pose) {
		double[] p = context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ()});
		return pose.toLocal(p[0], p[1], p[2]);
	}

	private static void tpLocal(TestServerContext server, ShipPose pose, double lx, double ly, double lz, float localYaw, float pitch) {
		double[] w = pose.toWorld(lx, ly, lz);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", w[0], w[1], w[2], (float) (pose.yaw() + localYaw), pitch));
	}

	/** A screenshot without the chat lines of the commands. */
	private static void shot(ClientGameTestContext context, Consumer<String> shot, String name) {
		context.runOnClient(c -> c.inGameHud.getChatHud().clear(false));
		context.waitTicks(2);
		shot.accept(name);
	}

	private static void lookLocal(TestServerContext server, ShipPose pose, double ex, double ey, double ez, double tx, double ty, double tz) {
		double[] e = pose.toWorld(ex, ey, ez), t = pose.toWorld(tx, ty, tz);
		double dx = t[0] - e[0], dy = t[1] - e[1], dz = t[2] - e[2];
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", e[0], e[1] - 1.62, e[2], yaw, pitch));
	}

	// ------------------------------------------------------------------ 1. the placement preview, the space check, the permission

	/** @return the airship placed with the item (kept for the panel and goto checks), or null */
	private static UUID preview(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot, List<UUID> mine) {
		ShipType type = Ships.STEAMPUNK_AIRSHIP;
		String id = type.id();
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -20 %d 0 20", X, Z));
		context.waitTicks(40);
		int ground = ground(server, X, Z);
		server.runCommand("gamemode creative @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.1f %d %.1f 0 20", X + 0.5, ground, Z + 0.5));
		world.waitForChunksRender();
		context.waitTicks(20);
		server.runCommand("item replace entity @p weapon.mainhand with medievalships:" + id);
		context.waitTicks(15);
		PlacementPreview.State st = context.computeOnClient((MinecraftClient c) -> PlacementPreview.current());
		check.accept(st != null && st.type() == type && st.valid(),
				"preview: holding the " + id + " item over open ground shows a green ghost (" + (st == null ? "none" : st.valid() + " " + st.pose()) + ")");
		if (st == null) {
			return null;
		}
		ShipPlacement.Spot sv = server.computeOnServer(srv ->
				ShipPlacement.find(srv.getOverworld(), type, st.hitX(), st.hitY(), st.hitZ(), st.yaw(), true));
		double agree = sv == null ? 99 : Math.hypot(Math.hypot(sv.pose().x() - st.pose().x(), sv.pose().y() - st.pose().y()), sv.pose().z() - st.pose().z());
		check.accept(sv != null && sv.valid() == st.valid() && agree < 1e-6,
				String.format(Locale.ROOT, "preview: the server's space check gives the same spot (%.6f blocks apart)", agree));
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, shot, "partage_1_apercu_vert");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));

		// placement still works, where the ghost was
		List<UUID> before = near(server, type, X, Z, 60);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(20);
		List<UUID> after = near(server, type, X, Z, 60);
		after.removeAll(before);
		UUID placed = after.isEmpty() ? null : after.get(0);
		mine.addAll(after);
		ShipPose p = placed == null ? null : pose(server, placed);
		double off = p == null ? 99 : Math.hypot(p.x() - st.pose().x(), p.z() - st.pose().z());
		check.accept(p != null && off < 0.6 && Math.abs(p.y() - st.pose().y()) < 0.6 && Math.abs(ShipPose.wrapDegrees(p.yaw() - st.pose().yaw())) < 3,
				String.format(Locale.ROOT, "preview: right click places the %s where the ghost was (%.2f blocks off, %s)", id, off, p));
		boolean ghostGone = context.computeOnClient((MinecraftClient c) -> {
			PlacementPreview.State s = PlacementPreview.current();
			return s == null || s.pose().y() != st.pose().y() || !s.valid() || Math.hypot(s.pose().x() - st.pose().x(), s.pose().z() - st.pose().z()) > 1;
		});
		check.accept(ghostGone, "preview: once placed, the spot is no longer shown free");

		// red where it cannot fit: aiming at the ground just before a stone cliff higher than the airship can be
		// placed above it; a right click places nothing
		server.runCommand(String.format(Locale.ROOT, "tp @p %.1f %d %.1f 180 20", X + 0.5, ground, Z - 29.5));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d stone", X - 9, ground, Z - 62, X + 9, ground + 36, Z - 36));
		context.waitTicks(25);
		PlacementPreview.State red = context.computeOnClient((MinecraftClient c) -> PlacementPreview.current());
		check.accept(red != null && !red.valid(), "preview: in front of a stone cliff the ghost is red (" + (red == null ? "none" : red.pose()) + ")");
		context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
		context.waitTicks(5);
		shot(context, shot, "partage_2_apercu_rouge");
		context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
		List<UUID> b2 = near(server, type, X, Z - 40, 40);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(15);
		List<UUID> a2 = near(server, type, X, Z - 40, 40);
		a2.removeAll(b2);
		mine.addAll(a2);
		check.accept(a2.isEmpty(), "preview: where it is red, a right click places nothing");
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", X - 9, ground, Z - 62, X + 9, ground + 36, Z - 36));

		// the permission: an airship reserved to the admins (placeAdminOnly)
		boolean admin = server.computeOnServer(srv -> ShipPermissions.isAdmin(srv.getPlayerManager().getPlayerList().get(0)));
		server.computeOnServer(srv -> {
			ConfigManager.server().placeAdminOnly.add(id);
			return null;
		});
		server.runCommand(String.format(Locale.ROOT, "tp @p %.1f %d %.1f 90 30", X - 29.5, ground, Z + 0.5));
		context.waitTicks(20);
		List<UUID> b3 = near(server, type, X - 50, Z, 30);
		context.getInput().pressKey(o -> o.useKey);
		context.waitTicks(15);
		List<UUID> a3 = near(server, type, X - 50, Z, 30);
		a3.removeAll(b3);
		mine.addAll(a3);
		server.computeOnServer(srv -> {
			ConfigManager.server().placeAdminOnly.remove(id);
			return null;
		});
		log.accept("shared features: player is admin: " + admin + ", placed with placeAdminOnly: " + a3.size());
		check.accept(admin ? a3.size() == 1 : a3.isEmpty(), admin
				? "permissions: an admin places a vessel reserved to the admins (placeAdminOnly)"
				: "permissions: a player who is not an admin cannot place a vessel reserved to the admins (placeAdminOnly)");
		server.runCommand("clear @a");
		context.waitTicks(5);
		boolean cleared = context.computeOnClient((MinecraftClient c) -> PlacementPreview.current() == null);
		check.accept(cleared, "preview: no ghost once the item is put away");
		return placed;
	}

	// ------------------------------------------------------------------ 2. the pilot's panel, 3. a destination with /pilote goto

	private static void hudAndGoto(ClientGameTestContext context, TestServerContext server, UUID id, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot) {
		server.runCommand("gamemode survival @a");
		ShipPose a = pose(server, id);
		ShipGeometry g = Ships.STEAMPUNK_AIRSHIP.geometry();
		tpLocal(server, a, 0, g.hull().mainDeckY + 0.1, -2, 0, 10);
		context.waitTicks(15);
		List<String> none = context.computeOnClient((MinecraftClient c) -> PilotHudOverlay.lines());
		check.accept(none.isEmpty(), "panel: a player on the deck (not at the helm) sees no pilot's panel " + none);
		boolean seated = server.computeOnServer(srv -> {
			ShipEntity s = byId(srv.getOverworld(), id);
			return s != null && s.seat(srv.getPlayerManager().getPlayerList().get(0), ShipGeometry.PILOT_SEAT);
		});
		context.waitTicks(15);
		List<String> hud = context.computeOnClient((MinecraftClient c) -> PilotHudOverlay.lines());
		log.accept("shared features: pilot's panel " + hud);
		String all = String.join(" | ", hud);
		check.accept(seated && all.contains("Vitesse :") && all.contains("Altitude :") && all.contains("Moteur :")
				&& all.contains("Pilote auto : inactif") && all.contains("Espace monter"),
				"panel: the pilot of the airship sees speed, altitude, engine and autopilot state, keys (" + all + ")");
		shot(context, shot, "partage_3_hud_pilote");

		// the pilot gives a destination: 45 blocks ahead, 6 blocks higher (as a player, from the chat)
		ShipPose s0 = pose(server, id);
		double[] dest = s0.toWorld(0, g.hull().mainDeckY + 6, 45);
		String cmd = String.format(Locale.ROOT, "pilote goto %.1f %.1f %.1f", dest[0], dest[1], dest[2]);
		context.runOnClient(c -> c.player.networkHandler.sendChatCommand(cmd));
		context.waitTicks(20);
		Object[] st = server.computeOnServer(srv -> {
			ShipEntity s = byId(srv.getOverworld(), id);
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			return s == null ? null : new Object[] {s.isAutopilotEnabled(), s.routeName(), pl.getVehicle() == s,
					ShipData.get(srv).route(s.routeName()) != null};
		});
		check.accept(st != null && (Boolean) st[0] && GotoRoutes.isGoto((String) st[1]) && !(Boolean) st[2] && (Boolean) st[3],
				"goto: /pilote goto x y z from the helm hands it to the autopilot on its own route (" + (st == null ? "none" : java.util.Arrays.toString(st)) + ")");
		context.waitTicks(20);
		List<String> auto = context.computeOnClient((MinecraftClient c) -> PilotHudOverlay.lines());
		String autoAll = String.join(" | ", auto);
		check.accept(autoAll.contains("Pilote auto : en route") && autoAll.contains("reprendre la main"),
				"panel: standing by the helm while the autopilot flies there, the panel shows it (" + autoAll + ")");
		shot(context, shot, "partage_4_hud_pilote_auto");
		ShipPose b = s0;
		String phase = "";
		for (int i = 0; i < 45; i++) {
			context.waitTicks(20);
			b = pose(server, id);
			phase = server.computeOnServer(srv -> {
				ShipEntity s = byId(srv.getOverworld(), id);
				return s == null ? "" : s.autopilot().phase.name();
			});
			if (Autopilot.Phase.FINISHED.name().equals(phase)) {
				break;
			}
		}
		double reach = Math.hypot(b.x() - dest[0], b.z() - dest[2]);
		double deck = b.y() + g.hull().mainDeckY;
		log.accept(String.format(Locale.ROOT, "shared features: goto: %s, %.1f blocks from the destination, deck %.2f for %.2f", phase, reach, deck, dest[1]));
		check.accept(Autopilot.Phase.FINISHED.name().equals(phase) && reach < 3.5 && Math.abs(deck - dest[1]) < 1.5,
				String.format(Locale.ROOT, "goto: the airship flies to the destination and stops there (%.1f blocks away, deck %.2f for %.2f)", reach, deck, dest[1]));
		double[] l = playerLocal(context, b);
		check.accept(g.inCarryVolume(l[0], l[1], l[2]), String.format(Locale.ROOT,
				"goto: the player standing by the helm arrived with it (local %.2f %.2f %.2f)", l[0], l[1], l[2]));
		// taking the helm back cancels the destination
		Object[] back = server.computeOnServer(srv -> {
			ShipEntity s = byId(srv.getOverworld(), id);
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			if (s == null) {
				return null;
			}
			String route = s.routeName();
			ShipInteractions.takeHelm(s, pl);
			return new Object[] {s.isAutopilotEnabled(), pl.getVehicle() == s && s.seatOf(pl) == ShipGeometry.PILOT_SEAT,
					route != null && ShipData.get(srv).route(route) == null};
		});
		check.accept(back != null && !(Boolean) back[0] && (Boolean) back[1] && (Boolean) back[2],
				"goto: taking the helm back cancels the destination and seats the player at the helm ("
						+ (back == null ? "none" : java.util.Arrays.toString(back)) + ")");
		server.runCommand("ride @p dismount");
		context.waitTicks(5);
	}

	// ------------------------------------------------------------------ 4. banking, with a player standing on the deck

	private static void banking(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, ShipType type,
			int x, int z, double radius, double deckY, double standX, double standY, double standZ, float standYaw, BiConsumer<Boolean, String> check,
			Consumer<String> log, Consumer<String> shot, List<UUID> mine) {
		String id = type.id();
		ShipGeometry g = type.geometry();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d -20 %d 0 20", x, z - 40));
		context.waitTicks(40);
		int ground = ground(server, x, z);
		List<UUID> before = near(server, type, x, z, 40);
		// placed high enough above the ground for its autopilot's clearance: it turns at once, without climbing first
		int air = ground + (int) Math.ceil(type.defaults().get().flight.aiClearance) + 2;
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d %d rotated 0 0 run ship spawn %s", x, air, z, id));
		context.waitTicks(20);
		List<UUID> after = near(server, type, x, z, 40);
		after.removeAll(before);
		if (after.isEmpty()) {
			check.accept(false, id + " banking: spawned");
			return;
		}
		UUID ship = after.get(0);
		mine.add(ship);
		ShipPose a = pose(server, ship);
		// a loop of 8 points on a circle to the right of the bow, at the airship's height (the autopilot keeps its
		// clearance over the ground): it turns all the time
		String route = "virage_" + id;
		server.runCommand("ship route delete " + route);
		server.runCommand("ship route create " + route + " loop air");
		double cx = a.x() - radius, cz = a.z(), deckWorld = a.y() + g.hull().mainDeckY;
		for (int k = 0; k < 8; k++) {
			double t = Math.toRadians(45 * k);
			server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route addpoint %s",
					cx + radius * Math.cos(t), deckWorld, cz + radius * Math.sin(t), route));
		}
		server.runCommand("gamemode survival @a");
		tpLocal(server, a, standX, deckY + standY, standZ, standYaw, 10);
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship route assign %s", a.x(), a.y(), a.z(), route));
		server.computeOnServer(srv -> {
			ShipEntity s = byId(srv.getOverworld(), ship);
			if (s != null) {
				s.physics().speed = s.config().normalSpeed; // already cruising: the turns start at once
			}
			return null;
		});
		double limit = Flight.bankLimit(g, type.defaults().get().flight);
		double maxBank = 0, worstDeck = 0;
		boolean aboard = true, shotTaken = false;
		double turned = 0;
		ShipPose last = a;
		for (int i = 0; i < 36; i++) {
			if (i == 8) {
				context.getInput().holdKeyFor(o -> o.forwardKey, 8); // a few steps on the banking deck
			} else if (i == 12) {
				context.getInput().holdKeyFor(o -> o.backKey, 8);
			}
			context.waitTicks(10);
			float bank = context.computeOnClient((MinecraftClient c) -> {
				for (ShipEntity s : ShipTracker.ships(c.world)) {
					if (s.getUuid().equals(ship)) {
						return s.bankVisual;
					}
				}
				return 0f;
			});
			maxBank = Math.max(maxBank, Math.abs(bank));
			ShipPose p = pose(server, ship);
			if (p == null) {
				break;
			}
			turned += Math.abs(ShipPose.wrapDegrees(p.yaw() - last.yaw()));
			last = p;
			double[] l = playerLocal(context, p);
			if (i >= 20) {
				aboard &= g.inCarryVolume(l[0], l[1], l[2]);
				worstDeck = Math.max(worstDeck, Math.abs(l[1] - deckY));
			}
			if (!shotTaken && Math.abs(bank) > 0.6 * limit) {
				shotTaken = true;
				context.runOnClient(c -> c.options.setPerspective(Perspective.THIRD_PERSON_BACK));
				context.waitTicks(3);
				shot(context, shot, "partage_5_inclinaison_" + id);
				context.runOnClient(c -> c.options.setPerspective(Perspective.FIRST_PERSON));
			}
		}
		log.accept(String.format(Locale.ROOT, "shared features: %s banking: turned %.0f deg, bank up to %.2f deg (limit %.2f), player %s, worst deck offset %.3f",
				id, turned, maxBank, limit, aboard ? "aboard" : "thrown off", worstDeck));
		check.accept(turned > 40, String.format(Locale.ROOT, "%s banking: the autopilot turns all the time on the loop (%.0f deg)", id, turned));
		check.accept(maxBank > 0.4 * limit && maxBank <= limit + 1e-3,
				String.format(Locale.ROOT, "%s banking: it banks into the turns, within its limit (%.2f of %.2f deg)", id, maxBank, limit));
		check.accept(aboard && worstDeck < 0.25, String.format(Locale.ROOT,
				"%s banking: the player standing (and walking) on the deck stays on it (worst %.3f blocks off the deck)", id, worstDeck));
		// from outside, still turning: in front of the bow, the bank shows as a tilt against the horizon
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		ShipPose p = pose(server, ship);
		if (p != null) {
			double r = g.boundingRadius();
			double mid = 0.5 * (g.lowestY() + g.topY());
			// where it will be in half a second (the spectator camera is placed by a command, the ship goes on)
			double half = type.defaults().get().normalSpeed * 0.5;
			ShipPose ahead = new ShipPose(p.worldX(0, half), p.y(), p.worldZ(0, half), p.yaw());
			lookLocal(server, ahead, 0, mid, 1.15 * r, 0, mid, 0);
			context.waitTicks(10);
			shot(context, shot, "partage_6_inclinaison_dehors_" + id);
		}
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.2f %.2f %.2f run ship ai disable", last.x(), last.y(), last.z()));
		server.runCommand("ship route delete " + route);
	}
}
