# SAJ Sununo-TL Series Monitor

A Home Assistant integration for monitoring SAJ Sununo-TL Series solar inverters via local network connection.

![Badge: Integration Type][device-badge]
![Badge: Python Version][python-badge]
![Badge: License][license-badge]

## Overview

This integration provides real-time monitoring of SAJ Sununo-TL Series solar inverters. It retrieves data directly from your inverter's local XML API endpoints without requiring cloud connectivity.

### Features

- 🌞 **Real-time Monitoring**: Get live data from your SAJ inverter every 3 seconds
- 📊 **20 Sensor Types**: Monitor voltage, current, power, temperature, energy production, and up to 4 PV strings
- 🎯 **Smart Averaging**: Collects data every 3 seconds but publishes smoothed averages every 5 minutes to reduce Home Assistant load
- 📍 **Multi-Device Support**: Add multiple inverters to your Home Assistant instance
- 🌐 **Bilingual**: Full support for English and Dutch
- ⚡ **Optimized**: Efficient local polling without cloud dependencies
- 🏠 **Home Area Integration**: Automatically assign devices to areas
- 🔌 **Dynamic String Detection**: Automatically detects available PV string connectors (2-4 strings)

### Tested Devices

This integration has been tested and confirmed working with:

- **SAJ Sununo-TL4KA** - 4kW Single-Phase Inverter (with 2 strings connected)

**Expected Compatibility:**
- Other Sununo TL Series inverters

The integration automatically detects available string connectors (up to 4 PV inputs). Unused string sensors are automatically hidden. If you successfully use this integration with another SAJ Sununo-TL model, please report it so we can update this list!

### Monitored Sensors

| Sensor | Unit | Type | Description |
|--------|------|------|-------------|
| **Grid Voltage** | V | Measurement | AC voltage at grid connection |
| **Grid Current** | A | Measurement | AC current flowing to grid |
| **Grid Frequency** | Hz | Measurement | Grid frequency |
| **Grid Power** | W | Measurement | Real-time AC power output |
| **Temperature** | °C | Measurement | Internal inverter temperature |
| **Energy Today** | kWh | Total Increasing | Energy produced today |
| **Energy Total** | kWh | Total Increasing | Cumulative energy produced |
| **PV1 Voltage** | V | Measurement | String 1 input voltage |
| **PV1 Current** | A | Measurement | String 1 input current |
| **PV2 Voltage*** | V | Measurement | String 2 input voltage |
| **PV2 Current*** | A | Measurement | String 2 input current |
| **PV3 Voltage*** | V | Measurement | String 3 input voltage |
| **PV3 Current*** | A | Measurement | String 3 input current |
| **PV4 Voltage*** | V | Measurement | String 4 input voltage |
| **PV4 Current*** | A | Measurement | String 4 input current |
| **Bus Voltage*** | V | Measurement | Internal bus voltage |
| **Runtime Today** | h | - | Operating hours today (diagnostic) |
| **Runtime Total** | h | - | Total operating hours (diagnostic) |
| **CO2 Reduction** | kg | - | Equivalent CO2 avoided (diagnostic) |
| **State** | - | - | Inverter operating state |

**Note**: Sensors marked with * only deliver a value if your inverter has those strings connected.

## Installation

### Manual Installation

1. Download this repository or clone it:
   ```bash
   git clone https://github.com/FrankCAD/saj_sununo_monitor.git
   ```

2. Copy the `saj_sununo_monitor` folder to your `config/custom_components/` directory:
   ```
   /config/custom_components/saj_sununo_monitor/
   ```

3. Restart Home Assistant

4. Go to **Settings** → **Devices & Services** → **Create Automation** and search for "SAJ Sununo-TL Series Monitor"

## Configuration

### Prerequisites

- SAJ Sununo-TL Series inverter with network connectivity
- IP address of your inverter (e.g., `192.168.1.100`)
- Local network access to the inverter

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Create Automation** button
3. Search for **"SAJ Sununo-TL Series Monitor"**
4. Select and click **Create Entry**
5. Fill in the configuration:
   - **Host IP address**: The IP address of your inverter
   - **Device name**: A friendly name for this inverter
   - **Area**: Select the area where the inverter is located (optional)
