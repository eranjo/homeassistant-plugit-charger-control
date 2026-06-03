"""Sensor entities for Plugit chargers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_SUCCESSFUL_REFRESH,
    ATTR_STATUS,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import PlugitDataUpdateCoordinator


@dataclass
class PlugitSensorDescription(SensorEntityDescription):
    """Sensor metadata."""

    value_fn: Any = None


STATUS_SENSOR = PlugitSensorDescription(
    key="status",
    name="Status",
    icon="mdi:ev-station",
    native_unit_of_measurement=None,
    state_class=None,
)

POWER_SENSOR = PlugitSensorDescription(
    key="power",
    name="Power",
    icon="mdi:flash",
    device_class=SensorDeviceClass.POWER,
    native_unit_of_measurement="W",
    state_class=SensorStateClass.MEASUREMENT,
)

CHARGING_DURATION_SENSOR = PlugitSensorDescription(
    key="charging_duration",
    name="Charging duration",
    icon="mdi:timer-outline",
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement="s",
    state_class=SensorStateClass.MEASUREMENT,
)

LAST_REFRESH_SENSOR = PlugitSensorDescription(
    key="last_refresh",
    name="Last successful refresh",
    icon="mdi:update",
    device_class=SensorDeviceClass.TIMESTAMP,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugit sensors."""

    coordinator: PlugitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PlugitStatusSensor(coordinator, STATUS_SENSOR),
            PlugitPowerSensor(coordinator, POWER_SENSOR),
            PlugitChargingDurationSensor(coordinator, CHARGING_DURATION_SENSOR),
            PlugitLastRefreshSensor(coordinator, LAST_REFRESH_SENSOR),
        ]
    )


class _BasePlugitSensor(CoordinatorEntity, SensorEntity):
    """Base class for Plugit sensors."""

    def __init__(
        self,
        coordinator: PlugitDataUpdateCoordinator,
        description: PlugitSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
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


class PlugitStatusSensor(_BasePlugitSensor):
    """Expose the raw Plugit status."""

    @property
    def unique_id(self) -> str:
        return "%s_%s_%s_status" % (
            self.coordinator.charge_point_id,
            self.coordinator.charge_box_group_id,
            self.coordinator.charge_box_id,
        )

    @property
    def native_value(self) -> Optional[str]:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.status

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        return {
            "chargePointId": self.coordinator.data.charge_point_id,
            "chargeBoxGroupId": self.coordinator.data.charge_box_group_id,
            "chargeBoxId": self.coordinator.data.charge_box_id,
            ATTR_STATUS: self.coordinator.data.status,
            ATTR_LAST_SUCCESSFUL_REFRESH: self.coordinator.last_successful_refresh,
        }


class PlugitPowerSensor(_BasePlugitSensor):
    """Expose the current charger power."""

    @property
    def unique_id(self) -> str:
        return "%s_%s_%s_power" % (
            self.coordinator.charge_point_id,
            self.coordinator.charge_box_group_id,
            self.coordinator.charge_box_id,
        )

    @property
    def native_value(self) -> Optional[float]:
        return self.coordinator.current_power_w


class PlugitChargingDurationSensor(_BasePlugitSensor):
    """Expose the charging duration for the current or last session."""

    @property
    def unique_id(self) -> str:
        return "%s_%s_%s_charging_duration" % (
            self.coordinator.charge_point_id,
            self.coordinator.charge_box_group_id,
            self.coordinator.charge_box_id,
        )

    @property
    def native_value(self) -> Optional[float]:
        return self.coordinator.charging_duration_seconds


class PlugitLastRefreshSensor(_BasePlugitSensor):
    """Expose the last successful refresh timestamp."""

    entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return "%s_%s_%s_last_refresh" % (
            self.coordinator.charge_point_id,
            self.coordinator.charge_box_group_id,
            self.coordinator.charge_box_id,
        )

    @property
    def native_value(self) -> Optional[datetime]:
        return self.coordinator.last_successful_refresh
