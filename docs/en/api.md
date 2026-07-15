# API Reference

**Version:** v1.0.0

**Base URL:** `http://your-server:8080`

## 1. Overview

The InkSight backend handles device rendering, previews, configuration storage, device state, statistics, firmware info, and user-device binding.

### Authentication

| Method | Header / Credential | Description |
|--------|---------------------|-------------|
| Device Auth | `X-Device-Token` | Used for device-facing APIs |
| User Auth | Session Cookie | Set by backend after login |
| Admin Auth | Session Cookie | Required for admin-level operations |

### Common Return Types

| Type | Description |
|------|-------------|
| `image/bmp` | Rendered image for the e-paper device |
| `image/png` | Image for browser preview / sharing / widgets |
| `application/json` | Config, state, stats, user, and mode data |

---

## 2. API Endpoints

### 2.1 Render & Preview

#### `GET /api/render`

Main rendering endpoint for the device. Returns `image/bmp`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `v` | `float` | No | Battery voltage, defaults to `3.3` |
| `mac` | `string` | No | Device MAC; requires `X-Device-Token` if provided |
| `persona` | `string` | No | Force a specific mode |
| `rssi` | `int` | No | WiFi signal strength |
| `refresh_min` | `int` | No | Actual refresh interval in minutes |
| `w` | `int` | No | Screen width |
| `h` | `int` | No | Screen height |
| `next` | `int` | No | `1` to switch to the next mode |

#### `GET /api/preview`

Browser preview endpoint. Returns `image/png`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `v` | `float` | No | Preview voltage |
| `mac` | `string` | No | Device MAC |
| `persona` | `string` | No | Force a specific mode |
| `city_override` | `string` | No | Override city for this preview only |
| `mode_override` | `string` | No | JSON override for the current mode |
| `memo_text` | `string` | No | Override text for MEMO mode |
| `w` | `int` | No | Screen width |
| `h` | `int` | No | Screen height |
| `no_cache` | `int` | No | `1` to bypass cache |

---

### 2.2 Configuration & Modes

#### `POST /api/config`
Save device configuration. Requires admin privileges.

#### `GET /api/config/{mac}`
Get current configuration. Requires `X-Device-Token`.

#### `GET /api/config/{mac}/history`
Get configuration history. Requires `X-Device-Token`.

#### `PUT /api/config/{mac}/activate/{config_id}`
Activate a specific historical configuration. Requires admin privileges.

#### `GET /api/modes`
Get all built-in and custom modes.

#### `POST /api/modes/custom/preview`
Preview a custom mode definition. Requires admin privileges.

#### `POST /api/modes/custom`
Create a custom mode. Requires admin privileges.

#### `GET /api/modes/custom/{mode_id}`
Get a specific custom mode definition.

#### `DELETE /api/modes/custom/{mode_id}`
Delete a custom mode. Requires admin privileges.

#### `POST /api/modes/generate`
Use AI to generate a mode definition from a description. Requires admin privileges.

---

### 2.3 Firmware & Device Discovery

#### `GET /api/firmware/releases`
Get available firmware list from GitHub Releases.
Parameters:
- `refresh`: Optional, `true` to force cache refresh

#### `GET /api/firmware/releases/latest`
Get the latest recommended firmware.
Parameters:
- `refresh`: Optional, `true` to force cache refresh

#### `GET /api/firmware/validate-url`
Validate a manually entered firmware download URL.
Parameters:
- `url`: Required, must be an accessible `.bin` file URL

#### `GET /api/devices/recent`
Get recently online devices, used for discovering devices after flashing.
Parameters:
- `minutes`: Optional, default `10`

---

### 2.4 Device Control & Content

The following endpoints target a single device and usually require `X-Device-Token`.

#### `POST /api/device/{mac}/refresh`
Mark the device to refresh immediately on its next wake-up.

#### `GET /api/device/{mac}/state`
Get device runtime state, online status, and refresh interval.

#### `POST /api/device/{mac}/runtime`
Set runtime mode, supports:
- `active`
- `interval`

#### `POST /api/device/{mac}/apply-preview`
Push a one-time preview image to the device, returned on the next `/api/render`.

#### `POST /api/device/{mac}/switch`
Set the device to switch to a specific mode on its next refresh.

#### `POST /api/device/{mac}/favorite`
Favorite the most recent content, or a specific mode.

#### `GET /api/device/{mac}/favorites`
Get the device's favorite list.

#### `GET /api/device/{mac}/history`
Get device content history.
Common parameters:
- `limit`
- `offset`
- `mode`

#### `POST /api/device/{mac}/habit/check`
Record a habit check-in.

#### `GET /api/device/{mac}/habit/status`
Get habit status for the current week.

#### `DELETE /api/device/{mac}/habit/{habit_name}`
Delete a habit and its records.

#### `POST /api/device/{mac}/token`
Generate or return an existing device token.

#### `GET /api/device/{mac}/qr`
Generate a device binding QR code, returns `image/bmp`.

#### `GET /api/device/{mac}/share`
Generate a sharing image, returns `image/png`.

---

### 2.5 User & Device Binding

#### `POST /api/auth/register`
User registration, sets login state.

#### `POST /api/auth/login`
User login, sets login state.

#### `GET /api/auth/me`
Get current logged-in user info.

#### `POST /api/auth/logout`
Logout.

#### `GET /api/user/devices`
Get the list of devices bound to the current user.

#### `POST /api/user/devices`
Bind a device to the current user.

#### `DELETE /api/user/devices/{mac}`
Unbind a device from the current user.

---

### 2.6 Statistics

#### `GET /api/stats/overview`
Get global statistics overview. Requires admin privileges.

#### `GET /api/stats/{mac}`
Get device statistics details. Requires `X-Device-Token`.

#### `GET /api/stats/{mac}/renders`
Get device render history. Requires `X-Device-Token`.
Parameters:
- `limit`
- `offset`

---

## 3. Battery Mapping Algorithm

The backend calculates the battery percentage based on the `v` parameter (battery voltage). The current algorithm is a simple linear mapping, using 3.3V as the full-charge baseline:

```python
def calc_battery_pct(voltage: float) -> int:
    pct = int(voltage / 3.30 * 100)
    if pct < 0:
        return 0
    if pct > 100:
        return 100
    return pct
```

> **Note**: If the device uses a 3.7V lithium battery with an LDO step-down, the ADC voltage is usually the battery voltage after a voltage divider, or a constant 3.3V from the LDO (depending on hardware design). The current algorithm is primarily designed for 3.3V direct-drive scenarios.

When rendering the top status bar, the battery icon fills according to the percentage and changes color on multi-color displays (like 3-color e-paper):

- `< 20%`: Red (if supported)
- `< 50%`: Yellow (if supported)
- `Other`: Default foreground color (Black)

## 4. ESP32 Client Handling

Due to limited RAM on the ESP32, the device must use stream processing to handle the image:

```cpp
// Initiate request
http.begin("http://server/api/render?v=3.2");
int httpCode = http.GET();

if (httpCode == 200) {
    int len = http.getSize();
    WiFiClient *stream = http.getStreamPtr();

    // Stream directly to display buffer
    uint8_t buffer[128];
    while (http.connected() && (len > 0 || len == -1)) {
        size_t size = stream->available();
        if (size) {
            int c = stream->readBytes(buffer,
                ((size > sizeof(buffer)) ? sizeof(buffer) : size));
            // Write buffer to e-paper driver memory
        }
    }
}
```
