package fr.medievalships.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.LightType;

import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;

/**
 * In-game checks of the eight street decorations (1.20.0). On a flat stone platform of their own on dry land (x 1300,
 * z 40, beside the tents' platform; chunks force-loaded), each decoration once: placed facing south by command (the
 * first through {@code /deco place}, the others through {@code /tent place}), its anchor block (a {@link TentBlock} of
 * that type), facing and block entity, its collision boxes registered, its first box (a post) answers a collision query
 * (the mixin's path) while a player-sized box between its two posts finds nothing (cloth, ropes and nets do not
 * collide), the light of its anchor block (the vanilla light engine: 15 at the hanging lantern's foot, 12 at the
 * bunting's, still lit two blocks above it), one screenshot from the reference's angle, removed by
 * {@code /deco remove x y z} (or {@code /tent remove}), its boxes forgotten and its light gone. Called once from
 * {@link ShipClientGameTest}.
 */
public final class DecorationGameTest {
	/** Dry ground of the flat world, beside the tents' platform (x 1300, z -14..14). */
	private static final int X = 1300, Z = 40;
	/** Top of the stone platform; the anchor block sits on it. */
	private static final int GROUND = -60;

	private DecorationGameTest() {
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
		server.runCommand(String.format(Locale.ROOT, "tp @p %d %d %d 0 40", X, GROUND + 12, Z));
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, Z - 16, X + 16, Z + 16));
		context.waitTicks(30);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", X - 12, Z - 10, X + 12, GROUND, Z + 10));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", X - 12, GROUND + 1, Z - 10, X + 12, GROUND + 9, Z + 10));
		context.waitTicks(10);
		check.accept(TentTypes.DECORATIONS.size() == 9, "the eight street decorations and the defensive stake are placed once each below (" + TentTypes.DECORATIONS.size()
				+ ")");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		BlockPos a = new BlockPos(X, GROUND + 1, Z);
		boolean first = true;
		for (TentType t : TentTypes.DECORATIONS) {
			TentType.Box e = t.extent(TentType.SOUTH);
			check.accept(e.x0() > -12 && e.x1() < 12 && e.z0() > -10 && e.z1() < 10 && e.y1() < 9,
					String.format(Locale.ROOT, "%s fits the cleared platform (extent x %.1f..%.1f z %.1f..%.1f h %.1f)", t.id(), e.x0(), e.x1(),
							e.z0(), e.z1(), e.y1()));
			one(t, a, first, context, server, world, check, log, shot);
			first = false;
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, Z - 16, X + 16, Z + 16));
	}

	private static void one(TentType type, BlockPos a, boolean viaDeco, ClientGameTestContext context, TestServerContext server,
			TestClientWorldContext world, BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		String id = type.id();
		int before = server.computeOnServer(srv -> TentCollisions.count(srv.getOverworld()));
		server.runCommand(String.format(Locale.ROOT, "%s place %s %d %d %d south", viaDeco ? "deco" : "tent", id, a.getX(), a.getY(), a.getZ()));
		world.waitForChunksRender();
		context.waitTicks(25);
		Object[] b0 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			var state = w.getBlockState(a);
			boolean ok = state.getBlock() instanceof TentBlock b && b.tentType() == type;
			return new Object[] {ok, ok ? state.get(TentBlock.FACING).asString() : state.getBlock().toString(), TentCollisions.count(w),
					w.getBlockEntity(a) != null, state.getLuminance(), w.getLightLevel(LightType.BLOCK, a), w.getLightLevel(LightType.BLOCK, a.up(2))};
		});
		check.accept(Boolean.TRUE.equals(b0[0]), String.format(Locale.ROOT, "%s placed by /%s place: anchor block at %s (%s)", id,
				viaDeco ? "deco" : "tent", a.toShortString(), b0[1]));
		check.accept("south".equals(b0[1]), id + " faces south (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[3]), id + " has its block entity");
		check.accept((Integer) b0[2] == before + 1, id + " registered its collision boxes (" + b0[2] + " prop(s) in the registry)");
		// the light: the anchor block's luminance, spread by the vanilla light engine
		int lum = (Integer) b0[4], here = (Integer) b0[5], above = (Integer) b0[6];
		log.accept(String.format(Locale.ROOT, "%s light: luminance %d, block light %d at the anchor, %d two blocks above", id, lum, here, above));
		check.accept(lum == type.light(), String.format(Locale.ROOT, "%s its anchor block's luminance is the JSON's light %d (%d)", id, type.light(), lum));
		if (type.light() > 0) {
			check.accept(here == type.light(), String.format(Locale.ROOT, "%s the area is lit: block light %d at its foot (expected %d)", id, here,
					type.light()));
			check.accept(above == type.light() - 2, String.format(Locale.ROOT, "%s still lit two blocks above its foot (%d, expected %d)", id, above,
					type.light() - 2));
		}
		// the posts collide; the passage between two posts does not (cloth, ropes, nets, lanterns)
		int[] hits = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			List<Box> boxes = TentCollisions.worldBoxes(type, a, TentType.SOUTH);
			if (boxes.isEmpty()) {
				return new int[] {-1, -1};
			}
			List<VoxelShape> out = new ArrayList<>();
			TentCollisions.append(out, null, boxes.get(0).expand(0.05), w);
			int post = out.size();
			int between = -1;
			List<TentType.Box> tall = new ArrayList<>();
			for (TentType.Box b : type.colliders(TentType.SOUTH)) {
				if (b.y1() > 2.0 && b.y0() < 1.0) { // posts stand on the ground or a footing (not the hanging lantern)
					tall.add(b);
				}
			}
			if (tall.size() >= 2) {
				TentType.Box p = tall.get(0), q = tall.get(1);
				double best = -1;
				for (TentType.Box u : tall) {
					for (TentType.Box v : tall) {
						double d = Math.hypot((u.x0() + u.x1() - v.x0() - v.x1()) / 2, (u.z0() + u.z1() - v.z0() - v.z1()) / 2);
						if (d > best) {
							best = d;
							p = u;
							q = v;
						}
					}
				}
				double mx = a.getX() + 0.5 + (p.x0() + p.x1() + q.x0() + q.x1()) / 4, mz = a.getZ() + 0.5 + (p.z0() + p.z1() + q.z0() + q.z1()) / 4;
				List<VoxelShape> mid = new ArrayList<>();
				TentCollisions.append(mid, null, new Box(mx - 0.3, a.getY() + 0.05, mz - 1.0, mx + 0.3, a.getY() + 1.8, mz + 1.0), w);
				between = mid.size();
			}
			return new int[] {post, between};
		});
		check.accept(hits[0] >= 1, id + " a collision query on its first box (a post) finds it (" + hits[0] + " shape(s))");
		if (hits[1] >= 0) {
			check.accept(hits[1] == 0, id + " the way between its posts is free (" + hits[1] + " shape(s))");
		}
		// one screenshot from the reference's angle: in front, a little to the left, at about head height
		TentType.Box e = type.extent(TentType.SOUTH);
		double cx = a.getX() + 0.5, cz = a.getZ() + 0.5;
		double r = Math.max(e.width(), e.height()) * 1.05 + 2.0;
		look(server, cx - r * 0.25, a.getY() + e.height() * 0.6 + 0.4, cz + r, cx, a.getY() + e.height() * 0.5, cz);
		context.waitTicks(25);
		shot.accept(id + "_1_reference");
		server.runCommand(String.format(Locale.ROOT, "%s remove %d %d %d", viaDeco ? "deco" : "tent", a.getX(), a.getY(), a.getZ()));
		context.waitTicks(15);
		Object[] b2 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			return new Object[] {w.getBlockState(a).getBlock() instanceof TentBlock, TentCollisions.count(w), w.getBlockEntity(a) != null,
					w.getLightLevel(LightType.BLOCK, a)};
		});
		check.accept(!Boolean.TRUE.equals(b2[0]) && !Boolean.TRUE.equals(b2[2]), id + " removed by command");
		check.accept((Integer) b2[1] == before, id + " its collision boxes are forgotten (" + b2[1] + " prop(s) left)");
		check.accept((Integer) b2[3] == 0, id + " no light left once removed (" + b2[3] + ")");
	}
}
