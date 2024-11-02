#! /usr/bin/env python3

import json
import sys

import bs4


def load_data(file):
    with open(file, "rt") as fp:
        soup = bs4.BeautifulSoup(fp, features="html.parser")
    data_elem = soup.find(name="script", type="application/discover+json")
    data = data_elem.string
    parsed_data = json.loads(data)
    useful_data: dict = parsed_data["mfe-orchestrator"]["props"]["apolloCache"]
    # Remove unneeded keys.
    del useful_data["ROOT_QUERY"]
    return useful_data.values()


def reduce_data(products: list[dict]):
    """Remove unneeded keys."""

    for product in products:
        if product["__typename"] != "ProductType":
            continue
        useful_product = {
            "id": product["id"],
            "title": product["title"],
            "defaultImageUrl": product["defaultImageUrl"],
            "shelfName": product["shelfName"],
            "price": product["price"],
        }
        yield useful_product


def process_file(file):
    products = reduce_data(load_data(file))
    for product in products:
        print(json.dumps(product, indent=2))


for file in sys.argv[1:]:
    process_file(file)