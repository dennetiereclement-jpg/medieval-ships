package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Nautilus of Captain Nemo ({@code medievalships:nautilus}). */
public class NautilusEntity extends ShipEntity {
	public NautilusEntity(EntityType<? extends NautilusEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.NAUTILUS;
	}

	@Override
	public Item item() {
		return MedievalShips.NAUTILUS_ITEM;
	}
}
