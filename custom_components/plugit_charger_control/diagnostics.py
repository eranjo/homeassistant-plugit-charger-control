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

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN


def _sanitize_charger(charger: Any) -> Dict[str, Any]:
    raw = getattr(charger, "raw", {}) or {}
    return {
        "status": getattr(charger, "status", None),
        "power": raw.get("power"),
        "powerType": raw.get("powerType"),
        "socketType": raw.get("socketType"),
    }


async def async_get_config_entry_diagnostics(hass: Any, entry: Any) -> Dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    charger = coordinator.data
    payload = {
        "config": {
            CONF_USERNAME: entry.data.get(CONF_USERNAME),
            CONF_PASSWORD: entry.data.get(CONF_PASSWORD),
        },
        "charger": None
        if charger is None
        else _sanitize_charger(charger),
        "last_successful_refresh": getattr(coordinator, "last_successful_refresh", None),
    }
    redacted = async_redact_data(payload, {CONF_PASSWORD})
    redacted["config"][CONF_USERNAME] = "REDACTED"
    return redacted
