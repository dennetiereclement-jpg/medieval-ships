package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Sky Leviathan ({@code medievalships:sky_leviathan}). */
public class SkyLeviathanEntity extends ShipEntity {
	public SkyLeviathanEntity(EntityType<? extends SkyLeviathanEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.SKY_LEVIATHAN;
	}

	@Override
	public Item item() {
		return MedievalShips.SKY_LEVIATHAN_ITEM;
	}
}
