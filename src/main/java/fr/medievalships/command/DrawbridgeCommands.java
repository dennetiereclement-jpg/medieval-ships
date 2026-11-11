package fr.medievalships.command;

import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Pattern;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import com.mojang.brigadier.tree.LiteralCommandNode;

import net.minecraft.command.CommandSource;
import net.minecraft.command.argument.BlockPosArgumentType;
import net.minecraft.command.argument.Vec3ArgumentType;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.bridge.Drawbridge;
import fr.medievalships.bridge.Drawbridges;
import fr.medievalships.core.bridge.BridgeCycle;
import fr.medievalships.core.bridge.BridgeTuning;
import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;

/**
 * {@code /pontlevis} (alias {@code /drawbridge}), administrators only: creating a drawbridge, selecting its two
 * leaves, its hinges, its channel, its settings, previewing, checking, converting the deck, running it, testing a
 * vessel, scripted requests, restoring the original blocks. See docs/PONT_LEVIS.md.
 */
public final class DrawbridgeCommands {
	private DrawbridgeCommands() {
	}

	private static final Pattern ID = Pattern.compile("[A-Za-z0-9_.-]{1,32}");
	private static final SuggestionProvider<ServerCommandSource> IDS = (ctx, builder) ->
			CommandSource.suggestMatching(Drawbridges.all().stream().map(b -> b.id), builder);
	private static final SuggestionProvider<ServerCommandSource> LEAVES = (ctx, builder) -> CommandSource.suggestMatching(new String[] {"A", "B"}, builder);

	public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
		LiteralArgumentBuilder<ServerCommandSource> root = CommandManager.literal("pontlevis").requires(ShipPermissions::isAdmin);
		root.then(CommandManager.literal("liste").executes(DrawbridgeCommands::list));
		root.then(CommandManager.literal("creer").then(CommandManager.argument("id", StringArgumentType.word()).executes(DrawbridgeCommands::create)));
		root.then(CommandManager.literal("supprimer").then(CommandManager.argument("id", StringArgumentType.word()).suggests(IDS)
				.executes(DrawbridgeCommands::delete)));

		var bridge = CommandManager.argument("id", StringArgumentType.word()).suggests(IDS);
		bridge.then(CommandManager.literal("etat").executes(DrawbridgeCommands::status));
		bridge.then(CommandManager.literal("supprimer").executes(DrawbridgeCommands::delete)); // both orders work

