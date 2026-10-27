package fr.medievalships.client;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.render.LightmapTextureManager;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.RotationAxis;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.client.model.BbModel;
import fr.medievalships.client.render.ShipModels;
import fr.medievalships.core.InteriorDecor;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.data.SyncedConfig;
import fr.medievalships.entity.ShipPlacement;
import fr.medievalships.item.ShipItem;

/**
 * Placement preview: while the local player holds the item of a vessel, a translucent ghost of its model is drawn
 * where a right click would put it, facing where the player looks, green if it fits and red if it does not (grey if
 * the server's config does not let this player place it). The spot and the space check are the server's own
 * ({@link ShipItem#placementTarget}, {@link ShipPlacement.Aim}, {@link ShipPlacement#find}), run on the client world
 * with the server's altitude ceiling: aiming at the same block face with the same heading (rounded to
 * {@link ShipPlacement#YAW_STEP} degrees) both compute exactly the same spot. Cheap: only for the local player,
 * recomputed when the aimed face or the rounded heading changes (and twice a second, the world may change), only the
 * hull and its exterior drawn (no rooms, furniture or small details).
 */
public final class PlacementPreview {
	/**
	 * What the preview shows: the vessel, where it would go, whether it fits, whether this player may place it, and
	 * the aimed point and heading it is for (rounded as for the click).
	 */
	public record State(ShipType type, ShipPose pose, boolean valid, boolean allowed, double hitX, double hitY, double hitZ, float yaw) {
	}

	/** Recompute at most this often while aiming at the same face with the same heading (the world may change). */
	private static final int REFRESH_TICKS = 10;
	private static final double MAX_DISTANCE = 160.0;
	/** Translucent tints (ARGB) of the ghost. */
	public static final int FITS_COLOR = 0x8C59FF6A;
	public static final int BLOCKED_COLOR = 0x8CFF3B3B;
	public static final int FORBIDDEN_COLOR = 0x8C808080;
	/**
	 * Not allowed: the ghost is also washed toward white by the entity overlay (the creeper's flash; u = 8 of 15 mixes
	 * 40 % white in), so it reads as a greyed-out vessel rather than a real one in the shade.
	 */
	private static final int FORBIDDEN_OVERLAY = OverlayTexture.packUv(8, OverlayTexture.getV(false));
	private static final String[] HIDDEN_BONES = {"rooms", "furniture", "fittings", "detail"};

	@Nullable
	private static volatile State current;
	private static String lastKey = "";
	private static int age;
	/** The bar message shown for the current preview (0 fits, 1 does not fit, 2 not allowed), -1 none. */
	private static int shownMessage = -1;

	private PlacementPreview() {
	}

	/** The preview being shown, or null. */
	@Nullable
	public static State current() {
		return current;
	}

	/**
	 * The vessel a right click would place, or null: the item in the main hand, or the one in the other hand when the
	 * main hand is empty (with something else in the main hand, that is what a right click uses).
	 */
	@Nullable
	static ShipType heldType(ClientPlayerEntity player) {
		ItemStack main = player.getMainHandStack();
		if (main.getItem() instanceof ShipItem item) {
			return item.shipType();
		}
		return main.isEmpty() && player.getOffHandStack().getItem() instanceof ShipItem item ? item.shipType() : null;
	}

