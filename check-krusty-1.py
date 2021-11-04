#!/usr/bin/env python

"""A _very_ primitive script to check that the API for Krusty-2021 is
implemented well enough to pass the project.

"""

from collections import Counter
from urllib.parse import quote, unquote
import itertools
import json
import random
import re
import requests
import sys
import textwrap


HOST="localhost"
PORT=8888

CUSTOMER_INPUT = [
    ("Bullar och bong", "Bakgatan 4, Lund"),
    ("Café Ingalunda", "Återvändsgränden 1, Kivik"),
    ("Kakbak HB", "Degkroken 8, Malmö"),
]

INGREDIENT_INPUT = [
    ("Flour", "g"),
    ("Butter", "g"),
    ("Icing sugar", "g"),
    ("Roasted chopped nuts", "g"),
    ("Fine-ground nuts", "g"),
    ("Ground roasted nuts", "g"),
    ("Bread crumbs", "g"),
    ("Sugar", "g"),
    ("Egg whites", "ml"),
    ("Chocolate", "g"),
    ("Marzipan", "g"),
    ("Eggs", "g"),
    ("Potato starch", "g"),
    ("Wheat flour", "g"),
    ("Sodium bicarbonate", "g"),
    ("Vanilla", "g"),
    ("Chopped almonds", "g"),
    ("Cinnamon", "g"),
    ("Vanilla sugar", "g"),
]

INGREDIENT_DELIVERY_INPUT = [
    ("Flour", 500_000),
    ("Butter", 200_000),
    ("Icing sugar", 100_000),
    ("Roasted chopped nuts", 200_000),
    ("Fine-ground nuts", 200_000),
    ("Ground roasted nuts", 200_000),
    ("Bread crumbs", 150_000),
    ("Sugar", 500_000),
    ("Egg whites", 350_000),
    ("Chocolate", 300_000),
    ("Marzipan", 100_000),
    ("Eggs", 300_000),
    ("Potato starch", 100_000),
    ("Wheat flour", 600_000),
    ("Sodium bicarbonate", 25_000),
    ("Vanilla", 100_000),
    ("Chopped almonds", 250_000),
    ("Cinnamon", 40_000),
    ("Vanilla sugar", 40_000),
]


COOKIE_INPUT = [
    {
        "name": "Tango",
        "recipe": [
            {
                "ingredient": "Butter",
                "amount": 200
            },
            {
                "ingredient": "Sugar",
                "amount": 250
            },
            {
                "ingredient": "Flour",
                "amount": 300
            },
            {
                "ingredient": "Sodium bicarbonate",
                "amount": 4
            },
            {
                "ingredient": "Vanilla",
                "amount": 2
            },
        ]
    },
    {
        "name": "Almond delight",
        "recipe": [
            {
                "ingredient": "Butter",
                "amount": 400
            },
            {
                "ingredient": "Sugar",
                "amount": 270
            },
            {
                "ingredient": "Chopped almonds",
                "amount": 279
            },
            {
                "ingredient": "Flour",
                "amount": 400
            },
            {
                "ingredient": "Cinnamon",
                "amount": 10
            },
        ]
    }
]



def abort(msg):
    print("\n\n   === Aborting: " + msg + " ===\n\n")
    exit(1)


def url(resource):
    return f"http://{HOST}:{PORT}{resource}"


def require(found, expected, *msg):
    if not found == expected:
        for m in msg:
            print(f"    {m}")
        else:
            print(f"    -> expected: {expected}, got: {found}")
            exit(1)


def require_close_enough(value, expected_value, message):
    if abs(value - expected_value)/expected_value > 0.01:
        abort(message)


def removeprefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s


def testing(subject):
    print(f"Testing {subject} ", end="")


def ok():
    print("-> OK")


def require_same_values(lhs, rhs, msg):
    if not set(lhs) == set(rhs):
        abort(msg)


