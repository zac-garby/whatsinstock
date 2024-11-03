from importlib import reload

import numpy as np
import random

population_size = 10

# item_info (per 100g)
# [ fat, satfat, carbs, sugars, fibre, protein, sodium ]

items = [
    ("UHT milk",     [1.8,  1.1, 4.8,  4.8, 0,   3.6, 28 ]),
    ("croissants",   [15.8, 9.1, 49.1, 7.4, 2.5, 9,   280]),
    ("whole milk",   [3.6,  2.3, 4.7,  4.7, 0,   3.4, 40 ]),
    ("basmati rice", [0.9,  0.1, 32.6, 0.1, 0.6, 3.6, 0  ]),
]

solutions = np.zeros((population_size, len(items)), dtype=np.float32)
for i in range(population_size):
    solutions[i, random.randrange(len(items))] = 1

items_nutr = np.array(list(i[1] for i in items), dtype=np.float32)
goal = np.array([70, 10, 333, 15, 30, 80, 2000], dtype=np.float32)

def evaluate():
    values = np.dot(solutions, items_nutr)
    error = values - goal
    return error

def iterate():
    old_err = evaluate()
