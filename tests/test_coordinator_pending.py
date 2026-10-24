"""Tests for coordinator pending charging state."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from custom_components.plugit_charger_control.api import PlugitCharger
from custom_components.plugit_charger_control.const import (
    STATUS_CHARGING,
    STATUS_PREPARING,
)
from custom_components.plugit_charger_control.coordinator import (
    PlugitDataUpdateCoordinator,
    _PENDING_TIMEOUT_FLOOR_SECONDS,
)


def _charger(status: str) -> PlugitCharger:
    return PlugitCharger(
        charge_point_id="cp",
        charge_box_group_id="group",
        charge_box_id="box",
        status=status,
        raw={"power": 0, "transactionId": "tx-1"},
    )


class _FakeHass:
    """Minimal hass stand-in for coordinator construction."""


class CoordinatorPendingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.api = AsyncMock()
        self.coordinator = PlugitDataUpdateCoordinator(
            hass=_FakeHass(),
            api=self.api,
            charge_point_id="cp",
            charge_box_group_id="group",
            charge_box_id="box",
            refresh_interval_seconds=60,
        )
        self.now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
        self.coordinator._now = lambda: self.now  # type: ignore[method-assign]

    def test_effective_charging_uses_pending_when_set(self) -> None:
        self.coordinator.data = _charger(STATUS_PREPARING)
        self.assertFalse(self.coordinator.effective_charging)

        self.coordinator._set_pending_charging(True)
        self.assertTrue(self.coordinator.is_command_pending)
        self.assertTrue(self.coordinator.effective_charging)

        self.coordinator._set_pending_charging(False)
        self.assertFalse(self.coordinator.effective_charging)

    def test_pending_clears_when_status_matches(self) -> None:
        self.coordinator._set_pending_charging(True)
        self.coordinator._reconcile_pending_charging(_charger(STATUS_PREPARING), self.now)
        self.assertTrue(self.coordinator.is_command_pending)

        self.coordinator._reconcile_pending_charging(_charger(STATUS_CHARGING), self.now)
        self.assertFalse(self.coordinator.is_command_pending)
        self.assertIsNone(self.coordinator.pending_charging)

    def test_pending_clears_on_timeout(self) -> None:
        self.coordinator._set_pending_charging(True)
        later = self.now + timedelta(seconds=_PENDING_TIMEOUT_FLOOR_SECONDS)
        self.coordinator._reconcile_pending_charging(_charger(STATUS_PREPARING), later)
        self.assertFalse(self.coordinator.is_command_pending)

    def test_pending_timeout_scales_with_refresh_interval(self) -> None:
        self.coordinator.refresh_interval_seconds = 90
        self.assertEqual(self.coordinator._pending_timeout_seconds(), 270)

    async def test_start_sets_pending_before_refresh(self) -> None:
        self.api.async_start_charging = AsyncMock()
        self.api.async_get_charger = AsyncMock(return_value=_charger(STATUS_PREPARING))

        await self.coordinator.async_start_charging()

        self.api.async_start_charging.assert_awaited_once()
        self.assertTrue(self.coordinator.pending_charging)
        self.assertIsNotNone(self.coordinator.data)

    async def test_stop_sets_pending_off(self) -> None:
        self.api.async_stop_charging = AsyncMock()
        self.api.async_get_charger = AsyncMock(return_value=_charger(STATUS_CHARGING))

        await self.coordinator.async_stop_charging()

        self.api.async_stop_charging.assert_awaited_once()
        self.assertFalse(self.coordinator.pending_charging)


if __name__ == "__main__":
    unittest.main()
