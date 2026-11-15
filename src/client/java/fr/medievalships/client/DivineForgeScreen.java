package fr.medievalships.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.Click;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.text.OrderedText;
import net.minecraft.text.Text;

import fr.medievalships.core.ForgeCategory;
import fr.medievalships.forge.DivineForgeScreenHandler;
import fr.medievalships.forge.ForgeMenu;
import fr.medievalships.forge.ForgeRecipes;

/**
 * The divine forge's interface (1.34.0), in French: on the left the recipes of a category ("Toutes les recettes" or one
 * of the five, chosen with the arrows) with the item each makes, greyed when it cannot be forged now; on the right the
 * selected recipe: its result, time and description, each ingredient owned / required (green when there is enough), the
 * requirements not met with their reason, and the "Forger" button (only when everything is there and the forge is
 * free). The header says whether the forge is at rest or crafting (what, the time left, a progress bar). Everything comes
 * from the server ({@link ForgeMenu}, refreshed after each click and when the inventory changes); the button sends the
 * recipe's index, and the server checks it all again.
 */
public class DivineForgeScreen extends HandledScreen<DivineForgeScreenHandler> {
	private static final int ROW = 18, LEFT_W = 130;
	private static final int BG = 0xF0201712, PANEL = 0xF02C2119, BORDER = 0xFFB8862E, ROW_SEL = 0xFF5A4322, ROW_HOVER = 0xFF3A2C1C;
	private static final int GOLD = 0xFFFFC94A, TEXT = 0xFFEDE3CC, GREY = 0xFF8C8273, RED = 0xFFFF6B5B, GREEN = 0xFF86DC7A, BAR = 0xFFFF9A2E;
	/** -1: every recipe; else the ordinal of a {@link ForgeCategory}. */
	private int category = -1;
	private String selected = "";
	private int scroll;
	private ButtonWidget forgeButton;
	private ForgeMenu lastMenu;
	private long menuTime;
	private ItemStack hoveredStack = ItemStack.EMPTY;
	private List<Text> hoveredText = List.of();

	public DivineForgeScreen(DivineForgeScreenHandler handler, PlayerInventory inventory, Text title) {
		super(handler, inventory, title);
	}

	@Override
	protected void init() {
		backgroundWidth = Math.min(340, width - 8);
		backgroundHeight = Math.min(210, height - 8);
		super.init();
		addDrawableChild(ButtonWidget.builder(Text.literal("<"), b -> cycle(-1)).dimensions(x + 6, y + 24, 14, 14).build());
		addDrawableChild(ButtonWidget.builder(Text.literal(">"), b -> cycle(1)).dimensions(x + 6 + LEFT_W - 14, y + 24, 14, 14).build());
		forgeButton = addDrawableChild(ButtonWidget.builder(Text.literal("Forger"), b -> forge())
				.dimensions(x + backgroundWidth - 6 - 76, y + backgroundHeight - 24, 76, 18).build());
	}

	private void cycle(int d) {
		int n = ForgeCategory.values().length + 1;
		category = Math.floorMod(category + 1 + d, n) - 1;
		scroll = 0;
		List<Integer> shown = shown();
		if (!shown.isEmpty() && shown.stream().noneMatch(i -> handler.menu().entries().get(i).id().equals(selected))) {
			selected = handler.menu().entries().get(shown.get(0)).id();
		}
	}

	/** Indices (in the menu's list) of the recipes of the chosen category. */
	private List<Integer> shown() {
		List<Integer> out = new ArrayList<>();
		List<ForgeMenu.Entry> all = handler.menu().entries();
		for (int i = 0; i < all.size(); i++) {
			if (category < 0 || all.get(i).category() == category) {
				out.add(i);
			}
		}
		return out;
	}

	private int selectedIndex() {
		List<ForgeMenu.Entry> all = handler.menu().entries();
		for (int i = 0; i < all.size(); i++) {
			if (all.get(i).id().equals(selected)) {
				return i;
			}
		}
		return -1;
	}

