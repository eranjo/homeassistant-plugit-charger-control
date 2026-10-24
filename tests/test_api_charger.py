"""Tests for PlugitCharger status helpers."""

from __future__ import annotations

import unittest

from custom_components.plugit_charger_control.api import PlugitCharger
from custom_components.plugit_charger_control.const import (
    STATUS_AVAILABLE,
    STATUS_CHARGING,
    STATUS_PREPARING,
)


def _charger(status: str) -> PlugitCharger:
    return PlugitCharger(
        charge_point_id="cp",
        charge_box_group_id="group",
        charge_box_id="box",
        status=status,
    )


class PlugitChargerStatusTests(unittest.TestCase):
    def test_can_start_only_when_preparing(self) -> None:
        self.assertTrue(_charger(STATUS_PREPARING).can_start)
        self.assertFalse(_charger(STATUS_AVAILABLE).can_start)
        self.assertFalse(_charger(STATUS_CHARGING).can_start)

    def test_is_charging_only_when_charging(self) -> None:
        self.assertTrue(_charger(STATUS_CHARGING).is_charging)
        self.assertFalse(_charger(STATUS_PREPARING).is_charging)
        self.assertFalse(_charger(STATUS_AVAILABLE).is_charging)

    def test_is_connected_for_cable_statuses(self) -> None:
        self.assertTrue(_charger(STATUS_PREPARING).is_connected)
        self.assertTrue(_charger(STATUS_CHARGING).is_connected)
        self.assertFalse(_charger(STATUS_AVAILABLE).is_connected)


if __name__ == "__main__":
    unittest.main()
