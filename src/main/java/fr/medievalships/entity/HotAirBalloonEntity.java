package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The steampunk hot-air balloon ({@code medievalships:hot_air_balloon}). */
public class HotAirBalloonEntity extends ShipEntity {
	public HotAirBalloonEntity(EntityType<? extends HotAirBalloonEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.HOT_AIR_BALLOON;
	}

	@Override
	public Item item() {
		return MedievalShips.HOT_AIR_BALLOON_ITEM;
	}
}
