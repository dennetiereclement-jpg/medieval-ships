package fr.medievalships.client;

import java.util.List;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.render.RenderTickCounter;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.world.Heightmap;

import fr.medievalships.core.GotoRoutes;
import fr.medievalships.core.PilotHud;
import fr.medievalships.core.ShipConfig;
import fr.medievalships.core.ShipGeometry;
import fr.medievalships.core.ShipPose;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * The pilot's panel, top left of the screen: see {@link PilotHud}. Only for the local player at the helm (and, while
 * the autopilot steers, for the player standing by the helm); hidden with the HUD (F1) and under the debug screen.
 */
public final class PilotHudOverlay {
	/** Distance from the helm within which a player sees the panel while the autopilot steers. */
	private static final double NEAR_HELM = 4.0;
	private static final int TITLE_COLOR = 0xFFFFC34D;
	private static final int TEXT_COLOR = 0xFFF2F2F2;
	private static final int KEYS_COLOR = 0xFFAAAAAA;
	private static final int BACKGROUND = 0x90000000;

	private static volatile List<String> lines = List.of();

	private PilotHudOverlay() {
	}

	/** The lines shown to the local player (empty: no panel). */
	public static List<String> lines() {
		return lines;
	}

	/** Client tick: what the panel shows. */
	static void tick(MinecraftClient client, ClientWorld world) {
		lines = compute(client, world);
	}

	private static List<String> compute(MinecraftClient client, ClientWorld world) {
		ClientPlayerEntity player = client.player;
		if (player == null || player.isSpectator()) {
			return List.of();
		}
		ShipEntity ship = null;
		boolean atHelm = false;
		if (player.getVehicle() instanceof ShipEntity riding && riding.seatOf(player) == ShipGeometry.PILOT_SEAT) {
			ship = riding;
			atHelm = true;
		} else {
			ShipEntity aboard = player.getVehicle() instanceof ShipEntity riding ? riding : ShipTracker.shipUnder(player);
			if (aboard != null && !aboard.isRemoved() && aboard.autopilotActive() && nearHelm(aboard, player)) {
				ship = aboard;
			}
		}
		if (ship == null || ship.isRemoved()) {
			return List.of();
		}
		ShipGeometry g = ship.geometry();
		ShipConfig cfg = ship.config();
		PilotHud.Status s = new PilotHud.Status();
		s.vessel = ship.hasCustomName() ? ship.getCustomName().getString() : capitalize(ship.shipType().frenchName());
		s.kind = g.flying() ? PilotHud.Kind.AIRCRAFT : g.submarine() ? PilotHud.Kind.SUBMARINE : PilotHud.Kind.SHIP;
		s.speed = ship.syncedSpeed();
		s.slowSpeed = cfg.slowSpeed;
		s.normalSpeed = cfg.normalSpeed;
		s.fastSpeed = cfg.fastSpeed;
		s.gait = ship.gait().frenchName();
		s.verticalSpeed = ship.syncedVerticalSpeed();
		s.deckY = ship.getY() + g.hull().mainDeckY;
		int bx = (int) Math.floor(ship.getX()), bz = (int) Math.floor(ship.getZ());
		if (world.isChunkLoaded(bx >> 4, bz >> 4)) {
			s.groundClearance = ship.getY() + g.lowestY() - world.getTopY(Heightmap.Type.MOTION_BLOCKING, bx, bz);
		}
		s.depth = ship.syncedDepth();
		s.autopilot = ship.autopilotActive();
		s.atHelm = atHelm;
		String[] info = ship.syncedAutopilotInfo().split(";", -1);
		if (s.autopilot && info.length >= 6) {
			s.autopilotPhase = info[0];
			s.autopilotGoto = GotoRoutes.isGoto(info[1]);
			s.autopilotTarget = info[2];
			try {
				s.autopilotDistance = Math.hypot(Double.parseDouble(info[3]) - ship.getX(), Double.parseDouble(info[5]) - ship.getZ());
			} catch (NumberFormatException e) {
				s.autopilotDistance = Double.NaN;
			}
		}
		return PilotHud.lines(s);
	}

	private static boolean nearHelm(ShipEntity ship, ClientPlayerEntity player) {
		ShipGeometry.Seat helm = ship.geometry().seats().get(ShipGeometry.PILOT_SEAT);
		ShipPose pose = ship.pose();
		double[] l = pose.toLocal(player.getX(), player.getY(), player.getZ());
		double dx = l[0] - helm.x(), dy = l[1] - helm.y(), dz = l[2] - helm.z();
		return dx * dx + dy * dy + dz * dz < NEAR_HELM * NEAR_HELM;
	}

	private static String capitalize(String s) {
		return s == null || s.isEmpty() ? "" : Character.toUpperCase(s.charAt(0)) + s.substring(1);
	}

	/** HUD element: a small dark panel, the vessel's name, the values, the keys. */
	static void render(DrawContext context, RenderTickCounter tickCounter) {
		List<String> l = lines;
		MinecraftClient client = MinecraftClient.getInstance();
		if (l.isEmpty() || client.options.hudHidden || client.inGameHud.getDebugHud().shouldShowDebugHud()) {
			return;
		}
		TextRenderer font = client.textRenderer;
		int width = 0;
		for (String line : l) {
			width = Math.max(width, font.getWidth(line));
		}
		int x = 6, y = 6, step = font.fontHeight + 2;
		context.fill(x - 4, y - 4, x + width + 4, y + l.size() * step + 1, BACKGROUND);
		for (int i = 0; i < l.size(); i++) {
			String line = l.get(i);
			int color = i == 0 ? TITLE_COLOR : line.startsWith("[") ? KEYS_COLOR : TEXT_COLOR;
			context.drawTextWithShadow(font, line, x, y + i * step, color);
		}
	}
}
