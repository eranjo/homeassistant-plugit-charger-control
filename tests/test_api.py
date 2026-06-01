"""Unit tests for the Plugit API client."""

from __future__ import annotations

import unittest

from custom_components.plugit_charger_control.api import (
    PlugitApi,
    PlugitApiError,
    PlugitAuthError,
    PlugitChargingNotReadyError,
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
START_URL = GATEWAY_BASE_URL + "/remote-start-transaction"
STOP_URL = GATEWAY_BASE_URL + "/remote-stop-transaction"


class PlugitApiTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_successful_login(self) -> None:
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

        api = PlugitApi(session, "user@example.com", "secret")
        token = await api.async_login()

        self.assertEqual(token, "access-token")
        self.assertEqual(api.session_token, "session-token")
        self.assertEqual(api.access_token, "access-token")

    async def test_failed_login(self) -> None:
        session = FakeSession()
        session.add_response("GET", LOGIN_FLOW_URL, FakeResponse(200, {"id": "flow-123"}))
        session.add_response(
            "POST",
            LOGIN_POST_URL,
            FakeResponse(401, {"error": "invalid credentials"}),
        )

        api = PlugitApi(session, "user@example.com", "wrong")

        with self.assertRaises(PlugitAuthError):
            await api.async_login()

    async def test_charger_discovery(self) -> None:
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
                                "name": "Garage",
                                "chargeBoxes": [
                                    {
                                        "_id": "box-1",
                                        "name": "Left socket",
                                        "status": "Preparing",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            ),
        )

        api = PlugitApi(session, "user@example.com", "secret")
        chargers = await api.async_discover_chargers()

        self.assertEqual(len(chargers), 1)
        charger = chargers[0]
        self.assertEqual(charger.charge_point_id, "cp-1")
        self.assertEqual(charger.charge_box_group_id, "cbg-1")
        self.assertEqual(charger.charge_box_id, "box-1")
        self.assertEqual(charger.status, "Preparing")
        self.assertEqual(charger.display_name, "Home charger / Garage / Left socket")

    async def test_remote_start_success(self) -> None:
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
        session.add_response("POST", START_URL, FakeResponse(200, {"ok": True}))

        api = PlugitApi(session, "user@example.com", "secret")
        await api.async_start_charging("cp-1", "cbg-1", "box-1")

        self.assertEqual(session.calls[-1]["url"], START_URL)
        self.assertEqual(session.calls[-1]["kwargs"]["json"]["chargePointId"], "cp-1")

    async def test_remote_start_failure(self) -> None:
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
        session.add_response("POST", START_URL, FakeResponse(500, {"error": "down"}))

        api = PlugitApi(session, "user@example.com", "secret")

        with self.assertRaises(PlugitApiError):
            await api.async_start_charging("cp-1", "cbg-1", "box-1")

    async def test_remote_start_requires_readiness(self) -> None:
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
                        "chargeBoxGroups": [
                            {
                                "_id": "cbg-1",
                                "chargeBoxes": [
                                    {"_id": "box-1", "status": "Available"}
                                ],
                            }
                        ],
                    }
                ],
            ),
        )

        api = PlugitApi(session, "user@example.com", "secret")

        with self.assertRaises(PlugitChargingNotReadyError):
            await api.async_start_charging("cp-1", "cbg-1", "box-1")

    async def test_api_unavailable_handling(self) -> None:
        session = FakeSession()
        session.add_response("GET", LOGIN_FLOW_URL, FakeResponse(500, {"error": "down"}))

        api = PlugitApi(session, "user@example.com", "secret")

        with self.assertRaises(PlugitApiError):
            await api.async_login()

    async def test_session_expiration_handling(self) -> None:
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
        chargers = await api.async_discover_chargers()

        self.assertEqual(chargers[0].status, "Charging")
        self.assertEqual(api.access_token, "access-token-2")

