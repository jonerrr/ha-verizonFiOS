# Verizon FiOS Router Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/skircr115/ha-verizonFiOS?include_prereleases)](https://github.com/skircr115/ha-verizonFiOS/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/skircr115/ha-verizonFiOS/blob/main/LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/skircr115/ha-verizonFiOS/graphs/commit-activity)

A comprehensive Home Assistant integration for Verizon FiOS CR1000A and CE1000A routers.

## Installation

### HACS (Recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=https%3A%2F%2Fgithub.com%2Fskircr115%2Fha-verizonFiOS&owner=skircr115&category=Integration)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3 dots in the top right
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/skircr115/ha-verizonFiOS`
6. Category: Integration
7. Click "Install"
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/verizon_fios` directory to your `config/custom_components` directory
2. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Verizon FiOS Router"
4. Enter your router details:
   - **Router URL**: `https://192.168.1.1` (default)
   - **Username**: `admin` (default)
   - **Password**: Your router admin password
5. Click **Submit**

### Supported Routers

- ✅ Verizon CR1000A (tested)
- ✅ Verizon CE1000A (mesh extender, tested)
- 🔶 Other Verizon FiOS routers (likely compatible)

## Features

### 🎯 **100+ Sensors!**

This integration provides extensive monitoring of your Verizon FiOS network:

**Sensor Count:**
- **Router only:** ~71 sensors
- **Router + 1 extender:** ~117 sensors ✅
- **Router + 2 extenders:** ~163 sensors

**Coverage:**

- **Router Performance**: CPU, memory, temperature, uptime
- **Network Quality**: Signal strength, SNR, retry rates, error rates per band
- **Device Tracking**: Total, active, inactive, by type, by vendor, by OS
- **WiFi Analytics**: Per-band device counts (main/IoT/guest), WiFi standards (4/5/6/6E)
- **Mesh Network**: Full extender monitoring with all the same metrics
- **All SSIDs**: Main, Guest, IoT, IPTV, Backhaul networks

### 🕹️ **Phase 1 Controls**

Writable entities are now available for:

- **Router reboot** button (`button.verizon_fios_reboot_router`)
- **Per-device internet block** switches (`switch.verizon_fios_*_internet_block`)

Notes:
- Device block/unblock support uses the same local control flow as the router UI.
- Because Verizon firmware differs by model/version, command support can vary.
- If a write action fails, enable debug logging and share logs in an issue.

### 📊 Sensor Categories

#### Core Router Metrics
- CPU usage (total, user, system, idle)
- Memory (used, free, total, percentage)
- Temperature monitoring
- Uptime tracking

#### Network Breakdown
- Devices per band: 2.4GHz, 5GHz, 6GHz
- Sub-network tracking: Main, IoT, Guest, IPTV, Backhaul
- Ethernet/wired connections
- WiFi standard distribution (WiFi 4/5/6/6E)

#### Network Quality (per band)
- Average signal strength
- Min/max signal strength
- Average SNR (signal-to-noise ratio)
- Average link rates
- Packet retry counts
- Error counts

#### Device Intelligence (Attribute-Based)
- **By Type**: Single sensor with device type breakdown in attributes (phones, tablets, computers, IoT, cameras, TVs, etc.)
- **By Vendor**: Single sensor with vendor breakdown in attributes (Apple, Samsung, Google, and more)
- **By OS**: Single sensor with OS breakdown in attributes (Android, iOS, Windows, macOS, Linux, embedded)

Access device details via attributes for cleaner entity management!

#### Mesh Extenders (per extender)
- All router metrics (CPU, memory, temperature, uptime)
- Connection details (signal, type, link rate)
- Per-band device counts
- Update status

## Design Philosophy

### Attribute-Based Device Analytics

Instead of creating 30-50 individual sensors for each device type, vendor, and OS (like traditional approaches), this integration uses a **smarter attribute-based design**:

**3 Summary Sensors:**
- `sensor.verizon_fios_router_device_types` - Shows count of device types
- `sensor.verizon_fios_router_device_vendors` - Shows count of vendors
- `sensor.verizon_fios_router_device_os` - Shows count of operating systems

**Each sensor has attributes with the full breakdown:**
```yaml
sensor.verizon_fios_router_device_types:
  state: "10 types"
  attributes:
    Phone: 5
    Tablet: 2
    Computer: 8
    IoT: 12
    Camera: 3
    ...
```

