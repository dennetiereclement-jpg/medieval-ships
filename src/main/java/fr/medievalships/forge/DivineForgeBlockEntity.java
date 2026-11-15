package fr.medievalships.forge;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.network.listener.ClientPlayPacketListener;
import net.minecraft.network.packet.Packet;
import net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.storage.ReadView;
import net.minecraft.storage.WriteView;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;
import net.minecraft.util.ItemScatterer;
import net.minecraft.util.Uuids;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.api.DivineForgeApi;
import fr.medievalships.core.ForgeAnimation;
import fr.medievalships.core.ForgeCraft;
import fr.medievalships.core.TentType;
import fr.medievalships.tent.TentBlockEntity;

/**
 * The block entity of the divine forge (1.34.0, type {@code medievalships:forge_divine}): a {@link TentBlockEntity} (the
 * collisions and the drawing follow it like any prop) that keeps the forge's crafting state ({@link ForgeCraft}: at rest
 * or crafting, end tick, recipe, player), the stack being crafted and the commands of its reward, and the results kept
 * for players who were away when their crafting ended ({@link Pending}, handed over at their next click). Persisted
 * (a crafting under way goes on after a restart, its end tick being game time) and sent to the clients (the crafting
 * state only: the stacks, commands and UUIDs stay on the server), which animate the forge from it.
 *
 * <p>The server ticker only compares the end tick with the clock and completes the crafting when it is due
 * ({@link #finish}); the client ticker hands the forge to the client's effects ({@link #clientEffects}: particles and
 * sounds near the player). No entity, no real fire, nothing burns.
 */
public class DivineForgeBlockEntity extends TentBlockEntity {
	/** Version of the saved data. */
	public static final int VERSION = 1;
	/** Most results kept for absent players (the oldest is dropped at the forge beyond). */
	public static final int MAX_PENDING = 64;
	/** The recipe id of a crafting started through {@link DivineForgeApi} with a result (no recipe file behind it). */
	public static final String API_RECIPE = "medievalships:api";

	/** A result kept for an absent player: who, the stack, the reward commands to run when it is handed over. */
	public record Pending(UUID player, String name, ItemStack stack, List<String> commands) {
		public static final Codec<Pending> CODEC = RecordCodecBuilder.create(i -> i.group(
				Uuids.CODEC.fieldOf("player").forGetter(Pending::player),
				Codec.STRING.optionalFieldOf("name", "").forGetter(Pending::name),
				ItemStack.OPTIONAL_CODEC.optionalFieldOf("stack", ItemStack.EMPTY).forGetter(Pending::stack),
				Codec.STRING.listOf().optionalFieldOf("commands", List.of()).forGetter(Pending::commands)).apply(i, Pending::new));
	}

	/** The client's effects (particles, sounds), set by the client initializer; null on a dedicated server. */
	@Nullable
	public static volatile Consumer<DivineForgeBlockEntity> clientEffects;

	private final ForgeCraft craft = new ForgeCraft();
	private ItemStack result = ItemStack.EMPTY;
	private List<String> commands = List.of();
	private final List<Pending> pending = new ArrayList<>();

	// ---- client side only, never saved: the eased pace of the animation and the effects' timers (game ticks)
	/** The renderer's eased pace (gears, flipbooks), integrated from frame to frame. */
	public final ForgeAnimation.Track track = new ForgeAnimation.Track();
	public long nextCrackle, nextMachine, nextSteam, nextHammer;
	/** Was the forge crafting at the last client tick (the change starts a burst of effects)? */
	public boolean wasCrafting;

	public DivineForgeBlockEntity(BlockPos pos, BlockState state) {
		super(DivineForge.BLOCK_ENTITY, pos, state);
	}

	/** The crafting state (read only for the callers: change it through the methods of this class). */
	public ForgeCraft craft() {
		return craft;
	}

	public boolean crafting() {
		return craft.crafting();
	}

	/** Ticks left of the crafting under way (0 at rest). */
	public long remainingTicks() {
		return world == null ? 0 : craft.remaining(world.getTime());
	}

	/** The stack being crafted (a copy; empty at rest or for an animation). Server side only. */
	public ItemStack pendingResult() {
		return result.copy();
	}

	/** The results kept for absent players (a copy). Server side only. */
	public List<Pending> pending() {
		return List.copyOf(pending);
	}

	/** How many results the forge keeps for this player. */
	public int pendingFor(UUID player) {
		int n = 0;
		for (Pending p : pending) {
			if (p.player().equals(player)) {
				n++;
			}
		}
		return n;
	}

	/** The forge's world box (its extent turned to its facing), for distances and for finding it from any point. */
	public net.minecraft.util.math.Box worldExtent() {
		TentType t = tentType();
		return t == null ? new net.minecraft.util.math.Box(pos) : fr.medievalships.tent.TentCollisions.worldExtent(t, pos, quarter());
	}

	// ------------------------------------------------------------------ starting and finishing (server)

