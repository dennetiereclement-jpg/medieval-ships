package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;

/**
 * 1.30.0: the faces of a model are lit the right way up. The entity layers the mod draws with ({@code entityCutoutNoCull},
 * {@code entityTranslucent}) have per-face lighting: OpenGL's front face (counter-clockwise on screen) is lit by the vertex
 * normal, the back face by the reversed normal. The loader emitted every face clockwise (the Blockbench UV corner order),
 * so every face was a back face: the tops lit as bottoms (x 0.4, dark), the bottoms as tops (x 1, bright). These tests pin
 * the up face of a plain cube to a +Y normal, counter-clockwise seen from above, through the plain and the baked paths,
 * for rotated, animated and mirrored cubes, and every face of every model of the mod.
 */
class BbModelWindingTest {
	/** Vanilla's level light directions ({@code DiffuseLighting}) and the shader's power and ambient ({@code light.glsl}). */
	private static final float[] LIGHT0 = norm(0.2f, 1.0f, -0.7f), LIGHT1 = norm(-0.2f, 1.0f, 0.7f);

	/** One 16 px cube in a bone; {@code extra}: the element's extra JSON fields, {@code anims}: the model's animations. */
	private static BbModel cube(String extra, String boneRotation, String anims) {
		String faces = "\"faces\":{"
				+ "\"north\":{\"uv\":[0,0,4,4],\"texture\":0},\"south\":{\"uv\":[4,0,8,4],\"texture\":0},"
				+ "\"west\":{\"uv\":[8,0,12,4],\"texture\":0},\"east\":{\"uv\":[12,0,16,4],\"texture\":0},"
				+ "\"up\":{\"uv\":[0,4,4,8],\"texture\":0},\"down\":{\"uv\":[4,4,8,8],\"texture\":0}}";
		String json = "{\"resolution\":{\"width\":16,\"height\":16},\"textures\":[{}],"
				+ "\"elements\":[{\"name\":\"box\",\"uuid\":\"e1\",\"from\":[-8,0,-8],\"to\":[8,16,8],\"origin\":[0,0,0]" + extra + "," + faces + "}],"
				+ "\"outliner\":[{\"name\":\"body\",\"uuid\":\"b1\",\"origin\":[0,8,0],\"rotation\":" + boneRotation + ",\"children\":[\"e1\"]}]"
				+ (anims == null ? "" : ",\"animations\":[" + anims + "]") + "}";
		return new BbModel(new StringReader(json));
	}

	private static BbModel plainCube() {
		return cube("", "[0,0,0]", null);
	}

	/** A quad as a renderer gets it: corners, normal. */
	private record Face(float[] p, float[] n) {
	}

	private static List<Face> faces(BbModel model, BbModel.Pose pose) {
		List<Face> out = new ArrayList<>();
		model.render(pose, (p, uv, n, glow) -> out.add(new Face(p.clone(), n.clone())));
		return out;
	}

	/** The same through the baked runs a {@link BbModel.MeshSink} gets (the ship renderer's path). */
	private static List<Face> bakedFaces(BbModel model, BbModel.Pose pose) {
		List<Face> out = new ArrayList<>();
		model.render(pose, new BbModel.MeshSink() {
			@Override
			public void mesh(float[] d, int from, int to, int lightClass, boolean twoSided) {
				for (int q = from; q < to; q++) {
					int o = q * BbModel.QUAD_FLOATS;
					float[] p = new float[12];
					for (int k = 0; k < 4; k++) {
						System.arraycopy(d, o + k * 5, p, k * 3, 3);
					}
					out.add(new Face(p, new float[] {d[o + 20], d[o + 21], d[o + 22]}));
				}
			}

			@Override
			public void quad(float[] p, float[] uv, float[] n, boolean glow) {
				out.add(new Face(p.clone(), n.clone()));
			}
		});
		return out;
	}

	/** The face whose normal is closest to {@code dir}. */
	private static Face facing(List<Face> faces, float x, float y, float z) {
		Face best = null;
		float bestDot = -2;
		for (Face f : faces) {
			float d = f.n[0] * x + f.n[1] * y + f.n[2] * z;
			if (d > bestDot) {
				bestDot = d;
				best = f;
			}
		}
		return best;
	}

	/**
	 * The entity shading the shader gives a face seen from a camera at {@code eye} (ship-local): front face (counter-
	 * clockwise seen from the eye) lit by its normal, back face by the reversed normal, as with PER_FACE_LIGHTING.
	 */
	private static float shading(Face f, float[] eye) {
		float[] p = f.p;
		float ax = p[3] - p[0], ay = p[4] - p[1], az = p[5] - p[2];
		float bx = p[6] - p[0], by = p[7] - p[1], bz = p[8] - p[2];
		float cx = ay * bz - az * by, cy = az * bx - ax * bz, cz = ax * by - ay * bx;
		boolean front = cx * (eye[0] - p[0]) + cy * (eye[1] - p[1]) + cz * (eye[2] - p[2]) > 0;
		float s = front ? 1 : -1;
		float l0 = Math.max(0, s * dot(LIGHT0, f.n)), l1 = Math.max(0, s * dot(LIGHT1, f.n));
		return Math.min(1f, (l0 + l1) * 0.6f + 0.4f);
	}

	private static void assertCounterClockwise(Face f, String what) {
		float len = (float) Math.sqrt(dot(f.n, f.n));
		assertEquals(1f, len, 1e-3f, what + ": unit normal");
		assertTrue(BbModel.windingDot(f.p, 0, f.n) > 0, what + ": counter-clockwise seen from its normal's side");
	}

