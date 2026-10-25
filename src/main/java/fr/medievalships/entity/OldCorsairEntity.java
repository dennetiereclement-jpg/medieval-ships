package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Old Corsair ({@code medievalships:old_corsair}). */
public class OldCorsairEntity extends ShipEntity {
	public OldCorsairEntity(EntityType<? extends OldCorsairEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.OLD_CORSAIR;
	}

	@Override
	public Item item() {
		return MedievalShips.OLD_CORSAIR_ITEM;
	}
}
