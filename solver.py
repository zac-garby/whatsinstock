#! /usr/bin/env python3

import sys
import numpy as np
from scipy.spatial import distance
import sqlite3

# Make numpy print sensibly.
np.set_printoptions(linewidth=120, suppress=True, precision=2)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


# Tuneable constants:
male_target_nutrients = {
    "price_per_100g": 0.1,
    # Macronutrients
    "protein_g": 55.5,
    "fat_g": 97,
    "carbohydrate_g": 333,
    "total_sugar_g": 33,
    "sat_fat_g": 31,
    # Vitamins and minerals
    "sodium_mg": 2400,
    "potassium_mg": 3500,
    "calcium_mg": 700,
    "magnesium_mg": 300,
    "phosphorus_mg": 550,
    "iron_mg": 8.7,
    "copper_mg": 1.2,
    "zinc_mg": 9.5,
    "chloride_mg": 2500,
    "manganese_mg": 300,
    "selenium_ug": 75,
    "iodine_ug": 140,
    "retinol_equiv_ug": 700,  # Vitamin A
    "vit_d_ug": 10,
    "thiamin_mg": 1,
    "riboflavin_mg": 1.3,
    "niacin_equiv_mg": 16.5,
    "vit_b6_mg": 1.4,
    "vit_b12_ug": 1.5,
    "folate_ug": 200,
    "vit_c_mg": 40,
}
female_target_nutrients = {
    "price_per_100g": 0.1,
    # Macronutrients
    "protein_g": 45.0,
    "fat_g": 78,
    "carbohydrate_g": 267,
    "total_sugar_g": 27,
    "sat_fat_g": 24,
    # Vitamins and minerals
    "sodium_mg": 2400,
    "potassium_mg": 3500,
    "calcium_mg": 700,
    "magnesium_mg": 300,
    "phosphorus_mg": 550,
    "iron_mg": 8.7,
    "copper_mg": 1.2,
    "zinc_mg": 7.0,
    "chloride_mg": 2500,
    "manganese_mg": 270,
    "selenium_ug": 60,
    "iodine_ug": 140,
    "retinol_equiv_ug": 600,  # Vitamin A
    "vit_d_ug": 10,
    "thiamin_mg": 0.8,
    "riboflavin_mg": 1.1,
    "niacin_equiv_mg": 13.2,
    "vit_b6_mg": 1.2,
    "vit_b12_ug": 1.5,
    "folate_ug": 200,
    "vit_c_mg": 40,
}
target_nutrients = male_target_nutrients
grams_per_step = 1


# Load ingredient data.
ingredients = {}
tesco_ids = {}
with sqlite3.connect("food.db") as db:
    db.row_factory = dict_factory

    for row in db.execute(
        "SELECT * FROM foods WHERE tesco_item_id IS NOT NULL and price_per_100g IS NOT NULL"
    ):
        nutrients = []
        for key in row:
            if key in target_nutrients.keys():
                if row[key]:
                    nutrients.append(row[key])
                else:
                    nutrients.append(0)
        ingredients[row["name"]] = np.array(nutrients, dtype=np.double)
        del nutrients

    for row in db.execute(
        "SELECT name,tesco_item_id FROM foods WHERE tesco_item_id IS NOT NULL and price_per_100g IS NOT NULL"
    ):
        tesco_ids[row["name"]] = row["tesco_item_id"]


# Calculate variables.
goal = np.array(list(target_nutrients.values()), dtype=np.double)
origin = np.zeros(len(target_nutrients), dtype=np.double)
nutrient_weighting = 1 / goal
original_distance = distance.euclidean(goal, origin, nutrient_weighting)
target_distance = original_distance / 20  # Within 5%.
current_nutrients = origin.copy()
current_distance = original_distance
last_distance = original_distance + 1
fraction_of_100_grams = grams_per_step / 100
chosen_ingredients = {}


def find_optimal_ingredient(
    current_nutrients, ingredients, goal, fraction_of_100_grams
) -> str:
    ingredient_distances = {}
    for key, value in ingredients.items():
        new_position = current_nutrients + value * fraction_of_100_grams
        ingredient_distances[key] = distance.euclidean(
            new_position, goal, nutrient_weighting
        )
    return min(ingredient_distances, key=lambda x: ingredient_distances[x])


assert len(goal) == len(origin)
assert len(origin) == len(
    ingredients["White sauce, savoury, made with skimmed milk, homemade"]
)
for ingredient in ingredients:
    if not np.isfinite(ingredients[ingredient]).all():
        raise ValueError(
            f"{ingredient} has non-finite values!\n{ingredients[ingredient]}"
        )

while current_distance < last_distance:
    last_distance = current_distance
    optimal_ingredient = find_optimal_ingredient(
        current_nutrients, ingredients, goal, fraction_of_100_grams
    )
    # Update current position.
    current_nutrients = (
        current_nutrients + ingredients[optimal_ingredient] * fraction_of_100_grams
    )
    current_distance = distance.euclidean(current_nutrients, goal, nutrient_weighting)
    # Update totals of chosen ingredients.
    chosen_ingredients[optimal_ingredient] = (
        chosen_ingredients.get(optimal_ingredient, 0) + grams_per_step
    )
    print(
        f"Added {grams_per_step} grams of {optimal_ingredient}, giving a nutrient of:\n{current_nutrients}\nWe are now {current_distance:g} away.",
        file=sys.stderr,
    )
    # Safety check to prevent infinite loops.
    if current_nutrients[6] > 3000:
        raise ValueError("Too salty.")


chosen_full_ingredients = {}
for ingredient in chosen_ingredients:
    chosen_full_ingredients[ingredient] = {
        "amount": chosen_ingredients[ingredient],
        "price": (chosen_ingredients[ingredient] * ingredients[ingredient][0]) / 100,
        "tesco_item_id": tesco_ids[ingredient],
    }

print(f"\n{'-'*80}\n", file=sys.stderr)
print(f"{'Ingredient':32}\tAmount (g)\tPrice (£)\tURL")
for ingredient in chosen_full_ingredients:
    print(
        f"{ingredient:32}\t{chosen_full_ingredients[ingredient]['amount']:8.1f} g\t£{chosen_full_ingredients[ingredient]['price']:8.2f}\thttps://www.tesco.com/groceries/en-GB/products/{chosen_full_ingredients[ingredient]['tesco_item_id']}"
    )
total_price = sum(
    chosen_full_ingredients[ingredient]["price"]
    for ingredient in chosen_full_ingredients
)
print(f"\nTotal Price: £{total_price:.2f}")
print(
    f"{', '.join(target_nutrients)}\nOptimal Nutrients:\n{', '.join(f'{i:.2f}' for i in goal)}\nActual Nutrients:\n{', '.join(f'{i:.2f}' for i in current_nutrients)}"
)
