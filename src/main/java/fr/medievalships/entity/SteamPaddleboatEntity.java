package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The armoured steam paddleboat ({@code medievalships:steam_paddleboat}). */
public class SteamPaddleboatEntity extends ShipEntity {
	public SteamPaddleboatEntity(EntityType<? extends SteamPaddleboatEntity> type, World world) {
		super(type, world);
	}

	@Override
	public ShipType shipType() {
		return Ships.STEAM_PADDLEBOAT;
	}

	@Override
	public Item item() {
		return MedievalShips.STEAM_PADDLEBOAT_ITEM;
	}
}
