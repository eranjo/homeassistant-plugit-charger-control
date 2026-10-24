"""Switch entity for Plugit charging control."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PlugitDataUpdateCoordinator

SWITCH_DESCRIPTION = SwitchEntityDescription(
    key="charging",
    name="Charging",
    icon="mdi:ev-station",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plugit charging switch."""

    coordinator: PlugitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlugitChargingSwitch(coordinator)])


class PlugitChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Toggle that starts or stops charging."""

    entity_description = SWITCH_DESCRIPTION

    def __init__(self, coordinator: PlugitDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "%s_%s_%s_%s" % (
            coordinator.charge_point_id,
            coordinator.charge_box_group_id,
            coordinator.charge_box_id,
            SWITCH_DESCRIPTION.key,
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
    def is_on(self) -> bool:
        """Return effective charging state, including pending commands."""

        return self.coordinator.effective_charging

    @property
    def available(self) -> bool:
        """Return whether the switch can be used."""

        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return False
        if self.coordinator.is_command_pending:
            return True
        return bool(self.coordinator.data.can_start or self.coordinator.data.is_charging)

    async def async_turn_on(self, **kwargs) -> None:
        """Start charging when the charger is ready."""

        if self.coordinator.effective_charging:
            return

        if self.coordinator.is_command_pending:
            raise HomeAssistantError(
                "A stop command is still in progress; wait for the charger status to update"
            )

        if self.coordinator.data is None or not self.coordinator.data.can_start:
            status = (
                "unknown"
                if self.coordinator.data is None
                else self.coordinator.data.status
            )
            raise HomeAssistantError(
                "Charging can only start when the cable is connected and the "
                "charger status is Preparing (current status: %s)" % status
            )

        try:
            await self.coordinator.async_start_charging()
        except Exception as err:
            raise HomeAssistantError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        """Stop charging when the charger is active."""

        if not self.coordinator.effective_charging:
            return

        if self.coordinator.pending_charging is True:
            raise HomeAssistantError(
                "A start command is still in progress; wait for the charger status to update"
            )

        if self.coordinator.data is None or not self.coordinator.data.is_charging:
            status = (
                "unknown"
                if self.coordinator.data is None
                else self.coordinator.data.status
            )
            raise HomeAssistantError(
                "Charging can only be stopped when the charger is actively "
                "charging (current status: %s)" % status
            )

        try:
            await self.coordinator.async_stop_charging()
        except Exception as err:
            raise HomeAssistantError(str(err)) from err
