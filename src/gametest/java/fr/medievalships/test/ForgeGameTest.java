package fr.medievalships.test;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiConsumer;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.block.BlockState;
import net.minecraft.client.MinecraftClient;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.entity.ItemEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ItemUsageContext;
import net.minecraft.item.Items;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.shape.VoxelShape;

import fr.medievalships.api.DivineForgeApi;
import fr.medievalships.client.DivineForgeScreen;
import fr.medievalships.client.model.BbModel;
import fr.medievalships.client.render.TentModels;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.forge.DivineForgeBlock;
import fr.medievalships.forge.DivineForgeBlockEntity;
import fr.medievalships.forge.DivineForgeScreenHandler;
import fr.medievalships.forge.ForgeMenu;
import fr.medievalships.forge.ForgeRecipes;
import fr.medievalships.tent.TentBlock;
import fr.medievalships.tent.TentCollisions;
import fr.medievalships.tent.Tents;

/**
 * In-game checks of the divine forge (1.34.0), on a stone platform of the flat world at x {@value #X}: its two models
 * loaded on the client with the bones of the contract; the item refused when something stands in the way, then placing
 * the forge facing the player (block, block entity, light 15, collision boxes known to the server and the client, the
 * extent within 13 x 10 x 6); the collisions (the furnace stops a player who walks in, nothing under the banners, the
 * platform is climbed on foot); screenshots (front, three quarters, close, at night); a right click with a command
 * configured for {@code forge_divine} runs it, without one it opens the forge's interface (the trial recipe listed, its
 * ingredients owned / required); the trial recipe forged through the interface's button (exactly 4 gold ingots and 1
 * diamond removed, "La forge est occupée" for a second crafting, the crafting seen by the client, the named golden sword
 * received after the time); {@code /forge animer}, {@code etat}, {@code arreter} and the API's events; the trial recipe
 * hidden with {@code forgeTestRecipe} false; the removal by {@code /tent remove} and by a creative player's break, with no
 * block, collision, block entity nor item left. The solo run keeps a crafting under way across a world restart
 * ({@link #beforeRestart}, {@link #afterRestart}); the dedicated server runs {@link #run} over the network. Called from
 * {@link ShipClientGameTest}.
 */
public final class ForgeGameTest {
	/** Away from every other scenario (the doors are at 8600 to 8656, the ships' boats at 7400). */
	private static final int X = 9400, Z = 0;
	private static final int GROUND = -60, Y = GROUND + 1;
	private static final BlockPos A = new BlockPos(X, Y, Z);
	/** Where the forge kept across the restart stands. */
	private static final BlockPos RESTART = new BlockPos(X + 40, Y, Z);
	private static final String TRIAL = "medievalships:forge_divine_essai";
	private static final String TRIAL_NAME = "Lame divine (essai)";
	private static final String RELIC = "Relique du redémarrage";
	private static final TentType F = TentTypes.FORGE_DIVINE;
	private static final AtomicInteger STARTED = new AtomicInteger(), FINISHED = new AtomicInteger();
	private static boolean listening;

	private ForgeGameTest() {
	}

	// ------------------------------------------------------------------ helpers

	private static ServerPlayerEntity player(MinecraftServer srv) {
		return srv.getPlayerManager().getPlayerList().get(0);
	}

	private static void tp(TestServerContext server, double x, double y, double z, float yaw, float pitch) {
		server.runCommand(String.format(Locale.ROOT, "tp @p %.3f %.3f %.3f %.1f %.1f", x, y, z, yaw, pitch));
	}

