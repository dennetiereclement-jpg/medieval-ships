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
}
