package fr.medievalships.core;

import java.util.Locale;

/** Text dump of every galley gameplay geometry value, used to prove refactors change nothing. */
final class GalleySnapshot {
	private GalleySnapshot() {
	}

	static String dump() {
		StringBuilder sb = new StringBuilder();
		ShipGeometry g = Ships.GALLEY.geometry();
		for (double[] p : g.probes()) {
			sb.append(String.format(Locale.ROOT, "probe %.4f %.4f %.4f%n", p[0], p[1], p[2]));
		}
		for (ShipGeometry.Seat s : g.seats()) {
			double[] d = s.dismountLocal();
			sb.append(String.format(Locale.ROOT, "seat %d %.4f %.4f %.4f %s %.4f %.4f %.4f%n", s.index(), s.x(), s.y(), s.z(), s.pilot(), d[0], d[1], d[2]));
		}
		double[] yaws = {0, 17.3, 45, 90, 133.7, 200, 271};
		for (double yaw : yaws) {
			ShipPose pose = new ShipPose(10.25, 62.889, -33.5, yaw);
			for (double qx = -12; qx <= 12; qx += 3.1) {
				for (double qz = -12; qz <= 12; qz += 3.1) {
					double[] w = pose.toWorld(qx, 0.4, qz);
					final StringBuilder line = new StringBuilder();
					g.collectBoxes(pose, w[0] - 0.4, w[1] - 1.5, w[2] - 0.4, w[0] + 0.4, w[1] + 1.9, w[2] + 0.4,
							(a, b, c, d, e, f) -> line.append(String.format(Locale.ROOT, "[%.4f %.4f %.4f %.4f %.4f %.4f]", a, b, c, d, e, f)));
					sb.append("boxes ").append(yaw).append(' ').append(qx).append(' ').append(qz).append(' ').append(line).append('\n');
				}
			}
			for (double ox = -8; ox <= 8; ox += 4) {
				for (double oz = -12; oz <= 12; oz += 6) {
					for (double[] dir : new double[][] {{1, -0.3, 0}, {-1, -0.2, 0.1}, {0, -1, 0}, {0.2, -0.5, 1}, {0, -0.4, -1}}) {
						double[] o = pose.toWorld(ox, 2.1, oz);
						ShipGeometry.Pick p = g.pick(pose, o[0], o[1], o[2], dir[0], dir[1], dir[2], 6);
						sb.append(p == null ? "pick null\n" : String.format(Locale.ROOT, "pick %s %d %.4f %.4f %.4f %.4f%n",
								p.kind(), p.seat(), p.distance(), p.lx(), p.ly(), p.lz()));
					}
				}
			}
		}
		for (double z = -11; z <= 11; z += 0.7) {
			for (double x = -3; x <= 3; x += 0.6) {
				for (double y = -2; y <= 5; y += 0.55) {
					sb.append(g.inCarryVolume(x, y, z) ? '1' : '0').append(g.insideHull(x, y, z) ? '1' : '0');
					double r = g.deckRescueY(x, y, z);
					sb.append(Double.isNaN(r) ? "n" : String.format(Locale.ROOT, "%.3f", r));
				}
				double[] b = g.boardingSpot(x * 2, z);
				sb.append(String.format(Locale.ROOT, " %.4f %.4f %.4f%n", b[0], b[1], b[2]));
			}
		}
		return sb.toString();
	}
}