**Benefits:**
- ✅ Cleaner entity list (~35 fewer sensors)
- ✅ All data still accessible via templates
- ✅ Professional, maintainable design
- ✅ Better database performance
- ✅ Easier to work with in dashboards

**Access in Templates:**
```jinja
{# Get specific device type count #}
{{ state_attr('sensor.verizon_fios_router_device_types', 'Phone') }}

{# List all device types #}
{% for type, count in state_attr('sensor.verizon_fios_router_device_types', 'attributes').items() %}
  {{ type }}: {{ count }}
{% endfor %}
```

## Usage

### Dashboard Examples

#### Quick Status Card
```yaml
type: glance
title: Network Status
entities:
  - entity: sensor.verizon_fios_router_total_connected_devices
    name: Devices
  - entity: sensor.verizon_fios_router_temperature
    name: Router
  - entity: sensor.verizon_fios_extender_1_temperature
    name: Extender
  - entity: sensor.verizon_fios_router_uptime_days
    name: Uptime
```

#### WiFi Network Load
```yaml
type: glance
title: WiFi Networks
entities:
  - entity: sensor.verizon_fios_router_devices_2g
    name: 2.4G Main
  - entity: sensor.verizon_fios_router_devices_5g
    name: 5G Main
  - entity: sensor.verizon_fios_router_devices_6g
    name: 6G Main
  - entity: sensor.verizon_fios_router_devices_wifi_total
    name: WiFi Total
```

#### Network Quality
```yaml
type: entities
title: Network Quality
entities:
  - entity: sensor.verizon_fios_router_2g_avg_signal
    name: 2.4G Signal (Avg)
  - entity: sensor.verizon_fios_router_5g_avg_signal
    name: 5G Signal (Avg)
  - entity: sensor.verizon_fios_router_6g_avg_signal
    name: 6G Signal (Avg)
  - entity: sensor.verizon_fios_router_2g_total_retries
    name: 2.4G Retries
  - entity: sensor.verizon_fios_router_5g_total_retries
    name: 5G Retries
```

#### Device Breakdown (Using Attributes)
```yaml
type: markdown
title: Device Analytics
content: |
  ### Device Types
  **Total Types:** {{ states('sensor.verizon_fios_router_device_types') }}
  {% for type, count in state_attr('sensor.verizon_fios_router_device_types', 'attributes').items() %}
  - **{{ type }}**: {{ count }}
  {% endfor %}
  
  ### Top Vendors
  **Total Vendors:** {{ states('sensor.verizon_fios_router_device_vendors') }}
  {% for vendor, count in (state_attr('sensor.verizon_fios_router_device_vendors', 'attributes').items() | sort(attribute=1, reverse=true))[:5] %}
  - **{{ vendor }}**: {{ count }}
  {% endfor %}
  
  ### Operating Systems
  **Total OS Types:** {{ states('sensor.verizon_fios_router_device_os') }}
  {% for os, count in state_attr('sensor.verizon_fios_router_device_os', 'attributes').items() %}
  - **{{ os }}**: {{ count }}
  {% endfor %}
```

Or use simple entity cards:
```yaml
type: entities
title: Device Summary
entities:
  - entity: sensor.verizon_fios_router_device_types
    name: Device Types
  - entity: sensor.verizon_fios_router_device_vendors
    name: Vendors
  - entity: sensor.verizon_fios_router_device_os
    name: Operating Systems
```

### Automations

#### High Temperature Alert
```yaml
automation:
  - alias: "Router Overheating"
    trigger:
      platform: numeric_state
      entity_id: sensor.verizon_fios_router_temperature
      above: 75
    action:
      service: notify.mobile_app
      data:
        title: "Router Temperature Alert"
        message: "Router temperature is {{ states('sensor.verizon_fios_router_temperature') }}°C"
```

#### Mesh Extender Offline
```yaml
automation:
  - alias: "Mesh Extender Offline"
    trigger:
      platform: numeric_state
      entity_id: sensor.verizon_fios_router_mesh_extenders
      below: 1
    action:
      service: notify.mobile_app
      data:
        message: "Mesh extender is offline!"
```

#### Too Many IoT Devices
```yaml
automation:
  - alias: "IoT Device Alert"
    trigger:
      platform: template
      value_template: >
        {{ state_attr('sensor.verizon_fios_router_device_types', 'IoT') | int(0) > 20 }}
    action:
      service: notify.mobile_app
      data:
        message: >
          Warning: {{ state_attr('sensor.verizon_fios_router_device_types', 'IoT') }} 
          IoT devices connected!
```

## Update Frequency

