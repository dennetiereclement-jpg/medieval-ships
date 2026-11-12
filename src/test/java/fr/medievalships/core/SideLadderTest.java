package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.junit.jupiter.api.Test;

import fr.medievalships.client.model.BbModel;

/**
 * The side ladders (1.30.0): every water-going vessel with a deck above the water has at least one ladder on each side (two
 * on the long hulls), none on the rowboat and the aircraft; each ladder lies on the hull side of its model and of its
 * collision hull (never through either, never far off), hangs from the bulwark top over a deck down to 1.5 blocks under
 * the water, keeps clear of the gunports, the gangplank and the boats carried on deck; the climbing zone, the collision
 * slab and the mesh agree with it.
 *
 * <p>{@link #main} measures the profiles on the models and the collision hulls and prints the table of
 * {@link SideLadder} (run it after moving a spot or changing a hull).
 */
class SideLadderTest {
	/** The vessels that must have side ladders (the brief's list). */
	static final List<String> WATER_SHIPS = List.of("galley", "galleon", "warship", "medieval_galley", "steam_paddleboat", "elven_sailboat",
			"nautilus", "old_corsair", "blue_frigate", "trade_sloop", "royal_lion_ship", "fortress_ship", "gear_steamship");

	/** The spots: ship, side, z, half width, style; the top when it is not the hull side's own (NaN). */
	record Spot(String ship, int side, double z, double halfWidth, String style, double topOverride) {
		Spot(String ship, int side, double z, double halfWidth, String style) {
			this(ship, side, z, halfWidth, style, Double.NaN);
		}
	}

	static final List<Spot> SPOTS = new ArrayList<>();

	static void both(String ship, double z, double halfWidth, String style) {
		SPOTS.add(new Spot(ship, SideLadder.PORT, z, halfWidth, style));
		SPOTS.add(new Spot(ship, SideLadder.STARBOARD, z, halfWidth, style));
	}

	static {
		both("galley", 0.0, 0.4, "wood");
		SPOTS.add(new Spot("galleon", SideLadder.PORT, -4.5, 0.4, "dark_wood"));
		SPOTS.add(new Spot("galleon", SideLadder.STARBOARD, -2.0, 0.35, "dark_wood"));
		both("galleon", 9.5, 0.4, "dark_wood");
		both("warship", 1.8, 0.38, "dark_wood");
		both("warship", 21.0, 0.4, "dark_wood");
		both("medieval_galley", -3.0, 0.4, "wood");
		both("steam_paddleboat", 6.5, 0.4, "steel");
		both("elven_sailboat", 1.0, 0.4, "elven");
		// the Nautilus surfaced: up the round hull and the side of the casing to the casing deck
		for (double z : new double[] {-12.9, 11.9}) {
			SPOTS.add(new Spot("nautilus", SideLadder.PORT, z, 0.4, "copper", Ships.NautilusLayout.CASING_TOP_Y));
			SPOTS.add(new Spot("nautilus", SideLadder.STARBOARD, z, 0.4, "copper", Ships.NautilusLayout.CASING_TOP_Y));
		}
		both("old_corsair", -5.0, 0.4, "worn");
		both("old_corsair", 9.0, 0.4, "worn");
		both("blue_frigate", -2.5, 0.4, "dark_wood");
		both("blue_frigate", 9.5, 0.4, "dark_wood");
		both("trade_sloop", 0.0, 0.4, "wood");
		both("royal_lion_ship", -1.3, 0.35, "dark_wood");
		both("royal_lion_ship", 10.75, 0.35, "dark_wood");
		both("fortress_ship", -7.2, 0.4, "steel");
		both("fortress_ship", 7.6, 0.4, "steel");
		both("gear_steamship", 6.0, 0.4, "steel");
		both("gear_steamship", 13.0, 0.4, "steel");
	}