	private void forge() {
		int i = selectedIndex();
		if (i >= 0 && client != null && client.interactionManager != null) {
			client.interactionManager.clickButton(handler.syncId, i);
		}
	}

	/** Ticks left of the forge's crafting, counted down since the menu arrived. */
	private int remaining(ForgeMenu m) {
		if (m != lastMenu) {
			lastMenu = m;
			menuTime = client != null && client.world != null ? client.world.getTime() : 0;
		}
		long now = client != null && client.world != null ? client.world.getTime() : menuTime;
		return (int) Math.max(0, m.busyRemaining() - (now - menuTime));
	}

	@Override
	public void render(DrawContext context, int mouseX, int mouseY, float deltaTicks) {
		ForgeMenu m = handler.menu();
		if (selectedIndex() < 0) {
			List<Integer> shown = shown();
			selected = shown.isEmpty() ? "" : m.entries().get(shown.get(0)).id();
		}
		int sel = selectedIndex();
		forgeButton.active = sel >= 0 && m.entries().get(sel).craftable() && !m.busy();
		forgeButton.visible = sel >= 0;
		// the hovered stack or text was found by drawBackground, drawn before this (renderWithTooltip)
		super.render(context, mouseX, mouseY, deltaTicks);
		if (!hoveredStack.isEmpty()) {
			context.drawItemTooltip(textRenderer, hoveredStack, mouseX, mouseY);
		} else if (!hoveredText.isEmpty()) {
			context.drawTooltip(textRenderer, hoveredText, mouseX, mouseY);
		} else if (forgeButton.visible && !forgeButton.active && forgeButton.isMouseOver(mouseX, mouseY) && sel >= 0) {
			context.drawTooltip(textRenderer, Text.literal(m.busy() ? "La forge est occupée" : "Il manque des ingrédients ou une exigence"), mouseX,
					mouseY);
		}
	}

	@Override
	protected void drawForeground(DrawContext context, int mouseX, int mouseY) {
		// everything is drawn in drawBackground (absolute coordinates)
	}

