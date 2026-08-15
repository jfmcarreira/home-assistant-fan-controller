# Fan Controller Agent Guide

## Project Layout

- `custom_components/fan_controller/`: Home Assistant custom integration.
- `coordinator.py`: Fan state machine, entity listeners, humidity decisions, and timers.
- `config_flow.py`: Setup and integration options.
- `switch.py`: Auto Mode entity and diagnostic attributes.
- `tests/`: pytest coverage using `pytest-homeassistant-custom-component` fixtures.
- `scripts/read_recorder_history.py`: Read-only Home Assistant recorder history helper.

## Development

Use Python 3.13 or later. Install test dependencies with:

```sh
.venv/bin/python -m pip install -r requirements_test.txt
```

Run before submitting changes:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check custom_components tests scripts
.venv/bin/python -m ruff format --check custom_components tests scripts
```

Ruff is configured in `pyproject.toml` with a 120-character line limit. Do not run the formatter over unrelated files unless the task calls for formatting them.

## Home Assistant Rules

- Keep configured entity IDs stable and validate any changed consumers.
- Add user-configurable values to `const.py`, `config_flow.py`, translations, and option-flow tests together.
- Use Home Assistant async APIs for service calls and state listeners.
- Do not use device IDs where entity IDs are available.
- Keep `manifest.json` keys ordered as `domain`, `name`, then alphabetically.
- Validate humidity sensors server-side: they must have the humidity device class and the room and average sensors must differ.
- Keep a config entry's `unique_id` stable during reconfiguration and use only one entry-reload mechanism.

## Fan State Machine

- `fan_on_high_humidity` handles humidity-driven operation after the light is off.
- `fan_on_timeout` is the post-run state; entering it starts the configured fan timeout.
- No-op self-transitions must remain `internal=True`, otherwise state-entry handlers can restart timers.
- Humidity progress checks apply only in `fan_on_high_humidity` and transition to `fan_on_timeout` when stalled.
- Humidity progress uses its own scheduled timer. Start or restart it with each progress window, and cancel it when leaving high humidity, disabling Auto Mode, or unloading the entry.
- A fan started while the light is on always uses `light_on_fan_on`; only a fan started while the light is off enters `fan_manual_on` and receives the manual runtime limit.
- `light_on_fan_off` represents a user opting out while the light is on. Re-enabling the fan in that session returns to `light_on_fan_on` without a manual timer.
- Treat fan and light updates as normal sequential events. Do not add high-humidity or post-run transitions solely for a coalesced "light on, fan off" snapshot unless explicitly requested.
- Add regression coverage for every state or timer behavior change.

## Recorder Script And Secrets

- The recorder script reads `DB_*` settings from a local `.env` file or environment variables.
- `.env` is ignored by Git. Never commit or print database credentials.
- The script requires `PyMySQL`, installed locally with `.venv/bin/python -m pip install PyMySQL`.
- Database access should be limited to a user with `SELECT` permission on the Home Assistant recorder database.

## CI

- `tests.yml` runs pytest and Ruff.
- `checks.yml` runs Hassfest and HACS validation.
- Releases run the reusable test and check workflows before creating a release.
