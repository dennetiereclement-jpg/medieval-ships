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
import fr.medievalships.tent.Tents;
import fr.medievalships.tent.WorkshopBlock;

/**
 * In-game checks of the seven crafting workshops (placeable props only: the crafting is not wired yet). On a flat
 * stone platform of their own on dry land (x 1600, east of every basin; chunks force-loaded), each workshop once:
 * placed by {@code /workshop place <id> x y z <facing>} (one through the alias {@code /atelier}), its anchor block (a
 * {@link WorkshopBlock}), facing and block entity, its collision boxes registered on the server and known to the
 * client, its first box answers a collision query (the mixin's path), one screenshot, removed by
 * {@code /workshop remove x y z} (one through {@code /atelier remove}), its boxes forgotten. Also {@code /workshop give}
 * and {@code /ship give} with a workshop id, and {@code /workshop remove} leaving a tent alone. Called once from
 * {@link ShipClientGameTest}.
 */
public final class WorkshopGameTest {
	/** Dry ground of the flat world, east of every basin and of the tents' (1300) and carts' (1000) platforms. */
	private static final int X = 1600;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;
	private static final String[] FACINGS = {"south", "west", "north", "east"};

	private WorkshopGameTest() {
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", ex, ey - 1.62, ez, yaw, pitch));
	}

	private static int itemCount(TestServerContext server, TentType type) {
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = srv.getPlayerManager().getPlayerList().get(0);
			return pl.getInventory().count(Tents.item(type));
		});
	}

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d 0 0 40", X, GROUND + 12));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, -16, X + 16, 16));
		context.waitTicks(30);
		// a flat stone platform of its own on dry land, the air cleared above it
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 -14 %d %d 14 stone", X - 14, X + 14, GROUND));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d -14 %d %d 14 air", X - 14, GROUND + 1, X + 14, GROUND + 12));
		context.waitTicks(10);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);

		// the items: /workshop give and /ship give accept the workshop ids
		int g0 = itemCount(server, TentTypes.WORKSHOP_COOK);
		server.runCommand("workshop give workshop_cook @p");
		server.runCommand("ship give workshop_cook @p");
		context.waitTicks(2);
		int g1 = itemCount(server, TentTypes.WORKSHOP_COOK);
		check.accept(g1 == g0 + 2, "workshop_cook item given by /workshop give and /ship give (" + g0 + " -> " + g1 + ")");

		BlockPos a = new BlockPos(X, GROUND + 1, 0);
		int i = 0;
		for (TentType type : TentTypes.WORKSHOPS) {
			String id = type.id();
			int q = i % 4;
			String facing = FACINGS[q];
			String cmd = i == 0 ? "atelier" : "workshop";
			String removeCmd = i == 1 ? "atelier" : "workshop";
			i++;
			int before = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
			server.runCommand(String.format(Locale.ROOT, "%s place %s %d %d %d %s", cmd, id, a.getX(), a.getY(), a.getZ(), facing));
			world.waitForChunksRender();
			context.waitTicks(15);
			Object[] b0 = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				var state = w.getBlockState(a);
				boolean ok = state.getBlock() instanceof WorkshopBlock b && b.tentType() == type;
				return new Object[] {ok, ok ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
						w.getBlockEntity(a) != null};
			});
			check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed by /%s place: workshop anchor block at %s (%s)", id, cmd,
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
			boolean client = context.computeOnClient((MinecraftClient c) -> {
				TentCollisions.Placed p = c.world == null ? null : TentCollisions.at(c.world, a);
				return p != null && p.type() == type && p.quarter() == q;
			});
			check.accept(client, id + " known to the client (block entity loaded: drawn, collisions predicted)");
			TentType.Box e = type.extent(q);
			double cx = a.getX() + 0.5 + (e.x0() + e.x1()) / 2, cz = a.getZ() + 0.5 + (e.z0() + e.z1()) / 2;
			double r = Math.max(e.width(), e.depth()) * 0.95 + 1.5;
			look(server, cx - r * 0.65, GROUND + 1 + e.height() + 1.2, cz + r * 0.75, cx, GROUND + 1 + e.height() * 0.4, cz);
			context.waitTicks(20);
			shot.accept(id + "_1_reference");
			server.runCommand(String.format(Locale.ROOT, "%s remove %d %d %d", removeCmd, a.getX(), a.getY(), a.getZ()));
			context.waitTicks(8);
			Object[] b2 = server.computeOnServer(srv -> {
				ServerWorld w = srv.getOverworld();
				return new Object[] {w.getBlockState(a).getBlock() instanceof TentBlock, TentCollisions.count(w), w.getBlockEntity(a) != null};
			});
			check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[2]), id + " removed by /" + removeCmd + " remove x y z");
			check.accept((Integer) b2[1] == before, id + " its collision boxes are forgotten (" + b2[1] + " left)");
			log.accept(String.format(Locale.ROOT, "%s extent %.1f x %.1f x %.1f, %d collision boxes, %d particle source(s)", id, e.width(),
					e.depth(), e.height(), type.colliders().size(), type.particles().size()));
		}

		// /workshop remove only sees workshops: a tent at the spot stays
		server.runCommand(String.format(Locale.ROOT, "tent place tent_camp %d %d %d south", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(5);
		server.runCommand(String.format(Locale.ROOT, "workshop remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		server.runCommand("workshop remove nearest");
		context.waitTicks(5);
		boolean tentStays = server.computeOnServer(srv -> srv.getOverworld().getBlockState(a).getBlock() instanceof TentBlock b
				&& b.tentType() == TentTypes.CAMP);
		check.accept(tentStays, "/workshop remove leaves a tent alone");
		server.runCommand(String.format(Locale.ROOT, "tent remove %d %d %d", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(5);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, -16, X + 16, 16));
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
	}
}
