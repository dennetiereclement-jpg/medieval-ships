package fr.medievalships.client.model;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.Reader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

import org.junit.jupiter.api.Test;

/**
 * The static mesh of 1.29.0 ({@link BbModel.MeshSink}): the bones no animation moves are baked once, in cells, and a
 * mesh sink gets exactly the quads a plain sink gets (the picture does not change); only the animated bones are
 * transformed each frame; a cell out of view takes only its own quads away; a face whose cube has no opposite face is
 * two-sided.
 */
class BbModelMeshTest {
	private static final Path GALLEY = Path.of("src/main/resources/assets/medievalships/models/entity/galley.bbmodel");
	private static final Path LION = Path.of("src/main/resources/assets/medievalships/models/entity/royal_lion_ship.bbmodel");

	private static BbModel load(Path path) throws Exception {
		try (Reader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
			return new BbModel(r);
		}
	}

	/** Every quad as 23 floats (corners with uv, normal), plus the light class and the two-sided flag. */
	private static float[] key(float[] p, float[] uv, float[] n, boolean glow, boolean lit, boolean twoSided) {
		float[] k = new float[25];
		for (int c = 0; c < 4; c++) {
			k[c * 5] = p[c * 3];
			k[c * 5 + 1] = p[c * 3 + 1];
			k[c * 5 + 2] = p[c * 3 + 2];
			k[c * 5 + 3] = uv[c * 2];
			k[c * 5 + 4] = uv[c * 2 + 1];
		}
		k[20] = n[0];
		k[21] = n[1];
		k[22] = n[2];
		k[23] = glow ? 2 : lit ? 1 : 0;
		k[24] = twoSided ? 1 : 0;
		return k;
	}

	private static final Comparator<float[]> ORDER = (a, b) -> {
		for (int i = 0; i < a.length; i++) {
			int c = Float.compare(a[i], b[i]);
			if (c != 0) {
				return c;
			}
		}
		return 0;
	};

	/** A mesh sink that expands the runs it gets into quads, counting the runs and the cells. */
	private static final class Expanding implements BbModel.MeshSink {
		final List<float[]> quads = new ArrayList<>();
		final List<float[]> single = new ArrayList<>();
		int runs, cells;
		int cullCell = -1;
		int culledQuads;
		float[] bounds;

		@Override
		public boolean cellVisible(float minX, float minY, float minZ, float maxX, float maxY, float maxZ) {
			int index = cells++;
			bounds = new float[] {minX, minY, minZ, maxX, maxY, maxZ};
			return index != cullCell;
		}

		@Override
		public void mesh(float[] d, int from, int to, int lightClass, boolean twoSided) {
			runs++;
			for (int q = from; q < to; q++) {
				int o = q * BbModel.QUAD_FLOATS;
				float[] k = new float[25];
				System.arraycopy(d, o, k, 0, 23);
				k[23] = lightClass;
				k[24] = twoSided ? 1 : 0;
				for (int c = 0; c < 4; c++) {
					for (int a = 0; a < 3; a++) {
						float v = d[o + c * 5 + a];
						assertTrue(v >= bounds[a] - 1e-4 && v <= bounds[a + 3] + 1e-4, "a quad lies in the box of its cell");
					}
				}
				quads.add(k);
			}
		}

		@Override
		public void quad(float[] p, float[] uv, float[] n, boolean glow) {
			quad(p, uv, n, glow, false, true);
		}

		@Override
		public void quad(float[] p, float[] uv, float[] n, boolean glow, boolean lit, boolean twoSided) {
			single.add(key(p, uv, n, glow, lit, twoSided));
		}
	}

	private static List<float[]> plain(BbModel model, BbModel.Pose pose) {
		List<float[]> out = new ArrayList<>();
		model.render(pose, new BbModel.QuadSink() {
			@Override
			public void quad(float[] p, float[] uv, float[] n, boolean glow) {
				throw new AssertionError("the full overload is used");
			}

			@Override
			public void quad(float[] p, float[] uv, float[] n, boolean glow, boolean lit, boolean twoSided) {
				out.add(key(p, uv, n, glow, lit, twoSided));
			}
		});
		return out;
	}

