package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The medieval galley ({@code medievalships:galley}). */
public class GalleyEntity extends ShipEntity {
	public GalleyEntity(EntityType<? extends GalleyEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.GALLEY;
	}

	@Override
	public Item item() {
		return MedievalShips.GALLEY_ITEM;
	}
}
