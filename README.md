# EU Ecolabel products & licence holders in Python: eco-certified supplier list, licence numbers, VAT and EAN barcodes

Get the official **EU Ecolabel Product Catalogue** as JSON or CSV from Python or Node: every certified product with its **licence number, licence holder (company), VAT number, holder country, product group, criteria decision, licence expiry, countries where it is sold and EAN barcodes**. Useful for green public procurement and tender checks, eco-certified supplier sourcing, retailer barcode checks and competitor certification tracking.

> I built this actor; it's a paid tool on Apify ([EU Ecolabel Certified Products & Licence Holders Scraper](https://apify.com/rel8ble/eu-ecolabel-products-scraper)), $1 per 1,000 rows, no start fee. This repo is a free example of calling it.

## What the data is

The EU Ecolabel is the EU's official environmental label. The European Commission publishes every licensed product in a public catalogue (environmental-data.ec.europa.eu/ecolabel). The actor reads that catalogue's public JSON API over plain HTTP (no browser, no login) and returns one clean row per product, or one row per licence holder.

Size on 10 November 2026: **86,859 products under 2,416 licences held by about 1,520 companies from 48 countries, in 24 product groups.** Biggest groups: decorative paints 17,185, tissue paper 16,367, furniture 11,941, textiles 11,548, hard surface cleaners 7,659.

No prices, MOQs, e-mails, phone numbers or contact persons. It is a certification register, not a shop.

## Python

```bash
pip install -r requirements.txt
python example.py --token <YOUR_APIFY_TOKEN> --groups "Hard Surface Cleaning Products" --sold-in FR
python example.py --from-json sample.json                          # offline, on the bundled real sample
python example.py --from-json sample.json --check-ean 0541128321788 --csv shortlist.csv
```

Minimal call:

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")
run = client.actor("rel8ble/eu-ecolabel-products-scraper").call(run_input={
    "mode": "products",
    "productGroups": ["Hard Surface Cleaning Products"],
    "availableIn": ["FR"],
    "validOnly": True,
    "maxResults": 200,
})
for r in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(r["licenceHolder"], r["licenceNumber"], r["productName"], r["expiresOn"], r["ean13"])
```

Want a supplier list instead of products? Set `"mode": "licenceHolders"` and you get one row per licence holder + licence number with `productCount`, `productsWithEan`, `sampleProducts` and all countries sold.

## Node

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/eu-ecolabel-products-scraper').call({
    mode: 'licenceHolders',
    productGroups: ['Hard Surface Cleaning Products'],
    licenceHolderCountries: ['Germany'],
    maxResults: 100,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
for (const h of items) console.log(h.licenceHolder, h.licenceHolderVat, h.licenceNumber, h.productCount);
```

## What example.py does

1. Pulls certified products (or reads `sample.json`).
2. Groups them by licence holder: number of certified products, how many carry an EAN, licence numbers, countries sold, first licence expiry, product subcategories.
3. Optionally keeps only products sold in given countries (`--sold-in FR DE`).
4. Optionally looks up shelf barcodes (`--check-ean ...`) and says which licence covers them.
5. Optionally writes the shortlist to CSV (`--csv`).

Output on the bundled sample (20 real rows, Hard Surface Cleaning Products, newest first, 10 November 2026):

```
20 certified products

RCSI (France): 9 products, 0 with EAN, sold in 1 countries, licence FR/020/022, expires 2026-12-31
Pollet s.a. (Belgium): 5 products, 5 with EAN, sold in 28 countries, licence PL/020/032, expires 2026-12-31
INOCENTE GARCÍA MORENO, SL (Spain): 4 products, 4 with EAN, sold in 1 countries, licence ES08/020/00002 ES08/020/00003 ES08/020/00004 ES08/020/00005, expires 2026-12-31
LABORATOIRES ROCHEX (France): 1 products, 0 with EAN, sold in 1 countries, licence FR/020/035, expires 2026-12-31
EUROCHIMIC - SOCHIPHARM - ELCOPHARMA (France): 1 products, 0 with EAN, sold in 1 countries, licence FR/020/028, expires 2026-12-31
```

With `--sold-in DE` only Pollet s.a. is left: it is the one holder in this sample whose products are listed for Germany (28 countries).

Two things the sample shows about the register itself: the Spanish holder files **one licence number per product** (ES08/020/00002 to 00005), and Pollet files **the same EAN (0541128321788) on all five of its products**, so a barcode lookup can return several rows. `example.py` prints all of them.

## Sample row

One real row (10 November 2026, trimmed; `availableIn` shortened):

```json
{
  "productName": "ODOR LINE INDOOR CAPS (80 CAPS)",
  "licenceNumber": "PL/020/032",
  "licenceHolder": "Pollet s.a.",
  "licenceHolderVat": "BE0418402966",
  "licenceHolderCountry": "Belgium",
  "productGroup": "Hard Surface Cleaning Products",
  "criteriaDecision": "2017/1217/EU",
  "expiresOn": "2026-12-31",
  "availableIn": ["AT", "BE", "BG", "CY", "CZ", "DE", "..."],
  "availableInCount": 28,
  "ean13": ["0541128321788"],
  "productUrl": "https://environmental-data.ec.europa.eu/ecolabel/products/product_162701.html"
}
```

`sample.json` has all 20 rows with these fields.

## Input

| Field | What it does |
|---|---|
| `mode` | `products` (one row per product) or `licenceHolders` (one row per licence holder + licence number). |
| `productGroups` | Product group ids or names, e.g. `Hard Surface Cleaning Products`, `Textile products`, `Furniture`. Empty = all 24. |
| `categories` | Group categories (Cleaning, Paper, Clothing and textiles, Furniture and mattresses, ...). |
| `searchText` | Words anywhere in the record: product, company, licence number, VAT. |
| `licenceHolder` | Part of the licence holder's company name. |
| `licenceHolderCountries` | Where the holder is based, full English names (`Germany`, `Italy`). |
| `availableIn` | Keep products sold in at least one of these ISO codes (`DE`, `FR`, `GB`). |
| `validOnly` | Skip expired licences (default on; skipped rows are never charged). |
| `newestFirst` | Products mode: newest catalogue entries first. |
| `maxResults` | Rows to save; 0 = all that match. |

## Price and limits

- **$1.00 per 1,000 rows** ($0.001 each), no start fee. 100 rows = $0.10; the full licence-holder list (about 2,400 rows) is about $2.40. Empty searches, skipped expired licences and failed requests are not charged.
- Speed: 20 rows in 3.3 s and the whole licence list (2,416 rows) in 242 s in local tests.
- Fill rates over the whole catalogue (10 November 2026): VAT 93.4%, description 42.6%, EAN 29.2%, own product photo 4.0%. Licence number, holder, country, group, expiry and countries sold are always present.
- The licence holder can be a brand owner rather than the factory. Product names are in the language the holder used.
- EU Ecolabel services (e.g. tourist accommodation) are not included.

Source: © European Union, EU Ecolabel Product Catalogue, reused under CC BY 4.0 (Commission Decision 2011/833/EU); fields renamed and lists split by the actor. **Not affiliated with or endorsed by the European Commission or the EU Ecolabel.**

Store page: https://apify.com/rel8ble/eu-ecolabel-products-scraper

## License

MIT for the code in this repo. The data belongs to its source.

Need a custom scraper or a ready dataset? Hire me on Fiverr: https://www.fiverr.com/rel8ble
