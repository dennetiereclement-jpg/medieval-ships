package fr.medievalships.test;

import java.util.Locale;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;

import net.minecraft.client.MinecraftClient;
import net.minecraft.registry.tag.FluidTags;
import net.minecraft.util.math.BlockPos;

import fr.medievalships.client.render.DryWater;
import fr.medievalships.core.InteriorGrid;
import fr.medievalships.core.ShipPose;
import fr.medievalships.core.ShipType;
import fr.medievalships.entity.ShipEntity;
import fr.medievalships.entity.ShipTracker;

/**
 * In-game checks that the world's water is not drawn across the rooms of a vessel (1.28.0: {@link DryWater} on the
 * client, {@link InteriorGrid#hidesWater} for the rule), run from the ships' own scenarios once the vessel floats in its
 * basin: on the client, every water block of the basin within the hull's bounding box is sorted by the rule's samples
 * (wholly inside the hull, wholly in the open sea, straddling the outer hull) and asked of the chunk renderer's filter;
 * all the inside ones must be hidden and none of the open sea. The camera's submersion type is read too (the fog of a
 * dry room under the sea must be that of the air).
 */
final class DryWaterGameTest {
	private DryWaterGameTest() {
	}

	/**
	 * {inside, inside hidden, open sea, open sea hidden, straddling, straddling hidden} over the vessel's bounding box,
	 * counted on the client; null when the client has no such vessel.
	 */
	static int[] count(ClientGameTestContext context, ShipType type) {
		return context.computeOnClient((MinecraftClient mc) -> {
			ShipEntity ship = null;
			for (ShipEntity s : ShipTracker.ships(mc.world)) {
				if (!s.isRemoved() && s.shipType() == type) {
					ship = s;
					break;
				}
			}
			if (ship == null || ship.geometry().interior() == null) {
				return null;
			}
			InteriorGrid grid = ship.geometry().interior();
			ShipPose pose = ship.pose();
			InteriorGrid.State state = ship.interiorState();
			double r = ship.geometry().boundingRadius();
			int[] n = new int[6];
			BlockPos.Mutable pos = new BlockPos.Mutable();
			int y0 = (int) Math.floor(pose.y() + grid.y0) - 1, y1 = (int) Math.ceil(pose.y() + grid.y0 + grid.ny * grid.cell) + 1;
			for (int x = (int) Math.floor(pose.x() - r); x <= (int) Math.ceil(pose.x() + r); x++) {
				for (int z = (int) Math.floor(pose.z() - r); z <= (int) Math.ceil(pose.z() + r); z++) {
					for (int y = y0; y <= y1; y++) {
						pos.set(x, y, z);
						if (!mc.world.getFluidState(pos).isIn(FluidTags.WATER)) {
							continue;
						}
						int[] s = grid.waterSamples(pose, x, y, z, state);
						int k = s[0] == 0 && s[1] > 0 ? 0 : s[0] == 27 ? 2 : 4;
						n[k]++;
						if (DryWater.hidden(pos)) {
							n[k + 1]++;
						}
					}
				}
			}
			return n;
		});
	}

	/** The camera's submersion type, as the fog and the underwater overlay read it ("NONE" in the air and in a dry room). */
	static String cameraSubmersion(ClientGameTestContext context) {
		return context.computeOnClient((MinecraftClient mc) -> mc.gameRenderer.getCamera().getSubmersionType().name());
	}

	/** Logs the counts and checks them: every water block inside the hull hidden, none of the open sea. */
	static void check(ClientGameTestContext context, ShipType type, BiConsumer<Boolean, String> check, Consumer<String> log) {
		String id = type.id();
		int[] n = count(context, type);
		if (n == null) {
			check.accept(false, id + ": the client has the vessel and its interior grid for the water check");
			return;
		}
		log.accept(String.format(Locale.ROOT, "%s water blocks: %d inside the hull (%d hidden), %d in the open sea (%d hidden), %d straddling the hull (%d hidden)",
				id, n[0], n[1], n[2], n[3], n[4], n[5]));
		check.accept(n[0] > 0 && n[1] == n[0],
				String.format(Locale.ROOT, "%s: the world's water is not drawn inside the hull (%d / %d blocks hidden)", id, n[1], n[0]));
		check.accept(n[2] > 0 && n[3] == 0, String.format(Locale.ROOT, "%s: the sea around the hull is drawn (%d / %d blocks hidden)", id, n[3], n[2]));
	}

	/** Checks that the camera, in a dry room of the vessel, is not under water for the fog and the overlay. */
	static void checkCameraDry(ClientGameTestContext context, ShipType type, String where, BiConsumer<Boolean, String> check,
			Consumer<String> log) {
		String sub = cameraSubmersion(context);
		log.accept(String.format(Locale.ROOT, "%s camera in %s: submersion %s", type.id(), where, sub));
		check.accept("NONE".equals(sub), String.format(Locale.ROOT, "%s: no underwater fog or overlay in %s (camera %s)", type.id(), where, sub));
	}
}
