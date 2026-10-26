package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Rustic Skyskiff ({@code medievalships:rustic_skiff}). */
public class RusticSkiffEntity extends ShipEntity {
	public RusticSkiffEntity(EntityType<? extends RusticSkiffEntity> type, World world) {
		super(type, world);
	}

	/**
	 * Players walk on its decks and in its rooms while it flies, climbs and turns (nimbly): its hull follows the server
	 * without the vanilla glide, so the decks the players stand on are where the server has them.
	 */
	@Override
	protected boolean followsServerExactly() {
		return true;
	}

	@Override
	public ShipType shipType() {
		return Ships.RUSTIC_SKIFF;
	}

	@Override
	public Item item() {
		return MedievalShips.RUSTIC_SKIFF_ITEM;
	}
}
