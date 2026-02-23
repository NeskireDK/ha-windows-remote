# Planned Features

Goal: seamless couch gaming with a desktop PC that power-saves when not in use.
The PC is a multi-function machine — desktop (keyboard + mouse, multiple monitors) and
couch/TV (controller, living room display). Switching between these modes gracefully is
the core use case.

---

## Blockers (fix before v1.0)

These are documented bugs that undermine trust in the integration.

- [ ] **Steam: tray 503** — `POST /api/steam/run/{appId}` returns 200 even when the tray
  is not running and no game launches. Service should return 503 so HA can surface the
  error to the user. *(service)*

- [ ] **Steam: running game not in source list** — `GetRunningGameAsync` falls back to
  `"Unknown ({appId})"` if the games cache isn't warm. Should call `GetGamesAsync()`
  internally to warm the cache, and inject the running game into the list if it falls
  outside the top-20 cutoff. *(service)*

---

## v1.0

### 1. PC Mode — `POST /api/system/mode` + `select` entity

Single endpoint that atomically sequences audio output, monitor profile, volume, and
app launch/kill from a named config block.

```json
"Modes": {
  "couch": {
    "AudioDevice": "HDMI Output",
    "MonitorProfile": "tv-only",
    "Volume": 40,
    "LaunchApp": "steam-bigpicture"
  },
  "desktop": {
    "AudioDevice": "Speakers",
    "MonitorProfile": "desk-full",
    "Volume": 25,
    "KillApp": "steam-bigpicture"
  }
}
```

HA exposes a `select` entity "PC Mode" with options from `GET /api/system/modes`.
Selecting a mode calls the endpoint. The service handles sequencing and waits between
steps — no fragile automation chains.

- [ ] Service: add `Modes` config section and `POST /api/system/mode` endpoint *(service)*
- [ ] Service: add `GET /api/system/modes` to list available mode names *(service)*
- [ ] Integration: `PcRemoteModeSelect` entity in `select.py` *(integration)*
- [ ] Integration: `set_mode()` in `api.py` *(integration)*

### 2. Couch Gaming Automation Blueprint

Blueprint with selector inputs — no hard-coded entity names.

Inputs:
- `trigger_entity` — any binary sensor or media player (TV power, controller sensor, etc.)
- `trigger_state` — state that activates couch mode
- `pc_power_switch` — PC Remote power switch
- `pc_mode_select` — PC Mode select entity (from feature 1)
- `couch_mode_name` — default: `couch`
- `desktop_mode_name` — default: `desktop`
- `sleep_on_revert` — sleep PC when leaving couch mode

Two automations in the blueprint: enter (wake if offline → select couch mode),
exit (select desktop mode → optionally sleep).

- [ ] `blueprints/automation/pc_remote/couch_gaming.yaml` *(integration)*

### 3. Aggregated State Endpoint — `GET /api/system/state`

Single endpoint replaces the 6+ individual coordinator calls per poll cycle.

```json
{
  "audio": { "devices": [...], "current": "Speakers", "volume": 40 },
  "monitors": [...],
  "monitorProfiles": [...],
  "apps": [...],
  "steam": { "games": [...], "running": null }
}
```

Prerequisite for reducing poll interval to 10s so mode switches feel responsive.

- [ ] Service: add `GET /api/system/state` endpoint *(service)*
- [ ] Integration: refactor `_async_update_data` to use single call *(integration)*

---

## v1.1

### 4. Controller Connected Binary Sensor

`Windows.Gaming.Input` via tray IPC exposes connected gamepads. HA gets a
`binary_sensor` that is `on` when at least one controller is connected.
`extra_state_attributes` lists controller names.

Natural automation trigger: pick up controller → enter couch mode automatically.

- [ ] Service: tray IPC `controllerGetConnected`, expose via `GET /api/system/controllers` *(service)*
- [ ] Integration: `PcRemoteControllerSensor` in new `binary_sensor.py` platform *(integration)*

### 5. Post-Session Sleep Blueprint

When the Steam media player transitions `playing → idle`, wait N minutes, confirm
still idle, then sleep the PC. Closes the power-saving loop without manual action.

Inputs: `steam_player`, `pc_power_switch`, `idle_minutes` (default: 10),
`require_controller_disconnected`.

- [ ] `blueprints/automation/pc_remote/post_session_sleep.yaml` *(integration)*

### 6. User Idle Time Sensor

`GetLastInputInfo` Win32 API (via tray IPC) → seconds since last keyboard/mouse input.
Guards the sleep blueprint against sleeping a PC that someone is actively using at the desk.

- [ ] Service: tray IPC `getIdleSeconds`, expose via `GET /api/system/idle` *(service)*
- [ ] Integration: `sensor` entity "Idle Time" (device class `duration`) *(integration)*
