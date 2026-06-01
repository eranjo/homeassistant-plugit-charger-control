"""Diagnostics for Plugit charger control."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - Home Assistant only
    from homeassistant.components.diagnostics import async_redact_data
except ImportError:  # pragma: no cover - local tests

    def async_redact_data(data: Dict[str, Any], fields: set[str]) -> Dict[str, Any]:
        redacted = dict(data)
        for field in fields:
            if field in redacted:
                redacted[field] = "REDACTED"
        return redacted

from .const import (
    ATTR_CHARGE_BOX_GROUP_ID,
    ATTR_CHARGE_BOX_ID,
    ATTR_CHARGE_POINT_ID,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(hass: Any, entry: Any) -> Dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    charger = coordinator.data
    payload = {
        "config": {
            CONF_USERNAME: entry.data.get(CONF_USERNAME),
            CONF_PASSWORD: entry.data.get(CONF_PASSWORD),
            ATTR_CHARGE_POINT_ID: entry.data.get(ATTR_CHARGE_POINT_ID),
            ATTR_CHARGE_BOX_GROUP_ID: entry.data.get(ATTR_CHARGE_BOX_GROUP_ID),
            ATTR_CHARGE_BOX_ID: entry.data.get(ATTR_CHARGE_BOX_ID),
        },
        "charger": None
        if charger is None
        else {
            ATTR_CHARGE_POINT_ID: charger.charge_point_id,
            ATTR_CHARGE_BOX_GROUP_ID: charger.charge_box_group_id,
            ATTR_CHARGE_BOX_ID: charger.charge_box_id,
            "status": charger.status,
            "display_name": charger.display_name,
            "raw": charger.raw,
        },
        "last_successful_refresh": getattr(coordinator, "last_successful_refresh", None),
    }
    return async_redact_data(payload, {CONF_PASSWORD})

