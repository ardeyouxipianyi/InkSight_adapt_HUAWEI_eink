# InkSight API 接口文档

**版本:** v1.0.0

**Base URL:** `http://your-server:8080`

## 1. 概述

InkSight 后端负责设备渲染、预览、配置存储、设备状态、统计、固件信息以及用户与设备绑定。

### 认证方式

| 方式 | 头 / 凭据 | 说明 |
|------|-----------|------|
| 设备鉴权 | `X-Device-Token` | 设备相关接口使用 |
| 用户鉴权 | Session Cookie | 登录后由后端写入 |
| 管理鉴权 | Session Cookie | 需要管理员权限的接口使用 |

### 常用返回类型

| 类型 | 说明 |
|------|------|
| `image/bmp` | 设备渲染图 |
| `image/png` | 浏览器预览图 / 分享图 / 小组件图 |
| `application/json` | 配置、状态、统计、用户、模式等数据 |

---

## 2. API 清单

### 2.1 渲染与预览

#### `GET /api/render`

设备端主渲染接口，返回 `image/bmp`。

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `v` | `float` | 否 | 电池电压，默认 `3.3` |
| `mac` | `string` | 否 | 设备 MAC；提供时需要 `X-Device-Token` |
| `persona` | `string` | 否 | 强制指定模式 |
| `rssi` | `int` | 否 | WiFi 信号强度 |
| `refresh_min` | `int` | 否 | 设备实际刷新间隔（分钟） |
| `w` | `int` | 否 | 屏幕宽度 |
| `h` | `int` | 否 | 屏幕高度 |
| `next` | `int` | 否 | `1` 表示切到下一个模式 |

可能返回的响应头：

- `X-Pending-Refresh`
- `X-Content-Fallback`
- `X-Preview-Push`

#### `GET /api/widget/{mac}`

只读小组件接口，返回 `image/png`，不会更新设备状态。

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `mode` | `string` | 否 | 指定模式 |
| `w` | `int` | 否 | 宽度 |
| `h` | `int` | 否 | 高度 |
| `size` | `string` | 否 | `small` / `medium` / `large` |

#### `GET /api/preview`

浏览器预览接口，返回 `image/png`。

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `v` | `float` | 否 | 预览电压 |
| `mac` | `string` | 否 | 设备 MAC |
| `persona` | `string` | 否 | 指定模式 |
| `city_override` | `string` | 否 | 仅本次预览覆盖城市 |
| `mode_override` | `string` | 否 | 当前模式的 JSON 覆盖 |
| `memo_text` | `string` | 否 | MEMO 模式文本覆盖 |
| `w` | `int` | 否 | 宽度 |
| `h` | `int` | 否 | 高度 |
| `no_cache` | `int` | 否 | `1` 表示跳过缓存 |

---

### 2.2 配置与模式

#### `POST /api/config`

保存设备配置。需要管理员权限。

#### `GET /api/config/{mac}`

获取当前配置。需要 `X-Device-Token`。

#### `GET /api/config/{mac}/history`

获取配置历史。需要 `X-Device-Token`。

#### `PUT /api/config/{mac}/activate/{config_id}`

激活指定历史配置。需要管理员权限。

#### `GET /api/modes`

获取全部内置和自定义模式。

#### `POST /api/modes/custom/preview`

预览自定义模式定义。需要管理员权限。

#### `POST /api/modes/custom`

创建自定义模式。需要管理员权限。

#### `GET /api/modes/custom/{mode_id}`

获取某个自定义模式定义。

#### `DELETE /api/modes/custom/{mode_id}`

删除自定义模式。需要管理员权限。

#### `POST /api/modes/generate`

使用 AI 根据描述生成模式定义。需要管理员权限。

---

### 2.3 固件与设备发现

#### `GET /api/firmware/releases`

获取 GitHub Releases 中可用的固件列表。

参数：

- `refresh`：可选，`true` 时强制刷新缓存

#### `GET /api/firmware/releases/latest`

获取最新推荐固件。

参数：

- `refresh`：可选，`true` 时强制刷新缓存

#### `GET /api/firmware/validate-url`

校验手动输入的固件下载地址。

参数：

- `url`：必填，必须为可访问的 `.bin` 文件地址

