import math
import random
import numpy as np
import sqlite3
from scipy.optimize import minimize

np.set_printoptions(linewidth=120, suppress=True, precision=2)

db = sqlite3.connect("food.db")
db.row_factory = sqlite3.Row
cur = db.cursor()

population_size = 10

# item_info (per 100g)
# [ unsat, sat, carbs_non_sugar, sugars, protein, sodium ]

def g(item, s):
    if item[s] is None:
        return 0
    return float(item[s])

items = []
costs = []
db_items = cur.execute("select * from foods")
for item in db_items:
    if item["price_per_100g"] is None:
        continue

    items.append((
        item["name"],
        [
            g(item, "fat_g") - g(item, "sat_fat_g"),
            g(item, "sat_fat_g"),
            g(item, "carbohydrate_g") - g(item, "total_sugar_g"),
            g(item, "total_sugar_g"),
            g(item, "protein_g"),
            g(item, "sodium_mg"),
        ],
        item["price_per_100g"]
    ))

    costs.append(float(item["price_per_100g"]))

costs = np.array(costs, dtype=np.float32)

solution = np.zeros(len(items), dtype=np.float32)
solution[random.randrange(len(items))] = 1

items_nutr = np.array(list(i[1] for i in items), dtype=np.float32)

goal_kcal = 2150
macro_kcal = np.array([9, 9, 4, 4, 4, 0], dtype=np.float32)
goal = np.array([60, 5, 280, 20, 80, 1000], dtype=np.float32)

def evaluate(solution, debug=False):
    # work out the amount of each item in each solution
    values = np.dot(solution, items_nutr)
    if debug: print("values:", values)

    # sum of each row n is the kcal of that solution
    kcals = sum(macro_kcal * values)
    if debug: print("kcals:", kcals)


    # adjust values for the correct amount of calories
    kcal_factor = goal_kcal / kcals
    if debug: print("kcal_factor:", kcal_factor)

    if debug: print("actual solution:", solution * kcal_factor)

    adjusted = values * kcal_factor
    if debug:
        print("    goal:", goal)
        print("adjusted:", adjusted)

    error = adjusted - goal
    if debug: print("error:", error)

    delta = math.sqrt(sum(error*error / goal))
    if debug: print("delta:", delta)

    deduction = np.sum(solution * kcal_factor > 0.1) * 100

    return (float(delta) - deduction * deduction, adjusted, kcal_factor)

x0 = np.random.random(len(items))

bounds = [(0, None) for _ in x0]
res = minimize(lambda n: evaluate(n)[0], x0, method="powell",
    options={"xatol": 1e-3, "disp": True}, bounds=bounds)

solution = res.x
_, adj, factor = evaluate(solution, debug=True)

ingredients = sorted(list(enumerate(solution)),
    key=lambda x: x[1])

total_cost = 0

for i, amount in ingredients:
    adjusted = amount * factor
    if adjusted > 0.01:
        item = items[i]
        cost = item[2] * adjusted
        total_cost += cost
        print(f"£{cost:.2f} - {adjusted*100:.2f}g  {item[0]}")

print("---------")
print(f"£{total_cost}")
