# Fan Controller

Fan Controller is a Home Assistant custom integration that automatically controls a bathroom fan from a light and humidity sensors. It provides an Auto Mode switch and configurable post-run, manual-runtime, and humidity-rise limits.

**This code is heavily generated using LLMs**

## Configuration

During setup, select the fan, light, and humidity entities for the room. The average humidity sensor supplies the baseline used to calculate the automatic-start threshold. Configure the Auto Mode switch after setup to enable or disable automatic control.

Options are available from the integration's **Configure** action:

- **Fan Timeout**: post-run duration after humidity recovers.
- **Maximum Fan Timeout**: cap for a manually enabled fan.
- **Humidity Threshold**: percentage increase above the baseline that starts the fan.
- **Minimum Delta**: percentage decrease produced by the fan to keep it running