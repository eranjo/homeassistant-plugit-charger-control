"""Constants for the Plugit charger control integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "plugit_charger_control"
MANUFACTURER = "Plugit"
NAME = "Plugit EV Charger"

ORY_BASE_URL = "https://ory.plugitcloud.com"
GATEWAY_BASE_URL = "https://app-gw.plugitcloud.com"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_REFRESH_INTERVAL = "refresh_interval"
CONF_CHARGE_POINT_ID = "chargePointId"
CONF_CHARGE_BOX_ID = "chargeBoxId"
CONF_CHARGE_BOX_GROUP_ID = "chargeBoxGroupId"
CONF_CHARGER_SELECTION = "charger_selection"

ATTR_CHARGE_POINT_ID = "chargePointId"
ATTR_CHARGE_BOX_ID = "chargeBoxId"
ATTR_CHARGE_BOX_GROUP_ID = "chargeBoxGroupId"
ATTR_STATUS = "status"
ATTR_LAST_SUCCESSFUL_REFRESH = "last_successful_refresh"

STATUS_AVAILABLE = "Available"
STATUS_PREPARING = "Preparing"
STATUS_CHARGING = "Charging"
STATUS_SUSPENDED_EV = "SuspendedEV"
STATUS_SUSPENDED_EVSE = "SuspendedEVSE"
STATUS_FINISHING = "Finishing"
STATUS_ERROR = "ERROR"
STATUS_UNAVAILABLE = "Unavailable"

VALID_STATUSES = (
    STATUS_AVAILABLE,
    STATUS_PREPARING,
    STATUS_CHARGING,
    STATUS_SUSPENDED_EV,
    STATUS_SUSPENDED_EVSE,
    STATUS_FINISHING,
    STATUS_ERROR,
    STATUS_UNAVAILABLE,
)

READY_TO_START_STATUSES = {STATUS_PREPARING}
CHARGING_ACTIVE_STATUSES = {STATUS_CHARGING}
CABLE_CONNECTED_STATUSES = {
    STATUS_PREPARING,
    STATUS_CHARGING,
    STATUS_SUSPENDED_EV,
    STATUS_SUSPENDED_EVSE,
    STATUS_FINISHING,
}
