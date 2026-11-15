package fr.medievalships.forge;

import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;

/**
 * The screen handler of the divine forge's interface (1.34.0, type {@code medievalships:forge_divine}): no slot (the
 * forge pays from the player's inventory), only the list of {@link ForgeMenu} and the "Forger" button, sent as a vanilla
 * button click whose id is the recipe's index in the list the client got ({@link #onButtonClick}: the server checks
 * everything again in {@link ForgeRecipes#tryCraft}). While it is open the server sends the list again when it changes
 * (every second at most: the inventory, the forge's business), and closes it when the player walks away or the forge is
 * removed ({@link #canUse}).
 */
public class DivineForgeScreenHandler extends ScreenHandler {
	/** Ticks between two checks of what the open interface shows. */
	private static final int REFRESH_TICKS = 20;
	private final BlockPos pos;
	private final PlayerEntity player;
	private ForgeMenu menu;
	private long sentSignature;
	private int ticks;

	/** Both sides: the client from the opening data, the server with the menu it sent. */
	public DivineForgeScreenHandler(int syncId, PlayerInventory inventory, ForgeMenu menu) {
		this(syncId, inventory, menu, menu.pos());
	}

	public DivineForgeScreenHandler(int syncId, PlayerInventory inventory, ForgeMenu menu, BlockPos pos) {
		super(DivineForge.SCREEN_HANDLER, syncId);
		this.menu = menu;
		this.pos = pos;
		this.player = inventory.player;
		this.sentSignature = menu.signature();
	}

	/** What the interface shows now. */
	public ForgeMenu menu() {
		return menu;
	}

	public BlockPos pos() {
		return pos;
	}

	/** The client: a refreshed list from the server ({@link ForgeMenuPayload}). */
	public void setMenu(ForgeMenu menu) {
		this.menu = menu;
	}

	@Override
	public ItemStack quickMove(PlayerEntity player, int slot) {
		return ItemStack.EMPTY;
	}

	@Override
	public boolean canUse(PlayerEntity player) {
		DivineForgeBlockEntity forge = forge(player);
		return forge != null && ForgeRecipes.inReach(player, forge);
	}

	private DivineForgeBlockEntity forge(PlayerEntity p) {
		return p.getEntityWorld().getBlockEntity(pos) instanceof DivineForgeBlockEntity f ? f : null;
	}

	/** "Forger" on the recipe of index {@code id} in the list this player was sent. */
	@Override
	public boolean onButtonClick(PlayerEntity clicker, int id) {
		if (!(clicker instanceof ServerPlayerEntity sp)) {
			return false;
		}
		DivineForgeBlockEntity forge = forge(sp);
		if (forge == null || id < 0 || id >= menu.entries().size()) {
			return false;
		}
		ForgeRecipes.Outcome outcome = ForgeRecipes.tryCraft(sp, forge, menu.entries().get(id).id());
		sp.sendMessage(Text.literal(outcome.message()).formatted(outcome.started() ? Formatting.GOLD : Formatting.RED), true);
		send(sp, ForgeRecipes.menu(sp, forge, outcome.message()));
		return true;
	}

	/** The server, every tick while open: the list sent again when what it shows changed. */
	@Override
	public void sendContentUpdates() {
		super.sendContentUpdates();
		if (!(player instanceof ServerPlayerEntity sp) || ++ticks < REFRESH_TICKS) {
			return;
		}
		ticks = 0;
		DivineForgeBlockEntity forge = forge(sp);
		if (forge == null) {
			return;
		}
		ForgeMenu now = ForgeRecipes.menu(sp, forge, "");
		if (now.signature() != sentSignature) {
			send(sp, now.withNotice(menu.notice()));
		}
	}

	private void send(ServerPlayerEntity sp, ForgeMenu m) {
		menu = m;
		sentSignature = m.signature();
		if (ServerPlayNetworking.canSend(sp, ForgeMenuPayload.ID)) {
			ServerPlayNetworking.send(sp, new ForgeMenuPayload(syncId, m));
		}
	}
}
