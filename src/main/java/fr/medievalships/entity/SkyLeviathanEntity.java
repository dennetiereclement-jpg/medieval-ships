package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Sky Leviathan ({@code medievalships:sky_leviathan}). */
public class SkyLeviathanEntity extends ShipEntity {
	public SkyLeviathanEntity(EntityType<? extends SkyLeviathanEntity> type, World world) {
		super(type, world);
	}

	/**
	 * Players walk in its rooms and climb its tower while it flies, climbs and turns: its hull follows the server
	 * without the vanilla glide, so the decks the players stand on are where the server has them.
	 */
	@Override
	protected boolean followsServerExactly() {
		return true;
	}

	@Override
	public ShipType shipType() {
		return Ships.SKY_LEVIATHAN;
	}

	@Override
	public Item item() {
		return MedievalShips.SKY_LEVIATHAN_ITEM;
	}
}
