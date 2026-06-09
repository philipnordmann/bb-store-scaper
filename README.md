# Store Stock — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/philipnordmann/bb-store-scaper.svg)](https://github.com/philipnordmann/bb-store-scaper/releases)

Monitor stock availability for any EU Store product directly in Home Assistant. Each product is a **device**, and every SKU/variant becomes a **sensor** with state `InStock` or `OutOfStock`.

---

## Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=philipnordmann&repository=bb-store-scaper&category=integration)

1. Click the button above (or in HACS go to **Integrations → ⋮ → Custom repositories** and add `philipnordmann/bb-store-scaper`)
2. Install **Store Stock**
3. Restart Home Assistant

## Setup

1. **Settings → Devices & Services → Add Integration**
2. Search for **Store Stock**
3. Paste a product URL including the `?id=` parameter
4. Optionally give the product a display name
5. A **device** is created with one **sensor per SKU variant** — repeat for each product

## Sensors

| State | Meaning |
|---|---|
| `InStock` | Variant is available to buy |
| `OutOfStock` | Variant is currently unavailable |

Sensors are polled every **5 minutes** and grouped under a device named after the product.

## Blueprint: stock alert notification

Get notified the moment a variant you care about comes back in stock:

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fphilipnordmann%2Fbb-store-scaper%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbb_store_scaper%2Fstock_notification.yaml)

Or import manually: **Settings → Automations → Blueprints → Import Blueprint** and paste the URL above.

## Self-hosted REST API (optional)

A standalone Flask API + Docker image is also included if you want to query stock data outside of Home Assistant:

```bash
docker build -t bb-store-scaper .
docker run -p 8080:8080 bb-store-scaper

# Stock availability for all variants
curl "http://localhost:8080/stock?url=https://.../de/products/pla-basic-filament?id=43992830017755"

# Full raw product data
curl "http://localhost:8080/product?url=..."
```

## Notes

- Polls the EU store with German locale — prices and names are in German
- No external Python dependencies; the integration uses stdlib only
- To pick up new SKUs added by the store: reload the integration entry
