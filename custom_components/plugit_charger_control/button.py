"""Button entities for Plugit chargers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, MANUFACTURER, STATUS_CHARGING, STATUS_PREPARING

from .coordinator import PlugitDataUpdateCoordinator


@dataclass
class PlugitButtonDescription(ButtonEntityDescription):
    """Button metadata."""

    action: str = ""


BUTTON_DESCRIPTIONS = (
    PlugitButtonDescription(
        key="start_charging",
        name="Start charging",
        icon="mdi:play",
        action="start",
    ),
    PlugitButtonDescription(
        key="stop_charging",
        name="Stop charging",
        icon="mdi:stop",
        action="stop",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plugit buttons."""

    coordinator: PlugitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [PlugitChargingButton(coordinator, description) for description in BUTTON_DESCRIPTIONS]
    )


class PlugitChargingButton(CoordinatorEntity, ButtonEntity):
    """Button that starts or stops charging."""

    entity_description: PlugitButtonDescription

    def __init__(
        self,
        coordinator: PlugitDataUpdateCoordinator,
        description: PlugitButtonDescription,
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
    def available(self) -> bool:
        """Return whether the button should be available."""

        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return False
        if self.entity_description.action == "start":
            return self.coordinator.data.status in {STATUS_PREPARING}
        if self.entity_description.action == "stop":
            return self.coordinator.data.status in {STATUS_CHARGING}
        return False

    async def async_press(self) -> None:
        """Execute the configured action."""

        try:
            if self.entity_description.action == "start":
                await self.coordinator.async_start_charging()
            elif self.entity_description.action == "stop":
                await self.coordinator.async_stop_charging()
            else:
                raise HomeAssistantError("Unsupported button action")
        except Exception as err:
            raise HomeAssistantError(str(err)) from err