	/** Boats carried on deck or hung in davits (z ranges, ship-local), see the usable boats. */
	static final Map<String, double[]> BOATS = Map.of(
			"galleon", new double[] {4.28, 7.83},
			"warship", new double[] {4.59, 11.6},
			"old_corsair", new double[] {-20.3, -17.2},
			"trade_sloop", new double[] {-6.8, -6.5},
			"nautilus", new double[] {Ships.NautilusLayout.LIFEBOAT_Z - 2.5, Ships.NautilusLayout.LIFEBOAT_Z + 2.5});

	// ------------------------------------------------------------------ measuring

	static final double YB = 0.0625, ZB = 0.05;
	static final double GAP = 0.02;

	/** The outer skin of a model on one side: max outboard x per (z, y) bin. */
	static final class Skin {
		final double z0, y0;
		final int nz, ny;
		final double[] max;

		Skin(String id, int side) throws Exception {
			BbModel m;
			try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/" + id + ".bbmodel"))) {
				m = new BbModel(r);
			}
			List<float[]> quads = new ArrayList<>();
			m.render(m.newPose(), -1, (p, uv, n, glow) -> quads.add(p.clone()));
			double zMin = 1e9, zMax = -1e9, yMin = 1e9, yMax = -1e9;
			for (float[] p : quads) {
				for (int k = 0; k < 4; k++) {
					zMin = Math.min(zMin, p[k * 3 + 2]);
					zMax = Math.max(zMax, p[k * 3 + 2]);
					yMin = Math.min(yMin, p[k * 3 + 1]);
					yMax = Math.max(yMax, p[k * 3 + 1]);
				}
			}
			z0 = zMin - 1;
			y0 = yMin - 1;
			nz = (int) ((zMax - zMin + 2) / ZB) + 1;
			ny = (int) ((Math.min(yMax, 30) - yMin + 2) / YB) + 1;
			max = new double[nz * ny];
			java.util.Arrays.fill(max, Double.NEGATIVE_INFINITY);
			for (float[] p : quads) {
				double len = 0;
				for (int k = 0; k < 3; k++) {
					len = Math.max(len, Math.abs(p[k] - p[6 + k]) + Math.abs(p[3 + k] - p[9 + k]));
				}
				int sub = Math.max(2, Math.min(200, (int) Math.ceil(len / 0.025)));
				for (int u = 0; u <= sub; u++) {
					for (int v = 0; v <= sub; v++) {
						double fu = u / (double) sub, fv = v / (double) sub;
						double x = 0, y = 0, z = 0;
						for (int k = 0; k < 3; k++) {
							double a0 = p[k] + (p[3 + k] - p[k]) * fu;
							double a1 = p[9 + k] + (p[6 + k] - p[9 + k]) * fu;
							double q = a0 + (a1 - a0) * fv;
							if (k == 0) {
								x = q;
							} else if (k == 1) {
								y = q;
							} else {
								z = q;
							}
						}
						int iz = (int) Math.floor((z - z0) / ZB), iy = (int) Math.floor((y - y0) / YB);
						if (iz < 0 || iz >= nz || iy < 0 || iy >= ny) {
							continue;
						}
						double X = side * x;
						if (X > max[iz * ny + iy]) {
							max[iz * ny + iy] = X;
						}
					}
				}
			}
		}