6. Click **Submit**

The integration will automatically:
- Fetch device information from your inverter
- Detect available PV string connectors
- Create sensors for all available data points
- Poll data every 3 seconds and publish averaged values every 5 minutes

### Reconfiguration

You can modify the configuration at any time by:

1. Going to **Settings** → **Devices & Services**
2. Finding your SAJ device under "Devices"
3. Clicking the three-dot menu and selecting **Reconfigure**

## Unavailability Handling

When the inverter becomes unavailable (unreachable or offline):

- **State**: Set to `"unreachable"` immediately
- **Grace Period**: Sensors retain their last known values for one polling cycle (3 seconds)
- **After Grace Period**:
  - **Protected sensors** retain last values indefinitely:
    - Total Energy
    - Total Runtime
    - Temperature
    - CO2 Reduction
  - **Other sensors**: Reset to `0`

When the inverter comes back online, sensors resume normal operation with fresh data.

## Device Information

Each inverter device includes:

- **Manufacturer**: SAJ
- **Model**: Retrieved from inverter
- **Model ID**: Product code from inverter
- **Serial Number**: Inverter serial number
- **Software Version**: Firmware version

## Troubleshooting

### Connection Issues

**"Failed to connect to the inverter"**

- Verify the inverter has sunlight (inverter must be operational)
- Verify the inverter IP address is correct
- Ensure your Home Assistant instance can reach the inverter on the local network
- Check firewall rules aren't blocking port 80 (HTTP)
- Verify the inverter is powered on and connected to your network

### Missing Data

**Sensors show "unavailable"**

- Check the inverter is powered on and in operation
- Verify network connectivity to the inverter
- Check Home Assistant logs for connection errors

**Missing PV string sensors (PV2, PV3, PV4)**

This is normal! The integration automatically detects available string connectors. If your inverter only has 2 strings connected, PV3 and PV4 sensors won't appear. You'll see one warning in the logs during initial setup identifying which strings are not connected - this is informational only.

If you add additional string connectors later, restart Home Assistant to detect them.

### Language Issues

The integration automatically detects your Home Assistant language. Supported languages:

- 🇬🇧 English
- 🇳🇱 Dutch

## Performance Tips

- **Optimized Polling**: The integration polls every 3 seconds but only updates Home Assistant every 5 minutes with averaged values, significantly reducing database writes and system load
- **Averaging Benefits**:
  - Smoother sensor values without noise/spikes
  - Reduced Home Assistant database size
  - Lower CPU usage
  - Better long-term statistics
- **Diagnostics**: Less important sensors (runtime, CO2, temperature) are marked as diagnostic to reduce dashboard clutter
- **Device Areas**: Assign your inverter to an area to organize it with other devices
- **String Detection**: Only sensors for connected strings are created, keeping your entity list clean

## Technical Details

- **Data Source**: Inverter XML API endpoints
- **Polling Architecture**:
  - Scan interval: 3 seconds (high-frequency data collection)
  - Storage interval: 300 seconds (5 minutes)
  - Data buffering with mean calculation for smooth averaged values
- **Communication**: Defused XML parsing for security
- **Data Type**: Strictly typed with validation
- **Load Optimization**: Reduces Home Assistant state updates by 100x compared to direct polling

## Development

This integration follows Home Assistant best practices:

- 📝 Full type hints and code documentation
- 🧪 Proper error handling and logging
- 🔒 Security: Defused XML parsing, no sensitive data logging
- 📍 Entity categories for better UX
- 🌍 Translation support (en and nl)

## Support

For issues, feature requests, or contributions:

- 📧 GitHub Issues: [FrankCAD/saj_sununo_monitor](https://github.com/FrankCAD/saj_sununo_monitor/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/FrankCAD/saj_sununo_monitor/discussions)

## License

This project is licensed under the MIT License.

---

**Tip**: Use this integration alongside Home Assistant's energy dashboard to track your solar energy production and consumption patterns.

[device-badge]: https://img.shields.io/badge/Integration-Device-blue
[python-badge]: https://img.shields.io/badge/Python-3.13+-blue
[license-badge]: https://img.shields.io/badge/License-MIT-green
