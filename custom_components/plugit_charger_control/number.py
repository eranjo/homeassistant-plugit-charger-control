"""Number entity for the Plugit refresh interval."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - Home Assistant only
    from homeassistant.components.number import (
        NumberDeviceClass,
        NumberEntity,
        NumberEntityDescription,
    )
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import EntityCategory
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import DeviceInfo
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
except ImportError:  # pragma: no cover - local tests

    class NumberDeviceClass:  # type: ignore[override]
        DURATION = "duration"

    class NumberEntityDescription:  # type: ignore[override]
        def __init__(self, **kwargs: object) -> None:
            self.__dict__.update(kwargs)

    class NumberEntity:  # type: ignore[override]
        pass

    class ConfigEntry:  # type: ignore[override]
        pass

    class HomeAssistant:  # type: ignore[override]
        pass

    class AddEntitiesCallback:  # type: ignore[override]
        pass

    class DeviceInfo:  # type: ignore[override]
        def __init__(self, **kwargs: object) -> None:
            self.__dict__.update(kwargs)

    class EntityCategory:  # type: ignore[override]
        CONFIG = "config"

    class CoordinatorEntity:  # type: ignore[override]
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

from .const import DOMAIN, MANUFACTURER
from .coordinator import PlugitDataUpdateCoordinator


REFRESH_INTERVAL_NUMBER = NumberEntityDescription(
    key="refresh_interval",
    name="Refresh interval",
    icon="mdi:clock-outline",
    device_class=NumberDeviceClass.DURATION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plugit refresh interval number."""

    coordinator: PlugitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlugitRefreshIntervalNumber(coordinator, REFRESH_INTERVAL_NUMBER)])


class PlugitRefreshIntervalNumber(CoordinatorEntity, NumberEntity):
    """Editable polling interval in seconds."""

    entity_description = REFRESH_INTERVAL_NUMBER
    entity_category = EntityCategory.CONFIG
    native_min_value = 5
    native_max_value = 24 * 60 * 60
    native_step = 1
    native_unit_of_measurement = "s"

    def __init__(
        self,
        coordinator: PlugitDataUpdateCoordinator,
        description: NumberEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = "%s_%s_%s_%s" % (
            coordinator.charge_point_id,
            coordinator.charge_box_group_id,
            coordinator.charge_box_id,
            description.key,
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    coordinator.charge_point_id,
                    coordinator.charge_box_group_id,
                    coordinator.charge_box_id,
                )
            },
            manufacturer=MANUFACTURER,
            name="Plugit charger",
        )

    @property
    def native_value(self) -> Optional[float]:
        return float(self.coordinator.refresh_interval_seconds)

    async def async_set_native_value(self, value: float) -> None:
        """Update the coordinator refresh interval."""

        seconds = int(value)
        await self.coordinator.async_set_refresh_interval(seconds)
        self.async_write_ha_state()
