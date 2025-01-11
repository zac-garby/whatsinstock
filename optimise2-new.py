import math
import random
import numpy as np
import sqlite3
from scipy.optimize import minimize

np.set_printoptions(linewidth=120, suppress=True, precision=2)

db = sqlite3.connect("food.db")
db.row_factory = sqlite3.Row
cur = db.cursor()

max_price = 5
cost_factor = 15
goal_factor = 15
num_of_items = 5

def g(item, s):
    if item[s] is None:
        return 0
    return float(item[s])

item_names = [
    "fat_g",
    "sat_fat_g",
    "carbohydrate_g",
    "total_sugar_g",
    "protein_g",

    "retinol_equiv_ug",
    "thiamin_mg",
    "riboflavin_mg",
    "niacin_equiv_mg",
    "vit_b6_mg",
    "vit_b12_ug",
    "folate_ug",
    "vit_c_mg",
    "vit_d_ug",
    "iron_mg",
    "calcium_mg",
    "magnesium_mg",
    "potassium_mg",
    "zinc_mg",
    "copper_mg",
    "iodine_ug",
    "selenium_ug",
    "phosphorus_mg",
    "chloride_mg",
    "sodium_mg",
]

items = []
costs = []
db_items = cur.execute("select * from foods")
n = 0
for item in db_items:
    if item["price_per_100g"] is None or item["match_sureness"] is None or item["ignore"] != 0 or "homemade" in item["name"]:
        continue

    # n += 1
    # if n > 100:
    #     break

    items.append((
        item["name"],
        [
            g(item, "fat_g") - g(item, "sat_fat_g"),
            g(item, "sat_fat_g"),
            g(item, "carbohydrate_g") - g(item, "total_sugar_g"),
            g(item, "total_sugar_g"),
            g(item, "protein_g"),

            g(item, "retinol_equiv_ug"),
            g(item, "thiamin_mg"),
            g(item, "riboflavin_mg"),
            g(item, "niacin_equiv_mg"),
            g(item, "vit_b6_mg"),
            g(item, "vit_b12_ug"),
            g(item, "folate_ug"),
            g(item, "vit_c_mg"),
            g(item, "vit_d_ug"),
            g(item, "iron_mg"),
            g(item, "calcium_mg"),
            g(item, "magnesium_mg"),
            g(item, "potassium_mg"),
            g(item, "zinc_mg"),
            g(item, "copper_mg"),
            g(item, "iodine_ug"),
            g(item, "selenium_ug"),
            g(item, "phosphorus_mg"),
            g(item, "chloride_mg"),
            g(item, "sodium_mg"),
        ],
        item["price_per_100g"]
    ))

    cost = g(item, "price_per_100g")
    costs.append(cost if cost > 0.0025 else 0.2)

items_nutr = np.array(list(i[1] for i in items), dtype=np.float32)

macro_kcal = np.array([
    9, 9, 4, 4, 4,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
], dtype=np.float32)

goal = np.array([
    55, 10, 280, 20, 110,
    700, 1, 1.3, 16.5, 1.4, 3, 200, 40, 10, 8.7, 700, 300, 3500, 9.5, 1.2, 140, 75, 550, 2500, 2400,
], dtype=np.float32)

allow_more = [2] + list(range(4, 23))
# allow_more = [2, 4]

goal_kcal = np.dot(macro_kcal, goal)
print("goal kcal =", goal_kcal)

def evaluate(solution, debug=False):
    # th = sum(solution) * 0.05
    # thresh = np.where(solution > th, solution, 0.0)
    thresh = top_n(solution)
    values = np.dot(thresh, items_nutr)
    kcals = sum(macro_kcal * values)
    kcal_factor = goal_kcal / kcals

    adjusted = values * kcal_factor
    if debug:
        print("                        goal      actual")
        for (n, g, a) in zip(item_names, goal, adjusted):
            print(f"{n:<24}{g:<10.2f}{a:<10.2f}")

    cost = sum(thresh * costs)

    error = adjusted - goal
    if debug: print("error:", error)

    for idx in allow_more:
        if error[idx] > 0:
            error[idx] *= 0.1
        else:
            error[idx] *= 3

    delta = float(sum(error*error / goal))

    if cost > max_price:
        cost *= 10

    return (
        delta * goal_factor + cost * cost_factor,
        adjusted,
        kcal_factor,
    )

def top_n(solution):
    n = num_of_items + 1
    th = np.partition(solution, -n)[-n]
    return np.where(solution > th, solution, 0)

costs = np.array(costs, dtype=np.float32)

def do_solver():
    print("starting the solver")

    solution = np.zeros(len(items), dtype=np.float32)
    for _ in range(num_of_items):
        solution[random.randrange(len(items))] = 1

    x0 = np.random.random(len(items))

    bounds = [(0, 1000) for _ in x0]
    res = minimize(lambda n: evaluate(n)[0], x0, method="powell",
        options={"disp": True}, bounds=bounds)

    solution = res.x
    _, adj, factor = evaluate(solution, debug=False)

    total_solution = sum(solution)
    # solution = np.where(solution * factor * 100 > 10, solution, 0.0)
    solution = top_n(solution)

    ingredients = sorted(list(enumerate(solution)),
        key=lambda x: x[1])

    total_cost = 0

    for i, amount in ingredients:
        adjusted = amount * factor
        if adjusted > 0:
            item = items[i]
            cost = item[2] * adjusted
            total_cost += cost
            print(f"£{cost:.2f} - {adjusted*100:.2f}g  {item[0]}")

    print("---------")
    print(f"£{total_cost:.2f}")

    print()
    evaluate(solution, debug=True)

    return (total_cost, solution)

def main():
    all = []

    for i in range(20):
        (total_cost, solution) = do_solver()
        all.append((total_cost, solution))

    (total_cost, solution) = min(all, key=lambda n: n[0])

    print("\n\n")
    print(f"the best solution ({goal_kcal}kcal):")

    _, adj, factor = evaluate(solution, debug=False)

    total_solution = sum(solution)
    # solution = np.where(solution * factor * 100 > 10, solution, 0.0)
    solution = top_n(solution)

    ingredients = sorted(list(enumerate(solution)),
        key=lambda x: x[1])

    total_cost = 0

    for i, amount in ingredients:
        adjusted = amount * factor
        if adjusted > 0:
            item = items[i]
            cost = item[2] * adjusted
            total_cost += cost
            print(f"£{cost:.2f} - {adjusted*100:.2f}g  {item[0]}")

    print("---------")
    print(f"£{total_cost:.2f}")

    print()
    evaluate(solution, debug=True)

if __name__ == "__main__":
    main()
