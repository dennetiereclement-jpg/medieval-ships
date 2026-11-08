package fr.medievalships.core.bridge;

/**
 * The adjustable numbers of one drawbridge (set by {@code /pontlevis}, defaults from {@link DrawbridgeConfig}).
 *
 * @param approach         length of each approach zone beyond the deck, blocks (50 by default)
 * @param hysteresis       extra distance (blocks) a vessel already taken into account keeps counting at
 * @param openAngle        angle of the raised leaves, degrees (0 closed, 90 upright)
 * @param durationTicks    ticks a full opening (or closing) takes
 * @param closeDelayTicks  ticks the bridge waits, once nothing needs it any more, before closing
 * @param warningTicks     ticks between the announcement and the start of a movement (time to leave the deck)
 * @param margin           blocks kept between a vessel's top and the deck's underside
 * @param stopDistance     blocks before the deck edge where an autopilot vessel waits for the leaves
 */
public record BridgeTuning(double approach, double hysteresis, double openAngle, int durationTicks, int closeDelayTicks, int warningTicks,
		double margin, double stopDistance) {

	/** Degrees the leaves turn per tick. */
	public double step() {
		return openAngle / Math.max(1, durationTicks);
	}

	public BridgeTuning sanitized() {
		return new BridgeTuning(clamp(approach, 4, 512), clamp(hysteresis, 0, 128), clamp(openAngle, 10, 90),
				(int) clamp(durationTicks, 10, 20 * 120), (int) clamp(closeDelayTicks, 0, 20 * 600), (int) clamp(warningTicks, 0, 20 * 120),
				clamp(margin, 0, 8), clamp(stopDistance, 0, 64));
	}

	private static double clamp(double v, double lo, double hi) {
		return Double.isNaN(v) ? lo : Math.max(lo, Math.min(hi, v));
	}

	public BridgeTuning withApproach(double v) {
		return new BridgeTuning(v, hysteresis, openAngle, durationTicks, closeDelayTicks, warningTicks, margin, stopDistance).sanitized();
	}

	public BridgeTuning withHysteresis(double v) {
		return new BridgeTuning(approach, v, openAngle, durationTicks, closeDelayTicks, warningTicks, margin, stopDistance).sanitized();
	}

	public BridgeTuning withOpenAngle(double v) {
		return new BridgeTuning(approach, hysteresis, v, durationTicks, closeDelayTicks, warningTicks, margin, stopDistance).sanitized();
	}

	public BridgeTuning withDurationTicks(int v) {
		return new BridgeTuning(approach, hysteresis, openAngle, v, closeDelayTicks, warningTicks, margin, stopDistance).sanitized();
	}

	public BridgeTuning withCloseDelayTicks(int v) {
		return new BridgeTuning(approach, hysteresis, openAngle, durationTicks, v, warningTicks, margin, stopDistance).sanitized();
	}

	public BridgeTuning withWarningTicks(int v) {
		return new BridgeTuning(approach, hysteresis, openAngle, durationTicks, closeDelayTicks, v, margin, stopDistance).sanitized();
	}

	public BridgeTuning withMargin(double v) {
		return new BridgeTuning(approach, hysteresis, openAngle, durationTicks, closeDelayTicks, warningTicks, v, stopDistance).sanitized();
	}

	public BridgeTuning withStopDistance(double v) {
		return new BridgeTuning(approach, hysteresis, openAngle, durationTicks, closeDelayTicks, warningTicks, margin, v).sanitized();
	}
}