def check_all():
    try:
        testing("reset")
        resource = url("/reset")
        r = requests.post(resource)
        require(r.status_code, 205, "Wrong status code from reset")
        # don't bother with the location for reset...
        ok()

        testing("add/get customers")
        resource = url("/customers")
        for c_name, c_addr in CUSTOMER_INPUT:
            payload = {"name": c_name, "address": c_addr}
            r = requests.post(resource, json=payload)
            require(r.status_code, 201, "Wrong status code from POST /customers")
            location = r.json()['location']
            cid = removeprefix(location, "/customers/")
            require(cid, quote(c_name), "Wrong id from POST /customers/")
            # new_resource = url(location)
            # r = requests.get(new_resource)
            # customer = r.json()['data']
            # require(customer['name'], unquote(cid))
            # require(customer['address'], c_addr)
        ok()

        
        testing("add/get ingredients")
        for ingredient_name, unit in INGREDIENT_INPUT:
            payload = {"ingredient": ingredient_name, "unit": unit}
            resource = url("/ingredients")
            r = requests.post(resource, json=payload)
            require(r.status_code, 201, "Wrong status code from POST on /ingredients")
            location = r.json()['location']
            ingredient_id = removeprefix(location, "/ingredients/")
            new_resource = url(location)
        ok()

        testing("add/get ingredients/.../deliveries")
        for ingredient_name, quantity in INGREDIENT_DELIVERY_INPUT:
            payload = {"quantity": quantity, "deliveryTime": "2021-03-19 10:30:00"}
            r = requests.post(url(f"/ingredients/{quote(ingredient_name)}/deliveries"), json=payload)
            require(r.status_code, 201, "Wrong status code from POST on /ingredientDeliveries")
        ok()
        

        
        testing("add/get cookies")
        resource = url("/cookies")
        for cookie in COOKIE_INPUT:
            payload = cookie
            r = requests.post(resource, json=cookie)
            require(r.status_code, 201, "Wrong status code from POST on /cookies")
            location = r.json()['location']
            cid = removeprefix(location, "/cookies/")
            require(cid, quote(cookie['name']), "Wrong id from POST /cookies")
            # new_resource = url(location)
            # r = requests.get(new_resource)
            # found_cookie = r.json()['data']
            # require(found_cookie['name'], unquote(cid), "Wrong id from GET /cookies")
            # We'll test the recipe when we bake (below)
        ok()

        testing("if all cookies are saved")
        found_cookies = [c['name'] for c in requests.get(resource).json()['data']]
        actual_cookies = [c['name'] for c in COOKIE_INPUT]
        require_same_values(found_cookies, actual_cookies, f"GET /cookies returned the wrong cookies")
        ok()

        testing("baking a number of pallets")
        ordered_cookies = ["Tango", "Almond delight", "Tango", "Almond delight", "Tango"] * 100
        count = 0
        pallet_ids = []
        for cookie in ordered_cookies:
            payload = {"cookie": cookie}
            r = requests.post(url("/pallets"), json=payload)
            if r.status_code == 422:
                break
            count += 1
            location = r.json()["location"]
            pallet_ids.append(removeprefix(location, "/pallets/"))
        require(count, 13, "Wrong number of pallets...")
        ok()

        testing("the pallet inventory")
        resource = url("/pallets")
        r = requests.get(resource)
        require(r.status_code, 200, "Wrong status from GET on /pallets")
        pallet_counter = Counter()
        expected_counter = Counter()
        for found_pallet in r.json()['data']:
            pallet_counter.update([found_pallet['cookie']])
        for cookie in ordered_cookies[:count]:
            expected_counter.update([cookie])
        require(pallet_counter, expected_counter, "The number of pallets of each cookie doesn't add up")
        ok()

        testing("adding butter and baking some more")
        payload = {"deliveryTime": "2021-03-20 10:30:00", "quantity": 400_000}
        r = requests.post(url(f"/ingredients/{quote('Butter')}/deliveries"), json=payload)
        require(r.status_code, 201, "Wrong status code from POST on /ingredients/.../deliveries")
        
        for cookie in ordered_cookies:
            payload = {"cookie": cookie}
            r = requests.post(url("/pallets"), json=payload)
            if r.status_code == 422:
                break
            count += 1
            location = r.json()["location"]
            pallet_ids.append(removeprefix(location, "/pallets/"))

        require(count, 27, "Wrong number of pallets...")
        ok()

        testing("adding flour and baking some more")
        payload = {"deliveryTime": "2021-03-21 10:30:00", "quantity": 500_000}
        r = requests.post(url(f"/ingredients/{quote('Flour')}/deliveries"), json=payload)
        require(r.status_code, 201, "Wrong status code from POST on /ingredientDeliveries")
        
        for cookie in ordered_cookies:
            payload = {"cookie": cookie}
            r = requests.post(url("/pallets"), json=payload)
            if r.status_code == 422:
                break
            count += 1
            location = r.json()["location"]
            pallet_ids.append(removeprefix(location, "/pallets/"))

        require(count, 35, "Wrong number of pallets...")
        ok()

        testing("inventory")
        r = requests.get(url("/ingredients"))
        inventory = { inv['ingredient']: inv['quantity'] for inv in r.json()['data']}
        for ingredient, expected_quantity in [("Bread crumbs", 150000),
                                              ("Butter", 70800),
                                              ("Chocolate", 300000),
                                              ("Chopped almonds", 39076),
                                              ("Cinnamon", 32440),
                                              ("Egg whites", 350000),
                                              ("Eggs", 300000),
                                              ("Fine-ground nuts", 200000),
                                              ("Flour", 357400),
                                              ("Ground roasted nuts", 200000),
                                              ("Icing sugar", 100000),
                                              ("Marzipan", 100000),
                                              ("Potato starch", 100000),
                                              ("Roasted chopped nuts", 200000),
                                              ("Sodium bicarbonate", 20464),
                                              ("Sugar", 12380),
                                              ("Vanilla", 97732),
                                              ("Vanilla sugar", 40000),
                                              ("Wheat flour", 600000)]:
            require_close_enough(inventory[ingredient], expected_quantity, f"Wrong quantity of {ingredient}")
        ok()

        print()
        print("Your program passes this test!")
        print()
        print(textwrap.dedent("""\
              If you polish up your README.md file in gitlab (make sure the
              ER file is updated, remove template text, etc.), you can make
              a submission."""))
        print()

    except KeyError as e:
        print(f"\n\n ### Check your JSON labels carefully, I expected {e} ###\n\n")

    except json.decoder.JSONDecodeError as e:
        print(f"\n\n ### I expected a JSON object, but got something else ###\n\n")

    except:
        print(f"\n\n ### Got exception: {sys.exc_info()} ###\n\n")


def main():
    try:
        check_all()
    except Exception as e:
        abort(f"The test program crashed: {e}")


if __name__ == '__main__':
    main()
