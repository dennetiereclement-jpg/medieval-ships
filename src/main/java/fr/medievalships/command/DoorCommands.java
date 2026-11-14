package fr.medievalships.command;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.ArgumentBuilder;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import com.mojang.brigadier.tree.LiteralCommandNode;

import net.minecraft.block.BlockState;
import net.minecraft.command.CommandSource;
import net.minecraft.command.argument.BlockPosArgumentType;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.core.DoorAccess;
import fr.medievalships.core.DoorDemands;
import fr.medievalships.core.DoorLayout;
import fr.medievalships.core.DoorType;
import fr.medievalships.core.DoorTypes;
import fr.medievalships.door.DoorBlockEntity;
import fr.medievalships.door.DoorItem;
import fr.medievalships.door.DoorRegistry;
import fr.medievalships.door.DoorStructure;
import fr.medievalships.door.KeyItem;
import fr.medievalships.entity.ShipPermissions;

/**
 * {@code /porte} (alias {@code /door}), administrators only (like {@code /pontlevis}): opening, closing, locking,
 * access, settings, linked levers, names, information, list, removal and placement of the doors of 1.31.0. Usable by
 * command blocks, by NPC mods' "command" actions and by quest systems. The door a command applies to is given right
 * after the action: nothing (the door the player looks at), {@code ici} (the same), its name, or the coordinates of
 * any of its cells. See docs/PORTES.md.
 *
 * <p>1.32.0: the key access ({@code acces ... cle}), {@code cle donner <joueurs> [porte]} (a key bound to the door,
 * for an NPC or a quest: the purchase of a house), {@code serrure changer [porte]} (a new lock: the old keys no longer
 * open it) and {@code serrure info [porte]}.
 */
public final class DoorCommands {
	private DoorCommands() {
	}

	private static final Pattern NAME = Pattern.compile("[a-z_][a-z0-9_.-]{0,31}");
	/** Words of the command tree that cannot be door names (they would be read as the words). */
	private static final Set<String> RESERVED = Set.of("ici", "libre", "verrouillee", "levier", "admin", "quete", "cle", "oui", "non", "tous", "lier",
			"delier", "liste", "aucun", "avant", "arriere");
	private static final SuggestionProvider<ServerCommandSource> NAMES = (ctx, builder) -> {
		List<String> names = new ArrayList<>(DoorRegistry.get(ctx.getSource().getServer()).names());
		names.add("ici");
		return CommandSource.suggestMatching(names, builder);
	};
	private static final SuggestionProvider<ServerCommandSource> TYPES = (ctx, builder) ->
			CommandSource.suggestMatching(DoorTypes.ALL.stream().map(DoorType::id), builder);
	private static final SuggestionProvider<ServerCommandSource> FACINGS = (ctx, builder) ->
			CommandSource.suggestMatching(new String[] {"nord", "sud", "est", "ouest"}, builder);

	/** The door a command applies to. */
	private record Target(ServerWorld world, BlockPos controller, DoorBlockEntity door, String label) {
		/** How a command names this door again: its name, or its controller's coordinates. */
		String ref() {
			return door.name().isEmpty() ? controller.getX() + " " + controller.getY() + " " + controller.getZ() : door.name();
		}
	}

	@FunctionalInterface
	private interface Resolver {
		Target get(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException;
	}

