# Verizon FiOS Router Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A comprehensive Home Assistant integration for Verizon FiOS CR1000A and CE1000A routers.

## Features

### 🎯 **100+ Sensors!**

This integration provides extensive monitoring of your Verizon FiOS network:

- **Router Performance**: CPU, memory, temperature, uptime
- **Network Quality**: Signal strength, SNR, retry rates, error rates per band
- **Device Tracking**: Total, active, inactive, by type, by vendor, by OS
- **WiFi Analytics**: Per-band device counts (main/IoT/guest), WiFi standards (4/5/6/6E)
- **Mesh Network**: Full extender monitoring with all the same metrics
- **All SSIDs**: Main, Guest, IoT, IPTV, Backhaul networks

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

#### Device Intelligence
- **By Type**: Phones, tablets, computers, IoT, cameras, TVs, etc.
- **By Vendor**: Apple, Samsung, Google, and more
- **By OS**: Android, iOS, Windows, macOS, Linux, embedded

#### Mesh Extenders (per extender)
- All router metrics (CPU, memory, temperature, uptime)
- Connection details (signal, type, link rate)
- Per-band device counts
- Update status

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3 dots in the top right
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/yourusername/verizon_fios_router`
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

#### Network Quality
```yaml
type: entities
title: Network Quality
entities:
  - entity: sensor.verizon_fios_router_2g_avg_signal
    name: 2.4GHz Signal
  - entity: sensor.verizon_fios_router_5g_avg_signal
    name: 5GHz Signal
  - entity: sensor.verizon_fios_router_6g_avg_signal
    name: 6GHz Signal
  - entity: sensor.verizon_fios_router_2g_total_retries
    name: 2.4GHz Retries
  - entity: sensor.verizon_fios_router_5g_total_retries
    name: 5GHz Retries
```

#### Device Breakdown
```yaml
type: entities
title: Device Types
entities:
  - entity: sensor.verizon_fios_router_devices_type_phone
    name: Phones
  - entity: sensor.verizon_fios_router_devices_type_computer
    name: Computers
  - entity: sensor.verizon_fios_router_devices_type_iot
    name: IoT Devices
  - entity: sensor.verizon_fios_router_devices_type_smart_tv
    name: Smart TVs
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
- ✅ Read-only operations (doesn't change router settings)

## Troubleshooting

### Can't Connect

- Verify router URL (default: `https://192.168.1.1`)
- Confirm username (default: `admin`)
- Check password is correct
- Ensure Home Assistant can reach the router

### Missing Sensors

- Some sensors only appear when devices are connected
- Dynamic sensors (device types, vendors) only show for detected devices
- Extender sensors only appear if extenders are configured

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

## Support

- 🐛 [Report Issues](https://github.com/yourusername/verizon_fios_router/issues)
- 💬 [Discussions](https://github.com/yourusername/verizon_fios_router/discussions)

## License

MIT License - see LICENSE file for details

## Credits

Developed through reverse-engineering of Verizon's proprietary router authentication and API.

## Changelog

### v1.0.0 (2025-11-12)
- 🎉 Initial release
- ✅ Support for CR1000A and CE1000A routers
- ✅ 100+ sensors covering all router metrics
- ✅ Config flow for easy setup
- ✅ Per-band device tracking
- ✅ Network quality monitoring
- ✅ Full mesh extender support

---

**⭐ If you find this integration useful, please star the repository!**
