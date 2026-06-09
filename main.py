import re
import json
import sys
import urllib.parse
import urllib.request

from flask import Flask, request, jsonify

app = Flask(__name__)


def parse_product_url(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.split("/products/")[1].strip("/")
    product_id = urllib.parse.parse_qs(parsed.query)["id"][0]
    return slug, product_id


def make_router_state_tree(slug: str, product_id: str) -> str:
    tree = [
        "",
        {"children": [
            ["locale", "de", "d"],
            {"children": [
                "(layout-default)",
                {"children": [
                    "products",
                    {"children": [
                        ["name", slug, "d"],
                        {"children": [
                            f'__PAGE__?{{"id":"{product_id}"}}',
                            {}
                        ]}
                    ]}
                ]}
            ]}
        ]},
        None, None, True
    ]
    return urllib.parse.quote(json.dumps(tree, separators=(',', ':')))

def extract_largest_rsc_blob(raw_bytes: bytes) -> dict:
    best = None
    best_length = 0

    for match in re.finditer(rb'[0-9a-f]+:T([0-9a-f]+),', raw_bytes):
        length = int(match.group(1), 16)
        if length > best_length:
            start = match.end()
            candidate = raw_bytes[start:start + length]
            # make sure it's actually valid JSON
            try:
                json.loads(candidate)
                best = candidate
                best_length = length
            except json.JSONDecodeError:
                continue

    if best is None:
        raise ValueError("No valid RSC JSON blob found")

    return json.loads(best)

def fetch_product(url: str) -> dict:
    slug, product_id = parse_product_url(url)
    rsc_url = f"https://eu.store.bambulab.com/de/products/{slug}?id={product_id}"

    headers = {
        "accept": "*/*",
        "accept-language": "de-DE,de;q=0.9",
        "rsc": "1",
        "next-url": f"/de/products/{slug}",
        "next-router-state-tree": make_router_state_tree(slug, product_id),
        "referer": url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "cookie": "bbl_release_track=primary; NEXT_LOCALE=de; notice_behavior=implied|eu",
    }

    req = urllib.request.Request(rsc_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        raw_bytes = response.read()

    return extract_largest_rsc_blob(raw_bytes)


def extract_stock(data) -> dict:
    results = {}

    def traverse(obj):
        if isinstance(obj, dict):
            if obj.get("@type") == "Product" and "sku" in obj and "offers" in obj:
                name = obj.get("name", obj["sku"])
                availability_url = obj.get("offers", {}).get("availability", "")
                # "https://schema.org/InStock" → "InStock"
                results[name] = availability_url.rsplit("/", 1)[-1] if availability_url else "Unknown"
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return results


@app.get("/stock")
def get_stock():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing required query parameter: url"}), 400

    try:
        data = fetch_product(url)
        stock = extract_stock(data)
    except (KeyError, IndexError, ValueError) as e:
        return jsonify({"error": f"Invalid product URL: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fetch product: {e}"}), 502

    return jsonify(stock)


@app.get("/product")
def get_product():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing required query parameter: url"}), 400

    try:
        data = fetch_product(url)
    except (KeyError, IndexError, ValueError) as e:
        return jsonify({"error": f"Invalid product URL: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fetch product: {e}"}), 502

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

