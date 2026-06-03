# Plugit Charger Control

Credit: this integration is based on the reverse-engineered work in [`okko/plugit-charger-control`](https://github.com/okko/plugit-charger-control).

[![Open your Home Assistant instance and show the integration in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eranjo&repository=homeassistant-plugit-charger-control&category=integration)

[![GitHub release](https://img.shields.io/github/v/release/eranjo/homeassistant-plugit-charger-control?style=for-the-badge)](https://github.com/eranjo/homeassistant-plugit-charger-control/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom%20Integration-41BDF5?style=for-the-badge)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-03A9F4?style=for-the-badge)](https://www.home-assistant.io/)

Home Assistant custom integration for Plugit EV chargers.

This integration is based on the reverse-engineered flow from the original `plugit-charger-control` project and uses the Plugit mobile API endpoints directly.

> **Warning**
> This is an unofficial community integration. Use it entirely at your own risk, and only if you are allowed to access and automate the Plugit account or chargers you connect to it.

## Features

- Config flow with username/password login
- Automatic charger discovery after sign-in
- Charger selection UI
- Polling via `DataUpdateCoordinator`
- Start charging and stop charging buttons
- Raw charger status sensor
- Current power sensor and charging duration sensor
- Binary sensors for charging activity and cable connection
- Editable refresh interval number entity
- Diagnostics with selected charger IDs

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository.
3. Select the integration category.
4. Install `Plugit EV Charger`.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/plugit_charger_control/` into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings > Devices & services > Add integration**.

## Configuration

1. Enter your Plugit username and password.
2. Home Assistant discovers your chargers from `GET /charge-points/user-charge-points`.
3. Select the charger you want to expose in Home Assistant.

The integration stores:

- `chargePointId`
- `chargeBoxId`
- `chargeBoxGroupId`

## Example entities

- `button.plugit_start_charging`
- `button.plugit_stop_charging`
- `sensor.plugit_status`
- `sensor.plugit_power`
- `sensor.plugit_charging_duration`
- `sensor.plugit_last_successful_refresh`
- `binary_sensor.plugit_charging_active`
- `binary_sensor.plugit_cable_connected`
- `number.plugit_refresh_interval`

The charging duration sensor is derived from the charger status timeline. It starts when the charger enters `Charging` and keeps the last session length after charging stops.

## Example automation

Start charging at 21:03 if plugged in:

```yaml
alias: Start charging at night
trigger:
  - platform: time
    at: "21:03:00"
condition:
  - condition: state
    entity_id: binary_sensor.plugit_cable_connected
    state: "on"
action:
  - service: button.press
    target:
      entity_id: button.plugit_start_charging
mode: single
```

## Notes

- The integration preserves the raw Plugit status values like `Available`, `Preparing`, `Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing`, `ERROR`, and `Unavailable`.
- Charging only starts when the charger is in a ready state.
- The integration avoids optimistic state updates and waits for a fresh API poll after each action.
- The refresh interval is editable from Home Assistant as a duration entity, stored in seconds internally.

## GitHub Setup

Recommended repository metadata:

- Description: `Home Assistant custom integration for Plugit EV chargers`
- Topics: `home-assistant`, `hacs`, `custom-component`, `ev-charger`, `plugit`, `home-automation`

Recommended repository layout:

- `custom_components/plugit_charger_control/`
- `tests/`
- `README.md`
- `LICENSE`
- `hacs.json` if you want to declare HACS metadata explicitly

## Release Checklist

Before publishing a release:

1. Run the unit test suite.
2. Verify the config flow still discovers chargers.
3. Confirm the `number.plugit_refresh_interval` entity updates the coordinator interval.
4. Check that the GitHub release tag matches the version in `manifest.json`.
5. Update the release notes with any API or entity changes.

## Legal And Attribution

- This project is an independent community integration and is not affiliated with, endorsed by, or supported by Plugit.
- It uses reverse-engineered, undocumented API endpoints from the Plugit mobile app. Those endpoints can change or stop working at any time.
- You are responsible for using the integration in a way that complies with Plugit's terms of service, your account permissions, and any applicable laws in your jurisdiction.
- If you choose to use this repository, you do so at your own risk.
- The repository is provided as-is, without warranty of any kind.
- If you reuse or redistribute parts of this project, make sure you have the rights to do so and that you keep any required notices intact.

## License Note

This repository is licensed under the MIT License. If you reuse or redistribute this project, make sure any upstream material you incorporated is permitted for that use and that you keep required notices intact.
