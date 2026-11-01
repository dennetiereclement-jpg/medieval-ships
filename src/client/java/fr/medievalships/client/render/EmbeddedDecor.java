package fr.medievalships.client.render;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.InteriorDecor;
import fr.medievalships.core.ShipType;

/**
 * Client side of {@link InteriorDecor}: the block states of the decoration blocks whose mod is
 * installed on this client (resolved once), and the stand-in bones to hide for them.
 */
final class EmbeddedDecor {
	private static final Map<Object, EmbeddedDecor> CACHE = new HashMap<>();

	final List<InteriorDecor.Block> blocks;
	/** Per block: its state, or null when its mod is missing (its stand-in is drawn instead). */
	final BlockState[] states;
	/** Stand-in bones of the blocks that are drawn. */
	final List<String> hidden;
	/** Vanilla paintings in the frames of the model. */
	final List<InteriorDecor.Painting> paintings;

	private EmbeddedDecor(InteriorDecor decor) {
		this.blocks = decor.blocks();
		this.paintings = decor.paintings();
		this.states = new BlockState[blocks.size()];
		List<String> hide = new ArrayList<>();
		for (int i = 0; i < blocks.size(); i++) {
			InteriorDecor.Block b = blocks.get(i);
			Block block = resolve(b.block());
			if (block == null && b.alt() != null && !b.alt().isEmpty()) {
				block = resolve(b.alt()); // the vanilla alternative when the decoration mod is missing
			}
			if (block != null && !block.getDefaultState().isAir()) {
				states[i] = block.getDefaultState();
				hide.add(b.fallback());
			}
		}
		this.hidden = List.copyOf(hide);
		MedievalShips.LOGGER.info("Interior decor: {} of {} furniture blocks drawn from installed mods, the others by their stand-ins",
				hide.size(), blocks.size());
	}

	@Nullable
	private static Block resolve(String name) {
		Identifier id = Identifier.tryParse(name);
		return id == null ? null : Registries.BLOCK.getOptionalValue(id).orElse(null);
	}

	/** The furniture of a tent (its decor file is read once). */
	@Nullable
	static EmbeddedDecor of(fr.medievalships.core.TentType type) {
		if (type.decor() == null) {
			return null;
		}
		return CACHE.computeIfAbsent(type, t -> new EmbeddedDecor(InteriorDecor.load(type.decor())));
	}

	@Nullable
	static EmbeddedDecor of(ShipType type) {
		InteriorDecor decor = type.geometry().decor();
		if (decor == null) {
			return null;
		}
		return CACHE.computeIfAbsent(type, t -> new EmbeddedDecor(decor));
	}
}
