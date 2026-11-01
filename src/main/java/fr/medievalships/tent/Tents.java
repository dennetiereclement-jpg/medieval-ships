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
 * Registration of the tents: one block and one block item per {@link TentType} ({@code medievalships:<id>}), one
 * block entity type for all of them, the creative tab "Tentes", and the collision registry fed by the block
 * entity load / unload events (chunks loading and unloading; placing and breaking go through the block itself).
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
		for (TentType type : TentTypes.ALL) {
			RegistryKey<Block> blockKey = RegistryKey.of(RegistryKeys.BLOCK, MedievalShips.id(type.id()));
			TentBlock block = Registry.register(Registries.BLOCK, blockKey, new TentBlock(type, AbstractBlock.Settings.create()
					.registryKey(blockKey).strength(0.6f).sounds(BlockSoundGroup.WOOL).nonOpaque()));
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
				.entries((context, entries) -> ITEMS.values().forEach(entries::add))
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
