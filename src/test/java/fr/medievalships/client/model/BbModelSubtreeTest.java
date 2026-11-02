package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

/**
 * {@link BbModel#renderSubtree} (1.19.0, the training targets): one bone's subtree drawn alone, at rest exactly as the
 * whole model draws it, turned about each bone's own origin with the pose's rotations ({@link BbModel#rotate}), the
 * children following their parent; the rest of the model with that bone hidden draws the rest.
 */
class BbModelSubtreeTest {
	/**
	 * A static base plate, and a target bone "target_0" (origin = pivot at the plate's top, bb (16, 2, 0) = prop-local
	 * (-1, 0.125, 0)) holding a post and a child "target_0_head" (origin at the neck, bb y 26).
	 */
	private static final String MODEL = """
			{"resolution": {"width": 16, "height": 16},
			 "elements": [
			   {"uuid": "e1", "name": "plate", "from": [0, 0, -8], "to": [32, 2, 8], "origin": [0, 0, 0], "faces": %s},
			   {"uuid": "e2", "name": "post", "from": [14, 2, -2], "to": [18, 26, 2], "origin": [0, 0, 0], "faces": %s},
			   {"uuid": "e3", "name": "head", "from": [13, 26, -3], "to": [19, 32, 3], "origin": [0, 0, 0], "faces": %s}
			 ],
			 "outliner": [
			   {"name": "base", "origin": [0, 0, 0], "children": ["e1"]},
			   {"name": "target_0", "origin": [16, 2, 0], "children": ["e2",
			     {"name": "target_0_head", "origin": [16, 26, 0], "children": ["e3"]}]}
			 ]}""";
	private static final String FACES = "{\"north\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"south\": {\"uv\": [0,0,1,1], \"texture\": 0},"
			+ " \"east\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"west\": {\"uv\": [0,0,1,1], \"texture\": 0},"
			+ " \"up\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"down\": {\"uv\": [0,0,1,1], \"texture\": 0}}";

	private static BbModel model() {
		return new BbModel(new StringReader(String.format(MODEL, FACES, FACES, FACES)));
	}

	private static List<float[]> quads(BbModel m, BbModel.Pose pose, String bone) {
		List<float[]> out = new ArrayList<>();
		if (bone == null) {
			m.render(pose, (p, uv, n, glow) -> out.add(p.clone()));
		} else {
			m.renderSubtree(pose, bone, (p, uv, n, glow) -> out.add(p.clone()));
		}
		return out;
	}

	@Test
	void subtreeAtRestIsWhatTheWholeModelDraws() {
		BbModel m = model();
		assertTrue(m.hasBone("target_0") && m.hasBone("target_0_head"));
		assertFalse(m.hasBone("target_1"));
		assertArrayEquals(new double[] {-1.0, 0.125, 0.0}, m.origin("target_0"), 1e-9);
		assertNull(m.origin("nothing"));
		List<float[]> whole = quads(m, m.newPose(), null);
		List<float[]> target = quads(m, m.newPose(), "target_0");
		BbModel.Pose hidden = m.newPose();
		m.hide(hidden, "target_0");
		List<float[]> rest = quads(m, hidden, null);
		assertEquals(18, whole.size());
		assertEquals(12, target.size(), "the post and the head");
		assertEquals(6, rest.size(), "the plate");
		// the exact same floats (the static renderer's cached path and the subtree's path agree bit for bit)
		for (int i = 0; i < target.size(); i++) {
			assertArrayEquals(whole.get(6 + i), target.get(i), "quad " + i);
		}
		assertTrue(quads(m, m.newPose(), "nothing").isEmpty());
	}

	@Test
	void bonesTurnAboutTheirOrigins() {
		BbModel m = model();
		BbModel.Pose pose = m.newPose();
		// the body tilted by 90 degrees about Blockbench -x: a prop-local rotation of +90 about x, its top goes to +z
		m.rotate(pose, "target_0", -90, 0, 0);
		List<float[]> q = quads(m, pose, "target_0");
		float maxZ = -1e9f, maxY = -1e9f;
		for (float[] p : q) {
			for (int k = 0; k < 4; k++) {
				maxY = Math.max(maxY, p[k * 3 + 1]);
				maxZ = Math.max(maxZ, p[k * 3 + 2]);
			}
		}
		// standing, the head's top is at y 2.0 and z within +-0.19; lying towards +z: z up to 0.125 + ... = about 1.875
		assertEquals(1.875, maxZ, 1e-4, "the top of the head, laid towards +z about the pivot");
		assertTrue(maxY < 0.125 + 0.2, "nothing stands up any more: " + maxY);
		// the head alone, nodded about its neck: the post does not move
		BbModel.Pose nod = m.newPose();
		m.rotate(nod, "target_0_head", 30, 0, 0);
		List<float[]> n = quads(m, nod, "target_0");
		List<float[]> still = quads(m, m.newPose(), "target_0");
		for (int i = 0; i < 6; i++) {
			assertArrayEquals(still.get(i), n.get(i), "post quad " + i + " unchanged");
		}
		boolean moved = false;
		for (int i = 6; i < 12; i++) {
			for (int k = 0; k < 12; k++) {
				moved |= Math.abs(still.get(i)[k] - n.get(i)[k]) > 1e-3;
			}
		}
		assertTrue(moved, "the head moved");
		// the rotations of a pose do not touch the whole model's static path (no animation moves these bones)
		List<float[]> whole = quads(m, pose, null);
		List<float[]> rest = quads(m, m.newPose(), null);
		for (int i = 0; i < whole.size(); i++) {
			assertArrayEquals(rest.get(i), whole.get(i));
		}
	}
}
