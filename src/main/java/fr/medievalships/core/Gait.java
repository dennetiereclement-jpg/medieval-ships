package fr.medievalships.core;

/** Allures: slow (harbour manoeuvres), normal (cruising), fast (open sea). */
public enum Gait {
	SLOW("lente"),
	NORMAL("normale"),
	FAST("rapide");

	private final String frenchName;

	Gait(String frenchName) {
		this.frenchName = frenchName;
	}

	public String frenchName() {
		return frenchName;
	}

	public Gait faster() {
		return this == SLOW ? NORMAL : FAST;
	}

	public Gait slower() {
		return this == FAST ? NORMAL : SLOW;
	}

	public static Gait byName(String name) {
		for (Gait g : values()) {
			if (g.name().equalsIgnoreCase(name) || g.frenchName.equalsIgnoreCase(name)) {
				return g;
			}
		}
		return null;
	}

	public static Gait byOrdinal(int i) {
		Gait[] v = values();
		return v[Math.max(0, Math.min(v.length - 1, i))];
	}
}
