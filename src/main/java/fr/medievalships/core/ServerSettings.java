package fr.medievalships.core;

/** Settings shared by every ship ({@code "server"} section of {@code config/medievalships.json}). */
public final class ServerSettings {
	/** Announce departures / arrivals to players aboard and near the ship. */
	public boolean announceDepartures = true;
	public double announceRadius = 40.0;
	/** Keep the chunks around autopilot ships loaded so ferries run without players nearby. */
	public boolean chunkLoadAutopilotShips = true;
	public int chunkLoadRadius = 2;
	/** Permission level for /ship and for picking ships up. */
	public int adminPermissionLevel = 2;
	/** If true, only admins can place a ship with the item. */
	public boolean placeRequiresAdmin = false;

	public void sanitize() {
		announceRadius = Math.max(0, Math.min(512, Double.isNaN(announceRadius) ? 40 : announceRadius));
		chunkLoadRadius = Math.max(2, Math.min(4, chunkLoadRadius)); // below 2 the centre chunk does not tick entities
		adminPermissionLevel = Math.max(0, Math.min(4, adminPermissionLevel));
	}
}
