from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BambooStockCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BambooStockCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create one sensor per variant discovered on first fetch.
    # To pick up newly added SKUs, reload the integration entry.
    async_add_entities(
        BambooSkuSensor(coordinator, entry, variant_name)
        for variant_name in coordinator.data
    )


class BambooSkuSensor(CoordinatorEntity[BambooStockCoordinator], SensorEntity):
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(
        self,
        coordinator: BambooStockCoordinator,
        entry: ConfigEntry,
        variant_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._variant_name = variant_name
        self._attr_name = variant_name
        self._attr_unique_id = f"{entry.entry_id}_{variant_name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.product_name,
            manufacturer="Bambu Lab",
            entry_type=None,
        )

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get(self._variant_name)
