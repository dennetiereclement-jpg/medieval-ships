package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Gear Steamship ({@code medievalships:gear_steamship}). */
public class GearSteamShipEntity extends ShipEntity {
	public GearSteamShipEntity(EntityType<? extends GearSteamShipEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.GEAR_STEAMSHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.GEAR_STEAMSHIP_ITEM;
	}
}