	@Test
	void upFaceOfAPlainCubeIsUpAndCounterClockwise() {
		for (boolean baked : new boolean[] {false, true}) {
			BbModel model = plainCube();
			List<Face> faces = baked ? bakedFaces(model, model.newPose()) : faces(model, model.newPose());
			assertEquals(6, faces.size());
			Face up = facing(faces, 0, 1, 0);
			assertEquals(0f, up.n[0], 1e-5f);
			assertEquals(1f, up.n[1], 1e-5f);
			assertEquals(0f, up.n[2], 1e-5f);
			for (int k = 0; k < 4; k++) {
				assertEquals(1f, up.p[k * 3 + 1], 1e-5f, "the up face is the top of the cube");
			}
			for (Face f : faces) {
				assertCounterClockwise(f, (baked ? "baked " : "") + "face " + java.util.Arrays.toString(f.n));
			}
			// what the player sees in daylight: the top bright, the bottom at the ambient 0.4, the sides in between
			float[] above = {0.3f, 5f, 0.2f}, below = {0.3f, -5f, 0.2f};
			float top = shading(up, above), bottom = shading(facing(faces, 0, -1, 0), below);
			float side = shading(facing(faces, 0, 0, 1), new float[] {0.2f, 0.5f, 5f});
			assertTrue(top > 0.99f, "top face shading " + top);
			assertEquals(0.4f, bottom, 1e-3f, "bottom face shading");
			assertTrue(top >= side && side > bottom, "top " + top + " >= side " + side + " > bottom " + bottom);
		}
	}

	@Test
	void rotatedCubesStayCounterClockwise() {
		// the element turned 45 degrees about x and the bone 30 about y and 20 about z
		BbModel model = cube(",\"rotation\":[45,0,0]", "[0,30,20]", null);
		for (List<Face> faces : List.of(faces(model, model.newPose()), bakedFaces(model, model.newPose()))) {
			assertEquals(6, faces.size());
			for (Face f : faces) {
				assertCounterClockwise(f, "rotated face " + java.util.Arrays.toString(f.n));
			}
			assertTrue(facing(faces, 0, 1, 0).n[1] > 0.5f, "the up face still faces up");
		}
	}

	@Test
	void animatedAndMirroredBonesStayCounterClockwise() {
		String spin = "{\"name\":\"spin\",\"length\":1,\"loop\":\"loop\",\"animators\":{\"b1\":{\"name\":\"body\",\"keyframes\":["
				+ "{\"channel\":\"rotation\",\"time\":0,\"data_points\":[{\"x\":\"25\",\"y\":\"40\",\"z\":\"0\"}]}]}}}";
		String mirror = "{\"name\":\"mirror\",\"length\":1,\"loop\":\"loop\",\"animators\":{\"b1\":{\"name\":\"body\",\"keyframes\":["
				+ "{\"channel\":\"scale\",\"time\":0,\"data_points\":[{\"x\":\"-1\",\"y\":\"0.5\",\"z\":\"1\"}]}]}}}";
		BbModel model = cube("", "[0,0,0]", spin + "," + mirror);
		for (String anim : new String[] {"spin", "mirror"}) {
			BbModel.Pose pose = model.newPose();
			model.apply(pose, anim, 0f, 1f);
			List<Face> faces = faces(model, pose);
			assertEquals(6, faces.size());
			for (Face f : faces) {
				assertCounterClockwise(f, anim + " face " + java.util.Arrays.toString(f.n));
			}
			// a normal still points out of the cube, from its centre (the bone's origin, 0.5 block up: turned and scaled
			// about it, it stays there) to the middle of the face
			for (Face f : faces) {
				float mx = (f.p[0] + f.p[6]) / 2, my = (f.p[1] + f.p[7]) / 2 - 0.5f, mz = (f.p[2] + f.p[8]) / 2;
				assertTrue(mx * f.n[0] + my * f.n[1] + mz * f.n[2] > 0, anim + ": outward normal " + java.util.Arrays.toString(f.n));
			}
		}
	}

	/** Every face of every model of the mod, at rest, through the ship renderer's baked path: counter-clockwise. */
	@Test
	void everyModelOfTheModIsCounterClockwise() throws Exception {
		List<Path> models;
		try (Stream<Path> s = Files.walk(Path.of("src/main/resources/assets/medievalships/models"))) {
			models = s.filter(p -> p.toString().endsWith(".bbmodel")).sorted().toList();
		}
		assertTrue(models.size() > 50, "models found: " + models.size());
		long faces = 0;
		for (Path path : models) {
			BbModel model;
			try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
				model = new BbModel(r);
			}
			BbModel.Pose pose = model.newPose();
			List<String> bad = new ArrayList<>();
			for (Face f : bakedFaces(model, pose)) {
				float area = (float) Math.sqrt(dot(cross(f.p), cross(f.p)));
				if (area < 1e-6f) {
					continue; // an edge of a zero-thickness plate: no area, never seen
				}
				faces++;
				if (BbModel.windingDot(f.p, 0, f.n) <= 0 && bad.size() < 3) {
					bad.add(java.util.Arrays.toString(f.p) + " n " + java.util.Arrays.toString(f.n));
				}
			}
			assertTrue(bad.isEmpty(), path.getFileName() + ": clockwise faces " + bad);
		}
		assertTrue(faces > 100_000, "faces checked: " + faces);
	}

	private static float[] cross(float[] p) {
		float ax = p[3] - p[0], ay = p[4] - p[1], az = p[5] - p[2];
		float bx = p[6] - p[0], by = p[7] - p[1], bz = p[8] - p[2];
		return new float[] {ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx};
	}

	private static float dot(float[] a, float[] b) {
		return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
	}

	private static float[] norm(float x, float y, float z) {
		float l = (float) Math.sqrt(x * x + y * y + z * z);
		return new float[] {x / l, y / l, z / l};
	}
}
