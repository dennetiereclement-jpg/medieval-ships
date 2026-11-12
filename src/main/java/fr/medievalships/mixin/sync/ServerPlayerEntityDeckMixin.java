package fr.medievalships.mixin.sync;

import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;

import net.minecraft.server.network.ServerPlayerEntity;

import fr.medievalships.entity.DeckSync;

/**
 * The deck state of a player (1.30.0, see {@link DeckSync}) lives in the player entity itself: a new entity (respawn,
 * another character of a multi-character mod under the same account) starts without any, nothing leaks.
 */
@Mixin(ServerPlayerEntity.class)
abstract class ServerPlayerEntityDeckMixin implements DeckSync.Holder {
	@Unique
	@Nullable
	private DeckSync.State medievalships$deckState;

	@Override
	@Nullable
	public DeckSync.State medievalships$deck() {
		return medievalships$deckState;
	}

	@Override
	public void medievalships$setDeck(@Nullable DeckSync.State state) {
		medievalships$deckState = state;
	}
}
