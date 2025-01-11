from importlib import reload
import math

import numpy as np
import random

np.set_printoptions(linewidth=120, suppress=True, precision=2)

population_size = 10

# item_info (per 100g)
# [ unsat, sat, carbs_non_sugar, sugars, fibre, protein, sodium ]

items = [
    ("UHT milk",     [0.7, 1.1, 0,    4.8, 0,   3.6, 28 ]),
    ("croissants",   [6.7, 9.1, 41.7, 7.4, 2.5, 9,   280]),
    ("whole milk",   [1.3, 2.3, 0,    4.7, 0,   3.4, 40 ]),
    ("basmati rice", [0.8, 0.1, 32.5, 0.1, 0.6, 3.6, 0  ]),
    ("lentil",       [0.9, 0.2, 61,   2,   11,  25,  6  ]),
    ("mackerel",     [3.2, 0.8, 0,    0,   0,   5.4, 25 ])
]

solutions = np.zeros((population_size, len(items)), dtype=np.float32)
for i in range(population_size):
    solutions[i, random.randrange(len(items))] = 1

items_nutr = np.array(list(i[1] for i in items), dtype=np.float32)

goal_kcal = 2150
macro_kcal = np.array([9, 9, 4, 4, 0, 4, 0], dtype=np.float32)
goal = np.array([60, 5, 280, 20, 30, 80, 1000], dtype=np.float32)

def evaluate(solutions, debug=False):
    # print(solutions)

    # work out the amount of each item in each solution
    values = np.dot(solutions, items_nutr)
    if debug: print("values:", values)

    # sum of each row n is the kcal of that solution
    kcals = np.sum(macro_kcal * values, axis=1)
    if debug: print("kcals:", kcals)

    # adjust values for the correct amount of calories
    kcal_factor = goal_kcal / kcals
    if debug: print("kcal_factor:", kcal_factor)

    adjusted = values * kcal_factor[:, np.newaxis]
    if debug: print("adjusted:", adjusted)

    error = adjusted - goal
    if debug: print("error:", error)

    return error

def anneal():
    k_max = 50000

    for k in range(k_max):
        t = temperature(1 - float(k+1)/k_max)
        print("temp:", t)

        err = evaluate(solutions)
        new_solutions = perturb(solutions, err)
        new_err = evaluate(new_solutions)

        print(solutions)

        for i in range(population_size):
            acc = acceptance(err[0], new_err[0], t)
            print("acc:", acc, "t:", t)
            if acc >= random.random():
                solutions[i] = new_solutions[i]
                print("accepted", i)

    evaluate(solutions, debug=True)
    print("final:", solutions)

def temperature(t):
    return t * t * 80 + 5

def perturb(solutions, err):
    new_solutions = np.copy(solutions)

    for i in range(population_size):
        it = random.randrange(len(items))
        if new_solutions[i][it] > 0:
            new_solutions[i][it] += random.random()
        elif random.random() > 0.3:
            new_solutions[i][it] += random.random()

        new_solutions[i][it] *= 0.7

    return new_solutions

def acceptance(old_errs, new_errs, t):
    e1 = sum(old_errs ** 2)
    e2 = sum(new_errs ** 2)

    if e2 < e1:
        return 1.0
    else:
        return math.exp(-(e2 - e1) / t)

anneal()
