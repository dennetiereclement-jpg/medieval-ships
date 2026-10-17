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
import fr.medievalships.entity.GalleyEntity;
import fr.medievalships.entity.ShipPermissions;
import fr.medievalships.entity.ShipPlacement;

/** Right click on water to launch a galley, like a vanilla boat. */
public class GalleyItem extends Item {
	public GalleyItem(Settings settings) {
		super(settings);
	}

	@Override
	public ActionResult use(World world, PlayerEntity user, Hand hand) {
		ItemStack stack = user.getStackInHand(hand);
		BlockHitResult hit = raycast(world, user, RaycastContext.FluidHandling.ANY);
		if (hit.getType() != HitResult.Type.BLOCK || !world.getFluidState(hit.getBlockPos()).isIn(FluidTags.WATER)) {
			return ActionResult.PASS;
		}
		if (!(world instanceof ServerWorld serverWorld)) {
			return ActionResult.SUCCESS;
		}
		if (ConfigManager.get().placeRequiresAdmin && !ShipPermissions.isAdmin(user)) {
			user.sendMessage(Text.literal("Seuls les administrateurs peuvent mettre un navire à l'eau.").formatted(Formatting.RED), true);
			return ActionResult.FAIL;
		}
		Vec3d hitPos = hit.getPos();
		GalleyEntity ship = ShipPlacement.place(serverWorld, hitPos.x, hitPos.y, hitPos.z, user.getYaw(), true);
		if (ship == null) {
			user.sendMessage(Text.literal("Pas assez d'eau libre ici pour un navire de 22 blocs.").formatted(Formatting.RED), true);
			return ActionResult.FAIL;
		}
		if (!user.isCreative()) {
			stack.decrement(1);
		}
		return ActionResult.SUCCESS_SERVER;
	}
}
