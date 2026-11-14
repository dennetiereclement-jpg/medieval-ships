package fr.medievalships.test;

import java.util.List;
import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestClientWorldContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;

import net.minecraft.block.BlockState;
import net.minecraft.client.MinecraftClient;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ItemUsageContext;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.client.render.DoorModels;
import fr.medievalships.core.DoorAccess;
import fr.medievalships.core.DoorData;
import fr.medievalships.core.DoorKeys;
import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorMotion;
import fr.medievalships.core.DoorType;
import fr.medievalships.core.DoorTypes;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.door.DoorBlockEntity;
import fr.medievalships.door.DoorRegistry;
import fr.medievalships.door.DoorStructure;
import fr.medievalships.door.Doors;
import fr.medievalships.door.KeyItem;

/**
 * In-game checks of the ten doors (1.31.0), on a stone platform of the flat world: the ten models loaded on the client
 * with their leaves, the item placing the three sizes centred on the aimed cell (and refusing when a cell is taken),
 * the four orientations, the click on any cell, the redstone (a redstone block, a lever stuck to the door), a lever
 * linked from a distance, the animation seen by the client half way, the collisions closed and open (server and
 * client), the commands ({@code /porte nommer, ouvrir <s>, fermer, basculer, info, liste, levier, acces, verrouiller,
 * supprimer, poser}), the locks (the click refused on every cell, a quest tag accepted), a closing door that never
 * closes on an entity (it reopens and tries again), the removal of a great gate by breaking one of its cells (no cell
 * left), screenshots of the ten doors closed and open. The solo run keeps one door open across a world restart
 * ({@link #beforeRestart}, {@link #afterRestart}); on the dedicated server, the client's copy is checked after every
 * movement. Called from {@link ShipClientGameTest}.
 *
 * <p>1.32.0 ({@link #keys}): an administrator binds a blank key (and a copy), a player who is not one cannot, the key
 * anywhere in the inventory opens its door, refused with the message without it or with the key of another door,
 * {@code /porte cle donner}, the master key opening a locked door for an administrator and refused to a player who is
 * not one (the permission level of the administrators raised for the click: nobody is one), the master key's free /
 * key switch, {@code /porte serrure changer} making the old key useless, the automatic closing (one minute by default,
 * then a short one measured; the redstone holding a door open), the migration of a 1.31.0 door's closing; the great
 * gate photographed at a quarter, half and three quarters of its opening; across the restart, a key door, its lock and
 * the player's key.
 *
 * <p>1.33.0: one key, one door ({@link #keys}): an administrator sneaking with a bound key on another door is refused
 * ("Cette clé est déjà liée à ...") and nothing changes; a key refused on a second door that has the same lock (a shared
 * lock of 1.32.0, simulated by copying the lock into it); a key of 1.32.0 bound to the first door it opens, then
 * refused on the other; a blank key bound to a door whose lock another door uses gives it a lock of its own. The
 * animation ({@link #animation}): a medium door and a great gate photographed twelve times at regular intervals while
 * they open, then while they close ({@code portes_anim_<id>_<ouv|ferm>_<nn>}, for a GIF), the pose drawn by the client
 * at each picture checked (steady, no jump back).
 */
public final class DoorGameTest {
	/** Away from every other scenario (the ships' boats are at 7400, the benchmark at 6000). */
	private static final int X = 8600, Z = 0;
	/** Top of the stone platform; the doors stand on it. */
	private static final int GROUND = -60, Y = GROUND + 1;
	/** Where the door kept across the restart stands, and the key door kept with it. */
	private static final BlockPos RESTART = new BlockPos(X + 40, Y, Z), RESTART_KEY = new BlockPos(X + 37, Y, Z);
	/** The lock of the key door before the restart (same JVM: read again after it). */
	private static String restartLock = "";
	/** The last message of the action bar the client received (the doors' refusals and confirmations). */
	private static volatile String lastOverlay = "";
	private static boolean listening;

