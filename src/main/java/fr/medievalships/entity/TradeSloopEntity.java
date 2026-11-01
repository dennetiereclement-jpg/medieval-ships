package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The trade sloop ({@code medievalships:trade_sloop}). */
public class TradeSloopEntity extends ShipEntity {
	public TradeSloopEntity(EntityType<? extends TradeSloopEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.TRADE_SLOOP;
	}

	@Override
	public Item item() {
		return MedievalShips.TRADE_SLOOP_ITEM;
	}
}