	/**
	 * Starts a player's crafting of a recipe that was paid already: the result and the reward commands are kept until the
	 * end. False (nothing kept) when the forge is busy.
	 */
	boolean startRecipe(ServerWorld world, @Nullable ServerPlayerEntity player, String recipeId, ItemStack stack, List<String> rewards, String label,
			int ticks) {
		if (!craft.start(world.getTime(), ticks, recipeId, player == null ? null : player.getUuidAsString(),
				player == null ? null : player.getGameProfile().name(), label)) {
			return false;
		}
		result = stack.copy();
		commands = List.copyOf(rewards);
		world.playSound(null, pos, SoundEvents.BLOCK_SMITHING_TABLE_USE, SoundCategory.BLOCKS, 1.0f, 0.8f);
		world.playSound(null, pos, SoundEvents.BLOCK_BLASTFURNACE_FIRE_CRACKLE, SoundCategory.BLOCKS, 1.0f, 0.7f);
		changed(world);
		DivineForgeApi.CRAFT_STARTED.invoker().onStarted(world, pos, player, Identifier.tryParse(recipeId), (int) craft.total());
		return true;
	}

	/** Starts a bare animation of {@code ticks} (no result, no player): {@code /forge animer}, the API. False when busy. */
	public boolean startAnimation(ServerWorld world, int ticks) {
		if (!craft.start(world.getTime(), ticks, null, null, null, "Animation")) {
			return false;
		}
		result = ItemStack.EMPTY;
		commands = List.of();
		world.playSound(null, pos, SoundEvents.BLOCK_BLASTFURNACE_FIRE_CRACKLE, SoundCategory.BLOCKS, 1.0f, 0.7f);
		changed(world);
		DivineForgeApi.CRAFT_STARTED.invoker().onStarted(world, pos, null, null, (int) craft.total());
		return true;
	}

	/**
	 * Ends the crafting under way now ({@code /forge arreter}, the API): a player's crafting is completed early (the
	 * result handed over), an animation simply stops. False at rest.
	 */
	public boolean stop(ServerWorld world) {
		if (!craft.crafting()) {
			return false;
		}
		craft.endAt(world.getTime());
		finish(world, false);
		return true;
	}

	static void serverTick(World world, BlockPos pos, BlockState state, DivineForgeBlockEntity forge) {
		if (forge.craft.due(world.getTime()) && world instanceof ServerWorld sw) {
			forge.finish(sw, false);
		}
	}

	static void clientTick(World world, BlockPos pos, BlockState state, DivineForgeBlockEntity forge) {
		Consumer<DivineForgeBlockEntity> fx = clientEffects;
		if (fx != null) {
			fx.accept(forge);
		}
	}

	/**
	 * Completes the crafting: the result goes to its player (into the inventory, at their feet when it is full) and the
	 * reward commands run as them; an absent player's result is kept ({@link Pending}); then the magic sound and light, the
	 * clients told, the {@link DivineForgeApi#CRAFT_FINISHED} event. {@code removed}: the forge is being taken away (an
	 * absent player's result is dropped at the forge instead of kept).
	 */
	void finish(ServerWorld world, boolean removed) {
		ForgeCraft.Finished f = craft.complete();
		if (f == null) {
			return;
		}
		ItemStack stack = result;
		List<String> rewards = commands;
		result = ItemStack.EMPTY;
		commands = List.of();
		UUID uuid = parse(f.player());
		ServerPlayerEntity player = uuid == null ? null : world.getServer().getPlayerManager().getPlayer(uuid);
		ItemStack given = stack.copy();
		if (!stack.isEmpty() || !rewards.isEmpty()) {
			if (player != null) {
				hand(player, stack, rewards, f.label());
			} else if (uuid != null && !removed) {
				pending.add(new Pending(uuid, f.playerName() == null ? "" : f.playerName(), stack, rewards));
				while (pending.size() > MAX_PENDING) {
					drop(world, pending.remove(0).stack());
				}
			} else {
				drop(world, stack);
			}
		}
		double[] c = center();
		world.playSound(null, pos, SoundEvents.BLOCK_BEACON_POWER_SELECT, SoundCategory.BLOCKS, 1.2f, 1.3f);
		if (!f.animationOnly()) {
			world.playSound(null, pos, SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME, SoundCategory.BLOCKS, 1.5f, 0.8f);
		}
		world.spawnParticles(ParticleTypes.END_ROD, c[0], c[1] + 1.2, c[2], 28, 0.8, 0.6, 0.8, 0.04);
		world.spawnParticles(ParticleTypes.WAX_ON, c[0], c[1] + 0.8, c[2], 14, 0.6, 0.3, 0.6, 0.5);
		if (!removed) {
			changed(world);
		}
		DivineForgeApi.CRAFT_FINISHED.invoker().onFinished(world, pos, player, uuid,
				f.recipe() == null ? null : Identifier.tryParse(f.recipe()), given, f.animationOnly());
	}

	/** Where the forge's effects come from: above the anvil, in front of the furnace (world coordinates). */
	double[] center() {
		double[] r = TentType.rotate(0, 1.4, quarter());
		return new double[] {pos.getX() + 0.5 + r[0], pos.getY() + 1.0, pos.getZ() + 0.5 + r[1]};
	}

