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
 * Registration of the tents, the carts, the workshops and the artillery: one block and one block item per
 * {@link TentType} ({@code medievalships:<id>}, {@link TentTypes#PROPS}; a {@link WorkshopBlock} for a workshop, a
 * {@link CannonBlock} for the cannon), one block entity type {@code tent} for all of them but the cannon, which has
 * its own ({@code cannon}, {@link CannonBlockEntity}: a persisted state), the creative tabs "Tentes", "Charrettes",
 * "Ateliers" and "Artillerie", and the collision registry fed by the block entity load / unload events (chunks loading
 * and unloading; placing and breaking go through the block itself).
 */
public final class Tents {
	public static BlockEntityType<TentBlockEntity> BLOCK_ENTITY;
	/** The cannon's block entity type ({@code medievalships:cannon}), drawn by the same renderer as the tents. */
	public static BlockEntityType<CannonBlockEntity> CANNON_BLOCK_ENTITY;
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
			boolean wooden = type.isCart() || type.isWorkshop() || type.isCannon() || type.isTraining();
			AbstractBlock.Settings settings = AbstractBlock.Settings.create().registryKey(blockKey)
					.strength(type.isCannon() ? 2.0f : wooden ? 1.0f : 0.6f)
					.sounds(wooden ? BlockSoundGroup.WOOD : BlockSoundGroup.WOOL).nonOpaque().solid();
			if (type.isTraining()) {
				// 1.19.0: the training areas cannot be broken in survival nor blown up nor pushed (creative or /tent remove)
				settings.strength(-1.0f, 3600000.0f).pistonBehavior(net.minecraft.block.piston.PistonBehavior.BLOCK);
			}
			// the workshops: the same block, plus their particles (forge smoke, enchanting glyphs...); the cannon: its
			// own block entity (the state of the future firing system)
			TentBlock block = Registry.register(Registries.BLOCK, blockKey, type.isWorkshop() ? new WorkshopBlock(type, settings)
					: type.isCannon() ? new CannonBlock(type, settings) : type.isTraining() ? new TrainingAreaBlock(type, settings)
					: new TentBlock(type, settings));
			BLOCKS.put(type, block);
			RegistryKey<Item> itemKey = RegistryKey.of(RegistryKeys.ITEM, MedievalShips.id(type.id()));
			ITEMS.put(type, Registry.register(Registries.ITEM, itemKey,
					new TentItem(block, new Item.Settings().registryKey(itemKey).maxCount(16).useBlockPrefixedTranslationKey())));
		}
		BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, MedievalShips.id("tent"), FabricBlockEntityTypeBuilder
				.create(TentBlockEntity::new, BLOCKS.values().stream().filter(b -> !(b instanceof CannonBlock)).toArray(Block[]::new)).build());
		CANNON_BLOCK_ENTITY = Registry.register(Registries.BLOCK_ENTITY_TYPE, MedievalShips.id("cannon"), FabricBlockEntityTypeBuilder
				.create(CannonBlockEntity::new, BLOCKS.values().stream().filter(b -> b instanceof CannonBlock).toArray(Block[]::new)).build());

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
		RegistryKey<ItemGroup> trainingKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("training"));
		Registry.register(Registries.ITEM_GROUP, trainingKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(TentTypes.TRAINING_DUMMY)))
				.displayName(Text.translatable("itemGroup.medievalships.training"))
				.entries((context, entries) -> TentTypes.TRAINING.forEach(t -> entries.add(ITEMS.get(t))))
				.build());
		RegistryKey<ItemGroup> artilleryKey = RegistryKey.of(RegistryKeys.ITEM_GROUP, MedievalShips.id("artillery"));
		Registry.register(Registries.ITEM_GROUP, artilleryKey, FabricItemGroup.builder()
				.icon(() -> new ItemStack(ITEMS.get(TentTypes.CANNON)))
				.displayName(Text.translatable("itemGroup.medievalships.artillery"))
				.entries((context, entries) -> TentTypes.ARTILLERY.forEach(t -> entries.add(ITEMS.get(t))))
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
		// the training areas' targets (1.19.0)
		fr.medievalships.training.TrainingTargets.register();
	}
}
