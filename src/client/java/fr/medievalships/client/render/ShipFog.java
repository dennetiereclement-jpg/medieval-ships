package fr.medievalships.client.render;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.Camera;
import net.minecraft.fluid.FluidState;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

import fr.medievalships.entity.ShipInteriors;

/** The view from the rooms of a submerged vessel: the sea behind the glass is fogged as for a swimmer. */
public final class ShipFog {
	/** Distance (blocks) the fog leaves clear: a room is seen as it is. */
	public static final float CLEAR_DISTANCE = 5f;
	/** Distance at which the sea fog hides everything. */
	public static final float END_DISTANCE = 36f;

	private ShipFog() {
	}

	/** Is the camera in a dry compartment of a vessel, under the surface of the water around it? */
	public static boolean inDryRoomUnderWater(Camera camera) {
		MinecraftClient client = MinecraftClient.getInstance();
		if (client.world == null) {
			return false;
		}
		Vec3d p = camera.getCameraPos();
		BlockPos pos = BlockPos.ofFloored(p);
		FluidState fluid = client.world.getFluidState(pos);
		if (!fluid.isIn(FluidTags.WATER) || p.y > pos.getY() + fluid.getHeight(client.world, pos)) {
			return false;
		}
		return ShipInteriors.dryAt(client.world, p.x, p.y, p.z);
	}
}