	/** Client tick: where would the held vessel go? */
	static void tick(MinecraftClient client, ClientWorld world) {
		ClientPlayerEntity player = client.player;
		ShipType type = player == null || player.isSpectator() ? null : heldType(player);
		// aiming at a ship: a right click talks to that ship, it places nothing
		if (type == null || ShipPicker.current() != null) {
			clear();
			return;
		}
		BlockHitResult hit = ShipItem.placementTarget(world, player, type);
		if (hit == null) {
			clear();
			return;
		}
		ShipPlacement.Aim aim = ShipPlacement.Aim.of(hit, player.getYaw());
		boolean allowed = SyncedConfig.mayPlace(player, type);
		// keyed on the rounded aim itself: two faces of one block on the same side (stairs, slabs) are two spots
		String key = type.id() + ":" + aim + ":" + allowed;
		if (key.equals(lastKey) && ++age < REFRESH_TICKS && current != null) {
			return;
		}
		lastKey = key;
		age = 0;
		ShipPlacement.Spot spot = ShipPlacement.find(world, type, aim.x(), aim.y(), aim.z(), aim.yaw(), true,
				SyncedConfig.vessel(type).maxAltitude());
		State s = spot == null ? null : new State(type, spot.pose(), spot.valid(), allowed, aim.x(), aim.y(), aim.z(), aim.yaw());
		current = s;
		int message = s == null ? -1 : !s.allowed() ? 2 : s.valid() ? 0 : 1;
		if (s != null && message != shownMessage) {
			shownMessage = message;
			client.inGameHud.setOverlayMessage(switch (message) {
				case 0 -> Text.literal("Clic droit : placer ici (" + type.frenchName() + ")").formatted(Formatting.GREEN);
				case 1 -> Text.literal("Pas assez d'espace libre ici (" + type.frenchName() + ")").formatted(Formatting.RED);
				default -> Text.literal("Placement non autorisé : réservé aux administrateurs (" + type.frenchName() + ")")
						.formatted(Formatting.GRAY);
			}, false);
		}
	}

	private static void clear() {
		current = null;
		lastKey = "";
		shownMessage = -1;
	}

	/** World rendering (before the entities): the translucent ghost. */
	static void render(WorldRenderContext context) {
		State s = current;
		if (s == null) {
			return;
		}
		ShipModels.Visual visual = ShipModels.of(s.type());
		BbModel model = visual == null ? null : ShipModels.get(visual);
		MinecraftClient client = MinecraftClient.getInstance();
		if (model == null || client.gameRenderer == null || client.gameRenderer.getCamera() == null) {
			return;
		}
		Vec3d cam = client.gameRenderer.getCamera().getCameraPos();
		ShipPose pose = s.pose();
		if (cam.squaredDistanceTo(pose.x(), pose.y(), pose.z()) > MAX_DISTANCE * MAX_DISTANCE) {
			return;
		}
		MatrixStack matrices = context.matrices();
		matrices.push();
		matrices.translate(pose.x() - cam.x, pose.y() - cam.y, pose.z() - cam.z);
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees((float) -pose.yaw()));
		int color = !s.allowed() ? FORBIDDEN_COLOR : s.valid() ? FITS_COLOR : BLOCKED_COLOR;
		int overlay = !s.allowed() ? FORBIDDEN_OVERLAY : OverlayTexture.DEFAULT_UV;
		int light = LightmapTextureManager.MAX_LIGHT_COORDINATE;
		InteriorDecor decor = s.type().geometry().decor();
		int textures = Math.min(model.textureCount(), visual.textures().size());
		for (int tex = 0; tex < textures; tex++) {
			int texture = visual.textures().size() > 1 ? tex : -1;
			RenderLayer layer = RenderLayers.entityTranslucent(visual.textures().get(tex));
			context.commandQueue().submitCustom(matrices, layer, (entry, vertices) -> {
				BbModel.Pose bp = model.newPose();
				for (String bone : HIDDEN_BONES) {
					model.hide(bp, bone);
				}
				if (decor != null) {
					for (InteriorDecor.Block b : decor.blocks()) {
						model.hide(bp, b.fallback());
					}
				}
				model.render(bp, texture, (p, uv, n, glow) -> {
					for (int k = 0; k < 4; k++) {
						vertices.vertex(entry, p[k * 3], p[k * 3 + 1], p[k * 3 + 2])
								.color(color)
								.texture(uv[k * 2], uv[k * 2 + 1])
								.overlay(overlay)
								.light(light)
								.normal(entry, n[0], n[1], n[2]);
					}
				});
			});
		}
		matrices.pop();
	}
}
