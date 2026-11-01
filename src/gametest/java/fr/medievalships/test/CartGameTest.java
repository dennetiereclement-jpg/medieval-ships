package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;

/**
 * In-game checks of the eight carts (short): on a flat stone platform of their own, each cart once: placed by
 * {@code /cart place <id> x y z <facing>} (the alias of {@code /tent}; one of them through {@code /tent place}),
 * its anchor block, facing and block entity, its first collision box answers a collision query (the mixin's path),
 * one screenshot, removed by {@code /cart remove x y z}, its boxes forgotten. Called once from {@link ShipClientGameTest}.
 */
public final class CartGameTest {
	private static final int X = 1000;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;
	private static final String[] FACINGS = {"south", "west", "north", "east"};

	private CartGameTest() {
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 10));
		context.waitTicks(20);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -10 %d %d 10 stone", X - 10, X + 10, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -10 %d %d 10 air", X - 10, GROUND + 1, X + 10, GROUND + 8));
		context.waitTicks(10);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		BlockPos a = new BlockPos(X, GROUND + 1, 0);
		int i = 0;
		for (TentType type : TentTypes.CARTS) {
			String id = type.id();
			int q = i % 4;
			String facing = FACINGS[q];
			String cmd = i == 0 ? "tent" : "cart";
			i++;
			int before = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
			server.runCommand(String.format(Locale.ROOT, "%s place %s %d %d %d %s", cmd, id, a.getX(), a.getY(), a.getZ(), facing));
			world.waitForChunksRender();
			context.waitTicks(15);
			Object[] b0 = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				var state = w.getBlockState(a);
				boolean ok = state.getBlock() instanceof TentBlock b && b.tentType() == type;
				return new Object[] {ok, ok ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
						w.getBlockEntity(a) != null};
			});
			check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed by /%s place: anchor block at %s (%s)", id, cmd,
					a.toShortString(), b0[1]));
			check.accept(facing.equals(b0[1]), id + " faces " + facing + " (" + b0[1] + ")");
			check.accept(Boolean.TRUE.equals(b0[3]), id + " has its block entity");
			check.accept((Integer) b0[2] == before + 1, id + " registered its collision boxes (" + b0[2] + " prop(s) in the registry)");
			int hits = server.computeOnServer(srv -> {
				var boxes = TentCollisions.worldBoxes(type, a, q);
				if (boxes.isEmpty()) {
					return -1;
				}
				java.util.List<net.minecraft.util.shape.VoxelShape> out = new java.util.ArrayList<>();
				TentCollisions.append(out, null, boxes.get(0).expand(0.05), srv.getOverworld());
				return out.size();
			});
			check.accept(hits >= 1, id + " a collision query on its first box finds it (" + hits + " shape(s))");
			TentType.Box e = type.extent(q);
			double cx = a.getX() + 0.5 + (e.x0() + e.x1()) / 2, cz = a.getZ() + 0.5 + (e.z0() + e.z1()) / 2;
			double r = Math.max(e.width(), e.depth()) * 0.95 + 1.5;
			look(server, cx - r * 0.65, GROUND + 1 + e.height() + 1.2, cz + r * 0.75, cx, GROUND + 1 + e.height() * 0.4, cz);
			context.waitTicks(20);
			shot.accept(id + "_1_reference");
			server.runCommand(String.format(Locale.ROOT, "cart remove %d %d %d", a.getX(), a.getY(), a.getZ()));
			context.waitTicks(8);
			Object[] b2 = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				return new Object[] {w.getBlockState(a).getBlock() instanceof TentBlock, TentCollisions.count(w), w.getBlockEntity(a) != null};
			});
			check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[2]), id + " removed by /cart remove x y z");
			check.accept((Integer) b2[1] == before, id + " its collision boxes are forgotten (" + b2[1] + " left)");
			log.accept(String.format(Locale.ROOT, "%s extent %.1f x %.1f x %.1f, %d collision boxes", id, e.width(), e.depth(), e.height(),
					type.colliders().size()));
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
	}
}