	private static void assertSameQuads(List<float[]> a, List<float[]> b) {
		assertEquals(a.size(), b.size(), "same number of quads");
		a.sort(ORDER);
		b.sort(ORDER);
		for (int i = 0; i < a.size(); i++) {
			float[] x = a.get(i), y = b.get(i);
			for (int j = 0; j < x.length; j++) {
				assertEquals(x[j], y[j], 1e-5f, "quad " + i + " value " + j);
			}
		}
	}

	@Test
	void staticMeshIsBakedOnceAndDrawsTheSameQuads() throws Exception {
		BbModel m = load(GALLEY);
		assertFalse(m.isBaked());
		long before = BbModel.bakedQuads;
		List<float[]> first = plain(m, m.newPose());
		assertTrue(m.isBaked());
		assertEquals(m.staticQuadCount(), BbModel.bakedQuads - before, "the first render bakes every static quad once");
		assertTrue(m.staticQuadCount() > 0.8 * m.quadCount(), "most of the galley never moves");
		List<float[]> second = plain(m, m.newPose());
		assertEquals(BbModel.bakedQuads - before, m.staticQuadCount(), "the second render bakes nothing");
		assertEquals(m.quadCount(), first.size());
		assertSameQuads(first, second);
	}

	@Test
	void meshSinkGetsExactlyWhatAPlainSinkGets() throws Exception {
		BbModel m = load(LION);
		List<float[]> plain = plain(m, m.newPose());
		Expanding mesh = new Expanding();
		m.render(m.newPose(), mesh);
		assertEquals(m.staticQuadCount(), mesh.quads.size(), "the static bones come as runs");
		assertEquals(m.quadCount() - m.staticQuadCount(), mesh.single.size(), "the animated bones come quad by quad");
		assertEquals(m.staticCellCount(), mesh.cells, "every cell is offered once");
		assertTrue(mesh.cells > 50 && mesh.runs >= mesh.cells, "the lion's static mesh is split into many cells (" + mesh.cells + ")");
		List<float[]> all = new ArrayList<>(mesh.quads);
		all.addAll(mesh.single);
		assertSameQuads(plain, all);
	}

	@Test
	void cullingACellRemovesOnlyItsQuads() throws Exception {
		BbModel m = load(LION);
		Expanding full = new Expanding();
		m.render(m.newPose(), full);
		// the cell with the most quads, by counting what each cell contributes
		Expanding probe = new Expanding();
		probe.cullCell = full.cells / 2;
		m.render(m.newPose(), probe);
		int removed = full.quads.size() - probe.quads.size();
		assertTrue(removed > 0, "the culled cell held quads");
		assertEquals(full.single.size(), probe.single.size(), "the animated bones are untouched");
		assertEquals(full.cells, probe.cells, "every cell is still offered");
		List<float[]> rest = new ArrayList<>(full.quads);
		rest.sort(ORDER);
		List<float[]> kept = new ArrayList<>(probe.quads);
		kept.sort(ORDER);
		// every kept quad is one of the full set
		int i = 0;
		for (float[] q : kept) {
			while (i < rest.size() && ORDER.compare(rest.get(i), q) < 0) {
				i++;
			}
			assertTrue(i < rest.size() && ORDER.compare(rest.get(i), q) == 0, "a kept quad is one of the model's");
			i++;
		}
	}

