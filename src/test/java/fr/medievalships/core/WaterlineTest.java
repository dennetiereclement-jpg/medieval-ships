package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Pattern;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

/**
 * 1.30.0: eight ships ride deeper in the water ("baisse la hauteur des bateaux dans l'eau"): their WATERLINE_Y (the model
 * height of the sea surface, the one number the buoyancy, the probes, the placement, the autopilot, the wake and the side
 * ladders derive from) is raised by about half a block, the great galleon by a quarter, the royal lion ship by 0.2 only
 * (its lit ports). What must stay out of the water does: the openings of the hull (ports, scuttles, windows, doors), the
 * gun ports, the decks of the open ships; and the rooms of the vessels with an interior grid that now dip under the sea
 * are dry (no point of the hull's inside left to the sea).
 */
class WaterlineTest {
	/** id -> {WATERLINE_Y of 1.29.0, of 1.30.0}. */
	private static final Map<String, double[]> CHANGED = new LinkedHashMap<>();

	static {
		CHANGED.put("galleon", new double[] {-0.4, -0.15});
		CHANGED.put("old_corsair", new double[] {0.5, 1.0});
		CHANGED.put("steam_paddleboat", new double[] {-0.35, 0.15});
		CHANGED.put("gear_steamship", new double[] {0.6, 1.0});
		CHANGED.put("elven_sailboat", new double[] {-0.35, 0.05});
		CHANGED.put("trade_sloop", new double[] {-0.5, 0.1});
		CHANGED.put("blue_frigate", new double[] {0.6, 1.0});
		CHANGED.put("royal_lion_ship", new double[] {0.6, 0.8});
	}

	/** The names of the model elements that are openings of the hull. */
	private static final Pattern OPENING = Pattern.compile("port|scuttle|window|door|hole", Pattern.CASE_INSENSITIVE);

	private static ShipType type(String id) {
		for (ShipType t : Ships.ALL) {
			if (t.id().equals(id)) {
				return t;
			}
		}
		throw new AssertionError("no ship " + id);
	}

	@Test
	void theEightShipsRideDeeper() {
		for (Map.Entry<String, double[]> e : CHANGED.entrySet()) {
			ShipType t = type(e.getKey());
			double before = e.getValue()[0], now = e.getValue()[1];
			assertEquals(now, t.hull().waterlineY, 1e-9, e.getKey());
			double deeper = now - before;
			if (e.getKey().equals("galleon")) {
				assertEquals(0.25, deeper, 1e-9, "the great galleon: about half as much as the others");
			} else if (e.getKey().equals("royal_lion_ship")) {
				assertEquals(0.2, deeper, 1e-9, "the royal lion ship: held by its lit ports");
			} else {
				assertTrue(deeper >= 0.4 - 1e-9 && deeper <= 0.6 + 1e-9, e.getKey() + ": " + deeper + " deeper");
			}
			// the probes and the keel follow (the probes come from the waterline, the keel stays where the model has it)
			assertTrue(t.hull().keelY(0) < now - 0.6, e.getKey() + ": the keel under the water");
			boolean probe = false;
			for (double[] p : t.geometry().probes()) {
				probe |= Math.abs(p[1] - (now + 0.15)) < 1e-9;
			}
			assertTrue(probe || t.geometry().interior() != null, e.getKey() + ": a probe just above the new waterline");
		}
	}

