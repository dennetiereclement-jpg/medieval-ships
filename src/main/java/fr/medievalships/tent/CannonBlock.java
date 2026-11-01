package fr.medievalships.tent;

import com.mojang.serialization.MapCodec;
import org.jetbrains.annotations.Nullable;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.util.ActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

import fr.medievalships.core.TentType;

/**
 * The anchor block of a cannon (the medieval cannon, {@code medievalships:canon_medieval}): a {@link TentBlock} (the
 * model drawn by the block entity renderer, collision boxes through {@link TentCollisions}, FACING = the breech's
 * side, towards the player who placed it, so the muzzle points where that player was looking; no tick) whose block
 * entity is a {@link CannonBlockEntity} with a persisted {@link fr.medievalships.core.CannonState}.
 *
 * <p>The firing is not written yet; its extension points are here and in the block entity (see docs/TENTES.md,
 * "Canon médiéval : architecture du tir"):
 * <ul>
 * <li>{@link #onUse}: right-click — today nothing ({@link ActionResult#PASS}); later: with a cannonball load, with
 * gunpowder ram a charge, with flint and steel light the fuse (set {@code fuseTicks}), all through
 * {@link CannonBlockEntity#setCannonState};</li>
 * <li>{@code getTicker}: not overridden (no ticker: a placed cannon costs nothing per tick); later a server ticker
 * returned only while the fuse burns ({@code CannonState.lit()}), counting down then firing;</li>
 * <li>the shot: smoke / flash particles and the sound at {@link CannonBlockEntity#muzzle()}, the projectile along
 * {@link CannonBlockEntity#muzzleDirection()} (the JSON's "muzzle" and "muzzle_dir"), the recoil animation on the
 * model's bones "barrel", "carriage", "wheel_left", "wheel_right".</li>
 * </ul>
 */
public class CannonBlock extends TentBlock {
	public CannonBlock(TentType type, AbstractBlock.Settings settings) {
		super(type, settings);
	}

	@Override
	protected MapCodec<? extends BlockWithEntity> getCodec() {
		TentType type = tentType();
		return AbstractBlock.createCodec(settings -> new CannonBlock(type, settings));
	}

	@Override
	@Nullable
	public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
		return new CannonBlockEntity(pos, state);
	}

	/** Right-click: nothing yet (the future load / ram / ignite actions plug in here). */
	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		return ActionResult.PASS;
	}
}
