package fr.medievalships.test;

import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.registry.Registries;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.bridge.Drawbridge;
import fr.medievalships.bridge.Drawbridges;
import fr.medievalships.client.bridge.DrawbridgeClient;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;
import fr.medievalships.core.bridge.BridgeCycle;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks of the automatic drawbridge (1.24.0), in a canal built by commands: two banks with four towers, a
 * plank deck 5 blocks over the water with fences, a fixed high walkway between the towers. The bridge is defined and
 * converted with the real {@code /pontlevis} commands (the block in the swept volume is reported, the deck stays
 * made of its blocks once converted), then:
 * <ul>
 * <li>a rowboat sails under the closed deck without any lift, with an occupant too; a bigger margin makes the same
 * loaded rowboat open the bridge; the deck's blocks come back once it has closed;</li>
 * <li>a galley on its autopilot coming from the west triggers the opening when its bow is 50 blocks from the deck,
 * waits before the deck while the leaves rise, passes once open (the bridge staying open while it is in the
 * passage), and the bridge closes after it has left the keep zone; the same from the east;</li>
 * <li>a player on the deck holds the opening (diagnostic), which starts once he steps off; a demand during the
 * closing reverses it; the barrier across the deck's end stops a walking player; the passage is really free when
 * open (a player there falls into the water);</li>
 * <li>restoration puts the original blocks back without touching the towers; deletion.</li>
 * </ul>
 * The solo run keeps the bridge open across a world restart (see {@link #beforeRestart}, {@link #afterRestart}).
 * Called from {@link ShipClientGameTest} (solo and on the dedicated server).
 */
public final class DrawbridgeGameTest {
	static final String ID = "test_pont";
	/** The canal runs along x; the deck is at x 2676..2680, the channel is z -9..9. */
	static final int X0 = 2560, X1 = 2800, Z0 = -24, Z1 = 24;
	static final int DECK_X0 = 2676, DECK_X1 = 2680, DECK_Y = -44;
	static final double WATER = -49.1;
	static final double DECK_WEST = 2676, DECK_EAST = 2681;

	private DrawbridgeGameTest() {
	}

	// ------------------------------------------------------------------ helpers

	private static BridgeCycle.State state(TestServerContext server) {
		return server.computeOnServer(srv -> {
			Drawbridge b = Drawbridges.get(ID);
			return b == null ? null : b.cycle().state();
		});
	}

	private static double angle(TestServerContext server) {
		return server.computeOnServer(srv -> {
			Drawbridge b = Drawbridges.get(ID);
			return b == null ? -1 : b.cycle().angle();
		});
	}

	private static String blockAt(TestServerContext server, int x, int y, int z) {
		return server.computeOnServer(srv -> Registries.BLOCK.getId(srv.getOverworld().getBlockState(new BlockPos(x, y, z)).getBlock()).getPath());
	}

	private static ShipEntity ship(ServerWorld world, ShipType type) {
		for (ShipEntity s : ShipTracker.ships(world)) {
			if (!s.isRemoved() && s.shipType() == type) {
				return s;
			}
		}
		return null;
	}

	/** {x, z, speed} of a vessel, or null. */
	private static double[] shipPos(TestServerContext server, ShipType type) {
		return server.computeOnServer(srv -> {
			ShipEntity s = ship(srv.getOverworld(), type);
			return s == null ? null : new double[] {s.getX(), s.getZ(), s.physics().speed};
		});
	}

	private static String trackedReason(TestServerContext server, String labelPart) {
		return server.computeOnServer(srv -> {
			Drawbridge b = Drawbridges.get(ID);
			if (b == null) {
				return null;
			}
			for (Drawbridge.Tracked t : b.tracked().values()) {
				if (t.label != null && t.label.toLowerCase(Locale.ROOT).contains(labelPart)) {
					return t.reason;
				}
			}
			return null;
		});
	}

	private static double[] player(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> new double[] {c.player.getX(), c.player.getY(), c.player.getZ()});
	}

	private static void tp(TestServerContext server, double x, double y, double z, float yaw, float pitch) {
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", x, y, z, yaw, pitch));
	}

	/** Puts the player (spectator) at a position, his eyes turned towards a point. */
	private static void look(TestServerContext server, double x, double y, double z, double tx, double ty, double tz) {
		double dx = tx - x, dy = ty - (y + 1.62), dz = tz - z;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		tp(server, x, y, z, yaw, pitch);
	}

	/** Waits for a state, up to maxTicks; returns the ticks waited, or -1. */
	private static int waitState(ClientGameTestContext context, TestServerContext server, BridgeCycle.State want, int maxTicks) {
		for (int t = 0; t < maxTicks; t += 5) {
			if (state(server) == want) {
				return t;
			}
			context.waitTicks(5);
		}
		return state(server) == want ? maxTicks : -1;
	}

	/** The client's copy of the bridge: {state ordinal, leaf boxes, barrier boxes}, or null. */
	private static int[] clientBridge(ClientGameTestContext context) {
		return context.computeOnClient(mc -> {
			for (DrawbridgeClient.ClientBridge b : DrawbridgeClient.bridges(mc.world)) {
				if (b.id.equals(ID)) {
					return new int[] {b.state.ordinal(), b.leavesOut() ? b.leafBoxes().size() : 0, b.leavesOut() ? b.barrierBoxes().size() : 0};
				}
			}
			return null;
		});
	}

	// ------------------------------------------------------------------ the canal and the bridge

	/** {@code /fill} refuses more than 32768 blocks: fills in slices along x. */
	private static void fill(TestServerContext server, int x0, int y0, int z0, int x1, int y1, int z1, String block) {
		int perX = Math.max(1, 30000 / ((y1 - y0 + 1) * (z1 - z0 + 1)));
		for (int x = x0; x <= x1; x += perX) {
			server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d %s", x, y0, z0, Math.min(x1, x + perX - 1), y1, z1, block));
		}
	}

	private static void build(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		tp(server, 2678.5, -28, -40, 0, 35);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		context.waitTicks(40);
		// the canal: stone bed, water 9 deep (surface -49.1), banks level with the deck's top, closed at both ends
		fill(server, X0, -63, -16, X1, -59, 16, "stone");
		fill(server, X0, -58, -9, X1, -50, 9, "water");
		fill(server, X0, -58, -16, X1, -44, -10, "stone");
		fill(server, X0, -58, 10, X1, -44, 16, "stone");
		fill(server, X0 - 1, -63, -16, X0 - 1, -44, 16, "stone");
		fill(server, X1 + 1, -63, -16, X1 + 1, -44, 16, "stone");
		// the four towers at the corners of the deck, and the fixed high walkway between them
		for (int[] tx : new int[][] {{DECK_X0 - 4, DECK_X0 - 1}, {DECK_X1 + 1, DECK_X1 + 4}}) {
			server.runCommand(String.format(Locale.ROOT, "fill %d -43 -14 %d -30 -10 stone_bricks", tx[0], tx[1]));
			server.runCommand(String.format(Locale.ROOT, "fill %d -43 10 %d -30 14 stone_bricks", tx[0], tx[1]));
		}
		server.runCommand(String.format(Locale.ROOT, "fill %d -33 -10 %d -33 10 dark_oak_planks", DECK_X0 + 1, DECK_X1 - 1));
		// the deck: planks 5 blocks over the water, fences along both edges, lanterns under the ends
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -9 %d %d 9 oak_planks", DECK_X0, DECK_Y, DECK_X1, DECK_Y));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -9 %d %d 9 oak_fence", DECK_X0, DECK_Y + 1, DECK_X0, DECK_Y + 1));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -9 %d %d 9 oak_fence", DECK_X1, DECK_Y + 1, DECK_X1, DECK_Y + 1));
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d -8 lantern[hanging=true]", DECK_X0 + 2, DECK_Y - 1));
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d 8 lantern[hanging=true]", DECK_X0 + 2, DECK_Y - 1));
		server.runCommand("kill @e[type=minecraft:item]");
		world.waitForChunksRender();
		context.waitTicks(40);
	}

	private static void cleanup(TestServerContext server) {
		server.runCommand("ship as galley remove");
		server.runCommand("ship as rowboat remove");
		server.runCommand("kill @e[type=minecraft:armor_stand,distance=..400]");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot, boolean restoreAtEnd) {
		build(context, server, world);
		shot.accept("pontlevis_0_construction");

		// ---- definition with the real commands
		server.runCommand("pontlevis creer " + ID);
		// the selections take the planks, the fences above and the lanterns hanging below (the hinge must stay on the planks)
		server.runCommand(String.format(Locale.ROOT, "pontlevis %s vantail A pos1 %d %d -9", ID, DECK_X0, DECK_Y - 1));
		server.runCommand(String.format(Locale.ROOT, "pontlevis %s vantail A pos2 %d %d -1", ID, DECK_X1, DECK_Y + 1));
		server.runCommand(String.format(Locale.ROOT, "pontlevis %s vantail B pos1 %d %d 0", ID, DECK_X0, DECK_Y - 1));
		server.runCommand(String.format(Locale.ROOT, "pontlevis %s vantail B pos2 %d %d 9", ID, DECK_X1, DECK_Y + 1));
		context.waitTicks(5);
		// a stone in the way of leaf A's swing: the check must refuse and name it
		server.runCommand(String.format(Locale.ROOT, "setblock %d -42 -8 stone", DECK_X0 + 2));
		context.waitTicks(5);
		List<String> problems = server.computeOnServer(srv -> {
			Drawbridge b = Drawbridges.get(ID);
			return b == null ? List.of("no bridge") : b.analyse(srv.getOverworld(), false).problems();
		});
		check.accept(problems.size() == 1 && problems.get(0).contains("heurteraient") && problems.get(0).contains("-42 -8"),
				"drawbridge: a block in the swept volume is reported by the check: " + problems);
		server.runCommand(String.format(Locale.ROOT, "setblock %d -42 -8 air", DECK_X0 + 2));
		context.waitTicks(5);
		server.runCommand("pontlevis " + ID + " verifier");
		context.waitTicks(5);
		double[] figures = server.computeOnServer(srv -> {
			Drawbridge b = Drawbridges.get(ID);
			if (b == null || !b.analysed()) {
				return null;
			}
			return new double[] {b.waterY(), b.undersideY(), b.zones().halfWidth(), b.zones().halfSpan(), Math.abs(b.zones().dx()), b.frame(0).hz(), b.frame(1).hz(),
					b.frame(0).hy()};
		});
		check.accept(figures != null, "drawbridge: the check passes once the stone is gone");
		if (figures == null) {
			cleanup(server);
			return;
		}
		log.accept(String.format(Locale.ROOT, "drawbridge: water %.2f, underside %.2f, half width %.2f, half span %.2f, |dx| %.2f, hinges z %.1f / %.1f at y %.1f",
				figures[0], figures[1], figures[2], figures[3], figures[4], figures[5], figures[6], figures[7]));
		check.accept(Math.abs(figures[0] - WATER) < 0.05, "drawbridge: water surface found at %.2f".formatted(figures[0]));
		check.accept(Math.abs(figures[1] - (DECK_Y - 1 + 0.0625)) < 0.01, "drawbridge: underside measured at the hanging lanterns (%.3f)".formatted(figures[1]));
		check.accept(Math.abs(figures[2] - 9.5) < 0.01 && Math.abs(figures[3] - 2.5) < 0.01 && figures[4] > 0.99,
				"drawbridge: channel 19 wide, deck 5 along the channel, channel along x");
		check.accept(Math.abs(figures[5] + 9) < 0.01 && Math.abs(figures[6] - 10) < 0.01 && Math.abs(figures[7] - DECK_Y) < 0.01,
				"drawbridge: automatic hinges on the outer bottom edges of the planks (z -9 and z 10, y %d), not at the lanterns".formatted(DECK_Y));

		// ---- conversion: the deck stays made of its blocks
		server.runCommand("pontlevis " + ID + " convertir");
		context.waitTicks(10);
		check.accept(state(server) == BridgeCycle.State.FERME, "drawbridge: converted, closed");
		check.accept("oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: the deck's planks are still in the world once converted");
		server.runCommand("pontlevis " + ID + " convertir");
		context.waitTicks(5);
		check.accept(state(server) == BridgeCycle.State.FERME && Drawbridges.all().size() >= 1, "drawbridge: a second conversion is refused, nothing changes");
		server.runCommand("execute as @p run pontlevis " + ID + " apercu on"); // these two need a player (the preview and the debug are his)
		server.runCommand("execute as @p run pontlevis " + ID + " debug on"); // these two need a player (the preview and the debug are his)
		tp(server, 2678.5, -20, -30, 0, 55);
		context.waitTicks(30);
		shot.accept("pontlevis_1_apercu");
		server.runCommand("execute as @p run pontlevis " + ID + " apercu off");
		// the mechanism seen from the deck: the winch beam just under the fixed walkway, its drums, the chains down to the shackles
		server.runCommand("pontlevis " + ID + " chaines 10.78");
		look(server, 2678.5, -43, 1.5, 2678.5, -37.5, -7);
		context.waitTicks(40);
		shot.accept("pontlevis_1b_mecanisme_ferme");

		// ---- the rowboat passes under, empty then with an occupant
		server.runCommand(String.format(Locale.ROOT, "execute positioned 2635 -50 0 rotated -90 0 run ship spawn rowboat"));
		context.waitTicks(20);
		check.accept(shipPos(server, Ships.ROWBOAT) != null, "drawbridge: the rowboat is on the canal");
		server.runCommand("ship as rowboat goto 2705 -50 0");
		boolean lifted = false;
		String reason = null;
		double passedX = 0;
		for (int t = 0; t < 1200; t += 10) {
			context.waitTicks(10);
			if (state(server) != BridgeCycle.State.FERME) {
				lifted = true;
			}
			String r = trackedReason(server, "barque");
			if (r != null) {
				reason = r;
			}
			double[] p = shipPos(server, Ships.ROWBOAT);
			if (p == null) {
				break;
			}
			passedX = p[0];
			if (p[0] > 2695) {
				break;
			}
		}
		check.accept(!lifted, "drawbridge: the empty rowboat never lifts the bridge");
		check.accept(passedX > 2695, "drawbridge: the rowboat sailed under the closed deck (x %.1f)".formatted(passedX));
		check.accept(reason != null && reason.contains("passe sous"), "drawbridge: its verdict was 'passes under': " + reason);
		server.runCommand("ship as rowboat remove");
		context.waitTicks(10);
		// loaded: an armour stand sits in it, 25 blocks from the deck; still under the free height with the default margin
		server.runCommand("execute positioned 2650 -50 0 rotated -90 0 run ship spawn rowboat");
		context.waitTicks(10);
		server.runCommand("summon minecraft:armor_stand 2650 -48 0 {Tags:[\"pontlevis_passager\"]}");
		context.waitTicks(5);
		server.runCommand("ride @e[tag=pontlevis_passager,limit=1] mount @e[type=medievalships:rowboat,limit=1,sort=nearest]");
		context.waitTicks(60);
		reason = trackedReason(server, "barque");
		check.accept(state(server) == BridgeCycle.State.FERME, "drawbridge: the rowboat with an occupant does not lift the bridge either");
		check.accept(reason != null && reason.contains("occupants") && reason.contains("passe sous"),
				"drawbridge: the occupant's head is counted, still passes: " + reason);
		// a bigger margin: the same loaded rowboat now needs the opening (the decision is the gauge's, not the name's)
		server.runCommand("pontlevis " + ID + " marge 3");
		int waited = waitState(context, server, BridgeCycle.State.ATTENTE_SECURITE, 60);
		check.accept(waited >= 0, "drawbridge: with a 3 block margin the loaded rowboat asks for the opening (safety wait)");
		int opening = waitState(context, server, BridgeCycle.State.OUVERTURE, 120);
		check.accept(opening >= 60 && opening <= 100, "drawbridge: the leaves start rising after the 4 s warning (%d ticks)".formatted(opening));
		check.accept("air".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: the deck's blocks leave the world when the leaves rise");
		int[] cb = clientBridge(context);
		check.accept(cb != null && cb[0] == BridgeCycle.State.OUVERTURE.ordinal() && cb[1] > 0 && cb[2] == 2,
				"drawbridge: the client has the moving leaves (%s boxes) and the two barriers".formatted(cb == null ? "no" : cb[1]));
		tp(server, 2660, -36, -22, -35, 25);
		context.waitTicks(40);
		shot.accept("pontlevis_2_ouverture");
		server.runCommand("pontlevis " + ID + " marge 0.5");
		server.runCommand("ship as rowboat remove");
		server.runCommand("kill @e[tag=pontlevis_passager]");
		int opened = waitState(context, server, BridgeCycle.State.OUVERT, 200);
		check.accept(opened >= 0, "drawbridge: open (%.0f degrees)".formatted(angle(server)));
		shot.accept("pontlevis_3_ouvert");
		int closing = waitState(context, server, BridgeCycle.State.FERMETURE, 200);
		check.accept(closing >= 80 && closing <= 140, "drawbridge: closes 5 s after the last vessel is gone (%d ticks)".formatted(closing));
		int closed = waitState(context, server, BridgeCycle.State.FERME, 220);
		check.accept(closed >= 0, "drawbridge: closed again");
		check.accept("oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)) && "oak_fence".equals(blockAt(server, DECK_X0, DECK_Y + 1, 3))
				&& "lantern".equals(blockAt(server, DECK_X0 + 2, DECK_Y - 1, -8)), "drawbridge: planks, fences and lanterns are back");

		// ---- the galley from the west, then from the east
		galley(context, server, check, log, shot, -1);
		galley(context, server, check, log, shot, 1);

		// ---- a player on the deck holds the opening; a demand during the closing reverses it
		server.runCommand("gamemode survival @a");
		server.runCommand("effect give @a minecraft:resistance infinite 4 true");
		tp(server, 2678.5, DECK_Y + 2, 0, 90, 10);
		context.waitTicks(20);
		double[] pp = player(context);
		check.accept(Math.abs(pp[1] - (DECK_Y + 1)) < 0.1, "drawbridge: the player stands on the closed deck (y %.2f)".formatted(pp[1]));
		server.runCommand("pontlevis " + ID + " demande scenario 120");
		waited = waitState(context, server, BridgeCycle.State.ATTENTE_SECURITE, 40);
		check.accept(waited >= 0, "drawbridge: a scripted request starts the safety wait");
		context.waitTicks(140);
		String diag = server.computeOnServer(srv -> Drawbridges.get(ID).cycle().diagnostic());
		check.accept(state(server) == BridgeCycle.State.ATTENTE_SECURITE && diag.contains("tablier"),
				"drawbridge: with the player on the deck the leaves do not move; diagnostic: " + diag);
		tp(server, 2678.5, DECK_Y + 2, -12, 0, 10);
		opening = waitState(context, server, BridgeCycle.State.OUVERTURE, 60);
		check.accept(opening >= 0, "drawbridge: the leaves rise once the player has left the deck");
		// the barrier: walking from the bank towards the missing deck stops at its end
		context.waitTicks(20);
		context.getInput().holdKeyFor(o -> o.forwardKey, 50);
		context.waitTicks(10);
		pp = player(context);
		check.accept(pp[2] < -9.3 && pp[1] > DECK_Y + 0.5, "drawbridge: the barrier stops the player at the end of the bank (z %.2f, y %.2f)".formatted(pp[2], pp[1]));
		shot.accept("pontlevis_4_barriere");
		opened = waitState(context, server, BridgeCycle.State.OUVERT, 200);
		check.accept(opened >= 0, "drawbridge: open for the request");
		// the passage is really free: the former deck is water and air
		server.runCommand("effect give @a minecraft:water_breathing infinite 0 true");
		tp(server, 2678.5, DECK_Y + 1, 0, 0, 0);
		context.waitTicks(30);
		pp = player(context);
		check.accept(pp[1] < DECK_Y - 1.5, "drawbridge: nothing holds a player where the deck was while open (fell to y %.2f)".formatted(pp[1]));
		server.runCommand("gamemode spectator @a");
		tp(server, 2660, -36, -22, -35, 25);
		server.runCommand("pontlevis " + ID + " demande annuler scenario");
		closing = waitState(context, server, BridgeCycle.State.FERMETURE, 200);
		check.accept(closing >= 0, "drawbridge: closes once the request is withdrawn");
		context.waitTicks(40);
		double mid = angle(server);
		server.runCommand("pontlevis " + ID + " demande encore 30");
		context.waitTicks(10);
		check.accept(state(server) == BridgeCycle.State.OUVERTURE && angle(server) >= mid - 0.01,
				"drawbridge: a new demand during the closing reverses it without a jump (%.1f -> %.1f degrees)".formatted(mid, angle(server)));
		server.runCommand("pontlevis " + ID + " demande annuler encore");
		opened = waitState(context, server, BridgeCycle.State.OUVERT, 200);
		closed = waitState(context, server, BridgeCycle.State.FERME, 420);
		check.accept(opened >= 0 && closed >= 0, "drawbridge: back to closed after the reversal");
		check.accept("oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: the deck is back");
		server.runCommand("execute as @p run pontlevis " + ID + " debug off");

		if (restoreAtEnd) {
			restoreAndDelete(context, server, check);
		}
		cleanup(server);
	}

	/** A galley on its autopilot through the bridge, from one side ({@code side} -1: from the west, +1: from the east). */
	private static void galley(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check, Consumer<String> log,
			Consumer<String> shot, int side) {
		String from = side < 0 ? "west" : "east";
		double startX = side < 0 ? 2600 : 2757;
		double endX = side < 0 ? 2757 : 2600;
		float yaw = side < 0 ? -90f : 90f;
		server.runCommand(String.format(Locale.ROOT, "execute positioned %.0f -50 0 rotated %.0f 0 run ship spawn galley", startX, yaw));
		context.waitTicks(20);
		double[] p0 = shipPos(server, Ships.GALLEY);
		check.accept(p0 != null, "drawbridge: the galley is on the canal (" + from + ")");
		if (p0 == null) {
			return;
		}
		check.accept(state(server) == BridgeCycle.State.FERME, "drawbridge: closed before the galley comes (" + from + ")");
		server.runCommand(String.format(Locale.ROOT, "ship as galley goto %.0f -50 0", endX));
		double triggerDist = Double.NaN, minDistBeforeOpen = Double.MAX_VALUE, maxSpeedNear = 0;
		boolean openWhilePassing = true, passed = false, reopened = false;
		BridgeCycle.State prev = BridgeCycle.State.FERME;
		int passTicks = 0;
		for (int t = 0; t < 2400; t += 5) {
			context.waitTicks(5);
			double[] p = shipPos(server, Ships.GALLEY);
			BridgeCycle.State st = state(server);
			if (p == null || st == null) {
				break;
			}
			// the bow's distance to the near deck edge (the galley points at the bridge)
			double bow = p[0] - side * 10.9;
			double dist = side < 0 ? DECK_WEST - bow : bow - DECK_EAST;
			if (Double.isNaN(triggerDist) && st != BridgeCycle.State.FERME) {
				triggerDist = dist;
			}
			if (st != BridgeCycle.State.OUVERT && dist > -30) {
				minDistBeforeOpen = Math.min(minDistBeforeOpen, dist);
				if (dist < 4) {
					maxSpeedNear = Math.max(maxSpeedNear, Math.abs(p[2]));
				}
			}
			boolean inPassage = Math.abs(p[0] - 2678.5) < 2.5 + 10.9;
			if (inPassage) {
				passTicks++;
				if (st != BridgeCycle.State.OUVERT) {
					openWhilePassing = false;
				}
				if (passTicks == 20) {
					shot.accept("pontlevis_5_passage_" + from);
				}
			}
			if (prev == BridgeCycle.State.FERMETURE && st == BridgeCycle.State.OUVERTURE) {
				reopened = true;
			}
			prev = st;
			double tail = p[0] + side * 10.9;
			if ((side < 0 && tail > 2740) || (side > 0 && tail < 2617)) {
				passed = true;
				break;
			}
		}
		log.accept(String.format(Locale.ROOT, "drawbridge %s: trigger at %.1f from the deck, nearest %.1f before open, speed near the deck %.2f, %d ticks in the passage",
				from, triggerDist, minDistBeforeOpen, maxSpeedNear, passTicks));
		check.accept(!Double.isNaN(triggerDist) && triggerDist <= 52 && triggerDist >= 44,
				"drawbridge: the galley from the " + from + " triggers the opening when its bow is 50 blocks from the deck (%.1f)".formatted(triggerDist));
		check.accept(minDistBeforeOpen >= 2.5, "drawbridge: the autopilot waited before the deck until open (nearest %.1f blocks)".formatted(minDistBeforeOpen));
		check.accept(passed, "drawbridge: the galley from the " + from + " went through");
		check.accept(passTicks > 0 && openWhilePassing, "drawbridge: open the whole time the galley was in the passage (" + from + ")");
		check.accept(!reopened, "drawbridge: no closing started while the galley was still counted (" + from + ")");
		int closing = waitState(context, server, BridgeCycle.State.FERMETURE, 400);
		check.accept(closing >= 0, "drawbridge: closes once the galley has left the keep zone (" + from + ")");
		int closed = waitState(context, server, BridgeCycle.State.FERME, 220);
		check.accept(closed >= 0 && "oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: closed, deck back (" + from + ")");
		server.runCommand("ship as galley remove");
		context.waitTicks(10);
	}

	/** Restoration touches only the deck; deletion forgets the bridge. */
	static void restoreAndDelete(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check) {
		String tower = blockAt(server, DECK_X0 - 2, -40, -12), walkway = blockAt(server, DECK_X0 + 2, -33, 0);
		server.runCommand("pontlevis " + ID + " restaurer");
		context.waitTicks(10);
		boolean converted = server.computeOnServer(srv -> Drawbridges.get(ID) != null && Drawbridges.get(ID).converted());
		check.accept(!converted, "drawbridge: restored, no longer converted");
		check.accept("oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)) && "oak_fence".equals(blockAt(server, DECK_X1, DECK_Y + 1, -5)),
				"drawbridge: the original deck is in place after the restoration");
		check.accept("stone_bricks".equals(tower) && "stone_bricks".equals(blockAt(server, DECK_X0 - 2, -40, -12)) && "dark_oak_planks".equals(walkway)
				&& "dark_oak_planks".equals(blockAt(server, DECK_X0 + 2, -33, 0)), "drawbridge: towers and high walkway untouched");
		server.runCommand("pontlevis " + ID + " supprimer");
		context.waitTicks(10);
		check.accept(server.computeOnServer(srv -> Drawbridges.get(ID) == null), "drawbridge: deleted");
	}

	/** Solo: leaves the bridge open (a long request) so the restart finds it so. */
	public static void beforeRestart(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check) {
		if (server.computeOnServer(srv -> Drawbridges.get(ID) == null)) {
			return;
		}
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		server.runCommand("pontlevis " + ID + " demande redemarrage 3600");
		int opened = waitState(context, server, BridgeCycle.State.OUVERT, 400);
		check.accept(opened >= 0 && "air".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: open before the restart, deck blocks out");
	}

	/**
	 * Solo, right after the world reopens: the scripted requests are not saved, so the one of the scenario is renewed at
	 * once; otherwise the bridge would start closing (5 s of hold) while the Nautilus checks run before it is looked at.
	 */
	public static void renewAfterRestart(TestServerContext server) {
		if (server.computeOnServer(srv -> Drawbridges.get(ID) == null)) {
			return;
		}
		server.runCommand("pontlevis " + ID + " demande redemarrage 3600");
	}

	/** Solo, the world reopened: the bridge is still open with its leaves, closes when asked, then is restored. */
	public static void afterRestart(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> shot) {
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X0, Z0, X1, Z1));
		// the scripted requests are not saved: renew the one of the scenario so that the bridge does not close by itself
		// before it is looked at (it would, after its 5 s of hold and its closing delay)
		server.runCommand("pontlevis " + ID + " demande redemarrage 3600");
		tp(server, 2660, -36, -22, -35, 25);
		context.waitTicks(100);
		world.waitForChunksRender();
		context.waitTicks(40);
		boolean exists = server.computeOnServer(srv -> Drawbridges.get(ID) != null && Drawbridges.get(ID).converted());
		check.accept(exists, "drawbridge: found again after the restart, converted");
		if (!exists) {
			return;
		}
		check.accept(state(server) == BridgeCycle.State.OUVERT && Math.abs(angle(server) - 80) < 0.01, "drawbridge: still open at 80 degrees after the restart");
		check.accept("air".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: its deck blocks are still out after the restart");
		int[] cb = clientBridge(context);
		check.accept(cb != null && cb[0] == BridgeCycle.State.OUVERT.ordinal() && cb[1] > 0, "drawbridge: the client got the open bridge on joining");
		shot.accept("pontlevis_6_apres_redemarrage");
		// the raised leaf, its axle and its chains wound up to the drums, from the water
		look(server, 2672.5, -41.1, -3.5, 2678.5, -38, -8.5);
		context.waitTicks(40);
		shot.accept("pontlevis_6b_mecanisme_ouvert");
		server.runCommand("pontlevis " + ID + " demande annuler redemarrage");
		int closed = waitState(context, server, BridgeCycle.State.FERME, 500);
		check.accept(closed >= 0 && "oak_planks".equals(blockAt(server, DECK_X0 + 2, DECK_Y, 0)), "drawbridge: closes after the restart, deck back");
		restoreAndDelete(context, server, check);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X0, Z0, X1, Z1));
	}
}
