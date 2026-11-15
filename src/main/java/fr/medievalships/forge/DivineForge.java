package fr.medievalships.forge;

import java.util.Collection;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType;

import net.minecraft.block.Block;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.recipe.RecipeSerializer;
import net.minecraft.recipe.RecipeType;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

import fr.medievalships.MedievalShips;

/**
 * Registration of the divine forge's game objects (1.34.0), all named {@code medievalships:forge_divine}: the block
 * entity type (from {@code Tents.register}, once the forge's block exists), the recipe type and its serializer (the
 * {@code "type"} of the recipe files), the screen handler type of its interface, and the payload that refreshes it.
 * The block and its item are the props' ({@code Tents}), in the tab "Ateliers".
 */
public final class DivineForge {
	public static final Identifier ID = MedievalShips.id("forge_divine");
	public static BlockEntityType<DivineForgeBlockEntity> BLOCK_ENTITY;
	public static RecipeType<DivineForgeRecipe> RECIPE_TYPE;
	public static RecipeSerializer<DivineForgeRecipe> RECIPE_SERIALIZER;
	public static ExtendedScreenHandlerType<DivineForgeScreenHandler, ForgeMenu> SCREEN_HANDLER;

	private DivineForge() {
	}

	/** The block entity type of the forge's anchor blocks (called by {@code Tents.register} with the forge's blocks). */
	public static void registerBlockEntity(Collection<? extends Block> blocks) {
		BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, ID,
				FabricBlockEntityTypeBuilder.create(DivineForgeBlockEntity::new, blocks.toArray(Block[]::new)).build());
	}

	/** The recipe type and serializer, the screen handler type, the refresh payload. */
	public static void register() {
		RECIPE_TYPE = Registry.register(Registries.RECIPE_TYPE, ID, new RecipeType<DivineForgeRecipe>() {
			@Override
			public String toString() {
				return ID.toString();
			}
		});
		RECIPE_SERIALIZER = Registry.register(Registries.RECIPE_SERIALIZER, ID, new DivineForgeRecipe.Serializer());
		SCREEN_HANDLER = Registry.register(Registries.SCREEN_HANDLER, ID,
				new ExtendedScreenHandlerType<>((syncId, inventory, menu) -> new DivineForgeScreenHandler(syncId, inventory, menu), ForgeMenu.CODEC));
		PayloadTypeRegistry.playS2C().register(ForgeMenuPayload.ID, ForgeMenuPayload.CODEC);
	}
}