#### `GET /api/devices/recent`

获取最近上线的设备列表，用于刷机后发现设备。

参数：

- `minutes`：可选，默认 `10`

---

### 2.4 设备控制与内容

以下接口均面向单设备，通常需要 `X-Device-Token`。

#### `POST /api/device/{mac}/refresh`

标记设备下次唤醒时立即刷新。

#### `GET /api/device/{mac}/state`

获取设备运行状态、在线状态和刷新间隔。

#### `POST /api/device/{mac}/runtime`

设置运行模式，支持：

- `active`
- `interval`

#### `POST /api/device/{mac}/apply-preview`

推送一次性预览图到设备，下次 `/api/render` 时返回。

#### `POST /api/device/{mac}/switch`

设置设备下次刷新时切换到指定模式。

#### `POST /api/device/{mac}/favorite`

收藏最近一次内容，或收藏指定模式。

#### `GET /api/device/{mac}/favorites`

获取设备收藏列表。

#### `GET /api/device/{mac}/history`

获取设备内容历史。

常用参数：

- `limit`
- `offset`
- `mode`

#### `POST /api/device/{mac}/habit/check`

记录习惯打卡。

#### `GET /api/device/{mac}/habit/status`

获取当前周的习惯状态。

#### `DELETE /api/device/{mac}/habit/{habit_name}`

删除习惯及其记录。

#### `POST /api/device/{mac}/token`

生成或返回已有设备令牌。

#### `GET /api/device/{mac}/qr`

生成设备绑定二维码，返回 `image/bmp`。

#### `GET /api/device/{mac}/share`

生成分享图片，返回 `image/png`。

---

### 2.5 用户与设备绑定

#### `POST /api/auth/register`

用户注册，并写入登录态。

#### `POST /api/auth/login`

用户登录，并写入登录态。

#### `GET /api/auth/me`

获取当前登录用户信息。

#### `POST /api/auth/logout`

退出登录。

#### `GET /api/user/devices`

获取当前用户已绑定设备列表。

#### `POST /api/user/devices`

绑定设备到当前用户。

#### `DELETE /api/user/devices/{mac}`

解绑当前用户下的设备。

---

### 2.6 统计

#### `GET /api/stats/overview`

获取全局统计概览。需要管理员权限。

#### `GET /api/stats/{mac}`

获取设备统计详情。需要 `X-Device-Token`。

#### `GET /api/stats/{mac}/renders`

获取设备渲染历史。需要 `X-Device-Token`。

参数：

- `limit`
- `offset`

---

## 3. 电量映射算法

后端根据传入的 `v` 参数（电池电压）计算电量百分比。当前算法为简单的线性映射，以 3.3V 作为满电基准：

```python
def calc_battery_pct(voltage: float) -> int:
    pct = int(voltage / 3.30 * 100)
    if pct < 0:
        return 0
    if pct > 100:
        return 100
    return pct
```

> **注意**：如果设备使用 3.7V 锂电池并通过 LDO 降压供电，ADC 测量到的电压通常是经过分压电阻处理后的电池端电压，或者是 LDO 输出的恒定 3.3V（取决于硬件设计）。当前算法主要针对 3.3V 直驱场景设计。

在屏幕顶部状态栏的渲染中，电池图标会根据百分比自动填充，并在支持多色的屏幕上（如三色屏）根据电量改变颜色：

- `< 20%`：红色（如果屏幕支持）
- `< 50%`：黄色（如果屏幕支持）
- `其他`：默认前景色（黑色）

## 4. ESP32 客户端处理规范

由于 ESP32 内存有限，需采用流式处理 (Stream Processing)：

```cpp
// 发起请求
http.begin("http://server/api/render?v=3.2");
int httpCode = http.GET();

if (httpCode == 200) {
    int len = http.getSize();
    WiFiClient *stream = http.getStreamPtr();

    // 流式写入屏幕缓冲区
    uint8_t buffer[128];
    while (http.connected() && (len > 0 || len == -1)) {
        size_t size = stream->available();
        if (size) {
            int c = stream->readBytes(buffer,
                ((size > sizeof(buffer)) ? sizeof(buffer) : size));
            // 将 buffer 写入屏幕驱动的显存
        }
    }
}
```