	@Override
	protected void drawBackground(DrawContext context, float deltaTicks, int mouseX, int mouseY) {
		hoveredStack = ItemStack.EMPTY;
		hoveredText = List.of();
		ForgeMenu m = handler.menu();
		int w = backgroundWidth, h = backgroundHeight;
		context.fill(x - 1, y - 1, x + w + 1, y + h + 1, BORDER);
		context.fill(x, y, x + w, y + h, BG);
		// header: the title, the forge's state
		context.drawText(textRenderer, title, x + 6, y + 6, GOLD, true);
		String status;
		int rem = remaining(m);
		if (m.busy()) {
			status = (m.busyMine() ? "Votre commande : " : "En fabrication : ") + m.busyLabel() + " — " + ForgeRecipes.seconds(Math.max(1, rem));
		} else {
			status = "Au repos";
		}
		if (m.pending() > 0) {
			status += " · " + m.pending() + " objet(s) gardé(s) pour vous";
		}
		String st = textRenderer.trimToWidth(status, w - 20 - textRenderer.getWidth(title));
		context.drawText(textRenderer, st, x + w - 6 - textRenderer.getWidth(st), y + 6, m.busy() ? BAR : GREY, false);
		if (m.busy() && m.busyTotal() > 0) {
			double p = 1.0 - rem / (double) m.busyTotal();
			context.fill(x + 6, y + 17, x + w - 6, y + 20, 0xFF3A2A18);
			context.fill(x + 6, y + 17, x + 6 + (int) Math.round((w - 12) * Math.max(0, Math.min(1, p))), y + 20, BAR);
		}

		// left: the category and its recipes
		int lx = x + 6, top = y + 42, bottom = y + h - 6;
		String cat = category < 0 ? "Toutes les recettes" : ForgeCategory.byIndex(category).label();
		context.fill(lx + 15, y + 24, lx + LEFT_W - 15, y + 38, PANEL);
		String ct = textRenderer.trimToWidth(cat, LEFT_W - 34);
		context.drawText(textRenderer, ct, lx + LEFT_W / 2 - textRenderer.getWidth(ct) / 2, y + 27, GOLD, false);
		context.fill(lx, top, lx + LEFT_W, bottom, PANEL);
		List<Integer> shown = shown();
		int visible = Math.max(1, (bottom - top) / ROW);
		scroll = Math.max(0, Math.min(scroll, Math.max(0, shown.size() - visible)));
		if (shown.isEmpty()) {
			for (OrderedText line : textRenderer.wrapLines(Text.literal(m.entries().isEmpty()
					? "Aucune recette n'est chargée (voir docs/FORGE.md)." : "Aucune recette dans cette catégorie."), LEFT_W - 8)) {
				context.drawText(textRenderer, line, lx + 4, top + 4, GREY, false);
				top += 10;
			}
			top = y + 42;
		}
		context.enableScissor(lx, top, lx + LEFT_W, bottom);
		for (int k = 0; k < visible && scroll + k < shown.size(); k++) {
			int idx = shown.get(scroll + k);
			ForgeMenu.Entry e = m.entries().get(idx);
			int ry = top + k * ROW;
			boolean over = mouseX >= lx && mouseX < lx + LEFT_W && mouseY >= ry && mouseY < ry + ROW;
			if (e.id().equals(selected)) {
				context.fill(lx, ry, lx + LEFT_W, ry + ROW, ROW_SEL);
			} else if (over) {
				context.fill(lx, ry, lx + LEFT_W, ry + ROW, ROW_HOVER);
			}
			context.drawItem(e.result(), lx + 1, ry + 1);
			String name = textRenderer.trimToWidth(e.name(), LEFT_W - 22);
			context.drawText(textRenderer, name, lx + 20, ry + 5, e.craftable() ? TEXT : GREY, false);
			if (over && mouseX < lx + 18) {
				hoveredStack = e.result();
			}
		}
		context.disableScissor();
		if (shown.size() > visible) {
			int barH = Math.max(8, (bottom - top) * visible / shown.size());
			int barY = top + (bottom - top - barH) * scroll / Math.max(1, shown.size() - visible);
			context.fill(lx + LEFT_W - 2, barY, lx + LEFT_W, barY + barH, BORDER);
		}

		// right: the selected recipe
		int rx = lx + LEFT_W + 8, rw = x + w - 6 - rx;
		context.fill(rx - 2, y + 24, x + w - 6, y + h - 6, PANEL);
		int sel = selectedIndex();
		if (sel < 0) {
			context.drawText(textRenderer, "Choisissez une recette à gauche.", rx + 4, y + 30, GREY, false);
			drawNotice(context, m, rx, rw);
			return;
		}
		ForgeMenu.Entry e = m.entries().get(sel);
		int ty = y + 28;
		context.drawItem(e.result(), rx + 2, ty);
		context.drawStackOverlay(textRenderer, e.result(), rx + 2, ty);
		if (mouseX >= rx + 2 && mouseX < rx + 18 && mouseY >= ty && mouseY < ty + 16) {
			hoveredStack = e.result();
		}
		context.drawText(textRenderer, textRenderer.trimToWidth(e.name(), rw - 26), rx + 22, ty, GOLD, false);
		String sub = ForgeCategory.byIndex(e.category()).label() + " · " + ForgeRecipes.seconds(e.duration()) + (e.trial() ? " · recette d'essai" : "");
		context.drawText(textRenderer, textRenderer.trimToWidth(sub, rw - 26), rx + 22, ty + 9, GREY, false);
		ty += 20;
		if (!e.description().isEmpty()) {
			for (OrderedText line : textRenderer.wrapLines(Text.literal(e.description()), rw - 6)) {
				if (ty > y + h - 70) {
					break;
				}
				context.drawText(textRenderer, line, rx + 3, ty, TEXT, false);
				ty += 10;
			}
			ty += 2;
		}
		context.drawText(textRenderer, "Ingrédients (possédés / requis) :", rx + 3, ty, GOLD, false);
		ty += 11;
		for (ForgeMenu.Ing g : e.ingredients()) {
			if (ty > y + h - 44) {
				context.drawText(textRenderer, "…", rx + 3, ty, GREY, false);
				break;
			}
			context.drawItem(g.icon(), rx + 3, ty - 3);
			if (mouseX >= rx + 3 && mouseX < rx + 19 && mouseY >= ty - 3 && mouseY < ty + 13) {
				hoveredStack = g.icon();
				if (!g.label().isEmpty()) {
					hoveredStack = ItemStack.EMPTY;
					hoveredText = List.of(Text.literal("N'importe quel objet du tag " + g.label()), g.icon().getName());
				}
			}
			String what = g.label().isEmpty() ? g.icon().getName().getString() : g.label();
			String line = Math.min(g.owned(), 99_999) + " / " + g.required() + "  " + what;
			context.drawText(textRenderer, textRenderer.trimToWidth(line, rw - 26), rx + 23, ty + 1, g.enough() ? GREEN : RED, false);
			ty += ROW - 2;
		}
		for (String problem : e.problems()) {
			if (ty > y + h - 36) {
				break;
			}
			for (OrderedText line : textRenderer.wrapLines(Text.literal("✖ " + problem), rw - 6)) {
				context.drawText(textRenderer, line, rx + 3, ty, RED, false);
				ty += 10;
			}
		}
		drawNotice(context, m, rx, rw);
	}