	private static void look(TestServerContext server, double ex, double ey, double ez, double tx, double ty, double tz) {
		double dx = tx - ex, dy = ty - ey, dz = tz - ez;
		float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
		float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.hypot(dx, dz)));
		tp(server, ex, ey - 1.62, ez, yaw, pitch);
	}

	private static String pos(BlockPos p) {
		return p.getX() + " " + p.getY() + " " + p.getZ();
	}

	private static int waitUntil(ClientGameTestContext context, BooleanSupplier cond, int maxTicks) {
		for (int t = 0; t <= maxTicks; t += 2) {
			if (cond.getAsBoolean()) {
				return t;
			}
			context.waitTicks(2);
		}
		return -1;
	}

	private static DivineForgeBlockEntity forge(MinecraftServer srv, BlockPos p) {
		return srv.getOverworld().getBlockEntity(p) instanceof DivineForgeBlockEntity f ? f : null;
	}

	/** Is the forge at {@code p} crafting, on the server? (null: no forge) */
	private static Boolean crafting(TestServerContext server, BlockPos p) {
		return server.computeOnServer(srv -> {
			DivineForgeBlockEntity f = forge(srv, p);
			return f == null ? null : f.crafting();
		});
	}

	/** Is the forge at {@code p} crafting, as this client sees it? (null: no forge known to the client) */
	private static Boolean clientCrafting(ClientGameTestContext context, BlockPos p) {
		return context.computeOnClient((MinecraftClient c) -> c.world != null && c.world.getBlockEntity(p) instanceof DivineForgeBlockEntity f
				? f.crafting() : null);
	}

	private static int count(TestServerContext server, net.minecraft.item.Item item) {
		return server.computeOnServer(srv -> player(srv).getInventory().count(item));
	}

	/** A world box from forge-local coordinates (facing south: local +z is the world's +z). */
	private static Box local(BlockPos a, double x0, double y0, double z0, double x1, double y1, double z1) {
		return new Box(a.getX() + 0.5 + x0, a.getY() + y0, a.getZ() + 0.5 + z0, a.getX() + 0.5 + x1, a.getY() + y1, a.getZ() + 0.5 + z1);
	}

	/** How many collision shapes of the props a box touches (the mixin's path), on the server. */
	private static int shapes(TestServerContext server, Box box) {
		return server.computeOnServer(srv -> {
			List<VoxelShape> out = new java.util.ArrayList<>();
			TentCollisions.append(out, null, box, srv.getOverworld());
			return out.size();
		});
	}

	/** Places a forge with its item as a player looking north from in front of {@code a}: the result's class name. */
	private static String placeWithItem(TestServerContext server, BlockPos a) {
		tp(server, a.getX() + 0.5, a.getY(), a.getZ() + 0.5 + 9, 180, 30);
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = player(srv);
			ItemStack stack = new ItemStack(Tents.item(F));
			pl.setStackInHand(Hand.MAIN_HAND, stack);
			BlockPos ground = a.down();
			BlockHitResult hit = new BlockHitResult(new Vec3d(ground.getX() + 0.5, ground.getY() + 1.0, ground.getZ() + 0.5), Direction.UP, ground, false);
			ActionResult r = stack.useOnBlock(new ItemUsageContext(pl, Hand.MAIN_HAND, hit));
			pl.setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
			return r.getClass().getSimpleName();
		});
	}

	/** A right click on the forge's anchor block by the first player, through the block's use path. */
	private static void click(TestServerContext server, BlockPos a) {
		server.runOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			w.getBlockState(a).onUse(w, player(srv), new BlockHitResult(Vec3d.ofCenter(a), Direction.UP, a, false));
		});
	}

	private static boolean screenOpen(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient c) -> c.currentScreen instanceof DivineForgeScreen);
	}

	/** The client's menu entry of a recipe (index, craftable, owned counts), or null. */
	private static Object[] clientEntry(ClientGameTestContext context, String id) {
		return context.computeOnClient((MinecraftClient c) -> {
			if (c.player == null || !(c.player.currentScreenHandler instanceof DivineForgeScreenHandler h)) {
				return null;
			}
			List<ForgeMenu.Entry> all = h.menu().entries();
			for (int i = 0; i < all.size(); i++) {
				ForgeMenu.Entry e = all.get(i);
				if (e.id().equals(id)) {
					StringBuilder owned = new StringBuilder();
					for (ForgeMenu.Ing g : e.ingredients()) {
						owned.append(g.owned()).append('/').append(g.required()).append(' ');
					}
					return new Object[] {i, e.craftable(), owned.toString().trim(), e.name(), all.size(), h.syncId};
				}
			}
			return new Object[] {-1, false, "", "", all.size(), h.syncId};
		});
	}

	private static void listen() {
		if (listening) {
			return;
		}
		listening = true;
		DivineForgeApi.CRAFT_STARTED.register((world, pos, player, recipe, ticks) -> STARTED.incrementAndGet());
		DivineForgeApi.CRAFT_FINISHED.register((world, pos, player, playerId, recipe, result, animationOnly) -> FINISHED.incrementAndGet());
	}

	// ------------------------------------------------------------------ the scenario

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		listen();
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode creative @a");
		server.runCommand("time set 6000");
		tp(server, X, Y + 8, Z + 14, 180, 30);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 24, Z - 24, X + 56, Z + 24));
		context.waitTicks(30);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", X - 20, Z - 16, X + 20, GROUND, Z + 16));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", X - 20, Y, Z - 16, X + 20, Y + 14, Z + 16));
		server.runCommand("kill @e[type=minecraft:item]");
		context.waitTicks(10);
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);

		// ---- the two models on the client, with the bones of the contract
		String models = context.computeOnClient((MinecraftClient c) -> {
			BbModel main = TentModels.get(F);
			List<TentModels.Extra> extras = TentModels.extras(F);
			StringBuilder sb = new StringBuilder();
			if (main == null) {
				return "structure absente";
			}
			for (String p : new String[] {"fire_f", "flow_l_f", "flow_r_f"}) {
				for (int i = 0; i < 4; i++) {
					if (!main.hasBone(p + i)) {
						sb.append(p).append(i).append(' ');
					}
				}
			}
			boolean gears = false, craft = false, spark = false;
			for (BbModel.Bone b : main.bones) {
				gears |= b.name.startsWith("gear_a_") || b.name.startsWith("gear_b_");
				craft |= b.name.startsWith("craft_");
				spark |= b.name.startsWith("fx_spark_");
			}
			if (!gears) {
				sb.append("gear_* ");
			}
			if (!craft) {
				sb.append("craft_* ");
			}
			if (!spark) {
				sb.append("fx_spark_* ");
			}
			if (extras.size() != 1) {
				return sb + "décor absent (" + extras.size() + ")";
			}
			boolean holy = false;
			for (BbModel.Bone b : extras.get(0).model().bones) {
				holy |= b.name.startsWith("fx_holy_");
			}
			if (!holy) {
				sb.append("fx_holy_* ");
			}
			return sb.length() == 0 ? "" : "manque : " + sb;
		});
		check.accept(models.isEmpty(), "forge: the structure and decor models are loaded with the contract's bones" + (models.isEmpty() ? "" : " (" + models + ")"));
		Object[] counts = context.computeOnClient((MinecraftClient c) -> {
			BbModel main = TentModels.get(F);
			List<TentModels.Extra> ex = TentModels.extras(F);
			return new Object[] {main == null ? 0 : main.bones.size(), main == null ? 0 : main.quadCount(),
					ex.isEmpty() ? 0 : ex.get(0).model().bones.size(), ex.isEmpty() ? 0 : ex.get(0).model().quadCount()};
		});
		log.accept(String.format(Locale.ROOT, "forge models: structure %s bones / %s faces, decor %s bones / %s faces", counts[0], counts[1], counts[2], counts[3]));

		// ---- refused when something stands in its way, then placed facing the player
		BlockPos obstacle = A.add(4, 2, 1);
		server.runCommand("setblock " + pos(obstacle) + " minecraft:cobblestone");
		context.waitTicks(2);
		String refused = placeWithItem(server, A);
		boolean nothing = server.computeOnServer(srv -> !(srv.getOverworld().getBlockState(A).getBlock() instanceof TentBlock));
		check.accept(nothing && !"Success".equals(refused), "forge: refused when a block stands in its extent (" + refused + ", nothing placed)");
		server.runCommand("setblock " + pos(obstacle) + " air");
		context.waitTicks(2);
		String placed = placeWithItem(server, A);
		world.waitForChunksRender();
		context.waitTicks(20);
		Object[] b0 = server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			BlockState s = w.getBlockState(A);
			boolean ok = s.getBlock() instanceof DivineForgeBlock b && b.tentType() == F;
			return new Object[] {ok, ok ? s.get(TentBlock.FACING).asString() : s.getBlock().toString(), w.getBlockEntity(A) instanceof DivineForgeBlockEntity,
					TentCollisions.at(w, A) != null, s.getLuminance()};
		});
		check.accept(Boolean.TRUE.equals(b0[0]), "forge: placed with its item (" + placed + ", block " + b0[1] + ")");
		check.accept("south".equals(b0[1]), "forge: faces the player who placed it (" + b0[1] + ")");
		check.accept(Boolean.TRUE.equals(b0[2]), "forge: has its own block entity (crafting state)");
		check.accept(Boolean.TRUE.equals(b0[3]), "forge: its collision boxes are registered on the server");
		check.accept(Integer.valueOf(15).equals(b0[4]), "forge: its anchor gives light 15 (" + b0[4] + ")");
		TentType.Box e = F.extent(0);
		check.accept(e.width() <= 13.0 + 1e-6 && e.height() <= 10.0 + 1e-6 && e.depth() <= 6.0 + 1e-6 && e.width() >= 8,
				String.format(Locale.ROOT, "forge: extent %.2f x %.2f x %.2f within 13 x 10 x 6", e.width(), e.height(), e.depth()));
		boolean clientKnows = context.computeOnClient((MinecraftClient c) -> c.world != null && TentCollisions.at(c.world, A) != null
				&& c.world.getBlockEntity(A) instanceof DivineForgeBlockEntity);
		check.accept(clientKnows, "forge: known to the client (block entity, collisions predicted)");

		// ---- collisions: the furnace is solid, nothing hangs under the banners, the platform is climbed on foot
		// inside the central body, under the statue's base (above the furnace's mouth)
		int body = shapes(server, local(A, -0.4, 4.6, -1.0, 0.4, 5.4, -0.5));
		check.accept(body >= 1, "forge: the furnace's mass is solid (" + body + " shape(s))");
		int bannerL = shapes(server, local(A, -5.75, 2.2, 0.45, -5.45, 7.8, 0.75)), bannerR = shapes(server, local(A, 5.45, 2.2, 0.45, 5.75, 7.8, 0.75));
		check.accept(bannerL == 0 && bannerR == 0, "forge: nothing solid under the banners (" + bannerL + ", " + bannerR + " shape(s))");
		server.runCommand("gamemode survival @a");
		double startZ = A.getZ() + 0.5 + e.z1() + 1.3;
		tp(server, A.getX() + 0.5 + 1.2, Y, startZ, 180, 10);
		context.waitTicks(10);
		double[] p0 = server.computeOnServer(srv -> new double[] {player(srv).getX(), player(srv).getY(), player(srv).getZ()});
		context.getInput().holdKeyFor(o -> o.forwardKey, 30);
		context.waitTicks(6);
		double[] p1 = server.computeOnServer(srv -> new double[] {player(srv).getX(), player(srv).getY(), player(srv).getZ()});
		double localZ = p1[2] - (A.getZ() + 0.5), climbed = p1[1] - Y;
		log.accept(String.format(Locale.ROOT, "forge walk: z %.2f -> %.2f (local %.2f), y %.2f -> %.2f", p0[2], p1[2], localZ, p0[1], p1[1]));
		check.accept(climbed >= 0.4, String.format(Locale.ROOT, "forge: the platform is climbed on foot (%.2f above the ground)", climbed));
		check.accept(p0[2] - p1[2] > 1.5 && localZ > -1.0, String.format(Locale.ROOT,
				"forge: the player walks onto the platform and is stopped by the forge's mass (moved %.2f, stopped at local z %.2f)", p0[2] - p1[2], localZ));
		// ---- screenshots (spectator: nobody falls): front, three quarters, close
		server.runCommand("gamemode spectator @a");
		look(server, A.getX() + 0.5, Y + 5.5, A.getZ() + 0.5 + 17, A.getX() + 0.5, Y + 4.5, A.getZ() + 0.5);
		context.waitTicks(30);
		shot.accept("forge_1_face");
		look(server, A.getX() + 0.5 - 11, Y + 6.5, A.getZ() + 0.5 + 12, A.getX() + 0.5, Y + 4, A.getZ() + 0.5);
		context.waitTicks(20);
		shot.accept("forge_2_trois_quarts");
		look(server, A.getX() + 0.5 + 1.5, Y + 2.6, A.getZ() + 0.5 + 5.5, A.getX() + 0.5, Y + 1.6, A.getZ() + 0.5);
		context.waitTicks(20);
		shot.accept("forge_3_pres");

		// ---- the right click: a configured command, else the forge's own interface
		Map<String, String> saved = server.computeOnServer(srv -> new LinkedHashMap<>(ConfigManager.server().workshopCommands));
		server.runCommand("gamemode survival @a");
		tp(server, A.getX() + 0.5 + 1.6, Y + 0.6, A.getZ() + 0.5 + 2.4, 180, 25);
		server.runCommand("clear @a");
		context.waitTicks(5);
		server.runOnServer(srv -> {
			ConfigManager.server().setWorkshopCommand("forge_divine", "tag @s add used_forge");
			player(srv).removeCommandTag("used_forge");
		});
		click(server, A);
		context.waitTicks(6);
		boolean tagged = server.computeOnServer(srv -> player(srv).getCommandTags().contains("used_forge"));
		check.accept(tagged && !screenOpen(context), "forge: with workshopCommands.forge_divine the click runs that command (no interface)");
		server.runOnServer(srv -> {
			ConfigManager.server().setWorkshopCommand("forge_divine", null);
			player(srv).removeCommandTag("used_forge");
		});
		context.waitTicks(12);
		click(server, A);
		int opened = waitUntil(context, () -> screenOpen(context), 40);
		boolean serverSide = server.computeOnServer(srv -> player(srv).currentScreenHandler instanceof DivineForgeScreenHandler);
		check.accept(opened >= 0 && serverSide, "forge: without a command the click opens the forge's interface (client " + (opened >= 0) + ", server "
				+ serverSide + ")");
		Object[] entry = clientEntry(context, TRIAL);
		check.accept(entry != null && (Integer) entry[0] >= 0, "forge: the interface lists the trial recipe ("
				+ (entry == null ? "no menu" : entry[4] + " recipe(s)") + ")");
		if (entry != null && (Integer) entry[0] >= 0) {
			check.accept(!(Boolean) entry[1] && "0/4 0/1".equals(entry[2]) && TRIAL_NAME.equals(entry[3]),
					"forge: with empty pockets it cannot be forged, ingredients owned / required " + entry[2] + " (" + entry[3] + ")");
		}
		context.waitTicks(10);
		shot.accept("forge_4_interface");

		// ---- the trial recipe forged through the button: ingredients removed exactly, the result after the time
		server.runCommand("give @p minecraft:gold_ingot 5");
		server.runCommand("give @p minecraft:diamond 2");
		int ready = waitUntil(context, () -> {
			Object[] en = clientEntry(context, TRIAL);
			return en != null && (Integer) en[0] >= 0 && (Boolean) en[1];
		}, 80);
		Object[] en2 = clientEntry(context, TRIAL);
		check.accept(ready >= 0, "forge: the open interface sees the new ingredients (" + (en2 == null ? "?" : en2[2]) + ", forgeable)");
		int before = STARTED.get(), finishedBefore = FINISHED.get();
		if (en2 != null && (Integer) en2[0] >= 0) {
			int index = (Integer) en2[0], syncId = (Integer) en2[5];
			context.runOnClient((MinecraftClient c) -> c.interactionManager.clickButton(syncId, index));
		}
		int started = waitUntil(context, () -> Boolean.TRUE.equals(crafting(server, A)), 40);
		check.accept(started >= 0, "forge: \"Forger\" starts the crafting");
		int gold = count(server, Items.GOLD_INGOT), diamond = count(server, Items.DIAMOND);
		check.accept(gold == 1 && diamond == 1, "forge: exactly 4 gold ingots and 1 diamond removed (left: " + gold + " gold, " + diamond + " diamond)");
		check.accept(STARTED.get() > before, "forge: the API's CRAFT_STARTED event fired");
		int seen = waitUntil(context, () -> Boolean.TRUE.equals(clientCrafting(context, A)), 40);
		check.accept(seen >= 0, "forge: the client sees the crafting under way (synced block entity)");
		ForgeRecipes.Outcome busy = server.computeOnServer(srv -> ForgeRecipes.tryCraft(player(srv), forge(srv, A), TRIAL));
		int gold2 = count(server, Items.GOLD_INGOT), diamond2 = count(server, Items.DIAMOND);
		check.accept(!busy.started() && busy.message().contains("occupée") && gold2 == 1 && diamond2 == 1,
				"forge: a second crafting is refused, nothing taken (" + busy.message() + ")");
		context.runOnClient((MinecraftClient c) -> {
			if (c.player != null) {
				c.player.closeHandledScreen();
			}
		});
		server.runCommand("gamemode spectator @a");
		look(server, A.getX() + 0.5 - 6, Y + 4.5, A.getZ() + 0.5 + 11, A.getX() + 0.5, Y + 3, A.getZ() + 0.5);
		context.waitTicks(30);
		shot.accept("forge_5_en_fabrication");
		look(server, A.getX() + 0.5 + 1.2, Y + 2.4, A.getZ() + 0.5 + 4.5, A.getX() + 0.5, Y + 1.4, A.getZ() + 0.5);
		context.waitTicks(10);
		shot.accept("forge_5b_en_fabrication_pres");
		int done = waitUntil(context, () -> server.computeOnServer(srv -> {
			ServerPlayerEntity pl = player(srv);
			for (int i = 0; i < pl.getInventory().size(); i++) {
				ItemStack s = pl.getInventory().getStack(i);
				Text name = s.get(DataComponentTypes.CUSTOM_NAME);
				if (s.isOf(Items.GOLDEN_SWORD) && name != null && TRIAL_NAME.equals(name.getString())) {
					return true;
				}
			}
			return false;
		}), 320);
		check.accept(done >= 0, "forge: the player receives the \"" + TRIAL_NAME + "\" after the time (" + done + " ticks after the pictures)");
		check.accept(Boolean.FALSE.equals(crafting(server, A)) && FINISHED.get() > finishedBefore, "forge: back at rest, CRAFT_FINISHED fired");
		int rest = waitUntil(context, () -> Boolean.FALSE.equals(clientCrafting(context, A)), 40);
		check.accept(rest >= 0, "forge: the client sees it back at rest");

		// ---- the trial recipe hidden by the server setting
		Object[] hidden = server.computeOnServer(srv -> {
			boolean shown = ForgeRecipes.byId(srv, TRIAL) != null;
			ConfigManager.server().forgeTestRecipe = false;
			boolean off = ForgeRecipes.byId(srv, TRIAL) == null;
			ConfigManager.server().forgeTestRecipe = true;
			return new Object[] {shown, off};
		});
		check.accept(Boolean.TRUE.equals(hidden[0]) && Boolean.TRUE.equals(hidden[1]), "forge: the trial recipe is hidden when forgeTestRecipe is false");

		// ---- /forge animer, etat, arreter (the profession systems' commands)
		server.runCommand("gamemode creative @a");
		server.runCommand("forge animer " + pos(A) + " 30");
		context.waitTicks(4);
		Object[] anim = server.computeOnServer(srv -> {
			DivineForgeBlockEntity f = forge(srv, A);
			return new Object[] {f.crafting(), f.craft().animationOnly(), f.remainingTicks()};
		});
		check.accept(Boolean.TRUE.equals(anim[0]) && Boolean.TRUE.equals(anim[1]) && (Long) anim[2] > 500, "forge: /forge animer x y z 30 plays the animation ("
				+ anim[2] + " ticks left)");
		check.accept(waitUntil(context, () -> Boolean.TRUE.equals(clientCrafting(context, A)), 40) >= 0, "forge: the client animates it");
		// at night, crafting
		server.runCommand("gamemode spectator @a");
		server.runCommand("time set 18000");
		look(server, A.getX() + 0.5 + 9, Y + 5, A.getZ() + 0.5 + 13, A.getX() + 0.5, Y + 3.5, A.getZ() + 0.5);
		context.waitTicks(30);
		shot.accept("forge_6_nuit");
		server.runCommand("time set 6000");
		server.runCommand("forge arreter " + pos(A.add(2, 1, 0)));
		context.waitTicks(4);
		check.accept(Boolean.FALSE.equals(crafting(server, A)), "forge: /forge arreter (any block of the forge) stops it");
		server.runCommand("execute at @p run forge animer 5");
		context.waitTicks(4);
		check.accept(Boolean.TRUE.equals(crafting(server, A)), "forge: /forge animer <secondes> finds the nearest forge");
		int ended = waitUntil(context, () -> Boolean.FALSE.equals(crafting(server, A)), 160);
		check.accept(ended >= 0, "forge: a 5 s animation ends by itself");
		boolean api = server.computeOnServer(srv -> DivineForgeApi.startCrafting(srv.getOverworld(), A.add(-3, 2, 0), 40)
				&& DivineForgeApi.isCrafting(srv.getOverworld(), A) && !DivineForgeApi.startCrafting(srv.getOverworld(), A, 40)
				&& DivineForgeApi.stopCrafting(srv.getOverworld(), A) && !DivineForgeApi.isCrafting(srv.getOverworld(), A));
		check.accept(api, "forge: DivineForgeApi start (from any block) / busy / stop");

		// ---- removal: /tent remove, then a creative player's break; nothing left
		server.runCommand("gamemode creative @a");
		tp(server, A.getX() + 0.5, Y, A.getZ() + 0.5 + 6, 180, 30);
		server.runCommand("tent remove " + pos(A));
		context.waitTicks(8);
		check.accept(nothingLeft(server, A), "forge: /tent remove leaves no block, collision, block entity nor item");
		check.accept(waitUntil(context, () -> context.computeOnClient((MinecraftClient c) -> c.world != null && TentCollisions.at(c.world, A) == null
				&& !(c.world.getBlockEntity(A) instanceof DivineForgeBlockEntity)), 40) >= 0, "forge: removed on the client too");
		server.runCommand(String.format(Locale.ROOT, "workshop place forge_divine %d %d %d north", A.getX(), A.getY(), A.getZ()));
		context.waitTicks(5);
		boolean north = server.computeOnServer(srv -> srv.getOverworld().getBlockState(A).getBlock() instanceof DivineForgeBlock
				&& srv.getOverworld().getBlockState(A).get(TentBlock.FACING) == Direction.NORTH);
		check.accept(north, "forge: /workshop place forge_divine x y z north");
		boolean broke = server.computeOnServer(srv -> player(srv).interactionManager.tryBreakBlock(A));
		context.waitTicks(8);
		check.accept(broke && nothingLeft(server, A), "forge: broken by a creative player, nothing left (no item either)");
		server.runOnServer(srv -> {
			ConfigManager.server().workshopCommands = new LinkedHashMap<>(saved);
			ConfigManager.server().sanitize();
		});
		server.runCommand("clear @a");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 24, Z - 24, X + 56, Z + 24));
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
	}

	/** No forge block, block entity, collision registration nor dropped item at the anchor's extent. */
	private static boolean nothingLeft(TestServerContext server, BlockPos a) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			Box around = local(a, -7, 0, -7, 7, 11, 7);
			return !(w.getBlockState(a).getBlock() instanceof TentBlock) && w.getBlockEntity(a) == null && TentCollisions.at(w, a) == null
					&& w.getEntitiesByClass(ItemEntity.class, around, x -> true).isEmpty();
		});
	}

	// ------------------------------------------------------------------ across a restart (solo)

	/** Before the restart: a forge crafting a named relic for the player (through the API), for five minutes. */
	public static void beforeRestart(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check) {
		listen();
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", RESTART.getX() - 10, RESTART.getZ() - 10, RESTART.getX() + 10,
				RESTART.getZ() + 10));
		context.waitTicks(10);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", RESTART.getX() - 8, RESTART.getZ() - 5, RESTART.getX() + 8, GROUND,
				RESTART.getZ() + 5));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", RESTART.getX() - 8, Y, RESTART.getZ() - 5, RESTART.getX() + 8, Y + 11,
				RESTART.getZ() + 5));
		server.runCommand("workshop place forge_divine " + pos(RESTART) + " south");
		context.waitTicks(5);
		boolean started = server.computeOnServer(srv -> {
			ItemStack relic = new ItemStack(Items.NETHER_STAR);
			relic.set(DataComponentTypes.CUSTOM_NAME, Text.literal(RELIC));
			return DivineForgeApi.startCrafting(srv.getOverworld(), RESTART, 6000, player(srv), relic);
		});
		check.accept(started && Boolean.TRUE.equals(crafting(server, RESTART)), "forge: a crafting under way before the restart");
	}

	/** After the restart: still crafting the same thing for the same player; stopped, the relic is handed over. */
	public static void afterRestart(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> shot) {
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", RESTART.getX() - 10, RESTART.getZ() - 10, RESTART.getX() + 10,
				RESTART.getZ() + 10));
		server.runCommand("gamemode spectator @a");
		look(server, RESTART.getX() + 0.5, Y + 5, RESTART.getZ() + 15, RESTART.getX() + 0.5, Y + 4, RESTART.getZ() + 0.5);
		context.waitTicks(40);
		world.waitForChunksRender();
		Object[] s = server.computeOnServer(srv -> {
			DivineForgeBlockEntity f = forge(srv, RESTART);
			return f == null ? null : new Object[] {f.crafting(), f.craft().recipe(), f.craft().playerName(), f.remainingTicks(),
					f.pendingResult().getName().getString(), player(srv).getGameProfile().name()};
		});
		check.accept(s != null, "forge: found again after the restart");
		if (s == null) {
			return;
		}
		check.accept(Boolean.TRUE.equals(s[0]) && DivineForgeBlockEntity.API_RECIPE.equals(s[1]) && (Long) s[3] > 0 && RELIC.equals(s[4])
				&& String.valueOf(s[5]).equals(s[2]), "forge: still crafting the same relic for the same player after the restart: " + java.util.Arrays.toString(s));
		check.accept(waitUntil(context, () -> Boolean.TRUE.equals(clientCrafting(context, RESTART)), 60) >= 0, "forge: the client got the crafting on joining");
		shot.accept("forge_7_apres_redemarrage");
		server.runCommand("forge arreter " + pos(RESTART));
		context.waitTicks(5);
		boolean got = server.computeOnServer(srv -> {
			ServerPlayerEntity pl = player(srv);
			for (int i = 0; i < pl.getInventory().size(); i++) {
				ItemStack st = pl.getInventory().getStack(i);
				Text name = st.get(DataComponentTypes.CUSTOM_NAME);
				if (st.isOf(Items.NETHER_STAR) && name != null && RELIC.equals(name.getString())) {
					return true;
				}
			}
			return false;
		});
		check.accept(got && Boolean.FALSE.equals(crafting(server, RESTART)), "forge: stopped after the restart, the relic is handed to its player");
		server.runCommand("tent remove " + pos(RESTART));
		context.waitTicks(5);
		check.accept(nothingLeft(server, RESTART), "forge: removed after the restart, nothing left");
		server.runCommand("clear @a minecraft:nether_star");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", RESTART.getX() - 10, RESTART.getZ() - 10, RESTART.getX() + 10,
				RESTART.getZ() + 10));
	}
}
