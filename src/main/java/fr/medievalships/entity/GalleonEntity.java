package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The great galleon ({@code medievalships:galleon}). */
public class GalleonEntity extends ShipEntity {
	public GalleonEntity(EntityType<? extends GalleonEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.GALLEON;
	}

	@Override
	public Item item() {
		return MedievalShips.GALLEON_ITEM;
	}
}
