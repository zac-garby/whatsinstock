#! /usr/bin/env python3

import numpy as np
from scipy.spatial import distance
import json

# Tuneable constants:
grams_per_step = 1
goal = np.array((70, 10, 333, 15, 30, 80, 2000), dtype=np.double)
origin = np.array((0, 0, 0, 0, 0, 0, 0), dtype=np.double)
nutrient_weighting = 1 / goal
original_distance = distance.euclidean(goal, origin, nutrient_weighting)
target_distance = original_distance / 20  # Within 5%.


# Ingredient information (per 100g)
# [ fat, saturated fat, carbs, sugars, fibre, protein, sodium ]
ingredients = {
    "UHT milk": np.array([1.8, 1.1, 4.8, 4.8, 0, 3.6, 28], dtype=np.double),
    "croissants": np.array([15.8, 9.1, 49.1, 7.4, 2.5, 9, 280], dtype=np.double),
    "whole milk": np.array([3.6, 2.3, 4.7, 4.7, 0, 3.4, 40], dtype=np.double),
    "basmati rice": np.array([0.9, 0.1, 32.6, 0.1, 0.6, 3.6, 0], dtype=np.double),
    "Green Peppers": np.array([0.3, 0.1, 2.6, 2.4, 1.6, 0.8, 0.01], dtype=np.double),
    "Radish Pack": np.array([0.4, 0.1, 1.4, 1.4, 1.5, 0.7, 0.05], dtype=np.double),
    "Brown Onions": np.array([0.2, 0, 7.9, 5.6, 1.4, 1.2, 0.01], dtype=np.double),
    "Beansprouts": np.array([2.8, 0.2, 2.1, 2.1, 1.8, 2.5, 0.03], dtype=np.double),
    "Lard": np.array([99.8, 44.0, 0, 0, 0, 0, 0.01], dtype=np.double),
    "Pearl Barley": np.array([0.8, 0.2, 20.8, 0.2, 4.5, 3.0, 0.02], dtype=np.double),
    "Red Split Lentils": np.array(
        [0.8, 0.1, 11.7, 0.1, 6.1, 7.3, 0.01], dtype=np.double
    ),
    "Salt": np.array([0, 0, 0, 0, 0, 0, 40000.0], dtype=np.double),
}


def find_optimal_ingredient(
    current_nutrients, ingredients, goal, fraction_of_100_grams
) -> str:
    ingredient_distances = {
        key: distance.euclidean(
            current_nutrients + value * fraction_of_100_grams, goal, nutrient_weighting
        )
        for key, value in ingredients.items()
    }
    return min(ingredient_distances, key=lambda x: ingredient_distances[x])


current_nutrients = origin.copy()
current_distance = original_distance
last_distance = original_distance + 1
fraction_of_100_grams = grams_per_step / 100
chosen_ingredients = {}

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
        f"Added {grams_per_step} grams of {optimal_ingredient}, giving a nutrient of:\n{current_nutrients}\nWe are now {current_distance} away."
    )
    # Safety check to prevent infinite loops.
    if current_nutrients[6] > 2500:
        raise ValueError("Too salty.")

print(f"Optimal Nutrients: {goal}\nAchieve Nutrients: {current_nutrients}")
print(f"Ingredients:\n{json.dumps(chosen_ingredients, indent=2)}")
