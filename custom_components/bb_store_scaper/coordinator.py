from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_PRODUCT_URL, CONF_PRODUCT_NAME, DEFAULT_SCAN_INTERVAL
from .scraper import fetch_product, extract_stock

_LOGGER = logging.getLogger(__name__)


class BambooStockCoordinator(DataUpdateCoordinator[dict[str, str]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.url: str = entry.data[CONF_PRODUCT_URL]
        self.product_name: str = entry.data[CONF_PRODUCT_NAME]

    async def _async_update_data(self) -> dict[str, str]:
        try:
            data = await self.hass.async_add_executor_job(fetch_product, self.url)
            return extract_stock(data)
        except Exception as err:
            raise UpdateFailed(f"Error fetching Bambu stock data: {err}") from err
