import re
import sqlite3
import json

with open("all_product_info.json", "r") as file:
    data = json.load(file)

prices = { d["id"]: d["price"] for d in data }

db = sqlite3.connect("food.db")
db.row_factory = sqlite3.Row

cur = db.cursor()
cur.execute("select * from foods")

db_items = cur.fetchall()
cur.close()

cur = db.cursor()
for row in db_items:
    item_id = row["tesco_item_id"]
    if item_id is None:
        continue

    price = prices[item_id]
    unit_price = price["unitPrice"]
    measure = price["unitOfMeasure"]

    grams = None

    g = re.findall("(\\d+)g", measure)
    kg = re.findall("(\\d+)kg", measure)
    ml = re.findall("(\\d+)ml", measure)
    cl = re.findall("(\\d+)cl", measure)

    if len(g) > 0:
        grams = int(g[0])
    elif len(kg) > 0:
        grams = int(kg[0]) * 1000
    elif len(ml) > 0:
        grams = int(ml[0])
    elif len(cl) > 0:
        grams = int(cl[0]) * 10
    elif "litre" in measure:
        grams = 1000
    elif "kg" in measure:
        grams = 1000
    else:
        print("unknown measure:", measure)
        grams = int(input("> "))

    price_per_100 = 100 * unit_price / grams
    cur.execute(f"update foods set price_per_100g = {price_per_100} where tesco_item_id = {item_id}")

cur.close()
db.commit()
db.close()
