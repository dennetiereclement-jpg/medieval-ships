package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Royal Lion Ship ({@code medievalships:royal_lion_ship}). */
public class RoyalLionShipEntity extends ShipEntity {
	public RoyalLionShipEntity(EntityType<? extends RoyalLionShipEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.ROYAL_LION_SHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.ROYAL_LION_SHIP_ITEM;
	}
}
