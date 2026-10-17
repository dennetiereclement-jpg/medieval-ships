package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The great warship ({@code medievalships:warship}). */
public class WarshipEntity extends ShipEntity {
	public WarshipEntity(EntityType<? extends WarshipEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.WARSHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.WARSHIP_ITEM;
	}
}
