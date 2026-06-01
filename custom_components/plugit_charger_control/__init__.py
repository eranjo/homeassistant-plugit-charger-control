"""Plugit charger control integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .api import PlugitApi
from .const import (
    CONF_CHARGE_BOX_GROUP_ID,
    CONF_CHARGE_BOX_ID,
    CONF_CHARGE_POINT_ID,
    CONF_REFRESH_INTERVAL,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import (
    ConfigEntryAuthFailed,
    PlugitDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - exercised in Home Assistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import Platform
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import aiohttp_client
    from homeassistant.exceptions import ConfigEntryNotReady
except ImportError:  # pragma: no cover - local tests

    class ConfigEntry:  # type: ignore[override]
        """Fallback config entry for local tests."""

        def __init__(
            self,
            data: Dict[str, Any],
            entry_id: str = "test",
            options: Optional[Dict[str, Any]] = None,
        ) -> None:
            self.data = data
            self.entry_id = entry_id
            self.options = options or {}
            self.runtime_data = None

    class HomeAssistant:  # type: ignore[override]
        """Fallback hass object for local tests."""

        def __init__(self) -> None:
            self.data = {}

    class Platform:  # type: ignore[override]
        BUTTON = "button"
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        NUMBER = "number"

    class ConfigEntryNotReady(Exception):
        """Fallback not-ready exception for local tests."""

    class _AiohttpClientFallback:
        @staticmethod
        def async_get_clientsession(hass: Any) -> Any:
            return getattr(hass, "client_session", None)

    aiohttp_client = _AiohttpClientFallback()  # type: ignore[assignment]


PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Plugit integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    session = aiohttp_client.async_get_clientsession(hass)
    api = PlugitApi(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )
    refresh_interval_seconds = int(
        entry.options.get(
            CONF_REFRESH_INTERVAL,
            DEFAULT_SCAN_INTERVAL.total_seconds(),
        )
    )
    coordinator = PlugitDataUpdateCoordinator(
        hass=hass,
        api=api,
        charge_point_id=entry.data[CONF_CHARGE_POINT_ID],
        charge_box_group_id=entry.data[CONF_CHARGE_BOX_GROUP_ID],
        charge_box_id=entry.data[CONF_CHARGE_BOX_ID],
        config_entry=entry,
        refresh_interval_seconds=refresh_interval_seconds,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Configured Plugit charger entry %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Plugit config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
