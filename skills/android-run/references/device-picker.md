# Device picker (android-run)

When multiple devices are connected, pick carefully.

## List devices

```
tool: mcp__plugin_build_android_apps_adb__list_devices
```

Returns:
```json
{
  "devices": [
    {"serial": "emulator-5554", "state": "device", "model": "Pixel_6_API_34", "api": 34},
    {"serial": "RF8M40ABCDE", "state": "device", "model": "SM-G998U", "api": 33}
  ]
}
```

## Pick logic

1. If exactly 1 device → use it silently.
2. If multiple → ask the user, showing serial + model + API for each.
3. If 0 devices → tell the user to plug in a phone or start an emulator, and exit cleanly.

## Wire-vs-wireless

- `emulator-*` serials are emulators.
- Real serials are usually alphanumeric (Samsung) or `xxx:yyy` (wireless ADB).

Do not assume which is faster. Emulators are typically more reliable for headless runs.