	/** The gun ports, the ports, scuttles, windows and doors of the hull, as drawn, stay above the water. */
	@Test
	void openingsStayOutOfTheWater() throws Exception {
		for (String id : CHANGED.keySet()) {
			ShipType t = type(id);
			HullShape h = t.hull();
			double water = h.waterlineY;
			for (ShipGeometry.Gunport g : t.geometry().gunports()) {
				assertTrue(g.y() > water + 1.0, id + ": gun port " + g.index() + " at " + g.y());
			}
			double lowest = Double.POSITIVE_INFINITY;
			String which = "";
			JsonObject model;
			try (Reader r = Files.newBufferedReader(Path.of("src/main/resources/assets/medievalships/models/entity/" + id + ".bbmodel"),
					StandardCharsets.UTF_8)) {
				model = JsonParser.parseReader(r).getAsJsonObject();
			}
			Map<String, String> topBone = new HashMap<>();
			for (JsonElement n : model.getAsJsonArray("outliner")) {
				if (n.isJsonObject()) {
					bones(n.getAsJsonObject(), n.getAsJsonObject().get("name").getAsString(), topBone);
				}
			}
			for (JsonElement el : model.getAsJsonArray("elements")) {
				JsonObject o = el.getAsJsonObject();
				String name = o.get("name").getAsString();
				String bone = topBone.getOrDefault(o.get("uuid").getAsString(), "");
				if (!OPENING.matcher(name).find() || name.startsWith("lit") || bone.equals("rooms") || bone.equals("furniture")
						|| bone.equals("fittings")) {
					continue;
				}
				JsonArray f = o.getAsJsonArray("from"), to = o.getAsJsonArray("to");
				double x = Math.abs(f.get(0).getAsDouble() + to.get(0).getAsDouble()) / 32;
				double z = -(f.get(2).getAsDouble() + to.get(2).getAsDouble()) / 32;
				double y = Math.min(f.get(1).getAsDouble(), to.get(1).getAsDouble()) / 16;
				// on the outside of the hull: its sides, or its ends (the transom, the bow)
				if (x < 0.8 * h.maxHalfWidth && Math.abs(z) < 0.8 * h.halfLength) {
					continue;
				}
				if (y < lowest) {
					lowest = y;
					which = name;
				}
			}
			if (lowest < Double.POSITIVE_INFINITY) {
				assertTrue(lowest >= water + 0.15, id + ": " + which + " at y " + lowest + ", the water at " + water);
			}
		}
	}

	private static void bones(JsonObject g, String top, Map<String, String> out) {
		for (JsonElement c : g.getAsJsonArray("children")) {
			if (c.isJsonObject()) {
				bones(c.getAsJsonObject(), top, out);
			} else {
				out.put(c.getAsString(), top);
			}
		}
	}

	/** The open ships (no rooms): their decks and seats half a block above the water at least (no sea on the deck). */
	@Test
	void openDecksStayDry() {
		for (String id : CHANGED.keySet()) {
			ShipType t = type(id);
			if (t.geometry().interior() != null) {
				continue;
			}
			HullShape h = t.hull();
			assertTrue(h.mainDeckY - h.waterlineY >= 0.5, id + ": deck " + h.mainDeckY + ", water " + h.waterlineY);
			for (ShipGeometry.Seat s : t.geometry().seats()) {
				assertTrue(s.y() > h.waterlineY + 0.5 && s.dismount()[1] > h.waterlineY + 0.5, id + ": seat " + s.index());
			}
		}
	}

	/**
	 * The vessels with rooms: every point of the inside of the hull from just under the old waterline to above the new one
	 * (what the deeper draught puts under the sea)
	 * belongs to the interior grid (a room, a floor, a wall: dry, the world's water hidden there), none is left to the sea.
	 */
	@Test
	void roomsUnderTheNewSeaLevelAreDry() {
		int grids = 0;
		for (Map.Entry<String, double[]> e : CHANGED.entrySet()) {
			ShipType t = type(e.getKey());
			InteriorGrid g = t.geometry().interior();
			if (g == null) {
				continue;
			}
			grids++;
			HullShape h = t.hull();
			double y0 = e.getValue()[0] - 0.25, y1 = h.waterlineY + 0.6;
			int checked = 0;
			// the fine ends left out: a raked stem or a transom cut the parametric hull there, and they are solid
			for (double z = -h.halfLength + 2.5; z <= h.halfLength - 3; z += 0.25) {
				double w = h.innerHalfWidth(z) - 0.35;
				for (double x = -w; x <= w; x += 0.25) {
					for (double y = Math.max(y0, h.bottomY(z, Math.abs(x)) + 0.35); y < y1; y += 0.25) {
						checked++;
						assertTrue(g.kindAt(x, y, z) != InteriorGrid.OUT, e.getKey() + ": the sea inside the hull at " + x + " " + y + " " + z);
						assertTrue(g.dryAt(x, y, z, InteriorGrid.State.CLOSED), e.getKey() + ": wet at " + x + " " + y + " " + z);
					}
				}
			}
			assertTrue(checked > 5000, e.getKey() + ": points checked " + checked);
		}
		assertEquals(4, grids, "the corsair, the frigate, the royal lion ship and the gear steamship have rooms");
		assertNotNull(Ships.OLD_CORSAIR);
	}
}
