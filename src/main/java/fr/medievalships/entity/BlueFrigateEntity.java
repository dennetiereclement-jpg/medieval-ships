package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Blue-Sailed Frigate ({@code medievalships:blue_frigate}). */
public class BlueFrigateEntity extends ShipEntity {
	public BlueFrigateEntity(EntityType<? extends BlueFrigateEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.BLUE_FRIGATE;
	}

	@Override
	public Item item() {
		return MedievalShips.BLUE_FRIGATE_ITEM;
	}
}
