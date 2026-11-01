package fr.medievalships.tent;

import java.util.LinkedHashMap;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerWorldEvents;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.text.Text;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.TentType;
import fr.medievalships.core.TentTypes;

/**
 * Registration of the tents, the carts and the workshops: one block and one block item per {@link TentType}
 * ({@code medievalships:<id>}, {@link TentTypes#PROPS}; a {@link WorkshopBlock} for a workshop), one block entity type
 * for all of them, the creative tabs "Tentes", "Charrettes" and "Ateliers", and the
 * collision registry fed by the block entity load / unload events (chunks loading and unloading; placing and
 * breaking go through the block itself).
 */
public final class Tents {
	public static BlockEntityType<TentBlockEntity> BLOCK_ENTITY;
	private static final Map<TentType, TentBlock> BLOCKS = new LinkedHashMap<>();
	private static final Map<TentType, Item> ITEMS = new LinkedHashMap<>();

	private Tents() {
	}

	public static TentBlock block(TentType type) {
		return BLOCKS.get(type);
	}

	public static Item item(TentType type) {
		return ITEMS.get(type);
	}

	public static Map<TentType, Item> items() {
		return ITEMS;
	}

	@Nullable
	public static TentType typeOf(Block block) {
		return block instanceof TentBlock t ? t.tentType() : null;
	}

	public static void register() {
		for (TentType type : TentTypes.PROPS) {
			RegistryKey<Block> blockKey = RegistryKey.of(RegistryKeys.BLOCK, MedievalShips.id(type.id()));
			// solid(): its collision shape is a thin floor, which vanilla would count as "not solid" and let flowing
			// water wash the prop away; a tent, a cart or a workshop at the water's edge must stay
			boolean wooden = type.isCart() || type.isWorkshop();
			AbstractBlock.Settings settings = AbstractBlock.Settings.create().registryKey(blockKey).strength(wooden ? 1.0f : 0.6f)
					.sounds(wooden ? BlockSoundGroup.WOOD : BlockSoundGroup.WOOL).nonOpaque().solid();
			// the workshops: the same block, plus their particles (forge smoke, enchanting glyphs...)
			TentBlock block = Registry.register(Registries.BLOCK, blockKey,
					type.isWorkshop() ? new WorkshopBlock(type, settings) : new TentBlock(type, settings));
			BLOCKS.put(type, block);
			RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, MedievalShips.id(type.id()));
			ITEMS.put(type, Registry.register(Registries.ITEM, itemKey,
					new TentItem(block, new Item.Settings().registryKey(itemKey).maxCount(16).useBlockPrefixedTranslationKey())));
		}
		BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, MedievalShips.id("tent"),
				FabricBlockEntityTypeBuilder.create(TentBlockEntity::new, BLOCKS.values().toArray(new Block[0])).build());

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("tents"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(TentTypes.ADVENTURER)))
				.displayName(Text.translatable("itemGroup.medievalships.tents"))
				.entries((context, entries) -> TentTypes.ALL.forEach(t -> entries.add(ITEMS.get(t))))
				.build());
		RegistryKey<ItemGroup> cartsKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("carts"));
		Registry.register(Registries.ITEM_GROUP, cartsKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(TentTypes.CART_OPEN)))
				.displayName(Text.translatable("itemGroup.medievalships.carts"))
				.entries((context, entries) -> TentTypes.CARTS.forEach(t -> entries.add(ITEMS.get(t))))
				.build());
		RegistryKey<ItemGroup> workshopsKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("workshops"));
		Registry.register(Registries.ITEM_GROUP, workshopsKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(TentTypes.WORKSHOP_BLACKSMITH)))
				.displayName(Text.translatable("itemGroup.medievalships.workshops"))
				.entries((context, entries) -> TentTypes.WORKSHOPS.forEach(t -> entries.add(ITEMS.get(t))))
				.build());

		// the collision boxes follow the chunks: known while the tent's chunk is loaded, forgotten with it
		ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, world) -> {
			if (be instanceof TentBlockEntity tent && tent.tentType() != null) {
				TentCollisions.add(world, be.getPos(), tent.tentType(), tent.quarter());
			}
		});
		ServerBlockEntityEvents.BLOCK_ENTITY_UNLOAD.register((be, world) -> {
			if (be instanceof TentBlockEntity) {
				TentCollisions.remove(world, be.getPos());
			}
		});
		ServerWorldEvents.UNLOAD.register((server, world) -> TentCollisions.clear(world));
	}
}
