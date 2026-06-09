"""Scraping logic — no external dependencies, stdlib only."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request


def parse_product_url(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.split("/products/")[1].strip("/")
    product_id = urllib.parse.parse_qs(parsed.query)["id"][0]
    return slug, product_id


def _make_router_state_tree(slug: str, product_id: str) -> str:
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
    return urllib.parse.quote(json.dumps(tree, separators=(",", ":")))


def _extract_largest_rsc_blob(raw_bytes: bytes) -> dict:
    best = None
    best_length = 0

    for match in re.finditer(rb"[0-9a-f]+:T([0-9a-f]+),", raw_bytes):
        length = int(match.group(1), 16)
        if length > best_length:
            start = match.end()
            candidate = raw_bytes[start : start + length]
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
    """Blocking — run via async_add_executor_job in HA."""
    slug, product_id = parse_product_url(url)
    rsc_url = f"https://eu.store.bambulab.com/de/products/{slug}?id={product_id}"

    headers = {
        "accept": "*/*",
        "accept-language": "de-DE,de;q=0.9",
        "rsc": "1",
        "next-url": f"/de/products/{slug}",
        "next-router-state-tree": _make_router_state_tree(slug, product_id),
        "referer": url,
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "cookie": "bbl_release_track=primary; NEXT_LOCALE=de; notice_behavior=implied|eu",
    }

    req = urllib.request.Request(rsc_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        raw_bytes = response.read()

    return _extract_largest_rsc_blob(raw_bytes)


def extract_stock(data: dict) -> dict[str, str]:
    """Return {variant_name: 'InStock' | 'OutOfStock'} from RSC blob."""
    results: dict[str, str] = {}

    def traverse(obj: object) -> None:
        if isinstance(obj, dict):
            if obj.get("@type") == "Product" and "sku" in obj and "offers" in obj:
                name = obj.get("name", obj["sku"])
                availability_url = obj.get("offers", {}).get("availability", "")
                results[name] = (
                    availability_url.rsplit("/", 1)[-1] if availability_url else "Unknown"
                )
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return results
