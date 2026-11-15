package fr.medievalships.forge;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.item.ItemStack;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.util.math.BlockPos;

/**
 * What the divine forge's interface shows (1.34.0), built by the server for one player ({@link ForgeRecipes#menu}) and
 * sent when the screen opens (the screen handler's opening data) and again after each click or when the player's
 * inventory changes ({@link ForgeMenuPayload}): the recipes are not sent to the clients in 1.21.11, so the list, the
 * ingredients owned and required, and the reasons a recipe is out of reach all come from here.
 *
 * @param pos          the forge's anchor block
 * @param busy         a crafting is under way (a new one is refused: "La forge est occupée")
 * @param busyMine     ...for this player
 * @param busyLabel    what is being made ("" at rest)
 * @param busyRemaining ticks left (0 at rest)
 * @param busyTotal    ticks of the whole crafting (0 at rest)
 * @param pending      items the forge keeps for this player (handed over at the next click)
 * @param entries      the recipes, sorted by category, order and name
 * @param notice       a line of news for the player (the outcome of their last click, the results handed over), or ""
 */
public record ForgeMenu(BlockPos pos, boolean busy, boolean busyMine, String busyLabel, int busyRemaining, int busyTotal, int pending,
		List<Entry> entries, String notice) {
	/** Most recipes sent (a server with more shows the first ones; the log says so). */
	public static final int MAX_ENTRIES = 512;

	/** One ingredient: a stack to show, a label (a tag's id, else empty), the quantity required and owned. */
	public record Ing(ItemStack icon, String label, int required, int owned) {
		public boolean enough() {
			return owned >= required;
		}
	}

	/**
	 * One recipe: its id (what the "Forger" button sends back, by index), its category (ordinal of
	 * {@link fr.medievalships.core.ForgeCategory}), the crafted stack, its name and description, the time (ticks), the
	 * ingredients, the requirements not met (French reasons) and whether the player can forge it now (requirements met
	 * and every ingredient paid, the forge's business aside).
	 */
	public record Entry(String id, int category, ItemStack result, String name, String description, int duration, List<Ing> ingredients,
			List<String> problems, boolean trial, boolean craftable) {
	}

	public static final PacketCodec<RegistryByteBuf, ForgeMenu> CODEC = PacketCodec.of(ForgeMenu::write, ForgeMenu::read);

	public void write(RegistryByteBuf buf) {
		buf.writeBlockPos(pos);
		buf.writeBoolean(busy);
		buf.writeBoolean(busyMine);
		buf.writeString(busyLabel);
		buf.writeVarInt(busyRemaining);
		buf.writeVarInt(busyTotal);
		buf.writeVarInt(pending);
		buf.writeString(notice);
		int n = Math.min(entries.size(), MAX_ENTRIES);
		buf.writeVarInt(n);
		for (int i = 0; i < n; i++) {
			Entry e = entries.get(i);
			buf.writeString(e.id());
			buf.writeVarInt(e.category());
			ItemStack.OPTIONAL_PACKET_CODEC.encode(buf, e.result());
			buf.writeString(e.name());
			buf.writeString(e.description());
			buf.writeVarInt(e.duration());
			buf.writeVarInt(e.ingredients().size());
			for (Ing g : e.ingredients()) {
				ItemStack.OPTIONAL_PACKET_CODEC.encode(buf, g.icon());
				buf.writeString(g.label());
				buf.writeVarInt(g.required());
				buf.writeVarInt(g.owned());
			}
			buf.writeVarInt(e.problems().size());
			for (String p : e.problems()) {
				buf.writeString(p);
			}
			buf.writeBoolean(e.trial());
			buf.writeBoolean(e.craftable());
		}
	}

	public static ForgeMenu read(RegistryByteBuf buf) {
		BlockPos pos = buf.readBlockPos();
		boolean busy = buf.readBoolean(), mine = buf.readBoolean();
		String label = buf.readString();
		int remaining = buf.readVarInt(), total = buf.readVarInt(), pending = buf.readVarInt();
		String notice = buf.readString();
		int n = Math.min(buf.readVarInt(), MAX_ENTRIES);
		List<Entry> entries = new ArrayList<>(n);
		for (int i = 0; i < n; i++) {
			String id = buf.readString();
			int category = buf.readVarInt();
			ItemStack result = ItemStack.OPTIONAL_PACKET_CODEC.decode(buf);
			String name = buf.readString(), description = buf.readString();
			int duration = buf.readVarInt();
			int ni = Math.min(buf.readVarInt(), 64);
			List<Ing> ings = new ArrayList<>(ni);
			for (int k = 0; k < ni; k++) {
				ItemStack icon = ItemStack.OPTIONAL_PACKET_CODEC.decode(buf);
				String l = buf.readString();
				int req = buf.readVarInt(), owned = buf.readVarInt();
				ings.add(new Ing(icon, l, req, owned));
			}
			int np = Math.min(buf.readVarInt(), 16);
			List<String> problems = new ArrayList<>(np);
			for (int k = 0; k < np; k++) {
				problems.add(buf.readString());
			}
			boolean trial = buf.readBoolean(), craftable = buf.readBoolean();
			entries.add(new Entry(id, category, result, name, description, duration, ings, problems, trial, craftable));
		}
		return new ForgeMenu(pos, busy, mine, label, remaining, total, pending, entries, notice);
	}

	/** The same menu with another line of news. */
	public ForgeMenu withNotice(String n) {
		return new ForgeMenu(pos, busy, busyMine, busyLabel, busyRemaining, busyTotal, pending, entries, n == null ? "" : n);
	}

	/** A short fingerprint of what changes while the screen is open (owned counts, business): resend only when it moves. */
	public long signature() {
		long h = 17;
		h = h * 31 + (busy ? 1 : 0);
		h = h * 31 + (busyMine ? 1 : 0);
		h = h * 31 + busyLabel.hashCode();
		h = h * 31 + busyTotal;
		h = h * 31 + pending;
		h = h * 31 + entries.size();
		for (Entry e : entries) {
			h = h * 31 + e.id().hashCode();
			h = h * 31 + (e.craftable() ? 1 : 0);
			h = h * 31 + e.problems().hashCode();
			for (Ing g : e.ingredients()) {
				h = h * 31 + g.owned();
			}
		}
		return h;
	}
}
