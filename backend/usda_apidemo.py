"""
usda fooddata central api demo and boilerplate

pulls nutrition info, may still need to add a piece that can calculate serving macros
based on serving size

- https://fdc.nal.usda.gov/api-guide

Usage:
    python usda_apidemo.py --query "tyson chicken" --limit 6
"""

import argparse
import json
import sys
from urllib import request, parse, error


API_KEY = "VdMHe0OBKst8hooGvmLAadybdabnUHygXwO2WGrY"

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"


NUTRIENTS_OF_INTEREST = {
    "Energy": "kcal",
    "Energy, kcal": "kcal",
    "Protein": "g",
    "Carbohydrate, by difference": "g",
    "Total lipid (fat)": "g",
}


def http_get(url, params=None):
    if params:
        url = f"{url}?{parse.urlencode(params, doseq=True)}"
    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        sys.stderr.write(f"[HTTP ERROR] {e.code} {e.reason}\n")
        body = e.read().decode("utf-8", "ignore")
        if body:
            sys.stderr.write(body + "\n")
        sys.exit(1)
    except error.URLError as e:
        sys.stderr.write(f"[URL ERROR] {e.reason}\n")
        sys.exit(1)


def search_foods(query, page_size=5, data_type=None):
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": page_size,
    }
    if data_type:
        params["dataType"] = data_type.split(",")
    data = http_get(SEARCH_URL, params)
    return data.get("foods", [])


def get_food_details(fdc_id):
    url = FOOD_URL.format(fdc_id=fdc_id)
    params = {"api_key": API_KEY}
    return http_get(url, params)


def extract_from_label_nutrients(label_nutrients):
    """
    Branded foods usually look like:
    "labelNutrients": {
        "calories": {"value": 230},
        "fat": {"value": 12},
        "carbohydrates": {"value": 15},
        "protein": {"value": 10}
    }
    """
    if not label_nutrients:
        return {}

    out = {}
    if "calories" in label_nutrients:
        out["Energy"] = f"{label_nutrients['calories'].get('value')} kcal"
    if "protein" in label_nutrients:
        out["Protein"] = f"{label_nutrients['protein'].get('value')} g"
    if "fat" in label_nutrients:
        out["Total lipid (fat)"] = f"{label_nutrients['fat'].get('value')} g"
    if "carbohydrates" in label_nutrients:
        out["Carbohydrate, by difference"] = f"{label_nutrients['carbohydrates'].get('value')} g"

    extras = [
        "sugars",
        "fiber",
        "saturatedFat",
        "transFat",
        "sodium",
    ]
    for k in extras:
        if k in label_nutrients:
            val = label_nutrients[k].get("value")
            unit = "g"
            if k == "sodium":
                unit = "mg"
            out[k] = f"{val} {unit}"

    return out


def extract_from_food_nutrients(food_json):
    out = {}
    for nutrient in food_json.get("foodNutrients", []):
        name = nutrient.get("nutrientName")
        amount = nutrient.get("value")
        unit = nutrient.get("unitName")
        if name in NUTRIENTS_OF_INTEREST:
            out[name] = f"{amount} {unit}"
    return out


def extract_nutrients(details_json):
    """
    Try labelNutrients first (branded), then foodNutrients (SR/FNDDS).
    Return a dict of nutrient_name -> str(value+unit)
    """
    # 1) Branded style
    label_nutrients = details_json.get("labelNutrients")
    branded = extract_from_label_nutrients(label_nutrients)
    if branded:
        return branded

    # 2) SR / FNDDS style
    classic = extract_from_food_nutrients(details_json)
    return classic


def main():
    parser = argparse.ArgumentParser(description="USDA FDC search + nutrient fetcher (hardcoded API key)")
    parser.add_argument("--query", required=True, help="Search term, e.g. 'banana'")
    parser.add_argument("--limit", type=int, default=5, help="How many results to fetch (default 5)")
    parser.add_argument("--data-type", help="Optional comma-separated FDC dataType filter, e.g. 'Branded,SR Legacy'")
    parser.add_argument("--no-details", action="store_true",
                        help="If set, don't fetch per-food details; just show search hits.")
    args = parser.parse_args()

    foods = search_foods(args.query, args.limit, args.data_type)

    if not foods:
        print("No foods found.")
        return

    for idx, food in enumerate(foods, 1):
        fdc_id = food.get("fdcId")
        desc = food.get("description", "N/A")
        data_type = food.get("dataType", "N/A")
        print(f"\n[{idx}] {desc} (FDC ID: {fdc_id}, type: {data_type})")

        if args.no_details:
            quick_nutrients = food.get("foodNutrients", [])
            if quick_nutrients:
                print("  Quick nutrients from search:")
                for n in quick_nutrients:
                    print(f"    - {n.get('nutrientName')}: {n.get('value')} {n.get('unitName')}")
            continue

        # full detail call
        details = get_food_details(fdc_id)
        nutrients = extract_nutrients(details)

        if nutrients:
            print("  Nutrients:")
            for name, val in nutrients.items():
                print(f"    - {name}: {val}")
        else:
            print("  (No nutrients found in details)")

    print("\nDone.")


if __name__ == "__main__":
    main()
