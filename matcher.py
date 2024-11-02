from typing import Any, Dict, List, Optional

import math
import sqlite3
import csv

db = sqlite3.connect("food.db")
db.row_factory = sqlite3.Row
cur = db.cursor()

type ScrapedItem = Dict[str, str]
type NutrItem = Dict[str, Any]

def main():
    with open("example.csv", mode="r", newline="") as file:
        scraped_items = csv.DictReader(file)

        for item in scraped_items:
            print("name:", item["name"])
            kws = item["name"].split()
            guesses = guess_by_keywords(kws)
            nutr = get_item_nutrition(item)

            print(f"  vitamins = {unpack_vitamins(item['vitamins'])}")

            for guess in guesses:
                dist = nutrient_distance(nutr, guess)
                guess['dist'] = dist
                guess['adjusted'] = 10 * guess['score'] / guess['dist']

            guesses.sort(key=lambda g: g['adjusted'], reverse=True)

            for i, guess in enumerate(guesses[:3]):
                print(f"  Guess {i+1}: {guess['name']}:")
                print(f"    score = {guess['score']:.2f}, dist = {guess['dist']:.2f}, adjusted score = {guess['adjusted']:.2f}")

            print()

def use_keyword(kw: str) -> Optional[str]:
    kw = kw.lower().replace("'", "")

    if not kw.isalpha() or kw in [
        "pack", "packet", "tesco", "all", "box", "carton",
        "x", "litre", "liter"]:
        return None

    return kw

def guess_by_keywords(kws: List[str]) -> List[NutrItem]:
    kws = [ kw for kw in map(use_keyword, kws) if kw is not None ]
    print("kws:", kws)

    clauses = " + ".join(f"(case when name like '%{kw}%' then {len(kw)} else 0 end)" for kw in kws)
    clauses_no_len = " + ".join(f"(name like '%{kw}%')" for kw in kws)

    query = f"""
    select *, {clauses_no_len} as matches, (({clauses} * 100.0) / length(name)) as score
    from foods
    where matches = (select max({clauses_no_len}) from foods)
    order by score desc
    limit 10
    """

    items = list(map(dict, cur.execute(query)))

    return items

def unpack_vitamins(item: str) -> Dict[str,float]:
    vits = {}
    parts = item.split(";")

    for part in parts:
        match part.split(":"):
            case [n, val]:
                vits[n] = float(val)

    return vits

def get_item_nutrition(item: ScrapedItem):
    return {
        "energy_kcal": float(item["kcal"]),
        "fat_g": float(item["fat"]),
        "sat_fat_g": float(item["saturates"]),
        "carbohydrate_g": float(item["carbs"]),
        "total_sugar_g": float(item["sugars"]),
        "protein_g": float(item["protein"]),
        "sodium_mg": float(item["salt"]) * 400,
    }

def nutrient_distance(a, b):
    keys = [ "protein_g", "fat_g", "carbohydrate_g", "energy_kcal", "total_sugar_g", "sodium_mg" ]
    d = 0

    for k in keys:
        if k in a and k in b:
            diff = a[k] - b[k]
            d += diff * diff

    return math.sqrt(d)

if __name__ == "__main__":
    main()
