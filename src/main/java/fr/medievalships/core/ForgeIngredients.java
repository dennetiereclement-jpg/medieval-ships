package fr.medievalships.core;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;

/**
 * Which stacks of an inventory pay for a divine forge recipe (1.34.0), exactly: for each ingredient its quantity, no
 * more, taken from the slots it matches. Two ingredients may match the same stack (a tag and one of its items, a plain
 * item and the same item with components): the stacks are shared out as a flow (augmenting paths, a few dozen nodes),
 * so the recipe is payable whenever some share-out exists, and the plan never takes more of a stack than it holds. The
 * game side ({@code fr.medievalships.forge.ForgeRecipes}) answers {@link Slots} from the player's inventory (main
 * inventory first, then the hotbar and the off hand) and removes what {@link Plan#take()} says.
 */
public final class ForgeIngredients {
	private ForgeIngredients() {
	}

	/** An inventory as the allocation sees it. */
	public interface Slots {
		int size();

		/** How many items the slot holds (0 for an empty one). */
		int count(int slot);

		/** Does the stack in the slot count as this ingredient (item or tag, components)? */
		boolean matches(int ingredient, int slot);
	}

	/**
	 * The share-out: {@code take[slot]} items to remove from each slot, {@code owned[i]} items the inventory holds for
	 * ingredient i (every matching stack counted, for the interface's "possédés / requis"), {@code missing[i]} what still
	 * lacks for it once the stacks are shared out (all zero when the recipe is payable).
	 */
	public record Plan(int[] take, int[] owned, int[] missing) {
		/** Can the recipe be paid? */
		public boolean complete() {
			for (int m : missing) {
				if (m > 0) {
					return false;
				}
			}
			return true;
		}

		/** How many items the plan removes in all. */
		public int total() {
			int t = 0;
			for (int n : take) {
				t += n;
			}
			return t;
		}
	}

	/** Shares the slots out among the ingredients ({@code required[i]} items each). */
	public static Plan plan(List<Integer> required, Slots slots) {
		int ni = required.size(), ns = slots.size();
		int[] owned = new int[ni];
		long need = 0;
		for (int i = 0; i < ni; i++) {
			need += Math.max(0, required.get(i));
			for (int s = 0; s < ns; s++) {
				if (slots.count(s) > 0 && slots.matches(i, s)) {
					owned[i] = (int) Math.min(Integer.MAX_VALUE, (long) owned[i] + slots.count(s));
				}
			}
		}
		// nodes: 0 source, 1..ni ingredients, ni+1..ni+ns slots, ni+ns+1 sink
		int n = ni + ns + 2, source = 0, sink = n - 1;
		int inf = (int) Math.min(Integer.MAX_VALUE, need + 1);
		int[][] cap = new int[n][n];
		for (int i = 0; i < ni; i++) {
			cap[source][1 + i] = Math.max(0, required.get(i));
			for (int s = 0; s < ns; s++) {
				if (slots.count(s) > 0 && slots.matches(i, s)) {
					cap[1 + i][1 + ni + s] = inf;
				}
			}
		}
		for (int s = 0; s < ns; s++) {
			cap[1 + ni + s][sink] = Math.max(0, slots.count(s));
		}
		int[][] flow = new int[n][n];
		int[] parent = new int[n];
		while (true) {
			Arrays.fill(parent, -1);
			parent[source] = source;
			ArrayDeque<Integer> queue = new ArrayDeque<>();
			queue.add(source);
			while (!queue.isEmpty() && parent[sink] < 0) {
				int u = queue.poll();
				for (int v = 0; v < n; v++) {
					if (parent[v] < 0 && cap[u][v] - flow[u][v] > 0) {
						parent[v] = u;
						queue.add(v);
					}
				}
			}
			if (parent[sink] < 0) {
				break;
			}
			int push = Integer.MAX_VALUE;
			for (int v = sink; v != source; v = parent[v]) {
				push = Math.min(push, cap[parent[v]][v] - flow[parent[v]][v]);
			}
			for (int v = sink; v != source; v = parent[v]) {
				flow[parent[v]][v] += push;
				flow[v][parent[v]] -= push;
			}
		}
		int[] take = new int[ns];
		for (int s = 0; s < ns; s++) {
			take[s] = flow[1 + ni + s][sink];
		}
		int[] missing = new int[ni];
		for (int i = 0; i < ni; i++) {
			missing[i] = Math.max(0, required.get(i) - flow[source][1 + i]);
		}
		return new Plan(take, owned, missing);
	}
}
