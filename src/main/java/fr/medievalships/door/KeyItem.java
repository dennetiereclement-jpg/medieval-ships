package fr.medievalships.door;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import net.minecraft.block.BlockState;
import net.minecraft.component.type.TooltipDisplayComponent;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ItemUsageContext;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.core.DoorKeys;

/**
 * A key of the doors (1.32.0): {@code medievalships:cle} (blank, or bound to one door by an administrator: the
 * {@link KeyLock} component, its lock and, since 1.33.0, the door itself) and the administrators' master key
 * {@code medievalships:cle_universelle}. One per stack; no recipe makes or copies them (an administrator gives them, by
 * hand or with {@code /porte cle donner}). One key opens one door.
 *
 * <p>The click on a door goes through the door's cells ({@link DoorCells#useWithItem}) when the player does not sneak;
 * sneaking with a key in hand, the game skips the block and uses the item: {@link #useOnBlock} then hands the gesture
 * to the door ({@link DoorBlockEntity#useKey}). Keys are looked for in the whole inventory only when a door is clicked
 * ({@link #carriedKeys}, {@link #carriesMaster}).
 */
public class KeyItem extends Item {
	private final boolean master;

	public KeyItem(Settings settings, boolean master) {
		super(settings);
		this.master = master;
	}

	/** Is this the master key? */
	public boolean master() {
		return master;
	}

	// ------------------------------------------------------------------ reading a stack

	/** What a stack in hand is for the gestures: another item, a blank key, a bound key, the master key. */
	public static DoorKeys.Held held(ItemStack stack) {
		if (stack == null || !(stack.getItem() instanceof KeyItem k)) {
			return DoorKeys.Held.OTHER;
		}
		if (k.master) {
			return DoorKeys.Held.MASTER;
		}
		return lockOf(stack).isEmpty() ? DoorKeys.Held.BLANK : DoorKeys.Held.BOUND;
	}

	/** The lock of a bound key, or "" (a blank key, another item). */
	public static String lockOf(ItemStack stack) {
		if (stack == null || !(stack.getItem() instanceof KeyItem k) || k.master) {
			return "";
		}
		KeyLock l = stack.get(Doors.LOCK);
		return l == null ? "" : l.lock();
	}

	/** The door a bound key opens ({@link DoorKeys#doorId}), or "" (a blank key, a key of 1.32.0 not used yet, another item). */
	public static String doorOf(ItemStack stack) {
		if (stack == null || !(stack.getItem() instanceof KeyItem k) || k.master) {
			return "";
		}
		KeyLock l = stack.get(Doors.LOCK);
		return l == null ? "" : l.door();
	}

	/** The label of the door of a bound key, or "". */
	public static String labelOf(ItemStack stack) {
		KeyLock l = stack == null ? null : stack.get(Doors.LOCK);
		return l == null ? "" : l.label();
	}

	/** Binds a key (in place) to a door: its lock, its label, its identity ({@link DoorKeys#doorId}). */
	public static void bind(ItemStack stack, String lock, String label, String door) {
		stack.set(Doors.LOCK, new KeyLock(lock, label, door));
	}

	/** A new key bound to a door. */
	public static ItemStack bound(String lock, String label, String door) {
		ItemStack stack = new ItemStack(Doors.KEY);
		bind(stack, lock, label, door);
		return stack;
	}

	/** Every key the player carries (hands, inventory, armour slots): its lock and its door, looked for on a click only. */
	public static List<DoorKeys.Key> carriedKeys(PlayerEntity player) {
		List<DoorKeys.Key> out = new ArrayList<>();
		PlayerInventory inv = player.getInventory();
		for (int i = 0; i < inv.size(); i++) {
			ItemStack s = inv.getStack(i);
			String l = lockOf(s);
			if (!l.isEmpty()) {
				out.add(new DoorKeys.Key(l, doorOf(s)));
			}
		}
		return out;
	}

	/**
	 * A key of 1.32.0 (bound to a lock, not to a door) that just opened a door becomes the key of that door: the first
	 * such key of that lock the player carries is bound to it (its label too). Returns whether one was.
	 */
	public static boolean adopt(PlayerEntity player, String lock, String door, String label) {
		PlayerInventory inv = player.getInventory();
		for (int i = 0; i < inv.size(); i++) {
			ItemStack s = inv.getStack(i);
			if (!lock.isEmpty() && lock.equals(lockOf(s)) && doorOf(s).isEmpty()) {
				bind(s, lock, label, door);
				inv.markDirty();
				return true;
			}
		}
		return false;
	}

	/** Does the player carry the master key anywhere in his inventory? */
	public static boolean carriesMaster(PlayerEntity player) {
		PlayerInventory inv = player.getInventory();
		for (int i = 0; i < inv.size(); i++) {
			if (inv.getStack(i).getItem() instanceof KeyItem k && k.master) {
				return true;
			}
		}
		return false;
	}

	// ------------------------------------------------------------------ using it

	/** Sneaking with a key in hand on a door: the game skips the door's block and comes here. */
	@Override
	public ActionResult useOnBlock(ItemUsageContext context) {
		World world = context.getWorld();
		BlockPos pos = context.getBlockPos();
		BlockState state = world.getBlockState(pos);
		if (!(state.getBlock() instanceof DoorBlock) && state.getBlock() != Doors.PART) {
			return super.useOnBlock(context);
		}
		PlayerEntity player = context.getPlayer();
		if (player == null) {
			return ActionResult.PASS;
		}
		if (world instanceof ServerWorld sw) {
			DoorBlockEntity door = DoorStructure.door(world, pos);
			if (door == null) {
				return ActionResult.PASS;
			}
			door.useKey(sw, player, context.getStack(), player.shouldCancelInteraction());
		}
		return ActionResult.SUCCESS;
	}

	@Override
	public void appendTooltip(ItemStack stack, Item.TooltipContext context, TooltipDisplayComponent displayComponent, Consumer<Text> textConsumer,
			TooltipType type) {
		if (master) {
			textConsumer.accept(Text.translatable("item.medievalships.cle_universelle.desc").formatted(Formatting.GOLD));
			textConsumer.accept(Text.translatable("item.medievalships.cle_universelle.geste").formatted(Formatting.GRAY));
			return;
		}
		KeyLock l = stack.get(Doors.LOCK);
		if (l == null || l.lock().isEmpty()) {
			textConsumer.accept(Text.translatable("item.medievalships.cle.vierge").formatted(Formatting.GRAY));
			return;
		}
		textConsumer.accept(Text.translatable("item.medievalships.cle.ouvre", l.label().isEmpty() ? "?" : l.label()).formatted(Formatting.GOLD));
		if (l.door().isEmpty()) {
			// a key of 1.32.0: bound to the first door of its lock it opens
			textConsumer.accept(Text.translatable("item.medievalships.cle.ancienne").formatted(Formatting.GRAY));
		}
		if (type.isAdvanced()) {
			textConsumer.accept(Text.translatable("item.medievalships.cle.serrure", l.lock()).formatted(Formatting.DARK_GRAY));
			if (!l.door().isEmpty()) {
				textConsumer.accept(Text.translatable("item.medievalships.cle.porte", l.door()).formatted(Formatting.DARK_GRAY));
			}
		}
	}
}
