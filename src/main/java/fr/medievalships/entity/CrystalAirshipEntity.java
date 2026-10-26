package fr.medievalships.entity;

import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.world.World;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.ShipType;
import fr.medievalships.core.Ships;

/** The Crystal Airship ({@code medievalships:crystal_airship}, "Le Grand Dirigeable de Cristal"). */
public class CrystalAirshipEntity extends ShipEntity {
	public CrystalAirshipEntity(EntityType<? extends CrystalAirshipEntity> type, World world) {
		super(type, world);
	}

	/**
	 * Players walk in its rooms and climb its stairs while it flies, climbs and turns: its hull follows the server
	 * without the vanilla glide, so the decks the players stand on are where the server has them.
	 */
	@Override
	protected boolean followsServerExactly() {
		return true;
	}

	@Override
	public ShipType shipType() {
		return Ships.CRYSTAL_AIRSHIP;
	}

	@Override
	public Item item() {
		return MedievalShips.CRYSTAL_AIRSHIP_ITEM;
	}
}
