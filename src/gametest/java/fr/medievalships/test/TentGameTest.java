package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;

/**
 * In-game checks of the tents (about 15 s of game time): {@code /tent place tent_adventurer} on a stone platform,
 * the anchor block and its facing, a survival player walking into a front leg is stopped by its collision box (the
 * static boxes of TentCollisions through the entity collision mixin), screenshots, {@code /tent remove}, the block
 * and the boxes are gone. Called once from {@link ShipClientGameTest}.
 */
public final class TentGameTest {
	private static final TentType TYPE = TentTypes.ADVENTURER;
	private static final int X = 900;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;

	private TentGameTest() {
	}

	private static BlockPos anchor() {
		return new BlockPos(X, GROUND + 1, 0);
	}

	private static Object[] blockAt(TestServerContext server, BlockPos pos) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var state = w.getBlockState(pos);
			boolean tent = state.getBlock() instanceof TentBlock b && b.tentType() == TYPE;
			return new Object[] {tent, tent ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
					w.getBlockEntity(pos) != null};
		});
	}

	private static double[] player(TestServerContext server) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			return new double[] {pl.getX(), pl.getY(), pl.getZ()};
		});
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = TYPE.id();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		context.waitTicks(20);
		// a flat stone platform of its own, the air cleared above it
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -12 %d %d 12 stone", X - 12, X + 12, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -12 %d %d 12 air", X - 12, GROUND + 1, X + 12, GROUND + 12));
		context.waitTicks(10);
		BlockPos a = anchor();
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", id, a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(30);
		Object[] b0 = blockAt(server, a);
		check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed by /tent place: anchor block at %s (%s)", id, a.toShortString(), b0[1]));
		check.accept("south".equals(b0[1]), id + " faces south as asked (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[3]), id + " has its block entity");
		check.accept((Integer) b0[2] >= 1, id + " registered its collision boxes (" + b0[2] + " tent(s) in the registry)");
		if (!Boolean.TRUE.equals(b0[0])) {
			return;
		}
		// the same tent placed again on top of it is refused (the area is not free)
		server.runCommand(String.format(Locale.ROOT, "tent place %s %d %d %d south", id, a.getX() + 1, a.getY(), a.getZ() + 1));
		context.waitTicks(5);
		Object[] b1 = blockAt(server, a.add(1, 0, 1));
		check.accept(!Boolean.TRUE.equals(b1[0]) && (Integer) b1[2] == (Integer) b0[2], id + " a second tent over the first is refused");

		// screenshots: the reference's view (front-left, above), the front, the inside
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f %.1f %.1f", X - 7.5, GROUND + 5.5, 9.5, 38.0, 22.0));
		context.waitTicks(25);
		shot.accept(id + "_1_reference");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f %.1f %.1f", X + 0.5, GROUND + 3.0, 11.0, 180.0, 8.0));
		context.waitTicks(12);
		shot.accept(id + "_2_face");
		server.runCommand(String.format(Locale.ROOT, "tp @p %.2f %.2f %.2f %.1f %.1f", X + 0.3, GROUND + 2.6, 3.2, 180.0, 18.0));
		context.waitTicks(12);
		shot.accept(id + "_3_interieur");

		// a survival player walks north into the right front leg (tent-local (1.3, 0, 2.45) -> world x+1.3, z+2.45): stopped by it
		TentType.Box leg = null;
		for (TentType.Box c : TYPE.colliders(TentType.SOUTH)) {
			if (c.z0() > 1.5 && c.y0() < 0.2 && c.x0() > 0.5) {
				leg = c;
				break;
			}
		}
		check.accept(leg != null, id + " has a front leg collision box");
		if (leg != null) {
			double lx = a.getX() + 0.5 + (leg.x0() + leg.x1()) / 2, lz = a.getZ() + 0.5 + leg.z1();
			server.runCommand("gamemode survival @a");
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 10", lx, a.getY(), lz + 1.2));
			context.waitTicks(10);
			double[] p0 = player(server);
			context.getInput().holdKeyFor(o -> o.forwardKey, 25);
			context.waitTicks(5);
			double[] p1 = player(server);
			log.accept(String.format(Locale.ROOT, "%s walk into the leg: z %.2f -> %.2f (leg face at %.2f)", id, p0[2], p1[2], lz));
			check.accept(p1[2] > lz + 0.25 && p0[2] - p1[2] > 0.3, String.format(Locale.ROOT,
					"%s the front leg stops the player (moved %.2f, stopped %.2f in front of it)", id, p0[2] - p1[2], p1[2] - lz));
			// and the player can walk freely through the entrance (no collision on the canvas)
			server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %d %.3f 180 10", a.getX() + 0.5, a.getY(), a.getZ() + 0.5 + 3.0));
			context.waitTicks(8);
			double[] q0 = player(server);
			context.getInput().holdKeyFor(o -> o.forwardKey, 20);
			context.waitTicks(5);
			double[] q1 = player(server);
			check.accept(q0[2] - q1[2] > 1.5, String.format(Locale.ROOT, "%s the entrance is open (walked %.2f blocks in)", id, q0[2] - q1[2]));
			server.runCommand("gamemode spectator @a");
		}

		// /tent remove: the block and its boxes are gone
		server.runCommand(String.format(Locale.ROOT, "execute positioned %d %d 0 run tent remove nearest", X, GROUND + 1));
		context.waitTicks(10);
		Object[] b2 = blockAt(server, a);
		check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[3]), id + " removed by /tent remove (block " + b2[1] + ")");
		check.accept((Integer) b2[2] == (Integer) b0[2] - 1, id + " its collision boxes are forgotten (" + b2[2] + " tent(s) left)");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
	}
}