	private DoorGameTest() {
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

	/** Yaw of a player looking towards the front of a door facing {@code quarter} from in front of it (he faces the door). */
	private static float yawFacingDoor(int quarter) {
		// the door's front faces the player: the player looks the opposite way (south 0 -> he looks north, yaw 180)
		return switch (quarter) {
			case 0 -> 180f;
			case 1 -> 270f;
			case 2 -> 0f;
			default -> 90f;
		};
	}

	/** Places a door with its item, as the player would, aiming at the top of the ground under {@code target}. */
	private static String placeWithItem(TestServerContext server, DoorType type, BlockPos target, int quarter) {
		int[] f = DoorLayout.front(quarter);
		tp(server, target.getX() + 0.5 + f[0] * 5, target.getY(), target.getZ() + 0.5 + f[1] * 5, yawFacingDoor(quarter), 20);
		return server.computeOnServer(srv -> {
			ServerPlayerEntity pl = player(srv);
			ItemStack stack = new ItemStack(Doors.item(type));
			pl.setStackInHand(Hand.MAIN_HAND, stack);
			BlockPos ground = target.down();
			BlockHitResult hit = new BlockHitResult(new Vec3d(ground.getX() + 0.5, ground.getY() + 1.0, ground.getZ() + 0.5), Direction.UP, ground, false);
			ActionResult r = stack.useOnBlock(new ItemUsageContext(pl, Hand.MAIN_HAND, hit));
			pl.setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
			return r.getClass().getSimpleName();
		});
	}

	/** How many cells of the door at {@code controller} are in place (each answering with that controller). */
	private static int cellsPresent(TestServerContext server, BlockPos controller, int quarter, DoorType type) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			int n = 0;
			for (BlockPos p : DoorStructure.cells(controller, quarter, type)) {
				if (controller.equals(DoorStructure.controllerOf(w, p))) {
					n++;
				}
			}
			return n;
		});
	}

	/** Door block cells left anywhere in the door's area (after a removal). */
	private static int doorBlocksIn(TestServerContext server, BlockPos controller, int quarter, DoorType type) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			int n = 0;
			for (BlockPos p : DoorStructure.cells(controller, quarter, type)) {
				var b = w.getBlockState(p).getBlock();
				if (b instanceof fr.medievalships.door.DoorBlock || b == Doors.PART) {
					n++;
				}
			}
			return n;
		});
	}

	/** {target, solid, progress} of a door on the server, or null. */
	private static Object[] door(TestServerContext server, BlockPos controller) {
		return server.computeOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			DoorBlockEntity d = DoorStructure.door(w, controller);
			return d == null ? null : new Object[] {d.target(), d.solid(), d.progress()};
		});
	}

	private static boolean open(TestServerContext server, BlockPos controller) {
		Object[] d = door(server, controller);
		return d != null && (Boolean) d[0] && (Double) d[2] >= 1.0 && !(Boolean) d[1];
	}

	private static boolean closed(TestServerContext server, BlockPos controller) {
		Object[] d = door(server, controller);
		return d != null && !(Boolean) d[0] && (Double) d[2] <= 0.0 && (Boolean) d[1];
	}

	/** The client's copy: {target, progress now, SOLID of the controller and of a top cell}, or null. */
	private static Object[] clientDoor(ClientGameTestContext context, BlockPos controller, BlockPos top) {
		return context.computeOnClient((MinecraftClient mc) -> {
			if (mc.world == null || !(mc.world.getBlockEntity(controller) instanceof DoorBlockEntity d)) {
				return null;
			}
			BlockState s = mc.world.getBlockState(controller), t = mc.world.getBlockState(top);
			return new Object[] {d.target(), d.progressAt(mc.world.getTime()), s.contains(DoorStructure.SOLID) && s.get(DoorStructure.SOLID),
					t.contains(DoorStructure.SOLID) && t.get(DoorStructure.SOLID)};
		});
	}

	/** A click (right click) on a cell of a door, by the player. */
	private static void click(TestServerContext server, BlockPos cell) {
		server.runOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ServerPlayerEntity pl = player(srv);
			w.getBlockState(cell).onUse(w, pl, new BlockHitResult(Vec3d.ofCenter(cell), Direction.NORTH, cell, false));
		});
	}

	/** A player-sized box in the middle of a cell (crosses the closed door's slab). */
	private static Box body(BlockPos cell) {
		return new Box(cell.getX() + 0.3, cell.getY() + 0.05, cell.getZ() + 0.3, cell.getX() + 0.7, cell.getY() + 0.95, cell.getZ() + 0.7);
	}

	private static boolean serverFree(TestServerContext server, Box box) {
		return server.computeOnServer(srv -> srv.getOverworld().isSpaceEmpty(box));
	}

	private static boolean clientFree(ClientGameTestContext context, Box box) {
		return context.computeOnClient((MinecraftClient mc) -> mc.world != null && mc.world.isSpaceEmpty(box));
	}

	private static String pos(BlockPos p) {
		return p.getX() + " " + p.getY() + " " + p.getZ();
	}

	/** Records the action bar messages the client receives (once per run of the game). */
	private static void listen() {
		if (!listening) {
			listening = true;
			ClientReceiveMessageEvents.GAME.register((message, overlay) -> {
				if (overlay) {
					lastOverlay = message.getString();
				}
			});
		}
	}

	private static DoorBlockEntity door(MinecraftServer srv, BlockPos p) {
		return DoorStructure.door(srv.getOverworld(), p);
	}

	/**
	 * A right click of the player on a cell through the game's own interaction ({@code interactBlock}: the door's block,
	 * or the item when he sneaks with something in hand), with {@code stack} in his main hand; {@code admin} forces the
	 * permission for this click (true: everybody is an administrator, false: nobody, null: as configured).
	 */
	private static void use(TestServerContext server, BlockPos cell, ItemStack stack, boolean sneaking, Boolean admin) {
		server.runOnServer(srv -> {
			ServerWorld w = srv.getOverworld();
			ServerPlayerEntity pl = player(srv);
			int saved = ConfigManager.server().adminPermissionLevel;
			if (admin != null) {
				ConfigManager.server().adminPermissionLevel = admin ? 0 : 5;
			}
			try {
				pl.setStackInHand(Hand.MAIN_HAND, stack);
				pl.setSneaking(sneaking);
				pl.interactionManager.interactBlock(pl, w, pl.getMainHandStack(), Hand.MAIN_HAND,
						new BlockHitResult(Vec3d.ofCenter(cell), Direction.SOUTH, cell, false));
			} finally {
				pl.setSneaking(false);
				ConfigManager.server().adminPermissionLevel = saved;
			}
		});
	}

	/** An empty-handed click (the keys looked for in the inventory) with the permission forced as in {@link #use}. */
	private static void clickAs(TestServerContext server, BlockPos cell, boolean admin) {
		server.runOnServer(srv -> {
			int saved = ConfigManager.server().adminPermissionLevel;
			ConfigManager.server().adminPermissionLevel = admin ? 0 : 5;
			try {
				ServerWorld w = srv.getOverworld();
				w.getBlockState(cell).onUse(w, player(srv), new BlockHitResult(Vec3d.ofCenter(cell), Direction.NORTH, cell, false));
			} finally {
				ConfigManager.server().adminPermissionLevel = saved;
			}
		});
	}

	/** The lock of the key in the player's main hand ("" for a blank key or another item). */
	private static String handLock(TestServerContext server) {
		return server.computeOnServer(srv -> KeyItem.lockOf(player(srv).getMainHandStack()));
	}

	private static void emptyHand(TestServerContext server) {
		server.runOnServer(srv -> player(srv).setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY));
	}

	/** Puts a stack in a slot of the player's inventory (not in hand). */
	private static void pocket(TestServerContext server, int slot, ItemStack stack) {
		server.runOnServer(srv -> player(srv).getInventory().setStack(slot, stack));
	}

	/** Waits until a condition holds on the server, up to maxTicks; returns the ticks waited or -1. */
	private static int waitUntil(ClientGameTestContext context, java.util.function.BooleanSupplier cond, int maxTicks) {
		for (int t = 0; t <= maxTicks; t += 2) {
			if (cond.getAsBoolean()) {
				return t;
			}
			context.waitTicks(2);
		}
		return -1;
	}

	// ------------------------------------------------------------------ the scenario

	public static void run(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world,
			BiConsumer<Boolean, String> check, Consumer<String> log, Consumer<String> shot) {
		server.runCommand("ride @p dismount");
		server.runCommand("gamemode creative @a");
		tp(server, X + 10, Y + 6, Z + 12, 180, 30);
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", X - 16, Z - 24, X + 56, Z + 40));
		context.waitTicks(30);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", X - 12, Z - 20, X + 50, GROUND, Z + 36));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", X - 12, Y, Z - 20, X + 50, Y + 9, Z + 36));
		server.runCommand("kill @e[type=minecraft:item]");
		context.waitTicks(10);

		// ---- the ten models on the client, with their leaves
		Object[] models = context.computeOnClient((MinecraftClient mc) -> {
			int loaded = 0, leavesOk = 0;
			StringBuilder bad = new StringBuilder();
			for (DoorType t : DoorTypes.ALL) {
				DoorModels.Loaded l = DoorModels.get(t);
				if (l == null) {
					bad.append(t.id()).append(" (absent) ");
					continue;
				}
				loaded++;
				int left = 0, right = 0;
				for (DoorModels.Part p : l.parts) {
					left += p.kind == DoorModels.Kind.LEAF_L ? 1 : 0;
					right += p.kind == DoorModels.Kind.LEAF_R ? 1 : 0;
				}
				if (left == 1 && right == (t.leaves() == 2 ? 1 : 0)) {
					leavesOk++;
				} else {
					bad.append(t.id()).append(" (").append(left).append("/").append(right).append(" leaves) ");
				}
			}
			return new Object[] {loaded, leavesOk, bad.toString()};
		});
		check.accept((Integer) models[0] == 10, "doors: the ten models are loaded on the client (" + models[0] + "; " + models[2] + ")");
		check.accept(((Integer) models[1]).intValue() == ((Integer) models[0]).intValue(), "doors: each model has its leaf_l, and its leaf_r for the double doors (" + models[2] + ")");

		// ---- placing the three sizes with the item, facing south, centred on the aimed cell
		BlockPos oakT = new BlockPos(X, Y, Z), barnT = new BlockPos(X + 4, Y, Z), castleT = new BlockPos(X + 10, Y, Z);
		DoorType[] sizes = {DoorTypes.OAK, DoorTypes.BARN, DoorTypes.CASTLE};
		BlockPos[] targets = {oakT, barnT, castleT};
		BlockPos[] ctrl = new BlockPos[3];
		for (int i = 0; i < 3; i++) {
			DoorType t = sizes[i];
			String r = placeWithItem(server, t, targets[i], 0);
			int[] c = DoorLayout.controllerFromTarget(targets[i].getX(), targets[i].getY(), targets[i].getZ(), 0, t.width());
			ctrl[i] = new BlockPos(c[0], c[1], c[2]);
			context.waitTicks(3);
			int present = cellsPresent(server, ctrl[i], 0, t);
			check.accept(present == t.cells(), String.format(Locale.ROOT, "doors: %s placed with its item (%s): %d/%d cells, controller at %s", t.id(), r, present,
					t.cells(), pos(ctrl[i])));
			BlockPos cp = ctrl[i];
			String facing = server.computeOnServer(srv -> {
				BlockState s = srv.getOverworld().getBlockState(cp);
				return s.contains(DoorStructure.FACING) ? s.get(DoorStructure.FACING).asString() : "?";
			});
			check.accept("south".equals(facing), "doors: " + t.id() + " faces the player (south): " + facing);
		}
		check.accept(ctrl[2].getX() == X + 9, "doors: the great gate spans the aimed cell -1 to +2 (controller x " + ctrl[2].getX() + ")");
		BlockPos oak = ctrl[0], barn = ctrl[1], castle = ctrl[2];
		BlockPos oakTop = oak.up(), castleTop = castle.up(5).east(3);
		int defaultClosing = server.computeOnServer(srv -> door(srv, oak).autoCloseSeconds());
		check.accept(defaultClosing == DoorData.AUTO_CLOSE_DEFAULT, "doors: a door placed closes by itself after one minute by default (" + defaultClosing
				+ " s)");
		// the barn door is opened once and checked much later (anti-crush): it must not close by itself meanwhile
		server.runCommand("porte fermeture " + pos(barn) + " 0");

		// ---- refused when a cell is taken
		BlockPos refusedT = new BlockPos(X + 20, Y, Z);
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d %d stone", X + 21, Y + 4, Z));
		String refused = placeWithItem(server, DoorTypes.WAREHOUSE, refusedT, 0);
		context.waitTicks(3);
		int left = doorBlocksIn(server, new BlockPos(X + 19, Y, Z), 0, DoorTypes.WAREHOUSE);
		check.accept(left == 0, "doors: a stone in the opening: the warehouse gate is refused (" + refused + ", " + left + " door block(s))");
		server.runCommand(String.format(Locale.ROOT, "setblock %d %d %d air", X + 21, Y + 4, Z));

		// ---- the four orientations
		for (int q = 0; q < 4; q++) {
			BlockPos t = new BlockPos(X + q * 6, Y, Z + 14);
			placeWithItem(server, DoorTypes.FORTRESS, t, q);
			context.waitTicks(3);
			int[] c = DoorLayout.controllerFromTarget(t.getX(), t.getY(), t.getZ(), q, 2);
			BlockPos cp = new BlockPos(c[0], c[1], c[2]);
			int present = cellsPresent(server, cp, q, DoorTypes.FORTRESS);
			int qq = q;
			String facing = server.computeOnServer(srv -> {
				BlockState s = srv.getOverworld().getBlockState(cp);
				return s.contains(DoorStructure.FACING) ? s.get(DoorStructure.FACING).asString() : "?";
			});
			check.accept(present == 8 && facing.equals(DoorStructure.facing(qq).asString()), String.format(Locale.ROOT,
					"doors: orientation %s: 8 cells to the right of the aimed cell seen from the front (%d), facing %s", DoorLayout.facingFr(q), present, facing));
			server.runCommand("porte supprimer " + pos(cp));
		}

		// ---- a click on any cell; the collisions closed and open, on the server and on the client
		check.accept(closed(server, oak) && !serverFree(server, body(oak)) && !clientFree(context, body(oak)),
				"doors: a closed door blocks the passage (server and client)");
		click(server, oak);
		int t1 = waitUntil(context, () -> open(server, oak), 40);
		check.accept(t1 >= 0, "doors: a click on the oak door opens it (" + t1 + " ticks)");
		context.waitTicks(4);
		check.accept(serverFree(server, body(oak)) && serverFree(server, body(oakTop)), "doors: once open nothing collides in the opening (server)");
		check.accept(clientFree(context, body(oak)), "doors: ... nor on the client");
		Object[] cd = clientDoor(context, oak, oakTop);
		check.accept(cd != null && (Boolean) cd[0] && !(Boolean) cd[2] && !(Boolean) cd[3], "doors: the client has the open door (target, states): "
				+ (cd == null ? "none" : java.util.Arrays.toString(cd)));
		click(server, oakTop); // the top cell: same door
		int t2 = waitUntil(context, () -> closed(server, oak), 40);
		check.accept(t2 >= 0, "doors: a click on its top cell closes it again (" + t2 + " ticks)");
		check.accept(!serverFree(server, body(oakTop)), "doors: closed again, it collides");

		// ---- redstone: a redstone block, then a lever stuck to the door
		BlockPos side = oak.west();
		server.runCommand("setblock " + pos(side) + " redstone_block");
		int r1 = waitUntil(context, () -> open(server, oak), 40);
		check.accept(r1 >= 0, "doors: a redstone block beside the door opens it (" + r1 + " ticks)");
		server.runCommand("setblock " + pos(side) + " air");
		int r2 = waitUntil(context, () -> closed(server, oak), 40);
		check.accept(r2 >= 0, "doors: the redstone gone, it closes (" + r2 + " ticks)");
		server.runCommand("setblock " + pos(side) + " lever[face=floor,powered=true]");
		int r3 = waitUntil(context, () -> open(server, oak), 40);
		check.accept(r3 >= 0, "doors: a lever stuck to the door opens it (" + r3 + " ticks)");
		server.runCommand("setblock " + pos(side) + " lever[face=floor,powered=false]");
		int r4 = waitUntil(context, () -> closed(server, oak), 40);
		check.accept(r4 >= 0, "doors: the lever off, it closes (" + r4 + " ticks)");
		server.runCommand("setblock " + pos(side) + " air");

		// ---- a lever linked from a distance
		BlockPos far = new BlockPos(X - 6, Y, Z + 10);
		server.runCommand("setblock " + pos(far) + " lever[face=floor,powered=false]");
		server.runCommand("porte levier lier " + pos(oak) + " " + pos(far));
		context.waitTicks(4);
		int linked = server.computeOnServer(srv -> {
			DoorBlockEntity d = DoorStructure.door(srv.getOverworld(), oak);
			return d == null ? -1 : d.levers().size();
		});
		check.accept(linked == 1, "doors: /porte levier lier links the lever (" + linked + ")");
		server.runCommand("setblock " + pos(far) + " lever[face=floor,powered=true]");
		int l1 = waitUntil(context, () -> open(server, oak), 40);
		check.accept(l1 >= 0, "doors: the linked lever, 11 blocks away, opens the door (" + l1 + " ticks)");
		server.runCommand("setblock " + pos(far) + " lever[face=floor,powered=false]");
		int l2 = waitUntil(context, () -> closed(server, oak), 40);
		check.accept(l2 >= 0, "doors: the linked lever off, it closes (" + l2 + " ticks)");
		server.runCommand("porte levier liste " + pos(oak));
		server.runCommand("porte levier delier " + pos(oak) + " tous");
		server.runCommand("setblock " + pos(far) + " air");

		// ---- the animation seen by the client, half way through the great gate's 3 seconds
		look(server, castle.getX() + 2, Y + 3.5, Z + 12, castle.getX() + 2, Y + 3, Z);
		world.waitForChunksRender();
		context.waitTicks(10);
		shot.accept("portes_1_trois_tailles_fermees");
		server.runCommand("porte ouvrir " + pos(castle));
		context.waitTicks(DoorTypes.LARGE_TICKS / 4);
		shot.accept("portes_2a_grande_porte_un_quart");
		double quarterLeaf = context.computeOnClient((MinecraftClient mc) -> mc.world != null && mc.world.getBlockEntity(castle) instanceof DoorBlockEntity d
				? d.leafAt(mc.world.getTime(), 0) : -1.0);
		context.waitTicks(DoorTypes.LARGE_TICKS / 2 - DoorTypes.LARGE_TICKS / 4);
		Object[] mid = clientDoor(context, castle, castleTop);
		double[] midLeaves = context.computeOnClient((MinecraftClient mc) -> mc.world != null && mc.world.getBlockEntity(castle) instanceof DoorBlockEntity d
				? new double[] {d.leafAt(mc.world.getTime(), 0), d.leafAt(mc.world.getTime(), 1)} : new double[] {-1, -1});
		check.accept(quarterLeaf >= 0 && quarterLeaf < midLeaves[0] && midLeaves[0] > 0.1 && midLeaves[0] < 0.9 && midLeaves[1] < midLeaves[0],
				String.format(Locale.ROOT, "doors: the client's curve: the great gate's left leaf %.2f at a quarter, %.2f half way, the right one later (%.2f)",
						quarterLeaf, midLeaves[0], midLeaves[1]));
		double sp = (Double) door(server, castle)[2];
		check.accept(mid != null && (Boolean) mid[0] && (Double) mid[1] > 0.2 && (Double) mid[1] < 0.8,
				String.format(Locale.ROOT, "doors: the client draws the great gate half open half way (client %.2f, server %.2f)", mid == null ? -1 : (Double) mid[1],
						sp));
		shot.accept("portes_2_grande_porte_en_mouvement");
		context.waitTicks(DoorTypes.LARGE_TICKS / 4);
		shot.accept("portes_2b_grande_porte_trois_quarts");
		int a1 = waitUntil(context, () -> open(server, castle), 80);
		check.accept(a1 >= 0, "doors: the great gate is open after its slow movement");
		check.accept(serverFree(server, body(castle.east(1))) && serverFree(server, body(castle.east(2).up(4))), "doors: the great gate's passage is free");
		server.runCommand("porte ouvrir " + pos(barn));
		waitUntil(context, () -> open(server, barn), 40);
		context.waitTicks(4);
		shot.accept("portes_3_trois_tailles_ouvertes");

		// ---- commands with a name
		server.runCommand("porte nommer " + pos(oak) + " chene_test");
		context.waitTicks(2);
		boolean named = server.computeOnServer(srv -> {
			DoorRegistry.Entry e = DoorRegistry.get(srv).byName("chene_test");
			return e != null && e.pos().equals(oak);
		});
		check.accept(named, "doors: /porte nommer puts the door in the registry under its name");
		server.runCommand("porte ouvrir chene_test 2");
		int c1 = waitUntil(context, () -> open(server, oak), 30);
		check.accept(c1 >= 0, "doors: /porte ouvrir chene_test 2 opens it");
		int c2 = waitUntil(context, () -> closed(server, oak), 100);
		check.accept(c2 >= 0, "doors: ... and it closes by itself after 2 s (" + c2 + " ticks later)");
		server.runCommand("porte basculer chene_test");
		check.accept(waitUntil(context, () -> open(server, oak), 30) >= 0, "doors: /porte basculer opens it");
		server.runCommand("porte fermer chene_test");
		check.accept(waitUntil(context, () -> closed(server, oak), 30) >= 0, "doors: /porte fermer closes it");
		server.runCommand("porte info chene_test");
		server.runCommand("porte liste");
		server.runCommand("door fermeture chene_test 1");
		click(server, oak);
		check.accept(waitUntil(context, () -> open(server, oak), 30) >= 0, "doors: opened by hand with an automatic closing of 1 s");
		check.accept(waitUntil(context, () -> closed(server, oak), 80) >= 0, "doors: ... it closes by itself");
		server.runCommand("door fermeture chene_test 0");

		// ---- locks: the click refused on every cell; a quest tag accepted
		server.runCommand("porte verrouiller chene_test");
		context.waitTicks(2);
		click(server, oak);
		click(server, oakTop);
		context.waitTicks(15);
		check.accept(closed(server, oak), "doors: locked: a click on either cell leaves it closed");
		server.runCommand("setblock " + pos(side) + " redstone_block");
		context.waitTicks(15);
		check.accept(closed(server, oak), "doors: locked: the redstone next to it is ignored");
		server.runCommand("setblock " + pos(side) + " air");
		server.runCommand("porte acces chene_test quete cle_test");
		context.waitTicks(2);
		DoorAccess acc = server.computeOnServer(srv -> DoorStructure.door(srv.getOverworld(), oak).access());
		check.accept(acc == DoorAccess.QUETE, "doors: /porte acces ... quete sets the quest access (" + acc + ")");
		click(server, oakTop);
		context.waitTicks(15);
		check.accept(closed(server, oak), "doors: quest access: refused without the tag");
		server.runCommand("tag @p add cle_test");
		click(server, oakTop);
		check.accept(waitUntil(context, () -> open(server, oak), 30) >= 0, "doors: quest access: the player with the tag opens it (top cell)");
		server.runCommand("tag @p remove cle_test");
		server.runCommand("porte deverrouiller chene_test");
		server.runCommand("porte fermer chene_test");
		waitUntil(context, () -> closed(server, oak), 30);

		// ---- never closing on an entity: it stays open, tries again, then closes
		check.accept(open(server, barn), "doors: the barn door is open for the anti-crush check");
		double[] mo = DoorLayout.toWorld(barn.getX(), barn.getY(), barn.getZ(), 0, 2, 0, 0, 0);
		server.runCommand(String.format(Locale.ROOT, "summon armor_stand %.2f %d %.2f {NoGravity:1b,Tags:[\"doorcrush\"]}", mo[0], Y, mo[2]));
		context.waitTicks(3);
		server.runCommand("porte fermer " + pos(barn));
		context.waitTicks(40);
		Object[] held = door(server, barn);
		check.accept(held != null && (Boolean) held[0] && !(Boolean) held[1], "doors: an entity in the opening: the barn door does not close on it");
		server.runCommand("kill @e[tag=doorcrush]");
		check.accept(waitUntil(context, () -> closed(server, barn), 120) >= 0, "doors: the entity gone, the barn door closes by itself");
		server.runCommand("porte ouvrir " + pos(barn));
		waitUntil(context, () -> open(server, barn), 40);
		server.runCommand("porte fermer " + pos(barn));
		context.waitTicks(6); // closing
		server.runCommand(String.format(Locale.ROOT, "summon armor_stand %.2f %d %.2f {NoGravity:1b,Tags:[\"doorcrush\"]}", mo[0], Y, mo[2]));
		context.waitTicks(6);
		Object[] back = door(server, barn);
		check.accept(back != null && (Boolean) back[0] && !(Boolean) back[1], "doors: an entity entering while it closes: the barn door opens again");
		server.runCommand("kill @e[tag=doorcrush]");
		check.accept(waitUntil(context, () -> closed(server, barn), 140) >= 0, "doors: ... and closes once the way is clear");

		// ---- the keys, the master key, the automatic closing (1.32.0)
		keys(context, server, check, log);

		// ---- /porte poser, then removal of a great gate by breaking one of its cells: nothing left
		server.runCommand(String.format(Locale.ROOT, "porte poser porte_entrepot %d %d %d sud", X + 30, Y, Z));
		context.waitTicks(3);
		BlockPos wh = new BlockPos(X + 29, Y, Z);
		check.accept(cellsPresent(server, wh, 0, DoorTypes.WAREHOUSE) == 24, "doors: /porte poser places the warehouse gate");
		server.runCommand("porte nommer " + pos(wh) + " entrepot_test");
		BlockPos part = wh.east(2).up(3);
		boolean broke = server.computeOnServer(srv -> player(srv).interactionManager.tryBreakBlock(part));
		context.waitTicks(5);
		int remaining = doorBlocksIn(server, wh, 0, DoorTypes.WAREHOUSE);
		boolean unregistered = server.computeOnServer(srv -> DoorRegistry.get(srv).byName("entrepot_test") == null);
		check.accept(broke && remaining == 0 && unregistered, "doors: breaking one cell of the great gate removes all of it (" + remaining
				+ " cell(s) left, registry " + (unregistered ? "clean" : "still has it") + ")");
		server.runCommand("setblock " + pos(barn.up(2)) + " air"); // a part removed by a command: the whole door goes
		context.waitTicks(5);
		check.accept(doorBlocksIn(server, barn, 0, DoorTypes.BARN) == 0, "doors: a cell removed by /setblock takes the whole door, no orphan");
		server.runCommand("porte supprimer " + pos(castle));
		context.waitTicks(5);
		check.accept(doorBlocksIn(server, castle, 0, DoorTypes.CASTLE) == 0, "doors: /porte supprimer removes the whole great gate");
		server.runCommand("porte supprimer chene_test");
		context.waitTicks(3);

		// ---- the animation (1.33.0): a medium door and a great gate opening and closing, image by image
		animation(context, server, world, check, shot);

		// ---- the ten doors, closed then open (screenshots)
		gallery(context, server, world, check, shot);

		server.runCommand("kill @e[type=minecraft:item]");
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", X - 16, Z - 24, X + 56, Z + 40));
	}

	/** The keys (1.32.0), on three doors of their own: see the class comment. */
	private static void keys(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check, Consumer<String> log) {
		listen();
		BlockPos a = new BlockPos(X + 30, Y, Z - 12), b = new BlockPos(X + 34, Y, Z - 12), c = new BlockPos(X + 38, Y, Z - 12);
		BlockPos aTop = a.up(), bTop = b.up(), cTop = c.up();
		server.runCommand("porte poser porte_chene " + pos(a) + " sud");
		server.runCommand("porte poser porte_chene " + pos(b) + " sud");
		server.runCommand("porte poser porte_prison " + pos(c) + " sud");
		server.runCommand("porte nommer " + pos(a) + " maison_test");
		server.runCommand("porte nommer " + pos(b) + " maison_test_arriere");
		server.runCommand("porte nommer " + pos(c) + " cachot_test");
		server.runCommand("clear @a medievalships:cle");
		server.runCommand("clear @a medievalships:cle_universelle");
		emptyHand(server);
		context.waitTicks(3);
		check.accept(cellsPresent(server, a, 0, DoorTypes.OAK) == 2 && cellsPresent(server, c, 0, DoorTypes.PRISON) == 2, "keys: the three test doors stand");

		// an administrator binds a blank key: the door gets a lock and the key access
		use(server, aTop, new ItemStack(Doors.KEY), false, true);
		Object[] bound = server.computeOnServer(srv -> {
			ItemStack h = player(srv).getMainHandStack();
			DoorBlockEntity d = door(srv, a);
			return new Object[] {KeyItem.lockOf(h), KeyItem.labelOf(h), d.lock(), d.access(), KeyItem.doorOf(h), d.doorId()};
		});
		String lockA = (String) bound[0], idA = (String) bound[5];
		check.accept(!lockA.isEmpty() && lockA.equals(bound[2]) && "maison_test".equals(bound[1]) && bound[3] == DoorAccess.CLE && idA.equals(bound[4]),
				"keys: an administrator's right click with a blank key binds it to that door, its lock and the door itself (\"Ouvre uniquement :"
						+ " maison_test\"), the door in key access: " + java.util.Arrays.toString(bound));
		server.runOnServer(srv -> {
			ItemStack k = player(srv).getMainHandStack().copy();
			player(srv).setStackInHand(Hand.MAIN_HAND, ItemStack.EMPTY);
			player(srv).getInventory().setStack(20, k);
		});
		lastOverlay = "";
		use(server, aTop, new ItemStack(Doors.KEY), false, true);
		context.waitTicks(2);
		String copy = handLock(server);
		String copyDoor = server.computeOnServer(srv -> KeyItem.doorOf(player(srv).getMainHandStack()));
		check.accept(lockA.equals(copy) && idA.equals(copyDoor) && lastOverlay.startsWith("Double de la clé"), "keys: a second blank key on the same door"
				+ " is a copy of the key of that door (\"" + lastOverlay + "\")");
		emptyHand(server);
		// renamed at an anvil (the custom name): still the key of the door
		server.runOnServer(srv -> player(srv).getInventory().getStack(20).set(net.minecraft.component.DataComponentTypes.CUSTOM_NAME,
				net.minecraft.text.Text.literal("Ma maison")));

		// a player who is not an administrator binds nothing
		lastOverlay = "";
		use(server, aTop, new ItemStack(Doors.KEY), false, false);
		context.waitTicks(3);
		String notAdmin = handLock(server);
		check.accept(notAdmin.isEmpty() && lastOverlay.contains("administrateur"), "keys: a blank key in the hand of a player who is not an administrator stays"
				+ " blank (\"" + lastOverlay + "\")");
		emptyHand(server);

		// the key, anywhere in the inventory, opens its door
		click(server, aTop);
		check.accept(waitUntil(context, () -> open(server, a), 40) >= 0, "keys: the player carrying the key (renamed, in his inventory) opens the door");
		long left = server.computeOnServer(srv -> door(srv, a).autoCloseAt() - srv.getOverworld().getTime());
		check.accept(left > 1100 && left <= 1200, "keys: opened with the key, it will close by itself in one minute (" + left + " ticks left)");
		click(server, a);
		check.accept(waitUntil(context, () -> closed(server, a), 40) >= 0, "keys: ... and closes it again");

		// without the key: refused, with the message
		server.runCommand("clear @a medievalships:cle");
		lastOverlay = "";
		click(server, aTop);
		context.waitTicks(15);
		check.accept(closed(server, a) && "Vous n'avez pas la clé de cette porte.".equals(lastOverlay),
				"keys: without the key, refused with \"Vous n'avez pas la clé de cette porte.\" (\"" + lastOverlay + "\")");

		// /porte cle donner: a bound key for the player (a free door becomes a key door); the key of another door
		server.runCommand("porte cle donner @a maison_test_arriere");
		context.waitTicks(2);
		Object[] given = server.computeOnServer(srv -> {
			var inv = player(srv).getInventory();
			DoorBlockEntity d = door(srv, b);
			int n = 0;
			String label = "";
			for (int i = 0; i < inv.size(); i++) {
				if (!d.lock().isEmpty() && d.lock().equals(KeyItem.lockOf(inv.getStack(i)))) {
					n++;
					label = KeyItem.labelOf(inv.getStack(i));
				}
			}
			return new Object[] {n, label, d.access(), d.lock()};
		});
		check.accept((Integer) given[0] == 1 && "maison_test_arriere".equals(given[1]) && given[2] == DoorAccess.CLE,
				"keys: /porte cle donner @a maison_test_arriere gives one key of that door, which becomes a key door: " + java.util.Arrays.toString(given));
		lastOverlay = "";
		click(server, aTop);
		context.waitTicks(15);
		check.accept(closed(server, a) && lastOverlay.startsWith("Vous n'avez pas la clé"), "keys: the key of another door does not open it");
		click(server, bTop);
		check.accept(waitUntil(context, () -> open(server, b), 40) >= 0, "keys: ... but opens its own door");
		click(server, b);
		waitUntil(context, () -> closed(server, b), 40);

		// one key, one door (1.33.0): an administrator sneaking with the key of the front door on the back door is refused,
		// nothing changes
		String lockB = (String) given[3];
		String idB = server.computeOnServer(srv -> door(srv, b).doorId());
		lastOverlay = "";
		use(server, bTop, KeyItem.bound(lockA, "maison_test", idA), true, true);
		context.waitTicks(3);
		Object[] after = server.computeOnServer(srv -> new Object[] {door(srv, b).lock(), KeyItem.lockOf(player(srv).getMainHandStack()),
				KeyItem.doorOf(player(srv).getMainHandStack())});
		check.accept(lockB.equals(after[0]) && lockA.equals(after[1]) && idA.equals(after[2])
				&& "Cette clé est déjà liée à « maison_test ». Une clé n'ouvre qu'une seule porte.".equals(lastOverlay),
				"keys: sneaking with the key of another door, an administrator is refused and nothing changes (\"" + lastOverlay + "\")");
		emptyHand(server);
		// the back door given the front door's lock (a lock shared in 1.32.0, a copied block entity): the front door's key
		// still does not open it
		server.runCommand("clear @a medievalships:cle");
		server.runCommand("data merge block " + pos(b) + " {lock:\"" + lockA + "\",lock_home:\"\"}");
		check.accept(lockA.equals(server.computeOnServer(srv -> door(srv, b).lock())), "keys: the back door now has the front door's lock (as in 1.32.0)");
		pocket(server, 21, KeyItem.bound(lockA, "maison_test", idA));
		lastOverlay = "";
		click(server, bTop);
		context.waitTicks(15);
		check.accept(closed(server, b) && "Vous n'avez pas la clé de cette porte.".equals(lastOverlay),
				"keys: one key, one door: the front door's key is refused on the back door that has the same lock (\"" + lastOverlay + "\")");
		click(server, aTop);
		check.accept(waitUntil(context, () -> open(server, a), 40) >= 0, "keys: ... and it still opens its own door");
		click(server, a);
		waitUntil(context, () -> closed(server, a), 40);
		// a key of 1.32.0 (bound to the lock, not to a door): it opens the first door of its lock it is used on, and that
		// door only from then on
		server.runCommand("clear @a medievalships:cle");
		pocket(server, 22, KeyItem.bound(lockA, "maison_test", ""));
		click(server, bTop);
		check.accept(waitUntil(context, () -> open(server, b), 40) >= 0, "keys: a key of 1.32.0 opens the back door (the first door of its lock it meets)");
		String adopted = server.computeOnServer(srv -> KeyItem.doorOf(player(srv).getInventory().getStack(22)));
		lastOverlay = "";
		click(server, aTop);
		context.waitTicks(15);
		check.accept(idB.equals(adopted) && closed(server, a) && lastOverlay.startsWith("Vous n'avez pas la clé"),
				"keys: ... it is now the back door's key and is refused on the front door (" + adopted + ")");
		click(server, b);
		waitUntil(context, () -> closed(server, b), 40);
		// a blank key bound to the back door, whose lock the front door uses: the back door gets a lock of its own
		server.runCommand("clear @a medievalships:cle");
		lastOverlay = "";
		use(server, bTop, new ItemStack(Doors.KEY), false, true);
		context.waitTicks(3);
		Object[] own = server.computeOnServer(srv -> new Object[] {door(srv, b).lock(), door(srv, a).lock(), KeyItem.lockOf(player(srv).getMainHandStack())});
		check.accept(!lockA.equals(own[0]) && lockA.equals(own[1]) && own[0].equals(own[2]) && lastOverlay.contains("nouvelle"),
				"keys: binding a key to a door whose lock another door uses gives it its own lock (\"" + lastOverlay + "\")");
		emptyHand(server);
		server.runCommand("clear @a medievalships:cle");

		// the master key: an administrator opens a locked door; refused to a player who is not one
		server.runCommand("porte verrouiller cachot_test");
		pocket(server, 23, new ItemStack(Doors.MASTER_KEY));
		lastOverlay = "";
		clickAs(server, cTop, true);
		check.accept(waitUntil(context, () -> open(server, c), 40) >= 0 && lastOverlay.startsWith("Passe-partout"),
				"keys: the master key (in the inventory) of an administrator opens a locked door (\"" + lastOverlay + "\")");
		server.runCommand("porte fermer cachot_test");
		waitUntil(context, () -> closed(server, c), 40);
		lastOverlay = "";
		clickAs(server, cTop, false);
		context.waitTicks(15);
		check.accept(closed(server, c) && "Ce passe-partout ne vous obéit pas.".equals(lastOverlay),
				"keys: the master key refuses a player who is not an administrator (\"" + lastOverlay + "\")");
		use(server, cTop, new ItemStack(Doors.MASTER_KEY), true, true);
		DoorAccess toKey = server.computeOnServer(srv -> door(srv, c).access());
		use(server, cTop, new ItemStack(Doors.MASTER_KEY), true, true);
		DoorAccess toFree = server.computeOnServer(srv -> door(srv, c).access());
		check.accept(toKey == DoorAccess.CLE && toFree == DoorAccess.LIBRE, "keys: sneaking with the master key, an administrator switches the door to key"
				+ " access, then free (" + toKey + ", " + toFree + ")");
		emptyHand(server);
		server.runCommand("clear @a medievalships:cle_universelle");

		// /porte serrure changer: the old key no longer opens; a new key does
		pocket(server, 20, KeyItem.bound(lockA, "maison_test", idA));
		server.runCommand("porte serrure info maison_test");
		server.runCommand("porte serrure changer maison_test");
		String newA = server.computeOnServer(srv -> door(srv, a).lock());
		lastOverlay = "";
		click(server, aTop);
		context.waitTicks(15);
		check.accept(!newA.equals(lockA) && closed(server, a) && lastOverlay.startsWith("Vous n'avez pas la clé"),
				"keys: after /porte serrure changer the old key no longer opens the door");
		server.runCommand("porte cle donner @a maison_test");
		context.waitTicks(2);
		click(server, aTop);
		check.accept(waitUntil(context, () -> open(server, a), 40) >= 0, "keys: a key given after the change opens it");
		click(server, a);
		waitUntil(context, () -> closed(server, a), 40);

		// the automatic closing: a short one measured from the click
		server.runCommand("porte fermeture maison_test 2");
		click(server, aTop);
		int opened = waitUntil(context, () -> open(server, a), 40);
		int shut = waitUntil(context, () -> closed(server, a), 140);
		int total = opened + shut;
		check.accept(opened >= 0 && shut >= 0 && total >= 40 && total <= 80, "keys: with /porte fermeture maison_test 2 the door closes by itself 2 s after"
				+ " the click (closed " + total + " ticks after it, the closing taking " + DoorTypes.SMALL_TICKS + ")");
		// the redstone holds a door open past its automatic closing, then lets it close
		server.runCommand("porte fermeture cachot_test 1");
		server.runCommand("setblock " + pos(c.west()) + " redstone_block");
		check.accept(waitUntil(context, () -> open(server, c), 40) >= 0, "keys: the redstone opens the free prison door");
		context.waitTicks(50);
		check.accept(open(server, c), "keys: the redstone holds it open past its automatic closing (1 s)");
		server.runCommand("setblock " + pos(c.west()) + " air");
		check.accept(waitUntil(context, () -> closed(server, c), 60) >= 0, "keys: the signal gone, it closes");

		// a door saved by 1.31.0 (no version) whose closing was the old default (never) takes the minute; 1.32.0 keeps 0
		server.runCommand("porte fermeture maison_test_arriere 0");
		int zero = server.computeOnServer(srv -> door(srv, b).autoCloseSeconds());
		server.runCommand("data merge block " + pos(b) + " {version:0,auto_close:0}");
		int migrated = server.computeOnServer(srv -> door(srv, b).autoCloseSeconds());
		server.runCommand("data merge block " + pos(b) + " {version:0,auto_close:7}");
		int kept = server.computeOnServer(srv -> door(srv, b).autoCloseSeconds());
		check.accept(zero == 0 && migrated == DoorData.AUTO_CLOSE_DEFAULT && kept == 7, "keys: the closing of a 1.31.0 door: the old default becomes one minute, a"
				+ " set one is kept (" + zero + ", " + migrated + ", " + kept + ")");
		log.accept("keys: lock of maison_test " + newA + ", its key's old lock " + lockA);

		server.runCommand("clear @a medievalships:cle");
		server.runCommand("porte supprimer maison_test");
		server.runCommand("porte supprimer maison_test_arriere");
		server.runCommand("porte supprimer cachot_test");
		context.waitTicks(3);
	}

	/**
	 * The animation of 1.33.0: a medium door (fortress) and a great gate (the great steam gate: gears, pistons, bolts)
	 * opening then closing, twelve pictures at regular intervals each time ({@code portes_anim_<id>_ouv_00..11},
	 * {@code ..._ferm_00..11}: a GIF), seen from behind, where the leaves swing; at each picture the pose the client drew
	 * is read and checked: opening, the leaves only ever open further and end open; closing, they only close (but for
	 * their tiny bounce at the frame) and end shut.
	 */
	private static void animation(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> shot) {
		DoorType[] types = {DoorTypes.FORTRESS, DoorTypes.GREAT_STEAM};
		int[] xs = {X, X + 9};
		server.runCommand("gamemode spectator @a"); // the camera stays still (no fall) for the whole sequence
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		for (int i = 0; i < types.length; i++) {
			DoorType t = types[i];
			BlockPos target = new BlockPos(xs[i], Y, Z - 16);
			server.runCommand(String.format(Locale.ROOT, "porte poser %s %d %d %d sud", t.id(), target.getX(), Y, target.getZ()));
			int[] cc = DoorLayout.controllerFromTarget(target.getX(), Y, target.getZ(), 0, t.width());
			BlockPos ctrl = new BlockPos(cc[0], cc[1], cc[2]);
			context.waitTicks(3);
			check.accept(cellsPresent(server, ctrl, 0, t) == t.cells(), "doors: " + t.id() + " placed for its animation");
			server.runCommand("porte fermeture " + pos(ctrl) + " 0");
			double[] o = DoorLayout.toWorld(ctrl.getX(), ctrl.getY(), ctrl.getZ(), 0, t.width(), 0, 0, 0);
			double r = t.height() * 1.1 + 2.5;
			// behind the door (north: it faces south), a little to its side and above: the leaves swing towards the camera
			look(server, o[0] + r * 0.55, Y + t.height() * 0.85 + 1.2, o[2] - r, o[0], Y + t.height() * 0.42, o[2] - 0.8);
			world.waitForChunksRender();
			context.waitTicks(10);
			for (boolean opening : new boolean[] {true, false}) {
				server.runCommand("porte " + (opening ? "ouvrir " : "fermer ") + pos(ctrl));
				double[] drawn = new double[12];
				int done = 0;
				for (int k = 0; k < 12; k++) {
					int at = Math.round(k * t.durationTicks() / 11f);
					if (at > done) {
						context.waitTicks(at - done);
						done = at;
					}
					shot.accept(String.format(Locale.ROOT, "portes_anim_%s_%s_%02d", t.id(), opening ? "ouv" : "ferm", k));
					drawn[k] = context.computeOnClient((MinecraftClient mc) -> mc.world != null && mc.world.getBlockEntity(ctrl) instanceof DoorBlockEntity d
							? d.track().pose[0] : -1.0);
				}
				context.waitTicks(10);
				double rebound = DoorMotion.curve(t).rebound();
				boolean steady = true;
				for (int k = 1; k < 12; k++) {
					steady &= opening ? drawn[k] >= drawn[k - 1] - 1e-6 : drawn[k] <= drawn[k - 1] + rebound + 1e-6;
				}
				double end = context.computeOnClient((MinecraftClient mc) -> mc.world != null && mc.world.getBlockEntity(ctrl) instanceof DoorBlockEntity d
						? d.track().pose[0] : -1.0);
				check.accept(steady && drawn[0] >= 0 && (opening ? end > 0.999 : end < 1e-6), String.format(Locale.ROOT,
						"doors: %s %s, the client draws its left leaf steadily (no jump back): %s, then %.3f", t.id(), opening ? "opening" : "closing",
						java.util.Arrays.toString(java.util.Arrays.stream(drawn).map(v -> Math.round(v * 1000) / 1000.0).toArray()), end));
				if (opening) {
					check.accept(waitUntil(context, () -> open(server, ctrl), 40) >= 0, "doors: " + t.id() + " open after its animation");
				} else {
					check.accept(waitUntil(context, () -> closed(server, ctrl), 40) >= 0, "doors: " + t.id() + " closed after its animation");
				}
			}
			server.runCommand("porte supprimer " + pos(ctrl));
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		server.runCommand("gamemode creative @a");
		context.waitTicks(3);
	}

	/** The ten doors in a row, closed then open: one picture of each, and of the row. */
	private static void gallery(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> shot) {
		List<DoorType> all = DoorTypes.ALL;
		BlockPos[] ctrl = new BlockPos[all.size()];
		int x = X - 8;
		for (int i = 0; i < all.size(); i++) {
			DoorType t = all.get(i);
			int target = x - DoorLayout.startColumn(t.width());
			server.runCommand(String.format(Locale.ROOT, "porte poser %s %d %d %d sud", t.id(), target, Y, Z + 26));
			ctrl[i] = new BlockPos(x, Y, Z + 26);
			x += t.width() + 2;
		}
		context.waitTicks(5);
		int placed = 0;
		for (int i = 0; i < all.size(); i++) {
			placed += cellsPresent(server, ctrl[i], 0, all.get(i)) == all.get(i).cells() ? 1 : 0;
		}
		check.accept(placed == 10, "doors: the ten doors stand in a row (" + placed + ")");
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = true);
		for (int pass = 0; pass < 2; pass++) {
			boolean opened = pass == 1;
			if (opened) {
				for (BlockPos c : ctrl) {
					server.runCommand("porte ouvrir " + pos(c));
				}
				context.waitTicks(DoorTypes.LARGE_TICKS + 10);
			}
			look(server, X + 22, Y + 5, Z + 44, X + 22, Y + 2, Z + 26);
			world.waitForChunksRender();
			context.waitTicks(10);
			shot.accept(opened ? "portes_5_les_dix_ouvertes" : "portes_4_les_dix_fermees");
			for (int i = 0; i < all.size(); i++) {
				DoorType t = all.get(i);
				double[] o = DoorLayout.toWorld(ctrl[i].getX(), ctrl[i].getY(), ctrl[i].getZ(), 0, t.width(), 0, 0, 0);
				double r = Math.max(t.width(), t.height()) * 0.9 + 2.0;
				look(server, o[0] - r * 0.3, Y + t.height() * 0.6 + 0.3, o[2] + r, o[0], Y + t.height() * 0.5, o[2]);
				context.waitTicks(6);
				shot.accept("porte_" + t.id() + (opened ? "_ouverte" : "_fermee"));
			}
		}
		context.runOnClient((MinecraftClient c) -> c.options.hudHidden = false);
		for (BlockPos c : ctrl) {
			server.runCommand("porte supprimer " + pos(c));
		}
	}

	// ------------------------------------------------------------------ across a restart (solo)

	/** Before the restart: a prison door named, opened by command, quest access, a lever linked. */
	public static void beforeRestart(ClientGameTestContext context, TestServerContext server, BiConsumer<Boolean, String> check) {
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", RESTART.getX() - 8, RESTART.getZ() - 8, RESTART.getX() + 8, RESTART.getZ() + 8));
		context.waitTicks(10);
		server.runCommand(String.format(Locale.ROOT, "fill %d -63 %d %d %d %d stone", RESTART.getX() - 4, RESTART.getZ() - 4, RESTART.getX() + 4, GROUND,
				RESTART.getZ() + 4));
		server.runCommand(String.format(Locale.ROOT, "fill %d %d %d %d %d %d air", RESTART.getX() - 4, Y, RESTART.getZ() - 4, RESTART.getX() + 4, Y + 4,
				RESTART.getZ() + 4));
		server.runCommand("porte poser porte_prison " + pos(RESTART) + " sud");
		server.runCommand("porte nommer " + pos(RESTART) + " prison_redemarrage");
		server.runCommand("setblock " + pos(RESTART.east(3)) + " lever[face=floor,powered=false]");
		server.runCommand("porte levier lier prison_redemarrage " + pos(RESTART.east(3)));
		server.runCommand("porte acces prison_redemarrage quete cle_prison");
		// no automatic closing: it must still be open after the restart (and "never" must be kept as such)
		server.runCommand("porte fermeture prison_redemarrage 0");
		server.runCommand("porte ouvrir prison_redemarrage");
		int t = waitUntil(context, () -> open(server, RESTART), 40);
		check.accept(t >= 0, "doors: the prison door is open before the restart");
		// a key door and the player's key (1.32.0)
		server.runCommand("porte poser porte_chene " + pos(RESTART_KEY) + " sud");
		server.runCommand("porte nommer " + pos(RESTART_KEY) + " maison_redemarrage");
		server.runCommand("clear @a medievalships:cle");
		server.runCommand("porte cle donner @a maison_redemarrage");
		context.waitTicks(3);
		restartLock = server.computeOnServer(srv -> {
			DoorBlockEntity d = door(srv, RESTART_KEY);
			return d == null ? "" : d.lock();
		});
		check.accept(!restartLock.isEmpty(), "keys: the key door has a lock before the restart");
	}

	public static void afterRestart(ClientGameTestContext context, TestServerContext server, TestClientWorldContext world, BiConsumer<Boolean, String> check,
			Consumer<String> shot) {
		server.runCommand("gamemode spectator @a");
		server.runCommand(String.format(Locale.ROOT, "forceload add %d %d %d %d", RESTART.getX() - 8, RESTART.getZ() - 8, RESTART.getX() + 8, RESTART.getZ() + 8));
		look(server, RESTART.getX() + 0.5, Y + 2, RESTART.getZ() + 6, RESTART.getX() + 0.5, Y + 1, RESTART.getZ() + 0.5);
		context.waitTicks(60);
		world.waitForChunksRender();
		context.waitTicks(10);
		Object[] s = server.computeOnServer(srv -> {
			DoorBlockEntity d = DoorStructure.door(srv.getOverworld(), RESTART);
			DoorRegistry.Entry e = DoorRegistry.get(srv).byName("prison_redemarrage");
			return d == null ? null : new Object[] {d.target(), d.solid(), d.access(), d.questTag(), d.levers().size(), e != null, d.name()};
		});
		check.accept(s != null, "doors: the prison door is found again after the restart");
		if (s == null) {
			return;
		}
		check.accept((Boolean) s[0] && !(Boolean) s[1], "doors: still open after the restart (passage free)");
		check.accept(s[2] == DoorAccess.QUETE && "cle_prison".equals(s[3]) && (Integer) s[4] == 1 && "prison_redemarrage".equals(s[6]),
				"doors: its access, quest tag, linked lever and name are kept: " + java.util.Arrays.toString(s));
		check.accept((Boolean) s[5], "doors: the registry still knows its name");
		Object[] c = clientDoor(context, RESTART, RESTART.up());
		check.accept(c != null && (Boolean) c[0] && !(Boolean) c[2], "doors: the client got the open door on joining");
		int never = server.computeOnServer(srv -> door(srv, RESTART).autoCloseSeconds());
		check.accept(never == 0, "doors: a closing set to \"never\" in 1.32.0 is kept after the restart (" + never + ")");
		shot.accept("portes_6_apres_redemarrage");
		// the key door: same lock, key access, the player's key still opens it
		Object[] k = server.computeOnServer(srv -> {
			DoorBlockEntity d = door(srv, RESTART_KEY);
			return d == null ? null : new Object[] {d.lock(), d.access(), DoorKeys.carries(KeyItem.carriedKeys(player(srv)), d.lock(), d.doorId())};
		});
		check.accept(k != null && restartLock.equals(k[0]) && k[1] == DoorAccess.CLE && (Boolean) k[2],
				"keys: after the restart the key door keeps its lock and access, the player keeps its key: " + (k == null ? "none" : java.util.Arrays.toString(k)));
		click(server, RESTART_KEY.up());
		check.accept(waitUntil(context, () -> open(server, RESTART_KEY), 40) >= 0, "keys: the key opens its door after the restart");
		server.runCommand("porte supprimer maison_redemarrage");
		server.runCommand("clear @a medievalships:cle");
		server.runCommand("porte fermer prison_redemarrage");
		check.accept(waitUntil(context, () -> closed(server, RESTART), 40) >= 0, "doors: closes after the restart");
		server.runCommand("porte supprimer prison_redemarrage");
		context.waitTicks(3);
		check.accept(doorBlocksIn(server, RESTART, 0, DoorTypes.PRISON) == 0, "doors: removed after the restart");
		server.runCommand("setblock " + pos(RESTART.east(3)) + " air");
		server.runCommand(String.format(Locale.ROOT, "forceload remove %d %d %d %d", RESTART.getX() - 8, RESTART.getZ() - 8, RESTART.getX() + 8,
				RESTART.getZ() + 8));
	}
}
