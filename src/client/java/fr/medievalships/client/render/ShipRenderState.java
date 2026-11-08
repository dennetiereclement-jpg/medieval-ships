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
	/** Aircraft: bank into the turn (degrees, positive = right side down), drawn about the main deck's axis. */
	public float bank;
	public float bankPivotY;
	public boolean aircraft;
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
	/** The camera is in the dry rooms of this vessel, under the water: the sea behind the glass is murky. */
	public boolean murk;
	/** Gangplank: its spec (null: none), angle (degrees, down positive), lever position (0 stowed .. 1 deployed), out of its stowed place. */
	public fr.medievalships.core.Gangplank.Spec gangplank;
	public double gangplankAngle;
	public float gangplankLever;
	public boolean gangplankOut;
	/** 0 .. 1: moored by its gangplank, the drawn model stops rocking and bobbing. */
	public float moored;
}
