# GitHub Publishing Notes

## Suggested repository details

- Repository name: `homeassistant-plugit-charger-control`
- Description: `Home Assistant custom integration for Plugit EV chargers`
- Topics:
  - `home-assistant`
  - `hacs`
  - `custom-component`
  - `ev-charger`
  - `plugit`
  - `home-automation`

## Recommended files

- `custom_components/plugit_charger_control/`
- `brand/icon.png`
- `tests/`
- `README.md`
- `LICENSE`
- `hacs.json` if you want to publish HACS metadata explicitly

## Release checklist

1. Run `python3 -m unittest discover -s tests -v`.
2. Confirm charger discovery and button actions work in Home Assistant.
3. Verify the refresh interval number entity still updates the coordinator interval.
4. Bump the version in `custom_components/plugit_charger_control/manifest.json`.
5. Create a GitHub release that matches the manifest version.
