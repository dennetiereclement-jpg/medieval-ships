package fr.medievalships.forge;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.DynamicOps;
import com.mojang.serialization.JsonOps;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.MapLike;
import com.mojang.serialization.RecordBuilder;
import org.jetbrains.annotations.Nullable;

import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.predicate.component.ComponentsPredicate;
import net.minecraft.recipe.IngredientPlacement;
import net.minecraft.recipe.Recipe;
import net.minecraft.recipe.RecipeSerializer;
import net.minecraft.recipe.RecipeType;
import net.minecraft.recipe.book.RecipeBookCategories;
import net.minecraft.recipe.book.RecipeBookCategory;
import net.minecraft.recipe.input.RecipeInput;
import net.minecraft.registry.Registries;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.util.Identifier;
import net.minecraft.world.World;

import fr.medievalships.core.ForgeIngredients;
import fr.medievalships.core.ForgeRecipeSpec;

/**
 * A recipe of the divine forge (1.34.0): the vanilla recipe type {@code medievalships:forge_divine}, read from the data
 * packs ({@code data/<ns>/recipe/*.json}) by the server's recipe manager like any recipe, so a server adds, replaces
 * or removes the forge's recipes with a data pack and {@code /reload}. The JSON (see {@link ForgeRecipeSpec}) is read
 * by the core class for everything plain, then here with the game's registries for the items, the tags, the data
 * components of the ingredients ({@code "components"}, {@code "predicates"}: the vanilla item predicate formats) and
 * the result stack (name, lore, enchantments...).
 *
 * <p>Never in the recipe book, never sent to the clients (1.21.11 sends only recipe displays, and the forge has none):
 * the forge's interface gets what it shows from {@link ForgeMenu}. The forge pays from the player's inventory, not a
 * grid: {@link #matches} and {@link #craft} exist for the interface of {@link Recipe} only.
 */
public final class DivineForgeRecipe implements Recipe<DivineForgeRecipe.Input> {
	/** The stacks a recipe is matched against (the forge passes the player's inventory). */
	public record Input(List<ItemStack> stacks) implements RecipeInput {
		@Override
		public ItemStack getStackInSlot(int slot) {
			return slot >= 0 && slot < stacks.size() ? stacks.get(slot) : ItemStack.EMPTY;
		}

		@Override
		public int size() {
			return stacks.size();
		}
	}

	/** An ingredient resolved: an item or an item tag, a quantity, the data components the stack must have. */
	public record Ingredient(@Nullable Item item, @Nullable TagKey<Item> tag, int count, ComponentsPredicate components) {
		/** Does this stack count as the ingredient (whatever its size)? */
		public boolean test(ItemStack stack) {
			if (stack.isEmpty()) {
				return false;
			}
			boolean kind = tag != null ? stack.isIn(tag) : stack.isOf(item);
			return kind && (components.isEmpty() || components.test(stack));
		}

		/** A stack to show for it in the interface: the item, or the tag's first item (a barrier for an empty tag). */
		public ItemStack icon() {
			if (item != null) {
				return new ItemStack(item, Math.min(count, item.getMaxCount()));
			}
			for (RegistryEntry<Item> e : Registries.ITEM.iterateEntries(tag)) {
				return new ItemStack(e, 1);
			}
			return new ItemStack(Items.BARRIER);
		}

		/** "#ns:path" for a tag, empty for an item (the interface shows the item's name). */
		public String label() {
			return tag != null ? "#" + tag.id() : "";
		}
	}

	private final ForgeRecipeSpec spec;
	private final JsonObject source;
	private final List<Ingredient> ingredients;
	private final ItemStack result;

	DivineForgeRecipe(ForgeRecipeSpec spec, JsonObject source, List<Ingredient> ingredients, ItemStack result) {
		this.spec = spec;
		this.source = source;
		this.ingredients = List.copyOf(ingredients);
		this.result = result;
	}

	/** What the recipe file says (category, time, requirements, commands, name...). */
	public ForgeRecipeSpec spec() {
		return spec;
	}

	public List<Ingredient> ingredients() {
		return ingredients;
	}

	/** The crafted stack (a copy: the recipe's own is never handed out). */
	public ItemStack result() {
		return result.copy();
	}

	/** The quantities of {@link #ingredients()}, in order. */
	public List<Integer> required() {
		List<Integer> out = new ArrayList<>();
		for (Ingredient i : ingredients) {
			out.add(i.count());
		}
		return out;
	}

	/** How the stacks pay for this recipe ({@link ForgeIngredients}). */
	public ForgeIngredients.Plan plan(List<ItemStack> stacks) {
		return ForgeIngredients.plan(required(), new ForgeIngredients.Slots() {
			@Override
			public int size() {
				return stacks.size();
			}

			@Override
			public int count(int slot) {
				ItemStack s = stacks.get(slot);
				return s == null || s.isEmpty() ? 0 : s.getCount();
			}

			@Override
			public boolean matches(int ingredient, int slot) {
				ItemStack s = stacks.get(slot);
				return s != null && ingredients.get(ingredient).test(s);
			}
		});
	}

	@Override
	public boolean matches(Input input, World world) {
		return plan(input.stacks()).complete();
	}

	@Override
	public ItemStack craft(Input input, RegistryWrapper.WrapperLookup registries) {
		return result();
	}

	@Override
	public boolean isIgnoredInRecipeBook() {
		return true;
	}

	@Override
	public boolean showNotification() {
		return false;
	}

