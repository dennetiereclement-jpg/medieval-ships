package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

/**
 * The seats of the props (1.19.0): the JSON's {@code "seats"} read by {@link TentType}, turned with the facing, the
 * nomad tavern registered with its seats, and the sitting geometry of {@link Seating} (picking ray, standing spots,
 * the sitter's height).
 */
public class SeatsTest {
	private static final double EPS = 1e-9;
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	private static TentType parse(String seats) {
		JsonObject root = JsonParser.parseString("{\"extent\": [-3, 0, -2, 3, 3, 4], \"seats\": " + seats + "}").getAsJsonObject();
		return TentType.parse(TentType.CARTS, "cart_x", "x", "X", root);
	}

	@Test
	void seatsAreReadFromTheJson() {
		TentType t = parse("[{\"pos\": [1.5, 0.5, 2.0], \"yaw\": 90}, {\"pos\": [-1, 0.47, 0.5]}, {\"pos\": [0, 0.6, 1], \"yaw\": -90},"
				+ " {\"yaw\": 10}, {\"pos\": [1, 2]}, 7, {\"pos\": [0, 0.5, 0], \"yaw\": 450}]");
		List<TentType.Seat> s = t.seats();
		assertEquals(4, s.size(), "the entries without a three-number pos are skipped: " + s);
		assertEquals(new TentType.Seat(1.5, 0.5, 2.0, 90f), s.get(0));
		assertEquals(0f, s.get(1).yaw(), "the yaw defaults to 0 (facing the prop's front, +z)");
		assertEquals(0.47, s.get(1).y(), EPS, "the seat's surface height");
		assertEquals(270f, s.get(2).yaw(), 1e-6, "yaws are kept in [0, 360)");
		assertEquals(90f, s.get(3).yaw(), 1e-6);
		assertEquals(s, t.seats(TentType.SOUTH), "facing south: unchanged");
		JsonObject plain = JsonParser.parseString("{\"extent\": [-1, 0, -1, 1, 2, 1]}").getAsJsonObject();
		TentType none = TentType.parse(TentType.CARTS, "cart_y", "y", "Y", plain);
		assertTrue(none.seats().isEmpty(), "a prop without the field has no seat");
		for (int q = 0; q < 4; q++) {
			assertTrue(none.seats(q).isEmpty());
		}
	}

	@Test
	void seatsTurnWithTheFacingLikeTheColliders() {
		TentType t = parse("[{\"pos\": [1.0, 0.5, 2.0], \"yaw\": 0}, {\"pos\": [-0.5, 0.45, -1.0], \"yaw\": 270}]");
		for (int q = 0; q < 4; q++) {
			List<TentType.Seat> turned = t.seats(q);
			assertEquals(2, turned.size());
			for (int i = 0; i < 2; i++) {
				TentType.Seat s = t.seats().get(i), r = turned.get(i);
				assertArrayEquals(TentType.rotate(s.x(), s.z(), q), new double[] {r.x(), r.z()}, EPS, "point turned like a collision box");
				assertEquals(s.y(), r.y(), EPS, "height unchanged");
				assertEquals(TentType.Seat.wrapYaw(s.yaw() + 90.0 * q), r.yaw(), 1e-4, "yaw + 90 per quarter turn");
			}
		}
		// a sitter facing the prop's front (+z, yaw 0) faces west (-x, yaw 90) when the prop faces west
		TentType.Seat w = t.seats(TentType.WEST).get(0);
		assertEquals(-2.0, w.x(), EPS);
		assertEquals(1.0, w.z(), EPS);
		assertEquals(90f, w.yaw(), 1e-6);
		double[] f = Seating.facing(w.yaw());
		assertEquals(-1.0, f[0], 1e-9, "yaw 90 looks towards -x");
		assertEquals(0.0, f[1], 1e-9);
		// the seat's facing turns exactly like the prop's front: the front (0, 1) turned to west is the yaw-90 vector
		double[] front = TentType.rotate(0, 1, TentType.WEST);
		assertArrayEquals(front, f, 1e-9);
		assertEquals(180f, t.seats(TentType.NORTH).get(0).yaw(), 1e-6);
		assertEquals(270f, t.seats(TentType.EAST).get(0).yaw(), 1e-6);
		assertEquals(0f, t.seats(TentType.WEST).get(1).yaw(), 1e-6, "270 + 90 wraps to 0");
	}