	/** Hands a crafted stack over to a player present: inventory or feet, the message, the reward commands. */
	static void hand(ServerPlayerEntity player, ItemStack stack, List<String> rewards, @Nullable String label) {
		if (!stack.isEmpty()) {
			Text name = stack.getName();
			int count = stack.getCount();
			player.getInventory().offerOrDrop(stack);
			player.sendMessage(Text.literal("La forge divine vous remet : ").formatted(Formatting.GOLD)
					.append(count > 1 ? Text.literal(count + " x ").append(name) : name), false);
		}
		ForgeRecipes.runCommands(player, rewards, label);
	}

	/**
	 * Hands this player the results the forge kept for them (a click on the forge): how many were handed over.
	 */
	public int deliverPending(ServerPlayerEntity player) {
		if (pending.isEmpty()) {
			return 0;
		}
		int n = 0;
		for (Iterator<Pending> it = pending.iterator(); it.hasNext();) {
			Pending p = it.next();
			if (p.player().equals(player.getUuid())) {
				it.remove();
				hand(player, p.stack(), p.commands(), null);
				n++;
			}
		}
		if (n > 0 && world instanceof ServerWorld sw) {
			changed(sw);
		}
		return n;
	}

	/**
	 * The forge is taken away (broken, {@code /tent remove}): a crafting under way is completed now (its player gets the
	 * result, or it is dropped here), the results kept for absent players are dropped here; nothing else is left.
	 */
	@Override
	public void onBlockReplaced(BlockPos pos, BlockState oldState) {
		super.onBlockReplaced(pos, oldState);
		if (world instanceof ServerWorld sw) {
			if (craft.crafting()) {
				craft.endAt(sw.getTime());
				finish(sw, true);
			}
			for (Pending p : pending) {
				drop(sw, p.stack());
			}
			pending.clear();
		}
	}

	private void drop(ServerWorld world, ItemStack stack) {
		if (!stack.isEmpty()) {
			double[] c = center();
			ItemScatterer.spawn(world, c[0], c[1] + 0.2, c[2], stack);
		}
	}

	@Nullable
	private static UUID parse(@Nullable String s) {
		if (s == null || s.isEmpty()) {
			return null;
		}
		try {
			return UUID.fromString(s);
		} catch (IllegalArgumentException e) {
			return null;
		}
	}

	/** Saved, and sent to the clients that see the forge (the block entity update packet). */
	void changed(ServerWorld world) {
		markDirty();
		BlockState s = getCachedState();
		world.updateListeners(pos, s, s, Block.NOTIFY_LISTENERS);
	}

	// ------------------------------------------------------------------ saving and syncing

	@Override
	protected void readData(ReadView view) {
		super.readData(view);
		craft.restore(view.getBoolean("crafting", false), view.getLong("start", 0L), view.getLong("end", 0L), view.getString("recipe", ""),
				view.getString("player", ""), view.getString("player_name", ""), view.getString("label", ""));
		result = view.read("result", ItemStack.CODEC).orElse(ItemStack.EMPTY);
		commands = view.read("commands", Codec.STRING.listOf()).orElse(List.of());
		pending.clear();
		view.getOptionalTypedListView("pending", Pending.CODEC).ifPresent(list -> list.stream().forEach(pending::add));
	}

	@Override
	protected void writeData(WriteView view) {
		super.writeData(view);
		view.putInt("forge_version", VERSION);
		view.putBoolean("crafting", craft.crafting());
		if (craft.crafting()) {
			view.putLong("start", craft.start());
			view.putLong("end", craft.end());
			if (craft.recipe() != null) {
				view.putString("recipe", craft.recipe());
			}
			if (craft.player() != null) {
				view.putString("player", craft.player());
			}
			if (craft.playerName() != null) {
				view.putString("player_name", craft.playerName());
			}
			if (craft.label() != null) {
				view.putString("label", craft.label());
			}
		}
		if (!result.isEmpty()) {
			view.put("result", ItemStack.CODEC, result);
		}
		if (!commands.isEmpty()) {
			view.put("commands", Codec.STRING.listOf(), commands);
		}
		if (!pending.isEmpty()) {
			WriteView.ListAppender<Pending> list = view.getListAppender("pending", Pending.CODEC);
			for (Pending p : pending) {
				list.add(p);
			}
		}
	}

	@Override
	public Packet<ClientPlayPacketListener> toUpdatePacket() {
		return BlockEntityUpdateS2CPacket.create(this);
	}

	/** What the clients get: the crafting state, never the stacks, the commands nor the players' UUIDs. */
	@Override
	public NbtCompound toInitialChunkDataNbt(RegistryWrapper.WrapperLookup registries) {
		NbtCompound nbt = createNbt(registries);
		nbt.remove("result");
		nbt.remove("commands");
		nbt.remove("pending");
		nbt.remove("player");
		return nbt;
	}
}