	@Override
	public RecipeSerializer<? extends Recipe<Input>> getSerializer() {
		return DivineForge.RECIPE_SERIALIZER;
	}

	@Override
	public RecipeType<? extends Recipe<Input>> getType() {
		return DivineForge.RECIPE_TYPE;
	}

	@Override
	public IngredientPlacement getIngredientPlacement() {
		return IngredientPlacement.NONE;
	}

	@Override
	public RecipeBookCategory getRecipeBookCategory() {
		return RecipeBookCategories.CRAFTING_MISC;
	}

	// ------------------------------------------------------------------ reading

	/** Reads a recipe from its JSON with registry-aware ops (the recipe manager's). */
	static <T> DataResult<DivineForgeRecipe> read(DynamicOps<T> ops, JsonObject json) {
		ForgeRecipeSpec spec;
		try {
			spec = ForgeRecipeSpec.parse(json);
		} catch (ForgeRecipeSpec.Invalid e) {
			String msg = e.getMessage();
			return DataResult.error(() -> "forge divine : " + msg);
		}
		List<Ingredient> ingredients = new ArrayList<>();
		for (ForgeRecipeSpec.Ingredient in : spec.ingredients()) {
			Item item = null;
			TagKey<Item> tag = null;
			if (in.isTag()) {
				Identifier id = Identifier.tryParse(in.tag());
				if (id == null) {
					return DataResult.error(() -> "forge divine : tag invalide " + in.tag());
				}
				tag = TagKey.of(RegistryKeys.ITEM, id);
			} else {
				Identifier id = Identifier.tryParse(in.item());
				Optional<Item> found = id == null ? Optional.empty() : Registries.ITEM.getOptionalValue(id);
				if (found.isEmpty() || found.get() == Items.AIR) {
					return DataResult.error(() -> "forge divine : objet inconnu " + in.item());
				}
				item = found.get();
			}
			ComponentsPredicate components = ComponentsPredicate.EMPTY;
			if (in.hasComponents()) {
				JsonObject o = new JsonObject();
				if (in.components() != null) {
					o.add("components", in.components());
				}
				if (in.predicates() != null) {
					o.add("predicates", in.predicates());
				}
				DataResult<ComponentsPredicate> c = ComponentsPredicate.CODEC.codec().parse(ops, JsonOps.INSTANCE.convertTo(ops, o));
				if (c.error().isPresent()) {
					String msg = c.error().get().message();
					return DataResult.error(() -> "forge divine : composants de " + in.id() + " : " + msg);
				}
				components = c.getOrThrow();
			}
			ingredients.add(new Ingredient(item, tag, in.count(), components));
		}
		DataResult<ItemStack> r = ItemStack.VALIDATED_CODEC.parse(ops, JsonOps.INSTANCE.convertTo(ops, spec.result()));
		if (r.error().isPresent()) {
			String msg = r.error().get().message();
			return DataResult.error(() -> "forge divine : résultat : " + msg);
		}
		JsonObject src = json.deepCopy();
		src.remove("type");
		return DataResult.success(new DivineForgeRecipe(spec, src, ingredients, r.getOrThrow()));
	}

	/** The serializer {@code medievalships:forge_divine}: the JSON read through {@link ForgeRecipeSpec}, written back as read. */
	public static final class Serializer implements RecipeSerializer<DivineForgeRecipe> {
		private static final MapCodec<DivineForgeRecipe> CODEC = new MapCodec<>() {
			@Override
			public <T> Stream<T> keys(DynamicOps<T> ops) {
				return Stream.of("categorie", "duree", "ingredients", "result", "metier", "niveau", "tag", "permission", "commande", "nom",
						"description", "ordre", "essai").map(ops::createString);
			}

			@Override
			public <T> DataResult<DivineForgeRecipe> decode(DynamicOps<T> ops, MapLike<T> input) {
				JsonObject json = new JsonObject();
				for (Pair<T, T> e : (Iterable<Pair<T, T>>) input.entries()::iterator) {
					Optional<String> key = ops.getStringValue(e.getFirst()).result();
					if (key.isPresent()) {
						json.add(key.get(), ops.convertTo(JsonOps.INSTANCE, e.getSecond()));
					}
				}
				return read(ops, json);
			}

			@Override
			public <T> RecordBuilder<T> encode(DivineForgeRecipe recipe, DynamicOps<T> ops, RecordBuilder<T> prefix) {
				for (var e : recipe.source.entrySet()) {
					prefix.add(e.getKey(), JsonOps.INSTANCE.convertTo(ops, e.getValue()));
				}
				return prefix;
			}
		};

		/** Recipes are not sent to the clients in 1.21.11; should a mod do it, the JSON goes as text and is read again. */
		private static final PacketCodec<RegistryByteBuf, DivineForgeRecipe> PACKET_CODEC = PacketCodec.ofStatic(
				(buf, recipe) -> buf.writeString(recipe.source.toString(), 262_144),
				buf -> {
					JsonElement json = JsonParser.parseString(buf.readString(262_144));
					return read(buf.getRegistryManager().getOps(JsonOps.INSTANCE), json.getAsJsonObject()).getOrThrow();
				});

		@Override
		public MapCodec<DivineForgeRecipe> codec() {
			return CODEC;
		}

		@Override
		@Deprecated
		public PacketCodec<RegistryByteBuf, DivineForgeRecipe> packetCodec() {
			return PACKET_CODEC;
		}
	}
}
