package fr.medievalships.client.render;

import net.minecraft.client.render.entity.state.EntityRenderState;

public class ShipRenderState extends EntityRenderState {
	public float yaw;
	public float oarTime;
	public float oarWeight;
	public float wheelTime;
	public float sailOpen;
	public float helm;
	public float speed;
	public float rockTime;
	public double rockScale;
	/** Aircraft: -1 descending .. 1 climbing (fins). */
	public float climb;
	/** Vessels with rooms: the rooms are lit by the vessel's lamps. */
	public boolean interiorLight;
	/** Vessels with rooms: opening of each door (0 closed .. 1 open). */
	public final float[] doors = new float[fr.medievalships.core.InteriorGrid.MAX_DOORS];
	/** Vessels with rooms: salon shutters (0 open .. 1 closed), airlock water level, fittings switched on. */
	public float shutters;
	public float airlockWater;
	public boolean floodlight;
	public boolean lightsOff;
	public boolean lifeboatAway;
}
