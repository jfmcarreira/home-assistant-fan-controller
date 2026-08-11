# Fan Controller

Fan Controller is a Home Assistant custom integration that automatically controls a bathroom fan from a light and humidity sensors. It provides an Auto Mode switch and configurable post-run, manual-runtime, and humidity-rise limits.

This code is heavilly generated using LLMs

## Requirements

- Home Assistant with HACS installed
- A fan entity and associated light entity
- A room humidity sensor and an average humidity sensor
- Optional dehumidifier switch

## Installation

1. In HACS, open **Integrations** and select the three-dot menu.
2. Choose **Custom repositories** and add this repository with category **Integration**.
3. Search for **Fan Controller** in HACS and select **Download**.
4. Restart Home Assistant.
5. Go to **Settings** > **Devices & services** > **Add integration**, then select **Fan Controller**.

## Configuration

During setup, select the fan, light, and humidity entities for the room. The average humidity sensor supplies the baseline used to calculate the automatic-start threshold. Configure the Auto Mode switch after setup to enable or disable automatic control.

Options are available from the integration's **Configure** action:

- **Fan Timeout**: post-run duration after humidity recovers.
- **Maximum Fan Timeout**: cap for a manually enabled fan.
- **Humidity Threshold**: percentage increase above the baseline that starts the fan.

## Development

Create a virtual environment and install the test dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements_test.txt
```

Run the test suite and lint checks:

```bash
source .venv/bin/activate
pytest -q
ruff check custom_components tests
```
