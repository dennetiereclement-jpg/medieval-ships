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
import net.minecraft.component.ComponentType;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.text.Text;
import net.minecraft.util.Rarity;

import fr.medievalships.MedievalShips;
import fr.medievalships.core.DoorKeys;
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
 *
 * <p>1.32.0: the keys ({@code medievalships:cle}, {@code medievalships:cle_universelle}, in the tab after the doors,
 * one per stack, no recipe) and the data component of a bound key {@code medievalships:serrure} ({@link KeyLock}).
 */
public final class Doors {
	public static BlockEntityType<DoorBlockEntity> BLOCK_ENTITY;
	public static DoorPartBlock PART;
	/** The lock and door label of a bound key (1.32.0). */
	public static ComponentType<KeyLock> LOCK;
	/** The key ({@code medievalships:cle}) and the administrators' master key ({@code medievalships:cle_universelle}). */
	public static KeyItem KEY, MASTER_KEY;
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
		LOCK = Registry.register(Registries.DATA_COMPONENT_TYPE, MedievalShips.id("serrure"),
				ComponentType.<KeyLock>builder().codec(KeyLock.CODEC).packetCodec(KeyLock.PACKET_CODEC).build());
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
		RegistryKey<Item> keyKey = RegistryKey.of(RegistryKeys.ITEM, MedievalShips.id(DoorKeys.KEY));
		KEY = Registry.register(Registries.ITEM, keyKey, new KeyItem(new Item.Settings().registryKey(keyKey).maxCount(1), false));
		RegistryKey<Item> masterKey = RegistryKey.of(RegistryKeys.ITEM, MedievalShips.id(DoorKeys.MASTER));
		MASTER_KEY = Registry.register(Registries.ITEM, masterKey, new KeyItem(new Item.Settings().registryKey(masterKey).maxCount(1)
				.rarity(Rarity.EPIC).component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true), true));

		RegistryKey<ItemGroup> groupKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("doors"));
		Registry.register(Registries.ITEM_GROUP, groupKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(DoorTypes.CASTLE)))
				.displayName(Text.translatable("itemGroup.medievalships.doors"))
				.entries((context, entries) -> {
					DoorTypes.ALL.forEach(t -> entries.add(ITEMS.get(t)));
					entries.add(KEY);
					entries.add(MASTER_KEY);
				})
				.build());

		// the doors placed otherwise than with their item (a structure, a copy) join the registry when their chunk loads,
		// and every door's lock is known there (1.33.0: a lock shared in 1.32.0 or copied is renewed when a key is bound)
		ServerBlockEntityEvents.BLOCK_ENTITY_LOAD.register((be, world) -> {
			if (be instanceof DoorBlockEntity door && door.doorType() != null) {
				DoorRegistry.get(world.getServer()).ensure(world, be.getPos(), door.doorType(), door.name(), door.lock());
			}
		});
	}
}
