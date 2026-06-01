"""Binary sensors for Plugit chargers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CHARGING_ACTIVE_STATUSES,
    CABLE_CONNECTED_STATUSES,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import PlugitDataUpdateCoordinator


@dataclass
class PlugitBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor metadata."""

    kind: str = ""


BINARY_SENSOR_DESCRIPTIONS = (
    PlugitBinarySensorDescription(
        key="charging_active",
        name="Charging active",
        device_class=BinarySensorDeviceClass.PLUG,
        kind="charging",
    ),
    PlugitBinarySensorDescription(
        key="cable_connected",
        name="Cable connected",
        device_class=BinarySensorDeviceClass.PLUG,
        kind="cable",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugit binary sensors."""

    coordinator: PlugitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PlugitChargingBinarySensor(coordinator, description)
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]
    )


class PlugitChargingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Expose charger state as binary sensors."""

    entity_description: PlugitBinarySensorDescription

    def __init__(
        self,
        coordinator: PlugitDataUpdateCoordinator,
        description: PlugitBinarySensorDescription,
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
    def is_on(self) -> Optional[bool]:
        if self.coordinator.data is None:
            return None
        if self.entity_description.kind == "charging":
            return self.coordinator.data.status in CHARGING_ACTIVE_STATUSES
        if self.entity_description.kind == "cable":
            return self.coordinator.data.status in CABLE_CONNECTED_STATUSES
        return None
