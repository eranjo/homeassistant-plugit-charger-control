"""DataUpdateCoordinator for Plugit chargers."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any, Optional

from .api import (
    PlugitApi,
    PlugitApiError,
    PlugitAuthError,
    PlugitCharger,
)
from .const import CONF_REFRESH_INTERVAL, DEFAULT_SCAN_INTERVAL

try:  # pragma: no cover - exercised only in Home Assistant
    from homeassistant.exceptions import ConfigEntryAuthFailed
    from homeassistant.helpers.update_coordinator import (
        DataUpdateCoordinator,
        UpdateFailed,
    )
except ImportError:  # pragma: no cover - local test fallback

    class ConfigEntryAuthFailed(Exception):
        """Fallback auth failure for local tests."""

    class UpdateFailed(Exception):
        """Fallback update failure for local tests."""

    class DataUpdateCoordinator:  # type: ignore[override]
        """Minimal fallback coordinator for unit tests."""

        def __init__(
            self,
            hass: Any,
            logger: logging.Logger,
            name: str,
            update_interval: Any = None,
        ) -> None:
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None
            self.last_update_success = False

        async def _async_update_data(self) -> Any:
            raise NotImplementedError

        async def async_request_refresh(self) -> Any:
            self.data = await self._async_update_data()
            self.last_update_success = True
            return self.data

        async def async_config_entry_first_refresh(self) -> Any:
            return await self.async_request_refresh()

        async def async_refresh(self) -> Any:
            return await self.async_request_refresh()


_LOGGER = logging.getLogger(__name__)


class PlugitDataUpdateCoordinator(DataUpdateCoordinator):
    """Poll the selected Plugit charger."""

    def __init__(
        self,
        hass: Any,
        api: PlugitApi,
        charge_point_id: str,
        charge_box_group_id: str,
        charge_box_id: str,
        config_entry: Any = None,
        refresh_interval_seconds: int = int(DEFAULT_SCAN_INTERVAL.total_seconds()),
    ) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Plugit charger",
            update_interval=timedelta(seconds=refresh_interval_seconds),
        )
        self.api = api
        self.charge_point_id = charge_point_id
        self.charge_box_group_id = charge_box_group_id
        self.charge_box_id = charge_box_id
        self.config_entry = config_entry
        self.refresh_interval_seconds = refresh_interval_seconds
        self.last_successful_refresh: Optional[datetime] = None

    async def _async_update_data(self) -> PlugitCharger:
        try:
            charger = await self.api.async_get_charger(
                self.charge_point_id,
                self.charge_box_group_id,
                self.charge_box_id,
            )
        except PlugitAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PlugitApiError as err:
            raise UpdateFailed(str(err)) from err

        self.last_successful_refresh = datetime.now(timezone.utc)
        self.last_update_success = True
        _LOGGER.debug(
            "Refreshed Plugit charger %s with status %s",
            charger.display_name,
            charger.status,
        )
        return charger

    async def async_start_charging(self) -> None:
        """Refresh state and request a remote start."""

        await self.api.async_start_charging(
            self.charge_point_id,
            self.charge_box_group_id,
            self.charge_box_id,
        )
        await self.async_request_refresh()

    async def async_stop_charging(self) -> None:
        """Refresh state and request a remote stop."""

        await self.api.async_stop_charging(
            self.charge_point_id,
            self.charge_box_group_id,
            self.charge_box_id,
        )
        await self.async_request_refresh()

    async def async_set_refresh_interval(self, seconds: int) -> None:
        """Update the polling interval and persist it to the config entry."""

        seconds = max(5, int(seconds))
        self.refresh_interval_seconds = seconds
        self.update_interval = timedelta(seconds=seconds)

        if self.config_entry is not None and hasattr(self.hass, "config_entries"):
            new_options = dict(getattr(self.config_entry, "options", {}) or {})
            new_options[CONF_REFRESH_INTERVAL] = seconds
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                options=new_options,
            )

        await self.async_request_refresh()
