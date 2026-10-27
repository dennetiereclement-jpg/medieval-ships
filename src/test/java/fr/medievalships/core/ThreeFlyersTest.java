package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * The three flying vessels of 1.9.0 together (each was built on its own branch, beside the shared features): every
 * vessel is registered once with its names and item files, the handling goes from the slow Crystal Airship through the
 * Dragon Junk to the agile Rustic Skyskiff, and the shared banking is on for all three.
 */
class ThreeFlyersTest {
	private static final List<ShipType> FLYERS = List.of(Ships.CRYSTAL_AIRSHIP, Ships.DRAGON_JUNK, Ships.RUSTIC_SKIFF);
	private static final Path ASSETS = Path.of("src/main/resources/assets/medievalships");

	@Test
	void everyVesselIsRegisteredOnceWithItsNamesAndFiles() throws Exception {
		Set<String> ids = new HashSet<>();
		for (ShipType t : Ships.ALL) {
			assertTrue(ids.add(t.id()), "id used twice: " + t.id());
		}
		for (ShipType t : FLYERS) {
			assertTrue(Ships.ALL.contains(t), t.id());
		}
		for (String lang : new String[] {"en_us", "fr_fr"}) {
			JsonObject names;
			try (Reader r = Files.newBufferedReader(ASSETS.resolve("lang/" + lang + ".json"), StandardCharsets.UTF_8)) {
				names = JsonParser.parseReader(r).getAsJsonObject();
			}
			for (ShipType t : Ships.ALL) {
				for (String key : new String[] {"item.medievalships." + t.id(), "entity.medievalships." + t.id()}) {
					assertTrue(names.has(key) && !names.get(key).getAsString().isBlank(), lang + ": " + key);
				}
			}
		}
		for (ShipType t : Ships.ALL) {
			for (String file : new String[] {"items/" + t.id() + ".json", "models/item/" + t.id() + ".json", "textures/item/" + t.id() + ".png",
					"models/entity/" + t.id() + ".bbmodel"}) {
				assertTrue(Files.isRegularFile(ASSETS.resolve(file)), t.id() + ": " + file);
			}
			if (t.geometry().interior() != null) {
				assertTrue(Files.isRegularFile(ASSETS.resolve("interiors/" + t.id() + ".grid")), t.id() + ": interior grid");
				assertNotNull(t.geometry().decor(), t.id() + ": decor");
			}
		}
	}

	@Test
	void allThreeFlyWithWalkableRooms() {
		for (ShipType t : FLYERS) {
			assertTrue(t.geometry().flying(), t.id());
			assertNotNull(t.geometry().interior(), t.id() + ": rooms");
			ShipConfig c = t.defaults().get();
			c.sanitize();
			assertNotNull(c.flight, t.id());
			assertTrue(t.geometry().seats().size() >= 8, t.id() + ": seats " + t.geometry().seats().size());
			assertTrue(t.geometry().seats().get(ShipGeometry.PILOT_SEAT).pilot(), t.id() + ": the helm");
		}
	}

	/** The specification: the Crystal Airship slow and majestic, the Rustic Skyskiff agile, the Dragon Junk in between. */
	@Test
	void handlingGoesFromTheCrystalAirshipThroughTheJunkToTheSkiff() {
		ShipConfig crystal = Ships.CRYSTAL_AIRSHIP.defaults().get(), junk = Ships.DRAGON_JUNK.defaults().get(),
				skiff = Ships.RUSTIC_SKIFF.defaults().get();
		for (ShipConfig c : List.of(crystal, junk, skiff)) {
			c.sanitize();
		}
		assertTrue(crystal.normalSpeed < junk.normalSpeed && junk.normalSpeed < skiff.normalSpeed, "cruising speed");
		assertTrue(crystal.fastSpeed < junk.fastSpeed && junk.fastSpeed < skiff.fastSpeed, "top speed");
		assertTrue(crystal.acceleration < junk.acceleration && junk.acceleration < skiff.acceleration, "acceleration");
		assertTrue(crystal.maxTurnRate < junk.maxTurnRate && junk.maxTurnRate < skiff.maxTurnRate, "turn rate");
		assertTrue(crystal.flight.climbSpeed < junk.flight.climbSpeed && junk.flight.climbSpeed < skiff.flight.climbSpeed, "climb");
		assertTrue(crystal.flight.verticalAcceleration < junk.flight.verticalAcceleration
				&& junk.flight.verticalAcceleration < skiff.flight.verticalAcceleration, "vertical acceleration");
	}

	/**
	 * The shared banking (visual only) is on for the three, the largest banking the least (the drift of their walkable
	 * cells is checked for every aircraft by SharedFeaturesTest).
	 */
	@Test
	void sharedBankingSuitsTheirSizes() {
		double crystal = bank(Ships.CRYSTAL_AIRSHIP), junk = bank(Ships.DRAGON_JUNK), skiff = bank(Ships.RUSTIC_SKIFF);
		assertTrue(crystal > 0 && junk > 0 && skiff > 0, "banking on");
		assertTrue(crystal <= junk && junk <= skiff, "bigger banks less: " + crystal + " " + junk + " " + skiff);
		assertEquals(0, Flight.bankLimit(Ships.DRAGON_JUNK.geometry(), 0.0), 1e-12, "bankAngle 0 turns it off");
	}

	private static double bank(ShipType t) {
		ShipConfig c = t.defaults().get();
		c.sanitize();
		return Flight.bankLimit(t.geometry(), c.flight);
	}
}
