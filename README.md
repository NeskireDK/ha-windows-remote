# ha-windows-remote

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for controlling a Windows PC via the [ha-windows-remote-service](https://github.com/YOUR_USERNAME/ha-windows-remote-service).

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Install "Windows Remote"
3. Restart Home Assistant
4. Go to Settings → Integrations → Add → Windows Remote
5. Enter the IP, port, and API key from the Windows service

### Manual

Copy `custom_components/windows_remote/` to your Home Assistant `custom_components/` directory.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `binary_sensor.windows_remote_online` | Binary Sensor | PC online status |
| `button.windows_remote_sleep` | Button | Suspend the PC |

## License

MIT
