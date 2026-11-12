package fr.medievalships.core;

/**
 * Deck coordinates shared by the clients and the server (1.30.0): what keeps several players glued to a moving deck,
 * for themselves and as seen by the others.
 *
 * <p>Every client draws a hull a few ticks behind the server's (network delay plus interpolation). A client carries its
 * own player with the hull it draws, so the world position it reports is right for <em>that</em> hull, not for the
 * server's one: under way the server copy of the player lagged behind on the deck by the ship's speed times that delay
 * (a block or two), and the other players saw him slide back and forth. The client therefore also reports the pose of
 * the hull it carries its player with (its <em>frame</em>): the server puts the player on the same spot of its own hull
 * ({@link #reframe}), and sends the other clients that spot in deck coordinates, which they place on the hull they draw.
 *
 * <p>Pure math, no Minecraft classes, no allocation in the per-tick paths (results go to a caller's array).
 */
public final class DeckFrame {
	/** Farthest a client's hull may be from the server's one for its frame to be believed (blocks). */
	public static final double MAX_FRAME_GAP = 48.0;
	/** Smallest change of the local position sent again to the other clients (blocks). */
	public static final double POS_EPSILON = 0.002;
	/** Smallest change of an angle sent again to the other clients (degrees). */
	public static final double ANGLE_EPSILON = 0.4;
	/** Ticks after which a player's deck position is sent again even if unchanged (lost packet, late tracker). */
	public static final int RESEND_TICKS = 20;
	/** Interpolation steps of the deck position of another player on the clients (vanilla interpolates over 3). */
	public static final int LERP_STEPS = 3;

	private DeckFrame() {
	}

	/** World point to the local point of a pose, written to {@code out[0..2]}. */
	public static void toLocal(ShipPose pose, double wx, double wy, double wz, double[] out) {
		double r = Math.toRadians(pose.yaw());
		double c = Math.cos(r), s = Math.sin(r);
		double dx = wx - pose.x(), dz = wz - pose.z();
		out[0] = dx * c + dz * s;
		out[1] = wy - pose.y();
		out[2] = -dx * s + dz * c;
	}

	/** Local point of a pose to the world, written to {@code out[0..2]}. */
	public static void toWorld(ShipPose pose, double lx, double ly, double lz, double[] out) {
		double r = Math.toRadians(pose.yaw());
		double c = Math.cos(r), s = Math.sin(r);
		out[0] = pose.x() + lx * c - lz * s;
		out[1] = pose.y() + ly;
		out[2] = pose.z() + lx * s + lz * c;
	}

	/**
	 * Where the server puts a position a client reported with the hull it drew at {@code client}: the same spot of
	 * the server's hull at {@code server}. Written to {@code out[0..2]}.
	 */
	public static void reframe(ShipPose client, ShipPose server, double x, double y, double z, double[] out) {
		toLocal(client, x, y, z, out);
		toWorld(server, out[0], out[1], out[2], out);
	}

	/** The yaw of a player turned with the hull from the client's frame to the server's. */
	public static float reframeYaw(ShipPose client, ShipPose server, float yaw) {
		return (float) (yaw + ShipPose.wrapDegrees(server.yaw() - client.yaw()));
	}

	/** Can a client's frame be believed: its hull near the server's one, every number finite? */
	public static boolean plausible(ShipPose client, ShipPose server) {
		if (!Double.isFinite(client.x()) || !Double.isFinite(client.y()) || !Double.isFinite(client.z()) || !Double.isFinite(client.yaw())) {
			return false;
		}
		double dx = client.x() - server.x(), dy = client.y() - server.y(), dz = client.z() - server.z();
		return dx * dx + dy * dy + dz * dz <= MAX_FRAME_GAP * MAX_FRAME_GAP;
	}

	/** Angle in (-180, 180]. */
	public static float wrap(double degrees) {
		return (float) ShipPose.wrapDegrees(degrees);
	}

	/**
	 * Must a deck position be sent again to the other clients? {@code last}: {x, y, z, yaw, head yaw, pitch} sent last
	 * (local, angles relative to the hull except the pitch).
	 */
	public static boolean changed(double[] last, double x, double y, double z, double yaw, double head, double pitch) {
		return Math.abs(last[0] - x) > POS_EPSILON || Math.abs(last[1] - y) > POS_EPSILON || Math.abs(last[2] - z) > POS_EPSILON
				|| Math.abs(ShipPose.wrapDegrees(last[3] - yaw)) > ANGLE_EPSILON || Math.abs(ShipPose.wrapDegrees(last[4] - head)) > ANGLE_EPSILON
				|| Math.abs(last[5] - pitch) > ANGLE_EPSILON;
	}

	/**
	 * Deck position of another player as a client draws it: interpolated towards the last one the server sent, in deck
	 * coordinates (so the hull's own motion never shows in it), one step per tick.
	 */
	public static final class Lerp {
		/** Current local position and angles (yaw and head yaw relative to the hull). */
		public double x, y, z;
		public float yaw, head, pitch;
		/** The previous tick's local position (the walking animation follows the walk on the deck only). */
		public double lastX, lastY, lastZ;
		private double tx, ty, tz;
		private float tyaw, thead, tpitch;
		private int steps;
		private boolean started;

		/** A new target from the server. */
		public void target(double x, double y, double z, float yaw, float head, float pitch) {
			tx = x;
			ty = y;
			tz = z;
			tyaw = yaw;
			thead = head;
			tpitch = pitch;
			steps = LERP_STEPS;
		}

		public boolean started() {
			return started;
		}

		/** Starts from where the entity is drawn now (no jump when a player steps aboard a moving ship). */
		public void start(double x, double y, double z, float yaw, float head, float pitch) {
			this.x = lastX = x;
			this.y = lastY = y;
			this.z = lastZ = z;
			this.yaw = yaw;
			this.head = head;
			this.pitch = pitch;
			started = true;
		}

		/** One tick of interpolation. */
		public void step() {
			lastX = x;
			lastY = y;
			lastZ = z;
			if (steps <= 0) {
				return;
			}
			double k = 1.0 / steps;
			x += (tx - x) * k;
			y += (ty - y) * k;
			z += (tz - z) * k;
			yaw = (float) (yaw + ShipPose.wrapDegrees(tyaw - yaw) * k);
			head = (float) (head + ShipPose.wrapDegrees(thead - head) * k);
			pitch = (float) (pitch + (tpitch - pitch) * k);
			steps--;
		}
	}
}