The integration updates every **4 hours** by default to avoid overloading the router. This can be adjusted in the source code if needed.

## Technical Details

### Authentication

This integration uses reverse-engineered Verizon router authentication:
- Custom "ArcMD5" hashing (MD5 → SHA512)
- Dynamic token-based password hashing
- Secure session management with cookies

### Data Sources

The integration fetches data from:
- `/cgi/cgi_basic.js` - Router topology and basic info
- `/cgi/cgi_owl.js` - Extended device and station information

### Privacy & Security

- ✅ All communication is local (no cloud required)
- ✅ Passwords are never stored in plain text
- ✅ Uses HTTPS with the router
- ✅ Local operations only (read + optional local write actions)

## Troubleshooting

### Can't Connect

- Verify router URL (default: `https://192.168.1.1`)
- Confirm username (default: `admin`)
- Check password is correct
- Ensure Home Assistant can reach the router

### Missing Sensors

- Some sensors only appear when devices are connected
- Device analytics sensors show type/vendor/OS breakdowns as **attributes** (not individual sensors)
- Extender sensors only appear if extenders are configured
- Network quality sensors (per band) only appear when devices are active on that band

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.verizon_fios: debug
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Contributors

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for a list of contributors who have helped make this project better!

## Support

- 🐛 [Report Issues](https://github.com/skircr115/ha-verizonFiOS/issues)
- 💬 [Discussions](https://github.com/skircr115/ha-verizonFiOS/discussions)
- 📖 [Documentation](README.md)

## License

MIT License - see LICENSE file for details

## Credits

Developed through reverse-engineering of Verizon's proprietary router authentication and API.

## Changelog

### v1.0.7 (2025-11-29) - Current Release
- 🎨 Improved sensor naming consistency
- ✅ Time sensors now show units: "Uptime (hours)", "Uptime (days)"
- ✅ Quality metrics use clearer format: "2G Signal (Avg)" instead of "2G Avg Signal"
- ✅ Device counts simplified: "2.4G Main Devices" instead of "2.4G Main SSID Devices"
- ✅ Aggregate sensors consistent: "WiFi All Devices" instead of "Total WiFi Devices"
- ✅ WiFi standards properly formatted: "WiFi 4 Devices" instead of "Devices: Wifi 4"
- ℹ️ No breaking changes - entity IDs unchanged, only friendly names updated

### v1.0.6 (2025-11-29)
- ✨ Added missing main SSID device sensors (2.4G, 5G, 6G)
- ✨ Added WiFi total rollup sensor (all WiFi devices, excludes ethernet)
- 🔧 Fixed aggregate sensor calculations (5G and 6G now include backhaul)
- ⚠️ Breaking: Renamed aggregate sensors for clarity
  - `devices_2g` → `devices_2g_total`
  - `devices_5g` → `devices_5g_total`
  - `devices_6g` → `devices_6g_total`

### v1.0.5 (2025-11-28)
- 🔧 Fixed unit of measurement for data_rate sensors (Mbps → Mbit/s)
- ✅ Resolved Home Assistant unit validation warnings
- ✅ All sensors now comply with HA standards

### v1.0.4 (2025-11-28)
- 🔧 Fixed numeric value parsing for link_rate and signal sensors
- ✅ Strip unit suffixes (Mbps, dBm) from router responses
- ✅ Proper int/float conversion for device_class compatibility

### v1.0.3 (2025-11-28)
- 🔧 Matched authentication flow to working PyScript version
- ✅ Complete User-Agent header
- ✅ Cookie extraction order (Set-Cookie header first)
- ✅ Improved login reliability

### v1.0.2 (2025-11-28)
- 🔧 Fixed JSON parsing for text/javascript content-type
- ✅ Manual JSON parsing instead of response.json()
- ✅ Handles router's non-standard content-type

### v1.0.1 (2025-11-28)
- 🔧 Enhanced debugging and error logging
- ✅ Comprehensive debug output at each authentication step
- ✅ Better timeout handling
- ✅ Improved exception handling

### v1.0.0 (2025-11-28) - Initial Release
- 🎉 Initial release
- ✅ Support for CR1000A and CE1000A routers
- ✅ 115+ sensors covering all router metrics (router + 1 extender)
- ✅ Config flow for easy setup
- ✅ Per-band device tracking
- ✅ Network quality monitoring
- ✅ Full mesh extender support
- ✅ Attribute-based device analytics (cleaner than individual sensors)

---

**⭐ If you find this integration useful, please star the repository!**
