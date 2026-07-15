# InkSight Widget Embedding Guide

## Overview

InkSight provides a read-only Widget API, allowing you to embed e-paper content into various platforms' widgets.

## API Endpoint

```
GET /api/widget/{mac}?mode=STOIC&size=medium
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mac` | Device MAC address | Required |
| `mode` | Content mode | The first mode configured on the device |
| `w` | Width (px) | 400 |
| `h` | Height (px) | 300 |
| `size` | Preset size: small/medium/large | medium |

### Size Presets

- `small`: 200x150 (suitable for small widgets)
- `medium`: 400x300 (standard size)
- `large`: 800x480 (large screen/landscape)

### Response

- Content-Type: `image/png`
- Cache-Control: `public, max-age=300` (5 minutes CDN cache)
- Does not trigger device state updates

## iOS Scriptable

```javascript
let mac = "AA:BB:CC:DD:EE:FF"
let server = "https://your-inksight-server.com"
let url = `${server}/api/widget/${mac}?size=medium`

let widget = new ListWidget()
let req = new Request(url)
let img = await req.loadImage()
widget.backgroundImage = img
widget.setPadding(0, 0, 0, 0)

if (config.runsInWidget) {
  Script.setWidget(widget)
} else {
  widget.presentMedium()
}
Script.complete()
```

## Android KWGT

1. Create a new widget in KWGT
2. Add an Image module
3. Set the image source to URL:
   ```
   https://your-server/api/widget/YOUR_MAC?size=small
   ```
4. Set the refresh interval to 30 minutes

## Web Embedding

```html
<iframe
  src="https://your-server/widget?mac=YOUR_MAC&mode=STOIC&size=medium"
  width="400"
  height="300"
  frameborder="0"
  style="border-radius: 8px; border: 1px solid #e5e5e5;"
></iframe>
```

## macOS Widgetsmith / Übersicht

```coffeescript
command: "curl -s 'https://your-server/api/widget/YOUR_MAC?size=large' -o /tmp/inksight.png && echo done"
refreshFrequency: 1800000  # 30 minutes

render: (output) ->
  """
  <img src="/tmp/inksight.png" style="width:100%;height:100%;object-fit:contain">
  """
```

## Web Page

Visit `https://your-server/widget?mac=YOUR_MAC` to see a live widget preview.

Supported URL parameters are the same as the API endpoint.
