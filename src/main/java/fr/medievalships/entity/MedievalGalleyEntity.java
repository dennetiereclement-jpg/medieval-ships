package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The red medieval galley ({@code medievalships:medieval_galley}). */
public class MedievalGalleyEntity extends ShipEntity {
	public MedievalGalleyEntity(EntityType<? extends MedievalGalleyEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.MEDIEVAL_GALLEY;
	}

	@Override
	public Item item() {
		return MedievalShips.MEDIEVAL_GALLEY_ITEM;
	}
}
