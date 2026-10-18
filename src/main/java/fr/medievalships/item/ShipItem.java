package fr.medievalships.item;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import net.minecraft.world.World;

import fr.medievalships.data.ConfigManager;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipPlacement;
import fr.medievalships.core.ShipType;

/** Right click on water to launch a ship, like a vanilla boat. One item per ship type. */
public class ShipItem extends Item {
	private final ShipType type;

	public ShipItem(ShipType type, Settings settings) {
		super(settings);
		this.type = type;
	}

	public ShipType shipType() {
		return type;
	}

	@Override
	public ActionResult use(World world, PlayerEntity user, Hand hand) {
		ItemStack stack = user.getStackInHand(hand);
		BlockHitResult hit = raycast(world, user, RaycastContext.FluidHandling.ANY);
		boolean flying = type.geometry().flying();
		// ships go on water; an aircraft is placed above whatever was clicked (ground, water, roof)
		if (hit.getType() != HitResult.Type.BLOCK || !flying && !world.getFluidState(hit.getBlockPos()).isIn(FluidTags.WATER)) {
			return ActionResult.PASS;
		}
		if (!(world instanceof ServerWorld serverWorld)) {
			return ActionResult.SUCCESS;
		}
		if (ConfigManager.server().placeRequiresAdmin && !ShipPermissions.isAdmin(user)) {
			user.sendMessage(Text.literal("Seuls les administrateurs peuvent mettre un navire à l'eau.").formatted(Formatting.RED), true);
			return ActionResult.FAIL;
		}
		Vec3d hitPos = hit.getPos();
		ShipEntity ship = ShipPlacement.place(serverWorld, type, hitPos.x, hitPos.y, hitPos.z, user.getYaw(), true);
		if (ship == null && flying) {
			user.sendMessage(Text.literal(String.format(java.util.Locale.ROOT,
					"Pas assez d'espace libre ici pour le dirigeable (%.0f blocs de long, %.0f de haut) : visez un endroit dégagé.",
					type.geometry().aiReach() + type.geometry().aiBack(), type.geometry().topY() - type.geometry().lowestY())).formatted(Formatting.RED), true);
			return ActionResult.FAIL;
		}
		if (ship == null) {
			user.sendMessage(Text.literal(String.format(java.util.Locale.ROOT, "Pas assez d'eau libre ici pour ce navire (%.0f x %.0f blocs, %.1f blocs de profondeur).", type.hull().tip * 2, type.hull().maxHalfWidth * 2 + 1, type.hull().waterlineY - type.hull().keelY(0) + 0.8)).formatted(Formatting.RED), true);
			return ActionResult.FAIL;
		}
		if (!user.isCreative()) {
			stack.decrement(1);
		}
		return ActionResult.SUCCESS_SERVER;
	}
}
