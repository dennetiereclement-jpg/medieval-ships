package fr.medievalships.core;

import java.util.List;

/**
 * Parametric hull shape, shared by every ship type. The same formulas are used by the model
 * generators in {@code tools/} so that collisions match what is drawn.
 *
 * <p>Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = waterline),
 * z = forward (+z = bow).
 */
public final class HullShape {
	/** A raised deck covering {@code fromZ < z < toZ} (open interval) at height {@code y}. */
	public record RaisedDeck(double fromZ, double toZ, double y) {
	}

	/** Builder-style parameters, see {@link Ships} for the actual ships. */
	public static final class Params {
		public double halfLength = 10.0;
		/** Extreme ends of the stem and stern posts. */
		public double tip = 10.9;
		public double maxHalfWidth = 2.55;
		/** Plan shape: halfWidth = max * (1 - (|z| / scale) ^ powA) ^ powB, separately fore and aft. */
		public double foreScale = 10.3;
		public double forePowA = 2.3;
		public double forePowB = 0.75;
		public double aftScale = 10.3;
		public double aftPowA = 2.3;
		public double aftPowB = 0.75;
		/** keelY = -keelDepth + keelRise * (|z| / halfLength) ^ keelPow. */
		public double keelDepth = 1.2;
		public double keelRise = 1.0;
		public double keelPow = 4.0;
		/** Sheer: railY = railBase + rise * (|z| / halfLength) ^ railPow (rise fore or aft). */
		public double railBase = 1.6;
		public double railRiseFore = 1.0;
		public double railRiseAft = 1.0;
		public double railPow = 3.0;
		/** If > 0, the rail is at least this high above the deck (bulwarks of raised decks). */
		public double railAboveDeck = 0.0;
		/** Bulwarks of castles that are not hull decks: the rail is at least {@code y} over the interval. */
		public List<RaisedDeck> railFloors = List.of();
		public double mainDeckY = 0.45;
		public List<RaisedDeck> raisedDecks = List.of();
		public double deckMinZ = -9.7;
		public double deckMaxZ = 9.6;
		/** Hull bottom cross-section: points (x / halfWidth, y / keelY), from the keel outwards. */
		public double[][] bottomSection = {{0.0, 1.0}, {0.62, 0.82}, {0.93, 0.25}};
	}

	public final double halfLength;
	public final double tip;
	public final double maxHalfWidth;
	public final double mainDeckY;
	public final double deckMinZ;
	public final double deckMaxZ;
	private final Params p;

	public HullShape(Params params) {
		this.p = params;
		this.halfLength = params.halfLength;
		this.tip = params.tip;
		this.maxHalfWidth = params.maxHalfWidth;
		this.mainDeckY = params.mainDeckY;
		this.deckMinZ = params.deckMinZ;
		this.deckMaxZ = params.deckMaxZ;
	}

	public Params params() {
		return p;
	}

	public double halfWidth(double z) {
		boolean fore = z >= 0;
		double a = Math.abs(z) / (fore ? p.foreScale : p.aftScale);
		if (a >= 1.0) {
			return 0.0;
		}
		return p.maxHalfWidth * Math.pow(1.0 - Math.pow(a, fore ? p.forePowA : p.aftPowA), fore ? p.forePowB : p.aftPowB);
	}

	public double deckY(double z) {
		double y = p.mainDeckY;
		for (RaisedDeck d : p.raisedDecks) {
			if (z > d.fromZ() && z < d.toZ()) {
				y = Math.max(y, d.y());
			}
		}
		return y;
	}

	public double railY(double z) {
		double a = Math.abs(z) / p.halfLength;
		double rise = z >= 0 ? p.railRiseFore : p.railRiseAft;
		double sheer = p.railBase + rise * Math.pow(a, p.railPow);
		for (RaisedDeck f : p.railFloors) {
			if (z > f.fromZ() && z < f.toZ()) {
				sheer = Math.max(sheer, f.y());
			}
		}
		return p.railAboveDeck > 0 ? Math.max(sheer, deckY(z) + p.railAboveDeck) : sheer;
	}

	public double keelY(double z) {
		double a = Math.abs(z) / p.halfLength;
		return -p.keelDepth + p.keelRise * Math.pow(a, p.keelPow);
	}

	/** Half width of the walkable deck (inside of the planking). */
	public double innerHalfWidth(double z) {
		return Math.max(0.0, 0.97 * halfWidth(z) - 0.12);
	}

	/**
	 * Height of the outside of the hull bottom at lateral distance {@code absX} from the keel,
	 * following the cross-section used by the model generator (keel, bilge, waterline).
	 */
	public double bottomY(double z, double absX) {
		double w = halfWidth(z), yk = keelY(z);
		if (w <= 0.1) {
			return yk;
		}
		double[][] s = p.bottomSection;
		int n = s.length;
		if (absX >= s[n - 1][0] * w) {
			return s[n - 1][1] * yk;
		}
		for (int i = 0; i < n - 1; i++) {
			double x0 = s[i][0] * w, x1 = s[i + 1][0] * w;
			if (absX <= x1) {
				double f = (absX - x0) / (x1 - x0);
				return s[i][1] * yk + (s[i + 1][1] - s[i][1]) * yk * f;
			}
		}
		return s[n - 1][1] * yk;
	}
}
