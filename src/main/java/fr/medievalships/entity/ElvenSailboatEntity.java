package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The elven sailboat ({@code medievalships:elven_sailboat}). */
public class ElvenSailboatEntity extends ShipEntity {
	public ElvenSailboatEntity(EntityType<? extends ElvenSailboatEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.ELVEN_SAILBOAT;
	}

	@Override
	public Item item() {
		return MedievalShips.ELVEN_SAILBOAT_ITEM;
	}
}
