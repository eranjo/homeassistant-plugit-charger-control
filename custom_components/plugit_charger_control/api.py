"""Async HTTP client for the Plugit mobile app API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .const import (
    ATTR_CHARGE_BOX_GROUP_ID,
    ATTR_CHARGE_BOX_ID,
    ATTR_CHARGE_POINT_ID,
    CABLE_CONNECTED_STATUSES,
    GATEWAY_BASE_URL,
    ORY_BASE_URL,
    READY_TO_START_STATUSES,
    STATUS_AVAILABLE,
    STATUS_ERROR,
    STATUS_UNAVAILABLE,
)

_LOGGER = logging.getLogger(__name__)


class PlugitError(Exception):
    """Base error for Plugit API failures."""


class PlugitAuthError(PlugitError):
    """Authentication or session refresh failed."""


class PlugitApiError(PlugitError):
    """Unexpected API failure."""


class PlugitChargeBoxNotFoundError(PlugitApiError):
    """Selected charger was not found in the API payload."""


class PlugitChargingNotReadyError(PlugitApiError):
    """The charger is not in a state that can start charging."""


class PlugitChargingNotActiveError(PlugitApiError):
    """The charger is not currently charging."""


@dataclass
class PlugitCharger:
    """Normalized charger state."""

    charge_point_id: str
    charge_box_group_id: str
    charge_box_id: str
    status: str
    charge_point_name: Optional[str] = None
    charge_box_group_name: Optional[str] = None
    charge_box_name: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Return a friendly charger label."""

        parts = [
            self.charge_point_name or self.charge_point_id,
            self.charge_box_group_name or self.charge_box_group_id,
            self.charge_box_name or self.charge_box_id,
        ]
        return " / ".join(parts)

    @property
    def can_start(self) -> bool:
        """Return whether the charger is ready to start."""

        return self.status in READY_TO_START_STATUSES

    @property
    def is_connected(self) -> bool:
        """Return whether the cable appears to be connected."""

        return self.status in CABLE_CONNECTED_STATUSES

    @property
    def is_charging(self) -> bool:
        """Return whether the charger is actively charging."""

        return self.status == "Charging"