	private void drawNotice(DrawContext context, ForgeMenu m, int rx, int rw) {
		if (!m.notice().isEmpty()) {
			List<OrderedText> lines = textRenderer.wrapLines(Text.literal(m.notice()), rw - 86);
			int ny = y + backgroundHeight - 24 + (lines.size() > 1 ? 0 : 5);
			for (int i = 0; i < Math.min(2, lines.size()); i++) {
				context.drawText(textRenderer, lines.get(i), rx + 3, ny + i * 10, m.notice().startsWith("La forge divine se met") ? GOLD : RED, false);
			}
		}
	}

	@Override
	public boolean mouseClicked(Click click, boolean doubled) {
		int lx = x + 6, top = y + 42, bottom = y + backgroundHeight - 6;
		double mx = click.x(), my = click.y();
		if (click.button() == 0 && mx >= lx && mx < lx + LEFT_W && my >= top && my < bottom) {
			List<Integer> shown = shown();
			int k = scroll + (int) ((my - top) / ROW);
			if (k >= 0 && k < shown.size()) {
				selected = handler.menu().entries().get(shown.get(k)).id();
			}
			return true;
		}
		return super.mouseClicked(click, doubled);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double horizontalAmount, double verticalAmount) {
		int lx = x + 6;
		if (mouseX >= lx && mouseX < lx + LEFT_W && mouseY >= y + 42 && mouseY < y + backgroundHeight - 6) {
			scroll = Math.max(0, scroll - (int) Math.signum(verticalAmount));
			return true;
		}
		return super.mouseScrolled(mouseX, mouseY, horizontalAmount, verticalAmount);
	}

	/** The client side of {@link fr.medievalships.forge.ForgeMenuPayload}: the open forge screen gets its new list. */
	public static void receive(int syncId, ForgeMenu menu) {
		net.minecraft.client.MinecraftClient mc = net.minecraft.client.MinecraftClient.getInstance();
		if (mc.player != null && mc.player.currentScreenHandler instanceof DivineForgeScreenHandler h && h.syncId == syncId) {
			h.setMenu(menu);
		}
	}
}
