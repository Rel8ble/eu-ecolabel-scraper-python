"""EU Ecolabel certified products -> supplier shortlist, in Python.

Calls the rel8ble/eu-ecolabel-products-scraper actor on Apify (or reads a saved
JSON file), then groups certified products by licence holder and prints a
shortlist: how many certified products each company has, how many carry an EAN
barcode, which countries they are sold in and when the licence expires.

    python example.py --token <YOUR_APIFY_TOKEN> --groups "Hard Surface Cleaning Products" --sold-in FR
    python example.py --from-json sample.json
    python example.py --from-json sample.json --check-ean 0541128321788
"""
import argparse
import csv
import json
import sys
from collections import defaultdict


def fetch(token, groups, holder_countries, sold_in, text, max_results):
    from apify_client import ApifyClient

    client = ApifyClient(token)
    run_input = {"mode": "products", "validOnly": True, "maxResults": max_results}
    if groups:
        run_input["productGroups"] = groups
    if holder_countries:
        run_input["licenceHolderCountries"] = holder_countries
    if sold_in:
        run_input["availableIn"] = sold_in
    if text:
        run_input["searchText"] = text
    run = client.actor("rel8ble/eu-ecolabel-products-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def shortlist(rows, sold_in=None):
    by_holder = defaultdict(lambda: {"products": 0, "with_ean": 0, "licences": set(),
                                     "countries": set(), "expires": None, "vat": None,
                                     "country": None, "subcats": set()})
    for r in rows:
        if sold_in and not set(sold_in) & set(r.get("availableIn") or []):
            continue
        h = by_holder[r["licenceHolder"]]
        h["products"] += 1
        h["with_ean"] += 1 if r.get("ean13") else 0
        h["licences"].add(r["licenceNumber"])
        h["countries"].update(r.get("availableIn") or [])
        h["vat"] = h["vat"] or r.get("licenceHolderVat")
        h["country"] = r.get("licenceHolderCountry")
        if r.get("productSubcategory"):
            h["subcats"].add(r["productSubcategory"])
        exp = r.get("expiresOn")
        if exp and (h["expires"] is None or exp < h["expires"]):
            h["expires"] = exp
    return sorted(by_holder.items(), key=lambda kv: -kv[1]["products"])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--token", help="Apify API token")
    p.add_argument("--from-json", help="read rows from a saved JSON file instead of calling Apify")
    p.add_argument("--groups", nargs="*", default=["Hard Surface Cleaning Products"])
    p.add_argument("--holder-countries", nargs="*", default=[])
    p.add_argument("--sold-in", nargs="*", default=[], help="ISO codes, e.g. FR DE")
    p.add_argument("--text", default="")
    p.add_argument("--max", type=int, default=200)
    p.add_argument("--check-ean", nargs="*", default=[], help="barcodes to look up in the rows")
    p.add_argument("--csv", help="write the shortlist to this CSV file")
    a = p.parse_args()

    if a.from_json:
        with open(a.from_json, encoding="utf-8") as f:
            rows = json.load(f)
    elif a.token:
        rows = fetch(a.token, a.groups, a.holder_countries, a.sold_in, a.text, a.max)
    else:
        sys.exit("give --token <YOUR_APIFY_TOKEN> or --from-json sample.json")

    print(f"{len(rows)} certified products\n")
    out = []
    for name, h in shortlist(rows, a.sold_in):
        line = {
            "licenceHolder": name,
            "country": h["country"],
            "vat": h["vat"] or "",
            "licences": " ".join(sorted(h["licences"])),
            "products": h["products"],
            "withEan": h["with_ean"],
            "soldInCount": len(h["countries"]),
            "subcategories": ", ".join(sorted(h["subcats"])),
            "firstExpiry": h["expires"],
        }
        out.append(line)
        print(f'{name} ({h["country"]}): {h["products"]} products, {h["with_ean"]} with EAN, '
              f'sold in {len(h["countries"])} countries, licence {line["licences"]}, expires {h["expires"]}')

    if a.check_ean:
        print()
        index = defaultdict(list)
        for r in rows:
            for e in r.get("ean13") or []:
                index[e].append(r)
        for ean in a.check_ean:
            hits = index.get(ean, [])
            if not hits:
                print(f"{ean}: not found in these rows")
            for r in hits:  # one barcode can be filed on several products
                print(f'{ean}: EU Ecolabel {r["licenceNumber"]} ({r["licenceHolder"]}), '
                      f'"{r["productName"]}", valid until {r["expiresOn"]}')

    if a.csv and out:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
        print(f"\nwrote {a.csv}")


if __name__ == "__main__":
    main()