	@Test
	void textureFilterAndHiddenBonesStillApply() throws Exception {
		BbModel m = load(LION);
		assertEquals(2, m.textureCount());
		Expanding t0 = new Expanding();
		m.render(m.newPose(), 0, t0);
		Expanding t1 = new Expanding();
		m.render(m.newPose(), 1, t1);
		assertEquals(m.quadCount(), t0.quads.size() + t0.single.size() + t1.quads.size() + t1.single.size(), "the two textures partition the quads");
		assertTrue(t1.quads.size() + t1.single.size() > 0, "the sails' texture has quads");
		BbModel.Pose pose = m.newPose();
		m.hide(pose, "detail");
		Expanding noDetail = new Expanding();
		m.render(pose, noDetail);
		assertTrue(noDetail.quads.size() < m.staticQuadCount(), "hiding the detail bone takes static quads away");
		assertEquals(m.quadCount() - m.staticQuadCount(), noDetail.single.size());
	}

	@Test
	void animatedBonesMoveAndStaticOnesDoNot() throws Exception {
		BbModel m = load(GALLEY);
		Expanding rest = new Expanding();
		m.render(m.newPose(), rest);
		BbModel.Pose pose = m.newPose();
		m.apply(pose, "row", 0.37f, 1f);
		m.apply(pose, "sail_wind", 1.2f, 1f);
		Expanding moved = new Expanding();
		m.render(pose, moved);
		assertSameQuads(new ArrayList<>(rest.quads), new ArrayList<>(moved.quads));
		assertEquals(rest.single.size(), moved.single.size());
		boolean different = false;
		for (int i = 0; i < rest.single.size() && !different; i++) {
			float[] a = rest.single.get(i), b = moved.single.get(i);
			for (int j = 0; j < 12 && !different; j++) {
				different = Math.abs(a[j] - b[j]) > 1e-4;
			}
		}
		assertTrue(different, "the oars and the sail moved");
	}

	@Test
	void aFaceWithoutItsOppositeIsTwoSided() {
		String faces = "{\"north\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"south\": {\"uv\": [0,0,1,1], \"texture\": 0},"
				+ " \"east\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"west\": {\"uv\": [0,0,1,1], \"texture\": 0},"
				+ " \"up\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"down\": {\"uv\": [0,0,1,1], \"texture\": 0}}";
		String topOnly = "{\"up\": {\"uv\": [0,0,1,1], \"texture\": 0}, \"north\": {\"uv\": [0,0,1,1], \"texture\": 0},"
				+ " \"south\": {\"uv\": [0,0,1,1], \"texture\": null}}";
		String json = "{\"resolution\": {\"width\": 16, \"height\": 16}, \"elements\": ["
				+ "{\"uuid\": \"a\", \"name\": \"box\", \"from\": [0, 0, 0], \"to\": [16, 16, 16], \"origin\": [0, 0, 0], \"faces\": " + faces + "},"
				+ "{\"uuid\": \"b\", \"name\": \"deck\", \"from\": [0, 20, 0], \"to\": [16, 20.2, 16], \"origin\": [0, 0, 0], \"faces\": " + topOnly + "}],"
				+ "\"outliner\": [{\"name\": \"root\", \"origin\": [0, 0, 0], \"children\": [\"a\", \"b\"]}]}";
		BbModel m = new BbModel(new StringReader(json));
		assertEquals(8, m.quadCount());
		List<float[]> quads = plain(m, m.newPose());
		int twoSided = 0, oneSided = 0;
		for (float[] q : quads) {
			if (q[24] == 1) {
				twoSided++;
			} else {
				oneSided++;
			}
		}
		assertEquals(6, oneSided, "the closed cube's faces hide each other");
		assertEquals(2, twoSided, "the deck's top and its north face (south is missing) are two-sided");
		Expanding mesh = new Expanding();
		m.render(m.newPose(), mesh);
		assertEquals(8, mesh.quads.size());
		// the cube sits on the cell boundaries of x = 0 and z = 0: its faces go with their neighbours, a few cells at most
		assertTrue(mesh.cells >= 1 && mesh.cells <= 8, "a few cells: " + mesh.cells + " " + Arrays.toString(mesh.bounds));
	}
}
