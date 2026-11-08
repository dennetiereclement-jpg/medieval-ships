package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Fortress Ship ({@code medievalships:fortress_ship}). */
public class FortressShipEntity extends ShipEntity {
	public FortressShipEntity(EntityType<? extends FortressShipEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.FORTRESS_SHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.FORTRESS_SHIP_ITEM;
	}
}
