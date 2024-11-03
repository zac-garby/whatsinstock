from typing import Any, Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer, util

import numpy as np

import math
import sqlite3
import csv
import json
import torch

db = sqlite3.connect("food.db")
db.row_factory = sqlite3.Row

model = SentenceTransformer("all-mpnet-base-v2")

type ScrapedItem = Dict[str, str]
type NutrItem = Dict[str, Any]

def main_old():
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

def main():
    with open("all_product_info.json", mode="r") as file:
        data = json.load(file)

    # later: try and guess this?
    data = [ item for item in data if item["price"]["unitOfMeasure"] != "each" ]

    if len(input("press enter to load embeddings, or anything else to regenerate them and quit:").strip()) > 0:
        print("starting to embed names")
        data_names = [ item["title"] for item in data ]
        data_title_embs = model.encode(data_names, convert_to_tensor=True)
        print("embedded all names")
        torch.save(data_title_embs, "embeddings.pt")
        return
    else:
        data_title_embs = torch.load("embeddings.pt")
        print("loaded embeddings")

    cur = db.cursor()
    db_items = cur.execute("select * from foods")
    mappings = {}

    for item in db_items:
        name = normalise_string(item["name"])
        print(f"matching {name}:")

        this_emb = model.encode(name, convert_to_tensor=True)
        sim_scores = model.similarity(this_emb, data_title_embs)[0]
        scores, idxs = torch.topk(sim_scores, k=5)

        if scores[0] < 0.6:
            print(f"  no match. best score was {scores[0]}")
            continue

        choice = data[idxs[0]]
        print(f"  got match: {choice['title']}")
        mappings[item["id"]] = choice["id"]

    cur.close()

    cur = db.cursor()

    print("done all! updating sql database")

    for item, choice in mappings.items():
        print("updating database", f"update foods set tesco_item_id = {choice} where id = {item}")
        cur.execute(f"update foods set tesco_item_id = {choice} where id = {item}")

    cur.close()
    db.commit()
    db.close()

def match_keywords(kws: List[str], s: str) -> Tuple[int, float]:
    matches = sum(1 for k in kws if k in s)
    counts = sum(len(k) for k in kws if k in s)
    score = (counts * 100.0) / (len(s) - counts)
    return (matches, score)

def normalise_string(s: str) -> str:
    kws = [ kw
            for kw in map(use_keyword, s.split())
            if kw is not None ]

    return " ".join(kws)

def use_keyword(kw: str) -> Optional[str]:
    kw = kw.lower().replace("'", "").replace(",", "")

    if not kw.isalpha() or kw in [
        "pack", "packet", "tesco", "all", "box", "carton",
        "x", "litre", "liter", "each", "skin", "flesh",
        "and", "homemade"]:
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
