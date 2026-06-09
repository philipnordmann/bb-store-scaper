from __future__ import annotations

import urllib.parse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_PRODUCT_URL, CONF_PRODUCT_NAME
from .scraper import fetch_product, extract_stock


def _slug_to_title(url: str) -> str:
    try:
        slug = urllib.parse.urlparse(url).path.split("/products/")[1].strip("/")
        return slug.replace("-", " ").title()
    except (IndexError, AttributeError):
        return "Product"


class BbStoreScaperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_PRODUCT_URL].strip()
            name = user_input.get(CONF_PRODUCT_NAME, "").strip() or _slug_to_title(url)

            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            try:
                data = await self.hass.async_add_executor_job(fetch_product, url)
                stock = extract_stock(data)
                if not stock:
                    errors["base"] = "no_variants"
            except (KeyError, IndexError, ValueError):
                errors["base"] = "invalid_url"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=name,
                    data={CONF_PRODUCT_URL: url, CONF_PRODUCT_NAME: name},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PRODUCT_URL): cv.string,
                    vol.Optional(CONF_PRODUCT_NAME): cv.string,
                }
            ),
            errors=errors,
        )
