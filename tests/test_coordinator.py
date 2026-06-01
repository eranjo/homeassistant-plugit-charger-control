"""Unit tests for the Plugit coordinator."""

from __future__ import annotations

import unittest

from custom_components.plugit_charger_control.api import PlugitApi
from custom_components.plugit_charger_control.coordinator import (
    PlugitDataUpdateCoordinator,
)
from custom_components.plugit_charger_control.const import (
    GATEWAY_BASE_URL,
    ORY_BASE_URL,
)

from tests.helpers import FakeResponse, FakeSession


USER_POINTS_URL = GATEWAY_BASE_URL + "/charge-points/user-charge-points"
LOGIN_FLOW_URL = ORY_BASE_URL + "/self-service/login/api"
LOGIN_POST_URL = ORY_BASE_URL + "/self-service/login?flow=flow-123"
REGISTER_URL = GATEWAY_BASE_URL + "/users/register-session"


class PlugitCoordinatorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_coordinator_refresh(self) -> None:
        session = FakeSession()
        session.add_response("GET", LOGIN_FLOW_URL, FakeResponse(200, {"id": "flow-123"}))
        session.add_response(
            "POST",
            LOGIN_POST_URL,
            FakeResponse(200, {"session_token": "session-token"}),
        )
        session.add_response(
            "POST",
            REGISTER_URL,
            FakeResponse(200, {"accessToken": "access-token"}),
        )
        session.add_response(
            "GET",
            USER_POINTS_URL,
            FakeResponse(
                200,
                [
                    {
                        "_id": "cp-1",
                        "name": "Home charger",
                        "chargeBoxGroups": [
                            {
                                "_id": "cbg-1",
                                "chargeBoxes": [
                                    {"_id": "box-1", "status": "Preparing"}
                                ],
                            }
                        ],
                    }
                ],
            ),
        )

        api = PlugitApi(session, "user@example.com", "secret")
        coordinator = PlugitDataUpdateCoordinator(
            hass=None,
            api=api,
            charge_point_id="cp-1",
            charge_box_group_id="cbg-1",
            charge_box_id="box-1",
        )

        await coordinator.async_request_refresh()

        self.assertTrue(coordinator.last_update_success)
        self.assertIsNotNone(coordinator.last_successful_refresh)
        self.assertEqual(coordinator.data.status, "Preparing")

    async def test_coordinator_session_expiration(self) -> None:
        session = FakeSession()
        session.add_response("GET", LOGIN_FLOW_URL, FakeResponse(200, {"id": "flow-123"}))
        session.add_response(
            "POST",
            LOGIN_POST_URL,
            FakeResponse(200, {"session_token": "session-token-1"}),
        )
        session.add_response(
            "POST",
            REGISTER_URL,
            FakeResponse(200, {"accessToken": "access-token-1"}),
        )
        session.add_response("GET", USER_POINTS_URL, FakeResponse(401, {"error": "expired"}))
        session.add_response("GET", LOGIN_FLOW_URL, FakeResponse(200, {"id": "flow-123"}))
        session.add_response(
            "POST",
            LOGIN_POST_URL,
            FakeResponse(200, {"session_token": "session-token-2"}),
        )
        session.add_response(
            "POST",
            REGISTER_URL,
            FakeResponse(200, {"accessToken": "access-token-2"}),
        )
        session.add_response(
            "GET",
            USER_POINTS_URL,
            FakeResponse(
                200,
                [
                    {
                        "_id": "cp-1",
                        "chargeBoxGroups": [
                            {
                                "_id": "cbg-1",
                                "chargeBoxes": [
                                    {"_id": "box-1", "status": "Charging"}
                                ],
                            }
                        ],
                    }
                ],
            ),
        )

        api = PlugitApi(session, "user@example.com", "secret")
        coordinator = PlugitDataUpdateCoordinator(
            hass=None,
            api=api,
            charge_point_id="cp-1",
            charge_box_group_id="cbg-1",
            charge_box_id="box-1",
        )

        await coordinator.async_request_refresh()

        self.assertEqual(coordinator.data.status, "Charging")
        self.assertEqual(api.access_token, "access-token-2")

    async def test_refresh_interval_update(self) -> None:
        class FakeConfigEntries:
            def __init__(self) -> None:
                self.updated = None

            def async_update_entry(self, entry, options) -> None:
                self.updated = {"entry": entry, "options": options}

        class FakeHass:
            def __init__(self) -> None:
                self.config_entries = FakeConfigEntries()

        session = FakeSession()
        api = PlugitApi(session, "user@example.com", "secret")
        entry = type("Entry", (), {"options": {}})()
        coordinator = PlugitDataUpdateCoordinator(
            hass=FakeHass(),
            api=api,
            charge_point_id="cp-1",
            charge_box_group_id="cbg-1",
            charge_box_id="box-1",
            config_entry=entry,
            refresh_interval_seconds=60,
        )

        await coordinator.async_set_refresh_interval(120)

        self.assertEqual(coordinator.refresh_interval_seconds, 120)
        self.assertEqual(coordinator.update_interval.total_seconds(), 120)
        self.assertEqual(coordinator.hass.config_entries.updated["options"]["refresh_interval"], 120)