def _extract_name(payload: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if value:
            return str(value)
    return None


class PlugitApi:
    """Plugit API client with cached access token refresh."""

    def __init__(self, session: Any, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._session_token: Optional[str] = None
        self._access_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    async def async_login(self, force: bool = False) -> str:
        """Authenticate against Ory Kratos and Plugit gateway."""

        if self._access_token and not force:
            return self._access_token

        _LOGGER.debug("Initializing Plugit login flow for %s", self._username)
        flow_response = await self._request_raw(
            "get",
            f"{ORY_BASE_URL}/self-service/login/api",
            auth=False,
        )
        flow_data = await self._response_json(
            flow_response,
            "Failed to initialize login flow",
        )
        flow_id = flow_data.get("id")
        if not flow_id:
            raise PlugitAuthError("Login flow response did not include an id")

        login_payload = {
            "method": "password",
            "identifier": self._username,
            "password": self._password,
        }
        login_response = await self._request_raw(
            "post",
            f"{ORY_BASE_URL}/self-service/login?flow={flow_id}",
            auth=False,
            json_body=login_payload,
            headers={"Content-Type": "application/json"},
        )
        login_data = await self._response_json(
            login_response,
            "Plugit login failed",
            auth_error=True,
        )
        session_token = login_data.get("session_token")
        if not session_token:
            raise PlugitAuthError("No session_token in login response")

        register_response = await self._request_raw(
            "post",
            f"{GATEWAY_BASE_URL}/users/register-session",
            auth=False,
            json_body={"token": session_token},
            headers={"Content-Type": "application/json"},
        )
        register_data = await self._response_json(
            register_response,
            "Register session failed",
            auth_error=True,
        )
        access_token = register_data.get("accessToken")
        if not access_token:
            raise PlugitAuthError("No accessToken in register-session response")

        self._session_token = str(session_token)
        self._access_token = str(access_token)
        _LOGGER.debug("Plugit authentication succeeded")
        return self._access_token

    async def async_discover_chargers(self) -> List[PlugitCharger]:
        """Fetch all available chargers for the authenticated user."""

        payload = await self._request_json("get", "/charge-points/user-charge-points")
        if not isinstance(payload, list):
            raise PlugitApiError("Unexpected discovery payload from Plugit API")

        chargers: List[PlugitCharger] = []
        for charge_point in payload:
            if not isinstance(charge_point, dict):
                continue

            charge_point_id = str(
                charge_point.get("_id")
                or charge_point.get(ATTR_CHARGE_POINT_ID)
                or charge_point.get("id")
                or ""
            )
            if not charge_point_id:
                continue
            charge_point_name = _extract_name(
                charge_point,
                "name",
                "displayName",
                "label",
                "title",
            )
            for charge_box_group in charge_point.get("chargeBoxGroups", []):
                if not isinstance(charge_box_group, dict):
                    continue
                charge_box_group_id = str(
                    charge_box_group.get("_id")
                    or charge_box_group.get(ATTR_CHARGE_BOX_GROUP_ID)
                    or charge_box_group.get("id")
                    or ""
                )
                if not charge_box_group_id:
                    continue
                charge_box_group_name = _extract_name(
                    charge_box_group,
                    "name",
                    "displayName",
                    "label",
                    "title",
                )
                for charge_box in charge_box_group.get("chargeBoxes", []):
                    if not isinstance(charge_box, dict):
                        continue
                    charge_box_id = str(
                        charge_box.get("_id")
                        or charge_box.get(ATTR_CHARGE_BOX_ID)
                        or charge_box.get("id")
                        or ""
                    )
                    if not charge_box_id:
                        continue
                    status = str(charge_box.get("status") or STATUS_UNAVAILABLE)
                    chargers.append(
                        PlugitCharger(
                            charge_point_id=charge_point_id,
                            charge_box_group_id=charge_box_group_id,
                            charge_box_id=charge_box_id,
                            status=status,
                            charge_point_name=charge_point_name,
                            charge_box_group_name=charge_box_group_name,
                            charge_box_name=_extract_name(
                                charge_box,
                                "name",
                                "displayName",
                                "label",
                                "title",
                            ),
                            raw=charge_box,
                        )
                    )

        chargers.sort(key=lambda charger: charger.display_name.lower())
        _LOGGER.debug("Discovered %s chargers", len(chargers))
        return chargers

    async def async_get_charger(
        self,
        charge_point_id: str,
        charge_box_group_id: str,
        charge_box_id: str,
    ) -> PlugitCharger:
        """Return the selected charger state."""

        chargers = await self.async_discover_chargers()
        for charger in chargers:
            if (
                charger.charge_point_id == charge_point_id
                and charger.charge_box_group_id == charge_box_group_id
                and charger.charge_box_id == charge_box_id
            ):
                return charger
        raise PlugitChargeBoxNotFoundError(
            "Charge box %s not found under charge point %s"
            % (charge_box_id, charge_point_id)
        )

    async def async_start_charging(
        self,
        charge_point_id: str,
        charge_box_group_id: str,
        charge_box_id: str,
    ) -> None:
        """Start charging only if the charger is ready."""

        charger = await self.async_get_charger(
            charge_point_id,
            charge_box_group_id,
            charge_box_id,
        )
        if not charger.can_start:
            raise PlugitChargingNotReadyError(
                "Charger status %s is not ready to start" % charger.status
            )

        payload = {
            ATTR_CHARGE_POINT_ID: charge_point_id,
            ATTR_CHARGE_BOX_GROUP_ID: charge_box_group_id,
            ATTR_CHARGE_BOX_ID: charge_box_id,
        }
        await self._request_json(
            "post",
            "/remote-start-transaction",
            json_body=payload,
        )
        _LOGGER.debug("Remote start requested for %s", charger.display_name)

    async def async_stop_charging(
        self,
        charge_point_id: str,
        charge_box_group_id: str,
        charge_box_id: str,
    ) -> None:
        """Stop charging when the charger is active."""

        charger = await self.async_get_charger(
            charge_point_id,
            charge_box_group_id,
            charge_box_id,
        )
        if not charger.is_charging:
            raise PlugitChargingNotActiveError(
                "Charger status %s is not actively charging" % charger.status
            )

        payload = {
            ATTR_CHARGE_POINT_ID: charge_point_id,
            ATTR_CHARGE_BOX_GROUP_ID: charge_box_group_id,
            ATTR_CHARGE_BOX_ID: charge_box_id,
        }
        await self._request_json(
            "post",
            "/remote-stop-transaction",
            json_body=payload,
        )
        _LOGGER.debug("Remote stop requested for %s", charger.display_name)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: bool = True,
        retry: bool = True,
    ) -> Any:
        response = await self._request_raw(
            method,
            path,
            json_body=json_body,
            headers=headers,
            auth=auth,
        )

        if response.status == 401 and auth and retry:
            _LOGGER.debug("Plugit access token expired, reauthenticating")
            await self.async_login(force=True)
            return await self._request_json(
                method,
                path,
                json_body=json_body,
                headers=headers,
                auth=auth,
                retry=False,
            )
        if response.status == 401 and auth:
            raise PlugitAuthError("Plugit access token rejected")

        return await self._response_json(response, "Plugit API request failed")

    async def _request_raw(
        self,
        method: str,
        url: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: bool = True,
    ) -> Any:
        if not url.startswith("http"):
            url = GATEWAY_BASE_URL + url
        request_headers = dict(headers or {})
        if auth:
            token = await self.async_login()
            request_headers["Authorization"] = token

        request_callable = getattr(self._session, method.lower(), None)
        if request_callable is None:
            request_callable = getattr(self._session, "request")
            context_manager = request_callable(
                method.upper(),
                url,
                headers=request_headers,
                json=json_body,
            )
        else:
            context_manager = request_callable(
                url,
                headers=request_headers,
                json=json_body,
            )

        async with context_manager as response:
            return _BufferedResponse(
                status=getattr(response, "status", 500),
                headers=getattr(response, "headers", {}),
                body=await response.text(),
            )

    async def _response_json(
        self,
        response: "_BufferedResponse",
        error: str,
        auth_error: bool = False,
    ) -> Any:
        if response.status >= 400:
            if auth_error and response.status in {400, 401, 403}:
                raise PlugitAuthError("%s: %s" % (error, response.body))
            raise PlugitApiError("%s: %s" % (error, response.body))

        if not response.body:
            return {}

        try:
            return json.loads(response.body)
        except ValueError as exc:
            raise PlugitApiError("%s: invalid JSON response" % error) from exc


@dataclass
class _BufferedResponse:
    status: int
    headers: Dict[str, Any]
    body: str