		// the leaves: /pontlevis <id> vantail <A|B> pos1|pos2 [<x y z>], charniere auto [bas|haut] | <x y z>
		var leaf = CommandManager.argument("vantail", StringArgumentType.word()).suggests(LEAVES);
		for (String which : new String[] {"pos1", "pos2"}) {
			boolean first = which.equals("pos1");
			leaf.then(CommandManager.literal(which)
					.executes(ctx -> selection(ctx, first, null))
					.then(CommandManager.argument("pos", BlockPosArgumentType.blockPos())
							.executes(ctx -> selection(ctx, first, BlockPosArgumentType.getBlockPos(ctx, "pos")))));
		}
		leaf.then(CommandManager.literal("charniere")
				.then(CommandManager.literal("auto").executes(ctx -> hinge(ctx, null, false))
						.then(CommandManager.literal("bas").executes(ctx -> hinge(ctx, null, false)))
						.then(CommandManager.literal("haut").executes(ctx -> hinge(ctx, null, true))))
				.then(CommandManager.argument("point", Vec3ArgumentType.vec3())
						.executes(ctx -> hinge(ctx, Vec3ArgumentType.getVec3(ctx, "point"), false))));
		bridge.then(CommandManager.literal("vantail").then(leaf));
		// the channel
		bridge.then(CommandManager.literal("axe")
				.then(CommandManager.literal("auto").executes(ctx -> axis(ctx, null)))
				.then(CommandManager.literal("x").executes(ctx -> axis(ctx, new double[] {1, 0})))
				.then(CommandManager.literal("z").executes(ctx -> axis(ctx, new double[] {0, 1})))
				.then(CommandManager.argument("dx", DoubleArgumentType.doubleArg(-1, 1))
						.then(CommandManager.argument("dz", DoubleArgumentType.doubleArg(-1, 1))
								.executes(ctx -> axis(ctx, new double[] {DoubleArgumentType.getDouble(ctx, "dx"), DoubleArgumentType.getDouble(ctx, "dz")})))));
		bridge.then(CommandManager.literal("chenal")
				.then(CommandManager.literal("centre")
						.executes(ctx -> centre(ctx, ctx.getSource().getPosition()))
						.then(CommandManager.literal("auto").executes(ctx -> centre(ctx, null)))
						.then(CommandManager.argument("point", Vec3ArgumentType.vec3()).executes(ctx -> centre(ctx, Vec3ArgumentType.getVec3(ctx, "point")))))
				.then(CommandManager.literal("largeur")
						.then(CommandManager.literal("auto").executes(ctx -> width(ctx, null)))
						.then(CommandManager.argument("blocs", DoubleArgumentType.doubleArg(1, 256))
								.executes(ctx -> width(ctx, DoubleArgumentType.getDouble(ctx, "blocs"))))));
		bridge.then(CommandManager.literal("eau")
				.then(CommandManager.literal("auto").executes(ctx -> water(ctx, null)))
				.then(CommandManager.argument("y", DoubleArgumentType.doubleArg(-64, 400)).executes(ctx -> water(ctx, DoubleArgumentType.getDouble(ctx, "y")))));
		// the settings
		bridge.then(CommandManager.literal("approche").then(CommandManager.argument("blocs", DoubleArgumentType.doubleArg(4, 512))
				.executes(ctx -> tune(ctx, t -> t.withApproach(DoubleArgumentType.getDouble(ctx, "blocs")), "zone d'approche"))));
		bridge.then(CommandManager.literal("hysteresis").then(CommandManager.argument("blocs", DoubleArgumentType.doubleArg(0, 128))
				.executes(ctx -> tune(ctx, t -> t.withHysteresis(DoubleArgumentType.getDouble(ctx, "blocs")), "hystérésis"))));
		bridge.then(CommandManager.literal("angle").then(CommandManager.argument("degres", DoubleArgumentType.doubleArg(10, 90))
				.executes(ctx -> tune(ctx, t -> t.withOpenAngle(DoubleArgumentType.getDouble(ctx, "degres")), "angle d'ouverture"))));
		bridge.then(CommandManager.literal("duree").then(CommandManager.argument("secondes", DoubleArgumentType.doubleArg(0.5, 120))
				.executes(ctx -> tune(ctx, t -> t.withDurationTicks((int) Math.round(DoubleArgumentType.getDouble(ctx, "secondes") * 20)), "durée du mouvement"))));
		bridge.then(CommandManager.literal("delai").then(CommandManager.argument("secondes", DoubleArgumentType.doubleArg(0, 600))
				.executes(ctx -> tune(ctx, t -> t.withCloseDelayTicks((int) Math.round(DoubleArgumentType.getDouble(ctx, "secondes") * 20)), "délai avant fermeture"))));
		bridge.then(CommandManager.literal("securite").then(CommandManager.argument("secondes", DoubleArgumentType.doubleArg(0, 120))
				.executes(ctx -> tune(ctx, t -> t.withWarningTicks((int) Math.round(DoubleArgumentType.getDouble(ctx, "secondes") * 20)), "temps de sécurité avant le mouvement"))));
		bridge.then(CommandManager.literal("marge").then(CommandManager.argument("blocs", DoubleArgumentType.doubleArg(0, 8))
				.executes(ctx -> tune(ctx, t -> t.withMargin(DoubleArgumentType.getDouble(ctx, "blocs")), "marge de gabarit"))));
		bridge.then(CommandManager.literal("arret").then(CommandManager.argument("blocs", DoubleArgumentType.doubleArg(0, 64))
				.executes(ctx -> tune(ctx, t -> t.withStopDistance(DoubleArgumentType.getDouble(ctx, "blocs")), "distance d'arrêt du pilote automatique"))));
		bridge.then(CommandManager.literal("chaines")
				.then(CommandManager.literal("on").executes(ctx -> chains(ctx, true, Double.NaN)))
				.then(CommandManager.literal("off").executes(ctx -> chains(ctx, false, Double.NaN)))
				.then(CommandManager.literal("auto").executes(ctx -> chains(ctx, true, 0)))
				.then(CommandManager.argument("hauteur", DoubleArgumentType.doubleArg(1, 128))
						.executes(ctx -> chains(ctx, true, DoubleArgumentType.getDouble(ctx, "hauteur")))));
		// preview, check, convert, run
		bridge.then(CommandManager.literal("apercu")
				.then(CommandManager.literal("on").executes(ctx -> preview(ctx, true)))
				.then(CommandManager.literal("off").executes(ctx -> preview(ctx, false))));
		bridge.then(CommandManager.literal("verifier").executes(DrawbridgeCommands::verify));
		bridge.then(CommandManager.literal("convertir").executes(DrawbridgeCommands::convert));
		bridge.then(CommandManager.literal("restaurer").executes(DrawbridgeCommands::restore));
		bridge.then(CommandManager.literal("auto")
				.then(CommandManager.literal("on").executes(ctx -> automatic(ctx, true)))
				.then(CommandManager.literal("off").executes(ctx -> automatic(ctx, false))));
		bridge.then(CommandManager.literal("ouvrir").executes(DrawbridgeCommands::open));
		bridge.then(CommandManager.literal("fermer").executes(DrawbridgeCommands::close));
		bridge.then(CommandManager.literal("tester").then(CommandManager.argument("ship", StringArgumentType.string()).suggests(ShipCommands.SHIPS)
				.executes(DrawbridgeCommands::test)));
		bridge.then(CommandManager.literal("demande")
				.then(CommandManager.literal("annuler").then(CommandManager.argument("cle", StringArgumentType.string())
						.executes(ctx -> cancelRequest(ctx, StringArgumentType.getString(ctx, "cle")))))
				.then(CommandManager.argument("cle", StringArgumentType.string()).suggests(ShipCommands.SHIPS)
						.executes(ctx -> request(ctx, StringArgumentType.getString(ctx, "cle"), 120))
						.then(CommandManager.argument("secondes", IntegerArgumentType.integer(1, 86400))
								.executes(ctx -> request(ctx, StringArgumentType.getString(ctx, "cle"), IntegerArgumentType.getInteger(ctx, "secondes"))))));
		bridge.then(CommandManager.literal("debug")
				.then(CommandManager.literal("on").executes(ctx -> debug(ctx, true)))
				.then(CommandManager.literal("off").executes(ctx -> debug(ctx, false))));
		root.then(bridge);
		LiteralCommandNode<ServerCommandSource> node = dispatcher.register(root);
		dispatcher.register(CommandManager.literal("drawbridge").requires(ShipPermissions::isAdmin).redirect(node));
	}

	// ------------------------------------------------------------------ helpers

	private static Drawbridge bridge(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String id = StringArgumentType.getString(ctx, "id");
		Drawbridge b = Drawbridges.get(id);
		if (b == null) {
			throw ShipCommands.error("Aucun pont-levis « " + id + " » (voir /pontlevis liste ; /pontlevis creer <id> pour en créer un).");
		}
		return b;
	}

	private static ServerWorld world(CommandContext<ServerCommandSource> ctx, Drawbridge b) throws CommandSyntaxException {
		ServerWorld world = ctx.getSource().getServer().getWorld(b.dimension);
		if (world == null) {
			throw ShipCommands.error("La dimension du pont-levis « " + b.id + " » n'est pas chargée (" + b.dimension.getValue() + ").");
		}
		return world;
	}

	private static int leafIndex(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String v = StringArgumentType.getString(ctx, "vantail").toUpperCase(Locale.ROOT);
		if (v.equals("A") || v.equals("1")) {
			return 0;
		}
		if (v.equals("B") || v.equals("2")) {
			return 1;
		}
		throw ShipCommands.error("Le vantail est A ou B.");
	}

	/** The definition may only change while the deck is not converted (its blocks are the world's). */
	private static void editable(Drawbridge b) throws CommandSyntaxException {
		if (b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » est converti : restaurez-le d'abord (/pontlevis " + b.id
					+ " restaurer) avant de modifier sa définition.");
		}
	}

	private static BlockPos lookedAt(ServerCommandSource source) throws CommandSyntaxException {
		ServerPlayerEntity player = source.getPlayerOrThrow();
		HitResult hit = player.raycast(64, 1f, false);
		if (hit.getType() != HitResult.Type.BLOCK) {
			throw ShipCommands.error("Visez un bloc (à moins de 64 blocs), ou donnez des coordonnées.");
		}
		return ((BlockHitResult) hit).getBlockPos();
	}

	private static void saved(CommandContext<ServerCommandSource> ctx, Drawbridge b) {
		b.markDirty();
		Drawbridges.save(ctx.getSource().getServer());
		ServerWorld world = ctx.getSource().getServer().getWorld(b.dimension);
		if (world != null) {
			Drawbridges.sync(b, world);
		}
	}

	private static void lines(CommandContext<ServerCommandSource> ctx, List<String> lines, Formatting color) {
		for (String l : lines) {
			ShipCommands.say(ctx, Text.literal(l).formatted(color));
		}
	}

	private interface Tuner {
		BridgeTuning apply(BridgeTuning t);
	}

	// ------------------------------------------------------------------ commands

	private static int list(CommandContext<ServerCommandSource> ctx) {
		if (Drawbridges.all().isEmpty()) {
			ShipCommands.say(ctx, Text.literal("Aucun pont-levis. /pontlevis creer <id> pour en définir un.").formatted(Formatting.YELLOW));
			return 0;
		}
		for (Drawbridge b : Drawbridges.all()) {
			String line = String.format(Locale.ROOT, "« %s » (%s) : %s, %s%s", b.id, b.dimension.getValue(), b.converted() ? "converti" : "en définition",
					b.cycle().state().french(), b.cycle().suspended() ? ", automatisme suspendu" : "");
			ShipCommands.say(ctx, Text.literal(line).formatted(Formatting.AQUA));
		}
		return Drawbridges.all().size();
	}

	private static int create(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		String id = StringArgumentType.getString(ctx, "id");
		if (!ID.matcher(id).matches()) {
			throw ShipCommands.error("Identifiant invalide : lettres, chiffres, _ . - (32 au plus).");
		}
		if (Drawbridges.get(id) != null) {
			throw ShipCommands.error("Le pont-levis « " + id + " » existe déjà.");
		}
		Drawbridges.create(ctx.getSource().getServer(), id, ctx.getSource().getWorld());
		ShipCommands.ok(ctx, "Pont-levis « " + id + " » créé dans " + ctx.getSource().getWorld().getRegistryKey().getValue()
				+ ". Sélectionnez ensuite les deux moitiés du tablier : /pontlevis " + id + " vantail A pos1 (en visant le bloc), pos2, puis vantail B.");
		return 1;
	}

	private static int delete(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		Drawbridges.delete(ctx.getSource().getServer(), b);
		ShipCommands.ok(ctx, "Pont-levis « " + b.id + " » supprimé" + (b.converted() ? "" : "") + " (ses blocs d'origine ont été remis s'ils étaient levés).");
		return 1;
	}

	private static int status(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		lines(ctx, b.status(ConfigManager.drawbridges()), Formatting.GOLD);
		return 1;
	}

	private static int selection(CommandContext<ServerCommandSource> ctx, boolean first, BlockPos given) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		int leaf = leafIndex(ctx);
		BlockPos pos = given != null ? given : lookedAt(ctx.getSource());
		b.setSelection(leaf, first, pos.getX(), pos.getY(), pos.getZ());
		saved(ctx, b);
		Drawbridge.LeafDef l = b.leaf(leaf);
		String extent = l.complete() ? String.format(Locale.ROOT, " ; sélection %d x %d x %d blocs", l.max()[0] - l.min()[0] + 1, l.max()[1] - l.min()[1] + 1,
				l.max()[2] - l.min()[2] + 1) : " ; donnez maintenant " + (first ? "pos2" : "pos1");
		ShipCommands.ok(ctx, String.format(Locale.ROOT, "Vantail %s : %s = %d %d %d%s.", l.name, first ? "pos1" : "pos2", pos.getX(), pos.getY(), pos.getZ(), extent));
		return 1;
	}

	private static int hinge(CommandContext<ServerCommandSource> ctx, Vec3d point, boolean top) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		int leaf = leafIndex(ctx);
		b.setHinge(leaf, point == null ? null : new double[] {point.x, point.y, point.z}, top);
		saved(ctx, b);
		ShipCommands.ok(ctx, point == null ? "Vantail " + b.leaf(leaf).name + " : charnière automatique sur le bord " + (top ? "haut" : "bas") + " côté rive."
				: String.format(Locale.ROOT, "Vantail %s : la charnière passe par %.2f %.2f %.2f (le long de l'axe du chenal).", b.leaf(leaf).name, point.x, point.y, point.z));
		return 1;
	}

	private static int axis(CommandContext<ServerCommandSource> ctx, double[] axis) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		if (axis != null && Math.hypot(axis[0], axis[1]) < 1e-6) {
			throw ShipCommands.error("L'axe ne peut pas être nul.");
		}
		b.setAxis(axis);
		saved(ctx, b);
		ShipCommands.ok(ctx, axis == null ? "Axe du chenal automatique (perpendiculaire à la travée)."
				: String.format(Locale.ROOT, "Axe du chenal : (%.2f, %.2f), le sens de circulation des bateaux.", axis[0], axis[1]));
		return 1;
	}

	private static int centre(CommandContext<ServerCommandSource> ctx, Vec3d point) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		b.setCentre(point == null ? null : new double[] {point.x, point.y, point.z});
		saved(ctx, b);
		ShipCommands.ok(ctx, point == null ? "Centre du chenal automatique (milieu des deux vantaux)."
				: String.format(Locale.ROOT, "Centre du chenal : %.1f %.1f %.1f.", point.x, point.y, point.z));
		return 1;
	}

	private static int width(CommandContext<ServerCommandSource> ctx, Double width) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		b.setHalfWidth(width == null ? null : width / 2);
		saved(ctx, b);
		ShipCommands.ok(ctx, width == null ? "Largeur navigable automatique (écart entre les charnières)."
				: String.format(Locale.ROOT, "Largeur navigable : %.1f blocs entre les tours.", width));
		return 1;
	}

	private static int water(CommandContext<ServerCommandSource> ctx, Double y) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		editable(b);
		b.setWaterY(y);
		saved(ctx, b);
		ShipCommands.ok(ctx, y == null ? "Niveau de l'eau automatique (trouvé sous le centre)." : String.format(Locale.ROOT, "Niveau de l'eau : %.2f.", y));
		return 1;
	}

	private static int tune(CommandContext<ServerCommandSource> ctx, Tuner tuner, String what) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		b.setTuning(tuner.apply(b.tuning()));
		saved(ctx, b);
		BridgeTuning t = b.tuning();
		ShipCommands.ok(ctx, String.format(Locale.ROOT,
				"Pont « %s », %s réglé(e). Approche %.0f (+%.0f), angle %.0f°, durée %.1f s, délai %.1f s, sécurité %.1f s, marge %.2f, arrêt à %.0f blocs.",
				b.id, what, t.approach(), t.hysteresis(), t.openAngle(), t.durationTicks() / 20.0, t.closeDelayTicks() / 20.0, t.warningTicks() / 20.0, t.margin(),
				t.stopDistance()));
		return 1;
	}

	/** {@code chaines on|off|auto|<hauteur>}: the lifting chains drawn from the free ends to anchors over the hinges. */
	private static int chains(CommandContext<ServerCommandSource> ctx, boolean on, double height) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		b.setChains(on, Double.isNaN(height) ? b.chainHeight() : height);
		saved(ctx, b);
		ShipCommands.ok(ctx, !on ? "Pont « " + b.id + " » : chaînes de levage masquées."
				: b.chainHeight() <= 0 ? "Pont « " + b.id + " » : chaînes de levage dessinées, ancres à hauteur automatique (longueur du vantail + 1,5)."
				: String.format(Locale.ROOT, "Pont « %s » : chaînes de levage dessinées, ancres à %.1f blocs au-dessus des charnières.", b.id, b.chainHeight()));
		return 1;
	}

	private static int preview(CommandContext<ServerCommandSource> ctx, boolean on) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		ServerPlayerEntity player = ctx.getSource().getPlayerOrThrow();
		if (on) {
			if (!b.analysed()) {
				Drawbridge.Report r = b.analyse(world(ctx, b), false);
				if (!r.ok()) {
					lines(ctx, r.problems(), Formatting.YELLOW);
					ShipCommands.say(ctx, Text.literal("L'aperçu montrera les sélections ; le reste viendra quand l'analyse passera.").formatted(Formatting.GRAY));
				}
			}
			b.previewPlayers().add(player.getUuid());
		} else {
			b.previewPlayers().remove(player.getUuid());
		}
		Drawbridges.syncTo(player, b);
		ShipCommands.ok(ctx, on ? "Aperçu du pont « " + b.id + " » affiché : sélections (vert A, bleu B), charnières (jaune), volume balayé et vantaux levés (orange), barrières (rouge), zones d'approche (cyan), passage (rouge), hauteur libre (violet)."
				: "Aperçu du pont « " + b.id + " » masqué.");
		return 1;
	}

	private static int verify(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		Drawbridge.Report r = b.analyse(world(ctx, b), false);
		lines(ctx, r.info(), Formatting.GRAY);
		lines(ctx, r.warnings(), Formatting.YELLOW);
		if (!r.ok()) {
			lines(ctx, r.problems(), Formatting.RED);
			ShipCommands.say(ctx, Text.literal("Vérification échouée : corrigez puis relancez /pontlevis " + b.id + " verifier.").formatted(Formatting.RED));
			return 0;
		}
		saved(ctx, b);
		ShipCommands.ok(ctx, "Vérification réussie : /pontlevis " + b.id + " convertir transforme le tablier en pont-levis (ses blocs restent en place tant qu'il est fermé).");
		return 1;
	}

	private static int convert(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		if (b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » est déjà converti.");
		}
		Drawbridge.Report r = b.convert(world(ctx, b));
		lines(ctx, r.info(), Formatting.GRAY);
		lines(ctx, r.warnings(), Formatting.YELLOW);
		if (!r.ok()) {
			lines(ctx, r.problems(), Formatting.RED);
			throw ShipCommands.error("Conversion refusée.");
		}
		Drawbridges.save(ctx.getSource().getServer());
		ShipCommands.ok(ctx, "Pont-levis « " + b.id + " » converti et en service (" + (b.cycle().suspended() ? "automatisme suspendu : /pontlevis " + b.id + " auto on" : "automatique")
				+ "). Les blocs d'origine sont enregistrés : /pontlevis " + b.id + " restaurer les remet et rend la main.");
		return 1;
	}

	private static int restore(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		if (!b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » n'est pas converti : rien à restaurer.");
		}
		int placed = b.restore(world(ctx, b));
		Drawbridges.save(ctx.getSource().getServer());
		ShipCommands.ok(ctx, "Pont « " + b.id + " » restauré : " + (placed > 0 ? placed + " blocs remis en place, " : "ses blocs étaient en place, ")
				+ "le tablier redevient une construction ordinaire. Sa définition est conservée (/pontlevis " + b.id + " convertir pour le remettre en service).");
		return 1;
	}

	private static int automatic(CommandContext<ServerCommandSource> ctx, boolean on) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		b.cycle().setSuspended(!on);
		saved(ctx, b);
		ShipCommands.ok(ctx, on ? "Pont « " + b.id + " » : automatisme actif (ouverture à l'approche d'un navire qui ne passe pas dessous, fermeture après dégagement)."
				: "Pont « " + b.id + " » : automatisme suspendu (il garde son état ; /pontlevis " + b.id + " ouvrir|fermer pour le manœuvrer).");
		return 1;
	}

	private static int open(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		if (!b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » n'est pas converti.");
		}
		BridgeCycle.State st = b.cycle().state();
		if (st == BridgeCycle.State.OUVERT || st == BridgeCycle.State.OUVERTURE) {
			ShipCommands.ok(ctx, "Le pont « " + b.id + " » est déjà " + st.french() + ".");
			return 1;
		}
		b.cycle().requestOpen();
		ShipCommands.ok(ctx, "Ouverture demandée : annonce, " + String.format(Locale.ROOT, "%.1f", b.tuning().warningTicks() / 20.0)
				+ " s de sécurité, puis levée si personne n'est sur le tablier ni dans le volume balayé.");
		return 1;
	}

	private static int close(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		if (!b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » n'est pas converti.");
		}
		b.requests().clear();
		BridgeCycle.State st = b.cycle().state();
		if (st == BridgeCycle.State.FERME || st == BridgeCycle.State.FERMETURE) {
			ShipCommands.ok(ctx, "Le pont « " + b.id + " » est déjà " + st.french() + ".");
			return 1;
		}
		b.cycle().requestClose();
		ShipCommands.ok(ctx, "Fermeture demandée (les demandes scriptées sont annulées) : les vantaux redescendent dès que rien n'est dans le passage ni dans leur volume ; un navire qui y entre les fait remonter.");
		return 1;
	}

	private static int test(CommandContext<ServerCommandSource> ctx) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		ShipEntity ship = ShipCommands.resolve(ctx.getSource(), StringArgumentType.getString(ctx, "ship"));
		if (!b.analysed()) {
			Drawbridge.Report r = b.analyse(world(ctx, b), false);
			if (!r.ok()) {
				lines(ctx, r.problems(), Formatting.RED);
				throw ShipCommands.error("Le pont n'est pas analysable : voir ci-dessus.");
			}
		}
		lines(ctx, b.measure(world(ctx, b), ship), Formatting.GOLD);
		return 1;
	}

	private static int request(CommandContext<ServerCommandSource> ctx, String key, int seconds) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		if (!b.converted()) {
			throw ShipCommands.error("Le pont « " + b.id + " » n'est pas converti.");
		}
		Drawbridges.request(b, key, seconds, world(ctx, b));
		ShipCommands.ok(ctx, "Demande d'ouverture « " + key + " » enregistrée pour " + seconds + " s : le pont s'ouvre (sécurités respectées) et reste ouvert tant qu'elle court ; /pontlevis "
				+ b.id + " demande annuler " + key + " la retire.");
		return 1;
	}

	private static int cancelRequest(CommandContext<ServerCommandSource> ctx, String key) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		boolean removed = Drawbridges.cancelRequest(b, key);
		ShipCommands.ok(ctx, removed ? "Demande « " + key + " » annulée." : "Aucune demande « " + key + " ».");
		return removed ? 1 : 0;
	}

	private static int debug(CommandContext<ServerCommandSource> ctx, boolean on) throws CommandSyntaxException {
		Drawbridge b = bridge(ctx);
		UUID uuid = ctx.getSource().getPlayerOrThrow().getUuid();
		if (on) {
			b.debugPlayers().add(uuid);
		} else {
			b.debugPlayers().remove(uuid);
		}
		ShipCommands.ok(ctx, on ? "Débogage du pont « " + b.id + " » : chaque seconde, l'état, l'angle, l'attente éventuelle et les navires pris en compte (distance, côté, verdict) dans la barre d'action ; /pontlevis "
				+ b.id + " etat pour le détail complet." : "Débogage du pont « " + b.id + " » arrêté.");
		return 1;
	}
}