		/** Max over the band [zc - hw, zc + hw] of (skin - slope (z - zc)) in the y bin of y. */
		double band(double zc, double hw, double slope, double y) {
			int iy = (int) Math.floor((y - y0) / YB);
			if (iy < 0 || iy >= ny) {
				return Double.NEGATIVE_INFINITY;
			}
			double best = Double.NEGATIVE_INFINITY;
			for (int iz = (int) Math.floor((zc - hw - z0) / ZB); iz <= (int) Math.floor((zc + hw - z0) / ZB); iz++) {
				double z = z0 + (iz + 0.5) * ZB;
				best = Math.max(best, max[iz * ny + iy] - slope * (z - zc));
			}
			return best;
		}
	}

	/** The collision hull on one side: per y bin, the outer face of the boxes across the band, and the boxes themselves. */
	static final class Collision {
		final List<double[]> boxes = new ArrayList<>();

		Collision(ShipGeometry g, double zc, double hw) {
			ShipPose pose = new ShipPose(0, 0, 0, 0);
			g.collectBoxes(pose, InteriorGrid.State.CLOSED, null, -40, -20, zc - hw, 40, 40, zc + hw,
					(a, b, c, d, e, f) -> boxes.add(new double[] {a, b, c, d, e, f}));
		}

		/** Outer face (outboard distance, minus the slope) of the boxes overlapping the band at height y, -inf if none. */
		double outer(int side, double zc, double hw, double slope, double y) {
			double best = Double.NEGATIVE_INFINITY;
			for (double[] b : boxes) {
				if (b[1] > y || b[4] <= y || b[5] <= zc - hw || b[2] >= zc + hw) {
					continue;
				}
				double X = side > 0 ? b[3] : -b[0];
				double z0 = Math.max(b[2], zc - hw), z1 = Math.min(b[5], zc + hw);
				best = Math.max(best, X - Math.min(slope * (z0 - zc), slope * (z1 - zc)));
			}
			return best;
		}

		/** Top of the highest box under {@code below} whose outer face is at most {@code maxX} (a deck inboard). */
		double floor(int side, double zc, double hw, double maxX, double below) {
			double best = Double.NEGATIVE_INFINITY;
			for (double[] b : boxes) {
				if (b[5] <= zc - hw || b[2] >= zc + hw || b[4] > below + 1e-6) {
					continue;
				}
				double X = side > 0 ? b[3] : -b[0];
				double in = side > 0 ? b[0] : -b[3];
				if (in < maxX && X > maxX - 2.5) {
					best = Math.max(best, b[4]);
				}
			}
			return best;
		}
	}

	/** Everything measured for one spot. */
	record Measure(Spot spot, double slope, double top, double deck, double[] profile, double gapTop) {
	}

	static final Map<String, Skin[]> SKINS = new HashMap<>();

	static Skin skin(String id, int side) throws Exception {
		Skin[] s = SKINS.computeIfAbsent(id, k -> new Skin[2]);
		int i = side > 0 ? 0 : 1;
		if (s[i] == null) {
			s[i] = new Skin(id, side);
		}
		return s[i];
	}

	static Measure measure(Spot spot) throws Exception {
		ShipType t = Ships.byId(spot.ship);
		ShipGeometry g = t.geometry();
		HullShape h = g.hull();
		double wl = h.waterlineY;
		Skin skin = skin(spot.ship, spot.side);
		double zc = spot.z, hw = spot.halfWidth;
		Collision col = new Collision(g, zc, hw + 0.05);
		// slope of the hull line in plan: the collision wall (open hulls) or the model's side (median over the heights)
		double slope;
		if (g.interior() == null) {
			slope = (h.halfWidth(zc + hw) - h.halfWidth(zc - hw)) / (2 * hw);
		} else {
			List<Double> ks = new ArrayList<>();
			for (double y = wl + 0.3; y < wl + 4; y += YB) {
				double l = skin.band(zc - hw * 2 / 3, hw / 3, 0, y), r = skin.band(zc + hw * 2 / 3, hw / 3, 0, y);
				if (Double.isFinite(l) && Double.isFinite(r)) {
					ks.add((r - l) / (hw * 4 / 3));
				}
			}
			ks.sort(Double::compare);
			slope = ks.isEmpty() ? 0 : ks.get(ks.size() / 2);
			slope = Math.round(slope * 100) / 100.0;
		}
		slope = Math.max(-0.6, Math.min(0.6, slope));
		// the top: walk up the collision side from the waterline while it does not step far inboard (a cell of a grid at
		// most: a curved side steps in by half a block at a time, a deck edge under a deckhouse by more)
		double prev = col.outer(spot.side, zc, hw, slope, wl);
		double top = wl;
		for (double y = wl; y < 30; y += YB) {
			double o = col.outer(spot.side, zc, hw, slope, y + YB / 2);
			if (!Double.isFinite(o) || o < prev - 0.6) {
				break;
			}
			prev = o;
			top = y + YB;
		}
		if (!Double.isNaN(spot.topOverride)) {
			top = spot.topOverride;
		}
		top = Math.round(top * 1000) / 1000.0;
		// the need: the running max of the collision side and the model's skin, from the top down to under the bottom
		double bottom = SideLadder.bottom(wl) - 1.0;
		int n = (int) Math.ceil((top - bottom) / YB) + 1;
		double[] ys = new double[n], need = new double[n];
		double run = Double.NEGATIVE_INFINITY;
		// the rail cap and handrails just over the top (the hooks lie over them)
		for (double y = top; y < top + 0.12; y += YB) {
			run = Math.max(run, skin.band(zc, hw, slope, y + YB / 2) + GAP);
		}
		for (int i = 0; i < n; i++) {
			double y = top - i * YB;
			double v = Math.max(col.outer(spot.side, zc, hw, slope, y - YB / 2), skin.band(zc, hw, slope, y - YB / 2) + GAP);
			run = Math.max(run, v);
			ys[i] = y;
			need[i] = run; // valid for the bin [y - YB, y]
		}
		// points every 0.25 at the value of the bin under them, then drop the points not needed (still >= the need, <= +0.06)
		List<double[]> pts = new ArrayList<>();
		int step = (int) Math.round(0.25 / YB);
		for (int i = 0; i < n; i += step) {
			int j = Math.min(n - 1, i + step - 1);
			pts.add(new double[] {ys[i], need[j]});
		}
		if (pts.get(pts.size() - 1)[0] > ys[n - 1] - YB) {
			pts.add(new double[] {ys[n - 1] - YB, need[n - 1]});
		}
		for (boolean removed = true; removed; ) {
			removed = false;
			for (int k = 1; k + 1 < pts.size(); k++) {
				double[] a = pts.get(k - 1), c = pts.get(k + 1);
				boolean ok = true;
				for (int i = 0; i < n && ok; i++) {
					double y0 = ys[i], y1 = ys[i] - YB;
					if (y0 > a[0] + 1e-9 || y1 < c[0] - 1e-9) {
						continue;
					}
					for (double y : new double[] {Math.min(y0, a[0]), Math.max(y1, c[0])}) {
						double v = a[1] + (c[1] - a[1]) * (a[0] - y) / (a[0] - c[0]);
						double cur = interp(pts, y);
						if (v < need[i] - 1e-9 || v > Math.max(cur, need[i] + 0.06) + 1e-9) {
							ok = false;
						}
					}
				}
				if (ok) {
					pts.remove(k);
					removed = true;
					break;
				}
			}
		}
		// the profile must not keep the last point under the true bottom alone: it extends constant anyway
		double[] profile = new double[pts.size() * 2];
		for (int k = 0; k < pts.size(); k++) {
			profile[2 * k] = Math.round(pts.get(k)[0] * 1000) / 1000.0;
			profile[2 * k + 1] = Math.ceil(pts.get(k)[1] * 1000) / 1000.0;
		}
		// deck under the top, inboard of the bulwark
		double deck = col.floor(spot.side, zc, hw, profile[1] - 0.6, top + 1e-3);
		// how far the ladder floats off the hull near the top
		double gapTop = 0;
		SideLadder.Ladder l = new SideLadder.Ladder(spot.side, zc, hw, slope, top, spot.style, profile);
		for (double y = top - 1.2; y + YB <= top + 1e-9; y += YB) {
			double sk = Math.max(col.outer(spot.side, zc, hw, slope, y + YB / 2), skin.band(zc, hw, slope, y + YB / 2));
			gapTop = Math.max(gapTop, l.hullX(y + YB / 2) - sk);
		}
		return new Measure(spot, slope, top, deck, profile, gapTop);
	}

	static double interp(List<double[]> pts, double y) {
		if (y >= pts.get(0)[0]) {
			return pts.get(0)[1];
		}
		for (int k = 1; k < pts.size(); k++) {
			double[] a = pts.get(k - 1), c = pts.get(k);
			if (y >= c[0]) {
				return a[1] + (c[1] - a[1]) * (a[0] - y) / (a[0] - c[0]);
			}
		}
		return pts.get(pts.size() - 1)[1];
	}

	/** Prints the table of {@link SideLadder} measured from the models and the collision hulls. */
	public static void main(String[] args) throws Exception {
		String ship = null;
		StringBuilder out = new StringBuilder();
		for (Spot s : SPOTS) {
			Measure m = measure(s);
			if (!s.ship.equals(ship)) {
				if (ship != null) {
					out.append(")),\n");
				}
				ship = s.ship;
				out.append("\t\t\tMap.entry(\"").append(ship).append("\", List.of(\n");
			} else {
				out.append(",\n");
			}
			StringBuilder p = new StringBuilder();
			for (double v : m.profile) {
				p.append(", ").append(fmt(v));
			}
			out.append(String.format(Locale.ROOT, "\t\t\t\t\t%s(%s, %s, %s, %s, \"%s\"%s)", s.side > 0 ? "port" : "starboard", fmt(s.z), fmt(s.halfWidth),
					fmt(m.slope), fmt(m.top), s.style, p));
			System.err.printf(Locale.ROOT, "%s %s z=%.2f slope=%.2f top=%.3f deck=%.3f (bulwark %.2f) gapTop=%.2f points=%d%n", s.ship,
					s.side > 0 ? "port" : "starboard", s.z, m.slope, m.top, m.deck, m.top - m.deck, m.gapTop, m.profile.length / 2);
		}
		out.append("))");
		System.out.println(out);
	}

	static String fmt(double v) {
		String s = String.format(Locale.ROOT, "%.3f", v);
		s = s.replaceAll("0+$", "");
		return s.endsWith(".") ? s + "0" : s;
	}

	// ------------------------------------------------------------------ the checks

	@Test
	void everyWaterShipHasLaddersOnBothSidesAndNoOtherHas() {
		for (String id : WATER_SHIPS) {
			List<SideLadder.Ladder> ls = SideLadder.of(id);
			long port = ls.stream().filter(l -> l.side() == SideLadder.PORT).count();
			long starboard = ls.stream().filter(l -> l.side() == SideLadder.STARBOARD).count();
			double halfLength = Ships.byId(id).geometry().hull().halfLength;
			int min = halfLength >= 15 ? 2 : 1;
			assertTrue(port >= min && starboard >= min, id + ": ladders port " + port + ", starboard " + starboard + " (at least " + min + " each)");
		}
		for (ShipType t : Ships.ALL) {
			if (!WATER_SHIPS.contains(t.id())) {
				assertTrue(SideLadder.of(t.id()).isEmpty(), t.id() + " (rowboat or aircraft) has no side ladder");
				assertTrue(t.id().equals("rowboat") || t.geometry().flying(), t.id() + " floats: it should have ladders");
			}
		}
		assertEquals(new java.util.HashSet<>(WATER_SHIPS), SideLadder.ships());
	}

	@Test
	void tableMatchesTheSpotsAndTheMeasuredProfiles() throws Exception {
		Map<String, Integer> seen = new HashMap<>();
		for (Spot s : SPOTS) {
			int k = seen.merge(s.ship, 1, Integer::sum) - 1;
			SideLadder.Ladder l = SideLadder.of(s.ship).get(k);
			assertEquals(s.side, l.side(), s.ship + " ladder " + k + " side");
			assertEquals(s.z, l.z(), 1e-9, s.ship + " ladder " + k + " z");
			assertEquals(s.halfWidth, l.halfWidth(), 1e-9);
			assertEquals(s.style, l.style());
			Measure m = measure(s);
			assertEquals(m.slope, l.slope(), 0.011, s + " slope (rerun SideLadderTest#main)");
			assertEquals(m.top, l.top(), 0.02, s + " top (rerun SideLadderTest#main)");
			assertEquals(m.profile.length, l.profile().length, s + " profile points (rerun SideLadderTest#main)");
			for (int i = 0; i < m.profile.length; i++) {
				assertEquals(m.profile[i], l.profile()[i], 0.011, s + " profile[" + i + "] (rerun SideLadderTest#main)");
			}
		}
		for (String id : WATER_SHIPS) {
			assertEquals(SideLadder.of(id).size(), seen.getOrDefault(id, 0), id + ": table and spots");
		}
	}

	@Test
	void laddersLieOnTheHullNeverThroughItAndHangFromABulwarkOverADeck() throws Exception {
		for (Spot s : SPOTS) {
			ShipType t = Ships.byId(s.ship);
			ShipGeometry g = t.geometry();
			double wl = g.hull().waterlineY;
			SideLadder.Ladder l = SideLadder.of(s.ship).stream().filter(x -> x.side() == s.side && x.z() == s.z).findFirst().orElseThrow();
			Skin skin = skin(s.ship, s.side);
			Collision col = new Collision(g, l.z(), l.halfWidth() + 0.05);
			double bottom = SideLadder.bottom(wl);
			assertTrue(bottom <= wl - 1.5, s + ": bottom 1.5 under the water");
			double[] p = l.profile();
			assertEquals(l.top(), p[0], 1e-9, s + ": the profile starts at the top");
			for (int i = 2; i < p.length; i += 2) {
				assertTrue(p[i] < p[i - 2] && p[i + 1] >= p[i - 1] - 1e-9, s + ": the profile goes down and never inboard");
			}
			double worstClip = 0, worstSnag = 0;
			for (double y = bottom; y < l.top() - 1e-6; y += YB) {
				double yc = y + YB / 2;
				double x = l.hullX(y); // the narrowest in the bin is at its top: the profile never narrows going down
				x = Math.min(x, l.hullX(y + YB));
				worstClip = Math.max(worstClip, skin.band(l.z(), l.halfWidth(), l.slope(), yc) - x);
				worstSnag = Math.max(worstSnag, col.outer(s.side, l.z(), l.halfWidth(), l.slope(), yc) - x);
			}
			assertTrue(worstClip <= 0.02, s + ": the ladder goes through the model by " + worstClip);
			assertTrue(worstSnag <= 0.03, s + ": the collision hull sticks out of the ladder by " + worstSnag + " (a climber would snag)");
			Measure m = measure(s);
			assertTrue(m.gapTop <= 0.6, s + ": the ladder floats " + m.gapTop + " off the hull under the bulwark");
			double deck = col.floor(s.side, l.z(), l.halfWidth(), l.hullX(l.top()) - 0.6, l.top() + 1e-3);
			assertTrue(deck >= l.top() - 2.3 && deck <= l.top() + 1e-3, s + ": a deck to step down on under the top " + l.top() + " (found " + deck + ")");
			assertTrue(l.top() >= wl + 0.8, s + ": the top is above the water");
			// within the hull's bounding circle (the collision broad phase)
			assertTrue(SideLadder.reach(List.of(l), wl) <= g.boundingRadius() + 1.5, s + ": inside the broad phase reach");
		}
	}

	@Test
	void laddersKeepClearOfGunportsGangplankAndBoats() {
		for (String id : WATER_SHIPS) {
			ShipGeometry g = Ships.byId(id).geometry();
			Gangplank.Spec gp = Gangplank.of(id);
			for (SideLadder.Ladder l : SideLadder.of(id)) {
				for (ShipGeometry.Gunport p : g.gunports()) {
					if (p.side() == l.side()) {
						assertTrue(Math.abs(p.z() - l.z()) >= l.halfWidth() + 0.4, id + " ladder at " + l.z() + " clashes with gunport " + p.index());
					}
				}
				if (gp != null && gp.o() == l.side()) {
					assertTrue(Math.abs(gp.hz() - l.z()) >= gp.width() / 2 + l.halfWidth() + 0.3, id + " ladder at " + l.z() + " clashes with the gangplank");
				}
				double[] boat = BOATS.get(id);
				if (boat != null) {
					assertTrue(l.z() + l.halfWidth() < boat[0] - 1.0 || l.z() - l.halfWidth() > boat[1] + 1.0, id + " ladder at " + l.z() + " is by the boat");
				}
				for (SideLadder.Ladder o : SideLadder.of(id)) {
					if (o != l && o.side() == l.side()) {
						assertTrue(Math.abs(o.z() - l.z()) > 3, id + ": two ladders too close");
					}
				}
			}
		}
	}

	@Test
	void climbingZoneTakesTheSwimmerAndTheClimberButNotTheDeck() {
		for (String id : WATER_SHIPS) {
			ShipGeometry g = Ships.byId(id).geometry();
			double wl = g.hull().waterlineY;
			List<SideLadder.Ladder> ls = SideLadder.of(id);
			for (SideLadder.Ladder l : ls) {
				double bottom = SideLadder.bottom(wl);
				// a swimmer pressed against the ladder, from under its bottom up to its top
				for (double y = bottom - 1.0; y <= l.top() + 0.25; y += 0.25) {
					double yy = Math.max(bottom, Math.min(l.top(), y));
					double x = l.localX(l.faceX(yy) + 0.3, 0);
					assertTrue(SideLadder.climbing(ls, wl, x, y, l.z(), 0, 0), id + " " + l.z() + ": climbing at y " + y);
					assertTrue(SideLadder.climbing(ls, wl, x, y, l.z() + l.halfWidth(), 0, 0), id + ": at the ladder's edge");
				}
				// stepping over the bulwark at the top
				assertTrue(SideLadder.climbing(ls, wl, l.localX(l.faceX(l.top()) - 0.5, 0), l.top() + 0.1, l.z(), 0, 0), id + ": over the bulwark");
				// on the deck inboard of the bulwark, beside the ladder, far out: not climbing
				assertFalse(SideLadder.climbing(ls, wl, l.localX(l.hullX(l.top()) - 0.75, 0), l.top() - 1.0, l.z(), 0, 0), id + ": on the deck");
				assertFalse(SideLadder.climbing(ls, wl, l.localX(l.faceX(1) + 0.3, 0), 1, l.z() + l.halfWidth() + 0.5, 0, 0), id + ": beside it");
				assertFalse(SideLadder.climbing(ls, wl, l.localX(l.faceX(1) + 1.5, 0), 1, l.z(), 0, 0), id + ": swimming away");
				assertFalse(SideLadder.climbing(ls, wl, l.localX(l.faceX(bottom) + 0.3, 0), bottom - 1.6, l.z(), 0, 0), id + ": far under it");
				// the server's allowance for a moving ship widens it
				assertTrue(SideLadder.climbing(ls, wl, l.localX(l.faceX(1) + 0.3, 0), 1, l.z() + l.halfWidth() + 1.0, 1.0, 0), id + ": allowance");
			}
		}
	}

	@Test
	void collisionSlabCoversTheLadderAndStaysOutboard() {
		for (String id : WATER_SHIPS) {
			ShipGeometry g = Ships.byId(id).geometry();
			double wl = g.hull().waterlineY;
			List<SideLadder.Ladder> ls = SideLadder.of(id);
			for (double yaw : new double[] {0, 37, 90, 211}) {
				ShipPose pose = new ShipPose(100, 64, -50, yaw);
				for (SideLadder.Ladder l : ls) {
					for (double y = SideLadder.bottom(wl) + 0.1; y < l.top() - 0.05; y += 0.5) {
						double[] w = pose.toWorld(l.localX(l.faceX(y) - 0.03, 0), y, l.z());
						double[] q = {w[0] - 0.05, w[1] - 0.05, w[2] - 0.05, w[0] + 0.05, w[1] + 0.05, w[2] + 0.05};
						boolean[] hit = {false};
						SideLadder.collectBoxes(ls, wl, pose, q[0], q[1], q[2], q[3], q[4], q[5], (a, b, c, d, e, f) -> {
							if (w[0] >= a && w[0] <= d && w[1] >= b && w[1] <= e && w[2] >= c && w[2] <= f) {
								hit[0] = true;
							}
						});
						assertTrue(hit[0], id + " " + l.z() + " yaw " + yaw + ": the slab covers the ladder at y " + y);
					}
					// nothing above the top, nothing over the deck
					double[] w = pose.toWorld(l.localX(l.hullX(l.top()) - 0.8, 0), l.top() + 0.3, l.z());
					boolean[] hit = {false};
					SideLadder.collectBoxes(ls, wl, pose, w[0] - 0.3, w[1], w[2] - 0.3, w[0] + 0.3, w[1] + 1.8, w[2] + 0.3, (a, b, c, d, e, f) -> {
						if (e > w[1] + 1e-6) {
							hit[0] = true;
						}
					});
					assertFalse(hit[0], id + ": no ladder box over the top");
				}
			}
		}
	}

	@Test
	void meshIsBakedAroundTheLadders() {
		for (String id : WATER_SHIPS) {
			double wl = Ships.byId(id).geometry().hull().waterlineY;
			List<SideLadder.Ladder> ls = SideLadder.of(id);
			float[] mesh = SideLadder.mesh(ls, wl);
			assertEquals(0, mesh.length % SideLadder.QUAD_FLOATS);
			int quads = mesh.length / SideLadder.QUAD_FLOATS;
			assertTrue(quads > 60 * ls.size() && quads < 900 * ls.size(), id + ": " + quads + " quads");
			for (int q = 0; q < quads; q++) {
				int o = q * SideLadder.QUAD_FLOATS;
				double nx = mesh[o + 20], ny = mesh[o + 21], nz = mesh[o + 22];
				assertEquals(1.0, Math.sqrt(nx * nx + ny * ny + nz * nz), 1e-3);
				float x = mesh[o], y = mesh[o + 1], z = mesh[o + 2];
				boolean near = false;
				for (SideLadder.Ladder l : ls) {
					double X = l.side() * x;
					if (Math.abs(z - l.z()) <= l.halfWidth() + 0.01 && y >= SideLadder.bottom(wl) - 0.01 && y <= l.top() + 0.1
							&& X >= l.hullX(l.top()) - 0.4 - Math.abs(l.slope()) && X <= l.faceX(SideLadder.bottom(wl)) + 0.2 + Math.abs(l.slope())) {
						near = true;
					}
				}
				assertTrue(near, id + ": vertex " + x + " " + y + " " + z + " is on a ladder");
				for (int k = 0; k < 4; k++) {
					assertTrue(mesh[o + k * 5 + 3] >= 0 && mesh[o + k * 5 + 3] <= 1 && mesh[o + k * 5 + 4] >= 0 && mesh[o + k * 5 + 4] <= 1);
				}
			}
		}
		assertEquals(BbModel.QUAD_FLOATS, SideLadder.QUAD_FLOATS);
	}
}
