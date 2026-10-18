package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The steampunk airship ({@code medievalships:steampunk_airship}). */
public class SteampunkAirshipEntity extends ShipEntity {
	public SteampunkAirshipEntity(EntityType<? extends SteampunkAirshipEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.STEAMPUNK_AIRSHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.STEAMPUNK_AIRSHIP_ITEM;
	}
}
