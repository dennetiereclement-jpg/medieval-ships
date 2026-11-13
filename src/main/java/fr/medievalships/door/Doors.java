package fr.medievalships.door;

import java.util.LinkedHashMap;
import java.util.Map;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerBlockEntityEvents;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.block.piston.PistonBehavior;
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
import fr.medievalships.core.DoorType;
import fr.medievalships.core.DoorTypes;

/**
 * Registration of the ten doors (1.31.0): one controller block and one item per {@link DoorType}
 * ({@code medievalships:<id>}, {@link DoorTypes#ALL}), the shared part block {@code medievalships:porte_partie}, the
 * block entity type {@code medievalships:porte}, the creative tab "Portes", and the registry of the doors filled as
 * their chunks load. No world generation, nothing in the vanilla doors changes.
 *
 * <p>Every door resists explosions (the blast resistance of obsidian) and cannot be pushed by a piston (its cells
 * would be torn apart); a door that is not free cannot be broken in survival ({@link DoorCells#mayBreak}).
 */
public final class Doors {
	public static BlockEntityType<DoorBlockEntity> BLOCK_ENTITY;
	public static DoorPartBlock PART;
	private static final Map<DoorType, DoorBlock> BLOCKS = new LinkedHashMap<>();
	private static final Map<DoorType, Item> ITEMS = new LinkedHashMap<>();
	/** Blast resistance of every door cell (obsidian's). */
	public static final float BLAST_RESISTANCE = 1200f;

	private Doors() {
	}

	public static DoorBlock block(DoorType type) {
		return BLOCKS.get(type);
	}

	public static Item item(DoorType type) {
		return ITEMS.get(type);
	}

	public static Map<DoorType, Item> items() {
		return ITEMS;
	}

	public static void register() {
		for (DoorType type : DoorTypes.ALL) {
			RegistryKey<Block> blockKey = RegistryKey.of(RegistryKeys.BLOCK, MedievalShips.id(type.id()));
			boolean wood = type.material() == DoorType.Material.WOOD;
			AbstractBlock.Settings settings = AbstractBlock.Settings.create().registryKey(blockKey)
					.strength(wood ? 3.0f : 5.0f, BLAST_RESISTANCE)
					.sounds(wood ? BlockSoundGroup.WOOD : BlockSoundGroup.METAL)
					.nonOpaque().solid().pistonBehavior(PistonBehavior.BLOCK);
			DoorBlock block = Registry.register(Registries.BLOCK, blockKey, new DoorBlock(type, settings));
			BLOCKS.put(type, block);
			RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, MedievalShips.id(type.id()));
			ITEMS.put(type, Registry.register(Registries.ITEM, itemKey,
					new DoorItem(block, new Item.Settings().registryKey(itemKey).maxCount(16).useBlockPrefixedTranslationKey())));
		}
		RegistryKey<Block> partKey = RegistryKey.of(RegistryKeys.BLOCK, MedievalShips.id("porte_partie"));
		PART = Registry.register(Registries.BLOCK, partKey, new DoorPartBlock(AbstractBlock.Settings.create().registryKey(partKey)
				.strength(3.0f, BLAST_RESISTANCE).sounds(BlockSoundGroup.WOOD).nonOpaque().solid().pistonBehavior(PistonBehavior.BLOCK)));
		BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, MedievalShips.id("porte"),
				FabricBlockEntityTypeBuilder.create(DoorBlockEntity::new, BLOCKS.values().toArray(Block[]::new)).build());

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("doors"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(DoorTypes.CASTLE)))
				.displayName(Text.translatable("itemGroup.medievalships.doors"))
				.entries((context, entries) -> DoorTypes.ALL.forEach(t -> entries.add(ITEMS.get(t))))
				.build());

		// the doors placed otherwise than with their item (a structure, a copy) join the registry when their chunk loads
		ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, world) -> {
			if (be instanceof DoorBlockEntity door && door.doorType() != null) {
				DoorRegistry.get(world.getServer()).ensure(world, be.getPos(), door.doorType(), door.name());
			}
		});
	}
}
