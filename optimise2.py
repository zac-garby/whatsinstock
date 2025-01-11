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
n = 0
for item in db_items:
    if item["price_per_100g"] is None or item["ignore"] != 0:
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
            # g(item, "sodium_mg"),
        ],
        item["price_per_100g"]
    ))

    cost = g(item, "price_per_100g")
    costs.append(cost if cost > 0.0025 else 0.2)

costs = np.array(costs, dtype=np.float32)

solution = np.zeros(len(items), dtype=np.float32)
solution[random.randrange(len(items))] = 1

items_nutr = np.array(list(i[1] for i in items), dtype=np.float32)

macro_kcal = np.array([9, 9, 4, 4, 4], dtype=np.float32)
goal = np.array([60, 10, 280, 20, 120], dtype=np.float32)
goal_kcal = np.dot(macro_kcal, goal)
print("goal kcal =", goal_kcal)

def evaluate(solution, debug=False):
    total_solution = sum(solution)
    th = total_solution / 10.0
    thresh = np.where(solution < th, solution, 0.0)
    if debug: print("thresh=", thresh, "th=", th)

    # work out the amount of each item in each solution
    values = np.dot(thresh, items_nutr)
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

    cost = sum(solution * costs)

    error = adjusted - goal
    if debug: print("error:", error)

    if error[4] > 0:
        error[4] = 0

    delta = sum(error*error / goal)
    if debug: print("delta:", delta)

    # deduction = np.sum(solution * kcal_factor > 0.1) * 100
    deduction = np.sum(solution > th) * 100

    # return (float(delta) - deduction * deduction, adjusted, kcal_factor)
    return (
        float(delta) * 35 + cost * 2 + deduction,
        adjusted,
        kcal_factor,
    )

x0 = np.random.random(len(items))

bounds = [(0, None) for _ in x0]
res = minimize(lambda n: evaluate(n)[0], x0, method="powell",
    options={"disp": True}, bounds=bounds)

solution = res.x
_, adj, factor = evaluate(solution, debug=False)
print(factor)

total_solution = sum(solution)
solution = np.where(solution * factor * 100 > 10, solution, 0.0)

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
print(f"£{total_cost}")

print()
evaluate(solution, debug=True)