	@Test
	void theNomadTavernIsACartWithSeats() throws Exception {
		TentType t = TentTypes.TAVERN;
		assertEquals("taverne_nomade", t.id());
		assertEquals(TentType.CARTS, t.group());
		assertTrue(t.isCart());
		assertFalse(t.masculine(), "la taverne");
		assertEquals("taverne nomade", t.frenchName());
		assertEquals("Nomad Tavern", t.englishName());
		assertTrue(TentTypes.CARTS.contains(t) && TentTypes.PROPS.contains(t) && !TentTypes.ALL.contains(t), "tab Charrettes");
		assertSame(t, TentTypes.byId("taverne_nomade"));
		assertSame(t, TentTypes.byId("medievalships:taverne_nomade"));
		assertSame(t, TentTypes.byId(" Taverne "));
		assertSame(t, TentTypes.byId("tavern"));
		assertTrue(t.seats().size() >= 2, "the tavern's stools are seats: " + t.seats().size());
		TentType.Box e = t.extent();
		for (TentType.Seat s : t.seats()) {
			assertTrue(s.x() > e.x0() && s.x() < e.x1() && s.z() > e.z0() && s.z() < e.z1(), "seat inside the extent " + s);
			// the bar stools stand on the ledge in front of the counter, about 1.6 up
			assertTrue(s.y() > 0.2 && s.y() < 2.0, "a seat's surface between 0.2 and 2.0 above the ground " + s);
			assertTrue(s.yaw() >= 0 && s.yaw() < 360, "yaw " + s);
		}
		for (String file : new String[] {"carts/taverne_nomade.json", "blockstates/taverne_nomade.json", "items/taverne_nomade.json",
				"models/item/taverne_nomade.json", "textures/item/taverne_nomade.png", t.model(), t.texture()}) {
			assertTrue(Files.exists(ASSETS.resolve(file)), "missing " + file);
		}
		for (String lang : new String[] {"en_us", "fr_fr"}) {
			JsonObject names = JsonParser.parseString(Files.readString(ASSETS.resolve("lang/" + lang + ".json"))).getAsJsonObject();
			assertNotNull(names.get("block.medievalships.taverne_nomade"), lang + " tavern name");
			assertNotNull(names.get("entity.medievalships.seat"), lang + " seat entity name");
		}
	}

	@Test
	void sittingHeightPutsTheThighsOnTheSurface() {
		// vanilla sitting pose of the player model (scale 0.9375): hip joint 12 px above the feet, the thigh 4 px thick
		// and pitched 81 degrees forwards: its underside at the hip is 2 px below the joint
		double scale = 0.9375 / 16.0;
		double hip = 12 * scale, thighUnder = hip - 2 * Math.sin(1.4137167) * scale;
		double feetBelowSurface = Seating.PLAYER_RIDING_DROP;
		double gap = thighUnder - feetBelowSurface; // underside of the thighs relative to the seat's surface
		assertTrue(Math.abs(gap) < 0.03, "thighs on the surface (gap " + gap + ")");
		// a seat's world point: anchor block centre + the turned seat; y on the anchor block's floor (= the ground)
		double[] w = Seating.world(10, 64, -3, new TentType.Seat(1.25, 0.5, -2.0, 0f));
		assertArrayEquals(new double[] {11.75, 64.5, -4.5}, w, EPS);
	}

	@Test
	void pickingRay() {
		double[] box = Seating.pickBox(0, 0.5, 0);
		assertArrayEquals(new double[] {-0.3, 0.05, -0.3, 0.3, 0.62, 0.3}, box, EPS);
		// from 2 blocks south at eye height, looking down at the stool's top
		double ox = 0, oy = 1.62, oz = 2.0;
		double dx = 0, dy = 0.5 - 1.62, dz = -2.0;
		double len = Math.sqrt(dx * dx + dy * dy + dz * dz);
		double t = Seating.rayBox(ox, oy, oz, dx / len, dy / len, dz / len, box, Seating.PICK_RANGE);
		assertFalse(Double.isNaN(t), "the look ray enters the seat's box");
		assertTrue(t > 1.5 && t < len, "entry distance " + t);
		assertTrue(Double.isNaN(Seating.rayBox(ox, oy, oz, dx / len, dy / len, dz / len, box, 1.0)), "beyond the allowed distance");
		assertTrue(Double.isNaN(Seating.rayBox(ox, oy, oz, 0, 0, 1, box, 10)), "looking away");
		assertTrue(Double.isNaN(Seating.rayBox(1.0, 0.5, 2.0, 0, 0, -1, box, 10)), "a parallel ray beside the box");
		assertEquals(0.0, Seating.rayBox(0, 0.4, 0, 1, 0, 0, box, 10), EPS, "from inside: distance 0");
		assertEquals(Seating.PICK_RANGE + 0.5, Seating.SERVER_REACH, EPS, "the server allows the pick range plus the box");
	}

	@Test
	void standingSpotsStartInFrontOfTheSeat() {
		List<double[]> o = Seating.standOffsets(0);
		assertEquals(Seating.STAND_DISTANCES.length * Seating.STAND_ANGLES.length, o.size());
		assertArrayEquals(new double[] {0, Seating.STAND_DISTANCES[0]}, o.get(0), 1e-9, "first in front (+z for yaw 0)");
		double[] behind = o.get(Seating.STAND_ANGLES.length - 1);
		assertEquals(-Seating.STAND_DISTANCES[0], behind[1], 1e-9, "behind last");
		for (double[] p : o) {
			double d = Math.hypot(p[0], p[1]);
			assertTrue(d >= Seating.STAND_DISTANCES[0] - 1e-9, "never on the seat " + d);
			// a standing player (0.6 wide) is then clear of a stool of up to 0.5 x 0.5
			assertTrue(Math.max(Math.abs(p[0]), Math.abs(p[1])) - 0.3 >= 0.25 - 1e-9, "clear of the stool");
		}
		// facing east (yaw 270): in front is +x
		double[] east = Seating.standOffsets(270).get(0);
		assertEquals(Seating.STAND_DISTANCES[0], east[0], 1e-9);
		assertEquals(0, east[1], 1e-9);
		assertEquals(-10.0, Seating.yawDifference(350, 0), 1e-9);
		assertEquals(170.0, Seating.yawDifference(170, 0), 1e-9);
		assertEquals(180.0, Seating.yawDifference(90, -90), 1e-9);
	}
}