	/** The rest of a command after its door: attached three times (looked at, coordinates, name). */
	@FunctionalInterface
	private interface Tail {
		void attach(ArgumentBuilder<ServerCommandSource, ?> node, Resolver door);
	}

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		LiteralArgumentBuilder<ServerCommandSource> root = CommandManager.literal("porte").requires(ShipPermissions::isAdmin);
		root.then(targeted("ouvrir", (node, door) -> {
			node.executes(ctx -> open(ctx, door.get(ctx), 0));
			node.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, 86400))
					.executes(ctx -> open(ctx, door.get(ctx), IntegerArgumentType.getInteger(ctx, "secondes"))));
		}));
		root.then(targeted("fermer", (node, door) -> node.executes(ctx -> close(ctx, door.get(ctx)))));
		root.then(targeted("basculer", (node, door) -> node.executes(ctx -> toggle(ctx, door.get(ctx)))));
		root.then(targeted("verrouiller", (node, door) -> node.executes(ctx -> access(ctx, door.get(ctx), DoorAccess.VERROUILLEE, null))));
		root.then(targeted("deverrouiller", (node, door) -> node.executes(ctx -> access(ctx, door.get(ctx), DoorAccess.LIBRE, null))));
		root.then(targeted("acces", (node, door) -> {
			for (DoorAccess a : new DoorAccess[] {DoorAccess.LIBRE, DoorAccess.VERROUILLEE, DoorAccess.LEVIER, DoorAccess.ADMIN, DoorAccess.CLE}) {
				node.then(CommandManager.literal(a.word()).executes(ctx -> access(ctx, door.get(ctx), a, null)));
			}
			node.then(CommandManager.literal("quete").then(CommandManager.argument("tag", StringArgumentType.word())
					.executes(ctx -> access(ctx, door.get(ctx), DoorAccess.QUETE, StringArgumentType.getString(ctx, "tag")))));
		}));
		root.then(targeted("manuel", (node, door) -> {
			node.then(CommandManager.literal("oui").executes(ctx -> manual(ctx, door.get(ctx), true)));
			node.then(CommandManager.literal("non").executes(ctx -> manual(ctx, door.get(ctx), false)));
		}));
		root.then(targeted("redstone", (node, door) -> {
			node.then(CommandManager.literal("oui").executes(ctx -> redstone(ctx, door.get(ctx), true)));
			node.then(CommandManager.literal("non").executes(ctx -> redstone(ctx, door.get(ctx), false)));
		}));
		root.then(targeted("fermeture", (node, door) -> node.then(CommandManager.argument("secondes", IntegerArgumentType.integer(0, 3600))
				.executes(ctx -> autoClose(ctx, door.get(ctx), IntegerArgumentType.getInteger(ctx, "secondes"))))));
		root.then(targeted("sens", (node, door) -> {
			node.then(CommandManager.literal("arriere").executes(ctx -> direction(ctx, door.get(ctx), true)));
			node.then(CommandManager.literal("avant").executes(ctx -> direction(ctx, door.get(ctx), false)));
		}));
		root.then(CommandManager.literal("levier")
				.then(targeted("lier", (node, door) -> node.then(CommandManager.argument("levier", BlockPosArgumentType.blockPos())
						.executes(ctx -> link(ctx, door.get(ctx), BlockPosArgumentType.getBlockPos(ctx, "levier"))))))
				.then(targeted("delier", (node, door) -> {
					node.then(CommandManager.literal("tous").executes(ctx -> unlink(ctx, door.get(ctx), null)));
					node.then(CommandManager.argument("levier", BlockPosArgumentType.blockPos())
							.executes(ctx -> unlink(ctx, door.get(ctx), BlockPosArgumentType.getBlockPos(ctx, "levier"))));
				}))
				.then(targeted("liste", (node, door) -> node.executes(ctx -> levers(ctx, door.get(ctx))))));
		// the keys (1.32.0): a key bound to the door for players (an NPC, a quest), a new lock, the lock's information
		root.then(CommandManager.literal("cle").then(CommandManager.literal("donner").then(withDoor(CommandManager.argument("joueurs",
				EntityArgumentType.players()), (node, door) -> node.executes(ctx -> giveKey(ctx, door.get(ctx),
						EntityArgumentType.getPlayers(ctx, "joueurs")))))));
		root.then(CommandManager.literal("serrure")
				.then(targeted("changer", (node, door) -> node.executes(ctx -> renewLock(ctx, door.get(ctx)))))
				.then(targeted("info", (node, door) -> node.executes(ctx -> lockInfo(ctx, door.get(ctx))))));
		root.then(targeted("nommer", (node, door) -> node.then(CommandManager.argument("nom", StringArgumentType.word())
				.executes(ctx -> rename(ctx, door.get(ctx), StringArgumentType.getString(ctx, "nom"))))));
		root.then(targeted("info", (node, door) -> node.executes(ctx -> info(ctx, door.get(ctx)))));
		root.then(targeted("supprimer", (node, door) -> node.executes(ctx -> delete(ctx, door.get(ctx)))));
		root.then(CommandManager.literal("liste").executes(DoorCommands::list));
		root.then(CommandManager.literal("poser").then(CommandManager.argument("type", StringArgumentType.word()).suggests(TYPES)
				.executes(ctx -> place(ctx, null, null))
				.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
						.executes(ctx -> place(ctx, BlockPosArgumentType.getBlockPos(ctx, "pos"), null))
						.then(CommandManager.argument("orientation", StringArgumentType.word()).suggests(FACINGS)
								.executes(ctx -> place(ctx, BlockPosArgumentType.getBlockPos(ctx, "pos"), StringArgumentType.getString(ctx, "orientation")))))));
		LiteralCommandNode<ServerCommandSource> node = dispatcher.register(root);
		dispatcher.register(CommandManager.literal("door").requires(ShipPermissions::isAdmin).redirect(node));
	}

	/**
	 * An action whose door comes first: the looked-at door (nothing more), the coordinates of a cell, or a name ({@code ici}
	 * = looked at). The looked-at form is attached first: on the same input it wins over a name.
	 */
	private static LiteralArgumentBuilder<ServerCommandSource> targeted(String action, Tail tail) {
		return withDoor(CommandManager.literal(action), tail);
	}

	/** The door given after {@code node} (looked at, coordinates, name), then the rest of the command: {@code node} itself. */
	private static <T extends ArgumentBuilder<ServerCommandSource, T>> T withDoor(T node, Tail tail) {
		tail.attach(node, DoorCommands::lookedAt);
		var pos = CommandManager.argument("pos", BlockPosArgumentType.blockPos());
		tail.attach(pos, ctx -> at(ctx.getSource().getWorld(), BlockPosArgumentType.getBlockPos(ctx, "pos")));
		node.then(pos);
		var named = CommandManager.argument("porte", StringArgumentType.word()).suggests(NAMES);
		tail.attach(named, ctx -> named(ctx, StringArgumentType.getString(ctx, "porte")));
		node.then(named);
		return node;
	}

	// ------------------------------------------------------------------ finding the door

	private static Target lookedAt(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		ServerPlayerEntity player = ctx.getSource().getPlayer();
		if (player == null) {
			throw ShipCommands.error("Précisez la porte : son nom ou les coordonnées d'une de ses cases (x y z).");
		}
		HitResult hit = player.raycast(16, 1f, false);
		if (hit.getType() != HitResult.Type.BLOCK) {
			throw ShipCommands.error("Visez une porte (à moins de 16 blocs), ou donnez son nom ou ses coordonnées.");
		}
		return at(player.getEntityWorld(), ((BlockHitResult) hit).getBlockPos());
	}

	private static Target at(ServerWorld world, BlockPos pos) throws CommandSyntaxException {
		BlockPos c = DoorStructure.controllerOf(world, pos);
		if (c == null || !(world.getBlockEntity(c) instanceof DoorBlockEntity be) || be.doorType() == null) {
			throw ShipCommands.error("Aucune porte en " + pos.getX() + " " + pos.getY() + " " + pos.getZ() + ".");
		}
		return new Target(world, c, be, label(be, c));
	}

	private static Target named(CommandContext<ServerCommandSource> ctx, String name) throws CommandSyntaxException {
		if (name.equalsIgnoreCase("ici")) {
			return lookedAt(ctx);
		}
		DoorRegistry registry = DoorRegistry.get(ctx.getSource().getServer());
		DoorRegistry.Entry e = registry.byName(name);
		if (e == null) {
			throw ShipCommands.error("Aucune porte nommée « " + name + " » (voir /porte liste).");
		}
		ServerWorld world = ctx.getSource().getServer().getWorld(RegistryKey.of(RegistryKeys.WORLD, Identifier.of(e.dimension)));
		if (world == null) {
			throw ShipCommands.error("La dimension de la porte « " + name + " » n'existe pas (" + e.dimension + ").");
		}
		// a named door far from everyone: its chunk is read for this command only (no ticket kept)
		if (!(world.getBlockEntity(e.pos()) instanceof DoorBlockEntity)) {
			registry.remove(world, e.pos());
			throw ShipCommands.error("La porte « " + name + " » n'existe plus (" + e.x + " " + e.y + " " + e.z + ") : retirée de la liste.");
		}
		return at(world, e.pos());
	}

	private static String label(DoorBlockEntity be, BlockPos c) {
		return be.name().isEmpty() ? String.format(Locale.ROOT, "%s en %d %d %d", be.doorType().nameFr(), c.getX(), c.getY(), c.getZ())
				: "« " + be.name() + " »";
	}

	private static void say(CommandContext<ServerCommandSource> ctx, String msg, Formatting color) {
		ctx.getSource().sendFeedback(() -> Text.literal(msg).formatted(color), false);
	}

	// ------------------------------------------------------------------ actions

	private static int open(CommandContext<ServerCommandSource> ctx, Target t, int seconds) {
		t.door().open(t.world(), seconds);
		ShipCommands.ok(ctx, "Porte " + t.label() + " : ouverte" + (seconds > 0 ? " pour " + seconds + " s." : "."));
		return 1;
	}

	private static int close(CommandContext<ServerCommandSource> ctx, Target t) {
		String held = t.door().close(t.world());
		if (held != null) {
			say(ctx, "Porte " + t.label() + " : elle reste ouverte, " + held + " la maintient.", Formatting.YELLOW);
			return 0;
		}
		ShipCommands.ok(ctx, "Porte " + t.label() + " : fermée.");
		return 1;
	}

	private static int toggle(CommandContext<ServerCommandSource> ctx, Target t) {
		String why = t.door().toggle(t.world());
		if (why != null) {
			say(ctx, "Porte " + t.label() + " : " + why, Formatting.YELLOW);
			return 0;
		}
		ShipCommands.ok(ctx, "Porte " + t.label() + " : " + (t.door().target() ? "ouverte." : "fermée."));
		return 1;
	}

	private static int access(CommandContext<ServerCommandSource> ctx, Target t, DoorAccess access, String tag) throws CommandSyntaxException {
		if (access == DoorAccess.QUETE && !DoorAccess.validTag(tag)) {
			throw ShipCommands.error("Tag invalide : lettres, chiffres, _ . - + (64 au plus), comme pour /tag.");
		}
		t.door().setAccess(t.world(), access, tag);
		String extra = access == DoorAccess.VERROUILLEE ? " (fermée si une main ou une commande l'avait ouverte)"
				: access == DoorAccess.CLE ? " ; donnez-en la clé : /porte cle donner <joueurs> " + t.ref() : "";
		ShipCommands.ok(ctx, "Porte " + t.label() + " : accès " + access.describe(tag) + extra + ".");
		return 1;
	}

	private static int manual(CommandContext<ServerCommandSource> ctx, Target t, boolean on) {
		t.door().setManual(t.world(), on);
		ShipCommands.ok(ctx, "Porte " + t.label() + " : ouverture à la main " + (on ? "permise." : "désactivée."));
		return 1;
	}

	private static int redstone(CommandContext<ServerCommandSource> ctx, Target t, boolean on) {
		t.door().setRedstone(t.world(), on);
		ShipCommands.ok(ctx, "Porte " + t.label() + " : redstone et leviers liés " + (on ? "pris en compte." : "ignorés."));
		return 1;
	}

	private static int autoClose(CommandContext<ServerCommandSource> ctx, Target t, int seconds) {
		t.door().setAutoClose(t.world(), seconds);
		ShipCommands.ok(ctx, "Porte " + t.label() + " : " + (seconds > 0
				? "se referme seule " + seconds + " s après une ouverture à la main, à la clé ou par commande sans durée."
				: "ne se referme plus seule."));
		return 1;
	}

	private static int giveKey(CommandContext<ServerCommandSource> ctx, Target t, Collection<ServerPlayerEntity> players) {
		DoorBlockEntity d = t.door();
		String extra = "";
		if (d.access() == DoorAccess.LIBRE) {
			// a key for a free door would open nothing more: the door becomes a key door
			d.setAccess(t.world(), DoorAccess.CLE, null);
			extra = " (la porte, qui était libre, passe en accès à clé)";
		} else if (d.access() != DoorAccess.CLE) {
			extra = " (attention : la porte est en accès " + d.access().word() + ", la clé n'y sert qu'en accès cle)";
		}
		String lock = d.ensureLock();
		List<String> names = new ArrayList<>();
		for (ServerPlayerEntity p : players) {
			p.giveOrDropStack(KeyItem.bound(lock, d.keyLabel()));
			names.add(p.getGameProfile().name());
		}
		ShipCommands.ok(ctx, "Porte " + t.label() + " : clé donnée à " + String.join(", ", names) + extra + ".");
		return players.size();
	}

	private static int renewLock(CommandContext<ServerCommandSource> ctx, Target t) {
		boolean had = !t.door().lock().isEmpty();
		t.door().renewLock(t.world());
		ShipCommands.ok(ctx, "Porte " + t.label() + " : nouvelle serrure" + (had ? " : les anciennes clés ne l'ouvrent plus" : "")
				+ ". Nouvelles clés : /porte cle donner <joueurs> " + t.ref() + " (ou une clé vierge en main).");
		return 1;
	}

	private static int lockInfo(CommandContext<ServerCommandSource> ctx, Target t) {
		DoorBlockEntity d = t.door();
		String lock = d.lock();
		say(ctx, "Porte " + t.label() + " : accès " + d.access().describe(d.questTag()) + ".", Formatting.GOLD);
		say(ctx, "  Serrure : " + (lock.isEmpty() ? "aucune (elle sera créée en liant une clé ou avec /porte acces ... cle)" : lock)
				+ " ; les clés de cette porte affichent « Ouvre : " + d.keyLabel() + " ».", Formatting.AQUA);
		return lock.isEmpty() ? 0 : 1;
	}

	private static int direction(CommandContext<ServerCommandSource> ctx, Target t, boolean backward) {
		t.door().setBackward(t.world(), backward);
		ShipCommands.ok(ctx, "Porte " + t.label() + " : s'ouvre " + (backward ? "vers l'arrière (loin de qui l'a posée)." : "vers l'avant."));
		return 1;
	}

	private static int link(CommandContext<ServerCommandSource> ctx, Target t, BlockPos lever) throws CommandSyntaxException {
		BlockState s = t.world().getBlockState(lever);
		if (!DoorBlockEntity.linkable(s)) {
			throw ShipCommands.error("Le bloc en " + lever.getX() + " " + lever.getY() + " " + lever.getZ() + " (" + s.getBlock().getName().getString()
					+ ") n'est ni un levier, ni un bouton, ni une plaque de pression.");
		}
		String why = t.door().link(t.world(), lever);
		if (why != null) {
			throw ShipCommands.error(why);
		}
		ShipCommands.ok(ctx, "Porte " + t.label() + " : levier " + lever.getX() + " " + lever.getY() + " " + lever.getZ() + " lié ("
				+ t.door().levers().size() + "/" + DoorBlockEntity.MAX_LEVERS + ").");
		return 1;
	}

	private static int unlink(CommandContext<ServerCommandSource> ctx, Target t, BlockPos lever) {
		int n = t.door().unlink(t.world(), lever);
		if (n == 0) {
			say(ctx, "Porte " + t.label() + " : aucun levier à délier.", Formatting.YELLOW);
			return 0;
		}
		ShipCommands.ok(ctx, "Porte " + t.label() + " : " + n + " levier(s) délié(s).");
		return n;
	}

	private static int levers(CommandContext<ServerCommandSource> ctx, Target t) {
		List<BlockPos> levers = t.door().levers();
		if (levers.isEmpty()) {
			say(ctx, "Porte " + t.label() + " : aucun levier lié.", Formatting.YELLOW);
			return 0;
		}
		say(ctx, "Porte " + t.label() + " : " + levers.size() + " levier(s) lié(s) :", Formatting.GOLD);
		for (BlockPos p : levers) {
			String state = DoorStructure.controllerOf(t.world(), t.controller()) != null && t.world().isChunkLoaded(p.getX() >> 4, p.getZ() >> 4)
					? (DoorBlockEntity.powered(t.world().getBlockState(p)) ? "activé" : "au repos") : "zone non chargée";
			say(ctx, String.format(Locale.ROOT, "  %d %d %d (%s)", p.getX(), p.getY(), p.getZ(), state), Formatting.AQUA);
		}
		return levers.size();
	}

	private static int rename(CommandContext<ServerCommandSource> ctx, Target t, String name) throws CommandSyntaxException {
		DoorRegistry registry = DoorRegistry.get(ctx.getSource().getServer());
		String n = name.toLowerCase(Locale.ROOT);
		if (n.equals("aucun")) {
			t.door().setName(t.world(), "");
			registry.put(t.world(), t.controller(), t.door().doorType(), "");
			ShipCommands.ok(ctx, "Porte " + t.label() + " : n'a plus de nom.");
			return 1;
		}
		if (!NAME.matcher(n).matches() || RESERVED.contains(n)) {
			throw ShipCommands.error("Nom invalide : une lettre puis lettres, chiffres, _ . - (32 au plus), et pas un mot de la commande ("
					+ String.join(", ", RESERVED.stream().sorted().toList()) + ").");
		}
		DoorRegistry.Entry other = registry.byName(n);
		if (other != null && !(other.pos().equals(t.controller()) && other.dimension.equals(t.world().getRegistryKey().getValue().toString()))) {
			throw ShipCommands.error("Le nom « " + n + " » est déjà celui d'une autre porte (" + other.x + " " + other.y + " " + other.z + ").");
		}
		String before = t.label();
		t.door().setName(t.world(), n);
		registry.put(t.world(), t.controller(), t.door().doorType(), n);
		ShipCommands.ok(ctx, "Porte " + before + " : s'appelle maintenant « " + n + " ».");
		return 1;
	}

	private static int info(CommandContext<ServerCommandSource> ctx, Target t) {
		DoorBlockEntity d = t.door();
		DoorType type = d.doorType();
		long now = t.world().getTime();
		double p = d.progress();
		String state = d.moving() ? String.format(Locale.ROOT, "%s (%.0f %%)", d.target() ? "s'ouvre" : "se ferme", p * 100)
				: d.target() ? "ouverte" : "fermée";
		say(ctx, String.format(Locale.ROOT, "Porte %s : %s, %d de large sur %d de haut, contrôleur en %d %d %d (%s), face au %s.", t.label(), type.nameFr(),
				type.width(), type.height(), t.controller().getX(), t.controller().getY(), t.controller().getZ(), t.world().getRegistryKey().getValue(),
				DoorLayout.facingFr(d.quarter())), Formatting.GOLD);
		say(ctx, "  État : " + state + (d.solid() ? ", bloque le passage" : ", passage libre"), Formatting.AQUA);
		say(ctx, "  Accès : " + d.access().describe(d.questTag()) + (d.lock().isEmpty() ? "" : " ; serrure " + d.lock()) + " ; à la main : "
				+ (d.manualEnabled() ? "oui" : "non") + " ; redstone : "
				+ (d.redstoneEnabled() ? "oui" : "non") + " ; fermeture automatique : " + (d.autoCloseSeconds() > 0 ? d.autoCloseSeconds() + " s" : "non")
				+ " ; s'ouvre vers " + (d.backward() ? "l'arrière" : "l'avant"), Formatting.AQUA);
		DoorDemands dm = d.demands();
		List<String> wants = new ArrayList<>();
		if (dm.manual) {
			wants.add("main ou commande");
		}
		if (dm.redstone) {
			wants.add("redstone" + (d.access().redstoneAccepted(d.redstoneEnabled()) ? "" : " (ignorée)"));
		}
		if (dm.lever) {
			wants.add("levier lié" + (d.access().leversAccepted(d.redstoneEnabled()) ? "" : " (ignoré)"));
		}
		if (dm.timedUntil > now) {
			wants.add("commande minutée (" + (dm.timedUntil - now + 19) / 20 + " s)");
		}
		say(ctx, "  Demandes d'ouverture : " + (wants.isEmpty() ? "aucune" : String.join(", ", wants)) + " ; leviers liés : " + d.levers().size(),
				Formatting.AQUA);
		return 1;
	}

	private static int list(CommandContext<ServerCommandSource> ctx) {
		List<DoorRegistry.Entry> all = DoorRegistry.get(ctx.getSource().getServer()).all();
		if (all.isEmpty()) {
			say(ctx, "Aucune porte posée.", Formatting.YELLOW);
			return 0;
		}
		say(ctx, all.size() + " porte(s) :", Formatting.GOLD);
		int shown = 0;
		for (DoorRegistry.Entry e : all) {
			if (shown++ >= 50) {
				say(ctx, "  ... (" + (all.size() - 50) + " de plus)", Formatting.GRAY);
				break;
			}
			DoorType type = DoorTypes.byId(e.type);
			say(ctx, String.format(Locale.ROOT, "  %s%s, %s %d %d %d", e.name.isEmpty() ? "" : "« " + e.name + " » ", type == null ? e.type : type.nameFr(),
					e.dimension, e.x, e.y, e.z), Formatting.AQUA);
		}
		return all.size();
	}

	private static int delete(CommandContext<ServerCommandSource> ctx, Target t) {
		DoorStructure.removeDoor(t.world(), t.controller(), t.world().getBlockState(t.controller()), null, false);
		ShipCommands.ok(ctx, "Porte " + t.label() + " supprimée (toutes ses cases).");
		return 1;
	}

	private static int place(CommandContext<ServerCommandSource> ctx, BlockPos at, String facing) throws CommandSyntaxException {
		String id = StringArgumentType.getString(ctx, "type");
		DoorType type = DoorTypes.byId(id);
		if (type == null) {
			throw ShipCommands.error("Porte inconnue « " + id + " » : " + String.join(", ", DoorTypes.ALL.stream().map(DoorType::id).toList()) + ".");
		}
		ServerCommandSource src = ctx.getSource();
		ServerWorld world = src.getWorld();
		BlockPos target = at != null ? at : BlockPos.ofFloored(src.getPosition());
		int quarter;
		if (facing != null) {
			quarter = DoorLayout.quarterOf(facing);
			if (quarter < 0) {
				throw ShipCommands.error("Orientation : nord, sud, est ou ouest (le côté vers lequel la face avant regarde).");
			}
		} else {
			ServerPlayerEntity player = src.getPlayer();
			quarter = player != null ? player.getHorizontalFacing().getOpposite().getHorizontalQuarterTurns() : 0;
		}
		int[] c = DoorLayout.controllerFromTarget(target.getX(), target.getY(), target.getZ(), quarter, type.width());
		BlockPos controller = new BlockPos(c[0], c[1], c[2]);
		String problem = DoorItem.problem(world, controller, quarter, type, null);
		if (problem != null) {
			throw ShipCommands.error(problem);
		}
		DoorItem.place(world, controller, quarter, type);
		ShipCommands.ok(ctx, String.format(Locale.ROOT, "%s posée : contrôleur en %d %d %d, face au %s.", type.nameFr(), controller.getX(), controller.getY(),
				controller.getZ(), DoorLayout.facingFr(quarter)));
		return 1;
	}
}
